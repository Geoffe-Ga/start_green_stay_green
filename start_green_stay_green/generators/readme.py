"""README generator.

Generates README.md file for target projects with project description,
installation instructions, usage guide, and quality tools documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import validate_language
from start_green_stay_green.utils.cpp import CATCH2_VERSION
from start_green_stay_green.utils.cpp import CMAKE_MINIMUM_VERSION
from start_green_stay_green.utils.cpp import CPP_STANDARD
from start_green_stay_green.utils.cpp import cpp_identifier
from start_green_stay_green.utils.cpp import tizen_app_id
from start_green_stay_green.utils.kotlin import android_package
from start_green_stay_green.utils.kotlin import android_package_path
from start_green_stay_green.utils.naming import pascal_case

if TYPE_CHECKING:
    from start_green_stay_green.utils.file_writer import FileWriter


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

    All 10 supported languages (python, typescript, go, rust, java, csharp,
    ruby, swift, kotlin, cpp) are available at the generator level. Note that
    the full CLI pipeline (``sgsg init``) skips its quality-tooling steps
    (pre-commit, scripts, CI, architecture, metrics) for java, csharp, ruby,
    and cpp; C/C++ tooling arrives with #362/#363. Kotlin runs the full
    pipeline (quality tooling #357, CI #358).

    Attributes:
        output_dir: Directory where README.md will be created
        config: Configuration for README generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: ReadmeConfig,
        *,
        file_writer: FileWriter | None = None,
    ) -> None:
        """Initialize the README Generator.

        Args:
            output_dir: Directory where README.md will be created
            config: ReadmeConfig with project settings
            file_writer: Optional FileWriter for additive behavior.
                If provided, existing files are skipped instead of overwritten.

        Raises:
            ValueError: If output_dir is invalid or language is unsupported
        """
        self.output_dir = Path(output_dir)
        self.config = config
        self._file_writer = file_writer
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

    def _write_readme(self, readme_path: Path, content: str) -> Path:
        """Write README.md to disk.

        If a FileWriter is configured, delegates to it for existence checking.
        Otherwise, writes directly (original behavior).

        Args:
            readme_path: Path where README.md will be written.
            content: README content to write.

        Returns:
            Path to the written README.md.

        Raises:
            GenerationError: If file cannot be written.
        """
        if self._file_writer is not None:
            self._file_writer.write_file(readme_path, content)
            return readme_path

        try:
            readme_path.write_text(content)
        except OSError as e:
            msg = f"Failed to write README.md: {e}"
            raise GenerationError(msg, cause=e) from e
        return readme_path

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
            "swift": self._generate_swift_readme,
            "kotlin": self._generate_kotlin_readme,
            "cpp": self._generate_cpp_readme,
        }
        return {"README.md": generators[self.config.language]()}

    def _generate_python_readme(self) -> Path:
        """Generate Python README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        return self._write_readme(readme_path, self._python_readme_content())

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
- ✅ Security scanning (bandit, pip-audit)
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
- **pip-audit**: Dependency vulnerability scanner
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
        return self._write_readme(readme_path, self._typescript_readme_content())

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
        return self._write_readme(readme_path, self._go_readme_content())

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
        return self._write_readme(readme_path, self._rust_readme_content())

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
        return self._write_readme(readme_path, self._java_readme_content())

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
        return self._write_readme(readme_path, self._csharp_readme_content())

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
        return self._write_readme(readme_path, self._ruby_readme_content())

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

    def _generate_swift_readme(self) -> Path:
        """Generate Swift README.md.

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        return self._write_readme(readme_path, self._swift_readme_content())

    def _swift_readme_content(self) -> str:
        """Generate Swift README.md content.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()
        type_name = pascal_case(self.config.package_name)

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Swift watchOS project generated with
Start Green Stay Green.

## Description

This Swift scaffold is a quality-controlled watchOS project. The following
are generated today:

