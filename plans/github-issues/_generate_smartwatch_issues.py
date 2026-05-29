#!/usr/bin/env python3
"""Generate GitHub issue bodies for full language-support parity.

Strategy: gap-driven per-language epics under one umbrella parity epic.
Each language only gets sub-issues for the generator cells it is actually
missing (verified against generators/*.py). Already-green cells (python,
typescript) get no work. `templates/<lang>/` is intentionally NOT treated as a
gap: every language ships only `.gitkeep` there yet python works, so
generation is code-based and the dir is vestigial.

Run from repo root:  python plans/github-issues/_generate_smartwatch_issues.py
"""

from __future__ import annotations

from pathlib import Path

OUT = Path("plans/github-issues")

# --------------------------------------------------------------------------- #
# Tooling matrix per language (content engineers implement against).
# --------------------------------------------------------------------------- #
TOOLING: dict[str, dict[str, str]] = {
    "swift": {
        "test": "XCTest (+ swift-testing)",
        "lint": "SwiftLint",
        "format": "swift-format",
        "security": "SwiftLint security rules + gitleaks (shared) + Periphery",
        "coverage": "swift test --enable-code-coverage → llvm-cov (≥90%)",
        "complexity": "SwiftLint cyclomatic_complexity (≤10)",
        "architecture": "SwiftLint custom rules (no native layer linter; document limits)",
        "pkg": "Swift Package Manager (SPM)",
        "versions": "Swift 5.9, 5.10, 6.0",
    },
    "kotlin": {
        "test": "JUnit5 + Kotest",
        "lint": "detekt + ktlint",
        "format": "ktlint (or ktfmt)",
        "security": "detekt security ruleset + OWASP dependency-check",
        "coverage": "Kover (or JaCoCo) (≥90%)",
        "complexity": "detekt ComplexMethod (≤10)",
        "architecture": "Konsist (or ArchUnit)",
        "pkg": "Gradle (Kotlin DSL)",
        "versions": "Kotlin 1.9 / 2.0; JDK 17, 21",
    },
    "cpp": {
        "test": "GoogleTest (gtest)",
        "lint": "clang-tidy + cppcheck",
        "format": "clang-format",
        "security": "cppcheck + clang static analyzer + flawfinder",
        "coverage": "gcov/lcov (≥90%)",
        "complexity": "lizard / clang-tidy cognitive-complexity (≤10)",
        "architecture": "include-what-you-use / cpp-dependencies (document limits)",
        "pkg": "CMake (+ Conan); Tizen Studio CLI for .tpk packaging",
        "versions": "C11/C17, C++17/C++20",
    },
    "java": {
        "test": "JUnit5",
        "lint": "Checkstyle + PMD + SpotBugs",
        "format": "google-java-format",
        "security": "SpotBugs + FindSecBugs + OWASP dependency-check",
        "coverage": "JaCoCo (≥90%)",
        "complexity": "PMD CyclomaticComplexity / Checkstyle (≤10)",
        "architecture": "ArchUnit",
        "pkg": "Maven (matches existing ci.py config)",
        "versions": "JDK 11, 17, 21",
    },
    "csharp": {
        "test": "xUnit",
        "lint": "Roslyn analyzers",
        "format": "dotnet format",
        "security": "security-code-scan + dotnet list package --vulnerable",
        "coverage": "Coverlet (≥90%)",
        "complexity": "Roslyn / SonarAnalyzer.CSharp (≤10)",
        "architecture": "NetArchTest (or ArchUnitNET)",
        "pkg": "NuGet",
        "versions": ".NET 6.0, 8.0",
    },
    "ruby": {
        "test": "RSpec",
        "lint": "RuboCop",
        "format": "RuboCop (--autocorrect)",
        "security": "Brakeman + bundler-audit",
        "coverage": "SimpleCov (≥90%)",
        "complexity": "RuboCop Metrics / flog (≤10)",
        "architecture": "Packwerk",
        "pkg": "Bundler",
        "versions": "Ruby 3.1, 3.2",
    },
    "go": {
        "test": "go test",
        "lint": "golangci-lint",
        "format": "gofmt",
        "security": "gosec",
        "coverage": "go test -coverprofile (≥90%)",
        "complexity": "gocyclo (≤10)",
        "architecture": "go-arch-lint (or depguard via golangci-lint)",
        "pkg": "Go modules",
        "versions": "Go 1.21, 1.22",
    },
    "rust": {
        "test": "cargo test",
        "lint": "clippy",
        "format": "rustfmt",
        "security": "cargo-audit",
        "coverage": "cargo-llvm-cov (≥90%)",
        "complexity": "clippy cognitive_complexity (≤10)",
        "architecture": "cargo-deny / cargo-modules",
        "pkg": "Cargo",
        "versions": "Rust 1.70, 1.75",
    },
}

