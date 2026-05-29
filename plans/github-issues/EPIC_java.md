## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **Java**
(Wear OS (legacy Android Wear)).

**Current state:** Java is registered and has `ci.py`/`dependencies.py`/`structure.py`/`readme.py`/`tests_gen.py` entries, but is **missing from `precommit.py`, `scripts.py`, `metrics.py`, and `architecture.py`** — so generating pre-commit config for Java raises today. Scaffolding is generic, not Wear OS.

Foundation work here is the Wear OS angle: extend scaffolding to a legacy Android Wear app (Wearable Support Library / androidx.wear), the common path for maintaining existing Java watch apps.

## Goal

Complete production-grade **Java** support so
`green init -l java` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

| Concern | Tooling |
|---|---|
| Test framework | JUnit5 |
| Linters | Checkstyle + PMD + SpotBugs |
| Formatters | google-java-format |
| Security | SpotBugs + FindSecBugs + OWASP dependency-check |
| Coverage | JaCoCo (≥90%) |
| Complexity | PMD CyclomaticComplexity / Checkstyle (≤10) |
| Architecture enforcement | ArchUnit |
| Package manager | Maven (matches existing ci.py config) |
| Versions | JDK 11, 17, 21 |


## Sub-Issues (gap-driven)

Only the generator cells Java is actually missing are filed:

1. **Foundation** — registration, CLI & scaffolding
2. **Quality tooling** — pre-commit, scripts, metrics & architecture
3. **Tests & coverage** — unit / integration / e2e
4. **Documentation** — CLAUDE.md, README, CLI reference, SPEC

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l java` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l java` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for Java is fully ✅
- [ ] CLAUDE.md / README list Java as fully supported

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
