## Context

Foundational sub-issue of the **Swift (watchOS / Apple Watch)** epic —
every other Swift sub-issue depends on it.

**Current state:** `templates/swift/` is `.gitkeep` only and `swift` is **absent from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No generator branch handles Swift — it is unsupported despite being advertised in CLAUDE.md.

## Goal

Make `green init -l swift` emit a valid watchOS / Apple Watch project skeleton
with a Swift Package Manager (SPM) manifest and generated README.

## Scope — files to touch

- `start_green_stay_green/generators/base.py` — add `"swift"` to `SUPPORTED_LANGUAGES`; verify `validate_language`
- `start_green_stay_green/cli.py` — `--language` help (`cli.py:1036`, `:1613`),
  interactive prompt choices, `_get_setup_instructions` (`cli.py:1325`) for
  Swift Package Manager (SPM)
- `start_green_stay_green/generators/structure.py` — `_generate_swift_structure`
  + dispatch entry (watchOS / Apple Watch app target)
- `start_green_stay_green/generators/dependencies.py` —
  `_generate_swift_dependencies` (Swift Package Manager (SPM) manifest)
- `start_green_stay_green/generators/readme.py` — `_generate_swift_readme`

## Tasks

- [ ] Register / validate the language in the CLI path
- [ ] Generate a Swift Package Manager (SPM) dependency manifest
- [ ] Generate the project directory structure incl. the watchOS / Apple Watch target
- [ ] Generate a language-appropriate README

## Acceptance Criteria

- [ ] `green init -l swift` creates a buildable watchOS / Apple Watch skeleton
- [ ] `validate_language("swift")` passes; unknown languages still raise
- [ ] Generated project must include a watchOS app/extension target (SwiftUI + WatchKit); CI must build for the watchOS simulator (`xcodebuild ... -destination 'platform=watchOS Simulator'`).

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
