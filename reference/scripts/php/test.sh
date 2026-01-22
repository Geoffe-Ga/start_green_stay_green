#!/usr/bin/env bash
# PHP testing script - runs test suite with coverage
set -euo pipefail

echo "=== Running PHP Tests ==="

# Run PHPUnit with coverage
vendor/bin/phpunit --coverage-text --coverage-clover=coverage.xml --coverage-threshold 90

echo "✓ Tests passed with required coverage!"
