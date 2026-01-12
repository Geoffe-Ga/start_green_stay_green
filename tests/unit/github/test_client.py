"""Tests for github.client module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.github import client


class TestGithubClientModule:
    """Test suite for GitHub API client."""

    def test_client_module_imports(self) -> None:
        """Test that client module can be imported."""
        assert client is not None

    def test_client_module_has_docstring(self) -> None:
        """Test that client module has proper documentation."""
        assert client.__doc__ is not None
        assert "github" in client.__doc__.lower()

    def test_client_path_exists(self) -> None:
        """Test that client module file exists."""
        client_file = Path("start_green_stay_green/github/client.py")
        assert client_file.exists()

    def test_client_is_valid_python_module(self) -> None:
        """Test that client module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.github.client"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_client_can_be_imported_from_package(self) -> None:
        """Test that client can be imported from github package."""
        from start_green_stay_green import github

        assert hasattr(github, "client")
