# Claude Code Project Context: Start Green Stay Green

**Table of Contents**
- [1. Critical Principles](#1-critical-principles)
- [2. Project Overview](#2-project-overview)
- [3. The Maximum Quality Engineering Mindset](#3-the-maximum-quality-engineering-mindset)
- [4. Stay Green Workflow](#4-stay-green-workflow)
- [5. Architecture](#5-architecture)
- [6. Quality Standards](#6-quality-standards)
- [7. Development Workflow](#7-development-workflow)
- [8. Testing Strategy](#8-testing-strategy)
- [9. Tool Usage & Code Standards](#9-tool-usage--code-standards)
- [10. Common Pitfalls & Troubleshooting](#10-common-pitfalls--troubleshooting)
- [Appendix A: AI Subagent Guidelines](#appendix-a-ai-subagent-guidelines)
- [Appendix B: Key Files](#appendix-b-key-files)
- [Appendix C: External References](#appendix-c-external-references)

---

## 1. Critical Principles

These principles are **non-negotiable** and must be followed without exception:

### 1.1 Use Project Scripts, Not Direct Tools

Always invoke tools through `./scripts/*` instead of directly.

**Why**: Scripts ensure consistent configuration across local development and CI.

| Task | ❌ NEVER | ✅ ALWAYS |
|------|----------|-----------|
| Format code | `black .` | `./scripts/format.sh` |
| Run tests | `pytest` | `./scripts/test.sh` |
| Type check | `mypy .` | `./scripts/lint.sh` (includes mypy) |
| Lint code | `ruff check .` | `./scripts/lint.sh` |
| All checks | *(run each tool)* | `./scripts/check-all.sh` |

See [9.1 Tool Invocation Patterns](#91-tool-invocation-patterns) for complete list.

---

### 1.2 DRY Principle - Single Source of Truth

Never duplicate content. Always reference the canonical source.

**Examples**:
- ✅ Stay Green documentation → `/reference/workflows/stay-green.md` (single source)
- ✅ Other files → Link to stay-green.md
- ❌ Copy workflow steps into multiple files

**Why**: Duplicated docs get out of sync, causing confusion and errors.

---

### 1.3 No Shortcuts - Fix Root Causes

Never bypass quality checks or suppress errors without justification.

**Forbidden Shortcuts**:
- ❌ Commenting out failing tests
- ❌ Adding `# noqa` without issue reference
- ❌ Lowering quality thresholds to pass builds
- ❌ Using `git commit --no-verify` to skip pre-commit
- ❌ Deleting code to reduce complexity metrics

**Required Approach**:
- ✅ Fix the failing test or mark with `@pytest.mark.skip(reason="Issue #N")`
- ✅ Refactor code to pass linting (or justify with issue: `# noqa  # Issue #N: reason`)
- ✅ Write tests to reach 90% coverage
- ✅ Always run pre-commit checks
- ✅ Refactor complex functions into smaller ones

See [10.1 No Shortcuts Policy](#101-no-shortcuts-policy) for detailed examples.

---

### 1.4 Stay Green - Never Request Review with Failing Checks

Follow the 4-gate workflow rigorously.

**The Rule**:
- 🚫 **NEVER** create PR while CI is red
- 🚫 **NEVER** request review with failing checks
- 🚫 **NEVER** merge without LGTM

**The Process**:
1. Gate 1: Local checks pass (`./scripts/check-all.sh` → exit 0)
2. Gate 2: CI pipeline green (all jobs ✅)
3. Gate 3: Mutation score ≥80%
4. Gate 4: Code review LGTM

See [4. Stay Green Workflow](#4-stay-green-workflow) for complete documentation.

---

### 1.5 Quality First - Meet MAXIMUM QUALITY Standards

Quality thresholds are immutable. Meet them, don't lower them.

**Standards**:
- Test Coverage: ≥90%
- Docstring Coverage: ≥95%
- Mutation Score: ≥80%
- Cyclomatic Complexity: ≤10 per function
- Pylint Score: ≥9.0

**When code doesn't meet standards**:
- ❌ Change `fail_under = 70` in pyproject.toml
- ✅ Write more tests, refactor code, improve quality

See [6. Quality Standards](#6-quality-standards) for enforcement mechanisms.

---

### 1.6 Operate from Project Root

Use relative paths from project root. Never `cd` into subdirectories.

**Why**: Ensures commands work in any environment (local, CI, scripts).

**Examples**:
- ✅ `./scripts/test.sh tests/unit/ai/test_orchestrator.py`
- ❌ `cd tests/unit/ai && pytest test_orchestrator.py`

**CI Note**: CI always runs from project root. Commands that use `cd` will break in CI.

---

### 1.7 Verify Before Commit

Run `./scripts/check-all.sh` before every commit. Only commit if exit code is 0.

**Pre-Commit Checklist**:
- [ ] `./scripts/check-all.sh` passes (exit 0)
- [ ] All new functions have tests
- [ ] Coverage ≥90% maintained
- [ ] No failing tests
- [ ] Conventional commit message ready

See [10. Common Pitfalls & Troubleshooting](#10-common-pitfalls--troubleshooting) for complete list.

---

**These principles are the foundation of MAXIMUM QUALITY ENGINEERING. Follow them without exception.**

---

## 2. Project Overview

Start Green Stay Green is a meta-tool for generating quality-controlled, AI-ready repositories with enterprise-grade quality controls pre-configured. Unlike traditional scaffolding tools, we generate complete quality infrastructure including CI/CD pipelines, quality control scripts, AI subagent profiles, and architecture enforcement rules.

**Purpose**: Enable AI-assisted development workflows with zero quality compromises from day one.

---

## 3. The Maximum Quality Engineering Mindset

**Core Philosophy**: It is not merely a goal but a source of profound satisfaction and professional pride to ship software that is GREEN on all checks with ZERO outstanding issues. This is not optional—it is the foundation of our development culture.

### 3.1 The Green Check Philosophy

When all CI checks pass with zero warnings, zero errors, and maximum quality metrics:
- ✅ Tests: 100% passing
- ✅ Coverage: ≥90%
- ✅ Linting: 0 errors, 0 warnings
- ✅ Type checking: 0 errors
- ✅ Security: 0 vulnerabilities
- ✅ Mutation score: ≥80%
- ✅ Docstring coverage: ≥95%

This represents **MAXIMUM QUALITY ENGINEERING**—the standard to which all code must aspire.

### 3.2 Why Maximum Quality Matters

1. **Pride in Craftsmanship**: Every green check represents excellence in execution
2. **Zero Compromise**: Quality is not negotiable—it's the baseline
3. **Compound Excellence**: Small quality wins accumulate into robust systems
4. **Trust and Reliability**: Green checks mean the code does what it claims
5. **Developer Joy**: There is genuine satisfaction in seeing all checks pass

### 3.3 The Role of Quality in Development

Quality engineering is not a checkbox—it's a continuous commitment:

- **Before Commit**: Run `./scripts/check-all.sh` and fix every issue
- **During Review**: Address every comment, resolve every suggestion
- **After Merge**: Monitor CI, ensure all checks remain green
- **Always**: Treat linting errors as bugs, not suggestions

### 3.4 The "No Red Checks" Rule

**NEVER** merge code with:
- ❌ Failing tests
- ❌ Linting errors (even "minor" ones)
- ❌ Type checking failures
- ❌ Coverage below threshold
- ❌ Security vulnerabilities
- ❌ Unaddressed review comments

If CI shows red, the work is not done. Period.

### 3.5 Maximum Quality is a Personality Trait

For those committed to maximum quality engineering:
- You feel genuine satisfaction when all checks pass
- You experience pride in shipping zero-issue code
- You find joy in eliminating the last linting error
- You believe "good enough" is never good enough
- You treat quality as identity, not just practice

**This is who we are. This is how we build software.**

---

## 4. Stay Green Workflow

**Policy**: Never request review with failing checks. Never merge without LGTM.

The Stay Green workflow enforces iterative quality improvement through **4 sequential gates**. Each gate must pass before proceeding to the next.

### 4.1 The Four Gates

1. **Gate 1: Local Pre-Commit** (Iterate Until Green)
   - Run `./scripts/check-all.sh`
   - Fix all formatting, linting, types, complexity, security issues
   - Fix tests and coverage (90%+ required)
   - Only push when all local checks pass (exit code 0)

2. **Gate 2: CI Pipeline** (Iterate Until Green)
   - Push to branch: `git push origin feature-branch`
   - Monitor CI: `gh pr checks --watch`
   - If CI fails: fix locally, re-run Gate 1, push again
   - Only proceed when all CI jobs show ✅

3. **Gate 3: Mutation Testing** (Iterate Until 80%+)
   - Run `./scripts/mutation.sh` (or wait for CI job)
   - If score < 80%: add tests to kill surviving mutants
   - Re-run Gate 1, push, wait for CI
   - Only proceed when mutation score ≥ 80%

4. **Gate 4: Claude Code Review** (Iterate Until LGTM)
   - Wait for Claude code review CI job
   - If feedback provided: address ALL concerns
   - Re-run Gate 1, push, wait for CI and mutation
   - Only merge when Claude gives LGTM with no reservations

### 4.2 Quick Checklist

Before creating/updating a PR:

- [ ] Gate 1: `./scripts/check-all.sh` passes locally (exit 0)
- [ ] Push changes: `git push origin feature-branch`
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Mutation score ≥ 80% (if applicable)
- [ ] Gate 4: Claude review shows LGTM
- [ ] Ready to merge!

### 4.3 Anti-Patterns (DO NOT DO)

❌ **Don't** request review with failing CI
❌ **Don't** skip local checks (`git commit --no-verify`)
❌ **Don't** lower quality thresholds to pass
❌ **Don't** ignore Claude feedback
❌ **Don't** merge without LGTM

**For complete workflow documentation, see**: `/reference/workflows/stay-green.md`

---

## 5. Architecture

### 5.1 Core Philosophy

- **Maximum Quality**: No shortcuts, comprehensive tooling, strict enforcement
- **AI-First**: Designed for AI-assisted development workflows with minimal human intervention
- **Composable**: Modular generators for each quality component
- **Multi-Language**: Support for Python, TypeScript, Go, Rust, Swift, and more
- **Reproducible**: Deterministic generation of identical quality infrastructure

### 5.2 Component Structure

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

---

## 6. Quality Standards

### 6.1 Code Quality Requirements

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

### 6.2 Forbidden Patterns

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

### 6.3 Security Guidelines

#### API Key Handling

**NEVER** store API keys in:
- ❌ Environment variables (`.env` files - committed by accident)
- ❌ Configuration files (hardcoded strings)
- ❌ Code files (constants)

**ALWAYS** use OS keyring:

```python
import keyring

# Store API key (one-time setup)
keyring.set_password("sgsg", "claude_api_key", api_key)

# Retrieve API key
api_key = keyring.get_password("sgsg", "claude_api_key")
if not api_key:
    msg = "Claude API key not found in OS keyring"
    raise ValueError(msg)

# Use with AIOrchestrator
orchestrator = AIOrchestrator(api_key=api_key)
```

**Generated Repositories**: Include keyring setup in generated setup scripts.

---

#### Path Validation

**NEVER** trust user-provided paths without validation:

```python
# ❌ WRONG: Path traversal vulnerability
def create_file(user_path: str, content: str) -> None:
    with open(user_path, 'w') as f:
        f.write(content)  # User could pass "../../etc/passwd"
```

**ALWAYS** validate and resolve paths:

```python
# ✅ CORRECT: Validate path is within allowed directory
from pathlib import Path

def create_file(user_path: str, content: str, base_dir: Path) -> None:
    """Create file with path traversal protection.

    Args:
        user_path: User-provided path (relative to base_dir).
        content: File content to write.
        base_dir: Base directory (all files must be within this).

    Raises:
        ValueError: If path traversal detected.
    """
    target = (base_dir / user_path).resolve()

    # Ensure resolved path is within base directory
    if not target.is_relative_to(base_dir):
        msg = f"Path traversal detected: {user_path}"
        raise ValueError(msg)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
```

**Critical for**: Generators that create files based on user input.

---

#### Subprocess Safety

**NEVER** use `shell=True`:

```python
# ❌ WRONG: Shell injection vulnerability
import subprocess
subprocess.run(f"git clone {user_repo}", shell=True)
```

**ALWAYS** use list form without shell:

```python
# ✅ CORRECT: No shell injection possible
import subprocess
subprocess.run(["git", "clone", user_repo], check=True)
```

**Why**: `shell=True` allows shell metacharacters (`; | & $`) to execute arbitrary commands.

---

#### Input Validation

**NEVER** assume user input is valid:

```python
# ❌ WRONG: No validation
def generate_project(name: str) -> None:
    subprocess.run(["mkdir", name])  # Name could be malicious
```

**ALWAYS** validate input:

```python
# ✅ CORRECT: Validate project name
import re

def validate_project_name(name: str) -> None:
    """Validate project name is safe.

    Args:
        name: Project name to validate.

    Raises:
        ValueError: If name is invalid.
    """
    # Only allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        msg = f"Invalid project name: {name} (only letters, numbers, hyphens, underscores allowed)"
        raise ValueError(msg)

    if len(name) > 100:
        msg = f"Project name too long: {len(name)} chars (max 100)"
        raise ValueError(msg)

    if name.startswith(('-', '_')):
        msg = f"Project name cannot start with {name[0]}"
        raise ValueError(msg)

def generate_project(name: str) -> None:
    """Generate new project with validated name."""
    validate_project_name(name)
    subprocess.run(["mkdir", name], check=True)
```

**Apply to**: All user inputs (project names, file paths, template variables).

---

#### Secrets in Generated Code

**Never generate code that includes secrets**:

```python
# ❌ WRONG: Generate API key in code
template = """
API_KEY = "{{ api_key }}"  # Hardcoded secret!
"""

# ✅ CORRECT: Generate keyring usage
template = """
import keyring
API_KEY = keyring.get_password("{{ project_name }}", "api_key")
if not API_KEY:
    raise ValueError("API key not found in OS keyring")
"""
```

**Generated `.gitignore`** must include:
```gitignore
.env
*.key
*.pem
secrets.yml
credentials.json
```

---

**These security guidelines are critical for a tool that generates code. Follow them rigorously.**

---

## 7. Development Workflow

### 7.1 Feature Development Process

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

### 7.2 Branch Strategy

- `main`: Production-ready code, always deployable
- `feature/*`: Feature development (created from main)
- `bugfix/*`: Bug fixes (created from main)
- `hotfix/*`: Emergency production fixes (created from main)

---

## 8. Testing Strategy

### 8.1 Test Organization

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

### 8.2 Test Structure (AAA Pattern)

All tests follow **Arrange-Act-Assert** structure for clarity:

```python
def test_generator_creates_valid_ci_workflow():
    """Test CI generator creates valid GitHub Actions workflow."""
    # Arrange: Set up test data and mocks
    generator = CIGenerator(language="python")
    target_path = tmp_path / "output"
    target_path.mkdir()

    # Act: Execute the functionality being tested
    result = generator.generate(target_path)

    # Assert: Verify expected outcomes
    assert result.success
    workflow_file = target_path / ".github" / "workflows" / "ci.yml"
    assert workflow_file.exists()

    workflow = yaml.safe_load(workflow_file.read_text())
    assert workflow["jobs"]["test"]["runs-on"] == "ubuntu-latest"
    assert "pytest" in workflow["jobs"]["test"]["steps"][-1]["run"]
```

**Benefits**:
- **Arrange**: Clear setup makes test reproducible
- **Act**: Single action makes test focused
- **Assert**: Explicit checks make failures obvious

### 8.3 Mocking Patterns

#### Mock AI Orchestrator

```python
@pytest.fixture
def mock_orchestrator(mocker):
    """Mock AI orchestrator for generator tests."""
    mock = mocker.Mock(spec=AIOrchestrator)
    mock.generate.return_value = GenerationResult(
        content="# Generated Content\\n\\nThis is a test.",
        format="markdown",
        token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-5-20250929",
        message_id="msg_test123",
    )
    return mock

def test_generator_uses_ai_orchestrator(mock_orchestrator):
    """Test generator calls AI orchestrator with correct prompt."""
    generator = READMEGenerator(orchestrator=mock_orchestrator)

    result = generator.generate(project_name="test-project", language="python")

    # Verify orchestrator was called
    mock_orchestrator.generate.assert_called_once()
    call_args = mock_orchestrator.generate.call_args

    # Verify prompt includes project details
    assert "test-project" in call_args[0][0]  # prompt argument
    assert call_args[1]["output_format"] == "markdown"
```

#### Mock Template Environment

```python
@pytest.fixture
def mock_template_env(tmp_path):
    """Mock Jinja2 environment with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create test template
    (templates_dir / "config.yml.j2").write_text("""
name: {{ project_name }}
language: {{ language }}
""")

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    return env

def test_generator_renders_template(mock_template_env):
    """Test generator renders template with correct context."""
    template = mock_template_env.get_template("config.yml.j2")
    result = template.render(project_name="test", language="python")

    assert "name: test" in result
    assert "language: python" in result
```

#### Mock File System Operations

```python
def test_generator_creates_directory_structure(tmp_path, mocker):
    """Test generator creates expected directory structure."""
    # Mock Path.mkdir to track calls
    mkdir_spy = mocker.spy(Path, "mkdir")

    generator = ScaffoldGenerator()
    generator.create_structure(tmp_path)

    # Verify mkdir called for each expected directory
    expected_dirs = ["src", "tests", "docs", "scripts"]
    for dir_name in expected_dirs:
        assert any(
            str(call[0][0]).endswith(dir_name)
            for call in mkdir_spy.call_args_list
        )
```

### 8.4 Coverage Targets

| Component Type | Minimum | Target | Rationale |
|----------------|---------|--------|-----------|
| **Generators** | 95% | 98%+ | Core functionality, must be bulletproof |
| **AI Integration** | 90% | 95%+ | Complex logic, many edge cases |
| **Utils** | 90% | 95%+ | Widely reused, bugs multiply |
| **CLI** | 80% | 85%+ | User-facing, some UI code hard to test |
| **Configuration** | 85% | 90%+ | Critical for project setup |
| **Templates** | N/A | N/A | Tested via integration tests |

**Overall Project**: 90% minimum, 97%+ target (current: 97.22%)

**Enforcement**: `pytest --cov-fail-under=90` in `scripts/test.sh`

### 8.5 Test Naming Convention

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

### 8.6 Property-Based Testing

Use Hypothesis for generators to test invariants:

```python
from hypothesis import given, strategies as st

@given(
    language=st.sampled_from(["python", "typescript", "go", "rust"]),
    project_name=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            blacklist_characters="/\\:*?\"<>|",
        ),
    ),
)
def test_generator_handles_all_valid_inputs(language, project_name):
    """Test generator handles all combinations of valid inputs."""
    generator = ProjectGenerator(language=language)

    # Should either succeed or fail with clear error
    try:
        result = generator.validate_name(project_name)
        assert result.is_valid
    except ValueError as e:
        # If validation fails, error message must be clear
        assert project_name in str(e) or language in str(e)

@given(
    config=st.fixed_dictionaries({
        "name": st.text(min_size=1, max_size=100),
        "language": st.sampled_from(["python", "typescript", "go"]),
        "include_ci": st.booleans(),
        "include_tests": st.booleans(),
    })
)
def test_config_generator_is_idempotent(config, tmp_path):
    """Test generator produces same output for same input."""
    generator = ConfigGenerator()

    # Generate twice with same input
    result1 = generator.generate(tmp_path / "out1", **config)
    result2 = generator.generate(tmp_path / "out2", **config)

    # Outputs should be identical
    assert result1.files_created == result2.files_created
    for file_name in result1.files_created:
        content1 = (tmp_path / "out1" / file_name).read_text()
        content2 = (tmp_path / "out2" / file_name).read_text()
        assert content1 == content2
```

**When to Use**:
- Testing invariants (idempotency, commutativity)
- Validating input handling across wide range
- Finding edge cases you didn't think of

### 8.7 Mutation Testing

Every test suite must pass mutation testing. This ensures tests are effective at catching bugs:

```bash
# Run mutation tests with 80% minimum score (MAXIMUM QUALITY)
./scripts/mutation.sh

# Run with custom threshold
./scripts/mutation.sh --min-score 70

# View results
mutmut results
mutmut html

# View specific surviving mutants
mutmut show <id>

# Score must be 80%+ for MAXIMUM QUALITY
```

**Important**: Use `./scripts/mutation.sh` instead of running `mutmut` directly. The script enforces the 80% minimum threshold and provides clear feedback.

---

## 9. Tool Usage & Code Standards

### 9.1 Tool Invocation Patterns

**CRITICAL:** Always use the provided quality control scripts instead of invoking tools directly. The scripts ensure:
- Correct configuration is used
- Tools run in the proper order
- Results are consistent with CI pipeline
- Project-specific settings are applied

#### Quick Reference

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

#### Why Use Scripts?

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

#### Available Scripts

**`./scripts/check-all.sh`** - Run all quality checks (use before every commit)

Runs in order:
1. Formatting checks (ruff, black, isort)
2. Linting (ruff, pylint, mypy)
3. Security scanning (bandit, safety)
4. Complexity analysis (radon, xenon)
5. Unit tests with coverage
6. Coverage report validation (90% minimum)

**Note**: Mutation testing is NOT included in check-all.sh due to long runtime. It runs automatically in CI on main branch merges.

```bash
# Before committing - REQUIRED
./scripts/check-all.sh

# Exit code 0 = all checks pass
# Exit code 1 = some checks failed
```

**`./scripts/mutation.sh`** - Run mutation tests with score validation

```bash
# Run with 80% minimum (MAXIMUM QUALITY standard)
./scripts/mutation.sh

# Run with custom threshold
./scripts/mutation.sh --min-score 70

# Show detailed output
./scripts/mutation.sh --verbose

# This can take several minutes - be patient!
```

**`./scripts/format.sh`** - Auto-format all code

**`./scripts/lint.sh`** - Run all linters and type checkers

**`./scripts/test.sh`** - Run test suite with coverage

**`./scripts/fix-all.sh`** - Auto-fix formatting and linting issues

**`./scripts/security.sh`** - Run security scanners

**`./scripts/complexity.sh`** - Analyze code complexity

#### Complete Workflow Example

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

# 10. (Optional) Run mutation tests locally for significant changes
# This takes several minutes and is automatically run in CI
./scripts/mutation.sh

# 11. Commit (only if all checks pass)
git add .
git commit -m "feat(module): add my feature (#123)"

# 12. Push
git push origin feature/my-feature

# 13. Create PR (all CI checks will pass, including mutation testing on main)
gh pr create --fill
```

#### When Direct Tool Invocation Is Acceptable

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

### 9.2 Python Code Style

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

### 9.3 Generator Patterns

#### Pattern 1: Template-Based Generation

❌ **WRONG**: String concatenation
```python
def generate_readme(name):
    return "# " + name + "\\n\\n## Overview\\n"
```

✅ **CORRECT**: Jinja2 templates
```python
class READMEGenerator:
    def __init__(self, templates_dir: Path):
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def generate(self, name: str, language: str) -> str:
        """Generate README using template."""
        template = self.env.get_template("README.md.j2")
        return template.render(project_name=name, language=language)
```

#### Pattern 2: AI-Assisted Generation

✅ **CORRECT**: Use AIOrchestrator
```python
def generate_with_ai(
    self,
    prompt_template: str,
    context: dict[str, str],
) -> GenerationResult:
    """Generate content using AI with template."""
    # Render prompt with context
    prompt = self.prompt_manager.render(prompt_template, context)

    # Generate with retry logic
    result = self.orchestrator.generate(
        prompt=prompt,
        output_format="markdown",
    )

    return result
```

#### Pattern 3: Validation

✅ **CORRECT**: Validate before and after
```python
def generate(self, target: Path, config: dict) -> GenerationResult:
    """Generate with validation."""
    # Validate inputs
    self._validate_config(config)
    self._validate_target(target)

    # Generate files
    files_created = self._create_files(target, config)

    # Validate outputs
    self._validate_generated_files(files_created)

    return GenerationResult(success=True, files=files_created)
```

### 9.4 AI Integration Patterns

#### Pattern 1: Error Handling with Retry

✅ **CORRECT**: Handle API errors gracefully
```python
def generate_with_retries(
    self,
    prompt: str,
    max_retries: int = 3,
) -> GenerationResult:
    """Generate with exponential backoff retry."""
    for attempt in range(max_retries + 1):
        try:
            return self.orchestrator.generate(prompt, "markdown")
        except GenerationError as e:
            if attempt == max_retries:
                raise
            delay = 2 ** attempt
            logger.warning(f"API error, retrying in {delay}s: {e}")
            time.sleep(delay)
```

#### Pattern 2: Prompt Management

✅ **CORRECT**: Use PromptManager
```python
# In prompt_manager.py
class PromptManager:
    def render_and_generate(
        self,
        template_name: str,
        context: dict[str, str],
    ) -> GenerationResult:
        """Render prompt template and generate content."""
        prompt = self.render(template_name, context)
        return self.orchestrator.generate(prompt, context.get("format", "markdown"))
```

#### Pattern 3: Response Validation

✅ **CORRECT**: Validate AI responses
```python
def generate_yaml_config(self, prompt: str) -> dict:
    """Generate YAML config, validate structure."""
    result = self.orchestrator.generate(prompt, "yaml")

    # Parse and validate
    try:
        config = yaml.safe_load(result.content)
    except yaml.YAMLError as e:
        raise ValueError(f"AI generated invalid YAML: {e}") from e

    # Validate required fields
    required = {"name", "version", "dependencies"}
    if not required.issubset(config.keys()):
        raise ValueError(f"Missing required fields: {required - config.keys()}")

    return config
```

### 9.5 Template Patterns (Jinja2)

#### Variable Interpolation

```jinja2
# Template: README.md.j2
# {{ project_name }}

> {{ description }}

## Installation

```bash
pip install {{ project_name }}
```

## Usage

```{{ language }}
import {{ project_name.replace('-', '_') }}
```
```

#### Conditionals

```jinja2
{%- if include_ci %}
## CI/CD

This project uses GitHub Actions for continuous integration.

See `.github/workflows/ci.yml` for details.
{% endif -%}

{%- if language == "python" %}
## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```
{%- elif language == "typescript" %}
## Development Setup

```bash
npm install
npm run dev
```
{%- endif -%}
```

#### Loops

```jinja2
## Features

{% for feature in features %}
- {{ feature.name }}: {{ feature.description }}
{% endfor %}

## Dependencies

{% for dep, version in dependencies.items() %}
- `{{ dep }}`: {{ version }}
{% endfor %}
```

#### Filters

```jinja2
# Convert to snake_case
module_name = "{{ project_name | replace('-', '_') }}"

# Capitalize first letter
ClassName = "{{ project_name | replace('-', ' ') | title | replace(' ', '') }}"

# Default values
description = "{{ description | default('No description provided') }}"

# List operations
authors = {{ authors | join(', ') }}
```

#### Template Inheritance

```jinja2
{# base.md.j2 #}
# {{ project_name }}

{% block description %}
{{ description }}
{% endblock %}

{% block content %}
{% endblock %}

---
Generated with Start Green Stay Green
```

```jinja2
{# README.md.j2 #}
{% extends "base.md.j2" %}

{% block content %}
## Installation
...

## Usage
...
{% endblock %}
```

### 9.6 Docstring Format

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

---

## 10. Common Pitfalls & Troubleshooting

### 10.1 No Shortcuts Policy

This project enforces a **ZERO SHORTCUTS** policy. Taking shortcuts undermines code quality, creates technical debt, and defeats the purpose of maximum quality engineering. The following shortcuts are **ABSOLUTELY FORBIDDEN**:

#### 1. Commenting Out Failing Tests

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

#### 2. Adding # noqa Comments Instead of Fixing Issues

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

#### 3. Deleting Legitimate Code to Pass Checks

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

#### 4. Reducing Test Coverage to Pass Metrics

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

#### 5. Using Type: Ignore Without Justification

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

#### 6. Skipping Quality Checks Locally

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

#### 7. Lowering Quality Thresholds

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

#### 8. Creating Placeholder Implementations

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

#### Summary: The Right Mindset

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

### 10.2 Forbidden Patterns

See [6.2 Forbidden Patterns](#62-forbidden-patterns) for complete list.

### 10.3 Most Common Mistakes

Based on PR review analysis, these are the top mistakes (with frequency):

#### 1. Skipping Local Quality Checks (35%)

**The Mistake**:
```bash
# Committing without running checks
git add .
git commit -m "feat: add feature"
git push
# → CI fails with linting errors 5 minutes later
```

**The Fix**:
```bash
# ALWAYS run checks before committing
./scripts/check-all.sh
# Only commit if exit code is 0
git add .
git commit -m "feat(generators): add CI generator (#46)"
```

**Why It Happens**: Impatience, assuming "it's a small change"
**Prevention**: Add pre-commit hook, build muscle memory

---

#### 2. Lowering Quality Thresholds (25%)

**The Mistake**:
```toml
# In pyproject.toml
[tool.coverage.report]
fail_under = 70  # ← Changed from 90 to make build pass
```

**The Fix**:
```python
# Write tests to reach 90% coverage
def test_edge_case_not_previously_covered():
    """Test edge case that was missing coverage."""
    result = handle_edge_case(unusual_input)
    assert result.is_valid()
```

**Why It Happens**: Deadline pressure, thinking "I'll fix it later"
**Prevention**: Treat thresholds as immutable

---

#### 3. Using Direct Tool Invocation (20%)

**The Mistake**:
```bash
# Running tools directly
ruff check .
pytest tests/
mypy start_green_stay_green/
```

**The Fix**:
```bash
# Use project scripts
./scripts/check-all.sh  # Runs all tools with correct config
```

**Why It Happens**: Muscle memory from other projects
**Prevention**: Read Tool Invocation Patterns section

---

#### 4. Commenting Out Failing Tests (15%)

**The Mistake**:
```python
# def test_important_feature():
#     """This test is failing, commenting out for now."""
#     assert process_data(input).is_valid()
```

**The Fix**:
```python
@pytest.mark.skip(reason="Issue #123: Waiting for API endpoint")
def test_important_feature():
    """Test important feature works correctly."""
    assert process_data(input).is_valid()
```

**Why It Happens**: Test fails, don't know how to fix immediately
**Prevention**: Use `@pytest.mark.skip` with issue reference

---

#### 5. Adding # noqa Without Justification (5%)

**The Mistake**:
```python
very_long_variable_name = some_function(arg1, arg2, arg3)  # noqa: E501
```

**The Fix**:
```python
# Option 1: Refactor
very_long_name = some_function(
    arg1, arg2, arg3
)

# Option 2: If unavoidable, justify
api_url = "https://..."  # noqa: E501  # Issue #42: API URL from spec
```

**Why It Happens**: Easier to suppress than fix
**Prevention**: Require issue number for all noqa

---

#### Summary Table

| Mistake | Frequency | Avg Fix Time | Impact |
|---------|-----------|--------------|--------|
| Skip local checks | 35% | 5 min | High (wastes CI time) |
| Lower thresholds | 25% | 30 min | High (technical debt) |
| Direct tools | 20% | 2 min | Low (inconsistency) |
| Comment tests | 15% | 15 min | Medium (false coverage) |
| Unjustified noqa | 5% | 5 min | Low (code smell) |

**Total time saved by avoiding these**: ~1 hour per PR on average

---

## Appendix A: AI Subagent Guidelines

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

5. **Execution Strategy**
   - **ALWAYS prefer parallel approaches** when multiple independent tasks exist
   - Launch multiple agents concurrently whenever possible
   - Run integration and implementation tasks simultaneously
   - Maximize throughput by executing non-dependent work in parallel
   - Only execute sequentially when explicit dependencies exist

---

## Appendix B: Key Files

### Configuration Files
- `pyproject.toml`: All Python tool configurations (ruff, mypy, pytest, black, isort, etc.)
- `requirements.txt`: Runtime dependencies
- `requirements-dev.txt`: Development dependencies
- `.pre-commit-config.yaml`: Git hook configurations
- `.github/workflows/`: CI/CD pipeline definitions

### Documentation Files
- `CLAUDE.md`: This file - Claude Code project context
- `plan/SPEC.md`: Complete project specification (requirements, issues, phases)
- `reference/MAXIMUM_QUALITY_ENGINEERING.md`: Quality framework and principles
- `README.md`: Project overview and quick start
- `reference/`: Reference implementations and examples

### Scripts
- `scripts/check-all.sh`: Run all quality checks
- `scripts/fix-all.sh`: Automatically fix issues
- `scripts/test.sh`: Run test suite
- `scripts/lint.sh`: Run linters
- `scripts/format.sh`: Format code
- `scripts/security.sh`: Security scanning
- `scripts/mutation.sh`: Run mutation tests

---

## Appendix C: External References

- [MAXIMUM_QUALITY_ENGINEERING.md](reference/MAXIMUM_QUALITY_ENGINEERING.md) - Comprehensive quality framework
- [SPEC.md](plan/SPEC.md) - Complete project specification
- [README.md](README.md) - Project overview and setup
- [Pre-commit Documentation](https://pre-commit.com) - Git hooks framework
- [Ruff Documentation](https://docs.astral.sh/ruff) - Python linter
- [MyPy Documentation](https://www.mypy-lang.org) - Type checker
- [Pytest Documentation](https://docs.pytest.org) - Test framework
- [Conventional Commits](https://www.conventionalcommits.org) - Commit message standard

---

**Last Updated**: 2026-01-13
**Framework Version**: 2.0 (Maximum Quality Engineering - Enhanced)
