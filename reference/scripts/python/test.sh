#!/usr/bin/env bash
# Python testing script - runs test suite with coverage
set -euo pipefail

echo "=== Running Python Tests ==="

# Run pytest with coverage
pytest \
  --cov=src \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-report=xml \
  --cov-fail-under=90 \
  -v

echo "✓ Tests passed with required coverage!"
