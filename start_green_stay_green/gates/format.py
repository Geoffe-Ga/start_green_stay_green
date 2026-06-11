"""Format gate — Black + isort (cross-platform port of ``scripts/format.sh``)."""

from __future__ import annotations

import json
import sys
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse format gate arguments (parity with format.sh's options).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser("format", "Format code using Black and isort.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply formatting changes",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check only, fail if changes needed (default mode)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results in JSON format",
    )
    return parser.parse_args(argv)


def _run_formatters(
    tools: dict[str, str],
    args: argparse.Namespace,
    *,
    check_mode: bool,
) -> int:
    """Run isort then Black, stopping at the first failure.

    Stderr from the tools is captured and discarded, exactly like the
    script's ``2>"$TMP_STDERR"`` redirection.

    Args:
        tools: Mapping of display name to executable path, in run order.
        args: Parsed gate arguments.
        check_mode: Whether to pass ``--check`` to the formatters.

    Returns:
        0 when both formatters succeed, 1 on the first failure.
    """
    mode = ["--check"] if check_mode else []
    for name, tool in tools.items():
        if not _run_one_formatter(name, tool, mode, args):
            return 1
    return 0


def _run_one_formatter(
    name: str, tool: str, mode: list[str], args: argparse.Namespace
) -> bool:
    """Run a single formatter, reporting failure like the script.

    Args:
        name: Display name (``isort`` / ``Black``).
        tool: Absolute path to the formatter executable.
        mode: ``["--check"]`` in check mode, empty in fix mode.
        args: Parsed gate arguments.

    Returns:
        True when the formatter exited cleanly.
    """
    if args.verbose and not args.json_output:
        print(f"Running {name}...")
    result = common.run_tool([tool, *mode, "."])
    if result.returncode != 0:
        if not args.json_output:
            print(f"✗ {name} failed", file=sys.stderr)
        return False
    return True


def _report_success(
    args: argparse.Namespace,
    *,
    check_mode: bool,
    total_time: int,
    format_time: int,
) -> int:
    """Print the success outcome for the format gate.

    Args:
        args: Parsed gate arguments.
        check_mode: Whether the gate ran in check-only mode.
        total_time: Whole seconds since gate start.
        format_time: Whole seconds spent in the formatters.

    Returns:
        Always 0.
    """
    if args.json_output:
        print(
            json.dumps(
                {
                    "status": "pass",
                    "duration_seconds": total_time,
                    "format_duration": format_time,
                }
            )
        )
        return 0
    if check_mode:
        print("✓ Code formatting check passed")
    else:
        print("✓ Code formatted successfully")
    if args.verbose:
        print(f"Format execution time: {format_time} seconds")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the format gate.

    Check mode is the default (CI parity); ``--fix`` overrides it,
    matching format.sh's mode-resolution logic.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 on success, 1 on formatting failures, 2 on runner errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    isort = common.resolve_tool("isort")
    black = common.resolve_tool("black")
    if isort is None or black is None:
        print("Error: isort/black are not installed", file=sys.stderr)
        return 2
    if not args.json_output:
        print("=== Formatting (Black + isort) ===")
    check_mode = not args.fix
    format_start = time.monotonic()
    failure = _run_formatters(
        {"isort": isort, "Black": black}, args, check_mode=check_mode
    )
    if failure:
        return failure
    return _report_success(
        args,
        check_mode=check_mode,
        total_time=common.elapsed_seconds(start),
        format_time=common.elapsed_seconds(format_start),
    )
