#!/usr/bin/env bash
# scripts/format.sh - Format code with Black and isort
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--json] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=true  # Default to check mode for consistency with CI
VERBOSE=false
JSON_OUTPUT=false
START_TIME=$(date +%s)

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --check)
            CHECK=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format code using Black and isort.

OPTIONS:
    --fix       Apply formatting changes (default)
    --check     Check only, fail if changes needed
    --verbose   Show detailed output
    --json      Output results in JSON format
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0") --fix         # Apply formatting
    $(basename "$0") --check       # Check only
    $(basename "$0") --verbose     # Show detailed output
    $(basename "$0") --json        # JSON output
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

if ! $JSON_OUTPUT; then
    echo "=== Formatting (Black + isort) ==="
fi

# Determine mode - check takes precedence, then fix
if $CHECK && ! $FIX; then
    MODE="--check"
elif $FIX; then
    CHECK=false  # Fix mode overrides check mode
    MODE=""
else
    MODE="--check"  # Default to check
fi

FORMAT_START=$(date +%s)

# Run isort
if $VERBOSE && ! $JSON_OUTPUT; then
    echo "Running isort..."
fi
isort $MODE . 2>/tmp/isort-stderr.txt || {
    if ! $JSON_OUTPUT; then
        echo "✗ isort failed" >&2
    fi
    exit 1
}

# Run Black
if $VERBOSE && ! $JSON_OUTPUT; then
    echo "Running Black..."
fi
black $MODE . 2>/tmp/black-stderr.txt || {
    if ! $JSON_OUTPUT; then
        echo "✗ Black failed" >&2
    fi
    exit 1
}

FORMAT_END=$(date +%s)
FORMAT_TIME=$((FORMAT_END - FORMAT_START))
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

if $JSON_OUTPUT; then
    echo "{\"status\": \"pass\", \"duration_seconds\": $TOTAL_TIME, \"format_duration\": $FORMAT_TIME}"
else
    if [ -n "$MODE" ]; then
        echo "✓ Code formatting check passed"
    else
        echo "✓ Code formatted successfully"
    fi
    if $VERBOSE; then
        echo "Format execution time: $FORMAT_TIME seconds"
    fi
fi
exit 0
