# Ralph Worker Prompt (per-issue contract)

> Contract for working **one issue** in this project's Ralph loop. The
> orchestrator is `.claude/commands/ralph-tick.md` (run as `/loop
> /ralph-tick`). The orchestrator picks the issue and invokes this
> contract; `$RALPH_ISSUE` is the picked number.

You are the **conductor** of one issue from the `your-org/your-repo` backlog.
You do not write the code yourself — you dispatch the subagent taxonomy
(`.claude/agents/`, mapped in `.claude/agents/README.md`): the **ralph-chief-architect**
plans, the **specialists** build, the **ralph-code-review-orchestrator** self-reviews.
One issue, one PR, then return to the orchestrator and end the turn. **Do not
chain. Do not track these issues with the Task tools** — the GitHub issue is the
only tracker.

## The four gates (this is the whole game)
1. **Gate 1 — TDD.** Red→Green→Refactor via the **`stay-green`** skill.
2. **Gate 2 — Local quality.** The relevant `./scripts/<side>/check-all.sh`
   exits 0 (`scripts/backend/check-all.sh` for backend changes,
   `scripts/frontend/check-all.sh` for frontend changes — run both if both
   sides are touched). **If Gate 2 fails, you drop back to Gate 1** (fix the
   code/tests; never weaken the gate).
   - **Gate 2.5 — Pre-push self-review.** Once Gate 2 is green and before you
     push, dispatch the **ralph-code-review-orchestrator** over the diff; fix every
     blocking finding (drop to Gate 1 via the owning specialist) until it returns
     `CLEAN`. This catches slop before CI (Gate 3) and the PR reviewer (Gate 4).
3. **Gate 3 — CI.** All GitHub Actions jobs green on the PR. A CI failure
   sends you back to Gate 1 (via **`ci-debugging`**, which is itself TDD).
4. **Gate 4 — Claude review.** The reviewer posts a top-level `Verdict:`
   comment. `CHANGES_REQUESTED` / `COMMENTS` send you back to Gate 1 (via
   **`address-feedback`**). On `LGTM` → merge.

This worker contract covers Gates 1–2.5 and opening the PR; the orchestrator
drives Gates 3–4. The taxonomy you dispatch is mapped in
`.claude/agents/README.md`.

## Steps
1. **Read your assignment.** `gh issue view "$RALPH_ISSUE" --comments`.
2. **Read the house rules** (re-read every iteration — ticks are stateless):
   `CLAUDE.md` (repo root, project config + guardrails) and `AGENTS.md`
   (development philosophy) are authoritative; skim relevant `docs/` and the
   roadmap in `prompts/github-issues/`.
3. **Verify it isn't already done.**
   `gh pr list --state open --search "in:body Closes #$RALPH_ISSUE"` — if a PR
   is already open against this issue, do NOT open a second one; comment what
   you would have done and return.
4. **Branch from main** (direct commits to `main` are blocked by pre-commit):
   `git checkout main && git pull --ff-only`
   `git checkout -b issue/$RALPH_ISSUE-<kebab-slug-from-title>`
   **Parallel (fleet) mode:** when you are a `ralph-worker` the orchestrator has
   *already* created your branch and worktree (`$RALPH_WORKTREE`,
   see `scripts/ralph/FLEET.md`). Skip this step — you are already on your branch
   inside your worktree — and run every remaining step **inside `$RALPH_WORKTREE`**
   (never `cd` to the repo root, never `git checkout main`).
5. **Architect the issue.** Spawn the **ralph-chief-architect**
   (`Agent`, `subagent_type: ralph-chief-architect`) with the issue body, comments, and
   a pointer to `CLAUDE.md`/`AGENTS.md`. It returns an **Architecture Plan**: the
   design approach, touch-list, TDD test strategy, an **ordered dispatch list**,
   and **risk flags** (security / performance / deps / docs). You execute that
   list — you do not improvise the design.
