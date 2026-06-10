"""Unit tests for Scripts Generator."""

from pathlib import Path
import shutil
import subprocess
import tempfile

from defusedxml import ElementTree as DefusedElementTree
import pytest
import yaml

from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator
from start_green_stay_green.utils.cpp import CPP_STANDARD


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
        languages = ["python", "typescript", "go", "rust", "swift", "javascript"]
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

    def test_python_check_all_uses_safe_array_expansion(self) -> None:
        """check-all.sh run_check must use the exact safe-expansion form.

        Regression guard: a stray trailing backslash-quote after the
        safe expansion is a bash parse error under strict shells and a
        silent literal argument under permissive ones. The expansion
        must match the TypeScript generator's correct form exactly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["check-all.sh"].read_text()
            assert '"${args[@]+"${args[@]}"}" $VERBOSE_FLAG' in content
            assert '}\\" $VERBOSE_FLAG' not in content

    def test_python_fix_all_uses_safe_array_expansion(self) -> None:
        """fix-all.sh must guard empty args with the safe expansion.

        Under ``set -u`` some bash versions raise a bad-substitution
        error when expanding an empty ``${args[@]}`` directly.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["fix-all.sh"].read_text()
            assert '--fix "${args[@]+"${args[@]}"}" $VERBOSE_FLAG' in content
            assert '--fix "${args[@]}" $VERBOSE_FLAG' not in content

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

    def test_python_security_script_contains_bandit_pip_audit(self) -> None:
        """Test Python security.sh mentions Bandit and pip-audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["security.sh"].read_text()
            assert "Bandit" in content
            assert "pip-audit" in content

    def test_python_security_script_supports_known_vuln_suppression(self) -> None:
        """Generated security.sh parses .pip-audit-known-vulnerabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["security.sh"].read_text()
            assert ".pip-audit-known-vulnerabilities" in content
            assert "PIP_AUDIT_ARGS=()" in content
            assert "--ignore-vuln" in content
            # The expanded args are passed to pip-audit
            assert 'pip-audit "${PIP_AUDIT_ARGS[@]}"' in content

    def test_python_pip_audit_template_written_to_project_root(self) -> None:
        """Template `.pip-audit-known-vulnerabilities` lands at project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scripts_dir = project_root / "scripts"
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(
                scripts_dir,
                config,
                project_root=project_root,
            )
            generator.generate()

            template = project_root / ".pip-audit-known-vulnerabilities"
            assert template.exists()

            body = template.read_text(encoding="utf-8")
            # Template is documented and empty (no active suppressions)
            assert "Known vulnerabilities" in body
            assert "pip-audit --ignore-vuln" in body
            # Every non-comment, non-blank line would be an active suppression.
            active = [
                line
                for line in body.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            assert not active

    def test_python_pip_audit_template_preserves_existing_file(self) -> None:
        """Existing `.pip-audit-known-vulnerabilities` is not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            scripts_dir = project_root / "scripts"
            template = project_root / ".pip-audit-known-vulnerabilities"
            template.write_text("CVE-2025-99999  # user customisation\n")

            config = ScriptConfig(language="python", package_name="my_package")
            generator = ScriptsGenerator(
                scripts_dir,
                config,
                project_root=project_root,
            )
            generator.generate()

            assert template.read_text() == "CVE-2025-99999  # user customisation\n"

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

    def test_typescript_format_script_restricts_prettier_to_source_globs(
        self,
    ) -> None:
        """Test TypeScript format.sh restricts Prettier to source file globs.

        Instead of running `npx prettier --check .` on the entire tree,
        format.sh must target specific file patterns to avoid formatting
        non-code files like Markdown, YAML, and shell scripts.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()
            # Must include source globs for TS/JS files
            assert "src/**" in content
            assert "tests/**" in content
            # Must include root config file patterns
            assert "*.{js,json}" in content or (
                "*.js" in content and "*.json" in content
            )

    def test_typescript_format_script_does_not_format_entire_tree(self) -> None:
        """Test format.sh does not use bare '.' target with Prettier.

        Positively asserts the PRETTIER_GLOBS array is used and negatively
        rules out any bare-tree Prettier invocation (quoted or unquoted).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["format.sh"].read_text()

            # Positive: format.sh must declare AND use the scoped globs
            # array in both --check and --write code paths.
            assert (
                "PRETTIER_GLOBS=(" in content
            ), "format.sh must declare a PRETTIER_GLOBS array scoped to source"
            assert (
                'prettier --check "${PRETTIER_GLOBS[@]}"' in content
            ), "format.sh --check must invoke Prettier with PRETTIER_GLOBS"
            assert (
                'prettier --write "${PRETTIER_GLOBS[@]}"' in content
            ), "format.sh --write must invoke Prettier with PRETTIER_GLOBS"

            # Negative: the original bug forms must not reappear in any shape
            forbidden_patterns = (
                "prettier --check .",
                "prettier --write .",
                'prettier --check "."',
                'prettier --write "."',
                "prettier --check './'",
                "prettier --write './'",
            )
            for pattern in forbidden_patterns:
                assert (
                    pattern not in content
                ), f"format.sh must not run Prettier on entire tree: {pattern!r}"

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


