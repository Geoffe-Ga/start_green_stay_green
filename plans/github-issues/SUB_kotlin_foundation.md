## Context

Foundational sub-issue of the **Kotlin (Wear OS (Google / Samsung Galaxy Watch 4+))** epic —
every other Kotlin sub-issue depends on it.

**Current state:** `templates/kotlin/` is `.gitkeep` only and `kotlin` is **absent from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No generator branch handles Kotlin.

## Goal

Make `green init -l kotlin` emit a valid Wear OS (Google / Samsung Galaxy Watch 4+) project skeleton
with a Gradle (Kotlin DSL) manifest and generated README.

## Scope — files to touch

- `start_green_stay_green/generators/base.py` — add `"kotlin"` to `SUPPORTED_LANGUAGES`; verify `validate_language`
- `start_green_stay_green/cli.py` — `--language` help (`cli.py:1036`, `:1613`),
  interactive prompt choices, `_get_setup_instructions` (`cli.py:1325`) for
  Gradle (Kotlin DSL)
- `start_green_stay_green/generators/structure.py` — `_generate_kotlin_structure`
  + dispatch entry (Wear OS (Google / Samsung Galaxy Watch 4+) app target)
- `start_green_stay_green/generators/dependencies.py` —
  `_generate_kotlin_dependencies` (Gradle (Kotlin DSL) manifest)
- `start_green_stay_green/generators/readme.py` — `_generate_kotlin_readme`

## Tasks

- [ ] Register / validate the language in the CLI path
- [ ] Generate a Gradle (Kotlin DSL) dependency manifest
- [ ] Generate the project directory structure incl. the Wear OS (Google / Samsung Galaxy Watch 4+) target
- [ ] Generate a language-appropriate README

## Acceptance Criteria

- [ ] `green init -l kotlin` creates a buildable Wear OS (Google / Samsung Galaxy Watch 4+) skeleton
- [ ] `validate_language("kotlin")` passes; unknown languages still raise
- [ ] Generated project must target Wear OS: Jetpack Compose for Wear OS (androidx.wear.compose) and the Wear OS SDK, with an Android Gradle module set to a `wear` device profile.

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/base.py:20`
- `start_green_stay_green/generators/structure.py:128` (dispatch map)
- `start_green_stay_green/generators/dependencies.py:129` (dispatch map)
- `start_green_stay_green/generators/readme.py:155` (dispatch map)
