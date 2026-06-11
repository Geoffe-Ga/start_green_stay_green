"""Typecheck gate — MyPy (cross-platform port of ``scripts/typecheck.sh``)."""

from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse typecheck gate arguments (parity with typecheck.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser("typecheck", "Run type checking using MyPy.")
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout and exit",
    )
    return parser.parse_args(argv)


def _count_errors(output: str) -> int:
    """Count mypy error lines (the script's ``grep -c ": error:"``).

    Args:
        output: Combined mypy stdout+stderr.

    Returns:
        Number of lines containing ``: error:``.
    """
    return sum(1 for line in output.splitlines() if ": error:" in line)


def _metrics(mypy: str) -> int:
    """Emit machine-readable typecheck metrics (typecheck.sh --metrics).

    Args:
        mypy: Absolute path to the mypy executable.

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    result = common.run_tool(
        [mypy, "."],
        stdout=common.PIPE,
        stderr=common.STDOUT,
    )
    errors = _count_errors(result.stdout or "")
    status = "pass" if errors == 0 else "fail"
    print(json.dumps({"errors": errors, "status": status}))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the typecheck gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on type errors, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    mypy = common.resolve_tool("mypy")
    if mypy is None:
        print("Error: mypy is not installed", file=sys.stderr)
        return 2
    if args.metrics:
        return _metrics(mypy)
    return _run_check(mypy, args, start)


def _run_check(mypy: str, args: argparse.Namespace, start: float) -> int:
    """Run mypy and report the outcome.

    Args:
        mypy: Absolute path to the mypy executable.
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.

    Returns:
        0 on success, 1 on type errors.
    """
    print("=== Type Checking (MyPy) ===")
    if args.verbose:
        print("Running MyPy type checker...")
    type_start = time.monotonic()
    result = common.run_tool([mypy, "."])
    if result.returncode != 0:
        print("✗ Type checking failed", file=sys.stderr)
        return 1
    print("✓ Type checks passed")
    if args.verbose:
        print(
            f"Type check execution time: {common.elapsed_seconds(type_start)} seconds"
        )
        print(f"Total execution time: {common.elapsed_seconds(start)} seconds")
    return 0