class TestScriptsGeneratorSwiftGeneration:
    """Test Swift script generation (#352)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Generate Swift scripts into ``tmpdir`` and return the mapping."""
        config = ScriptConfig(
            language="swift",
            package_name="my_watch_app",
        )
        generator = ScriptsGenerator(Path(tmpdir), config)
        return generator.generate()

    def test_generate_swift_scripts_creates_files(self) -> None:
        """Test generate creates the full Swift script set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "security.sh" in scripts

    def test_swift_format_script_uses_swift_format(self) -> None:
        """Test Swift format.sh uses swift-format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            assert "swift-format" in content

    def test_swift_lint_script_uses_swiftlint_strict(self) -> None:
        """Test Swift lint.sh runs SwiftLint with --strict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "swiftlint lint --strict" in content

    def test_swift_test_script_enables_code_coverage(self) -> None:
        """Test Swift test.sh runs swift test with coverage instrumentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "swift test --enable-code-coverage" in content

    def test_swift_test_script_enforces_90_percent_coverage(self) -> None:
        """Coverage mode reads the llvm-cov codecov JSON and gates at 90%."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            # llvm-cov export JSON path comes from swift test itself.
            assert "--show-codecov-path" in content
            assert "THRESHOLD=90" in content

    def test_swift_security_script_uses_periphery(self) -> None:
        """Test Swift security.sh runs Periphery dead-code analysis."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "periphery scan" in content

    def test_swift_check_all_runs_full_toolchain(self) -> None:
        """check-all.sh runs format, lint, tests (with coverage), security."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["check-all.sh"].read_text()
            assert 'run_check "Format" "format.sh"' in content
            assert 'run_check "Linting" "lint.sh"' in content
            assert 'run_check "Tests" "test.sh" --coverage' in content
            assert 'run_check "Security" "security.sh"' in content

    def test_swift_writes_swiftlint_config_companion(self) -> None:
        """A .swiftlint.yml companion lands at the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            config_path = Path(tmpdir) / ".swiftlint.yml"
            assert config_path.exists()

    def test_swiftlint_config_is_parseable_yaml(self) -> None:
        """.swiftlint.yml must be syntactically valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".swiftlint.yml").read_text()
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, dict)

    def test_swiftlint_config_caps_cyclomatic_complexity_at_10(self) -> None:
        """.swiftlint.yml errors when cyclomatic complexity exceeds 10."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".swiftlint.yml").read_text()
            parsed = yaml.safe_load(content)
            assert parsed["cyclomatic_complexity"]["error"] == 10

    def test_swiftlint_config_preserves_existing_file(self) -> None:
        """An existing user .swiftlint.yml is never overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / ".swiftlint.yml"
            existing.write_text("disabled_rules: [todo]\n")

            self._generate(tmpdir)

            assert existing.read_text() == "disabled_rules: [todo]\n"

    def test_swiftlint_config_documents_security_gap(self) -> None:
        """.swiftlint.yml discloses that secret scanning lives in pre-commit.

        SwiftLint has no dedicated security ruleset; the config must say
        where secret scanning actually happens instead of overclaiming.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".swiftlint.yml").read_text()
            assert "gitleaks" in content


