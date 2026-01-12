# Claude Code Project Context: Start Green Stay Green

## Project Overview

Start Green Stay Green is a meta-tool for generating quality-controlled, AI-ready repositories with enterprise-grade quality controls pre-configured. Unlike traditional scaffolding tools, we generate complete quality infrastructure including CI/CD pipelines, quality control scripts, AI subagent profiles, and architecture enforcement rules.

**Purpose**: Enable AI-assisted development workflows with zero quality compromises from day one.

## Architecture

### Core Philosophy

- **Maximum Quality**: No shortcuts, comprehensive tooling, strict enforcement
- **AI-First**: Designed for AI-assisted development workflows with minimal human intervention
- **Composable**: Modular generators for each quality component
- **Multi-Language**: Support for Python, TypeScript, Go, Rust, Swift, and more
- **Reproducible**: Deterministic generation of identical quality infrastructure

### Component Structure

```
start_green_stay_green/
├── start_green_stay_green/      # Main package
│   ├── ai/                      # AI orchestration and generation
│   │   ├── orchestrator.py      # Central coordination
│   │   ├── prompts/             # Prompt templates
│   │   └── responses.py         # Response parsing
│   │
│   ├── config/                  # Configuration management
│   │   ├── models.py            # Pydantic models for config
│   │   ├── loader.py            # Configuration loading
│   │   └── validators.py        # Config validation
│   │
│   ├── generators/              # Component generators
│   │   ├── base.py              # Base generator class
│   │   ├── ci_generator.py      # CI/CD pipeline generation
│   │   ├── scripts_generator.py # Quality script generation
│   │   ├── config_generator.py  # Tool configuration
│   │   └── subagent_generator.py # Subagent profile generation
│   │
│   ├── github/                  # GitHub integration
│   │   ├── client.py            # GitHub API client
│   │   ├── templates.py         # Issue/PR templates
│   │   └── actions.py           # GitHub Actions utilities
│   │
│   └── utils/                   # Common utilities
│       ├── paths.py             # Path handling
│       ├── file_ops.py          # File operations
│       └── validation.py        # Validation utilities
│
├── templates/                   # Jinja2 templates
│   ├── python/                  # Python project templates
│   ├── typescript/              # TypeScript project templates
│   ├── go/                      # Go project templates
│   └── shared/                  # Shared templates
│
├── reference/                   # Reference implementations
│   ├── MAXIMUM_QUALITY_ENGINEERING.md
│   ├── claude/                  # Claude subagent documentation
│   ├── subagents/               # Subagent profiles
│   └── scripts/                 # Reference scripts
│
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests (fast, isolated)
│   ├── integration/             # Component integration tests
│   ├── e2e/                     # End-to-end scenarios
│   └── fixtures/                # Test data and fixtures
│
└── plan/                        # Project planning
    ├── SPEC.md                  # Complete specification
    └── MAXIMUM_QUALITY_ENGINEERING.md
```

## Development Workflow

