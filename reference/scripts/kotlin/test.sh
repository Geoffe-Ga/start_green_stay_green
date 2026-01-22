#!/usr/bin/env bash
# Kotlin testing script - runs test suite with coverage
set -euo pipefail

echo "=== Running Kotlin Tests ==="

# Run Gradle tests with JaCoCo coverage
./gradlew test jacocoTestReport jacocoTestCoverageVerification

echo "✓ Tests passed with required coverage!"
