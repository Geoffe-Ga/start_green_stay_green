"""Unit tests for GitHub issue and epic creation.

Tests for parsing SPEC.md, creating issues, epics, and milestones
via GitHub API. All external API calls are mocked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from start_green_stay_green.github.issues import GitHubIssueManager
from start_green_stay_green.github.issues import IssueConfig
from start_green_stay_green.github.issues import MilestoneConfig

if TYPE_CHECKING:
    pass


@pytest.fixture
def valid_token() -> str:
    """Return valid test GitHub token."""
    return "ghp_test1234567890123456789012345678"


@pytest.fixture
def issue_config() -> IssueConfig:
    """Return test issue configuration."""
    return IssueConfig(
        title="Test Issue",
        body="This is a test issue",
        labels=["type: feature", "priority: high"],
        milestone=None,
        assignees=None,
    )


@pytest.fixture
def milestone_config() -> MilestoneConfig:
    """Return test milestone configuration."""
    return MilestoneConfig(
        title="Epic 1: Core Infrastructure",
        description="Establish the repository with quality controls",
        due_date="2024-03-01",
    )


class TestGitHubIssueManagerInit:
    """Test GitHubIssueManager initialization."""

    def test_manager_init_with_valid_token_succeeds(
        self,
        valid_token: str,
    ) -> None:
        """Test manager initializes with valid token."""
        manager = GitHubIssueManager(token=valid_token)
        assert manager.token == valid_token

    def test_manager_init_with_empty_token_raises_value_error(
        self,
    ) -> None:
        """Test manager raises ValueError for empty token."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            GitHubIssueManager(token="")

    def test_manager_init_with_custom_base_url(
        self,
        valid_token: str,
    ) -> None:
        """Test manager accepts custom base URL."""
        custom_url = "https://github.enterprise.com/api/v3"
        manager = GitHubIssueManager(token=valid_token, base_url=custom_url)
        assert manager.base_url == custom_url


class TestIssueCreation:
    """Test issue creation operations."""

    @patch("httpx.Client.post")
    def test_create_issue_with_valid_config_succeeds(
        self,
        mock_post: Mock,
        valid_token: str,
        issue_config: IssueConfig,
    ) -> None:
        """Test successful issue creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1000,
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "labels": [
                {"name": "type: feature"},
                {"name": "priority: high"},
            ],
            "html_url": "https://github.com/testuser/test-repo/issues/1",
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_issue(
            owner="testuser",
            repo="test-repo",
            issue=issue_config,
        )

        assert result["number"] == 1
        assert result["title"] == "Test Issue"
        assert result["state"] == "open"

    @patch("httpx.Client.post")
    def test_create_issue_with_assignees(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test creating issue with assignees."""
        issue = IssueConfig(
            title="Test Issue",
            body="Test",
            labels=["type: feature"],
            assignees=["user1", "user2"],
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1000,
            "number": 1,
            "title": "Test Issue",
            "assignees": [
                {"login": "user1"},
                {"login": "user2"},
            ],
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_issue(
            owner="testuser",
            repo="test-repo",
            issue=issue,
        )

        assert len(result["assignees"]) == 2

    @patch("httpx.Client.post")
    def test_create_issue_without_labels(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test creating issue without labels."""
        issue = IssueConfig(
            title="Test Issue",
            body="Test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1000,
            "number": 1,
            "title": "Test Issue",
            "labels": [],
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_issue(
            owner="testuser",
            repo="test-repo",
            issue=issue,
        )

        assert result["number"] == 1

    @patch("httpx.Client.post")
    def test_create_issue_with_api_error_raises_exception(
        self,
        mock_post: Mock,
        valid_token: str,
        issue_config: IssueConfig,
    ) -> None:
        """Test issue creation handles API errors."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "message": "Validation Failed",
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)

        with pytest.raises(Exception):
            manager.create_issue(
                owner="testuser",
                repo="test-repo",
                issue=issue_config,
            )


class TestMilestoneOperations:
    """Test milestone/epic creation."""

    @patch("httpx.Client.post")
    def test_create_milestone_with_valid_config_succeeds(
        self,
        mock_post: Mock,
        valid_token: str,
        milestone_config: MilestoneConfig,
    ) -> None:
        """Test successful milestone creation."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 5000,
            "number": 1,
            "title": "Epic 1: Core Infrastructure",
            "description": "Establish the repository with quality controls",
            "state": "open",
            "due_on": "2024-03-01T00:00:00Z",
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_milestone(
            owner="testuser",
            repo="test-repo",
            milestone=milestone_config,
        )

        assert result["number"] == 1
        assert result["title"] == "Epic 1: Core Infrastructure"
        assert result["state"] == "open"

    @patch("httpx.Client.post")
    def test_create_milestone_without_due_date(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test creating milestone without due date."""
        milestone = MilestoneConfig(
            title="Epic 1: Core Infrastructure",
            description="Test milestone",
        )

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 5000,
            "number": 1,
            "title": "Epic 1: Core Infrastructure",
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_milestone(
            owner="testuser",
            repo="test-repo",
            milestone=milestone,
        )

        assert result["number"] == 1

    @patch("httpx.Client.get")
    def test_get_milestone_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test retrieving milestone."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 5000,
            "number": 1,
            "title": "Epic 1: Core Infrastructure",
            "state": "open",
        }
        mock_get.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.get_milestone(
            owner="testuser",
            repo="test-repo",
            milestone_number=1,
        )

        assert result["title"] == "Epic 1: Core Infrastructure"

    @patch("httpx.Client.get")
    def test_list_milestones_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test listing milestones."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 5000,
                "number": 1,
                "title": "Epic 1: Core Infrastructure",
                "state": "open",
            },
            {
                "id": 5001,
                "number": 2,
                "title": "Epic 2: Quality Controls",
                "state": "open",
            },
        ]
        mock_get.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.list_milestones(
            owner="testuser",
            repo="test-repo",
        )

        assert len(result) == 2
        assert result[0]["title"] == "Epic 1: Core Infrastructure"


