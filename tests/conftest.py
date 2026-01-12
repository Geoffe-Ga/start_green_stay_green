"""Pytest configuration and shared fixtures for test suite."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def sample_api_key() -> str:
    """Provide sample API key for testing.

    Returns:
        Sample API key string for test instances.
    """
    return "test-api-key-abcd1234"


@pytest.fixture
def sample_context() -> dict[str, str]:
    """Provide sample context dictionary for testing.

    Returns:
        Dictionary with sample context variables.
    """
    return {
        "project": "TestProject",
        "language": "Python",
        "framework": "pytest",
    }


@pytest.fixture
def sample_prompt_template() -> str:
    """Provide sample prompt template for testing.

    Returns:
        Template string with context variables.
    """
    return "Create a {doc_type} for {project} using {language}"


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for file operations.

    Yields:
        Path object pointing to a temporary directory.
        Directory is automatically cleaned up after test.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_project_config() -> dict[str, str | bool]:
    """Provide sample project configuration for testing.

    Returns:
        Dictionary with sample project configuration.
    """
    return {
        "project_name": "test-project",
        "primary_language": "python",
        "include_ci": True,
        "include_github": True,
        "include_metrics": True,
    }


@pytest.fixture
def sample_generator_output() -> dict[str, str | list[str]]:
    """Provide sample generator output for testing.

    Returns:
        Dictionary with sample generator output structure.
    """
    return {
        "success": True,
        "generated_files": [
            "pyproject.toml",
            ".github/workflows/ci.yml",
            "scripts/check-all.sh",
            "CLAUDE.md",
        ],
        "configurations": {
            "ci": "github-actions",
            "language": "python",
        },
    }
