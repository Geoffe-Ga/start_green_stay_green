"""Tests for module import structure and package organization."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import types


class TestPackageStructure:
    """Test suite for package structure and module availability."""

    def test_main_package_exists(self) -> None:
        """Test that main package can be imported."""
        import start_green_stay_green

        assert start_green_stay_green is not None

    def test_ai_package_accessible(self) -> None:
        """Test that AI package is accessible."""
        from start_green_stay_green import ai

        assert ai is not None

    def test_config_package_accessible(self) -> None:
        """Test that config package is accessible."""
        from start_green_stay_green import config

        assert config is not None

    def test_generators_package_accessible(self) -> None:
        """Test that generators package is accessible."""
        from start_green_stay_green import generators

        assert generators is not None

    def test_github_package_accessible(self) -> None:
        """Test that github package is accessible."""
        from start_green_stay_green import github

        assert github is not None

    def test_utils_package_accessible(self) -> None:
        """Test that utils package is accessible."""
        from start_green_stay_green import utils

        assert utils is not None

    def test_all_modules_have_init(self) -> None:
        """Test that all packages have __init__.py files."""
        packages = [
            "start_green_stay_green",
            "start_green_stay_green/ai",
            "start_green_stay_green/config",
            "start_green_stay_green/generators",
            "start_green_stay_green/github",
            "start_green_stay_green/utils",
        ]
        for package in packages:
            init_file = Path(f"{package}/__init__.py")
            assert init_file.exists(), f"Missing {package}/__init__.py"

    def test_no_import_errors_on_import(self) -> None:
        """Test that importing modules doesn't raise errors."""
        try:
            import start_green_stay_green

            from start_green_stay_green import ai
            from start_green_stay_green import config
            from start_green_stay_green import generators
            from start_green_stay_green import github
            from start_green_stay_green import utils
        except ImportError as exc:
            pytest.fail(f"Import error: {exc}")

    def test_module_docstrings_exist(self) -> None:
        """Test that modules have docstrings."""
        modules_to_check = [
            "start_green_stay_green.ai.orchestrator",
            "start_green_stay_green.ai.tuner",
            "start_green_stay_green.config.settings",
            "start_green_stay_green.generators.base",
            "start_green_stay_green.utils.fs",
            "start_green_stay_green.utils.templates",
        ]

        for module_name in modules_to_check:
            module = importlib.import_module(module_name)
            assert (
                module.__doc__ is not None
            ), f"{module_name} has no docstring"

    def test_all_modules_are_importable(self) -> None:
        """Test that all implementation modules are importable."""
        modules = [
            "start_green_stay_green.ai.orchestrator",
            "start_green_stay_green.ai.tuner",
            "start_green_stay_green.config.settings",
            "start_green_stay_green.generators.base",
            "start_green_stay_green.generators.ci",
            "start_green_stay_green.generators.scripts",
            "start_green_stay_green.generators.claude_md",
            "start_green_stay_green.generators.github_actions",
            "start_green_stay_green.generators.metrics",
            "start_green_stay_green.generators.precommit",
            "start_green_stay_green.generators.skills",
            "start_green_stay_green.generators.subagents",
            "start_green_stay_green.generators.architecture",
            "start_green_stay_green.github.client",
            "start_green_stay_green.github.actions",
            "start_green_stay_green.github.issues",
            "start_green_stay_green.utils.fs",
            "start_green_stay_green.utils.templates",
        ]

        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                assert module is not None
            except ImportError as exc:
                pytest.fail(f"Failed to import {module_name}: {exc}")
