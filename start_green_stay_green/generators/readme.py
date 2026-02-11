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
from start_green_stay_green.generators.base import validate_language


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
        validate_language(self.config.language)

        # Dispatch to language-specific generator
        generators = {
            "python": self._generate_python_readme,
            "typescript": self._generate_typescript_readme,
            "go": self._generate_go_readme,
            "rust": self._generate_rust_readme,
            "java": self._generate_java_readme,
            "csharp": self._generate_csharp_readme,
            "ruby": self._generate_ruby_readme,
        }
        return {"README.md": generators[self.config.language]()}

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

    def _generate_typescript_readme(self) -> Path:
        """Generate TypeScript README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._typescript_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _typescript_readme_content(self) -> str:
        """Generate TypeScript README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled TypeScript project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (Jest with 90%+ coverage requirement)
- ✅ Code quality tools (ESLint, Prettier, TypeScript)
- ✅ Security scanning (npm audit)
- ✅ Type safety (strict TypeScript configuration)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Install dependencies
npm install

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
npm run build
npm start
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Run linter
npm run lint

# Run linter with auto-fix
npm run lint:fix

# Format code
npm run format

# Build project
npm run build
```

### Quality Tools

This project includes:

- **Jest**: Testing framework with 90%+ coverage requirement
- **ESLint**: JavaScript/TypeScript linter
- **Prettier**: Code formatter
- **TypeScript**: Static type checker
- **npm audit**: Dependency vulnerability scanner

### Project Structure

```
{self.config.project_name}/
├── src/                  # Source code
│   └── index.ts
├── tests/                # Test suite
│   └── index.test.ts
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── jest.config.js        # Jest configuration
├── .eslintrc.js          # ESLint configuration
└── .prettierrc           # Prettier configuration
```

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Type Coverage**: 100% type safety with strict TypeScript
- **All Linters**: Must pass with zero violations
- **Code Style**: Enforced by Prettier

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality TypeScript projects from day one.
"""

    def _generate_go_readme(self) -> Path:
        """Generate Go README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._go_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _go_readme_content(self) -> str:
        """Generate Go README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Go project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (go test with 90%+ coverage requirement)
- ✅ Code quality tools (golangci-lint, gofmt)
- ✅ Security scanning (gosec)
- ✅ Type safety (Go's strong typing system)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Download dependencies
go mod download

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
go run ./...
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run linter
golangci-lint run

# Format code
gofmt -w .

# Build project
go build ./...
```

### Quality Tools

This project includes:

- **go test**: Built-in testing framework with 90%+ coverage requirement
- **golangci-lint**: Comprehensive Go linter (runs multiple linters)
- **gofmt**: Official Go code formatter
- **gosec**: Security vulnerability scanner

### Project Structure

```
{self.config.project_name}/
├── cmd/                  # Command-line applications
│   └── main.go
├── pkg/                  # Reusable packages
├── internal/             # Private application code
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── go.mod                # Go module definition
└── go.sum                # Dependency checksums
```

### Testing

```bash
# Run all tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests with verbose output
go test -v ./...

# Run tests with race detection
go test -race ./...
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Type Safety**: 100% compile-time type checking
- **All Linters**: Must pass with zero violations
- **Code Style**: Enforced by gofmt

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Go projects from day one.
"""

    def _generate_rust_readme(self) -> Path:
        """Generate Rust README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._rust_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _rust_readme_content(self) -> str:
        """Generate Rust README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Rust project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (cargo test with 90%+ coverage requirement)
- ✅ Code quality tools (clippy, rustfmt)
- ✅ Security scanning (cargo audit)
- ✅ Memory safety (Rust's ownership system)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Build the project
cargo build

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
cargo run
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run linter
cargo clippy

# Run linter with strict checks
cargo clippy -- -D warnings

# Format code
cargo fmt

# Check formatting
cargo fmt -- --check

# Build project
cargo build

# Build for release
cargo build --release
```

### Quality Tools

This project includes:

- **cargo test**: Built-in testing framework with 90%+ coverage requirement
- **clippy**: Rust linter for catching common mistakes
- **rustfmt**: Official Rust code formatter
- **cargo audit**: Security vulnerability scanner
- **cargo-tarpaulin**: Code coverage tool

### Project Structure

```
{self.config.project_name}/
├── src/                  # Source code
│   └── main.rs
├── tests/                # Integration tests
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── Cargo.toml            # Package manifest
└── Cargo.lock            # Dependency lock file
```

### Testing

```bash
# Run all tests
cargo test

# Run tests with coverage
cargo tarpaulin --out Html

# Run tests with verbose output
cargo test -- --nocapture

# Run specific test
cargo test test_name
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Memory Safety**: Guaranteed by Rust's ownership system
- **All Linters**: Must pass with zero violations
- **Code Style**: Enforced by rustfmt

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Rust projects from day one.
"""

    def _generate_java_readme(self) -> Path:
        """Generate Java README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._java_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _java_readme_content(self) -> str:
        """Generate Java README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Java project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (JUnit with 90%+ coverage requirement)
- ✅ Code quality tools (Checkstyle, SpotBugs, PMD)
- ✅ Security scanning (OWASP Dependency Check)
- ✅ Type safety (Java's strong typing system)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Build with Maven
mvn clean install

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
mvn exec:java
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
mvn test

# Run tests with coverage
mvn clean test jacoco:report

# Run Checkstyle
mvn checkstyle:check

# Run SpotBugs
mvn spotbugs:check

# Run PMD
mvn pmd:check

# Compile project
mvn compile

# Build project
mvn clean package
```

