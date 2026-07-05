# CLI Reference

Complete reference documentation for the Start Green Stay Green command-line interface.

## Overview

Start Green Stay Green provides a simple command-line interface for generating quality-controlled projects:

```bash
start-green-stay-green [OPTIONS] COMMAND [ARGS]
```

All commands are interactive by default. Use `--no-interactive` for automation.

## Global Options

### `--verbose` / `-v`

Enable verbose output with detailed information about what's happening.

**Example**:
```bash
start-green-stay-green --verbose init --project-name my-app --language python
```

**Output**:
```
[dim]Loading project configuration...[/dim]
[dim]Validating project name: my-app[/dim]
[dim]Language: python[/dim]
[green]✓[/green] Project generated successfully at: /path/to/my-app
```

### `--quiet` / `-q`

Suppress non-essential output, showing only important messages.

**Example**:
```bash
start-green-stay-green --quiet init --project-name my-app --language python
```

**Note**: `--verbose` and `--quiet` are mutually exclusive.

### `--config` / `--config-file PATH`

Load configuration from a YAML or TOML file.

**Example**:
```bash
start-green-stay-green --config project.yaml init
```

Only `project_name`, `language`, `llm_provider`, and `llm_model` are read
from the file — see [Configuration Files](#configuration-files) below for
the full precedence rules. Other keys (`output_dir` included) are parsed
but ignored; pass those on the command line.

**Configuration File Format (YAML)**:
```yaml
project_name: my-awesome-project
language: python
llm_provider: anthropic  # optional; --provider / GREEN_LLM_PROVIDER override this
llm_model: claude-opus-4-5  # optional; --model / GREEN_LLM_MODEL override this
```

**Configuration File Format (TOML)**:
```toml
project_name = "my-awesome-project"
language = "python"
llm_provider = "anthropic"
llm_model = "claude-opus-4-5"
```

**Note**: API keys are never read from the config file. Set
`ANTHROPIC_API_KEY` (or `OPENAI_API_KEY` for the `openai` provider) as an
environment variable, or store it in the OS keyring — see
[API Keys & Credentials](#api-keys--credentials) below.

### `--help`

Show help message and exit.

**Example**:
```bash
start-green-stay-green --help
start-green-stay-green init --help
```

## Commands

### `init`

Initialize a new project with quality controls.

**Syntax**:
```bash
start-green-stay-green init [OPTIONS]
```

#### Options

##### `--project-name` / `-n TEXT` (Optional)

Name of the project to generate.

**Constraints**:
- Alphanumeric characters, hyphens, underscores only
- Maximum 100 characters
- Cannot start with hyphen or underscore
- Cannot be a Windows reserved name (CON, PRN, AUX, etc.)

**Examples**:
```bash
# Valid
--project-name my-app
--project-name MyApp
--project-name my_app
--project-name my123app

# Invalid
--project-name "my app"          # spaces not allowed
--project-name "my.app"          # dots not allowed
--project-name "-my-app"         # cannot start with hyphen
--project-name "con"             # Windows reserved name
```

**Interactive Fallback**:
If not provided in non-interactive mode, will prompt:
```
Project name:
```

##### `--language` / `-l TEXT` (Optional)

Primary programming language for the project.

**Supported Languages**:
- `python` - Python 3.11+
- `typescript` - TypeScript with Node.js
- `go` - Go 1.21+
- `rust` - Rust 1.70+
- `swift` - Swift 5.9/5.10/6.0 with Swift Package Manager (SPM), watchOS-ready
- `kotlin` - Kotlin 2.0 with Gradle (Kotlin DSL) on JDK 17/21, Wear OS-ready
- `cpp` - C/C++ (C++17 pinned, C++20-ready sources) with CMake ≥3.20 + Conan 2, Tizen-watch-ready
- `java` - Java 17 with Maven (pure logic), Wear OS (legacy Android Wear)-ready
- `csharp` - C# on .NET 8 (net8.0) with the dotnet CLI, xUnit, and NuGet
- `ruby` - Ruby 3.3/3.4 (the maintained lines) with Bundler, RSpec, and RuboCop

**Examples**:
```bash
--language python
--language typescript
--language go
--language rust
--language swift
--language kotlin
--language cpp
--language java
--language csharp
--language ruby
```

**Interactive Fallback**:
If not provided, will prompt with options:
```
Primary language: [python/typescript/go/rust/swift/kotlin/cpp/java/csharp/ruby]
```

**Swift Toolchain**:

A `--language swift` project is an SPM package (watchOS app scaffold)
wired with this quality toolchain:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | swift-format | `scripts/format.sh`, pre-commit, CI |
| Linting + complexity (≤10) | SwiftLint (`.swiftlint.yml`) | `scripts/lint.sh`, pre-commit, CI |
| Tests | XCTest via `swift test` | `scripts/test.sh`, CI |
| Coverage (≥90%) | llvm-cov export from `swift test --enable-code-coverage` | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit, CI |
| Dead-code analysis | Periphery | `scripts/security.sh` |
| Mutation testing | muter | periodic quality gate (tracked by the opt-in metrics dashboard) |

CI runs on macOS runners with a Swift 5.9/5.10/6.0 version matrix plus a
watchOS-simulator build-and-test job. Local prerequisites: a Swift
5.9/5.10/6.0 toolchain with SPM, and
`brew install swiftlint swift-format gitleaks` for the generated
pre-commit hooks (`brew install periphery` for dead-code scans).

**Kotlin Toolchain**:

A `--language kotlin` project is a Gradle (Kotlin DSL) Wear OS app
scaffold (Galaxy Watch 4+ / Wear OS 3, Jetpack Compose for Wear OS)
wired with this quality toolchain:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | ktlint (`ktlint --format`) | `scripts/format.sh`, pre-commit, CI |
| Static analysis + complexity (≤10) | detekt (`detekt.yml`) | `scripts/lint.sh`, pre-commit, CI |
| Tests | JUnit 4 via `./gradlew test` | `scripts/test.sh`, CI |
| Coverage (≥90%) | Kover (`koverVerifyDebug` — the bound lives in `app/build.gradle.kts`) | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit, CI |
| Dependency CVE scan | OWASP dependency-check | `scripts/security.sh` |
| Mutation testing | pitest | periodic quality gate (tracked by the opt-in metrics dashboard) |
| Architecture rules | Konsist test (`plans/architecture/`) | `plans/architecture/run-check.sh` |

CI runs on ubuntu runners with a JDK 17/21 (Temurin) test matrix, a
quality job enforcing the Kover ≥90% coverage gate, and a Wear OS
debug-APK build. The Gradle wrapper is **not generated** (binary
artifacts are never scaffolded): run `gradle wrapper` once locally; CI
provisions its own pinned Gradle and stays green either way. Local
prerequisites: JDK 17+, a local Gradle install, and
`brew install ktlint detekt` (or your platform's SDK manager) for the
generated pre-commit hooks.

**C/C++ Toolchain**:

A `--language cpp` project is a Tizen native watch-app scaffold (Samsung
Galaxy Watch, appcore `watch_app` lifecycle + EFL UI) wired with this
quality toolchain:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | clang-format (`.clang-format`; pre-commit uses the mirrors-clang-format v18.1.8 pinned wheel) | `scripts/format.sh`, pre-commit, CI |
| Static analysis | clang-tidy (`.clang-tidy`, bugprone/cert/clang-analyzer promoted to errors) + cppcheck | `scripts/lint.sh`, pre-commit, CI |
| Complexity (≤10) | lizard (the CCN bound lives in `scripts/lint.sh`) | `scripts/lint.sh`, CI |
| Tests | Catch2 via CMake + Conan (`ctest --test-dir build`) | `scripts/test.sh`, CI |
| Coverage (≥90%) | gcov/lcov (the bound lives in `scripts/test.sh` — CMake has no manifest home for a coverage threshold) | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit, CI |
| Security scan | flawfinder (CWE-mapped dangerous-API scan) | `scripts/security.sh`, CI |
| Dependency CVE scan | conan audit | periodic quality gate (tracked by the opt-in metrics dashboard) |
| Mutation testing | mull | periodic quality gate (tracked by the opt-in metrics dashboard) |
| Documentation | doxygen | tracked by the opt-in metrics dashboard |
| Architecture rules | include-boundary checker (stdlib-only Python, `plans/architecture/`) | `plans/architecture/run-check.sh` |

CI runs on pinned ubuntu-24.04 runners (apt's LLVM 18 matches the
pre-commit clang-format pin) with a quality job that invokes the
generated scripts themselves, plus a build-and-test matrix on both gcc
and clang. The scaffold deliberately splits into **two builds**: the
pure-logic library and its Catch2 tests build with plain CMake + Conan
on any host, while `src/main.cpp` (the watch app) and the installable
`.tpk` package require the Tizen Studio CLI (`tizen build-native` /
`tizen package`) — a manual install that neither the scaffold nor a CI
runner can provision, needed **only** for packaging. The scaffold pins
C++17 (`CMAKE_CXX_STANDARD`) with C++20-ready sources; C11/C17 sources
are linted by cppcheck. Local prerequisites: CMake ≥3.20, Conan 2,
`brew install clang-format llvm cppcheck lcov` (clang-tidy ships in the
keg-only `llvm` formula; Debian/Ubuntu:
`apt-get install clang-format clang-tidy cppcheck lcov`), and
`pip install lizard flawfinder`.

**Java Toolchain**:

A `--language java` project is a legacy Android Wear (Wear OS)
watch-app scaffold — the maintenance path for existing Java watch apps —
wired with this quality toolchain. Most of the tooling runs as Maven
goals pinned in the generated `pom.xml`, so the only extra install is
the formatter:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | google-java-format (a `repo: local` system hook — `brew install google-java-format`; Google style, no config file by design) | `scripts/format.sh`, pre-commit |
| Code style | Checkstyle (`mvn checkstyle:check`, google_checks) | `scripts/lint.sh`, pre-commit, CI |
| Source analysis + complexity (≤10) | PMD (`mvn pmd:check` — the CCN bound lives in the companion `pmd-ruleset.xml` at the project root, shared by the script, the pre-commit hook, and CI) | `scripts/lint.sh`, pre-commit, CI |
| Tests | JUnit 4 via Maven Surefire (`mvn test`) | `scripts/test.sh`, CI |
| Coverage (≥90%) | JaCoCo (`mvn jacoco:check` — the bound lives in `pom.xml`) | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit |
| Security scan | SpotBugs static bytecode analysis (compile-first: `mvn compile spotbugs:check` — the goal silently passes on an empty `target/classes`) | `scripts/security.sh`, pre-commit, CI |
| Dependency CVE scan | OWASP dependency-check (`mvn dependency-check:check`, CVSS ≥7 bound in `pom.xml`; needs a free NVD API key exported as `NVD_API_KEY`, otherwise skipped with a warning) | `scripts/security.sh` |
| Mutation testing | pitest | periodic quality gate (tracked by the opt-in metrics dashboard) |
| Documentation | javadoc | tracked by the opt-in metrics dashboard |
| Architecture rules | ArchUnit test (`plans/architecture/`; copy it into the package-matched `src/test/java/<package>/architecture/` path to enforce — ArchUnit is already test-scoped in the pom) | `plans/architecture/run-check.sh` |

CI runs on ubuntu runners with a JDK 17/21 (Temurin) quality matrix
running the same Maven goals as the local build — Checkstyle, PMD, the
compile-first SpotBugs step, tests with JaCoCo, a best-effort Codecov
upload (informational only: the enforced ≥90% gate is the pom-backed
`mvn jacoco:check` step), plus a build-and-package job. The scaffold
deliberately splits into **two builds**: `pom.xml` builds only the
pure-logic sources (`src/main/java` + `src/test/java`), so `mvn test`
and every quality goal run on any host, while the watch app under
`app/` needs the Android SDK and the androidx.wear AAR, which plain
Maven cannot consume (the android-maven-plugin is unmaintained) —
build the APK with Android tooling (Android Studio / Gradle), adding
`src/main/java/` as a source root. Local prerequisites: JDK 17+ (the
pom pins `maven.compiler.release` 17, within CI's 17/21 matrix), Maven,
and `brew install google-java-format` for the generated pre-commit
format hook.

**C# Toolchain**:

A `--language csharp` project is a general .NET 8 scaffold (a console
app plus xUnit tests compiling into one assembly) wired with this
quality toolchain. Every gate runs inside the dotnet CLI, and the
generated `.csproj` is the single source of the quality policy — the
analyzer configuration, the coverage bound, and the quality packages
all live there, so the scripts, hooks, and CI cannot version-drift
from the build:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | dotnet format (a `repo: local` system hook in check mode — `--verify-no-changes`, because a bare `dotnet format` rewrites files and exits 0 either way; `scripts/format.sh` keeps the fixing path; reads `.editorconfig`) | `scripts/format.sh`, pre-commit, CI |
| Lint + source security | Roslyn analyzers in every `dotnet build` — the csproj enables the .NET SDK analyzers and treats warnings as errors, and the SecurityCodeScan analyzer runs in the same compiler pass | `scripts/lint.sh`, pre-commit, CI |
| Complexity (≤10) | The Roslyn CA1502 rule — enabled in `.editorconfig`, with the bound's single home in the companion `CodeMetricsConfig.txt` at the project root (wired in via the csproj's AdditionalFiles; 10 reports 11+) | every `dotnet build` |
| Tests | xUnit (`dotnet test` — restore, analyzer-gated build, and tests in one invocation) | `scripts/test.sh`, CI |
| Coverage (≥90%) | Coverlet (`dotnet test /p:CollectCoverage=true` — the line bound lives in the csproj's `Threshold` properties, its single home; coverlet.msbuild hooks the test task itself, so a missed bound fails the run directly) | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit |
| Dependency CVE scan | `dotnet list package --vulnerable` (gated on the report output, not the exit code — the command's exit code unreliably stays 0 with findings across SDK lines; needs restore + network, so offline runs warn and skip) plus the SecurityCodeScan analyzer above for source-level findings | `scripts/security.sh` |
| Mutation testing | Stryker.NET (`dotnet stryker`) | periodic quality gate (tracked by the opt-in metrics dashboard) |
| Documentation | DocFX | tracked by the opt-in metrics dashboard |
| Architecture rules | NetArchTest xUnit test (`plans/architecture/`; copy it **flat** into `tests/` to enforce — C# namespaces carry no directory-matching requirement, and NetArchTest.Rules is already declared in the csproj) | `plans/architecture/run-check.sh` |

CI runs on ubuntu runners with a .NET 8 SDK quality job (the generated
csproj targets net8.0, which older SDKs cannot build, so the matrix
pins the 8.0 line — extend it together with the TargetFramework)
running the same dotnet CLI gates as the local build — restore, the
analyzer-gated build, the dotnet format check, tests with the
csproj-backed Coverlet ≥90% gate, and a best-effort Codecov upload
(informational only: the enforced gate is the Coverlet run), plus a
build-and-publish job. Local prerequisites: the .NET 8 SDK
(`brew install dotnet-sdk` on macOS, `apt-get install dotnet-sdk-8.0`
on Debian/Ubuntu) — `dotnet format`, the Roslyn analyzers, and NuGet
all ship inside the SDK, so there is nothing else to install.

**Ruby Toolchain**:

A `--language ruby` project is a plain-Ruby scaffold (a `lib/` module
plus RSpec specs) wired with this quality toolchain. The Ruby twist:
RuboCop is one tool wearing four hats — formatter (Layout cops),
linter (Lint/Style), complexity gate, and source-level security (the
Security cop department) — so the generated `.rubocop.yml` is the
single home of that whole policy, shared by the pre-commit hook, the
scripts, and CI:

| Concern | Tool | Where it runs |
|---------|------|---------------|
| Formatting | RuboCop Layout cops (`scripts/format.sh` owns the fixing path — `--autocorrect`; its `--check` mode runs the Layout department only, so check-all's Format and Lint slices never double-report) | `scripts/format.sh`, pre-commit, CI |
| Lint + source security | RuboCop Lint/Style departments plus the Security cop department (Security/Eval, Security/Open, …) in the same run — the pre-commit hook comes from the official rubocop/rubocop manifest (the repo ships a `.pre-commit-hooks.yaml`, so no `repo: local` system hook is needed), with one overridden default: the manifest's args include `--autocorrect` (fixing mode, which can never fail on correctable offenses), so the generated hook overrides args to `--force-exclusion` alone — plain check-mode RuboCop exits non-zero on ANY offense | `scripts/lint.sh`, pre-commit, CI |
| Complexity (≤10) | The RuboCop `Metrics/CyclomaticComplexity` cop — the bound's single home is `.rubocop.yml`; nothing else restates the number (flog is the documented standalone alternative for hotspot analysis, deliberately not wired so the bound keeps one home) | every full RuboCop run |
| Tests | RSpec (`bundle exec rspec` — a plain run stays fast because the coverage gate is opt-in via `COVERAGE=true`) | `scripts/test.sh`, CI |
| Coverage (≥90%) | SimpleCov (`COVERAGE=true bundle exec rspec` — the line bound lives in `spec/spec_helper.rb`, its single home; SimpleCov's at_exit hook fails the rspec invocation directly when the bound is missed, so there is no standalone-report no-op path) | `scripts/test.sh --coverage`, CI |
| Secret scanning | gitleaks + detect-secrets | pre-commit |
| Dependency CVE scan | bundler-audit against the ruby-advisory-db (the advisory database must be fetched over the network, so offline runs warn and skip; in CI the update is a hard gate). Brakeman is the deeper scanner to add WHEN the project adopts Rails — it is Rails-specific and errors on plain-Ruby projects, so it is documented rather than wired | `scripts/security.sh` |
| Mutation testing | mutant (`bundle exec mutant run`) | periodic quality gate (tracked by the opt-in metrics dashboard; the gem is not pinned in the generated Gemfile — add it when adopting the gate) |
| Documentation | YARD | tracked by the opt-in metrics dashboard (the gem is not pinned in the generated Gemfile) |
| Architecture rules | Packwerk package boundaries (`plans/architecture/`; parked templates — copy `packwerk.yml` and `package.yml` to the project root to activate; the packwerk gem is already pinned in the Gemfile. Packwerk performs **static** constant-reference analysis and assumes Zeitwerk-style autoload paths, so on the flat plain-Ruby scaffold the check passes vacuously until packages are defined. It matters because Ruby's `require` does NOT reject circular requires at load time — a cycle silently yields a partially-defined module at runtime — so `packwerk validate`'s acyclic package graph is the only early signal) | `plans/architecture/run-check.sh` |

CI runs on ubuntu runners with a Ruby 3.3/3.4 quality matrix (the
lines still receiving upstream maintenance — bump together with the
generated `.rubocop.yml`'s `TargetRubyVersion`), installing gems via
`ruby/setup-ruby`'s bundler-cache (no separate install step), then
running the same gates as the local build — the full RuboCop run
against the same `.rubocop.yml`, bundler-audit (a hard gate in CI,
where network access is guaranteed), RSpec with the
spec_helper-backed SimpleCov ≥90% gate, and a best-effort Codecov
upload (codecov-action@v6 with `fail_ci_if_error: false` —
informational only: the enforced gate is the SimpleCov run). There is
no packaging job: the scaffold ships no `.gemspec`, so a `gem build`
job would be red on every push — add one together with the gemspec
when the project becomes a gem. Local prerequisites: Ruby 3.3+ and
Bundler (`brew install ruby` on macOS, `apt-get install ruby-full` on
Debian/Ubuntu) — `bundle install` provisions every pinned quality gem
(RSpec, SimpleCov, RuboCop, bundler-audit, Packwerk).

##### `--agent TEXT` (Optional, repeatable)

Agent-context format(s) to generate. Repeat the flag or comma-separate for
multiple targets. All formats render the same shared content, just in a
different on-disk convention.

**Choices**:
- `claude` (default) — `CLAUDE.md` + `.claude/` (skills, subagents, commands).
- `agents-md` — `AGENTS.md`, the open cross-tool agent-context convention.
- `aider` — `CONVENTIONS.md` + `.aider.conf.yml` for the [aider](https://aider.chat) tool.

**Examples**:
```bash
--agent claude
--agent agents-md
--agent claude --agent agents-md
--agent claude,agents-md,aider
```

##### `--output-dir` / `-o PATH` (Optional)

Output directory for the generated project.

**Default**: Current working directory

**Examples**:
```bash
--output-dir /home/user/projects
--output-dir ~/projects
--output-dir ./generated

# With relative paths
--output-dir ../projects
--output-dir .  # Current directory
```

**Path Safety**:
- Paths are normalized and resolved to absolute paths
- Path traversal attempts (using `..`) are detected and rejected
- Project path must stay within output directory

##### `--dry-run` (Optional)

Preview what would be generated without creating files.

**Example**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --dry-run
```

**Output**:
```
Dry Run Mode - Preview only

Project: my-app
Language: python
Output: /path/to/my-app

Would generate:
  - CI/CD pipeline
  - Pre-commit hooks
  - Quality scripts
  - Skills
  - Subagent profiles
  - CLAUDE.md
  - GitHub Actions (AI review)
  - Architecture enforcement
```

**Note**: Does not prompt for missing options even in interactive mode.

##### `--force` / `-f` (Optional)

Overwrite all existing files without prompting. Off by default, so re-running
`init` against an existing project only adds missing files.

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --force
```

##### `--interactive` (Optional)

Prompt per-file when a conflict exists (skip/overwrite/diff), instead of the
default additive behavior (skip existing files silently) or `--force`
(overwrite everything silently). Mutually exclusive with `--force`.

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --interactive
```

##### `--no-interactive` (Optional)

Run in non-interactive mode without prompts.

**Behavior**:
- All required options must be provided via CLI or config file
- Fails with exit code 1 if any required option is missing
- No interactive prompts even for missing values

**Examples**:
```bash
# Valid - all options provided
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --no-interactive

# Invalid - missing --language
start-green-stay-green init \
  --project-name my-app \
  --no-interactive
# Error: --language required in non-interactive mode.
```

##### `--offline` (Optional)

Run only Pass 1 of the two-pass init: produce a complete project from
deterministic templates. No API key is read, no network call is made, no AI
tuning is attempted. Equivalent to `--no-enhance` plus suppressing every
API-key prompt. The scaffold is functionally complete either way — AI tuning
only polishes `CLAUDE.md` and subagent content.

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --offline
```

##### `--no-enhance` (Optional)

Skip Pass 2 (the AI-tuned polish over `CLAUDE.md` and subagents), but still
resolve an API key so a later `green enhance` call can pick up where this one
left off. Use `--offline` instead if you don't want the API-key resolution
step to run at all (e.g. fully air-gapped).

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --no-enhance
```

##### `--enable-live-dashboard` (Optional)

Generate a live-updating metrics dashboard (coverage, CI status, mutation
score) plus the GitHub Actions workflow that refreshes it after every merge.

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --enable-live-dashboard
```

##### `--windows-ci` (Optional)

Add an opt-in `windows-latest` job to the generated CI workflow that runs
the project's quality gates through Git Bash (`bash scripts/<gate>.sh`).
Default off: without this flag the generated CI is byte-for-byte unchanged
and uses no Windows runner minutes.

Supported languages: python, typescript, go, rust, java, csharp, ruby. Not
supported (the flag fails fast with an explanation): swift, cpp (their gate
toolchains aren't available on `windows-latest`), and kotlin (the gate
scripts need a Gradle wrapper jar `init` doesn't write). For a multi-language
project the leg follows the primary language (the first `-l` value).

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --windows-ci
```

To add the leg to an **existing** scaffolded repo, re-run `init` with the
flag plus a conflict-resolution mode (`init` never overwrites files by
default):
```bash
green init -n my-app -l python --windows-ci --interactive  # choose
# "overwrite" for .github/workflows/ci.yml when prompted
```

##### `--with-ralph-loop` (Optional)

Generate the opt-in Ralph autonomous fleet-loop scaffolding: a subagent
taxonomy under `.claude/agents/`, the fleet orchestrator
(`.claude/commands/ralph-tick.md`), worktree-fleet mechanics under
`scripts/ralph/`, and the maintenance-scan GitHub Actions. Default off — this
is a heavier, opinionated system that assumes a GitHub-hosted issue/PR
backlog and git worktrees, and requires manual secret/label setup after
generation (see the generated `FLEET.md` and `PROMPT.md`).

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --with-ralph-loop
```

##### `--timing-json PATH` (Optional)

Write a structured timing/telemetry report (JSON) for the generation run.
No effect on the default console output.

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --timing-json timing.json
```

##### API Keys & Credentials

There is no `--api-key` flag — passing a key on the command line would leave
it visible in the process list and shell history. AI-powered features
(Pass 2 tuning of `CLAUDE.md` and subagents) resolve credentials in this
order:

1. The active provider's environment variable — `ANTHROPIC_API_KEY` for the
   default `anthropic` provider, `OPENAI_API_KEY` for `openai` (see
   `--provider` below).
2. The OS keyring (macOS Keychain, Linux Secret Service, Windows Credential
   Manager) — populated by a prior interactive run.
3. An interactive prompt (unless `--no-interactive` or `--offline`), with the
   option to save the entered key to the keyring for next time.

**Examples**:
```bash
# Recommended: environment variable
export ANTHROPIC_API_KEY=sk-ant-abc123def456
start-green-stay-green init --project-name my-app --language python

# No key available / fully air-gapped: skip Pass 2 entirely
start-green-stay-green init --project-name my-app --language python --offline
```

Without any key, `init` still produces a complete project from deterministic
templates (Pass 1) — AI tuning is a polish step, not a requirement.

##### `--provider TEXT` (Optional)

LLM provider for AI features. Precedence: this flag > `GREEN_LLM_PROVIDER`
env var > `llm_provider` key in `--config` file > default (`anthropic`). Run
`green providers` to list every registered provider, its default model, its
credential env var, and its capability groups (batch, tool-use, token
accounting).

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --provider openai
```

For `openai`, `OPENAI_BASE_URL` can point at any OpenAI-compatible local
server (Ollama, vLLM, LM Studio, …) — a dummy key is fine in that case.

##### `--model TEXT` (Optional)

Model identifier for AI features. Precedence: this flag > `GREEN_LLM_MODEL`
env var > `llm_model` key in `--config` file > the provider's default model.
The case of the model id is preserved verbatim (API identifiers are
case-sensitive).

**Example**:
```bash
start-green-stay-green init --project-name my-app --language python --model claude-opus-4-5
```

##### `--config PATH` (Optional)

Path to configuration file (YAML or TOML).

**File Detection**:
- Automatically detects format based on extension
- `.yaml` / `.yml` for YAML
- `.toml` for TOML

Only `project_name`, `language`, `llm_provider`, and `llm_model` are read
from the file; other keys are parsed but ignored (`output_dir` and every
other `init` option must be passed on the command line).

**Example Configuration (YAML)**:
```yaml
project_name: my-awesome-project
language: python
llm_provider: anthropic
llm_model: claude-opus-4-5
```

**Example Configuration (TOML)**:
```toml
project_name = "my-awesome-project"
language = "python"
llm_provider = "anthropic"
llm_model = "claude-opus-4-5"
```

**Merge Behavior**:
1. Loads defaults
2. Merges config file values
3. Merges CLI argument values (highest priority)

#### Examples

**Interactive Mode**:
```bash
start-green-stay-green init

# Prompts for:
# Project name: my-app
# Primary language: python
```

**Non-Interactive Mode**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --output-dir ~/projects \
  --no-interactive
```

**With an API key (environment variable, recommended)**:
```bash
export ANTHROPIC_API_KEY=sk-ant-abc123
start-green-stay-green init --project-name my-app --language python
```

**Offline / no AI features**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --offline
```

**With Configuration File**:
```bash
start-green-stay-green init --config project.yaml
```

**Opt into Windows CI + the Ralph fleet loop**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --windows-ci \
  --with-ralph-loop
```

**Dry Run**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --dry-run
```

**Verbose Output**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --verbose
```

#### Exit Codes

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success - project generated | ✓ Project created |
| 1 | Validation error | Invalid project name, missing option, `--windows-ci` on an unsupported language |
| 1 | Generation failed | File system error, permission denied |
| 2 | Missing required option | Non-interactive mode missing argument |

#### Validation

The `init` command validates:

**Project Name**:
- Alphanumeric, hyphens, underscores only
- 1-100 characters
- Does not start with hyphen or underscore
- Not a Windows reserved name

**Language**:
- Must be one of: python, typescript, go, rust, swift, kotlin, cpp, java, csharp, ruby
- Case-insensitive

**Output Directory**:
- Path must be safe from traversal attacks
- Parent directories are created if needed
- **Additive by default**: re-running `init` against an existing directory is
  safe — existing files are preserved unless `--force` or `--interactive`
  chooses to overwrite them.

### `version`

Display version information.

**Syntax**:
```bash
start-green-stay-green version [OPTIONS]
```

#### Options

##### `--verbose` / `-v`

Show detailed version information.

**Example**:
```bash
start-green-stay-green version --verbose
```

**Output**:
```
Start Green Stay Green
Version: 1.0.0
Python: 3.11.6
Platform: darwin
```

#### Examples

**Simple Version**:
```bash
start-green-stay-green version

# Output: Start Green Stay Green v1.0.0
```

**Verbose Version**:
```bash
start-green-stay-green version --verbose

# Output:
# Start Green Stay Green
# Version: 1.0.0
# Python: 3.11.6
# Platform: darwin
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - version displayed |

### `providers`

List registered LLM providers and their capabilities.

**Syntax**:
```bash
start-green-stay-green providers
```

Shows, for each provider the `--provider` flag accepts: the default model,
the environment variable its API key is read from, and which capability
groups it implements (batch, tool-use, token accounting). The listing is
read from each provider's capability advertisement — no credentials,
network access, or optional vendor SDK required, so it works even with
nothing installed beyond the base package.

**Example**:
```bash
start-green-stay-green providers
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - provider list displayed |

### `enhance`

Re-run Pass 2 (AI tuning) on an existing `green init` project.

**Syntax**:
```bash
start-green-stay-green enhance [PROJECT_PATH] [OPTIONS]
```

Gives users who ran `green init --offline` (or who have updated their
reference skills/subagents) a way to add or refresh the AI-tuned artifacts
without re-scaffolding the whole project.

**Arguments**:

##### `project_path` (Optional)

Path to an existing `green init` project. Defaults to the current
directory. The directory must contain a `CLAUDE.md` produced by `green
init` — project name and language are auto-detected from it and from
canonical project files (`pyproject.toml`, `package.json`, `go.mod`,
`Cargo.toml`, ...).

#### Options

##### `--project-name` / `-n TEXT` (Optional)

Override the auto-detected project name (normally parsed from the existing
`CLAUDE.md`'s H1 title).

##### `--language` / `-l TEXT` (Optional)

Override the auto-detected primary language.

##### `--targets` / `-t TEXT` (Optional, repeatable)

Subset of artifacts to re-tune. Repeat the flag or comma-separate. Choices:
`claude-md`, `subagents`. Default: re-tune everything.

##### `--dry-run` (Optional)

Make the API calls but don't write any files — useful for previewing token
cost or expected changes before committing to a re-tune.

##### `--no-interactive` (Optional)

Run in non-interactive mode (skip keyring prompts).

##### `--force` / `-f` (Optional)

Overwrite files without prompting. Off by default.

##### `--batch` (Optional)

Submit subagent tunings via the Anthropic Message Batches API (50% cheaper,
≤24h SLA). Use with `--targets subagents`. The first run submits and exits;
re-run to fetch results, or pass `--wait` to block until done. Providers
without batch support (see `green providers`) fall back to sequential API
calls with a loud warning — never a crash, never silently dropped work.

##### `--wait` (Optional)

When used with `--batch`: block in-process, polling every 30s until the
batch ends or the timeout elapses. Default off (the two-call
submit-then-resume pattern is friendlier for CI). Has no effect on the
first `--batch` invocation (submit-only); pass `--wait` on the resume call
to block.

##### `--config`, `--provider`, `--model`

Same as `init` — see [API Keys & Credentials](#api-keys--credentials),
[`--provider`](#--provider-text-optional), and [`--model`](#--model-text-optional)
above. Provider/model resolve with the same four-tier precedence: CLI flag
> env (`GREEN_LLM_PROVIDER` / `GREEN_LLM_MODEL`) > config-file key
(`llm_provider` / `llm_model`, via `--config`) > built-in default.

**Examples**:
```bash
# Re-tune everything in the current directory
green enhance

# Re-tune only CLAUDE.md in a specific project
green enhance ./my-app --targets claude-md

# Preview the token cost without writing anything
green enhance --dry-run

# Cheaper subagent tuning via the Batches API
green enhance --targets subagents --batch
green enhance --targets subagents --batch --wait   # or block until done
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - artifacts re-tuned (or dry-run preview shown) |
| 1 | Invalid path, project metadata could not be inferred, unknown `--targets` value, or no API key available |

## Environment Variables

### `ANTHROPIC_API_KEY`

API key for the `anthropic` provider (the default) — see
[API Keys & Credentials](#api-keys--credentials).

**Usage**:
```bash
export ANTHROPIC_API_KEY=sk-ant-abc123def456
start-green-stay-green init --project-name my-app --language python
```

**Priority**: Higher than the OS keyring; there is no CLI flag equivalent
(passing a key on the command line would leave it visible in the process
list, so it's deliberately not offered).

### `OPENAI_API_KEY`

API key for the `openai` provider (opt in with `--provider openai`, requires
the `openai` extra: `pip install 'start-green-stay-green[openai]'`).

**Usage**:
```bash
export OPENAI_API_KEY=sk-...
start-green-stay-green init --project-name my-app --language python --provider openai
```

### `OPENAI_BASE_URL`

Override the OpenAI API endpoint for the `openai` provider — points at any
OpenAI-compatible local server (Ollama, vLLM, LM Studio, ...). A dummy
`OPENAI_API_KEY` value is fine when using a local server that doesn't check it.

**Usage**:
```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=unused
start-green-stay-green init --project-name my-app --language python --provider openai --model llama3
```

### `GREEN_LLM_PROVIDER`

Default LLM provider, used when `--provider` is omitted. Precedence: CLI
flag > this env var > config-file `llm_provider` key > built-in default
(`anthropic`).

**Usage**:
```bash
export GREEN_LLM_PROVIDER=openai
start-green-stay-green init --project-name my-app --language python
```

### `GREEN_LLM_MODEL`

Default model identifier, used when `--model` is omitted. Precedence: CLI
flag > this env var > config-file `llm_model` key > the provider's default
model.

**Usage**:
```bash
export GREEN_LLM_MODEL=claude-opus-4-5
start-green-stay-green init --project-name my-app --language python
```

### `PYTHONUNBUFFERED`

Disable Python output buffering for real-time logging.

**Usage**:
```bash
export PYTHONUNBUFFERED=1
start-green-stay-green init --verbose --project-name my-app --language python
```

**Benefit**: See log messages immediately instead of batched

## Configuration Files

Only four keys are read from a config file: `project_name`, `language`,
`llm_provider`, and `llm_model`. Every other `init`/`enhance` option
(`output_dir`, `force`, `windows_ci`, ...) must be passed on the command
line — the file is parsed in full, but unrecognized keys are silently
ignored rather than erroring, so a typo'd key doesn't fail the run.

### YAML Format

```yaml
# project.yaml
project_name: my-awesome-project
language: python
llm_provider: anthropic  # Optional
llm_model: claude-opus-4-5  # Optional
```

**Usage**:
```bash
start-green-stay-green init --config project.yaml
```

### TOML Format

```toml
# project.toml
project_name = "my-awesome-project"
language = "python"
llm_provider = "anthropic"
llm_model = "claude-opus-4-5"
```

**Usage**:
```bash
start-green-stay-green init --config project.toml
```

### Merge Priority

When using both config file and CLI arguments:

1. **Defaults** (lowest priority)
2. Config file values
3. **CLI arguments** (highest priority)

(`llm_provider`/`llm_model` add a fourth tier between these two — the
`GREEN_LLM_PROVIDER`/`GREEN_LLM_MODEL` environment variables — see
[API Keys & Credentials](#api-keys--credentials).)

Example:
```yaml
# config.yaml
project_name: config-project
language: python
```

```bash
start-green-stay-green init \
  --config config.yaml \
  --project-name cli-project

# Result: Uses "cli-project" from CLI argument
```

## Error Handling

### Validation Errors

**Invalid Project Name**:
```
Error: Invalid project name: my app.
Only letters, numbers, hyphens, and underscores are allowed.
```

**Missing Required Option**:
```
Error: --project-name required in non-interactive mode.
```

**`--windows-ci` on an Unsupported Language**:
```
Error: --windows-ci is not supported for 'swift' (supported: python, typescript, go, rust, java, csharp, ruby).
```

### File System Errors

**No Permission**:
```
Error: Generation failed: Permission denied creating directory
```

**Disk Full**:
```
Error: Generation failed: No space left on device
```

**Path Escape Attempt**:
```
Error: Output directory cannot contain '..' components
```

## Usage Patterns

### Creating a Single Project

```bash
start-green-stay-green init \
  --project-name my-service \
  --language python
```

### Creating a Swift (watchOS) Project

```bash
# Local prerequisites for the generated pre-commit hooks
brew install swiftlint swift-format gitleaks

start-green-stay-green init \
  --project-name wrist-timer \
  --language swift \
  --no-interactive

cd wrist-timer
swift package resolve
swift build
pre-commit install
./scripts/check-all.sh
```

See the [Swift Toolchain](#--language---l-text-optional) table above for
the full tool list, and [examples/swift/](../examples/swift/) for real
generated output.

### Creating a Kotlin (Wear OS) Project

```bash
# Local prerequisites for the generated pre-commit hooks
# (JDK 17+ and a local Gradle install are also required)
brew install gradle ktlint detekt

start-green-stay-green init \
  --project-name wrist-counter \
  --language kotlin \
  --no-interactive

cd wrist-counter
gradle wrapper   # the wrapper is not generated; materialize it once
./gradlew build
pre-commit install
./scripts/check-all.sh
```

See the [Kotlin Toolchain](#--language---l-text-optional) table above
for the full tool list, and [examples/kotlin/](../examples/kotlin/) for
real generated output.

### Creating a C/C++ (Tizen) Project

```bash
# Local prerequisites for the generated pre-commit hooks
# (CMake ≥3.20 and Conan 2 are also required; on Debian/Ubuntu:
# apt-get install clang-format clang-tidy cppcheck lcov)
brew install clang-format llvm cppcheck lcov
pip install lizard flawfinder

start-green-stay-green init \
  --project-name wrist-pulse \
  --language cpp \
  --no-interactive

cd wrist-pulse
conan install . --output-folder=build --build=missing
cmake -B build -S . \
    -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake \
    -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build
pre-commit install
./scripts/check-all.sh
```

Packaging the installable `.tpk` watch app additionally requires the
Tizen Studio CLI — only for packaging; everything above runs without it.

See the [C/C++ Toolchain](#--language---l-text-optional) table above
for the full tool list, and [examples/cpp/](../examples/cpp/) for real
generated output.

### Creating a Java (Wear OS legacy) Project

```bash
# Local prerequisites: JDK 17+ and Maven, plus the formatter for the
# generated pre-commit hooks (the linters are Maven plugins pinned in
# the generated pom.xml - no extra installs)
brew install google-java-format

start-green-stay-green init \
  --project-name wrist-tempo \
  --language java \
  --no-interactive

cd wrist-tempo
mvn test
pre-commit install
./scripts/check-all.sh
```

Building the watch APK additionally requires Android tooling (Android
Studio / Gradle) — only for the `app/` module; everything above runs
with plain Maven.

See the [Java Toolchain](#--language---l-text-optional) table above
for the full tool list, and [examples/java/](../examples/java/) for
real generated output.

### Creating a C# Project

```bash
# Local prerequisites: the .NET 8 SDK - dotnet format, the Roslyn
# analyzers, and NuGet all ship inside it, so nothing else to install
# (Debian/Ubuntu: apt-get install dotnet-sdk-8.0)
brew install dotnet-sdk

start-green-stay-green init \
  --project-name wrist-ledger \
  --language csharp \
  --no-interactive

cd wrist-ledger
dotnet test
pre-commit install
./scripts/check-all.sh
```

`dotnet test` restores, builds (with the Roslyn analyzers as errors),
and runs the xUnit suite in one invocation — the generated csproj owns
the whole quality policy, so the single command verifies the scaffold.

See the [C# Toolchain](#--language---l-text-optional) table above
for the full tool list, and [examples/csharp/](../examples/csharp/)
for real generated output.

### Creating a Ruby Project

```bash
# Local prerequisites: Ruby 3.3+ and Bundler - every quality gem
# (RSpec, SimpleCov, RuboCop, bundler-audit, Packwerk) is pinned in
# the generated Gemfile, so bundle install provisions the toolchain
# (Debian/Ubuntu: apt-get install ruby-full)
brew install ruby

start-green-stay-green init \
  --project-name wrist-cadence \
  --language ruby \
  --no-interactive

cd wrist-cadence
bundle install
bundle exec rspec
pre-commit install
./scripts/check-all.sh
```

`bundle install` provisions the pinned quality gems and
`bundle exec rspec` verifies the scaffold (a plain run stays fast —
the ≥90% SimpleCov coverage gate activates via `COVERAGE=true`, which
`./scripts/test.sh --coverage` and CI set).

See the [Ruby Toolchain](#--language---l-text-optional) table above
for the full tool list, and [examples/ruby/](../examples/ruby/) for
real generated output.

### Scripting Multiple Projects

```bash
#!/bin/bash
for project in api-server web-client data-pipeline; do
  start-green-stay-green init \
    --project-name "$project" \
    --language python \
    --output-dir ~/projects \
    --no-interactive
done
```

### Using in CI/CD

```yaml
# .github/workflows/generate.yml
- name: Generate project
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    start-green-stay-green init \
      --project-name ${{ github.event.inputs.name }} \
      --language ${{ github.event.inputs.language }} \
      --no-interactive
```

### Integration with Existing Scripts

```bash
# generate-project.sh
#!/bin/bash

PROJECT_NAME=${1:-my-app}
LANGUAGE=${2:-python}
OUTPUT_DIR=${3:-.}

start-green-stay-green init \
  --project-name "$PROJECT_NAME" \
  --language "$LANGUAGE" \
  --output-dir "$OUTPUT_DIR" \
  --no-interactive
```

## FAQ

**Q: Can I change the project name after creation?**
A: Yes, manually rename the directory and update references in configuration files.

**Q: What if I don't have an API key?**
A: The tool falls back to reference templates (Pass 2 AI tuning is skipped).
Use `--offline` to skip credential resolution entirely, or `--no-enhance` to
generate without AI tuning while still saving a resolved key to the keyring
for later `green enhance` runs. See
[API Keys & Credentials](#api-keys--credentials).

**Q: Can I use the same API key for multiple projects?**
A: Yes. The key is resolved fresh per invocation (env var, then OS keyring,
then interactive prompt) and isn't tied to a single project.

**Q: How do I update a project created by Start Green Stay Green?**
A: The generated infrastructure is yours to customize. Make changes directly to configuration files.

**Q: Can I integrate this into my existing CI/CD?**
A: Yes, use `--no-interactive` mode and pass configuration via environment variables or files.

## Related Documentation

- [Tutorials](TUTORIALS.md) - Step-by-step guides
- [Generator Guide](GENERATOR_GUIDE.md) - Detailed generator documentation
- [AI Orchestration](AI_ORCHESTRATION.md) - API key and credential management
