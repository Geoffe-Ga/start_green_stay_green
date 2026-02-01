#!/usr/bin/env bash
# scripts/metrics-complexity.sh - Output complexity metrics for dashboard
# Usage: ./scripts/metrics-complexity.sh
#
# Outputs radon complexity in format expected by scripts/collect_metrics.py
# Expected format: "Average complexity: A (4.5)"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Run radon and output results
# The -a flag shows average complexity in the format we need
radon cc start_green_stay_green/ -a
