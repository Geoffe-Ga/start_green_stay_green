#!/usr/bin/env bash
set -euo pipefail
echo "=== Running C# Tests ==="
dotnet test /p:CollectCoverage=true /p:Threshold=90 /p:ThresholdType=line
echo "✓ Tests passed with required coverage!"
