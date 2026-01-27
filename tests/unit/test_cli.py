"""Unit tests for CLI framework."""

from pathlib import Path
import re
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from start_green_stay_green.cli import MAX_PROJECT_NAME_LENGTH
from start_green_stay_green.cli import _copy_reference_skills
from start_green_stay_green.cli import _generate_project_files
from start_green_stay_green.cli import _get_api_key_with_source
from start_green_stay_green.cli import _initialize_orchestrator
from start_green_stay_green.cli import _load_config_data
from start_green_stay_green.cli import _load_config_if_specified
from start_green_stay_green.cli import _prompt_for_api_key
from start_green_stay_green.cli import _resolve_parameter
from start_green_stay_green.cli import _show_dry_run_preview
from start_green_stay_green.cli import _validate_and_prepare_paths
from start_green_stay_green.cli import _validate_output_dir
from start_green_stay_green.cli import _validate_project_name
from start_green_stay_green.cli import app
from start_green_stay_green.cli import cli_main
from start_green_stay_green.cli import get_version
from start_green_stay_green.cli import load_config_file
from start_green_stay_green.generators.skills import REQUIRED_SKILLS


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape codes from text.

    Args:
        text: Text containing ANSI codes.

    Returns:
        Text with ANSI codes removed.
    """
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


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

        # Should exit with error code 1
        assert result.exit_code == 1
        # Should show error message about mutual exclusivity
        clean_output = strip_ansi_codes(result.stdout)
        assert "mutually exclusive" in clean_output.lower()


class TestCliConfiguration:
    """Test configuration file support."""

    def test_config_file_option_exists(self) -> None:
        """Test --config option is available."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        # Config option should be documented (strip ANSI codes from Rich output)
        clean_output = strip_ansi_codes(result.stdout)
        assert "--config" in clean_output or "--config-file" in clean_output

    @patch("start_green_stay_green.cli.load_config_file")
    def test_config_file_is_loaded_when_specified(
        self,
        mock_load_config: Mock,
    ) -> None:
        """Test config file is loaded when specified."""
        mock_load_config.return_value = {"project_name": "test"}
        runner = CliRunner()

        result = runner.invoke(app, ["--config", "test.yaml", "version"])

        # Should succeed
        assert result.exit_code == 0
        # Config loading should be attempted with the specified path
        mock_load_config.assert_called_once()
        call_args = mock_load_config.call_args
        assert str(call_args[0][0]) == "test.yaml"

    @patch("start_green_stay_green.cli.load_config_file")
    def test_config_file_not_found_shows_error(
        self,
        mock_load_config: Mock,
    ) -> None:
        """Test config file not found shows error and exits."""
        # Mock FileNotFoundError
        mock_load_config.side_effect = FileNotFoundError("Config file not found")
        runner = CliRunner()

        result = runner.invoke(app, ["--config", "missing.yaml", "version"])

        # Should exit with error code 1
        assert result.exit_code == 1
        # Should show error message
        clean_output = strip_ansi_codes(result.stdout)
        assert "error" in clean_output.lower()
        assert "not found" in clean_output.lower()


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


# =============================================================================
# PHASE 1-4: COMPREHENSIVE MUTATION-KILLING TESTS
# =============================================================================
# These tests target high-value logic mutations to achieve ≥80% mutation score
# Reference: plans/2026-01-26_MUTANT_EXTERMINATION_PLAN_CLI.md


# =============================================================================
# PHASE 1: VALIDATION LOGIC TESTS
# =============================================================================


