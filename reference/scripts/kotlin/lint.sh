#!/usr/bin/env bash
# Kotlin linting script - runs all configured linters
set -euo pipefail

echo "=== Running Kotlin Linters ==="

# ktlint - Kotlin linter
echo "Running ktlint..."
./gradlew ktlintCheck

# detekt - Static code analysis
echo "Running detekt..."
./gradlew detekt

echo "✓ All linters passed!"
