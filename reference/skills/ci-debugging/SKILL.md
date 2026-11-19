---
name: ci-debugging
description: >-
  Debug CI test failures on pull requests with structured protocol.
  Use when CI fails on your PR, tests pass locally but fail in CI,
  or you're tempted to say "pre-existing issue". Covers state comparison,
  error reading, local reproduction, and common root causes.
  Do NOT use for local-only test failures or feature development.
metadata:
  author: Geoff
  version: 1.1.0
---

# CI Debugging

If tests passed before and fail now, YOUR changes broke something. Debug properly.

## Instructions

### Step 1: Compare States (2 minutes)

```bash
# What did the last passing PR have?
gh pr view <last-passing-pr> --json checks

# What does my PR have?
gh pr checks <my-pr>

# What changed between them?
git diff <last-passing-commit> HEAD
```

Ask: Did I modify config files? Add dependencies? Change imports or module structure?

**Prove "pre-existing" before you claim it.** If `main` doesn't run the full CI on every merge (nightly-only, or path-filtered jobs that skip unchanged areas), two earlier PRs that broke only in combination can first fail in your PR's CI. Don't assume it; prove it: run the failing check on a clean checkout of `origin/main`, or read `main`'s most recent full run (e.g. `gh run list --workflow <ci-workflow>.yml --branch main --limit 1`, adding `--event schedule` for a nightly). Only a failure reproduced on `main` itself is pre-existing.

### Step 2: Read the Actual Error (5 minutes)

```bash
gh run view --job=<failing-job-id> --log | grep -A 50 "ERROR\|FAILED\|AssertionError"
```

Look for: path issues, configuration errors, dependency problems, file artifacts.

### Step 3: Reproduce Locally (5 minutes)

```bash
pytest tests/ --strict-markers --strict-config -v
pytest --cov=<package> --cov-report=term --cov-fail-under=90
pytest <failing-test-file>::<failing-test> -vv
```

If it passes locally but fails in CI, check environment differences, test artifacts, coverage configuration, and absolute paths.

### Step 4: Inspect Your Changes (10 minutes)

```bash
# Config changes
git diff HEAD~1 pyproject.toml
git diff HEAD~1 .github/workflows/

# Test artifacts
find . -name "*project*" -o -name "MagicMock" -o -name "tmp*"

# Import validation
python -c "from my_package import main; print('OK')"
```

### Step 5: Fix and Verify

Make a targeted fix, verify locally, push, confirm CI passes.

## Examples

### Example 1: Coverage Failure

**Symptom**: "Required test coverage of 90% not reached. Total coverage: 57.14%"

**Root Cause**: Test-generated files being measured by coverage.

**Debug**:
```bash
pytest --cov=. --cov-report=term | grep -v "my_package"
# Shows: my_project/main.py  50.00%  ← shouldn't be measured
```

**Fix**: Add both glob patterns to coverage omit:
```toml
[tool.coverage.run]
omit = [
    "*/artifact/*",  # Nested paths
    "artifact/*",    # Root paths
]
```

### Example 2: Marker Error

**Symptom**: "'e2e' not found in `markers` configuration option"

**Root Cause**: Added `@pytest.mark.e2e` but didn't register marker.

**Fix**:
```toml
[tool.pytest.ini_options]
markers = [
    "e2e: marks tests as end-to-end tests",
]
```

### Example 3: Import Error After Module Rename

**Symptom**: "ModuleNotFoundError: No module named 'old_name'"

**Root Cause**: Renamed module but didn't update all imports.

**Debug**:
```bash
git diff HEAD~1 --name-status | grep -E "^R"  # Find renames
grep -r "old_name" src/ tests/                  # Find stale imports
```

## Troubleshooting

### Error: "Passes locally, fails in CI"
- Check for hardcoded paths or environment-specific assumptions
- Ensure test cleanup removes all artifacts (tmp files, directories)
- Verify coverage omit patterns work with both `*/pattern/*` and `pattern/*`
- Check working directory differences between local and CI

### Error: "Flaky test - sometimes passes, sometimes fails"
- Look for test order dependencies (use `pytest-randomly`)
- Check for shared state between tests (global variables, class-level state)
- Look for timing-sensitive code (use mocked time)
- Check for file system race conditions in parallel test runs

### Error: Spending more than 30 minutes debugging
- Re-read the actual error message carefully
- Check if you modified any config files (pyproject.toml, .github/)
- Compare your branch with the last green commit line by line
- Ask: "What's different between the passing state and my state?"
