#!/usr/bin/env python3
"""Collect quality metrics from test reports and generate metrics.json.

This script aggregates metrics from:
- pytest coverage reports (coverage.json)
- radon complexity analysis (complexity-report.txt)
- pydocstyle / ruff D rules documentation coverage (docs-report.txt)
- bandit security scanning (security-report.json)
- quality scripts via --metrics flag (script mode)

Threshold convention (Issue #206): pass/fail status is ALWAYS recomputed in
Python from the thresholds dict (see ``_default_thresholds``). Quality
scripts emit raw numbers; any ``status`` field they include is ignored so
threshold ownership lives in exactly one place.

Output: metrics.json in the specified output directory
"""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
from http import HTTPStatus
import http.client
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.generators.metrics import ci_status
from start_green_stay_green.generators.metrics import count_ci_jobs
from start_green_stay_green.generators.metrics import count_precommit_hooks
from start_green_stay_green.generators.metrics import precommit_status

if TYPE_CHECKING:
    from collections.abc import Mapping

# GitHub REST API endpoint used by the hybrid CI Status collection
# (Issue #159). HTTPS is enforced by construction via HTTPSConnection.
GITHUB_API_HOST = "api.github.com"
GITHUB_API_TIMEOUT_SECONDS = 10

# ``owner/repo`` slug as provided by the GITHUB_REPOSITORY env var.
GITHUB_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _github_api_json(path: str, token: str) -> object | None:
    """Fetch a JSON payload from the GitHub REST API over HTTPS.

    Args:
        path: Request path (e.g., ``/repos/owner/repo/actions/runs``).
        token: GitHub token used as a Bearer credential.

    Returns:
        The decoded JSON payload, or ``None`` on any network, HTTP, or
        decoding failure (callers fall back to static counting). Tokens
        containing interior whitespace are rejected outright —
        ``http.client`` does not sanitize header values, so this closes
        the header-injection path.
    """
    token = token.strip()
    if not token or re.search(r"\s", token):
        return None
    connection = http.client.HTTPSConnection(
        GITHUB_API_HOST, timeout=GITHUB_API_TIMEOUT_SECONDS
    )
    try:
        connection.request(
            "GET",
            path,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "start-green-stay-green-metrics",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response = connection.getresponse()
        if response.status != HTTPStatus.OK:
            return None
        payload: object = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, http.client.HTTPException):
        return None
    else:
        return payload
    finally:
        connection.close()


def _latest_main_run(runs_payload: object) -> dict[str, Any] | None:
    """Extract the latest workflow run from a runs API payload.

    Args:
        runs_payload: Decoded JSON from the workflow-runs endpoint.

    Returns:
        The first (most recent) run mapping with an ``id``, or ``None``
        when the payload is malformed or contains no runs.
    """
    if not isinstance(runs_payload, dict):
        return None
    runs = runs_payload.get("workflow_runs")
    if not isinstance(runs, list) or not runs:
        return None
    run = runs[0]
    if isinstance(run, dict) and "id" in run:
        return run
    return None


def _job_conclusion_counts(jobs_payload: object) -> tuple[int, int] | None:
    """Count total and successful jobs from a jobs API payload.

    Conditionally-skipped jobs (``conclusion: "skipped"``) are excluded
    from the denominator: a deploy job gated on a branch condition must
    not drag an otherwise all-green run below 100%.

    Args:
        jobs_payload: Decoded JSON from the run-jobs endpoint.

    Returns:
        A ``(total_jobs, passing_jobs)`` tuple counting only jobs that
        actually ran, or ``None`` when the payload is malformed.
    """
    if not isinstance(jobs_payload, dict):
        return None
    jobs = jobs_payload.get("jobs")
    if not isinstance(jobs, list):
        return None
    ran_jobs = [
        job
        for job in jobs
        if isinstance(job, dict) and job.get("conclusion") != "skipped"
    ]
    passing = sum(1 for job in ran_jobs if job.get("conclusion") == "success")
    return (len(ran_jobs), passing)