class TestScriptsGeneratorKotlinGeneration:
    """Test Kotlin script generation (#357)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Generate Kotlin scripts into ``tmpdir`` and return the mapping."""
        config = ScriptConfig(
            language="kotlin",
            package_name="my_wear_app",
        )
        generator = ScriptsGenerator(Path(tmpdir), config)
        return generator.generate()

    def test_generate_kotlin_scripts_creates_files(self) -> None:
        """Test generate creates the full Kotlin script set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "security.sh" in scripts

    def test_kotlin_format_script_uses_ktlint(self) -> None:
        """Test Kotlin format.sh uses ktlint."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            assert "ktlint" in content
            assert "ktlint --format" in content

    def test_kotlin_lint_script_uses_detekt_with_companion_config(self) -> None:
        """Test Kotlin lint.sh runs detekt against the shared detekt.yml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "detekt" in content
            assert "--config detekt.yml" in content
            assert "--build-upon-default-config" in content

    def test_kotlin_test_script_requires_gradle_wrapper(self) -> None:
        """test.sh fails with instructions when ./gradlew is missing.

        The #356 scaffold deliberately never writes the wrapper jar
        (binary artifact); the script must say how to create it instead
        of emitting a bare command-not-found.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "./gradlew" in content
            assert "gradle wrapper" in content

    def test_kotlin_test_script_enforces_coverage_via_kover(self) -> None:
        """Coverage mode runs the Kover verify task gating at 90%.

        The 90% bound itself lives in app/build.gradle.kts (kover block);
        the script must invoke the verify task and document where the
        bound is configured rather than duplicating the number in shell.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "koverVerifyDebug" in content
            assert "koverXmlReportDebug" in content
            assert "app/build.gradle.kts" in content

    def test_kotlin_security_script_uses_dependency_check(self) -> None:
        """Test Kotlin security.sh runs OWASP dependency-check."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "dependency-check" in content

    def test_kotlin_security_script_warns_and_skips_when_tool_missing(self) -> None:
        """security.sh degrades to a warning when dependency-check is absent.

        Mirrors the Swift Periphery precedent: a fresh clone must pass
        check-all.sh out of the box, with a documented tighten-me path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "command -v dependency-check" in content
            assert "brew install dependency-check" in content
            assert "Tighten" in content

    def test_kotlin_check_all_runs_full_toolchain(self) -> None:
        """check-all.sh runs format, lint, tests (with coverage), security."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["check-all.sh"].read_text()
            assert 'run_check "Format" "format.sh"' in content
            assert 'run_check "Linting" "lint.sh"' in content
            assert 'run_check "Tests" "test.sh" --coverage' in content
            assert 'run_check "Security" "security.sh"' in content

    def test_kotlin_writes_detekt_config_companion(self) -> None:
        """A detekt.yml companion lands at the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            config_path = Path(tmpdir) / "detekt.yml"
            assert config_path.exists()

    def test_detekt_config_is_parseable_yaml(self) -> None:
        """detekt.yml must be syntactically valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "detekt.yml").read_text()
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, dict)

    def test_detekt_config_caps_cyclomatic_complexity_at_10(self) -> None:
        """detekt.yml enforces the project-wide <=10 complexity ceiling.

        detekt 1.23.x reports methods whose McCabe complexity is >= the
        configured threshold, so a threshold of 11 reports 11+ and
        enforces <=10 — the same gate radon/eslint/gocyclo/clippy/
        SwiftLint apply for the other languages.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "detekt.yml").read_text()
            parsed = yaml.safe_load(content)
            rule = parsed["complexity"]["CyclomaticComplexMethod"]
            assert rule["active"] is True
            assert rule["threshold"] == 11

    def test_detekt_config_activates_potential_bugs(self) -> None:
        """detekt.yml keeps the potential-bugs ruleset active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "detekt.yml").read_text()
            parsed = yaml.safe_load(content)
            assert parsed["potential-bugs"]["active"] is True

    def test_detekt_config_preserves_existing_file(self) -> None:
        """An existing user detekt.yml is never overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "detekt.yml"
            existing.write_text("complexity:\n  active: false\n")

            self._generate(tmpdir)

            assert existing.read_text() == "complexity:\n  active: false\n"

    def test_detekt_config_documents_security_gap(self) -> None:
        """detekt.yml discloses that secret scanning lives in pre-commit.

        detekt has no dedicated security ruleset; the config must say
        where secret scanning actually happens instead of overclaiming.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "detekt.yml").read_text()
            assert "gitleaks" in content


