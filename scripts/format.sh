#!/usr/bin/env bash
# scripts/format.sh - Format code with Black and isort
# Usage: ./scripts/format.sh [--fix] [--check] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
CHECK=true  # Default to check mode for consistency with CI
VERBOSE=false

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
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Format code using Black and isort.

OPTIONS:
    --fix       Apply formatting changes (default)
    --check     Check only, fail if changes needed
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Code is properly formatted
    1           Formatting issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0") --fix         # Apply formatting
    $(basename "$0") --check       # Check only
    $(basename "$0") --verbose     # Show detailed output
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

echo "=== Formatting (Black + isort) ==="

# Determine mode - check takes precedence, then fix
if $CHECK && ! $FIX; then
    MODE="--check"
elif $FIX; then
    CHECK=false  # Fix mode overrides check mode
    MODE=""
else
    MODE="--check"  # Default to check
fi

# Run isort
if $VERBOSE; then
    echo "Running isort..."
fi
isort $MODE . || { echo "✗ isort failed" >&2; exit 1; }

# Run Black
if $VERBOSE; then
    echo "Running Black..."
fi
black $MODE . || { echo "✗ Black failed" >&2; exit 1; }

if [ -n "$MODE" ]; then
    echo "✓ Code formatting check passed"
else
    echo "✓ Code formatted successfully"
fi
exit 0
