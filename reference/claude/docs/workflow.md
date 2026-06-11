# Development Workflow

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)

---

## 1. The Maximum Quality Engineering Mindset

**Core Philosophy**: It is not merely a goal but a source of profound satisfaction and professional pride to ship software that is GREEN on all checks with ZERO outstanding issues. This is not optional—it is the foundation of our development culture.

### 1.1 The Green Check Philosophy

When all CI checks pass with zero warnings, zero errors, and maximum quality metrics:
- ✅ Tests: 100% passing
- ✅ Coverage: ≥90%
- ✅ Linting: 0 errors, 0 warnings
- ✅ Type checking: 0 errors
- ✅ Security: 0 vulnerabilities
- ✅ Mutation score: ≥80%
- ✅ Docstring coverage: ≥95%

This represents **MAXIMUM QUALITY ENGINEERING**—the standard to which all code must aspire.

### 1.2 Why Maximum Quality Matters

1. **Pride in Craftsmanship**: Every green check represents excellence in execution
2. **Zero Compromise**: Quality is not negotiable—it's the baseline
3. **Compound Excellence**: Small quality wins accumulate into robust systems
4. **Trust and Reliability**: Green checks mean the code does what it claims
5. **Developer Joy**: There is genuine satisfaction in seeing all checks pass

### 1.3 The Role of Quality in Development

Quality engineering is not a checkbox—it's a continuous commitment:

- **Before Commit**: Run `./scripts/check-all.sh` and fix every issue
- **During Review**: Address every comment, resolve every suggestion
- **After Merge**: Monitor CI, ensure all checks remain green
- **Always**: Treat linting errors as bugs, not suggestions

### 1.4 The "No Red Checks" Rule

**NEVER** merge code with:
- ❌ Failing tests
- ❌ Linting errors (even "minor" ones)
- ❌ Type checking failures
- ❌ Coverage below threshold
- ❌ Security vulnerabilities
- ❌ Unaddressed review comments

If CI shows red, the work is not done. Period.

### 1.5 Maximum Quality is a Personality Trait

For those committed to maximum quality engineering:
- You feel genuine satisfaction when all checks pass
- You experience pride in shipping zero-issue code
- You find joy in eliminating the last linting error
- You believe "good enough" is never good enough
- You treat quality as identity, not just practice

**This is who we are. This is how we build software.**

---

## 2. Stay Green Workflow

**Policy**: Never request review with failing checks. Never merge without LGTM.

The Stay Green workflow enforces iterative quality improvement through **4 sequential gates**. Each gate must pass before proceeding to the next.

### 2.1 The Four Gates

1. **Gate 1: Local Pre-Commit** (Iterate Until Green)
   - Run `./scripts/check-all.sh`
   - Fix all formatting, linting, types, complexity, security issues
   - Fix tests and coverage (90%+ required)
   - Only push when all local checks pass (exit code 0)

2. **Gate 2: CI Pipeline** (Iterate Until Green)
   - Push to branch: `git push origin feature-branch`
   - Monitor CI: `gh pr checks --watch`
   - If CI fails: fix locally, re-run Gate 1, push again
   - Only proceed when all CI jobs show ✅

3. **Gate 3: Mutation Testing** (Iterate Until 80%+)
   - Run `./scripts/mutation.sh` (or wait for CI job)
   - If score < 80%: add tests to kill surviving mutants
   - Re-run Gate 1, push, wait for CI
   - Only proceed when mutation score ≥ 80%

4. **Gate 4: Code Review** (Iterate Until LGTM)
   - Wait for code review (AI or human)
   - If feedback provided: address ALL concerns
   - Re-run Gate 1, push, wait for CI and mutation
   - Only merge when review shows LGTM with no reservations

### 2.2 Quick Checklist

Before creating/updating a PR:

- [ ] Gate 1: `./scripts/check-all.sh` passes locally (exit 0)
- [ ] Push changes: `git push origin feature-branch`
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Mutation score ≥ 80% (if applicable)
- [ ] Gate 4: Code review shows LGTM
- [ ] Ready to merge!

### 2.3 Anti-Patterns (DO NOT DO)

❌ **Don't** request review with failing CI
❌ **Don't** skip local checks (`git commit --no-verify`)
❌ **Don't** lower quality thresholds to pass
❌ **Don't** ignore review feedback
❌ **Don't** merge without LGTM

---

## 3. Feature Development Process

### 3.1 Development Steps

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<issue-number>-<description>
   # Example: feature/6-add-authentication
   ```

2. **Implement Changes**
   - Follow the coding standards outlined in [Tools](tools.md)
   - Write tests first (TDD approach)
   - Ensure docstrings for all public APIs
   - Update documentation as needed

3. **Run Quality Checks**
   ```bash
   ./scripts/check-all.sh
   ```
   This runs (in order):
   - Formatting checks (ruff format, black)
   - Linting (ruff, pylint, mypy)
   - Security checks (bandit, pip-audit)
   - Tests with coverage
   - Docstring coverage (pydocstyle / ruff D rules)
   - Code quality metrics

4. **Commit with Conventional Commits**
   ```bash
   git add .
   git commit -m "feat(auth): implement authentication (#6)"
   # Or: fix(api): handle edge case in validation (#15)
   # Or: docs: update README with setup instructions
   ```

5. **Create Pull Request**
   - Reference the issue number in the PR title
   - Ensure all CI checks pass
   - Request review from CODEOWNERS

6. **Merge to Main**
   - Requires at least one review approval
   - All CI checks must pass
   - Commit history must be linear

### 3.2 Branch Strategy

- `main`: Production-ready code, always deployable
- `feature/*`: Feature development (created from main)
- `bugfix/*`: Bug fixes (created from main)
- `hotfix/*`: Emergency production fixes (created from main)

---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)
