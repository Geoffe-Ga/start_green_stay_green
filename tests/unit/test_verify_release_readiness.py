"""Tests for scripts/verify_release_readiness.py check functions (#152).

These tests exercise the pure, filesystem-only check helpers against synthetic
project trees so the logic is validated quickly and deterministically without
invoking the real ``sgsg`` CLI. The end-to-end CLI flow is covered separately
by ``tests/e2e/test_release_readiness_e2e.py``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import verify_release_readiness as vrr


def _make_valid_project(root: Path) -> Path:
    """Create a synthetic project tree that passes every check.

    Args:
        root: Directory under which to create the project.

    Returns:
        The project root path.
    """
    project = root / vrr.PROJECT_NAME
    project.mkdir()

    for relative in vrr.REQUIRED_FILES:
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("content\n", encoding="utf-8")

    scripts_dir = project / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    for name in vrr.REQUIRED_SCRIPTS:
        script = scripts_dir / name
        script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        script.chmod(0o755)

    # Enough pre-commit hooks.
    hooks = "repos:\n" + "".join(
        f"  - id: hook-{i}\n" for i in range(vrr.MIN_PRECOMMIT_HOOKS)
    )
    (project / ".pre-commit-config.yaml").write_text(hooks, encoding="utf-8")

    workflows = project / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / "ci.yml").write_text("name: CI\non: [push]\n", encoding="utf-8")
    (workflows / "metrics.yml").write_text(
        "name: Metrics\non: [push]\n", encoding="utf-8"
    )

    docs = project / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "dashboard.html").write_text(
        "<html>metrics.json</html>\n", encoding="utf-8"
    )
    (docs / "metrics.json").write_text(
        json.dumps(
            {
                "timestamp": "now",
                "project": vrr.PROJECT_NAME,
                "thresholds": {"coverage": 90},
                "metrics": {"coverage": 0.0},
            }
        ),
        encoding="utf-8",
    )
    (scripts_dir / "collect_metrics.py").write_text("# collector\n", encoding="utf-8")
    return project


class TestRequiredFiles:
    """Tests for _check_required_files."""

    def test_passes_when_all_present(self, tmp_path: Path) -> None:
        """No failures when every required file exists and is non-empty."""
        project = _make_valid_project(tmp_path)
        assert vrr._check_required_files(project) == []

    def test_reports_missing_file(self, tmp_path: Path) -> None:
        """A missing required file is reported."""
        project = _make_valid_project(tmp_path)
        (project / "README.md").unlink()
        failures = vrr._check_required_files(project)
        assert any("README.md" in f for f in failures)

    def test_reports_empty_file(self, tmp_path: Path) -> None:
        """An empty required file is reported as empty."""
        project = _make_valid_project(tmp_path)
        (project / "pyproject.toml").write_text("", encoding="utf-8")
        failures = vrr._check_required_files(project)
        assert any("empty" in f and "pyproject.toml" in f for f in failures)


class TestScriptsExecutable:
    """Tests for _check_scripts_executable."""

    def test_passes_when_executable(self, tmp_path: Path) -> None:
        """No failures when all scripts exist and are executable."""
        project = _make_valid_project(tmp_path)
        assert vrr._check_scripts_executable(project) == []

    def test_reports_missing_script(self, tmp_path: Path) -> None:
        """A missing quality script is reported."""
        project = _make_valid_project(tmp_path)
        (project / "scripts" / "test.sh").unlink()
        failures = vrr._check_scripts_executable(project)
        assert any("test.sh" in f for f in failures)

    def test_reports_non_executable_script(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-executable quality script is reported (POSIX branch)."""
        # Pin the POSIX branch: Windows has no executable bit, so the
        # exec-bit half of the check is POSIX-only (#380).
        monkeypatch.setattr(os, "name", "posix")
        project = _make_valid_project(tmp_path)
        (project / "scripts" / "lint.sh").chmod(0o644)
        failures = vrr._check_scripts_executable(project)
        assert any("not executable" in f and "lint.sh" in f for f in failures)

    def test_windows_checks_existence_only(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On Windows the executable bit is not enforced (#380).

        Windows stat() derives the exec bits from the file extension, so
        enforcing 0o111 there would flag every .sh script. The check
        degrades to existence-only.
        """
        monkeypatch.setattr(os, "name", "nt")
        project = _make_valid_project(tmp_path)
        (project / "scripts" / "lint.sh").chmod(0o644)
        assert vrr._check_scripts_executable(project) == []

    def test_windows_still_reports_missing_script(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing scripts are reported on Windows too (#380)."""
        monkeypatch.setattr(os, "name", "nt")
        project = _make_valid_project(tmp_path)
        (project / "scripts" / "test.sh").unlink()
        failures = vrr._check_scripts_executable(project)
        assert any("test.sh" in f for f in failures)


class TestPrecommitHooks:
    """Tests for _check_precommit_hooks."""

    def test_passes_with_enough_hooks(self, tmp_path: Path) -> None:
        """No failures when hook count meets the minimum."""
        project = _make_valid_project(tmp_path)
        assert vrr._check_precommit_hooks(project) == []

    def test_reports_too_few_hooks(self, tmp_path: Path) -> None:
        """Too few declared hooks are reported with the actual count."""
        project = _make_valid_project(tmp_path)
        (project / ".pre-commit-config.yaml").write_text(
            "repos:\n  - id: only-one\n", encoding="utf-8"
        )
        failures = vrr._check_precommit_hooks(project)
        assert len(failures) == 1
        assert "1 hooks" in failures[0]


class TestCIWorkflow:
    """Tests for _check_ci_workflow."""

    def test_passes_with_valid_yaml(self, tmp_path: Path) -> None:
        """No failures when workflows exist and are valid YAML."""
        project = _make_valid_project(tmp_path)
        assert vrr._check_ci_workflow(project) == []

    def test_reports_no_workflows(self, tmp_path: Path) -> None:
        """An absent workflows directory is reported."""
        project = tmp_path / "empty"
        project.mkdir()
        failures = vrr._check_ci_workflow(project)
        assert failures == ["no CI workflows found under .github/workflows/"]

    def test_reports_invalid_yaml(self, tmp_path: Path) -> None:
        """A malformed workflow YAML file is reported."""
        project = _make_valid_project(tmp_path)
        (project / ".github" / "workflows" / "ci.yml").write_text(
            "name: [unclosed\n", encoding="utf-8"
        )
        failures = vrr._check_ci_workflow(project)
        assert any("invalid YAML" in f for f in failures)


class TestDashboard:
    """Tests for _check_dashboard."""

    def test_passes_when_complete(self, tmp_path: Path) -> None:
        """No failures when all dashboard artifacts are present and valid."""
        project = _make_valid_project(tmp_path)
        assert vrr._check_dashboard(project) == []

    def test_reports_missing_artifact(self, tmp_path: Path) -> None:
        """A missing dashboard artifact is reported."""
        project = _make_valid_project(tmp_path)
        (project / "docs" / "dashboard.html").unlink()
        failures = vrr._check_dashboard(project)
        assert any("dashboard.html" in f for f in failures)

    def test_reports_missing_metrics_key(self, tmp_path: Path) -> None:
        """A metrics.json missing a required key is reported."""
        project = _make_valid_project(tmp_path)
        (project / "docs" / "metrics.json").write_text(
            json.dumps({"project": vrr.PROJECT_NAME}), encoding="utf-8"
        )
        failures = vrr._check_dashboard(project)
        assert any("missing key: timestamp" in f for f in failures)

    def test_reports_project_name_mismatch(self, tmp_path: Path) -> None:
        """A metrics.json with the wrong project name is reported."""
        project = _make_valid_project(tmp_path)
        (project / "docs" / "metrics.json").write_text(
            json.dumps(
                {
                    "timestamp": "now",
                    "project": "wrong-name",
                    "thresholds": {},
                    "metrics": {},
                }
            ),
            encoding="utf-8",
        )
        failures = vrr._check_dashboard(project)
        assert any("project mismatch" in f for f in failures)

    def test_reports_malformed_metrics_json(self, tmp_path: Path) -> None:
        """Malformed metrics.json is reported, not raised as a traceback."""
        project = _make_valid_project(tmp_path)
        (project / "docs" / "metrics.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        failures = vrr._check_dashboard(project)
        assert any("not valid JSON" in f for f in failures)


class TestOfflineEnv:
    """Tests for _offline_env."""

    def test_strips_api_keys_and_disables_keyring(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """API keys are removed and a null keyring backend is selected."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
        monkeypatch.setenv("CLAUDE_API_KEY", "secret")
        env = vrr._offline_env()
        assert "ANTHROPIC_API_KEY" not in env
        assert "CLAUDE_API_KEY" not in env
        assert env["PYTHON_KEYRING_BACKEND"] == "keyring.backends.null.Keyring"


class TestVerify:
    """Tests for _verify orchestration."""

    def test_returns_zero_when_all_pass(self, tmp_path: Path) -> None:
        """_verify returns 0 when every check passes."""
        project = _make_valid_project(tmp_path)
        assert vrr._verify(project) == 0

    def test_returns_one_on_failure(self, tmp_path: Path) -> None:
        """_verify returns 1 when any check fails."""
        project = _make_valid_project(tmp_path)
        (project / "README.md").unlink()
        assert vrr._verify(project) == 1
