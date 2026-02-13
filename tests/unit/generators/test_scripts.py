"""Unit tests for Scripts Generator."""

from pathlib import Path
import tempfile

import pytest

from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator


class TestScriptConfig:
    """Test ScriptConfig data class."""

    def test_script_config_initialization_with_required_fields(self) -> None:
        """Test ScriptConfig initializes with required fields."""
        config = ScriptConfig(
            language="python",
            package_name="my_package",
        )
        assert config.language == "python"
        assert config.package_name == "my_package"

    def test_script_config_initialization_with_all_fields(self) -> None:
        """Test ScriptConfig initializes with all optional fields."""
        config = ScriptConfig(
            language="typescript",
            package_name="my_app",
            supports_pytest=False,
            supports_coverage=False,
            supports_mutation=False,
            supports_complexity=False,
            supports_security=False,
        )
        assert config.language == "typescript"
        assert config.package_name == "my_app"
        assert not config.supports_pytest
        assert not config.supports_coverage
        assert not config.supports_mutation
        assert not config.supports_complexity
        assert not config.supports_security

    def test_script_config_default_values(self) -> None:
        """Test ScriptConfig has correct default values."""
        config = ScriptConfig(
            language="go",
            package_name="go_module",
        )
        assert config.supports_pytest
        assert config.supports_coverage
        assert config.supports_mutation
        assert config.supports_complexity
        assert config.supports_security

    def test_script_config_is_immutable(self) -> None:
        """Test ScriptConfig is immutable (frozen)."""
        config = ScriptConfig(
            language="python",
            package_name="my_package",
        )
        with pytest.raises(AttributeError):
            config.language = "typescript"  # type: ignore[misc]

    def test_script_config_language_various_values(self) -> None:
        """Test ScriptConfig accepts various language values."""
        languages = ["python", "typescript", "go", "rust", "javascript"]
        for lang in languages:
            config = ScriptConfig(
                language=lang,
                package_name="test",
            )
            assert config.language == lang


class TestScriptsGeneratorInit:
    """Test ScriptsGenerator initialization."""

    def test_generator_initialization_with_valid_config(self) -> None:
        """Test generator initializes with valid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            assert generator.config == config
            assert generator.output_dir == Path(tmpdir)

    def test_generator_initialization_creates_output_directory(self) -> None:
        """Test generator creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "scripts"
            assert not nested_dir.exists()

            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            ScriptsGenerator(nested_dir, config)
            assert nested_dir.exists()

    def test_generator_initialization_with_empty_language_raises(self) -> None:
        """Test generator raises ValueError for empty language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="",
                package_name="my_package",
            )
            with pytest.raises(ValueError, match="Language cannot be empty"):
                ScriptsGenerator(Path(tmpdir), config)

    def test_generator_initialization_with_empty_package_raises(self) -> None:
        """Test generator raises ValueError for empty package name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="",
            )
            with pytest.raises(ValueError, match="Package name cannot be empty"):
                ScriptsGenerator(Path(tmpdir), config)


