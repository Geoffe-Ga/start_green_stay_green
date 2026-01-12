"""Tests for generators.scripts module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import scripts


class TestScriptsGeneratorModule:
    """Test suite for quality scripts generation."""

    def test_scripts_module_imports(self) -> None:
        """Test that scripts module can be imported."""
        assert scripts is not None

    def test_scripts_module_has_docstring(self) -> None:
        """Test that scripts module has proper documentation."""
        assert scripts.__doc__ is not None
        assert "script" in scripts.__doc__.lower()

    def test_scripts_path_exists(self) -> None:
        """Test that scripts module file exists."""
        scripts_file = Path("start_green_stay_green/generators/scripts.py")
        assert scripts_file.exists()

    def test_scripts_is_valid_python_module(self) -> None:
        """Test that scripts module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.scripts"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_scripts_can_be_imported_from_package(self) -> None:
        """Test that scripts can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "scripts")
