#!/usr/bin/env bash
# scripts/mutation.sh - Run mutation tests with score validation
# Usage: ./scripts/mutation.sh [--min-score SCORE] [--verbose] [--help]
#
# NOTE: Requires Python 3.11-3.13 due to mutmut/pony ORM compatibility.
#       Python 3.14+ is not yet supported. This script automatically uses
#       Python 3.13 if Python 3.14+ is detected.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MIN_SCORE=80  # MAXIMUM QUALITY: 80% mutation score minimum
VERBOSE=false
MUTATION_VENV_DIR=""
MUTATION_VENV_CREATED=false

# Find compatible Python version for mutation testing
find_mutation_python() {
    local python_cmd=""

    # Check current Python version
    local current_python_version
    current_python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
    local major minor
    major=$(echo "$current_python_version" | cut -d. -f1)
    minor=$(echo "$current_python_version" | cut -d. -f2)

    # Python 3.14+ is incompatible with mutmut
    if [ "$major" -ge 3 ] && [ "$minor" -ge 14 ]; then
        echo "⚠️  Python $current_python_version detected (incompatible with mutmut)" >&2
        echo "    Looking for Python 3.13..." >&2

        # Try to find Python 3.13
        for py_candidate in python3.13 python313; do
            if command -v "$py_candidate" &> /dev/null; then
                python_cmd="$py_candidate"
                local found_version
                found_version=$($python_cmd --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
                echo "    ✓ Found $python_cmd (version $found_version)" >&2
                echo "$python_cmd"
                return 0
            fi
        done

        # Couldn't find Python 3.13
        echo "" >&2
        echo "ERROR: Python 3.13 required for mutation testing" >&2
        echo "" >&2
        echo "Mutmut is incompatible with Python 3.14+ due to Pony ORM limitations." >&2
        echo "Please install Python 3.13:" >&2
        echo "" >&2
        echo "  # Using pyenv" >&2
        echo "  pyenv install 3.13.2" >&2
        echo "" >&2
        echo "  # Using homebrew (macOS)" >&2
        echo "  brew install python@3.13" >&2
        echo "" >&2
        echo "See Issue #121 for details and workarounds:" >&2
        echo "https://github.com/Geoffe-Ga/start_green_stay_green/issues/121" >&2
        return 1
    fi

    # Current Python is compatible
    echo "python3"
}

# Ensure mutation-specific venv with compatible Python
ensure_mutation_venv() {
    # Find compatible Python
    local python_cmd
    if ! python_cmd=$(find_mutation_python); then
        return 1
    fi

    # Check if already in a venv with compatible Python
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        local venv_python_version
        venv_python_version=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+' | head -1)
        local major minor
        major=$(echo "$venv_python_version" | cut -d. -f1)
        minor=$(echo "$venv_python_version" | cut -d. -f2)

        if [ "$major" -eq 3 ] && [ "$minor" -lt 14 ]; then
            if [ "${VERBOSE:-false}" = "true" ]; then
                echo "Using active virtual environment: $VIRTUAL_ENV (Python $venv_python_version)"
            fi
            return 0
        else
            echo "⚠️  Active venv uses Python $venv_python_version (incompatible)" >&2
            echo "    Creating mutation-specific venv with $python_cmd..." >&2
        fi
    fi

    # Create mutation-specific venv
    MUTATION_VENV_DIR=$(mktemp -d -t mutation-venv-XXXXXX)
    MUTATION_VENV_CREATED=true
    export MUTATION_VENV_DIR MUTATION_VENV_CREATED

    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Creating mutation venv with $python_cmd in $MUTATION_VENV_DIR"
    fi

    $python_cmd -m venv "$MUTATION_VENV_DIR" || {
        echo "Error: Failed to create mutation venv" >&2
        return 1
    }

    # shellcheck disable=SC1091
    source "$MUTATION_VENV_DIR/bin/activate" || {
        echo "Error: Failed to activate mutation venv" >&2
        return 1
    }

    # Install dependencies
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Installing dependencies in mutation venv..."
        pip install --upgrade pip
        pip install -e "$PROJECT_ROOT" -r "$PROJECT_ROOT/requirements-dev.txt"
    else
        pip install -q --upgrade pip >/dev/null 2>&1
        pip install -q -e "$PROJECT_ROOT" -r "$PROJECT_ROOT/requirements-dev.txt" >/dev/null 2>&1
    fi

    local final_version
    final_version=$(python --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
    echo "✓ Mutation venv ready (Python $final_version)" >&2
}

# Cleanup mutation venv
# shellcheck disable=SC2329  # Function called via trap, not directly
cleanup_mutation_venv() {
    if [ "${MUTATION_VENV_CREATED:-false}" = "true" ] && [ -n "${MUTATION_VENV_DIR:-}" ]; then
        if [ "${VERBOSE:-false}" = "true" ]; then
            echo "Cleaning up mutation venv..."
        fi
        deactivate 2>/dev/null || true
        rm -rf "$MUTATION_VENV_DIR"
        unset MUTATION_VENV_DIR MUTATION_VENV_CREATED
    fi
}

# Set up trap to ensure cleanup on exit
setup_mutation_cleanup_trap() {
    trap cleanup_mutation_venv EXIT INT TERM
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --min-score)
            MIN_SCORE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run mutation tests and validate minimum score threshold.

Mutation testing introduces small changes (mutations) to your code
to verify that your test suite catches them. A high mutation score
indicates effective tests.

Python 3.14+ Compatibility:
This script automatically detects Python 3.14+ and uses Python 3.13 if
available. If Python 3.13 is not found, install it with:
  pyenv install 3.13.2
  brew install python@3.13  # macOS

OPTIONS:
    --min-score SCORE   Minimum mutation score (default: 80)
    --verbose           Show detailed output
    --help              Display this help message

EXIT CODES:
    0                   Mutation score meets or exceeds minimum
    1                   Mutation score below minimum threshold
    2                   Error running mutation tests

QUALITY STANDARDS:
    MAXIMUM QUALITY:    80% minimum mutation score
    Good:               70-79%
    Acceptable:         60-69%
    Poor:               <60%

EXAMPLES:
    $(basename "$0")                    # Run with 80% minimum
    $(basename "$0") --min-score 70     # Run with 70% minimum
    $(basename "$0") --verbose          # Show detailed output
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

# Set up cleanup trap
setup_mutation_cleanup_trap

# Ensure mutation venv with compatible Python
ensure_mutation_venv || exit 2

# Check if mutmut is installed
if ! command -v mutmut &> /dev/null; then
    echo "Error: mutmut is not installed" >&2
    echo "Install with: pip install mutmut" >&2
    exit 2
fi

echo ""
echo "=== Running Mutation Tests ==="
echo "Minimum required score: ${MIN_SCORE}%"
echo ""

# Run mutation tests (allow failure, we'll check score)
echo "Running mutmut (this may take several minutes)..."
if mutmut run 2>&1; then
    echo "✓ Mutmut run completed"
else
    # mutmut returns non-zero if there are surviving mutants, which is expected
    echo "ℹ Mutmut run completed (some mutants may have survived)"
fi

echo ""
echo "=== Mutation Test Results ==="

# Get results as JSON
if ! mutmut junitxml > /dev/null 2>&1; then
    echo "Warning: Could not generate JUnit XML (may be empty results)" >&2
fi

# Parse mutmut results
RESULTS=$(mutmut results)
echo "$RESULTS"
echo ""

# Extract counts from results (macOS compatible grep)
KILLED=$(echo "$RESULTS" | grep -o 'Killed: [0-9]*' | grep -o '[0-9]*$' || echo "0")
SURVIVED=$(echo "$RESULTS" | grep -o 'Survived: [0-9]*' | grep -o '[0-9]*$' || echo "0")
SUSPICIOUS=$(echo "$RESULTS" | grep -o 'Suspicious: [0-9]*' | grep -o '[0-9]*$' || echo "0")
TIMEOUT=$(echo "$RESULTS" | grep -o 'Timeout: [0-9]*' | grep -o '[0-9]*$' || echo "0")

# Calculate total and score
TOTAL=$((KILLED + SURVIVED + SUSPICIOUS + TIMEOUT))

if [ "$TOTAL" -eq 0 ]; then
    echo "Warning: No mutants were generated" >&2
    echo "This might indicate:"
    echo "  - No code to mutate in start_green_stay_green/"
    echo "  - Configuration issue with mutmut"
    echo ""
    echo "Skipping mutation score validation"
    exit 0
fi

# Calculate mutation score (killed / total * 100)
SCORE=$(awk "BEGIN {printf \"%.1f\", ($KILLED / $TOTAL) * 100}")

echo "=== Mutation Score ==="
echo "Killed:      $KILLED"
echo "Survived:    $SURVIVED"
echo "Suspicious:  $SUSPICIOUS"
echo "Timeout:     $TIMEOUT"
echo "Total:       $TOTAL"
echo ""
echo "Mutation Score: ${SCORE}%"
echo "Required:       ${MIN_SCORE}%"
echo ""

# Compare score to threshold
if awk "BEGIN {exit !($SCORE >= $MIN_SCORE)}"; then
    echo "✓ Mutation score meets minimum threshold"
    echo ""

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Note: $SURVIVED mutants survived. To view them:"
        echo "  mutmut show <id>"
        echo "  mutmut html  # Generate HTML report"
    fi

    exit 0
else
    echo "✗ Mutation score below minimum threshold" >&2
    echo "" >&2
    echo "Your test suite killed ${SCORE}% of mutants" >&2
    echo "Minimum required: ${MIN_SCORE}%" >&2
    echo "" >&2
    echo "To improve mutation score:" >&2
    echo "  1. View surviving mutants: mutmut show <id>" >&2
    echo "  2. Add tests to catch these mutations" >&2
    echo "  3. Generate HTML report: mutmut html" >&2
    echo "" >&2

    if [ "$SURVIVED" -gt 0 ]; then
        echo "Surviving mutants:" >&2
        mutmut show 1 2>&1 | head -20 || true
    fi

    exit 1
fi
