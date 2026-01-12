"""GitHub Actions workflow management.

Manages workflow configuration and execution via GitHub API.
Supports triggering workflows, listing runs, and retrieving workflow status.
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_NO_CONTENT = 204
HTTP_BAD_REQUEST = 400

# Error messages
_ERR_EMPTY_WORKFLOW_NAME = "Workflow name cannot be empty"
_ERR_EMPTY_TOKEN = "Token cannot be empty"  # nosec B105  # noqa: S105
_ERR_GET_WORKFLOW_FAILED = "Failed to get workflow"
_ERR_LIST_WORKFLOWS_FAILED = "Failed to list workflows"
_ERR_TRIGGER_WORKFLOW_FAILED = "Failed to trigger workflow"
_ERR_LIST_RUNS_FAILED = "Failed to list workflow runs"
_ERR_GET_RUN_FAILED = "Failed to get workflow run"


class GitHubActionsError(Exception):
    """Raised when GitHub Actions API operation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        """Initialize GitHubActionsError.

        Args:
            message: Error message describing the failure.
            status_code: Optional HTTP status code from API response.
        """
        super().__init__(message)
        self.status_code = status_code


@dataclass
class WorkflowConfig:
    """Configuration for workflow operations.

    Attributes:
        name: Workflow name (required).
        file_path: Path to workflow YAML file (e.g., .github/workflows/ci.yml).
        description: Workflow description (optional).
    """

    name: str
    file_path: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        """Validate workflow configuration.

        Raises:
            ValueError: If name is empty or invalid.
        """
        if not self.name or not self.name.strip():
            raise ValueError(_ERR_EMPTY_WORKFLOW_NAME)


class GitHubActionsManager:
    """GitHub Actions workflow manager.

    Provides methods for managing GitHub Actions workflows including
    triggering runs, listing workflows, and retrieving run status.

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
        """Initialize GitHubActionsManager.

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

    def get_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str,
    ) -> dict[str, Any]:
        """Get information about a workflow.

        Retrieves metadata for a specific workflow by ID or filename.

        Args:
            owner: Repository owner.
            repo: Repository name.
            workflow_id: Workflow ID or filename (e.g., "ci.yml").

        Returns:
            Dictionary containing workflow information.

        Raises:
            GitHubActionsError: If workflow cannot be found.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubActionsError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_WORKFLOW_FAILED}: {exc}"
            raise GitHubActionsError(msg) from exc

    def list_workflows(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """List all workflows in a repository.

        Retrieves all workflows defined in a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.

        Returns:
            Dictionary containing list of workflows.

        Raises:
            GitHubActionsError: If workflows cannot be retrieved.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/workflows",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubActionsError:
            raise
        except Exception as exc:
            msg = f"{_ERR_LIST_WORKFLOWS_FAILED}: {exc}"
            raise GitHubActionsError(msg) from exc

    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str,
        ref: str,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> bool:
        """Trigger a workflow run.

        Triggers a new run of the specified workflow on the given branch
        or tag, optionally passing input values.

        Args:
            owner: Repository owner.
            repo: Repository name.
            workflow_id: Workflow ID or filename.
            ref: Git reference (branch or tag name).
            inputs: Optional input values for the workflow.

        Returns:
            True if workflow was triggered successfully, False otherwise.

        Examples:
            >>> manager = GitHubActionsManager(token="ghp_...")
            >>> manager.trigger_workflow(
            ...     owner="myorg",
            ...     repo="my-repo",
            ...     workflow_id="ci.yml",
            ...     ref="main",
            ...     inputs={"debug": "true"},
            ... )
        """
        try:
            payload = {
                "ref": ref,
            }
            if inputs:
                payload["inputs"] = inputs

            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches",
                    headers=self._get_headers(),
                    json=payload,
                )

                if response.status_code == HTTP_NO_CONTENT:
                    return True
                self._check_response(response)
                return False
        except (GitHubActionsError, httpx.HTTPError):
            logger.exception(_ERR_TRIGGER_WORKFLOW_FAILED)
            return False

    def list_workflow_runs(
        self,
        owner: str,
        repo: str,
        workflow_id: int | str,
        *,
        status: str | None = None,
        conclusion: str | None = None,
        limit: int = 30,
    ) -> dict[str, Any]:
        """List workflow runs for a specific workflow.

        Retrieves runs for a workflow, optionally filtered by status or conclusion.

        Args:
            owner: Repository owner.
            repo: Repository name.
            workflow_id: Workflow ID or filename.
            status: Optional status filter (queued, in_progress, completed).
            conclusion: Optional conclusion filter (success, failure, etc.).
            limit: Maximum number of runs to return. Defaults to 30.

        Returns:
            Dictionary containing list of workflow runs.

        Raises:
            GitHubActionsError: If runs cannot be retrieved.
        """
        try:
            params = {"per_page": limit}
            if status:
                params["status"] = status
            if conclusion:
                params["conclusion"] = conclusion

            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs",
                    headers=self._get_headers(),
                    params=params,
                )
                self._check_response(response)
                return response.json()
        except GitHubActionsError:
            raise
        except Exception as exc:
            msg = f"{_ERR_LIST_RUNS_FAILED}: {exc}"
            raise GitHubActionsError(msg) from exc

    def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> dict[str, Any]:
        """Get information about a specific workflow run.

        Retrieves detailed information about a workflow run including
        status, conclusion, and timestamps.

        Args:
            owner: Repository owner.
            repo: Repository name.
            run_id: Workflow run ID.

        Returns:
            Dictionary containing workflow run information.

        Raises:
            GitHubActionsError: If run cannot be found.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}",
                    headers=self._get_headers(),
                )
                self._check_response(response)
                return response.json()
        except GitHubActionsError:
            raise
        except Exception as exc:
            msg = f"{_ERR_GET_RUN_FAILED}: {exc}"
            raise GitHubActionsError(msg) from exc

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
            GitHubActionsError: If response indicates an API error.
        """
        if response.status_code >= HTTP_BAD_REQUEST:
            try:
                error_data = response.json()
                message = error_data.get("message", "Unknown error")
            except Exception:  # noqa: BLE001
                message = response.text or "Unknown error"

            raise GitHubActionsError(
                message,
                status_code=response.status_code,
            )
