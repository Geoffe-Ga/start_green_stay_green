---
name: bug-squashing-methodology
description: >-
  Structured 6-step bug fix process with reproduction, root cause analysis,
  and TDD. Use when fixing bugs, debugging failures, or investigating defects.
  Covers reproduction, RCA documentation, TDD fix cycle, and PR workflow.
  Do NOT use for filing a new bug report as an issue (use flare), general
  feature development (use stay-green), CI environment issues (use
  ci-debugging), giving code reviews (use comprehensive-pr-review),
  addressing review feedback (use address-feedback), or general git
  workflow like branching and PRs (use git-workflow).
metadata:
  author: Geoff
  version: 1.1.0
---

# Bug Squashing Methodology

Systematic process for fixing bugs: Document, Understand, Fix, Verify. Never skip straight to coding.

## Instructions

### Step 1: Reproduce First

Before writing anything down, reproduce the bug with a failing test or a
direct repro command — capture the exact error message, stack trace, and
input. An RCA written from a bug report's prose (not a real reproduction) is
guesswork; the reproduction is what makes every later step trustworthy.

Run the narrowest reproduction you can (a single test, e.g.
`pytest path::test_name -x -v` or `jest file -t "name"`). If no test exists
yet, write one that reproduces the bug before fixing anything. When the
failure is a validation error (e.g. an HTTP 422), capture the full response
body — it names the field at fault. When it involves mocks or fixtures,
check that they override the right dependencies and reset shared state.

### Step 2: Root Cause Analysis (RCA)

Create `RCA_ISSUE_XXX.md` with:
- **Problem Statement**: Error message, reproduction steps
- **Root Cause**: Exact line/logic causing failure
- **Analysis**: Why it happens, what was confused/wrong
- **Impact**: Severity, scope, frequency
- **Contributing Factors**: Why wasn't it caught earlier?
- **Fix Strategy**: Options with recommendation
- **Prevention**: How to avoid similar bugs

### Step 3: File a GitHub Issue (if none exists)

If the bug isn't tracked yet, file it (the flare skill does this end to end
when available). If an issue already exists, add the RCA summary to it.

```bash
gh issue create --title "bug(component): Brief description" \
  --body "Reproduction steps, root cause summary, proposed fix" \
  --label "bug"
```

### Step 4: Branch and Fix with TDD

```bash
git checkout -b fix-component-issue-XXX
```

1. **Red**: Write a test that reproduces the bug (should fail)
2. **Green**: Write minimal code to fix the bug (test passes)
3. **Refactor**: Clean up the fix while keeping tests green

### Step 5: Quality Gates

Run both gates before committing:

```bash
# Gate 1: All tests pass
./scripts/test.sh --all

# Gate 2: All quality checks pass (the stay-green skill's Gate 2;
# use pre-commit run --all-files where the repo has no check-all.sh)
./scripts/check-all.sh
```

### Step 6: Commit and PR

Use conventional commit format: `fix(component): brief description (#XXX)`

Include in commit body:
- Problem description (reference RCA)
- Solution description
- Specific file changes
- Testing confirmation (both gates green)

## Examples

### Example 1: Type Validation Bug

**Problem**: API endpoint crashes when receiving single object instead of list.

**RCA**: `src/services/business_logic.py:45` assumes input is always a list. Missing type validation causes runtime error.

**Fix**:
```python
# Red: Write test reproducing the bug
def test_process_handles_single_object():
    result = process_input({"key": "value"})  # Single object, not list
    assert result == [{"key": "value"}]

# Green: Fix the code
def process_input(data):
    if isinstance(data, dict):
        data = [data]
    return [transform(item) for item in data]
```

### Example 2: Off-by-One Boundary Error

**Problem**: Pagination returns duplicate items on page boundaries.

**RCA**: `offset = page * limit` should be `offset = (page - 1) * limit` since pages are 1-indexed.

**Fix**:
```python
# Red: Test that reproduces duplicate
def test_pagination_no_duplicates():
    page1 = get_items(page=1, limit=10)
    page2 = get_items(page=2, limit=10)
    assert not set(page1) & set(page2)  # No overlap

# Green: Fix offset calculation
def get_items(page: int, limit: int):
    offset = (page - 1) * limit  # Fixed: was page * limit
    return db.query(Item).offset(offset).limit(limit).all()
```

## Troubleshooting

### Error: Can't reproduce the bug locally
- Check environment differences (Python version, OS, dependencies, timezone, locale)
- Add debug logging at the failure point
- Try running with the exact same data/input as the report

### Error: Fix breaks other tests
- Your fix may have changed shared behavior. Check test assumptions.
- Run the full test suite, not just the new test
- Consider if the other tests were relying on buggy behavior
- Look for shared mutable state between tests (module globals, caches, rate limiters, a shared DB)

### Error: RCA seems like overkill for a simple bug
- Spend 10 minutes on RCA even for "obvious" bugs - they're rarely obvious
- The documentation prevents recurrence and builds institutional knowledge
- Skip RCA only for true typos (wrong variable name, missing comma)
