"""Tests for generators.claude_md module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import claude_md


class TestClaudeMdGeneratorModule:
    """Test suite for CLAUDE.md generation."""

    def test_claude_md_module_imports(self) -> None:
        """Test that claude_md module can be imported."""
        assert claude_md is not None

    def test_claude_md_module_has_docstring(self) -> None:
        """Test that claude_md module has proper documentation."""
        assert claude_md.__doc__ is not None
        assert "claude" in claude_md.__doc__.lower()

    def test_claude_md_path_exists(self) -> None:
        """Test that claude_md module file exists."""
        claude_md_file = Path(
            "start_green_stay_green/generators/claude_md.py"
        )
        assert claude_md_file.exists()

    def test_claude_md_is_valid_python_module(self) -> None:
        """Test that claude_md module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.claude_md"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_claude_md_can_be_imported_from_package(self) -> None:
        """Test that claude_md can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "claude_md")