- ✅ Apple Watch (watchOS) app target built with SwiftUI
- ✅ Swift Package Manager manifest (Package.swift)
- ✅ XCTest test target
- ✅ Code quality tools (SwiftLint + swift-format, configured in .swiftlint.yml)
- ✅ Pre-commit hooks (format, lint, secret scanning via gitleaks)
- ✅ Quality scripts (./scripts/check-all.sh with a 90%+ coverage gate)
- ✅ Security & dead-code scanning (Periphery via ./scripts/security.sh)
- ✅ Architecture enforcement (SwiftLint custom rules)
- ✅ This README

### Planned / coming soon

These quality features are part of the Start Green Stay Green roadmap for
Swift but are **not yet generated** by this scaffold — do not assume they
are configured:

- CI/CD pipeline (GitHub Actions)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Resolve package dependencies
swift package resolve

# Install the quality toolchain (Homebrew)
brew install swiftlint swift-format periphery

# Install the pre-commit hooks
pre-commit install
```

## Usage

Build and run the watchOS Hello World app:

```bash
swift build
```

Open the package in Xcode to run the SwiftUI app on the Apple Watch
simulator:

```bash
open Package.swift
```

Expected output (in the watchOS app UI):
```
Hello from {self.config.project_name}!
```

## Development

### Building and Testing

```bash
# Build the package
swift build

# Run all tests
swift test

# Run tests with code coverage
swift test --enable-code-coverage

# Run every quality gate (format, lint, tests + coverage, security)
./scripts/check-all.sh
```

> **Note:** A CI pipeline (GitHub Actions) is on the roadmap but not yet
> configured by this scaffold. See *Planned / coming soon* above.

### Quality Tools

This scaffold currently includes:

- **XCTest**: Built-in testing framework
- **Swift Package Manager**: Dependency management and build tooling
- **SwiftLint**: Linting with cyclomatic complexity ≤10 (.swiftlint.yml)
- **swift-format**: Code formatting (./scripts/format.sh)
- **Periphery**: Dead-code detection (./scripts/security.sh)
- **Pre-commit hooks**: swift-format, SwiftLint, gitleaks, detect-secrets
- **Architecture rules**: SwiftLint custom rules (plans/architecture/)

### Project Structure

```
{self.config.project_name}/
├── Sources/             # Swift source code (watchOS app target)
│   └── {self.config.package_name}/
│       ├── {type_name}App.swift  # SwiftUI @main App entry
│       └── ContentView.swift     # SwiftUI watchOS view
├── Tests/               # XCTest test target
└── Package.swift        # Swift Package Manager manifest
```

### Testing

```bash
# Run all tests
swift test

# Run tests with code coverage
swift test --enable-code-coverage

# Run a specific test
swift test --filter TestName
```

### Code Quality

This scaffold is a MAXIMUM QUALITY Swift project. Today it provides:

- **Type Safety**: 100% compile-time type checking (inherent to Swift)
- **XCTest test target**: ready for you to add tests
- **Coverage gate**: ./scripts/test.sh --coverage enforces ≥90% line coverage
- **Complexity gate**: SwiftLint errors on cyclomatic complexity >10
- **Formatting & linting**: swift-format and SwiftLint, locally and in
  pre-commit

A CI pipeline is planned (see *Planned / coming soon* above) and is not yet
wired into this scaffold.

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Swift watchOS projects from day one.
"""

    def _generate_kotlin_readme(self) -> Path:
        """Generate the Kotlin Wear OS README.md (#356).

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        return self._write_readme(readme_path, self._kotlin_readme_content())

    def _kotlin_readme_content(self) -> str:
        """Generate Kotlin README.md content.

        Only artifacts the scaffold actually generates carry a checkmark.
        With the #357 quality toolchain (ktlint/detekt, pre-commit hooks,
        quality scripts, Kover coverage gate, Konsist architecture test)
        and the #358 CI pipeline both generated, every roadmap item is
        real and the 'Planned / coming soon' section is gone (#360). The
        Gradle wrapper remains a documented install step — binary
        artifacts are never scaffolded.

        Returns:
            Content for README.md
        """
        # Convert project name to title case for display
        display_name = self.config.project_name.replace("-", " ").title()
        namespace = android_package(self.config.package_name)
        package_path = android_package_path(self.config.package_name)

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled Kotlin Wear OS project generated with
Start Green Stay Green.

## Description

This Kotlin scaffold is a quality-controlled Wear OS (Galaxy Watch 4+ /
Wear OS 3) project. The following are generated today:

- ✅ Wear OS app target built with Jetpack Compose for Wear OS
  (androidx.wear.compose)
- ✅ Gradle (Kotlin DSL) manifests (settings.gradle.kts, build.gradle.kts,
  gradle.properties, app/build.gradle.kts)
- ✅ AndroidManifest.xml with the `wear` device profile (watch hardware
  feature + standalone app metadata)
- ✅ JUnit unit-test scaffold (app/src/test)
- ✅ Code quality tools (ktlint + detekt, configured in detekt.yml)
- ✅ Pre-commit hooks (format, static analysis, secret scanning via gitleaks)
- ✅ Quality scripts (./scripts/check-all.sh with a 90%+ Kover coverage gate)
- ✅ Security scanning (OWASP dependency-check via ./scripts/security.sh)
- ✅ Architecture enforcement (Konsist test, plans/architecture/)
- ✅ CI/CD pipeline (.github/workflows/ci.yml — ubuntu runners, quality
  job with the Kover coverage gate, JDK 17 and 21 test matrix, Wear OS
  APK build)
- ✅ This README

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# The Gradle wrapper (gradlew + its jar) is NOT generated — binary
# artifacts are never scaffolded. Create it once with a local Gradle
# install:
gradle wrapper

# Install the quality toolchain (Homebrew)
brew install ktlint detekt

# Install the pre-commit hooks
pre-commit install
```