# --------------------------------------------------------------------------- #
# Per-language plan: mode, gaps (which component sub-issues to emit), context.
# Components: foundation, quality, ci, tests, docs. go/rust use a single
# "architecture" issue instead of an epic.
# --------------------------------------------------------------------------- #
LANGUAGES: dict[str, dict] = {
    "swift": {
        "display": "Swift",
        "platform": "watchOS / Apple Watch",
        "verb": "Add",
        "kind": "epic",
        "subs": ["foundation", "quality", "ci", "tests", "docs"],
        "status": (
            "`templates/swift/` is `.gitkeep` only and `swift` is **absent "
            "from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No "
            "generator branch handles Swift — it is unsupported despite being "
            "advertised in CLAUDE.md."
        ),
        "platform_notes": (
            "Generated project must include a watchOS app/extension target "
            "(SwiftUI + WatchKit); CI must build for the watchOS simulator "
            "(`xcodebuild ... -destination 'platform=watchOS Simulator'`)."
        ),
    },
    "kotlin": {
        "display": "Kotlin",
        "platform": "Wear OS (Google / Samsung Galaxy Watch 4+)",
        "verb": "Add",
        "kind": "epic",
        "subs": ["foundation", "quality", "ci", "tests", "docs"],
        "status": (
            "`templates/kotlin/` is `.gitkeep` only and `kotlin` is **absent "
            "from `SUPPORTED_LANGUAGES`** (generators/base.py:20). No "
            "generator branch handles Kotlin."
        ),
        "platform_notes": (
            "Generated project must target Wear OS: Jetpack Compose for "
            "Wear OS (androidx.wear.compose) and the Wear OS SDK, with an "
            "Android Gradle module set to a `wear` device profile."
        ),
    },
    "cpp": {
        "display": "C / C++",
        "platform": "Tizen (Samsung Galaxy Watch, native)",
        "verb": "Add",
        "kind": "epic",
        "subs": ["foundation", "quality", "ci", "tests", "docs"],
        "status": (
            "C/C++ is **completely absent**: no `templates/cpp/`, not in "
            "`SUPPORTED_LANGUAGES`, no generator branches. Full greenfield."
        ),
        "platform_notes": (
            "Target Tizen native watch apps: Tizen native API, EFL/Dali UI, "
            "`.tpk` packaging via Tizen Studio CLI, CMake build. The `cpp` "
            "slug should accept both C and C++ projects."
        ),
    },
    "java": {
        "display": "Java",
        "platform": "Wear OS (legacy Android Wear)",
        "verb": "Complete",
        "kind": "epic",
        "subs": ["foundation", "quality", "tests", "docs"],
        "status": (
            "Java is registered and has `ci.py`/`dependencies.py`/"
            "`structure.py`/`readme.py`/`tests_gen.py` entries, but is "
            "**missing from `precommit.py`, `scripts.py`, `metrics.py`, and "
            "`architecture.py`** — so generating pre-commit config for Java "
            "raises today. Scaffolding is generic, not Wear OS."
        ),
        "platform_notes": (
            "Foundation work here is the Wear OS angle: extend scaffolding to "
            "a legacy Android Wear app (Wearable Support Library / "
            "androidx.wear), the common path for maintaining existing Java "
            "watch apps."
        ),
    },
    "csharp": {
        "display": "C#",
        "platform": "general .NET",
        "verb": "Complete",
        "kind": "epic",
        "subs": ["quality", "tests", "docs"],
        "status": (
            "C# is registered with `ci.py`/`dependencies.py`/`structure.py`/"
            "`readme.py`/`tests_gen.py` entries, but is **missing from "
            "`precommit.py`, `scripts.py`, `metrics.py`, and "
            "`architecture.py`** — pre-commit generation raises for C#."
        ),
        "platform_notes": (
            "No smartwatch platform; this closes parity gaps so C# matches "
            "python/typescript as a fully green target."
        ),
    },
    "ruby": {
        "display": "Ruby",
        "platform": "general",
        "verb": "Complete",
        "kind": "epic",
        "subs": ["quality", "tests", "docs"],
        "status": (
            "Ruby is registered with `ci.py`/`dependencies.py`/`structure.py`/"
            "`readme.py`/`tests_gen.py` entries, but is **missing from "
            "`precommit.py`, `scripts.py`, `metrics.py`, and "
            "`architecture.py`** — pre-commit generation raises for Ruby."
        ),
        "platform_notes": (
            "No smartwatch platform; closes parity gaps so Ruby matches "
            "python/typescript as a fully green target."
        ),
    },
    "go": {
        "display": "Go",
        "platform": "general",
        "verb": "Complete",
        "kind": "single",  # one issue: architecture parity only
        "subs": ["architecture"],
        "status": (
            "Go is wired into precommit/scripts/metrics/ci, but is **missing "
            "from `architecture.py`** (`supported_languages = {python, "
            "typescript}` at architecture.py:94). Architecture enforcement is "
            "the only parity gap."
        ),
        "platform_notes": "",
    },
    "rust": {
        "display": "Rust",
        "platform": "general",
        "verb": "Complete",
        "kind": "single",
        "subs": ["architecture"],
        "status": (
            "Rust is wired into precommit/scripts/metrics/ci, but is "
            "**missing from `architecture.py`** (architecture.py:94). "
            "Architecture enforcement is the only parity gap."
        ),
        "platform_notes": "",
    },
}


