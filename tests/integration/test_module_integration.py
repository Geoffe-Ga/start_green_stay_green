"""Integration tests for module interactions."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


@pytest.mark.integration
class TestConfigAiIntegration:
    """Test integration between config and AI modules."""

    def test_config_module_exists(self) -> None:
        """Test that config module is available."""
        from start_green_stay_green import config

        assert config is not None

    def test_ai_module_exists(self) -> None:
        """Test that AI module is available."""
        from start_green_stay_green import ai

        assert ai is not None

    def test_config_and_ai_both_importable(self) -> None:
        """Test that config and AI can be imported together."""
        from start_green_stay_green import config
        from start_green_stay_green import ai

        assert config is not None
        assert ai is not None


@pytest.mark.integration
class TestGeneratorsIntegration:
    """Test integration with generators."""

    def test_all_generators_exist(self) -> None:
        """Test that all generator modules exist."""
        from start_green_stay_green import generators

        generators_list = [
            "base",
            "ci",
            "scripts",
            "claude_md",
            "github_actions",
            "metrics",
            "precommit",
            "skills",
            "subagents",
            "architecture",
        ]

        for generator_name in generators_list:
            assert hasattr(
                generators, generator_name
            ), f"Generator {generator_name} not found"

    def test_generators_are_importable(self) -> None:
        """Test that each generator can be imported."""
        from start_green_stay_green.generators import base
        from start_green_stay_green.generators import ci
        from start_green_stay_green.generators import scripts
        from start_green_stay_green.generators import claude_md
        from start_green_stay_green.generators import github_actions
        from start_green_stay_green.generators import metrics
        from start_green_stay_green.generators import precommit
        from start_green_stay_green.generators import skills
        from start_green_stay_green.generators import subagents
        from start_green_stay_green.generators import architecture

        modules = [
            base,
            ci,
            scripts,
            claude_md,
            github_actions,
            metrics,
            precommit,
            skills,
            subagents,
            architecture,
        ]

        for module in modules:
            assert module is not None


@pytest.mark.integration
class TestGithubIntegration:
    """Test integration with GitHub module."""

    def test_all_github_modules_exist(self) -> None:
        """Test that all GitHub modules exist."""
        from start_green_stay_green import github

        github_list = ["client", "actions", "issues"]

        for module_name in github_list:
            assert hasattr(
                github, module_name
            ), f"GitHub module {module_name} not found"

    def test_github_modules_importable(self) -> None:
        """Test that GitHub modules can be imported."""
        from start_green_stay_green.github import client
        from start_green_stay_green.github import actions
        from start_green_stay_green.github import issues

        assert client is not None
        assert actions is not None
        assert issues is not None


@pytest.mark.integration
class TestUtilsIntegration:
    """Test integration with utils module."""

    def test_all_utils_exist(self) -> None:
        """Test that all utils modules exist."""
        from start_green_stay_green import utils

        utils_list = ["fs", "templates"]

        for module_name in utils_list:
            assert hasattr(
                utils, module_name
            ), f"Utils module {module_name} not found"

    def test_utils_modules_importable(self) -> None:
        """Test that utils modules can be imported."""
        from start_green_stay_green.utils import fs
        from start_green_stay_green.utils import templates

        assert fs is not None
        assert templates is not None


@pytest.mark.integration
class TestCrossModuleImports:
    """Test cross-module import patterns."""

    def test_import_from_different_packages(self) -> None:
        """Test importing from different packages together."""
        from start_green_stay_green import ai
        from start_green_stay_green import config
        from start_green_stay_green import generators
        from start_green_stay_green import github
        from start_green_stay_green import utils

        all_modules = [ai, config, generators, github, utils]
        assert all(m is not None for m in all_modules)

    def test_module_load_order_independence(self) -> None:
        """Test that modules can be loaded in any order."""
        import importlib

        modules = [
            "start_green_stay_green.utils.templates",
            "start_green_stay_green.ai.orchestrator",
            "start_green_stay_green.github.client",
            "start_green_stay_green.generators.base",
            "start_green_stay_green.config.settings",
        ]

        loaded_modules = []
        for module_name in modules:
            module = importlib.import_module(module_name)
            loaded_modules.append(module)

        assert len(loaded_modules) == len(modules)
        assert all(m is not None for m in loaded_modules)
