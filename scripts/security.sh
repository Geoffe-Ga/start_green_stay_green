#!/usr/bin/env bash
# scripts/security.sh - Run security checks with Bandit and pip-audit
# Usage: ./scripts/security.sh [--full] [--verbose] [--version] [--help]

set -euo pipefail

VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FULL=false
VERBOSE=false
METRICS_OUTPUT=false
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

Run security checks using Bandit and pip-audit.

OPTIONS:
    --full      Run comprehensive security scan
    --metrics   Output machine-readable JSON metrics to stdout
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

# Machine-readable metrics mode
if $METRICS_OUTPUT; then
    BANDIT_JSON=$(bandit -r start_green_stay_green/ -ll -f json 2>/dev/null || true)
    ISSUES=$(echo "$BANDIT_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('results',[])))" 2>/dev/null || echo "0")
    if [ "$ISSUES" = "0" ]; then
        echo '{"bandit_issues": 0, "status": "pass"}'
    else
        echo "{\"bandit_issues\": $ISSUES, \"status\": \"fail\"}"
    fi
    exit 0
fi

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

echo "=== Security Checks (pip-audit) ==="

# Run pip-audit for dependency vulnerability scanning
if $VERBOSE; then
    echo "Running pip-audit dependency checker..."
fi

# Build ignore flags for known transitive dependency vulnerabilities
# that cannot be fixed (no fix available or deprecated transitive deps).
# Each entry should have a corresponding tracking issue.
PIP_AUDIT_ARGS=()
if [ -f "$PROJECT_ROOT/.pip-audit-known-vulnerabilities" ]; then
    while IFS= read -r line; do
        # Strip inline comments and trim whitespace
        vuln_id="${line%%#*}"
        vuln_id="${vuln_id%"${vuln_id##*[![:space:]]}"}"
        # Skip empty lines
        [[ -z "$vuln_id" ]] && continue
        PIP_AUDIT_ARGS+=(--ignore-vuln "$vuln_id")
    done < "$PROJECT_ROOT/.pip-audit-known-vulnerabilities"
fi

pip-audit "${PIP_AUDIT_ARGS[@]}" 2>/tmp/pip-audit-stderr.txt || {
    echo "✗ pip-audit found issues" >&2
    exit 1
}

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
    echo "Total execution time: $TOTAL_TIME seconds"
fi
exit 0
