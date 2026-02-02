"""Tests directory generator.

Generates tests directory structure for target projects (tests/, tests/__init__.py,
tests/test_main.py with passing test).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError


@dataclass(frozen=True)
class TestsConfig:
    """Configuration for tests structure generation.

    Attributes:
        project_name: Name of the project (e.g., "my-project")
        language: Programming language (python, typescript, go, rust, etc.)
        package_name: Name of the main package/module (e.g., "my_project")
    """

    project_name: str
    language: str
    package_name: str

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        Raises:
            ValueError: If any required field is empty
        """
        if not self.project_name:
            msg = "Project name cannot be empty"
            raise ValueError(msg)
        if not self.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)
        if not self.package_name:
            msg = "Package name cannot be empty"
            raise ValueError(msg)


class TestsGenerator(BaseGenerator):
    """Generate tests directory structure for target projects.

    This generator creates the tests directory structure (tests/, tests/__init__.py,
    tests/test_main.py) with a passing test for the Hello World code.

    Attributes:
        output_dir: Directory where tests structure will be created
        config: Configuration for tests generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: TestsConfig,
    ) -> None:
        """Initialize the Tests Generator.

        Args:
            output_dir: Directory where tests structure will be created
            config: TestsConfig with project settings

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration and ensure output directory exists.

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.config.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)

        if not self.config.package_name:
            msg = "Package name cannot be empty"
            raise ValueError(msg)

        if not self.config.project_name:
            msg = "Project name cannot be empty"
            raise ValueError(msg)

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> dict[str, Any]:
        """Generate tests directory structure.

        Returns:
            Dictionary mapping file names to their generated file paths

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        files: dict[str, Path] = {}

        # Generate language-specific tests structure
        if self.config.language == "python":
            files.update(self._generate_python_tests())
        else:
            # For now, only Python is supported
            msg = f"Language {self.config.language} not supported yet"
            raise GenerationError(msg)

        return files

    def _generate_python_tests(self) -> dict[str, Path]:
        """Generate Python tests structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create tests directory
        tests_dir = self.output_dir / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        # Generate tests/__init__.py
        init_key = "tests/__init__.py"
        files[init_key] = self._write_file(
            tests_dir / "__init__.py",
            self._python_tests_init_py(),
        )

        # Generate tests/test_main.py
        test_main_key = "tests/test_main.py"
        files[test_main_key] = self._write_file(
            tests_dir / "test_main.py",
            self._python_test_main_py(),
        )

        return files

    def _write_file(self, file_path: Path, content: str) -> Path:
        """Write a test file to disk.

        Args:
            file_path: Path where file will be written
            content: Content to write to the file

        Returns:
            Path to the written file

        Raises:
            GenerationError: If file cannot be written
        """
        try:
            file_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write {file_path.name}: {e}"
            raise GenerationError(msg, cause=e) from e
        return file_path

    def _python_tests_init_py(self) -> str:
        """Generate Python tests/__init__.py content.

        Returns:
            Content for tests/__init__.py with package docstring
        """
        return f'"""Tests for {self.config.project_name}."""\n'

    def _python_test_main_py(self) -> str:
        """Generate Python tests/test_main.py content.

        Returns:
            Content for test_main.py with passing test for main()
        """
        return f'''"""Tests for {self.config.package_name}.main module."""

from {self.config.package_name}.main import main


def test_main_runs() -> None:
    """Test that main() runs without error."""
    main()  # Should print "Hello from {self.config.project_name}!"
'''
