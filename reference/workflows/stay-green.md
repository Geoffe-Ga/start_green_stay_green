# Stay Green Workflow

**Version**: 1.0
**Last Updated**: 2026-01-13
**Status**: Canonical Specification (Single Source of Truth)

---

## Philosophy

**Start Green, Stay Green**: Never request review with failing checks. Never merge without LGTM.

This workflow enforces iterative quality improvement through sequential gates, preventing premature reviews and ensuring maximum quality at every stage.

---

## The Three Gates

### Gate 1: Local Pre-Commit (Iterate Until Green)

**Purpose**: Catch all quality issues before pushing to remote.

**Actions**:
```bash
# Run ALL 32 quality hooks
pre-commit run --all-files
```

**Checks** (32 hooks total):
- Git checks (large files, merge conflicts, etc.)
- Formatting (ruff, black, isort)
- Linting (ruff, pylint)
- Type checking (mypy strict mode)
- Security (bandit, secrets detection)
- Complexity (≤10 cyclomatic, grade A)
- Unit tests (pytest)
- Coverage (90% minimum)
- Docstrings (95% minimum)
- Code modernization (pyupgrade, autoflake, refurb)
- Exception handling (tryceratops)
- Dead code detection (vulture)
- Shell linting (shellcheck)

**Iteration**:
- If ANY hook fails → Fix locally (many issues auto-fixed by pre-commit)
- Run `pre-commit run --all-files` again
- Repeat until ALL hooks pass

**Proceed When**: `pre-commit run --all-files` shows all hooks passing

---

### Gate 2: CI Pipeline (Iterate Until Green)

**Purpose**: Verify checks pass in clean CI environment.

**Actions**:
```bash
git push origin feature/your-branch
# Watch CI status
gh pr checks --watch
```

**CI Jobs**:
- `quality` - Linting, formatting, types, security, complexity
- `test (3.11)` - Unit + integration tests on Python 3.11
- `test (3.12)` - Unit + integration tests on Python 3.12

**Iteration**:
- Push to branch
- Monitor CI via GitHub UI or `gh pr checks`
- If CI fails:
  1. Pull latest changes: `git pull origin feature/your-branch`
  2. Fix issues locally
  3. Run Gate 1 (`pre-commit run --all-files`) again
  4. Push again
  5. Wait for CI
- Repeat until CI is GREEN

**Proceed When**: All CI jobs show ✅ (passing)

---

### Gate 3: Claude Code Review (Iterate Until LGTM)

**Purpose**: AI-assisted code review for architecture, patterns, and quality.

**Actions**:
```bash
# Wait for Claude code review CI job
gh pr checks --watch

# If no Claude review appears, request manually:
# Add comment: "@claude-code please review"
```

**Review Criteria**:
- Architecture adherence
- Code patterns and best practices
- MAXIMUM QUALITY compliance
- Documentation completeness
- Test coverage adequacy

**Iteration**:
- Wait for Claude code review job to comment
- If feedback provided:
  1. Address ALL concerns in the review
  2. Fix issues locally
  3. Run Gate 1 (check-all.sh) again
  4. Push to branch
  5. Wait for Gate 2 (CI) to pass
  6. Wait for new Claude review
- Use polling/sleep to wait for CI jobs:
  ```bash
  # Wait for CI to complete
  gh pr checks --watch

  # Check review status
  gh pr view --json reviews
  ```
- Repeat until Claude provides LGTM with NO reservations

**Proceed When**: Claude review shows "LGTM" or "Approved" with no open concerns

---

### Mutation Testing (Periodic Quality Check)

**Note**: Mutation testing (≥80% score) is **recommended as a periodic quality check** for critical infrastructure, not enforced continuously.

**When to Run**:
- Before major releases
- For critical infrastructure (billing, authentication, core algorithms)
- Quarterly quality audits
- When test effectiveness is in question

**How to Run**:
```bash
# Target specific critical files
./scripts/mutation.sh --paths-to-mutate path/to/critical/file.py

# Check mutation score
python scripts/analyze_mutations.py critical-file.py
```

**Why Periodic**: Mutation testing provides valuable insights but takes 20-30 minutes per run. Running it continuously was breaking developer flow state. The new approach maintains quality through comprehensive test coverage (≥90%) while using mutation testing strategically for highest-risk code.

---

## Complete Workflow Pseudocode

