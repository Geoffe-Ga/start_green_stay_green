#!/usr/bin/env bash
# scripts/lint.sh - Run linting checks with Ruff
# Usage: ./scripts/lint.sh [--fix] [--check] [--verbose] [--json] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
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
            # CHECK mode not currently implemented - FIX mode controls behavior
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

Run linting checks on the project using Ruff.

OPTIONS:
    --fix       Auto-fix linting issues where possible
    --check     Check only, fail if issues found (default mode)
    --verbose   Show detailed output
    --json      Output results in JSON format
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           Linting issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0")              # Run checks in check mode
    $(basename "$0") --fix         # Auto-fix issues
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
    echo "=== Linting (Ruff) ==="
fi

LINT_START=$(date +%s)
if $FIX; then
    if $VERBOSE && ! $JSON_OUTPUT; then
        echo "Fixing linting issues..."
    fi
    ruff check . --fix 2>/tmp/ruff-stderr.txt
    EXIT_CODE=$?
else
    if $VERBOSE && ! $JSON_OUTPUT; then
        echo "Checking for linting issues..."
    fi
    ruff check . 2>/tmp/ruff-stderr.txt
    EXIT_CODE=$?
fi

LINT_END=$(date +%s)
LINT_TIME=$((LINT_END - LINT_START))
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

if [ $EXIT_CODE -eq 0 ]; then
    if $JSON_OUTPUT; then
        echo "{\"status\": \"pass\", \"duration_seconds\": $TOTAL_TIME, \"lint_duration\": $LINT_TIME}"
    else
        echo "✓ Linting checks passed"
        if $VERBOSE; then
            echo "Lint execution time: $LINT_TIME seconds"
        fi
    fi
    exit 0
else
    if $JSON_OUTPUT; then
        echo "{\"status\": \"fail\", \"duration_seconds\": $TOTAL_TIME, \"lint_duration\": $LINT_TIME}"
    else
        echo "✗ Linting checks failed" >&2
    fi
    exit 1
fi
