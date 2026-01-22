#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Java Tests ==="
mvn clean test jacoco:report
mvn jacoco:check
echo "✓ Tests passed with required coverage!"
