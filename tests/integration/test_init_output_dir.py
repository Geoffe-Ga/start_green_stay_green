"""Test init command with custom output directory (Issue #157, #158)."""
from __future__ import annotations

import subprocess
import sys
import tempfile

from pathlib import Path


def test_init_with_output_dir_creates_files() -> None:
    """Test that init with --output-dir creates all expected files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_name = "test-output-dir"
        output_dir = Path(tmpdir)

        # Run init command
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

        # Check that skills directory exists (path may be .claude/ or .claudecode/)
        skills_created = (
            (project_path / ".claude" / "skills").exists()
            or (project_path / ".claudecode" / "skills").exists()
        )
        assert skills_created, "Skills directory not created"

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

        # Run init
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