class TestLabelOperations:
    """Test label creation and management."""

    @patch("httpx.Client.post")
    def test_create_label_succeeds(
        self,
        mock_post: Mock,
        valid_token: str,
    ) -> None:
        """Test creating a label."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 2000,
            "name": "type: feature",
            "color": "0366d6",
            "description": "Feature request",
        }
        mock_post.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.create_label(
            owner="testuser",
            repo="test-repo",
            name="type: feature",
            color="0366d6",
            description="Feature request",
        )

        assert result["name"] == "type: feature"
        assert result["color"] == "0366d6"

    @patch("httpx.Client.get")
    def test_list_labels_succeeds(
        self,
        mock_get: Mock,
        valid_token: str,
    ) -> None:
        """Test listing labels."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "id": 2000,
                "name": "type: feature",
                "color": "0366d6",
            },
            {
                "id": 2001,
                "name": "priority: high",
                "color": "d73a49",
            },
        ]
        mock_get.return_value = mock_response

        manager = GitHubIssueManager(token=valid_token)
        result = manager.list_labels(
            owner="testuser",
            repo="test-repo",
        )

        assert len(result) == 2
        assert result[0]["name"] == "type: feature"


class TestIssueConfig:
    """Test issue configuration dataclass."""

    def test_issue_config_with_title_and_body(
        self,
    ) -> None:
        """Test creating issue config with required fields."""
        config = IssueConfig(
            title="Test Issue",
            body="Test body",
        )

        assert config.title == "Test Issue"
        assert config.body == "Test body"
        assert config.labels is None

    def test_issue_config_with_empty_title_raises_error(
        self,
    ) -> None:
        """Test issue config validation."""
        with pytest.raises(ValueError):
            IssueConfig(
                title="",
                body="Test",
            )

    def test_issue_config_with_all_fields(
        self,
    ) -> None:
        """Test creating issue config with all fields."""
        config = IssueConfig(
            title="Test Issue",
            body="Test body",
            labels=["type: feature"],
            assignees=["user1"],
        )

        assert config.title == "Test Issue"
        assert len(config.labels) == 1
        assert len(config.assignees) == 1


class TestErrorHandling:
    """Test error handling and edge cases."""

    @patch("httpx.Client.post")
    def test_network_error_in_issue_creation(
        self,
        mock_post: Mock,
        valid_token: str,
        issue_config: IssueConfig,
    ) -> None:
        """Test network errors are handled."""
        mock_post.side_effect = Exception("Connection timeout")

        manager = GitHubIssueManager(token=valid_token)

        with pytest.raises(Exception):
            manager.create_issue(
                owner="testuser",
                repo="test-repo",
                issue=issue_config,
            )