### Quality Tools

This project includes:

- **JUnit**: Testing framework with 90%+ coverage requirement
- **JaCoCo**: Code coverage tool
- **Checkstyle**: Code style checker
- **SpotBugs**: Static analysis tool for finding bugs
- **PMD**: Source code analyzer
- **Maven**: Build automation and dependency management

### Project Structure

```
{self.config.project_name}/
├── src/
│   ├── main/java/        # Application source code
│   └── test/java/        # Test suite
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── pom.xml               # Maven configuration
└── checkstyle.xml        # Checkstyle configuration
```

### Testing

```bash
# Run all tests
mvn test

# Run tests with coverage report
mvn clean test jacoco:report

# View coverage report
open target/site/jacoco/index.html

# Run specific test class
mvn test -Dtest=TestClassName
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Type Safety**: 100% compile-time type checking
- **All Linters**: Must pass with zero violations
- **Code Style**: Enforced by Checkstyle

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Java projects from day one.
"""

    def _generate_csharp_readme(self) -> Path:
        """Generate C# README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._csharp_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _csharp_readme_content(self) -> str:
        """Generate C# README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled C# project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (xUnit with 90%+ coverage requirement)
- ✅ Code quality tools (Roslyn analyzers, dotnet format)
- ✅ Security scanning (dotnet list package --vulnerable)
- ✅ Type safety (C#'s strong typing system)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Restore dependencies
dotnet restore

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
dotnet run
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
dotnet test

# Run tests with coverage
dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=opencover

# Format code
dotnet format

# Check formatting
dotnet format --verify-no-changes

# Build project
dotnet build

# Build for release
dotnet build -c Release
```

### Quality Tools

This project includes:

- **xUnit**: Testing framework with 90%+ coverage requirement
- **Coverlet**: Code coverage tool
- **Roslyn Analyzers**: Static code analysis
- **dotnet format**: Code formatter
- **NuGet**: Package management with vulnerability scanning

### Project Structure

```
{self.config.project_name}/
├── src/                  # Application source code
│   └── Program.cs
├── tests/                # Test suite
│   └── UnitTests.cs
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── {self.config.project_name}.sln  # Solution file
└── {self.config.project_name}.csproj  # Project file
```

### Testing

```bash
# Run all tests
dotnet test

# Run tests with coverage
dotnet test /p:CollectCoverage=true

# Run tests with verbose output
dotnet test -v detailed

# Run specific test
dotnet test --filter "FullyQualifiedName~TestName"
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Type Safety**: 100% compile-time type checking
- **All Analyzers**: Must pass with zero violations
- **Code Style**: Enforced by dotnet format

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality C# projects from day one.
"""

    def _generate_ruby_readme(self) -> Path:
        """Generate Ruby README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        content = self._ruby_readme_content()

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e

        return readme_path

    def _ruby_readme_content(self) -> str:
        """Generate Ruby README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Ruby project generated with
Start Green Stay Green.

## Description

This project was generated with maximum quality standards from day one, including:

- ✅ Comprehensive testing infrastructure (RSpec with 90%+ coverage requirement)
- ✅ Code quality tools (RuboCop, Reek)
- ✅ Security scanning (Bundler Audit)
- ✅ Type checking (Sorbet or RBS)
- ✅ Pre-commit hooks (quality checks)
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ AI-assisted development (Claude Code skills and subagents)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Install dependencies
bundle install

# Install pre-commit hooks
pre-commit install
```

## Usage

Run the Hello World application:

```bash
bundle exec ruby lib/main.rb
```

Expected output:
```
Hello from {self.config.project_name}!
```

## Development

### Running Quality Checks

```bash
# Run all tests
bundle exec rspec

# Run tests with coverage
bundle exec rspec --format documentation

# Run RuboCop
bundle exec rubocop

# Run RuboCop with auto-correct
bundle exec rubocop -a

# Run Reek (code smell detector)
bundle exec reek

# Run security scan
bundle exec bundle-audit check --update
```

### Quality Tools

This project includes:

- **RSpec**: Testing framework with 90%+ coverage requirement
- **SimpleCov**: Code coverage tool
- **RuboCop**: Ruby linter and code formatter
- **Reek**: Code smell detector
- **Bundler Audit**: Security vulnerability scanner
- **Bundler**: Dependency management

### Project Structure

```
{self.config.project_name}/
├── lib/                  # Application source code
│   └── main.rb
├── spec/                 # Test suite
│   ├── spec_helper.rb
│   └── main_spec.rb
├── scripts/              # Quality control scripts
├── .github/workflows/    # CI/CD pipelines
├── .claude/              # AI subagents and skills
├── Gemfile               # Dependency definition
├── Gemfile.lock          # Dependency lock file
└── .rubocop.yml          # RuboCop configuration
```

### Testing

```bash
# Run all tests
bundle exec rspec

# Run tests with coverage
bundle exec rspec

# View coverage report
open coverage/index.html

# Run specific test file
bundle exec rspec spec/main_spec.rb

# Run tests with documentation format
bundle exec rspec --format documentation
```

### Code Quality

This project maintains MAXIMUM QUALITY standards:

- **Test Coverage**: ≥90% required
- **Code Style**: Enforced by RuboCop
- **All Linters**: Must pass with zero violations
- **Code Smells**: Detected and resolved with Reek

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Ruby projects from day one.
"""
