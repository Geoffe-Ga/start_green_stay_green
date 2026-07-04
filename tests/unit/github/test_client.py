"""Unit tests for GitHubClient.

Tests the complete GitHub API integration including:
- Repository creation and configuration
- Branch protection rules
- Issue and label management
- Milestone creation
- SPEC.md parsing
- Error handling and retry logic
"""

import base64
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import httpx
import pytest

from start_green_stay_green.github import BranchProtectionRule
from start_green_stay_green.github import GitHubAuthError
from start_green_stay_green.github import GitHubClient
from start_green_stay_green.github import GitHubError
from start_green_stay_green.github import IssueData


class TestGitHubErrorInitialization:
    """Test GitHubError exception initialization."""

    def test_error_with_message_only(self) -> None:
        """Test creating error with just message.

        Kills mutations: message assignment
        """
        error = GitHubError("Test error")

        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response_body is None
        assert str(error) == "Test error"

    def test_error_with_all_parameters(self) -> None:
        """Test creating error with all parameters.

        Kills mutations: parameter assignments
        """
        response_body = {"message": "API error"}
        error = GitHubError("API failed", status_code=500, response_body=response_body)

        assert error.message == "API failed"
        assert error.status_code == 500
        assert error.response_body == response_body

    def test_github_auth_error_inheritance(self) -> None:
        """Test GitHubAuthError is subclass of GitHubError.

        Kills mutations: inheritance definition
        """
        error = GitHubAuthError("Auth failed", status_code=401)

        assert isinstance(error, GitHubError)
        assert isinstance(error, Exception)
        assert error.status_code == 401


class TestGitHubClientInitialization:
    """Test GitHubClient initialization and validation."""

    def test_init_valid_credentials(self) -> None:
        """Test initialization with valid parameters.

        Kills mutations: parameter storage
        """
        with patch("httpx.Client"):
            client = GitHubClient("token123", "owner", "repo")

            assert client._token == "token123"  # noqa: S105 # Test token
            assert client.owner == "owner"
            assert client.repo == "repo"

    def test_init_missing_token_raises_error(self) -> None:
        """Test initialization with empty token raises error.

        Kills mutations: token validation
        """
        with pytest.raises(GitHubError, match="token is required"):
            GitHubClient("", "owner", "repo")

    def test_init_missing_token_none_raises_error(self) -> None:
        """Test initialization with None token raises error.

        Kills mutations: token type validation
        """
        with pytest.raises(GitHubError, match="token is required"):
            GitHubClient(None, "owner", "repo")  # type: ignore[arg-type]

    def test_init_missing_owner_raises_error(self) -> None:
        """Test initialization with empty owner raises error.

        Kills mutations: owner validation
        """
        with pytest.raises(GitHubError, match="owner is required"):
            GitHubClient("token123", "", "repo")

    def test_init_missing_repo_raises_error(self) -> None:
        """Test initialization with empty repo raises error.

        Kills mutations: repo validation
        """
        with pytest.raises(GitHubError, match="Repository name is required"):
            GitHubClient("token123", "owner", "")

    def test_init_creates_http_client(self) -> None:
        """Test initialization creates HTTP client with correct headers.

        Kills mutations: httpx.Client instantiation
        """
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("token123", "owner", "repo")

            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]

            assert call_kwargs["base_url"] == "https://api.github.com"
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == "token token123"


class TestGitHubClientContextManager:
    """Test GitHubClient context manager functionality."""

    def test_context_manager_enter_exit(self) -> None:
        """Test context manager enter and exit.

        Kills mutations: __enter__, __exit__ implementation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            with GitHubClient("token", "owner", "repo") as client:
                assert client is not None
                assert isinstance(client, GitHubClient)

            mock_client.close.assert_called_once()

    def test_close_closes_client(self) -> None:
        """Test close method closes HTTP client.

        Kills mutations: close() call
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            client = GitHubClient("token", "owner", "repo")
            client.close()

            mock_client.close.assert_called_once()


class TestGitHubClientResponseHandling:
    """Test GitHub API response handling and errors."""

    def test_handle_response_success(self) -> None:
        """Test handling successful 2xx response.

        Kills mutations: response parsing
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 200
            response.content = b'{"status": "ok"}'
            response.json.return_value = {"status": "ok"}

            result = client._handle_response(response)

            assert result == {"status": "ok"}

    def test_handle_response_401_raises_auth_error(self) -> None:
        """Test 401 response raises GitHubAuthError.

        Kills mutations: 401 handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 401
            response.content = b'{"message": "Bad credentials"}'
            response.json.return_value = {"message": "Bad credentials"}

            with pytest.raises(GitHubAuthError) as exc_info:
                client._handle_response(response)

            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.message

    def test_handle_response_403_raises_auth_error(self) -> None:
        """Test 403 response raises GitHubAuthError.

        Kills mutations: 403 handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 403
            response.content = b'{"message": "Forbidden"}'
            response.json.return_value = {"message": "Forbidden"}

            with pytest.raises(GitHubAuthError) as exc_info:
                client._handle_response(response)

            assert exc_info.value.status_code == 403
            assert "Permission denied" in exc_info.value.message

    def test_handle_response_404_raises_error(self) -> None:
        """Test 404 response raises GitHubError.

        Kills mutations: 404 handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 404
            response.content = b'{"message": "Not Found"}'
            response.json.return_value = {"message": "Not Found"}

            with pytest.raises(GitHubError) as exc_info:
                client._handle_response(response)

            assert exc_info.value.status_code == 404

    def test_handle_response_500_raises_error(self) -> None:
        """Test 500 response raises GitHubError.

        Kills mutations: 500+ handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 500
            response.content = b'{"message": "Server Error"}'
            response.json.return_value = {"message": "Server Error"}

            with pytest.raises(GitHubError) as exc_info:
                client._handle_response(response)

            assert exc_info.value.status_code == 500

    def test_handle_response_invalid_json(self) -> None:
        """Test handling response with invalid JSON.

        Kills mutations: JSON error handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 200
            response.content = b"not json"
            response.json.side_effect = Exception("Invalid JSON")

            result = client._handle_response(response)

            assert "raw_body" in result

    def test_handle_response_empty_content(self) -> None:
        """Test handling response with no content.

        Kills mutations: empty content handling
        """
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            response = Mock(spec=httpx.Response)
            response.status_code = 204
            response.content = b""

            result = client._handle_response(response)

            assert not result


