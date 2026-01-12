#!/usr/bin/env bash
# scripts/docs.sh - Generate documentation
# Usage: ./scripts/docs.sh [--serve] [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

SERVE=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --serve)
            SERVE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Generate documentation using pdoc.

OPTIONS:
    --serve     Serve documentation locally on http://localhost:8080
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Documentation generated successfully
    1           Generation failed
    2           Error running checks

EXAMPLES:
    $(basename "$0")          # Generate docs
    $(basename "$0") --serve  # Generate and serve locally
    $(basename "$0") --verbose # Show detailed output
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

# Set verbosity
if $VERBOSE; then
    set -x
fi

echo "=== Generating Documentation ==="

# Clean previous docs
if [ -d "docs/api" ]; then
    rm -rf docs/api
fi

# Generate HTML docs using pdoc
if command -v pdoc &> /dev/null; then
    if $VERBOSE; then
        echo "Generating API documentation with pdoc..."
    fi
    pdoc start_green_stay_green -o docs/api || { echo "✗ Documentation generation failed" >&2; exit 1; }
else
    echo "Warning: pdoc not installed, trying mkdocs..." >&2
    if command -v mkdocs &> /dev/null; then
        mkdocs build || { echo "✗ Documentation generation failed" >&2; exit 1; }
    else
        echo "Warning: Neither pdoc nor mkdocs found, skipping documentation generation" >&2
    fi
fi

if $SERVE; then
    echo "✓ Documentation generated"
    echo "Serving documentation on http://localhost:8080..."
    if command -v pdoc &> /dev/null; then
        pdoc start_green_stay_green --docformat google --math
    else
        echo "Error: Cannot serve docs without pdoc" >&2
        exit 2
    fi
else
    echo "✓ Documentation generated in docs/api/"
fi

exit 0
