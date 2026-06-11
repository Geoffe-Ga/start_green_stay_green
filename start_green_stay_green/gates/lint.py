"""Lint gate — Ruff checks (cross-platform port of ``scripts/lint.sh``)."""

from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse lint gate arguments (parity with lint.sh's option surface).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser("lint", "Run linting checks using Ruff.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix linting issues where possible",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, fail if issues found (default mode)",
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


def _count_violations(payload: str) -> int:
    """Count violations in ruff's JSON output.

    Mirrors lint.sh --metrics, which defaults to 0 when the output
    cannot be parsed.

    Args:
        payload: Raw ``ruff check --output-format=json`` stdout.

    Returns:
        Number of reported violations (0 when unparseable).
    """
    try:
        return len(json.loads(payload))
    except (json.JSONDecodeError, TypeError):
        return 0


def _metrics(ruff: str) -> int:
    """Emit machine-readable lint metrics (lint.sh --metrics).

    Args:
        ruff: Absolute path to the ruff executable.

    Returns:
        Always 0, matching the script's unconditional ``exit 0``.
    """
    result = common.run_tool(
        [ruff, "check", ".", "--output-format=json"],
        stdout=common.PIPE,
        stderr=common.DEVNULL,
    )
    violations = _count_violations(result.stdout or "")
    status = "pass" if violations == 0 else "fail"
    print(json.dumps({"violations": violations, "status": status}))
    return 0


def _report(
    returncode: int,
    *,
    json_output: bool,
    verbose: bool,
    total_time: int,
    lint_time: int,
) -> int:
    """Print the gate outcome and translate it to an exit code.

    Args:
        returncode: Exit code from ruff.
        json_output: Whether to emit the JSON result envelope.
        verbose: Whether to print timing details.
        total_time: Whole seconds since gate start.
        lint_time: Whole seconds spent in ruff.

    Returns:
        0 when ruff passed, 1 otherwise.
    """
    passed = returncode == 0
    if json_output:
        return _report_json(passed=passed, total_time=total_time, lint_time=lint_time)
    if passed:
        print("✓ Linting checks passed")
        if verbose:
            print(f"Lint execution time: {lint_time} seconds")
        return 0
    print("✗ Linting checks failed", file=sys.stderr)
    return 1


def _report_json(*, passed: bool, total_time: int, lint_time: int) -> int:
    """Emit the JSON result envelope (lint.sh --json parity).

    Args:
        passed: Whether ruff exited cleanly.
        total_time: Whole seconds since gate start.
        lint_time: Whole seconds spent in ruff.

    Returns:
        0 when ruff passed, 1 otherwise.
    """
    print(
        json.dumps(
            {
                "status": "pass" if passed else "fail",
                "duration_seconds": total_time,
                "lint_duration": lint_time,
            }
        )
    )
    return 0 if passed else 1


def _check(ruff: str, args: argparse.Namespace, start: float) -> int:
    """Run ruff in check or fix mode and report the result.

    Args:
        ruff: Absolute path to the ruff executable.
        args: Parsed gate arguments.
        start: Monotonic timestamp of gate start.

    Returns:
        Gate exit code.
    """
    if not args.json_output:
        print("=== Linting (Ruff) ===")
        if args.verbose:
            message = (
                "Fixing linting issues..."
                if args.fix
                else "Checking for linting issues..."
            )
            print(message)
    lint_start = time.monotonic()
    cmd = [ruff, "check", "."]
    if args.fix:
        cmd.append("--fix")
    result = common.run_tool(cmd)
    lint_time = common.elapsed_seconds(lint_start)
    return _report(
        result.returncode,
        json_output=args.json_output,
        verbose=args.verbose,
        total_time=common.elapsed_seconds(start),
        lint_time=lint_time,
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for the lint gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on lint failures, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    ruff = common.resolve_tool("ruff")
    if ruff is None:
        print("Error: ruff is not installed", file=sys.stderr)
        return 2
    if args.metrics:
        return _metrics(ruff)
    return _check(ruff, args, start)
