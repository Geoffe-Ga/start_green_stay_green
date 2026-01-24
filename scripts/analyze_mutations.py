#!/usr/bin/env python3
"""Analyze mutmut cache database for mutation testing insights.

This script provides detailed analysis of mutation testing results including:
- Overall mutation score and statistics
- Files with the most surviving mutants
- Sample of specific surviving mutants for debugging

Usage:
    ./scripts/analyze_mutations.py
    python scripts/analyze_mutations.py --top 10
"""

# ruff: noqa: T201  # print() is intentional for CLI output script
# ruff: noqa: PLR0915  # Many statements acceptable for reporting script

import argparse
from pathlib import Path
import sqlite3
import sys

# Quality thresholds
MINIMUM_MUTATION_SCORE = 80


def analyze_cache(cache_path: Path, top_files: int = 20) -> None:
    """Analyze mutmut cache and print detailed statistics.

    Args:
        cache_path: Path to .mutmut-cache file.
        top_files: Number of top files to show (default: 20).
    """
    if not cache_path.exists():
        print(f"Error: Cache file not found: {cache_path}", file=sys.stderr)
        print("Run mutation tests first: ./scripts/mutation.sh", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(cache_path)
    cursor = conn.cursor()

    print("=== Mutmut Cache Analysis ===\n")

    # Get total mutants
    cursor.execute("SELECT COUNT(*) FROM Mutant")
    total = cursor.fetchone()[0]
    print(f"Total mutants: {total}")
    print()

    # Get status counts
    cursor.execute("SELECT status, COUNT(*) FROM Mutant GROUP BY status")
    status_counts = dict(cursor.fetchall())
    killed = status_counts.get("ok_killed", 0)
    survived = status_counts.get("bad_survived", 0)
    suspicious = status_counts.get("ok_suspicious", 0)
    timeout = status_counts.get("bad_timeout", 0)
    untested = status_counts.get("untested", 0)

    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    print()

    # Calculate score
    if total > 0:
        tested_total = total - untested
        if tested_total > 0:
            score = (killed / tested_total) * 100
            print(f"Mutation Score: {score:.1f}%")
            print(f"Required: {MINIMUM_MUTATION_SCORE}%")
            print()
            print("Breakdown:")
            killed_pct = killed / tested_total * 100
            survived_pct = survived / tested_total * 100
            suspicious_pct = suspicious / tested_total * 100
            timeout_pct = timeout / tested_total * 100
            print(f"  Killed: {killed} ({killed_pct:.1f}% of tested)")
            print(f"  Survived: {survived} ({survived_pct:.1f}% of tested)")
            print(f"  Suspicious: {suspicious} ({suspicious_pct:.1f}%)")
            print(f"  Timeout: {timeout} ({timeout_pct:.1f}%)")
            print(f"  Untested: {untested}")
            print()

            if score < MINIMUM_MUTATION_SCORE:
                gap = int((MINIMUM_MUTATION_SCORE / 100 * tested_total) - killed)
                msg = f"⚠️  Need to kill {gap} more mutants"
                msg += f" to reach {MINIMUM_MUTATION_SCORE}%"
                print(msg)
                print()

    # Show files with most survived mutants
    if survived > 0:
        print(f"=== Files with Most Survived Mutants (Top {top_files}) ===")
        cursor.execute(
            """
            SELECT sf.filename, COUNT(*) as count
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
            GROUP BY sf.filename
            ORDER BY count DESC
            LIMIT ?
        """,
            (top_files,),
        )
        for filename, count in cursor.fetchall():
            percentage = (count / survived) * 100
            print(f"  {count:3d} ({percentage:5.1f}%): {filename}")
        print()

        # Show sample of survived mutants
        print("Sample of survived mutants (first 10):")
        cursor.execute(
            """
            SELECT m.id, sf.filename, l.line_number
            FROM Mutant m, Line l, SourceFile sf
            WHERE m.line = l.id
              AND l.sourcefile = sf.id
              AND m.status = "bad_survived"
            ORDER BY sf.filename, l.line_number
            LIMIT 10
        """
        )
        for mutant_id, filename, line_number in cursor.fetchall():
            print(f"  Mutant {mutant_id}: {filename}:{line_number}")
        print()
        print("To view a specific mutant: mutmut show <id>")
        print("To generate HTML report: mutmut html")

    conn.close()


def main() -> None:
    """Parse arguments and run cache analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze mutation testing results from .mutmut-cache"
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".mutmut-cache"),
        help="Path to mutmut cache file (default: .mutmut-cache)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top files to show (default: 20)",
    )

    args = parser.parse_args()
    analyze_cache(args.cache, args.top)


if __name__ == "__main__":
    main()
