"""Test gate — Pytest (cross-platform port of ``scripts/test.sh``)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common
from start_green_stay_green.gates import mutation

if TYPE_CHECKING:
    import argparse

#: Pytest ``-m`` marker expression per (test type, ci mode). ``None``
#: means no marker filter (the ``--all`` non-CI case).
MARKER_EXPRESSIONS: dict[tuple[str, bool], str | None] = {
    ("unit", False): "not integration and not e2e",
    ("unit", True): "not integration and not e2e and not flaky_in_ci",
    ("integration", False): "integration",
    ("integration", True): "integration and not flaky_in_ci",
    ("e2e", False): "e2e",
    ("e2e", True): "e2e and not flaky_in_ci",
    ("all", False): None,
    ("all", True): "not flaky_in_ci",
}

_HEADERS = {
    "unit": "=== Running Unit Tests ===",
    "integration": "=== Running Integration Tests ===",
    "e2e": "=== Running End-to-End Tests ===",
    "all": "=== Running All Tests ===",
}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse test gate arguments (parity with test.sh's option surface).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser("test", "Run tests using Pytest.")
    for test_type in ("unit", "integration", "e2e", "all"):
        parser.add_argument(
            f"--{test_type}",
            dest="test_type",
            action="store_const",
            const=test_type,
            default="unit",
            help=f"Run {test_type} tests",
        )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    parser.add_argument(
        "--mutation",
        action="store_true",
        help="Run mutation tests",
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: skip flaky_in_ci tests",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout",
    )
    return parser.parse_args(argv)


def parse_pytest_summary(text: str) -> dict[str, float | int | str]:
    """Parse a ``pytest -q`` summary into metrics (test.sh --metrics).

    Distinguishes zero collected tests (broken suite, status "unknown")
    from zero failures, exactly like the script's inline parser.

    Args:
        text: Combined pytest output.

    Returns:
        Metrics dict with test counts, duration, and status.
    """
    passed = _summary_count(r"(\d+) passed", text)
    failed = _summary_count(r"(\d+) failed", text)
    skipped = _summary_count(r"(\d+) skipped", text)
    if _is_unknown_summary(passed, failed, skipped):
        return {
            "tests_total": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 0.0,
            "status": "unknown",
        }
    return _known_summary(passed or 0, failed or 0, skipped or 0, text)


def _is_unknown_summary(
    passed: int | None, failed: int | None, skipped: int | None
) -> bool:
    """Detect a broken suite (no pass/fail counts and nothing collected).

    Mirrors the script's ``total == 0 and not passed_m and not failed_m``.

    Args:
        passed: Parsed passed count (None when absent).
        failed: Parsed failed count (None when absent).
        skipped: Parsed skipped count (None when absent).

    Returns:
        True when the summary carries no test information.
    """
    return passed is None is failed and not skipped


def _summary_count(pattern: str, text: str) -> int | None:
    """Extract one integer count from the pytest summary line.

    Args:
        pattern: Regex with a single integer capture group.
        text: Combined pytest output.

    Returns:
        The captured count, or None when the pattern is absent.
    """
    match = re.search(pattern, text)
    if match is None:
        return None
    return int(match.group(1))


def _known_summary(
    passed: int, failed: int, skipped: int, text: str
) -> dict[str, float | int | str]:
    """Build the metrics dict for a summary with collected tests.

    Args:
        passed: Count of passed tests.
        failed: Count of failed tests.
        skipped: Count of skipped tests.
        text: Combined pytest output (for the duration).

    Returns:
        Metrics dict with pass/fail status.
    """
    duration_m = re.search(r"in ([0-9.]+)s", text)
    return {
        "tests_total": passed + failed + skipped,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_skipped": skipped,
        "duration_seconds": float(duration_m.group(1)) if duration_m else 0.0,
        "status": "fail" if failed > 0 else "pass",
    }


def _metrics(pytest_tool: str) -> int:
    """Emit machine-readable test metrics (test.sh --metrics).

    Args:
        pytest_tool: Absolute path to the pytest executable.

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    result = common.run_tool(
        [
            pytest_tool,
            "-m",
            "not integration and not e2e",
            "-q",
            "--tb=no",
            "--color=no",
            "-o",
            "addopts=",
            "tests/",
        ],
        stdout=common.PIPE,
        stderr=common.STDOUT,
    )
    print(json.dumps(parse_pytest_summary(result.stdout or "")))
    return 0


def build_pytest_args(args: argparse.Namespace, report_file: str | None) -> list[str]:
    """Build the pytest argument list (marker, coverage, JSON report).

    Args:
        args: Parsed gate arguments.
        report_file: Path for ``--json-report-file`` when JSON output is
            requested, else None.

    Returns:
        Pytest arguments matching test.sh's ``PYTEST_ARGS`` construction.
    """
    pytest_args = ["-v"]
    marker = MARKER_EXPRESSIONS[(args.test_type, args.ci)]
    if marker is not None:
        pytest_args.extend(["-m", marker])
    if args.coverage:
        pytest_args.extend(
            [
                "--cov=start_green_stay_green",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-report=xml",
                f"--cov-fail-under={common.COVERAGE_THRESHOLD}",
            ]
        )
    if report_file is not None:
        pytest_args.extend(["--json-report", f"--json-report-file={report_file}"])
    return pytest_args