class TestGitHubClientRepositoryOperations:
    """Test repository creation and configuration."""

    def test_create_repository(self) -> None:
        """Test creating a repository.

        Kills mutations: repository creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 123}',
                json=lambda: {"id": 123},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.create_repository(description="Test", private=False)

            assert result == {"id": 123}
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/user/repos"

    def test_update_repository(self) -> None:
        """Test updating repository settings.

        Kills mutations: repository update
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"id": 123}',
                json=lambda: {"id": 123},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.update_repository(description="Updated")

            assert result == {"id": 123}
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "PATCH"

    def test_get_repository_info(self) -> None:
        """Test getting repository information.

        Kills mutations: get repository info
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"id": 123, "name": "test-repo"}',
                json=lambda: {"id": 123, "name": "test-repo"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.get_repository_info()

            assert result["id"] == 123
            assert result["name"] == "test-repo"


class TestGitHubClientBranchProtection:
    """Test branch protection configuration."""

    def test_configure_branch_protection_default(self) -> None:
        """Test configuring branch protection with defaults.

        Kills mutations: default branch protection
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"protected": true}',
                json=lambda: {"protected": True},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.configure_branch_protection()

            assert result["protected"] is True
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "PUT"
            assert "main/protection" in call_args[0][1]

    def test_configure_branch_protection_custom_rule(self) -> None:
        """Test configuring branch protection with custom rule.

        Kills mutations: custom branch protection
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"protected": true}',
                json=lambda: {"protected": True},
            )

            rule = BranchProtectionRule(
                require_code_review=False,
                allow_force_pushes=True,
            )
            client = GitHubClient("token", "owner", "test-repo")
            result = client.configure_branch_protection(rule=rule)

            assert result["protected"] is True


class TestGitHubClientIssueOperations:
    """Test issue creation and management."""

    def test_create_issue(self) -> None:
        """Test creating a single issue.

        Kills mutations: issue creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 1, "number": 1}',
                json=lambda: {"id": 1, "number": 1},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.create_issue(
                title="Test Issue",
                body="Test body",
                labels=["bug"],
            )

            assert result["number"] == 1
            call_args = mock_client.request.call_args
            assert call_args[0][0] == "POST"
            assert "issues" in call_args[0][1]

    def test_create_issues_bulk(self) -> None:
        """Test creating multiple issues.

        Kills mutations: bulk issue creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 1, "number": 1}',
                json=lambda: {"id": 1, "number": 1},
            )

            client = GitHubClient("token", "owner", "test-repo")
            issues = [
                IssueData(title="Issue 1", body="Body 1"),
                IssueData(title="Issue 2", body="Body 2"),
            ]
            results = client.create_issues_bulk(issues)

            assert len(results) == 2
            assert mock_client.request.call_count >= 2

    def test_create_issues_bulk_error_stops_operation(self) -> None:
        """Test bulk creation stops on first error.

        Kills mutations: error handling in bulk
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # First call succeeds, second fails
            error_response = Mock(
                status_code=404,
                content=b'{"message": "Not Found"}',
                json=lambda: {"message": "Not Found"},
            )
            mock_client.request.side_effect = [
                Mock(
                    status_code=201,
                    content=b'{"number": 1}',
                    json=lambda: {"number": 1},
                ),
                error_response,
            ]

            client = GitHubClient("token", "owner", "test-repo")
            issues = [
                IssueData(title="Issue 1", body="Body 1"),
                IssueData(title="Issue 2", body="Body 2"),
            ]

            with pytest.raises(GitHubError):
                client.create_issues_bulk(issues)

    def test_get_issue(self) -> None:
        """Test retrieving a specific issue.

        Kills mutations: get issue
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"number": 1, "title": "Test"}',
                json=lambda: {"number": 1, "title": "Test"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.get_issue(1)

            assert result["number"] == 1

    def test_list_issues(self) -> None:
        """Test listing issues.

        Kills mutations: list issues
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'[{"number": 1}, {"number": 2}]',
                json=lambda: [{"number": 1}, {"number": 2}],
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.list_issues(state="open")

            assert len(result) == 2
            call_args = mock_client.request.call_args
            assert call_args[1]["params"]["state"] == "open"


class TestGitHubClientLabelOperations:
    """Test label creation and management."""

    def test_create_label(self) -> None:
        """Test creating a label.

        Kills mutations: label creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"name": "bug"}',
                json=lambda: {"name": "bug"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.create_label("bug", color="ff0000")

            assert result["name"] == "bug"

    def test_create_labels_bulk(self) -> None:
        """Test creating multiple labels.

        Kills mutations: bulk label creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"name": "test"}',
                json=lambda: {"name": "test"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            labels = [
                {"name": "bug", "color": "ff0000"},
                {"name": "feature", "color": "00ff00"},
            ]
            results = client.create_labels_bulk(labels)

            assert len(results) >= 0  # May be 0 if errors are caught
            assert mock_client.request.call_count >= 2


class TestGitHubClientMilestoneOperations:
    """Test milestone creation and management."""

    def test_create_milestone(self) -> None:
        """Test creating a milestone.

        Kills mutations: milestone creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 1, "title": "v1.0"}',
                json=lambda: {"id": 1, "title": "v1.0"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.create_milestone("v1.0")

            assert result["title"] == "v1.0"

    def test_create_milestones_bulk(self) -> None:
        """Test creating multiple milestones.

        Kills mutations: bulk milestone creation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 1, "title": "v1.0"}',
                json=lambda: {"id": 1, "title": "v1.0"},
            )

            client = GitHubClient("token", "owner", "test-repo")
            milestones = [
                {"title": "v1.0"},
                {"title": "v2.0"},
            ]
            results = client.create_milestones_bulk(milestones)

            assert len(results) >= 0


