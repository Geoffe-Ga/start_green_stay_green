# Critical Principles

**Navigation**: [← Back to CLAUDE.md](../../CLAUDE.md) | [Quality Standards →](quality-standards.md)

---

These principles are **non-negotiable** and must be followed without exception:

## 1. Run Pre-Commit for All Quality Checks

**For local development, ALWAYS use `pre-commit run --all-files` as the single comprehensive quality gate.**

**Why**: Pre-commit runs ALL quality checks (formatting, linting, tests, coverage, security, etc.) with correct configuration, ensuring consistency between local development and CI.

**Primary Command**:
```bash
# Run ALL quality checks before every commit
pre-commit run --all-files
```

**Individual Scripts (CI/Advanced Usage)**:

The `./scripts/*` files are used by pre-commit hooks and CI pipelines. You can run them individually for targeted checks during development, but ALWAYS run `pre-commit run --all-files` before committing.

| Task | Direct Tool (❌ NEVER) | Script (⚙️ CI/Advanced) | Pre-Commit (✅ PRIMARY) |
|------|----------|-----------|----------------------|
| Format code | `black .` | `./scripts/format.sh` | `pre-commit run --all-files` |
| Run tests | `pytest` | `./scripts/test.sh` | `pre-commit run --all-files` |
| Type check | `mypy .` | `./scripts/lint.sh` | `pre-commit run --all-files` |
| Lint code | `ruff check .` | `./scripts/lint.sh` | `pre-commit run --all-files` |
| All checks | *(run each tool)* | `./scripts/check-all.sh` | `pre-commit run --all-files` |

See [Tool Usage](tools.md) for complete patterns.

---

## 2. DRY Principle - Single Source of Truth

Never duplicate content. Always reference the canonical source.

**Examples**:
- ✅ Stay Green documentation → `/reference/workflows/stay-green.md` (single source)
- ✅ Other files → Link to stay-green.md
- ❌ Copy workflow steps into multiple files

**Why**: Duplicated docs get out of sync, causing confusion and errors.

---

## 3. No Shortcuts - Fix Root Causes

Never bypass quality checks or suppress errors without justification.

**Forbidden Shortcuts**:
- ❌ Commenting out failing tests
- ❌ Adding `# noqa` without issue reference
- ❌ Lowering quality thresholds to pass builds
- ❌ Using `git commit --no-verify` to skip pre-commit
- ❌ Deleting code to reduce complexity metrics

**Required Approach**:
- ✅ Fix the failing test or mark with `@pytest.mark.skip(reason="Issue #N")`
- ✅ Refactor code to pass linting (or justify with issue: `# noqa  # Issue #N: reason`)
- ✅ Write tests to reach 90% coverage
- ✅ Always run pre-commit checks
- ✅ Refactor complex functions into smaller ones

See [Troubleshooting](troubleshooting.md) for detailed examples.

---

## 4. Stay Green - Never Request Review with Failing Checks

Follow the 3-gate workflow rigorously.

**The Rule**:
- 🚫 **NEVER** create PR while CI is red
- 🚫 **NEVER** request review with failing checks
- 🚫 **NEVER** merge without LGTM

**The Process**:
1. Gate 1: Local checks pass (`pre-commit run --all-files` → all hooks pass)
2. Gate 2: CI pipeline green (all jobs ✅)
3. Gate 3: Code review LGTM

**Note**: Mutation testing (≥80% score) is recommended as a periodic quality check for critical infrastructure, not enforced continuously.

See [Workflow](workflow.md) for complete documentation.

---

## 5. Quality First - Meet MAXIMUM QUALITY Standards

Quality thresholds are immutable. Meet them, don't lower them.

**Standards**:
- Test Coverage: ≥90%
- Docstring Coverage: ≥95%
- Mutation Score: ≥80%
- Cyclomatic Complexity: ≤10 per function
- Pylint Score: ≥9.0

**When code doesn't meet standards**:
- ❌ Change `fail_under = 70` in pyproject.toml
- ✅ Write more tests, refactor code, improve quality

See [Quality Standards](quality-standards.md) for enforcement mechanisms.

---

## 6. Operate from Project Root

Use relative paths from project root. Never `cd` into subdirectories.

**Why**: Ensures commands work in any environment (local, CI, scripts).

**Examples**:
- ✅ `./scripts/test.sh tests/unit/ai/test_orchestrator.py`
- ❌ `cd tests/unit/ai && pytest test_orchestrator.py`

**CI Note**: CI always runs from project root. Commands that use `cd` will break in CI.

---

## 7. Verify Before Commit

Run `pre-commit run --all-files` before every commit. Only commit if all hooks pass.

**Pre-Commit Checklist**:
- [ ] `pre-commit run --all-files` passes (all hooks pass)
- [ ] All new functions have tests
- [ ] Coverage ≥90% maintained
- [ ] No failing tests
- [ ] Conventional commit message ready

**Note**: `pre-commit run --all-files` includes unit tests and coverage validation since Issue #90.

See [Troubleshooting](troubleshooting.md) for complete checklist.

---

**These principles are the foundation of MAXIMUM QUALITY ENGINEERING. Follow them without exception.**

---

**Navigation**: [← Back to CLAUDE.md](../../CLAUDE.md) | [Quality Standards →](quality-standards.md)