def gates() -> str:
    return (
        "## Quality Gates (non-negotiable)\n\n"
        "- [ ] `pre-commit run --all-files` passes (all hooks)\n"
        "- [ ] Repo coverage stays ≥90%, every function complexity ≤10, pylint ≥9.0\n"
        "- [ ] Docstring coverage ≥95% on new/changed code\n"
        "- [ ] No new `# noqa` / `type: ignore` without an issue reference\n"
        "- [ ] CI green (Gate 2) and review LGTM (Gate 3)\n"
    )


def tool_table(slug: str) -> str:
    t = TOOLING[slug]
    return (
        "| Concern | Tooling |\n|---|---|\n"
        f"| Test framework | {t['test']} |\n"
        f"| Linters | {t['lint']} |\n"
        f"| Formatters | {t['format']} |\n"
        f"| Security | {t['security']} |\n"
        f"| Coverage | {t['coverage']} |\n"
        f"| Complexity | {t['complexity']} |\n"
        f"| Architecture enforcement | {t['architecture']} |\n"
        f"| Package manager | {t['pkg']} |\n"
        f"| Versions | {t['versions']} |\n"
    )


SUB_LABELS = {
    "foundation": "Foundation: registration, CLI & scaffolding",
    "quality": "Quality tooling: pre-commit, scripts, metrics & architecture",
    "ci": "CI pipeline: ci.py config + GitHub Actions workflow",
    "tests": "Tests & coverage: unit / integration / e2e",
    "docs": "Documentation: CLAUDE.md, README, CLI reference, SPEC",
    "architecture": "Architecture-enforcement parity",
}


def short(display: str) -> str:
    return display.split(" /")[0].split(" ")[0].lower().replace("#", "sharp")


