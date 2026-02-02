"""Unit tests for Tests Generator."""

import ast
from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.tests_gen import TestsConfig as Config
from start_green_stay_green.generators.tests_gen import TestsGenerator as Generator


class TestGeneratorInitialization:
    """Test TestsGen initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test TestsGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, Generator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestGeneration:
    """Test tests directory structure generation."""

    def test_generate_creates_tests_directory(self) -> None:
        """Test generate creates tests directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            generator.generate()

            # Should create tests directory
            tests_dir = Path(tmpdir) / "tests"
            assert tests_dir.exists()
            assert tests_dir.is_dir()

    def test_generate_creates_init_file(self) -> None:
        """Test generate creates __init__.py in tests directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            assert "tests/__init__.py" in files
            init_path = files["tests/__init__.py"]
            assert init_path.exists()
            assert init_path.is_file()

    def test_generate_creates_test_main_file(self) -> None:
        """Test generate creates test_main.py."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            assert "tests/test_main.py" in files
            test_path = files["tests/test_main.py"]
            assert test_path.exists()
            assert test_path.is_file()

    def test_init_has_docstring(self) -> None:
        """Test tests/__init__.py contains docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["tests/__init__.py"]
            content = init_path.read_text()

            # Should have triple-quoted docstring
            assert '"""' in content

    def test_test_main_has_test_function(self) -> None:
        """Test test_main.py contains a test function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            assert "def test_" in content

    def test_test_main_imports_from_package(self) -> None:
        """Test test_main.py imports from the source package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            # Should import from the package
            assert "from test_project" in content or "import test_project" in content
            assert "main" in content

    def test_test_main_calls_main_function(self) -> None:
        """Test test_main.py calls main() function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            test_path = files["tests/test_main.py"]
            content = test_path.read_text()

            # Should call main()
            assert "main()" in content

    def test_generated_files_are_valid_python(self) -> None:
        """Test generated files are syntactically valid Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)
            files = generator.generate()

            # Try to compile the generated files
            for file_path in files.values():
                if file_path.suffix == ".py":
                    content = file_path.read_text()
                    # Should compile without SyntaxError
                    ast.parse(content)


class TestConfigValidation:
    """Test TestsGenConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            Config(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_generation_error(self) -> None:
        """Test that unsupported language raises GenerationError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(
                project_name="test-project",
                language="rust",  # Not yet supported
                package_name="test_project",
            )
            generator = Generator(Path(tmpdir), config)

            with pytest.raises(GenerationError) as exc_info:
                generator.generate()

            assert "not supported" in str(exc_info.value).lower()
            assert "rust" in str(exc_info.value).lower()
