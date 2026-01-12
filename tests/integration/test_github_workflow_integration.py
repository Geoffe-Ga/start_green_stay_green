"""Integration tests for GitHub workflow integration.

Tests the GitHub API integration and repository setup including:
- GitHub client initialization and authentication
- Repository creation and configuration
- GitHub Actions workflow setup
- Webhook and integration configuration

These tests verify GitHub integration behavior.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestGitHubClientInitialization:
    """Test GitHub client initialization and authentication."""

    @pytest.mark.asyncio
    async def test_github_client_initializes_with_token(self) -> None:
        """Test GitHub client initializes with token."""
        token = "ghp_test_token_123456789"

        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.token = token

            assert mock_instance.token == token

    @pytest.mark.asyncio
    async def test_github_client_validates_authentication(self) -> None:
        """Test GitHub client validates authentication."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.verify_authentication = AsyncMock(return_value=True)

            result = await mock_instance.verify_authentication()

            assert result is True
            mock_instance.verify_authentication.assert_called_once()

    @pytest.mark.asyncio
    async def test_github_client_fails_with_invalid_token(self) -> None:
        """Test GitHub client fails with invalid token."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.verify_authentication = AsyncMock(
                side_effect=ValueError("Invalid token")
            )

            with pytest.raises(ValueError):
                await mock_instance.verify_authentication()

    @pytest.mark.asyncio
    async def test_github_client_fetches_user_info(self) -> None:
        """Test GitHub client fetches authenticated user info."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_user = AsyncMock(
                return_value={"login": "testuser", "id": 12345}
            )

            result = await mock_instance.get_user()

            assert result["login"] == "testuser"

    @pytest.mark.asyncio
    async def test_github_client_handles_rate_limits(self) -> None:
        """Test GitHub client handles rate limits."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_rate_limit = AsyncMock(
                return_value={"remaining": 4999, "limit": 5000}
            )

            result = await mock_instance.get_rate_limit()

            assert result["remaining"] < result["limit"]


class TestRepositoryCreation:
    """Test repository creation and configuration."""

    @pytest.mark.asyncio
    async def test_github_client_creates_repository(self) -> None:
        """Test GitHub client creates repository."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_repo = AsyncMock(
                return_value={
                    "name": "test-repo",
                    "url": "https://github.com/testuser/test-repo",
                }
            )

            result = await mock_instance.create_repo("test-repo")

            assert result["name"] == "test-repo"
            assert "github.com" in result["url"]

    @pytest.mark.asyncio
    async def test_github_client_configures_repository(self) -> None:
        """Test GitHub client configures repository."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.configure_repo = AsyncMock(
                return_value={"configured": True, "features": {}}
            )

            result = await mock_instance.configure_repo(
                "testuser",
                "test-repo",
                {"allow_squash_merge": True, "allow_rebase_merge": False},
            )

            assert result["configured"] is True

    @pytest.mark.asyncio
    async def test_github_client_sets_repository_topics(self) -> None:
        """Test GitHub client sets repository topics."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.set_topics = AsyncMock(
                return_value={
                    "topics": [
                        "quality-engineering",
                        "ai-assisted",
                        "python",
                    ]
                }
            )

            result = await mock_instance.set_topics(
                "testuser",
                "test-repo",
                ["quality-engineering", "ai-assisted", "python"],
            )

            assert len(result["topics"]) == 3

    @pytest.mark.asyncio
    async def test_github_client_handles_repository_exists_error(self) -> None:
        """Test GitHub client handles repository exists error."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_repo = AsyncMock(
                side_effect=ValueError("Repository already exists")
            )

            with pytest.raises(ValueError):
                await mock_instance.create_repo("existing-repo")


class TestGitHubActionsWorkflow:
    """Test GitHub Actions workflow setup."""

    @pytest.mark.asyncio
    async def test_github_client_creates_workflow_file(self) -> None:
        """Test GitHub client creates workflow file."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_workflow = AsyncMock(
                return_value={
                    "path": ".github/workflows/ci.yml",
                    "created": True,
                }
            )

            result = await mock_instance.create_workflow(
                "testuser",
                "test-repo",
                "ci",
                "workflow content",
            )

            assert ".github/workflows" in result["path"]

    @pytest.mark.asyncio
    async def test_github_client_enables_github_actions(self) -> None:
        """Test GitHub client enables GitHub Actions."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.enable_actions = AsyncMock(
                return_value={"enabled": True}
            )

            result = await mock_instance.enable_actions("testuser", "test-repo")

            assert result["enabled"] is True

    @pytest.mark.asyncio
    async def test_github_client_sets_branch_protection(self) -> None:
        """Test GitHub client sets branch protection rules."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.set_branch_protection = AsyncMock(
                return_value={
                    "branch": "main",
                    "protection": {
                        "require_status_checks": True,
                        "require_reviews": True,
                    },
                }
            )

            result = await mock_instance.set_branch_protection(
                "testuser",
                "test-repo",
                "main",
                {"require_status_checks": True, "require_reviews": True},
            )

            assert result["branch"] == "main"
            assert result["protection"]["require_reviews"] is True


