#!/usr/bin/env bash
# scripts/setup-dev.sh - Set up development environment
# Usage: ./scripts/setup-dev.sh [--verbose] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Set up the development environment.

Setup includes:
  1. Create Python virtual environment
  2. Install dependencies (pip)
  3. Install dev dependencies
  4. Set up pre-commit hooks
  5. Verify installation

OPTIONS:
    --verbose   Show detailed output
    --help      Display this help message

EXIT CODES:
    0           Setup completed successfully
    1           Setup failed
    2           Error during setup

EXAMPLES:
    $(basename "$0")          # Set up dev environment
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

echo "=== Setting Up Development Environment ==="
echo ""

# Check Python availability
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed" >&2
    exit 2
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv || { echo "✗ Failed to create virtual environment" >&2; exit 1; }
    echo "✓ Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate || { echo "✗ Failed to activate virtual environment" >&2; exit 1; }
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip || { echo "✗ Failed to upgrade pip" >&2; exit 1; }
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || { echo "✗ Failed to install dependencies" >&2; exit 1; }
    echo "✓ Dependencies installed"
else
    echo "Warning: requirements.txt not found" >&2
fi
echo ""

# Install development dependencies
echo "Installing development dependencies..."
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt || { echo "✗ Failed to install dev dependencies" >&2; exit 1; }
    echo "✓ Development dependencies installed"
else
    echo "Warning: requirements-dev.txt not found" >&2
fi
echo ""

# Install package in development mode
echo "Installing package in development mode..."
pip install -e . || { echo "✗ Failed to install package" >&2; exit 1; }
echo "✓ Package installed in development mode"
echo ""

# Set up pre-commit hooks
if command -v pre-commit &> /dev/null; then
    echo "Setting up pre-commit hooks..."
    pre-commit install || { echo "✗ Failed to install pre-commit hooks" >&2; exit 1; }
    echo "✓ Pre-commit hooks installed"
else
    echo "Warning: pre-commit not available, skipping hook setup" >&2
fi
echo ""

# Verify installation
echo "=== Verifying Installation ==="
echo ""

if $VERBOSE; then
    echo "Python version:"
    python --version
    echo ""

    echo "Installed packages:"
    pip list
    echo ""
fi

echo "✓ Development environment setup completed!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Run checks: ./scripts/check-all.sh"
echo "  3. Run tests: ./scripts/test.sh --unit"
echo ""

exit 0