class TestScriptsGeneratorPythonGeneration:
    """Test Python script generation."""

    def test_generate_python_scripts_creates_all_files(self) -> None:
        """Test generate creates all Python scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "fix-all.sh" in scripts
            assert "security.sh" in scripts
            assert "complexity.sh" in scripts

    def test_generate_python_scripts_files_exist(self) -> None:
        """Test generated Python script files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            for script_path in scripts.values():
                assert script_path.exists()
                assert script_path.is_file()

    def test_generate_python_scripts_are_executable(self) -> None:
        """Test generated Python scripts are executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            for script_path in scripts.values():
                # Check execute permission (0o755 & 0o111 should be 0o111)
                assert script_path.stat().st_mode & 0o111

    def test_python_check_all_script_contains_expected_content(self) -> None:
        """Test Python check-all.sh contains expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["check-all.sh"].read_text()
            assert "#!/usr/bin/env bash" in content
            assert "Running All Quality Checks" in content
            assert "lint.sh" in content
            assert "format.sh" in content

    def test_python_format_script_contains_expected_content(self) -> None:
        """Test Python format.sh contains expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            assert "Black + isort" in content
            assert "isort" in content
            assert "black" in content

    def test_python_lint_script_contains_ruff(self) -> None:
        """Test Python lint.sh uses Ruff."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "ruff" in content
            assert "Ruff" in content

    def test_python_test_script_contains_pytest(self) -> None:
        """Test Python test.sh uses Pytest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["test.sh"].read_text()
            assert "pytest" in content
            assert "Pytest" in content

    def test_python_fix_all_script_contains_expected_content(self) -> None:
        """Test Python fix-all.sh contains expected content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["fix-all.sh"].read_text()
            assert "Auto-fix" in content
            assert "--fix" in content

    def test_python_security_script_contains_bandit_safety(self) -> None:
        """Test Python security.sh mentions Bandit and Safety."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["security.sh"].read_text()
            assert "Bandit" in content
            assert "Safety" in content

    def test_python_complexity_script_contains_radon_xenon(self) -> None:
        """Test Python complexity.sh mentions Radon and Xenon."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["complexity.sh"].read_text()
            assert "radon" in content
            assert "xenon" in content


class TestScriptsGeneratorTypeScriptGeneration:
    """Test TypeScript script generation."""

    def test_generate_typescript_scripts_creates_files(self) -> None:
        """Test generate creates TypeScript scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "typecheck.sh" in scripts
            assert "fix-all.sh" in scripts

    def test_typescript_format_script_uses_prettier(self) -> None:
        """Test TypeScript format.sh uses Prettier."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            assert "prettier" in content
            assert "Prettier" in content

    def test_typescript_lint_script_uses_eslint(self) -> None:
        """Test TypeScript lint.sh uses ESLint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "eslint" in content
            assert "ESLint" in content

    def test_typescript_test_script_uses_jest(self) -> None:
        """Test TypeScript test.sh uses Jest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["test.sh"].read_text()
            assert "jest" in content
            assert "Jest" in content

    def test_typescript_variant_ts_creates_scripts(self) -> None:
        """Test 'ts' language variant creates TypeScript scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="ts",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "format.sh" in scripts
            content = scripts["format.sh"].read_text()
            assert "prettier" in content


class TestScriptsGeneratorGoGeneration:
    """Test Go script generation."""

    def test_generate_go_scripts_creates_files(self) -> None:
        """Test generate creates Go scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="go",
                package_name="my_module",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts

    def test_go_format_script_uses_gofmt(self) -> None:
        """Test Go format.sh uses gofmt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="go",
                package_name="my_module",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            assert "gofmt" in content
            assert "goimports" in content

    def test_go_lint_script_uses_golangci_lint(self) -> None:
        """Test Go lint.sh uses golangci-lint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="go",
                package_name="my_module",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "golangci-lint" in content

    def test_go_test_script_uses_go_test(self) -> None:
        """Test Go test.sh uses go test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="go",
                package_name="my_module",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["test.sh"].read_text()
            assert "go test" in content


class TestScriptsGeneratorRustGeneration:
    """Test Rust script generation."""

    def test_generate_rust_scripts_creates_files(self) -> None:
        """Test generate creates Rust scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="rust",
                package_name="my_crate",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts

    def test_rust_format_script_uses_rustfmt(self) -> None:
        """Test Rust format.sh uses rustfmt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="rust",
                package_name="my_crate",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            assert "rustfmt" in content

    def test_rust_lint_script_uses_clippy(self) -> None:
        """Test Rust lint.sh uses clippy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="rust",
                package_name="my_crate",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "clippy" in content

    def test_rust_test_script_uses_cargo_test(self) -> None:
        """Test Rust test.sh uses cargo test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="rust",
                package_name="my_crate",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["test.sh"].read_text()
            assert "cargo test" in content


class TestScriptsGeneratorLanguageFallback:
    """Test language fallback behavior."""

    def test_unknown_language_falls_back_to_python(self) -> None:
        """Test unknown language falls back to Python scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="ruby",
                package_name="my_gem",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should create Python-style scripts
            content = scripts["format.sh"].read_text()
            assert "Black + isort" in content