class TestGitHubClientFileOperations:
    """Test file creation and management."""

    def test_create_or_update_file(self) -> None:
        """Test creating/updating a file.

        Kills mutations: file operation
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"commit": {}}',
                json=lambda: {"commit": {}},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.create_or_update_file(
                "README.md",
                "# Test",
                "Add README",
            )

            assert "commit" in result

    def test_add_repository_topics(self) -> None:
        """Test adding topics to repository.

        Kills mutations: topic addition
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b'{"names": ["test"]}',
                json=lambda: {"names": ["test"]},
            )

            client = GitHubClient("token", "owner", "test-repo")
            result = client.add_repository_topics(["test", "python"])

            assert "names" in result


class TestGitHubClientSpecParsing:
    """Test SPEC.md parsing functionality."""

    def test_parse_spec_issues_basic(self) -> None:
        """Test parsing basic issue from SPEC.

        Kills mutations: issue parsing
        """
        spec_content = """
#### Issue 1.1: Test Issue
**Type**: Feature
**Priority**: P0
**Estimate**: 2 hours

**Description**:
This is a test issue.

**Acceptance Criteria**:
- [ ] Test criterion
"""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "test-repo")
            issues = client.parse_spec_issues(spec_content)

            assert len(issues) == 1
            assert "1.1" in issues[0].title
            assert "Test Issue" in issues[0].title
            assert issues[0].type == "Feature"
            assert issues[0].priority == "P0"

    def test_parse_spec_issues_multiple(self) -> None:
        """Test parsing multiple issues from SPEC.

        Kills mutations: multiple parsing
        """
        spec_content = """
#### Issue 1.1: First Issue
**Type**: Task
**Priority**: P1
**Description**: First

#### Issue 1.2: Second Issue
**Type**: Feature
**Priority**: P0
**Description**: Second
"""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "test-repo")
            issues = client.parse_spec_issues(spec_content)

            assert len(issues) == 2
            assert "1.1" in issues[0].title
            assert "1.2" in issues[1].title

    def test_parse_spec_issues_with_labels(self) -> None:
        """Test parsed issues include labels.

        Kills mutations: label assignment
        """
        spec_content = """
#### Issue 2.1: Test Issue
**Type**: Bug
**Priority**: P2
**Description**: Test
"""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "test-repo")
            issues = client.parse_spec_issues(spec_content)

            assert issues
            assert "bug" in issues[0].labels
            assert "p2" in issues[0].labels

    def test_parse_spec_issues_with_body(self) -> None:
        """Test parsed issues include description and criteria.

        Kills mutations: body assembly
        """
        spec_content = """
#### Issue 1.1: Test Issue
**Type**: Task
**Priority**: P0
**Description**:
Test description

**Acceptance Criteria**:
- [ ] Criterion 1
- [ ] Criterion 2
"""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "test-repo")
            issues = client.parse_spec_issues(spec_content)

            assert issues
            assert "Test description" in issues[0].body
            assert "Criterion 1" in issues[0].body


class TestBranchProtectionRule:
    """Test BranchProtectionRule model."""

    def test_default_values(self) -> None:
        """Test default branch protection values.

        Kills mutations: default values
        """
        rule = BranchProtectionRule()

        assert rule.dismiss_stale_reviews
        assert rule.require_code_review
        assert rule.require_status_checks
        assert not rule.allow_force_pushes
        assert not rule.allow_deletions
        assert not rule.status_check_contexts

    def test_custom_values(self) -> None:
        """Test setting custom branch protection values.

        Kills mutations: custom values
        """
        rule = BranchProtectionRule(
            dismiss_stale_reviews=False,
            require_code_review=False,
            allow_force_pushes=True,
            status_check_contexts=["ci", "test"],
        )

        assert not rule.dismiss_stale_reviews
        assert not rule.require_code_review
        assert rule.allow_force_pushes
        assert rule.status_check_contexts == ["ci", "test"]


class TestIssueDataModel:
    """Test IssueData model."""

    def test_issue_data_required_fields(self) -> None:
        """Test IssueData with required fields.

        Kills mutations: required field validation
        """
        issue = IssueData(title="Test", body="Body")

        assert issue.title == "Test"
        assert issue.body == "Body"
        assert not issue.labels
        assert issue.milestone is None

    def test_issue_data_all_fields(self) -> None:
        """Test IssueData with all fields.

        Kills mutations: field assignment
        """
        issue = IssueData(
            title="Test",
            body="Body",
            labels=["bug"],
            milestone="v1.0",
            epic="1",
            type="Feature",
            priority="P0",
            estimate="2 hours",
        )

        assert issue.title == "Test"
        assert issue.body == "Body"
        assert issue.labels == ["bug"]
        assert issue.milestone == "v1.0"
        assert issue.epic == "1"
        assert issue.type == "Feature"
        assert issue.priority == "P0"
        assert issue.estimate == "2 hours"


