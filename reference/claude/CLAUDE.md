# Claude Code Project Context: {{PROJECT_NAME}}

**Version**: 2.0 (Modular)

---

## Quick Navigation

**Core Documentation** (in `.claude/docs/`):
- 📋 **[Critical Principles](.claude/docs/principles.md)** - Non-negotiable rules (READ FIRST)
- 🎯 **[Quality Standards](.claude/docs/quality-standards.md)** - Requirements and enforcement
- 🔄 **[Development Workflow](.claude/docs/workflow.md)** - Stay Green process & mindset
- 🧪 **[Testing Strategy](.claude/docs/testing.md)** - Test patterns and coverage
- 🛠️ **[Tool Usage](.claude/docs/tools.md)** - Scripts, patterns, and code standards
- 🚨 **[Troubleshooting](.claude/docs/troubleshooting.md)** - Common mistakes and fixes

**Additional Resources**:
- [Appendix A: AI Subagent Guidelines](#appendix-a-ai-subagent-guidelines)
- [Appendix B: Key Files](#appendix-b-key-files)
- [Appendix C: External References](#appendix-c-external-references)

---

## 📋 Critical Principles (Quick Reference)

**For detailed explanation, see [.claude/docs/principles.md](.claude/docs/principles.md)**

1. **Use project scripts, not direct tools** - Invoke `./scripts/*`, never raw tools
2. **Never duplicate content (DRY)** - Always reference the canonical source
3. **No shortcuts - fix root causes** - Never bypass quality checks
4. **Stay Green** - Never request review with failing checks (4-gate workflow)
5. **Quality First** - Meet MAXIMUM QUALITY standards (90% coverage, ≤10 complexity, ≥80% mutation)
6. **Operate from project root** - Use relative paths, never `cd`
7. **Verify before commit** - All checks must pass (`./scripts/check-all.sh` → exit 0)

**The 4 Gates**:
1. Gate 1: `./scripts/check-all.sh` passes (exit 0)
2. Gate 2: CI pipeline green (all jobs ✅)
3. Gate 3: Mutation score ≥80%
4. Gate 4: Code review LGTM

---

## 🎯 Quality Standards (Quick Reference)

**For complete standards, see [.claude/docs/quality-standards.md](.claude/docs/quality-standards.md)**

| Metric | Threshold | Tool |
|--------|-----------|------|
| **Code Coverage** | ≥90% | pytest-cov |
| **Docstring Coverage** | ≥95% | pydocstyle / ruff D rules |
| **Mutation Score** | ≥80% | mutmut |
| **Cyclomatic Complexity** | ≤10 per function | radon |
| **Pylint Score** | ≥9.0 | pylint |

---

## 📖 Project Overview

{{PROJECT_DESCRIPTION}}

**Purpose**: {{PROJECT_PURPOSE}}

---

## 🏗️ Architecture

**Core Philosophy**:
- **Maximum Quality**: No shortcuts, comprehensive tooling, strict enforcement
- **Composable**: Modular components with clear interfaces
- **Testable**: Every component designed for easy testing
- **Maintainable**: Clear structure, excellent documentation
- **Reproducible**: Consistent behavior across environments

**Component Structure**:

```
{{PROJECT_NAME}}/
{{ARCHITECTURE_TREE}}
```

**For workflow and architecture detail, see [.claude/docs/workflow.md](.claude/docs/workflow.md)**

---

## 🔄 Development Workflow (Quick Start)

**For the complete workflow, see [.claude/docs/workflow.md](.claude/docs/workflow.md)**

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and write tests (TDD)
# 3. Run ALL quality checks
./scripts/check-all.sh

# 4. Fix any issues and run again
./scripts/check-all.sh

# 5. Commit (only when all checks pass)
git add .
git commit -m "feat(module): add my feature (#123)"

# 6. Push and create PR
git push origin feature/my-feature
gh pr create --fill

# 7. Wait for the 4 gates to pass, then merge
```

---

## 🛠️ Tool Usage (Quick Reference)

**For complete patterns, see [.claude/docs/tools.md](.claude/docs/tools.md)**

**Primary Commands**:
- `./scripts/check-all.sh` - Run all quality checks (before every commit)
- `./scripts/test.sh` - Run tests with coverage
- `./scripts/lint.sh` - Linting and type checking
- `./scripts/format.sh` - Auto-format code
- `./scripts/security.sh` - Security scanning
- `./scripts/mutation.sh` - Mutation testing (80% threshold)

---

## 🚨 Common Mistakes (Quick Reference)

**For detailed examples, see [.claude/docs/troubleshooting.md](.claude/docs/troubleshooting.md)**

1. **Skipping local quality checks** (35%) - Always run `./scripts/check-all.sh` before committing
2. **Lowering quality thresholds** (25%) - Write more tests, don't lower standards
3. **Using direct tool invocation** (20%) - Use the `./scripts/*` wrappers
4. **Commenting out failing tests** (15%) - Fix tests or mark with `@pytest.mark.skip(reason="Issue #N")`
5. **Adding `# noqa` without justification** (5%) - Refactor code or provide issue reference

---

## Appendix A: AI Subagent Guidelines

When delegating work to subagents, provide:

1. **Clear Task Description**
   - What needs to be done
   - Why it matters
   - Success criteria

2. **Relevant Context**
   - Reference files and issues
   - Architecture decisions
   - Quality standards that apply

3. **Dependencies**
   - Other work that must complete first
   - Blocked dependencies
   - Integration points

4. **Acceptance Criteria**
   - All quality checks passing
   - Specific thresholds met
   - Testing requirements
   - Documentation requirements

5. **Execution Strategy**
   - **ALWAYS prefer parallel approaches** when multiple independent tasks exist
   - Launch multiple agents concurrently whenever possible
   - Run integration and implementation tasks simultaneously
   - Maximize throughput by executing non-dependent work in parallel
   - Only execute sequentially when explicit dependencies exist

---

## Appendix B: Key Files

### Configuration Files
- `pyproject.toml`: All tool configurations (ruff, mypy, pytest, black, isort, etc.)
- `requirements.txt`: Runtime dependencies
- `requirements-dev.txt`: Development dependencies
- `.pre-commit-config.yaml`: Git hook configurations
- `.github/workflows/`: CI/CD pipeline definitions

### Documentation Files
- `CLAUDE.md`: This file - Claude Code project context index
- `.claude/docs/*.md`: Modular documentation (principles, quality, workflow, testing, tools, troubleshooting)
- `README.md`: Project overview and quick start
- `docs/`: Additional documentation

### Scripts
- `scripts/check-all.sh`: Run all quality checks
- `scripts/fix-all.sh`: Automatically fix issues
- `scripts/test.sh`: Run test suite
- `scripts/lint.sh`: Run linters
- `scripts/format.sh`: Format code
- `scripts/security.sh`: Security scanning
- `scripts/mutation.sh`: Run mutation tests

---

## Appendix C: External References

- [Pre-commit Documentation](https://pre-commit.com) - Git hooks framework
- [Ruff Documentation](https://docs.astral.sh/ruff) - Python linter
- [MyPy Documentation](https://www.mypy-lang.org) - Type checker
- [Pytest Documentation](https://docs.pytest.org) - Test framework
- [Conventional Commits](https://www.conventionalcommits.org) - Commit message standard
- [Hypothesis Documentation](https://hypothesis.readthedocs.io) - Property-based testing

---

**Framework Version**: 2.0 (Maximum Quality Engineering - Modular)
**Generated By**: Start Green Stay Green
