"""Tests for multi-language --language support in green init.

Tests that multiple --language flags generate infrastructure for
all specified languages, and that single language still works.
"""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from rich.console import Console

from start_green_stay_green import cli as cli_mod
from start_green_stay_green.cli import _generate_project_files
from start_green_stay_green.cli import _generate_scripts_step
from start_green_stay_green.cli import _resolve_language_param
from start_green_stay_green.cli import _resolve_languages
from start_green_stay_green.cli import _scripts_dir_has_other_language
from start_green_stay_green.utils.file_writer import FileWriter

_STEP_NAMES = [
    "_generate_pass2_polish",
    "_generate_skills_step",
    "_generate_precommit_step",
    "_generate_scripts_step",
    "_generate_readme_step",
    "_generate_tests_step",
    "_generate_dependencies_step",
    "_generate_structure_step",
]

_CLI_MODULE = "start_green_stay_green.cli"


def _patch_all_steps() -> Any:
    """Create patch.multiple with fresh MagicMocks for all generation steps."""
    return patch.multiple(
        _CLI_MODULE,
        **{name: MagicMock() for name in _STEP_NAMES},
    )


def _get_mock(name: str) -> Any:
    """Get the current mock for a patched CLI step by name.

    Args:
        name: Name of the patched function (e.g. "_generate_structure_step").

    Returns:
        The MagicMock currently patching that function.
    """
    return vars(cli_mod)[name]


class TestResolveLanguages:
    """Test _resolve_languages helper."""

    def test_single_language_string(self) -> None:
        """Test single language string returns tuple with one element."""
        result = _resolve_languages(("python",))
        assert result == ("python",)

    def test_multiple_languages(self) -> None:
        """Test multiple languages returned as tuple."""
        result = _resolve_languages(("python", "typescript"))
        assert result == ("python", "typescript")

    def test_invalid_language_raises(self) -> None:
        """Test invalid language in list raises ValueError."""
        with pytest.raises(ValueError, match="brainfuck"):
            _resolve_languages(("python", "brainfuck"))

    def test_empty_tuple_raises(self) -> None:
        """Test empty tuple raises ValueError."""
        with pytest.raises(ValueError, match=r"[Aa]t least one language"):
            _resolve_languages(())

    def test_deduplicates(self) -> None:
        """Test duplicate languages are removed."""
        result = _resolve_languages(("python", "python", "go"))
        assert result == ("python", "go")


class TestCommaDelimitedLanguages:
    """Test comma-separated language parsing (#261)."""

    def test_comma_separated_split(self) -> None:
        """Test 'python,go' is split into two languages."""
        result = _resolve_language_param(["python,go"], {}, no_interactive=True)
        assert result == ("python", "go")

    def test_comma_with_spaces(self) -> None:
        """Test 'python, go' with spaces is handled."""
        result = _resolve_language_param(["python, go"], {}, no_interactive=True)
        assert result == ("python", "go")

    def test_mixed_comma_and_repeated(self) -> None:
        """Test mixing comma-separated and repeated flags."""
        result = _resolve_language_param(["python,go", "rust"], {}, no_interactive=True)
        assert result == ("python", "go", "rust")

    def test_single_language_no_comma(self) -> None:
        """Test single language without comma still works."""
        result = _resolve_language_param(["python"], {}, no_interactive=True)
        assert result == ("python",)


