# Claude Code Project Context: Start Green Stay Green

**Version**: 2.0 (Modular)
**Last Updated**: 2026-01-22

---

## Quick Navigation

**Core Documentation**:
- 📋 **[Critical Principles](claude/principles.md)** - Non-negotiable rules (READ FIRST)
- 🎯 **[Quality Standards](claude/quality-standards.md)** - Requirements and enforcement
- 🔄 **[Development Workflow](claude/workflow.md)** - Stay Green process
- 🧪 **[Testing Strategy](claude/testing.md)** - Test patterns and coverage
- 🛠️ **[Tool Usage](claude/tools.md)** - Scripts, patterns, and code standards
- 🚨 **[Troubleshooting](claude/troubleshooting.md)** - Common mistakes and fixes

**Additional Resources**:
- [Stay Green Workflow (Detailed)](reference/workflows/stay-green.md)
- [Appendix A: AI Subagent Guidelines](#appendix-a-ai-subagent-guidelines)
- [Appendix B: Key Files](#appendix-b-key-files)
- [Appendix C: External References](#appendix-c-external-references)

---

## 📋 Critical Principles (Quick Reference)

**For detailed explanation, see [claude/principles.md](claude/principles.md)**

1. **Run `pre-commit run --all-files` before every commit** - Single comprehensive quality gate
2. **Never duplicate content (DRY)** - Always reference canonical source
3. **No shortcuts - fix root causes** - Never bypass quality checks
4. **Stay Green** - Never request review with failing checks (3-gate workflow)
5. **Quality First** - Meet MAXIMUM QUALITY standards (90% coverage, ≤10 complexity, periodic mutation testing)
6. **Operate from project root** - Use relative paths, never `cd`
7. **Verify before commit** - All hooks must pass

**The 3 Gates**:
1. Gate 1: `pre-commit run --all-files` passes (all hooks)
2. Gate 2: CI pipeline green (all jobs ✅)
3. Gate 3: Code review LGTM

**Note**: Mutation testing (≥80% score) is recommended as a periodic quality gate for critical infrastructure, not enforced continuously.

---

## 🎯 Quality Standards (Quick Reference)

**For complete standards, see [claude/quality-standards.md](claude/quality-standards.md)**

| Metric | Threshold | Tool |
|--------|-----------|------|
| **Code Coverage** | ≥90% | pytest-cov |
| **Docstring Coverage** | ≥95% | interrogate |
| **Mutation Score** | ≥80% | mutmut |
| **Cyclomatic Complexity** | ≤10 per function | radon |
| **Pylint Score** | ≥9.0 | pylint |

**Pre-Commit Hooks**: 32 comprehensive hooks (formatting, linting, tests, coverage, security, etc.)

---

## 📖 Project Overview

Start Green Stay Green is a meta-tool for generating quality-controlled, AI-ready repositories with enterprise-grade quality controls pre-configured.

**Purpose**: Enable AI-assisted development workflows with zero quality compromises from day one.

**What We Generate**:
- CI/CD pipelines (GitHub Actions)
- Quality control scripts (`./scripts/*`)
- AI subagent profiles (`.claude/agents/`)
- Architecture enforcement rules
- Pre-commit hooks configuration
- Comprehensive documentation

---

## 🏗️ Architecture

**Core Philosophy**:
- **Maximum Quality**: No shortcuts, comprehensive tooling, strict enforcement
- **AI-First**: Designed for AI-assisted development with minimal human intervention
- **Composable**: Modular generators for each quality component
- **Multi-Language**: Python, TypeScript, Go, Rust, Swift support
- **Reproducible**: Deterministic generation of identical quality infrastructure

**Component Structure**:

```
start_green_stay_green/
├── start_green_stay_green/      # Main package
│   ├── ai/                      # AI orchestration (Claude API)
│   ├── config/                  # Configuration management
│   ├── generators/              # Component generators (CI, scripts, etc.)
│   ├── github/                  # GitHub API integration
│   └── utils/                   # Common utilities
├── templates/                   # Jinja2 templates (language-specific)
├── reference/                   # Reference implementations
│   ├── workflows/               # Workflow documentation
│   ├── subagents/               # Subagent profiles
│   └── scripts/                 # Script templates
├── tests/                       # Test suite (97%+ coverage)
│   ├── unit/                    # Fast, isolated tests
│   ├── integration/             # Component interaction tests
│   └── e2e/                     # End-to-end scenarios
└── scripts/                     # Quality control scripts
    ├── check-all.sh             # Run all quality checks
    ├── test.sh                  # Run tests with coverage
    ├── lint.sh                  # Linting and type checking
    ├── format.sh                # Auto-format code
    ├── security.sh              # Security scanning
    ├── complexity.sh            # Code complexity analysis
    └── mutation.sh              # Mutation testing
```

**For detailed architecture, see [claude/workflow.md](claude/workflow.md)**

---

## 🔄 Development Workflow (Quick Start)

**For complete workflow, see [claude/workflow.md](claude/workflow.md) and [reference/workflows/stay-green.md](reference/workflows/stay-green.md)**

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes and write tests
vim start_green_stay_green/my_module.py
vim tests/unit/test_my_module.py

# 3. Run ALL quality checks (32 hooks)
pre-commit run --all-files

# 4. Fix any issues and run again
# (Many issues auto-fixed: formatting, whitespace, etc.)
pre-commit run --all-files

# 5. Commit (only when all hooks pass)
git add .
git commit -m "feat(module): add my feature (#123)"

# 6. Push and create PR
git push origin feature/my-feature
gh pr create --fill

# 7. Wait for 3 gates to pass
# - Gate 1: Local (done ✅)
# - Gate 2: CI pipeline (monitor with `gh pr checks`)
# - Gate 3: Claude code review (LGTM)

# 8. Merge when all gates pass
```

---

## 🛠️ Tool Usage (Quick Reference)

**For complete patterns, see [claude/tools.md](claude/tools.md)**

**Primary Command** (local development):
```bash
pre-commit run --all-files  # Runs ALL 32 quality hooks
```

**Individual Scripts** (CI/advanced usage):
- `./scripts/check-all.sh` - Run all quality checks
- `./scripts/test.sh --unit` - Run unit tests with coverage
- `./scripts/lint.sh` - Linting and type checking
- `./scripts/format.sh` - Auto-format code
- `./scripts/security.sh` - Security scanning
- `./scripts/mutation.sh` - Mutation testing (80% threshold)

**Important**: Always use `pre-commit run --all-files` for local development. Scripts are for CI and advanced scenarios.

---

## 🚨 Common Mistakes (Quick Reference)

**For detailed examples, see [claude/troubleshooting.md](claude/troubleshooting.md)**

1. **Skipping local quality checks** (35%) - Always run `pre-commit run --all-files` before committing
2. **Lowering quality thresholds** (25%) - Write more tests, don't lower standards
3. **Using direct tool invocation** (20%) - Use `pre-commit run --all-files` instead of individual tools
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
- `pyproject.toml`: All Python tool configurations (ruff, mypy, pytest, black, isort, etc.)
- `requirements.txt`: Runtime dependencies
- `requirements-dev.txt`: Development dependencies
- `.pre-commit-config.yaml`: Pre-commit hook configurations (32 hooks)
- `.github/workflows/`: CI/CD pipeline definitions

### Documentation Files
- `CLAUDE.md`: This file - Project context index
- `claude/*.md`: Modular documentation (principles, quality, workflow, testing, tools, troubleshooting)
- `reference/workflows/stay-green.md`: Complete Stay Green workflow documentation
- `plan/SPEC.md`: Complete project specification
- `plan/MAXIMUM_QUALITY_ENGINEERING.md`: Quality framework
- `README.md`: Project overview and quick start

### Scripts
- `scripts/check-all.sh`: Run all quality checks
- `scripts/fix-all.sh`: Automatically fix issues
- `scripts/test.sh`: Run test suite
- `scripts/lint.sh`: Run linters
- `scripts/format.sh`: Format code
- `scripts/security.sh`: Security scanning
- `scripts/mutation.sh`: Run mutation tests
- `scripts/complexity.sh`: Analyze code complexity

---

## Appendix C: External References

- [MAXIMUM_QUALITY_ENGINEERING.md](plan/MAXIMUM_QUALITY_ENGINEERING.md) - Comprehensive quality framework
- [SPEC.md](plan/SPEC.md) - Complete project specification
- [README.md](README.md) - Project overview and setup
- [Pre-commit Documentation](https://pre-commit.com) - Git hooks framework
- [Ruff Documentation](https://docs.astral.sh/ruff) - Python linter
- [MyPy Documentation](https://www.mypy-lang.org) - Type checker
- [Pytest Documentation](https://docs.pytest.org) - Test framework
- [Conventional Commits](https://www.conventionalcommits.org) - Commit message standard

---

**Last Updated**: 2026-01-22
**Framework Version**: 2.0 (Modular Structure)
