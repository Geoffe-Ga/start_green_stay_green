"""Tests for github.actions module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.github import actions


class TestGithubActionsModule:
    """Test suite for GitHub Actions utilities."""

    def test_actions_module_imports(self) -> None:
        """Test that actions module can be imported."""
        assert actions is not None

    def test_actions_module_has_docstring(self) -> None:
        """Test that actions module has proper documentation."""
        assert actions.__doc__ is not None
        assert "action" in actions.__doc__.lower()

    def test_actions_path_exists(self) -> None:
        """Test that actions module file exists."""
        actions_file = Path("start_green_stay_green/github/actions.py")
        assert actions_file.exists()

    def test_actions_is_valid_python_module(self) -> None:
        """Test that actions module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.github.actions"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_actions_can_be_imported_from_package(self) -> None:
        """Test that actions can be imported from github package."""
        from start_green_stay_green import github

        assert hasattr(github, "actions")
