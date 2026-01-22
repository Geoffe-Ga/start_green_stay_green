#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Ruby Tests ==="
bundle exec rspec --format documentation --require simplecov --minimum-coverage 90
echo "✓ Tests passed with required coverage!"
