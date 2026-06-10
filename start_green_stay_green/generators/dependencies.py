"""Dependencies file generator.

Generates dependency files for target projects (requirements.txt, requirements-dev.txt,
pyproject.toml) with appropriate dependencies and tool configurations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import validate_language
from start_green_stay_green.utils.kotlin import ACTIVITY_COMPOSE_VERSION
from start_green_stay_green.utils.kotlin import AGP_VERSION
from start_green_stay_green.utils.kotlin import COMPOSE_BOM_VERSION
from start_green_stay_green.utils.kotlin import GRADLE_WRAPPER_VERSION
from start_green_stay_green.utils.kotlin import JUNIT_VERSION
from start_green_stay_green.utils.kotlin import KOTLIN_VERSION
from start_green_stay_green.utils.kotlin import WEAR_COMPOSE_VERSION
from start_green_stay_green.utils.kotlin import android_package
from start_green_stay_green.utils.swift import package_swift

if TYPE_CHECKING:
    from start_green_stay_green.utils.file_writer import FileWriter


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

    All 9 supported languages (python, typescript, go, rust, java, csharp,
    ruby, swift, kotlin) are available at the generator level. Note that the
    full CLI pipeline (``sgsg init``) skips its quality-tooling steps
    (pre-commit, scripts, CI, architecture, metrics) for java, csharp, ruby,
    and kotlin; Kotlin's tooling arrives with #357/#358.

    Attributes:
        output_dir: Directory where dependency files will be written
        config: Configuration for dependency file generation
    """

    def __init__(
        self,
        output_dir: Path,
        config: DependencyConfig,
        *,
        file_writer: FileWriter | None = None,
    ) -> None:
        """Initialize the Dependencies Generator.

        Args:
            output_dir: Directory where dependency files will be created
            config: DependencyConfig with project settings
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

    def generate(self) -> dict[str, Any]:
        """Generate all dependency files.

        Returns:
            Dictionary mapping file names to their generated file paths

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """
        # Validate language is supported
        validate_language(self.config.language)

        # Dispatch to language-specific generator
        generators = {
            "python": self._generate_python_dependencies,
            "typescript": self._generate_typescript_dependencies,
            "go": self._generate_go_dependencies,
            "rust": self._generate_rust_dependencies,
            "java": self._generate_java_dependencies,
            "csharp": self._generate_csharp_dependencies,
            "ruby": self._generate_ruby_dependencies,
            "swift": self._generate_swift_dependencies,
            "kotlin": self._generate_kotlin_dependencies,
        }
        return generators[self.config.language]()

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

        If a FileWriter is configured, delegates to it for existence checking.
        Otherwise, writes directly (original behavior).

        Args:
            filename: Name of the file to write
            content: Content to write to the file

        Returns:
            Path to the written file

        Raises:
            GenerationError: If file cannot be written
        """
        file_path = self.output_dir / filename

        if self._file_writer is not None:
            self._file_writer.write_file(file_path, content)
            return file_path

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
pip-audit>=2.7.0

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
    "pip-audit>=2.7.0",
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
exclude_lines = [
    "if __name__ == .__main__.",
    "pragma: no cover",
]

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

    def _generate_typescript_dependencies(self) -> dict[str, Path]:
        """Generate TypeScript dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate package.json with dependencies and scripts
        files["package.json"] = self._write_file(
            "package.json",
            self._typescript_package_json(),
        )

        return files

    def _typescript_package_json(self) -> str:
        """Generate TypeScript package.json content.

        Returns:
            Content for package.json with dependencies and scripts
        """
        return f"""{{
  "name": "{self.config.project_name}",
  "version": "0.1.0",
  "description": "A quality-controlled TypeScript project",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {{
    "build": "tsc",
    "test": "jest",
    "test:coverage": "jest --coverage",
    "lint": "eslint . --ext .ts",
    "format": "prettier --write .",
    "format:check": "prettier --check .",
    "type-check": "tsc --noEmit"
  }},
  "keywords": [],
  "author": "Generated by SGSG",
  "license": "MIT",
  "devDependencies": {{
    "@types/jest": "^29.5.0",
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.50.0",
    "jest": "^29.7.0",
    "prettier": "^3.0.0",
    "ts-jest": "^29.1.0",
    "typescript": "^5.2.0"
  }},
  "dependencies": {{}}
}}
"""

    def _generate_go_dependencies(self) -> dict[str, Path]:
        """Generate Go dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate go.mod with module name
        files["go.mod"] = self._write_file(
            "go.mod",
            self._go_mod(),
        )

        return files

    def _go_mod(self) -> str:
        """Generate Go go.mod content.

        Returns:
            Content for go.mod with module name and Go version
        """
        return f"""module github.com/user/{self.config.project_name}

go 1.21

require (
)
"""

    def _generate_rust_dependencies(self) -> dict[str, Path]:
        """Generate Rust dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate Cargo.toml with package info
        files["Cargo.toml"] = self._write_file(
            "Cargo.toml",
            self._rust_cargo_toml(),
        )

        return files

    def _rust_cargo_toml(self) -> str:
        """Generate Rust Cargo.toml content.

        Returns:
            Content for Cargo.toml with package info and dependencies
        """
        return f"""[package]