# --------------------------------------------------------------------------- #
# Body builders
# --------------------------------------------------------------------------- #
def epic_body(slug: str, lang: dict) -> str:
    sub_lines = "\n".join(
        f"{i}. **{SUB_LABELS[s].split(':')[0]}** — {SUB_LABELS[s].split(': ')[1]}"
        if ":" in SUB_LABELS[s]
        else f"{i}. **{SUB_LABELS[s]}**"
        for i, s in enumerate(lang["subs"], 1)
    )
    return f"""## Context

Part of the **language-support parity initiative**: every supported language
should be wired into every generator so `green init` produces a fully green
project regardless of language. This epic covers **{lang['display']}**
({lang['platform']}).

**Current state:** {lang['status']}

{lang['platform_notes']}

## Goal

{lang['verb']} production-grade **{lang['display']}** support so
`green init -l {slug}` generates a project that Starts Green and Stays Green
with the language's native quality tooling — passing all three gates.

## Target toolchain

{tool_table(slug)}

## Sub-Issues (gap-driven)

Only the generator cells {lang['display']} is actually missing are filed:

{sub_lines}

## Acceptance Criteria

- [ ] All sub-issues closed
- [ ] `green init -l {slug}` produces a project passing
      `pre-commit run --all-files` out of the box
- [ ] `green init -l python -l {slug}` (multi-language) works via the
      YAML-aware pre-commit merge
- [ ] Parity matrix row for {lang['display']} is fully ✅
- [ ] CLAUDE.md / README list {lang['display']} as fully supported

{gates()}
## References

- `start_green_stay_green/generators/base.py:20` — `SUPPORTED_LANGUAGES`
- `start_green_stay_green/generators/ci.py:40` — `LANGUAGE_CONFIGS`
- `start_green_stay_green/cli.py` — `_resolve_languages`, `_get_setup_instructions`
- `.claude/docs/quality-standards.md`, `reference/workflows/stay-green.md`
"""


def foundation_body(slug: str, lang: dict) -> str:
    new = lang["verb"] == "Add"
    reg = (
        f"add `\"{slug}\"` to `SUPPORTED_LANGUAGES`"
        if new
        else "confirm registration (already present) and extend scaffolding"
    )
    return f"""## Context

Foundational sub-issue of the **{lang['display']} ({lang['platform']})** epic —
every other {lang['display']} sub-issue depends on it.

**Current state:** {lang['status']}

## Goal

Make `green init -l {slug}` emit a valid {lang['platform']} project skeleton
with a {TOOLING[slug]['pkg']} manifest and generated README.

## Scope — files to touch

- `start_green_stay_green/generators/base.py` — {reg}; verify `validate_language`
- `start_green_stay_green/cli.py` — `--language` help (`cli.py:1036`, `:1613`),
  interactive prompt choices, `_get_setup_instructions` (`cli.py:1325`) for
  {TOOLING[slug]['pkg']}
- `start_green_stay_green/generators/structure.py` — `_generate_{slug}_structure`
  + dispatch entry ({lang['platform']} app target)
- `start_green_stay_green/generators/dependencies.py` —
  `_generate_{slug}_dependencies` ({TOOLING[slug]['pkg']} manifest)
- `start_green_stay_green/generators/readme.py` — `_generate_{slug}_readme`

## Tasks

- [ ] Register / validate the language in the CLI path
- [ ] Generate a {TOOLING[slug]['pkg']} dependency manifest
- [ ] Generate the project directory structure incl. the {lang['platform']} target
- [ ] Generate a language-appropriate README

## Acceptance Criteria

- [ ] `green init -l {slug}` creates a buildable {lang['platform']} skeleton
- [ ] `validate_language("{slug}")` passes; unknown languages still raise
- [ ] {lang['platform_notes'] or 'Scaffolding matches the python/typescript reference quality.'}

{gates()}
## References

- `start_green_stay_green/generators/base.py:20`
- `start_green_stay_green/generators/structure.py:128` (dispatch map)
- `start_green_stay_green/generators/dependencies.py:129` (dispatch map)
- `start_green_stay_green/generators/readme.py:155` (dispatch map)
"""


