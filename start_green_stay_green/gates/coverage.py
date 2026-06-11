"""Coverage gate — pytest-cov reports (port of ``scripts/coverage.sh``)."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse

#: Marker expression for the suites that own the coverage number.
_MARKER = "not integration and not e2e"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse coverage gate arguments (parity with coverage.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser(
        "coverage", "Generate coverage reports using coverage/pytest-cov."
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout",
    )
    return parser.parse_args(argv)


def _coverage_json_metrics(path: Path) -> dict[str, float | None]:
    """Compute line/branch coverage from a ``coverage.json`` payload.

    Args:
        path: Path to the coverage JSON report.

    Returns:
        Metrics dict (status is computed downstream by
        collect_metrics.py, matching the script).
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    totals = data["totals"]
    branches = totals.get("num_branches", 0)
    covered = totals.get("covered_branches", 0)
    branch_cov = round((covered / branches) * 100, 2) if branches > 0 else None
    return {
        "coverage_pct": round(totals["percent_covered"], 2),
        "branch_coverage_pct": branch_cov,
    }


def _metrics(pytest_tool: str) -> int:
    """Emit machine-readable coverage metrics (coverage.sh --metrics).

    Args:
        pytest_tool: Absolute path to the pytest executable.

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    common.run_tool(
        [
            pytest_tool,
            "-m",
            _MARKER,
            "--cov=start_green_stay_green",
            "--cov-branch",
            "--cov-report=json",
            "-q",
            "--tb=no",
            "tests/",
        ],
        stdout=common.DEVNULL,
        stderr=common.DEVNULL,
    )
    report = Path("coverage.json")
    if not report.is_file():
        print(
            '{"coverage_pct": null, "branch_coverage_pct": null, '
            '"status": "unknown"}'
        )
        return 0
    try:
        metrics = _coverage_json_metrics(report)
    except (KeyError, json.JSONDecodeError) as exc:
        # A schema drift or truncated report must read as a clean,
        # diagnosable failure rather than a raw traceback.
        print(f"✗ coverage.json is unreadable: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(metrics))
    return 0


def check_threshold() -> int:
    """Validate the coverage total against the 90% threshold.

    Mirrors coverage.sh: skipped when the ``coverage`` console script is
    unavailable; the TOTAL percentage is parsed from ``coverage report``.
    An unparseable report fails the gate (exit 2) rather than passing
    silently.

    Returns:
        0 when the threshold is met (or the tool is missing), 1 when
        coverage is below threshold, 2 when the report is unparseable.
    """
    coverage_tool = common.resolve_tool("coverage")
    if coverage_tool is None:
        return 0
    result = common.run_tool([coverage_tool, "report"], stdout=common.PIPE)
    percent = _parse_total_percent(result.stdout or "")
    if percent is None:
        print("✗ Could not parse coverage report TOTAL line", file=sys.stderr)
        return 2
    if percent < common.COVERAGE_THRESHOLD:
        print(
            f"✗ Coverage {percent}% is below threshold of "
            f"{common.COVERAGE_THRESHOLD}%",
            file=sys.stderr,
        )
        return 1
    return 0


def _parse_total_percent(report: str) -> float | None:
    """Extract the TOTAL percentage from a ``coverage report`` table.

    Args:
        report: Raw ``coverage report`` stdout.

    Returns:
        Percentage as a float, or None when no TOTAL row parses.
    """
    for line in report.splitlines():
        fields = line.split()
        if fields and fields[0] == "TOTAL":
            try:
                return float(fields[-1].rstrip("%"))
            except ValueError:
                return None
    return None


def main(argv: list[str] | None = None) -> int:
    """Entry point for the coverage gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on coverage failures, 2 on runner errors.
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
    return _generate(pytest_tool, args, start)


def _generate(pytest_tool: str, args: argparse.Namespace, start: float) -> int:
    """Run the coverage suite and validate the threshold.

    Args:
        pytest_tool: Absolute path to the pytest executable.
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.

    Returns:
        Gate exit code.
    """
    print("=== Generating Coverage Report ===")
    coverage_args = ["--cov=start_green_stay_green", "--cov-report=term-missing"]
    if args.html:
        print("Generating HTML coverage report...")
        coverage_args.append("--cov-report=html")
    if args.verbose:
        print("Running pytest with coverage...")
    cov_start = time.monotonic()
    result = common.run_tool([pytest_tool, "-m", _MARKER, *coverage_args, "tests/"])
    if result.returncode != 0:
        print("✗ Coverage generation failed", file=sys.stderr)
        return 1
    cov_time = common.elapsed_seconds(cov_start)
    threshold_rc = check_threshold()
    if threshold_rc != 0:
        return threshold_rc
    return _report(args, start, cov_time)


def _report(args: argparse.Namespace, start: float, cov_time: int) -> int:
    """Print the success output for the coverage gate.

    Args:
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.
        cov_time: Whole seconds spent in the pytest coverage run.

    Returns:
        Always 0.
    """
    if args.verbose:
        print(f"Coverage check completed in {common.elapsed_seconds(start)}s")
    if args.html:
        print("✓ HTML coverage report generated in htmlcov/index.html")
    else:
        print("✓ Coverage report generated")
    if args.verbose:
        print(f"Coverage execution time: {cov_time} seconds")
    return 0
