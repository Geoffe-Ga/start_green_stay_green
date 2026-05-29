## Context

Foundational sub-issue of the **Java (Wear OS (legacy Android Wear))** epic —
every other Java sub-issue depends on it.

**Current state:** Java is registered and has `ci.py`/`dependencies.py`/`structure.py`/`readme.py`/`tests_gen.py` entries, but is **missing from `precommit.py`, `scripts.py`, `metrics.py`, and `architecture.py`** — so generating pre-commit config for Java raises today. Scaffolding is generic, not Wear OS.

## Goal

Make `green init -l java` emit a valid Wear OS (legacy Android Wear) project skeleton
with a Maven (matches existing ci.py config) manifest and generated README.

## Scope — files to touch

- `start_green_stay_green/generators/base.py` — confirm registration (already present) and extend scaffolding; verify `validate_language`
- `start_green_stay_green/cli.py` — `--language` help (`cli.py:1036`, `:1613`),
  interactive prompt choices, `_get_setup_instructions` (`cli.py:1325`) for
  Maven (matches existing ci.py config)
- `start_green_stay_green/generators/structure.py` — `_generate_java_structure`
  + dispatch entry (Wear OS (legacy Android Wear) app target)
- `start_green_stay_green/generators/dependencies.py` —
  `_generate_java_dependencies` (Maven (matches existing ci.py config) manifest)
- `start_green_stay_green/generators/readme.py` — `_generate_java_readme`

## Tasks

- [ ] Register / validate the language in the CLI path
- [ ] Generate a Maven (matches existing ci.py config) dependency manifest
- [ ] Generate the project directory structure incl. the Wear OS (legacy Android Wear) target
- [ ] Generate a language-appropriate README

## Acceptance Criteria

- [ ] `green init -l java` creates a buildable Wear OS (legacy Android Wear) skeleton
- [ ] `validate_language("java")` passes; unknown languages still raise
- [ ] Foundation work here is the Wear OS angle: extend scaffolding to a legacy Android Wear app (Wearable Support Library / androidx.wear), the common path for maintaining existing Java watch apps.

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
