#!/usr/bin/env bash
# collect-evidence.sh — read-only slop-evidence collector for the de-slopify skill.
#
# Runs the repo's existing static-analysis toolbox plus grep heuristics and
# writes every raw result into an output directory. It NEVER modifies tracked
# files and NEVER fails the run because a single tool is missing or unhappy —
# each tool's exit status is captured, not propagated, so the agent always gets
# a complete evidence bundle to corroborate against.
#
# Usage:
#   scripts/collect-evidence.sh [OUTPUT_DIR]
#
# OUTPUT_DIR defaults to "$SCRATCHPAD/deslop-evidence" if SCRATCHPAD is set,
# else a mktemp dir. The chosen directory is printed on the last line so a
# caller can capture it:  EVID=$(scripts/collect-evidence.sh | tail -1)
#
# Exit codes: 0 always (collection is best-effort). 2 only on a setup error
# (no git repo / cannot create output dir).

set -uo pipefail

# --- locate the repo root (this script lives in .claude/skills/de-slopify/scripts) ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
if [[ ! -d "$REPO_ROOT/.git" ]]; then
  echo "collect-evidence: not a git repo at $REPO_ROOT" >&2
  exit 2
fi
cd "$REPO_ROOT" || exit 2

# --- output dir ---
OUT="${1:-${SCRATCHPAD:+$SCRATCHPAD/deslop-evidence}}"
if [[ -z "$OUT" ]]; then
  OUT="$(mktemp -d)"
fi
if ! mkdir -p "$OUT"; then
  echo "collect-evidence: cannot create output dir $OUT" >&2
  exit 2
fi

BACKEND="backend"
FRONTEND="frontend"
PY_SRC="$BACKEND/src"
TS_SRC="$FRONTEND/src"

log() { echo ">>> $*" >&2; }

# Activate the project venv if present (so backend tools resolve).
if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

# run <outfile> <cmd...> — run a tool, capture stdout+stderr and exit code,
# never abort the script. Skips gracefully if the binary is absent.
run() {
  local out="$1"; shift
  local bin="$1"
  if ! command -v "$bin" >/dev/null 2>&1; then
    echo "SKIPPED: $bin not installed" >"$OUT/$out"
    log "skip $bin (not installed)"
    return 0
  fi
  log "run $*"
  if "$@" >"$OUT/$out" 2>&1; then
    echo "[exit 0]" >>"$OUT/$out"
  else
    echo "[exit $?]" >>"$OUT/$out"
  fi
  return 0
}

# ----------------------------------------------------------------------------
# Backend (Python) — read-only analysis
# ----------------------------------------------------------------------------
if [[ -d "$PY_SRC" ]]; then
  run ruff.json            ruff check "$PY_SRC" --config="$BACKEND/pyproject.toml" --output-format=json
  run vulture.txt          vulture "$PY_SRC" --min-confidence 80
  run radon-cc.txt         radon cc "$PY_SRC" -s -n C
  run radon-mi.txt         radon mi "$PY_SRC" -s
  run mypy.txt             mypy "$PY_SRC" --config-file="$BACKEND/pyproject.toml"
  run bandit.json          bandit -r "$PY_SRC" -f json -c "$BACKEND/.bandit"
  run interrogate.txt      interrogate "$PY_SRC" -v
  run pip-audit.txt        pip-audit -r "$BACKEND/requirements.txt"
  run detect-secrets.txt   detect-secrets scan "$PY_SRC"
fi

# ----------------------------------------------------------------------------
# Frontend (TypeScript) — read-only analysis
# ----------------------------------------------------------------------------
if [[ -d "$TS_SRC" ]]; then
  # eslint and tsc are run via the frontend dir; capture but never abort.
  ( cd "$FRONTEND" && command -v npx >/dev/null 2>&1 \
      && npx --no-install eslint . -f json ) >"$OUT/eslint.json" 2>&1 \
      || echo "[eslint unavailable or reported issues — inspect output]" >>"$OUT/eslint.json"
  ( cd "$FRONTEND" && command -v npx >/dev/null 2>&1 \
      && npx --no-install tsc -p tsconfig.json --noEmit ) >"$OUT/tsc.txt" 2>&1 \
      || echo "[tsc reported issues — inspect output]" >>"$OUT/tsc.txt"
fi

# ----------------------------------------------------------------------------
# Cross-cutting grep heuristics (candidates only — need a 2nd signal)
# ----------------------------------------------------------------------------
GREP_BIN="grep"
GREP_FLAGS=(-rnE)
if command -v rg >/dev/null 2>&1; then
  GREP_BIN="rg"
  GREP_FLAGS=(-n)
fi
SEARCH_PATHS=()
[[ -d "$PY_SRC" ]] && SEARCH_PATHS+=("$PY_SRC")
[[ -d "$TS_SRC" ]] && SEARCH_PATHS+=("$TS_SRC")

