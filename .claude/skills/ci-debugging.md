# CI Debugging Skill

**Trigger**: When CI tests fail on your PR after passing on previous PRs, or when you're tempted to say "pre-existing issue" or "unrelated to my changes"

## Core Principle

**If tests passed before and fail now, YOUR changes broke something.**

Do not make excuses. Do not blame infrastructure. Do not say "unrelated". Debug properly.

## Anti-Patterns to Avoid

❌ "These are pre-existing infrastructure issues"
❌ "The CI has marker configuration problems"
❌ "This is unrelated to my changes"
❌ "This must be a flaky test"
❌ "The coverage pollution is from something else"
❌ "These failures existed before my PR"

## Debugging Protocol

When CI fails on your PR:

### 1. Compare States (2 minutes)
```bash
# What did the last passing PR have?
gh pr view <last-passing-pr> --json checks

# What does my PR have?
gh pr checks <my-pr>

# What changed between them?
git diff <last-passing-commit> HEAD
```

**Critical Questions:**
- Did I modify config files? (pyproject.toml, .github/, pytest.ini, tox.ini)
- Did I add new dependencies?
- Did I change imports or module structure?
- Did I add new test files or patterns?

### 2. Read the ACTUAL Error (5 minutes)

```bash
# Get the full log
gh run view --job=<failing-job-id> --log | grep -A 50 "ERROR\|FAILED\|AssertionError"
```

**Look for:**
- Path issues (working directory, imports)
- Configuration errors (markers, fixtures, coverage)
- Dependency problems (missing packages, version conflicts)
- File artifacts (temporary files interfering with coverage/tests)

### 3. Reproduce Locally (5 minutes)

```bash
# Match CI environment
pytest tests/ --strict-markers --strict-config -v

# Check coverage like CI does
pytest --cov=<package> --cov-report=term --cov-fail-under=90

# Run the specific failing test
pytest <failing-test-file>::<failing-test> -vv
```

**If it passes locally but fails in CI:**
- Check for environment differences (paths, temp directories)
- Look for test artifacts not cleaned up
- Check coverage configuration (omit patterns)
- Verify no absolute paths in tests

### 4. Inspect Your Changes (10 minutes)

**Config Changes:**
```bash
# What did I change in config?
git diff HEAD~1 pyproject.toml
git diff HEAD~1 .github/workflows/

# Validate syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
```

**Test Artifacts:**
```bash
# What files are tests creating?
find . -name "*project*" -o -name "MagicMock" -o -name "tmp*"

# Are these excluded from coverage?
grep -A 10 "\[tool.coverage.run\]" pyproject.toml
```

**Import/Path Changes:**
```bash
# Did I change module structure?
git diff HEAD~1 --name-status | grep -E "^(R|M|A|D)"

# Are imports still valid?
python -c "import start_green_stay_green; print('OK')"
```

### 5. Common Root Causes

#### Coverage Failures
**Symptom**: "Required test coverage of 90% not reached. Total coverage: 57.14%"

**Root Cause**: Test-generated files being measured by coverage

**Debug**:
```bash
# Check coverage report for unexpected files
pytest --cov=. --cov-report=term | grep -v "start_green_stay_green"

# Pattern issues?
# */my_project/* only matches nested: /foo/my_project/file.py
# my_project/* matches root: my_project/file.py
```

**Fix**: Add both patterns to coverage omit:
```toml
[tool.coverage.run]
omit = [
    "*/artifact/*",  # Nested
    "artifact/*",    # Root
]
```

#### Marker Errors
**Symptom**: "'e2e' not found in `markers` configuration option"

**Root Cause**:
- Added test with `@pytest.mark.e2e` decorator
- But didn't register marker in pyproject.toml
- Or marker registration has typo

**Debug**:
```bash
# What markers do I use?
grep -r "@pytest.mark" tests/

# Are they all registered?
grep -A 10 "markers =" pyproject.toml
```

**Fix**: Register ALL markers:
```toml
[tool.pytest.ini_options]
markers = [
    "e2e: marks tests as end-to-end tests",
    "integration: marks tests as integration tests",
]
```

#### Import Errors
**Symptom**: "ModuleNotFoundError" or "ImportError"

**Root Cause**:
- Changed package structure
- Added new files not in `__init__.py`
- Circular imports

**Debug**:
```bash
# Can package be imported?
python -c "from my_package.new_module import NewClass"

# Check for circular imports
python -c "import my_package; print(dir(my_package))"
```

#### Path Errors
**Symptom**: "FileNotFoundError" or relative path issues

**Root Cause**:
- Tests use relative paths that work locally but not in CI
- Working directory different in CI
- Test artifacts in unexpected locations

**Debug**:
```bash
# What's the working directory?
pytest tests/test_file.py::test_name -vv -s

# Add debug output to test
import os; print(f"CWD: {os.getcwd()}")
```

## MAX QUALITY = MAX OWNERSHIP

**When your PR breaks CI:**
1. ✅ It's your problem
2. ✅ It's your code
3. ✅ It's your responsibility to debug
4. ❌ Don't blame infrastructure
5. ❌ Don't blame "pre-existing issues"
6. ❌ Don't make excuses

**Stay Green = Never merge failing tests**

Even if you think the failure is unrelated, investigate until you can PROVE it's not your change. 95% of the time, it is.

## Example: Coverage Exclusion Bug

**Symptom**: CI fails with 57% coverage showing `my_project/main.py`

**Wrong Response**:
> "This is a pre-existing issue with test artifacts. The CI configuration has problems with coverage measurement that aren't related to my PR."

**Right Response**:
```bash
# 1. Compare states
git show HEAD~1:pyproject.toml | grep -A 5 "omit ="
# Shows: Previous version didn't have these patterns

# 2. Read actual error
# Coverage report shows: my_project/main.py  50.00%
# This file shouldn't be measured!

# 3. Check my changes
git diff HEAD~1 pyproject.toml
# I added: "*/my_project/*"

# 4. Test locally
mkdir my_project && echo "x = 1" > my_project/main.py
pytest --cov=. --cov-report=term
# my_project/main.py shows up! Pattern doesn't work!

# 5. Fix it
# */my_project/* only matches /foo/my_project/file.py
# Need: my_project/* to match root-level my_project/file.py
```

**Fixed in**: Added both `*/my_project/*` AND `my_project/*` to omit list.

## Time Budget

**Total debugging time**: 20-30 minutes

- 2 min: Compare states (what changed?)
- 5 min: Read actual error (what failed?)
- 5 min: Reproduce locally (can I see it?)
- 10 min: Inspect changes (what did I modify?)
- 5 min: Fix and verify

If you spend more than 30 minutes, you're either:
1. Making excuses instead of debugging
2. Not reading the error carefully
3. Missing obvious config changes

## Success Criteria

✅ Identified specific line/config that broke CI
✅ Explained WHY it broke (mechanism)
✅ Fixed it with targeted change
✅ Verified fix locally before pushing
✅ CI passes after fix

## Remember

**The best engineers own their mistakes and debug them quickly.**

**The worst engineers blame "infrastructure" and merge broken code.**

**Which one are you?**
