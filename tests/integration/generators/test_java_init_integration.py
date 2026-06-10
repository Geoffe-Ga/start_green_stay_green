"""Integration tests for ``sgsg init --language java`` (#366).

Runs the full init flow once via the Typer CliRunner and asserts the
generated Java (Wear OS, legacy Android Wear) project tree, the Maven
manifest, and the Android XML files. The AI orchestrator is patched to
``None`` so no real Anthropic API calls are made (Issue #196); the null
keyring backend is enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke Maven, a JDK, or
the Android SDK — so they pass on CI runners where none of those are
installed, mirroring ``test_cpp_init_integration.py`` (#361).

Foundation-stage boundaries: the CI workflow IS generated (ci.py has
had a java config all along), while the #367 quality tooling
(pre-commit config, quality scripts, metrics dashboard, architecture
rules) is not — init must skip those steps with informational messages
and the README must keep them under "Planned / coming soon".
"""

from pathlib import Path
from unittest.mock import patch

from defusedxml import ElementTree as DefusedElementTree
import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.utils.java import android_package
from start_green_stay_green.utils.java import android_package_path

# Project name chosen to exercise the hyphen sanitization path:
# wrist-timer -> package com.example.wrist_timer.
_PROJECT_NAME = "wrist-timer"
_PACKAGE = android_package("wrist_timer")
_PACKAGE_PATH = android_package_path("wrist_timer")


