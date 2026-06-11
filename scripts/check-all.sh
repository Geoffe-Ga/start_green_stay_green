#!/usr/bin/env bash
# scripts/check-all.sh - Thin POSIX delegate to the cross-platform gate runner (#382).
#
# All gate logic lives in start_green_stay_green/gates/ (one canonical
# implementation, DRY). This wrapper only bootstraps a virtualenv via
# scripts/common.sh so an interpreter with the package installed is on
# PATH, then hands every argument to the runner:
#
#   python -m start_green_stay_green.gates check-all [args...]
#
# Usage: ./scripts/check-all.sh [args...]   (see --help for options)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"
setup_cleanup_trap
ensure_venv || exit 2

python -m start_green_stay_green.gates check-all "$@"
