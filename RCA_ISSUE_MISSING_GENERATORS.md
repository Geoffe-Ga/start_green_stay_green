# Root Cause Analysis: New Generators Not Integrated into CLI

**Issue ID**: TBD (to be created)
**Date**: 2026-02-02
**Severity**: High (functionality broken - missing files)
**Status**: Identified

## Problem Statement

Generated projects are missing critical files that were implemented in Issue #170 fixes:
- Source code structure (`package_name/__init__.py`, `package_name/main.py`)
- Tests directory (`tests/__init__.py`, `tests/test_main.py`)
- Dependencies (`requirements.txt`, `requirements-dev.txt`, `pyproject.toml`)
- README.md

Additionally, user couldn't see hidden files (`.pre-commit-config.yaml`, `.claude/`, `.github/`) with plain `ls`.

## Reproduction

```bash
sgsg init \
  --project-name python-test-project \
  --language python \
  --output-dir /Users/geoffgallinger/Projects \
  --no-interactive

cd python-test-project
ls  # Only shows: CLAUDE.md, plans, scripts
ls -la  # Shows hidden files too
```

**Expected files**:
```
python-test-project/
├── .pre-commit-config.yaml    # EXISTS (hidden)
├── .claude/                   # EXISTS (hidden)
│   ├── skills/
│   └── agents/
├── .github/                   # EXISTS (hidden)
│   └── workflows/
│       ├── ci.yml
│       └── code-review.yml
├── python_test_project/       # MISSING!
│   ├── __init__.py
│   └── main.py
├── tests/                     # MISSING!
│   ├── __init__.py
│   └── test_main.py
├── scripts/                   # EXISTS
│   ├── check-all.sh
│   ├── test.sh
│   └── ...
├── plans/                     # EXISTS
│   └── architecture/
├── requirements.txt           # MISSING!
├── requirements-dev.txt       # MISSING!
├── pyproject.toml             # MISSING!
├── README.md                  # MISSING!
└── CLAUDE.md                  # EXISTS
```

## Root Cause

**Location**: `start_green_stay_green/cli.py:856-895`

**The Bug**: New generators not integrated into CLI

### What Happened