## Usage

Build the Wear OS Hello World app:

```bash
./gradlew build
```

Run it on a Wear OS emulator or a paired watch via Android Studio
(Run > Run 'app' with a Wear OS device profile selected).

Expected output (in the watch UI):
```
Hello from {self.config.project_name}!
```

## Development

### Building and Testing

```bash
# Build the app
./gradlew build

# Run the JVM unit tests
./gradlew test

# Run every quality gate (format, lint, tests + coverage, security)
./scripts/check-all.sh
```

> **Note:** CI runs these same gates on every push and pull request via
> the generated GitHub Actions pipeline (see *Quality Tools* below). CI
> provisions its own pinned Gradle, so it stays green even before you
> commit a wrapper.

### Quality Tools

This scaffold currently includes:

- **JUnit**: JVM unit-test scaffold (no emulator required)
- **Gradle (Kotlin DSL)**: Dependency management and build tooling
- **ktlint**: Formatting and code-style linting (./scripts/format.sh)
- **detekt**: Static analysis with cyclomatic complexity ≤10 (detekt.yml)
- **Kover**: Coverage gate ≥90% on the debug variant (app/build.gradle.kts)
- **OWASP dependency-check**: Dependency CVE scan (./scripts/security.sh)
- **Pre-commit hooks**: ktlint, detekt, gitleaks, detect-secrets
- **Architecture rules**: Konsist test (plans/architecture/)
- **CI pipeline**: GitHub Actions (.github/workflows/ci.yml) on ubuntu
  runners — quality job (ktlint, detekt, gitleaks, Kover gate), unit
  tests on JDK 17 and 21, Wear OS debug-APK build

### Project Structure

```
{self.config.project_name}/
├── settings.gradle.kts      # Root project + :app module wiring
├── build.gradle.kts         # Plugin versions (AGP, Kotlin, Compose)
├── gradle.properties        # AndroidX opt-in, JVM settings
└── app/
    ├── build.gradle.kts     # Wear OS app module ({namespace})
    └── src/
        ├── main/
        │   ├── AndroidManifest.xml          # wear device profile
        │   └── kotlin/{package_path}/
        │       └── MainActivity.kt          # Compose for Wear OS UI
        └── test/
            └── kotlin/{package_path}/
                └── GreetingTest.kt          # JUnit scaffold
```

### Testing

```bash
# Run all unit tests
./gradlew test

# Run a specific test class
./gradlew test --tests "{namespace}.GreetingTest"
```

### Code Quality

This scaffold is a MAXIMUM QUALITY Kotlin project. Today it provides:

