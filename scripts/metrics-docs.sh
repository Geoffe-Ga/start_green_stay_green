#!/usr/bin/env bash
# scripts/metrics-docs.sh - Output documentation coverage metrics for dashboard
# Usage: ./scripts/metrics-docs.sh
#
# Outputs pydocstyle / ruff D results in format expected by scripts/collect_metrics.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Run pydocstyle for docstring coverage checking
pydocstyle start_green_stay_green/ --count 2>&1 || true
