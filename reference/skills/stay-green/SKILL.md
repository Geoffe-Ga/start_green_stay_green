---
name: stay-green
description: >-
  Local TDD + quality-gate workflow run as a graduated ladder: Gate 1 is
  Red-Green-Refactor with targeted tests, Gate 2 is the repo's
  `./scripts/check-all.sh` (or `pre-commit run --all-files` where no
  check-all exists) exiting 0. Use when implementing features, fixing bugs,
  or doing any development work. Ensures code is never pushed without
  passing tests and quality checks. Gates 3 (CI) and 4 (Claude review) are
  covered by ci-debugging and address-feedback.
  Do NOT use for bug-specific debugging (use bug-squashing-methodology) or
  for draining a whole backlog autonomously (use ultracode).
metadata:
  author: Geoff
  version: 2.0.0
---

# Stay Green

Write tests first, then code. Never declare work finished until all checks pass.
This skill covers Gates 1-2 of the four-gate model (TDD, local checks, CI,
review); Gates 3 (CI) and 4 (Claude review) live in `ci-debugging` and
`address-feedback`.

## Instructions

### Gate 1: TDD (Red-Green-Refactor) with targeted tests

1. **Red** - Write a failing test describing the behavior you want
   ```bash
   ./scripts/test.sh <path/to/test_file>  # Should fail
   ```

2. **Green** - Write just enough code to make the test pass
   ```bash
   ./scripts/test.sh <path/to/test_file>  # Should pass
   ```

3. **Refactor** - Clean up while keeping tests green
   ```bash
   ./scripts/test.sh <path/to/test_file>  # Should still pass
   ```

Repeat for each small piece of functionality. Write tests incrementally, not
all at once. Run only the tests you are touching on each cycle — a targeted
run takes seconds, so it is cheap enough to run every time. The whole suite
belongs to Gate 2. (If the repo's `test.sh` takes no path argument, use the
test runner's own selector, e.g. `pytest path::test_name`, `jest -t`,
`go test -run`.)

### Gate 2: `check-all.sh`, once, when Gate 1 is green

Run each rung of the ladder once, cheapest first. Running one on top of
another buys nothing and doubles the wait:

| Rung | Runs | Typical cost |
| --- | --- | --- |
| Targeted tests (`./scripts/test.sh <paths>`) | every Red-Green cycle | seconds |
| `./scripts/check-all.sh` | once, when Gate 1 is green | minutes |
| `git commit` hooks (staged files only) | automatic | seconds to ~1 min |
| `git push` hooks (if configured: full suite + coverage) | automatic | minutes |
| CI | on push | longest |

```bash
./scripts/check-all.sh    # lint, format, types, security, complexity,
                          # full test suite, coverage
```

In a monorepo with per-area scripts, run the area you touched
(e.g. `./scripts/<side>/check-all.sh`). If the repo has no `check-all.sh`,
`pre-commit run --all-files` is Gate 2.

When checks fail: read errors, fix issues, run again. Repeat until all green.
Use the repo's auto-fixer (`./scripts/fix-all.sh` or `./scripts/format.sh
--fix`) for lint/format failures; never hand-patch what the formatter owns.

Quality checks typically include: formatting and linting (e.g. Ruff), type
checking (e.g. MyPy strict), complexity (<=10 per function), security
(e.g. Bandit, pip-audit), tests with coverage (>=90%), docstring coverage,
file hygiene. The repo's config is the source of truth for tools and
thresholds.

**Don't stack redundant whole-tree passes.** When `check-all.sh` already
swept the tree and `git commit` re-runs the hooks on your staged diff, a
ritual `pre-commit run --all-files` before every commit earns nothing. Reserve
it for what staged-file hooks cannot see: a wide rename, a suspected
cross-file type error, or a change to the hook configuration itself.

**Make sure the push rung is wired.** If the repo declares a `pre-push`
stage, it is installed only when `.pre-commit-config.yaml` sets
`default_install_hook_types` (or you ran `pre-commit install --hook-type
pre-push`). Confirm `.git/hooks/pre-push` exists; a push that produces no hook
output on such a repo means the rung is missing and failures will surface
later in CI instead.

**Respect gate-script safeguards.** Some repos' scripts cache a pass receipt
for an unchanged tree (so a re-run is near-instant) or take an exclusive lock
around the whole suite. If a run exits because another whole-suite run holds
the lock, wait for it; do not route around the lock. A failure observed while
another whole-suite run was in flight in the same worktree is unproven until
it is re-run alone.

### Work is DONE when:
1. All tests pass (Gate 1 complete)
2. `check-all.sh` (or the repo's equivalent Gate 2 command) exits 0 (Gate 2 complete)

No exceptions.

### After Push: Await the Reviewer (if applicable)

If the repo runs the Claude reviewer GitHub Action, "done" extends past local gates: the latest verdict for HEAD must be `LGTM`. Don't poll, don't `sleep`, and don't wait on "CI green" as a proxy — the PR webhook does **not** deliver CI passes, only comments and CI failures. Use `await-claude-review` to subscribe and end the turn; the bot's verdict comment wakes the session via `<github-webhook-activity>`. From there, `address-feedback` handles the merge gate or the fix loop, including calling `mcp__github__unsubscribe_pr_activity` once the PR merges or closes.

## Examples

### Example 1: Adding a New Function

```python
# Gate 1 - Red: Write failing test (./scripts/test.sh tests/test_cost.py)
def test_calculate_cost_from_impressions():
    result = calculate_cost(impressions=1000, cpm=5.0)
    assert result == 5.0

# Gate 1 - Green: Make it pass
def calculate_cost(impressions: int, cpm: float) -> float:
    return impressions * (cpm / 1000)

# Gate 1 - Refactor: (already clean, move on)
# Gate 2: ./scripts/check-all.sh -> All passed!
```

### Example 2: Fixing a Formatting Failure

```bash
# Gate 2 fails on formatting
$ ./scripts/check-all.sh
Running: Formatting
...failed

# Auto-fix and re-run
$ ./scripts/fix-all.sh
$ ./scripts/check-all.sh
# All passed!
```

## Troubleshooting

### Error: Coverage below 90%
```bash
./scripts/coverage.sh  # or ./scripts/test.sh --coverage; see what's not covered
# Add tests for uncovered lines, then re-run ./scripts/check-all.sh
```

### Error: Complexity above 10
```bash
./scripts/complexity.sh  # Find complex functions
# Extract helper functions, simplify branching
# Then verify: ./scripts/complexity.sh && ./scripts/check-all.sh
```

### Error: Type errors from MyPy
```bash
./scripts/typecheck.sh  # See specific errors
# Add/fix type annotations
# Then verify: ./scripts/typecheck.sh && ./scripts/check-all.sh
```

### Error: Push hook never runs
```bash
ls .git/hooks/          # pre-push missing?
pre-commit install      # with default_install_hook_types set, installs all stages
```
