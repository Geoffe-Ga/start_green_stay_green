"""Pytest configuration and shared fixtures for test suite."""

from __future__ import annotations

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
