#!/usr/bin/env bash
# scripts/test.sh - Run tests with Pytest
# Usage: ./scripts/test.sh [--unit|--integration|--e2e|--all] [--coverage] [--mutation] [--verbose] [--json] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

TEST_TYPE="unit"
COVERAGE=false
MUTATION=false
VERBOSE=false
JSON_OUTPUT=false
METRICS_OUTPUT=false
CI_MODE=false
START_TIME=$(date +%s)

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --metrics)
            METRICS_OUTPUT=true
            shift
            ;;
        --unit)
            TEST_TYPE="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --mutation)
            MUTATION=true
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
        --ci)
            CI_MODE=true
            shift
            ;;
        --version)
            echo "$(basename "$0") version $VERSION"
            exit 0
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run tests using Pytest.

OPTIONS:
    --unit          Run unit tests only (default)
    --integration   Run integration tests only
    --e2e           Run end-to-end tests only
    --all           Run all test types
    --coverage      Generate coverage report
    --mutation      Run mutation tests
    --ci            CI mode: skip flaky_in_ci tests
    --verbose       Show detailed output
    --json          Output results in JSON format
    --version       Show version and exit
    --help          Display this help message

EXIT CODES:
    0               All tests passed
    1               Test failures
    2               Error running tests

EXAMPLES:
    $(basename "$0")                     # Run unit tests
    $(basename "$0") --all               # Run all tests
    $(basename "$0") --unit --coverage   # Unit tests with coverage
    $(basename "$0") --mutation          # Run mutation tests
    $(basename "$0") --json              # JSON output
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

# Machine-readable metrics mode
if $METRICS_OUTPUT; then
    TEST_OUT=$(pytest -m "not integration and not e2e" -q --tb=no tests/ 2>&1 || true)
    # Parse pytest summary line like "X passed, Y failed, Z skipped in N.NNs"
    python3 -c "
import re, json, sys
text = sys.stdin.read()
# Match summary: '123 passed, 4 failed, 5 skipped in 12.34s'
passed = len(re.findall(r'(\d+) passed', text))
failed_m = re.search(r'(\d+) failed', text)
skipped_m = re.search(r'(\d+) skipped', text)
passed_m = re.search(r'(\d+) passed', text)
duration_m = re.search(r'in ([0-9.]+)s', text)

total_passed = int(passed_m.group(1)) if passed_m else 0
total_failed = int(failed_m.group(1)) if failed_m else 0
total_skipped = int(skipped_m.group(1)) if skipped_m else 0
total = total_passed + total_failed + total_skipped
duration = float(duration_m.group(1)) if duration_m else 0.0

print(json.dumps({
    'tests_total': total,
    'tests_passed': total_passed,
    'tests_failed': total_failed,
    'tests_skipped': total_skipped,
    'duration_seconds': duration,
}))
" <<< "$TEST_OUT"
    exit 0
fi

# Build pytest arguments
PYTEST_ARGS=(-v)

if ! $JSON_OUTPUT; then
    case "$TEST_TYPE" in
        unit)
            echo "=== Running Unit Tests ==="
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "not integration and not e2e and not flaky_in_ci")
                echo "CI mode: Skipping flaky_in_ci tests"
            else
                PYTEST_ARGS+=(-m "not integration and not e2e")
            fi
            ;;
        integration)
            echo "=== Running Integration Tests ==="
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "integration and not flaky_in_ci")
                echo "CI mode: Skipping flaky_in_ci tests"
            else
                PYTEST_ARGS+=(-m "integration")
            fi
            ;;
        e2e)
            echo "=== Running End-to-End Tests ==="
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "e2e and not flaky_in_ci")
                echo "CI mode: Skipping flaky_in_ci tests"
            else
                PYTEST_ARGS+=(-m "e2e")
            fi
            ;;
        all)
            echo "=== Running All Tests ==="
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "not flaky_in_ci")
                echo "CI mode: Skipping flaky_in_ci tests"
            fi
            ;;
    esac
else
    case "$TEST_TYPE" in
        unit)
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "not integration and not e2e and not flaky_in_ci")
            else
                PYTEST_ARGS+=(-m "not integration and not e2e")
            fi
            ;;
        integration)
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "integration and not flaky_in_ci")
            else
                PYTEST_ARGS+=(-m "integration")
            fi
            ;;
        e2e)
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "e2e and not flaky_in_ci")
            else
                PYTEST_ARGS+=(-m "e2e")
            fi
            ;;
        all)
            if $CI_MODE; then
                PYTEST_ARGS+=(-m "not flaky_in_ci")
            fi
            ;;
    esac
fi

# Add coverage if requested
if $COVERAGE; then
    if ! $JSON_OUTPUT; then
        echo "Coverage enabled"
    fi
    PYTEST_ARGS+=(
        --cov=start_green_stay_green
        --cov-branch
        --cov-report=term-missing
        --cov-report=html
        --cov-report=xml
        --cov-fail-under=90
    )
fi

# Add JSON output if requested
if $JSON_OUTPUT; then
    PYTEST_ARGS+=(--json-report --json-report-file=/tmp/pytest-report.json)
fi

# Run tests
TEST_START=$(date +%s)
if $VERBOSE; then
    if ! $JSON_OUTPUT; then
        echo "Running pytest with args: ${PYTEST_ARGS[*]}"
    fi
fi

pytest "${PYTEST_ARGS[@]}" tests/ 2>/tmp/pytest-stderr.txt || {
    TEST_END=$(date +%s)
    TEST_TIME=$((TEST_END - TEST_START))
    END_TIME=$(date +%s)
    TOTAL_TIME=$((END_TIME - START_TIME))

    if $JSON_OUTPUT; then
        echo "{\"status\": \"fail\", \"duration_seconds\": $TOTAL_TIME, \"test_duration\": $TEST_TIME}"
    else
        echo "✗ Tests failed" >&2
        # Output stderr to help debug the failure
        if [ -f /tmp/pytest-stderr.txt ]; then
            echo "=== Pytest stderr output ===" >&2
            cat /tmp/pytest-stderr.txt >&2
        fi
    fi
    exit 1
}

TEST_END=$(date +%s)
TEST_TIME=$((TEST_END - TEST_START))
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

if $JSON_OUTPUT; then
    # Output JSON format
    echo "{\"status\": \"pass\", \"duration_seconds\": $TOTAL_TIME, \"test_duration\": $TEST_TIME}"
else
    echo "✓ Tests passed"
    if $VERBOSE; then
        echo "Test execution time: $TEST_TIME seconds"
    fi
fi

# Run mutation tests if requested
if $MUTATION; then
    if ! $JSON_OUTPUT; then
        echo "=== Running Mutation Tests ==="
    fi
    "$SCRIPT_DIR/mutation.sh" || {
        if ! $JSON_OUTPUT; then
            echo "✗ Mutation tests failed" >&2
        fi
        exit 1
    }
fi

exit 0
