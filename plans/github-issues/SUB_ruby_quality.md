## Context

Sub-issue of the **Ruby (general)** epic. "Stay Green"
depends on native quality tooling. Today `precommit.py`, `scripts.py`, and
`metrics.py` only handle python/typescript/go/rust, and `architecture.py` only
python/typescript — so Ruby projects generate without enforceable
quality gates (and pre-commit generation may raise outright).

**Depends on:** the Foundation work (language must be registered first).

## Goal

Wire the full Ruby quality toolchain into the generated project so
`pre-commit run --all-files` enforces format, lint, type/security, coverage, and
complexity from day one.

## Scope — files to touch

- `start_green_stay_green/generators/precommit.py` — add `ruby` to
  `LANGUAGE_CONFIGS` / hook builders (`_validate_language_supported:398`,
  `get_language_hooks`)
- `start_green_stay_green/generators/scripts.py` — add `ruby` branch
  (`scripts.py:121`) emitting check/test/lint/format/security scripts
- `start_green_stay_green/generators/metrics.py` — add `ruby` metric config
  (`metrics.py:211`) for coverage/complexity/lint
- `start_green_stay_green/generators/architecture.py` — extend
  `supported_languages` (`architecture.py:94`) with `ruby` dependency
  enforcement via Packwerk

## Tooling to wire

- **Format:** RuboCop (--autocorrect)
- **Lint:** RuboCop
- **Security:** Brakeman + bundler-audit
- **Test/coverage:** RSpec → SimpleCov (≥90%)
- **Complexity:** RuboCop Metrics / flog (≤10)
- **Architecture:** Packwerk

## Acceptance Criteria

- [ ] Generated `.pre-commit-config.yaml` includes working Ruby hooks
- [ ] `./scripts/check-all.sh` runs the Ruby toolchain and fails on violations
- [ ] Metrics dashboard reports coverage/complexity for Ruby
- [ ] Architecture enforcement emits a config for Ruby

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
