"""Unit tests for Dependencies Generator."""

from pathlib import Path
import tempfile
import tomllib

import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.utils.kotlin import AGP_VERSION
from start_green_stay_green.utils.kotlin import JUNIT_VERSION
from start_green_stay_green.utils.kotlin import KOTLIN_VERSION
from start_green_stay_green.utils.kotlin import android_package
from start_green_stay_green.utils.swift import package_swift

# Expected primary dependency file per language
EXPECTED_DEP_FILES: dict[str, list[str]] = {
    "python": ["requirements.txt", "requirements-dev.txt", "pyproject.toml"],
    "typescript": ["package.json"],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml"],
    "csharp": ["test-project.csproj"],
    "ruby": ["Gemfile"],
    "swift": ["Package.swift"],
    "kotlin": [
        "settings.gradle.kts",
        "build.gradle.kts",
        "gradle.properties",
        "app/build.gradle.kts",
    ],
}


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


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="brainfuck",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)

            with pytest.raises(ValueError, match="Unsupported language"):
                generator.generate()


class TestMultiLanguageDependencies:
    """Test dependency generation for all supported languages."""

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_dependency_file(self, lang: str) -> None:
        """Test generate creates dependency files for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert files, f"No files generated for {lang}"
            for key, path in files.items():
                assert path.exists(), f"File {key} missing for {lang}"

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_expected_files(self, lang: str) -> None:
        """Test generate creates the expected dependency files for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            expected = EXPECTED_DEP_FILES[lang]
            for expected_file in expected:
                assert (
                    expected_file in files
                ), f"Expected {expected_file} for {lang}, got {list(files.keys())}"

    def test_typescript_package_json_has_dev_dependencies(self) -> None:
        """Test TypeScript package.json includes devDependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["package.json"].read_text()
            assert "devDependencies" in content
            assert "typescript" in content

    def test_go_mod_has_module_name(self) -> None:
        """Test Go go.mod contains module declaration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="go",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["go.mod"].read_text()
            assert "module" in content

    def test_rust_cargo_toml_has_package(self) -> None:
        """Test Rust Cargo.toml contains [package] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="rust",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["Cargo.toml"].read_text()
            assert "[package]" in content

    def test_java_pom_xml_has_project(self) -> None:
        """Test Java pom.xml contains project element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="java",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["pom.xml"].read_text()
            assert "<project" in content
            assert "junit" in content.lower() or "test" in content.lower()

    def test_csharp_csproj_has_project(self) -> None:
        """Test C# .csproj contains Project element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="csharp",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "test-project.csproj" in files
            content = files["test-project.csproj"].read_text()
            assert "<Project" in content

    def test_ruby_gemfile_has_source(self) -> None:
        """Test Ruby Gemfile contains source declaration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="ruby",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["Gemfile"].read_text()
            assert "source" in content

    def test_swift_package_swift_has_manifest(self) -> None:
        """Test Swift Package.swift contains an SPM manifest for watchOS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "Package.swift" in files
            content = files["Package.swift"].read_text()
            assert "swift-tools-version" in content
            assert "import PackageDescription" in content
            assert "Package(" in content
            assert ".watchOS" in content

    def test_swift_package_swift_has_no_library_product(self) -> None:
        """A watchOS app target is not a library, so no products block is emitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["Package.swift"].read_text()
            assert ".library" not in content
            assert "products:" not in content

    def test_swift_package_swift_uses_shared_helper(self) -> None:
        """Dependencies generator delegates manifest rendering to the shared helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["Package.swift"].read_text()
            assert content == package_swift("test_project")


class TestKotlinDependencies:
    """Test Kotlin Gradle (Kotlin DSL) manifest generation (#356)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Run the dependencies generator for a kotlin test project.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            Mapping of generated relative keys to file paths.
        """
        config = DependencyConfig(
            project_name="test-project",
            language="kotlin",
            package_name="test_project",
        )
        return DependenciesGenerator(Path(tmpdir), config).generate()

    def test_settings_includes_app_module_and_repositories(self) -> None:
        """settings.gradle.kts names the root project and includes :app."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["settings.gradle.kts"].read_text()
            assert 'rootProject.name = "test-project"' in content
            assert 'include(":app")' in content
            assert "google()" in content
            assert "mavenCentral()" in content

    def test_settings_documents_missing_gradle_wrapper(self) -> None:
        """The wrapper jar is a binary and is not generated; that is disclosed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["settings.gradle.kts"].read_text()
            assert "gradle wrapper" in content
            assert "not generated" in content.lower()

    def test_root_build_declares_plugin_versions(self) -> None:
        """The root build pins AGP, Kotlin, and the Compose compiler plugin."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["build.gradle.kts"].read_text()
            assert f'id("com.android.application") version "{AGP_VERSION}"' in content
            assert (
                f'id("org.jetbrains.kotlin.android") version "{KOTLIN_VERSION}"'
                in content
            )
            assert (
                'id("org.jetbrains.kotlin.plugin.compose") '
                f'version "{KOTLIN_VERSION}"' in content
            )
            assert "apply false" in content

    def test_app_module_targets_wear_os(self) -> None:
        """The app module declares Wear Compose dependencies and SDK levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            assert "androidx.wear.compose:compose-material" in content
            assert "androidx.wear.compose:compose-foundation" in content
            assert "minSdk = 30" in content

    def test_app_module_uses_shared_android_namespace(self) -> None:
        """The namespace/applicationId come from the shared kotlin helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            namespace = android_package("test_project")
            assert f'namespace = "{namespace}"' in content
            assert f'applicationId = "{namespace}"' in content

    def test_app_module_includes_junit_test_scaffold_dependency(self) -> None:
        """JUnit is wired so ./gradlew test runs the generated unit test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            assert f'testImplementation("junit:junit:{JUNIT_VERSION}")' in content

    def test_gradle_properties_enables_androidx(self) -> None:
        """gradle.properties opts into AndroidX (required by Compose)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["gradle.properties"].read_text()
            assert "android.useAndroidX=true" in content

    def test_no_gradle_wrapper_binaries_are_generated(self) -> None:
        """gradlew / wrapper jars are binaries and must not be scaffolded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            assert "gradlew" not in files
            assert "gradlew.bat" not in files
            assert not (Path(tmpdir) / "gradlew").exists()
            assert not (Path(tmpdir) / "gradle" / "wrapper").exists()
