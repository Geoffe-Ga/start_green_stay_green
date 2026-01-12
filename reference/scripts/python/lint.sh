#!/usr/bin/env bash
# Python linting script - runs all configured linters
set -euo pipefail

echo "=== Running Python Linters ==="

# Ruff - Fast linter
echo "Running Ruff..."
ruff check .

# Black - Code formatter check
echo "Checking Black formatting..."
black --check .

# isort - Import sorting check
echo "Checking isort..."
isort --check-only .

# MyPy - Type checking
echo "Running MyPy type checks..."
mypy .

# Pylint - Code quality
echo "Running Pylint..."
pylint src/ tests/

# Pydocstyle - Docstring conventions
echo "Checking docstring style..."
pydocstyle src/

echo "✓ All linters passed!"
