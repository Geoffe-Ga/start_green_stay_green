"""End-to-end tests for tool configuration auditor.

These tests verify the complete workflow from CLI invocation to report generation.

NOTE: This test suite uses subprocess.run() to invoke the CLI script with controlled
test inputs. The S603 rule (subprocess without shell=True check) is disabled for all
e2e test files via pyproject.toml per-file-ignores configuration.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def e2e_project(tmp_path: Path) -> Path:
    """Create a complete project for E2E testing."""
    # Create realistic project structure
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    # Create pyproject.toml with conflicts
    pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    # Create .pre-commit-config.yaml
    precommit_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
"""
    (tmp_path / ".pre-commit-config.yaml").write_text(precommit_content)

    return tmp_path


@pytest.mark.e2e
class TestAuditE2E:
    """End-to-end test scenarios."""

    def test_cli_dry_run(self, e2e_project: Path) -> None:
        """Test running the auditor via CLI in dry-run mode."""
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--project-root",
                str(e2e_project),
                "--output",
                str(e2e_project / "audit-report.md"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should succeed
        assert result.returncode == 0, f"STDERR: {result.stderr}"
        assert "Discovering configurations" in result.stdout
        assert "Analysis complete" in result.stdout

        # Should generate report
        report_path = e2e_project / "audit-report.md"
        assert report_path.exists()
        content = report_path.read_text()
        assert "Tool Configuration Audit Report" in content

    def test_cli_verbose_mode(self, e2e_project: Path) -> None:
        """Test running with verbose output."""
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--project-root",
                str(e2e_project),
                "--dry-run",
                "--verbose",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        # Verbose mode should show more details
        assert "ToolConfig" in result.stdout or "Discovering" in result.stdout

    def test_cli_missing_api_key(
        self, e2e_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test running without API key (should fail unless dry-run)."""
        # Remove API key
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--project-root",
                str(e2e_project),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should fail with error about API key
        assert result.returncode == 1
        assert "ANTHROPIC_API_KEY" in result.stderr

    def test_cli_help(self) -> None:
        """Test --help flag."""
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        stdout_lower = result.stdout.lower()
        assert "usage:" in stdout_lower or "audit tool configurations" in stdout_lower

    def test_report_format(self, e2e_project: Path) -> None:
        """Test that generated report has correct markdown format."""
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )

        output_path = e2e_project / "test-report.md"
        subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--project-root",
                str(e2e_project),
                "--output",
                str(output_path),
                "--dry-run",
            ],
            check=True,
        )

        # Verify report structure
        content = output_path.read_text()

        # Check headers
        assert "# Tool Configuration Audit Report" in content
        assert "## Summary" in content
        assert "## Discovered Configurations" in content
        assert "## Conflicts" in content
        assert "## Next Steps" in content

        # Check for specific content
        assert "Total Configurations Discovered" in content
        assert "Total Conflicts Detected" in content


@pytest.mark.e2e
class TestAuditRealProject:
    """Test auditing the SGSG project itself."""

    def test_audit_sgsg_project(self, tmp_path: Path) -> None:
        """Test auditing the actual SGSG project."""
        script_path = (
            Path(__file__).parent.parent.parent / "scripts" / "audit_tool_configs.py"
        )
        project_root = Path(__file__).parent.parent.parent

        output_path = tmp_path / "sgsg-audit.md"

        result = subprocess.run(
            [
                sys.executable,
                str(script_path),
                "--project-root",
                str(project_root),
                "--output",
                str(output_path),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Should succeed
        assert result.returncode == 0, f"STDERR: {result.stderr}"
        assert output_path.exists()

        # Should find many configurations
        content = output_path.read_text()
        assert "ruff" in content.lower()
        assert "black" in content.lower()
        assert "mypy" in content.lower()
