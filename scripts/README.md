# Scripts Directory

This directory contains all quality control scripts for the Start Green Stay Green project. These scripts are the **single source of truth** for running checks and quality gates across the project.

## Philosophy

- **Single source of truth**: All CI, pre-commit hooks, and local development use these scripts
- **Consistent interface**: All scripts follow standard conventions for arguments and exit codes
- **Cross-platform compatibility**: Scripts work on macOS, Linux, and in CI environments
- **Clear error handling**: Proper exit codes and error messages for debugging

## Standard Interface

All scripts follow these conventions:

### Common Arguments

```bash
--fix       # Auto-fix issues (if applicable)
--check     # Check only mode (fail if issues found)
--verbose   # Show detailed output
--help      # Display help message
```

### Exit Codes

```
0   # Success
1   # Check/test failure (issues found)
2   # Error running the command (missing tools, etc.)
```

### Help

Every script supports `--help`:

```bash
./scripts/lint.sh --help
./scripts/test.sh --help
```

## Scripts Overview

### 1. lint.sh - Linting Checks

Runs **Ruff** for fast Python linting.

```bash
./scripts/lint.sh              # Check mode (default)
./scripts/lint.sh --fix        # Auto-fix issues
./scripts/lint.sh --verbose    # Show details
```

**Tools**: Ruff

---

### 2. format.sh - Code Formatting

Format code with **Black** and **isort**.

```bash
./scripts/format.sh --fix      # Apply formatting (default)
./scripts/format.sh --check    # Check only
```

**Tools**: Black, isort

---

### 3. typecheck.sh - Type Checking

Run **MyPy** for static type analysis.

```bash
./scripts/typecheck.sh         # Run type checks
./scripts/typecheck.sh --verbose
```

**Tools**: MyPy

---

### 4. test.sh - Testing

Run tests with **Pytest**.

```bash
./scripts/test.sh                      # Unit tests (default)
./scripts/test.sh --unit               # Unit tests only
./scripts/test.sh --integration        # Integration tests
./scripts/test.sh --e2e                # End-to-end tests
./scripts/test.sh --all                # All test types
./scripts/test.sh --unit --coverage    # With coverage report
./scripts/test.sh --mutation           # Mutation tests (uses mutation.sh)
```

**Tools**: Pytest, pytest-cov, mutmut (optional)

---

### 4a. mutation.sh - Mutation Testing

Run mutation tests with score validation.

```bash
./scripts/mutation.sh                  # Run with 80% minimum (MAXIMUM QUALITY)
./scripts/mutation.sh --min-score 70   # Run with 70% minimum
./scripts/mutation.sh --verbose        # Show detailed output
```

**Quality Standards**:
- MAXIMUM QUALITY: 80% minimum mutation score
- Good: 70-79%
- Acceptable: 60-69%
- Poor: <60%

**Tools**: mutmut

**Note**: Mutation testing can take several minutes to complete. It's run separately from regular tests and typically only in CI on main branch merges.

---

### 5. security.sh - Security Checks

Run **Bandit** and **Safety** for security vulnerabilities.

```bash
./scripts/security.sh          # Basic security checks
./scripts/security.sh --full   # Comprehensive scan (includes secret detection)
```

**Tools**: Bandit, Safety, detect-secrets (optional)

---

### 6. coverage.sh - Coverage Reports

Generate test coverage reports.

```bash
./scripts/coverage.sh          # Terminal report
./scripts/coverage.sh --html   # Generate HTML report
```

Generates `htmlcov/index.html` for detailed coverage visualization.

**Tools**: pytest-cov, coverage

---

### 7. docs.sh - Documentation

Generate API documentation.

```bash
./scripts/docs.sh              # Generate docs
./scripts/docs.sh --serve      # Generate and serve locally
```

Generates documentation in `docs/api/` using **pdoc**.

**Tools**: pdoc, mkdocs (fallback)

---

### 8. review-pr.sh - PR Review

Review open pull requests (framework for AI integration).

```bash
./scripts/review-pr.sh              # Review all open PRs
./scripts/review-pr.sh --number=42  # Review specific PR
```

**Tools**: GitHub CLI (gh)

---

