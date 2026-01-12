"""Tests for generators.github_actions module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import github_actions


class TestGithubActionsGeneratorModule:
    """Test suite for GitHub Actions workflow generation."""

    def test_github_actions_module_imports(self) -> None:
        """Test that github_actions module can be imported."""
        assert github_actions is not None

    def test_github_actions_module_has_docstring(self) -> None:
        """Test that github_actions module has proper documentation."""
        assert github_actions.__doc__ is not None
        assert "github" in github_actions.__doc__.lower()

    def test_github_actions_path_exists(self) -> None:
        """Test that github_actions module file exists."""
        github_actions_file = Path(
            "start_green_stay_green/generators/github_actions.py"
        )
        assert github_actions_file.exists()

    def test_github_actions_is_valid_python_module(self) -> None:
        """Test that github_actions module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.github_actions"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_github_actions_can_be_imported_from_package(self) -> None:
        """Test that github_actions can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "github_actions")