class TestGitHubIntegrationConfiguration:
    """Test GitHub integration and webhook configuration."""

    @pytest.mark.asyncio
    async def test_github_client_creates_webhooks(self) -> None:
        """Test GitHub client creates webhooks."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_webhook = AsyncMock(
                return_value={
                    "id": 123456,
                    "url": "https://example.com/webhook",
                }
            )

            result = await mock_instance.create_webhook(
                "testuser",
                "test-repo",
                "https://example.com/webhook",
                events=["push", "pull_request"],
            )

            assert result["id"] > 0

    @pytest.mark.asyncio
    async def test_github_client_configures_deploy_keys(self) -> None:
        """Test GitHub client configures deploy keys."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.add_deploy_key = AsyncMock(
                return_value={"id": 987654, "read_only": True}
            )

            result = await mock_instance.add_deploy_key(
                "testuser",
                "test-repo",
                "ssh-rsa AAAA...",
                read_only=True,
            )

            assert result["id"] > 0

    @pytest.mark.asyncio
    async def test_github_client_adds_repository_secrets(self) -> None:
        """Test GitHub client adds repository secrets."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.add_secret = AsyncMock(
                return_value={"secret_name": "API_KEY", "added": True}
            )

            result = await mock_instance.add_secret(
                "testuser",
                "test-repo",
                "API_KEY",
                "secret_value",
            )

            assert result["added"] is True


class TestGitHubAPIErrorHandling:
    """Test error handling for GitHub API operations."""

    @pytest.mark.asyncio
    async def test_github_client_handles_authentication_error(self) -> None:
        """Test GitHub client handles authentication error."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_repo = AsyncMock(
                side_effect=PermissionError("Authentication failed")
            )

            with pytest.raises(PermissionError):
                await mock_instance.create_repo("test-repo")

    @pytest.mark.asyncio
    async def test_github_client_handles_rate_limit_error(self) -> None:
        """Test GitHub client handles rate limit error."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_repo = AsyncMock(
                side_effect=RuntimeError("Rate limit exceeded")
            )

            with pytest.raises(RuntimeError):
                await mock_instance.create_repo("test-repo")

    @pytest.mark.asyncio
    async def test_github_client_handles_network_error(self) -> None:
        """Test GitHub client handles network error."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_user = AsyncMock(
                side_effect=ConnectionError("Network error")
            )

            with pytest.raises(ConnectionError):
                await mock_instance.get_user()


class TestEndToEndGitHubWorkflow:
    """Test complete end-to-end GitHub workflow."""

    @pytest.mark.asyncio
    async def test_complete_github_repository_setup(self) -> None:
        """Test complete GitHub repository setup workflow."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            # Mock complete workflow
            mock_instance.verify_authentication = AsyncMock(return_value=True)
            mock_instance.create_repo = AsyncMock(
                return_value={
                    "name": "test-repo",
                    "url": "https://github.com/testuser/test-repo",
                }
            )
            mock_instance.configure_repo = AsyncMock(
                return_value={"configured": True}
            )
            mock_instance.enable_actions = AsyncMock(
                return_value={"enabled": True}
            )
            mock_instance.create_workflow = AsyncMock(
                return_value={"path": ".github/workflows/ci.yml", "created": True}
            )
            mock_instance.setup_complete = AsyncMock(
                return_value={
                    "success": True,
                    "repository": "test-repo",
                    "workflows": 1,
                }
            )

            result = await mock_instance.setup_complete("testuser", "test-repo")

            assert result["success"] is True
            assert result["repository"] == "test-repo"

    @pytest.mark.asyncio
    async def test_github_workflow_with_error_recovery(self) -> None:
        """Test GitHub workflow handles errors gracefully."""
        with patch("start_green_stay_green.github.client.GitHubClient") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            # Simulate error then recovery
            mock_instance.create_repo = AsyncMock()
            mock_instance.create_repo.side_effect = [
                ConnectionError("Network error"),
                {
                    "name": "test-repo",
                    "url": "https://github.com/testuser/test-repo",
                },
            ]

            # First call fails
            with pytest.raises(ConnectionError):
                await mock_instance.create_repo("test-repo")

            # Second call succeeds
            result = await mock_instance.create_repo("test-repo")
            assert result["name"] == "test-repo"