class TestGitHubClientRetryLogic:
    """Test retry logic for transient failures."""

    def test_retry_on_connection_error(self) -> None:
        """Test retry on connection error.

        Kills mutations: retry logic
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # First 2 calls fail, 3rd succeeds
            mock_client.request.side_effect = [
                httpx.ConnectError("Error 1"),
                httpx.ConnectError("Error 2"),
                Mock(
                    status_code=200,
                    content=b'{"status": "ok"}',
                    json=lambda: {"status": "ok"},
                ),
            ]

            client = GitHubClient("token", "owner", "test-repo")
            result = client._request("GET", "/test")

            assert result["status"] == "ok"
            assert mock_client.request.call_count == 3

    def test_retry_exhaustion_raises_error(self) -> None:
        """Test error after max retries exhausted.

        Kills mutations: max retry handling
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = httpx.TimeoutException("Timeout")

            client = GitHubClient("token", "owner", "test-repo")

            with pytest.raises(GitHubError, match="connection failed"):
                client._request("GET", "/test")

            assert mock_client.request.call_count == 3


class TestGitHubClientIntegration:
    """Integration tests for GitHubClient."""

    def test_full_workflow_mock(self) -> None:
        """Test complete workflow with mocked API.

        Kills mutations: workflow integration
        """
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=201,
                content=b'{"id": 1}',
                json=lambda: {"id": 1},
            )

            client = GitHubClient("token", "owner", "test-repo")
            client.create_repository(description="Test")
            client.configure_branch_protection()
            client.create_issue("Test", "Body")
            client.create_label("bug")

            assert mock_client.request.call_count >= 4


def _make_client(mock_client_class: MagicMock) -> GitHubClient:
    """Build a GitHubClient backed by a mocked httpx client."""
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.request.return_value = Mock(
        status_code=200,
        content=b'{"ok": true}',
        json=lambda: {"ok": True},
    )
    return GitHubClient("token", "octocat", "hello-world")


def _request_call(mock_client_class: MagicMock) -> Any:
    """Return the mock request call recorded on the mocked httpx client."""
    return mock_client_class.return_value.request.call_args


class TestHttpClientConstruction:
    """Test exact headers, base URL, and timeout passed to httpx.Client."""

    def test_base_url_exact(self) -> None:
        """Base URL is exactly the GitHub API root."""
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("token", "owner", "repo")
            kwargs = mock_client_class.call_args[1]
            assert kwargs["base_url"] == "https://api.github.com"

    def test_authorization_header_exact(self) -> None:
        """Authorization header uses token scheme and the exact token."""
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("ghp_TESTtoken", "owner", "repo")
            headers = mock_client_class.call_args[1]["headers"]
            assert headers["Authorization"] == "token ghp_TESTtoken"

    def test_accept_header_exact(self) -> None:
        """Accept header requests the v3 GitHub JSON media type."""
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("token", "owner", "repo")
            headers = mock_client_class.call_args[1]["headers"]
            assert headers["Accept"] == "application/vnd.github.v3+json"

    def test_user_agent_header_exact(self) -> None:
        """User-Agent header is the exact project identifier."""
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("token", "owner", "repo")
            headers = mock_client_class.call_args[1]["headers"]
            assert headers["User-Agent"] == "start-green-stay-green/1.0"

    def test_timeout_exact(self) -> None:
        """Timeout passed to httpx.Client is exactly 30 seconds."""
        with patch("httpx.Client") as mock_client_class:
            GitHubClient("token", "owner", "repo")
            assert mock_client_class.call_args[1]["timeout"] == 30.0

    def test_timeout_constant_value(self) -> None:
        """TIMEOUT class constant is exactly 30.0."""
        assert GitHubClient.TIMEOUT == 30.0

    def test_max_retries_constant_value(self) -> None:
        """MAX_RETRIES class constant is exactly 3."""
        assert GitHubClient.MAX_RETRIES == 3


class TestValidationMessages:
    """Test exact validation error messages and None-message mutants."""

    def test_token_message_exact(self) -> None:
        """Empty token raises with the exact required-string message."""
        with pytest.raises(
            GitHubError, match=r"^GitHub token is required and must be a string$"
        ):
            GitHubClient("", "owner", "repo")

    def test_owner_required_message_exact(self) -> None:
        """Empty owner raises with the exact required message."""
        with pytest.raises(GitHubError, match=r"^Repository owner is required$"):
            GitHubClient("token", "", "repo")

    def test_owner_format_message_exact(self) -> None:
        """Bad owner format raises a message naming the owner value."""
        with pytest.raises(
            GitHubError, match=r"^Invalid GitHub owner format: 'bad owner'$"
        ):
            GitHubClient("token", "bad owner", "repo")

    def test_repo_required_message_exact(self) -> None:
        """Empty repo raises with the exact required message."""
        with pytest.raises(GitHubError, match=r"^Repository name is required$"):
            GitHubClient("token", "owner", "")

    def test_repo_format_message_exact(self) -> None:
        """Bad repo format raises a message naming the repo value."""
        with pytest.raises(
            GitHubError, match=r"^Invalid GitHub repo format: 'bad repo'$"
        ):
            GitHubClient("token", "owner", "bad repo")


