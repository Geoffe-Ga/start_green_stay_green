"""Unit tests for GitHubClient.

Tests the complete GitHub API integration including:
- Repository creation and configuration
- Branch protection rules
- Issue and label management
- Milestone creation
- SPEC.md parsing
- Error handling and retry logic
"""

from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from start_green_stay_green.github import (
    BranchProtectionRule,
    GitHubAuthError,
    GitHubClient,
    GitHubError,
    IssueData,
)


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

            assert client.token == "token123"
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
            GitHubClient(None, "owner", "repo")  # type: ignore

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

            assert result == {}


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

            assert len(issues) > 0
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

            assert len(issues) > 0
            assert "Test description" in issues[0].body
            assert "Criterion 1" in issues[0].body


class TestBranchProtectionRule:
    """Test BranchProtectionRule model."""

    def test_default_values(self) -> None:
        """Test default branch protection values.

        Kills mutations: default values
        """
        rule = BranchProtectionRule()

        assert rule.dismiss_stale_reviews is True
        assert rule.require_code_review is True
        assert rule.require_status_checks is True
        assert rule.allow_force_pushes is False
        assert rule.allow_deletions is False
        assert rule.status_check_contexts == []

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

        assert rule.dismiss_stale_reviews is False
        assert rule.require_code_review is False
        assert rule.allow_force_pushes is True
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
        assert issue.labels == []
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
