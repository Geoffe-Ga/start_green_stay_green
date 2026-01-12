"""Tests for generators.skills module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import skills


class TestSkillsGeneratorModule:
    """Test suite for skills generation."""

    def test_skills_module_imports(self) -> None:
        """Test that skills module can be imported."""
        assert skills is not None

    def test_skills_module_has_docstring(self) -> None:
        """Test that skills module has proper documentation."""
        assert skills.__doc__ is not None
        assert "skill" in skills.__doc__.lower()

    def test_skills_path_exists(self) -> None:
        """Test that skills module file exists."""
        skills_file = Path("start_green_stay_green/generators/skills.py")
        assert skills_file.exists()

    def test_skills_is_valid_python_module(self) -> None:
        """Test that skills module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.skills"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_skills_can_be_imported_from_package(self) -> None:
        """Test that skills can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "skills")
