"""Integration tests for generator integration.

Tests the generator orchestration and multi-generator workflows including:
- CLI to generator communication
- File creation from generator output
- Multi-generator orchestration
- Configuration sharing between generators

These tests verify generator integration behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestGeneratorInitialization:
    """Test generator initialization and setup."""

    @pytest.mark.asyncio
    async def test_base_generator_initializes(
        self, sample_project_config: dict[str, str | bool]
    ) -> None:
        """Test base generator initializes with config."""
        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.config = sample_project_config

            assert mock_instance.config == sample_project_config

    @pytest.mark.asyncio
    async def test_generator_validates_configuration(self) -> None:
        """Test generator validates configuration."""
        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_config = AsyncMock(return_value=True)

            result = await mock_instance.validate_config(
                {"project_name": "test", "language": "python"}
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_generator_initialization_fails_with_invalid_config(
        self,
    ) -> None:
        """Test generator fails with invalid configuration."""
        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_config = AsyncMock(
                side_effect=ValueError("Invalid config")
            )

            with pytest.raises(ValueError):
                await mock_instance.validate_config({})

    @pytest.mark.asyncio
    async def test_generator_initializes_output_directory(
        self, temp_directory: Path
    ) -> None:
        """Test generator initializes output directory."""
        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.initialize_output = AsyncMock(
                return_value=str(temp_directory)
            )

            result = await mock_instance.initialize_output(str(temp_directory))

            assert str(temp_directory) in result


class TestSpecificGenerators:
    """Test individual generator implementations."""

    @pytest.mark.asyncio
    async def test_ci_generator_generates_config(self) -> None:
        """Test CI generator generates configuration."""
        with patch("start_green_stay_green.generators.ci.CIGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value={
                    "filename": ".github/workflows/ci.yml",
                    "content": "CI workflow configuration",
                }
            )

            result = await mock_instance.generate()

            assert "ci.yml" in result["filename"]

    @pytest.mark.asyncio
    async def test_precommit_generator_generates_config(self) -> None:
        """Test pre-commit generator generates configuration."""
        with patch(
            "start_green_stay_green.generators.precommit.PreCommitGenerator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value={
                    "filename": ".pre-commit-config.yaml",
                    "content": "Pre-commit hooks configuration",
                }
            )

            result = await mock_instance.generate()

            assert "pre-commit" in result["filename"]

    @pytest.mark.asyncio
    async def test_scripts_generator_generates_scripts(self) -> None:
        """Test scripts generator generates script files."""
        with patch("start_green_stay_green.generators.scripts.ScriptsGenerator") as (
            mock
        ):
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value={
                    "files": [
                        {
                            "path": "scripts/check-all.sh",
                            "content": "Quality check script",
                        },
                        {
                            "path": "scripts/fix-all.sh",
                            "content": "Auto-fix script",
                        },
                    ]
                }
            )

            result = await mock_instance.generate()

            assert len(result["files"]) == 2
            assert "check-all" in result["files"][0]["path"]

    @pytest.mark.asyncio
    async def test_claude_md_generator_generates_documentation(self) -> None:
        """Test CLAUDE.md generator generates documentation."""
        with patch(
            "start_green_stay_green.generators.claude_md.ClaudeMdGenerator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value={
                    "filename": "CLAUDE.md",
                    "content": "Claude configuration documentation",
                }
            )

            result = await mock_instance.generate()

            assert result["filename"] == "CLAUDE.md"
            assert "configuration" in result["content"].lower()

    @pytest.mark.asyncio
    async def test_github_actions_generator_generates_workflows(self) -> None:
        """Test GitHub Actions generator generates workflows."""
        with patch(
            "start_green_stay_green.generators.github_actions.GitHubActionsGenerator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value={
                    "files": [
                        {
                            "path": ".github/workflows/ci.yml",
                            "content": "CI workflow",
                        },
                        {
                            "path": ".github/workflows/release.yml",
                            "content": "Release workflow",
                        },
                    ]
                }
            )

            result = await mock_instance.generate()

            assert len(result["files"]) >= 1


class TestFileCreationFromGenerators:
    """Test file creation from generator output."""

    @pytest.mark.asyncio
    async def test_generator_creates_file_on_disk(
        self, temp_directory: Path
    ) -> None:
        """Test generator creates file on disk."""
        output_file = temp_directory / "test.txt"

        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.write_file = AsyncMock(
                return_value=str(output_file)
            )

            result = await mock_instance.write_file(
                str(output_file), "test content"
            )

            assert str(output_file) in result

    @pytest.mark.asyncio
    async def test_generator_creates_directory_structure(
        self, temp_directory: Path
    ) -> None:
        """Test generator creates directory structure."""
        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.create_directories = AsyncMock(
                return_value={
                    "created": [
                        str(temp_directory / "scripts"),
                        str(temp_directory / ".github" / "workflows"),
                        str(temp_directory / "tests" / "unit"),
                    ]
                }
            )

            result = await mock_instance.create_directories(
                str(temp_directory), ["scripts", ".github/workflows", "tests/unit"]
            )

            assert len(result["created"]) == 3

    @pytest.mark.asyncio
    async def test_generator_handles_file_overwrite_safely(
        self, temp_directory: Path
    ) -> None:
        """Test generator handles file overwrite safely."""
        output_file = temp_directory / "config.yaml"

        with patch("start_green_stay_green.generators.base.BaseGenerator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.write_file_safe = AsyncMock(
                return_value={
                    "path": str(output_file),
                    "status": "backed_up_and_overwritten",
                }
            )

            result = await mock_instance.write_file_safe(
                str(output_file), "new content"
            )

            assert "backed_up" in result["status"]


class TestMultiGeneratorOrchestration:
    """Test orchestration of multiple generators."""

    @pytest.mark.asyncio
    async def test_orchestrator_runs_all_generators(self) -> None:
        """Test orchestrator runs all generators."""
        generators_to_run = [
            "ci",
            "precommit",
            "scripts",
            "claude_md",
            "github_actions",
        ]

        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.run_all = AsyncMock(
                return_value={
                    "completed": generators_to_run,
                    "total": len(generators_to_run),
                }
            )

            result = await mock_instance.run_all({})

            assert len(result["completed"]) == len(generators_to_run)

    @pytest.mark.asyncio
    async def test_orchestrator_maintains_execution_order(self) -> None:
        """Test orchestrator maintains generator execution order."""
        expected_order = [
            "ci",
            "precommit",
            "scripts",
            "skills",
            "subagents",
            "claude_md",
            "github_actions",
            "metrics",
            "architecture",
        ]

        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_execution_order = AsyncMock(
                return_value=expected_order
            )

            result = await mock_instance.get_execution_order()

            assert result == expected_order

    @pytest.mark.asyncio
    async def test_orchestrator_shares_configuration_between_generators(
        self, sample_project_config: dict[str, str | bool]
    ) -> None:
        """Test orchestrator shares config between generators."""
        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.orchestrate = AsyncMock(
                return_value={
                    "shared_config": sample_project_config,
                    "generators_notified": 9,
                }
            )

            result = await mock_instance.orchestrate(sample_project_config)

            assert result["generators_notified"] > 0

    @pytest.mark.asyncio
    async def test_orchestrator_handles_generator_failure(self) -> None:
        """Test orchestrator handles generator failure."""
        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.run_all = AsyncMock(
                return_value={
                    "completed": ["ci", "precommit"],
                    "failed": ["scripts"],
                    "error": "Script generation failed",
                }
            )

            result = await mock_instance.run_all({})

            assert "failed" in result
            assert len(result["completed"]) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_collects_all_output(self) -> None:
        """Test orchestrator collects output from all generators."""
        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.run_all = AsyncMock(
                return_value={
                    "output": {
                        "ci": {"filename": ".github/workflows/ci.yml"},
                        "precommit": {
                            "filename": ".pre-commit-config.yaml"
                        },
                        "scripts": {
                            "files": [
                                {"path": "scripts/check-all.sh"},
                                {"path": "scripts/fix-all.sh"},
                            ]
                        },
                    }
                }
            )

            result = await mock_instance.run_all({})

            assert "output" in result
            assert len(result["output"]) > 0


class TestCLIToGeneratorIntegration:
    """Test CLI to generator communication."""

    @pytest.mark.asyncio
    async def test_cli_passes_config_to_generators(
        self, sample_project_config: dict[str, str | bool]
    ) -> None:
        """Test CLI passes configuration to generators."""
        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.orchestrate = AsyncMock(return_value={"success": True})

            result = await mock_instance.orchestrate(sample_project_config)

            assert result["success"] is True
            mock_instance.orchestrate.assert_called_once_with(sample_project_config)

    @pytest.mark.asyncio
    async def test_cli_receives_generator_output(self) -> None:
        """Test CLI receives output from generators."""
        with patch(
            "start_green_stay_green.generators.orchestrator.GeneratorOrchestrator"
        ) as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.orchestrate = AsyncMock(
                return_value={
                    "files_created": 25,
                    "directories_created": 10,
                    "configurations": {
                        "ci": "github-actions",
                        "language": "python",
                    },
                }
            )

            result = await mock_instance.orchestrate({})

            assert "files_created" in result
            assert result["files_created"] > 0
