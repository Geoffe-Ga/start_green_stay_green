"""Unit tests for the naming utility helpers."""

from __future__ import annotations

import pytest

from start_green_stay_green.utils.naming import pascal_case


class TestPascalCase:
    """Tests for :func:`pascal_case`."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("test_project", "TestProject"),
            ("test-project", "TestProject"),
            ("test-my_project", "TestMyProject"),
            ("project", "Project"),
            ("PROJECT", "Project"),
            ("my-cool-app", "MyCoolApp"),
            ("a_b_c", "ABC"),
        ],
    )
    def test_converts_separated_words_to_pascal_case(
        self, value: str, expected: str
    ) -> None:
        """Underscores and hyphens are treated as word separators."""
        assert pascal_case(value) == expected

    def test_collapses_repeated_separators(self) -> None:
        """Empty segments from repeated separators are dropped."""
        assert pascal_case("test__project") == "TestProject"
        assert pascal_case("test--project") == "TestProject"
        assert pascal_case("_leading_") == "Leading"

    def test_empty_string_returns_empty_string(self) -> None:
        """An empty input yields an empty output."""
        assert pascal_case("") == ""

    def test_only_separators_returns_empty_string(self) -> None:
        """A value of only separators yields an empty string."""
        assert pascal_case("_-_") == ""

    def test_does_not_lowercase_interior_capitals_of_word(self) -> None:
        """``capitalize`` lowercases the tail, normalising mixed case."""
        assert pascal_case("myProject") == "Myproject"
