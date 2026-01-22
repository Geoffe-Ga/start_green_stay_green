#!/usr/bin/env bash
set -euo pipefail
echo "=== Running Rust Tests ==="
cargo tarpaulin --out Xml --output-dir ./ --fail-under 90
echo "✓ Tests passed with required coverage!"
