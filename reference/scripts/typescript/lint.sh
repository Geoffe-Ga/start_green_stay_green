#!/usr/bin/env bash
# TypeScript linting script - runs all configured linters
set -euo pipefail

echo "=== Running TypeScript Linters ==="

# ESLint - Linter
echo "Running ESLint..."
npx eslint . --ext .ts,.tsx

# Prettier - Code formatter check
echo "Checking Prettier formatting..."
npx prettier --check "**/*.{ts,tsx}"

# TypeScript compiler - Type checking
echo "Running TypeScript type checks..."
npx tsc --noEmit

echo "✓ All linters passed!"
