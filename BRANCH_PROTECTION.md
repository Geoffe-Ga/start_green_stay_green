# Branch Protection Configuration

This document describes how to configure and verify GitHub branch protection rules for the Start Green Stay Green repository.

## Required Protection Rules

The `main` branch must have the following protection rules enabled:

### 1. Require Status Checks Before Merging

**Required checks:**
- `quality` - Linting, formatting, type checking
- `test (3.11)` - Unit tests on Python 3.11
- `test (3.12)` - Unit tests on Python 3.12
- `mutation` - Mutation testing (main branch only)
- `security` - Security scanning
- `coverage` - Coverage reporting

**Settings:**
- ✅ Require branches to be up to date before merging (strict mode)
- ✅ Require status checks to pass before merging

### 2. Require Pull Request Reviews

- ✅ Require at least 1 approving review
- ✅ Dismiss stale reviews when new commits are pushed
- ✅ Require review from Code Owners (optional but recommended)

### 3. Additional Protection

- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings
- ✅ Restrict pushes to specified people/teams (optional)

## Configuration via GitHub CLI

```bash
# Configure branch protection for main branch
gh api repos/Geoffe-Ga/start_green_stay_green/branches/main/protection \
  -X PUT \
  -f required_status_checks='{"strict":true,"contexts":["quality","test (3.11)","test (3.12)","mutation","security","coverage"]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":false,"required_approving_review_count":1}' \
  -f restrictions=null
```

## Configuration via GitHub Web UI

1. **Navigate to Settings:**
   - Go to: https://github.com/Geoffe-Ga/start_green_stay_green/settings/branches
   - Click "Add rule" or edit existing rule for `main`

2. **Branch name pattern:**
   - Enter: `main`

3. **Protect matching branches - Check the following:**
   - ✅ Require a pull request before merging
   - ✅ Require approvals (set to 1)
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - Add required status checks (see list above)
   - ✅ Require conversation resolution before merging
   - ✅ Do not allow bypassing the above settings

4. **Click "Create" or "Save changes"**

## Verification

### Via GitHub CLI

```bash
# View current branch protection settings
gh api repos/Geoffe-Ga/start_green_stay_green/branches/main/protection

# Check if specific protection is enabled
gh api repos/Geoffe-Ga/start_green_stay_green/branches/main/protection/required_status_checks
```

### Via GitHub Web UI

1. Go to: https://github.com/Geoffe-Ga/start_green_stay_green/settings/branches
2. Look for the `main` branch rule
3. Verify all checkboxes match the requirements above
4. Verify all required status checks are listed

### Via Test Push

The safest verification is to attempt a push directly to main (it should be rejected):

```bash
# This should fail if protection is properly configured
git checkout main
git commit --allow-empty -m "test: verify branch protection"
git push origin main
# Expected: remote: error: GH006: Protected branch update failed
```

## Troubleshooting

### Status Check Not Appearing

If a required status check doesn't appear in the dropdown:
1. Ensure the CI workflow has run at least once on a PR
2. The check name must match exactly what appears in CI
3. Wait a few minutes for GitHub to register the check

### Branch Protection Not Enforced

If pushes to main are still allowed:
1. Verify "Do not allow bypassing" is enabled
2. Check if you have admin bypass enabled (disable it)
3. Ensure you're not using a personal access token with admin scope

### Can't Merge PR Despite Passing Checks

1. Verify "Require branches to be up to date" setting
2. Rebase or merge main into your branch
3. Push and wait for checks to pass again

## Updating Branch Protection

When adding new CI jobs that should block merges:

1. Update the `required_status_checks` list in this document
2. Run the GitHub CLI command with updated contexts
3. Or update via web UI by adding the new check name

## References

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub REST API - Branch Protection](https://docs.github.com/en/rest/branches/branch-protection)
- [CLAUDE.md Section 4: Stay Green Workflow](../CLAUDE.md#4-stay-green-workflow)
