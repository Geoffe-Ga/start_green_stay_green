"""Unit tests for Dependencies Generator."""

from pathlib import Path
import tempfile
import tomllib

import pytest

from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig


class TestDependenciesGeneratorInitialization:
    """Test DependenciesGenerator initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test DependenciesGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, DependenciesGenerator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestDependenciesGeneration:
    """Test dependency file generation."""

    def test_generate_creates_all_files(self) -> None:
        """Test generate creates all dependency files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "requirements.txt" in files
            assert "requirements-dev.txt" in files
            assert "pyproject.toml" in files
            assert len(files) == 3

    def test_requirements_txt_is_empty(self) -> None:
        """Test requirements.txt is empty for Hello World starter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            requirements_path = files["requirements.txt"]
            content = requirements_path.read_text()
            # Should have comment but no actual dependencies
            assert "# Runtime dependencies" in content or not content.strip()

    def test_requirements_dev_has_all_tools(self) -> None:
        """Test requirements-dev.txt contains all development tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            requirements_dev_path = files["requirements-dev.txt"]
            content = requirements_dev_path.read_text()

            # All tools referenced by generated scripts
            assert "pytest" in content
            assert "pytest-cov" in content
            assert "ruff" in content
            assert "mypy" in content
            assert "black" in content
            assert "isort" in content
            assert "bandit" in content
            assert "radon" in content
            assert "mutmut" in content
            assert "pre-commit" in content

    def test_pyproject_toml_is_valid_toml(self) -> None:
        """Test pyproject.toml is valid TOML format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            pyproject_path = files["pyproject.toml"]
            content = pyproject_path.read_text()

            # Should parse without errors
            data = tomllib.loads(content)
            assert isinstance(data, dict)

    def test_pyproject_toml_has_tool_configs(self) -> None:
        """Test pyproject.toml contains tool configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            pyproject_path = files["pyproject.toml"]
            content = pyproject_path.read_text()
            data = tomllib.loads(content)

            # Should have tool configurations
            assert "tool" in data
            tools = data["tool"]

            # Check for common tool configs
            assert "black" in tools or "ruff" in tools
            assert "pytest" in tools or "tool.pytest.ini_options" in str(data)

    def test_pyproject_toml_has_project_metadata(self) -> None:
        """Test pyproject.toml contains project metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            pyproject_path = files["pyproject.toml"]
            content = pyproject_path.read_text()
            data = tomllib.loads(content)

            # Should have project metadata
            assert "project" in data
            project = data["project"]
            assert project["name"] == "test-project"

    def test_generated_files_exist_on_filesystem(self) -> None:
        """Test that generated files are actually written to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            for filename, filepath in files.items():
                assert filepath.exists(), f"{filename} should exist on filesystem"
                assert filepath.is_file(), f"{filename} should be a file"


class TestDependencyConfigValidation:
    """Test DependencyConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            DependencyConfig(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            DependencyConfig(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            DependencyConfig(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )
