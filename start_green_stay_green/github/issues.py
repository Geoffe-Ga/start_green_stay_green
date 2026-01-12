"""GitHub issue and epic creation.

Creates issues, epics (milestones), and manages labels
via GitHub API. Supports parsing specifications and bulk issue creation.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_BAD_REQUEST = 400

# Error messages
_ERR_EMPTY_ISSUE_TITLE = "Issue title cannot be empty"
_ERR_EMPTY_MILESTONE_TITLE = "Milestone title cannot be empty"
_ERR_EMPTY_TOKEN = "Token cannot be empty"  # nosec B105  # noqa: S105
_ERR_CREATE_ISSUE_FAILED = "Failed to create issue"
_ERR_GET_ISSUE_FAILED = "Failed to get issue"
_ERR_LIST_ISSUES_FAILED = "Failed to list issues"
_ERR_CREATE_MILESTONE_FAILED = "Failed to create milestone"
_ERR_GET_MILESTONE_FAILED = "Failed to get milestone"
_ERR_LIST_MILESTONES_FAILED = "Failed to list milestones"
_ERR_CREATE_LABEL_FAILED = "Failed to create label"
_ERR_LIST_LABELS_FAILED = "Failed to list labels"


class GitHubIssueError(Exception):
    """Raised when GitHub Issues API operation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        """Initialize GitHubIssueError.

        Args:
            message: Error message describing the failure.
            status_code: Optional HTTP status code from API response.
        """
        super().__init__(message)
        self.status_code = status_code


@dataclass
class IssueConfig:
    """Configuration for issue creation.

    Attributes:
        title: Issue title (required).
        body: Issue description/body (required).
        labels: List of label names to apply (optional).
        milestone: Milestone number to associate (optional).
        assignees: List of usernames to assign (optional).
    """

    title: str
    body: str
    labels: list[str] | None = None
    milestone: int | None = None
    assignees: list[str] | None = None

    def __post_init__(self) -> None:
        """Validate issue configuration.

        Raises:
            ValueError: If required fields are empty or invalid.
        """
        if not self.title or not self.title.strip():
            raise ValueError(_ERR_EMPTY_ISSUE_TITLE)


@dataclass
class MilestoneConfig:
    """Configuration for milestone (epic) creation.

    Attributes:
        title: Milestone title (required).
        description: Milestone description (optional).
        due_date: Due date in YYYY-MM-DD format (optional).
    """

    title: str
    description: str | None = None
    due_date: str | None = None

    def __post_init__(self) -> None:
        """Validate milestone configuration.

        Raises:
            ValueError: If title is empty or invalid.
        """
        if not self.title or not self.title.strip():
            raise ValueError(_ERR_EMPTY_MILESTONE_TITLE)


