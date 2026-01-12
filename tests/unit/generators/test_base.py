"""Tests for generators.base module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import base


class TestBaseGeneratorModule:
    """Test suite for base generator class."""

    def test_base_module_imports(self) -> None:
        """Test that base module can be imported."""
        assert base is not None

    def test_base_module_has_docstring(self) -> None:
        """Test that base module has proper documentation."""
        assert base.__doc__ is not None
        assert "base" in base.__doc__.lower()

    def test_base_path_exists(self) -> None:
        """Test that base module file exists."""
        base_file = Path("start_green_stay_green/generators/base.py")
        assert base_file.exists()

    def test_base_is_valid_python_module(self) -> None:
        """Test that base module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.base"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_base_can_be_imported_from_package(self) -> None:
        """Test that base can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "base")
