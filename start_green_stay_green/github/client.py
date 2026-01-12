"""GitHub API client.

Handles authentication and repository operations via GitHub REST API.
Supports token-based authentication and repository creation, configuration,
and branch protection rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Error messages
_ERR_EMPTY_REPO_NAME = "Repository name cannot be empty"
_ERR_EMPTY_TOKEN = "Token cannot be empty"  # nosec B105  # noqa: S105
_ERR_GET_USER_FAILED = "Failed to get authenticated user"
_ERR_CREATE_REPO_FAILED = "Failed to create repository"
_ERR_GET_REPO_FAILED = "Failed to get repository"
_ERR_SET_PROTECTION_FAILED = "Failed to set branch protection"


class GitHubError(Exception):
    """Raised when GitHub API operation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize GitHubError.

        Args:
            message: Error message describing the failure.
            status_code: Optional HTTP status code from API response.
            response_data: Optional response data from failed API call.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


@dataclass
class RepositoryConfig:
    """Configuration for repository creation.

    Attributes:
        name: Repository name (required, alphanumeric and hyphens).
        description: Repository description (optional).
        is_private: Whether repository is private (default: False).
        include_wiki: Whether to include wiki (default: False).
        include_projects: Whether to include projects (default: False).
        include_discussions: Whether to include discussions (default: False).
    """

    name: str
    description: str | None = None
    is_private: bool = False
    include_wiki: bool = False
    include_projects: bool = False
    include_discussions: bool = False

    def __post_init__(self) -> None:
        """Validate repository configuration.

        Raises:
            ValueError: If name is empty or invalid.
        """
        if not self.name or not self.name.strip():
            raise ValueError(_ERR_EMPTY_REPO_NAME)


class GitHubClient:
    """GitHub API client for repository operations.

    Provides methods for authenticating with GitHub, creating and configuring
    repositories, and managing branch protection rules via the GitHub REST API.

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
        """Initialize GitHubClient.

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

    def verify_token(self) -> bool:
        """Verify that the GitHub token is valid.

        Attempts to authenticate with the GitHub API to verify that
        the provided token has valid credentials.

        Returns:
            True if token is valid, False otherwise.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/user",
                    headers=self._get_headers(),
                )
                return response.status_code == 200
        except Exception as exc:
            logger.error("Error verifying token: %s", exc)
            return False

    def get_authenticated_user(self) -> dict[str, Any]:
        """Get information about the authenticated user.

        Retrieves user profile information for the authenticated account.

        Returns:
            Dictionary containing authenticated user information.

        Raises:
            GitHubError: If API request fails.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/user",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_USER_FAILED}: {exc}"
            raise GitHubError(msg) from exc

    def create_repository(
        self,
        config: RepositoryConfig,
    ) -> dict[str, Any]:
        """Create a new GitHub repository.

        Creates a new repository with the specified configuration.
        Requires 'public_repo' or 'repo' scope in GitHub token.

        Args:
            config: Repository configuration.

        Returns:
            Dictionary containing created repository information.

        Raises:
            GitHubError: If repository creation fails.

        Examples:
            >>> client = GitHubClient(token="ghp_...")
            >>> config = RepositoryConfig(
            ...     name="my-repo",
            ...     description="My repository",
            ...     is_private=False,
            ... )
            >>> repo = client.create_repository(config)
            >>> print(repo["full_name"])
        """
        try:
            payload = {
                "name": config.name,
                "description": config.description,
                "private": config.is_private,
                "has_wiki": config.include_wiki,
                "has_projects": config.include_projects,
                "has_discussions": config.include_discussions,
            }

            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/user/repos",
                    headers=self._get_headers(),
                    json=payload,
                )
                self._check_response(response)
                return response.json()
        except GitHubError:
            raise
        except Exception as exc:
            msg = f"{_ERR_CREATE_REPO_FAILED}: {exc}"
            raise GitHubError(msg) from exc

    def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """Get information about a repository.

        Retrieves metadata and configuration for a specific repository.

        Args:
            owner: Repository owner (username or organization).
            repo: Repository name.

        Returns:
            Dictionary containing repository information.

        Raises:
            GitHubError: If repository cannot be found or access is denied.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_REPO_FAILED}: {exc}"
            raise GitHubError(msg) from exc

    def set_branch_protection(
        self,
        owner: str,
        repo: str,
        branch: str,
        *,
        required_status_checks: dict[str, Any] | None = None,
        dismiss_stale_reviews: bool = False,
        require_code_owner_reviews: bool = False,
        required_approving_review_count: int = 0,
    ) -> dict[str, Any]:
        """Configure branch protection rules.

        Sets up branch protection rules including required status checks,
        review requirements, and other protection settings.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch name to protect (e.g., "main").
            required_status_checks: Status checks configuration dict with
                'strict' (bool) and 'contexts' (list) keys. Defaults to None.
            dismiss_stale_reviews: Whether to dismiss stale reviews.
                Defaults to False.
            require_code_owner_reviews: Whether to require code owner reviews.
                Defaults to False.
            required_approving_review_count: Number of required approvals.
                Defaults to 0.

        Returns:
            Dictionary containing branch protection configuration.

        Raises:
            GitHubError: If branch protection cannot be configured.

        Examples:
            >>> client = GitHubClient(token="ghp_...")
            >>> client.set_branch_protection(
            ...     owner="myorg",
            ...     repo="my-repo",
            ...     branch="main",
            ...     required_status_checks={
            ...         "strict": True,
            ...         "contexts": ["ci/build"],
            ...     },
            ...     require_code_owner_reviews=True,
            ...     required_approving_review_count=1,
            ... )
        """
        try:
            payload = {
                "required_status_checks": required_status_checks,
                "enforce_admins": True,
                "required_pull_request_reviews": {
                    "dismiss_stale_reviews": dismiss_stale_reviews,
                    "require_code_owner_reviews": require_code_owner_reviews,
                    "required_approving_review_count": required_approving_review_count,
                } if required_approving_review_count > 0 or require_code_owner_reviews or dismiss_stale_reviews else None,
                "restrictions": None,
            }

            with httpx.Client() as client:
                response = client.put(
                    f"{self.base_url}/repos/{owner}/{repo}/branches/{branch}/protection",
                    headers=self._get_headers(),
                    json=payload,
                )
                self._check_response(response)
                return response.json()
        except GitHubError:
            raise
        except Exception as exc:
            msg = f"{_ERR_SET_PROTECTION_FAILED}: {exc}"
            raise GitHubError(msg) from exc

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
            GitHubError: If response indicates an API error.
        """
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("message", "Unknown error")
            except Exception:  # noqa: BLE001
                message = response.text or "Unknown error"

            raise GitHubError(
                message,
                status_code=response.status_code,
                response_data=error_data if response.status_code >= 400 else None,
            )