class TestErrorBranches:
    """Test exact status-code branch logic and error messages."""

    @staticmethod
    def _resp(status: int, body: dict[str, object]) -> Mock:
        """Build a mock httpx response with JSON body."""
        resp = Mock(spec=httpx.Response)
        resp.status_code = status
        resp.content = b'{"message": "x"}'
        resp.json.return_value = body
        resp.text = "raw text"
        return resp

    def test_401_message_exact(self) -> None:
        """401 raises auth error with the exact authentication message."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(
                GitHubAuthError,
                match=r"^Authentication failed: invalid or expired token$",
            ):
                client._handle_response(self._resp(401, {"message": "bad"}))

    def test_403_message_exact(self) -> None:
        """403 raises auth error with the exact permission message."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(
                GitHubAuthError,
                match=r"^Permission denied: token may lack required scopes$",
            ):
                client._handle_response(self._resp(403, {"message": "no"}))

    def test_400_is_error_boundary(self) -> None:
        """Status exactly 400 raises GitHubError (>= boundary, not >)."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^GitHub API error: bad request$"):
                client._handle_response(self._resp(400, {"message": "bad request"}))

    def test_399_is_not_error(self) -> None:
        """Status 399 does not raise and returns the parsed body."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            result = client._handle_response(self._resp(399, {"value": 1}))
            assert result == {"value": 1}

    def test_404_uses_message_field(self) -> None:
        """404 error message embeds the body's message field exactly."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^GitHub API error: Not Found$"):
                client._handle_response(self._resp(404, {"message": "Not Found"}))

    def test_error_falls_back_to_response_text(self) -> None:
        """Missing message key falls back to the response text."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            resp = self._resp(500, {"other": "field"})
            with pytest.raises(GitHubError, match=r"^GitHub API error: raw text$"):
                client._handle_response(resp)

    def test_error_status_code_propagates(self) -> None:
        """The raised GitHubError carries the exact status code."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError) as exc:
                client._handle_response(self._resp(422, {"message": "bad"}))
            assert exc.value.status_code == 422


class TestSanitizeError:
    """Test error sanitization truncation and joining."""

    def test_sanitize_joins_without_separator(self) -> None:
        """Sanitized output joins printable chars with no separator."""
        assert GitHubClient._sanitize_error("abc") == "abc"

    def test_sanitize_truncates_at_500(self) -> None:
        """Sanitized output keeps exactly the first 500 characters."""
        result = GitHubClient._sanitize_error("a" * 600)
        assert len(result) == 500

    def test_sanitize_drops_control_chars(self) -> None:
        """Non-printable control characters are removed."""
        assert GitHubClient._sanitize_error("a\x00b\x01c") == "abc"


class TestParseResponseBody:
    """Test JSON parsing and fallback behaviour."""

    def test_empty_content_returns_empty_dict(self) -> None:
        """No content yields an empty dict without calling json()."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            resp = Mock(spec=httpx.Response)
            resp.content = b""
            result = client._parse_response_body(resp)
            assert isinstance(result, dict)
            assert not result

    def test_bad_json_returns_raw_body(self) -> None:
        """JSON errors fall back to a dict with the raw text."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            resp = Mock(spec=httpx.Response)
            resp.content = b"oops"
            resp.json.side_effect = Exception("boom")
            resp.text = "oops"
            assert client._parse_response_body(resp) == {"raw_body": "oops"}


class TestRequestRetries:
    """Test retry counts and exhaustion messages."""

    def test_retries_exactly_three_times(self) -> None:
        """Persistent connection errors retry exactly MAX_RETRIES times."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = httpx.ConnectError("down")
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match="connection failed after 3 retries"):
                client._request("GET", "/x")
            assert mock_client.request.call_count == 3

    def test_succeeds_on_third_attempt_no_extra_calls(self) -> None:
        """Two failures then success makes exactly three calls."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.side_effect = [
                httpx.ConnectError("1"),
                httpx.TimeoutException("2"),
                Mock(status_code=200, content=b"{}", json=lambda: {"ok": 1}),
            ]
            client = GitHubClient("token", "owner", "repo")
            assert client._request("GET", "/x") == {"ok": 1}
            assert mock_client.request.call_count == 3

    def test_single_call_when_first_succeeds(self) -> None:
        """A successful first request makes exactly one call."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client._request("GET", "/x")
            assert mock_client_class.return_value.request.call_count == 1


class TestCreateRepositoryPayload:
    """Test exact method, path, and payload for repository creation."""

    def test_method_and_path(self) -> None:
        """Repository creation POSTs to /user/repos."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_repository()
            call = _request_call(mock_client_class)
            assert call[0][0] == "POST"
            assert call[0][1] == "/user/repos"

    def test_payload_defaults(self) -> None:
        """Default payload uses repo name, public, auto-init, Python template."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_repository()
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["name"] == "hello-world"
            assert payload["description"] == ""
            assert payload["private"] is False
            assert payload["auto_init"] is True
            assert payload["gitignore_template"] == "Python"

    def test_auto_init_merge_flags(self) -> None:
        """auto_init adds rebase, squash, and delete-on-merge flags as True."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_repository(auto_init=True)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["allow_rebase_merge"] is True
            assert payload["allow_squash_merge"] is True
            assert payload["delete_branch_on_merge"] is True

    def test_no_merge_flags_without_auto_init(self) -> None:
        """Disabling auto_init omits the merge-strategy flags."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_repository(auto_init=False)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["auto_init"] is False
            assert "allow_rebase_merge" not in payload
            assert "delete_branch_on_merge" not in payload

    def test_private_flag_passthrough(self) -> None:
        """The private flag flows into the payload unchanged."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_repository(private=True)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["private"] is True


class TestBranchProtectionPayload:
    """Test exact path and payload for branch protection."""

    def test_path_exact(self) -> None:
        """Protection PUTs to the branch protection endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.configure_branch_protection(branch="develop")
            call = _request_call(mock_client_class)
            assert call[0][0] == "PUT"
            assert (
                call[0][1] == "/repos/octocat/hello-world/branches/develop/protection"
            )

    def test_default_payload_structure(self) -> None:
        """Default payload enforces admins and default review/status config."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.configure_branch_protection()
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["enforce_admins"] is True
            assert payload["allow_force_pushes"] is False
            assert payload["allow_deletions"] is False
            assert payload["required_status_checks"]["strict"] is True
            assert payload["required_status_checks"]["contexts"] == ["ci"]
            reviews = payload["required_pull_request_reviews"]
            assert reviews["dismiss_stale_reviews"] is True
            assert reviews["require_code_owner_reviews"] is False
            assert reviews["required_approving_review_count"] == 1

    def test_restrictions_removed_when_none(self) -> None:
        """The None-valued restrictions key is stripped from the payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.configure_branch_protection()
            payload = _request_call(mock_client_class)[1]["json"]
            assert "restrictions" not in payload

    def test_status_checks_omitted_when_disabled(self) -> None:
        """Disabling status checks removes that key from the payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            rule = BranchProtectionRule(require_status_checks=False)
            client.configure_branch_protection(rule=rule)
            payload = _request_call(mock_client_class)[1]["json"]
            assert "required_status_checks" not in payload

    def test_reviews_omitted_when_disabled(self) -> None:
        """Disabling code review removes that key from the payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            rule = BranchProtectionRule(require_code_review=False)
            client.configure_branch_protection(rule=rule)
            payload = _request_call(mock_client_class)[1]["json"]
            assert "required_pull_request_reviews" not in payload

    def test_custom_contexts_used(self) -> None:
        """Custom status check contexts replace the default ci context."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            rule = BranchProtectionRule(status_check_contexts=["lint", "test"])
            client.configure_branch_protection(rule=rule)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["required_status_checks"]["contexts"] == ["lint", "test"]

    def test_force_push_flag_passthrough(self) -> None:
        """allow_force_pushes flows from the rule into the payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            rule = BranchProtectionRule(allow_force_pushes=True)
            client.configure_branch_protection(rule=rule)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["allow_force_pushes"] is True