name = "{self.config.package_name}"
version = "0.1.0"
edition = "2021"
authors = ["Generated by SGSG"]
license = "MIT"
description = "A quality-controlled Rust project"

[dependencies]

[dev-dependencies]
# Add test dependencies here

[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
"""

    def _generate_java_dependencies(self) -> dict[str, Path]:
        """Generate Java dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate pom.xml for Maven projects
        files["pom.xml"] = self._write_file(
            "pom.xml",
            self._java_pom_xml(),
        )

        return files

    def _java_pom_xml(self) -> str:
        """Generate Java pom.xml content.

        Returns:
            Content for pom.xml with project info and dependencies
        """
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>{self.config.project_name}</artifactId>
    <version>0.1.0</version>
    <packaging>jar</packaging>

    <name>{self.config.project_name}</name>
    <description>A quality-controlled Java project</description>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <junit.version>5.10.0</junit.version>
    </properties>

    <dependencies>
        <!-- Test dependencies -->
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${{junit.version}}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
            </plugin>
        </plugins>
    </build>
</project>
"""

    def _generate_csharp_dependencies(self) -> dict[str, Path]:
        """Generate C# dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate .csproj file
        csproj_filename = f"{self.config.project_name}.csproj"
        files[csproj_filename] = self._write_file(
            csproj_filename,
            self._csharp_csproj(),
        )

        return files

    def _csharp_csproj(self) -> str:
        """Generate C# .csproj content.

        Returns:
            Content for .csproj with project settings and dependencies
        """
        return """<Project Sdk="Microsoft.NET.Sdk">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.6.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.3">
      <IncludeAssets>runtime; build; native; contentfiles; analyzers</IncludeAssets>
      <PrivateAssets>all</PrivateAssets>
    </PackageReference>
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.8.0" />
  </ItemGroup>

</Project>
"""

    def _generate_ruby_dependencies(self) -> dict[str, Path]:
        """Generate Ruby dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate Gemfile
        files["Gemfile"] = self._write_file(
            "Gemfile",
            self._ruby_gemfile(),
        )

        return files

    def _ruby_gemfile(self) -> str:
        """Generate Ruby Gemfile content.

        Returns:
            Content for Gemfile with gem dependencies
        """
        return """# frozen_string_literal: true

source "https://rubygems.org"

# Specify your gem's dependencies in gemspec if building a gem
# gemspec

group :development, :test do
  gem "rspec", "~> 3.12"
  gem "rubocop", "~> 1.57"
  gem "simplecov", "~> 0.22"
end
"""

    def _generate_swift_dependencies(self) -> dict[str, Path]:
        """Generate Swift dependency files.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        # Generate the Swift Package Manager manifest
        files["Package.swift"] = self._write_file(
            "Package.swift",
            self._swift_package_swift(),
        )

        return files

    def _swift_package_swift(self) -> str:
        """Generate the Swift Package Manager manifest for watchOS.

        Delegates to the shared :func:`~start_green_stay_green.utils.swift.\
package_swift` helper so the structure and dependency generators emit an
        identical manifest from one source of truth.

        Returns:
            Content for ``Package.swift`` declaring a watchOS app target
        """
        return package_swift(self.config.package_name)

    def _generate_kotlin_dependencies(self) -> dict[str, Path]:
        """Generate the Gradle (Kotlin DSL) manifests for Wear OS (#356).

        Emits ``settings.gradle.kts``, the root ``build.gradle.kts``,
        ``gradle.properties``, and the ``app`` module's
        ``build.gradle.kts`` with Jetpack Compose for Wear OS
        dependencies. The Gradle wrapper (``gradlew`` and its jar) is
        deliberately NOT generated — it is a binary artifact; the
        settings file and README direct users to run ``gradle wrapper``
        once instead.

        Returns:
            Dictionary mapping file names to file paths
        """
        files: dict[str, Path] = {}

        files["settings.gradle.kts"] = self._write_file(
            "settings.gradle.kts",
            self._kotlin_settings_gradle_kts(),
        )
        files["build.gradle.kts"] = self._write_file(
            "build.gradle.kts",
            self._kotlin_root_build_gradle_kts(),
        )
        files["gradle.properties"] = self._write_file(
            "gradle.properties",
            self._kotlin_gradle_properties(),
        )

        # The app module's manifest lives under app/.
        (self.output_dir / "app").mkdir(parents=True, exist_ok=True)
        files["app/build.gradle.kts"] = self._write_file(
            "app/build.gradle.kts",
            self._kotlin_app_build_gradle_kts(),
        )

        return files

    def _kotlin_settings_gradle_kts(self) -> str:
        """Generate ``settings.gradle.kts`` for the Wear OS project.

        Returns:
            Settings script declaring plugin/dependency repositories, the
            root project name, and the ``:app`` module. Includes an honest
            note that the Gradle wrapper binary is not generated.
        """
        project = self.config.project_name
        return f"""// Gradle (Kotlin DSL) settings for the {project} Wear OS project.
//
// NOTE: the Gradle wrapper (gradlew, gradle/wrapper/gradle-wrapper.jar)
// is NOT generated — binary artifacts do not belong in a generator.
// With a local Gradle install, create it once via:
//   gradle wrapper --gradle-version {GRADLE_WRAPPER_VERSION}
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}

dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}

rootProject.name = "{self.config.project_name}"
include(":app")
"""

    def _kotlin_root_build_gradle_kts(self) -> str:
        """Generate the root ``build.gradle.kts``.

        Returns:
            Root build script pinning the Android Gradle Plugin, the
            Kotlin Android plugin, and the Compose compiler plugin (which
            must match the Kotlin version) for all modules.
        """
        return f"""// Root Gradle build: pins plugin versions for all modules.
// The Compose compiler plugin version must match the Kotlin version.
plugins {{
    id("com.android.application") version "{AGP_VERSION}" apply false
    id("org.jetbrains.kotlin.android") version "{KOTLIN_VERSION}" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "{KOTLIN_VERSION}" apply false
}}
"""

    def _kotlin_gradle_properties(self) -> str:
        """Generate ``gradle.properties``.

        Returns:
            Project-wide Gradle settings: AndroidX opt-in (required by
            Compose), JVM memory, and the official Kotlin code style.
        """
        return """# Project-wide Gradle settings for the Wear OS app.
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
# AndroidX is required by Jetpack Compose.
android.useAndroidX=true
kotlin.code.style=official
"""

    def _kotlin_app_build_gradle_kts(self) -> str:
        """Generate the ``app`` module's ``build.gradle.kts``.

        Returns:
            Android application module configured for Wear OS: minSdk 30
            (Wear OS 3, the Galaxy Watch 4+ baseline), Compose enabled,
            Jetpack Compose for Wear OS dependencies, and a JUnit
            ``testImplementation`` so ``./gradlew test`` runs the
            generated unit-test scaffold.
        """
        namespace = android_package(self.config.package_name)
        return f"""// Android application module for the Wear OS app.
plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}}

android {{
    namespace = "{namespace}"
    compileSdk = 35

    defaultConfig {{
        applicationId = "{namespace}"
        // Wear OS 3 (Galaxy Watch 4+) baseline.
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }}

    buildFeatures {{
        compose = true
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
}}

kotlin {{
    jvmToolchain(17)
}}

dependencies {{
    implementation(platform("androidx.compose:compose-bom:{COMPOSE_BOM_VERSION}"))
    implementation("androidx.activity:activity-compose:{ACTIVITY_COMPOSE_VERSION}")

    // Jetpack Compose for Wear OS (androidx.wear.compose).
    implementation("androidx.wear.compose:compose-material:{WEAR_COMPOSE_VERSION}")
    implementation("androidx.wear.compose:compose-foundation:{WEAR_COMPOSE_VERSION}")

    // JUnit scaffold for the unit tests (run: ./gradlew test).
    testImplementation("junit:junit:{JUNIT_VERSION}")
}}
"""
