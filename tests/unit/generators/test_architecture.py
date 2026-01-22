"""Unit tests for Architecture Enforcement Generator."""

from pathlib import Path
from unittest.mock import create_autospec

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator,
)


class TestArchitectureEnforcementGeneratorInit:
    """Test ArchitectureEnforcementGenerator initialization."""

    def test_init_with_orchestrator(self) -> None:
        """Test initialization with AI orchestrator."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ArchitectureEnforcementGenerator(orchestrator)

        assert generator.orchestrator is orchestrator

    def test_init_with_output_dir(self) -> None:
        """Test initialization with custom output directory."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = Path("/custom/plans/architecture")

        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        assert generator.output_dir == output_dir

    def test_init_with_default_output_dir(self) -> None:
        """Test initialization sets default output directory."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ArchitectureEnforcementGenerator(orchestrator)

        assert generator.output_dir == Path("plans/architecture")


class TestArchitectureEnforcementGeneratorGenerate:
    """Test architecture enforcement generation."""

    def test_generate_python_creates_importlinter_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating import-linter config for Python."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="python", project_name="test-project")

        # Should create output directory
        assert output_dir.exists()

        # Should create .importlinter file
        importlinter_file = output_dir / ".importlinter"
        assert importlinter_file.exists()

        # Should create README
        readme_file = output_dir / "README.md"
        assert readme_file.exists()

        # Should create run script
        run_script = output_dir / "run-check.sh"
        assert run_script.exists()

    def test_generate_typescript_creates_dependency_cruiser_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating dependency-cruiser config for TypeScript."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(
            language="typescript",
            project_name="test-project",
        )

        # Should create .dependency-cruiser.js file
        dc_file = output_dir / ".dependency-cruiser.js"
        assert dc_file.exists()

    def test_generate_raises_on_unsupported_language(self) -> None:
        """Test generate raises ValueError for unsupported languages."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ArchitectureEnforcementGenerator(orchestrator)

        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="ruby", project_name="test")

    def test_generate_creates_readme_with_usage_instructions(
        self,
        tmp_path: Path,
    ) -> None:
        """Test README contains usage instructions."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="python", project_name="test-project")

        readme = output_dir / "README.md"
        content = readme.read_text()

        # Should contain usage instructions
        assert "Architecture Enforcement" in content
        assert "import-linter" in content
        assert "run-check.sh" in content

    def test_generate_run_script_is_executable(
        self,
        tmp_path: Path,
    ) -> None:
        """Test run-check.sh is created with executable permissions."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="python", project_name="test-project")

        run_script = output_dir / "run-check.sh"
        # Check file has executable bit
        assert run_script.stat().st_mode & 0o111  # Any execute bit set


class TestArchitectureEnforcementGeneratorPython:
    """Test Python-specific architecture rules."""

    def test_python_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Python config enforces layer separation."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="python", project_name="myapp")

        importlinter = output_dir / ".importlinter"
        content = importlinter.read_text()

        # Should enforce layer separation
        assert "layers" in content.lower() or "contract" in content.lower()

    def test_python_config_prevents_circular_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Python config prevents circular dependencies."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="python", project_name="myapp")

        importlinter = output_dir / ".importlinter"
        content = importlinter.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()


class TestArchitectureEnforcementGeneratorTypeScript:
    """Test TypeScript-specific architecture rules."""

    def test_typescript_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test TypeScript config enforces layer separation."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="typescript", project_name="myapp")

        dc_file = output_dir / ".dependency-cruiser.js"
        content = dc_file.read_text()

        # Should enforce layer rules
        assert "forbidden" in content or "allowed" in content

    def test_typescript_config_prevents_circular_dependencies(
        self,
        tmp_path: Path,
    ) -> None:
        """Test TypeScript config prevents circular dependencies."""
        orchestrator = create_autospec(AIOrchestrator)
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(
            orchestrator,
            output_dir=output_dir,
        )

        generator.generate(language="typescript", project_name="myapp")

        dc_file = output_dir / ".dependency-cruiser.js"
        content = dc_file.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()
