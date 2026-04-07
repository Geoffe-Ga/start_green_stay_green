# Root Cause Analysis: Subagents Reference Directory Path Bug

**Issue ID**: #167 (to be created)
**Date**: 2026-02-01
**Severity**: Critical (blocks project generation)
**Status**: Identified

## Problem Statement

`sgsg init` command fails with FileNotFoundError:
```
Error: Generation failed: Reference directory not found: /private/tmp/tmp/python-test-project/.claude/agents
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

**Location**: `start_green_stay_green/cli.py:689-690`

The code incorrectly passes the **TARGET project's** `.claude/agents` directory as the `reference_dir` parameter to `SubagentsGenerator`:

```python
subagents_dir = project_path / ".claude" / "agents"
subagents_generator = SubagentsGenerator(
    orchestrator, reference_dir=subagents_dir  # ❌ WRONG!
)
```

### The Confusion

The code confuses two different directories:

1. **REFERENCE directory** (input): Where to READ template agent files FROM
   - Should be: `REFERENCE_AGENTS_DIR` (the SGSG project's `.claude/agents/`)
   - Contains: Template agent markdown files (chief-architect.md, etc.)

2. **OUTPUT directory** (output): Where to WRITE generated agent files TO
   - Should be: `project_path / ".claude" / "agents"`
   - Will contain: Generated, tuned agent files for the target project

The bug: **Uses OUTPUT directory path as REFERENCE directory path**

## Analysis

### What Happens

1. User runs `sgsg init` to create a new project
2. CLI creates `project_path` for the new project (e.g., `/path/to/python-test-project`)
3. CLI calculates `subagents_dir = project_path / ".claude" / "agents"` (doesn't exist yet!)
4. CLI passes `subagents_dir` as `reference_dir` to `SubagentsGenerator`
5. `SubagentsGenerator.__init__()` calls `_validate_reference_dir()`
6. Validation fails because target project's `.claude/agents/` doesn't exist yet
7. Raises: `FileNotFoundError: Reference directory not found: <target-project>/.claude/agents`

### Why This Is Wrong

The `SubagentsGenerator` is designed to:
1. **READ** template agents from a REFERENCE directory (SGSG's `.claude/agents/`)
2. **TUNE** them for the target project using ContentTuner
3. **WRITE** tuned agents to the OUTPUT directory (target project's `.claude/agents/`)

By passing the target project's path as `reference_dir`, we're telling it to read from a directory that doesn't exist yet.

### Correct Behavior

`SubagentsGenerator` already has a sensible default for `reference_dir`:

```python
# In subagents.py:23
REFERENCE_AGENTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "agents"

# In subagents.py:97
self.reference_dir = reference_dir or REFERENCE_AGENTS_DIR
```

This default points to the SGSG project's own `.claude/agents/` directory, which contains all the template agents.

**Solution**: Don't override `reference_dir` - let it use the default!

## Impact

- **User Impact**: Cannot generate projects - complete blocker
- **Scope**: Affects all project generation when AI features enabled
- **Frequency**: 100% reproduction rate with AI-enabled generation
- **Workaround**: None (generation completely blocked)

## Contributing Factors

1. **Naming confusion**: Variable named `subagents_dir` suggests it's for SubagentsGenerator, but it's actually the OUTPUT directory
2. **Missing abstraction**: No clear separation between "where to read templates" vs "where to write output"
3. **Insufficient testing**: Integration tests didn't catch this (likely used mocks or test fixtures)
4. **Documentation gap**: `reference_dir` parameter purpose not clearly documented in function call

## Fix Strategy

**Option 1: Remove Parameter Override (Recommended)**
- Remove `reference_dir=subagents_dir` argument
- Let `SubagentsGenerator` use its default `REFERENCE_AGENTS_DIR`
- Simplest fix, least risk

**Option 2: Explicit Reference Path**
- Calculate SGSG's reference directory explicitly
- Pass it as `reference_dir` for clarity
- More verbose, same behavior

**Option 3: Separate Output Parameter**
- Add `output_dir` parameter to `SubagentsGenerator`
- Keep `reference_dir` for templates
- Larger refactor, better API design

**Recommended**: **Option 1** - Simple fix that uses existing defaults correctly

## Proposed Solution

### Changes Required

**File**: `start_green_stay_green/cli.py:686-700`

**Before**:
```python
subagents_dir = project_path / ".claude" / "agents"
subagents_generator = SubagentsGenerator(
    orchestrator, reference_dir=subagents_dir  # ❌ Wrong!
)
```

**After**:
```python
# SubagentsGenerator uses REFERENCE_AGENTS_DIR by default
subagents_generator = SubagentsGenerator(orchestrator)  # ✅ Correct!

# OUTPUT directory is created separately when writing files
subagents_output_dir = project_path / ".claude" / "agents"
```

### Test Strategy (TDD)

1. **Unit test**: SubagentsGenerator uses default reference_dir when not provided
2. **Unit test**: Validation passes when using default REFERENCE_AGENTS_DIR
3. **Integration test**: End-to-end subagent generation succeeds
4. **Integration test**: Generated files written to correct output directory
5. **Regression test**: Ensure existing functionality still works

## Prevention

1. **Clear naming**: Rename variables to distinguish input vs output directories
2. **Better defaults**: Make `reference_dir` truly optional with clear default
3. **Integration tests**: Test actual generation flow, not just mocked units
4. **Documentation**: Document parameter purposes clearly in code

## Timeline

- **Discovery**: 2026-02-01 (user manual testing, immediately after fixing #165)
- **RCA Completed**: 2026-02-01
- **Fix Target**: 2026-02-01 (same day - critical blocker)

## Related Files

- `start_green_stay_green/cli.py` - Incorrect reference_dir usage
- `start_green_stay_green/generators/subagents.py` - Validation logic
- `tests/unit/generators/test_subagents.py` - Unit tests
- `tests/integration/generators/test_subagents_integration.py` - Integration tests

## Notes

The fix for this issue should also verify that the generated agent files are actually written to the correct output directory (`project_path / ".claude" / "agents"`).

## Conclusion

Classic parameter confusion bug: passing OUTPUT directory as REFERENCE directory parameter. The fix is simple - remove the incorrect parameter override and let the default work correctly. Use TDD to ensure the fix works and add regression protection.