@pytest.fixture(scope="module")
def java_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language java`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("java-init")
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
                "java",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for java: {result.output}"
    return output_dir / _PROJECT_NAME


class TestJavaInitTree:
    """Assert the generated legacy Android Wear project tree."""

    def test_project_directory_created(self, java_project: Path) -> None:
        """Init creates the project directory."""
        assert java_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            "pom.xml",
            f"src/main/java/{_PACKAGE_PATH}/Greeting.java",
            f"src/test/java/{_PACKAGE_PATH}/GreetingTest.java",
            "app/src/main/AndroidManifest.xml",
            f"app/src/main/java/{_PACKAGE_PATH}/MainActivity.java",
            "app/src/main/res/layout/activity_main.xml",
            "README.md",
            # The CI workflow is real today: ci.py has a java config and
            # reference/ci/java.yml backs it.
            ".github/workflows/ci.yml",
        ],
    )
    def test_expected_file_generated(
        self, java_project: Path, relative_path: str
    ) -> None:
        """Every expected java project file exists and is non-empty."""
        file_path = java_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # #367 quality tooling must not be scaffolded yet.
            ".pre-commit-config.yaml",
            "scripts/check-all.sh",
            "scripts/test.sh",
            "plans/architecture",
            # The metrics dashboard is opt-in and unsupported for java.
            "docs/metrics.json",
            # No Gradle manifests: the Android build is deliberately not
            # scaffolded (the two-builds split).
            "build.gradle",
            "settings.gradle",
            "app/build.gradle",
            # The pre-#366 generic scaffold is gone.
            "src/main/java/wrist_timer/Main.java",
            "src/test/java/wrist_timer/MainTest.java",
        ],
    )
    def test_out_of_scope_artifact_not_generated(
        self, java_project: Path, relative_path: str
    ) -> None:
        """The scaffold must not emit #367 tooling or Gradle manifests."""
        assert not (java_project / relative_path).exists()


class TestJavaInitManifests:
    """Assert the Maven manifest and the Android XML files."""

    def test_pom_is_well_formed_xml(self, java_project: Path) -> None:
        """pom.xml parses as XML rooted at the Maven project element."""
        root = DefusedElementTree.fromstring((java_project / "pom.xml").read_text())
        assert root.tag == "{http://maven.apache.org/POM/4.0.0}project"

    def test_pom_builds_and_gates_the_pure_logic(self, java_project: Path) -> None:
        """The pom wires JUnit 4, Surefire, and the JaCoCo 90% gate."""
        pom = (java_project / "pom.xml").read_text()
        assert "<artifactId>wrist-timer</artifactId>" in pom
        assert "<artifactId>junit</artifactId>" in pom
        assert "<artifactId>maven-surefire-plugin</artifactId>" in pom
        assert "<minimum>0.90</minimum>" in pom

    def test_pom_backs_every_ci_quality_goal(self, java_project: Path) -> None:
        """The plugins behind the generated CI's mvn goals are declared.

        reference/ci/java.yml invokes checkstyle:check, pmd:check,
        spotbugs:check, jacoco:report, and jacoco:check — each needs its
        plugin in the pom (the spotbugs and jacoco prefixes do not
        resolve from Maven's default plugin groups).
        """
        pom = (java_project / "pom.xml").read_text()
        assert "<artifactId>maven-checkstyle-plugin</artifactId>" in pom
        assert "<artifactId>maven-pmd-plugin</artifactId>" in pom
        assert "<artifactId>spotbugs-maven-plugin</artifactId>" in pom
        assert "<artifactId>jacoco-maven-plugin</artifactId>" in pom

    def test_pom_documents_android_tooling_split(self, java_project: Path) -> None:
        """The pom discloses that the APK build is Android tooling's job."""
        pom = (java_project / "pom.xml").read_text()
        assert "THE TWO BUILDS" in pom
        assert "Android Studio" in pom

    def test_android_manifest_is_well_formed_xml(self, java_project: Path) -> None:
        """AndroidManifest.xml parses with a manifest root."""
        manifest_path = java_project / "app" / "src" / "main" / "AndroidManifest.xml"
        root = DefusedElementTree.fromstring(manifest_path.read_text())
        assert root.tag == "manifest"
        assert root.get("package") == _PACKAGE

    def test_android_manifest_declares_wear_watch_app(self, java_project: Path) -> None:
        """The manifest declares the watch feature and standalone flag."""
        manifest = (
            java_project / "app" / "src" / "main" / "AndroidManifest.xml"
        ).read_text()
        assert '<uses-feature android:name="android.hardware.type.watch" />' in (
            manifest
        )
        assert "com.google.android.wearable.standalone" in manifest
        assert 'android:name="com.google.android.wearable"' in manifest

    def test_layout_is_well_formed_box_inset_layout(self, java_project: Path) -> None:
        """activity_main.xml parses and roots at BoxInsetLayout."""
        layout_path = (
            java_project
            / "app"
            / "src"
            / "main"
            / "res"
            / "layout"
            / "activity_main.xml"
        )
        root = DefusedElementTree.fromstring(layout_path.read_text())
        assert root.tag == "androidx.wear.widget.BoxInsetLayout"

    def test_ci_workflow_parses_and_runs_maven_goals(self, java_project: Path) -> None:
        """ci.yml parses as YAML and gates via the pom-backed mvn goals."""
        content = (java_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        assert parsed["name"] == "Java Quality Checks"
        assert "mvn checkstyle:check" in content
        assert "mvn jacoco:check" in content


class TestJavaInitSources:
    """Assert the generated Java source and test files."""

    def test_pure_logic_unit_is_android_free(self, java_project: Path) -> None:
        """Greeting.java has no Android dependencies (Maven-buildable)."""
        source = (
            java_project / "src" / "main" / "java" / _PACKAGE_PATH / "Greeting.java"
        ).read_text()
        assert f"package {_PACKAGE};" in source
        assert '"Hello from " + projectName + "!"' in source
        assert "import android" not in source
        assert "androidx" not in source

    def test_main_activity_uses_wear_widget_layout(self, java_project: Path) -> None:
        """MainActivity renders the BoxInsetLayout and the greeting."""
        source = (
            java_project
            / "app"
            / "src"
            / "main"
            / "java"
            / _PACKAGE_PATH
            / "MainActivity.java"
        ).read_text()
        assert "public class MainActivity extends Activity" in source
        assert "setContentView(R.layout.activity_main);" in source
        assert f'Greeting.greet("{_PROJECT_NAME}")' in source
        assert "extends WearableActivity" not in source

    def test_generated_test_uses_junit4_against_greet(self, java_project: Path) -> None:
        """The JUnit 4 scaffold exercises the Greeting.greet logic."""
        source = (
            java_project / "src" / "test" / "java" / _PACKAGE_PATH / "GreetingTest.java"
        ).read_text()
        assert "import org.junit.Test;" in source
        assert f'Greeting.greet("{_PROJECT_NAME}")' in source
        assert f'"Hello from {_PROJECT_NAME}!"' in source
        assert "jupiter" not in source


class TestJavaInitReadme:
    """Assert the generated README stays truthful (#366 boundaries)."""

    def test_readme_targets_legacy_android_wear(self, java_project: Path) -> None:
        """README documents the Wear OS (legacy Android Wear) scaffold."""
        readme = (java_project / "README.md").read_text()
        assert "Wear OS" in readme
        assert "legacy Android Wear" in readme

    def test_readme_advertises_generated_ci_pipeline(self, java_project: Path) -> None:
        """README documents the generated CI pipeline as real.

        The ci.yml the README advertises must actually exist next to it
        — the truthfulness contract from #365.
        """
        readme = (java_project / "README.md").read_text()
        assert ".github/workflows/ci.yml" in readme
        assert (java_project / ".github" / "workflows" / "ci.yml").is_file()

    def test_readme_keeps_367_tooling_under_planned(self, java_project: Path) -> None:
        """README lists the #367 quality tooling as planned, not real."""
        readme = (java_project / "README.md").read_text()
        assert "Planned / coming soon" in readme
        assert "#367" in readme

    def test_readme_documents_android_tooling_gap(self, java_project: Path) -> None:
        """README explains that the APK build needs Android Studio/Gradle."""
        readme = (java_project / "README.md").read_text()
        assert "## The two builds" in readme
        assert "Android Studio" in readme


class TestJavaInitConsoleOutput:
    """Assert init's console output reflects the #366 boundaries."""

    def test_init_skips_only_the_367_steps(self, tmp_path: Path) -> None:
        """Init skips pre-commit/scripts/architecture but generates CI.

        The #367 quality tooling must be announced as unavailable while
        the CI pipeline (real since ci.py gained its java config) is
        generated without a skip notice.
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
                    "java",
                    "--output-dir",
                    str(tmp_path),
                    "--no-interactive",
                ],
            )
        assert result.exit_code == 0
        assert "Pre-commit config unavailable for java" in result.output
        assert "Quality scripts unavailable for java" in result.output
        assert "Architecture rules unavailable for java" in result.output
        assert "CI pipeline unavailable for java" not in result.output
        assert "Generated CI pipeline" in result.output
