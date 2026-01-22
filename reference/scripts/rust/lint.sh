#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Rust Linters ==="
echo "Running rustfmt..."
cargo fmt -- --check
echo "Running clippy..."
cargo clippy -- -D warnings
echo "✓ All linters passed!"