class TestScriptsGeneratorHelp:
    """Test help text in generated scripts."""

    def test_python_script_has_help_option(self) -> None:
        """Test Python scripts have --help option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "--help" in content
            assert "Usage:" in content

    def test_script_help_includes_options(self) -> None:
        """Test script help includes available options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            assert "OPTIONS:" in content
            assert "--fix" in content
            assert "--check" in content


class TestScriptsGeneratorErrorHandling:
    """Test error handling in scripts."""

    def test_python_scripts_have_error_handling(self) -> None:
        """Test bash scripts have set -euo pipefail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Only check bash scripts (.sh files) for bash error handling
            for script_path in scripts.values():
                if script_path.suffix == ".sh":
                    content = script_path.read_text()
                    assert "set -euo pipefail" in content

    def test_python_scripts_have_exit_codes(self) -> None:
        """Test Python scripts document exit codes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["lint.sh"].read_text()
            assert "EXIT CODES:" in content
            assert "exit 0" in content
            assert "exit 1" in content


class TestScriptsGeneratorEdgeCases:
    """Test edge cases in script generation."""

    def test_script_generation_with_special_package_names(self) -> None:
        """Test script generation with special package names."""
        special_names = [
            "my-package",
            "my_package",
            "MyPackage",
            "MYPACKAGE",
            "my.package",
        ]

        for package_name in special_names:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = ScriptConfig(
                    language="python",
                    package_name=package_name,
                )
                generator = ScriptsGenerator(Path(tmpdir), config)
                scripts = generator.generate()
                assert scripts

    def test_script_generation_with_existing_output_dir(self) -> None:
        """Test script generation overwrites existing output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "scripts"
            output_dir.mkdir()

            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(output_dir, config)
            scripts = generator.generate()

            assert output_dir.exists()
            assert scripts


class TestMutationKillers:
    """Targeted tests to kill specific mutations.

    These tests explicitly verify exact values, boundary conditions, and
    specific behavior to ensure mutations are caught.
    """

    def test_script_config_language_exact_value(self) -> None:
        """Test ScriptConfig.language is EXACTLY set to input value.

        Kills mutations in field assignments.
        """
        config = ScriptConfig(
            language="python",
            package_name="test",
        )
        assert config.language == "python"
        assert config.language != "typescript"
        assert config.language != ""

    def test_script_config_package_name_exact_value(self) -> None:
        """Test ScriptConfig.package_name is EXACTLY set to input value."""
        config = ScriptConfig(
            language="python",
            package_name="my_package",
        )
        assert config.package_name == "my_package"
        assert config.package_name != "my-package"
        assert config.package_name != ""

    def test_generator_output_dir_is_path_object(self) -> None:
        """Test generator.output_dir is a Path object, not string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            assert isinstance(generator.output_dir, Path)
            assert not isinstance(generator.output_dir, str)

    def test_python_language_dispatches_to_python_generator(self) -> None:
        """Test 'python' language dispatches to Python generator.

        Kills mutations in language comparison logic.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate Python scripts with Ruff
            content = scripts["lint.sh"].read_text()
            assert "ruff" in content

    def test_typescript_language_dispatches_to_typescript_generator(self) -> None:
        """Test 'typescript' language dispatches to TypeScript generator.

        Kills mutations in language comparison logic.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate TypeScript scripts with ESLint
            content = scripts["lint.sh"].read_text()
            assert "eslint" in content

    def test_go_language_dispatches_to_go_generator(self) -> None:
        """Test 'go' language dispatches to Go generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="go",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate Go scripts with golangci-lint
            content = scripts["lint.sh"].read_text()
            assert "golangci-lint" in content

    def test_rust_language_dispatches_to_rust_generator(self) -> None:
        """Test 'rust' language dispatches to Rust generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="rust",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate Rust scripts with clippy
            content = scripts["lint.sh"].read_text()
            assert "clippy" in content

    def test_generated_scripts_exact_count_python(self) -> None:
        """Test Python generator creates EXACTLY 9 scripts.

        Kills mutations in script count logic.
        Scripts: check-all, format, lint, test, fix-all, security, complexity,
        mutation, analyze_mutations.py
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 11
            assert len(scripts) > 10
            assert len(scripts) < 12

    def test_generated_scripts_exact_count_typescript(self) -> None:
        """Test TypeScript generator creates EXACTLY 6 scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 6
            assert len(scripts) > 5
            assert len(scripts) < 7

    def test_script_file_executable_permission_exact(self) -> None:
        """Test generated scripts have EXACT executable permission (0o755).

        Kills mutations in chmod value.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            for script_path in scripts.values():
                mode = script_path.stat().st_mode
                # 0o755 means rwxr-xr-x
                assert mode & 0o700 == 0o700  # Owner can read, write, execute
                assert mode & 0o070 == 0o050  # Group can read, execute
                assert mode & 0o007 == 0o005  # Others can read, execute

    def test_script_content_is_string_not_bytes(self) -> None:
        """Test script generator returns file paths, not bytes.

        Kills mutations in write_script return type.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            for script_path in scripts.values():
                assert isinstance(script_path, Path)
                assert not isinstance(script_path, bytes)
                content = script_path.read_text()
                assert isinstance(content, str)
                assert not isinstance(content, bytes)

    def test_python_check_all_contains_all_check_names(self) -> None:
        """Test check-all.sh references all checks by exact name.

        Kills mutations in check naming.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["check-all.sh"].read_text()
            # Exact check names
            assert "lint.sh" in content
            assert "format.sh" in content
            assert "typecheck.sh" in content
            assert "security.sh" in content
            assert "complexity.sh" in content
            assert "test.sh" in content
            assert "coverage.sh" in content

    def test_empty_language_error_exact_message(self) -> None:
        """Test exact error message for empty language.

        Kills mutations in error message string.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="",
                package_name="test",
            )
            with pytest.raises(ValueError, match="Language cannot be empty"):
                ScriptsGenerator(Path(tmpdir), config)

    def test_empty_package_name_error_exact_message(self) -> None:
        """Test exact error message for empty package name.

        Kills mutations in error message string.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="",
            )
            with pytest.raises(ValueError, match="Package name cannot be empty"):
                ScriptsGenerator(Path(tmpdir), config)


class TestPythonMutationScript:
    """Test Python mutation.sh script generation.

    Addresses Claude Code Review blocking issue: Missing unit tests
    for _python_mutation_script() method (175 lines of code).
    """

    def test_mutation_script_contains_mutmut_commands(self) -> None:
        """Test mutation.sh contains mutmut run and results commands.

        Verifies the script calls mutmut for mutation testing.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "mutmut run" in content
            assert "mutmut results" in content
            assert "mutmut junitxml" in content

    def test_mutation_script_has_80_percent_threshold(self) -> None:
        """Test mutation.sh has MIN_SCORE=80 (MAXIMUM QUALITY standard).

        Verifies the script enforces 80% mutation score threshold.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "MIN_SCORE=80" in content
            assert "80% minimum mutation score" in content
            assert "MAXIMUM QUALITY" in content

    def test_mutation_script_interpolates_package_name(self) -> None:
        """Test mutation.sh interpolates package_name into script content.

        Verifies the script references the correct package for mutation testing.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            # Package name should appear in path context
            assert "test_package" in content

    def test_mutation_script_has_comprehensive_help_text(self) -> None:
        """Test mutation.sh has --help option with comprehensive documentation.

        Verifies the script provides usage instructions and examples.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "--help" in content
            assert "Usage:" in content
            assert "OPTIONS:" in content
            assert "EXIT CODES:" in content
            assert "QUALITY STANDARDS:" in content
            assert "EXAMPLES:" in content

    def test_mutation_script_has_bash_safety(self) -> None:
        """Test mutation.sh has set -euo pipefail for error handling.

        Verifies the script follows bash best practices for safety.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "set -euo pipefail" in content

    def test_mutation_script_has_score_validation_logic(self) -> None:
        """Test mutation.sh has score calculation and validation logic.

        Verifies the script calculates mutation score and compares to threshold.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            # Score calculation
            assert "KILLED" in content
            assert "SURVIVED" in content
            assert "SUSPICIOUS" in content
            assert "TIMEOUT" in content
            # Validation
            assert "Mutation Score:" in content
            assert "Required:" in content

    def test_mutation_script_has_verbose_mode(self) -> None:
        """Test mutation.sh supports --verbose flag.

        Verifies the script provides detailed output option.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "--verbose" in content
            assert "VERBOSE=false" in content

    def test_mutation_script_has_min_score_option(self) -> None:
        """Test mutation.sh supports --min-score option.

        Verifies the script allows custom threshold configuration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "--min-score" in content

    def test_mutation_script_checks_mutmut_installation(self) -> None:
        """Test mutation.sh checks if mutmut is installed.

        Verifies the script fails gracefully if mutmut is not available.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "command -v mutmut" in content
            assert "mutmut is not installed" in content

    def test_mutation_script_has_proper_exit_codes(self) -> None:
        """Test mutation.sh documents and uses proper exit codes.

        Verifies the script returns appropriate exit codes for different outcomes.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["mutation.sh"].read_text()
            assert "exit 0" in content
            assert "exit 1" in content
            assert "exit 2" in content


class TestPythonAnalyzeMutationsScript:
    """Test Python analyze_mutations.py script generation.

    Verifies the token-efficient mutation analysis script is generated correctly.
    """

    def test_analyze_mutations_script_is_generated(self) -> None:
        """Test analyze_mutations.py is included in generated scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "analyze_mutations.py" in scripts
            assert scripts["analyze_mutations.py"].exists()

    def test_analyze_mutations_script_is_executable(self) -> None:
        """Test analyze_mutations.py is executable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            script_path = scripts["analyze_mutations.py"]
            assert script_path.stat().st_mode & 0o111

    def test_analyze_mutations_script_has_shebang(self) -> None:
        """Test analyze_mutations.py has Python shebang."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert content.startswith("#!/usr/bin/env python3")

    def test_analyze_mutations_script_has_docstring(self) -> None:
        """Test analyze_mutations.py has module docstring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert '"""Analyze mutmut cache database' in content
            assert "mutation testing insights" in content

    def test_analyze_mutations_script_has_sqlite3_import(self) -> None:
        """Test analyze_mutations.py imports sqlite3 for cache analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "import sqlite3" in content

    def test_analyze_mutations_script_has_argparse(self) -> None:
        """Test analyze_mutations.py uses argparse for CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "import argparse" in content
            assert "ArgumentParser" in content

    def test_analyze_mutations_script_has_mutation_score_threshold(self) -> None:
        """Test analyze_mutations.py has 80% threshold constant."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "MINIMUM_MUTATION_SCORE = 80" in content

    def test_analyze_mutations_script_has_analyze_cache_function(self) -> None:
        """Test analyze_mutations.py has analyze_cache function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "def analyze_cache(" in content
            assert "cache_path: Path" in content
            assert "top_files: int" in content
            assert "filter_file: str | None" in content

    def test_analyze_mutations_script_has_main_function(self) -> None:
        """Test analyze_mutations.py has main() entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "def main() -> None:" in content
            assert 'if __name__ == "__main__":' in content

    def test_analyze_mutations_script_has_cli_arguments(self) -> None:
        """Test analyze_mutations.py supports --cache, --top, and filename args."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "--cache" in content
            assert "--top" in content
            assert '"filename"' in content

    def test_analyze_mutations_script_queries_mutant_status(self) -> None:
        """Test analyze_mutations.py queries mutant status from cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "ok_killed" in content
            assert "bad_survived" in content
            assert "ok_suspicious" in content
            assert "bad_timeout" in content

    def test_analyze_mutations_script_calculates_mutation_score(self) -> None:
        """Test analyze_mutations.py calculates mutation score percentage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "Mutation Score:" in content
            assert "score = (killed / tested_total) * 100" in content

    def test_analyze_mutations_script_shows_top_files(self) -> None:
        """Test analyze_mutations.py shows files with most survived mutants."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "Files with Most Survived Mutants" in content
            assert "ORDER BY count DESC" in content

    def test_analyze_mutations_script_shows_sample_mutants(self) -> None:
        """Test analyze_mutations.py shows sample of survived mutants."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "Sample of survived mutants" in content
            assert "mutmut show <id>" in content
            assert "mutmut html" in content

    def test_analyze_mutations_script_has_no_unnecessary_noqa(self) -> None:
        """Test analyze_mutations.py omits noqa for rules not in generated config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            # T201 and PLR0915 are not enabled in generated ruff config
            assert "# ruff: noqa: T201" not in content
            assert "# ruff: noqa: PLR0915" not in content
            # S608 should not appear inside SQL f-strings as string content
            assert "# noqa: S608" not in content

    def test_analyze_mutations_script_handles_file_filter(self) -> None:
        """Test analyze_mutations.py supports filtering by filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "filter_file" in content
            assert "AND sf.filename LIKE ?" in content

    def test_analyze_mutations_script_exits_on_missing_cache(self) -> None:
        """Test analyze_mutations.py exits with error if cache missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "Cache file not found" in content
            assert "sys.exit(1)" in content

    def test_analyze_mutations_script_has_helpful_usage_examples(self) -> None:
        """Test analyze_mutations.py includes usage examples in help."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["analyze_mutations.py"].read_text()
            assert "Examples:" in content
            assert "%(prog)s" in content  # argparse example format


