#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Ruby Linters ==="
echo "Running RuboCop..."
bundle exec rubocop
echo "Running Reek..."
bundle exec reek
echo "Running Brakeman..."
bundle exec brakeman --no-pager
echo "✓ All linters passed!"