def quality_body(slug: str, lang: dict) -> str:
    t = TOOLING[slug]
    return f"""## Context

Sub-issue of the **{lang['display']} ({lang['platform']})** epic. "Stay Green"
depends on native quality tooling. Today `precommit.py`, `scripts.py`, and
`metrics.py` only handle python/typescript/go/rust, and `architecture.py` only
python/typescript — so {lang['display']} projects generate without enforceable
quality gates (and pre-commit generation may raise outright).

**Depends on:** the Foundation work (language must be registered first).

## Goal

Wire the full {lang['display']} quality toolchain into the generated project so
`pre-commit run --all-files` enforces format, lint, type/security, coverage, and
complexity from day one.

## Scope — files to touch

- `start_green_stay_green/generators/precommit.py` — add `{slug}` to
  `LANGUAGE_CONFIGS` / hook builders (`_validate_language_supported:398`,
  `get_language_hooks`)
- `start_green_stay_green/generators/scripts.py` — add `{slug}` branch
  (`scripts.py:121`) emitting check/test/lint/format/security scripts
- `start_green_stay_green/generators/metrics.py` — add `{slug}` metric config
  (`metrics.py:211`) for coverage/complexity/lint
- `start_green_stay_green/generators/architecture.py` — extend
  `supported_languages` (`architecture.py:94`) with `{slug}` dependency
  enforcement via {t['architecture']}

## Tooling to wire

- **Format:** {t['format']}
- **Lint:** {t['lint']}
- **Security:** {t['security']}
- **Test/coverage:** {t['test']} → {t['coverage']}
- **Complexity:** {t['complexity']}
- **Architecture:** {t['architecture']}

## Acceptance Criteria

- [ ] Generated `.pre-commit-config.yaml` includes working {lang['display']} hooks
- [ ] `./scripts/check-all.sh` runs the {lang['display']} toolchain and fails on violations
- [ ] Metrics dashboard reports coverage/complexity for {lang['display']}
- [ ] Architecture enforcement emits a config for {lang['display']}

{gates()}
## References

- `start_green_stay_green/generators/precommit.py:398`
- `start_green_stay_green/generators/scripts.py:121`
- `start_green_stay_green/generators/metrics.py:211`
- `start_green_stay_green/generators/architecture.py:94`
"""


def ci_body(slug: str, lang: dict) -> str:
    t = TOOLING[slug]
    return f"""## Context

Sub-issue of the **{lang['display']} ({lang['platform']})** epic. Gate 2 is a
green CI pipeline. `ci.py` drives `LANGUAGE_CONFIGS` and the generated GitHub
Actions workflow, which must build and test on the actual target.

**Depends on:** Foundation + Quality sub-issues.

## Goal

Generate a GitHub Actions pipeline that builds, tests, lints, and security-scans
a {lang['display']} ({lang['platform']}) project across {t['versions']}.

## Scope — files to touch

- `start_green_stay_green/generators/ci.py` — add the `{slug}` entry to
  `LANGUAGE_CONFIGS` (`ci.py:40`): test_framework={t['test']},
  linters={t['lint']}, formatters={t['format']}, security_tools={t['security']},
  supported_versions={t['versions']}, package_manager={t['pkg']}
- `start_green_stay_green/generators/github_actions.py` — render {lang['display']}
  setup/build/test steps
- keep CI ⇄ local pre-commit hook parity

## Tasks

- [ ] Add the `{slug}` `LANGUAGE_CONFIGS` entry
- [ ] Render a version matrix ({t['versions']})
- [ ] {lang['platform_notes'] or 'Standard build/test steps.'}
- [ ] Emit a coverage gate step ({t['coverage']})

## Acceptance Criteria

- [ ] Generated workflow YAML lints clean (actionlint)
- [ ] Workflow builds for the {lang['platform']} target
- [ ] Coverage threshold enforced in CI (≥90%)

{gates()}
## References

- `start_green_stay_green/generators/ci.py:40` — `LANGUAGE_CONFIGS`
- `start_green_stay_green/generators/github_actions.py`
"""


