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
import json
import re
from typing import Any, Literal, Optional

import httpx
from pydantic import BaseModel, Field


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
        status_code: Optional[int] = None,
        response_body: Optional[dict[str, Any]] = None,
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

    pass


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
    milestone: Optional[str] = None
    epic: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    estimate: Optional[str] = None


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
        if not token or not isinstance(token, str):
            msg = "GitHub token is required and must be a string"
            raise GitHubError(msg)

        if not owner or not isinstance(owner, str):
            msg = "Repository owner is required"
            raise GitHubError(msg)

        if not repo or not isinstance(repo, str):
            msg = "Repository name is required"
            raise GitHubError(msg)

        self.token = token
        self.owner = owner
        self.repo = repo

        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "start-green-stay-green/1.0",
            },
            timeout=self.TIMEOUT,
        )

    def __enter__(self) -> "GitHubClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
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
        try:
            response_body = response.json() if response.content else {}
        except json.JSONDecodeError:
            response_body = {"raw_body": response.text}

        if response.status_code == 401:
            msg = "Authentication failed: invalid or expired token"
            raise GitHubAuthError(
                msg,
                status_code=401,
                response_body=response_body,
            )

        if response.status_code == 403:
            msg = "Permission denied: token may lack required scopes"
            raise GitHubAuthError(
                msg,
                status_code=403,
                response_body=response_body,
            )

        if response.status_code >= 400:
            error_msg = response_body.get("message", response.text)
            msg = f"GitHub API error: {error_msg}"
            raise GitHubError(
                msg,
                status_code=response.status_code,
                response_body=response_body,
            )

        return response_body

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
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
                return self._handle_response(response)
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == self.MAX_RETRIES - 1:
                    msg = f"GitHub API connection failed after {self.MAX_RETRIES} retries: {e}"
                    raise GitHubError(msg) from e
                # Retry on transient errors
                continue

    def create_repository(
        self,
        description: str = "",
        private: bool = False,
        initialize_readme: bool = True,
        auto_init: bool = True,
        gitignore_template: str = "Python",
    ) -> dict[str, Any]:
        """Create a new GitHub repository.

        Args:
            description: Repository description
            private: Whether repository should be private
            initialize_readme: Create README.md on init
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

        response = self._request("POST", "/user/repos", json=payload)
        return response

    def configure_branch_protection(
        self,
        branch: str = "main",
        rule: Optional[BranchProtectionRule] = None,
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

        # Map rule to GitHub API format
        payload = {
            "required_status_checks": {
                "strict": True,
                "contexts": rule.status_check_contexts or ["ci"],
            } if rule.require_status_checks else None,
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": rule.dismiss_stale_reviews,
                "require_code_owner_reviews": False,
                "required_approving_review_count": 1,
            } if rule.require_code_review else None,
            "restrictions": None,
            "allow_force_pushes": rule.allow_force_pushes,
            "allow_deletions": rule.allow_deletions,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        response = self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/branches/{branch}/protection",
            json=payload,
        )
        return response

    def create_issue(
        self,
        title: str,
        body: str = "",
        labels: Optional[list[str]] = None,
        milestone: Optional[int] = None,
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

        response = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/issues",
            json=payload,
        )
        return response

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
            try:
                result = self.create_issue(
                    title=issue.title,
                    body=issue.body,
                    labels=issue.labels,
                )
                results.append(result)
            except GitHubError:
                # Re-raise to stop bulk operation on error
                raise

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

        response = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/labels",
            json=payload,
        )
        return response

    def create_labels_bulk(
        self,
        labels: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """Create multiple labels in bulk.

        Args:
            labels: List of dicts with keys: name, color (optional), description (optional)

        Returns:
            List of created label data from GitHub API

        Raises:
            GitHubError: If any label creation fails (partial creation possible)
        """
        results = []

        for label in labels:
            try:
                result = self.create_label(
                    name=label.get("name", ""),
                    color=label.get("color", "0075ca"),
                    description=label.get("description", ""),
                )
                results.append(result)
            except GitHubError:
                # Continue on label already exists (409), fail on other errors
                pass

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

        response = self._request(
            "POST",
            f"/repos/{self.owner}/{self.repo}/milestones",
            json=payload,
        )
        return response

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
            try:
                result = self.create_milestone(
                    title=milestone.get("title", ""),
                    description=milestone.get("description", ""),
                )
                results.append(result)
            except GitHubError:
                # Continue on milestone already exists (409), fail on other errors
                pass

        return results

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

        # Pattern to match issue sections
        # Matches: "#### Issue X.Y: Title" or "Issue X.Y: Title"
        issue_pattern = r"#+\s*(?:Issue|Epic)\s+([\d.]+):\s*(.+?)(?=(?:####|###|$))"

        for match in re.finditer(issue_pattern, spec_content, re.DOTALL):
            issue_id = match.group(1)
            issue_content = match.group(2)

            # Extract title (first line after header)
            title_match = re.search(r"^(.+?)$", issue_content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f"Issue {issue_id}"

            # Extract type
            type_match = re.search(r"\*\*Type\*\*:\s*(.+?)(?:\n|$)", issue_content)
            issue_type = type_match.group(1).strip() if type_match else "Task"

            # Extract priority
            priority_match = re.search(r"\*\*Priority\*\*:\s*(.+?)(?:\n|$)", issue_content)
            priority = priority_match.group(1).strip() if priority_match else "P2"

            # Extract estimate
            estimate_match = re.search(r"\*\*Estimate\*\*:\s*(.+?)(?:\n|$)", issue_content)
            estimate = estimate_match.group(1).strip() if estimate_match else None

            # Extract description
            description_match = re.search(
                r"\*\*Description\*\*:\s*(.+?)(?=(?:\*\*|$))",
                issue_content,
                re.DOTALL,
            )
            description = description_match.group(1).strip() if description_match else ""

            # Extract acceptance criteria
            criteria_match = re.search(
                r"\*\*Acceptance Criteria\*\*:\s*(.+?)(?=(?:\*\*|$))",
                issue_content,
                re.DOTALL,
            )
            criteria = criteria_match.group(1).strip() if criteria_match else ""

            # Build body with description and criteria
            body = description
            if criteria:
                body += f"\n\n## Acceptance Criteria\n{criteria}"

            # Create labels
            labels = [issue_type.lower(), priority.lower()]

            # Parse epic from section hierarchy
            epic = None
            if match.start() > 0:
                # Look for epic heading before this issue
                epic_match = re.search(
                    r"###\s*Epic\s+([\d.]+):",
                    spec_content[: match.start()],
                )
                if epic_match:
                    epic = epic_match.group(1)

            issue_data = IssueData(
                title=f"{issue_id}: {title}",
                body=body,
                labels=labels,
                epic=epic,
                type=issue_type,
                priority=priority,
                estimate=estimate,
            )

            issues.append(issue_data)

        return issues

    def get_repository_info(self) -> dict[str, Any]:
        """Get repository information.

        Returns:
            Repository data from GitHub API

        Raises:
            GitHubError: If request fails
        """
        response = self._request("GET", f"/repos/{self.owner}/{self.repo}")
        return response

    def update_repository(
        self,
        description: Optional[str] = None,
        homepage: Optional[str] = None,
        private: Optional[bool] = None,
        has_issues: Optional[bool] = None,
        has_projects: Optional[bool] = None,
        has_downloads: Optional[bool] = None,
        has_wiki: Optional[bool] = None,
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
        payload = {}

        if description is not None:
            payload["description"] = description
        if homepage is not None:
            payload["homepage"] = homepage
        if private is not None:
            payload["private"] = private
        if has_issues is not None:
            payload["has_issues"] = has_issues
        if has_projects is not None:
            payload["has_projects"] = has_projects
        if has_downloads is not None:
            payload["has_downloads"] = has_downloads
        if has_wiki is not None:
            payload["has_wiki"] = has_wiki

        response = self._request(
            "PATCH",
            f"/repos/{self.owner}/{self.repo}",
            json=payload,
        )
        return response

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

        response = self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/contents/{path}",
            json=payload,
        )
        return response

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

        response = self._request(
            "PUT",
            f"/repos/{self.owner}/{self.repo}/topics",
            json=payload,
        )
        return response

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
        response = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/issues/{issue_number}",
        )
        return response

    def list_issues(
        self,
        state: Literal["open", "closed", "all"] = "open",
        labels: Optional[list[str]] = None,
        milestone: Optional[int] = None,
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

        response = self._request(
            "GET",
            f"/repos/{self.owner}/{self.repo}/issues",
            params=params,
        )
        return response if isinstance(response, list) else [response]
