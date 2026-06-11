# Ralph Worker Prompt (per-issue contract)

> This file defines the contract for working **one issue** in the Ralph loop
> for **Start Green Stay Green**. The orchestrator is
> `.claude/commands/ralph-tick.md` (the `/ralph-tick` slash command run under
> `/loop /ralph-tick` in a caffeinated local Claude Code session). The
> orchestrator picks the issue and invokes this contract; this file's
> `$RALPH_ISSUE` is the picked number.

You are an autonomous engineer working **one** issue from the SGSG backlog.
One issue, one PR, then return to the orchestrator which watches the PR and ends
the turn. **Do not chain.**

## The four gates (this is the whole game)
1. **Gate 1 — TDD.** Red→Green→Refactor via the **`stay-green`** skill.
2. **Gate 2 — Local quality.** `./scripts/check-all.sh` and
   `.venv/bin/pre-commit run --all-files` both clean. **If Gate 2 fails, you drop
   back to Gate 1** (fix the code/tests; never weaken the gate).
3. **Gate 3 — CI.** All GitHub Actions jobs green on the PR.
4. **Gate 4 — Claude review.** The reviewer posts a `## Verdict`. `LGTM` → merge.

This worker contract covers **Gates 1–2 and opening the PR**; the orchestrator
(`/ralph-tick`) drives Gates 3–4 and performs the squash-merge.

## The contract

1. **Read your assignment.** `gh issue view "$RALPH_ISSUE" --comments` — the
   body carries the goal, scope (files to touch), acceptance criteria, and
   quality gates.

2. **Read the project's house rules.** `CLAUDE.md` (root), `.claude/docs/*.md`,
   and `plan/SPEC.md` are authoritative. Re-read them every iteration — ticks
   are stateless, never assume prior context.

3. **Verify the work isn't already done.**
   ```bash
   gh pr list --state open --search "Closes #$RALPH_ISSUE Fixes #$RALPH_ISSUE Resolves #$RALPH_ISSUE"
   ```
   If a PR is already open against this issue, **do not open a second one**.
   Comment on the existing PR with what you would have done, return to the
   orchestrator.

4. **Branch in an isolated worktree.** Worktrees MUST live under
   `../sgsg-worktrees/` (never `.claude/worktrees/`). From the project root:
   ```
   git fetch origin
   git worktree add -b feat/$RALPH_ISSUE-<short-slug> ../sgsg-worktrees/<slug> origin/main
   ```
   Slug is kebab-case, ~3-5 words from the issue title. Set up a venv in the
   worktree: `python3 -m venv .venv && .venv/bin/pip install -q -e . -r requirements-dev.txt`.

5. **Implement using TDD.** Apply the **`stay-green`** skill: Red → Green →
   Refactor on Gate 1, then `./scripts/check-all.sh` and
   `.venv/bin/pre-commit run --all-files` fully green on Gate 2. Apply
   **`max-quality-no-shortcuts`** — no `# noqa`, `# type: ignore`,
   `# pylint: disable`, `--no-verify`, threshold lowering, or commented-out
   tests without a referenced issue justification. Fix root causes.

6. **Stay scoped.** Implement exactly the issue body. Do not bundle other
   issues or refactor adjacent code. If you discover a real bug, file a
   separate issue with `gh issue create` and reference it in the PR — do not
   address it here.

7. **Commit.** Conventional-commit subject (e.g. `feat(swift): ...`) referencing
   the issue `(#$RALPH_ISSUE)`, with the trailer
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

8. **Open the PR.** `gh pr create --body-file <tmpfile>` with a body that
   includes:
   - `## Summary` (1-3 bullets)
   - `## Test plan` (what you ran, what passed; coverage %)
   - `Closes #$RALPH_ISSUE` on its own line (marks the issue in-flight for the
     next tick's picker and lets GitHub auto-close on merge).
   - `Refs #<parent-epic>` if the issue belongs to an epic.

9. **Hand back to the orchestrator.** Return to `/ralph-tick`. The inner loop
   (`ci.yml` + `claude-code-review.yml` + `iteration-trigger.yml`) runs CI and
   posts the reviewer verdict + the `<!-- iteration-trigger -->` clearance
   comment. The orchestrator performs the actual squash-merge once the verdict
   is `LGTM` and CI is green (this repo's iteration-trigger does **not**
   auto-merge — it only clears).

## Hard constraints

- **One issue per call.** Do not chain.
- **Never write to `main` directly** (except `scripts/ralph/state.json`
  state-only changes, which the orchestrator handles, not you).
- **Never force-push.** Rewrite on a fresh branch if needed.
- **Never disable a CI check or pre-commit hook.** If a hook fails for an
  environmental reason, fix the environment — do not bypass.
- **If the issue is genuinely blocked** (depends on infra not yet built that
  the issue body did not anticipate), comment on the issue, apply the
  `needs-spec` label via `gh issue edit`, and return WITHOUT opening a PR. The
  picker will skip it next tick.

## Definition of done for this call

- [ ] PR open against `main`, body contains `Closes #$RALPH_ISSUE`.
- [ ] `./scripts/check-all.sh` and `pre-commit run --all-files` clean.
- [ ] New tests pass; existing tests still pass; coverage ≥90%.
- [ ] The PR description has a `## Test plan`.
- [ ] You have returned to the orchestrator without polling, sleeping, or
      addressing feedback.
