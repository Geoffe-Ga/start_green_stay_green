# Start Green Stay Green — Project Specification

> **A meta-tool for generating quality-controlled, AI-ready repositories**

## Executive Summary

Start Green Stay Green is a CLI tool that scaffolds new software projects with enterprise-grade quality controls pre-configured. Unlike traditional scaffolding tools (create-react-app, cookiecutter), Start Green Stay Green generates **AI-orchestrated quality infrastructure** — including CI pipelines, scripts, subagents, skills, and architecture enforcement — customized to the user's technology stack and project requirements.

The core insight: Claude Code can produce excellent code **if given strict guardrails**. Start Green Stay Green generates those guardrails.

---

## Project Scope

### What Start Green Stay Green IS

- A CLI tool that generates repository scaffolding
- A quality control framework generator
- A GitHub integration for automated project setup
- An AI-orchestrated workflow generator

### What Start Green Stay Green IS NOT

- A code generator (it generates infrastructure, not business logic)
- A package manager
- A deployment tool
- A runtime dependency

### Technology Stack

| Component | Technology |
|-----------|------------|
| CLI | Python (Typer/Click) |
| AI Orchestration | Anthropic Claude API (Opus for generation, Sonnet for tuning) |
| Version Control | Git + GitHub API |
| Configuration | YAML/TOML |
| Templates | Jinja2 |

### Supported Target Languages

The tool generates quality infrastructure for projects in any of the following languages:

| Language | Package Manager | Test Framework | Linter | Formatter |
|----------|----------------|----------------|--------|-----------|
| Python | pip/poetry/uv | pytest | ruff | black/ruff |
| TypeScript/JavaScript | npm/yarn/pnpm | jest/vitest | eslint | prettier |
| Go | go modules | go test | golangci-lint | gofmt/goimports |
| Rust | cargo | cargo test | clippy | rustfmt |
| Java | maven/gradle | junit | checkstyle | google-java-format |
| C# | nuget/dotnet | xunit/nunit | roslyn | dotnet format |
| Swift | swift package manager | xctest | swiftlint | swiftformat |
| Ruby | bundler | rspec | rubocop | rubocop |
| PHP | composer | phpunit | phpstan | php-cs-fixer |
| Kotlin | gradle/maven | junit | ktlint | ktlint |

---

## Architecture Overview

```
start_green_stay_green/
├── start_green_stay_green/
│   ├── __init__.py
│   ├── cli.py                    # Main CLI entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py           # Global settings
│   │   └── templates/            # Base templates per language
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract generator
│   │   ├── ci.py                 # CI pipeline generator
│   │   ├── precommit.py          # Pre-commit config generator
│   │   ├── scripts.py            # Scripts directory generator
│   │   ├── skills.py             # Claude skills generator
│   │   ├── subagents.py          # Subagent profiles generator
│   │   ├── claude_md.py          # CLAUDE.md generator
│   │   ├── github_actions.py     # GitHub Actions generator
│   │   ├── metrics.py            # Quality metrics dashboard
│   │   └── architecture.py       # Architecture enforcement
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # AI generation orchestrator
│   │   ├── prompts/              # Prompt templates
│   │   └── tuner.py              # Lightweight model tuning pass
│   ├── github/
│   │   ├── __init__.py
│   │   ├── client.py             # GitHub API client
│   │   ├── issues.py             # Issue/Epic creation
│   │   └── actions.py            # Actions workflow management
│   └── utils/
│       ├── __init__.py
│       ├── fs.py                 # Filesystem utilities
│       └── templates.py          # Template rendering
├── templates/                    # Jinja2 templates
│   ├── python/
│   ├── typescript/
│   ├── go/
│   ├── rust/
│   ├── java/
│   ├── csharp/
│   ├── swift/
│   ├── ruby/
│   ├── php/
│   ├── kotlin/
│   └── shared/
├── reference/                    # Reference implementations
│   ├── MAXIMUM_QUALITY_ENGINEERING.md
│   ├── ci/
│   ├── scripts/
│   ├── skills/
│   └── subagents/
├── tests/
├── plans/
│   └── SPEC.md                   # This file
├── pyproject.toml
├── CLAUDE.md
└── README.md
```

---

## Deliverables

### Epic 1: Core Infrastructure Setup

**Goal**: Establish the Start Green Stay Green repository with its own quality controls (dogfooding).

#### Issue 1.1: Repository Initialization
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 1 hour

**Description**:
Initialize the Start Green Stay Green repository with Git, create initial directory structure, and configure GitHub repository settings.

**Acceptance Criteria**:
- [ ] Git repository initialized with `main` branch
- [ ] `.gitignore` configured for Python
- [ ] Directory structure matches architecture overview
- [ ] GitHub repository created (if token provided)
- [ ] Branch protection rules configured
- [ ] CODEOWNERS file created

**Implementation Notes**:
```bash
# Commands to execute
git init
gh repo create start_green_stay_green --public --source=. --remote=origin
gh api repos/{owner}/start_green_stay_green/branches/main/protection -X PUT -f required_status_checks='{"strict":true,"contexts":["ci"]}'
```

---

#### Issue 1.2: Python Project Configuration
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 2 hours

