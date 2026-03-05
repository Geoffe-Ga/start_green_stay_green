#!/usr/bin/env bash
# scripts/metrics-docs.sh - Output documentation coverage metrics for dashboard
# Usage: ./scripts/metrics-docs.sh
#
# Computes docstring coverage percentage using ruff D rules and AST item count.
# Outputs in format expected by scripts/collect_metrics.py: "RESULT: XX.X%"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Count ruff D violations (missing/malformed docstrings)
violations=$(ruff check --select D start_green_stay_green/ --output-format json 2>/dev/null | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

# Count total docstring-eligible items (modules, classes, public functions/methods)
total=$(python3 -c "
import ast, pathlib
total = 0
for f in pathlib.Path('start_green_stay_green').rglob('*.py'):
    try:
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if isinstance(node, ast.Module) or not node.name.startswith('_') or node.name == '__init__':
                    total += 1
    except SyntaxError:
        pass
print(total)
")

if [ "$total" -eq 0 ]; then
    coverage="100.0"
else
    coverage=$(python3 -c "print(round(($total - $violations) / $total * 100, 1))")
fi

echo "RESULT: ${coverage}%"
