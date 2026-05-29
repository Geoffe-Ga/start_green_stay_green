## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **Kotlin**
(Wear OS (Google / Samsung Galaxy Watch 4+)).

**Current state:** `templates/kotlin/` is `.gitkeep` only and `kotlin` is **absent from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No generator branch handles Kotlin.

Generated project must target Wear OS: Jetpack Compose for Wear OS (androidx.wear.compose) and the Wear OS SDK, with an Android Gradle module set to a `wear` device profile.

## Goal

Add production-grade **Kotlin** support so
`green init -l kotlin` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

| Concern | Tooling |
|---|---|
| Test framework | JUnit5 + Kotest |
| Linters | detekt + ktlint |
| Formatters | ktlint (or ktfmt) |
| Security | detekt security ruleset + OWASP dependency-check |
| Coverage | Kover (or JaCoCo) (≥90%) |
| Complexity | detekt ComplexMethod (≤10) |
| Architecture enforcement | Konsist (or ArchUnit) |
| Package manager | Gradle (Kotlin DSL) |
| Versions | Kotlin 1.9 / 2.0; JDK 17, 21 |


## Sub-Issues (gap-driven)

Only the generator cells Kotlin is actually missing are filed:

1. **Foundation** — registration, CLI & scaffolding
2. **Quality tooling** — pre-commit, scripts, metrics & architecture
3. **CI pipeline** — ci.py config + GitHub Actions workflow
4. **Tests & coverage** — unit / integration / e2e
5. **Documentation** — CLAUDE.md, README, CLI reference, SPEC

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l kotlin` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l kotlin` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for Kotlin is fully ✅
- [ ] CLAUDE.md / README list Kotlin as fully supported

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/base.py:20` — `SUPPORTED_LANGUAGES`
- `start_green_stay_green/generators/ci.py:40` — `LANGUAGE_CONFIGS`
- `start_green_stay_green/cli.py` — `_resolve_languages`, `_get_setup_instructions`
- `.claude/docs/quality-standards.md`, `reference/workflows/stay-green.md`