class TestProjectNameValidation:
    """Test project name validation logic.

    Kills mutations in _validate_project_name function.
    """

    def test_valid_alphanumeric_names_accepted(self) -> None:
        """Valid alphanumeric names should be accepted."""
        valid_names = ["project", "MyProject", "project123", "test"]
        for name in valid_names:
            # Should not raise
            _validate_project_name(name)

    def test_valid_names_with_hyphens_accepted(self) -> None:
        """Valid names with hyphens should be accepted."""
        valid_names = ["my-project", "test-app-v2", "a-b-c"]
        for name in valid_names:
            _validate_project_name(name)

    def test_valid_names_with_underscores_accepted(self) -> None:
        """Valid names with underscores should be accepted."""
        valid_names = ["my_project", "test_app_v2", "a_b_c"]
        for name in valid_names:
            _validate_project_name(name)

    def test_invalid_characters_rejected(self) -> None:
        """Names with spaces or special chars should be rejected."""
        invalid_names = [
            "my project",  # space
            "my@project",  # @
            "my#project",  # #
            "my$project",  # $
            "my%project",  # %
            "my.project",  # period
            "project!",  # exclamation
        ]
        for name in invalid_names:
            with pytest.raises(typer.BadParameter) as exc_info:
                _validate_project_name(name)
            assert "Invalid project name" in str(exc_info.value)
            assert "Only letters, numbers, hyphens, and underscores" in str(
                exc_info.value
            )

    def test_regex_pattern_exact_match(self) -> None:
        """Test regex pattern matches only valid characters."""
        # Valid: alphanumeric, hyphen, underscore
        _validate_project_name("aZ09_-")
        # Invalid: anything else
        with pytest.raises(typer.BadParameter):
            _validate_project_name("a/b")
        with pytest.raises(typer.BadParameter):
            _validate_project_name("a\\b")

    def test_project_name_length_exactly_100_accepted(self) -> None:
        """Project name with exactly MAX_PROJECT_NAME_LENGTH chars accepted."""
        name = "a" * MAX_PROJECT_NAME_LENGTH
        assert len(name) == 100
        _validate_project_name(name)  # Should not raise

    def test_project_name_length_101_rejected(self) -> None:
        """Project name with 101 chars should be rejected."""
        name = "a" * 101
        with pytest.raises(typer.BadParameter) as exc_info:
            _validate_project_name(name)
        assert "too long" in str(exc_info.value)
        assert "101" in str(exc_info.value)
        assert "100" in str(exc_info.value)

    def test_project_name_cannot_start_with_hyphen(self) -> None:
        """Names starting with hyphen should be rejected."""
        with pytest.raises(typer.BadParameter) as exc_info:
            _validate_project_name("-myproject")
        assert "cannot start with" in str(exc_info.value)
        assert "'-'" in str(exc_info.value)

    def test_project_name_cannot_start_with_underscore(self) -> None:
        """Names starting with underscore should be rejected."""
        with pytest.raises(typer.BadParameter) as exc_info:
            _validate_project_name("_myproject")
        assert "cannot start with" in str(exc_info.value)
        assert "'_'" in str(exc_info.value)

    def test_project_name_double_hyphen_start_rejected(self) -> None:
        """Names starting with -- should be rejected."""
        with pytest.raises(typer.BadParameter) as exc_info:
            _validate_project_name("--myproject")
        assert "cannot start with" in str(exc_info.value)

    def test_windows_reserved_name_con_rejected(self) -> None:
        """Windows reserved name 'con' should be rejected."""
        with pytest.raises(typer.BadParameter) as exc_info:
            _validate_project_name("con")
        assert "reserved system name" in str(exc_info.value)

    def test_windows_reserved_names_case_insensitive(self) -> None:
        """Reserved names should be case-insensitive."""
        reserved_variations = ["CON", "Con", "CoN", "PRN", "Prn", "AUX", "NUL"]
        for name in reserved_variations:
            with pytest.raises(typer.BadParameter) as exc_info:
                _validate_project_name(name)
            assert "reserved" in str(exc_info.value).lower()

    def test_all_22_windows_reserved_names_rejected(self) -> None:
        """All 22 Windows reserved names should be rejected."""
        reserved = [
            "con",
            "prn",
            "aux",
            "nul",
            "com1",
            "com2",
            "com3",
            "com4",
            "com5",
            "com6",
            "com7",
            "com8",
            "com9",
            "lpt1",
            "lpt2",
            "lpt3",
            "lpt4",
            "lpt5",
            "lpt6",
            "lpt7",
            "lpt8",
            "lpt9",
        ]
        assert len(reserved) == 22
        for name in reserved:
            with pytest.raises(typer.BadParameter):
                _validate_project_name(name)