**Description**:
Set up `pyproject.toml` with all dependencies, tool configurations, and metadata. This must match the strictness level defined in MAXIMUM_QUALITY_ENGINEERING.md Part 2.1.

**Acceptance Criteria**:
- [ ] `pyproject.toml` created with project metadata
- [ ] All dev dependencies specified (ruff, mypy, black, pytest, etc.)
- [ ] Tool configurations match MAXIMUM_QUALITY_ENGINEERING.md
- [ ] `requirements.txt` and `requirements-dev.txt` generated
- [ ] Package installable via `pip install -e .`

**Dependencies**:
- Issue 1.1 (Repository Initialization)

**Reference**:
- MAXIMUM_QUALITY_ENGINEERING.md Section 2.1 (Python Projects)

---

#### Issue 1.3: Pre-commit Configuration
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 1 hour

**Description**:
Copy and adapt `.pre-commit-config.yaml` from MAXIMUM_QUALITY_ENGINEERING.md. All hooks must run scripts from `/scripts/` where possible rather than invoking tools directly.

**Acceptance Criteria**:
- [ ] `.pre-commit-config.yaml` created
- [ ] All hooks from MAXIMUM_QUALITY_ENGINEERING.md Section 2.1 included
- [ ] Hooks point to local scripts where feasible
- [ ] `pre-commit install` runs successfully
- [ ] All hooks pass on clean repository

**Script Mapping**:
| Hook | Script |
|------|--------|
| ruff | `scripts/lint.sh --check` |
| black | `scripts/format.sh --check` |
| mypy | `scripts/typecheck.sh` |
| bandit | `scripts/security.sh` |
| pytest | `scripts/test.sh --unit` |

**Dependencies**:
- Issue 1.2 (Python Project Configuration)
- Issue 1.4 (Scripts Directory)

---

#### Issue 1.4: Scripts Directory
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 3 hours

**Description**:
Create the `/scripts/` directory with all quality control scripts. Scripts must be the **single source of truth** for running checks — CI, pre-commit, and local development all invoke these scripts.

**Acceptance Criteria**:
- [ ] All scripts executable (`chmod +x`)
- [ ] Consistent argument interface (`--fix`, `--check`, `--verbose`)
- [ ] Exit codes follow conventions (0=success, 1=failure, 2=error)
- [ ] Each script has `--help` documentation
- [ ] Scripts work on macOS) Linux, and in CI

**Required Scripts**:

```
scripts/
├── lint.sh              # Ruff linting (--fix to auto-fix)
├── format.sh            # Black + isort formatting
├── typecheck.sh         # MyPy type checking
├── test.sh              # Pytest (--unit, --integration, --e2e, --all)
├── security.sh          # Bandit + Safety
├── coverage.sh          # Coverage report generation
├── docs.sh              # Documentation generation
├── review-pr.sh         # Automated PR review (loops through open PRs)
├── check-all.sh         # Runs all checks in sequence
├── fix-all.sh           # Auto-fixes everything possible
├── audit-deps.sh        # Dependency audit
├── complexity.sh        # Radon/Xenon complexity analysis
└── setup-dev.sh         # Developer environment setup
```

**Script Template**:
```bash
#!/usr/bin/env bash
set -euo pipefail

# scripts/lint.sh - Run linting checks
# Usage: ./scripts/lint.sh [--fix] [--verbose]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FIX=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fix) FIX=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --help) echo "Usage: $0 [--fix] [--verbose]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 2 ;;
    esac
done

cd "$PROJECT_ROOT"

if $FIX; then
    ruff check . --fix
else
    ruff check .
fi
```

**Dependencies**:
- Issue 1.2 (Python Project Configuration)

---

#### Issue 1.5: CI Pipeline
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 3 hours

**Description**:
Create GitHub Actions CI workflow that invokes scripts (not tools directly). Must include all jobs from MAXIMUM_QUALITY_ENGINEERING.md Part 3.1.

**Acceptance Criteria**:
- [ ] `.github/workflows/ci.yml` created
- [ ] All jobs invoke scripts from `/scripts/`
- [ ] Jobs run in parallel where possible
- [ ] Matrix testing for Python versions (3.11, 3.12)
- [ ] Caching configured for pip dependencies
- [ ] Artifacts uploaded (coverage, test results)
- [ ] All quality gates enforced

**Job Structure**:
```yaml
jobs:
  quality:
    steps:
      - run: ./scripts/lint.sh
      - run: ./scripts/format.sh --check
      - run: ./scripts/typecheck.sh
      - run: ./scripts/security.sh
      - run: ./scripts/complexity.sh

  test:
    needs: quality
    strategy:
      matrix:
        python: ['3.11', '3.12']
    steps:
      - run: ./scripts/test.sh --unit --coverage
      - run: ./scripts/test.sh --integration

  mutation:
    needs: test
    steps:
      - run: ./scripts/test.sh --mutation

  security:
    steps:
      - run: ./scripts/security.sh --full
      - run: ./scripts/audit-deps.sh
```

**Dependencies**:
- Issue 1.4 (Scripts Directory)

**Reference**:
- MAXIMUM_QUALITY_ENGINEERING.md Section 3.1

---

