"""Unit tests for Structure Generator."""

import ast
from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.structure import StructureConfig
from start_green_stay_green.generators.structure import StructureGenerator

# Expected source directories per language
EXPECTED_SOURCE_DIRS: dict[str, str] = {
    "python": "test_project",
    "typescript": "src",
    "go": "cmd",
    "rust": "src",
    "java": "src",
    "csharp": "src",
    "ruby": "lib",
}

# Expected entry point files per language
EXPECTED_ENTRY_POINTS: dict[str, str] = {
    "python": "test_project/main.py",
    "typescript": "src/index.ts",
    "go": "cmd/test_project/main.go",
    "rust": "src/main.rs",
    "java": "src/main/java/test_project/Main.java",
    "csharp": "src/Program.cs",
    "ruby": "lib/test_project.rb",
}

# Expected config files per language
EXPECTED_CONFIG_FILES: dict[str, list[str]] = {
    "python": [],
    "typescript": [
        "tsconfig.json",
        ".eslintrc.js",
        ".prettierrc",
        "jest.config.js",
        ".prettierignore",
    ],
    "go": ["go.mod"],
    "rust": ["Cargo.toml"],
    "java": ["pom.xml"],
    "csharp": [],
    "ruby": ["Gemfile"],
}


class TestStructureGeneratorInitialization:
    """Test StructureGenerator initialization and basic instantiation."""

    def test_generator_can_be_instantiated(self) -> None:
        """Test StructureGenerator can be created with config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            assert generator is not None
            assert isinstance(generator, StructureGenerator)

    def test_generator_has_generate_method(self) -> None:
        """Test generator has generate method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            assert hasattr(generator, "generate")
            assert callable(generator.generate)


class TestStructureGeneration:
    """Test project structure generation."""

    def test_generate_creates_source_directory(self) -> None:
        """Test generate creates source directory with package name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            generator.generate()

            # Should create package directory
            package_dir = Path(tmpdir) / "test_project"
            assert package_dir.exists()
            assert package_dir.is_dir()

    def test_generate_creates_init_file(self) -> None:
        """Test generate creates __init__.py in package directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "test_project/__init__.py" in files
            init_path = files["test_project/__init__.py"]
            assert init_path.exists()
            assert init_path.is_file()

    def test_generate_creates_main_file(self) -> None:
        """Test generate creates main.py with Hello World."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "test_project/main.py" in files
            main_path = files["test_project/main.py"]
            assert main_path.exists()
            assert main_path.is_file()

    def test_init_has_version(self) -> None:
        """Test __init__.py contains version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["test_project/__init__.py"]
            content = init_path.read_text()

            assert "__version__" in content
            assert "0.1.0" in content

    def test_init_has_docstring(self) -> None:
        """Test __init__.py contains package docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            init_path = files["test_project/__init__.py"]
            content = init_path.read_text()

            # Should have triple-quoted docstring
            assert '"""' in content

    def test_main_has_hello_world_function(self) -> None:
        """Test main.py contains a main() function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            main_path = files["test_project/main.py"]
            content = main_path.read_text()

            assert "def main()" in content
            assert "print(" in content

    def test_main_has_if_name_main(self) -> None:
        """Test main.py has if __name__ == '__main__' guard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            main_path = files["test_project/main.py"]
            content = main_path.read_text()

            assert 'if __name__ == "__main__"' in content
            assert "main()" in content

    def test_generated_files_are_valid_python(self) -> None:
        """Test generated files are syntactically valid Python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="python",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            # Try to compile the generated files
            for file_path in files.values():
                if file_path.suffix == ".py":
                    content = file_path.read_text()
                    # Should compile without SyntaxError
                    ast.parse(content)


class TestStructureConfigValidation:
    """Test StructureConfig validation."""

    def test_config_requires_project_name(self) -> None:
        """Test config validates project_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="",  # Empty string
                language="python",
                package_name="test",
            )

    def test_config_requires_language(self) -> None:
        """Test config validates language is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="test",
                language="",  # Empty string
                package_name="test",
            )

    def test_config_requires_package_name(self) -> None:
        """Test config validates package_name is provided."""
        with pytest.raises((TypeError, ValueError)):
            StructureConfig(
                project_name="test",
                language="python",
                package_name="",  # Empty string
            )


class TestUnsupportedLanguage:
    """Test error handling for unsupported languages."""

    def test_unsupported_language_raises_error(self) -> None:
        """Test that unsupported language raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="brainfuck",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)

            with pytest.raises(ValueError, match="Unsupported language"):
                generator.generate()


