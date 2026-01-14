#!/usr/bin/env bash
# scripts/typecheck.sh - Run type checking with MyPy
# Usage: ./scripts/typecheck.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

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
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run type checking using MyPy.

OPTIONS:
    --verbose   Show detailed output
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

if $VERBOSE; then
    echo "Running MyPy type checker..."
fi
mypy . || { echo "✗ Type checking failed" >&2; exit 1; }

echo "✓ Type checks passed"
exit 0