class TestScriptsGeneratorCppGeneration:
    """Test C/C++ script generation (#362)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Generate cpp scripts into ``tmpdir`` and return the mapping."""
        config = ScriptConfig(
            language="cpp",
            package_name="my_watch_app",
        )
        generator = ScriptsGenerator(Path(tmpdir), config)
        return generator.generate()

    def test_generate_cpp_scripts_creates_files(self) -> None:
        """Test generate creates the full cpp script set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "security.sh" in scripts

    def test_cpp_format_script_uses_clang_format(self) -> None:
        """Test cpp format.sh uses clang-format against the shared config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            assert "clang-format -i" in content
            assert "clang-format --dry-run --Werror" in content
            assert ".clang-format" in content

    def test_cpp_format_script_covers_all_cpp_extensions(self) -> None:
        """format.sh finds every extension the pre-commit hook covers.

        The clang-format hook uses types_or c/c++ (covering .c/.cc/.cxx/
        .hh automatically); the standalone script's find must not
        silently skip those files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            for ext in ("*.c", "*.cc", "*.cpp", "*.cxx", "*.h", "*.hh", "*.hpp"):
                assert f"-name '{ext}'" in content, ext

    def test_cpp_shell_scripts_pass_bash_syntax_check(self) -> None:
        """Every generated cpp shell script parses under bash -n.

        Completes the parse-validation pattern: the templates embed
        run_check() with array expansions, so a literal syntax check
        guards against template-escaping regressions.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            for name, path in scripts.items():
                if not name.endswith(".sh"):
                    continue
                bash = shutil.which("bash")
                assert bash is not None, "bash not found on PATH"
                result = subprocess.run(  # noqa: S603  # Issue #362: bash -n on generated content, no untrusted input
                    [bash, "-n", str(path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, f"{name}: {result.stderr}"

    def test_cpp_lint_script_runs_full_static_analysis(self) -> None:
        """lint.sh runs clang-tidy, cppcheck, and the lizard CCN gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "clang-tidy" in content
            assert "cppcheck --enable=warning,performance,portability" in content
            assert "lizard --CCN" in content

    def test_cpp_lint_script_gates_complexity_at_10_in_one_place(self) -> None:
        """The CCN ceiling lives once, as MAX_CCN=10 in lint.sh.

        The companion .clang-tidy deliberately does not duplicate the
        bound via readability-function-cognitive-complexity; lizard owns
        the complexity gate (single source of truth).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "MAX_CCN=10" in content
            assert 'lizard --CCN "$MAX_CCN"' in content

    def test_cpp_lint_script_requires_compile_commands(self) -> None:
        """lint.sh fails with instructions when the build is unconfigured.

        clang-tidy needs build/compile_commands.json; the script must say
        how to produce it (the cmake configure step) instead of emitting
        a bare clang-tidy error.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "build/compile_commands.json" in content
            assert "conan install . --output-folder=build --build=missing" in content

    def test_cpp_test_script_runs_ctest(self) -> None:
        """Test cpp test.sh runs the Catch2 suite via CTest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "ctest --test-dir build" in content

    def test_cpp_test_script_enforces_90_percent_coverage(self) -> None:
        """Coverage mode rebuilds instrumented and gates at 90% via lcov.

        THRESHOLD=90 in test.sh is the single place the bound lives; the
        ENABLE_COVERAGE instrumentation option it toggles is defined in
        the generated CMakeLists.txt.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "THRESHOLD=90" in content
            assert "-DENABLE_COVERAGE=ON" in content
            assert "lcov --capture" in content

    def test_cpp_test_script_excludes_third_party_from_coverage(self) -> None:
        """The lcov data is narrowed to first-party src/ and inc/ sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert 'lcov --extract build/coverage.info "*/src/*" "*/inc/*"' in content

    def test_cpp_test_script_documents_main_cpp_coverage_limit(self) -> None:
        """test.sh discloses that the Tizen entry point is not measured.

        src/main.cpp needs the Tizen SDK and is outside the host build,
        so the coverage gate honestly excludes it rather than implying
        whole-project coverage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "src/main.cpp" in content
            assert "coverage denominator" in content

    def test_cpp_security_script_uses_flawfinder(self) -> None:
        """Test cpp security.sh runs flawfinder's dangerous-API scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "flawfinder --error-level=4" in content

    def test_cpp_security_script_warns_and_skips_when_tool_missing(self) -> None:
        """security.sh degrades to a warning when flawfinder is absent.

        Mirrors the Swift Periphery / Kotlin dependency-check precedent:
        a fresh clone must pass check-all.sh out of the box, with a
        documented tighten-me path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "command -v flawfinder" in content
            assert "pip install flawfinder" in content
            assert "Tighten" in content

    def test_cpp_security_script_documents_division_of_labor(self) -> None:
        """security.sh discloses where the other security passes live.

        cppcheck and the clang-analyzer checks run in lint.sh; secret
        scanning runs in pre-commit; scan-build is the documented
        tighten-me. The script must say so instead of overclaiming.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "gitleaks" in content
            assert "clang-analyzer" in content
            assert "scan-build" in content

    def test_cpp_check_all_runs_full_toolchain(self) -> None:
        """check-all.sh runs format, lint, tests (with coverage), security."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["check-all.sh"].read_text()
            assert 'run_check "Format" "format.sh"' in content
            assert 'run_check "Linting" "lint.sh"' in content
            assert 'run_check "Tests" "test.sh" --coverage' in content
            assert 'run_check "Security" "security.sh"' in content

    def test_cpp_writes_clang_config_companions(self) -> None:
        """.clang-format and .clang-tidy companions land at the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            assert (Path(tmpdir) / ".clang-format").exists()
            assert (Path(tmpdir) / ".clang-tidy").exists()

    def test_clang_format_config_is_parseable_yaml(self) -> None:
        """.clang-format must be syntactically valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".clang-format").read_text()
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, dict)
            assert parsed["BasedOnStyle"] == "Google"

    def test_clang_format_config_pins_the_cpp_standard(self) -> None:
        """.clang-format's Standard matches the CMakeLists C++ standard.

        Both interpolate utils.cpp.CPP_STANDARD, so the formatter and the
        compiler can never disagree about the language version.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".clang-format").read_text()
            parsed = yaml.safe_load(content)
            assert parsed["Standard"] == f"c++{CPP_STANDARD}"

    def test_clang_tidy_config_is_parseable_yaml(self) -> None:
        """.clang-tidy must be syntactically valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".clang-tidy").read_text()
            parsed = yaml.safe_load(content)
            assert isinstance(parsed, dict)

    def test_clang_tidy_config_promotes_warnings_to_errors(self) -> None:
        """.clang-tidy enables the analyzer checks and fails on findings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".clang-tidy").read_text()
            parsed = yaml.safe_load(content)
            assert parsed["WarningsAsErrors"] == "*"
            assert "clang-analyzer-*" in parsed["Checks"]
            assert "bugprone-*" in parsed["Checks"]

    def test_clang_tidy_config_documents_tighten_me_checks(self) -> None:
        """.clang-tidy discloses the deliberately deferred check groups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / ".clang-tidy").read_text()
            assert "Tighten-me" in content
            assert "cppcoreguidelines" in content

    def test_clang_config_companions_preserve_existing_files(self) -> None:
        """Existing user .clang-format/.clang-tidy are never overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_format = Path(tmpdir) / ".clang-format"
            existing_format.write_text("BasedOnStyle: LLVM\n")
            existing_tidy = Path(tmpdir) / ".clang-tidy"
            existing_tidy.write_text("Checks: bugprone-*\n")

            self._generate(tmpdir)

            assert existing_format.read_text() == "BasedOnStyle: LLVM\n"
            assert existing_tidy.read_text() == "Checks: bugprone-*\n"


class TestScriptsGeneratorJavaGeneration:
    """Test Java script generation (#367)."""

    @staticmethod
    def _generate(tmpdir: str) -> dict[str, Path]:
        """Generate java scripts into ``tmpdir`` and return the mapping."""
        config = ScriptConfig(
            language="java",
            package_name="my_wear_app",
        )
        generator = ScriptsGenerator(Path(tmpdir), config)
        return generator.generate()

    def test_generate_java_scripts_creates_files(self) -> None:
        """Test generate creates the full java script set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            assert "check-all.sh" in scripts
            assert "format.sh" in scripts
            assert "lint.sh" in scripts
            assert "test.sh" in scripts
            assert "security.sh" in scripts

    def test_java_shell_scripts_pass_bash_syntax_check(self) -> None:
        """Every generated java shell script parses under bash -n.

        The #362 lesson: this literal syntax check caught a real
        template-escaping bug in the cpp scripts, so every new language
        gets it from day one.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            for name, path in scripts.items():
                if not name.endswith(".sh"):
                    continue
                bash = shutil.which("bash")
                assert bash is not None, "bash not found on PATH"
                result = subprocess.run(  # noqa: S603  # Issue #367: bash -n on generated content, no untrusted input
                    [bash, "-n", str(path)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, f"{name}: {result.stderr}"

    def test_java_format_script_uses_google_java_format(self) -> None:
        """format.sh formats in place and verifies with --dry-run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            assert "google-java-format" in content
            assert "--replace" in content
            assert "--dry-run --set-exit-if-changed" in content

    def test_java_format_script_requires_the_formatter(self) -> None:
        """format.sh fails with install instructions when the tool is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["format.sh"].read_text()
            assert "command -v google-java-format" in content
            assert "brew install google-java-format" in content

    def test_java_lint_script_runs_pom_backed_goals(self) -> None:
        """lint.sh runs Checkstyle and PMD via the Maven goals the pom pins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "mvn -q checkstyle:check" in content
            assert "mvn -q pmd:check" in content

    def test_java_lint_script_requires_maven(self) -> None:
        """lint.sh fails with install instructions when mvn is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "command -v mvn" in content
            assert "brew install maven" in content

    def test_java_lint_script_documents_pmd_as_complexity_owner(self) -> None:
        """The CCN ceiling lives once, in the pmd-ruleset.xml companion.

        PMD's CyclomaticComplexity rule owns the <=10 gate (single
        source of truth); lint.sh and the script's help text must point
        at the companion ruleset rather than duplicating a threshold.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["lint.sh"].read_text()
            assert "pmd-ruleset.xml" in content
            assert "CyclomaticComplexity" in content
            # No shell-side duplicate of the bound.
            assert "MAX_CCN" not in content

    def test_java_test_script_runs_maven_tests(self) -> None:
        """test.sh runs the JUnit 4 suite via plain `mvn test`.

        The literal string `mvn test` doubles as the language marker
        cli._scripts_dir_has_other_language probes for java.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "mvn test" in content
            assert "command -v mvn" in content

    def test_java_test_script_enforces_coverage_via_pom_jacoco_gate(self) -> None:
        """Coverage mode runs the full lifecycle; the bound stays in the pom.

        ``mvn clean verify`` fires the pom's bound jacoco executions
        (prepare-agent -> report -> check) in order; invoking
        ``jacoco:check`` as a standalone goal can silently pass against
        an empty report. Unlike the cpp THRESHOLD=90 (CMake has no
        manifest home for the bound), the JaCoCo plugin rules in pom.xml
        are the single source of the coverage bound, so the script must
        not restate the number.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "mvn clean verify" in content
            # No standalone goal invocation remains in the command line
            # (the string may still appear in explanatory comments).
            assert "mvn clean test jacoco:report jacoco:check" not in content
            assert "pom.xml" in content
            assert "THRESHOLD=" not in content

    def test_java_test_script_documents_app_module_coverage_limit(self) -> None:
        """test.sh discloses that the Android app module is not measured.

        app/ needs the Android SDK and sits outside the Maven build, so
        the coverage gate honestly excludes it rather than implying
        whole-project coverage — the cpp src/main.cpp precedent.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["test.sh"].read_text()
            assert "app/" in content
            assert "coverage denominator" in content

    def test_java_security_script_compiles_before_spotbugs(self) -> None:
        """security.sh compiles before the SpotBugs bytecode scan.

        `mvn spotbugs:check` silently skips when target/classes is
        empty, so the script must run the compile phase first or the
        gate is a no-op.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "mvn -q compile spotbugs:check" in content

    def test_java_security_script_gates_dependency_check_on_nvd_key(self) -> None:
        """dependency-check runs only when an NVD API key is configured.

        The pom pins org.owasp:dependency-check-maven, so there is no
        binary to install — but without an NVD API key the NVD download
        is throttled to impracticality, so the pragmatic warn-first
        default skips the scan with a documented tighten-me path.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "NVD_API_KEY" in content
            assert "dependency-check:check" in content
            assert "Tighten" in content

    def test_java_security_script_documents_division_of_labor(self) -> None:
        """security.sh discloses where the other security passes live."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["security.sh"].read_text()
            assert "gitleaks" in content
            assert "detect-secrets" in content

    def test_java_check_all_runs_full_toolchain(self) -> None:
        """check-all.sh runs format, lint, tests (with coverage), security."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scripts = self._generate(tmpdir)

            content = scripts["check-all.sh"].read_text()
            assert 'run_check "Format" "format.sh"' in content
            assert 'run_check "Linting" "lint.sh"' in content
            assert 'run_check "Tests" "test.sh" --coverage' in content
            assert 'run_check "Security" "security.sh"' in content

    def test_java_writes_pmd_ruleset_companion(self) -> None:
        """The pmd-ruleset.xml companion lands at the project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            assert (Path(tmpdir) / "pmd-ruleset.xml").exists()

    def test_pmd_ruleset_is_well_formed_xml_with_ccn_rule(self) -> None:
        """pmd-ruleset.xml parses as XML and gates CCN at <=10.

        PMD reports methods whose complexity is >= methodReportLevel,
        so 11 reports 11+ and enforces the <=10 ceiling the other
        languages gate on (the detekt threshold: 11 precedent).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "pmd-ruleset.xml").read_text()
            root = DefusedElementTree.fromstring(content)
            assert root.tag.endswith("ruleset")
            assert "CyclomaticComplexity" in content
            assert 'value="11"' in content
            assert "methodReportLevel" in content

    def test_pmd_ruleset_documents_the_threshold_mapping(self) -> None:
        """The ruleset explains the report-at-11 == ceiling-10 mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            self._generate(tmpdir)

            content = (Path(tmpdir) / "pmd-ruleset.xml").read_text()
            assert "<= 10" in content

    def test_pmd_ruleset_preserves_existing_file(self) -> None:
        """An existing user pmd-ruleset.xml is never overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            existing = Path(tmpdir) / "pmd-ruleset.xml"
            existing.write_text("<ruleset />\n")

            self._generate(tmpdir)

            assert existing.read_text() == "<ruleset />\n"


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

    def test_script_generation_with_valid_package_names(self) -> None:
        """Test script generation with valid package names."""
        valid_names = [
            "my_package",
            "MyPackage",
            "MYPACKAGE",
            "pkg123",
        ]

        for package_name in valid_names:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = ScriptConfig(
                    language="python",
                    package_name=package_name,
                )
                generator = ScriptsGenerator(Path(tmpdir), config)
                scripts = generator.generate()
                assert scripts

    def test_script_generation_rejects_unsafe_package_names(self) -> None:
        """Test that package names with shell-unsafe chars are rejected."""
        unsafe_names = [
            "my-package",
            "my.package",
            "pkg;rm -rf",
            "$(whoami)",
        ]

        for package_name in unsafe_names:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = ScriptConfig(
                    language="python",
                    package_name=package_name,
                )
                with pytest.raises(
                    ValueError,
                    match="Package name must contain only",
                ):
                    ScriptsGenerator(Path(tmpdir), config)

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

    def test_swift_language_dispatches_to_swift_generator(self) -> None:
        """Test 'swift' language dispatches to Swift generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="swift",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate Swift scripts with SwiftLint
            content = scripts["lint.sh"].read_text()
            assert "swiftlint" in content

    def test_kotlin_language_dispatches_to_kotlin_generator(self) -> None:
        """Test 'kotlin' language dispatches to Kotlin generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="kotlin",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate Kotlin scripts with detekt
            content = scripts["lint.sh"].read_text()
            assert "detekt" in content

    def test_cpp_language_dispatches_to_cpp_generator(self) -> None:
        """Test 'cpp' language dispatches to the C/C++ generator."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="cpp",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate cpp scripts with clang-tidy
            content = scripts["lint.sh"].read_text()
            assert "clang-tidy" in content

    def test_java_language_dispatches_to_java_generator(self) -> None:
        """Test 'java' language dispatches to the Java generator (#367)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="java",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            # Should generate java scripts with the pom-backed goals
            content = scripts["lint.sh"].read_text()
            assert "checkstyle:check" in content

    def test_generated_scripts_exact_count_python(self) -> None:
        """Test Python generator creates EXACTLY 12 scripts.

        Kills mutations in script count logic.
        Scripts: check-all, format, lint, test, fix-all, security, complexity,
        mutation, analyze_mutations.py, typecheck, coverage, pr-status
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 12
            assert len(scripts) > 11
            assert len(scripts) < 13

    def test_generated_scripts_exact_count_cpp(self) -> None:
        """Test C/C++ generator creates EXACTLY 6 scripts.

        Kills mutations in script count logic and catches silent script
        additions/removals. Scripts: check-all, format, lint, test,
        security, pr-status (companion configs .clang-format/.clang-tidy
        are written separately and not counted here).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="cpp",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 6
            assert sorted(scripts) == [
                "check-all.sh",
                "format.sh",
                "lint.sh",
                "pr-status.sh",
                "security.sh",
                "test.sh",
            ]

    def test_generated_scripts_exact_count_java(self) -> None:
        """Test Java generator creates EXACTLY 6 scripts (#367).

        Kills mutations in script count logic and catches silent script
        additions/removals. Scripts: check-all, format, lint, test,
        security, pr-status (the pmd-ruleset.xml companion is written
        separately and not counted here).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="java",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 6
            assert sorted(scripts) == [
                "check-all.sh",
                "format.sh",
                "lint.sh",
                "pr-status.sh",
                "security.sh",
                "test.sh",
            ]

    def test_generated_scripts_exact_count_typescript(self) -> None:
        """Test TypeScript generator creates EXACTLY 6 scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="test",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert len(scripts) == 7
            assert len(scripts) > 6
            assert len(scripts) < 8

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

    def test_pr_status_script_generated_for_typescript(self) -> None:
        """Test pr-status.sh is included in TypeScript generated scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="typescript",
                package_name="my_app",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "pr-status.sh" in scripts

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


class TestPrStatusScript:
    """Test pr-status.sh script generation (language-agnostic)."""

    def test_pr_status_script_generated_for_python(self) -> None:
        """Test pr-status.sh is included in Python generated scripts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            assert "pr-status.sh" in scripts
            assert scripts["pr-status.sh"].exists()

    def test_pr_status_script_generated_for_all_languages(self) -> None:
        """Test pr-status.sh is generated for all supported languages."""
        languages = ["python", "typescript", "go", "rust", "swift"]
        for lang in languages:
            with tempfile.TemporaryDirectory() as tmpdir:
                config = ScriptConfig(
                    language=lang,
                    package_name="test_pkg",
                )
                generator = ScriptsGenerator(Path(tmpdir), config)
                scripts = generator.generate()

                assert "pr-status.sh" in scripts, f"Missing for {lang}"

    def test_pr_status_script_has_subcommands(self) -> None:
        """Test pr-status.sh contains all subcommand case patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "list)" in content
            assert "view)" in content
            assert "watch)" in content
            assert "checks)" in content
            assert "status)" in content

    def test_pr_status_script_is_executable(self) -> None:
        """Test pr-status.sh has executable permissions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            script_path = scripts["pr-status.sh"]
            assert script_path.stat().st_mode & 0o111

    def test_pr_status_script_has_version_flag(self) -> None:
        """Test pr-status.sh supports --version flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "--version)" in content
            assert "VERSION=" in content

    def test_pr_status_script_has_bash_safety(self) -> None:
        """Test pr-status.sh has set -euo pipefail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "set -euo pipefail" in content
            assert "#!/usr/bin/env bash" in content

    def test_pr_status_script_has_help_text(self) -> None:
        """Test pr-status.sh has comprehensive help output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "SUBCOMMANDS:" in content
            assert "EXAMPLES:" in content
            assert "EXIT CODES:" in content
            assert "--help" in content

    def test_pr_status_script_has_claude_review_parsing(self) -> None:
        """Test pr-status.sh status subcommand parses Claude review verdicts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "LGTM" in content
            assert "CHANGES_REQUESTED" in content
            assert "Verdict:" in content
            assert "READY TO MERGE" in content

    def test_pr_status_script_defaults_to_ci_yml_workflow(self) -> None:
        """Test pr-status.sh defaults to ci.yml for workflow filename."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_package",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert 'workflow="ci.yml"' in content

    def test_pr_status_script_interpolates_package_name(self) -> None:
        """Test pr-status.sh includes the project package name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(
                language="python",
                package_name="my_special_project",
            )
            generator = ScriptsGenerator(Path(tmpdir), config)
            scripts = generator.generate()

            content = scripts["pr-status.sh"].read_text()
            assert "my_special_project" in content
