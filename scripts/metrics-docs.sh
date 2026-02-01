#!/usr/bin/env bash
# scripts/metrics-docs.sh - Output documentation coverage metrics for dashboard
# Usage: ./scripts/metrics-docs.sh
#
# Outputs interrogate results in format expected by scripts/collect_metrics.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Run interrogate with verbose output
# The -v flag provides detailed output including the coverage percentage
interrogate start_green_stay_green/ -v
