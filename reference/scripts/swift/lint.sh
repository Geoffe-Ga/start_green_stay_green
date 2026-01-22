#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Swift Linters ==="
echo "Running SwiftLint..."
swiftlint lint --strict
echo "Running SwiftFormat..."
swiftformat --lint .
echo "✓ All linters passed!"