### 9. check-all.sh - Run All Checks

Run all quality checks in sequence.

```bash
./scripts/check-all.sh         # Run all checks
./scripts/check-all.sh --verbose
```

Runs in order:
1. Linting
2. Formatting (check only)
3. Type checking
4. Security checks
5. Complexity analysis
6. Unit tests
7. Coverage report

**Note**: Mutation testing is NOT included in check-all.sh due to long runtime. Run separately with `./scripts/mutation.sh` or `./scripts/test.sh --mutation`

---

### 10. fix-all.sh - Auto-fix Everything

Auto-fix all auto-fixable issues.

```bash
./scripts/fix-all.sh           # Apply all fixes
./scripts/fix-all.sh --verbose
```

Applies:
1. Linting fixes (Ruff)
2. Formatting fixes (Black + isort)

**Note**: Some issues require manual intervention. Review changes before committing.

---

### 11. audit-deps.sh - Dependency Audit

Audit dependencies for vulnerabilities and outdated packages.

```bash
./scripts/audit-deps.sh             # Audit dependencies
./scripts/audit-deps.sh --outdated  # Show outdated packages
./scripts/audit-deps.sh --fix       # Update dependencies
```

**Tools**: Safety, pip-audit

---

### 12. complexity.sh - Complexity Analysis

Analyze code complexity using **Radon** and **Xenon**.

```bash
./scripts/complexity.sh         # Analyze complexity
./scripts/complexity.sh --verbose
```

Metrics:
- Cyclomatic complexity (max 10)
- Maintainability index (min 20)

**Tools**: Radon, Xenon

---

### 13. setup-dev.sh - Development Setup

Set up the development environment.

```bash
./scripts/setup-dev.sh         # Set up dev environment
./scripts/setup-dev.sh --verbose
```

Includes:
1. Python virtual environment
2. Dependency installation
3. Dev dependencies
4. Pre-commit hooks
5. Package installation (editable mode)

---

## Recommended Workflows

### Before Committing

```bash
# Auto-fix issues and run all checks
./scripts/fix-all.sh
./scripts/check-all.sh
```

### Full Quality Check

```bash
./scripts/check-all.sh --verbose
```

### Coverage Check

```bash
./scripts/coverage.sh --html
# Open htmlcov/index.html
```

### Security Audit

```bash
./scripts/security.sh --full
./scripts/audit-deps.sh
```

### Development Setup

```bash
./scripts/setup-dev.sh
source .venv/bin/activate
```

## CI/CD Integration

All GitHub Actions workflows invoke these scripts directly:

```yaml
- name: Run linting
  run: ./scripts/lint.sh --check

- name: Run tests
  run: ./scripts/test.sh --unit --coverage

- name: Security audit
  run: ./scripts/security.sh
```

## Pre-commit Integration

The `.pre-commit-config.yaml` uses these scripts:

```yaml
- id: lint
  name: Lint
  entry: ./scripts/lint.sh --check
  language: script
  types: [python]
```

## Troubleshooting

### Script not executable

```bash
chmod +x scripts/*.sh
```

### Missing tools

Scripts gracefully handle missing tools with informative error messages.

Install all required tools:

```bash
./scripts/setup-dev.sh
```

### Exit code 2 (Error)

Indicates missing dependencies. Run:

```bash
./scripts/setup-dev.sh
```

### Verbose troubleshooting

All scripts support `--verbose`:

```bash
./scripts/check-all.sh --verbose
```

## Adding New Scripts

When adding a new script:

1. **Follow the template** from SPEC.md (lines 243-272)
2. **Use set -euo pipefail** for error handling
3. **Support standard arguments**: `--fix`, `--check`, `--verbose`, `--help`
4. **Use proper exit codes**: 0=success, 1=failure, 2=error
5. **Add help documentation** with `--help`
6. **Update this README** with description and examples
7. **Make executable**: `chmod +x scripts/newscript.sh`

## References

- SPEC.md Issue 1.4: Scripts Directory (lines 208-277)
- MAXIMUM_QUALITY_ENGINEERING.md: Quality standards reference
- GitHub Actions workflows: `.github/workflows/`
- Pre-commit configuration: `.pre-commit-config.yaml`
