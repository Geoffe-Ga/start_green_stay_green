# Quality Standards

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Principles](principles.md) | [Workflow →](workflow.md)

---


### 1. Code Quality Requirements

All code must meet these standards before merging to main:

#### Test Coverage
- **Code Coverage**: 90% minimum (branch coverage)
- **Docstring Coverage**: 95% minimum (interrogate)
- **Mutation Score**: 80% minimum recommended for critical infrastructure (periodic, not continuous)
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

### 2. Forbidden Patterns

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

### 3. Security Guidelines

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



---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Principles](principles.md) | [Workflow →](workflow.md)