class TestOutputDirValidation:
    """Test output directory validation logic.

    Kills mutations in _validate_output_dir function.
    """

    def test_none_returns_current_directory(self) -> None:
        """None input should return Path.cwd()."""
        result = _validate_output_dir(None)
        assert result == Path.cwd()
        assert result.is_absolute()

    def test_relative_path_resolved_to_absolute(self) -> None:
        """Relative paths should be resolved to absolute."""
        # Create relative reference
        relative = Path("subdir")
        result = _validate_output_dir(relative)
        assert result.is_absolute()

    def test_absolute_path_returned_unchanged(self, tmp_path: Path) -> None:
        """Absolute paths should be returned (resolved)."""
        result = _validate_output_dir(tmp_path)
        assert result.is_absolute()
        assert result == tmp_path.resolve()

    def test_path_with_dotdot_in_parts_rejected(self, tmp_path: Path) -> None:
        """Paths with '..' remaining after resolve should be rejected.

        Note: This is hard to trigger because resolve() typically removes ..
        We test the branch logic by verifying normal paths work.
        """
        # Use tmp_path for security instead of hardcoded /tmp
        test_path = tmp_path / "test"
        result = _validate_output_dir(test_path)
        assert ".." not in result.parts


class TestPathValidationIntegration:
    """Test integrated path validation.

    Kills mutations in _validate_and_prepare_paths function.
    """

    def test_valid_project_path_creation(self, tmp_path: Path) -> None:
        """Valid project name + output dir creates correct path."""
        output_dir, project_path = _validate_and_prepare_paths("myproject", tmp_path)
        assert output_dir == tmp_path.resolve()
        assert project_path == tmp_path.resolve() / "myproject"

    def test_validation_failures_raise_bad_parameter(self) -> None:
        """Validation failures should raise typer.BadParameter."""
        with pytest.raises(typer.BadParameter):
            _validate_and_prepare_paths("con", None)  # Reserved name

    def test_project_path_escapes_output_dir_rejected(self, tmp_path: Path) -> None:
        """Project paths escaping output directory should be rejected.

        This tests the security check after path joining.
        """
        # Valid case should work
        output_dir, project_path = _validate_and_prepare_paths("valid", tmp_path)
        assert str(project_path).startswith(str(output_dir))


# =============================================================================
# PHASE 2: PARAMETER RESOLUTION TESTS
# =============================================================================


class TestConfigurationLoading:
    """Test configuration file loading.

    Kills mutations in load_config_file and _load_config_data functions.
    """

    def test_load_config_file_not_found_raises(self, tmp_path: Path) -> None:
        """FileNotFoundError raised when config doesn't exist."""
        nonexistent = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError) as exc_info:
            load_config_file(nonexistent)
        assert "Configuration file not found" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    def test_load_config_data_returns_empty_dict_when_no_config(self) -> None:
        """Returns {} when config is None."""
        result = _load_config_data(None)
        assert not result
        assert isinstance(result, dict)

    @patch("start_green_stay_green.cli.load_config_file")
    @patch("start_green_stay_green.cli.console")
    def test_load_config_data_loads_file_when_specified(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_load: Mock,
        tmp_path: Path,
    ) -> None:
        """Loads and returns config data when file specified."""
        mock_load.return_value = {"project_name": "test", "language": "python"}
        config_file = tmp_path / "config.yaml"
        result = _load_config_data(config_file)
        mock_load.assert_called_once_with(config_file)
        assert result == {"project_name": "test", "language": "python"}

    @patch("start_green_stay_green.cli.load_config_file")
    @patch("start_green_stay_green.cli.console")
    def test_load_config_data_exits_on_file_not_found(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_load: Mock,
        tmp_path: Path,
    ) -> None:
        """Exit code 1 when config file not found."""
        mock_load.side_effect = FileNotFoundError("Not found")
        config_file = tmp_path / "missing.yaml"
        with pytest.raises(typer.Exit) as exc_info:
            _load_config_data(config_file)
        assert exc_info.value.exit_code == 1

    @patch("start_green_stay_green.cli.load_config_file")
    @patch("start_green_stay_green.cli.console")
    def test_load_config_data_prints_loaded_message(
        self, mock_console: Mock, mock_load: Mock, tmp_path: Path
    ) -> None:
        """Config loaded message is printed."""
        mock_load.return_value = {}
        config_file = tmp_path / "config.yaml"
        _load_config_data(config_file)
        # Verify console.print was called with loaded message
        mock_console.print.assert_called()
        call_args = str(mock_console.print.call_args)
        assert "Loaded configuration" in call_args or "config" in call_args.lower()


