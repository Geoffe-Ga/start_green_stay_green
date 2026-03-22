"""Tests for multi-language --language support in green init.

Tests that multiple --language flags generate infrastructure for
all specified languages, and that single language still works.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from start_green_stay_green import cli as cli_mod
from start_green_stay_green.cli import _generate_project_files
from start_green_stay_green.cli import _resolve_languages

_STEP_NAMES = [
    "_generate_with_orchestrator",
    "_generate_skills_step",
    "_generate_precommit_step",
    "_generate_scripts_step",
    "_generate_readme_step",
    "_generate_tests_step",
    "_generate_dependencies_step",
    "_generate_structure_step",
]

_CLI_MODULE = "start_green_stay_green.cli"


def _patch_all_steps() -> Any:
    """Create patch.multiple with fresh MagicMocks for all generation steps."""
    return patch.multiple(
        _CLI_MODULE,
        **{name: MagicMock() for name in _STEP_NAMES},
    )


def _get_mock(name: str) -> Any:
    """Get the current mock for a patched CLI step by name.

    Args:
        name: Name of the patched function (e.g. "_generate_structure_step").

    Returns:
        The MagicMock currently patching that function.
    """
    return vars(cli_mod)[name]


class TestResolveLanguages:
    """Test _resolve_languages helper."""

    def test_single_language_string(self) -> None:
        """Test single language string returns tuple with one element."""
        result = _resolve_languages(("python",))
        assert result == ("python",)

    def test_multiple_languages(self) -> None:
        """Test multiple languages returned as tuple."""
        result = _resolve_languages(("python", "typescript"))
        assert result == ("python", "typescript")

    def test_invalid_language_raises(self) -> None:
        """Test invalid language in list raises ValueError."""
        with pytest.raises(ValueError, match="brainfuck"):
            _resolve_languages(("python", "brainfuck"))

    def test_empty_tuple_raises(self) -> None:
        """Test empty tuple raises ValueError."""
        with pytest.raises(ValueError, match=r"[Aa]t least one language"):
            _resolve_languages(())

    def test_deduplicates(self) -> None:
        """Test duplicate languages are removed."""
        result = _resolve_languages(("python", "python", "go"))
        assert result == ("python", "go")


class TestMultiLanguageGeneration:
    """Test _generate_project_files with multiple languages."""

    def test_multi_language_calls_per_language_steps(self) -> None:
        """Test multi-language calls per-language generators for each."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(),
                "my-project",
                ("python", "typescript"),
                None,
                MagicMock(),
            )

            assert _get_mock("_generate_structure_step").call_count == 2
            assert _get_mock("_generate_dependencies_step").call_count == 2
            assert _get_mock("_generate_tests_step").call_count == 2
            assert _get_mock("_generate_scripts_step").call_count == 2
            assert _get_mock("_generate_precommit_step").call_count == 2
            _get_mock("_generate_skills_step").assert_called_once()
            _get_mock("_generate_with_orchestrator").assert_called_once()

    def test_single_language_backward_compatible(self) -> None:
        """Test single language works identically to before."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python",), None, MagicMock()
            )

            _get_mock("_generate_scripts_step").assert_called_once()
            _get_mock("_generate_precommit_step").assert_called_once()
            _get_mock("_generate_skills_step").assert_called_once()

    def test_per_language_steps_receive_correct_language(self) -> None:
        """Test each per-language step gets the correct language arg."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python", "go"), None, MagicMock()
            )

            calls = _get_mock("_generate_structure_step").call_args_list
            assert calls[0][0][2] == "python"
            assert calls[1][0][2] == "go"
