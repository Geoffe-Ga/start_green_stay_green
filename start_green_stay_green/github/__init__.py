"""GitHub integration for repository and issue management.

Exports:
- GitHubClient: Main GitHub API client
- GitHubError: Base exception for GitHub API errors
- GitHubAuthError: Authentication/authorization errors
- BranchProtectionRule: Branch protection configuration
- IssueData: Parsed issue data structure
"""

from start_green_stay_green.github.client import BranchProtectionRule
from start_green_stay_green.github.client import GitHubAuthError
from start_green_stay_green.github.client import GitHubClient
from start_green_stay_green.github.client import GitHubError
from start_green_stay_green.github.client import IssueData

__all__ = [
    "BranchProtectionRule",
    "GitHubAuthError",
    "GitHubClient",
    "GitHubError",
    "IssueData",
]
