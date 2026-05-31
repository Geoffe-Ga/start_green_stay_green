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
        """Passing an orchestrator still works but emits a DeprecationWarning."""
        orchestrator = create_autospec(AIOrchestrator)
        with pytest.warns(DeprecationWarning, match="'orchestrator' parameter"):
            generator = ArchitectureEnforcementGenerator(orchestrator)

        assert generator.orchestrator is orchestrator

    def test_init_without_orchestrator_is_silent(self) -> None:
        """The default (no orchestrator) does not emit a warning."""
        generator = ArchitectureEnforcementGenerator()
        assert generator.orchestrator is None

    def test_init_with_output_dir(self) -> None:
        """Test initialization with custom output directory."""
        output_dir = Path("/custom/plans/architecture")

        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        assert generator.output_dir == output_dir

    def test_init_with_default_output_dir(self) -> None:
        """Test initialization sets default output directory."""
        generator = ArchitectureEnforcementGenerator()

        assert generator.output_dir == Path("plans/architecture")


class TestArchitectureEnforcementGeneratorGenerate:
    """Test architecture enforcement generation."""

    def test_generate_python_creates_importlinter_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating import-linter config for Python."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

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
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(
            language="typescript",
            project_name="test-project",
        )

        # Should create .dependency-cruiser.js file
        dc_file = output_dir / ".dependency-cruiser.js"
        assert dc_file.exists()

    def test_generate_raises_on_unsupported_language(self) -> None:
        """Test generate raises ValueError for unsupported languages."""
        generator = ArchitectureEnforcementGenerator()

        with pytest.raises(ValueError, match="Unsupported language"):
            generator.generate(language="ruby", project_name="test")

    def test_generate_creates_readme_with_usage_instructions(
        self,
        tmp_path: Path,
    ) -> None:
        """Test README contains usage instructions."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

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
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

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
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

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
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="python", project_name="myapp")

        importlinter = output_dir / ".importlinter"
        content = importlinter.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()


class TestArchitectureEnforcementGeneratorGo:
    """Test Go-specific architecture rules."""

    def test_generate_go_creates_go_arch_lint_config(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generating go-arch-lint config for Go."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="test-project")

        # Should create the go-arch-lint config file
        config_file = output_dir / ".go-arch-lint.yml"
        assert config_file.exists()

        # Should create README and run script
        assert (output_dir / "README.md").exists()
        assert (output_dir / "run-check.sh").exists()

    def test_go_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Go config enforces layered architecture components."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        config = (output_dir / ".go-arch-lint.yml").read_text()

        # Should define the architecture layers as components
        assert "components" in config.lower()
        assert "domain" in config.lower()
        assert "presentation" in config.lower()

    def test_go_config_enforces_domain_independence(
        self,
        tmp_path: Path,
    ) -> None:
        """Test Go config keeps the domain layer dependency-free."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        config = (output_dir / ".go-arch-lint.yml").read_text()

        # Domain dependency rules must be present (deps section)
        assert "deps" in config.lower()
        assert "infrastructure" in config.lower()

    def test_go_readme_mentions_go_arch_lint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go README references the go-arch-lint tooling."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        readme = (output_dir / "README.md").read_text()
        assert "go-arch-lint" in readme

    def test_go_run_script_invokes_go_arch_lint(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the Go run-check.sh script invokes go-arch-lint."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="go", project_name="myapp")

        script = (output_dir / "run-check.sh").read_text()
        assert "go-arch-lint" in script

    def test_go_result_reports_go_language(
        self,
        tmp_path: Path,
    ) -> None:
        """Test the result object records the Go language."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        result = generator.generate(language="go", project_name="myapp")

        assert result.language == "go"


class TestArchitectureEnforcementGeneratorTypeScript:
    """Test TypeScript-specific architecture rules."""

    def test_typescript_config_enforces_layer_separation(
        self,
        tmp_path: Path,
    ) -> None:
        """Test TypeScript config enforces layer separation."""
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

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
        output_dir = tmp_path / "plans" / "architecture"
        generator = ArchitectureEnforcementGenerator(output_dir=output_dir)

        generator.generate(language="typescript", project_name="myapp")

        dc_file = output_dir / ".dependency-cruiser.js"
        content = dc_file.read_text()

        # Should check for circular dependencies
        assert "circular" in content.lower() or "cycle" in content.lower()
