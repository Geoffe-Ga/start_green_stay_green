"""Test init command with custom output directory (Issue #157, #158).

All tests mock the AI orchestrator to prevent real Anthropic API calls.
See Issue #196.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile

from tests.conftest import get_env_without_api_keys


def test_init_with_output_dir_creates_files() -> None:
    """Test that init with --output-dir creates all expected files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_name = "test-output-dir"
        output_dir = Path(tmpdir)

        # Run init command (with API keys stripped to prevent real API calls)
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "start_green_stay_green.cli",
                "init",
                "--project-name",
                project_name,
                "--language",
                "python",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=get_env_without_api_keys(),
        )

        # Check command succeeded
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check project directory was created
        project_path = output_dir / project_name
        assert project_path.exists(), f"Project directory not created at {project_path}"
        assert project_path.is_dir(), "Project path is not a directory"

        # Check core required files exist
        core_files = [
            ".pre-commit-config.yaml",
            "scripts/test.sh",
            "scripts/lint.sh",
            "scripts/format.sh",
            "scripts/check-all.sh",
            "scripts/security.sh",
            "scripts/mutation.sh",
            "scripts/complexity.sh",
        ]

        for expected_file in core_files:
            file_path = project_path / expected_file
            assert file_path.exists(), f"Expected file not created: {expected_file}"

        skills_dir = project_path / ".claude" / "skills"
        assert skills_dir.exists(), "Skills directory not created"

        # Verify pre-commit config has content
        precommit_config = project_path / ".pre-commit-config.yaml"
        content = precommit_config.read_text()
        assert len(content) > 100, "Pre-commit config is too short"
        assert "repos:" in content, "Pre-commit config missing repos section"


def test_init_output_dir_resolves_correctly() -> None:
    """Test that output directory path is resolved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_name = "path-resolution-test"
        output_dir = Path(tmpdir)

        # Run init (with API keys stripped to prevent real API calls)
        result = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-m",
                "start_green_stay_green.cli",
                "init",
                "--project-name",
                project_name,
                "--language",
                "python",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=get_env_without_api_keys(),
        )

        assert result.returncode == 0

        # On macOS, /tmp is a symlink to /private/tmp
        # The resolved path should work regardless
        project_path = output_dir / project_name
        resolved_path = project_path.resolve()

        # Both paths should point to the same directory
        assert project_path.exists()
        assert resolved_path.exists()
        assert project_path.is_dir()

        # Success message should show the resolved path
        # Remove all whitespace to handle line wrapping by rich console
        stdout_clean = "".join(result.stdout.split())
        path_clean = "".join(str(resolved_path).split())
        path_alt_clean = "".join(str(project_path).split())
        assert (
            path_clean in stdout_clean or path_alt_clean in stdout_clean
        ), f"Path not found in output. Looking for {resolved_path} or {project_path}"
