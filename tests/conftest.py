"""Pytest fixtures and configuration for all tests.

This module provides shared test fixtures, mock factories, and test utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def tmp_project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure.

    Args:
        tmp_path: Pytest's temporary directory fixture.

    Returns:
        Path to the temporary project directory.
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


@pytest.fixture
def sample_config() -> dict[str, str | bool]:
    """Provide sample configuration for testing.

    Returns:
        Dictionary with basic project configuration.
    """
    return {
        "project_name": "test-project",
        "language": "python",
        "description": "Test project",
        "include_ci": True,
        "include_precommit": True,
    }


@pytest.fixture
def mock_anthropic_client() -> MagicMock:
    """Create a mock Anthropic API client.

    Returns:
        MagicMock simulating Anthropic client behavior.
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated content")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_github_client() -> MagicMock:
    """Create a mock GitHub API client.

    Returns:
        MagicMock simulating GitHub client behavior.
    """
    mock_client = MagicMock()
    mock_client.get_user.return_value = MagicMock(login="test-user")
    mock_client.get_repo.return_value = MagicMock(name="test-repo")
    return mock_client


@pytest.fixture
def environment_variables(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up clean environment variables for testing.

    Args:
        monkeypatch: Pytest's monkeypatch fixture.

    Returns:
        Dictionary of environment variables.
    """
    env_vars = {
        "ANTHROPIC_API_KEY": "test-api-key",
        "GITHUB_TOKEN": "test-github-token",
        "HOME": "/tmp/test",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def mock_jinja_template() -> MagicMock:
    """Create a mock Jinja2 template.

    Returns:
        MagicMock simulating Jinja2 Template behavior.
    """
    mock_template = MagicMock()
    mock_template.render.return_value = "Rendered template content"
    return mock_template


@pytest.fixture
def sample_jinja_env() -> MagicMock:
    """Create a mock Jinja2 environment.

    Returns:
        MagicMock simulating Jinja2 Environment behavior.
    """
    mock_env = MagicMock()
    mock_template = MagicMock()
    mock_template.render.return_value = "rendered content"
    mock_env.get_template.return_value = mock_template
    return mock_env
