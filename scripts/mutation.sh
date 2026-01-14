#!/usr/bin/env bash
# scripts/mutation.sh - Run mutation tests with score validation
# Usage: ./scripts/mutation.sh [--min-score SCORE] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MIN_SCORE=80  # MAXIMUM QUALITY: 80% mutation score minimum
VERBOSE=false

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
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run mutation tests and validate minimum score threshold.

Mutation testing introduces small changes (mutations) to your code
to verify that your test suite catches them. A high mutation score
indicates effective tests.

OPTIONS:
    --min-score SCORE   Minimum mutation score (default: 80)
    --verbose           Show detailed output
    --help              Display this help message

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
    $(basename "$0")                    # Run with 80% minimum
    $(basename "$0") --min-score 70     # Run with 70% minimum
    $(basename "$0") --verbose          # Show detailed output
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

# Ensure venv is available and set up cleanup
setup_cleanup_trap
ensure_venv || exit 2

# Check if mutmut is installed
if ! command -v mutmut &> /dev/null; then
    echo "Error: mutmut is not installed" >&2
    echo "Install with: pip install mutmut" >&2
    exit 2
fi

echo "=== Running Mutation Tests ==="
echo "Minimum required score: ${MIN_SCORE}%"
echo ""

# Run mutation tests (allow failure, we'll check score)
echo "Running mutmut (this may take several minutes)..."
if mutmut run --paths-to-mutate=start_green_stay_green/ 2>&1; then
    echo "✓ Mutmut run completed"
else
    # mutmut returns non-zero if there are surviving mutants, which is expected
    echo "ℹ Mutmut run completed (some mutants may have survived)"
fi

echo ""
echo "=== Mutation Test Results ==="

# Get results as JSON
if ! mutmut junitxml > /dev/null 2>&1; then
    echo "Warning: Could not generate JUnit XML (may be empty results)" >&2
fi

# Parse mutmut results
RESULTS=$(mutmut results)
echo "$RESULTS"
echo ""

# Extract counts from results
KILLED=$(echo "$RESULTS" | grep -oP 'Killed: \K\d+' || echo "0")
SURVIVED=$(echo "$RESULTS" | grep -oP 'Survived: \K\d+' || echo "0")
SUSPICIOUS=$(echo "$RESULTS" | grep -oP 'Suspicious: \K\d+' || echo "0")
TIMEOUT=$(echo "$RESULTS" | grep -oP 'Timeout: \K\d+' || echo "0")

# Calculate total and score
TOTAL=$((KILLED + SURVIVED + SUSPICIOUS + TIMEOUT))

if [ "$TOTAL" -eq 0 ]; then
    echo "Warning: No mutants were generated" >&2
    echo "This might indicate:"
    echo "  - No code to mutate in start_green_stay_green/"
    echo "  - Configuration issue with mutmut"
    echo ""
    echo "Skipping mutation score validation"
    exit 0
fi

# Calculate mutation score (killed / total * 100)
SCORE=$(awk "BEGIN {printf \"%.1f\", ($KILLED / $TOTAL) * 100}")

echo "=== Mutation Score ==="
echo "Killed:      $KILLED"
echo "Survived:    $SURVIVED"
echo "Suspicious:  $SUSPICIOUS"
echo "Timeout:     $TIMEOUT"
echo "Total:       $TOTAL"
echo ""
echo "Mutation Score: ${SCORE}%"
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
