#!/usr/bin/env bash
# scripts/metrics-docs.sh - Output documentation coverage metrics for dashboard
# Usage: ./scripts/metrics-docs.sh [--metrics] [--help]
#
# Computes docstring coverage percentage using ruff D rules and AST item count.
# Default output format (consumed as docs-report.txt): "RESULT: XX.X%"
# With --metrics, emits machine-readable JSON for collect_metrics.py:
#   {"docs_coverage_pct": XX.X}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

METRICS_OUTPUT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --metrics)
            METRICS_OUTPUT=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Compute docstring coverage from ruff D rules and an AST item count.

OPTIONS:
    --metrics   Output machine-readable JSON metrics to stdout
    --help      Display this help message

EXIT CODES:
    0           Coverage computed successfully
    2           Error computing coverage
EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Count ruff D violations (missing/malformed docstrings).
# ruff exits non-zero when violations exist; that is expected input here,
# not an error, so capture output without tripping set -e/pipefail.
ruff_json=$(ruff check --select D start_green_stay_green/ --output-format json 2>/dev/null) || true
violations=$(printf '%s' "$ruff_json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

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

if $METRICS_OUTPUT; then
    echo "{\"docs_coverage_pct\": ${coverage}}"
else
    echo "RESULT: ${coverage}%"
fi
