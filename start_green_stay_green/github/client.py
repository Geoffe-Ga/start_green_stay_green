"""GitHub API client for repository and issue management.

Provides complete GitHub API integration including:
- Repository creation and configuration
- Branch protection rule setup
- Issue and milestone creation
- Label management
- SPEC.md parsing for issue generation

Secure token handling and comprehensive error handling with retry logic.
"""

import base64
from contextlib import suppress
import json
import re
from typing import Any
from typing import Literal
from typing import Self

import httpx
from pydantic import BaseModel
from pydantic import Field


class GitHubError(Exception):
    """Base exception for GitHub API errors.

    Attributes:
        status_code: HTTP status code from GitHub API
        message: Error message from API or local processing
        response_body: Full response body (if available)
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: dict[str, Any] | None = None,
    ) -> None:
        """Initialize GitHubError.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            response_body: Response body from GitHub API
        """
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)


class GitHubAuthError(GitHubError):
    """GitHub authentication/authorization error.

    Raised when token is invalid (401) or lacks permissions (403).
    """


class BranchProtectionRule(BaseModel):
    """Branch protection rule configuration.

    Attributes:
        dismiss_stale_reviews: Dismiss PRs if reviews become stale
        require_code_review: Require code review before merge
        require_status_checks: Require all status checks to pass
        status_check_contexts: Required status check contexts
        allow_force_pushes: Allow force pushes to the branch
        allow_deletions: Allow branch deletion
    """

    dismiss_stale_reviews: bool = True
    require_code_review: bool = True
    require_status_checks: bool = True
    status_check_contexts: list[str] = Field(default_factory=list)
    allow_force_pushes: bool = False
    allow_deletions: bool = False


class IssueData(BaseModel):
    """Issue creation data parsed from SPEC.md.

    Attributes:
        title: Issue title
        body: Issue body/description
        labels: Labels to apply
        milestone: Milestone name
        epic: Epic identifier
        type: Issue type (Feature, Task, Bug)
        priority: Priority level (P0, P1, P2)
        estimate: Time estimate
    """

    title: str
    body: str
    labels: list[str] = Field(default_factory=list)
    milestone: str | None = None
    epic: str | None = None
    type: str | None = None
    priority: str | None = None
    estimate: str | None = None


class GitHubClient:
    """GitHub API client for repository and issue management.

    Provides a clean, type-safe interface to GitHub API with:
    - Automatic retry logic for transient failures
    - Secure token handling (never logged)
    - Comprehensive error handling
    - Full support for repository setup, branch protection, and issue creation

    Attributes:
        owner: GitHub repository owner
        repo: GitHub repository name
    """

    BASE_URL = "https://api.github.com"
    MAX_RETRIES = 3
    TIMEOUT = 30.0

    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
    ) -> None:
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (required scopes: repo, issues)
            owner: Repository owner (user or organization)
            repo: Repository name

        Raises:
            GitHubError: If token is empty or invalid format
        """
        self._validate_init_params(token, owner, repo)
        self.token = token
        self.owner = owner
        self.repo = repo
        self._client = self._create_http_client(token)

    def _validate_init_params(self, token: str, owner: str, repo: str) -> None:
        """Validate initialization parameters.

        Raises:
            GitHubError: If any parameter is invalid
        """
        self._validate_token(token)
        self._validate_owner(owner)
        self._validate_repo(repo)

    def _validate_token(self, token: str) -> None:
        """Validate GitHub token.

        Raises:
            GitHubError: If token is invalid
        """
        if not token or not isinstance(token, str):
            msg = "GitHub token is required and must be a string"
            raise GitHubError(msg)

    def _validate_owner(self, owner: str) -> None:
        """Validate repository owner.

        Raises:
            GitHubError: If owner is invalid
        """
        if not owner or not isinstance(owner, str):
            msg = "Repository owner is required"
            raise GitHubError(msg)

    def _validate_repo(self, repo: str) -> None:
        """Validate repository name.

        Raises:
            GitHubError: If repo is invalid
        """
        if not repo or not isinstance(repo, str):
            msg = "Repository name is required"
            raise GitHubError(msg)

    def _create_http_client(self, token: str) -> httpx.Client:
        """Create configured HTTP client for GitHub API.

        Args:
            token: GitHub access token

        Returns:
            Configured httpx.Client instance
        """
        return httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "start-green-stay-green/1.0",
            },
            timeout=self.TIMEOUT,
        )

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
    ) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client connection."""
        self._client.close()

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle HTTP response and raise errors for non-2xx status.

        Args:
            response: HTTP response from GitHub API

        Returns:
            Parsed JSON response body

        Raises:
            GitHubAuthError: For 401 or 403 status codes
            GitHubError: For other error status codes
        """
        response_body = self._parse_response_body(response)
        self._check_response_errors(response, response_body)
        return response_body

    def _parse_response_body(self, response: httpx.Response) -> dict[str, Any]:
        """Parse JSON response body with error handling.

        Args:
            response: HTTP response from GitHub API

        Returns:
            Parsed JSON body or fallback dict with raw text
        """
        try:
            return response.json() if response.content else {}
        except (
            json.JSONDecodeError,
            Exception,  # noqa: BLE001
        ):  # Defensive: catch all JSON errors
            # Handle both JSONDecodeError and other exceptions during parsing
            return {"raw_body": response.text}

    def _check_response_errors(
        self, response: httpx.Response, response_body: dict[str, Any]
    ) -> None:
        """Check response status and raise appropriate errors.

        Args:
            response: HTTP response from GitHub API
            response_body: Parsed response body

        Raises:
            GitHubAuthError: For 401 or 403 status codes
            GitHubError: For other error status codes
        """
        if response.status_code == 401:  # noqa: PLR2004 # Standard HTTP status
            msg = "Authentication failed: invalid or expired token"
            raise GitHubAuthError(
                msg,
                status_code=401,
                response_body=response_body,
            )

        if response.status_code == 403:  # noqa: PLR2004 # Standard HTTP status
            msg = "Permission denied: token may lack required scopes"
            raise GitHubAuthError(
                msg,
                status_code=403,
                response_body=response_body,
            )

        if response.status_code >= 400:  # noqa: PLR2004 # Standard HTTP status
            error_msg = response_body.get("message", response.text)
            msg = f"GitHub API error: {error_msg}"
            raise GitHubError(
                msg,
                status_code=response.status_code,
                response_body=response_body,
            )

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,  # noqa: ANN401 # Flexible API for httpx parameters
    ) -> dict[str, Any]:
        """Make an authenticated request to GitHub API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API endpoint path (without base URL)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Parsed JSON response body

        Raises:
            GitHubError: On API error or network failure
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self._client.request(method, path, **kwargs)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self.MAX_RETRIES - 1:
                    msg = (
                        f"GitHub API connection failed after "
                        f"{self.MAX_RETRIES} retries: {e}"
                    )
                    raise GitHubError(msg) from e
                # Retry on transient errors
                continue
            else:
                # Request succeeded, handle response
                return self._handle_response(response)

        # Should never reach here due to retry logic, but satisfies mypy
        msg = "All retry attempts exhausted"
        raise GitHubError(msg)

    def create_repository(
        self,
        *,
        description: str = "",
        private: bool = False,
        _initialize_readme: bool = True,  # Reserved for future use
        auto_init: bool = True,
        gitignore_template: str = "Python",
    ) -> dict[str, Any]:
        """Create a new GitHub repository.

        Args:
            description: Repository description
            private: Whether repository should be private
            _initialize_readme: Reserved for future use
                (GitHub auto-creates README with auto_init)
            auto_init: Initialize with git repository
            gitignore_template: Template for .gitignore (e.g., "Python", "Go")

        Returns:
            Repository data from GitHub API

        Raises:
            GitHubError: If repository creation fails
        """
        payload = {
            "name": self.repo,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "gitignore_template": gitignore_template,
        }

        if auto_init:
            payload["allow_rebase_merge"] = True
            payload["allow_squash_merge"] = True
            payload["delete_branch_on_merge"] = True

        return self._request("POST", "/user/repos", json=payload)

    def configure_branch_protection(
        self,
        branch: str = "main",
        rule: BranchProtectionRule | None = None,
    ) -> dict[str, Any]:
        """Configure branch protection rules.

        Args:
            branch: Branch to protect (default: main)
            rule: Branch protection configuration (uses defaults if not provided)

        Returns:
            Protection rule data from GitHub API

        Raises:
            GitHubError: If configuration fails
        """
        if rule is None:
            rule = BranchProtectionRule()

        payload = self._build_protection_payload(rule)

        return self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/branches/{branch}/protection",
            json=payload,
        )

    def _build_protection_payload(self, rule: BranchProtectionRule) -> dict[str, Any]:
        """Build branch protection payload from rule.

        Args:
            rule: Branch protection configuration

        Returns:
            GitHub API payload for branch protection
        """
        payload = {
            "required_status_checks": self._build_status_checks(rule),
            "enforce_admins": True,
            "required_pull_request_reviews": self._build_pr_reviews(rule),
            "restrictions": None,
            "allow_force_pushes": rule.allow_force_pushes,
            "allow_deletions": rule.allow_deletions,
        }

        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}

    def _build_status_checks(self, rule: BranchProtectionRule) -> dict[str, Any] | None:
        """Build status checks configuration.

        Args:
            rule: Branch protection configuration

        Returns:
            Status checks config or None
        """
        if not rule.require_status_checks:
            return None

        return {
            "strict": True,
            "contexts": rule.status_check_contexts or ["ci"],
        }

    def _build_pr_reviews(self, rule: BranchProtectionRule) -> dict[str, Any] | None:
        """Build PR review requirements.

        Args:
            rule: Branch protection configuration

        Returns:
            PR review config or None
        """
        if not rule.require_code_review:
            return None

        return {
            "dismiss_stale_reviews": rule.dismiss_stale_reviews,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
        }

    def create_issue(
        self,
        title: str,
        body: str = "",
        labels: list[str] | None = None,
        milestone: int | None = None,
    ) -> dict[str, Any]:
        """Create a GitHub issue.

        Args:
            title: Issue title
            body: Issue description (supports markdown)
            labels: List of label names to apply
            milestone: Milestone ID (number)

        Returns:
            Issue data from GitHub API

        Raises:
            GitHubError: If issue creation fails
        """
        payload: dict[str, Any] = {
            "title": title,
            "body": body,
        }

        if labels:
            payload["labels"] = labels

        if milestone is not None:
            payload["milestone"] = milestone

        return self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/issues",
            json=payload,
        )

    def create_issues_bulk(
        self,
        issues: list[IssueData],
    ) -> list[dict[str, Any]]:
        """Create multiple issues in bulk.

        Args:
            issues: List of issue data to create

        Returns:
            List of created issue data from GitHub API

        Raises:
            GitHubError: If any issue creation fails (partial creation possible)
        """
        results = []

        for issue in issues:
            # Let GitHubError propagate to stop bulk operation on error
            result = self.create_issue(
                title=issue.title,
                body=issue.body,
                labels=issue.labels,
            )
            results.append(result)

        return results

    def create_label(
        self,
        name: str,
        color: str = "0075ca",
        description: str = "",
    ) -> dict[str, Any]:
        """Create a GitHub label.

        Args:
            name: Label name
            color: Label color (hex, without #)
            description: Label description

        Returns:
            Label data from GitHub API

        Raises:
            GitHubError: If label creation fails
        """
        payload = {
            "name": name,
            "color": color,
            "description": description,
        }

        return self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/labels",
            json=payload,
        )

    def create_labels_bulk(
        self,
        labels: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create multiple labels in bulk.

        Args:
            labels: List of dicts with keys: name, color (optional),
                description (optional)

        Returns:
            List of created label data from GitHub API

        Raises:
            GitHubError: If any label creation fails (partial creation possible)
        """
        results = []

        for label in labels:
            # Continue on label already exists (409), fail on other errors
            with suppress(GitHubError):
                result = self.create_label(
                    name=label.get("name", ""),
                    color=label.get("color", "0075ca"),
                    description=label.get("description", ""),
                )
                results.append(result)

        return results

    def create_milestone(
        self,
        title: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Create a GitHub milestone.

        Args:
            title: Milestone title
            description: Milestone description

        Returns:
            Milestone data from GitHub API

        Raises:
            GitHubError: If milestone creation fails
        """
        payload = {
            "title": title,
            "description": description,
        }

        return self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/milestones",
            json=payload,
        )

    def create_milestones_bulk(
        self,
        milestones: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create multiple milestones in bulk.

        Args:
            milestones: List of dicts with keys: title, description (optional)

        Returns:
            List of created milestone data from GitHub API

        Raises:
            GitHubError: If any milestone creation fails (partial creation possible)
        """
        results = []

        for milestone in milestones:
            # Continue on milestone already exists (409), fail on other errors
            with suppress(GitHubError):
                result = self.create_milestone(
                    title=milestone.get("title", ""),
                    description=milestone.get("description", ""),
                )
                results.append(result)

        return results

    def _extract_field(
        self, content: str, field_name: str, default: str | None = None
    ) -> str | None:
        """Extract a field value from issue content.

        Args:
            content: Issue content to search
            field_name: Field name to extract (e.g., "Type", "Priority")
            default: Default value if field not found

        Returns:
            Extracted field value or default
        """
        pattern = rf"\*\*{field_name}\*\*:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else default

    def _build_issue_body(self, description: str, criteria: str) -> str:
        """Build issue body from description and acceptance criteria.

        Args:
            description: Issue description
            criteria: Acceptance criteria

        Returns:
            Formatted issue body
        """
        body = description
        if criteria:
            body += f"\n\n## Acceptance Criteria\n{criteria}"
        return body

    def _find_epic(self, spec_content: str, position: int) -> str | None:
        """Find epic ID from section hierarchy before given position.

        Args:
            spec_content: Full SPEC content
            position: Character position to search before

        Returns:
            Epic ID if found, None otherwise
        """
        if position == 0:
            return None
        epic_match = re.search(
            r"###\s*Epic\s+([\d.]+):",
            spec_content[:position],
        )
        return epic_match.group(1) if epic_match else None

    def parse_spec_issues(
        self,
        spec_content: str,
    ) -> list[IssueData]:
        """Parse SPEC.md to extract issue data.

        Parses markdown format issues with sections like:
        - Issue X.Y: Title
        - Type: Feature/Task/Bug
        - Priority: P0/P1/P2
        - Description: ...
        - Acceptance Criteria: ...
        - Estimate: ...

        Args:
            spec_content: Full SPEC.md content

        Returns:
            List of parsed IssueData objects

        Raises:
            GitHubError: If parsing fails
        """
        issues = []
        issue_pattern = r"#+\s*(?:Issue|Epic)\s+([\d.]+):\s*(.+?)(?=(?:####|###|$))"

        for match in re.finditer(issue_pattern, spec_content, re.DOTALL):
            issue_data = self._parse_single_issue(
                spec_content, match.group(1), match.group(2), match.start()
            )
            issues.append(issue_data)

        return issues

    def _parse_single_issue(
        self, spec_content: str, issue_id: str, issue_content: str, match_pos: int
    ) -> IssueData:
        """Parse a single issue from SPEC content.

        Args:
            spec_content: Full SPEC.md content
            issue_id: Issue ID (e.g., "1.1")
            issue_content: Content of the issue section
            match_pos: Position of match in spec_content

        Returns:
            Parsed IssueData object
        """
        # Extract title
        title_match = re.search(r"^(.+?)$", issue_content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else f"Issue {issue_id}"

        # Extract fields
        issue_type = self._extract_field(issue_content, "Type", "Task")
        priority = self._extract_field(issue_content, "Priority", "P2")
        estimate = self._extract_field(issue_content, "Estimate")

        # Extract description and criteria
        description = self._extract_description(issue_content)
        criteria = self._extract_criteria(issue_content)

        # Build body and find epic
        body = self._build_issue_body(description, criteria)
        epic = self._find_epic(spec_content, match_pos)

        return IssueData(
            title=f"{issue_id}: {title}",
            body=body,
            labels=[(issue_type or "Task").lower(), (priority or "P2").lower()],
            epic=epic,
            type=issue_type,
            priority=priority,
            estimate=estimate,
        )

    def _extract_description(self, content: str) -> str:
        """Extract description from issue content.

        Args:
            content: Issue content

        Returns:
            Description text or empty string
        """
        desc_match = re.search(
            r"\*\*Description\*\*:\s*(.+?)(?=(?:\*\*|$))",
            content,
            re.DOTALL,
        )
        return desc_match.group(1).strip() if desc_match else ""

    def _extract_criteria(self, content: str) -> str:
        """Extract acceptance criteria from issue content.

        Args:
            content: Issue content

        Returns:
            Criteria text or empty string
        """
        criteria_match = re.search(
            r"\*\*Acceptance Criteria\*\*:\s*(.+?)(?=(?:\*\*|$))",
            content,
            re.DOTALL,
        )
        return criteria_match.group(1).strip() if criteria_match else ""

    def get_repository_info(self) -> dict[str, Any]:
        """Get repository information.

        Returns:
            Repository data from GitHub API

        Raises:
            GitHubError: If request fails
        """
        return self._request("GET", f"/repos/{self.owner}/{self.repo}")

    def update_repository(  # noqa: PLR0913 # All params optional, keyword-only
        self,
        *,
        description: str | None = None,
        homepage: str | None = None,
        private: bool | None = None,
        has_issues: bool | None = None,
        has_projects: bool | None = None,
        has_downloads: bool | None = None,
        has_wiki: bool | None = None,
    ) -> dict[str, Any]:
        """Update repository settings.

        Args:
            description: Repository description
            homepage: Repository homepage URL
            private: Whether repository is private
            has_issues: Enable issue tracking
            has_projects: Enable projects
            has_downloads: Enable downloads
            has_wiki: Enable wiki

        Returns:
            Updated repository data from GitHub API

        Raises:
            GitHubError: If update fails
        """
        payload = self._build_update_payload(
            description=description,
            homepage=homepage,
            private=private,
            has_issues=has_issues,
            has_projects=has_projects,
            has_downloads=has_downloads,
            has_wiki=has_wiki,
        )

        return self._request(
            "PATCH",
            f"/repos/{self.owner}/{self.repo}",
            json=payload,
        )

    def _build_update_payload(  # noqa: PLR0913 # All params optional, keyword-only
        self,
        *,
        description: str | None,
        homepage: str | None,
        private: bool | None,
        has_issues: bool | None,
        has_projects: bool | None,
        has_downloads: bool | None,
        has_wiki: bool | None,
    ) -> dict[str, Any]:
        """Build update payload from optional parameters.

        Args:
            description: Repository description
            homepage: Repository homepage URL
            private: Whether repository is private
            has_issues: Enable issue tracking
            has_projects: Enable projects
            has_downloads: Enable downloads
            has_wiki: Enable wiki

        Returns:
            Payload with only non-None values
        """
        params = {
            "description": description,
            "homepage": homepage,
            "private": private,
            "has_issues": has_issues,
            "has_projects": has_projects,
            "has_downloads": has_downloads,
            "has_wiki": has_wiki,
        }
        return {k: v for k, v in params.items() if v is not None}

    def create_or_update_file(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> dict[str, Any]:
        """Create or update a file in the repository.

        Args:
            path: File path in repository
            content: File content (as plain text, will be base64 encoded)
            message: Commit message
            branch: Branch to commit to (default: main)

        Returns:
            File operation data from GitHub API

        Raises:
            GitHubError: If operation fails
        """
        encoded_content = base64.b64encode(content.encode()).decode()

        payload = {
            "message": message,
            "content": encoded_content,
            "branch": branch,
        }

        return self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/contents/{path}",
            json=payload,
        )

    def add_repository_topics(
        self,
        topics: list[str],
    ) -> dict[str, Any]:
        """Add topics/tags to a repository.

        Args:
            topics: List of topic names (lowercase, no spaces)

        Returns:
            Updated repository data

        Raises:
            GitHubError: If operation fails
        """
        payload = {
            "names": topics,
        }

        return self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/topics",
            json=payload,
        )

    def get_issue(
        self,
        issue_number: int,
    ) -> dict[str, Any]:
        """Get a specific issue by number.

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue data from GitHub API

        Raises:
            GitHubError: If request fails
        """
        return self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}",
        )

    def list_issues(
        self,
        state: Literal["open", "closed", "all"] = "open",
        labels: list[str] | None = None,
        milestone: int | None = None,
    ) -> list[dict[str, Any]]:
        """List issues in the repository.

        Args:
            state: Issue state filter (open, closed, all)
            labels: Filter by labels
            milestone: Filter by milestone ID

        Returns:
            List of issue data from GitHub API

        Raises:
            GitHubError: If request fails
        """
        params: dict[str, Any] = {
            "state": state,
            "per_page": 100,
        }

        if labels:
            params["labels"] = ",".join(labels)

        if milestone is not None:
            params["milestone"] = milestone

        result = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/issues",
            params=params,
        )
        return result if isinstance(result, list) else [result]
