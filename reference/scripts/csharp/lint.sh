#!/usr/bin/env bash
set -euo pipefail
echo "=== Running C# Linters ==="
echo "Running dotnet format..."
dotnet format --verify-no-changes
# All Roslyn analysis (CA rules, the CA1502 complexity ceiling,
# SecurityCodeScan) runs inside the compiler with warnings as errors
# per the csproj, so the build IS the analyzer gate — without it the
# lint script could never see an analyzer finding.
echo "Running Roslyn analyzers (dotnet build)..."
dotnet build --nologo
echo "✓ All linters passed!"
