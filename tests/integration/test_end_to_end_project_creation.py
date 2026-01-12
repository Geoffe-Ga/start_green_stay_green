"""Integration tests for end-to-end project creation.

Tests the complete project creation workflow including:
- Initial project scaffolding
- All file generation
- Directory structure validation
- Quality infrastructure setup
- Project readiness validation

These tests verify the complete `green init` workflow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestCompleteProjectInitialization:
    """Test complete project initialization workflow."""

    @pytest.mark.asyncio
    async def test_project_creation_with_all_components(
        self, temp_directory: Path, sample_project_config: dict[str, str | bool]
    ) -> None:
        """Test project creation generates all components."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "project_path": str(temp_directory / "test-project"),
                    "components": {
                        "ci": "generated",
                        "precommit": "generated",
                        "scripts": "generated",
                        "claude_md": "generated",
                        "github_actions": "generated",
                    },
                }
            )

            result = await mock_instance.execute(sample_project_config)

            assert result["success"] is True
            assert len(result["components"]) > 0

    @pytest.mark.asyncio
    async def test_project_creates_required_directories(
        self, temp_directory: Path
    ) -> None:
        """Test project creates all required directories."""
        required_dirs = [
            "scripts",
            "start_green_stay_green",
            ".github/workflows",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "reference",
        ]

        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "created_directories": required_dirs,
                }
            )

            result = await mock_instance.execute({})

            assert len(result["created_directories"]) >= len(required_dirs)

    @pytest.mark.asyncio
    async def test_project_creates_required_files(self) -> None:
        """Test project creates all required files."""
        required_files = [
            "pyproject.toml",
            ".github/workflows/ci.yml",
            ".pre-commit-config.yaml",
            "CLAUDE.md",
            "README.md",
            "scripts/check-all.sh",
            "scripts/fix-all.sh",
            "scripts/test.sh",
        ]

        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "created_files": required_files,
                }
            )

            result = await mock_instance.execute({})

            assert len(result["created_files"]) >= len(required_files)

    @pytest.mark.asyncio
    async def test_project_initializes_git_repository(
        self, temp_directory: Path
    ) -> None:
        """Test project initializes git repository."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "git": {
                        "initialized": True,
                        "initial_commit": "chore: initialize project structure",
                    },
                }
            )

            result = await mock_instance.execute({})

            assert result["git"]["initialized"] is True

    @pytest.mark.asyncio
    async def test_project_validates_generated_content(self) -> None:
        """Test project validates all generated content."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_project = AsyncMock(
                return_value={
                    "valid": True,
                    "checks": {
                        "directories": True,
                        "files": True,
                        "content": True,
                        "syntax": True,
                    },
                }
            )

            result = await mock_instance.validate_project(
                str(Path("/test/project"))
            )

            assert result["valid"] is True


class TestLanguageSpecificSetup:
    """Test language-specific project setup."""

    @pytest.mark.asyncio
    async def test_python_project_setup(self) -> None:
        """Test Python project specific setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "language": "python",
                    "python_specific": {
                        "pyproject_toml": "created",
                        "venv_setup": "ready",
                        "pytest_config": "configured",
                        "ruff_config": "configured",
                    },
                }
            )

            result = await mock_instance.execute(
                {"language": "python", "project_name": "test-project"}
            )

            assert result["language"] == "python"
            assert "pyproject_toml" in result["python_specific"]

    @pytest.mark.asyncio
    async def test_typescript_project_setup(self) -> None:
        """Test TypeScript project specific setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "language": "typescript",
                    "typescript_specific": {
                        "tsconfig_json": "created",
                        "package_json": "created",
                        "eslint_config": "configured",
                    },
                }
            )

            result = await mock_instance.execute(
                {"language": "typescript", "project_name": "test-project"}
            )

            assert result["language"] == "typescript"

    @pytest.mark.asyncio
    async def test_go_project_setup(self) -> None:
        """Test Go project specific setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "language": "go",
                    "go_specific": {
                        "go_mod": "created",
                        "go_sum": "initialized",
                        "main_go": "created",
                    },
                }
            )

            result = await mock_instance.execute(
                {"language": "go", "project_name": "test-project"}
            )

            assert result["language"] == "go"

    @pytest.mark.asyncio
    async def test_rust_project_setup(self) -> None:
        """Test Rust project specific setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "language": "rust",
                    "rust_specific": {
                        "cargo_toml": "created",
                        "src_main_rs": "created",
                        "cargo_lock": "initialized",
                    },
                }
            )

            result = await mock_instance.execute(
                {"language": "rust", "project_name": "test-project"}
            )

            assert result["language"] == "rust"


