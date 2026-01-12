"""Tests for generators.ci module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import ci


class TestCiGeneratorModule:
    """Test suite for CI pipeline generation."""

    def test_ci_module_imports(self) -> None:
        """Test that ci module can be imported."""
        assert ci is not None

    def test_ci_module_has_docstring(self) -> None:
        """Test that ci module has proper documentation."""
        assert ci.__doc__ is not None
        assert "ci" in ci.__doc__.lower()

    def test_ci_path_exists(self) -> None:
        """Test that ci module file exists."""
        ci_file = Path("start_green_stay_green/generators/ci.py")
        assert ci_file.exists()

    def test_ci_is_valid_python_module(self) -> None:
        """Test that ci module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.ci"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_ci_can_be_imported_from_package(self) -> None:
        """Test that ci can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "ci")