greps() {
  local out="$1" pat="$2"
  if [[ ${#SEARCH_PATHS[@]} -eq 0 ]]; then return 0; fi
  "$GREP_BIN" "${GREP_FLAGS[@]}" "$pat" "${SEARCH_PATHS[@]}" >"$OUT/$out" 2>/dev/null \
    || echo "(no matches)" >"$OUT/$out"
}

greps grep-stubs.txt        'NotImplementedError|not implemented|throw new Error\(.?not implemented|return None\s*#\s*TODO|\bpass\s*#\s*(stub|placeholder)'
greps grep-ai-tells.txt     'In a real implementation|real implementation|placeholder|for now|as an AI|should probably'
greps grep-debt.txt         'TODO|FIXME|HACK|XXX'
greps grep-escape-hatch.txt 'type: ?ignore|@ts-ignore|@ts-nocheck|eslint-disable|# ?noqa|cast\(Any'
greps grep-swallow.txt      'except (Exception|BaseException)?\s*:|catch\s*\([^)]*\)\s*\{\s*\}|\.catch\(\(\)\s*=>\s*\{?\s*\}?\)'
greps grep-commented.txt    '^\s*#\s*(def |class |return |if |for |while |import |from )'
greps grep-any.txt          ':\s*any\b|<any>|as any'

# Git churn / hotspots (top 30 most-changed files in the last 90 days).
# PRIORITIZATION SIGNAL ONLY — churn (and reading-targets below) decide which
# area the reading pass starts with; they NEVER decide which areas are skipped.
# Files untouched in 90 days never appear here, so a run anchored to this list
# would never read stable code. Coverage is governed by area-inventory.txt
# (every area must be read each run); this is just the order to read it in.
if command -v git >/dev/null 2>&1; then
  git log --since="90 days ago" --format= --name-only 2>/dev/null \
    | grep -E '^(backend|frontend)/' \
    | sort | uniq -c | sort -rn | head -30 >"$OUT/churn.txt" 2>/dev/null \
    || echo "(churn unavailable)" >"$OUT/churn.txt"
fi

# Reading targets: the largest source files by line count. PRIORITIZATION ONLY
# (same caveat as churn.txt) — together with churn they say where to START
# reading, because size and change-frequency are where bloaters, duplication,
# and god-objects accumulate. They are NOT the coverage set.
{
  echo "# Largest source files (LoC) — prime reading-pass START targets."
  echo "# Prioritization order only; NOT a coverage filter (see area-inventory.txt)."
  if [[ ${#SEARCH_PATHS[@]} -gt 0 ]]; then
    find "${SEARCH_PATHS[@]}" -type f \
      \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) \
      -not -path '*/node_modules/*' -print0 2>/dev/null \
      | xargs -0 wc -l 2>/dev/null | sort -rn | sed '/ total$/d' | head -30
  fi
} >"$OUT/reading-targets.txt"

# ----------------------------------------------------------------------------
# Area inventory — the AUTHORITATIVE coverage set for the reading pass.
# EVERY area listed here MUST be read every run (whole-codebase audit). Churn /
# reading-targets decide the ORDER only. The coverage ledger must enumerate
# every area below and mark it read this run; a "0 findings" verdict is only
# defensible when the ledger covers this entire inventory — never "delta since
# last run". Best-effort + never-fail: missing dirs are simply skipped.
# ----------------------------------------------------------------------------
{
  echo "# Area inventory — the coverage set the reading pass MUST cover in full."
  echo "# Every area must be read each run; churn/reading-targets are order only."
  echo
  echo "## backend routers"
  [[ -d "$PY_SRC/routers" ]] \
    && find "$PY_SRC/routers" -maxdepth 1 -name '*.py' ! -name '__init__.py' 2>/dev/null | sort
  echo
  echo "## backend domain modules"
  [[ -d "$PY_SRC/domain" ]] \
    && find "$PY_SRC/domain" -maxdepth 1 -name '*.py' ! -name '__init__.py' 2>/dev/null | sort
  echo
  echo "## backend services modules"
  [[ -d "$PY_SRC/services" ]] \
    && find "$PY_SRC/services" -maxdepth 1 -name '*.py' ! -name '__init__.py' 2>/dev/null | sort
  echo
  echo "## frontend feature areas"
  [[ -d "$TS_SRC/features" ]] \
    && find "$TS_SRC/features" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort
  echo
  echo "## frontend shared areas"
  for shared in api design components store; do
    [[ -d "$TS_SRC/$shared" ]] && echo "$TS_SRC/$shared"
  done
} >"$OUT/area-inventory.txt"

# ----------------------------------------------------------------------------
# Manifest
# ----------------------------------------------------------------------------
{
  echo "# De-Slop Evidence Bundle"
  echo "Repo:    $REPO_ROOT"
  echo "Out:     $OUT"
  echo
  echo "## Files"
  find "$OUT" -maxdepth 1 -type f -exec basename {} \; | sort | sed 's/^/  - /'
  echo
  echo "Each *.json / *.txt holds raw tool or grep output. Every entry is a"
  echo "CANDIDATE only — apply the Two-Signal Rule from detection-playbook.md"
  echo "before filing anything. Tool exit codes are appended as [exit N]."
  echo
  echo "## IMPORTANT — this bundle is a MAP, not the findings"
  echo "The linter outputs (ruff/mypy/radon/bandit/eslint/tsc) are TABLE STAKES:"
  echo "the repo already passes them in pre-commit and CI, so they cannot be"
  echo "findings. Do NOT file complexity grades, lint rules, or type errors."
  echo "Drive a Task fan-out that READS the source for what linters cannot see"
  echo "(dead/stubbed/orphaned code, duplication, architecture, lying flags,"
  echo "verbosity, comment slop, AI tells, weak tests). That reading pass is the"
  echo "actual audit."
  echo
  echo "## COVERAGE IS MANDATORY AND WHOLE-CODEBASE"
  echo "area-inventory.txt is the AUTHORITATIVE coverage set: the reading pass"
  echo "MUST cover EVERY area in it EVERY run. churn.txt + reading-targets.txt"
  echo "are PRIORITIZATION ORDER ONLY — they say where to start, never which"
  echo "areas to skip. A clean linter bundle or an unchanged file is NOT a reason"
  echo "to skip reading an area. 'Delta-focused' / 'since last run' / 'building on"
  echo "last week's baseline' scoping is FORBIDDEN. A '0 findings' verdict is only"
  echo "valid when the coverage ledger enumerates this entire inventory as read"
  echo "this run."
} >"$OUT/README.txt"

log "evidence collected in $OUT"
echo "$OUT"
