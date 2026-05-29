## Context

Sub-issue of the **Swift (watchOS / Apple Watch)** epic. Gate 2 is a
green CI pipeline. `ci.py` drives `LANGUAGE_CONFIGS` and the generated GitHub
Actions workflow, which must build and test on the actual target.

**Depends on:** Foundation + Quality sub-issues.

## Goal

Generate a GitHub Actions pipeline that builds, tests, lints, and security-scans
a Swift (watchOS / Apple Watch) project across Swift 5.9, 5.10, 6.0.

## Scope — files to touch

- `start_green_stay_green/generators/ci.py` — add the `swift` entry to
  `LANGUAGE_CONFIGS` (`ci.py:40`): test_framework=XCTest (+ swift-testing),
  linters=SwiftLint, formatters=swift-format, security_tools=SwiftLint security rules + gitleaks (shared) + Periphery,
  supported_versions=Swift 5.9, 5.10, 6.0, package_manager=Swift Package Manager (SPM)
- `start_green_stay_green/generators/github_actions.py` — render Swift
  setup/build/test steps
- keep CI ⇄ local pre-commit hook parity

## Tasks

- [ ] Add the `swift` `LANGUAGE_CONFIGS` entry
- [ ] Render a version matrix (Swift 5.9, 5.10, 6.0)
- [ ] Generated project must include a watchOS app/extension target (SwiftUI + WatchKit); CI must build for the watchOS simulator (`xcodebuild ... -destination 'platform=watchOS Simulator'`).
- [ ] Emit a coverage gate step (swift test --enable-code-coverage → llvm-cov (≥90%))

## Acceptance Criteria

- [ ] Generated workflow YAML lints clean (actionlint)
- [ ] Workflow builds for the watchOS / Apple Watch target
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
