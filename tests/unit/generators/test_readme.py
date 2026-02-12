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