def _announce(args: argparse.Namespace, pytest_args: list[str]) -> None:
    """Print the run headers (suppressed in JSON mode, like the script).

    Args:
        args: Parsed gate arguments.
        pytest_args: Final pytest argument list (echoed under --verbose).
    """
    if args.json_output:
        return
    print(_HEADERS[args.test_type])
    if args.ci:
        print("CI mode: Skipping flaky_in_ci tests")
    if args.coverage:
        print("Coverage enabled")
    if args.verbose:
        print(f"Running pytest with args: {' '.join(pytest_args)}")


def _report_failure(
    args: argparse.Namespace, stderr: str, durations: tuple[int, int]
) -> int:
    """Report a pytest failure, surfacing captured stderr.

    Args:
        args: Parsed gate arguments.
        stderr: Captured pytest stderr.
        durations: (total seconds, test-run seconds).

    Returns:
        Always 1.
    """
    total_time, test_time = durations
    if args.json_output:
        print(
            json.dumps(
                {
                    "status": "fail",
                    "duration_seconds": total_time,
                    "test_duration": test_time,
                }
            )
        )
        return 1
    print("✗ Tests failed", file=sys.stderr)
    print("=== Pytest stderr output ===", file=sys.stderr)
    print(stderr, file=sys.stderr, end="")
    return 1


def _report_success(args: argparse.Namespace, durations: tuple[int, int]) -> None:
    """Report a pytest success.

    Args:
        args: Parsed gate arguments.
        durations: (total seconds, test-run seconds).
    """
    total_time, test_time = durations
    if args.json_output:
        print(
            json.dumps(
                {
                    "status": "pass",
                    "duration_seconds": total_time,
                    "test_duration": test_time,
                }
            )
        )
        return
    print("✓ Tests passed")
    if args.verbose:
        print(f"Test execution time: {test_time} seconds")


def _run_mutation_chain(args: argparse.Namespace) -> int:
    """Chain into the mutation gate when ``--mutation`` was requested.

    Args:
        args: Parsed gate arguments.

    Returns:
        0 when mutation testing passed (or was not requested), 1 on
        mutation failure.
    """
    if not args.mutation:
        return 0
    if not args.json_output:
        print("=== Running Mutation Tests ===")
    if mutation.main([]) != 0:
        if not args.json_output:
            print("✗ Mutation tests failed", file=sys.stderr)
        return 1
    return 0


def _run_suite(pytest_tool: str, args: argparse.Namespace, start: float) -> int:
    """Run the selected pytest suite and report the outcome.

    Args:
        pytest_tool: Absolute path to the pytest executable.
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.

    Returns:
        Gate exit code.
    """
    report_file = _make_report_file() if args.json_output else None
    pytest_args = build_pytest_args(args, report_file)
    _announce(args, pytest_args)
    test_start = time.monotonic()
    result = _run_pytest(pytest_tool, pytest_args, report_file)
    durations = (common.elapsed_seconds(start), common.elapsed_seconds(test_start))
    if result.returncode != 0:
        return _report_failure(args, result.stderr or "", durations)
    _report_success(args, durations)
    return _run_mutation_chain(args)


def _run_pytest(
    pytest_tool: str, pytest_args: list[str], report_file: str | None
) -> common.ToolResult:
    """Run pytest, cleaning up the throwaway JSON report afterwards.

    Args:
        pytest_tool: Absolute path to the pytest executable.
        pytest_args: Pytest argument list.
        report_file: Throwaway JSON report path, or None.

    Returns:
        Completed pytest process (stderr captured).
    """
    try:
        return common.run_tool([pytest_tool, *pytest_args, "tests/"])
    finally:
        if report_file is not None:
            Path(report_file).unlink(missing_ok=True)


def _make_report_file() -> str:
    """Create the throwaway path for pytest's JSON report.

    The script wrote the report to a mktemp file it never read; the
    runner preserves that behavior and deletes the file afterwards.

    Returns:
        Path to a fresh temporary file.
    """
    descriptor, name = tempfile.mkstemp(prefix="pytest-report-", suffix=".json")
    os.close(descriptor)
    return name


def main(argv: list[str] | None = None) -> int:
    """Entry point for the test gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on test failures, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    pytest_tool = common.resolve_tool("pytest")
    if pytest_tool is None:
        print("Error: pytest is not installed", file=sys.stderr)
        return 2
    if args.metrics:
        return _metrics(pytest_tool)
    return _run_suite(pytest_tool, args, start)