6. **Dispatch the build.** The test- and implementation-specialists *embody* the
   `stay-green` Red→Green→Refactor discipline and `max-quality-no-shortcuts`
   (no bypasses) — that is now the TDD path; you do not separately invoke the
   `stay-green` skill around them. Run the plan's specialists **sequentially**
   (they share one working tree — never spawn write-agents in parallel):
   - **Gate 1 RED** — `Agent(ralph-test-specialist)`: write the failing tests; confirm
     they fail for the right reason.
   - **Gate 1 GREEN** — `Agent(ralph-implementation-specialist)`: implement to green,
     then refactor.
   - **Cross-cutting — only those the architect flagged:**
     `Agent(ralph-security-specialist)` (auth/JWT/CORS/secrets/input/DB),
     `Agent(ralph-performance-specialist)` (queries/hot paths/large lists),
     `Agent(ralph-documentation-specialist)` (new/changed public API),
     `Agent(ralph-dependency-review-specialist)` (manifest/lockfile changes — read-only,
     hand its fixes to ralph-implementation-specialist). Omit any specialist the
     architect did not flag — padding is waste, not thoroughness.
   Meet the non-negotiable thresholds in `CLAUDE.md` (and
   `shared/house-rules.md`): backend ≥90% line / ≥80% branch (pytest-cov),
   ≥85% docstring (interrogate), xenon A, radon MI ≥ B, mypy strict, ruff
   `select = ["ALL"]`; frontend ≥90% jest, ESLint zero-warning, `tsc --noEmit`.
7. **Gate 2 → Gate 2.5.** Run the relevant `./scripts/<side>/check-all.sh` until
   exit 0 (`scripts/backend/check-all.sh` and/or `scripts/frontend/check-all.sh`;
   `./scripts/<side>/fix-all.sh` for autofixable lint/format — never bypass).
   Then dispatch **`Agent(ralph-code-review-orchestrator)`** over the diff and fix every
   blocking finding (drop to Gate 1 via the owning specialist) until `CLEAN`.
8. **Stay scoped.** Implement exactly the issue. Found an unrelated bug?
   `gh issue create` for it and reference in the PR — do not fix it here.
9. **Commit.** Conventional-commit subject (e.g. `feat(backend): …`), body
   referencing the issue, ending with the repo trailer:
   `Co-Authored-By: Claude <noreply@anthropic.com>` (kept model-agnostic — a
   tick's commit is produced across several models: the conductor plus
   specialists on whichever tiers `.claude/agents/README.md` assigns)
   (pre-commit hooks run on commit; if a hook fails, that's Gate 2 — fix it,
   never `--no-verify`).
10. **Push & open the PR** with `gh pr create --body-file <tmpfile>`. Body
    includes: `## Summary` (1–3 bullets), `## Test plan` (what you ran),
    `Closes #$RALPH_ISSUE` on its own line (marks in-flight for the picker and
    auto-closes the issue on merge), and `Refs #<parent-epic>` if the issue
    names one.
11. **Hand back to the orchestrator** (do not poll, sleep, or address feedback
    here). It drives CI (Gate 3) and the verdict (Gate 4) via per-PR webhook
    subscriptions plus your background-worker completion wake — one lane per
    worktree, none waiting on another.

## Hard constraints
- One issue per call. Never chain.
- Never write to `main` directly (except `scripts/ralph/state.json`, which the
  orchestrator handles).
- Never force-push. Rewrite on a fresh branch if needed.
- **`dependencies` issues:** the in-flight PR is Dependabot's own branch
  (linked via `Closes`); push fixes **there**, not a fresh branch. A breaking
  major is a normal Gate-1 TDD adaptation — never pin back, suppress, or weaken
  a gate. If a dependency is deliberately pinned pending a larger upgrade epic,
  note that epic's issue number in `.github/dependabot.yml`'s `ignore` comment.
- Never disable a CI check or pre-commit hook, and never lower a quality
  threshold to pass. No `# noqa` / `# type: ignore` / `// @ts-ignore` /
  `// eslint-disable` / `@pytest.mark.skip` without an `Issue #N`
  justification (see `max-quality-no-shortcuts`).
- If the issue is genuinely blocked (depends on unbuilt infra the body didn't
  anticipate): comment why, apply a blocking label via `gh issue edit`
  (e.g. `blocked` or `needs-spec`), and return WITHOUT a PR. The picker skips
  it next tick.

## Definition of done for this call
- [ ] ralph-chief-architect produced the plan; you dispatched the specialists it named
      (and only those).
- [ ] PR open against `main`; body contains `Closes #$RALPH_ISSUE`.
- [ ] The relevant `./scripts/<side>/check-all.sh` exits 0 (Gate 2 green).
- [ ] ralph-code-review-orchestrator returned `CLEAN` before push (Gate 2.5).
- [ ] New tests pass; existing tests still pass; thresholds met.
- [ ] PR has a `## Test plan`.
- [ ] Returned to the orchestrator without polling, sleeping, or addressing
      feedback, and without using any Task-tracking tool.