class TestTypeScriptTypecheckScript:
    """Test TypeScript typecheck.sh script generation."""

    def test_typescript_typecheck_script_uses_tsc(self) -> None:
        """Test TypeScript typecheck.sh runs tsc --noEmit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["typecheck.sh"].read_text()
            assert "npx tsc --noEmit" in content
            assert "Type Checking" in content

    def test_typescript_typecheck_script_has_bash_safety(self) -> None:
        """Test TypeScript typecheck.sh has set -euo pipefail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["typecheck.sh"].read_text()
            assert "set -euo pipefail" in content
            assert "#!/usr/bin/env bash" in content

    def test_typescript_typecheck_script_has_help(self) -> None:
        """Test TypeScript typecheck.sh has --help option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["typecheck.sh"].read_text()
            assert "--help" in content
            assert "Usage:" in content
            assert "--verbose" in content

    def test_typescript_check_all_references_typecheck(self) -> None:
        """Test TypeScript check-all.sh references typecheck.sh."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["check-all.sh"].read_text()
            assert "typecheck.sh" in content

    def test_typescript_test_script_handles_empty_jest_args(self) -> None:
        """Test TypeScript test.sh uses safe empty-array expansion for JEST_ARGS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["test.sh"].read_text()
            # Should use safe expansion pattern, not bare "${JEST_ARGS[@]}"
            assert '${JEST_ARGS[@]+"${JEST_ARGS[@]}"}' in content
