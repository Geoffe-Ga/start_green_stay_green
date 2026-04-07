# Root Cause Analysis: Spinners Never Show Checkmarks

**Issue ID**: #171 (to be created)
**Date**: 2026-02-01
**Severity**: Low (cosmetic, but poor UX)
**Status**: Identified

## Problem Statement

Progress spinners during `sgsg init` never resolve to checkmarks (✓). They just keep spinning even after tasks complete successfully.

## Reproduction

```bash
sgsg init \
  --project-name python-test-project \
  --language python \
  --output-dir . \
  --no-interactive
```

**Observed**:
```
✓ AI features enabled (from environment variable)
⠇ Generating scripts...
⠇ Generating pre-commit config...
⠇ Generating skills...
⠇ Generating CI pipeline...
⠇ Generating GitHub Actions review...
⠇ Generating CLAUDE.md...
⠇ Generating architecture rules...
⠇ Generating subagents...
```

All spinners continue spinning, never show ✓ checkmark.

**Expected**:
```
✓ AI features enabled
✓ Generating scripts...
✓ Generating pre-commit config...
✓ Generating skills...
✓ Generating CI pipeline...
✓ Generating GitHub Actions review...
✓ Generating CLAUDE.md...
✓ Generating architecture rules...
✓ Generating subagents...
```

## Root Cause

**Location**: Multiple `_generate_*_step()` functions in `start_green_stay_green/cli.py`

**The Bug**: Incorrect Rich Progress API usage

Every generator step follows this pattern:
```python
def _generate_scripts_step(project_path, progress):
    task = progress.add_task("Generating scripts...", total=None)
    # ... do work ...
    progress.update(task, completed=True)  # ❌ WRONG!
```

**The Problem**:

1. **`total=None`** creates an **indeterminate progress task** (spinner)
2. **`progress.update(task, completed=True)`** is **invalid** - `completed` is not a parameter of `Progress.update()`
3. Rich's `Progress.update()` signature:
   ```python
   def update(
       task_id: TaskID,
       *,
       total: float | None = None,
       completed: float | None = None,  # ❌ This is progress amount, NOT boolean!
       advance: float | None = None,
       description: str | None = None,
       visible: bool | None = None,
       refresh: bool = False,
       **fields: Any,
   )
   ```

4. The `completed` parameter expects a **float** (progress amount), not a **boolean**
5. For indeterminate tasks (`total=None`), setting `completed=True` doesn't stop the spinner

**What Actually Happens**:
- `progress.update(task, completed=True)` is silently ignored (True coerced to 1.0)
- Spinner keeps spinning because task is still visible
- No checkmark appears because task never finishes

## Analysis

### How Rich Progress Works

**For Determinate Progress** (with total):
```python
task = progress.add_task("Task", total=100)
progress.update(task, advance=10)  # Updates progress
progress.update(task, completed=100)  # Marks as complete
```

**For Indeterminate Progress** (spinner):
```python
task = progress.add_task("Task", total=None)  # Creates spinner
# ... do work ...
progress.stop_task(task)  # Stops spinner
# OR
progress.remove_task(task)  # Removes task entirely
```

### Correct Approaches

**Option 1: Stop Task (keeps visible, stops spinner)**
```python
progress.stop_task(task)
```

**Option 2: Remove Task (hides entirely)**
```python
progress.remove_task(task)
```

**Option 3: Update Description (change to checkmark)**
```python
progress.update(task, description="[green]✓[/green] Generating scripts...")
progress.stop_task(task)
```

**Option 4: Use Determinate Progress**
```python
task = progress.add_task("Generating scripts...", total=1)
# ... do work ...
progress.update(task, advance=1)  # Completes and shows checkmark
```

## Impact

- **Severity**: Low - Cosmetic issue only
- **UX Impact**: Confusing - looks like tasks are still running
- **Functionality**: No impact - generation still succeeds
- **User Perception**: Tool appears "stuck" or "slow"

## Contributing Factors

1. **Incorrect API understanding**: Assumed `completed=True` would work
2. **No visual feedback testing**: Never ran tool to see spinners
3. **Copy-paste programming**: Same pattern repeated in all functions
4. **Missing Rich documentation review**: Didn't read Progress API docs

## Fix Strategy

**Recommended: Option 3** (Update description to checkmark + stop)

**Reasons**:
- Shows clear completion indicator (✓)
- Keeps tasks visible for user to review
- Matches expected UX from reproduction
- Simple to implement

**Implementation**:
1. Update all `_generate_*_step()` functions
2. Replace `progress.update(task, completed=True)` with:
   ```python
   progress.update(
       task,
       description="[green]✓[/green] Generated scripts"
   )
   progress.stop_task(task)
   ```

## Proposed Solution

### Changes Required

**Pattern to Replace** (11 occurrences):
```python
# OLD (broken):
task = progress.add_task("Generating X...", total=None)
# ... do work ...
progress.update(task, completed=True)

# NEW (working):
task = progress.add_task("Generating X...", total=None)
# ... do work ...
progress.update(
    task,
    description="[green]✓[/green] Generated X"
)
progress.stop_task(task)
```

### Files to Update

**File**: `start_green_stay_green/cli.py`

**Functions to fix**:
1. `_generate_scripts_step()` - Line 557
2. `_generate_precommit_step()` - Line 574
3. `_generate_skills_step()` - Line 582
4. `_generate_ci_step()` - Lines 599, 602
5. `_generate_review_step()` - Lines 617, 620
6. `_generate_claude_md_step()` - Lines 649, 652
7. `_generate_architecture_step()` - Lines 670, 675
8. `_generate_subagents_step()` - Lines 704, 707
9. `_generate_metrics_dashboard_step()` - Line 805

**Total**: 13 lines to fix

### Test Strategy

**Manual Test**:
```bash
sgsg init --project-name test --language python --output-dir /tmp --no-interactive
```

**Expected Output**:
```
✓ AI features enabled
✓ Generated scripts
✓ Generated pre-commit config
✓ Generated skills
✓ Generated CI pipeline
✓ Generated GitHub Actions review
✓ Generated CLAUDE.md
✓ Generated architecture rules
✓ Generated subagents
✓ Project generated successfully
```

**Unit Test** (optional):
```python
def test_progress_tasks_show_checkmarks(capsys):
    """Test that progress tasks show checkmarks on completion."""
    # Mock Progress and verify update calls
    # Check that description contains "✓"
    # Check that stop_task is called
```

## Prevention

1. **Read API documentation**: Always check library docs before use
2. **Visual testing**: Run CLI commands to verify UX
3. **Type checking**: Use type hints to catch wrong parameter types
4. **Code review**: Review visual/UX aspects, not just functionality

## Timeline

- **Discovery**: 2026-02-01 (user manual testing)
- **RCA Completed**: 2026-02-01
- **Fix Target**: Quick win - same day

## Related Files

- `start_green_stay_green/cli.py` - All `_generate_*_step()` functions

## Conclusion

Simple API misuse - passing boolean to float parameter. Easy fix with immediate visible improvement to UX. Quick win before tackling larger Issue #170.
