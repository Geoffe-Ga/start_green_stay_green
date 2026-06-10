"""Integration tests for ``sgsg init --language java`` (#366/#367).

Runs the full init flow once via the Typer CliRunner and asserts the
generated Java (Wear OS, legacy Android Wear) project tree, the Maven
manifest, and the Android XML files. The AI orchestrator is patched to
``None`` so no real Anthropic API calls are made (Issue #196); the null
keyring backend is enforced globally by ``tests/conftest.py``.

These tests are structural only — they never invoke Maven, a JDK, or
the Android SDK — so they pass on CI runners where none of those are
installed, mirroring ``test_cpp_init_integration.py`` (#361).

With #367 the quality toolchain (pre-commit config, quality scripts,
the pmd-ruleset.xml companion, architecture rules) is generated for
java alongside the #366 foundation and its CI workflow, so this suite
locks in the presence of every pipeline artifact.
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
            # Quality tooling (#367) is now generated alongside the
            # foundation scaffold.
            ".pre-commit-config.yaml",
            "pmd-ruleset.xml",
            "scripts/check-all.sh",
            "scripts/format.sh",
            "scripts/lint.sh",
            "scripts/test.sh",
            "scripts/security.sh",
            "plans/architecture/ArchitectureTest.java",
            "plans/architecture/run-check.sh",
        ],
    )
    def test_quality_tooling_artifact_generated(
        self, java_project: Path, relative_path: str
    ) -> None:
        """#367 quality-tooling artifacts exist and are non-empty."""
        file_path = java_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"

    @pytest.mark.parametrize(
        "relative_path",
        [
            # The metrics dashboard is opt-in (--enable-live-dashboard).
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
        """The scaffold must not emit opt-in artifacts or Gradle manifests."""
        assert not (java_project / relative_path).exists()


class TestJavaInitQualityTooling:
    """Assert the generated quality-tooling configs are valid (#367)."""

    def test_precommit_config_parses_and_includes_java_hooks(
        self, java_project: Path
    ) -> None:
        """.pre-commit-config.yaml parses and wires the Java toolchain."""
        content = (java_project / ".pre-commit-config.yaml").read_text()
        parsed = yaml.safe_load(
            "\n".join(line for line in content.split("\n") if not line.startswith("#"))
        )
        local_repo = next(
            repo for repo in parsed["repos"] if repo.get("repo") == "local"
        )
        hook_ids = {hook["id"] for hook in local_repo["hooks"]}
        assert {"google-java-format", "checkstyle", "pmd", "spotbugs"} <= hook_ids

    def test_pmd_ruleset_parses_and_gates_complexity(self, java_project: Path) -> None:
        """pmd-ruleset.xml parses as XML and carries the CCN rule."""
        content = (java_project / "pmd-ruleset.xml").read_text()
        root = DefusedElementTree.fromstring(content)
        assert root.tag.endswith("ruleset")
        assert "CyclomaticComplexity" in content

    def test_check_all_script_runs_the_java_toolchain(self, java_project: Path) -> None:
        """check-all.sh chains format, lint, coverage-gated tests, security."""
        content = (java_project / "scripts" / "check-all.sh").read_text()
        assert 'run_check "Tests" "test.sh" --coverage' in content

    def test_architecture_test_defines_the_layer_matrix(
        self, java_project: Path
    ) -> None:
        """The ArchUnit template derives its layers from the project name."""
        source = (
            java_project / "plans" / "architecture" / "ArchitectureTest.java"
        ).read_text()
        assert f"package {_PACKAGE}.architecture;" in source
        assert "Architectures.layeredArchitecture()" in source


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

    def test_ci_workflow_compiles_before_spotbugs(self, java_project: Path) -> None:
        """The generated workflow's SpotBugs step is never a no-op (#368).

        SpotBugs reads bytecode, so a bare `mvn spotbugs:check` silently
        passes when target/classes is empty — the generated CI must
        compile within the same invocation, matching the pre-commit hook
        and scripts/security.sh.
        """
        content = (java_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        run_commands = [
            cmd
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if (cmd := step.get("run"))
        ]
        spotbugs_runs = [cmd for cmd in run_commands if "spotbugs:check" in cmd]
        assert spotbugs_runs, "CI must run the SpotBugs gate"
        for command in spotbugs_runs:
            assert "compile" in command
            assert command.index("compile") < command.index("spotbugs:check")

    def test_ci_codecov_upload_cannot_fail_a_fresh_project(
        self, java_project: Path
    ) -> None:
        """The Codecov upload is best-effort in generated projects (#368).

        A fresh `green init` project ships no CODECOV_TOKEN secret, so
        `fail_ci_if_error: true` would start the project red; the real
        coverage gate is the pom-backed `mvn jacoco:check` step.
        """
        content = (java_project / ".github" / "workflows" / "ci.yml").read_text()
        parsed = yaml.safe_load(content)
        codecov_steps = [
            step
            for job in parsed["jobs"].values()
            for step in job["steps"]
            if "codecov" in step.get("uses", "")
        ]
        assert codecov_steps, "CI must still upload coverage to Codecov"
        for step in codecov_steps:
            assert step["with"]["fail_ci_if_error"] is False


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

    def test_readme_advertises_367_tooling_as_real(self, java_project: Path) -> None:
        """README advertises the now-generated #367 quality tooling.

        Every artifact the README checkmarks must exist next to it —
        the truthfulness contract; the 'Planned / coming soon' section
        is gone because every roadmap item is generated.
        """
        readme = (java_project / "README.md").read_text()
        assert "Planned / coming soon" not in readme
        assert "./scripts/check-all.sh" in readme
        assert (java_project / "scripts" / "check-all.sh").is_file()
        assert "plans/architecture" in readme
        assert (
            java_project / "plans" / "architecture" / "ArchitectureTest.java"
        ).is_file()

    def test_readme_documents_android_tooling_gap(self, java_project: Path) -> None:
        """README explains that the APK build needs Android Studio/Gradle."""
        readme = (java_project / "README.md").read_text()
        assert "## The two builds" in readme
        assert "Android Studio" in readme


class TestJavaInitConsoleOutput:
    """Assert init's console output reflects the #367 wiring."""

    def test_init_skips_no_pipeline_steps(self, tmp_path: Path) -> None:
        """Init prints no skip notice for any java pipeline step.

        The pre-commit, scripts, and architecture steps gained java
        support with #367 (CI has been real since #366), so every
        "unavailable" notice must be gone.
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
        assert "Pre-commit config unavailable for java" not in result.output
        assert "Quality scripts unavailable for java" not in result.output
        assert "Architecture rules unavailable for java" not in result.output
        assert "CI pipeline unavailable for java" not in result.output
        assert "Generated CI pipeline" in result.output
