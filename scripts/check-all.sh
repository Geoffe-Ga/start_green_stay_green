#!/usr/bin/env bash
# scripts/check-all.sh - Run all quality checks
# Usage: ./scripts/check-all.sh [--verbose] [--json] [--parallel] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
JSON_OUTPUT=false
PARALLEL=false
START_TIME=$(date +%s)

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run all quality checks in sequence.

Runs:
  1. Linting (Ruff)
  2. Formatting (Black + isort)
  3. Type checking (MyPy)
  4. Security checks (Bandit + Safety)
  5. Complexity analysis (Radon)
  6. Unit tests
  7. Coverage report

OPTIONS:
    --verbose   Show detailed output
    --json      Output results in JSON format
    --parallel  Run independent checks in parallel
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           All checks passed
    1           One or more checks failed
    2           Error running checks

EXAMPLES:
    $(basename "$0")          # Run all checks
    $(basename "$0") --verbose # Show detailed output
    $(basename "$0") --json    # JSON output
    $(basename "$0") --parallel # Run in parallel
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
VERBOSE_FLAG=""
if $VERBOSE; then
    VERBOSE_FLAG="--verbose"
fi

if ! $JSON_OUTPUT; then
    echo "=== Running All Quality Checks ==="
    echo ""
fi

FAILED_CHECKS=()
PASSED_CHECKS=()
declare -A CHECK_TIMES

# Helper function to run a check
run_check() {
    local check_name=$1
    local script=$2
    shift 2
    local args=("$@")

    if ! $JSON_OUTPUT; then
        echo "Running: $check_name"
    fi

    local check_start
    local check_end
    check_start=$(date +%s)
    if "$SCRIPT_DIR/$script" "${args[@]+"${args[@]}"}" $VERBOSE_FLAG; then
        PASSED_CHECKS+=("$check_name")
        if ! $JSON_OUTPUT; then
            echo "✓ $check_name passed"
        fi
    else
        FAILED_CHECKS+=("$check_name")
        if ! $JSON_OUTPUT; then
            echo "✗ $check_name failed" >&2
        fi
    fi
    check_end=$(date +%s)
    CHECK_TIMES["$check_name"]=$((check_end - check_start))

    if ! $JSON_OUTPUT; then
        echo ""
    fi
}