```python
def stay_green_workflow():
    """Complete Stay Green workflow."""

    # Gate 1: Local Pre-Commit
    while not local_checks_pass():
        run("pre-commit run --all-files")  # Auto-fixes many issues
        fix_remaining_issues_manually()  # Fix mypy errors, add tests, etc.
        run("pre-commit run --all-files")

    # Push to remote
    git("push origin feature-branch")

    # Gate 2: CI Pipeline
    while not ci_checks_pass():
        wait_for_ci_completion()
        if ci_failed():
            git("pull origin feature-branch")
            fix_ci_failures_locally()
            # Re-run Gate 1
            run("pre-commit run --all-files")
            git("push origin feature-branch")

    # Gate 3: Claude Code Review
    while not claude_approved():
        wait_for_claude_review()
        if has_feedback():
            address_all_concerns()
            # Re-run Gate 1
            run("pre-commit run --all-files")
            git("push origin feature-branch")
            # Re-run Gate 2
            wait_for_ci_completion()

    # All gates passed!
    merge_pr()
```

---

## Visual Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                       STAY GREEN WORKFLOW                            │
│                     (Iterate Until All Pass)                         │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  Make Changes    │
│  Write Tests     │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────┐
│ GATE 1: Local Pre-Commit                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ./scripts/check-all.sh                                       │ │
│ │  • Formatting (ruff, black, isort)                          │ │
│ │  • Linting (ruff, pylint, mypy)                            │ │
│ │  • Security (bandit, safety)                               │ │
│ │  • Complexity (≤10, grade A)                               │ │
│ │  • Tests + Coverage (90%+)                                 │ │
│ └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         │ PASS (exit 0)                                           │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ▼
     git push
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│ GATE 2: CI Pipeline                                              │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ GitHub Actions                                               │ │
│ │  • quality (lint, format, types, security, complexity)      │ │
│ │  • test (3.11) (unit + integration)                        │ │
│ │  • test (3.12) (unit + integration)                        │ │
│ └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         │ PASS (all ✅)                                            │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│ GATE 3: Mutation Testing                                         │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ./scripts/mutation.sh (local or CI)                         │ │
│ │  • Score ≥ 80% required                                     │ │
│ │  • Kills 80% of mutants                                     │ │
│ │  • Validates test effectiveness                            │ │
│ └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         │ PASS (≥80%)                                              │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│ GATE 4: Claude Code Review                                       │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ AI Code Review                                               │ │
│ │  • Architecture adherence                                   │ │
│ │  • Code patterns and best practices                        │ │
│ │  • MAXIMUM QUALITY compliance                              │ │
│ │  • Documentation completeness                              │ │
│ └──────────────────────────────────────────────────────────────┘ │
│         │                                                          │
│         │ LGTM                                                     │
└─────────┼──────────────────────────────────────────────────────────┘
          │
          ▼
     ┌─────────┐
     │  MERGE  │
     └─────────┘

         ┌─────────────────┐
         │  Fix Issues     │◀────────────┐
         │  Locally        │             │
         └────────┬────────┘             │
                  │                      │
                  └──────────────────────┘
                    (Loop back to Gate 1)
```

---

## Quality Thresholds

| Metric | Threshold | Gate | Tool |
|--------|-----------|------|------|
| **Code Coverage** | ≥ 90% | Gate 1, Gate 2 | pytest --cov |
| **Docstring Coverage** | ≥ 95% | Gate 1, Gate 2 | interrogate |
| **Cyclomatic Complexity** | ≤ 10 per function | Gate 1, Gate 2 | radon cc |
| **Maintainability Index** | ≥ 20 | Gate 1, Gate 2 | radon mi |
| **Complexity Grade** | A (1-5) | Gate 1, Gate 2 | xenon |
| **Pylint Score** | ≥ 9.0 | Gate 1, Gate 2 | pylint |
| **Type Checking** | Strict, 0 errors | Gate 1, Gate 2 | mypy |
| **Security Issues** | 0 | Gate 1, Gate 2 | bandit, safety |
| **Mutation Score** | ≥ 80% (periodic) | Recommended for critical code | mutmut |
| **Claude Review** | LGTM | Gate 3 | AI review |

---

## Common Failure Scenarios and Fixes

### Gate 1 Failures

**Formatting Issues**:
```bash
# Auto-fix
./scripts/format.sh
./scripts/check-all.sh
```

**Linting Issues**:
```bash
# Auto-fix what's possible
./scripts/fix-all.sh
# Manually fix remaining issues (mypy errors, design issues)
./scripts/check-all.sh
```

**Coverage < 90%**:
```bash
# Identify missing coverage
./scripts/test.sh
# Add tests for uncovered lines
# Re-run check-all.sh
```

**Complexity > 10**:
```bash
# Refactor complex functions
# Extract helper methods
# Simplify branching logic
./scripts/complexity.sh
```

### Gate 2 Failures

**CI failing but local passing**:
```bash
# Pull latest changes
git pull origin feature-branch
# Check for dependency issues
pip install -e ".[dev]"
# Re-run local checks
./scripts/check-all.sh
```

**Merge conflicts**:
```bash
# Update from main
git fetch origin main
git merge origin/main
# Resolve conflicts
# Re-run local checks
./scripts/check-all.sh
git push origin feature-branch
```

### Gate 3 Failures

**Claude requests changes**:
```bash
# Address ALL concerns in review
# Don't skip any feedback
# Re-run Gate 1
./scripts/check-all.sh
git push origin feature-branch
# Wait for new review
gh pr checks --watch
```

---

## Waiting and Polling Strategies

### Wait for CI Completion

```bash
# Option 1: GitHub CLI (recommended)
gh pr checks --watch

