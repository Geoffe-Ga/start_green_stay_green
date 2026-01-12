"""Tests for generators.precommit module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import precommit


class TestPrecommitGeneratorModule:
    """Test suite for pre-commit hook generation."""

    def test_precommit_module_imports(self) -> None:
        """Test that precommit module can be imported."""
        assert precommit is not None

    def test_precommit_module_has_docstring(self) -> None:
        """Test that precommit module has proper documentation."""
        assert precommit.__doc__ is not None
        assert "precommit" in precommit.__doc__.lower()

    def test_precommit_path_exists(self) -> None:
        """Test that precommit module file exists."""
        precommit_file = Path(
            "start_green_stay_green/generators/precommit.py"
        )
        assert precommit_file.exists()

    def test_precommit_is_valid_python_module(self) -> None:
        """Test that precommit module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.precommit"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_precommit_can_be_imported_from_package(self) -> None:
        """Test that precommit can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "precommit")
