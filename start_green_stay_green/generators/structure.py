"""Project structure generator.

Generates source code directory structure for target projects (source directory,
__init__.py, Hello World starter code).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError


@dataclass(frozen=True)
class StructureConfig:
    """Configuration for project structure generation.

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


class StructureGenerator(BaseGenerator):
    """Generate project source code structure for target projects.

    This generator creates the source code directory structure (package directory,
    __init__.py, Hello World starter code) for the target project's language.

    Attributes:
        output_dir: Directory where structure will be created
        config: Configuration for structure generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: StructureConfig,
    ) -> None:
        """Initialize the Structure Generator.

        Args:
            output_dir: Directory where structure will be created
            config: StructureConfig with project settings

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
        """Generate project source code structure.

        Returns:
            Dictionary mapping file names to their generated file paths

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        files: dict[str, Path] = {}

        # Generate language-specific structure
        if self.config.language == "python":
            files.update(self._generate_python_structure())
        else:
            # For now, only Python is supported
            msg = f"Language {self.config.language} not supported yet"
            raise GenerationError(msg)

        return files

    def _generate_python_structure(self) -> dict[str, Path]:
        """Generate Python project structure.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Create package directory
        package_dir = self.output_dir / self.config.package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # Generate __init__.py
        init_key = f"{self.config.package_name}/__init__.py"
        files[init_key] = self._write_file(
            package_dir / "__init__.py",
            self._python_init_py(),
        )

        # Generate main.py
        main_key = f"{self.config.package_name}/main.py"
        files[main_key] = self._write_file(
            package_dir / "main.py",
            self._python_main_py(),
        )

        return files

    def _write_file(self, file_path: Path, content: str) -> Path:
        """Write a source file to disk.

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

    def _python_init_py(self) -> str:
        """Generate Python __init__.py content.

        Returns:
            Content for __init__.py with package docstring and version
        """
        # Convert package name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f'''"""{display_name} package."""

__version__ = "0.1.0"
'''

    def _python_main_py(self) -> str:
        """Generate Python main.py content.

        Returns:
            Content for main.py with Hello World function
        """
        return f'''"""Main entry point for {self.config.project_name}."""


def main() -> None:
    """Run the main application."""
    print("Hello from {self.config.project_name}!")


if __name__ == "__main__":
    main()
'''
