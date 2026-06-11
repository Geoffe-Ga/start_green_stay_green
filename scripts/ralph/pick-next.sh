#!/usr/bin/env bash
# scripts/ralph/pick-next.sh
#
# Ralph's picker for Start Green Stay Green. Prints the lowest-numbered open
# issue that is a real, unblocked implementation issue. Prints the issue number
# on stdout, or nothing if no eligible issue exists.
#
# Rules (adapted to SGSG label/title conventions):
#   - Open issues only, ascending by number.
#   - EXCLUDE umbrella epics: their title starts with "epic:" (case-insensitive).
#     (SGSG applies `epic:<name>` labels to BOTH umbrellas and their children, so
#     the label cannot distinguish them — the title prefix does.)
#   - EXCLUDE deferred/unactionable labels: `needs-spec`, `future-work`,
#     `blocked`, `wontfix`, `duplicate`, `question`.
#   - EXCLUDE issues that already have an open PR pointing at them
#     (`Closes/Fixes/Resolves #N` in any open PR body, case-insensitive), so
#     Ralph never opens a second PR while iteration is in flight.
#
# Numbering encodes intra-epic dependency order (Foundation < Quality < CI <
# Tests < Docs; windows/multi-agent T1 < T2 < ...), so "lowest eligible" respects
# ordering. Combined with the one-PR-at-a-time orchestrator, a dependency parent
# always merges before its child is picked.
#
# Usage:   scripts/ralph/pick-next.sh
# Exit:    0 — issue number printed (or nothing if backlog empty); 2 — gh missing.
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "pick-next: gh CLI not found" >&2
  exit 2
fi

# Open issues, ascending by number, minus umbrellas and deferred labels.
candidates=$(
  gh issue list \
    --state open \
    --limit 300 \
    --json number,title,labels \
    --jq '
      sort_by(.number)
      | map(select(
          (.title | test("^\\s*epic:";"i")) | not
        ))
      | map(select(
          ([.labels[].name]
            | any(. == "needs-spec" or . == "future-work" or . == "blocked"
                  or . == "wontfix" or . == "duplicate" or . == "question")
          ) | not
        ))
      | .[].number
    '
)

if [[ -z "$candidates" ]]; then
  exit 0
fi

# Issue numbers already addressed by an open PR (any author).
inflight=$(
  gh pr list \
    --state open \
    --limit 200 \
    --json body \
    --jq '.[].body' \
  | grep -oiE '(closes|fixes|resolves)[[:space:]]+#[0-9]+' \
  | grep -oE '[0-9]+' \
  | sort -u || true
)

# Print the lowest candidate that isn't already in-flight.
while IFS= read -r n; do
  [[ -z "$n" ]] && continue
  if [[ -z "$inflight" ]] || ! grep -qx "$n" <<<"$inflight"; then
    echo "$n"
    exit 0
  fi
done <<<"$candidates"

# No eligible issue (all open ones already have PRs in flight, or backlog drained).
exit 0