class GitHubIssueManager:
    """GitHub issue and milestone manager.

    Provides methods for managing GitHub issues, milestones (epics),
    and labels. Supports creating issues from specifications and
    bulk operations.

    Attributes:
        token: GitHub personal access token for authentication.
        base_url: GitHub API base URL (default: https://api.github.com).
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
    ) -> None:
        """Initialize GitHubIssueManager.

        Args:
            token: GitHub personal access token. Cannot be empty.
            base_url: Base URL for GitHub API. Defaults to GitHub.com API.

        Raises:
            ValueError: If token is empty or contains only whitespace.
        """
        if not token or not token.strip():
            raise ValueError(_ERR_EMPTY_TOKEN)

        self.token = token
        self.base_url = base_url

    def create_issue(
        self,
        owner: str,
        repo: str,
        issue: IssueConfig,
    ) -> dict[str, Any]:
        """Create a new GitHub issue.

        Creates a new issue in the specified repository with the
        provided configuration.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue: Issue configuration.

        Returns:
            Dictionary containing created issue information.

        Raises:
            GitHubIssueError: If issue creation fails.

        Examples:
            >>> manager = GitHubIssueManager(token="ghp_...")
            >>> issue = IssueConfig(
            ...     title="Bug: Login fails",
            ...     body="User cannot log in with email",
            ...     labels=["type: bug", "priority: high"],
            ... )
            >>> result = manager.create_issue("myorg", "my-repo", issue)
            >>> print(result["number"])
        """
        try:
            payload = {
                "title": issue.title,
                "body": issue.body,
            }

            if issue.labels:
                payload["labels"] = issue.labels
            if issue.milestone is not None:
                payload["milestone"] = issue.milestone
            if issue.assignees:
                payload["assignees"] = issue.assignees

            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/repos/{owner}/{repo}/issues",
                    headers=self._get_headers(),
                    json=payload,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_CREATE_ISSUE_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def get_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict[str, Any]:
        """Get information about a specific issue.

        Retrieves metadata for an issue including comments, labels,
        and assignees.

        Args:
            owner: Repository owner.
            repo: Repository name.
            issue_number: Issue number.

        Returns:
            Dictionary containing issue information.

        Raises:
            GitHubIssueError: If issue cannot be found.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_ISSUE_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def list_issues(
        self,
        owner: str,
        repo: str,
        *,
        state: str = "open",
        labels: list[str] | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """List issues in a repository.

        Retrieves issues from a repository with optional filtering
        by state and labels.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Issue state (open, closed, all). Defaults to "open".
            labels: Optional list of label names to filter by.
            limit: Maximum number of issues to return. Defaults to 30.

        Returns:
            List of issue dictionaries.

        Raises:
            GitHubIssueError: If issues cannot be retrieved.
        """
        try:
            params = {
                "state": state,
                "per_page": limit,
            }
            if labels:
                params["labels"] = ",".join(labels)

            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/issues",
                    headers=self._get_headers(),
                    params=params,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_LIST_ISSUES_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def create_milestone(
        self,
        owner: str,
        repo: str,
        milestone: MilestoneConfig,
    ) -> dict[str, Any]:
        """Create a new milestone (epic).

        Creates a new milestone in the repository. Milestones are used
        to group related issues and track progress.

        Args:
            owner: Repository owner.
            repo: Repository name.
            milestone: Milestone configuration.

        Returns:
            Dictionary containing created milestone information.

        Raises:
            GitHubIssueError: If milestone creation fails.

        Examples:
            >>> manager = GitHubIssueManager(token="ghp_...")
            >>> milestone = MilestoneConfig(
            ...     title="Epic 1: Core Features",
            ...     description="Implement core features",
            ...     due_date="2024-06-30",
            ... )
            >>> result = manager.create_milestone("myorg", "my-repo", milestone)
            >>> print(result["number"])
        """
        try:
            payload = {
                "title": milestone.title,
            }

            if milestone.description:
                payload["description"] = milestone.description
            if milestone.due_date:
                payload["due_on"] = f"{milestone.due_date}T00:00:00Z"

            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/repos/{owner}/{repo}/milestones",
                    headers=self._get_headers(),
                    json=payload,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_CREATE_MILESTONE_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def get_milestone(
        self,
        owner: str,
        repo: str,
        milestone_number: int,
    ) -> dict[str, Any]:
        """Get information about a specific milestone.

        Retrieves metadata for a milestone including progress and due date.

        Args:
            owner: Repository owner.
            repo: Repository name.
            milestone_number: Milestone number.

        Returns:
            Dictionary containing milestone information.

        Raises:
            GitHubIssueError: If milestone cannot be found.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/milestones/{milestone_number}",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_MILESTONE_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def list_milestones(
        self,
        owner: str,
        repo: str,
        *,
        state: str = "open",
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """List milestones in a repository.

        Retrieves all milestones from a repository with optional
        state filtering.

        Args:
            owner: Repository owner.
            repo: Repository name.
            state: Milestone state (open, closed, all). Defaults to "open".
            limit: Maximum number of milestones to return. Defaults to 30.

        Returns:
            List of milestone dictionaries.

        Raises:
            GitHubIssueError: If milestones cannot be retrieved.
        """
        try:
            params = {
                "state": state,
                "per_page": limit,
            }

            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/milestones",
                    headers=self._get_headers(),
                    params=params,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_LIST_MILESTONES_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def create_label(
        self,
        owner: str,
        repo: str,
        name: str,
        color: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new label.

        Creates a new label that can be applied to issues and pull requests.

        Args:
            owner: Repository owner.
            repo: Repository name.
            name: Label name.
            color: Label color (6-character hex code, no #).
            description: Optional label description.

        Returns:
            Dictionary containing created label information.

        Raises:
            GitHubIssueError: If label creation fails.

        Examples:
            >>> manager = GitHubIssueManager(token="ghp_...")
            >>> label = manager.create_label(
            ...     owner="myorg",
            ...     repo="my-repo",
            ...     name="type: feature",
            ...     color="0366d6",
            ...     description="Feature request",
            ... )
            >>> print(label["name"])
        """
        try:
            payload = {
                "name": name,
                "color": color,
            }

            if description:
                payload["description"] = description

            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/repos/{owner}/{repo}/labels",
                    headers=self._get_headers(),
                    json=payload,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_CREATE_LABEL_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def list_labels(
        self,
        owner: str,
        repo: str,
        *,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """List all labels in a repository.

        Retrieves all labels that can be applied to issues and
        pull requests in a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            limit: Maximum number of labels to return. Defaults to 30.

        Returns:
            List of label dictionaries.

        Raises:
            GitHubIssueError: If labels cannot be retrieved.
        """
        try:
            params = {"per_page": limit}

            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/labels",
                    headers=self._get_headers(),
                    params=params,
                )
                self._check_response(response)
                return response.json()
        except GitHubIssueError:
            raise
        except Exception as exc:
            msg = f"{_ERR_LIST_LABELS_FAILED}: {exc}"
            raise GitHubIssueError(msg) from exc

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for GitHub API requests.

        Returns:
            Dictionary containing authorization and content-type headers.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }

    def _check_response(self, response: httpx.Response) -> None:
        """Check API response status and raise errors if needed.

        Args:
            response: HTTP response object.

        Raises:
            GitHubIssueError: If response indicates an API error.
        """
        if response.status_code >= HTTP_BAD_REQUEST:
            try:
                error_data = response.json()
                message = error_data.get("message", "Unknown error")
            except Exception:  # noqa: BLE001
                message = response.text or "Unknown error"

            raise GitHubIssueError(
                message,
                status_code=response.status_code,
            )