#### Issue 1.6: CLAUDE.md Configuration
**Type**: Task
**Priority**: P1 - High
**Estimate**: 2 hours

**Description**:
Create CLAUDE.md that instructs Claude Code on how to work within this repository. Must reference MAXIMUM_QUALITY_ENGINEERING.md principles and enforce strict quality standards.

**Acceptance Criteria**:
- [ ] CLAUDE.md created at repository root
- [ ] Project overview and architecture documented
- [ ] Development workflow documented
- [ ] Quality standards explicitly stated
- [ ] Common commands listed
- [ ] Forbidden patterns documented
- [ ] Testing requirements specified

**Structure**:
```markdown
# CLAUDE.md

## Project Overview
[Brief description of Start Green Stay Green]

## Architecture
[Key components and their relationships]

## Development Workflow
1. Create feature branch
2. Implement changes
3. Run ./scripts/check-all.sh
4. Commit with conventional commits
5. Create PR

## Quality Standards
- Code coverage: ≥90%
- All linters must pass
- Type annotations required
- Docstrings required (Google style)

## Commands
- `./scripts/check-all.sh` - Run all checks
- `./scripts/test.sh --unit` - Run unit tests
- `./scripts/lint.sh --fix` - Fix linting issues

## Forbidden Patterns
- No `# type: ignore` without justification
- No `noqa` without issue reference
- No print statements (use logging)
- No TODO without issue reference

