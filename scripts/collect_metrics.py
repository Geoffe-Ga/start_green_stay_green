#!/usr/bin/env python3
"""Collect quality metrics from test reports and generate metrics.json.

This script aggregates metrics from:
- pytest coverage reports (coverage.json)
- radon complexity analysis (complexity-report.txt)
- interrogate documentation coverage (docs-report.txt)
- bandit security scanning (security-report.json)
- quality scripts via --metrics flag (script mode)

Output: metrics.json in the specified output directory
"""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


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
        self.metrics["coverage_status"] = (
            "pass" if total_cov >= self.thresholds["coverage"] else "fail"
        )

        # Branch coverage
        num_branches = cov_data["totals"].get("num_branches", 0)
        covered_branches = cov_data["totals"].get("covered_branches", 0)
        if num_branches > 0:
            branch_cov = (covered_branches / num_branches) * 100
            self.metrics["branch_coverage"] = round(branch_cov, 2)
            self.metrics["branch_coverage_status"] = (
                "pass" if branch_cov >= self.thresholds["branch_coverage"] else "fail"
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
        self.metrics["complexity_status"] = (
            "pass" if comp <= self.thresholds["complexity"] else "fail"
        )

    def collect_docs_coverage(self, docs_file: Path) -> None:
        """Parse documentation coverage from interrogate report.

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
        self.metrics["docs_status"] = (
            "pass" if docs >= self.thresholds["docs_coverage"] else "fail"
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
        self.metrics["security_status"] = (
            "pass" if issues == self.thresholds["security_issues"] else "fail"
        )

    def add_mutation_score(self, score: float) -> None:
        """Add mutation testing score.

        Args:
            score: Mutation score (0-100)
        """
        self.metrics["mutation_score"] = score
        self.metrics["mutation_status"] = (
            "pass" if score >= self.thresholds["mutation_score"] else "fail"
        )

    def _set_mutation_unknown(self) -> None:
        """Set mutation metrics to unknown/null state."""
        self.metrics["mutation_score"] = None
        self.metrics["mutation_status"] = "unknown"

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
            conn.close()
            self._set_mutation_unknown()
        else:
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
            self.metrics["mutation_status"] = (
                "pass" if score >= self.thresholds["mutation_score"] else "fail"
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

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("lint.sh", scripts_dir)
        if data is not None:
            self.metrics["lint_violations"] = data.get("violations", 0)
            self.metrics["lint_status"] = data.get("status", "unknown")
        else:
            self.metrics["lint_violations"] = None
            self.metrics["lint_status"] = "unknown"

    def collect_typecheck_metrics(self, scripts_dir: Path) -> None:
        """Collect type checking metrics via typecheck.sh --metrics.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("typecheck.sh", scripts_dir)
        if data is not None:
            self.metrics["type_errors"] = data.get("errors", 0)
            self.metrics["typecheck_status"] = data.get("status", "unknown")
        else:
            self.metrics["type_errors"] = None
            self.metrics["typecheck_status"] = "unknown"

    def collect_test_metrics(self, scripts_dir: Path) -> None:
        """Collect test count metrics via test.sh --metrics.

        Args:
            scripts_dir: Directory containing quality scripts
        """
        data = self.collect_from_script("test.sh", scripts_dir)
        if data is not None:
            self.metrics["tests_total"] = data.get("tests_total", 0)
            self.metrics["tests_passed"] = data.get("tests_passed", 0)
            self.metrics["tests_failed"] = data.get("tests_failed", 0)
            self.metrics["tests_skipped"] = data.get("tests_skipped", 0)
            self.metrics["tests_status"] = (
                "pass" if data.get("tests_failed", 0) == 0 else "fail"
            )
        else:
            self.metrics["tests_total"] = None
            self.metrics["tests_status"] = "unknown"

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
            self.metrics["complexity_status"] = (
                "pass"
                if cc_avg is not None and cc_avg <= self.thresholds["complexity"]
                else ("fail" if cc_avg is not None else "unknown")
            )
            self.metrics["maintainability_avg"] = mi_avg
            self.metrics["maintainability_status"] = (
                "pass"
                if mi_avg is not None
                and mi_avg >= self.thresholds.get("maintainability", 20)
                else ("fail" if mi_avg is not None else "unknown")
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
        print(json.dumps(metrics_data, indent=2))


def _default_thresholds() -> dict[str, int | float]:
    """Return default quality thresholds aligned with SGSG standards."""
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
        "tests_total": 0,
    }


def _collect_script_mode(
    collector: MetricsCollector,
    args: argparse.Namespace,
    thresholds: dict[str, int | float],
) -> None:
    """Collect metrics using script mode (--metrics flag on each script).

    Args:
        collector: MetricsCollector instance
        args: Parsed CLI arguments
        thresholds: Quality thresholds
    """
    scripts_dir = args.scripts_dir

    # Coverage via script
    cov_data = collector.collect_from_script("coverage.sh", scripts_dir)
    if cov_data is not None:
        cov_pct = cov_data.get("coverage_pct")
        if cov_pct is not None:
            collector.metrics["coverage"] = cov_pct
            collector.metrics["coverage_status"] = (
                "pass" if cov_pct >= thresholds["coverage"] else "fail"
            )
        branch_pct = cov_data.get("branch_coverage_pct")
        if branch_pct is not None:
            collector.metrics["branch_coverage"] = branch_pct
            collector.metrics["branch_coverage_status"] = (
                "pass" if branch_pct >= thresholds["branch_coverage"] else "fail"
            )

    # Complexity + Maintainability via script
    collector.collect_complexity_from_script(scripts_dir)

    # Docs coverage via file (interrogate doesn't have a script yet)
    try:
        collector.collect_docs_coverage(args.docs_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: Could not parse docs coverage ({type(e).__name__}): {e}")
        collector.metrics["docs_coverage"] = None
        collector.metrics["docs_status"] = "unknown"

    # Security via script
    sec_data = collector.collect_from_script("security.sh", scripts_dir)
    if sec_data is not None:
        collector.metrics["security_issues"] = sec_data.get("bandit_issues", 0)
        collector.metrics["security_status"] = sec_data.get("status", "unknown")
    else:
        collector.metrics["security_issues"] = None
        collector.metrics["security_status"] = "unknown"

    # Mutation score: read SQLite cache directly (not mutation.sh --metrics)
    # because running mutmut is expensive; the cache already has results.
    _collect_mutation(collector, args)

    # New metrics only available in script mode
    collector.collect_lint_metrics(scripts_dir)
    collector.collect_typecheck_metrics(scripts_dir)
    collector.collect_test_metrics(scripts_dir)


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
        _collect_script_mode(collector, args, thresholds)
    else:
        _collect_file_mode(collector, args)

    collector.generate_json(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
