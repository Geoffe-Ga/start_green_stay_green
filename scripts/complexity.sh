#!/usr/bin/env bash
# scripts/complexity.sh - Code complexity analysis with MAXIMUM QUALITY enforcement
# Usage: ./scripts/complexity.sh [--verbose] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
START_TIME=$(date +%s)

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# MAXIMUM QUALITY thresholds
MAX_CYCLOMATIC_COMPLEXITY=10
MIN_MAINTAINABILITY_INDEX=20
MAX_COMPLEXITY_GRADE="A"  # A = 1-5 (best), B = 6-10, C = 11-20, etc.

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

Analyze code complexity and enforce MAXIMUM QUALITY thresholds.

MAXIMUM QUALITY THRESHOLDS:
  - Cyclomatic Complexity: ≤ 10 per function
  - Maintainability Index: ≥ 20
  - Overall Grade: A (complexity 1-5)
  - Max Arguments: 5 (enforced by ruff/pylint)
  - Max Branches: 12 (enforced by ruff/pylint)
  - Max Lines: 50 per function (enforced by ruff/pylint)

OPTIONS:
    --verbose   Show detailed output
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           All complexity thresholds met
    1           One or more thresholds exceeded
    2           Error during analysis (tools not installed)

EXAMPLES:
    $(basename "$0")          # Analyze with MAXIMUM QUALITY thresholds
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

# Ensure venv is available and set up cleanup
setup_cleanup_trap
ensure_venv || exit 2

echo "=== Code Complexity Analysis (MAXIMUM QUALITY) ==="
echo ""

FAILED_CHECKS=()
PASSED_CHECKS=()

# Check if tools are installed
if ! command -v radon &> /dev/null; then
    echo "Error: radon not installed" >&2
    echo "Install with: pip install radon" >&2
    exit 2
fi

if ! command -v xenon &> /dev/null; then
    echo "Warning: xenon not installed (recommended for strict enforcement)" >&2
    echo "Install with: pip install xenon" >&2
fi

# 1. Check Cyclomatic Complexity with Radon
echo "Checking Cyclomatic Complexity (max $MAX_CYCLOMATIC_COMPLEXITY)..."
CC_OUTPUT=$(radon cc -s -a start_green_stay_green/ 2>&1)

if $VERBOSE; then
    echo "$CC_OUTPUT"
fi

# Check for C, D, E, or F grades (complexity > 10)
if echo "$CC_OUTPUT" | grep -qE "^[[:space:]]*[C-F] "; then
    FAILED_CHECKS+=("Cyclomatic Complexity")
    echo "✗ Cyclomatic Complexity exceeds threshold (max $MAX_CYCLOMATIC_COMPLEXITY)" >&2
    echo "" >&2
    echo "Functions exceeding threshold:" >&2
    echo "$CC_OUTPUT" | grep -E "^[[:space:]]*[C-F] " || true
    echo "" >&2
else
    PASSED_CHECKS+=("Cyclomatic Complexity")
    echo "✓ Cyclomatic Complexity: All functions ≤ $MAX_CYCLOMATIC_COMPLEXITY"
fi

echo ""

# 2. Check Maintainability Index with Radon
echo "Checking Maintainability Index (min $MIN_MAINTAINABILITY_INDEX)..."
MI_OUTPUT=$(radon mi -s start_green_stay_green/ 2>&1)

if $VERBOSE; then
    echo "$MI_OUTPUT"
fi

# Check for C, D, E, or F grades (MI < 20)
if echo "$MI_OUTPUT" | grep -qE "^[[:space:]]*[C-F] "; then
    FAILED_CHECKS+=("Maintainability Index")
    echo "✗ Maintainability Index below threshold (min $MIN_MAINTAINABILITY_INDEX)" >&2
    echo "" >&2
    echo "Modules below threshold:" >&2
    echo "$MI_OUTPUT" | grep -E "^[[:space:]]*[C-F] " || true
    echo "" >&2
else
    PASSED_CHECKS+=("Maintainability Index")
    echo "✓ Maintainability Index: All modules ≥ $MIN_MAINTAINABILITY_INDEX"
fi

echo ""

# 3. Check overall complexity with Xenon (if available)
if command -v xenon &> /dev/null; then
    echo "Checking overall complexity grade (max grade $MAX_COMPLEXITY_GRADE)..."

    # Xenon options:
    # --max-absolute A: Maximum complexity grade (A = 1-5, B = 6-10, C = 11-20)
    # --max-modules A: Maximum average complexity per module
    # --max-average A: Maximum average complexity overall

    if xenon --max-absolute A --max-modules A --max-average A start_green_stay_green/ 2>&1; then
        PASSED_CHECKS+=("Xenon Complexity")
        echo "✓ Xenon: All complexity metrics grade A"
    else
        FAILED_CHECKS+=("Xenon Complexity")
        echo "✗ Xenon complexity checks failed (grade must be A)" >&2
        echo "" >&2
        echo "Run with --verbose to see details, or run directly:" >&2
        echo "  xenon --max-absolute A start_green_stay_green/" >&2
    fi
else
    echo "ℹ Xenon not available (skipping strict grade enforcement)"
fi

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo ""
echo "=== Complexity Analysis Summary ==="
echo "Passed: ${#PASSED_CHECKS[@]}"
echo "Failed: ${#FAILED_CHECKS[@]}"

if $VERBOSE; then
    echo "Execution time: $TOTAL_TIME seconds"
fi

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    echo ""
    echo "Failed checks:"
    for check in "${FAILED_CHECKS[@]}"; do
        echo "  ✗ $check"
    done
    echo ""
    echo "MAXIMUM QUALITY STANDARDS:"
    echo "  - Cyclomatic Complexity: ≤ $MAX_CYCLOMATIC_COMPLEXITY"
    echo "  - Maintainability Index: ≥ $MIN_MAINTAINABILITY_INDEX"
    echo "  - Complexity Grade: $MAX_COMPLEXITY_GRADE"
    echo ""
    echo "To fix:"
    echo "  1. Refactor complex functions"
    echo "  2. Extract helper methods"
    echo "  3. Simplify branching logic"
    echo "  4. Break large functions into smaller ones"
    echo ""
    exit 1
else
    echo ""
    echo "✓ All complexity checks passed (MAXIMUM QUALITY)"
    exit 0
fi
