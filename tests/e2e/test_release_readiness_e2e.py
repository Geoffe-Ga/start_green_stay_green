"""E2E release-readiness checks for the v1.0.0 manual testing plan (#152).

These tests automate the *automatable* portions of the v1.0.0 manual testing
plan that were not already covered by the existing test suite. In particular
they exercise the live metrics dashboard flow (``--enable-live-dashboard``)
end-to-end through the real ``sgsg`` CLI, asserting the generated artifacts
exist on disk and have the expected structure.

The pre-existing dashboard tests in ``tests/unit/test_cli_mocked.py`` mock
``MetricsGenerator`` and ``shutil.copy``, so they never verify that the real
generator + template copy actually produces ``docs/dashboard.html``,
``docs/metrics.json``, ``.github/workflows/metrics.yml`` and
``scripts/collect_metrics.py`` on disk. This module fills that gap.

All tests use an environment with API keys stripped and a null keyring backend
to prevent real Anthropic API calls. See Issue #196. The dashboard flow is
fully deterministic and offline (no API key required).
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from tests.conftest import get_env_without_api_keys

# Artifacts that --enable-live-dashboard must produce (relative to project root).
EXPECTED_DASHBOARD_ARTIFACTS = (
    "docs/dashboard.html",
    "docs/metrics.json",
    ".github/workflows/metrics.yml",
    "scripts/collect_metrics.py",
)


def _run_init_with_dashboard(
    tmpdir: str, project_name: str
) -> subprocess.CompletedProcess[str]:
    """Run ``sgsg init`` with the live dashboard enabled, offline.

    Args:
        tmpdir: Output directory for the generated project.
        project_name: Name of the project to generate.

    Returns:
        The completed subprocess result.
    """
    return subprocess.run(
        [
            "sgsg",
            "init",
            "--project-name",
            project_name,
            "--language",
            "python",
            "--output-dir",
            tmpdir,
            "--enable-live-dashboard",
            "--no-interactive",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=get_env_without_api_keys(),
    )


class TestLiveDashboardE2E:
    """E2E coverage for Part 1.3 of the #152 manual testing plan."""

    def test_dashboard_artifacts_created_on_disk(self) -> None:
        """Live dashboard flow creates all four expected artifacts on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_init_with_dashboard(tmpdir, "dash-e2e-project")

            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            project_dir = Path(tmpdir) / "dash-e2e-project"
            assert project_dir.exists(), "Project directory not created"

            for relative in EXPECTED_DASHBOARD_ARTIFACTS:
                artifact = project_dir / relative
                assert artifact.exists(), f"Missing dashboard artifact: {relative}"
                assert (
                    artifact.stat().st_size > 0
                ), f"Empty dashboard artifact: {relative}"

    def test_dashboard_html_references_metrics_json(self) -> None:
        """Generated dashboard.html loads metrics.json and is a quality dashboard."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_init_with_dashboard(tmpdir, "dash-html-project")
            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            dashboard = Path(tmpdir) / "dash-html-project" / "docs" / "dashboard.html"
            content = dashboard.read_text(encoding="utf-8")

            assert (
                "Quality Metrics Dashboard" in content
            ), "Dashboard should have its title heading"
            assert "metrics.json" in content, "Dashboard should load metrics.json"

    def test_metrics_json_has_expected_structure(self) -> None:
        """Generated metrics.json is valid JSON with timestamp/project/metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_init_with_dashboard(tmpdir, "dash-json-project")
            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            metrics_path = Path(tmpdir) / "dash-json-project" / "docs" / "metrics.json"
            data = json.loads(metrics_path.read_text(encoding="utf-8"))

            assert "timestamp" in data, "metrics.json must record a timestamp"
            assert data["project"] == "dash-json-project"
            assert "thresholds" in data
            assert "metrics" in data
            # Thresholds match the release quality bar wired in cli.py.
            assert data["thresholds"]["coverage"] == 90
            assert data["thresholds"]["mutation_score"] == 80

    def test_metrics_workflow_uses_project_name(self) -> None:
        """metrics.yml is rebranded to the new project (no SGSG name leaks)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_init_with_dashboard(tmpdir, "dash-wf-project")
            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            workflow = (
                Path(tmpdir)
                / "dash-wf-project"
                / ".github"
                / "workflows"
                / "metrics.yml"
            )
            content = workflow.read_text(encoding="utf-8")

            assert (
                "start-green-stay-green" not in content
            ), "Generated metrics.yml must not leak the SGSG project name"
            assert (
                "dash-wf-project" in content
            ), "Generated metrics.yml must reference the new project name"

    def test_init_without_dashboard_omits_artifacts(self) -> None:
        """Without --enable-live-dashboard, no dashboard artifacts are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "no-dash-project",
                    "--language",
                    "python",
                    "--output-dir",
                    tmpdir,
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                check=False,
                env=get_env_without_api_keys(),
            )
            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            project_dir = Path(tmpdir) / "no-dash-project"
            for relative in EXPECTED_DASHBOARD_ARTIFACTS:
                assert not (
                    project_dir / relative
                ).exists(), f"Unexpected dashboard artifact without flag: {relative}"