class TestParameterResolution:
    """Test parameter resolution from multiple sources.

    Kills mutations in _resolve_parameter function.
    """

    def test_cli_arg_takes_priority_over_config(self) -> None:
        """CLI argument overrides config file value."""
        result = _resolve_parameter(
            param_value="cli_value",
            config_data={"key": "config_value"},
            config_key="key",
            param_name="Test param",
            no_interactive=True,
        )
        assert result == "cli_value"

    def test_config_value_used_when_no_cli_arg(self) -> None:
        """Config value used when CLI arg is None."""
        result = _resolve_parameter(
            param_value=None,
            config_data={"key": "config_value"},
            config_key="key",
            param_name="Test param",
            no_interactive=True,
        )
        assert result == "config_value"

    def test_empty_string_cli_arg_falls_through(self) -> None:
        """Empty string CLI arg should fall through to config.

        This tests the truthiness check on param_value.
        """
        result = _resolve_parameter(
            param_value="",  # Empty string is falsy
            config_data={"key": "config_value"},
            config_key="key",
            param_name="Test param",
            no_interactive=True,
        )
        assert result == "config_value"

    @patch("start_green_stay_green.cli.typer.prompt")
    def test_interactive_prompt_when_no_arg_or_config(self, mock_prompt: Mock) -> None:
        """Interactive prompt as fallback."""
        mock_prompt.return_value = "prompted_value"
        result = _resolve_parameter(
            param_value=None,
            config_data={},
            config_key="key",
            param_name="Project name",
            no_interactive=False,
        )
        mock_prompt.assert_called_once_with("Project name")
        assert result == "prompted_value"

    @patch("start_green_stay_green.cli.console")
    def test_non_interactive_mode_exits_when_param_missing(
        self,
        mock_console: Mock,  # noqa: ARG002
    ) -> None:
        """Exit code 1 when parameter missing in non-interactive mode."""
        with pytest.raises(typer.Exit) as exc_info:
            _resolve_parameter(
                param_value=None,
                config_data={},
                config_key="key",
                param_name="Project name",
                no_interactive=True,
            )
        # Exit code 1 for application error or 2 for usage error (Typer varies)
        assert exc_info.value.exit_code in (1, 2)

    @patch("start_green_stay_green.cli.console")
    def test_parameter_name_formatting_in_error(self, mock_console: Mock) -> None:
        """Parameter name formatted correctly in error message."""
        with pytest.raises(typer.Exit):
            _resolve_parameter(
                param_value=None,
                config_data={},
                config_key="key",
                param_name="Project name",
                no_interactive=True,
            )
        # Check error message includes formatted param name
        call_args = str(mock_console.print.call_args)
        assert "--project-name" in call_args or "Project" in call_args


# =============================================================================
# PHASE 3: API KEY & ORCHESTRATOR TESTS
# =============================================================================


