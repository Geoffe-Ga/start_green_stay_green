# Common Pitfalls & Troubleshooting

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Tools](tools.md)

---


### 1 No Shortcuts Policy

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

### 2 Forbidden Patterns

See [6.2 Forbidden Patterns](#62-forbidden-patterns) for complete list.

### 3 Most Common Mistakes

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
pre-commit run --all-files
# Only commit if all hooks pass
git add .
git commit -m "feat(generators): add CI generator (#46)"
```

**Why It Happens**: Impatience, assuming "it's a small change"
**Prevention**: Pre-commit hooks run automatically on commit (since Issue #90)

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
# Running tools directly or individually
ruff check .
pytest tests/
mypy start_green_stay_green/
./scripts/lint.sh  # Only runs linting, not tests/coverage
```

**The Fix**:
```bash
# Use pre-commit for comprehensive quality checks
pre-commit run --all-files  # Runs ALL 32 hooks with correct config
```

**Why It Happens**: Muscle memory from other projects, not knowing about pre-commit
**Prevention**: Use `pre-commit run --all-files` as the single quality gate (Issue #90)

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



---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Tools](tools.md)
