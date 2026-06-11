#!/usr/bin/env python3
"""Automated v1.0.0 release-readiness verification (#152).

Generates a Python project offline via the public ``sgsg`` CLI into a temporary
directory and asserts the automatable, structural release-readiness criteria
from the v1.0.0 manual testing plan:

* core project structure (precommit config, scripts, README, source, tests),
* generated quality scripts exist and are executable,
* the pre-commit config declares enough hooks,
* a CI workflow is present and is valid YAML,
* the live metrics dashboard flow produces dashboard/metrics/workflow/script
  artifacts.

The script is deterministic and fully offline: no Anthropic API key is required
and no network calls are made. Each check returns a (possibly empty) list of
failure messages; the script reports all failures and exits non-zero if any
check fails, so it can gate a release in CI.

Usage:
    python3 scripts/verify_release_readiness.py [--keep] [--help]

Exit codes:
    0  All automatable release-readiness checks passed.
    1  One or more checks failed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml

from start_green_stay_green.utils.fs import is_windows

# Minimum number of pre-commit hooks a generated Python project must declare.
MIN_PRECOMMIT_HOOKS = 25

# Quality scripts that must be generated and executable.
REQUIRED_SCRIPTS = (
    "check-all.sh",
    "test.sh",
    "lint.sh",
    "format.sh",
    "security.sh",
    "mutation.sh",
    "fix-all.sh",
)

# Critical structural files every generated Python project must contain.
REQUIRED_FILES = (
    ".pre-commit-config.yaml",
    "README.md",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
)

# Dashboard artifacts produced by --enable-live-dashboard.
DASHBOARD_ARTIFACTS = (
    "docs/dashboard.html",
    "docs/metrics.json",
    ".github/workflows/metrics.yml",
    "scripts/collect_metrics.py",
)

# Keys that the generated docs/metrics.json must contain.
REQUIRED_METRICS_KEYS = ("timestamp", "project", "thresholds", "metrics")

PROJECT_NAME = "release-readiness-check"


def _offline_env() -> dict[str, str]:
    """Return an environment with API keys stripped and keyring disabled.

    Returns:
        A copy of ``os.environ`` that prevents real Anthropic API calls.
    """
    env = os.environ.copy()
    for key in ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"):
        env.pop(key, None)
    # Disable keyring lookups so no stored credentials trigger API calls.
    env["PYTHON_KEYRING_BACKEND"] = "keyring.backends.null.Keyring"
    return env


def _run_init(output_dir: Path) -> list[str]:
    """Generate a Python project with the live dashboard enabled, offline.

    Args:
        output_dir: Directory that will contain the generated project.

    Returns:
        A list of failure messages (empty when the CLI succeeds).
    """
    sgsg = shutil.which("sgsg")
    if sgsg is None:
        return ["'sgsg' CLI not found on PATH (install with: pip install -e .)"]

    result = subprocess.run(
        [
            sgsg,
            "init",
            "--project-name",
            PROJECT_NAME,
            "--language",
            "python",
            "--output-dir",
            str(output_dir),
            "--enable-live-dashboard",
            "--no-interactive",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=_offline_env(),
    )
    if result.returncode != 0:
        detail = f"{result.stdout}\n{result.stderr}".strip()
        return [f"'sgsg init' failed (exit {result.returncode}): {detail}"]
    return []


def _check_required_files(project_dir: Path) -> list[str]:
    """Check that critical structural files exist and are non-empty.

    Args:
        project_dir: Root of the generated project.

    Returns:
        A list of failure messages (empty when all files are present).
    """
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        path = project_dir / relative
        if not path.is_file():
            failures.append(f"missing required file: {relative}")
        elif path.stat().st_size == 0:
            failures.append(f"required file is empty: {relative}")
    return failures


def _check_scripts_executable(project_dir: Path) -> list[str]:
    """Check that each required quality script exists and is executable.

    On Windows the POSIX executable bit does not exist (stat() derives
    the exec bits from the file extension, so every .sh script would be
    flagged), so the check degrades to existence-only there (#380).

    Args:
        project_dir: Root of the generated project.

    Returns:
        A list of failure messages (empty when all scripts are runnable).
    """
    failures: list[str] = []
    scripts_dir = project_dir / "scripts"
    for name in REQUIRED_SCRIPTS:
        path = scripts_dir / name
        if not path.is_file():
            failures.append(f"missing quality script: scripts/{name}")
        elif not is_windows() and not path.stat().st_mode & 0o111:
            failures.append(f"quality script not executable: scripts/{name}")
    return failures


def _check_precommit_hooks(project_dir: Path) -> list[str]:
    """Check that the pre-commit config declares at least the minimum hooks.

    A missing config file is not reported here: ``_check_required_files``
    already reports it, so this check returns cleanly instead of crashing
    with ``FileNotFoundError`` (#402).

    Args:
        project_dir: Root of the generated project.

    Returns:
        A list of failure messages (empty when enough hooks are declared).
    """
    config = project_dir / ".pre-commit-config.yaml"
    if not config.is_file():
        return []
    text = config.read_text(encoding="utf-8")
    hook_count = sum(
        1 for line in text.splitlines() if line.strip().startswith("- id:")
    )
    if hook_count < MIN_PRECOMMIT_HOOKS:
        return [
            f"pre-commit config declares {hook_count} hooks, "
            f"expected >= {MIN_PRECOMMIT_HOOKS}"
        ]
    return []


def _check_ci_workflow(project_dir: Path) -> list[str]:
    """Check that at least one CI workflow exists and parses as valid YAML.

    Args:
        project_dir: Root of the generated project.

    Returns:
        A list of failure messages (empty when a valid workflow exists).
    """
    workflows_dir = project_dir / ".github" / "workflows"
    workflows = sorted(workflows_dir.glob("*.yml")) if workflows_dir.is_dir() else []
    if not workflows:
        return ["no CI workflows found under .github/workflows/"]

    failures: list[str] = []
    for workflow in workflows:
        try:
            yaml.safe_load(workflow.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"invalid YAML in {workflow.name}: {exc}")
    return failures


def _check_dashboard(project_dir: Path) -> list[str]:
    """Check that dashboard artifacts exist and metrics.json is well-formed.

    Args:
        project_dir: Root of the generated project.

    Returns:
        A list of failure messages (empty when the dashboard is complete).
    """
    failures: list[str] = []
    for relative in DASHBOARD_ARTIFACTS:
        path = project_dir / relative
        if not path.is_file():
            failures.append(f"missing dashboard artifact: {relative}")
        elif path.stat().st_size == 0:
            failures.append(f"dashboard artifact is empty: {relative}")

    metrics_path = project_dir / "docs" / "metrics.json"
    if not metrics_path.is_file():
        return failures

    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"metrics.json is not valid JSON: {exc}")
        return failures
    failures.extend(
        f"metrics.json missing key: {key}"
        for key in REQUIRED_METRICS_KEYS
        if key not in metrics
    )
    if metrics.get("project") != PROJECT_NAME:
        actual = metrics.get("project")
        failures.append(
            f"metrics.json project mismatch: {actual!r} != {PROJECT_NAME!r}"
        )
    return failures


CHECKS = (
    ("required files present", _check_required_files),
    ("quality scripts executable", _check_scripts_executable),
    ("pre-commit hook count", _check_precommit_hooks),
    ("CI workflow valid", _check_ci_workflow),
    ("live dashboard artifacts", _check_dashboard),
)


def _verify(project_dir: Path) -> int:
    """Run every check against the generated project.

    Args:
        project_dir: Root of the generated project.

    Returns:
        Process exit code: 0 if all checks pass, 1 otherwise.
    """
    total_failures = 0
    for label, check in CHECKS:
        failures = check(project_dir)
        if failures:
            total_failures += len(failures)
            for failure in failures:
                print(f"  FAIL  {label}: {failure}")
        else:
            print(f"  PASS  {label}")
    return 1 if total_failures else 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Automated v1.0.0 release-readiness verification (#152)."
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the generated temp project for inspection.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Generate a project and run all release-readiness checks.

    Args:
        argv: Optional argument vector (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code: 0 on success, 1 on any failure.
    """
    args = _parse_args(argv)

    print("Release-readiness verification (#152)")
    tmpdir = Path(tempfile.mkdtemp(prefix="sgsg-release-"))
    try:
        print(f"Generating project in {tmpdir} ...")
        init_failures = _run_init(tmpdir)
        if init_failures:
            for failure in init_failures:
                print(f"  FAIL  generate project: {failure}")
            return 1

        project_dir = tmpdir / PROJECT_NAME
        if not project_dir.is_dir():
            print(f"  FAIL  project directory not created: {project_dir}")
            return 1
        exit_code = _verify(project_dir)
    finally:
        if args.keep:
            print(f"Kept generated project at {tmpdir}")
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)

    if exit_code == 0:
        print("All automatable release-readiness checks PASSED.")
    else:
        print("Release-readiness verification FAILED.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
