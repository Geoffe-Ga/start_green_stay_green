# Root Cause Analysis: Missing Project Structure Generation

**Issue ID**: #170 (to be created)
**Date**: 2026-02-01
**Severity**: Critical (generated projects are non-functional)
**Status**: Identified

## Problem Statement

`sgsg init` generates infrastructure files (scripts, CI, skills, etc.) but **omits core project structure**, making generated projects non-functional.

### What's Missing

**Current Generation** ✅:
- ✅ `.claude/agents/` - Subagent profiles
- ✅ `.claude/skills/` - Skills
- ✅ `.github/workflows/` - CI workflows (ci.yml, code-review.yml)
- ✅ `.pre-commit-config.yaml` - Pre-commit hooks
- ✅ `CLAUDE.md` - Project context
- ✅ `plans/architecture/` - Architecture enforcement
- ✅ `scripts/` - Quality scripts (check-all.sh, lint.sh, etc.)

**Missing** ❌:
- ❌ Source code directory (`python_test_project/` or `src/`)
- ❌ `__init__.py` files
- ❌ Hello World starter code
- ❌ `tests/` directory
- ❌ Example test file
- ❌ `requirements.txt`
- ❌ `requirements-dev.txt`
- ❌ `pyproject.toml`
- ❌ `README.md`
- ❌ `typecheck.sh` script
- ❌ `coverage.sh` script

## Reproduction

```bash
sgsg init \
  --project-name python-test-project \
  --language python \
  --output-dir . \
  --no-interactive

cd python-test-project
ls  # Only: CLAUDE.md, plans/, scripts/
./scripts/check-all.sh  # Fails: no tests, no source, missing scripts
```

## Root Cause

**Two-Part Problem**:

### Part 1: Incomplete ScriptsGenerator

**Location**: `start_green_stay_green/generators/scripts.py`

The `ScriptsGenerator` generates:
- ✅ check-all.sh
- ✅ format.sh
- ✅ lint.sh
- ✅ test.sh
- ✅ fix-all.sh
- ✅ security.sh
- ✅ complexity.sh
- ✅ mutation.sh
- ✅ analyze_mutations.py

But **check-all.sh references scripts it doesn't generate**:
- ❌ Line 333: `run_check "Type checking" "typecheck.sh"`
- ❌ Line 337: `run_check "Coverage report" "coverage.sh"`

