# Start Green Stay Green

> Generate quality-controlled, AI-ready repositories with enterprise-grade standards from day one.

[![CI](https://github.com/Geoffe-Ga/start_green_stay_green/workflows/CI/badge.svg)](https://github.com/Geoffe-Ga/start_green_stay_green/actions)
[![Coverage](https://img.shields.io/badge/coverage-96.99%25-brightgreen)](https://github.com/Geoffe-Ga/start_green_stay_green)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

📊 **[View Live Quality Metrics Dashboard](https://geoffe-ga.github.io/start_green_stay_green/dashboard.html)** - Auto-updated after every PR merge

## What is Start Green Stay Green?

Start Green Stay Green is a meta-tool that scaffolds new software projects with comprehensive quality infrastructure pre-configured. Unlike traditional project generators, Start Green Stay Green creates **AI-orchestrated quality controls** that ensure your project stays green from the first commit.

### Key Features

- **Enterprise-Grade Quality**: 90%+ code coverage, mutation testing, comprehensive linting
- **AI Integration**: Pre-configured AI subagent profiles and code review workflows
- **Multi-Language Support**: Python, TypeScript, Go, Rust, Swift (watchOS), Kotlin (Wear OS), C/C++ (Tizen), Java (Wear OS legacy), C# (.NET), and Ruby
- **Architecture Enforcement**: import-linter (Python), dependency-cruiser (TypeScript), go-arch-lint (Go), cargo-deny (Rust), SwiftLint custom rules (Swift), Konsist (Kotlin), an include-boundary checker (C/C++), ArchUnit (Java), NetArchTest (C#), and Packwerk (Ruby)
- **Complete CI/CD**: GitHub Actions workflows with quality gates
- **Additive Init**: Safe to re-run in existing directories — preserves your files
- **Developer Experience**: Rich console output, interactive prompts, dry-run mode

### What Gets Generated

When you run `start-green-stay-green init`, you get:

- **CI/CD Pipeline**: GitHub Actions with comprehensive quality checks
- **Pre-commit Hooks**: 32 quality hooks including format, lint, type, security, tests
- **Quality Scripts**: `check-all.sh`, `test.sh`, `lint.sh`, `mutation.sh`, etc.
- **AI Subagents**: Claude Code profiles for specialized development tasks
- **GitHub Skills**: Custom slash commands for AI-assisted workflows
- **CLAUDE.md**: Project context document for AI code assistance
- **Architecture Rules**: Layer separation and circular dependency prevention
- **Testing Infrastructure**: Unit, integration, and E2E test structure

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or pipx

### Install via pipx (Recommended)

```bash
pipx install start-green-stay-green
```

### Install via pip

```bash
pip install start-green-stay-green
```

### Install from Source

```bash
git clone https://github.com/Geoffe-Ga/start_green_stay_green.git
cd start_green_stay_green
pip install -e .
```

## Quick Start

### Interactive Mode

```bash
# Start interactive project creation
start-green-stay-green init

# Follow the prompts:
# Project name: my-awesome-project
# Primary language: python
```

### Non-Interactive Mode

```bash
# Specify all options upfront
start-green-stay-green init \
  --project-name my-awesome-project \
  --language python \
  --output-dir ~/projects \
  --no-interactive
```

### Dry Run Mode

Preview what would be generated without creating files:

```bash
start-green-stay-green init \
  --project-name my-project \
  --language python \
  --dry-run
```

### Using a Config File

```bash
# Create config.yaml
cat > config.yaml <<EOF
project_name: my-project
language: python
EOF

# Use config file
start-green-stay-green init --config config.yaml
```

## Command Reference

### `init` - Initialize a New Project

Generate a new project with quality controls.

**Usage:**

```bash
start-green-stay-green init [OPTIONS]
```

**Options:**

- `--project-name, -n TEXT`: Name of the project to generate
- `--language, -l TEXT`: Programming language(s). Repeat for multi-language: `-l python -l typescript`
- `--agent TEXT`: Agent-context format(s) to generate. Repeat for multiple: `--agent claude --agent agents-md` (choices: `claude` (default), `agents-md`, `aider`)
- `--output-dir, -o PATH`: Output directory for generated project (default: current directory)
- `--force, -f`: Overwrite all existing files without prompting
- `--interactive`: Prompt per-file when conflicts exist (skip/overwrite/diff)
- `--dry-run`: Preview what would be generated without creating files
- `--no-interactive`: Run in non-interactive mode (requires all options)
- `--offline`: Run only Pass 1 (deterministic templates); no API key read, no network, no AI tuning
- `--no-enhance`: Skip Pass 2 (AI tuning) but still resolve an API key for a later `green enhance`
- `--enable-live-dashboard`: Generate a live metrics dashboard with an auto-updating workflow
- `--windows-ci`: Add an opt-in `windows-latest` job to the generated CI workflow (default off; see below)
- `--with-ralph-loop`: Generate the opt-in Ralph autonomous fleet-loop scaffolding (agents, `ralph-tick.md`, `scripts/ralph/`, maintenance-scan workflows); default off
- `--timing-json PATH`: Write a timing/telemetry report to PATH; no effect on default output
- `--config, --config-file PATH`: Path to configuration file (YAML or TOML)
- `--provider TEXT`: LLM provider override (see [AI Enhancement](#ai-enhancement))
- `--model TEXT`: Model identifier override (see [AI Enhancement](#ai-enhancement))

**Examples:**

```bash
# Interactive mode
start-green-stay-green init

# Non-interactive with all options
start-green-stay-green init -n my-app -l python --no-interactive

# Multi-language project
start-green-stay-green init -n fullstack-app -l python -l typescript

# Opt into a Windows CI leg for the generated project
start-green-stay-green init -n my-app -l python --windows-ci

# Re-run safely in existing project (skips existing files)
start-green-stay-green init -n my-app -l python

# Force overwrite everything
start-green-stay-green init -n my-app -l python --force

# Interactively choose per file
start-green-stay-green init -n my-app -l python --interactive

# Dry run to preview
start-green-stay-green init -n my-app -l typescript --dry-run
```

#### `--windows-ci`: opt-in Windows CI leg for generated projects

By default the generated `.github/workflows/ci.yml` runs on Linux only.
Passing `--windows-ci` appends a `quality-windows` job that runs the
project's quality gates on `windows-latest` through Git Bash — the same
`bash scripts/<gate>.sh` invocation documented in the generated
`scripts/README.md` — gated behind the Linux quality job so a red Linux
run never burns Windows minutes. Default off: without the flag the
generated CI is byte-for-byte unchanged and uses no Windows runner
minutes.

Supported languages: python, typescript, go, rust, java, csharp, ruby.
Not supported (the flag fails fast with an explanation): swift and cpp
(their gate toolchains are not available on `windows-latest`) and
kotlin (the gate scripts need a Gradle wrapper jar that `init` cannot
write). For a multi-language project the leg follows the primary
language (the first `-l` value), matching how the CI workflow itself is
generated. The go leg runs only its test gate — golangci-lint is
provisioned by a Linux-only action in the quality job.

To add the leg to an **existing** scaffolded repo, re-run init with the
flag plus a conflict-resolution mode, since init never overwrites your
files by default:

```bash
green init -n my-app -l python --windows-ci --interactive  # choose
# "overwrite" for .github/workflows/ci.yml when prompted
```

(There is no YAML-aware merge for workflow files yet — unlike
`.pre-commit-config.yaml`, which init merges — so overwriting the
generated `ci.yml` is the supported path; copy your own edits back in
afterwards.)

### `version` - Display Version Information

Show the current version of Start Green Stay Green.

**Usage:**

```bash
start-green-stay-green version [OPTIONS]
```

**Options:**

- `--verbose, -v`: Show additional version details

**Examples:**

```bash
# Simple version
start-green-stay-green version

# Verbose version with details
start-green-stay-green version --verbose
```

### Global Options

These options work with all commands:

- `--verbose, -v`: Enable verbose output with detailed information
- `--quiet, -q`: Suppress non-essential output
- `--config, --config-file PATH`: Path to configuration file (YAML or TOML)
- `--help`: Show help message and exit

### `providers` - List Registered LLM Providers

```bash
start-green-stay-green providers
```

Shows, for each provider the `--provider` flag accepts: the default
model, the environment variable its API key is read from, and which
capability groups it implements (batch, tool-use, token accounting).
Reads each provider's capability advertisement — no credentials, network
access, or optional vendor SDK required.

### `green enhance` — re-tune an existing project

Re-runs Pass 2 (AI tuning) over a project that already has the
deterministic scaffold in place. Useful after `green init --offline`
when you're ready to add the AI-tuned subagents, or after the
reference subagents in this repo are updated and you want to pull
the new style into your project.

```bash
# Re-tune everything in the current directory:
green enhance

# Subset:
green enhance --targets claude-md

# Preview the token cost without writing anything:
green enhance --dry-run
```

#### Batch mode (Phase 5)

For bulk runs (CI projects, batch enhancement of many repos), the
Anthropic Message Batches API is 50% cheaper at the cost of a ≤24 h
SLA. `green enhance --batch` submits subagent tunings via that path
and exits — re-run the same command to pick up results once the
batch ends:

```bash
# Submit:
green enhance --batch --targets subagents
# → "Submitted batch msgbatch_42 covering 8 subagent(s).
#    Re-run `green enhance --batch` to fetch results."

# (later — minutes to hours later) Resume:
green enhance --batch --targets subagents
# → "✓ Batch reconciled: 8 agent(s) written, 0 failed."
```

For a single blocking command (typical in CI), pass `--wait`:

```bash
green enhance --batch --wait --targets subagents
# Polls every 30 s until the batch ends or the timeout (default 1h)
# elapses.
```

Limits and trade-offs:

* Batch mode currently handles `--targets subagents` only —
  `claude-md` uses a free-text path that the Batches API does not
  yet wrap. Mixing the two errors before any API call.
* Batches expire after 24 h server-side. `green enhance --batch`
  detects an expired record on the resume side and clears it with
  a "submit a fresh batch" message rather than producing an opaque
  error. Note: the expiry check runs only at the *start* of a
  resume call, so when `--wait` blocks across the 24 h boundary
  the loop will surface as `--wait timed out` rather than `expired`
  — re-running once afterwards picks up the (now-recognised)
  expired record and clears it.
* Per-request failures (`errored` / `canceled` / `expired`) do *not*
  abort the whole batch — successful agents land on disk, failed
  ones are listed with their names so the user can re-run.

See [`plans/architecture/ADR-001-batch-enhance.md`](plans/architecture/ADR-001-batch-enhance.md)
for the full design rationale.


## AI Enhancement

`green` ships a two-pass generation model: a deterministic scaffold
runs first (no API calls, always succeeds), then a parallel AI polish
pass tunes the AI-facing artifacts (`CLAUDE.md`, `.claude/agents/*`)
to the project's specifics. Choose the mode that fits your
constraints:

| Mode | Wall-clock | API calls | When to use |
|---|---|---|---|
| `green init --offline` | ~3 s | 0 | Air-gapped, no key, or you want the scaffold first and the polish later. Identical scaffold to the default mode. |
| `green init` (default) | ~6–10 s | ≤3 | First-class path. Scaffold + parallel Pass-2 polish in one command. |
| `green init --no-enhance` | ~3 s | 0 | Same output as `--offline`; convenient when you have a key in the environment but want to skip the polish for this run. |
| `green enhance` | ~3–6 s | ≤3 | Re-tune the AI artifacts of an existing `green init` project (e.g. after pulling fresh reference subagents from this repo). |
| `green enhance --batch` | minutes – hours | ≤3 | Same outputs as `green enhance` at 50 % cost via the Anthropic Batches API. Two-call submit-then-resume; pair with `--wait` for a single blocking command. Subagents only. |

Numbers are rough order-of-magnitude on a Mac M-series with the
default Sonnet model (see `green --help` for the current pin); your
mileage varies with network and rate-limit conditions. The scaffold
half is deterministic and offline; only the polish half varies with
the API.

### What "Pass 2 polish" actually does

| Artifact | Pass 1 (scaffold) | Pass 2 (polish) |
|---|---|---|
| `CLAUDE.md` | Generic baseline keyed off `--language` | Tuned around the user's project name + language metadata |
| `.claude/agents/*.md` | Reference profiles copied as-is | Each profile re-tuned for the target project's domain (FastAPI vs CLI vs library, Python vs TypeScript, etc.) |
| `.github/workflows/*.yml` | Templated from language presets | (Pass-1 only — no AI rewrite) |
| `pyproject.toml`, scripts, configs | Templated from language presets | (Pass-1 only — no AI rewrite) |

The "polish" is structurally tool-use against the
`report_tuning` schema, so output is parseable JSON, not free text;
results come with a per-agent change list the CLI surfaces on
completion.

### Switching modes after the fact

* **`--offline` → polished**: re-run `green enhance` (no need to
  re-init).
* **Default → re-tune after editing reference subagents**: same —
  `green enhance`.
* **Default → cheaper bulk re-tune**: `green enhance --batch
  --targets subagents`. See the [Batch mode](#batch-mode-phase-5)
  subsection above.

### Choosing a provider and model

`--provider`/`--model` (both `init` and `enhance`) pick the LLM backend
for Pass 2 polish. Precedence: CLI flag > `GREEN_LLM_PROVIDER`/
`GREEN_LLM_MODEL` env var > config-file `llm_provider`/`llm_model` key >
built-in default (Anthropic, current Sonnet pin). Run `green providers`
to list every registered provider, its default model, its API-key env
var, and its capability groups (batch support, tool-use, token
accounting) without needing credentials or the optional vendor SDK
installed.

```bash
# Use OpenAI instead of the Anthropic default:
export OPENAI_API_KEY=sk-...
green init -n my-app -l python --provider openai --model gpt-5

# Point at any OpenAI-compatible local server:
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=unused
green init -n my-app -l python --provider openai --model llama3
```


## Documentation

Comprehensive documentation for using Start Green Stay Green:

### User Documentation

- **[Tutorials](docs/TUTORIALS.md)** - Step-by-step guides and common workflows
  - Getting started with your first project
  - Common use cases and patterns
  - Advanced project customization
  - Troubleshooting guide

- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command-line reference
  - All commands with options and examples
  - Configuration file formats
  - Environment variables
  - Error codes and troubleshooting

- **[Generator Guide](docs/GENERATOR_GUIDE.md)** - Generator documentation
  - Built-in generator reference (PreCommit, Scripts, CI, Subagents, etc.)
  - Custom generator development
  - Integration patterns
  - Examples for all generators

- **[AI Orchestration](docs/AI_ORCHESTRATION.md)** - AI features guide
  - API key management and credential storage
  - Using AI-powered generators
  - Error handling and best practices
  - Integration with CI/CD

### Developer Documentation

- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command-line interface documentation
- **[Generator Guide](docs/GENERATOR_GUIDE.md)** - Component generator API reference
- **[AI Orchestration](docs/AI_ORCHESTRATION.md)** - AI integration and API usage
- **[Tutorials](docs/TUTORIALS.md)** - Step-by-step guides and examples
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines
- **[Architecture](plan/SPEC.md)** - Project specification and design
- **[Quality Standards](reference/MAXIMUM_QUALITY_ENGINEERING.md)** - Quality framework

### Viewing Documentation

**For the Start Green Stay Green project itself:**

```bash
# Generate and serve API documentation locally
./scripts/docs.sh --serve

# Open http://localhost:8080 in your browser
```

**For generated projects:**

Once you run `start-green-stay-green init` to create a project, you can generate documentation for that project:

```bash
# Navigate to your generated project
cd my-project

# Generate and serve its documentation
./scripts/docs.sh --serve

# Open http://localhost:8080 in your browser
```

### Online Documentation

- **[ReadTheDocs](https://start-green-stay-green.readthedocs.io)** - Hosted API documentation (auto-deployed on commits to main)
- **[GitHub Pages Dashboard](https://geoffe-ga.github.io/start_green_stay_green/)** - Live metrics dashboard with quality metrics

## Configuration

### Configuration File Format

Start Green Stay Green supports YAML and TOML configuration files. Only
`project_name`, `language`, `llm_provider`, and `llm_model` are read from
the file today — other keys are parsed but ignored (`output_dir` and every
other `init` option must be passed on the command line).

**YAML Example:**

```yaml
# project-config.yaml
project_name: my-awesome-project
language: python
llm_provider: anthropic  # Optional
llm_model: claude-opus-4-5  # Optional
```

**TOML Example:**

```toml
# project-config.toml
project_name = "my-awesome-project"
language = "python"
llm_provider = "anthropic"
llm_model = "claude-opus-4-5"
```

### Configuration Priority

Configuration values are resolved in this order (highest to lowest priority):

1. **Command-line arguments**: `--project-name my-app`
2. **Environment variables** (`llm_provider`/`llm_model` only): `GREEN_LLM_PROVIDER`, `GREEN_LLM_MODEL`
3. **Configuration file**: `config.yaml` or `config.toml`
4. **Interactive prompts** (`project_name`/`language` only): asked if value not provided
5. **Built-in default** (`llm_provider`/`llm_model` only)

### Project Name Validation

Project names must follow these rules:

- Only letters, numbers, hyphens, and underscores
- Cannot start with hyphen or underscore
- Maximum 100 characters
- Cannot use Windows reserved names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)

### Supported Languages

- **Python**: pytest, mypy, ruff, black, isort, bandit
- **TypeScript**: jest, eslint, prettier, typescript
- **Go**: go test, golangci-lint, gofmt
- **Rust**: cargo test, clippy, rustfmt
- **Swift**: swift test (≥90% coverage via llvm-cov), SwiftLint, swift-format, Periphery
- **Kotlin**: ./gradlew test (≥90% coverage via Kover), detekt, ktlint, OWASP dependency-check
- **C/C++**: ctest (≥90% coverage via gcov/lcov), clang-format, clang-tidy + cppcheck, lizard, flawfinder
- **Java**: mvn test (≥90% coverage via JaCoCo), google-java-format, Checkstyle + PMD, SpotBugs, OWASP dependency-check
- **C#**: dotnet test (≥90% coverage via Coverlet), dotnet format, Roslyn analyzers (CA1502 complexity ≤10), SecurityCodeScan + vulnerable-package scan
- **Ruby**: bundle exec rspec (≥90% coverage via SimpleCov), RuboCop (format + lint + complexity ≤10 + Security cops in one `.rubocop.yml` policy home), bundler-audit

See the [CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for the
full per-language toolchain table and prerequisites.

(More languages coming soon)

## Examples

### Example 1: Python Project with All Features

```bash
start-green-stay-green init \
  --project-name data-pipeline \
  --language python \
  --output-dir ~/projects \
  --no-interactive

cd ~/projects/data-pipeline

# All quality infrastructure is ready
./scripts/check-all.sh  # Run all quality checks
./scripts/test.sh       # Run tests with coverage
./scripts/lint.sh       # Run linters and type checkers
```

### Example 2: TypeScript Project

```bash
start-green-stay-green init \
  --project-name web-app \
  --language typescript \
  --dry-run  # Preview first

# If preview looks good, run without --dry-run
start-green-stay-green init \
  --project-name web-app \
  --language typescript
```

### Example 3: Using Config File for Team Standard

```bash
# Create team-standard.yaml
cat > team-standard.yaml <<EOF
language: python
llm_provider: anthropic
llm_model: claude-opus-4-5
EOF

# Generate project with team standards
start-green-stay-green init \
  --project-name new-service \
  --config team-standard.yaml
```

### Example 4: Batch Project Creation

```bash
# Create multiple projects with same standards
for name in service-a service-b service-c; do
  start-green-stay-green init \
    --project-name "$name" \
    --language python \
    --no-interactive
done
```

### Example 5: Swift (watchOS) Project

```bash
# Prerequisites: Swift 5.9, 5.10, or 6.0 with Swift Package Manager (SPM),
# plus the local quality toolchain for the generated pre-commit hooks:
brew install swiftlint swift-format gitleaks

start-green-stay-green init \
  --project-name wrist-timer \
  --language swift \
  --no-interactive

cd wrist-timer
swift package resolve
swift build
pre-commit install
./scripts/check-all.sh  # swift-format, SwiftLint, swift test + ≥90% llvm-cov coverage
```

The generated CI pipeline runs on macOS runners with a Swift
5.9/5.10/6.0 version matrix and a watchOS-simulator build-and-test job.
See [examples/swift/](examples/swift/) for real generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full Swift toolchain table.

### Example 6: Kotlin (Wear OS) Project

```bash
# Prerequisites: JDK 17+ and a local Gradle install (the Gradle wrapper
# is NOT generated — binary artifacts are never scaffolded), plus the
# quality toolchain for the generated pre-commit hooks:
brew install gradle ktlint detekt   # or your platform's SDK manager

start-green-stay-green init \
  --project-name wrist-counter \
  --language kotlin \
  --no-interactive

cd wrist-counter
gradle wrapper        # materialize gradlew once, locally
./gradlew build
pre-commit install
./scripts/check-all.sh  # ktlint, detekt, ./gradlew test + ≥90% Kover coverage
```

The generated CI pipeline runs on ubuntu runners with a JDK 17/21 test
matrix, a quality job enforcing the Kover ≥90% coverage gate, and a
Wear OS debug-APK build (CI provisions its own pinned Gradle, so it is
green before you commit a wrapper). See [examples/kotlin/](examples/kotlin/)
for real generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full Kotlin toolchain table.

### Example 7: C/C++ (Tizen) Project

```bash
# Prerequisites: CMake ≥3.20, Conan 2, and a C11/C17 or C++17/C++20
# compiler (the scaffold pins C++17), plus the quality toolchain for the
# generated pre-commit hooks (clang-tidy ships in the keg-only llvm
# formula on macOS; Debian/Ubuntu: apt-get install clang-format
# clang-tidy cppcheck lcov):
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
./scripts/check-all.sh  # clang-format, clang-tidy + cppcheck + lizard, ctest + ≥90% lcov coverage, flawfinder
```

The generated CI pipeline runs on ubuntu runners with a gcc/clang
build-and-test matrix and a quality job that invokes the generated
scripts themselves (≥90% lcov coverage gate included). The scaffold
deliberately splits into two builds: unit tests need only CMake + Conan,
while packaging the installable `.tpk` watch app requires the Tizen
Studio CLI (a manual install — see the generated README). See
[examples/cpp/](examples/cpp/) for real generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full C/C++ toolchain table.

### Example 8: Java (Wear OS legacy) Project

```bash
# Prerequisites: JDK 17+ and Maven, plus google-java-format for the
# generated pre-commit format hook (the linters are Maven plugins
# pinned in the generated pom.xml - no extra installs):
brew install google-java-format

start-green-stay-green init \
  --project-name wrist-tempo \
  --language java \
  --no-interactive

cd wrist-tempo
mvn test
pre-commit install
./scripts/check-all.sh  # google-java-format, Checkstyle + PMD (CCN ≤10), mvn test + ≥90% JaCoCo coverage, SpotBugs + OWASP dependency-check
```

The generated CI pipeline runs on ubuntu runners with a JDK 17/21
(Temurin) quality matrix running the same Maven goals as the local
build, including the pom-backed `mvn jacoco:check` ≥90% coverage gate.
The scaffold deliberately splits into two builds: the pure logic and
its JUnit 4 tests build with plain Maven on any host, while the watch
APK requires Android tooling (Android Studio / Gradle — see the
generated README). See [examples/java/](examples/java/) for real
generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full Java toolchain table.

### Example 9: C# (.NET) Project

```bash
# Prerequisites: the .NET 8 SDK - dotnet format, the Roslyn analyzers,
# and NuGet all ship inside it, so nothing else to install
# (Debian/Ubuntu: apt-get install dotnet-sdk-8.0):
brew install dotnet-sdk

start-green-stay-green init \
  --project-name wrist-ledger \
  --language csharp \
  --no-interactive

cd wrist-ledger
dotnet test
pre-commit install
./scripts/check-all.sh  # dotnet format, Roslyn analyzers as errors (CA1502 complexity ≤10), dotnet test + ≥90% Coverlet coverage, vulnerable NuGet package scan
```

The generated CI pipeline runs on ubuntu runners with a .NET 8 SDK
quality job (the generated csproj targets net8.0) running the same
dotnet CLI gates as the local build — the csproj is the single home of
the analyzer policy and the ≥90% Coverlet coverage bound, so the
scripts, hooks, and CI cannot drift from it. See
[examples/csharp/](examples/csharp/) for real generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full C# toolchain table.

### Example 10: Ruby Project

```bash
# Prerequisites: Ruby 3.3+ and Bundler - every quality gem (RSpec,
# SimpleCov, RuboCop, bundler-audit, Packwerk) is pinned in the
# generated Gemfile, so bundle install provisions the whole toolchain
# (Debian/Ubuntu: apt-get install ruby-full):
brew install ruby

start-green-stay-green init \
  --project-name wrist-cadence \
  --language ruby \
  --no-interactive

cd wrist-cadence
bundle install
bundle exec rspec
pre-commit install
./scripts/check-all.sh  # RuboCop format check + lint + complexity ≤10 + Security cops, RSpec + ≥90% SimpleCov coverage, bundler-audit dependency CVE scan
```

The generated CI pipeline runs on ubuntu runners with a Ruby 3.3/3.4
quality matrix (the maintained Ruby lines) running the same gates as
the local build — RuboCop reads the same `.rubocop.yml` (the single
home of the format/lint/complexity/security-cop policy) and the ≥90%
SimpleCov coverage bound lives only in `spec/spec_helper.rb`, so the
scripts, hooks, and CI cannot drift from them. See
[examples/ruby/](examples/ruby/) for real generated output and the
[CLI Reference](docs/CLI_REFERENCE.md#--language---l-text-optional) for
the full Ruby toolchain table.

## Project Structure

After running `start-green-stay-green init`, your project will have:

```
my-project/
├── .github/
│   └── workflows/
│       ├── ci.yml                # CI/CD pipeline
│       └── code-review.yml       # AI code review
├── .claude/
│   ├── skills/                   # Custom slash commands
│   └── subagents/                # AI subagent profiles
├── plans/
│   └── architecture/
│       ├── .importlinter         # Python architecture rules
│       ├── README.md             # Architecture documentation
│       └── run-check.sh          # Architecture validation script
├── scripts/
│   ├── check-all.sh              # Run all quality checks
│   ├── test.sh                   # Run tests with coverage
│   ├── lint.sh                   # Run linters and type checkers
│   ├── format.sh                 # Auto-format code
│   ├── security.sh               # Security scanning
│   ├── mutation.sh               # Mutation testing
│   └── fix-all.sh                # Auto-fix issues
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── .pre-commit-config.yaml       # Pre-commit hooks (32 checks)
├── CLAUDE.md                     # Project context for AI
├── pyproject.toml                # Python configuration
└── README.md                     # Project documentation
```

## Quality Standards

All generated projects enforce:

- **Code Coverage**: ≥90% (branch coverage)
- **Docstring Coverage**: ≥95% (pydocstyle / ruff D rules)
- **Mutation Score**: ≥80% (mutmut)
- **Cyclomatic Complexity**: ≤10 per function
- **Maintainability Index**: ≥20 (radon)
- **Type Checking**: MyPy strict mode
- **Security**: Bandit + Safety with zero exceptions
- **Linting**: Ruff (all rules) + Pylint ≥9.0

## Development Workflow

### The 4-Gate Stay Green Methodology

All generated projects follow the Stay Green workflow with 3 sequential quality gates:

1. **Gate 1 - Local Pre-Commit**: Run `./scripts/check-all.sh` - all checks must pass
2. **Gate 2 - CI Pipeline**: Push to branch - all CI jobs must show ✅
3. **Gate 3 - Code Review**: Address all feedback - only merge with LGTM

**Mutation Testing**: Recommended as periodic quality check for critical infrastructure (≥80% score). Run with `./scripts/mutation.sh --paths-to-mutate <files>`.

**Never request review with failing checks. Never merge without LGTM.**

See [Stay Green Workflow](reference/workflows/stay-green.md) for complete documentation.

### Local Development

```bash
# Before every commit
./scripts/check-all.sh  # Must pass before committing

# Auto-fix formatting and linting
./scripts/fix-all.sh

# Run specific checks
./scripts/test.sh       # Tests with coverage
./scripts/lint.sh       # Linters and type checkers
./scripts/security.sh   # Security scanning
./scripts/mutation.sh   # Mutation testing (takes several minutes)
```

### CI Integration

All generated projects include GitHub Actions workflows that run:

- Tests on Python 3.11, 3.12, 3.13
- Code quality checks (ruff, pylint, mypy)
- Security scanning (bandit, pip-audit)
- Coverage reporting with badge updates
- Mutation testing on main branch merges
- AI code review with Claude

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md).

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Geoffe-Ga/start_green_stay_green.git
cd start_green_stay_green

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run all quality checks
./scripts/check-all.sh
```

### Running Tests

```bash
# Run all tests
./scripts/test.sh

# Run specific test file
pytest tests/unit/test_cli.py -v

# Run with coverage report
pytest --cov --cov-report=html
open htmlcov/index.html
```

### Code Style

This project follows:

- **Black**: Code formatting (88-character line length)
- **isort**: Import sorting
- **Ruff**: Comprehensive linting (all rules enabled)
- **MyPy**: Strict type checking
- **Google-style docstrings**: All public APIs

### Quality Standards

All contributions must:

- Pass all 32 pre-commit hooks
- Maintain ≥90% code coverage
- Achieve ≥80% mutation score
- Follow conventional commit format: `feat(scope): description`
- Include tests for new functionality
- Update documentation for user-facing changes

## Roadmap

### Completed

- ✅ Core CLI framework with Typer
- ✅ Init command with parameter validation
- ✅ Architecture enforcement generator
- ✅ GitHub Actions code review workflow
- ✅ Pre-commit hook generation
- ✅ Scripts generation (check-all, test, lint, etc.)
- ✅ Skills generation (Claude Code slash commands)
- ✅ Subagents generation (AI development profiles)
- ✅ CLAUDE.md generation
- ✅ Additive init — safe to re-run in existing directories (#250)
- ✅ `--force` and `--interactive` conflict resolution (#252)
- ✅ YAML-aware pre-commit config merging (#253)
- ✅ Multi-language `--language` support (#254)
- ✅ Swift (watchOS) language support — scaffold, quality tooling, CI, tests (#351, #352, #353, #354)
- ✅ Kotlin (Wear OS) language support — scaffold, quality tooling, CI, tests (#356, #357, #358, #359)
- ✅ C/C++ (Tizen native) language support — scaffold, quality tooling, CI, tests (#361, #362, #363, #364)
- ✅ Java (Wear OS legacy) language support — scaffold, quality tooling, CI, tests, docs (#366, #367, #368, #369)
- ✅ C# (.NET) language support — quality tooling on the foundation scaffold + CI, tests, docs (#370, #371, #372)
- ✅ Ruby language support — quality tooling on the foundation scaffold + CI, tests, docs (#373, #374, #375)

### Planned

- 📋 Template customization
- 📋 Plugin system for custom generators
- 📋 Project upgrade command
- 📋 Integration with more CI platforms

See [SPEC.md](plan/SPEC.md) for complete project specification.

## Troubleshooting

### Common Issues

**Issue**: Command not found after installation

```bash
# Ensure pip install location is in PATH
python -m pip show start-green-stay-green

# Or use python -m
python -m start_green_stay_green init
```

**Issue**: Pre-commit hooks failing on generated project

```bash
# Update pre-commit hooks to latest versions
pre-commit autoupdate

# Clear cache and reinstall
pre-commit clean
pre-commit install --install-hooks
```

**Issue**: Project name validation error

```bash
# Valid names: letters, numbers, hyphens, underscores
start-green-stay-green init --project-name my-app-123  # ✅ Valid

# Invalid names
start-green-stay-green init --project-name "my app"     # ❌ Spaces
start-green-stay-green init --project-name -my-app      # ❌ Starts with -
start-green-stay-green init --project-name con          # ❌ Windows reserved
```

### Getting Help

- **Documentation**: [CLAUDE.md](CLAUDE.md)
- **Issues**: [GitHub Issues](https://github.com/Geoffe-Ga/start_green_stay_green/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Geoffe-Ga/start_green_stay_green/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Claude AI**: For AI-assisted development capabilities
- **Typer**: For the excellent CLI framework
- **Ruff**: For fast and comprehensive Python linting
- **Pre-commit**: For git hook management
- **All contributors**: Thank you for making this project better!

---

**Generated repositories stay green from day one** 🟢
