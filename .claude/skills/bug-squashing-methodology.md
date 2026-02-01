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
