# Bug Squashing Methodology

**When to use**: Critical bugs blocking functionality, especially those discovered during manual testing or user reports.

## Core Principle

**Document → Understand → Fix → Verify** - Never skip straight to coding. Root cause analysis prevents recurrence and builds institutional knowledge.

## The 5-Step Process

### 1. Root Cause Analysis (RCA)

Create `RCA_ISSUE_XXX.md` with:
- **Problem Statement**: Error message, reproduction steps
- **Root Cause**: Exact line/logic causing failure
- **Analysis**: Why it happens, what was confused/wrong
- **Impact**: Severity, scope, frequency
- **Contributing Factors**: Why wasn't it caught earlier?
- **Fix Strategy**: Options with recommendation
- **Prevention**: How to avoid similar bugs

**Example**:
```markdown
## Root Cause
Location: `generators/ci.py:323`
Code requires both 'quality' and 'test' jobs, but reference
workflows run tests within quality job. AI follows reference
pattern → validation fails.
```

### 2. GitHub Issue

File issue with:
- Clear title: `bug(component): Brief description`
- Reproduction steps
- Root cause summary
- Proposed fix
- Link to RCA document
- Labels: `bug`

**Purpose**: Trackability, team awareness, automatic linking when PR merged

### 3. Branch & Fix

```bash
git checkout -b fix-component-issue-XXX
```

**Fix Guidelines**:
- **TDD when possible**: Write failing test → Fix → Verify
- **Simplest solution**: Remove wrong parameter vs. add complexity
- **Clear naming**: Rename variables that caused confusion
- **Add comments**: Explain why, not what

### 4. The 3-Gate Workflow

**Gate 0 - TDD (Optional but Recommended)**:
```bash
# Write failing test first
pytest tests/path/to/test.py::test_name  # Should FAIL
# Fix the code
pytest tests/path/to/test.py::test_name  # Should PASS
```

**Gate 1 - Local (Pre-Commit)**:
```bash
pre-commit run --all-files  # All 32 hooks must pass
```

**Gate 2 - CI Pipeline**:
- Push and monitor: `gh pr checks <PR#>`
- All jobs must pass (tests, coverage, linting, security)

**Gate 3 - Claude Review**:
- Wait for automated Claude code review
- Must receive LGTM

**Rule**: Never merge until ALL THREE gates are green ✅

## CRITICAL: Gate Failure = Return to Gate 0

**When ANY gate fails, you MUST return to Gate 0 and iterate through ALL gates again.**

### If Gate 1 (Pre-Commit) Fails:
```bash
# DON'T: Just fix and re-run Gate 1
# DO: Return to Gate 0
pytest tests/  # Verify tests still pass
# Fix the issue
pytest tests/  # Verify fix works
pre-commit run --all-files  # Gate 1 again
```

### If Gate 2 (CI) Fails:
```bash
# DON'T: Just fix and push
# DO: Return to Gate 0
git checkout fix-branch

# Gate 0: TDD - Add test for CI failure scenario
pytest tests/path/to/test.py::test_that_exposes_ci_bug  # Should FAIL
# Fix the code
pytest tests/path/to/test.py::test_that_exposes_ci_bug  # Should PASS

# Gate 1: Local verification
pre-commit run --all-files  # Must pass

# Commit and push
git add . && git commit -m "fix: address CI failure" && git push

# Gate 2: Monitor CI again
gh pr checks <PR#>  # Wait for green
```

### If Gate 3 (Claude Review) Requests Changes:
```bash
# DON'T: Just make changes and push
# DO: Return to Gate 0

# Gate 0: TDD for requested changes
# Write/update tests for the changes Claude requested
pytest tests/  # Verify current behavior
# Make the changes Claude requested
pytest tests/  # Verify changes work

# Gate 1: Local verification
pre-commit run --all-files  # Must pass

# Commit and push
git add . && git commit -m "fix: address code review feedback" && git push

# Gate 2: Wait for CI
gh pr checks <PR#>

# Gate 3: Wait for new review
# Claude will re-review automatically
```

