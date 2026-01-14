# Contributing to Start Green Stay Green

Thank you for your interest in contributing! This project follows MAXIMUM QUALITY ENGINEERING principles.

## Getting Started

### Development Environment Setup

```bash
git clone https://github.com/Geoffe-Ga/start_green_stay_green.git
cd start_green_stay_green
./scripts/setup-dev.sh
```

## Development Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/<issue-number>-<description>
```

### 2. Run Quality Checks Before Commit
```bash
./scripts/check-all.sh  # Must exit 0
```

### 3. Commit with Conventional Commits
```bash
git commit -m "feat(scope): description (#issue)"
```

### 4. Push and Create PR
```bash
git push origin feature/<issue-number>
gh pr create --fill
```

## Stay Green Workflow (4 Gates)

1. **Gate 1:** Local checks pass (`./scripts/check-all.sh`)
2. **Gate 2:** CI pipeline green  
3. **Gate 3:** Mutation score ≥80%
4. **Gate 4:** Code review LGTM

**NEVER** merge with failing checks.

## Quality Standards

- **Coverage:** ≥90% (line and branch)
- **Docstrings:** ≥95% (Google-style)
- **Complexity:** ≤10 per function
- **Linting:** Zero warnings
- **Type Checking:** MyPy strict mode

## Testing

```bash
./scripts/test.sh          # All tests
./scripts/test.sh --unit   # Unit only
./scripts/test.sh --coverage  # With coverage
```

## Forbidden Patterns

- ❌ `git commit --no-verify`
- ❌ `# noqa` without issue reference
- ❌ Lowering quality thresholds
- ❌ Commenting out failing tests
- ❌ Direct tool invocation (use `./scripts/*`)

## Getting Help

- Issues: https://github.com/Geoffe-Ga/start_green_stay_green/issues
- Documentation: See CLAUDE.md

Thank you for contributing!
