## Context

Sub-issue of the **Swift (watchOS / Apple Watch)** epic. No code lands
without tests, and repo coverage must stay ≥90%. New generator branches for
Swift need parallel coverage.

**Depends on:** Foundation, Quality, CI sub-issues.

## Goal

Prove the tool generates correct, green Swift (watchOS / Apple Watch)
projects, keeping repo coverage ≥90%.

## Scope — files to touch

- `tests/unit/generators/` — unit tests for each new/changed generator branch
- `tests/integration/generators/` — `green init -l swift` generation assertions
- `tests/unit/test_multi_language.py` — add `swift` to the parametrized
  all-language matrix
- `tests/e2e/` — generate a swift project and assert it passes its own
  `pre-commit run --all-files`

## Tasks

- [ ] Unit tests for every new branch (happy path + invalid input)
- [ ] Integration test asserting generated tree + manifest contents
- [ ] Parametrize `test_multi_language.py` to include `swift`
- [ ] e2e test: generated project is green
- [ ] Mutation-test new generator logic (≥80% on changed files)

## Acceptance Criteria

- [ ] Repo coverage stays ≥90%
- [ ] `swift` appears in the parametrized multi-language tests
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
