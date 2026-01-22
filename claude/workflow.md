# Development Workflow

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)

---

## Stay Green Workflow

See [/reference/workflows/stay-green.md](../reference/workflows/stay-green.md) for complete documentation.


### 4.1 The Four Gates

1. **Gate 1: Local Pre-Commit** (Iterate Until Green)
   - Run `pre-commit run --all-files`
   - Fix all formatting, linting, types, complexity, security issues
   - Fix tests and coverage (90%+ required)
   - Only push when all hooks pass (no failures)

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

4. **Gate 4: Claude Code Review** (Iterate Until LGTM)
   - Wait for Claude code review CI job
   - If feedback provided: address ALL concerns
   - Re-run Gate 1, push, wait for CI and mutation
   - Only merge when Claude gives LGTM with no reservations

### 4.2 Quick Checklist

Before creating/updating a PR:

- [ ] Gate 1: `pre-commit run --all-files` passes (all hooks pass)
- [ ] Push changes: `git push origin feature-branch`
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Mutation score ≥ 80% (if applicable)
- [ ] Gate 4: Claude review shows LGTM
- [ ] Ready to merge!

### 4.3 Anti-Patterns (DO NOT DO)

❌ **Don't** request review with failing CI
❌ **Don't** skip local checks (`git commit --no-verify`)
❌ **Don't** lower quality thresholds to pass
❌ **Don't** ignore Claude feedback
❌ **Don't** merge without LGTM

**For complete workflow documentation, see**: `/reference/workflows/stay-green.md`

---

## 5. Architecture

### 5.1 Core Philosophy


---

## Feature Development Process


### 7.1 Feature Development Process

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<issue-number>-<description>
   # Example: feature/6-claude-md-configuration
   ```

2. **Implement Changes**
   - Follow the coding standards outlined below
   - Write tests first (TDD approach)
   - Ensure docstrings for all public APIs
   - Update documentation as needed

3. **Run Quality Checks**
   ```bash
   pre-commit run --all-files
   ```
   This runs all quality hooks (in order):
   - Git checks (large files, merge conflicts, etc.)
   - Security (bandit, secrets detection)
   - Formatting (black, isort, ruff format)
   - Linting (ruff, pylint)
   - Type checking (mypy)
   - Complexity analysis (radon, xenon)
   - Unit tests (pytest)
   - Coverage validation (90% threshold)
   - Code modernization (pyupgrade, autoflake, refurb)
   - Exception handling (tryceratops)
   - Dead code detection (vulture)
   - Docstring coverage (interrogate, 95% threshold)
   - Shell linting (shellcheck)

4. **Commit with Conventional Commits**
   ```bash
   git add .
   git commit -m "feat(ai): implement orchestrator core (#6)"
   # Or: fix(generators): handle edge case in path resolution (#15)
   # Or: docs: update CLAUDE.md configuration guidelines
   ```

5. **Create Pull Request**
   - Reference the issue number in the PR title
   - Ensure all CI checks pass
   - Request review from CODEOWNERS

6. **Merge to Main**
   - Requires at least one review approval
   - All CI checks must pass
   - Commit history must be linear

### 7.2 Branch Strategy



---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)
