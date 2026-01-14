# Stay Green Skill

**Skill Name**: `stay-green`
**Purpose**: Guide AI agents through the Stay Green workflow's 4 iterative quality gates
**Canonical Reference**: `/reference/workflows/stay-green.md`

---

## Quick Reference

When working on code changes, follow these 4 gates in sequence:

### Gate 1: Local Pre-Commit ✅

```bash
./scripts/check-all.sh
```

**If fails**:
- Run `./scripts/fix-all.sh` for auto-fixes
- Manually fix remaining issues
- Re-run `./scripts/check-all.sh`
- Repeat until exit code 0

### Gate 2: CI Pipeline ✅

```bash
git push origin feature-branch
gh pr checks --watch
```

**If fails**:
- Pull latest changes
- Fix issues locally
- Re-run Gate 1
- Push again
- Wait for CI

### Gate 3: Mutation Testing ✅

```bash
./scripts/mutation.sh  # Or wait for CI job
```

**If score < 80%**:
- Review surviving mutants: `mutmut results`
- Add tests to kill mutants
- Re-run Gate 1
- Push and wait for CI
- Check mutation score again

### Gate 4: Claude Code Review ✅

```bash
gh pr checks --watch
# Wait for Claude review comment
```

**If has feedback**:
- Address ALL concerns
- Re-run Gate 1
- Push and wait for CI
- Wait for new review
- Repeat until LGTM

---

## Common Fixes

### Formatting Issues
```bash
./scripts/format.sh
./scripts/check-all.sh
```

### Coverage < 90%
```bash
# Identify gaps
./scripts/test.sh

# Add tests for uncovered code
# Re-run check-all.sh
```

### Complexity > 10
```bash
# Refactor complex functions
# Extract helper methods
# Simplify branching

./scripts/complexity.sh
```

### Mutation Score < 80%
```bash
# View surviving mutants
mutmut results
mutmut html

# Add tests for:
# - Boundary conditions
# - Error paths
# - Edge cases

./scripts/test.sh
./scripts/mutation.sh
```

---

## Anti-Patterns (Avoid)

❌ **Don't** request review with failing CI
❌ **Don't** skip local checks (`--no-verify`)
❌ **Don't** lower quality thresholds to pass
❌ **Don't** ignore Claude feedback
❌ **Don't** merge without LGTM

---

## Complete Workflow

```python
# Pseudocode for AI agents
def implement_feature():
    # Make changes
    edit_code()
    write_tests()

    # Gate 1: Local checks
    while not run("./scripts/check-all.sh").success:
        run("./scripts/fix-all.sh")
        fix_remaining_issues()

    # Push
    run("git push origin feature-branch")

    # Gate 2: CI
    while not ci_passing():
        wait_for_ci()
        if ci_failed():
            pull_changes()
            fix_failures()
            # Back to Gate 1
            run("./scripts/check-all.sh")
            run("git push")

    # Gate 3: Mutation
    while mutation_score() < 80:
        add_tests_to_kill_mutants()
        # Back to Gate 1
        run("./scripts/check-all.sh")
        run("git push")
        wait_for_ci()

    # Gate 4: Review
    while not claude_approved():
        wait_for_review()
        address_feedback()
        # Back to Gate 1
        run("./scripts/check-all.sh")
        run("git push")
        wait_for_ci()

    # Merge!
    merge_pr()
```

---

## Thresholds

| Check | Minimum | Tool |
|-------|---------|------|
| Coverage | 90% | pytest --cov |
| Docstrings | 95% | interrogate |
| Complexity | ≤10 | radon, xenon |
| Pylint | 9.0+ | pylint |
| Mutation | 80% | mutmut |

---

## Helpful Commands

```bash
# Run all checks
./scripts/check-all.sh

# Auto-fix issues
./scripts/fix-all.sh

# Run tests
./scripts/test.sh

# Check mutation score
./scripts/mutation.sh

# Watch CI status
gh pr checks --watch

# View PR reviews
gh pr view --json reviews
```

---

**Always iterate through gates sequentially. Never skip ahead. Stay Green!**
