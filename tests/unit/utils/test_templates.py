"""Tests for utils.templates module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.utils import templates


class TestTemplatesModule:
    """Test suite for template utilities."""

    def test_templates_module_imports(self) -> None:
        """Test that templates module can be imported."""
        assert templates is not None

    def test_templates_module_has_docstring(self) -> None:
        """Test that templates module has proper documentation."""
        assert templates.__doc__ is not None
        assert "template" in templates.__doc__.lower()

    def test_templates_path_exists(self) -> None:
        """Test that templates module file exists."""
        templates_file = Path("start_green_stay_green/utils/templates.py")
        assert templates_file.exists()

    def test_templates_is_valid_python_module(self) -> None:
        """Test that templates module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.utils.templates"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_templates_can_be_imported_from_package(self) -> None:
        """Test that templates can be imported from utils package."""
        from start_green_stay_green import utils

        assert hasattr(utils, "templates")