def tests_body(slug: str, lang: dict) -> str:
    return f"""## Context

Sub-issue of the **{lang['display']} ({lang['platform']})** epic. No code lands
without tests, and repo coverage must stay ≥90%. New generator branches for
{lang['display']} need parallel coverage.

**Depends on:** Foundation, Quality{', CI' if 'ci' in lang['subs'] else ''} sub-issues.

## Goal

Prove the tool generates correct, green {lang['display']} ({lang['platform']})
projects, keeping repo coverage ≥90%.

## Scope — files to touch

- `tests/unit/generators/` — unit tests for each new/changed generator branch
- `tests/integration/generators/` — `green init -l {slug}` generation assertions
- `tests/unit/test_multi_language.py` — add `{slug}` to the parametrized
  all-language matrix
- `tests/e2e/` — generate a {slug} project and assert it passes its own
  `pre-commit run --all-files`

## Tasks

- [ ] Unit tests for every new branch (happy path + invalid input)
- [ ] Integration test asserting generated tree + manifest contents
- [ ] Parametrize `test_multi_language.py` to include `{slug}`
- [ ] e2e test: generated project is green
- [ ] Mutation-test new generator logic (≥80% on changed files)

## Acceptance Criteria

- [ ] Repo coverage stays ≥90%
- [ ] `{slug}` appears in the parametrized multi-language tests
- [ ] e2e generation test passes in CI

{gates()}
## References

- `tests/unit/test_multi_language.py`
- `tests/integration/generators/`, `tests/e2e/`, `.claude/docs/testing.md`
"""


def docs_body(slug: str, lang: dict) -> str:
    return f"""## Context

Sub-issue of the **{lang['display']} ({lang['platform']})** epic. Support isn't
done until documented; several docs enumerate supported languages.

**Depends on:** the other sub-issues (document what was built).

## Goal

Document {lang['display']} ({lang['platform']}) support across all
language-listing surfaces, with a usage example.

## Scope — files to touch

- `CLAUDE.md` — multi-language list + supported-languages references
- `README.md` — supported languages / quick start
- `docs/CLI_REFERENCE.md` — `green init -l {slug}` usage
- `plan/SPEC.md` — language support section
- `examples/` — minimal generated {lang['display']} example
- `CHANGELOG.md` — note the new/completed language

## Tasks

- [ ] Update every supported-languages list to include {lang['display']}
- [ ] Add a `green init -l {slug}` usage example with the toolchain table
- [ ] Document prerequisites ({TOOLING[slug]['pkg']}, {TOOLING[slug]['versions']})
- [ ] Add a CHANGELOG entry

## Acceptance Criteria

- [ ] No doc implies {lang['display']} is unsupported/partial
- [ ] Docs lint clean (markdownlint + link check)
- [ ] Example reflects real generated output

{gates()}
## References

- `CLAUDE.md`, `README.md`, `docs/CLI_REFERENCE.md`, `plan/SPEC.md`
"""


def architecture_single_body(slug: str, lang: dict) -> str:
    t = TOOLING[slug]
    return f"""## Context

Part of the **language-support parity initiative**. {lang['status']}

{lang['display']} is otherwise fully wired (precommit, scripts, metrics, ci),
so this is a single focused parity issue rather than a full epic.

## Goal

Add {lang['display']} dependency/layer enforcement to `architecture.py` so
generated {lang['display']} projects get the same architecture gate as
python/typescript.

## Scope — files to touch

- `start_green_stay_green/generators/architecture.py` — add `{slug}` to
  `supported_languages` (`architecture.py:94`) and a generation branch using
  **{t['architecture']}** (parallel to import-linter/dependency-cruiser)
- `tests/unit/generators/` — tests for the new branch
- `tests/unit/test_multi_language.py` — ensure `{slug}` exercises architecture
- docs: note {lang['display']} architecture enforcement where relevant

## Acceptance Criteria

- [ ] `green init -l {slug}` emits an architecture-enforcement config
      ({t['architecture']})
- [ ] Architecture parity row for {lang['display']} is ✅
- [ ] Repo coverage stays ≥90%

{gates()}
## References

- `start_green_stay_green/generators/architecture.py:94`
- `tests/unit/test_multi_language.py`
"""


BODY = {
    "foundation": foundation_body,
    "quality": quality_body,
    "ci": ci_body,
    "tests": tests_body,
    "docs": docs_body,
    "architecture": architecture_single_body,
}


