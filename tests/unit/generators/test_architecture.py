"""Tests for generators.architecture module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import architecture


class TestArchitectureGeneratorModule:
    """Test suite for architecture generation."""

    def test_architecture_module_imports(self) -> None:
        """Test that architecture module can be imported."""
        assert architecture is not None

    def test_architecture_module_has_docstring(self) -> None:
        """Test that architecture module has proper documentation."""
        assert architecture.__doc__ is not None
        assert "architecture" in architecture.__doc__.lower()

    def test_architecture_path_exists(self) -> None:
        """Test that architecture module file exists."""
        architecture_file = Path(
            "start_green_stay_green/generators/architecture.py"
        )
        assert architecture_file.exists()

    def test_architecture_is_valid_python_module(self) -> None:
        """Test that architecture module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.architecture"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_architecture_can_be_imported_from_package(self) -> None:
        """Test that architecture can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "architecture")
