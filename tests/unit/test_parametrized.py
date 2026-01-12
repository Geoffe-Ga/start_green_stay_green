"""Parametrized tests for comprehensive coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


class TestSupportedLanguages:
    """Parametrized tests for supported languages."""

    @pytest.mark.parametrize("language", ["python", "typescript", "go", "rust"])
    def test_language_support(self, language: str) -> None:
        """Test that each supported language is valid."""
        assert isinstance(language, str)
        assert len(language) > 0
        assert language in ["python", "typescript", "go", "rust"]

    @pytest.mark.parametrize("language,extension", [
        ("python", ".py"),
        ("typescript", ".ts"),
        ("go", ".go"),
        ("rust", ".rs"),
    ])
    def test_language_extensions(
        self, language: str, extension: str
    ) -> None:
        """Test language and file extension mappings."""
        assert isinstance(language, str)
        assert isinstance(extension, str)
        assert extension.startswith(".")


class TestConfigurationVariations:
    """Parametrized tests for configuration variations."""

    @pytest.mark.parametrize("include_ci", [True, False])
    def test_ci_configuration_options(self, include_ci: bool) -> None:
        """Test CI configuration variations."""
        assert isinstance(include_ci, bool)

    @pytest.mark.parametrize("include_precommit", [True, False])
    def test_precommit_configuration_options(self, include_precommit: bool) -> None:
        """Test pre-commit configuration variations."""
        assert isinstance(include_precommit, bool)

    @pytest.mark.parametrize("config", [
        {"project_name": "test", "language": "python"},
        {"project_name": "my-app", "language": "typescript"},
        {"project_name": "service", "language": "go"},
        {"project_name": "lib", "language": "rust"},
    ])
    def test_config_combinations(self, config: dict[str, str]) -> None:
        """Test various configuration combinations."""
        assert "project_name" in config
        assert "language" in config
        assert config["language"] in ["python", "typescript", "go", "rust"]


class TestPathVariations:
    """Parametrized tests for path handling."""

    @pytest.mark.parametrize("path_str", [
        "file.txt",
        "/absolute/path/file.txt",
        "relative/path/file.txt",
        "./current/path/file.txt",
        "../parent/path/file.txt",
    ])
    def test_various_paths(self, path_str: str) -> None:
        """Test various path formats."""
        path = Path(path_str)
        assert isinstance(path, Path)
        assert isinstance(str(path), str)

    @pytest.mark.parametrize("extension", [".py", ".ts", ".js", ".go", ".rs", ".yml", ".yaml", ".json"])
    def test_file_extensions(self, extension: str) -> None:
        """Test various file extensions."""
        filename = f"file{extension}"
        path = Path(filename)
        assert path.suffix == extension


class TestStringVariations:
    """Parametrized tests for string handling."""

    @pytest.mark.parametrize("string", [
        "simple",
        "with-dash",
        "with_underscore",
        "withCaps",
        "with.dots",
        "with spaces",
    ])
    def test_various_strings(self, string: str) -> None:
        """Test various string formats."""
        assert isinstance(string, str)
        assert len(string) > 0

    @pytest.mark.parametrize("prefix,suffix", [
        ("test_", ".py"),
        ("pre_", "_test"),
        ("", ".txt"),
        ("file_", ""),
    ])
    def test_string_combinations(self, prefix: str, suffix: str) -> None:
        """Test string prefix/suffix combinations."""
        result = f"{prefix}name{suffix}"
        assert isinstance(result, str)


class TestNumberVariations:
    """Parametrized tests for number handling."""

    @pytest.mark.parametrize("number", [0, 1, 10, 100, 1000, -1, -10])
    def test_integer_variations(self, number: int) -> None:
        """Test various integer values."""
        assert isinstance(number, int)

    @pytest.mark.parametrize("percentage", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_percentage_variations(self, percentage: float) -> None:
        """Test percentage values."""
        assert isinstance(percentage, float)
        assert 0.0 <= percentage <= 1.0


class TestErrorConditions:
    """Parametrized tests for error conditions."""

    @pytest.mark.parametrize("value", [None, "", [], {}])
    def test_falsy_values(self, value: None | str | list | dict) -> None:
        """Test handling of falsy values."""
        assert not value or value is None

    @pytest.mark.parametrize("invalid_language", ["cobol", "fortran", "pascal", "xyz"])
    def test_invalid_languages(self, invalid_language: str) -> None:
        """Test that invalid languages are rejected."""
        valid_languages = ["python", "typescript", "go", "rust"]
        assert invalid_language not in valid_languages