def _fetch_ci_status_from_api(repo: str, token: str) -> dict[str, object] | None:
    """Fetch CI job pass/fail counts for the latest main run via GitHub API.

    Queries the most recent completed workflow run on ``main`` and counts
    job conclusions (``success`` counts as passing). Any failure — invalid
    repo slug, network error, non-200 response, malformed payload, or no
    completed runs — returns ``None`` so the caller falls back to static
    workflow counting. Never raises.

    Args:
        repo: ``owner/repo`` slug (from the GITHUB_REPOSITORY env var).
        token: GitHub token (from the GITHUB_TOKEN env var).

    Returns:
        A ``ci_status`` mapping built by the canonical helper (including
        ``run_url``), or ``None`` when the API path is unavailable.
    """
    if not GITHUB_REPOSITORY_PATTERN.match(repo):
        return None

    runs_payload = _github_api_json(
        f"/repos/{repo}/actions/runs?branch=main&status=completed&per_page=1",
        token,
    )
    run = _latest_main_run(runs_payload)
    if run is None:
        return None

    # GitHub paginates this endpoint at 100 jobs per page; runs with more
    # jobs than that would be silently under-counted here.
    jobs_payload = _github_api_json(
        f"/repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100", token
    )
    counts = _job_conclusion_counts(jobs_payload)
    if counts is None:
        return None

    total_jobs, passing_jobs = counts
    run_url = run.get("html_url")
    return ci_status(
        total_jobs,
        passing_jobs,
        run_url=run_url if isinstance(run_url, str) else None,
    )