- **Type Safety**: 100% compile-time type checking (inherent to Kotlin)
- **JUnit test scaffold**: ready for you to add tests
- **Coverage gate**: ./scripts/test.sh --coverage enforces ≥90% line
  coverage via Kover (koverVerifyDebug)
- **Complexity gate**: detekt errors on cyclomatic complexity >10
- **Formatting & static analysis**: ktlint and detekt, locally and in
  pre-commit
- **CI enforcement**: every gate above also runs in GitHub Actions on
  every push and pull request

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality Kotlin Wear OS projects from day one.
"""

    def _generate_cpp_readme(self) -> Path:
        """Generate the C/C++ Tizen watch-app README.md (#361).

        Returns:
            Path to generated README.md
        """
        readme_path = self.output_dir / "README.md"
        return self._write_readme(readme_path, self._cpp_readme_content())

    def _cpp_readme_content(self) -> str:
        """Generate C/C++ README.md content.

        Only artifacts the scaffold actually generates carry a checkmark.
        With the #362 quality toolchain (clang-format/clang-tidy/cppcheck,
        pre-commit hooks, quality scripts with the lcov coverage gate,
        lizard complexity, flawfinder, include-boundary architecture
        checker) generated, only the CI pipeline (#363) remains under
        "Planned / coming soon". The Tizen Studio split is documented
        explicitly: unit tests build with plain CMake + Conan, while
        ``.tpk`` packaging needs the Tizen Studio CLI, which cannot be
        generated or installed by the scaffold.

        Returns:
            Content for README.md
        """
        display_name = self.config.project_name.replace("-", " ").title()
        app_id = tizen_app_id(self.config.package_name)
        namespace = cpp_identifier(self.config.package_name)

        return f"""# {self.config.project_name}

{display_name} - A quality-controlled C/C++ Tizen watch-app project generated
with Start Green Stay Green.

## Description

This C/C++ scaffold is the foundation of a quality-controlled Tizen native
(Samsung Galaxy Watch) project. The following are generated today:

- ✅ Tizen native watch-app target (appcore `watch_app` lifecycle + EFL UI,
  `src/main.cpp`)
- ✅ Pure-logic library (`src/greeting.cpp` + `inc/greeting.h`) testable
  without Tizen Studio
- ✅ `tizen-manifest.xml` watch-application manifest (wearable profile,
  app ID `{app_id}`)
- ✅ CMake build (`CMakeLists.txt`, CMake ≥{CMAKE_MINIMUM_VERSION},
  C++{CPP_STANDARD}) and Conan manifest (`conanfile.txt`)
- ✅ Catch2 {CATCH2_VERSION} unit-test scaffold (`tests/test_greeting.cpp`)
- ✅ Code quality tools (clang-format + clang-tidy + cppcheck, configured
  in `.clang-format` / `.clang-tidy`)
- ✅ Pre-commit hooks (format, static analysis, secret scanning via gitleaks)
- ✅ Quality scripts (`./scripts/check-all.sh` with a 90%+ lcov coverage gate)
- ✅ Complexity gate (lizard, cyclomatic complexity ≤10 in `./scripts/lint.sh`)
- ✅ Security scanning (flawfinder via `./scripts/security.sh`)
- ✅ Architecture enforcement (include-boundary checker, `plans/architecture/`)
- ✅ This README

### Planned / coming soon

These quality features are part of the Start Green Stay Green roadmap for
C/C++ but are **not yet generated** by this scaffold — do not assume they
are configured:

- CI/CD pipeline (GitHub Actions)

## The two builds (read this first)

This project deliberately splits into two builds:

1. **Pure logic + unit tests — plain CMake + Conan, no Tizen Studio.**
   `CMakeLists.txt` builds only the `greeting` library and its Catch2
   tests, so the tests run on any host (and any future CI runner).
2. **The watch app itself — Tizen Studio.** `src/main.cpp` needs the
   Tizen native SDK headers (`watch_app.h`, EFL), and the installable
   `.tpk` package is produced by the Tizen Studio CLI
   (`tizen build-native` / `tizen package`). Tizen Studio is **not**
   generated or installed by this scaffold — install it from
   https://developer.tizen.org/development/tizen-studio and import this
   project.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self.config.project_name}