## Before Committing
Always run: `./scripts/check-all.sh`
```

**Dependencies**:
- Issue 1.4 (Scripts Directory)

---

### Epic 2: AI Orchestration Layer

**Goal**: Implement the AI-powered generation system that creates customized quality infrastructure.

#### Issue 2.1: AI Orchestrator Core
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 4 hours

**Description**:
Implement the core AI orchestration system that coordinates generation tasks using Claude API. The orchestrator manages prompt construction, context injection, and response handling.

**Acceptance Criteria**:
- [ ] `ai/orchestrator.py` implemented
- [ ] Anthropic API client configured
- [ ] Prompt template loading system
- [ ] Context injection from reference files
- [ ] Response parsing and validation
- [ ] Error handling and retry logic
- [ ] Token usage tracking

**Interface**:
```python
class AIOrchestrator:
    """Coordinates AI-powered generation tasks."""

    def __init__(self, api_key: str, model: str = "claude-opus-4-20250514"):
        ...

    async def generate(
        self,
        prompt_template: str,
        context: dict[str, str],
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Generate content using AI with injected context."""
        ...

    async def tune(
        self,
        content: str,
        target_context: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> str:
        """Lightweight tuning pass to adapt content to specific repo."""
        ...
```

**Dependencies**:
- Issue 1.2 (Python Project Configuration)

---

#### Issue 2.2: Prompt Templates
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 3 hours

**Description**:
Create Jinja2 prompt templates for each generator. Templates must include:
1. System context (role, constraints)
2. Reference material injection points
3. User configuration placeholders
4. Output format specifications

**Acceptance Criteria**:
- [ ] `ai/prompts/` directory created
- [ ] Template for each generator type
- [ ] Templates use Jinja2 syntax
- [ ] Reference injection points clearly marked
- [ ] Output format strictly specified
- [ ] Templates tested with sample inputs

**Template Structure**:
```
ai/prompts/
├── base.j2                 # Shared preamble
├── ci.j2                   # CI pipeline generation
├── precommit.j2            # Pre-commit config generation
├── scripts.j2              # Scripts generation
├── skills.j2               # Skills generation
├── subagents.j2            # Subagent profiles generation
├── claude_md.j2            # CLAUDE.md generation
├── github_actions.j2       # GitHub Actions generation
├── metrics.j2              # Metrics dashboard generation
└── architecture.j2         # Architecture rules generation
```

**Example Template** (`ci.j2`):
```jinja2
{% extends "base.j2" %}

{% block system %}
You are generating a CI pipeline configuration for a {{ language }} project.
The pipeline MUST invoke scripts from /scripts/ rather than tools directly.
All quality gates from the reference must be enforced.
{% endblock %}

{% block reference %}
## Reference CI Configuration
{{ reference_ci }}

## Quality Standards
{{ maximum_quality_engineering_part_3 }}
{% endblock %}

{% block user_config %}
## Project Configuration
- Language: {{ language }}
- Framework: {{ framework }}
- Test Runner: {{ test_runner }}
- Package Manager: {{ package_manager }}
{% endblock %}

{% block output_format %}
Output ONLY valid YAML for a GitHub Actions workflow.
Do not include any explanation or markdown code fences.
{% endblock %}
```

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)

---

#### Issue 2.3: Tuning Pass System
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 2 hours

**Description**:
Implement a lightweight tuning system using Sonnet that adapts copied content to fit the target repository context. This is used for Skills and Subagents that are "copied over with a quick pass."

**Acceptance Criteria**:
- [ ] `ai/tuner.py` implemented
- [ ] Uses Claude Sonnet (not Opus) for cost efficiency
- [ ] Preserves structure while adapting content
- [ ] Validates output matches input format
- [ ] Logs changes made
- [ ] Supports dry-run mode

**Interface**:
```python
class ContentTuner:
    """Adapts content to fit target repository context."""

    async def tune(
        self,
        source_content: str,
        source_context: str,
        target_context: str,
        preserve_sections: list[str] | None = None,
    ) -> TuningResult:
        """
        Tune content from source to target context.

        Args:
            source_content: Original content to adapt
            source_context: Description of source repo
            target_context: Description of target repo
            preserve_sections: Sections to leave unchanged

        Returns:
            TuningResult with adapted content and changelog
        """
        ...
```

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)

---

### Epic 3: Generator Implementations

**Goal**: Implement individual generators for each deliverable type.

#### Issue 3.1: CI Generator
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 4 hours

**Description**:
Implement the CI pipeline generator that creates GitHub Actions workflows customized to the target project's language and framework.

**Acceptance Criteria**:
- [ ] `generators/ci.py` implemented
- [ ] Supports all target languages (Python, TypeScript, Go, Rust, Java, C#, Swift, Ruby, PHP, Kotlin)
- [ ] Injects MAXIMUM_QUALITY_ENGINEERING.md Part 3 as context
- [ ] Injects Start Green Stay Green's own CI as reference
- [ ] Generated CI invokes scripts, not tools
- [ ] Validates generated YAML
- [ ] Includes all required jobs (quality, test, mutation, security)

**Generation Flow**:
```
User Config → Prompt Template → AI Generation → YAML Validation → Output
     ↓              ↓
  Language      Reference CI
  Framework     MAXIMUM_QUALITY_ENGINEERING
```

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)
- Issue 2.2 (Prompt Templates)

---

#### Issue 3.2: Pre-commit Generator
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 3 hours

**Description**:
Generate `.pre-commit-config.yaml` customized to target language. Must prefer local scripts over tool invocations.

**Acceptance Criteria**:
- [ ] `generators/precommit.py` implemented
- [ ] Language-specific hook selection
- [ ] Scripts preferred over tools
- [ ] Injects MAXIMUM_QUALITY_ENGINEERING.md Part 2 as context
- [ ] Validates generated YAML
- [ ] Includes all security hooks

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)
- Issue 2.2 (Prompt Templates)

---

#### Issue 3.3: Scripts Generator
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 4 hours

**Description**:
Generate the `/scripts/` directory with all quality control scripts adapted to the target project.

**Acceptance Criteria**:
- [ ] `generators/scripts.py` implemented
- [ ] All scripts from Issue 1.4 generated
- [ ] Scripts adapted to target language/tools
- [ ] Consistent interface (--fix, --check, --verbose)
- [ ] Scripts are executable
- [ ] --help implemented for each

**Script Customization Matrix**:
| Script | Python | TypeScript | Go | Rust | Java | C# | Swift | Ruby | PHP | Kotlin |
|--------|--------|------------|----|----|------|-------|-------|------|-----|--------|
| lint.sh | ruff | eslint | golangci-lint | clippy | checkstyle | roslyn | swiftlint | rubocop | phpstan | ktlint |
| format.sh | black/ruff | prettier | gofmt | rustfmt | google-java-format | dotnet format | swiftformat | rubocop | php-cs-fixer | ktlint |
| typecheck.sh | mypy | tsc | - | - | - | - | - | sorbet | psalm | - |
| test.sh | pytest | jest | go test | cargo test | junit | xunit/nunit | xctest | rspec | phpunit | junit |
| security.sh | bandit | npm audit | gosec | cargo audit | spotbugs | security code scan | - | brakeman | security-checker | - |

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)
- Issue 2.2 (Prompt Templates)

---

#### Issue 3.4: Skills Generator
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Copy skills from Start Green Stay Green reference and tune them for the target repository using lightweight Sonnet pass.

**Acceptance Criteria**:
- [ ] `generators/skills.py` implemented
- [ ] Copies from `reference/skills/`
- [ ] Tunes using ContentTuner
- [ ] Includes vibe skill (coding style/tone)
- [ ] Includes concurrency skill
- [ ] Preserves skill structure
- [ ] Validates output

**Required Skills**:
```
skills/
├── vibe.md               # Coding style and tone guidelines
├── concurrency.md        # Async/threading patterns
├── error-handling.md     # Exception patterns
├── testing.md            # Test writing guidelines
├── documentation.md      # Doc style guidelines
└── security.md           # Security patterns
```

**Dependencies**:
- Issue 2.3 (Tuning Pass System)

---

#### Issue 3.5: Subagents Generator
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 4 hours

**Description**:
Generate subagent profiles for AI-driven development workflow. Must include dependency checker agent that reviews packages before shipping.

**Acceptance Criteria**:
- [ ] `generators/subagents.py` implemented
- [ ] Copies from `reference/subagents/`
- [ ] Tunes using ContentTuner
- [ ] Includes all agents from MAXIMUM_QUALITY_ENGINEERING.md Part 8
- [ ] Includes dependency checker agent
- [ ] Agent allocation via chief-architect pattern
- [ ] Validates output structure

**Required Subagents**:
```
subagents/
├── chief-architect.md    # Coordinates other agents, allocates work
├── quality-reviewer.md   # Code quality enforcement
├── test-generator.md     # Test generation
├── security-auditor.md   # Security review
├── dependency-checker.md # Package/dependency validation (NEW)
├── documentation.md      # Documentation writer
├── refactorer.md         # Code improvement suggestions
└── performance.md        # Performance analysis
```

**Dependency Checker Agent Spec**:
```markdown
# Dependency Checker Agent Profile

## Role
You review all package additions and updates before they ship.
You are the last line of defense against supply chain attacks.

## Checks (ALL MANDATORY)
- [ ] Package source is trusted (npm, PyPI, not random GitHub)
- [ ] Package has recent commits (not abandoned)
- [ ] Package has reasonable download count
- [ ] No known vulnerabilities (CVE check)
- [ ] License is compatible
- [ ] Package size is reasonable
- [ ] No suspicious install scripts
- [ ] Transitive dependencies reviewed

## Response Format
APPROVED: [package] - all checks pass
REJECTED: [package] - [specific reason with evidence]
REVIEW_NEEDED: [package] - [concerns requiring human review]
```

**Dependencies**:
- Issue 2.3 (Tuning Pass System)

---

#### Issue 3.6: CLAUDE.md Generator
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 3 hours

**Description**:
Generate CLAUDE.md customized to the target project, incorporating project-specific commands and quality standards.

**Acceptance Criteria**:
- [ ] `generators/claude_md.py` implemented
- [ ] Injects MAXIMUM_QUALITY_ENGINEERING.md as context
- [ ] Injects Start Green Stay Green's own CLAUDE.md as reference
- [ ] Includes project-specific commands
- [ ] Documents generated scripts
- [ ] Documents generated skills
- [ ] Validates markdown structure

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)
- Issue 2.2 (Prompt Templates)

---

#### Issue 3.7: GitHub Actions Code Review
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Generate GitHub Actions workflow for automated PR code review. Must provide unequivocal LGTM or categorized issues.

**Acceptance Criteria**:
- [ ] `generators/github_actions.py` implemented
- [ ] Workflow triggers on PR open/update
- [ ] Uses Claude API for review
- [ ] Response format strictly enforced
- [ ] Issue categorization (Low/Medium/High/Critical)
- [ ] Auto-creates GitHub issues for Low issues
- [ ] Blocks merge for Medium+ issues
- [ ] Template included in workflow

**Response Format**:
```
## Code Review Results

### Status: [LGTM | CHANGES_REQUESTED]

### Issues Found

#### Critical (Block Merge)
- [ ] [Issue description with line reference]

#### High (Block Merge)
- [ ] [Issue description with line reference]

#### Medium (Block Merge)
- [ ] [Issue description with line reference]

#### Low (Create GitHub Issue for Future PR)
- [ ] [Issue description] → Created issue #123
```

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)

---

#### Issue 3.8: Quality Metrics Dashboard
**Type**: Feature
**Priority**: P2 - Medium
**Estimate**: 4 hours

**Description**:
Generate quality metrics tracking configuration per MAXIMUM_QUALITY_ENGINEERING.md Part 9.1.

**Acceptance Criteria**:
- [ ] `generators/metrics.py` implemented
- [ ] All 10 metrics from Part 9.1 configured
- [ ] SonarQube configuration generated (if applicable)
- [ ] GitHub badge generation
- [ ] Threshold enforcement in CI
- [ ] Trend tracking setup
- [ ] Dashboard template (HTML/React)

**Metrics to Track**:
| Metric | Threshold | Tool |
|--------|-----------|------|
| Code Coverage | ≥90% | pytest-cov / jest |
| Branch Coverage | ≥85% | pytest-cov / jest |
| Mutation Score | ≥80% | mutmut / stryker |
| Cyclomatic Complexity | ≤10 | radon / eslint |
| Cognitive Complexity | ≤15 | sonarqube |
| Maintainability Index | ≥20 | radon |
| Technical Debt Ratio | ≤5% | sonarqube |
| Documentation Coverage | ≥95% | interrogate |
| Dependency Freshness | ≤30 days | npm-check-updates |
| Security Vulnerabilities | 0 critical/high | safety / npm audit |

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)

---

#### Issue 3.9: Architecture Enforcement Generator
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Generate architecture enforcement configuration (import-linter for Python, dependency-cruiser for TypeScript) to be run manually after code is generated.

**Acceptance Criteria**:
- [ ] `generators/architecture.py` implemented
- [ ] Python: `.importlinter` generated
- [ ] TypeScript: `.dependency-cruiser.js` generated
- [ ] Rules enforce layer separation
- [ ] Rules prevent circular dependencies
- [ ] Rules enforce domain independence
- [ ] Output placed in `/plans/architecture/`
- [ ] README with usage instructions

**Output Structure**:
```
plans/architecture/
├── README.md              # Usage instructions
├── .importlinter          # Python rules (if applicable)
├── .dependency-cruiser.js # TypeScript rules (if applicable)
└── run-check.sh           # Script to execute check
```

**Dependencies**:
- Issue 2.1 (AI Orchestrator Core)

---

### Epic 4: CLI Interface

**Goal**: Implement the user-facing CLI for Start Green Stay Green.

#### Issue 4.1: CLI Framework Setup
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 2 hours

**Description**:
Set up the CLI framework using Typer with rich output formatting.

**Acceptance Criteria**:
- [ ] `cli.py` implemented with Typer
- [ ] Rich console output configured
- [ ] Help text for all commands
- [ ] Version command
- [ ] Verbose/quiet modes
- [ ] Configuration file support

**Commands**:
```
green --help                    # Primary command (if available on PyPI)
green version                   # Alternative: sgsg (if "green" unavailable)
green init [options]            # Initialize new project
green generate [component]      # Generate specific component
green validate                  # Validate generated output
green github                    # GitHub integration commands
```

**Note**: The CLI command will be `green` if available on PyPI, otherwise `sgsg`.

**Dependencies**:
- Issue 1.2 (Python Project Configuration)

---

#### Issue 4.2: Init Command
**Type**: Feature
**Priority**: P0 - Critical
**Estimate**: 4 hours

**Description**:
Implement the main `start_green_stay_green init` command that orchestrates project generation.

**Acceptance Criteria**:
- [ ] Interactive prompts for configuration
- [ ] Non-interactive mode with config file
- [ ] Progress indicator for generation steps
- [ ] Error handling with clear messages
- [ ] Dry-run mode
- [ ] Output directory selection
- [ ] Git initialization

**Interactive Flow**:
```
$ green init

🚀 Welcome to Start Green Stay Green

? Project name: my-awesome-project
? Primary language: Python
? Framework (optional): FastAPI
? Include TypeScript frontend? Yes
? Frontend framework: React
? GitHub repository? Yes
? Create GitHub issues? Yes

📋 Configuration Summary:
   Project: my-awesome-project
   Backend: Python + FastAPI
   Frontend: TypeScript + React
   GitHub: Enabled with issues

? Proceed with generation? Yes

⏳ Generating CI pipeline... ✓
⏳ Generating pre-commit config... ✓
⏳ Generating scripts... ✓
⏳ Generating skills... ✓
⏳ Generating subagents... ✓
⏳ Generating CLAUDE.md... ✓
⏳ Generating GitHub Actions... ✓
⏳ Setting up quality metrics... ✓
⏳ Generating architecture rules... ✓
⏳ Initializing Git... ✓
⏳ Creating GitHub repository... ✓
⏳ Creating GitHub issues... ✓

✅ Project generated successfully!

Next steps:
  cd my-awesome-project
  ./scripts/setup-dev.sh
  git push -u origin main
```

**Dependencies**:
- Issue 4.1 (CLI Framework Setup)
- All Epic 3 generators

---

#### Issue 4.3: GitHub Integration
**Type**: Feature
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Implement GitHub integration for repository creation and issue generation.

**Acceptance Criteria**:
- [ ] `github/client.py` implemented
- [ ] Repository creation via API
- [ ] Branch protection configuration
- [ ] Issue creation from SPEC.md
- [ ] Epic/milestone creation
- [ ] Labels setup
- [ ] Token management (secure)

**Commands**:
```
green github auth          # Configure GitHub token
green github create-repo   # Create repository
green github create-issues # Create issues from SPEC.md
green github setup-all     # Full GitHub setup
```

**Issue Generation from SPEC.md**:
Parse this SPEC.md (or generated SPEC.md) and create GitHub issues for each Issue section with:
- Title from Issue header
- Body from Description + Acceptance Criteria
- Labels from Type/Priority
- Milestone from Epic
- Estimate as label

**Dependencies**:
- Issue 4.1 (CLI Framework Setup)

---

### Epic 5: Reference Implementation

**Goal**: Create and maintain reference implementations that serve as context for AI generation.

#### Issue 5.1: Copy Existing Start Green Stay Green Assets
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 2 hours

**Description**:
Copy all reusable assets from the existing Start Green Stay Green repository into the `reference/` directory.

**Acceptance Criteria**:
- [ ] `reference/` directory created
- [ ] MAXIMUM_QUALITY_ENGINEERING.md copied
- [ ] CI workflows copied to `reference/ci/`
- [ ] Scripts copied to `reference/scripts/`
- [ ] Skills created in `reference/skills/`
- [ ] Subagents created in `reference/subagents/`
- [ ] Pre-commit config copied
- [ ] All references validated

**Reference Structure**:
```
reference/
├── MAXIMUM_QUALITY_ENGINEERING.md
├── ci/
│   ├── python.yml
│   ├── typescript.yml
│   ├── go.yml
│   ├── rust.yml
│   ├── java.yml
│   ├── csharp.yml
│   ├── swift.yml
│   ├── ruby.yml
│   ├── php.yml
│   └── kotlin.yml
├── scripts/
│   ├── python/
│   ├── typescript/
│   ├── go/
│   ├── rust/
│   ├── java/
│   ├── csharp/
│   ├── swift/
│   ├── ruby/
│   ├── php/
│   └── kotlin/
├── skills/
│   ├── vibe.md
│   ├── concurrency.md
│   └── ...
├── subagents/
│   ├── chief-architect.md
│   ├── quality-reviewer.md
│   └── ...
├── precommit/
│   ├── python.yaml
│   ├── typescript.yaml
│   ├── go.yaml
│   ├── rust.yaml
│   ├── java.yaml
│   ├── csharp.yaml
│   ├── swift.yaml
│   ├── ruby.yaml
│   ├── php.yaml
│   └── kotlin.yaml
└── claude/
    └── template.md
```

**Dependencies**:
- Issue 1.1 (Repository Initialization)

---

#### Issue 5.2: Create Missing Skills
**Type**: Task
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Create skills that are mentioned in deliverables but not in MAXIMUM_QUALITY_ENGINEERING.md.

**Acceptance Criteria**:
- [ ] `reference/skills/vibe.md` created
- [ ] `reference/skills/concurrency.md` created
- [ ] Skills follow consistent format
- [ ] Skills include examples
- [ ] Skills are language-agnostic where possible

**Vibe Skill**:
```markdown
# Vibe Skill

## Purpose
Establishes coding style, tone, and aesthetic consistency.

## Principles
1. Code should read like well-written prose
2. Names should be self-documenting
3. Comments explain "why", not "what"
4. Formatting should be invisible (consistent)
5. Complexity should be hidden behind simple interfaces

## Anti-patterns
- Clever code over clear code
- Abbreviations in names
- Deep nesting
- Long functions
- Mixed abstraction levels

## Examples
[Language-specific examples]
```

**Concurrency Skill**:
```markdown
# Concurrency Skill

## Purpose
Safe and efficient concurrent code patterns.

## Principles
1. Prefer immutability
2. Minimize shared state
3. Use structured concurrency
4. Explicit cancellation handling
5. Proper resource cleanup

## Patterns by Language
### Python
- asyncio with proper task management
- ThreadPoolExecutor for CPU-bound
- ProcessPoolExecutor for true parallelism

### TypeScript
- Promise.all with proper error handling
- Worker threads for CPU-bound

## Anti-patterns
- Fire and forget tasks
- Unhandled rejections
- Callback hell
- Race conditions in shared state
```

**Dependencies**:
- Issue 5.1 (Copy Existing Start Green Stay Green Assets)

---

#### Issue 5.3: Create Dependency Checker Subagent
**Type**: Task
**Priority**: P1 - High
**Estimate**: 2 hours

**Description**:
Create the dependency checker subagent that's mentioned in deliverables but not in MAXIMUM_QUALITY_ENGINEERING.md.

**Acceptance Criteria**:
- [ ] `reference/subagents/dependency-checker.md` created
- [ ] All checks from Issue 3.5 documented
- [ ] Response format clearly specified
- [ ] Examples included
- [ ] Integration with CI documented

**Dependencies**:
- Issue 5.1 (Copy Existing Start Green Stay Green Assets)

---

### Epic 6: Testing & Documentation

**Goal**: Comprehensive testing and documentation for Start Green Stay Green itself.

#### Issue 6.1: Unit Tests for Generators
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 4 hours

**Description**:
Write unit tests for all generator modules.

**Acceptance Criteria**:
- [ ] Tests for each generator in `tests/unit/generators/`
- [ ] Mock AI responses for deterministic tests
- [ ] Test valid output generation
- [ ] Test error handling
- [ ] Test edge cases
- [ ] Coverage ≥90%

**Dependencies**:
- All Epic 3 issues

---

#### Issue 6.2: Integration Tests
**Type**: Task
**Priority**: P1 - High
**Estimate**: 3 hours

**Description**:
Write integration tests that verify end-to-end generation flow.

**Acceptance Criteria**:
- [ ] Test full init flow
- [ ] Test GitHub integration (mocked)
- [ ] Test generated output validity
- [ ] Test generated scripts execute
- [ ] Test generated CI syntax valid

**Dependencies**:
- Issue 4.2 (Init Command)
- Issue 6.1 (Unit Tests)

---

#### Issue 6.3: README Documentation
**Type**: Task
**Priority**: P0 - Critical
**Estimate**: 2 hours

**Description**:
Write comprehensive README for Start Green Stay Green.

**Acceptance Criteria**:
- [ ] Project overview
- [ ] Installation instructions
- [ ] Quick start guide
- [ ] Full command reference
- [ ] Configuration options
- [ ] Examples
- [ ] Contributing guidelines
- [ ] License information

**Dependencies**:
- Issue 4.2 (Init Command)

---

#### Issue 6.4: API Documentation
**Type**: Task
**Priority**: P2 - Medium
**Estimate**: 2 hours

**Description**:
Generate API documentation for all public modules.

**Acceptance Criteria**:
- [ ] pdoc configuration
- [ ] All public APIs documented
- [ ] Examples in docstrings
- [ ] Generated HTML docs
- [ ] Docs deployment setup

**Dependencies**:
- All Epic 3 issues

---

## Issue Dependencies Graph

```
Epic 1 (Foundation)
├── 1.1 Repository Init
│   └── 1.2 Python Config
│       ├── 1.3 Pre-commit
│       │   └── (depends on 1.4)
│       ├── 1.4 Scripts
│       │   ├── 1.3 Pre-commit
│       │   ├── 1.5 CI
│       │   └── 1.6 CLAUDE.md
│       └── 1.5 CI
│           └── (depends on 1.4)

Epic 2 (AI Layer)
├── 2.1 Orchestrator
│   ├── 2.2 Prompt Templates
│   │   └── All Epic 3 generators
│   └── 2.3 Tuner
│       ├── 3.4 Skills
│       └── 3.5 Subagents

Epic 3 (Generators) - All depend on 2.1 + 2.2
├── 3.1 CI Generator
├── 3.2 Pre-commit Generator
├── 3.3 Scripts Generator
├── 3.4 Skills Generator (also 2.3)
├── 3.5 Subagents Generator (also 2.3)
├── 3.6 CLAUDE.md Generator
├── 3.7 GitHub Actions Generator
├── 3.8 Metrics Generator
└── 3.9 Architecture Generator

Epic 4 (CLI)
├── 4.1 CLI Framework
│   ├── 4.2 Init Command
│   │   └── (depends on all Epic 3)
│   └── 4.3 GitHub Integration

Epic 5 (Reference)
├── 5.1 Copy Assets
│   ├── 5.2 Missing Skills
│   └── 5.3 Dependency Checker

Epic 6 (Testing)
├── 6.1 Unit Tests (after Epic 3)
│   └── 6.2 Integration Tests (after 4.2)
├── 6.3 README (after 4.2)
└── 6.4 API Docs (after Epic 3)
```

---

## Implementation Order (Recommended)

### Phase 1: Foundation (Week 1)
1. Issue 1.1: Repository Initialization
2. Issue 1.2: Python Project Configuration
3. Issue 5.1: Copy Existing Start Green Stay Green Assets
4. Issue 1.4: Scripts Directory
5. Issue 1.3: Pre-commit Configuration
6. Issue 1.5: CI Pipeline
7. Issue 1.6: CLAUDE.md Configuration

### Phase 2: AI Layer (Week 2)
1. Issue 2.1: AI Orchestrator Core
2. Issue 2.2: Prompt Templates
3. Issue 2.3: Tuning Pass System
4. Issue 5.2: Create Missing Skills
5. Issue 5.3: Create Dependency Checker Subagent

### Phase 3: Generators (Week 3)
1. Issue 3.1: CI Generator
2. Issue 3.2: Pre-commit Generator
3. Issue 3.3: Scripts Generator
4. Issue 3.6: CLAUDE.md Generator
5. Issue 3.4: Skills Generator
6. Issue 3.5: Subagents Generator

### Phase 4: Advanced Generators (Week 4)
1. Issue 3.7: GitHub Actions Code Review
2. Issue 3.8: Quality Metrics Dashboard
3. Issue 3.9: Architecture Enforcement Generator

### Phase 5: CLI & Integration (Week 5)
1. Issue 4.1: CLI Framework Setup
2. Issue 4.2: Init Command
3. Issue 4.3: GitHub Integration

### Phase 6: Polish (Week 6)
1. Issue 6.1: Unit Tests
2. Issue 6.2: Integration Tests
3. Issue 6.3: README Documentation
4. Issue 6.4: API Documentation

---

## Success Criteria

Start Green Stay Green v2.0 is complete when:

1. **Functional**: `start_green_stay_green init` successfully generates a complete project scaffold
2. **Quality**: Generated projects pass all their own quality checks
3. **Dogfooding**: Start Green Stay Green repository uses Start Green Stay Green-generated infrastructure
4. **Documentation**: Full documentation and examples available
5. **Testing**: ≥90% test coverage with mutation score ≥80%
6. **GitHub**: Can create repository and issues from SPEC.md

---

## Appendix A: gh CLI Commands for Issue Creation

```bash
#!/usr/bin/env bash
# scripts/create-github-issues.sh
# Creates GitHub issues from this SPEC.md

# Epic 1: Core Infrastructure Setup
gh issue create \
  --title "1.1: Repository Initialization" \
  --body "$(cat <<'EOF'
## Type: Task
## Priority: P0 - Critical
## Estimate: 1 hour

### Description
Initialize the start_green_stay_green repository with Git, create initial directory structure, and configure GitHub repository settings.

### Acceptance Criteria
- [ ] Git repository initialized with `main` branch
- [ ] `.gitignore` configured for Python
- [ ] Directory structure matches architecture overview
- [ ] GitHub repository created (if token provided)
- [ ] Branch protection rules configured
- [ ] CODEOWNERS file created
EOF
)" \
  --label "task,P0-critical,epic:foundation" \
  --milestone "Phase 1: Foundation"

# ... (repeat for each issue)
```

---

## Appendix B: Configuration Schema

```yaml
# start_green_stay_green.yaml - Project configuration file
project:
  name: my-project
  description: "A brief description"

languages:
  # Supported: python, typescript, javascript, go, rust, java, csharp, swift, ruby, php, kotlin
  primary: python
  secondary:
    - typescript

frameworks:
  # Framework support is language-specific and extensible
  backend: fastapi  # or: express, gin, actix, spring-boot, aspnet-core, vapor, rails, laravel, ktor
  frontend: react   # or: vue, angular, svelte, solid

github:
  enabled: true
  create_issues: true
  branch_protection: true

quality:
  coverage_threshold: 90
  mutation_score_threshold: 80
  complexity_threshold: 10

generate:
  ci: true
  precommit: true
  scripts: true
  skills: true
  subagents: true
  claude_md: true
  github_actions: true  # Make AI PR review optional
  metrics: true
  architecture: true
```

---

*Generated by Start Green Stay Green Planning System*
*Last Updated: January 2026*
