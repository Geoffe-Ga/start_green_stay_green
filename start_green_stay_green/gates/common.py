"""Shared plumbing for the cross-platform quality-gate runner (#382).

Holds the quality thresholds (single in-package source), cross-platform
tool resolution (``Scripts/`` vs ``bin/`` venv layouts), subprocess
helpers that mirror the historical bash scripts' stream handling, and
UTF-8 output configuration for Windows consoles.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404 — single audited seam; runs only resolved quality tools
import sys
import time

from start_green_stay_green.utils.fs import is_windows

#: Re-exported stream dispositions so gate modules never import
#: subprocess themselves — this module is the single audited subprocess
#: seam for the whole gate runner.
PIPE = subprocess.PIPE
DEVNULL = subprocess.DEVNULL
STDOUT = subprocess.STDOUT

#: Result type returned by :func:`run_tool` (text-mode).
ToolResult = subprocess.CompletedProcess[str]

#: Minimum coverage percentage enforced by the ``test --coverage`` and
#: ``coverage`` gates. Mirrors ``[tool.coverage.report] fail_under`` in
#: pyproject.toml (the user-editable source of truth).
COVERAGE_THRESHOLD = 90

#: Minimum mutation score (MAXIMUM QUALITY) enforced by the mutation gate.
MUTATION_MIN_SCORE = 80

#: Per-function cyclomatic complexity ceiling enforced by the complexity
#: gate. Mirrors ``[tool.ruff.lint.mccabe] max-complexity``.
MAX_CYCLOMATIC_COMPLEXITY = 10

#: Minimum maintainability index enforced by the complexity gate.
MIN_MAINTAINABILITY_INDEX = 20

#: Maximum radon/xenon complexity grade (A = complexity 1-5).
MAX_COMPLEXITY_GRADE = "A"

#: Version string reported by every gate's ``--version`` flag (parity
#: with the historical ``VERSION="1.0.0"`` in scripts/*.sh).
GATE_VERSION = "1.0.0"


def configure_utf8_output() -> None:
    """Force UTF-8 (replacement on failure) on stdout/stderr.

    Windows consoles default to a legacy ANSI code page (cp1252) which
    cannot encode the gate output glyphs (per the #380 PYTHONUTF8
    conventions). Streams without ``reconfigure`` (test doubles,
    pytest captures) are left untouched.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def project_root() -> Path:
    """Return the repository root (two levels above this package).

    Returns:
        Absolute path to the project root, mirroring the bash scripts'
        ``PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"`` resolution.
    """
    return Path(__file__).resolve().parents[2]


def enter_project_root() -> None:
    """Change the working directory to the repository root.

    Every gate operates from the project root, exactly like the bash
    scripts' ``cd "$PROJECT_ROOT"``.
    """
    os.chdir(project_root())


def resolve_tool(name: str) -> str | None:
    """Resolve a quality tool to an absolute executable path.

    Prefers the console script that lives next to the running
    interpreter (``Scripts/<name>.exe`` on Windows, ``bin/<name>`` on
    POSIX) so the gate uses the active environment's tools, then falls
    back to ``shutil.which``. Never assumes bash or a POSIX layout.

    Args:
        name: Console-script name, e.g. ``"ruff"`` or ``"pip-audit"``.

    Returns:
        Absolute path to the executable, or None if the tool is not
        installed.
    """
    suffix = ".exe" if is_windows() else ""
    candidate = Path(sys.executable).parent / f"{name}{suffix}"
    if candidate.exists():
        return str(candidate)
    return shutil.which(name)


def run_tool(
    cmd: list[str],
    *,
    stdout: int | None = None,
    stderr: int | None = PIPE,
) -> ToolResult:
    """Run a quality tool, mirroring the bash scripts' stream handling.

    By default stdout streams to the console and stderr is captured —
    the equivalent of the scripts' ``tool 2>"$TMP_STDERR"`` pattern,
    where callers decide whether to surface the captured stderr on
    failure.

    Args:
        cmd: Full argument vector; the executable must be an absolute
            path from :func:`resolve_tool` or ``sys.executable``.
        stdout: ``subprocess`` stdout disposition (None streams).
        stderr: ``subprocess`` stderr disposition (PIPE captures).

    Returns:
        Completed process with text-mode captured streams.
    """
    flush_streams()
    return subprocess.run(  # nosec B603 — argv list (no shell), executable resolved via resolve_tool/sys.executable
        cmd,
        check=False,
        text=True,
        stdout=stdout,
        stderr=stderr,
    )


def flush_streams() -> None:
    """Flush stdout/stderr so gate output precedes child-process output.

    Python buffers ``print`` when stdout is a pipe (pre-commit, CI),
    while child processes write to the inherited file descriptor
    directly — without a flush the gate headers would appear after the
    tool output they introduce.
    """
    sys.stdout.flush()
    sys.stderr.flush()


def stream_tool(cmd: list[str]) -> tuple[int, str]:
    """Run a tool streaming combined output while capturing it (bash ``tee``).

    Args:
        cmd: Full argument vector with an absolute executable path.

    Returns:
        Tuple of (exit code, combined stdout+stderr text).
    """
    flush_streams()
    lines: list[str] = []
    with subprocess.Popen(  # nosec B603 — argv list (no shell), executable resolved via resolve_tool
        cmd,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
    ) as process:
        if process.stdout is not None:
            for line in process.stdout:
                print(line, end="")
                lines.append(line)
    return process.returncode, "".join(lines)


def elapsed_seconds(start: float) -> int:
    """Return whole seconds elapsed since ``start`` (a monotonic stamp).

    Args:
        start: Value previously returned by ``time.monotonic()``.

    Returns:
        Elapsed time truncated to whole seconds, matching the bash
        ``$(($(date +%s) - START_TIME))`` arithmetic.
    """
    return int(time.monotonic() - start)


def gate_parser(
    prog: str,
    description: str,
    *,
    version_flag: bool = True,
) -> argparse.ArgumentParser:
    """Build the base argument parser shared by every gate.

    argparse preserves the bash scripts' exit-code contract: unknown
    options exit 2, ``--help`` exits 0, and (when enabled) ``--version``
    prints ``<gate> version 1.0.0`` and exits 0.

    Args:
        prog: Gate name used in usage/version output.
        description: One-line gate description for ``--help``.
        version_flag: Whether the gate exposes ``--version``
            (mutation.sh historically did not).

    Returns:
        Parser pre-populated with ``--verbose`` and optional
        ``--version``.
    """
    parser = argparse.ArgumentParser(prog=prog, description=description)
    if version_flag:
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s version {GATE_VERSION}",
        )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    return parser
