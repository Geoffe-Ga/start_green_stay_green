# Changelog

All notable changes to **Start Green Stay Green** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions before `1.0.0` were unreleased internal milestones; the
`1.0.0` line collects every roadmap phase that landed before the
first tagged release.

## [Unreleased]

Phase 6 follow-ups in progress (issues #316–#319).

### Added

- **Swift (watchOS) language support** — `green init --language swift`
  generates an SPM package (watchOS app scaffold, Swift 5.9/5.10/6.0)
  with the full quality stack: swift-format + SwiftLint pre-commit hooks
  and scripts (complexity ≤10), XCTest with a ≥90% llvm-cov coverage
  gate, gitleaks/detect-secrets secret scanning, Periphery dead-code
  analysis, SwiftLint custom-rule architecture enforcement, and a
  macOS-runner CI pipeline with a Swift version matrix plus a
  watchOS-simulator build-and-test job. Foundation (#351), quality
  tooling (#352), CI pipeline (#353), tests (#354), documentation
  (#355). A real generated example lives in `examples/swift/`.

- **Kotlin (Wear OS) language support** — `green init --language kotlin`
  generates a Gradle (Kotlin DSL) Wear OS app scaffold (Galaxy Watch 4+ /
  Wear OS 3, Jetpack Compose for Wear OS, Kotlin 2.0 on JDK 17/21) with
  the full quality stack: ktlint + detekt pre-commit hooks and scripts
  (complexity ≤10), JUnit tests with a ≥90% Kover coverage gate,
  gitleaks/detect-secrets secret scanning, OWASP dependency-check CVE
  scanning, Konsist architecture enforcement, and an ubuntu-runner CI
  pipeline with a JDK 17/21 test matrix plus a Wear OS debug-APK build.
  Foundation (#356), quality tooling (#357), CI pipeline (#358), tests
  (#359), documentation (#360). A real generated example lives in
  `examples/kotlin/`.

- **C/C++ (Tizen native) language support** — `green init --language cpp`
  generates a Tizen native watch-app scaffold (Samsung Galaxy Watch,
  appcore `watch_app` lifecycle + EFL UI) with a deliberate two-build
  split: the pure-logic library and its Catch2 tests build with plain
  CMake ≥3.20 + Conan 2 (C++17 pinned) on any host, while `.tpk`
  packaging stays a local Tizen Studio CLI step. Full quality stack:
  clang-format + clang-tidy + cppcheck pre-commit hooks and scripts,
  lizard complexity gate (≤10), a ≥90% gcov/lcov coverage gate,
  gitleaks/detect-secrets secret scanning, flawfinder CWE-mapped
  dangerous-API scanning, a stdlib-Python include-boundary architecture
  checker, and an ubuntu-24.04 CI pipeline that runs the generated
  scripts themselves with a gcc/clang build-and-test matrix. Foundation
  (#361), quality tooling (#362), CI pipeline (#363), tests (#364),
  documentation (#365). A real generated example lives in
  `examples/cpp/`. Also fixed with #365: the generated Swift README now
  advertises its real CI pipeline (generated since #353) instead of
  listing CI/CD as planned.

- **Java (Wear OS legacy Android Wear) language support** —
  `green init --language java` generates a legacy Android Wear
  watch-app scaffold — the maintenance path for existing Java watch
  apps — with a deliberate two-build split: the pure-logic sources and
  their JUnit 4 tests build with plain Maven (Java 17) on any host,
  while the watch APK stays an Android-tooling (Android Studio /
  Gradle) build the generator does not scaffold. Full quality stack:
  google-java-format plus Checkstyle/PMD/SpotBugs pre-commit hooks as
  Maven goals, a PMD cyclomatic-complexity gate (≤10,
  `pmd-ruleset.xml`), a ≥90% JaCoCo line-coverage gate bound in
  `pom.xml`, gitleaks/detect-secrets secret scanning, OWASP
  dependency-check CVE scanning (NVD_API_KEY-gated), an ArchUnit
  architecture test, and an ubuntu CI pipeline with a JDK 17/21
  (Temurin) matrix running the same Maven goals as the local build.
  Foundation (#366), quality tooling (#367), tests (#368),
  documentation (#369). A real generated example lives in
  `examples/java/`.

- **C# (.NET) language support** — `green init --language csharp`
  generates a general .NET 8 scaffold (a console app plus xUnit tests
  compiling into one assembly) where every quality gate runs inside
  the dotnet CLI and the generated `.csproj` is the single source of
  the quality policy: Roslyn analyzers with warnings-as-errors in
  every build, dotnet format in check mode as a pre-commit hook, a
  CA1502 cyclomatic-complexity gate (≤10, bound in
  `CodeMetricsConfig.txt`), a ≥90% Coverlet line-coverage gate bound
  in the csproj, gitleaks/detect-secrets secret scanning, the
  SecurityCodeScan analyzer plus a `dotnet list package --vulnerable`
  CVE scan, a NetArchTest architecture test, and an ubuntu CI pipeline
  on the .NET 8 SDK running the same dotnet gates as the local build.
  Quality tooling on the foundation scaffold + CI (#370), tests
  (#371), documentation (#372). A real generated example lives in
  `examples/csharp/`.

- **Ruby language support** — `green init --language ruby` generates
  a plain-Ruby scaffold (a `lib/` module plus RSpec specs) where
  RuboCop is one tool wearing four hats — formatter (Layout cops),
  linter (Lint/Style), cyclomatic-complexity gate (≤10 via
  `Metrics/CyclomaticComplexity`), and source-level security (the
  Security cop department) — with the generated `.rubocop.yml` as the
  single home of that whole policy. The toolchain: a check-mode
  RuboCop pre-commit hook from the official rubocop/rubocop manifest
  (the upstream `--autocorrect` default overridden), RSpec with a
  ≥90% SimpleCov line-coverage gate bound in `spec/spec_helper.rb`
  and activated by `COVERAGE=true`, gitleaks/detect-secrets secret
  scanning, a bundler-audit dependency CVE scan (Brakeman is
  documented as the add-on for when Rails is adopted — it errors on
  plain-Ruby projects), parked Packwerk architecture-boundary
  templates, and an ubuntu CI pipeline with a Ruby 3.3/3.4 matrix
  running the same gates as the local build. Quality tooling on the
  foundation scaffold + CI (#373), tests (#374), documentation
  (#375). A real generated example lives in `examples/ruby/`.

## [1.0.0] — 2026-05-10

First tagged release. Bundles the entire claude-init optimization
roadmap (Phases 0 → 5b).

### Added

- **`green enhance` command** (Phase 3b, [#309]) — re-run Pass 2 (AI
  tuning) over an existing `green init` project without
  re-scaffolding. Useful after `--offline` initial runs or after
  reference subagents change in this repo.
- **`green enhance --batch` and `--wait` flags** (Phase 5b, [#315]) —
  submit subagent tunings via the Anthropic Message Batches API for
  a 50 % cost discount at the price of a ≤24 h SLA. Two-call submit-
  then-resume by default; `--wait` blocks in-process. See
  [`plans/architecture/ADR-001-batch-enhance.md`](plans/architecture/ADR-001-batch-enhance.md).
- **`green init --offline` and `--no-enhance` flags** (Phase 3a,
  [#308]) — split init into a deterministic Pass 1 scaffold + an
  optional Pass 2 polish so users without an API key (or who don't
  want the polish today) get a complete project in ~3 s.
- **`.claude/.enhance-state.json` resume cursor** (Phase 3c, [#310])
  — `green enhance` skips targets whose source content hasn't
  changed since the last successful run; `--force` overrides.
- **Anthropic Message Batches API primitives** (Phase 5a, [#313]):
  `submit_tool_use_batch`, `poll_batch`, `fetch_batch_results` on
  `AIOrchestrator`; `BatchProgress` state extension; new
  `start_green_stay_green/ai/types.py` shared types module breaking
  the orchestrator ↔ batch import cycle.
- **6-component prompt templates** (Phase 4, [#312]) — every
  generator prompt hoisted into Jinja2 templates under
  `start_green_stay_green/ai/prompts/templates/`, each conforming to
  the Role / Goal / Context / Format / Examples / Constraints
  framework.
- **Prompt caching + `tool_use` structured output** (Phase 2c,
  [#311]) — system blocks now carry `cache_control` markers so
  identical prefixes hit Anthropic's cache; tuning results return
  via the `report_tuning` tool schema instead of free-text JSON.
- **Language-specific setup instructions** in `green init` output
  (#279).
- **`await-claude-review`, `address-feedback`, and Phase-5 skills**
  imported from `well-worn-tools` ([#303], [#314]).

### Changed

- **Default `green init` is two-pass** (Phase 3a, [#308]). Pass 1
  (deterministic scaffold) writes a complete project in ~3 s; Pass 2
  (AI polish) runs in parallel afterwards. Fall back to Pass 1 only
  with `--offline` or `--no-enhance`.
- **AI-orchestrated generation runs in parallel** (Phase 2, [#305])
  — `asyncio.gather` over the per-target tunings instead of
  sequential awaits. ~3× speedup on the AI-bound segment.
- **Generator prompts share a cache prefix** (Phase 2c, [#311]). The
  system blocks for `claude_md_tune`, `ci_enhance`, and
  `content_tune` are byte-identical across runs so Anthropic's
  prompt cache hits; observed ~80 % cache-hit rate on the second
  invocation in a row.
- **`green init`'s "Skipped (no API key)" steps removed** (Phase 3a,
  [#308]) — the new two-pass model means Pass 1 always succeeds and
  Pass 2 is gated explicitly by `--offline` / `--no-enhance` /
  presence of `ANTHROPIC_API_KEY`. Behavior change worth calling
  out: a user without a key now sees a complete (Pass-1-only)
  project rather than a partially-scaffolded one with explicit
  skips.

### Deprecated

- **`green init --api-key VALUE`** (since #308). The flag still
  works but is hidden from `--help` because passing secrets via
  argv leaks them into shell history and `ps` listings. Use
  `ANTHROPIC_API_KEY` in the environment or the system keyring
  (prompted automatically) instead. Removal is targeted for the
  next minor release.

### Fixed

- TypeScript projects with Prettier no longer fail their own quality
  gates (#287).
- Pre-commit version drift on Black (#289).
- Dependency upgrades for `pyupgrade` / `refurb` Python 3.14 compat
  (#290).
- Language deduplication in `_get_setup_instructions` (#288).
- Dependabot allowed in `claude-review` workflow (#278).

### Performance

- **`green init --offline`**: ~3 s wall clock, 0 API calls.
- **`green init` (default, two-pass)**: ~6–10 s wall clock, ≤3 API
  calls (one per Pass-2 target). Down from ~25–40 s pre-Phase-2.
- **`green enhance`**: ~3–6 s wall clock, ≤3 API calls.
- **`green enhance --batch`**: minutes – hours wall clock (gated by
  the Anthropic SLA), ≤3 API calls, 50 % cost vs sync.

Numbers are rough order-of-magnitude on a Mac M-series with the
default model; see `plans/2026-05-03-claude-init-optimization-roadmap.md`
for the methodology.

### Tests + quality

- **1783 unit + integration/e2e tests** (was ~1700 pre-roadmap).
- **Coverage 92.92 %** (threshold 90 %).
- All five CI gate scripts (lint, format, typecheck, security,
  complexity) pass; every function grade A under xenon.

[#303]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/303
[#308]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/308
[#309]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/309
[#310]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/310
[#311]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/311
[#312]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/312
[#313]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/313
[#314]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/314
[#315]: https://github.com/Geoffe-Ga/start_green_stay_green/pull/315
[Unreleased]: https://github.com/Geoffe-Ga/start_green_stay_green/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Geoffe-Ga/start_green_stay_green/releases/tag/v1.0.0