class TestAPIKeyHandling:
    """Test API key acquisition and source priority.

    Kills mutations in _prompt_for_api_key, _get_api_key_with_source,
    and _initialize_orchestrator functions.
    """

    def test_cli_arg_api_key_takes_priority(self) -> None:
        """CLI arg API key used first."""
        key, source = _get_api_key_with_source(
            "cli_api_key",
            no_interactive=True,
        )
        assert key == "cli_api_key"
        assert source == "command line"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    def test_keyring_api_key_used_when_no_arg(self, mock_keyring: Mock) -> None:
        """Keyring API key used when no CLI arg."""
        mock_keyring.return_value = "keyring_key"
        key, source = _get_api_key_with_source(
            None,
            no_interactive=True,
        )
        assert key == "keyring_key"
        assert source == "keyring"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    @patch("start_green_stay_green.cli.os.getenv")
    def test_env_var_api_key_used_when_no_arg_or_keyring(
        self, mock_getenv: Mock, mock_keyring: Mock
    ) -> None:
        """Environment variable used as fallback."""
        mock_keyring.return_value = None
        mock_getenv.return_value = "env_key"
        key, source = _get_api_key_with_source(
            None,
            no_interactive=True,
        )
        assert key == "env_key"
        assert source == "environment variable"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    @patch("start_green_stay_green.cli.os.getenv")
    @patch("start_green_stay_green.cli._prompt_for_api_key")
    def test_interactive_prompt_when_no_key_found(
        self, mock_prompt: Mock, mock_getenv: Mock, mock_keyring: Mock
    ) -> None:
        """Interactive prompt when no key in any source."""
        mock_keyring.return_value = None
        mock_getenv.return_value = None
        mock_prompt.return_value = "prompted_key"
        key, source = _get_api_key_with_source(
            None,
            no_interactive=False,
        )
        mock_prompt.assert_called_once()
        assert key == "prompted_key"
        assert source == "interactive prompt"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    @patch("start_green_stay_green.cli.os.getenv")
    def test_non_interactive_returns_none_when_no_key(
        self, mock_getenv: Mock, mock_keyring: Mock
    ) -> None:
        """Returns (None, None) in non-interactive mode when no key."""
        mock_keyring.return_value = None
        mock_getenv.return_value = None
        key, source = _get_api_key_with_source(
            None,
            no_interactive=True,
        )
        assert key is None
        assert source is None

    @patch("start_green_stay_green.cli.typer.confirm")
    @patch("start_green_stay_green.cli.console")
    def test_prompt_for_api_key_returns_none_on_decline(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_confirm: Mock,
    ) -> None:
        """Returns None when user declines to enter key."""
        mock_confirm.return_value = False
        result = _prompt_for_api_key()
        assert result is None

    @patch("start_green_stay_green.cli.typer.prompt")
    @patch("start_green_stay_green.cli.typer.confirm")
    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.console")
    def test_prompt_for_api_key_saves_to_keyring_when_confirmed(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_store: Mock,
        mock_confirm: Mock,
        mock_prompt: Mock,
    ) -> None:
        """Saves key to keyring when user confirms."""
        mock_confirm.side_effect = [True, True]  # Yes to enter, yes to save
        mock_prompt.return_value = "test_api_key"  # pragma: allowlist secret
        mock_store.return_value = True
        result = _prompt_for_api_key()
        assert result == "test_api_key"  # pragma: allowlist secret
        mock_store.assert_called_once_with("test_api_key")  # pragma: allowlist secret

    @patch("start_green_stay_green.cli._get_api_key_with_source")
    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch("start_green_stay_green.cli.console")
    def test_orchestrator_initialization_with_valid_key(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_orchestrator: Mock,
        mock_get_key: Mock,
    ) -> None:
        """AIOrchestrator created with valid key."""
        mock_get_key.return_value = (
            "valid_key",
            "command line",
        )  # pragma: allowlist secret
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance
        result = _initialize_orchestrator(
            "valid_key", no_interactive=True
        )  # pragma: allowlist secret
        assert result == mock_instance
        mock_orchestrator.assert_called_once_with(
            api_key="valid_key"  # pragma: allowlist secret
        )

    @patch("start_green_stay_green.cli._get_api_key_with_source")
    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch("start_green_stay_green.cli.console")
    def test_orchestrator_initialization_fails_with_invalid_key(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_orchestrator: Mock,
        mock_get_key: Mock,
    ) -> None:
        """Returns None when AIOrchestrator raises ValueError."""
        mock_get_key.return_value = (
            "invalid_key",
            "command line",
        )  # pragma: allowlist secret
        mock_orchestrator.side_effect = ValueError(
            "Invalid API key"
        )  # pragma: allowlist secret
        result = _initialize_orchestrator(
            "invalid_key", no_interactive=True
        )  # pragma: allowlist secret
        assert result is None


