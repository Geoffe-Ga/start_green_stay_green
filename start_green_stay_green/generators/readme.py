"""README generator.

Generates README.md file for target projects with project description,
installation instructions, usage guide, and quality tools documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError


@dataclass(frozen=True)
class ReadmeConfig:
    """Configuration for README generation.

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


class ReadmeGenerator(BaseGenerator):
    """Generate README.md for target projects.

    This generator creates a comprehensive README.md file with project
    description, installation instructions, usage guide, and documentation
    for the quality tools included in the project.

    Attributes:
        output_dir: Directory where README.md will be created
        config: Configuration for README generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: ReadmeConfig,
    ) -> None:
        """Initialize the README Generator.

        Args:
            output_dir: Directory where README.md will be created
            config: ReadmeConfig with project settings

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
        """Generate README.md.

        Returns:
            Dictionary mapping file name to generated file path

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        files: dict[str, Path] = {}

        # Generate language-specific README
        if self.config.language == "python":
            files["README.md"] = self._generate_python_readme()
        else:
            # For now, only Python is supported
            msg = f"Language {self.config.language} not supported yet"
            raise GenerationError(msg)

        return files

    def _generate_python_readme(self) -> Path:
        """Generate Python README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._python_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _python_readme_content(self) -> str:
        """Generate Python README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Python project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (pytest with 90%+ coverage requirement)
- ✅ Code quality tools (ruff, black, isort, mypy)
- ✅ Security scanning (bandit, safety)
- ✅ Complexity analysis (radon, xenon)
- ✅ Mutation testing (mutmut)
- ✅ Pre-commit hooks (32 quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
python -m {self.config.package_name}.main
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all quality checks (recommended before commit)
pre-commit run --all-files

# Or run individual checks:
./scripts/test.sh          # Run tests with coverage
./scripts/lint.sh          # Run linting
./scripts/format.sh --fix  # Auto-format code
./scripts/typecheck.sh     # Run type checking
./scripts/check-all.sh     # Run all checks
```

### Quality Tools

This project includes:

- **pytest**: Testing framework with 90%+ coverage requirement
- **ruff**: Fast Python linter (replaces flake8, isort, and more)
- **black**: Code formatter
- **isort**: Import sorting
- **mypy**: Static type checker
- **bandit**: Security linter
- **safety**: Dependency vulnerability scanner
- **radon/xenon**: Code complexity analysis (≤10 cyclomatic complexity)
- **mutmut**: Mutation testing (≥80% mutation score recommended)
- **pre-commit**: Git hooks framework (32 quality checks)

### Project Structure

```
{self.config.project_name}/
├── {self.config.package_name}/     # Main package
│   ├── __init__.py
│   └── main.py
├── tests/                # Test suite
│   ├── __init__.py
│   └── test_main.py
├── scripts/              # Quality control scripts
│   ├── check-all.sh
│   ├── test.sh
│   ├── lint.sh
│   ├── format.sh
│   ├── typecheck.sh
│   ├── coverage.sh
│   ├── security.sh
│   ├── complexity.sh
│   └── mutation.sh
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── requirements.txt      # Runtime dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml        # Tool configurations
└── .pre-commit-config.yaml  # Pre-commit hooks
```

### Testing

```bash
# Run tests
./scripts/test.sh

# Run tests with coverage report
./scripts/coverage.sh

# Run tests with HTML coverage report
./scripts/coverage.sh --html
# View htmlcov/index.html in browser
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Cyclomatic Complexity**: ≤10 per function
- **Mutation Score**: ≥80% recommended (periodic check)
- **All Linters**: Must pass with zero violations
- **Type Coverage**: 100% type hints

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Python projects from day one.
"""
