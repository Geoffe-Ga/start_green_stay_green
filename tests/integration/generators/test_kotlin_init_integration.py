"""Integration tests for ``sgsg init --language kotlin`` (#356).

Runs the full init flow once via the Typer CliRunner and asserts the
generated Kotlin (Wear OS) project tree and the Gradle (Kotlin DSL)
manifest contents. The AI orchestrator is patched to ``None`` so no real
Anthropic API calls are made (Issue #196); the null keyring backend is
enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke the Kotlin/Gradle
toolchain — so they pass on CI runners where the Android SDK and Gradle
are not installed, mirroring ``test_swift_init_integration.py`` (#354).

With #357 the quality toolchain (pre-commit config, quality scripts,
metrics dashboard, architecture rules) landed, and with #358 the CI
workflow (.github/workflows/ci.yml) is generated too, so this suite
locks in the presence of all tooling artifacts; only the wrapper
binaries remain forbidden output.
"""

from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as DefusedElementTree
import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.utils.java import android_package_path

# Project name chosen to exercise the hyphen-to-underscore Android
# package conversion (wear-timer -> com.example.wear_timer).
_PROJECT_NAME = "wear-timer"
_PACKAGE_PATH = android_package_path("wear_timer")


@pytest.fixture(scope="module")
def kotlin_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language kotlin`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("kotlin-init")
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
                "kotlin",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for kotlin: {result.output}"
    return output_dir / _PROJECT_NAME


class TestKotlinInitTree:
    """Assert the generated Kotlin Wear OS project tree."""

    def test_project_directory_created(self, kotlin_project: Path) -> None:
        """Init creates the project directory."""
        assert kotlin_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            "settings.gradle.kts",
            "build.gradle.kts",
            "gradle.properties",
            "app/build.gradle.kts",
            "app/src/main/AndroidManifest.xml",
            f"app/src/main/kotlin/{_PACKAGE_PATH}/MainActivity.kt",
            f"app/src/test/kotlin/{_PACKAGE_PATH}/GreetingTest.kt",
            "README.md",
        ],
    )
    def test_expected_file_generated(
        self, kotlin_project: Path, relative_path: str
    ) -> None:
        """Every expected Kotlin project file exists and is non-empty."""
        file_path = kotlin_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # Quality tooling (#357) is now generated alongside the
            # foundation scaffold.
            ".pre-commit-config.yaml",
            "detekt.yml",
            "scripts/check-all.sh",
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/test.sh",
            "scripts/security.sh",
            "plans/architecture/ArchitectureTest.kt",
            "plans/architecture/run-check.sh",
            # CI pipeline (#358) is now generated alongside the tooling.
            ".github/workflows/ci.yml",
        ],
    )
    def test_quality_tooling_artifact_generated(
        self, kotlin_project: Path, relative_path: str
    ) -> None:
        """#357 quality-tooling artifacts exist and are non-empty."""
        file_path = kotlin_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # Binary wrapper artifacts must never be scaffolded.
            "gradlew",
            "gradle/wrapper/gradle-wrapper.jar",
        ],
    )
    def test_out_of_scope_artifact_not_generated(
        self, kotlin_project: Path, relative_path: str
    ) -> None:
        """The scaffold must never emit wrapper binaries."""
        assert not (kotlin_project / relative_path).exists()


class TestKotlinInitQualityTooling:
    """Assert the generated quality-tooling configs are valid (#357)."""

    def test_precommit_config_parses_and_includes_kotlin_hooks(
        self, kotlin_project: Path
    ) -> None:
        """.pre-commit-config.yaml parses and wires ktlint + detekt."""
        content = (kotlin_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        local_repo = next(
            repo for repo in parsed["repos"] if repo.get("repo") == "local"
        )
        hook_ids = {hook["id"] for hook in local_repo["hooks"]}
        assert {"ktlint", "detekt"} <= hook_ids

    def test_detekt_config_parses_and_gates_complexity(
        self, kotlin_project: Path
    ) -> None:
        """detekt.yml parses and enforces the <=10 complexity ceiling."""
        parsed = yaml.safe_load((kotlin_project / "detekt.yml").read_text())
        assert parsed["complexity"]["CyclomaticComplexMethod"]["threshold"] == 11

    def test_check_all_script_runs_the_kotlin_toolchain(
        self, kotlin_project: Path
    ) -> None:
        """check-all.sh chains format, lint, coverage-gated tests, security."""
        content = (kotlin_project / "scripts" / "check-all.sh").read_text()
        assert 'run_check "Tests" "test.sh" --coverage' in content

    def test_architecture_test_uses_project_namespace(
        self, kotlin_project: Path
    ) -> None:
        """The Konsist test derives layer packages from the project name."""
        source = (
            kotlin_project / "plans" / "architecture" / "ArchitectureTest.kt"
        ).read_text()
        assert '"com.example.wear_timer.domain.."' in source

    def test_app_manifest_wires_kover_coverage_gate(self, kotlin_project: Path) -> None:
        """app/build.gradle.kts carries the 90% Kover verify bound."""
        build = (kotlin_project / "app" / "build.gradle.kts").read_text()
        assert 'id("org.jetbrains.kotlinx.kover")' in build
        assert "minBound(90)" in build


class TestKotlinInitCIWorkflow:
    """Assert the generated CI workflow matches the scaffold (#358)."""

    def test_ci_workflow_parses_and_declares_kotlin_jobs(
        self, kotlin_project: Path
    ) -> None:
        """ci.yml parses as YAML and carries the quality/test/wear jobs."""
        content = (kotlin_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Kotlin Quality Checks"
        assert set(parsed["jobs"]) == {"quality", "test", "wear"}

    def test_ci_workflow_never_invokes_the_missing_wrapper(
        self, kotlin_project: Path
    ) -> None:
        """CI provisions Gradle itself: the scaffold ships no gradlew.

        Run commands are parsed (comments may mention the wrapper when
        documenting why the workflow avoids it).
        """
        content = (kotlin_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        run_commands = [
            step.get("run", "")
            for job in parsed["jobs"].values()
            for step in job["steps"]
        ]
        assert not any("gradlew" in cmd for cmd in run_commands)
        assert "gradle/actions/setup-gradle" in content


class TestKotlinInitManifests:
    """Assert the generated Gradle manifests and AndroidManifest.xml."""

    def test_settings_names_root_project_and_app_module(
        self, kotlin_project: Path
    ) -> None:
        """settings.gradle.kts wires the root project and :app module."""
        settings = (kotlin_project / "settings.gradle.kts").read_text()
        assert f'rootProject.name = "{_PROJECT_NAME}"' in settings
        assert 'include(":app")' in settings

    def test_app_module_declares_wear_compose_dependencies(
        self, kotlin_project: Path
    ) -> None:
        """The app module depends on Jetpack Compose for Wear OS."""
        build = (kotlin_project / "app" / "build.gradle.kts").read_text()
        assert "androidx.wear.compose:compose-material" in build
        assert "androidx.wear.compose:compose-foundation" in build

    def test_app_module_targets_wear_os_3_baseline(self, kotlin_project: Path) -> None:
        """minSdk 30 is the Wear OS 3 (Galaxy Watch 4+) baseline."""
        build = (kotlin_project / "app" / "build.gradle.kts").read_text()
        assert "minSdk = 30" in build

    def test_android_manifest_is_well_formed_xml(self, kotlin_project: Path) -> None:
        """AndroidManifest.xml parses as XML with a manifest root."""
        manifest_path = kotlin_project / "app" / "src" / "main" / "AndroidManifest.xml"
        root = DefusedElementTree.fromstring(manifest_path.read_text())
        assert root.tag == "manifest"

    def test_android_manifest_declares_watch_feature(
        self, kotlin_project: Path
    ) -> None:
        """The manifest declares the Wear device profile and standalone flag."""
        manifest = (
            kotlin_project / "app" / "src" / "main" / "AndroidManifest.xml"
        ).read_text()
        assert "android.hardware.type.watch" in manifest
        assert "com.google.android.wearable.standalone" in manifest


class TestKotlinInitSources:
    """Assert the generated Kotlin source and test files."""

    def test_main_activity_uses_wear_compose(self, kotlin_project: Path) -> None:
        """MainActivity hosts a Compose-for-Wear-OS UI."""
        source = (
            kotlin_project
            / "app"
            / "src"
            / "main"
            / "kotlin"
            / _PACKAGE_PATH
            / "MainActivity.kt"
        ).read_text()
        assert "import androidx.wear.compose.material.Text" in source
        assert "class MainActivity : ComponentActivity()" in source
        assert f'greeting("{_PROJECT_NAME}")' in source

    def test_generated_test_uses_junit_against_greeting(
        self, kotlin_project: Path
    ) -> None:
        """The JUnit scaffold exercises the greeting() interpolation logic."""
        source = (
            kotlin_project
            / "app"
            / "src"
            / "test"
            / "kotlin"
            / _PACKAGE_PATH
            / "GreetingTest.kt"
        ).read_text()
        assert "import org.junit.Test" in source
        assert f'greeting("{_PROJECT_NAME}")' in source
        assert f'"Hello from {_PROJECT_NAME}!"' in source


class TestKotlinInitReadme:
    """Assert the generated README stays truthful (#356 boundaries)."""

    def test_readme_targets_wear_os(self, kotlin_project: Path) -> None:
        """README documents the Wear OS / Compose scaffold."""
        readme = (kotlin_project / "README.md").read_text()
        assert "Wear OS" in readme
        assert "Jetpack Compose" in readme

    def test_readme_advertises_generated_ci_pipeline(
        self, kotlin_project: Path
    ) -> None:
        """README documents the now-generated CI pipeline (#358) as real.

        The ci.yml the README advertises must actually exist next to it
        — the truthfulness contract that previously kept CI under a
        'Planned / coming soon' section.
        """
        readme = (kotlin_project / "README.md").read_text()
        assert "Planned / coming soon" not in readme
        assert ".github/workflows/ci.yml" in readme
        assert (kotlin_project / ".github" / "workflows" / "ci.yml").is_file()