class TestMultiLanguageGeneration:
    """Test _generate_project_files with multiple languages."""

    def test_multi_language_calls_per_language_steps(self) -> None:
        """Test multi-language calls per-language generators for each."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(),
                "my-project",
                ("python", "typescript"),
                None,
                MagicMock(),
            )

            assert _get_mock("_generate_structure_step").call_count == 2
            assert _get_mock("_generate_dependencies_step").call_count == 2
            assert _get_mock("_generate_tests_step").call_count == 2
            assert _get_mock("_generate_scripts_step").call_count == 2
            assert _get_mock("_generate_precommit_step").call_count == 2

            # Shared steps called once (not per-language)
            _get_mock("_generate_readme_step").assert_called_once()
            _get_mock("_generate_skills_step").assert_called_once()
            _get_mock("_generate_pass2_polish").assert_called_once()

    def test_single_language_backward_compatible(self) -> None:
        """Test single language works identically to before."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python",), None, MagicMock()
            )

            _get_mock("_generate_scripts_step").assert_called_once()
            _get_mock("_generate_precommit_step").assert_called_once()
            _get_mock("_generate_skills_step").assert_called_once()

    def test_per_language_steps_receive_correct_language(self) -> None:
        """Test each per-language step gets the correct language arg."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python", "go"), None, MagicMock()
            )

            calls = _get_mock("_generate_structure_step").call_args_list
            assert calls[0][0][2] == "python"
            assert calls[1][0][2] == "go"


class TestMultiLanguageArchitectureParity:
    """Go (#341), Rust (#342), Swift (#352), Kotlin (#357), cpp (#362)."""

    def test_go_exercises_architecture_enforcement(self, tmp_path: Path) -> None:
        """Go must emit an architecture-enforcement config like py/ts."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "go")

        config = tmp_path / "plans" / "architecture" / ".go-arch-lint.yml"
        assert config.exists(), "Go init must emit a go-arch-lint config"

    def test_rust_exercises_architecture_enforcement(self, tmp_path: Path) -> None:
        """Rust must emit an architecture-enforcement config like py/ts/go."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "rust")

        config = tmp_path / "plans" / "architecture" / "deny.toml"
        assert config.exists(), "Rust init must emit a cargo-deny config"

    def test_swift_exercises_architecture_enforcement(self, tmp_path: Path) -> None:
        """Swift must emit an architecture-enforcement config like py/ts/go."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "swift")

        config = tmp_path / "plans" / "architecture" / ".swiftlint-architecture.yml"
        assert config.exists(), "Swift init must emit a SwiftLint rules config"

    def test_kotlin_exercises_architecture_enforcement(self, tmp_path: Path) -> None:
        """Kotlin must emit an architecture-enforcement config like py/ts/go."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "kotlin")

        config = tmp_path / "plans" / "architecture" / "ArchitectureTest.kt"
        assert config.exists(), "Kotlin init must emit a Konsist test template"

    def test_cpp_exercises_architecture_enforcement(self, tmp_path: Path) -> None:
        """cpp must emit an architecture-enforcement config like py/ts/go."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "cpp")

        config = tmp_path / "plans" / "architecture" / "check_architecture.py"
        assert config.exists(), "cpp init must emit the include-boundary checker"

    @pytest.mark.parametrize(
        "language", ["python", "typescript", "go", "rust", "swift", "kotlin", "cpp"]
    )
    def test_supported_languages_emit_architecture_config(
        self, tmp_path: Path, language: str
    ) -> None:
        """Every supported language produces architecture rules."""
        project = tmp_path / language
        cli_mod._generate_architecture_step(project, "my-project", language)

        arch_dir = project / "plans" / "architecture"
        assert (arch_dir / "README.md").exists()
        assert (arch_dir / "run-check.sh").exists()


class TestMultiLanguageScriptsDir:
    """Test multi-language scripts use subdirectories (#262)."""

    def test_multi_language_scripts_get_subdirectories(self) -> None:
        """Test scripts_step receives subdirectory for each language."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python", "go"), None, MagicMock()
            )

            calls = _get_mock("_generate_scripts_step").call_args_list
            assert len(calls) == 2
            # Both get subdirectory=language for multi-language
            assert calls[0].kwargs.get("subdirectory") == "python"
            assert calls[1].kwargs.get("subdirectory") == "go"

    def test_single_language_no_subdirectory(self) -> None:
        """Test single language scripts go to scripts/ (no subdirectory)."""
        with _patch_all_steps():
            _generate_project_files(
                MagicMock(), "my-project", ("python",), None, MagicMock()
            )

            calls = _get_mock("_generate_scripts_step").call_args_list
            assert len(calls) == 1
            assert calls[0].kwargs.get("subdirectory") is None


class TestSequentialLanguageDetection:
    """Test auto-detection of other language scripts for sequential runs."""

    def test_detects_go_scripts_when_adding_python(self, tmp_path: Path) -> None:
        """Test Go test.sh is detected as different from Python."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\ngo test ./...\n")

        assert _scripts_dir_has_other_language(scripts_dir, "python")

    def test_detects_python_scripts_when_adding_go(self, tmp_path: Path) -> None:
        """Test Python test.sh is detected as different from Go."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\npytest tests/\n")

        assert _scripts_dir_has_other_language(scripts_dir, "go")

    def test_same_language_returns_false(self, tmp_path: Path) -> None:
        """Test same language scripts are not detected as different."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\npytest tests/\n")

        assert not _scripts_dir_has_other_language(scripts_dir, "python")

    def test_no_scripts_dir_returns_false(self, tmp_path: Path) -> None:
        """Test missing scripts dir returns False."""
        assert not _scripts_dir_has_other_language(tmp_path / "scripts", "python")

    def test_empty_scripts_dir_returns_false(self, tmp_path: Path) -> None:
        """Test empty scripts dir returns False."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()

        assert not _scripts_dir_has_other_language(scripts_dir, "python")

    def test_java_marker_detected(self, tmp_path: Path) -> None:
        """Test Java scripts detected when adding Python."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\nmvn test\n")

        assert _scripts_dir_has_other_language(scripts_dir, "python")

    def test_csharp_marker_detected(self, tmp_path: Path) -> None:
        """Test C# scripts detected when adding Go."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\ndotnet test\n")

        assert _scripts_dir_has_other_language(scripts_dir, "go")

    def test_ruby_marker_detected(self, tmp_path: Path) -> None:
        """Test Ruby scripts detected when adding TypeScript."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test.sh").write_text("#!/bin/bash\nrspec spec/\n")

        assert _scripts_dir_has_other_language(scripts_dir, "typescript")

    def test_subdirectory_created_for_second_language(self, tmp_path: Path) -> None:
        """Integration: sequential init creates scripts subdirectory."""
        project = tmp_path / "myproject"
        project.mkdir()
        writer = FileWriter(project_root=project, console=Console(quiet=True))

        # First language: scripts go to scripts/
        _generate_scripts_step(project, "myproject", "go", writer)
        assert (project / "scripts" / "test.sh").exists()
        assert "go test" in (project / "scripts" / "test.sh").read_text()

        # Second language: auto-detects and uses scripts/python/
        _generate_scripts_step(project, "myproject", "python", writer)
        assert (project / "scripts" / "python" / "test.sh").exists()
        assert "pytest" in (project / "scripts" / "python" / "test.sh").read_text()


