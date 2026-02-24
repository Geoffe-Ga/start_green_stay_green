# RCA: Deprecated `safety` Package Used for Dependency Scanning

**Date**: 2026-02-23
**Severity**: Medium
**Component**: scripts/security.sh, generators, dependencies

---

## Problem Statement

The project uses `safety` (PyUp Safety CLI) for dependency vulnerability scanning.
Safety has been deprecated in favor of `pip-audit` (maintained by PyPA/Google).
This affects both our own development scripts and the code we generate for users.

## Root Cause

The project was originally built using `safety` which was the standard at the time.
The `safety` package has since been deprecated and its free tier discontinued. The
recommended replacement is `pip-audit` from PyPA.

## Impact

- **Our scripts**: `scripts/security.sh` and `scripts/audit-deps.sh` use `safety`
- **Generated output**: Users who run `sgsg init` get projects that depend on `safety`
- **Dependencies**: `safety>=3.0.0` in `requirements-dev.txt` and `pyproject.toml`
- **Pre-commit**: Generated pre-commit config references `safety` hooks

## Affected Files

### Our own scripts (direct usage)
- `scripts/security.sh` - Runs `safety check`
- `scripts/audit-deps.sh` - Runs `safety check`
- `requirements-dev.txt` - Lists `safety>=3.0.0`
- `pyproject.toml` - Lists `safety>=3.0.0`

### Generated code (what we output for users)
- `start_green_stay_green/generators/scripts.py` - Generates security.sh with `safety`
- `start_green_stay_green/generators/dependencies.py` - Lists `safety` as dependency
- `start_green_stay_green/generators/precommit.py` - Adds safety pre-commit hook
- `start_green_stay_green/generators/ci.py` - References `safety` in CI config
- `start_green_stay_green/generators/metrics.py` - References `safety` as security tool
- `start_green_stay_green/generators/readme.py` - Documents `safety` usage

### Reference docs
- `reference/ci/python.yml`, `reference/precommit/.pre-commit-config.yaml`
- `reference/MAXIMUM_QUALITY_ENGINEERING.md`

### Tests
- `tests/unit/generators/test_scripts.py`
- `tests/unit/generators/test_precommit.py`
- `tests/unit/generators/test_ci.py`
- `tests/unit/generators/test_metrics.py`

## Fix Strategy

Replace all `safety` references with `pip-audit`:
- `safety check` → `pip-audit`
- `safety>=3.0.0` → `pip-audit>=2.7.0`
- Pre-commit hooks: Remove safety hook, add pip-audit hook
- Update tests to match new tool name and commands

## Prevention

- Periodic dependency freshness audit to catch deprecated packages
