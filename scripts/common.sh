#!/usr/bin/env bash
# scripts/common.sh - Common utilities for quality scripts
# Source this file in other scripts to get venv handling

# Ensure venv with required dependencies
# Usage: ensure_venv
# Sets global variable: TEMP_VENV_CREATED=true if venv was created
ensure_venv() {
    # Check if we're already in a virtual environment
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        if [ "${VERBOSE:-false}" = "true" ]; then
            echo "Using active virtual environment: $VIRTUAL_ENV"
        fi
        return 0
    fi

    # Check if .venv exists
    if [ -d ".venv" ]; then
        if [ "${VERBOSE:-false}" = "true" ]; then
            echo "Activating existing .venv"
        fi
        # shellcheck disable=SC1091
        source .venv/bin/activate
        return 0
    fi

    # Need to create temporary venv
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Creating temporary virtual environment..."
    fi

    TEMP_VENV_DIR=$(mktemp -d)
    TEMP_VENV_CREATED=true
    export TEMP_VENV_DIR TEMP_VENV_CREATED

    python3 -m venv "$TEMP_VENV_DIR" || {
        echo "Error: Failed to create temporary venv" >&2
        return 1
    }

    # shellcheck disable=SC1091
    source "$TEMP_VENV_DIR/bin/activate" || {
        echo "Error: Failed to activate temporary venv" >&2
        return 1
    }

    # Install project and dev dependencies
    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Installing project and dependencies..."
        pip install -q --upgrade pip
        pip install -e . -r requirements-dev.txt
    else
        pip install -q --upgrade pip >/dev/null 2>&1
        pip install -q -e . -r requirements-dev.txt >/dev/null 2>&1
    fi

    if [ "${VERBOSE:-false}" = "true" ]; then
        echo "Temporary venv created and activated"
    fi
}

# Clean up temporary venv if we created one
# Usage: cleanup_venv
cleanup_venv() {
    if [ "${TEMP_VENV_CREATED:-false}" = "true" ] && [ -n "${TEMP_VENV_DIR:-}" ]; then
        if [ "${VERBOSE:-false}" = "true" ]; then
            echo "Cleaning up temporary venv..."
        fi
        deactivate 2>/dev/null || true
        rm -rf "$TEMP_VENV_DIR"
        unset TEMP_VENV_DIR TEMP_VENV_CREATED
    fi
}

# Set up trap to ensure cleanup on exit
setup_cleanup_trap() {
    trap cleanup_venv EXIT INT TERM
}
