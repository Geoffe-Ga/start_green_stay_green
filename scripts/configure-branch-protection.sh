#!/usr/bin/env bash
# scripts/configure-branch-protection.sh - Configure GitHub branch protection for Stay Green workflow
# Usage: ./scripts/configure-branch-protection.sh [--dry-run] [--apply] [--help]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DRY_RUN=true
BRANCH="main"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --apply)
            DRY_RUN=false
            shift
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Usage: $(basename "$0") [OPTIONS]

Configure GitHub branch protection rules to enforce Stay Green workflow.

OPTIONS:
    --dry-run      Show what would be configured (default)
    --apply        Actually apply the configuration
    --branch NAME  Branch to protect (default: main)
    --help         Display this help message

BRANCH PROTECTION RULES:
    • Required status checks:
        - CI / quality
        - CI / test (3.11)
        - CI / test (3.12)
    • Require branches to be up to date before merging
    • Require linear history (no merge commits)
    • Require at least 1 review approval
    • Enforce for administrators

EXAMPLES:
    $(basename "$0") --dry-run           # Show configuration (default)
    $(basename "$0") --apply             # Apply to main branch
    $(basename "$0") --apply --branch dev  # Apply to dev branch

PREREQUISITES:
    • GitHub CLI (gh) installed
    • Authenticated with sufficient permissions
    • Repository owner or admin access

EOF
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

cd "$PROJECT_ROOT"

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) not installed" >&2
    echo "Install from: https://cli.github.com/" >&2
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI" >&2
    echo "Run: gh auth login" >&2
    exit 1
fi

# Get repository information
REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner')
OWNER=$(echo "$REPO" | cut -d'/' -f1)
REPO_NAME=$(echo "$REPO" | cut -d'/' -f2)

echo "=== GitHub Branch Protection Configuration ==="
echo ""
echo "Repository: $REPO"
echo "Branch: $BRANCH"
echo "Mode: $([ "$DRY_RUN" = true ] && echo "DRY RUN" || echo "APPLY")"
echo ""

# Branch protection configuration
PROTECTION_CONFIG=$(cat <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI / quality",
      "CI / test (3.11)",
      "CI / test (3.12)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "restrictions": null
}
EOF
)

echo "Configuration to apply:"
echo "$PROTECTION_CONFIG" | jq '.'
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "ℹ DRY RUN MODE - No changes will be made"
    echo ""
    echo "This would configure the following rules:"
    echo "  ✓ Required status checks:"
    echo "    - CI / quality"
    echo "    - CI / test (3.11)"
    echo "    - CI / test (3.12)"
    echo "  ✓ Require branches up to date before merging"
    echo "  ✓ Require linear history (no merge commits)"
    echo "  ✓ Require 1 review approval"
    echo "  ✓ Dismiss stale reviews on new commits"
    echo "  ✓ Enforce for administrators"
    echo "  ✓ Prevent force pushes"
    echo "  ✓ Prevent branch deletion"
    echo ""
    echo "To apply this configuration, run:"
    echo "  $0 --apply"
    echo ""
    exit 0
fi

echo "Applying branch protection rules..."
echo ""

# Apply branch protection using GitHub API
if gh api \
    -X PUT \
    "repos/$OWNER/$REPO_NAME/branches/$BRANCH/protection" \
    --input - <<< "$PROTECTION_CONFIG" \
    > /dev/null 2>&1; then
    echo "✓ Branch protection rules applied successfully"
    echo ""
    echo "Configured rules:"
    echo "  ✓ Required status checks: CI / quality, CI / test (3.11), CI / test (3.12)"
    echo "  ✓ Require branches up to date: enabled"
    echo "  ✓ Require linear history: enabled"
    echo "  ✓ Require 1 review approval: enabled"
    echo "  ✓ Enforce for administrators: enabled"
    echo ""
    echo "Verify at: https://github.com/$OWNER/$REPO_NAME/settings/branches"
else
    echo "✗ Failed to apply branch protection rules" >&2
    echo "" >&2
    echo "Possible causes:" >&2
    echo "  • Insufficient permissions (requires admin access)" >&2
    echo "  • Branch '$BRANCH' does not exist" >&2
    echo "  • Required status checks do not exist yet" >&2
    echo "" >&2
    echo "To check current protection:" >&2
    echo "  gh api repos/$OWNER/$REPO_NAME/branches/$BRANCH/protection" >&2
    exit 1
fi

exit 0
