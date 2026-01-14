#!/usr/bin/env bash
# scripts/security.sh - Run security checks with Bandit and Safety
# Usage: ./scripts/security.sh [--full] [--verbose] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FULL=false
VERBOSE=false
START_TIME=$(date +%s)

# Source common utilities
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL=true
            shift
            ;;
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

Run security checks using Bandit and Safety.

OPTIONS:
    --full      Run comprehensive security scan
    --verbose   Show detailed output
    --version   Show version and exit
    --help      Display this help message

EXIT CODES:
    0           No security issues found
    1           Security issues found
    2           Error running checks

EXAMPLES:
    $(basename "$0")             # Run basic security checks
    $(basename "$0") --full      # Run comprehensive scan
    $(basename "$0") --verbose   # Show detailed output
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

echo "=== Security Checks (Bandit) ==="

SEC_START=$(date +%s)

# Run Bandit
if $VERBOSE; then
    echo "Running Bandit security scanner..."
fi
bandit -r start_green_stay_green/ 2>/tmp/bandit-stderr.txt || {
    echo "✗ Bandit found issues" >&2
    exit 1
}

echo "=== Security Checks (Safety) ==="

# Run Safety with policy file
if $VERBOSE; then
    echo "Running Safety dependency checker..."
fi
if [ -f "$PROJECT_ROOT/.safety-policy.yml" ]; then
    safety check --policy-file "$PROJECT_ROOT/.safety-policy.yml" 2>/tmp/safety-stderr.txt || {
        echo "✗ Safety found issues" >&2
        exit 1
    }
else
    safety check 2>/tmp/safety-stderr.txt || {
        echo "✗ Safety found issues" >&2
        exit 1
    }
fi

if $FULL; then
    echo "=== Comprehensive Security Scan ==="

    # Check for hardcoded secrets
    if command -v detect-secrets &> /dev/null; then
        if $VERBOSE; then
            echo "Running detect-secrets scan..."
        fi
        detect-secrets scan . 2>/tmp/detect-secrets-stderr.txt || true
    fi
fi

SEC_END=$(date +%s)
SEC_TIME=$((SEC_END - SEC_START))
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

echo "✓ Security checks passed"
if $VERBOSE; then
    echo "Security check execution time: $SEC_TIME seconds"
fi
exit 0
