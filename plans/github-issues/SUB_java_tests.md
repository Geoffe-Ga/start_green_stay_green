## Context

Sub-issue of the **Java (Wear OS (legacy Android Wear))** epic. No code lands
without tests, and repo coverage must stay ≥90%. New generator branches for
Java need parallel coverage.

**Depends on:** Foundation, Quality sub-issues.

## Goal

Prove the tool generates correct, green Java (Wear OS (legacy Android Wear))
projects, keeping repo coverage ≥90%.

## Scope — files to touch

- `tests/unit/generators/` — unit tests for each new/changed generator branch
- `tests/integration/generators/` — `green init -l java` generation assertions
- `tests/unit/test_multi_language.py` — add `java` to the parametrized
  all-language matrix
- `tests/e2e/` — generate a java project and assert it passes its own
  `pre-commit run --all-files`

## Tasks

- [ ] Unit tests for every new branch (happy path + invalid input)
- [ ] Integration test asserting generated tree + manifest contents
- [ ] Parametrize `test_multi_language.py` to include `java`
- [ ] e2e test: generated project is green
- [ ] Mutation-test new generator logic (≥80% on changed files)

## Acceptance Criteria

- [ ] Repo coverage stays ≥90%
- [ ] `java` appears in the parametrized multi-language tests
- [ ] e2e generation test passes in CI

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `tests/unit/test_multi_language.py`
- `tests/integration/generators/`, `tests/e2e/`, `.claude/docs/testing.md`
