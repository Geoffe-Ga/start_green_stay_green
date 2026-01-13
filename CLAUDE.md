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
│   │   └── tuner.py             # Response parsing and tuning
│   │
│   ├── config/                  # Configuration management
│   │   ├── settings.py          # Application settings
│   │   └── templates/           # Configuration templates
│   │
│   ├── generators/              # Component generators
│   │   ├── base.py              # Base generator class
│   │   ├── ci.py                # CI/CD pipeline generation
│   │   ├── scripts.py           # Quality script generation
│   │   ├── claude_md.py         # CLAUDE.md generation
│   │   ├── github_actions.py    # GitHub Actions generation
│   │   ├── metrics.py           # Metrics generation
│   │   ├── precommit.py         # Pre-commit hook generation
│   │   ├── skills.py            # Skills generation
│   │   ├── subagents.py         # Subagent profile generation
│   │   └── architecture.py      # Architecture generation
│   │
│   ├── github/                  # GitHub integration
│   │   ├── client.py            # GitHub API client
│   │   ├── actions.py           # GitHub Actions utilities
│   │   └── issues.py            # Issue management
│   │
│   └── utils/                   # Common utilities
│       ├── fs.py                # File system operations
│       └── templates.py         # Template utilities
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

## No Shortcuts Allowed

This project enforces a **ZERO SHORTCUTS** policy. Taking shortcuts undermines code quality, creates technical debt, and defeats the purpose of maximum quality engineering. The following shortcuts are **ABSOLUTELY FORBIDDEN**:

### 1. Commenting Out Failing Tests

❌ **FORBIDDEN - Commenting out tests:**
```python
# def test_critical_feature():
#     """Test critical feature works correctly."""
#     result = process_data(input_data)
#     assert result.is_valid()
```

✅ **REQUIRED - Fix the test or implementation:**
```python
def test_critical_feature():
    """Test critical feature works correctly."""
    # Fixed: process_data now handles edge case properly
    result = process_data(input_data)
    assert result.is_valid()
    assert result.error_count == 0
```

**Why this matters:** Commented-out tests hide broken functionality. If a test fails, either:
- Fix the bug in the implementation
- Fix the incorrect test expectation
- If the feature is genuinely not ready, use `@pytest.mark.skip(reason="Issue #N: description")`

### 2. Adding # noqa Comments Instead of Fixing Issues

❌ **FORBIDDEN - Suppressing legitimate warnings:**
```python
def complex_function(a, b, c, d, e, f, g):  # noqa: PLR0913
    """Too many arguments - suppressed instead of refactored."""
    result = a + b + c + d + e + f + g  # noqa: E501
    return result
```

✅ **REQUIRED - Refactor the code:**
```python
@dataclass
class FunctionParams:
    """Parameters for complex_function."""

    a: int
    b: int
    c: int
    d: int
    e: int
    f: int
    g: int

def complex_function(params: FunctionParams) -> int:
    """Refactored to use parameter object pattern."""
    return sum([
        params.a, params.b, params.c, params.d,
        params.e, params.f, params.g
    ])
```

**Why this matters:** `# noqa` comments hide design problems. They should ONLY be used when:
- The linting rule is genuinely incorrect for this specific case
- There's a documented issue explaining why
- Example: `x = value  # noqa: E501  # Issue #42: API requires exact 120-char string`

### 3. Deleting Legitimate Code to Pass Checks

❌ **FORBIDDEN - Removing code to fix linting:**
```python
# Before: legitimate error handling
def load_config(path: str) -> dict[str, Any]:
    """Load configuration from file."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        # DELETED: Error handling removed to reduce complexity
        return {}
```

✅ **REQUIRED - Refactor while preserving functionality:**
```python
def load_config(path: str) -> dict[str, Any]:
    """Load configuration from file.

    Returns:
        Configuration dictionary, or empty dict if file not found.

    Raises:
        JSONDecodeError: If file contains invalid JSON.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Config file not found: %s, using defaults", path)
        return {}
```

