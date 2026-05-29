## Context

Sub-issue of the **Kotlin (Wear OS (Google / Samsung Galaxy Watch 4+))** epic. Gate 2 is a
green CI pipeline. `ci.py` drives `LANGUAGE_CONFIGS` and the generated GitHub
Actions workflow, which must build and test on the actual target.

**Depends on:** Foundation + Quality sub-issues.

## Goal

Generate a GitHub Actions pipeline that builds, tests, lints, and security-scans
a Kotlin (Wear OS (Google / Samsung Galaxy Watch 4+)) project across Kotlin 1.9 / 2.0; JDK 17, 21.

## Scope — files to touch

- `start_green_stay_green/generators/ci.py` — add the `kotlin` entry to
  `LANGUAGE_CONFIGS` (`ci.py:40`): test_framework=JUnit5 + Kotest,
  linters=detekt + ktlint, formatters=ktlint (or ktfmt), security_tools=detekt security ruleset + OWASP dependency-check,
  supported_versions=Kotlin 1.9 / 2.0; JDK 17, 21, package_manager=Gradle (Kotlin DSL)
- `start_green_stay_green/generators/github_actions.py` — render Kotlin
  setup/build/test steps
- keep CI ⇄ local pre-commit hook parity

## Tasks

- [ ] Add the `kotlin` `LANGUAGE_CONFIGS` entry
- [ ] Render a version matrix (Kotlin 1.9 / 2.0; JDK 17, 21)
- [ ] Generated project must target Wear OS: Jetpack Compose for Wear OS (androidx.wear.compose) and the Wear OS SDK, with an Android Gradle module set to a `wear` device profile.
- [ ] Emit a coverage gate step (Kover (or JaCoCo) (≥90%))

## Acceptance Criteria

- [ ] Generated workflow YAML lints clean (actionlint)
- [ ] Workflow builds for the Wear OS (Google / Samsung Galaxy Watch 4+) target
- [ ] Coverage threshold enforced in CI (≥90%)

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/ci.py:40` — `LANGUAGE_CONFIGS`
- `start_green_stay_green/generators/github_actions.py`
