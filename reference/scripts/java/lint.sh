#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Java Linters ==="
echo "Running Checkstyle..."
mvn checkstyle:check
echo "Running PMD..."
mvn pmd:check
echo "Running SpotBugs..."
# SpotBugs reads bytecode; without compiled classes `mvn spotbugs:check`
# silently passes, so compile first.
mvn compile spotbugs:check
echo "✓ All linters passed!"