class TestGeneratorOnlyLanguagePipelineGates:
    """Pipeline steps skip gracefully for generator-only languages (#356).

    java/csharp/ruby have structure/dependencies/tests/readme generators
    but no quality-tooling support — instead of crashing init, the tooling
    steps must no-op with an informational message. Kotlin graduated from
    this set when #357 wired its pre-commit/scripts/metrics/architecture
    tooling and #358 wired its CI workflow.
    """

    def test_precommit_step_writes_for_kotlin(self, tmp_path: Path) -> None:
        """Kotlin now generates a pre-commit config (#357)."""
        cli_mod._generate_precommit_step(tmp_path, "my-project", "kotlin")

        config = tmp_path / ".pre-commit-config.yaml"
        assert config.exists()
        assert "ktlint" in config.read_text()

    def test_precommit_step_skips_ruby_without_writing(self, tmp_path: Path) -> None:
        """No .pre-commit-config.yaml is written and no error is raised."""
        cli_mod._generate_precommit_step(tmp_path, "my-project", "ruby")

        assert not (tmp_path / ".pre-commit-config.yaml").exists()

    def test_precommit_step_still_writes_for_python(self, tmp_path: Path) -> None:
        """Supported languages keep generating the pre-commit config."""
        cli_mod._generate_precommit_step(tmp_path, "my-project", "python")

        assert (tmp_path / ".pre-commit-config.yaml").exists()

    def test_scripts_step_writes_kotlin_scripts(self, tmp_path: Path) -> None:
        """Kotlin now receives its own quality scripts (#357)."""
        cli_mod._generate_scripts_step(tmp_path, "my-project", "kotlin")

        test_script = tmp_path / "scripts" / "test.sh"
        assert test_script.exists()
        assert "gradlew" in test_script.read_text()

    def test_scripts_step_skips_ruby_without_python_fallback(
        self, tmp_path: Path
    ) -> None:
        """Ruby must not receive the Python-fallback quality scripts."""
        cli_mod._generate_scripts_step(tmp_path, "my-project", "ruby")

        assert not (tmp_path / "scripts").exists()

    def test_ci_step_writes_kotlin_workflow(self, tmp_path: Path) -> None:
        """The kotlin CI workflow is now generated (#358)."""
        cli_mod._generate_ci_step(tmp_path, "my-project", "kotlin", None)

        ci_file = tmp_path / ".github" / "workflows" / "ci.yml"
        assert ci_file.exists()
        assert "Kotlin Quality Checks" in ci_file.read_text()

    def test_metrics_step_writes_kotlin_dashboard(self, tmp_path: Path) -> None:
        """The metrics dashboard is now generated for kotlin (#357)."""
        cli_mod._generate_metrics_dashboard_step(tmp_path, "my-project", "kotlin")

        assert (tmp_path / "docs" / "metrics.json").exists()

    def test_metrics_step_skips_ruby_without_dashboard(self, tmp_path: Path) -> None:
        """No metrics dashboard is written for unsupported languages."""
        cli_mod._generate_metrics_dashboard_step(tmp_path, "my-project", "ruby")

        assert not (tmp_path / "docs" / "metrics.json").exists()

    def test_architecture_step_writes_kotlin_rules(self, tmp_path: Path) -> None:
        """Architecture rules are now generated for kotlin (#357)."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "kotlin")

        assert (tmp_path / "plans" / "architecture" / "ArchitectureTest.kt").exists()

    def test_architecture_step_skips_ruby(self, tmp_path: Path) -> None:
        """No architecture rules are generated for unsupported languages."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "ruby")

        assert not (tmp_path / "plans" / "architecture").exists()


