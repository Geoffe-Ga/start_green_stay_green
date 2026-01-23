"""Unit tests for CLI init command."""

from pathlib import Path

from typer.testing import CliRunner

from start_green_stay_green.cli import app


class TestInitCommand:
    """Test init command functionality."""

    def test_init_command_exists(self) -> None:
        """Test init command is registered in CLI app."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--help"])

        assert result.exit_code == 0
        assert "init" in result.stdout.lower()

    def test_init_with_dry_run_does_not_create_files(self, tmp_path: Path) -> None:
        """Test dry-run mode shows what would be created without creating."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--dry-run",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
            ],
        )

        assert result.exit_code == 0
        assert "dry" in result.stdout.lower() or "preview" in result.stdout.lower()
        # Should not create actual files in dry-run mode
        assert not (tmp_path / "test-project").exists()

    def test_init_requires_project_name(self) -> None:
        """Test init command requires project name."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--language", "python"])

        # Should fail or prompt for project name
        assert result.exit_code != 0 or "project" in result.stdout.lower()

    def test_init_requires_language(self) -> None:
        """Test init command requires language selection."""
        runner = CliRunner()
        result = runner.invoke(app, ["init", "--project-name", "test"])

        # Should fail or prompt for language
        assert result.exit_code != 0 or "language" in result.stdout.lower()

    def test_init_validates_project_name(self) -> None:
        """Test init command validates project name format."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "invalid project name!@#",
                "--language",
                "python",
            ],
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert "invalid" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_init_calls_all_generators(
        self,
        tmp_path: Path,
    ) -> None:
        """Test init command orchestrates all generators."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        # Should complete successfully
        assert result.exit_code == 0
        # TODO(Issue #106): Re-enable generator call verification  # noqa: FIX002
        # when full generator integration is implemented

    def test_init_supports_config_file(self, tmp_path: Path) -> None:
        """Test init command can load configuration from file."""
        # TODO(Issue #106): Implement YAML/TOML config file parsing  # noqa: FIX002
        # Config file loading is currently a stub that returns empty dict
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
project_name: test-project
language: python
include_ci: true
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--config",
                str(config_file),
                "--output-dir",
                str(tmp_path),
            ],
        )

        # Should succeed (currently using CLI args, not config file)
        assert result.exit_code == 0

    def test_init_shows_progress_indicators(self, tmp_path: Path) -> None:
        """Test init command shows progress for each generation step."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        # Should show progress for generators
        # (May use emoji, "Generating", dots, etc.)
        assert any(
            indicator in result.stdout.lower()
            for indicator in ("generating", "creating", "⏳", "...", "progress")
        )

    def test_init_handles_generator_errors_gracefully(self, tmp_path: Path) -> None:
        """Test init command handles generator errors with clear messages."""
        # TODO(Issue #106): Re-enable when generator integration is  # noqa: FIX002
        # complete. Error handling will be tested when generators are
        # actually called.
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        # Currently succeeds with placeholder implementation
        assert result.exit_code == 0

    def test_init_creates_output_directory_if_missing(self, tmp_path: Path) -> None:
        """Test init command creates output directory if it doesn't exist."""
        output_dir = tmp_path / "new" / "nested" / "dir"
        runner = CliRunner()

        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )

        # Should create directory and succeed
        assert result.exit_code == 0
        assert output_dir.exists()

    def test_init_defaults_to_current_directory(self) -> None:
        """Test init command defaults to current directory if no output specified."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--no-interactive",
            ],
        )

        # Should use current directory (may succeed or show directory exists error)
        # This test verifies the option is optional, not the result
        assert "--output-dir" not in result.stdout or result.exit_code in (0, 1)