**Why this matters:** Deleting error handling, validation, or logging to reduce complexity is dangerous. Instead:
- Extract helper functions to reduce complexity
- Use design patterns (Strategy, Command, etc.)
- Simplify the logic while maintaining safety

### 4. Reducing Test Coverage to Pass Metrics

❌ **FORBIDDEN - Excluding files from coverage:**
```python
# In pyproject.toml - WRONG approach
[tool.coverage.run]
omit = [
    "*/my_module.py",  # Added because it's hard to test
]
```

✅ **REQUIRED - Write the missing tests:**
```python
# In tests/unit/test_my_module.py
def test_my_module_handles_edge_case():
    """Test my_module handles previously untested edge case."""
    result = my_module.process(edge_case_input)
    assert result.is_valid()

def test_my_module_error_handling():
    """Test my_module raises appropriate errors."""
    with pytest.raises(ValueError, match="Invalid input"):
        my_module.process(invalid_input)
```

**Why this matters:** Coverage metrics exist to ensure code is tested. Excluding files defeats the purpose.

### 5. Using Type: Ignore Without Justification

❌ **FORBIDDEN - Blanket type ignores:**
```python
def process_items(items):  # type: ignore
    """No types because it's too hard."""
    return [x for x in items if x.valid]  # type: ignore
```

✅ **REQUIRED - Add proper types:**
```python
from typing import TypeVar, Protocol

class Validatable(Protocol):
    """Protocol for objects with valid property."""

    @property
    def valid(self) -> bool: ...

T = TypeVar('T', bound=Validatable)

def process_items(items: list[T]) -> list[T]:
    """Filter items to only valid ones."""
    return [x for x in items if x.valid]
```

**Why this matters:** Type hints catch bugs at development time. If types are hard to add, the design may need refactoring.

### 6. Skipping Quality Checks Locally

❌ **FORBIDDEN - Bypassing pre-commit hooks:**
```bash
git commit --no-verify -m "quick fix"
```

❌ **FORBIDDEN - Skipping checks manually:**
```bash
# Don't run check-all.sh, it takes too long
git add . && git commit -m "feat: add feature"
```

✅ **REQUIRED - Run all checks:**
```bash
# Before every commit
./scripts/check-all.sh

# If checks fail, fix the issues
./scripts/fix-all.sh

# Then commit
git commit -m "feat(module): add feature (#123)"
```

**Why this matters:** Quality checks catch issues before they reach CI. Bypassing them wastes CI time and reviewer time.

### 7. Lowering Quality Thresholds

❌ **FORBIDDEN - Reducing standards:**
```toml
# In pyproject.toml - WRONG
[tool.coverage.report]
fail_under = 70  # Reduced from 90 because it's hard

[tool.pylint.main]
fail-under = 7.0  # Reduced from 9.0
```

✅ **REQUIRED - Meet the standards:**
```python
# Write better tests to reach 90% coverage
# Refactor code to improve pylint score
# If truly impossible, create issue to discuss threshold adjustment
```

**Why this matters:** Quality thresholds are set intentionally. If code can't meet them, it needs improvement, not lower standards.

### 8. Creating Placeholder Implementations

❌ **FORBIDDEN - Empty implementations:**
```python
def generate_report(data: dict[str, Any]) -> str:
    """Generate comprehensive report."""
    # TODO: implement this later
    return ""

def validate_input(value: str) -> bool:
    """Validate input meets requirements."""
    return True  # Skip validation for now
```

✅ **REQUIRED - Implement or raise NotImplementedError:**
```python
def generate_report(data: dict[str, Any]) -> str:
    """Generate comprehensive report.

    Raises:
        NotImplementedError: Report generation not yet implemented.
    """
    raise NotImplementedError(
        "Report generation tracked in Issue #456"
    )

def validate_input(value: str) -> bool:
    """Validate input meets requirements."""
    if not value:
        return False
    if len(value) < 3:
        return False
    if not value.isalnum():
        return False
    return True
```

**Why this matters:** Placeholder implementations hide incomplete features and can cause bugs. Either implement the feature properly or make the incompleteness explicit with `NotImplementedError`.

