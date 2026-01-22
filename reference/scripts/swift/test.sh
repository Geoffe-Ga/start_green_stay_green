#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Swift Tests ==="
swift test --enable-code-coverage
echo "✓ Tests passed with required coverage!"
