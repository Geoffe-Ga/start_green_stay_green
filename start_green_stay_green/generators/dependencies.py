"""Dependencies file generator.

Generates dependency files for target projects (requirements.txt, requirements-dev.txt,
pyproject.toml) with appropriate dependencies and tool configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError


@dataclass(frozen=True)
class DependencyConfig:
    """Configuration for dependency file generation.

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


class DependenciesGenerator(BaseGenerator):
    """Generate dependency files for target projects.

    This generator creates dependency files (requirements.txt, requirements-dev.txt,
    pyproject.toml) with appropriate dependencies and tool configurations for the
    target project's language and tooling.

    Attributes:
        output_dir: Directory where dependency files will be written
        config: Configuration for dependency file generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: DependencyConfig,
    ) -> None:
        """Initialize the Dependencies Generator.

        Args:
            output_dir: Directory where dependency files will be created
            config: DependencyConfig with project settings

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
        """Generate all dependency files.

        Returns:
            Dictionary mapping file names to their generated file paths

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        files: dict[str, Path] = {}

        # Generate language-specific dependency files
        if self.config.language == "python":
            files.update(self._generate_python_dependencies())
        else:
            # For now, only Python is supported
            msg = f"Language {self.config.language} not supported yet"
            raise GenerationError(msg)

        return files

    def _generate_python_dependencies(self) -> dict[str, Path]:
        """Generate Python dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate requirements.txt (empty for Hello World)
        files["requirements.txt"] = self._write_file(
            "requirements.txt",
            self._python_requirements_txt(),
        )

        # Generate requirements-dev.txt (all dev tools)
        files["requirements-dev.txt"] = self._write_file(
            "requirements-dev.txt",
            self._python_requirements_dev_txt(),
        )

        # Generate pyproject.toml (project metadata + tool configs)
        files["pyproject.toml"] = self._write_file(
            "pyproject.toml",
            self._python_pyproject_toml(),
        )

        return files

    def _write_file(self, filename: str, content: str) -> Path:
        """Write a dependency file to disk.

        Args:
            filename: Name of the file to write
            content: Content to write to the file

        Returns:
            Path to the written file

        Raises:
            GenerationError: If file cannot be written
        """
        file_path = self.output_dir / filename
        try:
            file_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write {filename}: {e}"
            raise GenerationError(msg, cause=e) from e
        return file_path

    def _python_requirements_txt(self) -> str:
        """Generate Python requirements.txt content.

        Returns:
            Content for requirements.txt (empty for Hello World starter)
        """
        return """# Runtime dependencies
# Add your production dependencies here
"""

    def _python_requirements_dev_txt(self) -> str:
        """Generate Python requirements-dev.txt content.

        Returns:
            Content for requirements-dev.txt with all dev tools
        """
        return """# Development dependencies
# Testing
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0
pytest-xdist>=3.3.0

# Code quality
ruff>=0.1.0
black>=23.0.0
isort>=5.12.0
mypy>=1.5.0

# Security
bandit>=1.7.5
safety>=2.3.0

# Complexity analysis
radon>=6.0.0
xenon>=0.9.0

# Mutation testing
mutmut>=2.4.0

# Pre-commit hooks
pre-commit>=3.4.0

# Type stubs
types-PyYAML>=6.0.0
"""

    def _python_pyproject_toml(self) -> str:
        """Generate Python pyproject.toml content.

        Returns:
            Content for pyproject.toml with project metadata and tool configs
        """
        return f"""# pyproject.toml - Python project configuration

[project]
name = "{self.config.project_name}"
version = "0.1.0"
description = "A quality-controlled Python project"
readme = "README.md"
requires-python = ">=3.11"
license = {{ text = "MIT" }}
authors = [
    {{ name = "Generated by SGSG" }}
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "bandit>=1.7.5",
    "radon>=6.0.0",
    "mutmut>=2.4.0",
    "pre-commit>=3.4.0",
]

[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ["py311", "py312", "py313"]
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--cov={self.config.package_name}",
    "--cov-branch",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=90",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

[tool.coverage.run]
source = ["{self.config.package_name}"]
branch = true
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/venv/*",
    "*/virtualenv/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
fail_under = 90

[tool.coverage.html]
directory = "htmlcov"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_equality = true
strict_concatenate = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "RUF",    # Ruff-specific rules
]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/**/*" = ["S101"]  # Allow assert in tests

[tool.bandit]
exclude_dirs = ["tests", "venv", "virtualenv"]
skips = ["B101"]  # Skip assert_used in tests

[tool.mutmut]
paths_to_mutate = "{self.config.package_name}/"
backup = false
runner = "python -m pytest --exitfirst --quiet --tb=no"
tests_dir = "tests/"
"""
