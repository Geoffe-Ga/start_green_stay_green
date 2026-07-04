"""Unit tests for Dependencies Generator."""

import json
from pathlib import Path
import tempfile
import tomllib

from defusedxml import ElementTree as DefusedElementTree
import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.dependencies import DependenciesGenerator
from start_green_stay_green.generators.dependencies import DependencyConfig
from start_green_stay_green.utils.cpp import CATCH2_VERSION
from start_green_stay_green.utils.cpp import CMAKE_MINIMUM_VERSION
from start_green_stay_green.utils.cpp import CPP_STANDARD
from start_green_stay_green.utils.csharp import COVERLET_MSBUILD_VERSION
from start_green_stay_green.utils.csharp import NETARCHTEST_RULES_VERSION
from start_green_stay_green.utils.csharp import SECURITY_CODE_SCAN_VERSION
from start_green_stay_green.utils.csharp import TEST_SDK_VERSION
from start_green_stay_green.utils.csharp import XUNIT_RUNNER_VERSION
from start_green_stay_green.utils.csharp import XUNIT_VERSION
from start_green_stay_green.utils.java import ARCHUNIT_VERSION
from start_green_stay_green.utils.java import CHECKSTYLE_PLUGIN_VERSION
from start_green_stay_green.utils.java import DEPENDENCY_CHECK_PLUGIN_VERSION
from start_green_stay_green.utils.java import JACOCO_VERSION
from start_green_stay_green.utils.java import JAVA_RELEASE
from start_green_stay_green.utils.java import JUNIT4_VERSION
from start_green_stay_green.utils.java import PMD_PLUGIN_VERSION
from start_green_stay_green.utils.java import SPOTBUGS_PLUGIN_VERSION
from start_green_stay_green.utils.java import SUREFIRE_VERSION
from start_green_stay_green.utils.java import android_package
from start_green_stay_green.utils.kotlin import AGP_VERSION
from start_green_stay_green.utils.kotlin import JUNIT_VERSION
from start_green_stay_green.utils.kotlin import KONSIST_VERSION
from start_green_stay_green.utils.kotlin import KOTLIN_VERSION
from start_green_stay_green.utils.kotlin import KOVER_VERSION
from start_green_stay_green.utils.ruby import BUNDLER_AUDIT_VERSION
from start_green_stay_green.utils.ruby import PACKWERK_VERSION
from start_green_stay_green.utils.ruby import RSPEC_VERSION
from start_green_stay_green.utils.ruby import RUBOCOP_VERSION
from start_green_stay_green.utils.ruby import SIMPLECOV_VERSION
from start_green_stay_green.utils.ruby import ruby_gemfile
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
    "cpp": ["CMakeLists.txt", "conanfile.txt"],
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

    def test_typescript_package_json_includes_stryker_dev_dependencies(self) -> None:
        """package.json carries StrykerJS so `npm ci` makes the mutation
        gate runnable (parity with mutmut in requirements-dev.txt, #398).

        Versions live-verified on the npm registry 2026-06-11
        (@stryker-mutator/core latest 9.6.1).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            parsed = json.loads(files["package.json"].read_text())
            dev_deps = parsed["devDependencies"]
            assert dev_deps["@stryker-mutator/core"] == "^9.6.0"
            assert dev_deps["@stryker-mutator/jest-runner"] == "^9.6.0"

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
            assert "junit" in content.lower()

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

    def test_ruby_gemfile_pins_quality_toolchain(self) -> None:
        """The Gemfile wires the #373 quality gems with live pins.

        rspec/simplecov/rubocop/bundler-audit/packwerk back the test,
        coverage, lint/complexity, dependency-CVE, and architecture
        gates; the pessimistic pins come from utils.ruby (verified
        against rubygems.org).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="ruby",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["Gemfile"].read_text()
            assert f'gem "rspec", "~> {RSPEC_VERSION}"' in content
            assert f'gem "simplecov", "~> {SIMPLECOV_VERSION}"' in content
            assert f'gem "rubocop", "~> {RUBOCOP_VERSION}"' in content
            assert f'gem "bundler-audit", "~> {BUNDLER_AUDIT_VERSION}"' in content
            assert f'gem "packwerk", "~> {PACKWERK_VERSION}"' in content

    def test_ruby_gemfile_matches_structure_generator(self) -> None:
        """The dependencies and structure generators emit one Gemfile.

        Both delegate to utils.ruby.ruby_gemfile (#373) so the two can
        never drift apart again (before #373 they emitted diverging
        manifests with stale tool lines).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DependencyConfig(
                project_name="test-project",
                language="ruby",
                package_name="test_project",
            )
            generator = DependenciesGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert files["Gemfile"].read_text() == ruby_gemfile()

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

    def test_root_build_pins_kover_plugin(self) -> None:
        """The root build pins the Kover coverage plugin version (#357)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["build.gradle.kts"].read_text()
            assert (
                f'id("org.jetbrains.kotlinx.kover") version "{KOVER_VERSION}" '
                "apply false" in content
            )

    def test_app_module_applies_kover_plugin(self) -> None:
        """The app module applies Kover so coverage tasks exist (#357)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            assert 'id("org.jetbrains.kotlinx.kover")' in content

    def test_app_module_gates_debug_coverage_at_90_percent(self) -> None:
        """Kover verifies >=90% coverage on the debug variant (#357).

        scripts/test.sh --coverage runs ./gradlew koverVerifyDebug, so
        the bound must live here in the manifest as the single source
        of truth.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            assert 'variant("debug")' in content
            assert "minBound(90)" in content

    def test_app_module_includes_konsist_test_dependency(self) -> None:
        """Konsist is wired so the architecture test compiles (#357).

        plans/architecture/ArchitectureTest.kt is a Konsist JUnit test;
        once copied into app/src/test/kotlin it must build without any
        further dependency edits.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["app/build.gradle.kts"].read_text()
            assert (
                f'testImplementation("com.lemonappdev:konsist:{KONSIST_VERSION}")'
                in content
            )


class TestJavaDependencies:
    """Test the Java Maven (pure-logic) manifest generation (#366)."""

    @staticmethod
    def _pom(tmpdir: str) -> str:
        """Generate the java dependency files and return the pom content.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            The generated ``pom.xml`` content.
        """
        config = DependencyConfig(
            project_name="wrist-timer",
            language="java",
            package_name="wrist_timer",
        )
        files = DependenciesGenerator(Path(tmpdir), config).generate()
        pom_path: Path = files["pom.xml"]
        return pom_path.read_text()

    def test_pom_is_well_formed_xml_with_maven_namespace(self) -> None:
        """pom.xml parses as XML rooted at the Maven project element."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = DefusedElementTree.fromstring(self._pom(tmpdir))
            assert root.tag == "{http://maven.apache.org/POM/4.0.0}project"

    def test_pom_names_project_under_com_example(self) -> None:
        """The artifact is the project name under the com.example group."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<groupId>com.example</groupId>" in content
            assert "<artifactId>wrist-timer</artifactId>" in content

    def test_pom_targets_pinned_java_release(self) -> None:
        """The compiler release matches the pinned Java version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            release = f"<maven.compiler.release>{JAVA_RELEASE}"
            assert f"{release}</maven.compiler.release>" in content

    def test_pom_manages_junit4_test_dependency(self) -> None:
        """JUnit 4 (the Android-ecosystem convention) is test-scoped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<artifactId>junit</artifactId>" in content
            assert f"<version>{JUNIT4_VERSION}</version>" in content
            assert "<scope>test</scope>" in content
            # The old JUnit 5 (jupiter) manifest is gone.
            assert "jupiter" not in content

    def test_pom_wires_surefire_and_compiler_plugins(self) -> None:
        """Surefire (mvn test) and the compiler plugin are pinned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<artifactId>maven-surefire-plugin</artifactId>" in content
            assert f"<version>{SUREFIRE_VERSION}</version>" in content

    def test_pom_carries_the_jacoco_coverage_gate(self) -> None:
        """The JaCoCo plugin enforces the >=90% line-coverage bound.

        The rules live at plugin level so the CI's standalone
        ``mvn jacoco:check`` invocation (reference/ci/java.yml) applies
        them too, not just the lifecycle-bound check execution.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<artifactId>jacoco-maven-plugin</artifactId>" in content
            assert f"<version>{JACOCO_VERSION}</version>" in content
            assert "<goal>prepare-agent</goal>" in content
            assert "<minimum>0.90</minimum>" in content

    def test_pom_declares_every_ci_quality_plugin(self) -> None:
        """Checkstyle, PMD, and SpotBugs back the CI's mvn goals.

        reference/ci/java.yml runs checkstyle:check, pmd:check, and
        spotbugs:check; the spotbugs prefix only resolves when the
        plugin is declared in the pom.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<artifactId>maven-checkstyle-plugin</artifactId>" in content
            assert f"<version>{CHECKSTYLE_PLUGIN_VERSION}</version>" in content
            assert "<configLocation>google_checks.xml</configLocation>" in content
            assert "<artifactId>maven-pmd-plugin</artifactId>" in content
            assert f"<version>{PMD_PLUGIN_VERSION}</version>" in content
            assert "<artifactId>spotbugs-maven-plugin</artifactId>" in content
            assert f"<version>{SPOTBUGS_PLUGIN_VERSION}</version>" in content

    def test_pom_documents_two_builds_split(self) -> None:
        """The pom discloses that the APK build is Android tooling's job."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "THE TWO BUILDS" in content
            assert "Android Studio" in content
            assert "android-maven-plugin is unmaintained" in content

    def test_pom_manages_archunit_test_dependency(self) -> None:
        """ArchUnit is test-scoped so the architecture test compiles (#367).

        The #357 manifest-touch precedent: the architecture template in
        plans/architecture only compiles once copied into src/test/java,
        and that copy needs the archunit dependency already declared.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<groupId>com.tngtech.archunit</groupId>" in content
            assert "<artifactId>archunit</artifactId>" in content
            assert f"<version>{ARCHUNIT_VERSION}</version>" in content

    def test_pom_pmd_plugin_layers_the_ccn_companion_ruleset(self) -> None:
        """The PMD plugin layers quickstart baseline + pmd-ruleset.xml.

        The companion ruleset (written by the scripts generator) is the
        single home of the <=10 cyclomatic-complexity bound; the PMD 7
        ``category/java/quickstart.xml`` baseline is referenced
        explicitly (pre-7 ``rulesets/java/*`` paths no longer resolve)
        so adding the companion does not silently drop stock analysis.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<ruleset>category/java/quickstart.xml</ruleset>" in content
            assert "<ruleset>pmd-ruleset.xml</ruleset>" in content

    def test_pom_declares_owasp_dependency_check_plugin(self) -> None:
        """dependency-check-maven is pinned with the CVSS>=7 failure gate.

        Declared in the pom (rather than a brew-installed CLI) so
        ``mvn dependency-check:check`` resolves with zero extra installs
        — the org.owasp group is not in Maven's default plugin-prefix
        search path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._pom(tmpdir)
            assert "<groupId>org.owasp</groupId>" in content
            assert "<artifactId>dependency-check-maven</artifactId>" in content
            assert f"<version>{DEPENDENCY_CHECK_PLUGIN_VERSION}</version>" in content
            assert "<failBuildOnCVSS>7</failBuildOnCVSS>" in content


class TestCsharpDependencies:
    """Test the C# .csproj manifest generation (#370)."""

    @staticmethod
    def _csproj(tmpdir: str) -> str:
        """Generate the csharp dependency files and return the csproj.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            The generated ``.csproj`` content.
        """
        config = DependencyConfig(
            project_name="wrist-ledger",
            language="csharp",
            package_name="wrist_ledger",
        )
        files = DependenciesGenerator(Path(tmpdir), config).generate()
        csproj_path: Path = files["wrist-ledger.csproj"]
        return csproj_path.read_text()

    def test_csproj_is_well_formed_xml_with_sdk_attribute(self) -> None:
        """The csproj parses as XML rooted at an SDK-style Project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = DefusedElementTree.fromstring(self._csproj(tmpdir))
            assert root.tag == "Project"
            assert root.get("Sdk") == "Microsoft.NET.Sdk"

    def test_csproj_pins_the_xunit_test_stack(self) -> None:
        """xUnit, its VS runner, and the test SDK are pinned from utils."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert f'Include="xunit" Version="{XUNIT_VERSION}"' in content
            assert (
                f'Include="xunit.runner.visualstudio" Version="{XUNIT_RUNNER_VERSION}"'
                in content
            )
            assert (
                f'Include="Microsoft.NET.Test.Sdk" Version="{TEST_SDK_VERSION}"'
                in content
            )

    def test_csproj_carries_the_coverlet_coverage_gate(self) -> None:
        """coverlet.msbuild is pinned and the >=90% bound lives here.

        The csproj is the single home of the coverage threshold (the
        Kover/JaCoCo manifest-owned precedent): scripts/test.sh and CI
        only pass ``/p:CollectCoverage=true`` and never restate the
        number. coverlet.msbuild hooks the dotnet test task itself, so
        the gate fails the test invocation directly — there is no
        standalone-goal/empty-report no-op path to guard against.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert (
                f'Include="coverlet.msbuild" Version="{COVERLET_MSBUILD_VERSION}"'
                in content
            )
            assert "<Threshold>90</Threshold>" in content
            assert "<ThresholdType>line</ThresholdType>" in content
            assert "<ThresholdStat>total</ThresholdStat>" in content

    def test_csproj_enables_roslyn_analyzers_as_errors(self) -> None:
        """The Roslyn analyzer gate is build-borne and warnings fail it.

        ``EnableNETAnalyzers``/``AnalysisLevel`` turn the SDK analyzers
        on and ``TreatWarningsAsErrors`` makes every ``dotnet build``
        (pre-commit hook, lint.sh, CI) a failing lint gate — the csproj
        is the single home of that policy.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert "<EnableNETAnalyzers>true</EnableNETAnalyzers>" in content
            assert "<AnalysisLevel>latest</AnalysisLevel>" in content
            assert "<TreatWarningsAsErrors>true</TreatWarningsAsErrors>" in content

    def test_csproj_declares_the_code_metrics_config(self) -> None:
        """CodeMetricsConfig.txt is wired as an AdditionalFiles item.

        The .NET SDK's CA1502 complexity rule reads its threshold from
        an AdditionalFiles entry named exactly CodeMetricsConfig.txt
        (written by the scripts generator — the pmd-ruleset.xml split);
        without this item the <=10 gate would silently use the default
        threshold of 25.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert '<AdditionalFiles Include="CodeMetricsConfig.txt" />' in content
            # The numeric bound must NOT be duplicated here; its single
            # home is CodeMetricsConfig.txt itself.
            assert "CA1502: 10" not in content

    def test_csproj_pins_netarchtest_for_the_architecture_template(self) -> None:
        """NetArchTest.Rules backs plans/architecture/ArchitectureTest.cs.

        Declared in the manifest (the ArchUnit/Konsist precedent) so the
        parked template compiles as soon as it is copied into tests/.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert (
                f'Include="NetArchTest.Rules" Version="{NETARCHTEST_RULES_VERSION}"'
                in content
            )

    def test_csproj_pins_security_code_scan_analyzer(self) -> None:
        """SecurityCodeScan runs as a Roslyn analyzer in every build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            expected = (
                'Include="SecurityCodeScan.VS2019" '
                f'Version="{SECURITY_CODE_SCAN_VERSION}"'
            )
            assert expected in content

    def test_csproj_documents_the_single_project_design(self) -> None:
        """The csproj discloses that src/ and tests/ share one assembly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._csproj(tmpdir)
            assert "Single-project layout" in content
            assert "tests/" in content


class TestCppDependencies:
    """Test C/C++ CMake + Conan manifest generation (#361/#362)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Run the dependencies generator for a cpp test project.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            Mapping of generated relative keys to file paths.
        """
        config = DependencyConfig(
            project_name="test-project",
            language="cpp",
            package_name="test_project",
        )
        return DependenciesGenerator(Path(tmpdir), config).generate()

    def test_cmakelists_pins_minimum_version_and_standard(self) -> None:
        """CMakeLists.txt pins the shared CMake minimum and C++ standard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert f"cmake_minimum_required(VERSION {CMAKE_MINIMUM_VERSION})" in content
            assert f"set(CMAKE_CXX_STANDARD {CPP_STANDARD})" in content
            assert "set(CMAKE_CXX_STANDARD_REQUIRED ON)" in content

    def test_cmakelists_builds_library_and_catch2_test_target(self) -> None:
        """The build covers the pure-logic library plus the Catch2 tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert "add_library(greeting src/greeting.cpp)" in content
            assert "find_package(Catch2 3 REQUIRED)" in content
            assert "Catch2::Catch2WithMain" in content
            assert "catch_discover_tests(greeting_tests)" in content

    def test_cmakelists_uses_sanitized_project_identifier(self) -> None:
        """The CMake project name comes from the shared cpp helper."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert "project(test_project VERSION 0.1.0 LANGUAGES CXX)" in content

    def test_cmakelists_excludes_tizen_entry_point(self) -> None:
        """src/main.cpp (Tizen Studio's job) is not in the CMake build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert "src/main.cpp" not in [
                line.strip()
                for line in content.splitlines()
                if not line.lstrip().startswith("#")
            ]
            assert "Tizen Studio" in content

    def test_cmakelists_exports_compile_commands(self) -> None:
        """CMakeLists.txt exports the compile database clang-tidy needs.

        scripts/lint.sh and the pre-commit clang-tidy hook both read
        build/compile_commands.json (#362), so the configure step must
        export it unconditionally.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert "set(CMAKE_EXPORT_COMPILE_COMMANDS ON)" in content

    def test_cmakelists_defines_opt_in_coverage_option(self) -> None:
        """CMakeLists.txt wires the gcov instrumentation behind an option.

        scripts/test.sh --coverage reconfigures with -DENABLE_COVERAGE=ON
        (#362); plain builds must stay uninstrumented, and the gcov
        runtime must propagate to the test executable (PUBLIC).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["CMakeLists.txt"].read_text()
            assert 'option(ENABLE_COVERAGE "' in content
            assert "OFF)" in content
            assert "target_compile_options(greeting PUBLIC --coverage" in content
            assert "target_link_options(greeting PUBLIC --coverage)" in content

    def test_conanfile_pins_catch2(self) -> None:
        """conanfile.txt requires the pinned Catch2 version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["conanfile.txt"].read_text()
            assert f"catch2/{CATCH2_VERSION}" in content
            assert "[requires]" in content

    def test_conanfile_declares_cmake_generators(self) -> None:
        """conanfile.txt emits the toolchain the documented build consumes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = self._generate(tmpdir)

            content = files["conanfile.txt"].read_text()
            assert "CMakeDeps" in content
            assert "CMakeToolchain" in content
