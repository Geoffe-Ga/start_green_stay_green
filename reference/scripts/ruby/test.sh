#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Ruby Tests ==="
# COVERAGE=true activates the SimpleCov gate; the >=90% line bound
# lives in spec/spec_helper.rb (its single home), so this invocation
# enforces it without restating the number — parity with the generated
# scripts/test.sh and reference/ci/ruby.yml. SimpleCov's at_exit hook
# fails the rspec run directly when the bound is missed.
COVERAGE=true bundle exec rspec --format documentation
echo "✓ Tests passed with required coverage!"
