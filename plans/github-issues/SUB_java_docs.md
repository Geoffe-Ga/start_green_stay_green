## Context

Sub-issue of the **Java (Wear OS (legacy Android Wear))** epic. Support isn't
done until documented; several docs enumerate supported languages.

**Depends on:** the other sub-issues (document what was built).

## Goal

Document Java (Wear OS (legacy Android Wear)) support across all
language-listing surfaces, with a usage example.

## Scope — files to touch

- `CLAUDE.md` — multi-language list + supported-languages references
- `README.md` — supported languages / quick start
- `docs/CLI_REFERENCE.md` — `green init -l java` usage
- `plan/SPEC.md` — language support section
- `examples/` — minimal generated Java example
- `CHANGELOG.md` — note the new/completed language

## Tasks

- [ ] Update every supported-languages list to include Java
- [ ] Add a `green init -l java` usage example with the toolchain table
- [ ] Document prerequisites (Maven (matches existing ci.py config), JDK 11, 17, 21)
- [ ] Add a CHANGELOG entry

## Acceptance Criteria

- [ ] No doc implies Java is unsupported/partial
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
