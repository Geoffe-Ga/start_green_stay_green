#!/usr/bin/env bash
set -euo pipefail
echo "=== Running C# Linters ==="
echo "Running dotnet format..."
dotnet format --verify-no-changes
echo "✓ All linters passed!"