In Issue #170, we created 4 new generators with full test coverage:
1. **DependenciesGenerator** (PR #177) - `start_green_stay_green/generators/dependencies.py`
2. **StructureGenerator** (PR #179) - `start_green_stay_green/generators/structure.py`
3. **TestsGenerator** (PR #181) - `start_green_stay_green/generators/tests_gen.py`
4. **ReadmeGenerator** (PR #183) - `start_green_stay_green/generators/readme.py`

Each generator:
- ✅ Implemented with BaseGenerator inheritance
- ✅ Has 14 comprehensive unit tests
- ✅ Tests passing with 97%+ coverage
- ✅ Code reviewed and merged

**BUT**: None were integrated into `cli.py`!

### Current CLI Flow

```python
# start_green_stay_green/cli.py:856-895
def _generate_project_files(...):
    with Progress(...) as progress:
        _generate_scripts_step(...)              # ✅ Called
        _generate_precommit_step(...)            # ✅ Called
        _generate_skills_step(...)               # ✅ Called
        _generate_with_orchestrator(...)         # ✅ Called
            # Inside _generate_with_orchestrator:
            _generate_ci_step(...)               # ✅ Called
            _generate_review_step(...)           # ✅ Called
            _generate_claude_md_step(...)        # ✅ Called
            _generate_architecture_step(...)     # ✅ Called
            _generate_subagents_step(...)        # ✅ Called

        # MISSING GENERATORS:
        # ❌ _generate_dependencies_step(...)   NOT CALLED!
        # ❌ _generate_structure_step(...)      NOT CALLED!
        # ❌ _generate_tests_step(...)          NOT CALLED!
        # ❌ _generate_readme_step(...)         NOT CALLED!
```

### Why This Happened

**Issue #170 workflow**:
1. Created RCA ✅
2. Created Issue #170 ✅
3. Broke into 5 tasks ✅
4. Created generators with tests ✅
5. Merged PRs #177, #179, #181, #183 ✅
6. Closed Issue #170 ✅
7. **FORGOT** to integrate into CLI ❌

The generators exist and work perfectly, but they're never called!

## Contributing Factors

1. **Large refactor**: Issue #170 was split into 5 PRs (Tasks #10-14)
2. **Focus on generators**: Each PR focused on generator implementation + tests
3. **No integration task**: Never created a final task to wire generators into CLI
4. **No E2E test**: Existing tests use MagicMock, so generators aren't actually called
5. **Manual testing gap**: Never ran `sgsg init` after merging to verify end-to-end

## Impact

**Severity**: High
- **Functionality**: Generated projects are incomplete and unusable
- **User Experience**: Users see "success" but files are missing
- **Quality**: Can't run quality checks without dependencies/tests
- **Discoverability**: Hidden files issue confuses users

**User Impact**:
- ❌ Can't install dependencies (no requirements.txt)
- ❌ Can't run code (no source structure)
- ❌ Can't run tests (no tests directory)
- ❌ No documentation (no README.md)
- ❌ Confusing output (says "generated" but files missing)

## Fix Strategy

### Part 1: Integrate Missing Generators (HIGH PRIORITY)

**Create new _generate_*_step() functions**:

```python
def _generate_dependencies_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate dependencies files with progress indicator."""
    task = progress.add_task("Generating dependencies...", total=None)
    config = DependenciesConfig(
        project_name=project_name,
        language=language,
        package_name=project_name.replace("-", "_"),
    )
    generator = DependenciesGenerator(project_path, config)
    generator.generate()
    progress.stop_task(task)
    progress.update(task, description="[green]✓[/green] Generated dependencies")

def _generate_structure_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate source code structure with progress indicator."""
    task = progress.add_task("Generating source structure...", total=None)
    config = StructureConfig(
        project_name=project_name,
        language=language,
        package_name=project_name.replace("-", "_"),
    )
    generator = StructureGenerator(project_path, config)
    generator.generate()
    progress.stop_task(task)
    progress.update(task, description="[green]✓[/green] Generated source structure")

def _generate_tests_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate tests directory with progress indicator."""
    task = progress.add_task("Generating tests...", total=None)
    config = TestsConfig(
        project_name=project_name,
        language=language,
        package_name=project_name.replace("-", "_"),
    )
    generator = TestsGenerator(project_path, config)
    generator.generate()
    progress.stop_task(task)
    progress.update(task, description="[green]✓[/green] Generated tests")

def _generate_readme_step(
    project_path: Path, project_name: str, language: str, progress: Progress
) -> None:
    """Generate README.md with progress indicator."""
    task = progress.add_task("Generating README...", total=None)
    config = ReadmeConfig(
        project_name=project_name,
        language=language,
        package_name=project_name.replace("-", "_"),
    )
    generator = ReadmeGenerator(project_path, config)
    generator.generate()
    progress.stop_task(task)
    progress.update(task, description="[green]✓[/green] Generated README")
```

**Update _generate_project_files()**:

```python
def _generate_project_files(...):
    with Progress(...) as progress:
        # Core structure first
        _generate_structure_step(...)       # NEW!
        _generate_dependencies_step(...)    # NEW!
        _generate_tests_step(...)           # NEW!
        _generate_readme_step(...)          # NEW!

        # Quality infrastructure
        _generate_scripts_step(...)
        _generate_precommit_step(...)
        _generate_skills_step(...)

        # AI-powered features
        _generate_with_orchestrator(...)

        # Optional dashboard
        if enable_live_dashboard:
            _generate_metrics_dashboard_step(...)
```

**Add imports**:

```python
from start_green_stay_green.generators.dependencies import DependenciesConfig
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator
from start_green_stay_green.generators.tests_gen import TestsConfig
from start_green_stay_green.generators.tests_gen import TestsGenerator
from start_green_stay_green.generators.readme import ReadmeConfig
from start_green_stay_green.generators.readme import ReadmeGenerator
```

### Part 2: Add E2E Test with TDD Approach

**Create E2E test that actually runs init**:

```python
# tests/e2e/test_init_command.py
"""E2E tests for init command that verify actual file generation."""

import tempfile
from pathlib import Path
import subprocess

def test_init_generates_all_expected_files() -> None:
    """Test that init command generates complete project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run actual CLI command
        result = subprocess.run(
            [
                "sgsg",
                "init",
                "--project-name", "test-project",
                "--language", "python",
                "--output-dir", tmpdir,
                "--no-interactive",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        project_dir = Path(tmpdir) / "test-project"

        # Verify ALL files exist
        assert (project_dir / "test_project" / "__init__.py").exists()
        assert (project_dir / "test_project" / "main.py").exists()
        assert (project_dir / "tests" / "__init__.py").exists()
        assert (project_dir / "tests" / "test_main.py").exists()
        assert (project_dir / "requirements.txt").exists()
        assert (project_dir / "requirements-dev.txt").exists()
        assert (project_dir / "pyproject.toml").exists()
        assert (project_dir / "README.md").exists()
        assert (project_dir / ".pre-commit-config.yaml").exists()
        assert (project_dir / ".claude" / "skills").exists()
        assert (project_dir / "scripts" / "check-all.sh").exists()
        assert (project_dir / "CLAUDE.md").exists()
        assert (project_dir / "plans" / "architecture").exists()
```

This test will FAIL until we integrate the generators, following TDD red-green-refactor.

### Part 3: Improve User Communication

**Add better output messages**:

```python
console.print("\n[green]✓[/green] Project generated successfully at: {project_path}")
console.print("\n[bold]Files created:[/bold]")
console.print("  Source:     test_project/__init__.py, test_project/main.py")
console.print("  Tests:      tests/__init__.py, tests/test_main.py")
console.print("  Deps:       requirements.txt, requirements-dev.txt, pyproject.toml")
console.print("  Docs:       README.md, CLAUDE.md")
console.print("  Quality:    .pre-commit-config.yaml, scripts/")
console.print("  AI:         .claude/, .github/workflows/, plans/")
console.print("\n[dim]Tip: Use 'ls -la' to see hidden files (starting with '.')")
```

## Files to Change

**1. CLI Integration** (`start_green_stay_green/cli.py`):
- Add 8 new imports (4 configs + 4 generators)
- Add 4 new `_generate_*_step()` functions (~20 lines each)
- Update `_generate_project_files()` to call new steps
- ~100 lines of changes

**2. E2E Test** (`tests/e2e/test_init_command.py`):
- Create new E2E test file
- Test actual CLI execution
- Verify all files generated
- ~50 lines

**Total**: ~150 lines across 2 files

## Test Strategy

### TDD Red-Green-Refactor

**1. RED - Write failing E2E test**:
```bash
pytest tests/e2e/test_init_command.py -v
# Should FAIL - missing files
```

**2. GREEN - Integrate generators**:
- Add imports
- Create step functions
- Wire into _generate_project_files()
```bash
pytest tests/e2e/test_init_command.py -v
# Should PASS - all files generated
```

**3. REFACTOR - Run all quality checks**:
```bash
pre-commit run --all-files
# Verify no regressions
```

### Manual Verification

```bash
sgsg init --project-name test-proj --language python --output-dir /tmp --no-interactive
cd /tmp/test-proj
ls -la  # Verify all files present
./scripts/check-all.sh  # Verify quality checks pass
```

## Prevention

1. **E2E testing**: Add E2E test that runs actual CLI (not mocked)
2. **Integration checklist**: When adding new generators, require CLI integration
3. **Manual smoke test**: Always run `sgsg init` after generator PRs
4. **CI improvement**: Add E2E test to CI pipeline

## Timeline

- **Discovery**: 2026-02-02 (user manual testing)
- **RCA Completed**: 2026-02-02
- **Fix Target**: Same session - HIGH PRIORITY

## Related Issues

- Issue #170: Generated projects missing core structure (parent issue)
- PR #177: DependenciesGenerator (merged, not integrated)
- PR #179: StructureGenerator (merged, not integrated)
- PR #181: TestsGenerator (merged, not integrated)
- PR #183: ReadmeGenerator (merged, not integrated)

## Conclusion

Critical bug: We created and tested 4 new generators but never wired them into the CLI. The generators work perfectly (97%+ test coverage), but they're never called. Need to:

1. **Integrate generators into CLI** (4 new step functions + imports)
2. **Add E2E test** (TDD approach - red, green, refactor)
3. **Verify end-to-end** (manual `sgsg init` test)

Follow SGSG 3-gate methodology for the fix.
