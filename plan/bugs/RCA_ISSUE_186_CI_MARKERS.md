# Root Cause Analysis: Issue #186 - CI Integration Tests Fail with Marker Errors

**Date**: 2026-02-03
**Issue**: PR #187 CI failures - pytest cannot find markers during integration test run
**Status**: Under Investigation
**Severity**: Critical - Blocks PR merge

---

## Problem Statement

### Symptoms
CI integration tests fail with marker configuration errors:
```
ERROR tests/e2e/test_audit_e2e.py - Failed: 'e2e' not found in `markers` configuration option
ERROR tests/integration/ai/test_orchestrator_integration.py - Failed: 'integration' not found in `markers` configuration option
ERROR tests/integration/generators/test_precommit_integration.py - Failed: 'integration' not found in `markers` configuration option
ERROR tests/unit/ai/test_orchestrator.py - Failed: 'flaky_in_ci' not found in `markers` configuration option
```

Additionally:
- Coverage reports `my_project/main.py` file (57.14% total coverage vs 90% requirement)
- Unit tests pass successfully before integration tests fail
- Both test runs use same `configfile: pyproject.toml`
- **All tests pass locally** with 95.61% coverage, no marker errors, no `my_project/` in coverage

### Reproduction Steps (CI Only)
1. Push to PR #187
2. CI runs unit tests: `./scripts/test.sh --unit --coverage --ci` → ✅ PASS
3. CI runs integration tests: `./scripts/test.sh --integration --ci` → ❌ FAIL
4. Marker errors occur during test collection
5. `my_project/main.py` appears in coverage report

### Reproduction Steps (Local - Cannot Reproduce)
```bash
./scripts/test.sh --unit --coverage --ci     # PASS - 95.61% coverage
./scripts/test.sh --integration --ci         # PASS - 21 tests
```

**Result**: Tests pass locally, no marker errors, no `my_project/` directory

---

## Root Cause

### Location
**Suspected**: Tests creating `my_project/` directory that interferes with pytest configuration

### Evidence

#### 1. Unit Tests Pass, Integration Tests Fail (Sequential)
```
Unit tests (04:00:52 - 04:01:46): ✅ PASS
  - collected 1236 items / 28 deselected / 1208 selected
  - configfile: pyproject.toml
  - All markers recognized

Integration tests (04:01:46 - 04:01:57): ❌ FAIL
  - collected 1146 items / 4 errors / 1146 deselected / 0 selected
  - configfile: pyproject.toml (same file!)
  - Markers NOT recognized: 'e2e' not found, 'integration' not found, 'flaky_in_ci' not found
```

#### 2. Coverage Shows `my_project/main.py`
```
Name                 Stmts   Miss Branch BrPart   Cover   Missing
-----------------------------------------------------------------
my_project/main.py       4      2      2      1  50.00%   6, 10
-----------------------------------------------------------------
TOTAL                    5      2      2      1  57.14%
```

**This file should NOT exist** - it's excluded in pyproject.toml:
```toml
[tool.coverage.run]
omit = [
    "*/my_project/*",  # Exclude test-generated sample projects (nested)
    "my_project/*",    # Exclude test-generated sample projects (root)
]
```

