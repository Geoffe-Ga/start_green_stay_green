"""Check-all gate — orchestrates every check (port of ``scripts/check-all.sh``).

Child gates run as ``python -m start_green_stay_green.gates <gate>``
subprocesses so sequential output streams through unchanged and parallel
mode gets real process-level concurrency, exactly like the script's
backgrounded jobs. Parallel logs are written to a temp directory and
discarded (script parity), only pass/fail is reported.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from dataclasses import field
import json
from pathlib import Path
import subprocess  # nosec B404 — child gates are this package, run via sys.executable
import sys
import tempfile
import time
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse

#: Independent checks (run in parallel under ``--parallel``).
PARALLEL_CHECKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Linting", "lint", ("--check",)),
    ("Formatting", "format", ("--check",)),
    ("Type checking", "typecheck", ()),
    ("Security checks", "security", ()),
    ("Complexity analysis", "complexity", ()),
)

#: Checks that always run sequentially after the independent ones.
FINAL_CHECKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Unit tests", "test", ("--unit",)),
    ("Coverage report", "coverage", ()),
)


@dataclass
class _Session:
    """Mutable run state shared by the sequential and parallel paths."""

    json_output: bool
    verbose: bool
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def record(self, name: str, *, ok: bool) -> None:
        """File a check outcome and print the per-check verdict.

        Args:
            name: Display name of the check.
            ok: Whether the check passed.
        """
        if ok:
            self.passed.append(name)
            if not self.json_output:
                print(f"✓ {name} passed")
        else:
            self.failed.append(name)
            if not self.json_output:
                print(f"✗ {name} failed", file=sys.stderr)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse check-all gate arguments (parity with check-all.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser("check-all", "Run all quality checks in sequence.")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results in JSON format",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run independent checks in parallel",
    )
    return parser.parse_args(argv)


def gate_command(gate: str, args: tuple[str, ...], *, verbose: bool) -> list[str]:
    """Build the subprocess command for a child gate.

    Args:
        gate: Gate name as accepted by the dispatcher.
        args: Gate-specific arguments.
        verbose: Whether to forward ``--verbose`` (the script's
            ``VERBOSE_FLAG`` propagation).

    Returns:
        Full argument vector starting with the running interpreter.
    """
    cmd = [sys.executable, "-m", "start_green_stay_green.gates", gate, *args]
    if verbose:
        cmd.append("--verbose")
    return cmd


def _run_sequential(
    session: _Session,
    checks: tuple[tuple[str, str, tuple[str, ...]], ...],
) -> None:
    """Run checks one at a time, streaming their output through.

    Args:
        session: Run state accumulator.
        checks: (display name, gate, args) triples to run in order.
    """
    for name, gate, args in checks:
        if not session.json_output:
            print(f"Running: {name}")
        common.flush_streams()
        result = subprocess.run(  # nosec B603 — argv list invoking this package via sys.executable
            gate_command(gate, args, verbose=session.verbose),
            check=False,
        )
        session.record(name, ok=result.returncode == 0)
        if not session.json_output:
            print()


def _run_parallel(session: _Session) -> None:
    """Run the independent checks concurrently, discarding their logs.

    Args:
        session: Run state accumulator.
    """
    if not session.json_output:
        print("Running checks in parallel mode...\n")
    with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
        procs: list[tuple[str, subprocess.Popen[bytes]]] = []
        for name, gate, args in PARALLEL_CHECKS:
            log = stack.enter_context(
                (Path(tmp) / f"{gate}.log").open("w", encoding="utf-8")
            )
            proc = stack.enter_context(
                subprocess.Popen(  # nosec B603 — argv list invoking this package via sys.executable
                    gate_command(gate, args, verbose=session.verbose),
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            )
            procs.append((name, proc))
        for name, proc in procs:
            session.record(name, ok=proc.wait() == 0)
    if not session.json_output:
        print()


def _emit_json(session: _Session, duration: int) -> None:
    """Print the JSON result envelope (check-all.sh --json parity).

    Args:
        session: Completed run state.
        duration: Whole seconds for the entire run.
    """
    checks: dict[str, dict[str, str]] = {}
    for name in session.passed:
        checks[name] = {"status": "pass"}
    for name in session.failed:
        checks[name] = {"status": "fail"}
    print(
        json.dumps(
            {
                "status": "fail" if session.failed else "pass",
                "duration_seconds": duration,
                "passed": len(session.passed),
                "failed": len(session.failed),
                "checks": checks,
            }
        )
    )


def _print_summary(session: _Session, duration: int) -> None:
    """Print the human-readable summary block.

    Args:
        session: Completed run state.
        duration: Whole seconds for the entire run.
    """
    print("=== Quality Checks Summary ===")
    print(f"Passed: {len(session.passed)}")
    print(f"Failed: {len(session.failed)}")
    if session.verbose:
        print(f"Execution time: {duration} seconds")
    if session.failed:
        print("\nFailed checks:")
        for check in session.failed:
            print(f"  ✗ {check}")


def main(argv: list[str] | None = None) -> int:
    """Entry point for the check-all gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 when every check passed, 1 when any failed, 2 on errors.
    """
    args = _parse_args(argv)
    start = time.monotonic()
    common.enter_project_root()
    session = _Session(json_output=args.json_output, verbose=args.verbose)
    if not session.json_output:
        print("=== Running All Quality Checks ===\n")
    if args.parallel:
        _run_parallel(session)
        _run_sequential(session, FINAL_CHECKS)
    else:
        _run_sequential(session, PARALLEL_CHECKS + FINAL_CHECKS)
    duration = common.elapsed_seconds(start)
    if session.json_output:
        _emit_json(session, duration)
    else:
        _print_summary(session, duration)
    if session.failed:
        return 1
    print("\n✓ All quality checks passed!")
    return 0
