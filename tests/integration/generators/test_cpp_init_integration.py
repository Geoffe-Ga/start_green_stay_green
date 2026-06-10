"""Integration tests for ``sgsg init --language cpp`` (#361/#362).

Runs the full init flow once via the Typer CliRunner and asserts the
generated C/C++ (Tizen native watch-app) project tree and the CMake/Conan
manifest contents. The AI orchestrator is patched to ``None`` so no real
Anthropic API calls are made (Issue #196); the null keyring backend is
enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke a C++ toolchain,
CMake, Conan, or Tizen Studio — so they pass on CI runners where none of
those are installed, mirroring ``test_kotlin_init_integration.py`` (#356).

With #362 the quality toolchain (pre-commit config, quality scripts,
clang companion configs, architecture rules) is generated for C/C++;
only the CI workflow remains deferred (#363), so this suite locks in
the presence of the tooling artifacts and the *absence* of ci.yml.
"""

from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as DefusedElementTree
import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.utils.cpp import tizen_app_id

# Project name chosen to exercise the hyphen sanitization paths:
# watch-timer -> app ID org.example.watchtimer, namespace watch_timer.
_PROJECT_NAME = "watch-timer"
_APP_ID = tizen_app_id("watch_timer")


@pytest.fixture(scope="module")
def cpp_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language cpp`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("cpp-init")
    runner = CliRunner()
    with patch(
        "start_green_stay_green.cli._initialize_orchestrator", return_value=None
    ):
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                _PROJECT_NAME,
                "--language",
                "cpp",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for cpp: {result.output}"
    return output_dir / _PROJECT_NAME


class TestCppInitTree:
    """Assert the generated Tizen native watch-app project tree."""

    def test_project_directory_created(self, cpp_project: Path) -> None:
        """Init creates the project directory."""
        assert cpp_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            "CMakeLists.txt",
            "conanfile.txt",
            "tizen-manifest.xml",
            "src/main.cpp",
            "src/greeting.cpp",
            "inc/greeting.h",
            "res/README.md",
            "shared/res/README.md",
            "tests/test_greeting.cpp",
            "README.md",
        ],
    )
    def test_expected_file_generated(
        self, cpp_project: Path, relative_path: str
    ) -> None:
        """Every expected cpp project file exists and is non-empty."""
        file_path = cpp_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # Quality tooling (#362) is now generated alongside the
            # foundation scaffold.
            ".pre-commit-config.yaml",
            ".clang-format",
            ".clang-tidy",
            "scripts/check-all.sh",
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/test.sh",
            "scripts/security.sh",
            "plans/architecture/check_architecture.py",
            "plans/architecture/run-check.sh",
        ],
    )
    def test_quality_tooling_artifact_generated(
        self, cpp_project: Path, relative_path: str
    ) -> None:
        """#362 quality-tooling artifacts exist and are non-empty."""
        file_path = cpp_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # CI is #363 — it must not be generated yet.
            ".github/workflows/ci.yml",
            # The metrics dashboard is opt-in (--enable-live-dashboard).
            "docs/metrics.json",
            # Tizen Studio project/packaging artifacts and icon binaries
            # must never be scaffolded.
            ".tproject",
            "shared/res/watch_timer.png",
        ],
    )
    def test_out_of_scope_artifact_not_generated(
        self, cpp_project: Path, relative_path: str
    ) -> None:
        """The scaffold must not emit #363 artifacts or Tizen binaries."""
        assert not (cpp_project / relative_path).exists()


class TestCppInitQualityTooling:
    """Assert the generated quality-tooling configs are valid (#362)."""

    def test_precommit_config_parses_and_includes_cpp_hooks(
        self, cpp_project: Path
    ) -> None:
        """.pre-commit-config.yaml parses and wires the C/C++ linters."""
        content = (cpp_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        local_repo = next(
            repo for repo in parsed["repos"] if repo.get("repo") == "local"
        )
        hook_ids = {hook["id"] for hook in local_repo["hooks"]}
        assert {"clang-tidy", "cppcheck"} <= hook_ids
        repo_urls = [repo.get("repo", "") for repo in parsed["repos"]]
        assert any("mirrors-clang-format" in url for url in repo_urls)

    def test_clang_configs_parse_as_yaml(self, cpp_project: Path) -> None:
        """.clang-format and .clang-tidy parse and gate as configured."""
        clang_format = yaml.safe_load((cpp_project / ".clang-format").read_text())
        assert clang_format["BasedOnStyle"] == "Google"

        clang_tidy = yaml.safe_load((cpp_project / ".clang-tidy").read_text())
        assert clang_tidy["WarningsAsErrors"] == "*"

    def test_check_all_script_runs_the_cpp_toolchain(self, cpp_project: Path) -> None:
        """check-all.sh chains format, lint, coverage-gated tests, security."""
        content = (cpp_project / "scripts" / "check-all.sh").read_text()
        assert 'run_check "Tests" "test.sh" --coverage' in content

    def test_architecture_checker_defines_the_layer_matrix(
        self, cpp_project: Path
    ) -> None:
        """The include-boundary checker carries the editable matrix."""
        source = (
            cpp_project / "plans" / "architecture" / "check_architecture.py"
        ).read_text()
        assert "ALLOWED_DEPENDENCIES" in source

    def test_cmakelists_wires_the_coverage_option(self, cpp_project: Path) -> None:
        """CMakeLists.txt carries the ENABLE_COVERAGE instrumentation."""
        cmake = (cpp_project / "CMakeLists.txt").read_text()
        assert "option(ENABLE_COVERAGE" in cmake
        assert "set(CMAKE_EXPORT_COMPILE_COMMANDS ON)" in cmake


class TestCppInitManifests:
    """Assert the generated CMake/Conan manifests and tizen-manifest.xml."""

    def test_cmakelists_names_project_and_test_target(self, cpp_project: Path) -> None:
        """CMakeLists.txt wires the sanitized project and Catch2 tests."""
        cmake = (cpp_project / "CMakeLists.txt").read_text()
        assert "project(watch_timer VERSION 0.1.0 LANGUAGES CXX)" in cmake
        assert "add_library(greeting src/greeting.cpp)" in cmake
        assert "catch_discover_tests(greeting_tests)" in cmake

    def test_cmakelists_documents_tizen_studio_split(self, cpp_project: Path) -> None:
        """The CMake build discloses that .tpk packaging is Tizen Studio's."""
        cmake = (cpp_project / "CMakeLists.txt").read_text()
        assert "Tizen Studio" in cmake
        assert "tizen build-native" in cmake

    def test_conanfile_requires_catch2(self, cpp_project: Path) -> None:
        """conanfile.txt manages the Catch2 test dependency."""
        conanfile = (cpp_project / "conanfile.txt").read_text()
        assert "[requires]" in conanfile
        assert "catch2/" in conanfile
        assert "CMakeToolchain" in conanfile

    def test_tizen_manifest_is_well_formed_xml(self, cpp_project: Path) -> None:
        """tizen-manifest.xml parses as XML with a manifest root."""
        manifest_path = cpp_project / "tizen-manifest.xml"
        root = DefusedElementTree.fromstring(manifest_path.read_text())
        assert root.tag == "{http://tizen.org/ns/packages}manifest"

    def test_tizen_manifest_declares_wearable_watch_application(
        self, cpp_project: Path
    ) -> None:
        """The manifest declares the wearable profile and watch app."""
        manifest = (cpp_project / "tizen-manifest.xml").read_text()
        assert '<profile name="wearable" />' in manifest
        assert f'appid="{_APP_ID}"' in manifest
        assert "http://tizen.org/feature/watch_app" in manifest


class TestCppInitSources:
    """Assert the generated C++ source and test files."""

    def test_main_uses_tizen_watch_app_lifecycle(self, cpp_project: Path) -> None:
        """src/main.cpp hosts the appcore watch_app + EFL entry point."""
        source = (cpp_project / "src" / "main.cpp").read_text()
        assert "#include <watch_app.h>" in source
        assert "#include <Elementary.h>" in source
        assert 'watch_timer::format_greeting("watch-timer")' in source

    def test_pure_logic_unit_is_tizen_free(self, cpp_project: Path) -> None:
        """The greeting translation unit has no Tizen dependencies."""
        header = (cpp_project / "inc" / "greeting.h").read_text()
        impl = (cpp_project / "src" / "greeting.cpp").read_text()
        assert "namespace watch_timer {" in header
        assert '"Hello from " + project_name + "!"' in impl
        for content in (header, impl):
            assert "watch_app" not in content
            assert "Elementary" not in content

    def test_generated_test_uses_catch2_against_format_greeting(
        self, cpp_project: Path
    ) -> None:
        """The Catch2 scaffold exercises the format_greeting logic."""
        source = (cpp_project / "tests" / "test_greeting.cpp").read_text()
        assert "#include <catch2/catch_test_macros.hpp>" in source
        assert f'watch_timer::format_greeting("{_PROJECT_NAME}")' in source
        assert f'"Hello from {_PROJECT_NAME}!"' in source


class TestCppInitReadme:
    """Assert the generated README stays truthful (#361 boundaries)."""

    def test_readme_targets_tizen_galaxy_watch(self, cpp_project: Path) -> None:
        """README documents the Tizen native Galaxy Watch scaffold."""
        readme = (cpp_project / "README.md").read_text()
        assert "Tizen" in readme
        assert "Galaxy Watch" in readme

    def test_readme_discloses_planned_tooling(self, cpp_project: Path) -> None:
        """README lists the deferred CI pipeline (#363) as planned."""
        readme = (cpp_project / "README.md").read_text()
        assert "Planned / coming soon" in readme
        assert "CI/CD pipeline" in readme

    def test_readme_documents_tizen_studio_packaging_gap(
        self, cpp_project: Path
    ) -> None:
        """README explains that .tpk packaging needs Tizen Studio."""
        readme = (cpp_project / "README.md").read_text()
        assert "Tizen Studio" in readme
        assert ".tpk" in readme


class TestCppInitConsoleOutput:
    """Assert init's console output reflects the #362 wiring."""

    def test_init_skips_only_the_ci_step(self, tmp_path: Path) -> None:
        """Init prints the dim skip line for CI (#363) and nothing else.

        The pre-commit, scripts, and architecture steps gained cpp
        support with #362, so their skip notices must be gone.
        """
        runner = CliRunner()
        with patch(
            "start_green_stay_green.cli._initialize_orchestrator",
            return_value=None,
        ):
            result = runner.invoke(
                app,
                [
                    "init",
                    "--project-name",
                    "skip-check",
                    "--language",
                    "cpp",
                    "--output-dir",
                    str(tmp_path),
                    "--no-interactive",
                ],
            )
        assert result.exit_code == 0
        assert "CI pipeline unavailable for cpp" in result.output
        assert "Pre-commit config unavailable for cpp" not in result.output
        assert "Quality scripts unavailable for cpp" not in result.output
        assert "Architecture rules unavailable for cpp" not in result.output
