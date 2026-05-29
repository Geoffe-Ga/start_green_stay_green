## Context

Sub-issue of the **C / C++ (Tizen (Samsung Galaxy Watch, native))** epic. Gate 2 is a
green CI pipeline. `ci.py` drives `LANGUAGE_CONFIGS` and the generated GitHub
Actions workflow, which must build and test on the actual target.

**Depends on:** Foundation + Quality sub-issues.

## Goal

Generate a GitHub Actions pipeline that builds, tests, lints, and security-scans
a C / C++ (Tizen (Samsung Galaxy Watch, native)) project across C11/C17, C++17/C++20.

## Scope — files to touch

- `start_green_stay_green/generators/ci.py` — add the `cpp` entry to
  `LANGUAGE_CONFIGS` (`ci.py:40`): test_framework=GoogleTest (gtest),
  linters=clang-tidy + cppcheck, formatters=clang-format, security_tools=cppcheck + clang static analyzer + flawfinder,
  supported_versions=C11/C17, C++17/C++20, package_manager=CMake (+ Conan); Tizen Studio CLI for .tpk packaging
- `start_green_stay_green/generators/github_actions.py` — render C / C++
  setup/build/test steps
- keep CI ⇄ local pre-commit hook parity

## Tasks

- [ ] Add the `cpp` `LANGUAGE_CONFIGS` entry
- [ ] Render a version matrix (C11/C17, C++17/C++20)
- [ ] Target Tizen native watch apps: Tizen native API, EFL/Dali UI, `.tpk` packaging via Tizen Studio CLI, CMake build. The `cpp` slug should accept both C and C++ projects.
- [ ] Emit a coverage gate step (gcov/lcov (≥90%))

## Acceptance Criteria

- [ ] Generated workflow YAML lints clean (actionlint)
- [ ] Workflow builds for the Tizen (Samsung Galaxy Watch, native) target
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
