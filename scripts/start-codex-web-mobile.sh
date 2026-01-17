#!/usr/bin/env bash
# scripts/start-codex-web-mobile.sh - Configure environment for the web/mobile Codex agent
# Usage: ./scripts/start-codex-web-mobile.sh [OPTIONS] [-- command...]
#   Or:  source ./scripts/start-codex-web-mobile.sh [OPTIONS]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

VERBOSE=false
ENV_NAME="dev"
CONFIG_PATH=""
NO_VENV=false
PRINT_EXPORTS=false
START_SHELL=false
COMMAND=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENV_NAME="${2:-}"
            shift 2
            ;;
        --config)
            CONFIG_PATH="${2:-}"
            shift 2
            ;;
        --no-venv)
            NO_VENV=true
            shift
            ;;
        --print)
            PRINT_EXPORTS=true
            shift
            ;;
        --shell)
            START_SHELL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS] [-- command...]

Configure the environment for the web/mobile Codex agent.

OPTIONS:
    --env NAME      Environment name (default: dev)
    --config PATH   Set SGSG_CONFIG_PATH to PATH
    --no-venv       Skip virtual environment setup
    --print         Print export statements and exit
    --shell         Start an interactive shell with the configured env
    --verbose       Show detailed output
    --help          Display this help message

COMMAND:
    Pass a command after -- to run it with the configured environment.

EXAMPLES:
    $(basename "$0") --shell
    $(basename "$0") --env staging -- --help
    $(basename "$0") --print
    source $(basename "$0") --env dev
EOF
            exit 0
            ;;
        --)
            shift
            COMMAND=("$@")
            break
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

cd "$PROJECT_ROOT"

if $VERBOSE; then
    set -x
fi

# Load optional Codex-specific environment overrides.
if [ -f ".env.codex" ]; then
    # shellcheck disable=SC1091
    source ".env.codex"
fi

if ! $NO_VENV; then
    # shellcheck disable=SC1091
    source "$SCRIPT_DIR/common.sh"
    ensure_venv
    setup_cleanup_trap
fi

export CODEX_AGENT_ROLE="web-mobile"
export SGSG_ENV="$ENV_NAME"
export SGSG_PROJECT_ROOT="$PROJECT_ROOT"

if [ -n "$CONFIG_PATH" ]; then
    export SGSG_CONFIG_PATH="$CONFIG_PATH"
fi

if [ -n "${PYTHONPATH:-}" ]; then
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
else
    export PYTHONPATH="$PROJECT_ROOT"
fi

if $PRINT_EXPORTS; then
    echo "export CODEX_AGENT_ROLE=\"$CODEX_AGENT_ROLE\""
    echo "export SGSG_ENV=\"$SGSG_ENV\""
    echo "export SGSG_PROJECT_ROOT=\"$SGSG_PROJECT_ROOT\""
    if [ -n "${SGSG_CONFIG_PATH:-}" ]; then
        echo "export SGSG_CONFIG_PATH=\"$SGSG_CONFIG_PATH\""
    fi
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "export VIRTUAL_ENV=\"$VIRTUAL_ENV\""
        echo "export PATH=\"$VIRTUAL_ENV/bin:\$PATH\""
    fi
    echo "export PYTHONPATH=\"$PYTHONPATH\""
    exit 0
fi

if [[ ${#COMMAND[@]} -gt 0 ]]; then
    exec "${COMMAND[@]}"
fi

if $START_SHELL; then
    exec "${SHELL:-/bin/bash}"
fi

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    cat << EOF >&2
Environment configured for this process only.
To persist, run: source ./scripts/start-codex-web-mobile.sh
Or start a shell: ./scripts/start-codex-web-mobile.sh --shell
EOF
fi