#### 3. pyproject.toml Markers Are Defined
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "unit: marks tests as unit tests",
    "flaky_in_ci: marks tests that are flaky in CI due to resource cleanup timing (must pass locally)",
]
```

Verified locally:
```bash
$ pytest --markers 2>&1 | grep -E "e2e|integration|flaky_in_ci"
@pytest.mark.integration: marks tests as integration tests
@pytest.mark.e2e: marks tests as end-to-end tests
@pytest.mark.flaky_in_ci: marks tests that are flaky in CI due to resource cleanup timing (must pass locally)
```

#### 4. Tests Use MagicMock Project Name
In `tests/unit/test_cli_mocked.py:184`:
```python
valid_names = [
    "my-project",
    "my_project",  # ← This name
    "MyProject",
    "project123",
]
```

However, this is just a validation test and shouldn't create files.

---

## Analysis

### Why It Happens

**Hypothesis 1: Test Artifact Pollution (Most Likely)**

Some test during the unit test run creates a `my_project/` directory containing a `main.py` file in the CI working directory. This directory might contain its own configuration that interferes with pytest's marker recognition.

**Evidence**:
- `my_project/main.py` appears in coverage report
- Only happens in CI, not locally
- Unit tests pass, then integration tests immediately fail
- Both runs use same pyproject.toml but integration tests can't find markers

**Mechanism**:
1. Unit tests run, one test creates `my_project/` directory
2. Directory persists after unit test run completes
3. Integration test run starts in same working directory
4. pytest discovers `my_project/` directory
5. If `my_project/` contains `pyproject.toml` or `pytest.ini`, it might override project config
6. Markers from project root are no longer visible

**Hypothesis 2: pytest Cache Corruption**

pytest's cache might be corrupted between test runs, causing marker registry to be lost.

**Evidence**:
- `configfile: pyproject.toml` shows pytest reads the file
- But markers aren't recognized
- pyproject.toml uses `-p no:cacheprovider` to disable cache

**Less likely** because cache is disabled.

**Hypothesis 3: Coverage Plugin Interference**

Coverage measurement might interfere with pytest's configuration loading on second run.

**Evidence**:
- Unit tests use `--cov`, integration tests don't
- But coverage shouldn't affect marker registration

**Less likely** - coverage and markers are independent.

### Why Wasn't It Caught Earlier?

1. **Tests pass locally** - Local environment cleans up properly or test ordering differs
2. **conftest.py has cleanup** - But might not catch all cases in CI
3. **New E2E tests** - PR #187 added E2E tests that might create artifacts
4. **Different test runners** - Local uses different Python version (3.13.7 vs CI 3.11.14)

---

## Impact

- **Severity**: Critical
- **Scope**: Blocks PR #187 merge
- **Frequency**: 100% failure rate on CI for this PR
- **Workaround**: None - Cannot merge until fixed

---

## Fix Strategy

### Option 1: Find and Fix Test Creating `my_project/` (Recommended)

**Approach**:
1. Search for tests that use `"my_project"` as project name
2. Check if they properly use `tmp_path` or `tempfile.TemporaryDirectory()`
3. Add explicit cleanup or ensure tests use isolated directories

**Verification**:
```bash
# Run unit tests and check for artifacts
./scripts/test.sh --unit --coverage --ci
ls -la | grep my_project  # Should be empty
```

**Files to Check**:
- `tests/unit/test_cli_mocked.py` - Uses "my_project" in validation
- `tests/unit/generators/test_structure.py` - Creates test_project directories
- `tests/e2e/test_init_command.py` - Runs actual CLI

**Pros**: Fixes root cause
**Cons**: Requires investigation to find which test

### Option 2: Add Explicit Cleanup Between Test Runs

**Approach**:
Modify `.github/workflows/ci.yml` to clean up between unit and integration tests:
```yaml
- name: Run unit tests with coverage
  run: ./scripts/test.sh --unit --coverage --ci

- name: Clean up test artifacts
  run: |
    rm -rf my_project MagicMock *_project
    find . -type d -name "__pycache__" -exec rm -rf {} +

- name: Run integration tests
  run: ./scripts/test.sh --integration --ci
```

**Pros**: Quick fix, explicit
**Cons**: Treats symptom, not root cause

### Option 3: Run Tests in Separate CI Jobs

**Approach**:
Split unit and integration tests into separate jobs with fresh checkouts.

**Pros**: Complete isolation
**Cons**: More CI time, doesn't fix underlying issue

### Option 4: Debug pytest Configuration Discovery

**Approach**:
Add debug output to see what pytest is reading:
```yaml
- name: Debug pytest config before integration tests
  run: |
    pytest --markers
    cat pyproject.toml | grep -A 10 "markers ="
    ls -la

- name: Run integration tests
  run: ./scripts/test.sh --integration --ci
```

**Pros**: Helps understand the issue
**Cons**: Doesn't fix it

---

## Recommended Fix

**Combine Option 1 + Option 2**:

1. **Immediate**: Add cleanup step in CI (Option 2) to unblock PR
2. **Root cause**: Investigate and fix test creating `my_project/` (Option 1)

### Implementation Plan

#### Phase 1: Unblock PR (Quick Fix)
```yaml
# .github/workflows/ci.yml
- name: Run unit tests with coverage
  run: ./scripts/test.sh --unit --coverage --ci

- name: Clean up test artifacts before integration tests
  if: always()
  run: |
    echo "Cleaning up test artifacts..."
    rm -rf my_project MagicMock *_project test-project
    ls -la | grep project || echo "No project directories found"

- name: Run integration tests
  run: ./scripts/test.sh --integration --ci
```

#### Phase 2: Root Cause Fix (Proper Solution)
1. Run unit tests locally with verbose output:
   ```bash
   pytest tests/unit/ -v --tb=short | tee unit_test_output.txt
   ls -la | grep project
   ```
2. Check which test creates `my_project/`
3. Fix test to use proper isolation or cleanup
4. Verify fix with repeated runs:
   ```bash
   for i in {1..5}; do
     ./scripts/test.sh --unit && ./scripts/test.sh --integration || break
   done
   ```

---

## Prevention

### Short Term
- Add CI step to verify no test artifacts remain after test runs
- Improve conftest.py cleanup fixture

### Long Term
- Enforce strict test isolation in pre-commit hook
- Add test that verifies working directory is clean after test run
- Document test artifact patterns in testing guidelines
- Consider using `pytest-cleanslate` plugin

---

## Related Issues

- Issue #112: Test artifacts polluting working directory (addressed in conftest.py)
- PR #187: Integration of generators from Issue #170

---

## Next Steps

1. ✅ Created RCA document
2. ⏳ Implement Phase 1: Add cleanup step to CI workflow
3. ⏳ Push fix and verify CI passes
4. ⏳ Phase 2: Investigate which test creates `my_project/`
5. ⏳ Create follow-up issue for root cause fix