### Feature Development Process

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<issue-number>-<description>
   # Example: feature/6-claude-md-configuration
   ```

2. **Implement Changes**
   - Follow the coding standards outlined below
   - Write tests first (TDD approach)
   - Ensure docstrings for all public APIs
   - Update documentation as needed

3. **Run Quality Checks**
   ```bash
   ./scripts/check-all.sh
   ```
   This runs (in order):
   - Formatting checks (ruff format, black)
   - Linting (ruff, pylint, mypy)
   - Security checks (bandit, safety)
   - Tests with coverage
   - Docstring coverage (interrogate)
   - Code quality metrics

4. **Commit with Conventional Commits**
   ```bash
   git add .
   git commit -m "feat(ai): implement orchestrator core (#6)"
   # Or: fix(generators): handle edge case in path resolution (#15)
   # Or: docs: update CLAUDE.md configuration guidelines
   ```

5. **Create Pull Request**
   - Reference the issue number in the PR title
   - Ensure all CI checks pass
   - Request review from CODEOWNERS

6. **Merge to Main**
   - Requires at least one review approval
   - All CI checks must pass
   - Commit history must be linear

### Branch Strategy

- `main`: Production-ready code, always deployable
- `feature/*`: Feature development (created from main)
- `bugfix/*`: Bug fixes (created from main)
- `hotfix/*`: Emergency production fixes (created from main)

## Quality Standards

### Code Quality Requirements

All code must meet these standards before merging to main:

#### Test Coverage
- **Code Coverage**: 90% minimum (branch coverage)
- **Docstring Coverage**: 95% minimum (interrogate)
- **Mutation Score**: 80% minimum (mutmut)
- **Test Types**: Unit, Integration, and E2E coverage required

#### Type Checking
- **MyPy**: Strict mode, no `# type: ignore` without justification
- **Type Hints**: All function parameters and return types required
- **Generic Types**: Use for collections (List, Dict, etc.)

#### Code Complexity
- **Cyclomatic Complexity**: Max 10 per function
- **Maintainability Index**: Minimum 20 (radon)
- **Max Arguments**: 5 per function
- **Max Branches**: 12 per function
- **Max Lines per Function**: 50 lines

#### Linting and Formatting
- **Ruff**: ALL rules enabled (no exceptions unless documented)
- **Black**: Line length 88 characters
- **isort**: Import sorting per configuration
- **Pylint**: Score of 9.0+ required
- **Bandit**: Security scanning with zero exceptions
- **Safety**: Dependency vulnerability checking

#### Documentation Standards
- **Google-style Docstrings**: All public APIs
- **Type Hints in Docstrings**: Args, Returns, Raises sections
- **Code Examples**: For complex functions
- **Architecture Decision Records**: For significant decisions
- **README Sections**: Updated when adding new components

### Forbidden Patterns

The following patterns are NEVER allowed without explicit justification and issue reference:

1. **Type Ignore**
   ```python
   # ❌ FORBIDDEN
   value = some_function()  # type: ignore

   # ✅ ALLOWED (with issue reference)
   value = some_function()  # type: ignore  # Issue #42: Third-party lib returns Any
   ```

2. **NoQA Comments**
   ```python
   # ❌ FORBIDDEN
   x = 1  # noqa: E741

   # ✅ ALLOWED (with issue reference)
   i = 0  # noqa: E741 (Issue #99: Loop convention in legacy code)
   ```

3. **TODO/FIXME Comments**
   ```python
   # ❌ FORBIDDEN
   # TODO: optimize this later
   def process_data():
       pass

   # ✅ ALLOWED (with issue reference)
   # TODO(Issue #123): Optimize query performance in production
   def process_data():
       pass
   ```

4. **Print Statements**
   ```python
   # ❌ FORBIDDEN
   print("Debug info:", value)

   # ✅ ALLOWED
   logger.debug("Processing value: %s", value)
   ```

5. **Bare Except Clauses**
   ```python
   # ❌ FORBIDDEN
   try:
       risky_operation()
   except:
       pass

   # ✅ ALLOWED
   try:
       risky_operation()
   except FileNotFoundError as e:
       logger.error("Config file missing: %s", e)
   except Exception as e:
       logger.critical("Unexpected error: %s", e)
       raise
   ```

6. **Skipped Tests**
   ```python
   # ❌ FORBIDDEN
   @pytest.mark.skip
   def test_important_feature():
       pass

   # ✅ ALLOWED (with issue reference)
   @pytest.mark.skip(reason="Issue #456: Waiting for API endpoint")
   def test_important_feature():
       pass
   ```

## Common Commands

### Quality Checks

```bash
# Run all quality checks (required before commit)
./scripts/check-all.sh

# Run specific checks
./scripts/format.sh                 # Format code (black, isort, ruff)
./scripts/lint.sh                   # Run linters (ruff, pylint, mypy)
./scripts/test.sh                   # Run tests with coverage
./scripts/test.sh --unit            # Run unit tests only
./scripts/test.sh --integration     # Run integration tests only
./scripts/test.sh --e2e             # Run end-to-end tests only
./scripts/security.sh               # Run security scanners (bandit, safety)
./scripts/complexity.sh             # Check code complexity (radon, xenon)
./scripts/docstring.sh              # Check docstring coverage (interrogate)
```

### Fixing Issues

```bash
# Automatically fix most issues
./scripts/fix-all.sh

# Or fix specific aspects
./scripts/fix-all.sh --format       # Fix formatting only
./scripts/fix-all.sh --lint         # Fix lint issues only

# Manual fixes may be required for some issues
ruff check . --fix                  # Let ruff auto-fix what it can
black .                             # Format with black
isort .                             # Sort imports
mypy src/                           # Check types (no auto-fix)
pylint src/                         # Lint (no auto-fix)
```

### Development Workflow

```bash
# Start development
git checkout -b feature/my-feature
make setup                          # Install dev dependencies (if applicable)

# While developing (frequent checks)
./scripts/check-all.sh

# Before committing
./scripts/check-all.sh              # Full validation required
git commit -m "feat(module): description (#123)"

# After push, before PR merge
# - All CI checks must pass
# - At least one approval required
# - Coverage must be 90%+
```

## Testing Requirements

### Test Strategy

Every code change must include tests covering:

1. **Happy Path**
   - Normal operation with valid inputs
   - Expected output/behavior verified

2. **Error Handling**
   - Invalid inputs rejected appropriately
   - Exceptions raised with correct types
   - Error messages are clear

3. **Edge Cases**
   - Boundary conditions tested
   - Empty collections handled
   - None/null values managed
   - Type edge cases covered

4. **Integration**
   - Component interactions verified
   - Dependencies properly mocked
   - State management correct

5. **Property-Based Testing**
   - Use Hypothesis for invariants
   - Test idempotent operations
   - Verify mathematical properties

### Test Organization

```
tests/
├── unit/                           # Fast, isolated tests
│   ├── ai/
│   ├── config/
│   ├── generators/
│   └── utils/
├── integration/                    # Component interaction tests
│   ├── test_generator_integration.py
│   └── test_ai_config_flow.py
├── e2e/                           # End-to-end workflow tests
│   └── test_full_generation_flow.py
└── fixtures/                       # Shared test data
    ├── conftest.py               # Pytest configuration
    └── data/
```

### Test Naming Convention

```python
# Format: test_<unit>_<scenario>_<expected_outcome>

# Examples:
def test_orchestrator_generate_with_valid_prompt_returns_result():
    """Test orchestrator generates content with valid input."""
    pass

def test_config_loader_missing_file_raises_file_not_found():
    """Test loader raises FileNotFoundError for missing config."""
    pass

def test_generator_empty_config_raises_validation_error():
    """Test generator rejects empty configuration."""
    pass
```

### Mutation Testing

Every test suite must pass mutation testing. This ensures tests are effective at catching bugs:

```bash
# Run mutation tests
mutmut run --paths-to-mutate=src/

# View results
mutmut results
mutmut html

# Score must be 80%+
```

## AI Subagent Guidelines

When delegating work to subagents, provide:

1. **Clear Task Description**
   - What needs to be done
   - Why it matters
   - Success criteria

2. **Relevant Context**
   - Reference files and issues
   - Architecture decisions
   - Quality standards that apply

3. **Dependencies**
   - Other work that must complete first
   - Blocked dependencies
   - Integration points

4. **Acceptance Criteria**
   - All quality checks passing
   - Specific thresholds met
   - Testing requirements
   - Documentation requirements

## Key Files

### Configuration Files
- `pyproject.toml`: All Python tool configurations (ruff, mypy, pytest, black, isort, etc.)
- `requirements.txt`: Runtime dependencies
- `requirements-dev.txt`: Development dependencies
- `.pre-commit-config.yaml`: Git hook configurations
- `.github/workflows/`: CI/CD pipeline definitions

### Documentation Files
- `CLAUDE.md`: This file - Claude Code project context
- `plan/SPEC.md`: Complete project specification (requirements, issues, phases)
- `plan/MAXIMUM_QUALITY_ENGINEERING.md`: Quality framework and principles
- `README.md`: Project overview and quick start
- `reference/`: Reference implementations and examples

### Scripts
- `scripts/check-all.sh`: Run all quality checks
- `scripts/fix-all.sh`: Automatically fix issues
- `scripts/test.sh`: Run test suite
- `scripts/lint.sh`: Run linters
- `scripts/format.sh`: Format code
- `scripts/security.sh`: Security scanning

## Important Notes

### Never Skip

These are non-negotiable:

- Type checking (mypy strict mode)
- Security scanning (bandit, safety)
- Test coverage (90% minimum)
- Docstring coverage (95% minimum)
- Conventional commits
- CI checks before merge
- Code review approval
- Linting (ALL ruff rules enabled)

### Always Include

Every code change must include:

- Type hints on all functions (no `Any` unless justified)
- Docstrings on all public APIs (Google style)
- Error handling for external operations
- Tests for all new functionality
- Updates to relevant documentation
- Mutation test verification

### Prefer

When making design choices, prefer:

- Composition over inheritance
- Explicit over implicit
- Standard library over third-party (when reasonable)
- Async/await over callbacks
- Pathlib over os.path
- Dataclasses/Pydantic over dicts
- Type hints over comments
- Small functions over large ones
- Pure functions over side effects
- Tests that verify behavior, not implementation

## Development Standards

### Python Code Style

```python
# Use explicit imports
from pathlib import Path
from typing import Optional

# Type all function signatures
def generate_config(
    project_name: str,
    language: str,
    *,
    include_ci: bool = True,
) -> dict[str, str]:
    """Generate project configuration.

    Args:
        project_name: Name of the project.
        language: Programming language (python, typescript, go, rust).
        include_ci: Whether to include CI configuration.

    Returns:
        Dictionary containing configuration data.

    Raises:
        ValueError: If language is not supported.
    """
    if language not in {"python", "typescript", "go", "rust"}:
        raise ValueError(f"Unsupported language: {language}")

    return {
        "name": project_name,
        "language": language,
        "ci": include_ci,
    }


# Use meaningful variable names (no abbreviations)
def validate_config(config: dict[str, str]) -> None:
    """Validate project configuration."""
    required_fields = {"name", "language"}
    missing_fields = required_fields - config.keys()

    if missing_fields:
        raise ValueError(f"Missing fields: {missing_fields}")
```

### Docstring Format

All public functions, classes, and modules must have docstrings:

```python
def calculate_complexity(
    code_ast: ast.AST,
    *,
    include_nested: bool = False,
) -> float:
    """Calculate cyclomatic complexity for Python AST.

    Analyzes the abstract syntax tree and computes complexity
    based on decision points and branching logic.

    Args:
        code_ast: Abstract syntax tree to analyze.
        include_nested: Whether to include nested function complexity.
            Defaults to False.

    Returns:
        Complexity score as float (typically 1-20+).

    Raises:
        TypeError: If code_ast is not an ast.AST instance.
        ValueError: If AST cannot be analyzed.

    Examples:
        >>> import ast
        >>> code = "def f(x):\\n  if x: return 1\\n  return 0"
        >>> tree = ast.parse(code)
        >>> score = calculate_complexity(tree)
        >>> assert 1 < score < 10

    Note:
        This function requires valid Python AST. Use ast.parse()
        to generate AST from source code.

    See Also:
        - ast.parse: Parse Python source code to AST
        - radon: Reference complexity calculation tool
    """
```

## External References

- [MAXIMUM_QUALITY_ENGINEERING.md](plan/MAXIMUM_QUALITY_ENGINEERING.md) - Comprehensive quality framework
- [SPEC.md](plan/SPEC.md) - Complete project specification
- [README.md](README.md) - Project overview and setup
- [Pre-commit Documentation](https://pre-commit.com) - Git hooks framework
- [Ruff Documentation](https://docs.astral.sh/ruff) - Python linter
- [MyPy Documentation](https://www.mypy-lang.org) - Type checker
- [Pytest Documentation](https://docs.pytest.org) - Test framework
- [Conventional Commits](https://www.conventionalcommits.org) - Commit message standard

## Quality Checklist Before Committing

Run this checklist before every commit:

```bash
# 1. Format code
./scripts/format.sh

# 2. Run linters and type checker
./scripts/lint.sh

# 3. Run all tests with coverage
./scripts/test.sh

# 4. Check security
./scripts/security.sh

# 5. Verify docstring coverage
./scripts/docstring.sh

# 6. Or run everything at once
./scripts/check-all.sh

# 7. Verify commit message format
# feat(module): description (#issue-number)

# 8. Push to feature branch and create PR
git push origin feature/your-feature
# Create PR on GitHub
```

All checks MUST pass before merging to main.

---

**Last Updated**: 2026-01-12
**Framework Version**: 1.0 (Maximum Quality Engineering)
