# Tool Usage & Code Standards

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Testing](testing.md) | [Troubleshooting →](troubleshooting.md)

---


### 9.1 Tool Invocation Patterns

**CRITICAL:** Always use `pre-commit run --all-files` for local development. This is the single comprehensive command that runs ALL quality checks with correct configuration.

**Primary Command (Local Development)**:
```bash
# Run ALL quality checks - formatting, linting, tests, coverage, security, etc.
pre-commit run --all-files
```

The `./scripts/*` files are used by pre-commit hooks and CI pipelines. They can be run individually during development for targeted checks, but **ALWAYS run `pre-commit run --all-files` before committing**.

#### Quick Reference

| Task | ❌ Direct Tool | ⚙️ Individual Script (CI/Advanced) | ✅ Pre-Commit (PRIMARY) |
|------|----------------|----------------------------------|------------------------|
| **Format code** | `black .`, `isort .` | `./scripts/format.sh` | `pre-commit run --all-files` |
| **Lint code** | `ruff check .`, `pylint` | `./scripts/lint.sh` | `pre-commit run --all-files` |
| **Type check** | `mypy src/` | `./scripts/lint.sh` | `pre-commit run --all-files` |
| **Run tests** | `pytest` | `./scripts/test.sh` | `pre-commit run --all-files` |
| **Check coverage** | `pytest --cov` | `./scripts/test.sh` | `pre-commit run --all-files` |
| **Security scan** | `bandit -r src/` | `./scripts/security.sh` | `pre-commit run --all-files` |
| **Fix issues** | `ruff check --fix` | `./scripts/fix-all.sh` | Auto-fixed by pre-commit |
| **All checks** | *(manual tools)* | `./scripts/check-all.sh` | `pre-commit run --all-files` |

#### Why Use Pre-Commit?

**Direct tool invocation bypasses project configuration:**

❌ **BAD - Direct invocation:**
```bash
# Missing project-specific flags
black tests/unit/ai/test_orchestrator.py

# Wrong configuration
ruff check . --fix

# Incomplete - doesn't run tests or coverage
pytest tests/
```

**Issues with direct invocation:**
- May use different settings than CI
- Easy to forget running all checks (tests, linting, coverage, security, etc.)
- Won't generate proper coverage reports
- Results differ from CI pipeline
- Wastes time debugging CI failures locally

✅ **BEST - Use pre-commit (single comprehensive command):**
```bash
# Runs ALL 32 quality hooks in correct order with proper configuration
pre-commit run --all-files
```

**Benefits of using pre-commit:**
- ✅ Single command runs everything (formatting, linting, tests, coverage, security)
- ✅ Same configuration as CI pipeline
- ✅ Proper tool ordering (e.g., black before isort)
- ✅ Comprehensive coverage reporting (90% threshold enforced)
- ✅ Consistent results across developers
- ✅ Catches issues before CI runs
- ✅ Auto-fixes many issues (formatting, trailing whitespace, etc.)
- ✅ Impossible to forget a check - all 32 hooks run automatically

#### Available Scripts (CI/Advanced Usage)

**For local development, use `pre-commit run --all-files` instead of these scripts.**

The scripts below are used by pre-commit hooks and CI pipelines. They can be run individually for targeted checks during development, but running them manually is unnecessary since pre-commit runs them all.

**`./scripts/check-all.sh`** - Run all quality checks (CI usage)

Runs the same checks as pre-commit (minus git hooks):
1. Formatting checks (ruff, black, isort)
2. Linting (ruff, pylint, mypy)
3. Security scanning (bandit, safety)
4. Complexity analysis (radon, xenon)
5. Unit tests with coverage
6. Coverage report validation (90% minimum)

```bash
# Use pre-commit instead for local development
pre-commit run --all-files

# Or run this script directly (advanced usage)
./scripts/check-all.sh
```

**`./scripts/mutation.sh`** - Run mutation tests with score validation

```bash
# Run with 80% minimum (MAXIMUM QUALITY standard)
./scripts/mutation.sh

# This takes several minutes - runs automatically in CI
```

**Other Available Scripts** (used by pre-commit hooks):

- **`./scripts/format.sh`** - Auto-format code (use `pre-commit run --all-files` instead)
- **`./scripts/lint.sh`** - Run linters and type checkers
- **`./scripts/test.sh`** - Run test suite with coverage
- **`./scripts/fix-all.sh`** - Auto-fix formatting and linting issues
- **`./scripts/security.sh`** - Run security scanners
- **`./scripts/complexity.sh`** - Analyze code complexity

**All of these are automatically run by `pre-commit run --all-files`.**

#### Complete Workflow Example

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make code changes
vim start_green_stay_green/my_module.py

# 3. Write tests
vim tests/unit/test_my_module.py

# 4. Run ALL quality checks (formatting, linting, tests, coverage, security, etc.)
pre-commit run --all-files

# 5. If checks fail, fix issues
# - Many issues are auto-fixed (formatting, trailing whitespace, etc.)
# - For others, edit files to fix mypy errors, add tests for coverage, etc.

# 6. Run checks again after fixes
pre-commit run --all-files

# 7. (Optional) Run mutation tests locally for significant changes
# This takes several minutes and is automatically run in CI
./scripts/mutation.sh

# 8. Commit (pre-commit hooks will run automatically)
git add .
git commit -m "feat(module): add my feature (#123)"
# Note: Pre-commit hooks run on commit and will block if checks fail

# 9. Push
git push origin feature/my-feature

# 10. Create PR (all CI checks will pass, including mutation testing on main)
gh pr create --fill
```

**Key Difference from Old Workflow:**
- **Old**: Run `./scripts/format.sh`, then `./scripts/check-all.sh`, then `./scripts/fix-all.sh`, then `./scripts/check-all.sh` again
- **New**: Run `pre-commit run --all-files` once - it does everything in correct order

#### When Direct Tool Invocation Is Acceptable

**Only these cases justify direct tool invocation:**

1. **Running a single test file during development:**
   ```bash
   # Acceptable for quick iteration
   pytest tests/unit/ai/test_orchestrator.py -v

   # But still run pre-commit run --all-files before committing
   ```

2. **Checking a specific file's types:**
   ```bash
   # Acceptable for quick feedback
   mypy start_green_stay_green/ai/orchestrator.py

   # But still run pre-commit run --all-files before committing
   ```

3. **Debugging a specific linting rule:**
   ```bash
   # Acceptable to understand a specific error
   ruff check start_green_stay_green/ai/ --select E501

   # But still run pre-commit run --all-files before committing
   ```

**Golden Rule:** Direct tool invocation is ONLY acceptable during active development for quick feedback. **ALWAYS** run `pre-commit run --all-files` before committing.

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



---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Testing](testing.md) | [Troubleshooting →](troubleshooting.md)