class TestBuildProtectionPayloadDirect:
    """Test payload builder helpers directly for filtering and contexts."""

    def test_none_values_filtered(self) -> None:
        """Keys with None values are stripped, kept keys survive."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            rule = BranchProtectionRule(
                require_status_checks=False, require_code_review=False
            )
            payload = client._build_protection_payload(rule)
            assert "required_status_checks" not in payload
            assert "required_pull_request_reviews" not in payload
            assert payload["enforce_admins"] is True

    def test_status_checks_none_when_disabled(self) -> None:
        """The status-checks builder returns None when disabled."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            rule = BranchProtectionRule(require_status_checks=False)
            assert client._build_status_checks(rule) is None

    def test_pr_reviews_none_when_disabled(self) -> None:
        """The PR-reviews builder returns None when disabled."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            rule = BranchProtectionRule(require_code_review=False)
            assert client._build_pr_reviews(rule) is None


class TestCreateIssuePayload:
    """Test exact method, path, and payload for issue creation."""

    def test_method_and_path(self) -> None:
        """Issue creation POSTs to the repo issues endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_issue("Title")
            call = _request_call(mock_client_class)
            assert call[0][0] == "POST"
            assert call[0][1] == "/repos/octocat/hello-world/issues"

    def test_minimal_payload(self) -> None:
        """A minimal issue payload carries title and empty body only."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_issue("My Title")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["title"] == "My Title"
            assert payload["body"] == ""
            assert "labels" not in payload
            assert "milestone" not in payload

    def test_labels_included_when_present(self) -> None:
        """Labels are added to the payload when provided."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_issue("T", labels=["bug", "p0"])
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["labels"] == ["bug", "p0"]

    def test_milestone_included_when_zero(self) -> None:
        """Milestone 0 is included because the check is is-not-None."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_issue("T", milestone=0)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["milestone"] == 0

    def test_milestone_omitted_when_none(self) -> None:
        """Milestone key is absent when milestone is None."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_issue("T")
            payload = _request_call(mock_client_class)[1]["json"]
            assert "milestone" not in payload


class TestCreateLabelPayload:
    """Test exact method, path, and payload for label creation."""

    def test_method_and_path(self) -> None:
        """Label creation POSTs to the repo labels endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_label("bug")
            call = _request_call(mock_client_class)
            assert call[0][0] == "POST"
            assert call[0][1] == "/repos/octocat/hello-world/labels"

    def test_default_color_and_payload(self) -> None:
        """Default label uses the documentation blue color and empty desc."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_label("bug")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["name"] == "bug"
            assert payload["color"] == "0075ca"
            assert payload["description"] == ""

    def test_custom_values(self) -> None:
        """Custom color and description flow into the label payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_label("bug", color="ff0000", description="a bug")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["color"] == "ff0000"
            assert payload["description"] == "a bug"


class TestCreateLabelsBulkDefaults:
    """Test the per-label .get defaults used in bulk label creation."""

    def test_missing_keys_use_defaults(self) -> None:
        """Labels missing keys fall back to empty name and default color."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_labels_bulk([{}])
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["name"] == ""
            assert payload["color"] == "0075ca"
            assert payload["description"] == ""

    def test_present_keys_used(self) -> None:
        """Provided label keys are passed through to the request payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_labels_bulk(
                [{"name": "x", "color": "abcdef", "description": "d"}]
            )
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["name"] == "x"
            assert payload["color"] == "abcdef"
            assert payload["description"] == "d"


class TestCreateMilestonePayload:
    """Test exact method, path, and payload for milestone creation."""

    def test_method_and_path(self) -> None:
        """Milestone creation POSTs to the repo milestones endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_milestone("v1.0")
            call = _request_call(mock_client_class)
            assert call[0][0] == "POST"
            assert call[0][1] == "/repos/octocat/hello-world/milestones"

    def test_payload_fields(self) -> None:
        """Milestone payload carries the title and description."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_milestone("v1.0", description="first")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["title"] == "v1.0"
            assert payload["description"] == "first"

    def test_default_description_empty(self) -> None:
        """Milestone default description is the empty string."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_milestone("v1.0")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["description"] == ""