**Additionally**, test.sh has **hardcoded package name**:
- Line 115 in generated test.sh: `--cov=start_green_stay_green` (SGSG's package!)
- Should be: `--cov={{ project_name_snake }}` (user's package)

### Part 2: Missing Project Structure Generators

**Location**: `start_green_stay_green/cli.py:_generate_project_files()`

The project generation function **only generates quality infrastructure**, not the actual project:

```python
def _generate_project_files(...):
    with Progress(...) as progress:
        _generate_scripts_step(...)          # ✅ Generated
        _generate_precommit_step(...)        # ✅ Generated
        _generate_skills_step(...)           # ✅ Generated
        _generate_with_orchestrator(...)     # ✅ CI, CLAUDE.md, etc.

        # ❌ MISSING: _generate_project_structure_step(...)
        # ❌ MISSING: _generate_starter_code_step(...)
        # ❌ MISSING: _generate_dependencies_step(...)
        # ❌ MISSING: _generate_readme_step(...)
```

### Missing Generator Functions

There are **NO generators** for:
1. Project structure (source dir, __init__.py)
2. Starter code (Hello World + test)
3. Dependencies (requirements.txt, pyproject.toml)
4. Documentation (README.md)

And **ScriptsGenerator is incomplete**:
5. Missing typecheck.sh generation
6. Missing coverage.sh generation
7. Wrong template (hardcoded package name in test.sh)

## Analysis

### Why This Happened

**SGSG is a meta-tool** for generating quality-controlled projects, but the implementation is **incomplete**:

1. **Phase 1 Complete**: Quality infrastructure generation
   - Scripts, pre-commit, CI, skills, subagents ✅

2. **Phase 2 Missing**: Actual project generation
   - Source code, tests, dependencies, docs ❌

The tool currently assumes:
- User will manually create source structure
- User will manually write starter code
- User will manually create requirements files

But this defeats the purpose of a **project generator**!

### Contributing Factors

1. **Incremental development**: Quality infrastructure built first, project structure never added
2. **Missing specification**: No clear definition of "complete project"
3. **Insufficient testing**: Integration tests didn't verify generated project works
4. **No end-to-end validation**: Never ran `check-all.sh` on generated project
5. **Focus on quality tools**: Emphasized quality over functionality

## Impact

- **User Impact**: Generated projects are **non-functional** out of the box
- **Scope**: 100% of generated projects
- **Frequency**: Every `sgsg init` call
- **Severity**: **CRITICAL** - Complete blocker for tool's intended purpose
- **User Experience**: Extremely poor - "why doesn't this work?"

## Breakdown of Missing Components

### Analysis of Generated Scripts

**Scripts that ARE generated** (9 total):
- ✅ `check-all.sh` - Orchestrates all quality checks
- ✅ `lint.sh` - Runs ruff (expects source to lint)
- ✅ `format.sh` - Runs black/isort (expects source to format)
- ✅ `test.sh` - Runs pytest (expects `tests/` dir)
- ✅ `security.sh` - Runs bandit
- ✅ `complexity.sh` - Runs radon
- ✅ `mutation.sh` - Runs mutmut
- ✅ `fix-all.sh` - Auto-fixes issues
- ✅ `analyze_mutations.py` - Analyzes mutations

**Scripts called by check-all.sh but MISSING**:
- ❌ `typecheck.sh` (line 91) - Should run mypy
- ❌ `coverage.sh` (line 95) - Should run pytest with coverage

### Bug 1: Missing Scripts
**Files needed**:
- `scripts/typecheck.sh` (runs mypy)
- `scripts/coverage.sh` (runs pytest --cov)

**Impact**: check-all.sh fails because it tries to call non-existent scripts

### Bug 2: Hardcoded Package Name in test.sh
**Location**: `scripts/test.sh` line 115

**Current** (wrong):
```bash
--cov=start_green_stay_green  # SGSG's package name!
```

**Should be** (templated):
```bash
--cov={{ project_name_snake }}  # User's project name
```

**Impact**: Coverage reports analyze wrong package or fail

### Bug 3: Missing Source Code Structure
**Files needed**:
- `python_test_project/__init__.py`
- `python_test_project/main.py` (Hello World)

**Behavior**: Simple "Hello, World!" application
**Dependencies**: None (stdlib only)
**Impact**: lint.sh, format.sh, security.sh have nothing to operate on

### Bug 4: Missing Tests Structure
**Files needed**:
- `tests/__init__.py`
- `tests/test_main.py` (test Hello World)

**Behavior**: Test passes, demonstrates TDD pattern
**Dependencies**: pytest
**Impact**: test.sh fails - "ERROR: file or directory not found: tests/"

### Bug 5: Missing Dependency Files
**Files needed**:
- `requirements.txt` (runtime: none for Hello World)
- `requirements-dev.txt` (dev tools: pytest, ruff, mypy, black, etc.)
- `pyproject.toml` (modern Python config)

**Content**: All tools referenced by scripts (ruff, mypy, black, isort, pytest, bandit, radon, mutmut)
**Impact**: Tools not installed, scripts fail with "command not found"

### Bug 6: Missing Documentation
**Files needed**:
- `README.md` (project description, quickstart)

**Content**: What the project is, how to use it, how to run checks
**Impact**: No user-facing documentation

## Fix Strategy

**Option 1: Template-Based Generation (Recommended)**
- Create template directories for each language
- Copy templates during project generation
- Simple, reliable, fast

**Option 2: Dynamic Generation**
- Generate files programmatically
- More flexible but complex
- Risk of generation errors

**Option 3: Hybrid Approach**
- Templates for structure/boilerplate
- AI-generated customization
- Best of both worlds

**Recommended**: **Option 1** (templates) with **Option 3** (AI customization) for advanced features

## Proposed Solution

### Phase 1: Fix ScriptsGenerator (Quickest Win)

**File**: `start_green_stay_green/generators/scripts.py`

1. **Add missing script methods**:
   - `_python_typecheck_script()` - Generate typecheck.sh (runs mypy)
   - `_python_coverage_script()` - Generate coverage.sh (runs pytest --cov)

2. **Fix test.sh template**:
   - Replace hardcoded `start_green_stay_green` with `{{ project_name_snake }}`
   - Use Jinja2 templating or string replacement

3. **Update _generate_python_scripts()**:
   - Add calls to write typecheck.sh and coverage.sh
   ```python
   scripts["typecheck.sh"] = self._write_script("typecheck.sh", self._python_typecheck_script())
   scripts["coverage.sh"] = self._write_script("coverage.sh", self._python_coverage_script())
   ```

### Phase 2: Core Structure (Critical)

**Add new generators**:
1. `_generate_project_structure_step()` - Create src directory
2. `_generate_starter_code_step()` - Hello World + test
3. `_generate_dependencies_step()` - requirements files
4. `_generate_readme_step()` - Basic README.md

**Template structure**:
```
templates/
├── python/
│   ├── src/
│   │   ├── __init__.py.j2
│   │   └── main.py.j2
│   ├── tests/
│   │   ├── __init__.py.j2
│   │   └── test_main.py.j2
│   ├── requirements.txt.j2
│   ├── requirements-dev.txt.j2
│   ├── pyproject.toml.j2
│   └── README.md.j2
```

### Phase 2: Integration

Update `_generate_project_files()`:
```python
def _generate_project_files(...):
    with Progress(...) as progress:
        # Core structure FIRST (before quality tools)
        _generate_project_structure_step(...)  # NEW
        _generate_dependencies_step(...)       # NEW
        _generate_starter_code_step(...)       # NEW
        _generate_readme_step(...)             # NEW

        # Quality infrastructure
        _generate_scripts_step(...)
        _generate_precommit_step(...)
        _generate_skills_step(...)
        _generate_with_orchestrator(...)
```

### Phase 3: Validation

Add end-to-end test:
```python
def test_generated_project_passes_check_all(tmp_path):
    """Test that generated project passes all quality checks."""
    # Generate project
    result = run_sgsg_init(tmp_path)

    # Install dependencies
    run(["pip", "install", "-r", "requirements-dev.txt"])

    # Run all checks
    result = run(["./scripts/check-all.sh"])
    assert result.returncode == 0  # All checks pass!
```

## Prevention

1. **E2E Testing**: Always test generated projects work end-to-end
2. **Completeness Checklist**: Define what makes a "complete" project
3. **Template Maintenance**: Keep templates in sync with tools
4. **Integration Tests**: Run `check-all.sh` on generated projects in CI
5. **User Testing**: Manual testing before releases

## Timeline

- **Discovery**: 2026-02-01 (user manual testing)
- **RCA Completed**: 2026-02-01
- **Fix Target**: High priority - multi-step implementation

## Related Files

- `start_green_stay_green/cli.py` - Missing generator calls
- `start_green_stay_green/generators/` - Need new generators
- `templates/` - Need template directories (doesn't exist yet)
- `scripts/check-all.sh` - References missing scripts

## Test Strategy

**TDD Approach**:
1. Write test: generated project has source directory
2. Write test: generated project has tests directory
3. Write test: generated project has requirements files
4. Write test: generated project has README
5. Write test: `check-all.sh` passes on generated project
6. Implement generators to make tests pass
7. Verify all gates pass

## Conclusion

This is a **fundamental gap** in the tool's implementation - it generates quality infrastructure but not the actual project. The fix requires:
1. Creating template system
2. Adding new generator functions
3. Integrating generators into main flow
4. Adding E2E validation

This is a larger effort than previous bugs but follows the same methodology: RCA → Issues → TDD → 3-Gate Workflow.