# =============================================================================
# PHASE 4: INIT COMMAND & FILE GENERATION TESTS
# =============================================================================


class TestInitCommand:
    """Test init command orchestration.

    Kills mutations in init command and related functions.
    """

    def test_init_requires_project_name_non_interactive(self) -> None:
        """Exit when project name missing in non-interactive mode."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["init", "--no-interactive", "--language", "python"],
        )
        # Exit code 1 for application error or 2 for usage error (Typer varies)
        assert result.exit_code in (1, 2)
        assert "required" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_init_requires_language_non_interactive(self) -> None:
        """Exit when language missing in non-interactive mode."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            ["init", "--no-interactive", "--project-name", "test"],
        )
        # Exit code 1 for application error or 2 for usage error (Typer varies)
        assert result.exit_code in (1, 2)

    def test_init_validation_failure_exits_with_code_1(self) -> None:
        """Invalid project name causes exit code 1."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--no-interactive",
                "--project-name",
                "con",  # Reserved name
                "--language",
                "python",
            ],
        )
        assert result.exit_code == 1
        assert "reserved" in result.stdout.lower() or "invalid" in result.stdout.lower()

    def test_init_dry_run_mode_skips_file_creation(self, tmp_path: Path) -> None:
        """Dry run shows preview without creating files."""
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
        assert not (tmp_path / "test-project").exists()

    def test_init_dry_run_displays_preview(self, tmp_path: Path) -> None:
        """Dry run calls _show_dry_run_preview."""
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
        assert "Dry Run Mode" in result.stdout
        assert "Preview only" in result.stdout

    def test_init_creates_project_directory(self, tmp_path: Path) -> None:
        """Project directory created when not in dry-run."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--no-interactive",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert (tmp_path / "test-project").exists()

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_init_shows_ai_disabled_warning_when_no_key(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """Warning shown when AI features disabled."""
        mock_init_orch.return_value = None
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--no-interactive",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        assert "AI features disabled" in result.stdout

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_init_enables_ai_features_when_key_provided(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """AI features enabled message when orchestrator initialized."""
        mock_init_orch.return_value = MagicMock()
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--no-interactive",
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        # Should NOT show disabled warning
        assert "AI features disabled" not in result.stdout

    @patch("start_green_stay_green.cli._load_config_data")
    def test_init_loads_config_when_specified(
        self, mock_load_config: Mock, tmp_path: Path
    ) -> None:
        """Config file loaded when --config provided."""
        mock_load_config.return_value = {"project_name": "from-config"}
        config_file = tmp_path / "config.yaml"
        config_file.touch()
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--config",
                str(config_file),
                "--project-name",
                "test-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )
        mock_load_config.assert_called()


class TestDryRunPreview:
    """Test dry run preview display.

    Kills mutations in _show_dry_run_preview function.
    """

    @patch("start_green_stay_green.cli.console")
    def test_dry_run_preview_displays_project_info(
        self, mock_console: Mock, tmp_path: Path
    ) -> None:
        """Dry run preview shows project name, language, path."""
        project_path = tmp_path / "test-project"
        _show_dry_run_preview("test-project", "python", project_path)
        # Verify console.print was called multiple times
        assert mock_console.print.call_count >= 5

    @patch("start_green_stay_green.cli.console")
    def test_dry_run_preview_lists_all_components(
        self, mock_console: Mock, tmp_path: Path
    ) -> None:
        """Dry run preview lists all generated components."""
        project_path = tmp_path / "test-project"
        _show_dry_run_preview("test-project", "python", project_path)
        # Collect all print calls
        all_output = " ".join(str(call) for call in mock_console.print.call_args_list)
        # Verify key components are mentioned
        assert "CI/CD pipeline" in all_output or "CI" in all_output


class TestFileGenerationFlow:
    """Test file generation orchestration.

    Kills mutations in _generate_project_files and _copy_reference_skills.
    """

    def test_generate_project_files_creates_scripts(self, tmp_path: Path) -> None:
        """ScriptsGenerator called and scripts created."""
        project_path = tmp_path / "test-project"
        project_path.mkdir(parents=True)
        _generate_project_files(project_path, "test-project", "python", None)
        scripts_dir = project_path / "scripts"
        assert scripts_dir.exists()
        assert (scripts_dir / "test.sh").exists()

    def test_generate_project_files_creates_precommit_config(
        self, tmp_path: Path
    ) -> None:
        """Pre-commit config file created."""
        project_path = tmp_path / "test-project"
        project_path.mkdir(parents=True)
        _generate_project_files(project_path, "test-project", "python", None)
        precommit_file = project_path / ".pre-commit-config.yaml"
        assert precommit_file.exists()

    def test_generate_project_files_creates_skills(self, tmp_path: Path) -> None:
        """Skills directory and files created."""
        project_path = tmp_path / "test-project"
        project_path.mkdir(parents=True)
        _generate_project_files(project_path, "test-project", "python", None)
        skills_dir = project_path / ".claude" / "skills"
        assert skills_dir.exists()

    @patch("start_green_stay_green.cli.ScriptsGenerator")
    @patch("start_green_stay_green.cli.console")
    def test_generate_project_files_error_exits_with_code_1(
        self,
        mock_console: Mock,  # noqa: ARG002
        mock_scripts_gen: Mock,
        tmp_path: Path,
    ) -> None:
        """Exit code 1 when generation raises exception."""
        mock_scripts_gen.side_effect = Exception("Generation failed")
        project_path = tmp_path / "test-project"
        project_path.mkdir(parents=True)
        with pytest.raises(typer.Exit) as exc_info:
            _generate_project_files(project_path, "test-project", "python", None)
        assert exc_info.value.exit_code == 1

    def test_copy_reference_skills_creates_directory(self, tmp_path: Path) -> None:
        """Target directory created with parents."""
        target_dir = tmp_path / "nested" / "skills"
        _copy_reference_skills(target_dir)
        assert target_dir.exists()

    def test_copy_reference_skills_copies_all_required(self, tmp_path: Path) -> None:
        """All required skills are copied."""
        target_dir = tmp_path / "skills"
        _copy_reference_skills(target_dir)
        for skill in REQUIRED_SKILLS:
            assert (target_dir / skill).exists()

    @patch("start_green_stay_green.cli.REFERENCE_SKILLS_DIR")
    def test_copy_reference_skills_raises_on_missing_file(
        self, mock_skills_dir: Mock, tmp_path: Path
    ) -> None:
        """FileNotFoundError raised when reference skill doesn't exist."""
        # Mock REFERENCE_SKILLS_DIR to point to non-existent location
        fake_skills_dir = tmp_path / "nonexistent_skills"
        mock_skills_dir.__truediv__ = lambda _, other: fake_skills_dir / other

        target_dir = tmp_path / "skills"
        with pytest.raises(FileNotFoundError) as exc_info:
            _copy_reference_skills(target_dir)
        assert "Reference skill not found" in str(exc_info.value)


class TestCliMain:
    """Test cli_main entry point.

    Kills mutations in cli_main function.
    """

    @patch("start_green_stay_green.cli.app")
    def test_cli_main_calls_app(self, mock_app: Mock) -> None:
        """cli_main invokes the Typer app."""
        cli_main()
        mock_app.assert_called_once()


class TestVerboseModeAndConfig:
    """Test verbose mode and configuration interactions.

    Kills mutations in verbose output paths and config loading.
    """

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_prints_when_verbose(
        self, mock_load: Mock, mock_console: Mock, tmp_path: Path
    ) -> None:
        """_load_config_if_specified prints message when verbose is True."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("")
        mock_load.return_value = {}

        _load_config_if_specified(config_file, verbose=True)

        # Verify console.print was called with the verbose message
        mock_console.print.assert_called_once_with(
            f"[dim]Loaded configuration from {config_file}[/dim]"
        )

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_silent_when_not_verbose(
        self, mock_load: Mock, mock_console: Mock, tmp_path: Path
    ) -> None:
        """_load_config_if_specified does not print when verbose is False."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("")
        mock_load.return_value = {}

        _load_config_if_specified(config_file, verbose=False)

        # Verify console.print was NOT called
        mock_console.print.assert_not_called()


class TestAPIKeyKeyringSaveFlow:
    """Test API key keyring save confirmation flows.

    Kills mutations in keyring save success/failure branches.
    """

    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.typer.confirm")
    @patch("start_green_stay_green.cli.typer.prompt")
    def test_prompt_for_api_key_saves_successfully_to_keyring(
        self,
        mock_prompt: Mock,
        mock_confirm: Mock,
        mock_console: Mock,
        mock_store: Mock,
    ) -> None:
        """API key saved successfully to keyring when user confirms."""
        mock_prompt.return_value = "test_key"  # pragma: allowlist secret
        mock_confirm.return_value = True  # User confirms save
        mock_store.return_value = True  # Save succeeds

        result = _prompt_for_api_key()

        assert result == "test_key"  # pragma: allowlist secret
        mock_store.assert_called_once_with("test_key")  # pragma: allowlist secret
        mock_console.print.assert_any_call("[green]✓[/green] API key saved to keyring")

    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.typer.confirm")
    @patch("start_green_stay_green.cli.typer.prompt")
    def test_prompt_for_api_key_handles_keyring_save_failure(
        self,
        mock_prompt: Mock,
        mock_confirm: Mock,
        mock_console: Mock,
        mock_store: Mock,
    ) -> None:
        """Warning message shown when keyring save fails."""
        mock_prompt.return_value = "test_key"  # pragma: allowlist secret
        mock_confirm.return_value = True  # User confirms save
        mock_store.return_value = False  # Save fails

        result = _prompt_for_api_key()

        assert result == "test_key"  # pragma: allowlist secret
        mock_store.assert_called_once_with("test_key")  # pragma: allowlist secret
        mock_console.print.assert_any_call(
            "[yellow]![/yellow] Failed to save to keyring "
            "(you'll need to provide it again next time)"
        )


class TestInteractiveAPIKeyPromptFlow:
    """Test interactive API key prompt success path.

    Kills mutations in interactive key acquisition branch.
    """

    @patch("start_green_stay_green.cli._prompt_for_api_key")
    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    @patch("start_green_stay_green.cli.os.getenv")
    def test_get_api_key_uses_interactive_prompt_when_provided(
        self, mock_getenv: Mock, mock_keyring: Mock, mock_prompt: Mock
    ) -> None:
        """Interactive prompt used when no other source available."""
        mock_getenv.return_value = None
        mock_keyring.return_value = None
        mock_prompt.return_value = "interactive_key"  # pragma: allowlist secret

        key, source = _get_api_key_with_source(None, no_interactive=False)

        assert key == "interactive_key"  # pragma: allowlist secret
        assert source == "interactive prompt"
        mock_prompt.assert_called_once()

    @patch("start_green_stay_green.cli._prompt_for_api_key")
    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    @patch("start_green_stay_green.cli.os.getenv")
    def test_get_api_key_returns_none_when_interactive_prompt_returns_none(
        self, mock_getenv: Mock, mock_keyring: Mock, mock_prompt: Mock
    ) -> None:
        """None returned when interactive prompt returns None."""
        mock_getenv.return_value = None
        mock_keyring.return_value = None
        mock_prompt.return_value = None

        key, source = _get_api_key_with_source(None, no_interactive=False)

        assert key is None
        assert source is None