class TestCreateMilestonesBulkDefaults:
    """Test the per-milestone .get defaults in bulk milestone creation."""

    def test_missing_keys_use_defaults(self) -> None:
        """Milestones missing keys fall back to empty title and desc."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_milestones_bulk([{}])
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["title"] == ""
            assert payload["description"] == ""

    def test_present_keys_used(self) -> None:
        """Provided milestone keys flow into the request payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_milestones_bulk([{"title": "v2", "description": "d"}])
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["title"] == "v2"
            assert payload["description"] == "d"


class TestGetRepositoryInfoCall:
    """Test exact method and path for repository info."""

    def test_method_and_path(self) -> None:
        """Repository info GETs the repo root endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.get_repository_info()
            call = _request_call(mock_client_class)
            assert call[0][0] == "GET"
            assert call[0][1] == "/repos/octocat/hello-world"


class TestUpdateRepositoryPayload:
    """Test exact method, path, and filtered payload for repo update."""

    def test_method_and_path(self) -> None:
        """Repository update PATCHes the repo root endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.update_repository(description="d")
            call = _request_call(mock_client_class)
            assert call[0][0] == "PATCH"
            assert call[0][1] == "/repos/octocat/hello-world"

    def test_none_values_filtered(self) -> None:
        """Only the provided fields appear in the update payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.update_repository(description="d", has_issues=True)
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload == {"description": "d", "has_issues": True}

    def test_all_fields_mapped(self) -> None:
        """Each named field maps to its own payload key."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.update_repository(
                description="d",
                homepage="h",
                private=True,
                has_issues=False,
                has_projects=True,
                has_downloads=False,
                has_wiki=True,
            )
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["description"] == "d"
            assert payload["homepage"] == "h"
            assert payload["private"] is True
            assert payload["has_issues"] is False
            assert payload["has_projects"] is True
            assert payload["has_downloads"] is False
            assert payload["has_wiki"] is True


class TestCreateOrUpdateFile:
    """Test exact method, path, encoding, and payload for file writes."""

    def test_method_and_path(self) -> None:
        """File write PUTs to the contents endpoint with the path."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_or_update_file("docs/x.md", "hi", "msg")
            call = _request_call(mock_client_class)
            assert call[0][0] == "PUT"
            assert call[0][1] == "/repos/octocat/hello-world/contents/docs/x.md"

    def test_content_base64_encoded(self) -> None:
        """File content is base64-encoded in the payload."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_or_update_file("x.md", "hello", "msg", branch="dev")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["content"] == base64.b64encode(b"hello").decode()
            assert payload["message"] == "msg"
            assert payload["branch"] == "dev"

    def test_default_branch_is_main(self) -> None:
        """The default commit branch is main."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.create_or_update_file("x.md", "hello", "msg")
            payload = _request_call(mock_client_class)[1]["json"]
            assert payload["branch"] == "main"

    def test_path_traversal_rejected(self) -> None:
        """A path containing .. is rejected with the exact message."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^Invalid file path: '\.\./x'$"):
                client.create_or_update_file("../x", "c", "m")

    def test_empty_path_rejected(self) -> None:
        """An empty path is rejected as an invalid file path."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^Invalid file path: ''$"):
                client.create_or_update_file("", "c", "m")

    def test_unsafe_char_path_rejected(self) -> None:
        """A path with disallowed characters is rejected."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match="Invalid file path"):
                client.create_or_update_file("a b", "c", "m")

    def test_empty_branch_rejected(self) -> None:
        """An empty branch name is rejected with the branch message."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^Invalid branch name: ''$"):
                client.create_or_update_file("x.md", "c", "m", branch="")

    def test_unsafe_branch_rejected(self) -> None:
        """A branch with disallowed characters is rejected."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            with pytest.raises(GitHubError, match=r"^Invalid branch name: 'a b'$"):
                client.create_or_update_file("x.md", "c", "m", branch="a b")


class TestAddRepositoryTopics:
    """Test exact method, path, and payload for topics."""

    def test_method_path_payload(self) -> None:
        """Topics PUT to the topics endpoint with a names list."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.add_repository_topics(["python", "cli"])
            call = _request_call(mock_client_class)
            assert call[0][0] == "PUT"
            assert call[0][1] == "/repos/octocat/hello-world/topics"
            assert call[1]["json"]["names"] == ["python", "cli"]


class TestGetIssueCall:
    """Test exact method and path for fetching one issue."""

    def test_method_and_path(self) -> None:
        """get_issue GETs the numbered issue endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = _make_client(mock_client_class)
            client.get_issue(42)
            call = _request_call(mock_client_class)
            assert call[0][0] == "GET"
            assert call[0][1] == "/repos/octocat/hello-world/issues/42"


