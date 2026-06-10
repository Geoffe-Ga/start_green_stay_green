"""Unit tests for README Generator."""

from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.readme import ReadmeConfig
from start_green_stay_green.generators.readme import ReadmeGenerator

# Expected commands that should appear in README per language
EXPECTED_COMMANDS: dict[str, list[str]] = {
    "python": ["pip install", "pytest"],
    "typescript": ["npm install", "npm test"],
    "go": ["go build", "go test"],
    "rust": ["cargo build", "cargo test"],
    "java": ["mvn compile", "mvn test"],
    "csharp": ["dotnet build", "dotnet test"],
    "ruby": ["bundle install", "rspec"],
    "swift": ["swift build", "swift test"],
    "kotlin": ["./gradlew build", "./gradlew test"],
    "cpp": ["cmake --build build", "ctest --test-dir build"],
}


class TestReadmeGeneratorInitialization:
    """Test ReadmeGenerator initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test ReadmeGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, ReadmeGenerator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestReadmeGeneration:
    """Test README.md generation."""

    def test_generate_creates_readme(self) -> None:
        """Test generate creates README.md file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "README.md" in files
            readme_path = files["README.md"]
            assert readme_path.exists()
            assert readme_path.is_file()

    def test_readme_has_project_title(self) -> None:
        """Test README.md contains project title."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have title with project name
            assert "# test-project" in content or "# Test Project" in content

    def test_readme_has_description(self) -> None:
        """Test README.md contains description."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have description section
            assert "## Description" in content or "description" in content.lower()

    def test_readme_has_installation_section(self) -> None:
        """Test README.md contains installation instructions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have installation section
            assert "## Installation" in content or "install" in content.lower()

    def test_readme_has_usage_section(self) -> None:
        """Test README.md contains usage/quickstart."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have usage section
            assert (
                "## Usage" in content
                or "## Quickstart" in content
                or "usage" in content.lower()
            )

    def test_readme_has_development_section(self) -> None:
        """Test README.md contains development/quality tools section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have development section
            assert "## Development" in content or "quality" in content.lower()

    def test_readme_mentions_quality_tools(self) -> None:
        """Test README.md mentions quality control tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should mention at least some quality tools
            assert (
                "pytest" in content.lower()
                or "ruff" in content.lower()
                or "quality" in content.lower()
            )

    def test_readme_has_license(self) -> None:
        """Test README.md contains license information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            readme_path = files["README.md"]
            content = readme_path.read_text()

            # Should have license section
            assert "## License" in content or "license" in content.lower()


class TestReadmeConfigValidation:
    """Test ReadmeConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            ReadmeConfig(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            ReadmeConfig(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            ReadmeConfig(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="brainfuck",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)

            with pytest.raises(ValueError, match="Unsupported language"):
                generator.generate()


class TestMultiLanguageReadme:
    """Test README generation for all supported languages."""

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_readme(self, lang: str) -> None:
        """Test generate creates README.md for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "README.md" in files
            readme_path = files["README.md"]
            assert readme_path.exists()

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_readme_contains_project_name(self, lang: str) -> None:
        """Test README contains project name for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "test-project" in content

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_readme_contains_language_commands(self, lang: str) -> None:
        """Test README contains language-specific commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            expected = EXPECTED_COMMANDS[lang]
            for cmd in expected:
                assert (
                    cmd in content
                ), f"Expected command '{cmd}' not in README for {lang}"

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_readme_has_installation_section(self, lang: str) -> None:
        """Test README has installation section for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "## Installation" in content or "install" in content.lower()

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_readme_has_license_section(self, lang: str) -> None:
        """Test README has license section for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "License" in content


class TestSwiftReadme:
    """Test Swift-specific README content."""

    def test_swift_readme_mentions_watchos(self) -> None:
        """Test Swift README documents the watchOS / Apple Watch target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "watchOS" in content
            assert "SwiftUI" in content

    def test_swift_readme_mentions_spm(self) -> None:
        """Test Swift README documents Swift Package Manager usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "swift build" in content
            assert "swift test" in content
            assert "Package.swift" in content

    def test_swift_readme_only_checkmarks_generated_features(self) -> None:
        """Swift README must not ✅ features the scaffold does not generate.

        After #352 the quality toolchain (SwiftLint, swift-format,
        pre-commit hooks, quality scripts) IS generated and may carry a
        checkmark; the CI/CD pipeline (#353) remains deferred and must not.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()

            # Features that ARE generated may carry a checkmark.
            assert "- ✅" in content
            assert "Swift Package Manager manifest" in content
            wired = ("SwiftLint", "swift-format", "Pre-commit hooks")
            for feature in wired:
                assert any(
                    "✅" in line and feature in line for line in content.splitlines()
                ), f"README must advertise wired feature: {feature}"

            # Unwired features must never be claimed with a ✅ checkmark.
            unwired = ("CI/CD pipeline",)
            for feature in unwired:
                assert (
                    f"✅ {feature}" not in content
                ), f"README falsely advertises unwired feature: {feature}"
                # The checkmark must not appear on the same line either.
                for line in content.splitlines():
                    if feature in line:
                        assert (
                            "✅" not in line
                        ), f"Unwired feature {feature!r} marked with ✅"

    def test_swift_readme_lists_unwired_features_as_planned(self) -> None:
        """Deferred Swift tooling is disclosed under a 'Planned' section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "Planned / coming soon" in content
            assert "CI/CD pipeline" in content

    def test_swift_readme_instructs_pre_commit_install(self) -> None:
        """README tells users to install the now-generated pre-commit hooks.

        Inverted from the #351 foundation scaffold: #352 wires a Swift
        .pre-commit-config.yaml, so the README must document installing it.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "pre-commit install" in content

    def test_swift_readme_documents_quality_tool_installs(self) -> None:
        """README documents installing the brew-distributed quality tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ReadmeConfig(
                project_name="test-project",
                language="swift",
                package_name="test_project",
            )
            generator = ReadmeGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["README.md"].read_text()
            assert "brew install swiftlint swift-format periphery" in content


class TestKotlinReadme:
    """Test Kotlin-specific README content (#356)."""

    @staticmethod
    def _readme_content(tmpdir: str) -> str:
        """Generate the kotlin README and return its text.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            The rendered README.md content.
        """
        config = ReadmeConfig(
            project_name="test-project",
            language="kotlin",
            package_name="test_project",
        )
        files = ReadmeGenerator(Path(tmpdir), config).generate()
        readme_path: Path = files["README.md"]
        return readme_path.read_text()

    def test_kotlin_readme_mentions_wear_os_and_compose(self) -> None:
        """Kotlin README documents the Wear OS / Compose target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "Wear OS" in content
            assert "Jetpack Compose" in content

    def test_kotlin_readme_documents_gradle_usage(self) -> None:
        """Kotlin README documents Gradle build and test commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "./gradlew build" in content
            assert "./gradlew test" in content
            assert "settings.gradle.kts" in content

    def test_kotlin_readme_documents_missing_gradle_wrapper(self) -> None:
        """README tells users to create the wrapper (it is not generated)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "gradle wrapper" in content
            assert "not generated" in content.lower()

    def test_kotlin_readme_only_checkmarks_generated_features(self) -> None:
        """Kotlin README ✅-marks the full generated pipeline.

        After #357 the quality toolchain (ktlint, detekt, pre-commit
        hooks, quality scripts) IS generated, and after #358 the CI
        pipeline is too — every one of them must carry a checkmark.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)

            assert "- ✅" in content
            wired = ("ktlint", "detekt", "Pre-commit hooks", "CI/CD pipeline")
            for feature in wired:
                assert any(
                    "✅" in line and feature in line for line in content.splitlines()
                ), f"README must advertise wired feature: {feature}"

    def test_kotlin_readme_advertises_generated_ci_pipeline(self) -> None:
        """The CI pipeline (#358) is generated — no 'Planned' disclosure left.

        Inverted from the #356/#357 scaffolds, which truthfully deferred
        CI under a 'Planned / coming soon' section. #358 generates
        .github/workflows/ci.yml, so the README must document it as real
        (ubuntu runners, JDK 17/21 matrix) and drop the planned section.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "Planned / coming soon" not in content
            assert ".github/workflows/ci.yml" in content
            assert "JDK 17 and 21" in content
            assert "ubuntu" in content

    def test_kotlin_readme_instructs_pre_commit_install(self) -> None:
        """README tells users to install the now-generated pre-commit hooks.

        Inverted from the #356 foundation scaffold: #357 wires a Kotlin
        .pre-commit-config.yaml, so the README must document installing it.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "pre-commit install" in content

    def test_kotlin_readme_documents_quality_tool_installs(self) -> None:
        """README documents installing the brew-distributed quality tools."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "brew install ktlint detekt" in content

    def test_kotlin_readme_documents_check_all_gate(self) -> None:
        """README points at the generated quality-gate entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "./scripts/check-all.sh" in content


class TestCppReadme:
    """Test C/C++ Tizen-specific README content (#361/#362)."""

    @staticmethod
    def _readme_content(tmpdir: str) -> str:
        """Generate the cpp README and return its text.

        Args:
            tmpdir: Directory to generate into.

        Returns:
            The rendered README.md content.
        """
        config = ReadmeConfig(
            project_name="test-project",
            language="cpp",
            package_name="test_project",
        )
        files = ReadmeGenerator(Path(tmpdir), config).generate()
        readme_path: Path = files["README.md"]
        return readme_path.read_text()

    def test_cpp_readme_mentions_tizen_watch_target(self) -> None:
        """cpp README documents the Tizen native Galaxy Watch target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "Tizen" in content
            assert "Galaxy Watch" in content
            assert "org.example.testproject" in content

    def test_cpp_readme_discloses_planned_tooling(self) -> None:
        """README lists the deferred CI pipeline (#363) as planned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "Planned / coming soon" in content
            assert "not yet generated" in content
            assert "CI/CD pipeline" in content

    def test_cpp_readme_only_checkmarks_generated_features(self) -> None:
        """cpp README must not ✅ features the scaffold does not generate.

        After #362 the quality toolchain (clang-format/clang-tidy/cppcheck,
        pre-commit hooks, quality scripts, architecture rules) IS generated
        and may carry a checkmark; the CI/CD pipeline (#363) remains
        deferred and must not.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)

            wired = ("clang-format", "clang-tidy", "Pre-commit hooks", "lizard")
            for feature in wired:
                assert any(
                    "✅" in line and feature in line for line in content.splitlines()
                ), f"README must advertise wired feature: {feature}"

            unwired = ("CI/CD pipeline",)
            for feature in unwired:
                assert not any(
                    "✅" in line and feature in line for line in content.splitlines()
                ), f"README must not checkmark planned feature: {feature}"

    def test_cpp_readme_instructs_pre_commit_install(self) -> None:
        """README tells users to install the now-generated pre-commit hooks.

        Inverted from the #361 foundation scaffold: #362 wires a cpp
        .pre-commit-config.yaml, so the README must document installing it.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "pre-commit install" in content

    def test_cpp_readme_documents_quality_tool_installs(self) -> None:
        """README documents installing the quality toolchain.

        clang-format/llvm/cppcheck/lcov come from brew or apt; lizard and
        flawfinder are pip-installable — both install paths must appear.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "brew install clang-format llvm cppcheck lcov" in content
            assert "apt-get install clang-format clang-tidy cppcheck lcov" in content
            assert "pip install lizard flawfinder" in content

    def test_cpp_readme_documents_check_all_gate(self) -> None:
        """README points at the generated quality-gate entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "./scripts/check-all.sh" in content

    def test_cpp_readme_documents_coverage_denominator_limit(self) -> None:
        """README discloses that main.cpp is outside the coverage gate.

        src/main.cpp needs the Tizen SDK and is not part of the host
        build, so the >=90% lcov gate cannot see it; the README must say
        so instead of implying whole-project coverage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "coverage denominator" in content

    def test_cpp_readme_documents_tizen_studio_split(self) -> None:
        """README explains the plain-CMake vs Tizen Studio build split."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "Tizen Studio" in content
            assert "tizen package" in content
            assert "no Tizen Studio" in content

    def test_cpp_readme_documents_cmake_conan_commands(self) -> None:
        """README documents the Conan install and CMake/CTest commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = self._readme_content(tmpdir)
            assert "conan install . --output-folder=build --build=missing" in content
            assert "cmake --build build" in content
            assert "ctest --test-dir build" in content
