# Tool Usage & Code Standards

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Testing](testing.md) | [Troubleshooting →](troubleshooting.md)

---

## 1. Tool Invocation Patterns

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
black tests/unit/test_module.py

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

**`./scripts/check-all.sh`** - Run all quality checks (use before every commit)

Runs in order:
1. Formatting checks (ruff, black, isort)
2. Linting (ruff, pylint, mypy)
3. Security scanning (bandit, pip-audit)
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

### Complete Workflow Example

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make code changes
vim src/my_module.py

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

# 13. Create PR (all CI checks will pass, including mutation testing)
gh pr create --fill
```

### When Direct Tool Invocation Is Acceptable

**Only these cases justify direct tool invocation:**

1. **Running a single test file during development:**
   ```bash
   # Acceptable for quick iteration
   pytest tests/unit/test_module.py -v

   # But still run ./scripts/test.sh before committing
   ```

2. **Checking a specific file's types:**
   ```bash
   # Acceptable for quick feedback
   mypy src/module.py

   # But still run ./scripts/lint.sh before committing
   ```

3. **Debugging a specific linting rule:**
   ```bash
   # Acceptable to understand a specific error
   ruff check src/ --select E501

   # But still run ./scripts/lint.sh before committing
   ```

**Golden Rule:** Direct tool invocation is ONLY acceptable during active development for quick feedback. **ALWAYS** run the appropriate script before committing.

## 2. Code Style

{{LANGUAGE_SPECIFIC_STYLE_GUIDE}}

## 3. Docstring Format

All public functions, classes, and modules must have docstrings:

```python
def calculate_total(
    items: list[dict[str, float]],
    *,
    apply_discount: bool = False,
) -> float:
    """Calculate total cost of items.

    Sums the cost of all items in the list, optionally
    applying a discount based on quantity.

    Args:
        items: List of items with 'cost' and 'quantity' keys.
        apply_discount: Whether to apply bulk discount.
            Defaults to False.

    Returns:
        Total cost as float.

    Raises:
        ValueError: If items list is empty.
        KeyError: If required keys missing from item dicts.

    Examples:
        >>> items = [{"cost": 10.0, "quantity": 2}]
        >>> total = calculate_total(items)
        >>> assert total == 20.0

    Note:
        Discount is 10% for orders over 100 items.

    See Also:
        - apply_bulk_discount: Discount calculation logic
    """
```

---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Testing](testing.md) | [Troubleshooting →](troubleshooting.md)
