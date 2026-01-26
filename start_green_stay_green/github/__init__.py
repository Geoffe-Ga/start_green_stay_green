"""GitHub integration for repository and issue management.

Exports:
- GitHubClient: Main GitHub API client
- GitHubError: Base exception for GitHub API errors
- GitHubAuthError: Authentication/authorization errors
- BranchProtectionRule: Branch protection configuration
- IssueData: Parsed issue data structure
"""

from start_green_stay_green.github.client import (
    BranchProtectionRule,
    GitHubAuthError,
    GitHubClient,
    GitHubError,
    IssueData,
)

__all__ = [
    "GitHubClient",
    "GitHubError",
    "GitHubAuthError",
    "BranchProtectionRule",
    "IssueData",
]
