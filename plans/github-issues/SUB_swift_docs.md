## Context

Sub-issue of the **Swift (watchOS / Apple Watch)** epic. Support isn't
done until documented; several docs enumerate supported languages.

**Depends on:** the other sub-issues (document what was built).

## Goal

Document Swift (watchOS / Apple Watch) support across all
language-listing surfaces, with a usage example.

## Scope — files to touch

- `CLAUDE.md` — multi-language list + supported-languages references
- `README.md` — supported languages / quick start
- `docs/CLI_REFERENCE.md` — `green init -l swift` usage
- `plan/SPEC.md` — language support section
- `examples/` — minimal generated Swift example
- `CHANGELOG.md` — note the new/completed language

## Tasks

- [ ] Update every supported-languages list to include Swift
- [ ] Add a `green init -l swift` usage example with the toolchain table
- [ ] Document prerequisites (Swift Package Manager (SPM), Swift 5.9, 5.10, 6.0)
- [ ] Add a CHANGELOG entry

## Acceptance Criteria

- [ ] No doc implies Swift is unsupported/partial
- [ ] Docs lint clean (markdownlint + link check)
- [ ] Example reflects real generated output

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `CLAUDE.md`, `README.md`, `docs/CLI_REFERENCE.md`, `plan/SPEC.md`
