"""Unit tests for GitHub API client.

Tests for authentication, repository operations, and branch protection
configuration via GitHub's REST API. All external API calls are mocked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from start_green_stay_green.github.client import GitHubClient
from start_green_stay_green.github.client import GitHubError
from start_green_stay_green.github.client import RepositoryConfig

if TYPE_CHECKING:
    pass


@pytest.fixture
def valid_token() -> str:
    """Return valid test GitHub token."""
    return "ghp_test1234567890123456789012345678"


@pytest.fixture
def repository_config() -> RepositoryConfig:
    """Return test repository configuration."""
    return RepositoryConfig(
        name="test-repo",
        description="Test repository",
        is_private=False,
        include_wiki=False,
        include_projects=False,
        include_discussions=False,
    )


class TestGitHubClientInit:
    """Test GitHubClient initialization."""

    def test_client_init_with_valid_token_succeeds(
        self,
        valid_token: str,
    ) -> None:
        """Test client initializes with valid token."""
        client = GitHubClient(token=valid_token)
        assert client.token == valid_token

    def test_client_init_with_empty_token_raises_value_error(
        self,
    ) -> None:
        """Test client raises ValueError for empty token."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            GitHubClient(token="")

    def test_client_init_with_whitespace_token_raises_value_error(
        self,
    ) -> None:
        """Test client raises ValueError for whitespace token."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            GitHubClient(token="   ")

    def test_client_init_with_custom_base_url(
        self,
        valid_token: str,
    ) -> None:
        """Test client accepts custom base URL."""
        custom_url = "https://github.enterprise.com/api/v3"
        client = GitHubClient(token=valid_token, base_url=custom_url)
        assert client.base_url == custom_url

    def test_client_init_with_default_base_url(
        self,
        valid_token: str,
    ) -> None:
        """Test client uses default GitHub API URL."""
        client = GitHubClient(token=valid_token)
        assert client.base_url == "https://api.github.com"


class TestRepositoryOperations:
    """Test repository creation and configuration."""

    @patch("httpx.Client.post")
    def test_create_repository_with_valid_config_succeeds(
        self,
        mock_post: Mock,
        valid_token: str,
        repository_config: RepositoryConfig,
    ) -> None:
        """Test successful repository creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123456,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "html_url": "https://github.com/testuser/test-repo",
            "description": "Test repository",
            "private": False,
            "owner": {
                "login": "testuser",
                "id": 12345,
            },
        }
        mock_post.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.create_repository(repository_config)

        assert result["name"] == "test-repo"
        assert result["full_name"] == "testuser/test-repo"
        assert result["id"] == 123456

    @patch("httpx.Client.post")
    def test_create_repository_with_api_error_raises_github_error(
        self,
        mock_post: Mock,
        valid_token: str,
        repository_config: RepositoryConfig,
    ) -> None:
        """Test repository creation handles API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "message": "Repository already exists",
            "errors": [{"message": "name already exists on this account"}],
        }
        mock_post.return_value = mock_response

        client = GitHubClient(token=valid_token)

        with pytest.raises(GitHubError, match="Repository already exists"):
            client.create_repository(repository_config)

    @patch("httpx.Client.post")
    def test_create_repository_without_description(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test repository creation without description."""
        config = RepositoryConfig(
            name="test-repo",
            description=None,
            is_private=False,
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123456,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
        }
        mock_post.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.create_repository(config)

        assert result["name"] == "test-repo"

    @patch("httpx.Client.get")
    def test_get_repository_with_valid_name_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test retrieving repository information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123456,
            "name": "test-repo",
            "full_name": "testuser/test-repo",
            "description": "Test repository",
        }
        mock_get.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.get_repository("testuser", "test-repo")

        assert result["name"] == "test-repo"
        assert result["id"] == 123456

    @patch("httpx.Client.get")
    def test_get_repository_with_not_found_raises_github_error(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test getting nonexistent repository raises error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_get.return_value = mock_response

        client = GitHubClient(token=valid_token)

        with pytest.raises(GitHubError, match="Not Found"):
            client.get_repository("testuser", "nonexistent")


class TestBranchProtection:
    """Test branch protection rules."""

    @patch("httpx.Client.put")
    def test_set_branch_protection_with_required_checks_succeeds(
        self,
        mock_put: Mock,
        valid_token: str,
    ) -> None:
        """Test setting branch protection with required checks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "url": "https://api.github.com/repos/testuser/test-repo/branches/main/protection",
            "required_status_checks": {
                "enforcement_level": "everyone",
                "contexts": ["ci/build"],
            },
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": True,
            "required_approving_review_count": 1,
        }
        mock_put.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.set_branch_protection(
            owner="testuser",
            repo="test-repo",
            branch="main",
            required_status_checks={"strict": True, "contexts": ["ci/build"]},
            dismiss_stale_reviews=True,
            require_code_owner_reviews=True,
            required_approving_review_count=1,
        )

        assert result["required_status_checks"]["contexts"] == ["ci/build"]

    @patch("httpx.Client.put")
    def test_set_branch_protection_with_api_error_raises_github_error(
        self,
        mock_put: Mock,
        valid_token: str,
    ) -> None:
        """Test branch protection handles API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_put.return_value = mock_response

        client = GitHubClient(token=valid_token)

        with pytest.raises(GitHubError, match="Not Found"):
            client.set_branch_protection(
                owner="testuser",
                repo="test-repo",
                branch="main",
            )

    @patch("httpx.Client.put")
    def test_set_branch_protection_minimal_config(
        self,
        mock_put: Mock,
        valid_token: str,
    ) -> None:
        """Test branch protection with minimal configuration."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "url": "https://api.github.com/repos/testuser/test-repo/branches/main/protection",
        }
        mock_put.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.set_branch_protection(
            owner="testuser",
            repo="test-repo",
            branch="main",
        )

        assert "url" in result


class TestAuthentication:
    """Test authentication and token handling."""

    @patch("httpx.Client.get")
    def test_verify_token_with_valid_token_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test token verification with valid token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "id": 12345,
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        }
        mock_get.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.verify_token()

        assert result is True

    @patch("httpx.Client.get")
    def test_verify_token_with_invalid_token_returns_false(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test token verification with invalid token."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Bad credentials"}
        mock_get.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.verify_token()

        assert result is False

    @patch("httpx.Client.get")
    def test_get_authenticated_user_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test getting authenticated user information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "testuser",
            "id": 12345,
            "type": "User",
        }
        mock_get.return_value = mock_response

        client = GitHubClient(token=valid_token)
        result = client.get_authenticated_user()

        assert result["login"] == "testuser"
        assert result["id"] == 12345


class TestErrorHandling:
    """Test error handling and edge cases."""

    @patch("httpx.Client.get")
    def test_network_error_raises_github_error(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test network errors are wrapped in GitHubError."""
        mock_get.side_effect = Exception("Connection timeout")

        client = GitHubClient(token=valid_token)

        with pytest.raises(GitHubError, match="Connection timeout"):
            client.get_authenticated_user()

    def test_repository_config_with_invalid_name_raises_error(
        self,
    ) -> None:
        """Test repository config validation."""
        with pytest.raises(ValueError):
            RepositoryConfig(
                name="",  # Empty name invalid
                description="Test",
            )

    def test_repository_config_with_special_characters_in_name(
        self,
    ) -> None:
        """Test repository config with valid special characters."""
        config = RepositoryConfig(
            name="test-repo-123",
            description="Test",
        )
        assert config.name == "test-repo-123"
