## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **Swift**
(watchOS / Apple Watch).

**Current state:** `templates/swift/` is `.gitkeep` only and `swift` is **absent from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No generator branch handles Swift — it is unsupported despite being advertised in CLAUDE.md.

Generated project must include a watchOS app/extension target (SwiftUI + WatchKit); CI must build for the watchOS simulator (`xcodebuild ... -destination 'platform=watchOS Simulator'`).

## Goal

Add production-grade **Swift** support so
`green init -l swift` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

| Concern | Tooling |
|---|---|
| Test framework | XCTest (+ swift-testing) |
| Linters | SwiftLint |
| Formatters | swift-format |
| Security | SwiftLint security rules + gitleaks (shared) + Periphery |
| Coverage | swift test --enable-code-coverage → llvm-cov (≥90%) |
| Complexity | SwiftLint cyclomatic_complexity (≤10) |
| Architecture enforcement | SwiftLint custom rules (no native layer linter; document limits) |
| Package manager | Swift Package Manager (SPM) |
| Versions | Swift 5.9, 5.10, 6.0 |


## Sub-Issues (gap-driven)

Only the generator cells Swift is actually missing are filed:

1. **Foundation** — registration, CLI & scaffolding
2. **Quality tooling** — pre-commit, scripts, metrics & architecture
3. **CI pipeline** — ci.py config + GitHub Actions workflow
4. **Tests & coverage** — unit / integration / e2e
5. **Documentation** — CLAUDE.md, README, CLI reference, SPEC

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l swift` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l swift` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for Swift is fully ✅
- [ ] CLAUDE.md / README list Swift as fully supported

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
