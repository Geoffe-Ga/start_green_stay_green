## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **C / C++**
(Tizen (Samsung Galaxy Watch, native)).

**Current state:** C/C++ is **completely absent**: no `templates/cpp/`, not in `SUPPORTED_LANGUAGES`, no generator branches. Full greenfield.

Target Tizen native watch apps: Tizen native API, EFL/Dali UI, `.tpk` packaging via Tizen Studio CLI, CMake build. The `cpp` slug should accept both C and C++ projects.

## Goal

Add production-grade **C / C++** support so
`green init -l cpp` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

| Concern | Tooling |
|---|---|
| Test framework | GoogleTest (gtest) |
| Linters | clang-tidy + cppcheck |
| Formatters | clang-format |
| Security | cppcheck + clang static analyzer + flawfinder |
| Coverage | gcov/lcov (≥90%) |
| Complexity | lizard / clang-tidy cognitive-complexity (≤10) |
| Architecture enforcement | include-what-you-use / cpp-dependencies (document limits) |
| Package manager | CMake (+ Conan); Tizen Studio CLI for .tpk packaging |
| Versions | C11/C17, C++17/C++20 |


## Sub-Issues (gap-driven)

Only the generator cells C / C++ is actually missing are filed:

1. **Foundation** — registration, CLI & scaffolding
2. **Quality tooling** — pre-commit, scripts, metrics & architecture
3. **CI pipeline** — ci.py config + GitHub Actions workflow
4. **Tests & coverage** — unit / integration / e2e
5. **Documentation** — CLAUDE.md, README, CLI reference, SPEC

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l cpp` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l cpp` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for C / C++ is fully ✅
- [ ] CLAUDE.md / README list C / C++ as fully supported

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