### Why This Matters

**Skipping Gate 0 after failures leads to:**
- ❌ Pushing broken fixes that fail at Gate 1
- ❌ Fixing Gate 1 issues that then fail at Gate 2
- ❌ Multiple failed CI runs wasting resources
- ❌ Accumulating technical debt
- ❌ Breaking the "Stay Green" principle

**Returning to Gate 0 ensures:**
- ✅ Tests verify your fix works
- ✅ Local checks pass before pushing
- ✅ CI passes on first try after fix
- ✅ No wasted CI resources
- ✅ Maintains "Stay Green" discipline

### Example: CI Failure Iteration

**Wrong Approach** (what I did):
```bash
# CI fails with coverage issue
vim pyproject.toml  # Fix coverage config
git commit -m "fix coverage" && git push  # Push without testing
# CI fails again with different issue
vim pyproject.toml  # Fix again
git commit -m "fix coverage again" && git push
# CI fails AGAIN...
# 3-4 failed CI runs, wasted time
```

**Right Approach** (Stay Green):
```bash
# CI fails with coverage issue

# Gate 0: Reproduce and test fix locally
pytest tests/e2e/ --cov=start_green_stay_green  # See the problem
vim pyproject.toml  # Fix coverage config
pytest tests/e2e/ --cov=start_green_stay_green  # Verify fix works

# Gate 1: Run all pre-commit hooks
pre-commit run --all-files  # All pass

# Commit and push ONCE
git commit -m "fix(tests): correct coverage exclusion patterns" && git push

# Gate 2: CI passes on first try ✅
```

**Savings**: 3 failed CI runs → 1 successful CI run

### 5. Commit & PR

**Commit Message Format**:
```
fix(component): brief description (#XXX)

## Problem
[What failed and why]

## Solution
[What you changed]

## Changes
- File: specific change
- File: specific change

## Testing
- Gate 1: ✅ All hooks pass
- Gate 2: ⏳ CI running
- Gate 3: ⏳ Review pending

## Impact
- Fixes Issue #XXX
- Scope: what's affected

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**PR Body**: Similar structure, reference RCA document

## What Makes This Effective

1. **RCA prevents recurrence**: Understanding root cause → better prevention
2. **Documentation = knowledge**: Future developers understand "why"
3. **3-gate workflow = quality**: Catches issues before production
4. **GitHub integration**: Auto-closes issues, tracks history
5. **Commit discipline**: Clear history, easy rollback if needed

## Anti-Patterns to Avoid

❌ **Don't**:
- Skip RCA for "obvious" bugs (they're rarely obvious)
- Lower quality thresholds to "fix faster"
- Bypass pre-commit hooks with `--no-verify`
- Merge with failing CI "to fix later"
- Create commits like "fix bug" or "update file"

✅ **Do**:
- Spend 10 minutes on RCA even for simple bugs
- Fix root cause, not symptoms
- Let all gates complete before merge
- Write detailed commit messages
- Reference issues in commits (`#XXX`)

## Time Investment

- **RCA**: 10-15 minutes (saves hours debugging recurrence)
- **Issue filing**: 5 minutes (enables tracking)
- **Fix**: Varies (TDD adds upfront time, saves debugging)
- **Gate verification**: 5-10 minutes (automated)

**Total overhead**: ~20-30 minutes per bug
**Value**: Prevents recurrence, builds knowledge, maintains quality

## Real Examples

See project history:
- **Issue #165**: CI validation bug - RCA found reference/validation mismatch
- **Issue #167**: Path confusion bug - RCA revealed parameter semantic confusion

Both fixed same-day using this methodology with zero recurrence.

## Integration with SGSG

This methodology IS the SGSG workflow applied to bugs:
- **Stay Green**: 3-gate verification ensures main stays green
- **Maximum Quality**: RCA + comprehensive testing
- **No Shortcuts**: Complete all gates before merge

Use for any bug blocking functionality or discovered in production testing.