### Summary: The Right Mindset

**When you encounter a quality issue:**

1. ❌ Don't suppress the warning
2. ❌ Don't delete the problematic code
3. ❌ Don't comment out the failing test
4. ❌ Don't lower the quality threshold
5. ✅ **DO** understand why the issue exists
6. ✅ **DO** fix the root cause
7. ✅ **DO** refactor if needed
8. ✅ **DO** ask for help if stuck

**Remember:** The goal is **maximum quality**, not **minimum effort**. Every shortcut taken is technical debt accrued.

## Tool Invocation Patterns

**CRITICAL:** Always use the provided quality control scripts instead of invoking tools directly. The scripts ensure:
- Correct configuration is used
- Tools run in the proper order
- Results are consistent with CI pipeline
- Project-specific settings are applied

### Quick Reference

| Task | ❌ NEVER DO THIS | ✅ ALWAYS DO THIS |
|------|------------------|-------------------|
| **Format code** | `black .`<br>`isort .` | `./scripts/format.sh` |
| **Check formatting** | `black --check .` | `./scripts/check-all.sh` |
| **Lint code** | `ruff check .`<br>`pylint src/` | `./scripts/lint.sh` |
| **Type check** | `mypy src/` | `./scripts/lint.sh` |
| **Run tests** | `pytest` | `./scripts/test.sh` |
| **Run unit tests** | `pytest tests/unit/` | `./scripts/test.sh --unit` |
| **Check coverage** | `pytest --cov` | `./scripts/test.sh` |
| **Security scan** | `bandit -r src/` | `./scripts/security.sh` |
| **Fix issues** | `ruff check --fix .` | `./scripts/fix-all.sh` |
| **All checks** | *(running each tool manually)* | `./scripts/check-all.sh` |

### Why Use Scripts?

**Direct tool invocation bypasses project configuration:**

❌ **BAD - Direct invocation:**
```bash
# Missing project-specific flags
black tests/unit/ai/test_orchestrator.py

# Wrong configuration
ruff check . --fix

# Incomplete coverage reporting
pytest tests/
```

**Issues with direct invocation:**
- May use different settings than CI
- Might skip important checks (e.g., isort after black)
- Won't generate proper coverage reports
- Results differ from CI pipeline
- Wastes time debugging CI failures locally

✅ **GOOD - Use scripts:**
```bash
# Formats with black + isort + ruff, correct config
./scripts/format.sh

# Fixes formatting and linting issues automatically
./scripts/fix-all.sh

# Runs all checks exactly as CI does
./scripts/check-all.sh
```

**Benefits of using scripts:**
- ✅ Same configuration as CI pipeline
- ✅ Proper tool ordering (e.g., black before isort)
- ✅ Comprehensive coverage reporting
- ✅ Consistent results across developers
- ✅ Catches issues before CI runs

### Available Scripts

#### `./scripts/check-all.sh`
**Run all quality checks (use before every commit)**

Runs in order:
1. Formatting checks (ruff, black, isort)
2. Linting (ruff, pylint, mypy)
3. Security scanning (bandit, safety)
4. Complexity analysis (radon, xenon)
5. Unit tests with coverage
6. Coverage report validation (90% minimum)

```bash
# Before committing - REQUIRED
./scripts/check-all.sh

# Exit code 0 = all checks pass
# Exit code 1 = some checks failed
```

#### `./scripts/format.sh`
**Auto-format all code**

Runs:
1. `ruff format` (fast formatter)
2. `black` (code formatter)
3. `isort` (import sorter)

```bash
# Format all code
./scripts/format.sh

# Always run this before check-all.sh
```

#### `./scripts/lint.sh`
**Run all linters and type checkers**

Runs:
1. `ruff check` (fast linter)
2. `pylint` (comprehensive linter)
3. `mypy` (type checker)

```bash
# Check for linting issues
./scripts/lint.sh

# This is included in check-all.sh
```

#### `./scripts/test.sh`
**Run test suite with coverage**

