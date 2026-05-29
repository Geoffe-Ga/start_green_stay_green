## Context

Sub-issue of the **C / C++ (Tizen (Samsung Galaxy Watch, native))** epic. "Stay Green"
depends on native quality tooling. Today `precommit.py`, `scripts.py`, and
`metrics.py` only handle python/typescript/go/rust, and `architecture.py` only
python/typescript — so C / C++ projects generate without enforceable
quality gates (and pre-commit generation may raise outright).

**Depends on:** the Foundation work (language must be registered first).

## Goal

Wire the full C / C++ quality toolchain into the generated project so
`pre-commit run --all-files` enforces format, lint, type/security, coverage, and
complexity from day one.

## Scope — files to touch

- `start_green_stay_green/generators/precommit.py` — add `cpp` to
  `LANGUAGE_CONFIGS` / hook builders (`_validate_language_supported:398`,
  `get_language_hooks`)
- `start_green_stay_green/generators/scripts.py` — add `cpp` branch
  (`scripts.py:121`) emitting check/test/lint/format/security scripts
- `start_green_stay_green/generators/metrics.py` — add `cpp` metric config
  (`metrics.py:211`) for coverage/complexity/lint
- `start_green_stay_green/generators/architecture.py` — extend
  `supported_languages` (`architecture.py:94`) with `cpp` dependency
  enforcement via include-what-you-use / cpp-dependencies (document limits)

## Tooling to wire

- **Format:** clang-format
- **Lint:** clang-tidy + cppcheck
- **Security:** cppcheck + clang static analyzer + flawfinder
- **Test/coverage:** GoogleTest (gtest) → gcov/lcov (≥90%)
- **Complexity:** lizard / clang-tidy cognitive-complexity (≤10)
- **Architecture:** include-what-you-use / cpp-dependencies (document limits)

## Acceptance Criteria

- [ ] Generated `.pre-commit-config.yaml` includes working C / C++ hooks
- [ ] `./scripts/check-all.sh` runs the C / C++ toolchain and fails on violations
- [ ] Metrics dashboard reports coverage/complexity for C / C++
- [ ] Architecture enforcement emits a config for C / C++

## Quality Gates (non-negotiable)

- [ ] `pre-commit run --all-files` passes (all hooks)
- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0
- [ ] Docstring coverage ≥95% on new/changed code
- [ ] No new `# noqa` / `type: ignore` without an issue reference
- [ ] CI green (Gate 2) and review LGTM (Gate 3)

## References

- `start_green_stay_green/generators/precommit.py:398`
- `start_green_stay_green/generators/scripts.py:121`
- `start_green_stay_green/generators/metrics.py:211`
- `start_green_stay_green/generators/architecture.py:94`
