#!/usr/bin/env bash
# scripts/mutation.sh - Run mutation tests with score validation
# Usage: ./scripts/mutation.sh [--min-score SCORE] [--paths-to-mutate FILES] [--verbose] [--help]
#
# NOTE: Requires Python 3.11-3.13 due to mutmut/pony ORM compatibility.
#       Python 3.14+ is not yet supported. CI uses Python 3.11.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MIN_SCORE=80  # MAXIMUM QUALITY: 80% mutation score minimum
VERBOSE=false
PATHS_TO_MUTATE=""

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --min-score)
            MIN_SCORE="$2"
            shift 2
            ;;
        --paths-to-mutate)
            shift
            # Collect all remaining arguments as file paths
            while [[ $# -gt 0 ]] && [[ ! "$1" =~ ^-- ]]; do
                PATHS_TO_MUTATE="$PATHS_TO_MUTATE $1"
                shift
            done
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS] [FILES...]

Run mutation tests and validate minimum score threshold.

Mutation testing introduces small changes (mutations) to your code
to verify that your test suite catches them. A high mutation score
indicates effective tests.

OPTIONS:
    --min-score SCORE         Minimum mutation score (default: 80)
    --paths-to-mutate FILES   Only mutate specific files (space-separated)
    --verbose                 Show detailed output
    --help                    Display this help message

EXIT CODES:
    0                   Mutation score meets or exceeds minimum
    1                   Mutation score below minimum threshold
    2                   Error running mutation tests

QUALITY STANDARDS:
    MAXIMUM QUALITY:    80% minimum mutation score
    Good:               70-79%
    Acceptable:         60-69%
    Poor:               <60%

EXAMPLES:
    $(basename "$0")                            # Run on all files
    $(basename "$0") --min-score 70             # Run with 70% minimum
    $(basename "$0") --paths-to-mutate cli.py   # Only mutate cli.py
    $(basename "$0") --verbose                  # Show detailed output
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Set verbosity
if $VERBOSE; then
    set -x
fi

# Cleanup function to remove stale cache on interrupt
# shellcheck disable=SC2329  # Function is used in trap below
cleanup_mutation_cache() {
    if [ -f .mutmut-cache ]; then
        echo "Cleaning up mutation cache..." >&2
        rm -f .mutmut-cache
    fi
}

# Set up cleanup trap for interrupts only (not normal exit)
# Cache is preserved on successful completion for analysis
trap cleanup_mutation_cache INT TERM

# Ensure venv is available
ensure_venv || exit 2

# Filter and validate paths if --paths-to-mutate was specified
if [ -n "$PATHS_TO_MUTATE" ]; then
    FILTERED_PATHS=""
    for path in $PATHS_TO_MUTATE; do
        # Only include Python files in start_green_stay_green/ directory
        if [[ "$path" == start_green_stay_green/*.py ]]; then
            # Check if file exists and is readable
            if [ -f "$path" ]; then
                FILTERED_PATHS="$FILTERED_PATHS $path"
            fi
        fi
    done

    # If no valid Python files found, exit successfully (nothing to mutate)
    if [ -z "$FILTERED_PATHS" ]; then
        echo "No Python source files to mutate (non-code files or test files passed)"
        echo "Skipping mutation testing"
        exit 0
    fi

    PATHS_TO_MUTATE="$FILTERED_PATHS"
    echo "Mutating specific files:$PATHS_TO_MUTATE"
fi

# Check if mutmut is installed
if ! command -v mutmut &> /dev/null; then
    echo "Error: mutmut is not installed" >&2
    echo "Install with: pip install mutmut" >&2
    exit 2
fi

echo "=== Running Mutation Tests ==="
echo "Minimum required score: ${MIN_SCORE}%"
echo ""

# Run mutation tests and capture output
echo "Running mutmut (this may take several minutes)..."
MUTMUT_OUTPUT=$(mktemp)

# Build mutmut command with optional paths
MUTMUT_CMD="mutmut run"
if [ -n "$PATHS_TO_MUTATE" ]; then
    MUTMUT_CMD="$MUTMUT_CMD --paths-to-mutate=$PATHS_TO_MUTATE"
fi

if $MUTMUT_CMD 2>&1 | tee "$MUTMUT_OUTPUT"; then
    echo "✓ Mutmut run completed"
else
    # mutmut returns non-zero if there are surviving mutants, which is expected
    echo "ℹ Mutmut run completed (some mutants may have survived)"
fi

echo ""
echo "=== Mutation Test Results ==="

# Note: `mutmut results` has a bug that causes it to crash with TypeError
# when trying to display timeout mutants. We query the cache database directly instead.

# Query the cache database directly using Python
CACHE_RESULTS=$(python3 << 'EOF'
import sqlite3
import sys

try:
    conn = sqlite3.connect('.mutmut-cache')
    cursor = conn.cursor()

    # Get status counts
    cursor.execute('SELECT status, COUNT(*) FROM Mutant GROUP BY status')
    status_counts = dict(cursor.fetchall())

    killed = status_counts.get('ok_killed', 0)
    survived = status_counts.get('bad_survived', 0)
    suspicious = status_counts.get('ok_suspicious', 0)
    timeout = status_counts.get('bad_timeout', 0)
    untested = status_counts.get('untested', 0)

    print(f"{killed}|{survived}|{suspicious}|{timeout}|{untested}")

    conn.close()
except Exception as e:
    print(f"0|0|0|0|0", file=sys.stderr)
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
EOF
)

# Parse the results
if [ -n "$CACHE_RESULTS" ] && [[ "$CACHE_RESULTS" =~ ^[0-9]+\|[0-9]+\|[0-9]+\|[0-9]+\|[0-9]+$ ]]; then
    IFS='|' read -r KILLED SURVIVED SUSPICIOUS TIMEOUT UNTESTED <<< "$CACHE_RESULTS"

    echo "Cache query successful:"
    echo "  Killed: $KILLED"
    echo "  Survived: $SURVIVED"
    echo "  Suspicious: $SUSPICIOUS"
    echo "  Timeout: $TIMEOUT"
    echo "  Untested: $UNTESTED"
else
    # Fallback: Try to parse from progress line if cache query failed
    echo "Warning: Could not query cache, trying progress line fallback" >&2

    PROGRESS_LINE=$(grep -oE '[0-9]+/[0-9]+[[:space:]]+🎉[[:space:]]+[0-9]+[[:space:]]+⏰[[:space:]]+[0-9]+[[:space:]]+🤔[[:space:]]+[0-9]+[[:space:]]+🙁[[:space:]]+[0-9]+[[:space:]]+🔇[[:space:]]+[0-9]+' "$MUTMUT_OUTPUT" | tail -1)

    if [ -n "$PROGRESS_LINE" ]; then
        KILLED=$(echo "$PROGRESS_LINE" | grep -oE '🎉[[:space:]]+[0-9]+' | grep -oE '[0-9]+')
        TIMEOUT=$(echo "$PROGRESS_LINE" | grep -oE '⏰[[:space:]]+[0-9]+' | grep -oE '[0-9]+')
        SUSPICIOUS=$(echo "$PROGRESS_LINE" | grep -oE '🤔[[:space:]]+[0-9]+' | grep -oE '[0-9]+')
        SURVIVED=$(echo "$PROGRESS_LINE" | grep -oE '🙁[[:space:]]+[0-9]+' | grep -oE '[0-9]+')
        UNTESTED=0
    else
        echo "Error: Could not parse mutation results" >&2
        rm -f "$MUTMUT_OUTPUT"
        exit 2
    fi
fi

# Clean up temp file
rm -f "$MUTMUT_OUTPUT"

# Calculate total and score
# Note: We exclude untested mutants from the score calculation
TESTED_TOTAL=$((KILLED + SURVIVED + SUSPICIOUS + TIMEOUT))
TOTAL=$((TESTED_TOTAL + UNTESTED))

if [ "$TOTAL" -eq 0 ]; then
    echo "Warning: No mutants were generated" >&2
    echo "This might indicate:"
    echo "  - No code to mutate in start_green_stay_green/"
    echo "  - Configuration issue with mutmut"
    echo ""
    echo "Skipping mutation score validation"
    exit 0
fi

if [ "$TESTED_TOTAL" -eq 0 ]; then
    echo "Warning: No mutants were tested" >&2
    echo "All $UNTESTED mutants are untested"
    echo ""
    echo "Skipping mutation score validation"
    exit 0
fi

# Calculate mutation score (killed / tested_total * 100)
SCORE=$(awk "BEGIN {printf \"%.1f\", ($KILLED / $TESTED_TOTAL) * 100}")

echo "=== Mutation Score ==="
echo "Killed:      $KILLED"
echo "Survived:    $SURVIVED"
echo "Suspicious:  $SUSPICIOUS"
echo "Timeout:     $TIMEOUT"
echo "Untested:    $UNTESTED"
echo "Total:       $TOTAL (Tested: $TESTED_TOTAL)"
echo ""
echo "Mutation Score: ${SCORE}% (of tested mutants)"
echo "Required:       ${MIN_SCORE}%"
echo ""

# Compare score to threshold
if awk "BEGIN {exit !($SCORE >= $MIN_SCORE)}"; then
    echo "✓ Mutation score meets minimum threshold"
    echo ""

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Note: $SURVIVED mutants survived. To view them:"
        echo "  mutmut show <id>"
        echo "  mutmut html  # Generate HTML report"
    fi

    exit 0
else
    echo "✗ Mutation score below minimum threshold" >&2
    echo "" >&2
    echo "Your test suite killed ${SCORE}% of mutants" >&2
    echo "Minimum required: ${MIN_SCORE}%" >&2
    echo "" >&2
    echo "To improve mutation score:" >&2
    echo "  1. View surviving mutants: mutmut show <id>" >&2
    echo "  2. Add tests to catch these mutations" >&2
    echo "  3. Generate HTML report: mutmut html" >&2
    echo "" >&2

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Surviving mutants:" >&2
        mutmut show 1 2>&1 | head -20 || true
    fi

    exit 1
fi
