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
- **Multi-Language Support**: Python, TypeScript, Go, Rust, and more
- **Architecture Enforcement**: Import-linter (Python) and dependency-cruiser (TypeScript)
- **Complete CI/CD**: GitHub Actions workflows with quality gates
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
include_ci: true
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
- `--language, -l TEXT`: Primary programming language (python, typescript, go, rust)
- `--output-dir, -o PATH`: Output directory for generated project (default: current directory)
- `--dry-run`: Preview what would be generated without creating files
- `--no-interactive`: Run in non-interactive mode (requires all options)
- `--config, --config-file PATH`: Path to configuration file (YAML or TOML)

**Examples:**

```bash
# Interactive mode
start-green-stay-green init

# Non-interactive with all options
start-green-stay-green init -n my-app -l python --no-interactive

# Dry run to preview
start-green-stay-green init -n my-app -l typescript --dry-run

# With config file
start-green-stay-green init --config project-config.yaml
```

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

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines
- **[Architecture](plan/SPEC.md)** - Project specification and design
- **[Quality Standards](plan/MAXIMUM_QUALITY_ENGINEERING.md)** - Quality framework

### Generate Local Documentation

Generate and view API documentation locally:

```bash
# Navigate to a generated project
cd my-project

# Generate and serve documentation
./scripts/docs.sh --serve

# Open http://localhost:8000 in your browser
```

### Online Documentation

- **[ReadTheDocs](https://start-green-stay-green.readthedocs.io)** - Hosted documentation with search
- **[GitHub Pages](https://geoffe-ga.github.io/start_green_stay_green/)** - API reference

## Configuration

### Configuration File Format

Start Green Stay Green supports YAML and TOML configuration files.

**YAML Example:**

```yaml
# project-config.yaml
project_name: my-awesome-project
language: python
output_dir: ~/projects
include_ci: true
include_tests: true
```

**TOML Example:**

```toml
# project-config.toml
project_name = "my-awesome-project"
language = "python"
output_dir = "~/projects"
include_ci = true
include_tests = true
```

### Configuration Priority

Configuration values are resolved in this order (highest to lowest priority):

1. **Command-line arguments**: `--project-name my-app`
2. **Configuration file**: `config.yaml` or `config.toml`
3. **Interactive prompts**: Asked if value not provided

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
include_ci: true
include_tests: true
include_docs: true
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
- **Docstring Coverage**: ≥95% (interrogate)
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
- Security scanning (bandit, safety)
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

### In Progress

- 🚧 Full generator orchestration (Issue #106)
- 🚧 YAML/TOML config file parsing
- 🚧 Claude API integration for code review (Issue #102)

### Planned

- 📋 Additional language support (Go, Rust, Swift)
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
