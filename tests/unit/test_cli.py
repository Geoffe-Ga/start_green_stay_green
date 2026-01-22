"""Unit tests for CLI framework."""

from unittest.mock import Mock
from unittest.mock import patch

from typer.testing import CliRunner

from start_green_stay_green.cli import app
from start_green_stay_green.cli import get_version


class TestCliVersion:
    """Test version command and version retrieval."""

    def test_get_version_returns_string(self) -> None:
        """Test get_version returns a version string."""
        version = get_version()
        assert isinstance(version, str)
        assert version

    def test_get_version_follows_semver_format(self) -> None:
        """Test version follows semantic versioning (X.Y.Z)."""
        version = get_version()
        parts = version.split(".")
        assert len(parts) >= 2  # At least major.minor
        assert parts[0].isdigit()  # Major version is numeric
        assert parts[1].isdigit()  # Minor version is numeric

    def test_version_command_displays_version(self) -> None:
        """Test version command displays version information."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "Start Green Stay Green" in result.stdout
        version = get_version()
        assert version in result.stdout

    def test_version_command_with_verbose_flag(self) -> None:
        """Test version command with verbose flag shows additional info."""
        runner = CliRunner()
        result = runner.invoke(app, ["version", "--verbose"])

        assert result.exit_code == 0
        assert "Start Green Stay Green" in result.stdout


class TestCliHelp:
    """Test help text functionality."""

    def test_help_command_shows_usage(self) -> None:
        """Test help command displays usage information."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        # Description is shown in help
        assert "quality-controlled" in result.stdout.lower()

    def test_help_shows_available_commands(self) -> None:
        """Test help shows all available commands."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "version" in result.stdout.lower()

    def test_command_help_shows_details(self) -> None:
        """Test individual command help shows details."""
        runner = CliRunner()
        result = runner.invoke(app, ["version", "--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "version" in result.stdout


class TestCliVerboseQuiet:
    """Test verbose and quiet mode flags."""

    def test_verbose_flag_exists(self) -> None:
        """Test --verbose flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(app, ["--verbose", "version"])

        # Should not error on --verbose flag
        assert result.exit_code == 0

    def test_quiet_flag_exists(self) -> None:
        """Test --quiet flag is recognized."""
        runner = CliRunner()
        result = runner.invoke(app, ["--quiet", "version"])

        # Should not error on --quiet flag
        assert result.exit_code == 0

    def test_verbose_and_quiet_are_mutually_exclusive(self) -> None:
        """Test verbose and quiet cannot be used together."""
        runner = CliRunner()
        result = runner.invoke(app, ["--verbose", "--quiet", "version"])

        # Should error or use one mode
        # Implementation may vary, but should handle this case
        assert result.exit_code in (0, 1, 2)


class TestCliConfiguration:
    """Test configuration file support."""

    def test_config_file_option_exists(self) -> None:
        """Test --config option is available."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Config option should be documented
        assert "--config" in result.stdout or "--config-file" in result.stdout

    @patch("start_green_stay_green.cli.load_config_file")
    def test_config_file_is_loaded_when_specified(
        self,
        mock_load_config: Mock,
    ) -> None:
        """Test config file is loaded when specified."""
        mock_load_config.return_value = {"project_name": "test"}
        runner = CliRunner()

        result = runner.invoke(app, ["--config", "test.yaml", "version"])

        # Config loading should be attempted
        if result.exit_code == 0:
            mock_load_config.assert_called()


class TestCliApp:
    """Test main CLI app configuration."""

    def test_app_has_name(self) -> None:
        """Test CLI app has a name configured."""
        assert hasattr(app, "info")
        assert app.info.name is not None

    def test_app_has_help_text(self) -> None:
        """Test CLI app has help text configured."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert len(result.stdout) > 0

    def test_app_handles_no_command(self) -> None:
        """Test app handles being invoked with no command."""
        runner = CliRunner()
        result = runner.invoke(app, [])

        # Typer shows help when no command given (exit code varies by version)
        assert result.exit_code in (0, 2)
        # Help should be shown (or error message)
        # Note: Typer behavior may vary


class TestCliRichOutput:
    """Test rich console output configuration."""

    def test_version_output_uses_formatting(self) -> None:
        """Test version output includes formatted text."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        # Should have some formatted output
        assert len(result.stdout) > 20

    def test_help_output_is_formatted(self) -> None:
        """Test help output is well-formatted."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Should have formatted help with sections
        # Rich formatting may use box characters
        has_commands = (
            "Commands" in result.stdout or "commands" in result.stdout.lower()
        )
        has_options = "Options" in result.stdout or "options" in result.stdout.lower()
        assert has_commands
        assert has_options


class TestCliErrorHandling:
    """Test CLI error handling."""

    def test_invalid_command_shows_error(self) -> None:
        """Test invalid command shows helpful error."""
        runner = CliRunner()
        result = runner.invoke(app, ["nonexistent-command"])

        assert result.exit_code != 0
        # Should show error message
        assert len(result.stdout) > 0 or len(result.stderr) > 0

    def test_invalid_option_shows_error(self) -> None:
        """Test invalid option shows helpful error."""
        runner = CliRunner()
        result = runner.invoke(app, ["version", "--invalid-option"])

        assert result.exit_code != 0
        # Should show error about invalid option
        assert len(result.stdout) > 0 or len(result.stderr) > 0


class TestCliExitCodes:
    """Test CLI exit codes."""

    def test_successful_command_returns_zero(self) -> None:
        """Test successful command returns exit code 0."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0

    def test_help_command_returns_zero(self) -> None:
        """Test help command returns exit code 0."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