if $PARALLEL; then
    # Run independent checks in parallel
    if ! $JSON_OUTPUT; then
        echo "Running checks in parallel mode..."
        echo ""
    fi

    # Start all parallel checks in background
    "$SCRIPT_DIR/lint.sh" --check $VERBOSE_FLAG >/tmp/lint.log 2>&1 &
    LINT_PID=$!

    "$SCRIPT_DIR/format.sh" --check $VERBOSE_FLAG >/tmp/format.log 2>&1 &
    FORMAT_PID=$!

    "$SCRIPT_DIR/typecheck.sh" $VERBOSE_FLAG >/tmp/typecheck.log 2>&1 &
    TYPE_PID=$!

    "$SCRIPT_DIR/security.sh" $VERBOSE_FLAG >/tmp/security.log 2>&1 &
    SEC_PID=$!

    "$SCRIPT_DIR/complexity.sh" $VERBOSE_FLAG >/tmp/complexity.log 2>&1 &
    COMP_PID=$!

    # Wait for all parallel checks and collect results
    if wait $LINT_PID 2>/dev/null; then
        PASSED_CHECKS+=("Linting")
        if ! $JSON_OUTPUT; then echo "✓ Linting passed"; fi
    else
        FAILED_CHECKS+=("Linting")
        if ! $JSON_OUTPUT; then echo "✗ Linting failed" >&2; fi
    fi
    CHECK_TIMES["Linting"]=0

    if wait $FORMAT_PID 2>/dev/null; then
        PASSED_CHECKS+=("Formatting")
        if ! $JSON_OUTPUT; then echo "✓ Formatting passed"; fi
    else
        FAILED_CHECKS+=("Formatting")
        if ! $JSON_OUTPUT; then echo "✗ Formatting failed" >&2; fi
    fi
    CHECK_TIMES["Formatting"]=0

    if wait $TYPE_PID 2>/dev/null; then
        PASSED_CHECKS+=("Type checking")
        if ! $JSON_OUTPUT; then echo "✓ Type checking passed"; fi
    else
        FAILED_CHECKS+=("Type checking")
        if ! $JSON_OUTPUT; then echo "✗ Type checking failed" >&2; fi
    fi
    CHECK_TIMES["Type checking"]=0

    if wait $SEC_PID 2>/dev/null; then
        PASSED_CHECKS+=("Security checks")
        if ! $JSON_OUTPUT; then echo "✓ Security checks passed"; fi
    else
        FAILED_CHECKS+=("Security checks")
        if ! $JSON_OUTPUT; then echo "✗ Security checks failed" >&2; fi
    fi
    CHECK_TIMES["Security checks"]=0

    if wait $COMP_PID 2>/dev/null; then
        PASSED_CHECKS+=("Complexity analysis")
        if ! $JSON_OUTPUT; then echo "✓ Complexity analysis passed"; fi
    else
        FAILED_CHECKS+=("Complexity analysis")
        if ! $JSON_OUTPUT; then echo "✗ Complexity analysis failed" >&2; fi
    fi
    CHECK_TIMES["Complexity analysis"]=0

    if ! $JSON_OUTPUT; then
        echo ""
    fi

    # Run sequential checks that may depend on parallel ones
    run_check "Unit tests" "test.sh" --unit
    run_check "Coverage report" "coverage.sh"
else
    # Run all checks sequentially
    run_check "Linting" "lint.sh" --check
    run_check "Formatting" "format.sh" --check
    run_check "Type checking" "typecheck.sh"
    run_check "Security checks" "security.sh"
    run_check "Complexity analysis" "complexity.sh"
    run_check "Unit tests" "test.sh" --unit
    run_check "Coverage report" "coverage.sh"
fi

# Calculate total execution time
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

if $JSON_OUTPUT; then
    # Output JSON format
    status="pass"
    if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
        status="fail"
    fi

    # Build JSON output
    json_output='{'
    json_output="$json_output\"status\": \"$status\","
    json_output="$json_output\"duration_seconds\": $TOTAL_TIME,"
    json_output="$json_output\"passed\": ${#PASSED_CHECKS[@]},"
    json_output="$json_output\"failed\": ${#FAILED_CHECKS[@]},"
    json_output="$json_output\"checks\": {"

    first=true
    for check in "${PASSED_CHECKS[@]}"; do
        if [ "$first" = false ]; then json_output="$json_output,"; fi
        json_output="$json_output\"$check\": {\"status\": \"pass\", \"time\": ${CHECK_TIMES[$check]:-0}}"
        first=false
    done

    for check in "${FAILED_CHECKS[@]}"; do
        if [ "$first" = false ]; then json_output="$json_output,"; fi
        json_output="$json_output\"$check\": {\"status\": \"fail\", \"time\": ${CHECK_TIMES[$check]:-0}}"
        first=false
    done

    json_output="$json_output}}"
    echo "$json_output"
else
    echo "=== Quality Checks Summary ==="
    echo "Passed: ${#PASSED_CHECKS[@]}"
    echo "Failed: ${#FAILED_CHECKS[@]}"

    if [ $VERBOSE = true ]; then
        echo "Execution time: $TOTAL_TIME seconds"
    fi

    if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
        echo ""
        echo "Failed checks:"
        for check in "${FAILED_CHECKS[@]}"; do
            echo "  ✗ $check"
        done
    fi
fi

if [ ${#FAILED_CHECKS[@]} -gt 0 ]; then
    exit 1
else
    echo ""
    echo "✓ All quality checks passed!"
    exit 0
fi
