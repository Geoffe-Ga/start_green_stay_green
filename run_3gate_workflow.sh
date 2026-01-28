#!/usr/bin/env bash
#
# 3-Gate Workflow Automation Script
# Issue #132: Tool Configuration Auditor
# Branch: feature/tool-config-auditor
#
# This script executes the complete 3-gate workflow:
# - Gate 1: Local pre-commit checks
# - Gate 2: Commit, push, and CI monitoring
# - Gate 3: PR creation and review
#

set -euo pipefail

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (worktree root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}3-Gate Workflow: Tool Config Auditor${NC}"
echo -e "${BLUE}Issue #132${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verify we're in the correct worktree
if [[ ! -f "IMPLEMENTATION_STATUS.md" ]]; then
    echo -e "${RED}ERROR: Not in tool-auditor worktree${NC}"
    echo "Expected: /Users/geoffgallinger/Projects/sgsg-worktrees/tool-auditor"
    echo "Current:  $(pwd)"
    exit 1
fi

echo -e "${GREEN}✅ Worktree verified${NC}"
echo ""

#
# GATE 1: Local Quality Checks
#
echo -e "${YELLOW}=== GATE 1: Local Quality Checks ===${NC}"
echo ""

# Check git status
echo "Current git status:"
git status --short
echo ""

# Run pre-commit checks
echo -e "${BLUE}Running pre-commit on all files...${NC}"
echo "This will run all 32 hooks (formatting, linting, tests, coverage, etc.)"
echo ""

if pre-commit run --all-files; then
    echo ""
    echo -e "${GREEN}✅ GATE 1 PASSED: All pre-commit hooks passed!${NC}"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠️  Some hooks failed or fixed issues${NC}"
    echo ""
    echo "Common auto-fixes applied by hooks:"
    echo "  - Trailing whitespace removed"
    echo "  - End-of-file fixes"
    echo "  - Import sorting (isort)"
    echo "  - Code formatting (black)"
    echo ""
    echo "Re-running pre-commit to verify fixes..."
    echo ""

    if pre-commit run --all-files; then
        echo ""
        echo -e "${GREEN}✅ GATE 1 PASSED: All hooks now pass after auto-fixes!${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ GATE 1 FAILED: Manual fixes required${NC}"
        echo ""
        echo "Please review the errors above and fix manually."
        echo "Common issues requiring manual fixes:"
        echo "  - Line length violations (split long lines)"
        echo "  - Missing docstrings (add documentation)"
        echo "  - Type hint coverage (add type annotations)"
        echo "  - Test coverage < 90% (add more tests)"
        echo "  - Complexity > 10 (refactor complex functions)"
        echo ""
        echo "After fixing, run this script again."
        exit 1
    fi
fi

#
# GATE 2: Commit and Push
#
echo -e "${YELLOW}=== GATE 2: Commit and Push ===${NC}"
echo ""

# Verify all changes are ready to commit
echo "Files to be committed:"
git status --short
echo ""

read -p "Proceed with commit and push? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted by user"
    exit 0
fi

# Stage all changes
echo "Staging all changes..."
git add .

# Commit with prepared message
echo "Committing with message from COMMIT_MESSAGE.txt..."
git commit -F COMMIT_MESSAGE.txt

echo -e "${GREEN}✅ Changes committed${NC}"
echo ""

# Push to remote
echo "Pushing to remote branch..."
BRANCH=$(git branch --show-current)
echo "Branch: $BRANCH"

git push origin "$BRANCH"

echo -e "${GREEN}✅ Changes pushed to remote${NC}"
echo ""

#
# Create PR if not exists
#
echo "Checking if PR exists..."
if gh pr view &>/dev/null; then
    echo -e "${GREEN}✅ PR already exists${NC}"
    PR_URL=$(gh pr view --json url --jq '.url')
    echo "PR URL: $PR_URL"
else
    echo "Creating pull request..."
    gh pr create \
        --title "feat(audit): implement tool configuration auditor (#132)" \
        --body-file IMPLEMENTATION_STATUS.md \
        --assignee @me

    echo -e "${GREEN}✅ PR created${NC}"
    PR_URL=$(gh pr view --json url --jq '.url')
    echo "PR URL: $PR_URL"
fi

echo ""

#
# Monitor CI
#
echo -e "${YELLOW}=== Monitoring CI Pipeline ===${NC}"
echo ""

echo "Watching CI checks..."
echo "Press Ctrl+C to stop watching (CI will continue)"
echo ""

if gh pr checks --watch; then
    echo ""
    echo -e "${GREEN}✅ GATE 2 PASSED: All CI checks passed!${NC}"
    echo ""
else
    echo ""
    echo -e "${RED}❌ GATE 2 FAILED: Some CI checks failed${NC}"
    echo ""
    echo "View details:"
    echo "  gh pr checks"
    echo "  gh pr view --web"
    echo ""
    exit 1
fi

#
# GATE 3: Code Review
#
echo -e "${YELLOW}=== GATE 3: Code Review ===${NC}"
echo ""

echo "PR is ready for review!"
echo ""
echo "Next steps:"
echo "  1. Review PR at: $PR_URL"
echo "  2. Address any review feedback"
echo "  3. Wait for LGTM (Looks Good To Me)"
echo "  4. Merge when approved"
echo ""

echo "To merge when approved:"
echo "  gh pr merge --squash --delete-branch"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Workflow automation complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Status:"
echo "  ✅ Gate 1: Local checks passed"
echo "  ✅ Gate 2: CI pipeline passed"
echo "  ⏳ Gate 3: Awaiting code review"
echo ""