# Option 2: Manual polling
while true; do
  gh pr view --json statusCheckRollup | jq '.statusCheckRollup'
  sleep 30
done

# Option 3: GitHub UI
# Visit PR page and monitor status checks
```

### Wait for Claude Review

```bash
# Check for review comments
gh pr view --json reviews | jq '.reviews'

# Check for review comments periodically
while ! gh pr view --json reviews | jq -e '.reviews[] | select(.state == "APPROVED")'; do
  echo "Waiting for Claude review..."
  sleep 60
done
```

---

## Branch Protection Configuration

### Required Status Checks

Configure via GitHub API or UI:

**Required Checks**:
- `CI / quality`
- `CI / test (3.11)`
- `CI / test (3.12)`

**Optional Checks** (if available):
- `CI / mutation` (main branch only)
- `Claude Code Review / claude-review`

### Configuration Script

Use `scripts/configure-branch-protection.sh`:

```bash
# Dry-run (show what would be configured)
./scripts/configure-branch-protection.sh --dry-run

# Apply configuration
./scripts/configure-branch-protection.sh --apply

# Configuration includes:
# - Required status checks
# - Require branches up to date
# - Require linear history
# - Require at least 1 review approval
```

---

## Anti-Patterns (DO NOT DO)

### ❌ Premature Review Requests

```bash
# WRONG: Requesting review with failing CI
git push origin feature-branch
gh pr create  # ← CI is still running/failing!
```

**Correct**:
```bash
git push origin feature-branch
gh pr checks --watch  # Wait for CI to pass
# Only create PR AFTER CI is green
gh pr create
```

### ❌ Bypassing Local Checks

```bash
# WRONG: Skipping local checks
git commit -m "quick fix" --no-verify
git push
```

**Correct**:
```bash
./scripts/check-all.sh  # ALWAYS run before commit
git commit -m "fix: correct validation logic (#123)"
git push
```

### ❌ Ignoring Claude Feedback

```bash
# WRONG: Merging despite Claude review concerns
# Claude: "Please add error handling for edge case X"
# Developer: *merges anyway*
```

**Correct**:
```bash
# Address ALL Claude feedback
# Add error handling for edge case X
./scripts/check-all.sh
git push
# Wait for new Claude review showing approval
```

### ❌ Lowering Thresholds to Pass

```toml
# WRONG: Reducing standards to pass checks
[tool.coverage.report]
fail_under = 70  # ← Reduced from 90 to make it pass
```

**Correct**:
```bash
# Add tests to reach 90% coverage
# Meet the standards, don't lower them
```

---

## Integration with Tools

### Pre-Commit Hooks

Gate 1 can be enforced with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-all
        name: Run all quality checks
        entry: ./scripts/check-all.sh
        language: system
        pass_filenames: false
        always_run: true
```

### Git Aliases

Add helpful aliases:

```bash
# .gitconfig or run:
git config alias.check '!./scripts/check-all.sh'
git config alias.fix '!./scripts/fix-all.sh'

# Usage:
git check  # Run all checks
git fix    # Auto-fix issues
```

### Editor Integration

Configure editor to run checks on save:

**VS Code** (`.vscode/settings.json`):
```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": "\\.py$",
        "cmd": "./scripts/format.sh ${file}"
      }
    ]
  }
}
```

---

## Success Criteria

The Stay Green workflow is being followed correctly when:

1. ✅ **No PR** has failing CI at review time
2. ✅ **All commits** pass `./scripts/check-all.sh` before push
3. ✅ **Mutation scores** are ≥ 80% on all merges
4. ✅ **Claude reviews** show LGTM before merge
5. ✅ **Main branch** stays green 100% of time
6. ✅ **Generated repos** inherit this workflow automatically

---

## Quick Reference Checklist

Before creating/updating a PR:

- [ ] Gate 1: `pre-commit run --all-files` passes (all hooks pass)
- [ ] Push changes: `git push origin feature-branch`
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Claude review shows LGTM
- [ ] Ready to merge!

**Optional**: Run mutation testing on critical code: `./scripts/mutation.sh --paths-to-mutate <files>`

---

## Related Documentation

- [MAXIMUM_QUALITY_ENGINEERING.md](../MAXIMUM_QUALITY_ENGINEERING.md) - Quality framework
- [CLAUDE.md](../../CLAUDE.md) - Project context for Claude Code
- [Quality Scripts](../../scripts/) - Implementation of quality checks

---

**This document is the single source of truth for the Stay Green workflow. All other documentation references this specification.**
