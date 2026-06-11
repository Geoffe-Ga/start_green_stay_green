"""Integration tests for ``sgsg init --language swift`` (#354).

Runs the full init flow once via the Typer CliRunner and asserts the
generated Swift (watchOS) project tree and the ``Package.swift`` manifest
contents. The AI orchestrator is patched to ``None`` so no real Anthropic
API calls are made (Issue #196); the null keyring backend is enforced
globally by ``tests/conftest.py``.

These tests are structural only — they never invoke the Swift toolchain —
so they pass on CI runners (ubuntu) where swift/swiftlint/swift-format are
not installed, mirroring the established multi-language e2e pattern in
``tests/e2e/test_language_e2e.py``.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app

# Project name chosen to exercise the hyphen-to-underscore package-name
# conversion (wrist-timer -> wrist_timer) and PascalCase type naming
# (wrist-timer -> WristTimer).
_PROJECT_NAME = "wrist-timer"
_PACKAGE_NAME = "wrist_timer"
_TYPE_NAME = "WristTimer"


@pytest.fixture(scope="module")
def swift_project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run ``sgsg init --language swift`` once and return the project root.

    Args:
        tmp_path_factory: Pytest factory for a module-scoped temp directory.

    Returns:
        Path to the generated project directory.
    """
    output_dir = tmp_path_factory.mktemp("swift-init")
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
                "swift",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )
    assert result.exit_code == 0, f"sgsg init failed for swift: {result.output}"
    return output_dir / _PROJECT_NAME


class TestSwiftInitTree:
    """Assert the generated Swift project tree."""

    def test_project_directory_created(self, swift_project: Path) -> None:
        """Init creates the project directory."""
        assert swift_project.is_dir()

    @pytest.mark.parametrize(
        "relative_path",
        [
            "Package.swift",
            f"Sources/{_PACKAGE_NAME}/{_TYPE_NAME}App.swift",
            f"Sources/{_PACKAGE_NAME}/ContentView.swift",
            f"Tests/{_PACKAGE_NAME}Tests/{_PACKAGE_NAME}Tests.swift",
            ".swiftlint.yml",
            ".pre-commit-config.yaml",
            ".github/workflows/ci.yml",
            "plans/architecture/.swiftlint-architecture.yml",
            "scripts/check-all.sh",
            "scripts/test.sh",
            "scripts/lint.sh",
            "scripts/format.sh",
            "scripts/security.sh",
            "README.md",
        ],
    )
    def test_expected_file_generated(
        self, swift_project: Path, relative_path: str
    ) -> None:
        """Every expected Swift project file exists and is non-empty."""
        file_path = swift_project / relative_path
        assert file_path.is_file(), f"Missing {relative_path}"
        assert file_path.read_text(), f"Empty {relative_path}"


class TestSwiftInitManifest:
    """Assert the generated ``Package.swift`` manifest contents."""

    def test_manifest_declares_swift_tools_version(self, swift_project: Path) -> None:
        """The manifest pins swift-tools-version 5.9 on its first line."""
        first_line = (swift_project / "Package.swift").read_text().splitlines()[0]
        assert first_line == "// swift-tools-version:5.9"

    def test_manifest_names_package_in_pascal_case(self, swift_project: Path) -> None:
        """The package name is the PascalCase form of the project name."""
        manifest = (swift_project / "Package.swift").read_text()
        assert f'name: "{_TYPE_NAME}",' in manifest

    def test_manifest_targets_watchos_v10(self, swift_project: Path) -> None:
        """The manifest declares the watchOS v10 platform."""
        manifest = (swift_project / "Package.swift").read_text()
        assert ".watchOS(.v10)" in manifest

    def test_manifest_declares_main_target(self, swift_project: Path) -> None:
        """The manifest declares the package-named source target."""
        manifest = (swift_project / "Package.swift").read_text()
        assert f'.target(name: "{_PACKAGE_NAME}")' in manifest

    def test_manifest_declares_test_target_with_dependency(
        self, swift_project: Path
    ) -> None:
        """The test target depends on the main target."""
        manifest = (swift_project / "Package.swift").read_text()
        assert f'name: "{_PACKAGE_NAME}Tests"' in manifest
        assert f'dependencies: ["{_PACKAGE_NAME}"]' in manifest


class TestSwiftInitSources:
    """Assert the generated Swift source and test files."""

    def test_app_entry_point_is_watchos_gated(self, swift_project: Path) -> None:
        """@main is gated to watchOS so the macOS test host can link."""
        app_source = (
            swift_project / "Sources" / _PACKAGE_NAME / f"{_TYPE_NAME}App.swift"
        ).read_text()
        assert "#if os(watchOS)" in app_source
        assert "@main" in app_source
        assert f"struct {_TYPE_NAME}App: App" in app_source

    def test_generated_tests_use_xctest(self, swift_project: Path) -> None:
        """The generated test file imports XCTest and the package target."""
        test_source = (
            swift_project
            / "Tests"
            / f"{_PACKAGE_NAME}Tests"
            / f"{_PACKAGE_NAME}Tests.swift"
        ).read_text()
        assert "import XCTest" in test_source
        assert f"@testable import {_PACKAGE_NAME}" in test_source
        assert f"final class {_TYPE_NAME}Tests: XCTestCase" in test_source


class TestSwiftInitQualityConfigs:
    """Assert the generated quality-tooling configuration files."""

    def test_precommit_config_wires_swift_hooks(self, swift_project: Path) -> None:
        """The pre-commit config contains strict swiftlint and swift-format."""
        config = yaml.safe_load((swift_project / ".pre-commit-config.yaml").read_text())
        hooks = {hook["id"]: hook for repo in config["repos"] for hook in repo["hooks"]}
        assert hooks["swiftlint"]["entry"] == "swiftlint lint --strict"
        assert hooks["swift-format"]["entry"] == "swift-format format --in-place"
        assert "gitleaks" in hooks
        assert "detect-secrets" in hooks

    def test_swiftlint_config_is_parseable_and_scoped(
        self, swift_project: Path
    ) -> None:
        """.swiftlint.yml parses as YAML and lints Sources and Tests."""
        config = yaml.safe_load((swift_project / ".swiftlint.yml").read_text())
        assert config["included"] == ["Sources", "Tests"]

    def test_test_script_enables_coverage(self, swift_project: Path) -> None:
        """scripts/test.sh runs swift test with code coverage enabled."""
        test_script = (swift_project / "scripts" / "test.sh").read_text()
        assert "swift test --enable-code-coverage" in test_script


class TestSwiftInitReadme:
    """Assert the generated README stays truthful (#365 boundaries)."""

    def test_readme_advertises_generated_ci_pipeline(self, swift_project: Path) -> None:
        """README documents the now-generated CI pipeline (#353) as real.

        The ci.yml the README advertises must actually exist next to it
        — the truthfulness contract that previously kept CI under a
        'Planned / coming soon' section. The Swift README stayed stale
        after #353 landed CI; fixed alongside the identical C/C++ flip
        (#365).
        """
        readme = (swift_project / "README.md").read_text()
        assert "Planned / coming soon" not in readme
        assert ".github/workflows/ci.yml" in readme
        assert (swift_project / ".github" / "workflows" / "ci.yml").is_file()
