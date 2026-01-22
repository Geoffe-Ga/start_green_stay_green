#!/usr/bin/env bash
# TypeScript testing script - runs test suite with coverage
set -euo pipefail

echo "=== Running TypeScript Tests ==="

# Run Jest with coverage
npm test -- --coverage --verbose

echo "✓ Tests passed with required coverage!"