def umbrella_body() -> str:
    rows = []
    matrix = {
        "python": "✅✅✅✅✅✅✅✅ (reference)",
        "typescript": "✅✅✅✅✅✅✅✅ (reference)",
        "go": "missing: architecture",
        "rust": "missing: architecture",
        "java": "missing: precommit, scripts, metrics, architecture (+Wear OS scaffold)",
        "csharp": "missing: precommit, scripts, metrics, architecture",
        "ruby": "missing: precommit, scripts, metrics, architecture",
        "swift": "NEW — all generators",
        "kotlin": "NEW — all generators",
        "cpp": "NEW — all generators",
    }
    for lng, gap in matrix.items():
        rows.append(f"| `{lng}` | {gap} |")
    table = "| Language | Parity gaps |\n|---|---|\n" + "\n".join(rows)
    return f"""## Context

Audit of `start_green_stay_green/generators/*.py` shows uneven language
support: `precommit.py`, `scripts.py`, `metrics.py` cover only
python/typescript/go/rust, and `architecture.py` only python/typescript — yet
`base.py` advertises 7 languages and CLAUDE.md advertises Swift. Several
languages (java, csharp, ruby) **raise** when generating pre-commit config.
Smartwatch platforms additionally require Swift (watchOS), Kotlin/Java
(Wear OS), and C/C++ (Tizen).

## Goal

Reach **full parity**: every supported language wired into every generator so
`green init -l <lang>` produces a fully green project. python/typescript are
the reference; all others are brought up to match.

## Parity gaps (current)

{table}

## Approach

Gap-driven per-language epics (this issue is the umbrella tracker). Each
language epic only files sub-issues for cells it actually lacks; `templates/`
is excluded (vestigial — every language ships only `.gitkeep` yet python works).

## Language Support Contract (new invariant)

To prevent regression, adding a language MUST wire all of: registration
(`base.py` + CLI), scaffolding (`structure`/`dependencies`/`readme`), quality
(`precommit`/`scripts`/`metrics`/`architecture`), `ci`, tests
(incl. `test_multi_language.py`), and docs. Add a test asserting every
`SUPPORTED_LANGUAGES` entry is handled by every generator.

## Child Epics / Issues

Linked as GitHub sub-issues below (swift, kotlin, cpp, java, csharp, ruby
epics; go, rust single architecture issues).

## Acceptance Criteria

- [ ] All child epics/issues closed
- [ ] A guard test fails if any `SUPPORTED_LANGUAGES` entry is unhandled by any generator
- [ ] Parity matrix is fully ✅ for every language
- [ ] CLAUDE.md / README accurately list supported languages

{gates()}
## References

- `start_green_stay_green/generators/base.py:20`
- `start_green_stay_green/generators/{{precommit,scripts,metrics,architecture,ci}}.py`
- `.claude/docs/quality-standards.md`
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[str] = []

    (OUT / "EPIC_00_umbrella.md").write_text(umbrella_body(), encoding="utf-8")
    manifest.append(
        "UMBRELLA\tumbrella\tfeat(lang): Achieve full language-support parity "
        "across all generators"
    )

    for slug, lang in LANGUAGES.items():
        sslug = slug
        if lang["kind"] == "epic":
            title = (
                f"feat(lang): {lang['verb']} {lang['display']} support "
                f"({lang['platform']})"
            )
            (OUT / f"EPIC_{slug}.md").write_text(epic_body(slug, lang), encoding="utf-8")
            manifest.append(f"EPIC\t{slug}\t{title}")
            for comp in lang["subs"]:
                body = BODY[comp](slug, lang)
                sub_title = f"feat({sslug}): {SUB_LABELS[comp]}"
                (OUT / f"SUB_{slug}_{comp}.md").write_text(body, encoding="utf-8")
                manifest.append(f"SUB\t{slug}\t{comp}\t{sub_title}")
        else:  # single issue (go, rust)
            body = architecture_single_body(slug, lang)
            title = f"feat({sslug}): {SUB_LABELS['architecture']}"
            (OUT / f"ISSUE_{slug}_architecture.md").write_text(body, encoding="utf-8")
            manifest.append(f"SINGLE\t{slug}\tarchitecture\t{title}")

    (OUT / "_manifest.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    n = len(list(OUT.glob("*.md")))
    print(f"Wrote {n} issue body files to {OUT}/\n")
    print("\n".join(manifest))


if __name__ == "__main__":
    main()
