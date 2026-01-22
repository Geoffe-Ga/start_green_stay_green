#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Java Linters ==="
echo "Running Checkstyle..."
mvn checkstyle:check
echo "Running PMD..."
mvn pmd:check
echo "Running SpotBugs..."
mvn spotbugs:check
echo "✓ All linters passed!"
