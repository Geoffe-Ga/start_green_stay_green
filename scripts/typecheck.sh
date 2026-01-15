#!/usr/bin/env bash
# scripts/typecheck.sh - Run type checking with MyPy
# Usage: ./scripts/typecheck.sh [--verbose] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
START_TIME=$(date +%s)

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run type checking using MyPy.

OPTIONS:
    --verbose   Show detailed output
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           All type checks passed
    1           Type errors found
    2           Error running checks

EXAMPLES:
    $(basename "$0")              # Run type checks
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

echo "=== Type Checking (MyPy) ==="

TYPE_START=$(date +%s)
if $VERBOSE; then
    echo "Running MyPy type checker..."
fi
mypy . 2>/tmp/mypy-stderr.txt || {
    echo "✗ Type checking failed" >&2
    exit 1
}

TYPE_END=$(date +%s)
TYPE_TIME=$((TYPE_END - TYPE_START))
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "✓ Type checks passed"
if $VERBOSE; then
    echo "Type check execution time: $TYPE_TIME seconds"
    echo "Total execution time: $TOTAL_TIME seconds"
fi
exit 0
