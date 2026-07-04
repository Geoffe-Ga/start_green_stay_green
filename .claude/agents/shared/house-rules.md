# Shared constraints — Ralph subagent taxonomy

> Single source of truth for every agent in `.claude/agents/`. Each agent links
> here instead of restating the rules. If a rule changes, change it **once**,
> here. The taxonomy map lives in [`README.md`](README.md).

## Product north star (read before building)

Start Green Stay Green is a meta-tool that generates quality-controlled,
AI-ready repositories with enterprise-grade quality controls pre-configured
(`green init`). It deliberately never lowers a generated project's quality
bar to make generation easier, and never ships a generated artifact (CI
config, pre-commit hook, skill, subagent) that this repo doesn't itself pass.

- Product thesis / architecture: `CLAUDE.md` (repo root).
- Full specification: `plan/SPEC.md`.
- Quality framework: `reference/MAXIMUM_QUALITY_ENGINEERING.md`.

## The stack

A single Python package (no frontend/backend split):

- **Language:** Python 3.11–3.13. Package: `start_green_stay_green/`.
  Tests: `pytest`, `tests/{unit,integration,e2e}/`.
- Templates for generated projects live in `templates/`; reference content
  generators vendor into generated projects lives in `reference/`.
- Layout, commands, and patterns are authoritative in `CLAUDE.md` (repo root).

## The four gates (the whole game)

| Gate | Check | On pass | On fail |
| --- | --- | --- | --- |
| 1 | **TDD** Red→Green→Refactor (`stay-green` skill) | → Gate 2 | — |
| 2 | **`pre-commit run --all-files`** exits 0 (CI runs the equivalent `./scripts/check-all.sh`) | → self-review → push → Gate 3 | **drop to Gate 1** |
| 3 | **CI** all green | → Gate 4 | **drop to Gate 1** (`ci-debugging`) |
| 4 | **Claude review `Verdict:`** | `LGTM` → merge | **drop to Gate 1** (`address-feedback`) |

"Drop to Gate 1" means: fix the **root cause** with a failing-test-first cycle,
re-clear Gate 2 locally, push, climb again. **Never weaken a gate to pass it.**

## Quality thresholds (non-negotiable — from `CLAUDE.md`)

These are the values `./scripts/check-all.sh` (`pre-commit run --all-files`)
enforces:

- **Code coverage:** ≥90% (pytest-cov).
- **Docstring coverage:** ≥95% (pydocstyle / ruff D rules).
- **Mutation score:** ≥80% (mutmut), as a periodic gate for critical infra.
- **Cyclomatic complexity:** ≤10 per function (radon/xenon).
- **Pylint score:** ≥9.0.
- Type-checker strictness: mypy. Linter: ruff. Formatter: black + isort.
  Security scanners: bandit, detect-secrets, pip-audit.
- Run `pre-commit run --all-files` for autofixable lint/format; never
  hand-patch what the formatter owns.

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