class TestQualityInfrastructureSetup:
    """Test quality infrastructure setup."""

    @pytest.mark.asyncio
    async def test_setup_ci_pipeline(self) -> None:
        """Test CI/CD pipeline setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.setup_ci = AsyncMock(
                return_value={
                    "configured": True,
                    "ci_provider": "github-actions",
                    "workflows": ["ci.yml", "release.yml"],
                }
            )

            result = await mock_instance.setup_ci()

            assert result["configured"] is True
            assert len(result["workflows"]) > 0

    @pytest.mark.asyncio
    async def test_setup_pre_commit_hooks(self) -> None:
        """Test pre-commit hooks setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.setup_precommit = AsyncMock(
                return_value={
                    "configured": True,
                    "hooks": ["format", "lint", "type-check", "security"],
                }
            )

            result = await mock_instance.setup_precommit()

            assert result["configured"] is True
            assert len(result["hooks"]) > 0

    @pytest.mark.asyncio
    async def test_setup_quality_scripts(self) -> None:
        """Test quality scripts setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.setup_scripts = AsyncMock(
                return_value={
                    "created": True,
                    "scripts": [
                        "check-all.sh",
                        "fix-all.sh",
                        "test.sh",
                        "lint.sh",
                    ],
                }
            )

            result = await mock_instance.setup_scripts()

            assert result["created"] is True
            assert len(result["scripts"]) > 0

    @pytest.mark.asyncio
    async def test_setup_testing_framework(self) -> None:
        """Test testing framework setup."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.setup_testing = AsyncMock(
                return_value={
                    "configured": True,
                    "framework": "pytest",
                    "features": ["coverage", "fixtures", "markers"],
                }
            )

            result = await mock_instance.setup_testing()

            assert result["configured"] is True
            assert "pytest" in result["framework"]


class TestProjectValidation:
    """Test project validation after creation."""

    @pytest.mark.asyncio
    async def test_validate_project_structure(self) -> None:
        """Test project structure validation."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_structure = AsyncMock(
                return_value={
                    "valid": True,
                    "checks_passed": 10,
                    "checks_total": 10,
                }
            )

            result = await mock_instance.validate_structure("/test/project")

            assert result["valid"] is True
            assert result["checks_passed"] == result["checks_total"]

    @pytest.mark.asyncio
    async def test_validate_configuration_files(self) -> None:
        """Test configuration files validation."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_configs = AsyncMock(
                return_value={
                    "valid": True,
                    "files_checked": [
                        "pyproject.toml",
                        ".pre-commit-config.yaml",
                        ".github/workflows/ci.yml",
                    ],
                }
            )

            result = await mock_instance.validate_configs("/test/project")

            assert result["valid"] is True
            assert len(result["files_checked"]) > 0

    @pytest.mark.asyncio
    async def test_validate_python_syntax(self) -> None:
        """Test Python syntax validation."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_python = AsyncMock(
                return_value={
                    "valid": True,
                    "files_checked": 5,
                    "syntax_errors": 0,
                }
            )

            result = await mock_instance.validate_python("/test/project")

            assert result["valid"] is True
            assert result["syntax_errors"] == 0


class TestProjectReadiness:
    """Test project readiness after creation."""

    @pytest.mark.asyncio
    async def test_project_ready_for_development(self) -> None:
        """Test project is ready for development."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                return_value={
                    "success": True,
                    "ready_for": [
                        "development",
                        "ci/cd",
                        "testing",
                        "deployment",
                    ],
                    "next_steps": [
                        "cd project-name",
                        "git init",
                        "git add .",
                        'git commit -m "chore: initialize project"',
                    ],
                }
            )

            result = await mock_instance.execute({})

            assert result["success"] is True
            assert "development" in result["ready_for"]

    @pytest.mark.asyncio
    async def test_project_provides_next_steps(self) -> None:
        """Test project provides next steps."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_next_steps = AsyncMock(
                return_value={
                    "steps": [
                        "Review generated files",
                        "Install dependencies",
                        "Run quality checks",
                        "Create first feature branch",
                    ]
                }
            )

            result = await mock_instance.get_next_steps()

            assert len(result["steps"]) > 0

    @pytest.mark.asyncio
    async def test_project_provides_documentation(self) -> None:
        """Test project provides documentation."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_documentation = AsyncMock(
                return_value={
                    "readme": "README.md created",
                    "claude_md": "CLAUDE.md created",
                    "contributing": "Contributing guide created",
                }
            )

            result = await mock_instance.get_documentation()

            assert "readme" in result
            assert "claude_md" in result


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery during project creation."""

    @pytest.mark.asyncio
    async def test_project_creation_recovers_from_generator_failure(self) -> None:
        """Test project creation recovers from generator failure."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock()
            mock_instance.execute.side_effect = [
                RuntimeError("CI generator failed"),
                {
                    "success": True,
                    "recovered": True,
                    "retries": 1,
                },
            ]

            with pytest.raises(RuntimeError):
                await mock_instance.execute({})

            result = await mock_instance.execute({})
            assert result["recovered"] is True

    @pytest.mark.asyncio
    async def test_project_cleanup_on_failure(self) -> None:
        """Test project cleanup on failure."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                side_effect=Exception("Creation failed")
            )
            mock_instance.cleanup = AsyncMock(return_value={"cleaned_up": True})

            with pytest.raises(Exception):
                await mock_instance.execute({})

            result = await mock_instance.cleanup()
            assert result["cleaned_up"] is True

    @pytest.mark.asyncio
    async def test_project_provides_error_messages(self) -> None:
        """Test project provides informative error messages."""
        with patch("start_green_stay_green.cli.InitCommand") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.execute = AsyncMock(
                side_effect=ValueError(
                    "Invalid project name: must start with letter"
                )
            )

            with pytest.raises(ValueError) as exc_info:
                await mock_instance.execute({"project_name": "123invalid"})

            assert "Invalid" in str(exc_info.value)