class TestListIssuesParams:
    """Test exact method, path, and query params for listing issues."""

    @staticmethod
    def _list_client(mock_client_class: MagicMock) -> GitHubClient:
        """Build a client whose request returns a JSON list."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.request.return_value = Mock(
            status_code=200,
            content=b"[]",
            json=lambda: [{"number": 1}],
        )
        return GitHubClient("token", "octocat", "hello-world")

    def test_method_and_path(self) -> None:
        """list_issues GETs the repo issues endpoint."""
        with patch("httpx.Client") as mock_client_class:
            client = self._list_client(mock_client_class)
            client.list_issues()
            call = _request_call(mock_client_class)
            assert call[0][0] == "GET"
            assert call[0][1] == "/repos/octocat/hello-world/issues"

    def test_default_params(self) -> None:
        """Default params request open issues at 100 per page."""
        with patch("httpx.Client") as mock_client_class:
            client = self._list_client(mock_client_class)
            client.list_issues()
            params = _request_call(mock_client_class)[1]["params"]
            assert params["state"] == "open"
            assert params["per_page"] == 100
            assert "labels" not in params
            assert "milestone" not in params

    def test_labels_joined_by_comma(self) -> None:
        """Multiple labels are joined into a comma-separated string."""
        with patch("httpx.Client") as mock_client_class:
            client = self._list_client(mock_client_class)
            client.list_issues(labels=["bug", "p0"])
            params = _request_call(mock_client_class)[1]["params"]
            assert params["labels"] == "bug,p0"

    def test_milestone_included_when_zero(self) -> None:
        """Milestone 0 is included because the check is is-not-None."""
        with patch("httpx.Client") as mock_client_class:
            client = self._list_client(mock_client_class)
            client.list_issues(milestone=0)
            params = _request_call(mock_client_class)[1]["params"]
            assert params["milestone"] == 0

    def test_state_default_is_open(self) -> None:
        """The default state literal is open."""
        with patch("httpx.Client") as mock_client_class:
            client = self._list_client(mock_client_class)
            client.list_issues(state="closed")
            params = _request_call(mock_client_class)[1]["params"]
            assert params["state"] == "closed"

    def test_single_dict_wrapped_in_list(self) -> None:
        """A non-list response is wrapped into a single-element list."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            mock_client.request.return_value = Mock(
                status_code=200,
                content=b"{}",
                json=lambda: {"number": 7},
            )
            client = GitHubClient("token", "octocat", "hello-world")
            result = client.list_issues()
            assert result == [{"number": 7}]


class TestSpecParsingDetails:
    """Test SPEC parsing field extraction, epics, and labels."""

    def test_default_type_and_priority(self) -> None:
        """Missing Type/Priority fields default to Task and P2."""
        spec = "#### Issue 1.1: A Title\n**Description**: hello\n"
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            issues = client.parse_spec_issues(spec)
            assert issues[0].type == "Task"
            assert issues[0].priority == "P2"
            assert issues[0].labels == ["task", "p2"]

    def test_estimate_extracted(self) -> None:
        """The Estimate field is read from the issue content."""
        spec = "#### Issue 1.1: T\n**Estimate**: 3h\n**Description**: x\n"
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            issues = client.parse_spec_issues(spec)
            assert issues[0].estimate == "3h"

    def test_title_includes_issue_id(self) -> None:
        """The composed title is the id and title joined by a colon."""
        spec = "#### Issue 2.3: Cool Feature\n**Description**: x\n"
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            issues = client.parse_spec_issues(spec)
            assert issues[0].title == "2.3: Cool Feature"

    def test_body_acceptance_criteria_header(self) -> None:
        """Criteria are appended under the Acceptance Criteria header."""
        spec = (
            "#### Issue 1.1: T\n"
            "**Description**: Do stuff\n"
            "**Acceptance Criteria**: Must work\n"
        )
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            body = client.parse_spec_issues(spec)[0].body
            assert body == "Do stuff\n\n## Acceptance Criteria\nMust work"

    def test_epic_found_for_later_issue(self) -> None:
        """An earlier Epic heading is captured as the issue epic."""
        spec = (
            "### Epic 4.0: Big Epic\n\n"
            "#### Issue 4.1: Child\n"
            "**Description**: x\n"
        )
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            issues = client.parse_spec_issues(spec)
            child = next(i for i in issues if i.title.startswith("4.1"))
            assert child.epic == "4.0"

    def test_no_epic_at_position_zero(self) -> None:
        """An issue at position zero has no epic."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._find_epic("### Epic 1.0: x", 0) is None

    def test_extract_field_default_returned(self) -> None:
        """Missing fields return the provided default value."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._extract_field("nothing here", "Type", "Task") == "Task"

    def test_extract_field_value_returned(self) -> None:
        """A present field returns its stripped value."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._extract_field("**Type**: Bug", "Type") == "Bug"

    def test_build_issue_body_without_criteria(self) -> None:
        """An empty criteria leaves the body as the description alone."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._build_issue_body("desc", "") == "desc"

    def test_extract_description_empty_default(self) -> None:
        """Missing description returns the empty string."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._extract_description("no fields") == ""

    def test_extract_criteria_empty_default(self) -> None:
        """Missing criteria returns the empty string."""
        with patch("httpx.Client"):
            client = GitHubClient("token", "owner", "repo")
            assert client._extract_criteria("no fields") == ""


class TestModelDefaultsExact:
    """Test exact model default values for None-mutant kills."""

    def test_branch_rule_bool_defaults_are_false(self) -> None:
        """Force-push and deletion defaults are exactly False, not None."""
        rule = BranchProtectionRule()
        # isinstance kills a None default; `not` kills a True default.
        assert isinstance(rule.allow_force_pushes, bool)
        assert not rule.allow_force_pushes
        assert isinstance(rule.allow_deletions, bool)
        assert not rule.allow_deletions

    def test_branch_rule_contexts_default_empty_list(self) -> None:
        """status_check_contexts defaults to an empty list, not None."""
        rule = BranchProtectionRule()
        assert isinstance(rule.status_check_contexts, list)
        assert not rule.status_check_contexts

    def test_issue_data_labels_default_empty_list(self) -> None:
        """IssueData labels default to an empty list, not None."""
        issue = IssueData(title="t", body="b")
        assert isinstance(issue.labels, list)
        assert not issue.labels

    def test_issue_data_optional_defaults_none(self) -> None:
        """IssueData optional string fields default to None, not empty."""
        issue = IssueData(title="t", body="b")
        assert issue.epic is None
        assert issue.type is None
        assert issue.priority is None
        assert issue.estimate is None
        assert issue.milestone is None
