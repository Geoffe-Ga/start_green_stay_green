# Root Cause Analysis: CI Workflow Generation Failure

**Issue ID**: #165 (to be created)
**Date**: 2026-02-01
**Severity**: High (blocks project generation)
**Status**: Identified

## Problem Statement

`sgsg init` command fails with validation error:
```
Error: Generation failed: Workflow validation failed: Workflow missing required jobs: {'quality'}
```

## Reproduction Steps

```bash
sgsg init \
  --project-name python-test-project \
  --language python \
  --output-dir . \
  --no-interactive
```

## Root Cause

**Location**: `start_green_stay_green/generators/ci.py:314-328`

The `_validate_required_jobs()` method requires both "quality" and "test" jobs:

```python
def _validate_required_jobs(self, parsed: dict[str, Any]) -> None:
    required_jobs = {"quality", "test"}
    actual_jobs = set(parsed["jobs"].keys())
    missing_jobs = required_jobs - actual_jobs
    if missing_jobs:
        msg = f"Workflow missing required jobs: {missing_jobs}"
        raise ValueError(msg)
```

However, the **reference CI workflow** (`reference/ci/python.yml`) uses a different job structure:
- `quality` job (lines 14-85) - includes linting, security, tests, and coverage
- `complexity` job (lines 86-107) - complexity analysis
- `build` job (lines 109-134) - package build verification

The reference workflow runs tests **within** the quality job (lines 66-68), not as a separate job.

## Analysis

**Mismatch Between Validation and Reference Implementation**:

1. **Validation expects**: `{"quality", "test"}`
2. **Reference provides**: `{"quality", "complexity", "build"}`
3. **AI likely generates**: Workflows following reference pattern (no separate "test" job)

The validation logic is **overly prescriptive** and doesn't match the actual best practices demonstrated in the reference implementations.

## Impact

- **User Impact**: Cannot generate projects - complete blocker
- **Scope**: Affects all language workflows generated via AI
- **Frequency**: 100% reproduction rate when using AI-enabled generation

## Contributing Factors

1. **Validation rigidity**: Hard-coded job names don't allow for workflow variations
2. **Reference divergence**: Reference workflows evolved but validation didn't
3. **Missing fallback**: No graceful degradation or template fallback
4. **Insufficient testing**: Integration tests didn't catch validation/reference mismatch

## Fix Strategy

**Option 1: Relax Validation (Recommended)**
- Require only "quality" job (most critical)
- Make "test" job optional or check if tests run in quality job
- Allow flexibility in job naming patterns

**Option 2: Update Reference Workflows**
- Add explicit "test" job to all reference workflows
- Separate concerns (linting vs testing)
- More complex, affects all language references

**Option 3: Use Reference Workflows as Fallback**
- Skip AI generation, use reference templates directly
- Faster, more reliable
- Loses customization benefits

**Recommended**: **Option 1** - Relax validation to accept workflows with quality job that includes tests

## Proposed Solution

### Changes Required

**File**: `start_green_stay_green/generators/ci.py`

1. Update `_validate_required_jobs()` to:
   - Require only "quality" job
   - OR check if quality job has test steps
   - OR accept "test" job as alternative

2. Update prompt to be more explicit about job structure requirements

3. Add integration test with actual AI generation to catch mismatches

### Test Strategy (TDD)

1. **Unit test**: Validation accepts workflow with only quality job
2. **Unit test**: Validation accepts workflow with tests in quality job
3. **Integration test**: End-to-end generation with AI produces valid workflow
4. **Regression test**: Ensure existing valid workflows still pass

## Prevention

1. **Sync validation with references**: Add CI check that reference workflows pass generator validation
2. **Comprehensive integration tests**: Test actual AI generation, not just mocks
3. **Validation documentation**: Document what makes a valid workflow structure
4. **Flexible validation**: Use configurable rules instead of hard-coded requirements

## Timeline

- **Discovery**: 2026-02-01 (user manual testing)
- **RCA Completed**: 2026-02-01
- **Fix Target**: 2026-02-01 (same day - high priority blocker)

## Related Files

- `start_green_stay_green/generators/ci.py` - Validation logic
- `reference/ci/python.yml` - Reference workflow structure
- `tests/unit/generators/test_ci.py` - Existing tests (likely using mocks)

## Conclusion

The validation logic is **out of sync with reference implementations**. The fix is straightforward: relax the validation to match actual workflow patterns. Use TDD approach to ensure fix works and add regression protection.
