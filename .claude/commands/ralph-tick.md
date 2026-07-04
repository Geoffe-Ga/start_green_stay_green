---
description: One tick of the local Ralph loop for Start Green Stay Green. Re-entrant — reads state from disk and does the next atomic thing across the four gates (TDD → check-all → CI → review → merge).
---

You are Ralph's brain for one tick of Start Green Stay Green's local outer loop.

> Driven by `/loop /ralph-tick` in a caffeinated local Claude Code session at
> the repo root. The `/loop` skill fires you again when your turn ends — either
> by a `Monitor` event on your active PR watch or by a `ScheduleWakeup`. Be
> **re-entrant**: every tick reads state from disk and PR state from GitHub,
> then figures out what to do. Never assume continuity with the previous tick.

## The four gates (and the drop-back rule)
| Gate | Check | On pass | On fail |
| --- | --- | --- | --- |
| 1 | **TDD** (Red→Green→Refactor, `stay-green`) | → Gate 2 | — |
| 2 | **`./scripts/check-all.sh` + `pre-commit run --all-files`** | → push → Gate 3 | **drop to Gate 1** |
| 3 | **CI** all green | → Gate 4 | **drop to Gate 1** (via `ci-debugging`) |
| 4 | **Claude review `## Verdict`** | `LGTM` → **merge + mark issue done** | **drop to Gate 1** (via `address-feedback`) |

"Drop to Gate 1" means: fix the root cause with a failing-test-first cycle,
re-clear Gate 2 locally, push, and climb again. Never weaken a gate to pass it.

This repo's `iteration-trigger.yml` is **comment-only — it does NOT auto-merge**.
It posts a `<!-- iteration-trigger -->` clearance summary, but **the orchestrator
(you) performs the squash-merge** once the reviewer verdict is a fresh `LGTM` and
CI is fully green. Do not wait for a workflow to merge for you — it never will.

---

## Step 0 — Pause check, then read state

```bash
if [ -f scripts/ralph/.paused ]; then echo "paused"; fi
cat scripts/ralph/state.json
```