Options:
- `./scripts/test.sh` - Run all tests
- `./scripts/test.sh --unit` - Unit tests only
- `./scripts/test.sh --integration` - Integration tests only
- `./scripts/test.sh --e2e` - End-to-end tests only

```bash
# Run all tests with coverage
./scripts/test.sh

# Run only unit tests (fast)
./scripts/test.sh --unit

# Run specific test file (use pytest directly for this)
pytest tests/unit/ai/test_orchestrator.py -v
```

#### `./scripts/fix-all.sh`
**Auto-fix formatting and linting issues**

Runs:
1. `ruff check --fix` (auto-fixable issues)
2. `black .` (formatting)
3. `isort .` (import sorting)

```bash
# Fix all auto-fixable issues
./scripts/fix-all.sh

# Then run check-all.sh to verify
./scripts/check-all.sh
```

#### `./scripts/security.sh`
**Run security scanners**

Runs:
1. `bandit` (security issue scanner)
2. `safety` (dependency vulnerability checker)

```bash
# Check for security issues
./scripts/security.sh

# This is included in check-all.sh
```

#### `./scripts/complexity.sh`
**Analyze code complexity**

Runs:
1. `radon cc` (cyclomatic complexity)
2. `radon mi` (maintainability index)
3. `xenon` (complexity thresholds)

```bash
# Check code complexity
./scripts/complexity.sh

# This is included in check-all.sh
```

### Complete Workflow Example

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make code changes
vim start_green_stay_green/my_module.py

# 3. Write tests
vim tests/unit/test_my_module.py

# 4. Format code
./scripts/format.sh

# 5. Run all checks
./scripts/check-all.sh

# 6. If checks fail, auto-fix what you can
./scripts/fix-all.sh

# 7. Run checks again
./scripts/check-all.sh

# 8. Manually fix remaining issues if needed
# (edit files to fix mypy errors, add tests for coverage, etc.)

# 9. Final check before commit
./scripts/check-all.sh

# 10. Commit (only if all checks pass)
git add .
git commit -m "feat(module): add my feature (#123)"

# 11. Push
git push origin feature/my-feature

# 12. Create PR (all CI checks will pass)
gh pr create --fill
```

### When Direct Tool Invocation Is Acceptable

**Only these cases justify direct tool invocation:**

1. **Running a single test file during development:**
   ```bash
   # Acceptable for quick iteration
   pytest tests/unit/ai/test_orchestrator.py -v

   # But still run ./scripts/test.sh before committing
   ```

2. **Checking a specific file's types:**
   ```bash
   # Acceptable for quick feedback
   mypy start_green_stay_green/ai/orchestrator.py

   # But still run ./scripts/lint.sh before committing
   ```

3. **Debugging a specific linting rule:**
   ```bash
   # Acceptable to understand a specific error
   ruff check start_green_stay_green/ai/ --select E501

   # But still run ./scripts/lint.sh before committing
   ```

**Golden Rule:** Direct tool invocation is ONLY acceptable during active development for quick feedback. **ALWAYS** run the appropriate script before committing.

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
```

### Fixing Issues

```bash
# Automatically fix most issues
./scripts/fix-all.sh

# Or fix specific aspects
./scripts/fix-all.sh --format       # Fix formatting only
./scripts/fix-all.sh --lint         # Fix lint issues only

# After auto-fixing, verify all checks pass
./scripts/check-all.sh

# Manual fixes required for:
# - MyPy type errors (add type hints, fix type mismatches)
# - Pylint design issues (refactor complex code)
# - Test failures (fix bugs or update tests)
# - Coverage gaps (write missing tests)
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
mutmut run --paths-to-mutate=start_green_stay_green/

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

# 5. Or run everything at once
./scripts/check-all.sh

# 6. Verify commit message format
# feat(module): description (#issue-number)

# 7. Push to feature branch and create PR
git push origin feature/your-feature
# Create PR on GitHub
```

All checks MUST pass before merging to main.

---

**Last Updated**: 2026-01-12
**Framework Version**: 1.0 (Maximum Quality Engineering)
