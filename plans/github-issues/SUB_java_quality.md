## Context

Sub-issue of the **Java (Wear OS (legacy Android Wear))** epic. "Stay Green"
depends on native quality tooling. Today `precommit.py`, `scripts.py`, and
`metrics.py` only handle python/typescript/go/rust, and `architecture.py` only
python/typescript — so Java projects generate without enforceable
quality gates (and pre-commit generation may raise outright).

**Depends on:** the Foundation work (language must be registered first).

## Goal

Wire the full Java quality toolchain into the generated project so
`pre-commit run --all-files` enforces format, lint, type/security, coverage, and
complexity from day one.

## Scope — files to touch

- `start_green_stay_green/generators/precommit.py` — add `java` to
  `LANGUAGE_CONFIGS` / hook builders (`_validate_language_supported:398`,
  `get_language_hooks`)
- `start_green_stay_green/generators/scripts.py` — add `java` branch
  (`scripts.py:121`) emitting check/test/lint/format/security scripts
- `start_green_stay_green/generators/metrics.py` — add `java` metric config
  (`metrics.py:211`) for coverage/complexity/lint
- `start_green_stay_green/generators/architecture.py` — extend
  `supported_languages` (`architecture.py:94`) with `java` dependency
  enforcement via ArchUnit

## Tooling to wire

- **Format:** google-java-format
- **Lint:** Checkstyle + PMD + SpotBugs
- **Security:** SpotBugs + FindSecBugs + OWASP dependency-check
- **Test/coverage:** JUnit5 → JaCoCo (≥90%)
- **Complexity:** PMD CyclomaticComplexity / Checkstyle (≤10)
- **Architecture:** ArchUnit

## Acceptance Criteria

- [ ] Generated `.pre-commit-config.yaml` includes working Java hooks
- [ ] `./scripts/check-all.sh` runs the Java toolchain and fails on violations
- [ ] Metrics dashboard reports coverage/complexity for Java
- [ ] Architecture enforcement emits a config for Java

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
