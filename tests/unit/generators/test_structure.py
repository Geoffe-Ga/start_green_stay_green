"""Unit tests for Structure Generator."""

import ast
from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator


class TestStructureGeneratorInitialization:
    """Test StructureGenerator initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test StructureGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, StructureGenerator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestStructureGeneration:
    """Test project structure generation."""

    def test_generate_creates_source_directory(self) -> None:
        """Test generate creates source directory with package name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            generator.generate()

            # Should create package directory
            package_dir = Path(tmpdir) / "test_project"
            assert package_dir.exists()
            assert package_dir.is_dir()

    def test_generate_creates_init_file(self) -> None:
        """Test generate creates __init__.py in package directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "test_project/__init__.py" in files
            init_path = files["test_project/__init__.py"]
            assert init_path.exists()
            assert init_path.is_file()

    def test_generate_creates_main_file(self) -> None:
        """Test generate creates main.py with Hello World."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "test_project/main.py" in files
            main_path = files["test_project/main.py"]
            assert main_path.exists()
            assert main_path.is_file()

    def test_init_has_version(self) -> None:
        """Test __init__.py contains version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["test_project/__init__.py"]
            content = init_path.read_text()

            assert "__version__" in content
            assert "0.1.0" in content

    def test_init_has_docstring(self) -> None:
        """Test __init__.py contains package docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["test_project/__init__.py"]
            content = init_path.read_text()

            # Should have triple-quoted docstring
            assert '"""' in content

    def test_main_has_hello_world_function(self) -> None:
        """Test main.py contains a main() function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            main_path = files["test_project/main.py"]
            content = main_path.read_text()

            assert "def main()" in content
            assert "print(" in content

    def test_main_has_if_name_main(self) -> None:
        """Test main.py has if __name__ == '__main__' guard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            main_path = files["test_project/main.py"]
            content = main_path.read_text()

            assert 'if __name__ == "__main__"' in content
            assert "main()" in content

    def test_generated_files_are_valid_python(self) -> None:
        """Test generated files are syntactically valid Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            # Try to compile the generated files
            for file_path in files.values():
                if file_path.suffix == ".py":
                    content = file_path.read_text()
                    # Should compile without SyntaxError
                    ast.parse(content)


class TestStructureConfigValidation:
    """Test StructureConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_generation_error(self) -> None:
        """Test that unsupported language raises GenerationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="rust",  # Not yet supported
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)

            with pytest.raises(GenerationError) as exc_info:
                generator.generate()

            assert "not supported" in str(exc_info.value).lower()
            assert "rust" in str(exc_info.value).lower()
