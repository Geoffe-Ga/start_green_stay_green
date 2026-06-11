#!/usr/bin/env bash
set -euo pipefail
echo "=== Running C# Tests ==="
# /p:CollectCoverage=true activates the Coverlet gate; the >=90% line
# bound lives in the csproj (Threshold/ThresholdType/ThresholdStat —
# its single home), so this invocation enforces it without restating
# the number.
dotnet test /p:CollectCoverage=true
echo "✓ Tests passed with required coverage!"
