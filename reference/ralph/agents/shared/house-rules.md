# Shared constraints — Ralph subagent taxonomy

> Single source of truth for every agent in `.claude/agents/`. Each agent links
> here instead of restating the rules. If a rule changes, change it **once**,
> here. The taxonomy map lives in [`README.md`](README.md).
>
> **This file ships as a template.** The mechanism (four gates, anti-bypass,
> commit conventions) is stack-agnostic and works as-is. The "Product north
> star" and "The stack" sections below are placeholders — fill them in for
> your project before running the Ralph loop for real, so every agent inherits
> accurate context instead of guessing at your conventions.

## Product north star (read before building)

<Replace this section with your project's own thesis — the one or two
paragraphs a new contributor needs before touching code: what the product is
for, what it deliberately does NOT do, and any non-negotiable product
principles (e.g. accessibility commitments, privacy stance, anti-patterns to
avoid). Point at the authoritative docs, e.g.:>

- Product thesis / vision doc: `<path, e.g. NORTH-STAR.md>`
- Design system / visual direction: `<path, e.g. frontend/src/design/DESIGN.md>`
- Development philosophy: `<path, e.g. AGENTS.md>`

## The stack

<Replace with your actual stack. Keep it terse — this is what every agent
reads before writing a line of code.>

- **Frontend:** `<framework, language, state mgmt, nav>`. Tests: `<framework>`.
  Lives in `<path, e.g. frontend/>`.
- **Backend:** `<framework, ORM, migration tool, DB>`. Tests: `<framework +
  fixture conventions>`. Lives in `<path, e.g. backend/>`.
- Layout, commands, and patterns are authoritative in `CLAUDE.md` (repo root).

## The four gates (the whole game)

| Gate | Check | On pass | On fail |
| --- | --- | --- | --- |
| 1 | **TDD** Red→Green→Refactor (`stay-green` skill) | → Gate 2 | — |
| 2 | **`./scripts/<side>/check-all.sh`** exits 0 (backend and/or frontend) | → self-review → push → Gate 3 | **drop to Gate 1** |
| 3 | **CI** all green | → Gate 4 | **drop to Gate 1** (`ci-debugging`) |
| 4 | **Claude review `Verdict:`** | `LGTM` → merge | **drop to Gate 1** (`address-feedback`) |

"Drop to Gate 1" means: fix the **root cause** with a failing-test-first cycle,
re-clear Gate 2 locally, push, climb again. **Never weaken a gate to pass it.**

## Quality thresholds (non-negotiable — from `CLAUDE.md`)

<Replace with your project's actual gate thresholds — these are the values
`scripts/<side>/check-all.sh` enforces. Example shape:>

- **Backend:** `<coverage %>` line / `<%>` branch coverage, `<%>` docstring
  coverage, complexity grade, type-checker strictness, linter ruleset, and any
  security scanners (e.g. bandit, pip-audit, detect-secrets).
- **Frontend:** `<coverage %>` test coverage, linter zero-warning policy,
  type-checker strictness, formatter-clean.
- Run `./scripts/<side>/fix-all.sh` for autofixable lint/format; never hand-patch
  what the formatter owns.

## Anti-bypass (verbatim, non-negotiable)

> No bypasses. Do not add `# noqa`, `# type: ignore`, `# pylint: disable`,
> `@pytest.mark.skip`, `// @ts-ignore`, `// eslint-disable`, or
> `git commit --no-verify`; do not lower coverage / branch / complexity /
> docstring thresholds in `pyproject.toml`, `jest.config`, or the scripts; do
> not delete tests or code to make a metric pass; do not swallow exceptions to
> silence a linter. Fix the root cause. The only allowed escape hatch is an
> inline `# noqa: RULE  # Issue #N: <reason>` (or `# type: ignore  # Issue #N:
> …`) tied to a real tracking issue, per `max-quality-no-shortcuts`.

## Minimal change & scope discipline

- Implement **exactly** the issue — smallest change that satisfies it.
- Found an unrelated bug or improvement? `gh issue create` for it and reference
  it; **do not** fix it in this change.
- Respect existing patterns and conventions; write code that teaches (comment
  intent, not syntax); no magic numbers without a named constant.
- One issue → one PR. Never chain. Never write to `main` directly. Never
  force-push.

## Commit & PR conventions

- Conventional-commit subjects (`feat(backend): …`, `fix(frontend): …`,
  `refactor(...): …`, `test(...): …`), body referencing the issue, ending with
  the repo trailer (kept model-agnostic on purpose — a tick's commit is produced
  across several models: the conductor plus specialists on opus/sonnet/haiku/fable):
  `Co-Authored-By: Claude <noreply@anthropic.com>`
- PR body: `## Summary` (1–3 bullets), `## Test plan` (what you ran),
  `Closes #N` on its own line, `Refs #<epic>` if the issue names one.
