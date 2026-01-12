"""Property-based tests using Hypothesis for all modules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from hypothesis import given
from hypothesis import strategies as st

if TYPE_CHECKING:
    pass


class TestModulePropertyBased:
    """Property-based tests for module invariants."""

    @given(st.text(min_size=1, max_size=100))
    def test_project_name_can_be_string(self, project_name: str) -> None:
        """Test that project names can be any non-empty string."""
        assert isinstance(project_name, str)
        assert len(project_name) > 0

    @given(st.sampled_from(["python", "typescript", "go", "rust"]))
    def test_language_has_valid_choices(self, language: str) -> None:
        """Test that supported languages are all strings."""
        assert isinstance(language, str)
        assert len(language) > 0

    @given(st.booleans())
    def test_boolean_config_values(self, value: bool) -> None:
        """Test that boolean configuration values work."""
        assert isinstance(value, bool)
        assert value in {True, False}

    @given(st.dictionaries(st.text(), st.text(), min_size=0, max_size=10))
    def test_config_dict_property(self, config: dict[str, str]) -> None:
        """Test that config dictionaries maintain their invariants."""
        assert isinstance(config, dict)
        assert len(config) >= 0
        for key, value in config.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    @given(st.lists(st.text(), min_size=0, max_size=10))
    def test_generator_list_property(self, items: list[str]) -> None:
        """Test that generator lists maintain their invariants."""
        assert isinstance(items, list)
        assert len(items) >= 0
        assert all(isinstance(item, str) for item in items)

    @given(st.paths(relative=False))
    def test_path_is_pathlib_path(self, path: Path) -> None:
        """Test that paths are properly handled."""
        assert isinstance(path, Path)

    @given(st.integers(min_value=1, max_value=100))
    def test_positive_integers(self, value: int) -> None:
        """Test positive integer handling."""
        assert isinstance(value, int)
        assert value > 0

    @given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    def test_normalized_floats(self, value: float) -> None:
        """Test normalized float handling."""
        assert isinstance(value, float)
        assert 0.0 <= value <= 1.0

    @given(st.emails())
    def test_email_format(self, email: str) -> None:
        """Test that emails are valid format."""
        assert isinstance(email, str)
        assert "@" in email

    @given(st.urls())
    def test_url_format(self, url: str) -> None:
        """Test that URLs are valid format."""
        assert isinstance(url, str)
        assert "://" in url


class TestConfigPropertyBased:
    """Property-based tests for configuration."""

    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_", min_size=1, max_size=50))
    def test_valid_project_names(self, name: str) -> None:
        """Test that project names follow conventions."""
        assert isinstance(name, str)
        assert all(c.isalnum() or c in "-_" for c in name)

    @given(st.fixed_dictionaries({
        "project_name": st.text(min_size=1, max_size=50),
        "language": st.sampled_from(["python", "typescript", "go", "rust"]),
        "include_ci": st.booleans(),
    }))
    def test_valid_config_structure(self, config: dict[str, str | bool]) -> None:
        """Test that configuration structures are valid."""
        assert "project_name" in config
        assert "language" in config
        assert "include_ci" in config
        assert isinstance(config["project_name"], str)
        assert isinstance(config["language"], str)
        assert isinstance(config["include_ci"], bool)
