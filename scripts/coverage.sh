#!/usr/bin/env bash
# scripts/coverage.sh - Generate coverage reports
# Usage: ./scripts/coverage.sh [--html] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

HTML=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --html)
            HTML=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Generate coverage reports using coverage/pytest-cov.

OPTIONS:
    --html      Generate HTML coverage report
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Coverage report generated
    1           Coverage threshold not met
    2           Error generating report

EXAMPLES:
    $(basename "$0")          # Generate terminal report
    $(basename "$0") --html   # Generate HTML report
    $(basename "$0") --verbose # Show detailed output
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

echo "=== Generating Coverage Report ==="

# Run tests with coverage
COVERAGE_ARGS=(--cov=start_green_stay_green --cov-report=term-missing)

if $HTML; then
    echo "Generating HTML coverage report..."
    COVERAGE_ARGS+=(--cov-report=html)
fi

if $VERBOSE; then
    echo "Running pytest with coverage..."
fi

pytest "${COVERAGE_ARGS[@]}" tests/ || { echo "✗ Coverage generation failed" >&2; exit 1; }

# Check coverage threshold (90%)
COVERAGE_THRESHOLD=90
if command -v coverage &> /dev/null; then
    COVERAGE_PERCENT=$(coverage report | grep TOTAL | awk '{print $NF}' | sed 's/%//')
    if (( $(echo "$COVERAGE_PERCENT < $COVERAGE_THRESHOLD" | bc -l) )); then
        echo "✗ Coverage ${COVERAGE_PERCENT}% is below threshold of ${COVERAGE_THRESHOLD}%" >&2
        exit 1
    fi
fi

if $HTML; then
    echo "✓ HTML coverage report generated in htmlcov/index.html"
else
    echo "✓ Coverage report generated"
fi

exit 0
