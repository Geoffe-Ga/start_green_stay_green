"""Complexity gate — Radon + Xenon (port of ``scripts/complexity.sh``).

Enforces the MAXIMUM QUALITY thresholds: cyclomatic complexity ≤ 10 per
function, maintainability index ≥ 20, and xenon grade A across absolute,
module, and average metrics.
"""

from __future__ import annotations

import re
import sys
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse

#: Package directory analyzed by every radon/xenon invocation.
TARGET = "start_green_stay_green/"

#: Lines whose grade letter is C-F breach the radon thresholds.
_GRADE_LINE = re.compile(r"^\s*[C-F] ")

#: Average cyclomatic complexity in ``radon cc -a`` output.
_CC_AVERAGE = re.compile(r"Average complexity: [A-Z] \(([0-9.]+)\)")

#: Per-module maintainability score in ``radon mi -s`` output.
_MI_SCORE = re.compile(r"- [A-F] \(([0-9.]+)\)")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse complexity gate arguments (parity with complexity.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser(
        "complexity",
        "Analyze code complexity and enforce MAXIMUM QUALITY thresholds.",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout and exit",
    )
    return parser.parse_args(argv)


def _radon_output(radon: str, *args: str) -> str:
    """Run radon capturing combined output (the script's ``2>&1``).

    Args:
        radon: Absolute path to the radon executable.
        *args: Radon subcommand and flags.

    Returns:
        Combined stdout+stderr text.
    """
    result = common.run_tool(
        [radon, *args, TARGET],
        stdout=common.PIPE,
        stderr=common.STDOUT,
    )
    return result.stdout or ""


def _average_maintainability(output: str) -> str | None:
    """Average the per-module maintainability scores.

    Args:
        output: ``radon mi -s`` output.

    Returns:
        Two-decimal average as a string, or None when no scores parse.
    """
    scores = [float(match.group(1)) for match in _MI_SCORE.finditer(output)]
    if not scores:
        return None
    return f"{sum(scores) / len(scores):.2f}"


def _metrics(radon: str) -> int:
    """Emit machine-readable complexity metrics (complexity.sh --metrics).

    Args:
        radon: Absolute path to the radon executable.

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    cc_match = _CC_AVERAGE.search(_radon_output(radon, "cc", "-s", "-a", "-n", "A"))
    cc_avg = cc_match.group(1) if cc_match else None
    mi_avg = _average_maintainability(_radon_output(radon, "mi", "-s"))
    print(
        f'{{"cyclomatic_avg": {cc_avg or "null"}, '
        f'"maintainability_avg": {mi_avg or "null"}}}'
    )
    return 0


def _grade_failures(output: str) -> list[str]:
    """Collect lines whose grade letter breaches the threshold.

    Args:
        output: Radon report text.

    Returns:
        Lines graded C through F.
    """
    return [line for line in output.splitlines() if _GRADE_LINE.match(line)]


def _check_cyclomatic(radon: str, *, verbose: bool) -> bool:
    """Check cyclomatic complexity against the MAXIMUM QUALITY ceiling.

    Args:
        radon: Absolute path to the radon executable.
        verbose: Whether to print the full radon report.

    Returns:
        True when every function is at or below the ceiling.
    """
    limit = common.MAX_CYCLOMATIC_COMPLEXITY
    print(f"Checking Cyclomatic Complexity (max {limit})...")
    output = _radon_output(radon, "cc", "-s", "-a")
    if verbose:
        print(output)
    failures = _grade_failures(output)
    if failures:
        print(
            f"✗ Cyclomatic Complexity exceeds threshold (max {limit})\n",
            file=sys.stderr,
        )
        print("Functions exceeding threshold:", file=sys.stderr)
        print("\n".join(failures) + "\n", file=sys.stderr)
        return False
    print(f"✓ Cyclomatic Complexity: All functions ≤ {limit}")
    return True


def _check_maintainability(radon: str, *, verbose: bool) -> bool:
    """Check the maintainability index against the MAXIMUM QUALITY floor.

    Args:
        radon: Absolute path to the radon executable.
        verbose: Whether to print the full radon report.

    Returns:
        True when every module is at or above the floor.
    """
    floor = common.MIN_MAINTAINABILITY_INDEX
    print(f"Checking Maintainability Index (min {floor})...")
    output = _radon_output(radon, "mi", "-s")
    if verbose:
        print(output)
    failures = _grade_failures(output)
    if failures:
        print(
            f"✗ Maintainability Index below threshold (min {floor})\n",
            file=sys.stderr,
        )
        print("Modules below threshold:", file=sys.stderr)
        print("\n".join(failures) + "\n", file=sys.stderr)
        return False
    print(f"✓ Maintainability Index: All modules ≥ {floor}")
    return True


def _check_xenon(xenon: str | None) -> bool | None:
    """Enforce xenon grade A across absolute, module, and average metrics.

    Args:
        xenon: Absolute path to the xenon executable, or None when it is
            not installed (the check is skipped, matching the script).

    Returns:
        True/False for pass/fail, or None when xenon is unavailable.
    """
    if xenon is None:
        print("\u2139 Xenon not available (skipping strict grade enforcement)")
        return None
    grade = common.MAX_COMPLEXITY_GRADE
    print(f"Checking overall complexity grade (max grade {grade})...")
    result = common.run_tool(
        [
            xenon,
            "--max-absolute",
            grade,
            "--max-modules",
            grade,
            "--max-average",
            grade,
            TARGET,
        ],
        stderr=common.STDOUT,
    )
    if result.returncode == 0:
        print(f"✓ Xenon: All complexity metrics grade {grade}")
        return True
    print(
        f"✗ Xenon complexity checks failed (grade must be {grade})\n", file=sys.stderr
    )
    print("Run with --verbose to see details, or run directly:", file=sys.stderr)
    print(f"  xenon --max-absolute {grade} {TARGET}", file=sys.stderr)
    return False


def _print_summary(
    passed: list[str], failed: list[str], *, verbose: bool, total_time: int
) -> int:
    """Print the analysis summary and translate it to an exit code.

    Args:
        passed: Names of passed checks.
        failed: Names of failed checks.
        verbose: Whether to print timing details.
        total_time: Whole seconds since gate start.

    Returns:
        0 when every check passed, 1 otherwise.
    """
    print("\n=== Complexity Analysis Summary ===")
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    if verbose:
        print(f"Execution time: {total_time} seconds")
    if not failed:
        print("\n✓ All complexity checks passed (MAXIMUM QUALITY)")
        return 0
    print("\nFailed checks:")
    for check in failed:
        print(f"  ✗ {check}")
    print("\nMAXIMUM QUALITY STANDARDS:")
    print(f"  - Cyclomatic Complexity: ≤ {common.MAX_CYCLOMATIC_COMPLEXITY}")
    print(f"  - Maintainability Index: ≥ {common.MIN_MAINTAINABILITY_INDEX}")
    print(f"  - Complexity Grade: {common.MAX_COMPLEXITY_GRADE}")
    print("\nTo fix:")
    print("  1. Refactor complex functions")
    print("  2. Extract helper methods")
    print("  3. Simplify branching logic")
    print("  4. Break large functions into smaller ones\n")
    return 1


def _record(
    name: str, passed: list[str], failed: list[str], *, result: bool | None
) -> None:
    """File a check outcome into the pass/fail lists.

    Args:
        name: Display name of the check.
        passed: Accumulator for passed checks.
        failed: Accumulator for failed checks.
        result: Check outcome (None means skipped).
    """
    if result is True:
        passed.append(name)
    elif result is False:
        failed.append(name)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the complexity gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on threshold breaches, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    radon = common.resolve_tool("radon")
    if radon is None:
        print("Error: radon not installed", file=sys.stderr)
        print("Install with: pip install radon", file=sys.stderr)
        return 2
    if args.metrics:
        return _metrics(radon)
    print("=== Code Complexity Analysis (MAXIMUM QUALITY) ===\n")
    xenon = common.resolve_tool("xenon")
    if xenon is None:
        print(
            "Warning: xenon not installed (recommended for strict enforcement)",
            file=sys.stderr,
        )
        print("Install with: pip install xenon", file=sys.stderr)
    passed: list[str] = []
    failed: list[str] = []
    _record(
        "Cyclomatic Complexity",
        passed,
        failed,
        result=_check_cyclomatic(radon, verbose=args.verbose),
    )
    print()
    _record(
        "Maintainability Index",
        passed,
        failed,
        result=_check_maintainability(radon, verbose=args.verbose),
    )
    print()
    _record("Xenon Complexity", passed, failed, result=_check_xenon(xenon))
    return _print_summary(
        passed, failed, verbose=args.verbose, total_time=common.elapsed_seconds(start)
    )