class TestCppPipelineGates:
    """Pipeline steps all run for cpp after #362/#363.

    The #361 foundation shipped structure/dependencies/tests/readme only;
    #362 wired the pre-commit/scripts/metrics/architecture tooling and
    #363 completed the pipeline with the CI workflow, so every step must
    now generate real artifacts.
    """

    def test_precommit_step_writes_for_cpp(self, tmp_path: Path) -> None:
        """cpp now generates a pre-commit config (#362)."""
        cli_mod._generate_precommit_step(tmp_path, "my-project", "cpp")

        config = tmp_path / ".pre-commit-config.yaml"
        assert config.exists()
        assert "clang-tidy" in config.read_text()

    def test_scripts_step_writes_cpp_scripts(self, tmp_path: Path) -> None:
        """cpp now receives its own quality scripts (#362)."""
        cli_mod._generate_scripts_step(tmp_path, "my-project", "cpp")

        test_script = tmp_path / "scripts" / "test.sh"
        assert test_script.exists()
        assert "ctest" in test_script.read_text()

    def test_scripts_step_writes_clang_companions_at_project_root(
        self, tmp_path: Path
    ) -> None:
        """The .clang-format/.clang-tidy companions land at the root.

        The pre-commit hooks and the format/lint scripts resolve these
        files relative to the project root, not the scripts directory.
        """
        cli_mod._generate_scripts_step(tmp_path, "my-project", "cpp")

        assert (tmp_path / ".clang-format").exists()
        assert (tmp_path / ".clang-tidy").exists()

    def test_ci_step_writes_cpp_workflow(self, tmp_path: Path) -> None:
        """ci.yml is now generated for cpp (#363)."""
        cli_mod._generate_ci_step(tmp_path, "my-project", "cpp", None)

        ci_file = tmp_path / ".github" / "workflows" / "ci.yml"
        assert ci_file.exists()
        assert "C/C++ Quality Checks" in ci_file.read_text()

    def test_metrics_step_writes_cpp_dashboard(self, tmp_path: Path) -> None:
        """The metrics dashboard is now generated for cpp (#362)."""
        cli_mod._generate_metrics_dashboard_step(tmp_path, "my-project", "cpp")

        assert (tmp_path / "docs" / "metrics.json").exists()

    def test_architecture_step_writes_cpp_rules(self, tmp_path: Path) -> None:
        """Architecture rules are now generated for cpp (#362)."""
        cli_mod._generate_architecture_step(tmp_path, "my-project", "cpp")

        checker = tmp_path / "plans" / "architecture" / "check_architecture.py"
        assert checker.exists()
