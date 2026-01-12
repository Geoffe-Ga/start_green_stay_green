"""Unit tests for GitHub Actions workflow management.

Tests for workflow configuration and execution via GitHub API.
All external API calls are mocked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from start_green_stay_green.github.actions import GitHubActionsManager
from start_green_stay_green.github.actions import WorkflowConfig

if TYPE_CHECKING:
    pass


@pytest.fixture
def valid_token() -> str:
    """Return valid test GitHub token."""
    return "ghp_test1234567890123456789012345678"


@pytest.fixture
def workflow_config() -> WorkflowConfig:
    """Return test workflow configuration."""
    return WorkflowConfig(
        name="CI",
        file_path=".github/workflows/ci.yml",
        description="Continuous Integration workflow",
    )


class TestGitHubActionsManagerInit:
    """Test GitHubActionsManager initialization."""

    def test_manager_init_with_valid_token_succeeds(
        self,
        valid_token: str,
    ) -> None:
        """Test manager initializes with valid token."""
        manager = GitHubActionsManager(token=valid_token)
        assert manager.token == valid_token

    def test_manager_init_with_empty_token_raises_value_error(
        self,
    ) -> None:
        """Test manager raises ValueError for empty token."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            GitHubActionsManager(token="")

    def test_manager_init_with_custom_base_url(
        self,
        valid_token: str,
    ) -> None:
        """Test manager accepts custom base URL."""
        custom_url = "https://github.enterprise.com/api/v3"
        manager = GitHubActionsManager(token=valid_token, base_url=custom_url)
        assert manager.base_url == custom_url


class TestWorkflowOperations:
    """Test workflow configuration and execution."""

    @patch("httpx.Client.get")
    def test_get_workflow_with_valid_id_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test retrieving workflow information."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123456,
            "node_id": "W_kwDOA",
            "name": "CI",
            "path": ".github/workflows/ci.yml",
            "state": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-02T00:00:00Z",
        }
        mock_get.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.get_workflow(
            owner="testuser",
            repo="test-repo",
            workflow_id=123456,
        )

        assert result["name"] == "CI"
        assert result["state"] == "active"

    @patch("httpx.Client.get")
    def test_get_workflow_with_invalid_id_raises_error(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test retrieving nonexistent workflow raises error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"message": "Not Found"}
        mock_get.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)

        with pytest.raises(Exception):
            manager.get_workflow(
                owner="testuser",
                repo="test-repo",
                workflow_id=999999,
            )

    @patch("httpx.Client.get")
    def test_list_workflows_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test listing all workflows in repository."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_count": 2,
            "workflows": [
                {
                    "id": 123456,
                    "name": "CI",
                    "path": ".github/workflows/ci.yml",
                    "state": "active",
                },
                {
                    "id": 789012,
                    "name": "CD",
                    "path": ".github/workflows/cd.yml",
                    "state": "active",
                },
            ],
        }
        mock_get.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.list_workflows(
            owner="testuser",
            repo="test-repo",
        )

        assert result["total_count"] == 2
        assert len(result["workflows"]) == 2
        assert result["workflows"][0]["name"] == "CI"

    @patch("httpx.Client.post")
    def test_trigger_workflow_succeeds(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test triggering a workflow run."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.trigger_workflow(
            owner="testuser",
            repo="test-repo",
            workflow_id=123456,
            ref="main",
            inputs={"debug": "true"},
        )

        assert result is True

    @patch("httpx.Client.post")
    def test_trigger_workflow_with_api_error_returns_false(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test workflow trigger handles API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.trigger_workflow(
            owner="testuser",
            repo="test-repo",
            workflow_id=999999,
            ref="main",
        )

        assert result is False


class TestWorkflowRuns:
    """Test workflow run operations."""

    @patch("httpx.Client.get")
    def test_list_workflow_runs_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test listing workflow runs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_count": 2,
            "workflow_runs": [
                {
                    "id": 111,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "created_at": "2024-01-02T00:00:00Z",
                },
                {
                    "id": 222,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "failure",
                    "created_at": "2024-01-01T00:00:00Z",
                },
            ],
        }
        mock_get.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.list_workflow_runs(
            owner="testuser",
            repo="test-repo",
            workflow_id=123456,
        )

        assert result["total_count"] == 2
        assert len(result["workflow_runs"]) == 2

    @patch("httpx.Client.get")
    def test_get_workflow_run_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test retrieving specific workflow run."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 111,
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
            "run_number": 1,
        }
        mock_get.return_value = mock_response

        manager = GitHubActionsManager(token=valid_token)
        result = manager.get_workflow_run(
            owner="testuser",
            repo="test-repo",
            run_id=111,
        )

        assert result["status"] == "completed"
        assert result["conclusion"] == "success"


class TestWorkflowConfig:
    """Test workflow configuration dataclass."""

    def test_workflow_config_creation_succeeds(
        self,
    ) -> None:
        """Test creating workflow config."""
        config = WorkflowConfig(
            name="CI",
            file_path=".github/workflows/ci.yml",
            description="Continuous Integration",
        )

        assert config.name == "CI"
        assert config.file_path == ".github/workflows/ci.yml"

    def test_workflow_config_with_empty_name_raises_error(
        self,
    ) -> None:
        """Test workflow config validation."""
        with pytest.raises(ValueError):
            WorkflowConfig(
                name="",
                file_path=".github/workflows/ci.yml",
            )

    def test_workflow_config_with_optional_description(
        self,
    ) -> None:
        """Test workflow config without description."""
        config = WorkflowConfig(
            name="CI",
            file_path=".github/workflows/ci.yml",
        )

        assert config.name == "CI"
        assert config.description is None


class TestErrorHandling:
    """Test error handling and edge cases."""

    @patch("httpx.Client.get")
    def test_network_error_in_workflow_operations(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test network errors are handled."""
        mock_get.side_effect = Exception("Connection timeout")

        manager = GitHubActionsManager(token=valid_token)

        with pytest.raises(Exception):
            manager.get_workflow(
                owner="testuser",
                repo="test-repo",
                workflow_id=123456,
            )
