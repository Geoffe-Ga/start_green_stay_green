## Context

Foundational sub-issue of the **C / C++ (Tizen (Samsung Galaxy Watch, native))** epic —
every other C / C++ sub-issue depends on it.

**Current state:** C/C++ is **completely absent**: no `templates/cpp/`, not in `SUPPORTED_LANGUAGES`, no generator branches. Full greenfield.

## Goal

Make `green init -l cpp` emit a valid Tizen (Samsung Galaxy Watch, native) project skeleton
with a CMake (+ Conan); Tizen Studio CLI for .tpk packaging manifest and generated README.

## Scope — files to touch

- `start_green_stay_green/generators/base.py` — add `"cpp"` to `SUPPORTED_LANGUAGES`; verify `validate_language`
- `start_green_stay_green/cli.py` — `--language` help (`cli.py:1036`, `:1613`),
  interactive prompt choices, `_get_setup_instructions` (`cli.py:1325`) for
  CMake (+ Conan); Tizen Studio CLI for .tpk packaging
- `start_green_stay_green/generators/structure.py` — `_generate_cpp_structure`
  + dispatch entry (Tizen (Samsung Galaxy Watch, native) app target)
- `start_green_stay_green/generators/dependencies.py` —
  `_generate_cpp_dependencies` (CMake (+ Conan); Tizen Studio CLI for .tpk packaging manifest)
- `start_green_stay_green/generators/readme.py` — `_generate_cpp_readme`

## Tasks

- [ ] Register / validate the language in the CLI path
- [ ] Generate a CMake (+ Conan); Tizen Studio CLI for .tpk packaging dependency manifest
- [ ] Generate the project directory structure incl. the Tizen (Samsung Galaxy Watch, native) target
- [ ] Generate a language-appropriate README

## Acceptance Criteria

- [ ] `green init -l cpp` creates a buildable Tizen (Samsung Galaxy Watch, native) skeleton
- [ ] `validate_language("cpp")` passes; unknown languages still raise
- [ ] Target Tizen native watch apps: Tizen native API, EFL/Dali UI, `.tpk` packaging via Tizen Studio CLI, CMake build. The `cpp` slug should accept both C and C++ projects.

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
