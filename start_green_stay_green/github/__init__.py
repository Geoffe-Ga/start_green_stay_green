"""GitHub integration for repository and issue management.

Provides GitHub API integration for creating repositories, managing
issues, milestones, labels, and GitHub Actions workflows.
"""

from start_green_stay_green.github.actions import GitHubActionsError
from start_green_stay_green.github.actions import GitHubActionsManager
from start_green_stay_green.github.actions import WorkflowConfig
from start_green_stay_green.github.client import GitHubClient
from start_green_stay_green.github.client import GitHubError
from start_green_stay_green.github.client import RepositoryConfig
from start_green_stay_green.github.issues import GitHubIssueError
from start_green_stay_green.github.issues import GitHubIssueManager
from start_green_stay_green.github.issues import IssueConfig
from start_green_stay_green.github.issues import MilestoneConfig

__all__ = [
    "GitHubActionsError",
    "GitHubActionsManager",
    "GitHubClient",
    "GitHubError",
    "GitHubIssueError",
    "GitHubIssueManager",
    "IssueConfig",
    "MilestoneConfig",
    "RepositoryConfig",
    "WorkflowConfig",
]
