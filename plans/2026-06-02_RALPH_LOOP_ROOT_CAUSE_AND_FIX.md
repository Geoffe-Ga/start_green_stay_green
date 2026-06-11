# Ralph Loop: Why SGSG's Stalled While creek-tools & PillBreakfast Thrive

**Date:** 2026-06-02
**Author:** Ralph harness audit
**Scope:** `.claude/commands/ralph-tick.md`, `scripts/ralph/PROMPT.md`

## Symptom

| Repo | `total_completed` | Open Ralph PRs | Status |
| --- | --- | --- | --- |
| **start_green_stay_green** | **0** | **3 stuck (#390, #392, #394)** | never completed a cycle |
| creek-tools | 39 | converging | self-sustaining |
| PillBreakfast | 75 | converging | self-sustaining |

SGSG's `state.json` had `started_at: null`, `last_groom_at: null`,
`last_completed_issue: null` — the orchestrator state machine had **never once**
advanced through a full open→merge→advance cycle. Ralph kept *opening* PRs but
never *merged* any, so the picker's in-flight exclusion let new issues pile up
into parallel stuck PRs.

## Root cause

The inner loop is **identical** between SGSG and creek-tools: both
`iteration-trigger.yml` files are byte-for-byte the same and **neither
auto-merges** — they only post a `<!-- iteration-trigger -->` clearance comment.
So the merge must be performed by the orchestrator. The only thing that differed
between the repo that works (creek-tools, 39) and the one that doesn't (SGSG, 0)
was the **orchestrator's watch/merge logic** in `ralph-tick.md`.

SGSG's Step 2e "watch" was fragile in three compounding ways:

1. **Author-coupled verdict detection.** It waited for a comment from
   `author.login=="Geoffe-Ga"` whose body matched `test("VERDICT")` — i.e. the
   `iteration-trigger.yml` *clearance* comment, not the reviewer's actual
   verdict. That clearance comment only posts as `Geoffe-Ga` when the
   `GEOFFE_GA_PAT` secret is present; otherwise it posts as `github-actions[bot]`
   (or not at all), and the Monitor's author filter **never fires → infinite
   stall**. The authoritative `## Verdict` from `claude-code-review.yml` was
   being ignored.

2. **No CI-terminal escape.** The watch only exited on a matching verdict
   comment or a CI failure. If CI went green but the clearance comment never
   materialised, the Monitor polled silently until timeout every tick, forever —
   "silence hid a crashed run."

3. **Merge gated on the wrong signal.** Because merge-readiness was inferred from
   the clearance comment rather than read directly from `## Verdict` + the CI
   rollup, the merge action in Step 2b effectively never triggered.

creek-tools avoided all three: its Step 4 Monitor matches `test("Verdict")` on
**any** comment (the reviewer's own), emits each CI check as it goes terminal,
and exits once **CI is terminal AND a verdict exists** (or on any CI failure).

## Fix (this PR)

Ported creek-tools' proven orchestrator robustness into SGSG's `ralph-tick.md`,
preserving SGSG specifics (worktrees under `../sgsg-worktrees/`, the dual Gate-2
of `check-all.sh` + `pre-commit`, the epic-title picker, and the comment-only /
orchestrator-merges model):

- **Four-gates table + drop-back rule** at the top — crisp mental model.
- **Author-independent verdict detection** — read the reviewer's `## Verdict`
  directly via `test("Verdict")`; the clearance comment is a hint, never the
  source of truth.
- **Robust combined CI + verdict Monitor (Step 4)** — emits on every terminal
  CI signal and the first verdict, exits when CI is terminal AND a verdict is
  present **or** on any CI failure, so silence can't hide a stall.
- **`--author "@me"`** in-flight detection.
- **Explicit `BEHIND` handling** for strict branch protection (`update-branch`
  → re-await fresh verdict).
- **Verbatim Python anti-bypass block.**

CI / workflow files are **unchanged** (orchestrator-merge model retained, per
decision) — the blast radius is limited to the two harness docs.

## Provenance

This corrected harness is intended as the **canonical/official** Ralph loop:
shipped with `green` and exported to `well-worn-tools` for cross-repo sync. See
the companion draft issue for making `well-worn-tools` an imported package so the
harness and skills stay synchronized across SGSG and every generated project.
