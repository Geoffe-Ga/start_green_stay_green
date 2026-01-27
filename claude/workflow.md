# Development Workflow

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)

---

## 1. Stay Green Workflow

**Policy**: Never request review with failing checks. Never merge without LGTM.

See [/reference/workflows/stay-green.md](../reference/workflows/stay-green.md) for complete documentation.

### 1.1 The Four Gates

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

3. **Gate 3: Claude Code Review** (Iterate Until LGTM)
   - Wait for Claude code review CI job
   - If feedback provided: address ALL concerns
   - Re-run Gate 1, push, wait for CI
   - Only merge when Claude gives LGTM with no reservations

**Note**: Mutation testing (80%+ score) is recommended as a periodic quality check for critical infrastructure (e.g., billing, authentication), not enforced continuously. Run with `./scripts/mutation.sh --paths-to-mutate <files>`.

### 1.2 Quick Checklist

Before creating/updating a PR:

- [ ] Gate 1: `pre-commit run --all-files` passes (all hooks pass)
- [ ] Push changes: `git push origin feature-branch`
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Claude review shows LGTM
- [ ] Ready to merge!

### 1.3 Anti-Patterns (DO NOT DO)

❌ **Don't** request review with failing CI
❌ **Don't** skip local checks (`git commit --no-verify`)
❌ **Don't** lower quality thresholds to pass
❌ **Don't** ignore Claude feedback
❌ **Don't** merge without LGTM

**For complete workflow documentation, see**: `/reference/workflows/stay-green.md`

---

## 2. Feature Development Process

### 2.1 Development Steps

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/<issue-number>-<description>
   # Example: feature/6-claude-md-configuration
   ```

2. **Implement Changes**
   - Follow the coding standards in [tools.md](tools.md)
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

### 2.2 Branch Strategy

- `main`: Production-ready code, always deployable
- `feature/*`: Feature development (created from main)
- `bugfix/*`: Bug fixes (created from main)
- `hotfix/*`: Emergency production fixes (created from main)

---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Quality Standards](quality-standards.md) | [Testing →](testing.md)