# Install the Conan-managed test dependency (Catch2)
conan install . --output-folder=build --build=missing

# Install the quality toolchain
# macOS (clang-tidy ships in the keg-only llvm formula; add its bin to PATH)
brew install clang-format llvm cppcheck lcov
# Debian/Ubuntu:
# apt-get install clang-format clang-tidy cppcheck lcov
pip install lizard flawfinder

# Install the pre-commit hooks
pre-commit install
```

## Usage

Build the pure-logic library and unit tests (no Tizen Studio needed):

```bash
cmake -B build -S . \\
    -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake \\
    -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

To run the watch app on a Galaxy Watch or the Tizen emulator, import the
project into Tizen Studio and package it there (see *The two builds*).

Expected output (on the watch face):
```
Hello from {self.config.project_name}!
```

## Development

### Building and Testing

```bash
# Configure and build (after `conan install`, see Installation)
cmake --build build

# Run the Catch2 unit tests
ctest --test-dir build

# Run every quality gate (format, lint, tests + coverage, security)
./scripts/check-all.sh
```

> **Note:** The CI/CD pipeline is on the roadmap but not yet generated by
> this scaffold (see *Planned / coming soon* above); run
> `./scripts/check-all.sh` locally until it lands.

### Quality Tools

This scaffold currently includes:

- **Catch2**: Unit-test framework (managed by Conan, runs via CTest)
- **CMake + Conan**: Build system and dependency management
- **clang-format**: Formatting (`.clang-format`, `./scripts/format.sh`)
- **clang-tidy + cppcheck**: Static analysis incl. clang-analyzer security
  checks (`.clang-tidy`, `./scripts/lint.sh`)
- **lizard**: Cyclomatic complexity ≤10 gate (`./scripts/lint.sh`)
- **gcov/lcov**: Coverage gate ≥90% (`./scripts/test.sh --coverage`;
  instrumentation via the `ENABLE_COVERAGE` CMake option)
- **flawfinder**: CWE-mapped dangerous-API scan (`./scripts/security.sh`)
- **Pre-commit hooks**: clang-format, clang-tidy, cppcheck, gitleaks,
  detect-secrets
- **Architecture rules**: include-boundary checker (`plans/architecture/`)

### Project Structure

```
{self.config.project_name}/
├── CMakeLists.txt           # Pure-logic library + Catch2 tests
├── conanfile.txt            # Conan 2 manifest (Catch2)
├── tizen-manifest.xml       # Watch application manifest ({app_id})
├── inc/
│   └── greeting.h           # Pure-logic header (namespace {namespace})
├── src/
│   ├── greeting.cpp         # Pure logic: format_greeting()
│   └── main.cpp             # Tizen watch_app + EFL entry (Tizen Studio)
├── res/                     # Private resources (see res/README.md)
├── shared/res/              # Launcher icon goes here (see README note)
└── tests/
    └── test_greeting.cpp    # Catch2 scaffold
```

### Testing

```bash
# Run all unit tests
ctest --test-dir build

# Run the test binary directly with Catch2's CLI
./build/greeting_tests "[greeting]"
```

### Code Quality

This scaffold is a MAXIMUM QUALITY C/C++ project. Today it provides:

- **C++{CPP_STANDARD} with strict standard conformance**: \
`CMAKE_CXX_STANDARD_REQUIRED ON`, extensions off
- **Catch2 test scaffold**: ready for you to add tests
- **Coverage gate**: `./scripts/test.sh --coverage` enforces ≥90% line
  coverage via gcov/lcov (only the host-built pure-logic sources count;
  `src/main.cpp` needs the Tizen SDK and sits outside the host build,
  so it is honestly outside the coverage denominator too)
- **Complexity gate**: lizard fails on cyclomatic complexity >10
- **Formatting & static analysis**: clang-format, clang-tidy, and
  cppcheck, locally and in pre-commit

CI enforcement of these gates is planned (see *Planned / coming soon*
above) and is not yet wired into this scaffold.

## License

MIT License

## Attribution

Generated with [Start Green Stay Green](https://github.com/Geoffe-Ga/start_green_stay_green)
- Maximum quality C/C++ Tizen watch projects from day one.
"""