If `scripts/ralph/.paused` exists: call `ScheduleWakeup` (~1800s, reason "ralph
paused — re-checking later") and end the turn. Do not pick or work.

Otherwise read `state.json` and determine the mode:

| Mode | Trigger | Action |
| --- | --- | --- |
| **A. Backlog drained** | `scripts/ralph/pick-next.sh` empty AND no in-flight Ralph PR | Announce "Backlog drained. Ralph is done." and call `/loop` to **stop** (do not reschedule). |
| **B. In-flight PR** | An open PR exists whose body has `Closes/Fixes/Resolves #N` | Step 2 (branch by gate status). |
| **C. Groom gate** | No in-flight PR AND `completed_since_groom >= groom_interval` | Step 1, then fall through to D. |
| **D. New issue** | No in-flight PR AND counter below threshold | Step 3 (pick + work). |

Detect in-flight Ralph PRs:

```bash
gh pr list --state open --author "@me" --json number,headRefName,body \
  --jq '.[] | select(.body | test("(?i)(closes|fixes|resolves)\\s+#[0-9]+")) | .number'
```

(Dependabot PRs do not carry `Closes #N`, so they are naturally excluded. If
several Ralph PRs are open, process the **lowest-numbered** one this tick; the
loop is re-entrant and cycles the rest on subsequent ticks.)

---

## Step 1 — Groom gate (every Nth tick)

When `completed_since_groom >= groom_interval`:

1. Invoke **`/backlog-grooming`** as a Skill; let it run its full pass — close
   resolved issues, identify gaps, file missing issues. Do not second-guess it.
2. Reset the counter:
   ```bash
   python3 -c "import json,datetime;p='scripts/ralph/state.json';s=json.load(open(p));s['completed_since_groom']=0;s['last_groom_at']=datetime.datetime.now().isoformat();json.dump(s,open(p,'w'),indent=2)"
   ```
3. Commit the state change directly on `main` (state-only changes are not
   load-bearing) and `git push`.
4. Fall through to Step 3.

---

## Step 2 — In-flight PR: branch by gate status

Read the PR once:

```bash
PR_NUM=<the open PR number>
gh pr view "$PR_NUM" --json state,mergeable,mergeStateStatus,headRefOid,commits,statusCheckRollup,comments
```

Identify three things:

- **The latest reviewer verdict.** The `claude-code-review.yml` reviewer posts a
  top-level comment containing a `## Verdict` line (`✅ LGTM` /
  `🔄 CHANGES_REQUESTED` / `💬 COMMENTS`). Match it directly — any comment whose
  body matches `test("Verdict")` — **do not** depend on the `Geoffe-Ga`
  `<!-- iteration-trigger -->` clearance comment, which only mirrors the verdict
  and may be absent (e.g. if its PAT is unset). The clearance comment is a hint,
  never the source of truth.
- **The CI status-check rollup** (pass / fail / pending).
- **The PR state** (open / merged / closed).

**Verdict freshness:** a verdict counts only if its `createdAt` is **after** the
current HEAD commit's `committedDate`. A verdict from before your last push is
stale — treat the PR as "awaiting review" (Step 2e), not LGTM.

### 2a. PR is `MERGED`
Process completion and advance state:
```bash
ISSUE_N=<issue this PR closed>
gh issue view "$ISSUE_N" --json state --jq .state   # expect CLOSED (auto-closed by "Closes #N")
python3 -c "import json;p='scripts/ralph/state.json';s=json.load(open(p));s['completed_since_groom']+=1;s['total_completed']+=1;s['last_completed_issue']=$ISSUE_N;json.dump(s,open(p,'w'),indent=2)"
git checkout main && git pull --ff-only
```
Commit + push the state change on `main`. Clean up the merged branch's worktree
(`git worktree remove ../sgsg-worktrees/<slug>`). Fall through to Step 3.

### 2b. Fresh verdict is `LGTM` AND CI fully green AND PR still `OPEN`
This is the merge action — **you merge** (the workflow won't):
```bash
# If mergeStateStatus is BEHIND (strict branch protection), update first.
# Updating HEAD invalidates the LGTM → re-await a fresh verdict (back to 2e).
if [ "<mergeStateStatus>" = "BEHIND" ]; then
  gh pr update-branch "$PR_NUM"   # then go to Step 4 (re-await fresh verdict on new HEAD)
else
  gh pr merge "$PR_NUM" --squash --delete-branch
fi
```
Only merge when the LGTM is **fresh** (newer than HEAD) AND all required checks
pass. After a successful merge, do the 2a completion block (bump state, checkout
main, remove worktree). Fall through to Step 3.

### 2c. Fresh verdict is `CHANGES_REQUESTED` or `COMMENTS` → drop to Gate 1
Invoke the **`address-feedback`** skill: it parses the verdict, triages
blockers/problems/nits, runs a TDD fix loop (Gate 1), re-clears Gate 2, commits,
pushes, and replies to/resolves threads. When it returns, go to Step 4 (arm the
watch) and end the turn.

### 2d. CI failed (rollup includes a failure on current HEAD) → drop to Gate 1
Invoke the **`ci-debugging`** skill on the failing job. Reproduce locally, fix the
root cause with a failing test first (Gate 1), re-clear Gate 2, push. Never
"pre-existing". Go to Step 4 and end the turn.

### 2e. PR open, no fresh verdict yet, CI in progress
Go to Step 4 (arm the Monitor) and end the turn.

---

## Step 3 — Pick next issue and open a PR

```bash
ISSUE_N=$(scripts/ralph/pick-next.sh)
```

Empty → Mode A (backlog drained): announce and call `/loop` to stop.

Otherwise work the issue per the contract in `scripts/ralph/PROMPT.md` (read it
now, with `$RALPH_ISSUE = $ISSUE_N`): branch in a worktree under
`../sgsg-worktrees/`; **Gate 1** TDD with `stay-green`; **Gate 2**
`./scripts/check-all.sh` then `.venv/bin/pre-commit run --all-files` until both
are clean (`max-quality-no-shortcuts` — no bypasses); conventional commit with
the repo trailer; push; open a PR whose body has `## Summary`, `## Test plan`,
`Closes #$RALPH_ISSUE`, and `Refs #<epic>` if named. You MAY delegate the heavy
build to a subagent that stops at "pre-commit green, ready to PR" and hands the
branch back — **the merge gate stays in this loop**. Then go to Step 4.

If an issue is genuinely blocked (depends on something unbuilt), comment why,
apply the `needs-spec` label via `gh issue edit`, open **no** PR, and end the
turn; next tick the picker skips it.

---

## Step 4 — Arm the watch (Gates 3 & 4) with Monitor, then end the turn

After any push or PR open, watch CI **and** the review verdict with **one**
Monitor that emits on every terminal signal you'd act on, and exits once CI is
terminal AND a verdict is present **or** on any CI failure — so silence never
hides a crashed run. Then end the turn; the Monitor event wakes you and `/loop`
re-enters Step 0.

```bash
# Combined CI + verdict watch for $PR_NUM. Emits each CI check as it reaches a
# terminal bucket and the first Verdict line, then exits when CI is terminal AND
# a verdict exists, or immediately on any CI failure.
# NOTE: gh's --jq accepts ONE filter and does NOT support `jq --arg` — inline
# values into the filter string. Match the reviewer's `## Verdict` directly via
# test("Verdict"); do NOT filter by author login (the verdict may post under the
# review app, not Geoffe-Ga).
PR=$PR_NUM
prev_checks=""; seen_verdict=""
for _ in $(seq 1 60); do            # ~30 min at 30s; Monitor timeout_ms backstops
  roll=$(gh pr checks "$PR" 2>/dev/null) || true
  cur=$(awk -F'\t' '$2!="pending"{print $1": "$2}' <<<"$roll" | sort)
  comm -13 <(printf '%s\n' "$prev_checks") <(printf '%s\n' "$cur") | sed 's/^/CI: /'
  prev_checks="$cur"
  v=$(gh pr view "$PR" --json comments \
        --jq '[.comments[]|select(.body|test("Verdict"))]|last.body // empty' 2>/dev/null) || true
  if [ -n "$v" ] && [ -z "$seen_verdict" ]; then
    seen_verdict=1
    printf 'VERDICT: %s\n' "$(grep -oiE '(LGTM|CHANGES_REQUESTED|COMMENTS)' <<<"$v" | head -1)"
  fi
  if grep -qiE ': (fail|failure|error|cancelled)' <<<"$cur"; then echo "CI: FAILED — drop to Gate 1"; break; fi
  if [ -n "$cur" ] && ! grep -q ': pending' <<<"$roll" && [ -n "$seen_verdict" ]; then echo "READY: ci terminal + verdict present"; break; fi
  sleep 30
done
```

Run it via the **Monitor** tool (e.g. `timeout_ms: 1800000`, `persistent: false`,
description "PR $PR_NUM CI + verdict"). When it emits `CI: FAILED` → next tick
hits 2d; a `CHANGES_REQUESTED`/`COMMENTS` verdict → 2c; `LGTM` + green → 2b. If
the Monitor times out with nothing terminal, `ScheduleWakeup` (~1800s) as the
fallback heartbeat and end the turn.

---

## Hard rules (do not deviate)

- **One issue per tick of work.** Never bundle.
- **Never write to `main` directly** except `scripts/ralph/state.json`.
- **Never force-push. Never `--no-verify`. Never disable a CI check or
  pre-commit hook, and never lower a threshold to pass.** Fix the root cause
  (`max-quality-no-shortcuts`). If a tool is missing for an environmental reason,
  install it.
- **Re-entrancy first.** Read `state.json` + live PR state at the top of every
  tick. Never assume the previous tick succeeded.
- **Worktrees in `../sgsg-worktrees/` only.** Operate from project root; never
  `cd` into committing.
- **End the turn after each atomic action.** Monitor is the preferred wake
  signal; `ScheduleWakeup` (~30 min) is the fallback.
- **On merge, mark the issue done** (Step 2a/2b) and bump `state.json`.

## Anti-bypass (verbatim, non-negotiable — Python edition)
> No bypasses. Do not add `# noqa`, `# type: ignore`, `# pylint: disable`,
> `@pytest.mark.skip`, or `git commit --no-verify`; do not lower coverage /
> complexity / docstring thresholds in `pyproject.toml` or the scripts; do not
> delete tests or code to make a metric pass; do not swallow exceptions to
> silence a linter. Fix the root cause. The only allowed escape hatch is an
> inline `# noqa: RULE  # Issue #N: <reason>` (or `# type: ignore  # Issue #N:
> …`) tied to a real tracking issue, per `max-quality-no-shortcuts`.
