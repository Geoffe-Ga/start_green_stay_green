#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Ruby Linters ==="
# RuboCop's full cop set IS the lint gate: Lint/Style departments, the
# Metrics/CyclomaticComplexity <=10 ceiling, and the Security cops all
# live in .rubocop.yml (the single home of the policy), so this
# invocation restates none of it — parity with the generated
# scripts/lint.sh and reference/ci/ruby.yml. Reek and Brakeman are
# deliberately absent: neither gem is in the generated Gemfile, and
# Brakeman is Rails-specific (it errors on plain-Ruby projects) — add
# them to the Gemfile first if the project adopts them.
echo "Running RuboCop..."
bundle exec rubocop --force-exclusion
echo "✓ All linters passed!"
