"""Mutation gate — mutmut score validation (port of ``scripts/mutation.sh``).

The invocation is ported faithfully even though mutmut is currently
broken repo-wide (configuration crash, tracked separately): this gate is
a periodic quality check, not part of the continuous check-all surface,
and the port must not paper over or "fix" the mutmut config here.

NOTE: Requires Python 3.11-3.13 due to mutmut/pony ORM compatibility.
"""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys
from typing import TYPE_CHECKING

from start_green_stay_green.gates import common

if TYPE_CHECKING:
    import argparse

#: SQLite cache mutmut writes its results to.
CACHE_FILE = ".mutmut-cache"

#: mutmut progress line, e.g. ``12/40  🎉 30  ⏰ 2  🤔 1  🙁 7  🔇 0``
#: (fallback when the cache cannot be queried — mutmut's own
#: ``results`` command crashes on timeout mutants).
_PROGRESS_LINE = re.compile(
    r"\d+/\d+\s+🎉\s+(?P<killed>\d+)\s+⏰\s+(?P<timeout>\d+)"
    r"\s+🤔\s+(?P<suspicious>\d+)\s+🙁\s+(?P<survived>\d+)\s+🔇\s+\d+"
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse mutation gate arguments (parity with mutation.sh).

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        Parsed namespace.
    """
    parser = common.gate_parser(
        "mutation",
        "Run mutation tests and validate minimum score threshold.",
        version_flag=False,
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=common.MUTATION_MIN_SCORE,
        help=f"Minimum mutation score (default: {common.MUTATION_MIN_SCORE})",
    )
    parser.add_argument(
        "--paths-to-mutate",
        nargs="+",
        default=None,
        metavar="FILES",
        help="Only mutate specific files (space-separated)",
    )
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Output machine-readable JSON metrics to stdout",
    )
    return parser.parse_args(argv)


def query_cache() -> dict[str, int] | None:
    """Query the mutmut SQLite cache for per-status mutant counts.

    Args:
        None.

    Returns:
        Counts dict (killed/survived/suspicious/timeout/untested), or
        None when the cache is missing or unreadable.
    """
    if not Path(CACHE_FILE).is_file():
        return None
    try:
        # closing() because sqlite3's context manager only scopes the
        # transaction; the connection itself must be closed explicitly.
        with closing(sqlite3.connect(CACHE_FILE)) as connection:
            rows = connection.execute(
                "SELECT status, COUNT(*) FROM Mutant GROUP BY status"
            ).fetchall()
    except sqlite3.Error:
        return None
    counts = dict(rows)
    return {
        "killed": counts.get("ok_killed", 0),
        "survived": counts.get("bad_survived", 0),
        "suspicious": counts.get("ok_suspicious", 0),
        "timeout": counts.get("bad_timeout", 0),
        "untested": counts.get("untested", 0),
    }


def _metrics() -> int:
    """Emit machine-readable mutation metrics from the cache only.

    Never runs mutmut, matching mutation.sh --metrics.

    Returns:
        Always 0.
    """
    counts = query_cache()
    if counts is None:
        print('{"killed": null, "survived": null, "timeout": null, "score": null}')
        return 0
    tested = counts["killed"] + counts["survived"] + counts["timeout"]
    score = round((counts["killed"] / tested) * 100, 1) if tested > 0 else None
    print(
        json.dumps(
            {
                "killed": counts["killed"],
                "survived": counts["survived"],
                "timeout": counts["timeout"],
                "score": score,
            }
        )
    )
    return 0


def filter_paths(paths: list[str]) -> list[str]:
    """Keep only existing Python sources under the package directory.

    Mirrors mutation.sh's filtering: only ``start_green_stay_green/*.py``
    files that exist are mutated; everything else (test files, docs,
    deleted files) is dropped.

    Args:
        paths: Candidate paths from ``--paths-to-mutate``.

    Returns:
        The mutate-worthy subset, in input order.
    """
    return [
        path
        for path in paths
        if path.startswith("start_green_stay_green/")
        and path.endswith(".py")
        and Path(path).is_file()
    ]


def _cleanup_cache() -> None:
    """Remove a stale mutation cache after an interrupt (mutation.sh trap)."""
    cache = Path(CACHE_FILE)
    if cache.exists():
        print("Cleaning up mutation cache...", file=sys.stderr)
        cache.unlink()


def _run_mutmut(mutmut: str, paths: list[str] | None) -> tuple[int, str]:
    """Run ``mutmut run``, streaming and capturing output (bash ``tee``).

    The cache is cleaned up on interrupt, mirroring the script's
    ``trap cleanup_mutation_cache INT TERM`` (SIGTERM cleanup is not
    replicated; KeyboardInterrupt covers the interactive case).

    Args:
        mutmut: Absolute path to the mutmut executable.
        paths: Filtered file list, or None to mutate everything.

    Returns:
        Tuple of (exit code, combined output).
    """
    cmd = [mutmut, "run"]
    if paths:
        # One flag per path: mutmut does not split a joined value, so a
        # single space-joined argument would name a nonexistent path.
        for path in paths:
            cmd.extend(["--paths-to-mutate", path])
    try:
        return common.stream_tool(cmd)
    except KeyboardInterrupt:
        _cleanup_cache()
        raise


def parse_progress_fallback(output: str) -> dict[str, int] | None:
    """Parse mutant counts from mutmut's progress line (cache fallback).

    Args:
        output: Combined ``mutmut run`` output.

    Returns:
        Counts dict with untested fixed at 0 (parity with the script),
        or None when no progress line is present.
    """
    matches = list(_PROGRESS_LINE.finditer(output))
    if not matches:
        return None
    last = matches[-1]
    return {
        "killed": int(last.group("killed")),
        "survived": int(last.group("survived")),
        "suspicious": int(last.group("suspicious")),
        "timeout": int(last.group("timeout")),
        "untested": 0,
    }


def _collect_counts(output: str) -> dict[str, int] | None:
    """Resolve mutant counts from the cache, falling back to the output.

    Args:
        output: Combined ``mutmut run`` output.

    Returns:
        Counts dict, or None when neither source parses.
    """
    counts = query_cache()
    if counts is not None:
        print("Cache query successful:")
        print(f"  Killed: {counts['killed']}")
        print(f"  Survived: {counts['survived']}")
        print(f"  Suspicious: {counts['suspicious']}")
        print(f"  Timeout: {counts['timeout']}")
        print(f"  Untested: {counts['untested']}")
        return counts
    print(
        "Warning: Could not query cache, trying progress line fallback",
        file=sys.stderr,
    )
    return parse_progress_fallback(output)


def _print_score_block(counts: dict[str, int], score: float, min_score: float) -> None:
    """Print the mutation score breakdown.

    Args:
        counts: Per-status mutant counts.
        score: Computed mutation score percentage.
        min_score: Required minimum score.
    """
    tested = sum(counts[key] for key in ("killed", "survived", "suspicious", "timeout"))
    print("=== Mutation Score ===")
    print(f"Killed:      {counts['killed']}")
    print(f"Survived:    {counts['survived']}")
    print(f"Suspicious:  {counts['suspicious']}")
    print(f"Timeout:     {counts['timeout']}")
    print(f"Untested:    {counts['untested']}")
    print(f"Total:       {tested + counts['untested']} (Tested: {tested})")
    print(f"\nMutation Score: {score:.1f}% (of tested mutants)")
    print(f"Required:       {min_score:g}%\n")


def _report_failure(
    mutmut: str, counts: dict[str, int], score: float, min_score: float
) -> int:
    """Report a below-threshold mutation score with remediation hints.

    Args:
        mutmut: Absolute path to the mutmut executable.
        counts: Per-status mutant counts.
        score: Computed mutation score percentage.
        min_score: Required minimum score.

    Returns:
        Always 1.
    """
    print("✗ Mutation score below minimum threshold\n", file=sys.stderr)
    print(f"Your test suite killed {score:.1f}% of mutants", file=sys.stderr)
    print(f"Minimum required: {min_score:g}%\n", file=sys.stderr)
    print("To improve mutation score:", file=sys.stderr)
    print("  1. View surviving mutants: mutmut show <id>", file=sys.stderr)
    print("  2. Add tests to catch these mutations", file=sys.stderr)
    print("  3. Generate HTML report: mutmut html\n", file=sys.stderr)
    if counts["survived"] > 0:
        print("Surviving mutants:", file=sys.stderr)
        _show_first_survivor(mutmut)
    return 1


def _show_first_survivor(mutmut: str) -> None:
    """Print the first surviving mutant (``mutmut show 1 | head -20``).

    Errors are ignored, matching the script's ``|| true``.

    Args:
        mutmut: Absolute path to the mutmut executable.
    """
    result = common.run_tool(
        [mutmut, "show", "1"],
        stdout=common.PIPE,
        stderr=common.STDOUT,
    )
    lines = (result.stdout or "").splitlines()[:20]
    print("\n".join(lines), file=sys.stderr)


def _evaluate(mutmut: str, counts: dict[str, int], min_score: float) -> int:
    """Validate the mutation score against the threshold.

    Args:
        mutmut: Absolute path to the mutmut executable.
        counts: Per-status mutant counts.
        min_score: Required minimum score.

    Returns:
        0 when the score meets the threshold (or there was nothing to
        test), 1 when below threshold.
    """
    skip = _skip_when_untestable(counts)
    if skip is not None:
        return skip
    tested = _tested_count(counts)
    score = round((counts["killed"] / tested) * 100, 1)
    _print_score_block(counts, score, min_score)
    if score >= min_score:
        return _report_pass(counts)
    return _report_failure(mutmut, counts, score, min_score)


def _tested_count(counts: dict[str, int]) -> int:
    """Sum the mutants that actually ran (everything but untested).

    Args:
        counts: Per-status mutant counts.

    Returns:
        Number of tested mutants.
    """
    return (
        counts["killed"] + counts["survived"] + counts["suspicious"] + counts["timeout"]
    )


def _skip_when_untestable(counts: dict[str, int]) -> int | None:
    """Handle the no-mutants and all-untested warning paths.

    Args:
        counts: Per-status mutant counts.

    Returns:
        0 when score validation must be skipped, None to proceed.
    """
    tested = _tested_count(counts)
    if tested + counts["untested"] == 0:
        print("Warning: No mutants were generated", file=sys.stderr)
        print("This might indicate:")
        print("  - No code to mutate in start_green_stay_green/")
        print("  - Configuration issue with mutmut")
        print("\nSkipping mutation score validation")
        return 0
    if tested == 0:
        print("Warning: No mutants were tested", file=sys.stderr)
        print(f"All {counts['untested']} mutants are untested")
        print("\nSkipping mutation score validation")
        return 0
    return None


def _report_pass(counts: dict[str, int]) -> int:
    """Report a passing mutation score with the survivors note.

    Args:
        counts: Per-status mutant counts.

    Returns:
        Always 0.
    """
    print("✓ Mutation score meets minimum threshold\n")
    if counts["survived"] > 0:
        print(f"Note: {counts['survived']} mutants survived. To view them:")
        print("  mutmut show <id>")
        print("  mutmut html  # Generate HTML report")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the mutation gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        0 when the score meets the threshold, 1 when below it, 2 on
        runner errors.
    """
    args = _parse_args(argv)
    common.enter_project_root()
    if args.metrics:
        return _metrics()
    paths = _resolve_paths(args.paths_to_mutate)
    if paths is not None and not paths:
        return 0
    mutmut = common.resolve_tool("mutmut")
    if mutmut is None:
        print("Error: mutmut is not installed", file=sys.stderr)
        print("Install with: pip install mutmut", file=sys.stderr)
        return 2
    return _execute(mutmut, paths, args.min_score)


def _resolve_paths(requested: list[str] | None) -> list[str] | None:
    """Filter the requested mutate paths, announcing the outcome.

    Args:
        requested: Raw ``--paths-to-mutate`` values, or None when the
            whole package should be mutated.

    Returns:
        None to mutate everything, a non-empty filtered list to mutate
        specific files, or an empty list when nothing mutate-worthy was
        requested (the gate then exits 0, matching the script).
    """
    if requested is None:
        return None
    paths = filter_paths(requested)
    if not paths:
        print("No Python source files to mutate (non-code files or test files passed)")
        print("Skipping mutation testing")
        return []
    print(f"Mutating specific files: {' '.join(paths)}")
    return paths


def _execute(mutmut: str, paths: list[str] | None, min_score: float) -> int:
    """Run mutmut and validate the resulting score.

    Args:
        mutmut: Absolute path to the mutmut executable.
        paths: Filtered file list, or None to mutate everything.
        min_score: Required minimum score.

    Returns:
        Gate exit code.
    """
    print("=== Running Mutation Tests ===")
    print(f"Minimum required score: {min_score:g}%\n")
    print("Running mutmut (this may take several minutes)...")
    returncode, output = _run_mutmut(mutmut, paths)
    if returncode == 0:
        print("✓ Mutmut run completed")
    else:
        print("\u2139 Mutmut run completed (some mutants may have survived)")
    print("\n=== Mutation Test Results ===")
    counts = _collect_counts(output)
    if counts is None:
        print("Error: Could not parse mutation results", file=sys.stderr)
        return 2
    return _evaluate(mutmut, counts, min_score)