class MetricsCollector:
    """Collects and aggregates quality metrics from various report files."""

    def __init__(
        self,
        project_name: str,
        thresholds: Mapping[str, int | float],
    ) -> None:
        """Initialize metrics collector.

        Args:
            project_name: Name of the project
            thresholds: Dictionary of metric name -> threshold value
        """
        self.project_name = project_name
        self.thresholds = thresholds
        self.metrics: dict[str, Any] = {}

    def collect_coverage(self, coverage_file: Path) -> None:
        """Parse coverage from pytest JSON report.

        Args:
            coverage_file: Path to coverage.json file

        Raises:
            FileNotFoundError: If coverage file doesn't exist
            json.JSONDecodeError: If coverage file is not valid JSON
            KeyError: If expected keys are missing from coverage data
        """
        if not coverage_file.exists():
            msg = f"Coverage file not found: {coverage_file}"
            raise FileNotFoundError(msg)

        cov_data = json.loads(coverage_file.read_text())
        total_cov = cov_data["totals"]["percent_covered"]
        self.metrics["coverage"] = round(total_cov, 2)
        self.metrics["coverage_status"] = self._compute_status(
            total_cov, self.thresholds["coverage"]
        )

        # Branch coverage
        num_branches = cov_data["totals"].get("num_branches", 0)
        covered_branches = cov_data["totals"].get("covered_branches", 0)
        if num_branches > 0:
            branch_cov = (covered_branches / num_branches) * 100
            self.metrics["branch_coverage"] = round(branch_cov, 2)
            self.metrics["branch_coverage_status"] = self._compute_status(
                branch_cov, self.thresholds["branch_coverage"]
            )

    def collect_complexity(self, complexity_file: Path) -> None:
        """Parse complexity from radon report.

        Args:
            complexity_file: Path to complexity-report.txt file

        Raises:
            FileNotFoundError: If complexity file doesn't exist
            ValueError: If complexity pattern not found in file
        """
        if not complexity_file.exists():
            msg = f"Complexity file not found: {complexity_file}"
            raise FileNotFoundError(msg)

        complexity_text = complexity_file.read_text()
        patterns = [
            r"Average complexity: [A-Z] \(([0-9.]+)\)",
            r"Average complexity:\s+[A-Z]\s+\(([0-9.]+)\)",
            r"average:\s+([0-9.]+)",
        ]

        comp = None
        for pattern in patterns:
            match = re.search(pattern, complexity_text, re.IGNORECASE)
            if match:
                comp = float(match.group(1))
                break

        if comp is None:
            msg = "Could not find complexity pattern in report"
            raise ValueError(msg)

        self.metrics["complexity_avg"] = round(comp, 2)
        self.metrics["complexity_status"] = self._compute_status(
            comp, self.thresholds["complexity"], higher_is_better=False
        )

    def collect_docs_coverage(self, docs_file: Path) -> None:
        """Parse documentation coverage from docs report.

        Args:
            docs_file: Path to docs-report.txt file

        Raises:
            FileNotFoundError: If docs file doesn't exist
            ValueError: If docs coverage pattern not found in file
        """
        if not docs_file.exists():
            msg = f"Docs file not found: {docs_file}"
            raise FileNotFoundError(msg)

        docs_text = docs_file.read_text()
        patterns = [
            r"RESULT: ([0-9.]+)%",
            r"RESULT:\s+([0-9.]+)\s*%",
            r"Overall:\s+([0-9.]+)%",
            r"Coverage:\s+([0-9.]+)%",
        ]

        docs = None
        for pattern in patterns:
            match = re.search(pattern, docs_text, re.IGNORECASE)
            if match:
                docs = float(match.group(1))
                break

        if docs is None:
            msg = "Could not find docs coverage pattern in report"
            raise ValueError(msg)

        self.metrics["docs_coverage"] = round(docs, 2)
        self.metrics["docs_status"] = self._compute_status(
            docs, self.thresholds["docs_coverage"]
        )

    def collect_security(self, security_file: Path) -> None:
        """Parse security issues from bandit report.

        Args:
            security_file: Path to security-report.json file

        Raises:
            FileNotFoundError: If security file doesn't exist
            json.JSONDecodeError: If security file is not valid JSON
            KeyError: If expected keys are missing from security data
        """
        if not security_file.exists():
            msg = f"Security file not found: {security_file}"
            raise FileNotFoundError(msg)

        security_data = json.loads(security_file.read_text())
        issues = len(security_data["results"])
        self.metrics["security_issues"] = issues
        self.metrics["security_status"] = self._compute_status(
            issues, self.thresholds["security_issues"], higher_is_better=False
        )

    def collect_precommit_status(self, config_path: Path) -> None:
        """Collect pre-commit hooks status from the config file (Issue #154).

        Counts the total hooks configured in ``.pre-commit-config.yaml`` and
        records a ``precommit_status`` entry with ``total_hooks``,
        ``passing_hooks``, ``percentage`` and ``status``. Because running
        ``pre-commit run --all-files`` is expensive and CI already gates on
        it, this treats configured hooks as passing; a missing or empty
        config degrades gracefully to zero hooks with ``unknown`` status.

        Args:
            config_path: Path to the ``.pre-commit-config.yaml`` file.
        """
        total = count_precommit_hooks(config_path)
        self.metrics["precommit_status"] = precommit_status(total)

    def collect_ci_status(self, workflows_dir: Path) -> None:
        """Collect CI job status using the hybrid API/static strategy (#159).

        When ``GITHUB_TOKEN`` and ``GITHUB_REPOSITORY`` are available
        (GitHub Actions), the latest completed workflow run on ``main`` is
        queried via the GitHub API and job conclusions are counted
        (``success`` counts as passing), including the run URL. On any API
        failure — or outside CI — this degrades to statically counting jobs
        across ``.github/workflows/*.yml`` with ``unknown`` status (pass or
        fail cannot be known statically). Never raises.

        Args:
            workflows_dir: Path to the ``.github/workflows`` directory used
                for the static fallback count.
        """
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("GITHUB_REPOSITORY")

        status: dict[str, object] | None = None
        if token and repo:
            status = _fetch_ci_status_from_api(repo, token)
        if status is None:
            status = ci_status(count_ci_jobs(workflows_dir))
        self.metrics["ci_status"] = status

    def add_mutation_score(self, score: float) -> None:
        """Add mutation testing score.

        Args:
            score: Mutation score (0-100)
        """
        self.metrics["mutation_score"] = score
        self.metrics["mutation_status"] = self._compute_status(
            score, self.thresholds["mutation_score"]
        )

    def _set_mutation_unknown(self) -> None:
        """Set mutation metrics to unknown/null state."""
        self.metrics["mutation_score"] = None
        self.metrics["mutation_status"] = "unknown"

    @staticmethod
    def _compute_status(
        value: float | None,
        threshold: float,
        *,
        higher_is_better: bool = True,
    ) -> str:
        """Compute pass/fail/unknown status from a metric value.

        Args:
            value: Metric value, or None if unavailable
            threshold: Threshold for pass/fail
            higher_is_better: If True, value >= threshold is pass;
                if False, value <= threshold is pass

        Returns:
            "pass", "fail", or "unknown"
        """
        if value is None:
            return "unknown"
        if higher_is_better:
            return "pass" if value >= threshold else "fail"
        return "pass" if value <= threshold else "fail"

    def collect_mutation_from_cache(self, cache_path: Path) -> None:
        """Read mutation score directly from .mutmut-cache SQLite database.

        Args:
            cache_path: Path to .mutmut-cache file
        """
        if not cache_path.exists():
            self._set_mutation_unknown()
            return

        # Verify file looks like a SQLite database before connecting
        try:
            header = cache_path.read_bytes()[:16]
        except OSError:
            self._set_mutation_unknown()
            return

        if not header.startswith(b"SQLite format 3"):
            self._set_mutation_unknown()
            return

        conn = sqlite3.connect(str(cache_path))
        try:
            cursor = conn.execute("SELECT status, COUNT(*) FROM Mutant GROUP BY status")
            counts = dict(cursor.fetchall())
            cursor.close()
        except (sqlite3.Error, KeyError):
            self._set_mutation_unknown()
            return
        finally:
            conn.close()
        self._apply_mutation_counts(counts)

    def _apply_mutation_counts(self, counts: dict[str, int]) -> None:
        """Apply mutation counts from cache to metrics.

        Args:
            counts: Dictionary of status -> count from mutmut cache
        """
        killed = counts.get("ok_killed", 0)
        survived = counts.get("bad_survived", 0)
        timeout = counts.get("bad_timeout", 0)
        total = killed + survived + timeout

        if total > 0:
            score = round((killed / total) * 100, 1)
            self.metrics["mutation_score"] = score
            self.metrics["mutation_status"] = self._compute_status(
                score, self.thresholds["mutation_score"]
            )
        else:
            self._set_mutation_unknown()

    def collect_from_script(
        self, script_path: str, scripts_dir: Path
    ) -> dict[str, Any] | None:
        """Run a quality script with --metrics and parse JSON output.

        Args:
            script_path: Script filename (e.g., "lint.sh")
            scripts_dir: Directory containing the scripts

        Returns:
            Parsed JSON dict from script stdout, or None on failure.
        """
        full_path = scripts_dir / script_path
        if not full_path.exists():
            return None

        try:
            result = subprocess.run(  # noqa: S603 — script_path is a hardcoded internal filename, validated by exists() above
                [str(full_path), "--metrics"],
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
        else:
            try:
                parsed: dict[str, Any] = json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return None
            else:
                return parsed

    def collect_lint_metrics(self, scripts_dir: Path) -> None:
        """Collect lint metrics via lint.sh --metrics.

        Status is recomputed from the ``lint_violations`` threshold; any
        ``status`` field emitted by the script is ignored (Issue #206).

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("lint.sh", scripts_dir)
        violations = data.get("violations") if data is not None else None
        self.metrics["lint_violations"] = violations
        self.metrics["lint_status"] = self._compute_status(
            violations, self.thresholds["lint_violations"], higher_is_better=False
        )

    def collect_typecheck_metrics(self, scripts_dir: Path) -> None:
        """Collect type checking metrics via typecheck.sh --metrics.

        Status is recomputed from the ``type_errors`` threshold; any
        ``status`` field emitted by the script is ignored (Issue #206).

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("typecheck.sh", scripts_dir)
        errors = data.get("errors") if data is not None else None
        self.metrics["type_errors"] = errors
        self.metrics["typecheck_status"] = self._compute_status(
            errors, self.thresholds["type_errors"], higher_is_better=False
        )

    def collect_security_metrics(self, scripts_dir: Path) -> None:
        """Collect security metrics via security.sh --metrics.

        Status is recomputed from the ``security_issues`` threshold; any
        ``status`` field emitted by the script is ignored (Issue #206). A
        null ``bandit_issues`` value (scan failed) yields ``unknown``.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("security.sh", scripts_dir)
        issues = data.get("bandit_issues") if data is not None else None
        self.metrics["security_issues"] = issues
        self.metrics["security_status"] = self._compute_status(
            issues, self.thresholds["security_issues"], higher_is_better=False
        )

    def collect_docs_metrics(self, scripts_dir: Path, docs_file: Path) -> None:
        """Collect documentation coverage via metrics-docs.sh --metrics (#217).

        Runs the canonical docstring-coverage script (ruff D rules over an
        AST item count) and recomputes status from the ``docs_coverage``
        threshold (Issue #206). When the script yields no usable payload,
        falls back to parsing a pre-generated report file; if that also
        fails, the metric degrades to ``None``/``unknown``.

        Args:
            scripts_dir: Directory containing quality scripts
            docs_file: Fallback docs report file (e.g., docs-report.txt)
        """
        data = self.collect_from_script("metrics-docs.sh", scripts_dir)
        pct = data.get("docs_coverage_pct") if data is not None else None
        if pct is None and docs_file.exists():
            try:
                self.collect_docs_coverage(docs_file)
            except ValueError:
                pct = None
            else:
                return
        self.metrics["docs_coverage"] = pct
        self.metrics["docs_status"] = self._compute_status(
            pct, self.thresholds["docs_coverage"]
        )

    def collect_coverage_metrics(self, scripts_dir: Path) -> None:
        """Collect coverage metrics via coverage.sh --metrics.

        Status is recomputed from the ``coverage`` and ``branch_coverage``
        thresholds; any ``status`` field emitted by the script is ignored
        (Issue #206). Missing raw percentages yield ``unknown``.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("coverage.sh", scripts_dir)
        cov_pct = data.get("coverage_pct") if data is not None else None
        branch_pct = data.get("branch_coverage_pct") if data is not None else None
        self.metrics["coverage"] = cov_pct
        self.metrics["coverage_status"] = self._compute_status(
            cov_pct, self.thresholds["coverage"]
        )
        self.metrics["branch_coverage"] = branch_pct
        self.metrics["branch_coverage_status"] = self._compute_status(
            branch_pct, self.thresholds["branch_coverage"]
        )

    def collect_test_metrics(self, scripts_dir: Path) -> None:
        """Collect test count metrics via test.sh --metrics.

        Status is recomputed from raw counts; any ``status`` field emitted
        by the script is ignored (Issue #206). Tests have no tunable
        threshold: any failed test is a failure, and zero collected tests
        (a broken suite) or missing counts yield ``unknown``.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("test.sh", scripts_dir)
        if data is None:
            data = {}
        total = data.get("tests_total")
        failed = data.get("tests_failed")
        self.metrics["tests_total"] = total
        self.metrics["tests_passed"] = data.get("tests_passed")
        self.metrics["tests_failed"] = failed
        self.metrics["tests_skipped"] = data.get("tests_skipped")
        if not total or failed is None:
            self.metrics["tests_status"] = "unknown"
        else:
            self.metrics["tests_status"] = "pass" if failed == 0 else "fail"

    def collect_complexity_from_script(self, scripts_dir: Path) -> None:
        """Collect complexity metrics via complexity.sh --metrics.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("complexity.sh", scripts_dir)
        if data is not None:
            cc_avg = data.get("cyclomatic_avg")
            mi_avg = data.get("maintainability_avg")

            self.metrics["complexity_avg"] = cc_avg
            self.metrics["complexity_status"] = self._compute_status(
                cc_avg, self.thresholds["complexity"], higher_is_better=False
            )
            self.metrics["maintainability_avg"] = mi_avg
            self.metrics["maintainability_status"] = self._compute_status(
                mi_avg, self.thresholds["maintainability"]
            )
        else:
            self.metrics["complexity_avg"] = None
            self.metrics["complexity_status"] = "unknown"
            self.metrics["maintainability_avg"] = None
            self.metrics["maintainability_status"] = "unknown"

    def generate_json(self, output_file: Path) -> None:
        """Write metrics to JSON file.

        Args:
            output_file: Path where metrics.json will be written
        """
        metrics_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "project": self.project_name,
            "thresholds": self.thresholds,
            "metrics": self.metrics,
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(metrics_data, indent=2))
        print(f"✓ Generated {output_file}")


def _default_thresholds() -> dict[str, int | float]:
    """Return default quality thresholds aligned with SGSG standards.

    This is the single source of truth for pass/fail thresholds
    (Issue #206): every status in metrics.json is computed from these
    values, never from a quality script's own hardcoded threshold.

    Returns:
        Mapping of metric name to its pass/fail threshold.
    """
    return {
        "coverage": 90,
        "branch_coverage": 85,
        "mutation_score": 80,
        "complexity": 10,
        "docs_coverage": 95,
        "security_issues": 0,
        "maintainability": 20,
        "lint_violations": 0,
        "type_errors": 0,
    }


def _collect_script_mode(
    collector: MetricsCollector,
    args: argparse.Namespace,
) -> None:
    """Collect metrics using script mode (--metrics flag on each script).

    Args:
        collector: MetricsCollector instance
        args: Parsed CLI arguments
    """
    scripts_dir = args.scripts_dir

    # Coverage via script
    collector.collect_coverage_metrics(scripts_dir)

    # Complexity + Maintainability via script
    collector.collect_complexity_from_script(scripts_dir)

    # Docs coverage via script (Issue #217), report-file fallback
    collector.collect_docs_metrics(scripts_dir, args.docs_file)

    # Security via script
    collector.collect_security_metrics(scripts_dir)

    # Mutation score: read SQLite cache directly (not mutation.sh --metrics)
    # because running mutmut is expensive; the cache already has results.
    _collect_mutation(collector, args)

    # New metrics only available in script mode
    collector.collect_lint_metrics(scripts_dir)
    collector.collect_typecheck_metrics(scripts_dir)
    collector.collect_test_metrics(scripts_dir)

    # Pre-Commit Status (Issue #154): derived from .pre-commit-config.yaml
    collector.collect_precommit_status(Path(".pre-commit-config.yaml"))

    # CI Status (Issue #159): GitHub API when available, static otherwise
    collector.collect_ci_status(Path(".github/workflows"))


def _collect_file_mode(
    collector: MetricsCollector,
    args: argparse.Namespace,
) -> None:
    """Collect metrics from report files (backward compatible mode).

    Args:
        collector: MetricsCollector instance
        args: Parsed CLI arguments
    """
    try:
        collector.collect_coverage(args.coverage_file)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse coverage ({type(e).__name__}): {e}")

    try:
        collector.collect_complexity(args.complexity_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: Could not parse complexity ({type(e).__name__}): {e}")
        collector.metrics["complexity_avg"] = None
        collector.metrics["complexity_status"] = "unknown"

    try:
        collector.collect_docs_coverage(args.docs_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: Could not parse docs coverage ({type(e).__name__}): {e}")
        collector.metrics["docs_coverage"] = None
        collector.metrics["docs_status"] = "unknown"

    try:
        collector.collect_security(args.security_file)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse security ({type(e).__name__}): {e}")
        collector.metrics["security_issues"] = None
        collector.metrics["security_status"] = "unknown"

    # Pre-Commit Status (Issue #154): derived from .pre-commit-config.yaml
    collector.collect_precommit_status(Path(".pre-commit-config.yaml"))

    # CI Status (Issue #159): GitHub API when available, static otherwise
    collector.collect_ci_status(Path(".github/workflows"))

    _collect_mutation(collector, args)


def _collect_mutation(
    collector: MetricsCollector,
    args: argparse.Namespace,
) -> None:
    """Collect mutation score from explicit arg or cache.

    Args:
        collector: MetricsCollector instance
        args: Parsed CLI arguments
    """
    if args.mutation_score is not None:
        collector.add_mutation_score(args.mutation_score)
    else:
        collector.collect_mutation_from_cache(Path(".mutmut-cache"))


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/metrics.json"),
        help="Output file path (default: docs/metrics.json)",
    )
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path("coverage.json"),
        help="Path to coverage.json (default: coverage.json)",
    )
    parser.add_argument(
        "--complexity-file",
        type=Path,
        default=Path("complexity-report.txt"),
        help="Path to complexity report (default: complexity-report.txt)",
    )
    parser.add_argument(
        "--docs-file",
        type=Path,
        default=Path("docs-report.txt"),
        help="Path to docs coverage report (default: docs-report.txt)",
    )
    parser.add_argument(
        "--security-file",
        type=Path,
        default=Path("security-report.json"),
        help="Path to security report (default: security-report.json)",
    )
    parser.add_argument(
        "--mutation-score",
        type=float,
        default=None,
        help="Mutation score override (omit to read from cache or script)",
    )
    parser.add_argument(
        "--metrics-mode",
        choices=["file", "script"],
        default="file",
        help="Collection mode: 'file' reads report files, "
        "'script' runs scripts with --metrics (default: file)",
    )
    parser.add_argument(
        "--scripts-dir",
        type=Path,
        default=Path("scripts"),
        help="Directory containing quality scripts (default: scripts/)",
    )
    return parser


def main() -> int:
    """Collect metrics and generate metrics.json."""
    args = _build_parser().parse_args()
    thresholds = _default_thresholds()
    collector = MetricsCollector(args.project_name, thresholds)

    if args.metrics_mode == "script":
        _collect_script_mode(collector, args)
    else:
        _collect_file_mode(collector, args)

    collector.generate_json(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