class TestMultiLanguageStructure:
    """Test structure generation for all supported languages."""

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_source_directory(self, lang: str) -> None:
        """Test generate creates source directory for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert files, f"No files generated for {lang}"
            # All generated files should exist
            for key, path in files.items():
                assert path.exists(), f"File {key} missing for {lang}"

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_entry_point(self, lang: str) -> None:
        """Test generate creates an entry point file for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            expected_entry = EXPECTED_ENTRY_POINTS[lang]
            assert expected_entry in files, (
                f"Entry point {expected_entry} not in files for {lang}: "
                f"{list(files.keys())}"
            )
            entry_path = files[expected_entry]
            assert entry_path.exists()
            content = entry_path.read_text()
            assert len(content) > 0, f"Entry point empty for {lang}"
            # Should contain hello/print message
            assert (
                "hello" in content.lower()
                or "print" in content.lower()
                or "fmt" in content.lower()
            )

    @pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
    def test_generate_creates_expected_source_dir(self, lang: str) -> None:
        """Test generate creates the expected source directory for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            generator.generate()

            expected_dir = EXPECTED_SOURCE_DIRS[lang]
            source_dir = Path(tmpdir) / expected_dir
            assert (
                source_dir.exists()
            ), f"Source dir '{expected_dir}' not created for {lang}"

    @pytest.mark.parametrize(
        ("lang", "config_files"),
        [
            (lang, files)
            for lang, files in EXPECTED_CONFIG_FILES.items()
            if files  # Only test languages with config files
        ],
    )
    def test_generate_creates_config_files(
        self, lang: str, config_files: list[str]
    ) -> None:
        """Test generate creates language-specific config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language=lang,
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            for config_file in config_files:
                assert config_file in files, (
                    f"Config file {config_file} not in files for {lang}: "
                    f"{list(files.keys())}"
                )
                assert files[config_file].exists()

    def test_typescript_creates_tsconfig(self) -> None:
        """Test TypeScript generates tsconfig.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "tsconfig.json" in files
            content = files["tsconfig.json"].read_text()
            assert "compilerOptions" in content

    def test_go_creates_go_mod(self) -> None:
        """Test Go generates go.mod."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="go",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "go.mod" in files
            content = files["go.mod"].read_text()
            assert "module" in content
            assert "go " in content

    def test_rust_creates_cargo_toml(self) -> None:
        """Test Rust generates Cargo.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="rust",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "Cargo.toml" in files
            content = files["Cargo.toml"].read_text()
            assert "[package]" in content
            assert "test-project" in content

    def test_java_creates_pom_xml(self) -> None:
        """Test Java generates pom.xml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="java",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "pom.xml" in files
            content = files["pom.xml"].read_text()
            assert "<project" in content

    def test_csharp_creates_program_cs(self) -> None:
        """Test C# generates Program.cs source file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="csharp",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "src/Program.cs" in files
            content = files["src/Program.cs"].read_text()
            assert "Hello from" in content

    def test_ruby_creates_gemfile(self) -> None:
        """Test Ruby generates Gemfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="ruby",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "Gemfile" in files
            content = files["Gemfile"].read_text()
            assert "source" in content


class TestTypeScriptConfigGeneration:
    """Test TypeScript config file generation."""

    def test_typescript_creates_eslintrc(self) -> None:
        """Test TypeScript generates .eslintrc.js."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert ".eslintrc.js" in files
            assert files[".eslintrc.js"].exists()

    def test_eslintrc_uses_typescript_parser(self) -> None:
        """Test .eslintrc.js configures @typescript-eslint/parser."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files[".eslintrc.js"].read_text()
            assert "@typescript-eslint/parser" in content
            assert "@typescript-eslint" in content

    def test_eslintrc_has_jest_env(self) -> None:
        """Test .eslintrc.js enables jest environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files[".eslintrc.js"].read_text()
            assert "jest: true" in content

    def test_eslintrc_ignores_dist_and_node_modules(self) -> None:
        """Test .eslintrc.js ignores dist and node_modules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files[".eslintrc.js"].read_text()
            assert "dist" in content
            assert "node_modules" in content

    def test_typescript_creates_prettierrc(self) -> None:
        """Test TypeScript generates .prettierrc."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert ".prettierrc" in files
            assert files[".prettierrc"].exists()

    def test_prettierrc_has_formatting_options(self) -> None:
        """Test .prettierrc contains formatting options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files[".prettierrc"].read_text()
            assert "semi" in content
            assert "trailingComma" in content
            assert "printWidth" in content
            assert "tabWidth" in content

    def test_typescript_creates_jest_config(self) -> None:
        """Test TypeScript generates jest.config.js."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert "jest.config.js" in files
            assert files["jest.config.js"].exists()

    def test_jest_config_uses_ts_jest_preset(self) -> None:
        """Test jest.config.js uses ts-jest preset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["jest.config.js"].read_text()
            assert "ts-jest" in content
            assert "node" in content

    def test_jest_config_has_coverage_thresholds(self) -> None:
        """Test jest.config.js has 90% coverage thresholds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["jest.config.js"].read_text()
            assert "coverageThreshold" in content
            assert "90" in content

    def test_jest_config_excludes_declaration_files(self) -> None:
        """Test jest.config.js excludes .d.ts files from coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files["jest.config.js"].read_text()
            assert ".d.ts" in content

    def test_typescript_creates_prettierignore(self) -> None:
        """Test TypeScript generates .prettierignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            assert ".prettierignore" in files
            assert files[".prettierignore"].exists()

    def test_prettierignore_excludes_claude_directory(self) -> None:
        """Test .prettierignore excludes .claude directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = StructureConfig(
                project_name="test-project",
                language="typescript",
                package_name="test_project",
            )
            generator = StructureGenerator(Path(tmpdir), config)
            files = generator.generate()

            content = files[".prettierignore"].read_text()
            assert ".claude" in content
            assert "dist" in content
            assert "node_modules" in content
