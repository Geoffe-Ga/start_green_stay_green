#!/usr/bin/env bash
# scripts/verify_release_readiness.sh - Automated v1.0.0 release-readiness checks (#152)
#
# Thin wrapper around scripts/verify_release_readiness.py. Generates a Python
# project offline via the public `sgsg` CLI and asserts the automatable
# structural release-readiness criteria from the v1.0.0 manual testing plan.
#
# Usage: ./scripts/verify_release_readiness.sh [--keep] [--help]
#
# Exit codes:
#   0  All automatable release-readiness checks passed.
#   1  One or more checks failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat <<'EOF'
Usage: ./scripts/verify_release_readiness.sh [--keep] [--help]

Run automated v1.0.0 release-readiness verification (#152). Generates a Python
project offline via the `sgsg` CLI and asserts critical files, executable
scripts, pre-commit hook count, CI workflow validity, and live dashboard
artifacts.

Options:
  --keep    Keep the generated temporary project for inspection.
  --help    Show this help message and exit.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --help|-h)
            usage
            exit 0
            ;;
    esac
done

exec python3 "$SCRIPT_DIR/verify_release_readiness.py" "$@"
