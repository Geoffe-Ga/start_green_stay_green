#!/usr/bin/env bash
# scripts/audit-deps.sh - Dependency audit and update check
# Usage: ./scripts/audit-deps.sh [--fix] [--outdated] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
OUTDATED=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX=true
            shift
            ;;
        --outdated)
            OUTDATED=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Audit project dependencies for vulnerabilities and outdated packages.

OPTIONS:
    --fix       Update dependencies to latest safe versions
    --outdated  Show outdated packages
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           No vulnerabilities found
    1           Vulnerabilities or outdated packages found
    2           Error during audit

EXAMPLES:
    $(basename "$0")            # Audit dependencies
    $(basename "$0") --outdated # Show outdated packages
    $(basename "$0") --fix      # Update dependencies
    $(basename "$0") --verbose  # Show detailed output
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

echo "=== Dependency Audit ==="

# Check for vulnerabilities using Safety
if $VERBOSE; then
    echo "Checking for known vulnerabilities..."
fi
safety check || { echo "✗ Vulnerabilities found" >&2; exit 1; }

# Check for outdated packages
if $OUTDATED || $VERBOSE; then
    echo ""
    echo "=== Checking for Outdated Packages ==="
    if command -v pip-audit &> /dev/null; then
        pip-audit || true
    elif command -v pip-outdated &> /dev/null; then
        pip list --outdated || true
    else
        if $VERBOSE; then
            echo "Note: pip-audit or pip-outdated not available"
        fi
    fi
fi

# Update dependencies if requested
if $FIX; then
    echo ""
    echo "=== Updating Dependencies ==="
    if $VERBOSE; then
        echo "Upgrading all packages to latest safe versions..."
    fi
    pip install --upgrade pip
    pip install --upgrade -r requirements.txt || { echo "✗ Update failed" >&2; exit 1; }
    pip install --upgrade -r requirements-dev.txt || { echo "✗ Dev dependencies update failed" >&2; exit 1; }
fi

echo "✓ Dependency audit completed"
exit 0
