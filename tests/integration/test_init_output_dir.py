"""Test init command with custom output directory (Issue #157, #158)."""
import subprocess
import sys
import tempfile
from pathlib import Path


def test_init_with_output_dir_creates_files():
    """Test that init with --output-dir creates all expected files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_name = "test-output-dir"
        output_dir = Path(tmpdir)

        # Run init command
        result = subprocess.run(
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

        # Check all required files exist
        expected_files = [
            ".pre-commit-config.yaml",
            "scripts/test.sh",
            "scripts/lint.sh",
            "scripts/format.sh",
            "scripts/check-all.sh",
            "scripts/security.sh",
            "scripts/mutation.sh",
            "scripts/complexity.sh",
            ".claude/skills/stay-green.md",
            ".claude/skills/mutation-testing.md",
            ".claude/skills/comprehensive-pr-review.md",
        ]

        for expected_file in expected_files:
            file_path = project_path / expected_file
            assert file_path.exists(), f"Expected file not created: {expected_file}"

        # Verify pre-commit config has content
        precommit_config = project_path / ".pre-commit-config.yaml"
        content = precommit_config.read_text()
        assert len(content) > 100, "Pre-commit config is too short"
        assert "repos:" in content, "Pre-commit config missing repos section"


def test_init_output_dir_resolves_correctly():
    """Test that output directory path is resolved correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_name = "path-resolution-test"
        output_dir = Path(tmpdir)

        # Run init
        result = subprocess.run(
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
        assert str(resolved_path) in result.stdout or str(project_path) in result.stdout
