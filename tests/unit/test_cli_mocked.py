"""Mock-based tests for CLI module - fast, no CliRunner.

This module replaces the slow CliRunner-based tests with fast mock-based tests.
Tests CLI behavior by mocking dependencies instead of running full CLI.

## Mocking Patterns Used

### Path Mocking
- Use `MagicMock()` for Path objects instead of `tmp_path`
- Mock `Path.exists()`, `Path.resolve()`, `Path.mkdir()`, etc.
- Mock path operations with `.side_effect` or `.return_value`

### File Operation Mocking
- Mock `Path.read_text()` instead of creating actual files
- Mock `Path.write_text()` instead of writing to disk
- This improves test isolation and performance

### Example Pattern
```python
@patch('pathlib.Path')
def test_something(mock_path: Mock) -> None:
    mock_instance = mock_path.return_value
    mock_instance.exists.return_value = True
    mock_instance.read_text.return_value = "content"
    # Test code here
```
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import typer

from start_green_stay_green import cli


class TestVersionCommand:
    """Test version-related functionality."""

    def test_get_version_returns_version_string(self) -> None:
        """Test get_version returns __version__."""
        version = cli.get_version()
        assert isinstance(version, str)
        assert version == "1.0.0"

    def test_get_version_is_semantic_versioning(self) -> None:
        """Test get_version returns valid semantic version."""
        version = cli.get_version()
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)


class TestConfigLoading:
    """Test configuration file loading."""

    def test_load_config_file_raises_on_missing_file(self) -> None:
        """Test load_config_file raises FileNotFoundError for missing file."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            cli.load_config_file(mock_path)

    def test_load_config_file_checks_path_exists(self) -> None:
        """Test load_config_file calls exists() on the path."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        with pytest.raises(FileNotFoundError):
            cli.load_config_file(mock_path)
        mock_path.exists.assert_called_once()

    def test_load_config_file_returns_empty_dict_when_file_exists(self) -> None:
        """Test load_config_file returns empty dict (stub implementation)."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        result = cli.load_config_file(mock_path)
        assert not result
        assert isinstance(result, dict)

    def test_load_config_file_path_string_in_error_message(self) -> None:
        """Test error message includes the file path."""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            cli.load_config_file(mock_path)


class TestValidation:
    """Test validation functions."""

    def test_validate_options_accepts_verbose_only(self) -> None:
        """Test _validate_options accepts verbose=True, quiet=False."""
        cli._validate_options(verbose=True, quiet=False)  # Should not raise

    def test_validate_options_accepts_quiet_only(self) -> None:
        """Test _validate_options accepts verbose=False, quiet=True."""
        cli._validate_options(verbose=False, quiet=True)  # Should not raise

    def test_validate_options_accepts_neither(self) -> None:
        """Test _validate_options accepts verbose=False, quiet=False."""
        cli._validate_options(verbose=False, quiet=False)  # Should not raise

    @patch("start_green_stay_green.cli.console")
    def test_validate_options_rejects_both_verbose_and_quiet(
        self, mock_console: Mock
    ) -> None:
        """Test _validate_options raises Exit when both verbose and quiet are True."""
        with pytest.raises(typer.Exit) as exc_info:
            cli._validate_options(verbose=True, quiet=True)
        assert exc_info.value.exit_code == 1
        mock_console.print.assert_called_once()
        # Verify error message contains key words
        call_args = mock_console.print.call_args
        assert "mutually exclusive" in call_args[0][0]

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_loads_when_config_provided(
        self, mock_load: Mock
    ) -> None:
        """Test _load_config_if_specified calls load_config_file."""
        mock_load.return_value = {}
        mock_config_path = MagicMock(spec=Path)
        cli._load_config_if_specified(mock_config_path, verbose=False)
        mock_load.assert_called_once_with(mock_config_path)

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_does_nothing_when_none(
        self, mock_load: Mock
    ) -> None:
        """Test _load_config_if_specified does nothing when config is None."""
        cli._load_config_if_specified(None, verbose=False)
        mock_load.assert_not_called()

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_exits_on_file_not_found(
        self, mock_load: Mock, mock_console: Mock
    ) -> None:
        """Test _load_config_if_specified exits when config file not found."""
        mock_load.side_effect = FileNotFoundError("Not found")
        mock_config_path = MagicMock(spec=Path)
        with pytest.raises(typer.Exit) as exc_info:
            cli._load_config_if_specified(mock_config_path, verbose=False)
        assert exc_info.value.exit_code == 1
        mock_console.print.assert_called()

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_prints_verbose_message(
        self, mock_load: Mock, mock_console: Mock
    ) -> None:
        """Test _load_config_if_specified prints message in verbose mode."""
        mock_load.return_value = {}
        mock_config_path = MagicMock(spec=Path)
        cli._load_config_if_specified(mock_config_path, verbose=True)
        assert mock_console.print.call_count == 1

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_no_verbose_message_when_not_verbose(
        self, mock_load: Mock, mock_console: Mock
    ) -> None:
        """Test _load_config_if_specified doesn't print when verbose=False."""
        mock_load.return_value = {}
        mock_config_path = MagicMock(spec=Path)
        cli._load_config_if_specified(mock_config_path, verbose=False)
        mock_console.print.assert_not_called()


class TestProjectNameValidation:
    """Test project name validation."""

    def test_validate_project_name_accepts_valid_names(self) -> None:
        """Test _validate_project_name accepts valid project names."""
        valid_names = [
            "my-project",
            "my_project",
            "MyProject",
            "project123",
            "a",
            "a-b-c",
        ]
        for name in valid_names:
            cli._validate_project_name(name)  # Should not raise

    def test_validate_project_name_accepts_long_valid_name(self) -> None:
        """Test _validate_project_name accepts long valid names."""
        # Create a valid name that's within the limit
        long_name = "a" * cli.MAX_PROJECT_NAME_LENGTH
        cli._validate_project_name(long_name)  # Should not raise

    def test_validate_project_name_rejects_empty_string(self) -> None:
        """Test _validate_project_name rejects empty string."""
        with pytest.raises(typer.BadParameter):
            cli._validate_project_name("")

    def test_validate_project_name_rejects_invalid_chars(self) -> None:
        """Test _validate_project_name rejects invalid characters."""
        invalid_names = ["my project", "my@project", "my#project", "my.project"]
        for name in invalid_names:
            with pytest.raises(typer.BadParameter):
                cli._validate_project_name(name)

    def test_validate_project_name_rejects_leading_hyphen(self) -> None:
        """Test _validate_project_name rejects names starting with hyphen."""
        with pytest.raises(typer.BadParameter):
            cli._validate_project_name("-project")

    def test_validate_project_name_rejects_leading_underscore(self) -> None:
        """Test _validate_project_name rejects names starting with underscore."""
        with pytest.raises(typer.BadParameter):
            cli._validate_project_name("_project")

    def test_validate_project_name_rejects_too_long_name(self) -> None:
        """Test _validate_project_name rejects names exceeding max length."""
        too_long_name = "a" * (cli.MAX_PROJECT_NAME_LENGTH + 1)
        with pytest.raises(typer.BadParameter):
            cli._validate_project_name(too_long_name)

    def test_validate_project_name_rejects_windows_reserved_names(self) -> None:
        """Test _validate_project_name rejects Windows reserved names."""
        reserved_names = ["con", "prn", "aux", "nul", "COM1", "LPT1"]
        for name in reserved_names:
            with pytest.raises(typer.BadParameter):
                cli._validate_project_name(name)


class TestOutputDirValidation:
    """Test output directory validation."""

    def test_validate_output_dir_accepts_path(self, tmp_path: Path) -> None:
        """Test _validate_output_dir accepts valid path."""
        result = cli._validate_output_dir(tmp_path)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_validate_output_dir_defaults_to_cwd_when_none(self) -> None:
        """Test _validate_output_dir returns current working directory when None."""
        result = cli._validate_output_dir(None)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_validate_output_dir_calls_resolve(self) -> None:
        """Test _validate_output_dir calls resolve() on path."""
        mock_path = MagicMock(spec=Path)
        mock_resolved = MagicMock(spec=Path)
        mock_resolved.parts = ("a", "b", "c")
        mock_path.resolve.return_value = mock_resolved

        cli._validate_output_dir(mock_path)
        mock_path.resolve.assert_called()

    def test_validate_output_dir_rejects_path_traversal(self) -> None:
        """Test _validate_output_dir rejects paths with '..' after resolution."""
        mock_path = MagicMock(spec=Path)
        mock_path.resolve.return_value = MagicMock(
            spec=Path, parts=("a", "b", "..", "c")
        )
        with pytest.raises(typer.BadParameter):
            cli._validate_output_dir(mock_path)


class TestAPIKeyHandling:
    """Test API key handling functionality."""

    @patch("start_green_stay_green.cli.typer.confirm")
    def test_prompt_for_api_key_returns_none_when_declined(
        self, mock_confirm: Mock
    ) -> None:
        """Test _prompt_for_api_key returns None when user declines."""
        mock_confirm.return_value = False
        result = cli._prompt_for_api_key()
        assert result is None

    @patch("start_green_stay_green.cli.typer.prompt")
    @patch("start_green_stay_green.cli.typer.confirm")
    def test_prompt_for_api_key_returns_key(
        self,
        mock_confirm: Mock,
        mock_prompt: Mock,
    ) -> None:
        """Test _prompt_for_api_key returns user input."""
        mock_confirm.side_effect = [True, False]  # Confirm enter key, decline save
        mock_prompt.return_value = "user-entered-key"
        result = cli._prompt_for_api_key()
        assert result == "user-entered-key"

    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.typer.prompt")
    @patch("start_green_stay_green.cli.typer.confirm")
    def test_prompt_for_api_key_saves_to_keyring_when_accepted(
        self,
        mock_confirm: Mock,
        mock_prompt: Mock,
        mock_store: Mock,
    ) -> None:
        """Test _prompt_for_api_key saves to keyring when user accepts."""
        mock_confirm.side_effect = [True, True]  # Confirm enter key, accept save
        mock_prompt.return_value = "user-key"
        mock_store.return_value = True
        result = cli._prompt_for_api_key()
        assert result == "user-key"
        mock_store.assert_called_once_with("user-key")

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.typer.prompt")
    @patch("start_green_stay_green.cli.typer.confirm")
    def test_prompt_for_api_key_shows_success_message_on_keyring_save(
        self,
        mock_confirm: Mock,
        mock_prompt: Mock,
        mock_store: Mock,
        mock_console: Mock,
    ) -> None:
        """Test _prompt_for_api_key prints success message when saved to keyring."""
        mock_confirm.side_effect = [True, True]
        mock_prompt.return_value = "key"
        mock_store.return_value = True
        cli._prompt_for_api_key()
        # Check that console.print was called with success message
        calls = [str(call_args) for call_args in mock_console.print.call_args_list]
        assert any("✓" in call or "success" in call.lower() for call in calls)

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.store_api_key_in_keyring")
    @patch("start_green_stay_green.cli.typer.prompt")
    @patch("start_green_stay_green.cli.typer.confirm")
    def test_prompt_for_api_key_shows_warning_on_keyring_failure(
        self,
        mock_confirm: Mock,
        mock_prompt: Mock,
        mock_store: Mock,
        mock_console: Mock,
    ) -> None:
        """Test _prompt_for_api_key prints warning when keyring save fails."""
        mock_confirm.side_effect = [True, True]
        mock_prompt.return_value = "key"
        mock_store.return_value = False
        cli._prompt_for_api_key()
        # Check that console.print was called with warning message
        calls = [str(call_args) for call_args in mock_console.print.call_args_list]
        assert any("Failed" in call or "warning" in call.lower() for call in calls)


class TestPathValidation:
    """Test path validation and preparation."""

    def test_validate_and_prepare_paths_creates_valid_paths(
        self, tmp_path: Path
    ) -> None:
        """Test _validate_and_prepare_paths creates valid output paths."""
        output_dir = tmp_path / "output"
        target_dir, project_path = cli._validate_and_prepare_paths(
            "my-project", output_dir
        )
        assert isinstance(target_dir, Path)
        assert isinstance(project_path, Path)
        assert project_path.name == "my-project"

    def test_validate_and_prepare_paths_validates_project_name(
        self, tmp_path: Path
    ) -> None:
        """Test _validate_and_prepare_paths validates project name."""
        with pytest.raises(typer.BadParameter):
            cli._validate_and_prepare_paths("invalid!", tmp_path)

    def test_validate_and_prepare_paths_validates_output_dir(self) -> None:
        """Test _validate_and_prepare_paths validates output directory."""
        mock_path = MagicMock(spec=Path)
        mock_path.resolve.return_value = MagicMock(
            spec=Path, parts=("a", "b", "..", "c")
        )
        with pytest.raises(typer.BadParameter):
            cli._validate_and_prepare_paths("my-project", mock_path)

    @patch("start_green_stay_green.cli._validate_output_dir")
    def test_validate_and_prepare_paths_returns_project_path_correctly(
        self, mock_validate_dir: Mock
    ) -> None:
        """Test _validate_and_prepare_paths returns correct project path."""
        mock_output_dir = MagicMock(spec=Path)
        mock_project_dir = MagicMock(spec=Path)
        mock_output_dir.__truediv__.return_value = mock_project_dir
        mock_validate_dir.return_value = mock_output_dir

        # Setup resolve to return proper paths that won't trigger escape check
        mock_project_resolved = MagicMock(spec=Path)
        mock_output_resolved = MagicMock(spec=Path)
        mock_project_dir.resolve.return_value = mock_project_resolved
        mock_output_dir.resolve.return_value = mock_output_resolved

        # Setup strings (str is callable but we can configure it)
        mock_project_resolved.configure_mock(
            **{"__str__.return_value": "/output/my-project"}
        )
        mock_output_resolved.configure_mock(**{"__str__.return_value": "/output"})

        target_dir, project_path = cli._validate_and_prepare_paths(
            "my-project", mock_output_dir
        )
        assert target_dir == mock_output_dir
        assert project_path == mock_project_dir


class TestGetAPIKeyWithSource:
    """Test _get_api_key_with_source function."""

    def test_get_api_key_with_source_uses_arg(self) -> None:
        """Test _get_api_key_with_source returns CLI arg if provided."""
        with patch(
            "start_green_stay_green.cli.get_api_key_from_keyring", return_value=None
        ):
            key, source = cli._get_api_key_with_source("cli-key", no_interactive=True)
            assert key == "cli-key"
            assert source == "command line"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    def test_get_api_key_with_source_uses_keyring(self, mock_keyring: Mock) -> None:
        """Test _get_api_key_with_source returns keyring if available."""
        mock_keyring.return_value = "keyring-key"
        with patch.dict("os.environ", {}, clear=True):
            key, source = cli._get_api_key_with_source(None, no_interactive=True)
            assert key == "keyring-key"
            assert source == "keyring"

    def test_get_api_key_with_source_uses_env_var(self) -> None:
        """Test _get_api_key_with_source returns env var if available."""
        with (
            patch(
                "start_green_stay_green.cli.get_api_key_from_keyring",
                return_value=None,
            ),
            patch.dict(
                "os.environ",
                {"ANTHROPIC_API_KEY": "env-key"},  # pragma: allowlist secret
            ),
        ):
            key, source = cli._get_api_key_with_source(None, no_interactive=True)
            assert key == "env-key"
            assert source == "environment variable"

    def test_get_api_key_with_source_priority_arg_over_keyring(self) -> None:
        """Test CLI arg takes priority over keyring."""
        with patch(
            "start_green_stay_green.cli.get_api_key_from_keyring",
            return_value="keyring-key",
        ):
            key, source = cli._get_api_key_with_source("cli-key", no_interactive=True)
            assert key == "cli-key"
            assert source == "command line"

    def test_get_api_key_with_source_priority_keyring_over_env(self) -> None:
        """Test keyring takes priority over environment variable."""
        with (
            patch(
                "start_green_stay_green.cli.get_api_key_from_keyring",
                return_value="keyring-key",
            ),
            patch.dict(
                "os.environ",
                {"ANTHROPIC_API_KEY": "env-key"},  # pragma: allowlist secret
            ),
        ):
            key, source = cli._get_api_key_with_source(None, no_interactive=True)
            assert key == "keyring-key"
            assert source == "keyring"

    @patch("start_green_stay_green.cli._prompt_for_api_key")
    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    def test_get_api_key_with_source_prompts_in_interactive_mode(
        self, mock_keyring: Mock, mock_prompt: Mock
    ) -> None:
        """Test interactive prompt works when no key found."""
        mock_keyring.return_value = None
        mock_prompt.return_value = "interactive-key"
        with patch.dict("os.environ", {}, clear=True):
            key, source = cli._get_api_key_with_source(None, no_interactive=False)
            assert key == "interactive-key"
            assert source == "interactive prompt"

    @patch("start_green_stay_green.cli.get_api_key_from_keyring")
    def test_get_api_key_with_source_returns_none_in_non_interactive_no_key(
        self, mock_keyring: Mock
    ) -> None:
        """Test returns (None, None) when no key in non-interactive mode."""
        mock_keyring.return_value = None
        with patch.dict("os.environ", {}, clear=True):
            key, source = cli._get_api_key_with_source(None, no_interactive=True)
            assert key is None
            assert source is None


class TestInitCommand:
    """Test init command execution."""

    @patch("start_green_stay_green.cli._show_dry_run_preview")
    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_dry_run_shows_preview(
        self, mock_validate: Mock, mock_preview: Mock
    ) -> None:
        """Test init with dry_run=True shows preview."""
        mock_path = MagicMock(spec=Path)
        mock_validate.return_value = (mock_path, mock_path / "test-project")

        cli.init(
            project_name="test-project",
            output_dir=mock_path,
            language="python",
            api_key=None,
            dry_run=True,
            no_interactive=True,
        )
        mock_preview.assert_called_once()

    @patch("start_green_stay_green.cli._generate_project_files")
    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_generates_files_when_not_dry_run(
        self, mock_validate: Mock, mock_generate: Mock
    ) -> None:
        """Test init with dry_run=False calls generate."""
        mock_path = MagicMock(spec=Path)
        mock_validate.return_value = (mock_path, mock_path / "test-project")
        mock_generate.return_value = None

        cli.init(
            project_name="test-project",
            output_dir=mock_path,
            language="python",
            api_key=None,
            dry_run=False,
            no_interactive=True,
        )
        mock_generate.assert_called_once()

    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_handles_validation_error(self, mock_validate: Mock) -> None:
        """Test init exits on validation error."""
        mock_validate.side_effect = typer.BadParameter("Invalid project name")
        with pytest.raises(SystemExit) as exc_info:
            cli.init(
                project_name="invalid!",
                output_dir=None,
                language="python",
                api_key=None,
                dry_run=False,
                no_interactive=True,
            )
        assert exc_info.value.code == 1

    @patch("start_green_stay_green.cli._load_config_data")
    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_loads_config_when_provided(
        self, mock_validate: Mock, mock_load_config: Mock
    ) -> None:
        """Test init loads config data."""
        mock_path = MagicMock(spec=Path)
        mock_validate.return_value = (mock_path, mock_path / "test-project")
        mock_load_config.return_value = {}

        cli.init(
            project_name="test-project",
            output_dir=mock_path,
            language="python",
            api_key=None,
            config=mock_path,
            dry_run=True,
            no_interactive=True,
        )
        mock_load_config.assert_called()

    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_calls_validate_paths(self, mock_validate: Mock) -> None:
        """Test init calls _validate_and_prepare_paths."""
        mock_path = MagicMock(spec=Path)
        mock_validate.return_value = (mock_path, mock_path / "test-project")

        cli.init(
            project_name="test-project",
            output_dir=mock_path,
            language="python",
            api_key=None,
            dry_run=True,
            no_interactive=True,
        )
        mock_validate.assert_called_once_with("test-project", mock_path)


class TestShowDryRunPreview:
    """Test dry run preview display."""

    @patch("start_green_stay_green.cli.console")
    def test_show_dry_run_preview_prints_output(self, mock_console: Mock) -> None:
        """Test _show_dry_run_preview prints to console."""
        mock_path = MagicMock(spec=Path)
        mock_path.configure_mock(**{"__str__.return_value": "/output/project"})
        cli._show_dry_run_preview("my-project", "python", mock_path)
        assert mock_console.print.call_count > 0

    @patch("start_green_stay_green.cli.console")
    def test_show_dry_run_preview_includes_project_name(
        self, mock_console: Mock
    ) -> None:
        """Test _show_dry_run_preview includes project name."""
        mock_path = MagicMock(spec=Path)
        cli._show_dry_run_preview("test-project", "python", mock_path)
        calls = mock_console.print.call_args_list
        # Check that project name appears in some call
        assert any("test-project" in str(call) for call in calls)


class TestResolveParameter:
    """Test parameter resolution from multiple sources."""

    def test_resolve_parameter_uses_param_value_first(self) -> None:
        """Test _resolve_parameter prefers param_value."""
        result = cli._resolve_parameter(
            param_value="from-arg",
            config_data={"key": "from-config"},
            config_key="key",
            param_name="test",
            no_interactive=True,
        )
        assert result == "from-arg"

    def test_resolve_parameter_uses_config_when_no_arg(self) -> None:
        """Test _resolve_parameter uses config when arg not provided."""
        result = cli._resolve_parameter(
            param_value=None,
            config_data={"key": "from-config"},
            config_key="key",
            param_name="test",
            no_interactive=True,
        )
        assert result == "from-config"

    def test_resolve_parameter_exits_in_non_interactive_without_value(
        self,
    ) -> None:
        """Test _resolve_parameter exits in non-interactive mode without value."""
        with pytest.raises(typer.Exit) as exc_info:
            cli._resolve_parameter(
                param_value=None,
                config_data={},
                config_key="key",
                param_name="test",
                no_interactive=True,
            )
        assert exc_info.value.exit_code == 1

    @patch("start_green_stay_green.cli.typer.prompt")
    def test_resolve_parameter_prompts_in_interactive_mode(
        self, mock_prompt: Mock
    ) -> None:
        """Test _resolve_parameter prompts in interactive mode."""
        mock_prompt.return_value = "interactive-value"
        result = cli._resolve_parameter(
            param_value=None,
            config_data={},
            config_key="key",
            param_name="test",
            no_interactive=False,
        )
        assert result == "interactive-value"


class TestLoadConfigData:
    """Test config data loading."""

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_data_returns_empty_when_none(self, mock_load: Mock) -> None:
        """Test _load_config_data returns empty dict when config is None."""
        result = cli._load_config_data(None)
        assert not result
        mock_load.assert_not_called()

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_data_loads_file(self, mock_load: Mock) -> None:
        """Test _load_config_data loads config file."""
        mock_load.return_value = {"key": "value"}
        mock_path = MagicMock(spec=Path)
        result = cli._load_config_data(mock_path)
        assert result == {"key": "value"}

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_data_exits_on_file_not_found(self, mock_load: Mock) -> None:
        """Test _load_config_data exits on FileNotFoundError."""
        mock_load.side_effect = FileNotFoundError("Not found")
        mock_path = MagicMock(spec=Path)
        with pytest.raises(typer.Exit) as exc_info:
            cli._load_config_data(mock_path)
        assert exc_info.value.exit_code == 1


class TestInitializeOrchestrator:
    """Test AI orchestrator initialization."""

    @patch("start_green_stay_green.cli._get_api_key_with_source")
    def test_initialize_orchestrator_returns_none_without_key(
        self, mock_get_key: Mock
    ) -> None:
        """Test _initialize_orchestrator returns None when no API key."""
        mock_get_key.return_value = (None, None)
        result = cli._initialize_orchestrator(no_interactive=True)
        assert result is None

    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch("start_green_stay_green.cli._get_api_key_with_source")
    def test_initialize_orchestrator_creates_instance(
        self, mock_get_key: Mock, mock_orchestrator: Mock
    ) -> None:
        """Test _initialize_orchestrator creates AIOrchestrator instance."""
        mock_get_key.return_value = ("test-key", "test-source")
        mock_instance = MagicMock()
        mock_orchestrator.return_value = mock_instance

        result = cli._initialize_orchestrator(
            api_key_arg="test-key", no_interactive=True  # pragma: allowlist secret
        )
        assert result == mock_instance

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch("start_green_stay_green.cli._get_api_key_with_source")
    def test_initialize_orchestrator_handles_invalid_key(
        self, mock_get_key: Mock, mock_orchestrator: Mock, mock_console: Mock
    ) -> None:
        """Test _initialize_orchestrator handles ValueError."""
        mock_get_key.return_value = ("invalid-key", "test-source")
        mock_orchestrator.side_effect = ValueError("Invalid API key")

        result = cli._initialize_orchestrator(
            api_key_arg="invalid-key", no_interactive=True  # pragma: allowlist secret
        )
        assert result is None
        mock_console.print.assert_called()


class TestVersionCommandDetails:
    """Test version command."""

    @patch("start_green_stay_green.cli.console")
    def test_version_command_simple_output(self, mock_console: Mock) -> None:
        """Test version command prints simple output."""
        cli.version(verbose=False)
        mock_console.print.assert_called()

    @patch("start_green_stay_green.cli.console")
    def test_version_command_verbose_output(self, mock_console: Mock) -> None:
        """Test version command prints verbose output."""
        cli.version(verbose=True)
        mock_console.print.assert_called()


class TestMainCallback:
    """Test main callback function."""

    @patch("start_green_stay_green.cli._validate_options")
    def test_main_validates_options(self, mock_validate: Mock) -> None:
        """Test main calls _validate_options."""
        cli.main(verbose=True, quiet=False)
        mock_validate.assert_called_once()

    @patch("start_green_stay_green.cli._load_config_if_specified")
    def test_main_loads_config(self, mock_load_config: Mock) -> None:
        """Test main calls _load_config_if_specified."""
        cli.main(quiet=False, config=None)
        mock_load_config.assert_called_once()


class TestCopyReferenceSkills:
    """Test copying reference skills."""

    @patch("start_green_stay_green.cli.REFERENCE_SKILLS_DIR", new_callable=MagicMock)
    def test_copy_reference_skills_creates_target_dir(self, mock_ref_dir: Mock) -> None:
        """Test _copy_reference_skills creates target directory."""
        mock_target = MagicMock(spec=Path)
        mock_ref_dir.__truediv__.return_value = MagicMock(
            spec=Path, exists=lambda: True
        )

        # Mock REQUIRED_SKILLS to be empty to avoid file not found errors
        with patch("start_green_stay_green.cli.REQUIRED_SKILLS", []):
            cli._copy_reference_skills(mock_target)
            mock_target.mkdir.assert_called()

    @patch("start_green_stay_green.cli.REFERENCE_SKILLS_DIR", new_callable=MagicMock)
    def test_copy_reference_skills_raises_on_missing_reference(
        self, mock_ref_dir: Mock
    ) -> None:
        """Test _copy_reference_skills raises FileNotFoundError."""
        mock_target = MagicMock(spec=Path)
        mock_skill_file = MagicMock(spec=Path)
        mock_skill_file.exists.return_value = False
        mock_ref_dir.__truediv__.return_value = mock_skill_file

        with (
            patch("start_green_stay_green.cli.REQUIRED_SKILLS", ["missing_skill.md"]),
            pytest.raises(FileNotFoundError),
        ):
            cli._copy_reference_skills(mock_target)


class TestGenerateSteps:
    """Test individual generation steps."""

    @patch("start_green_stay_green.cli.ScriptsGenerator")
    def test_generate_scripts_step_creates_generator(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_scripts_step creates ScriptsGenerator."""
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)

        cli._generate_scripts_step(mock_path, "my-project", "python", mock_progress)

        mock_generator_class.assert_called()
        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli.PreCommitGenerator")
    def test_generate_precommit_step_creates_generator(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_precommit_step creates PreCommitGenerator."""
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_generator.generate.return_value = "# config"
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_precommit_step(mock_path, "my-project", "python", mock_progress)

        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli._copy_reference_skills")
    def test_generate_skills_step_copies_skills(self, mock_copy: Mock) -> None:
        """Test _generate_skills_step copies reference skills."""
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.REQUIRED_SKILLS", []):
            cli._generate_skills_step(mock_path, mock_progress)
            mock_copy.assert_called()

    @patch("start_green_stay_green.cli.CIGenerator")
    def test_generate_ci_step_with_orchestrator(
        self, mock_ci_generator_class: Mock
    ) -> None:
        """Test _generate_ci_step with orchestrator."""
        mock_orchestrator = MagicMock()
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate_workflow.return_value = mock_workflow
        mock_ci_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_ci_step(mock_path, "python", mock_orchestrator, mock_progress)

        mock_ci_generator_class.assert_called_with(mock_orchestrator, "python")

    def test_generate_ci_step_skips_without_orchestrator(self) -> None:
        """Test _generate_ci_step skips without orchestrator."""
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_path = MagicMock(spec=Path)

        # Should not raise when orchestrator is None
        cli._generate_ci_step(mock_path, "python", None, mock_progress)

    @patch("start_green_stay_green.cli.GitHubActionsReviewGenerator")
    def test_generate_review_step_with_orchestrator(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_review_step with orchestrator."""
        mock_orchestrator = MagicMock()
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate.return_value = mock_workflow
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_review_step(mock_path, mock_orchestrator, mock_progress)

        mock_generator_class.assert_called_with(mock_orchestrator)

    def test_generate_review_step_skips_without_orchestrator(self) -> None:
        """Test _generate_review_step skips without orchestrator."""
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_path = MagicMock(spec=Path)

        # Should not raise when orchestrator is None
        cli._generate_review_step(mock_path, None, mock_progress)

    @patch("start_green_stay_green.cli.ClaudeMdGenerator")
    def test_generate_claude_md_step(self, mock_generator_class: Mock) -> None:
        """Test _generate_claude_md_step creates generator."""
        mock_orchestrator = MagicMock()
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "# CLAUDE.md content"
        mock_generator.generate.return_value = mock_result
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_claude_md_step(
            mock_path, "my-project", "python", mock_orchestrator, mock_progress
        )

        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step creates generator."""
        mock_orchestrator = MagicMock()
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_architecture_step(
            mock_path, "my-project", "python", mock_orchestrator, mock_progress
        )

        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli.run_async")
    @patch("start_green_stay_green.cli.SubagentsGenerator")
    def test_generate_subagents_step(
        self, mock_generator_class: Mock, mock_run_async: Mock
    ) -> None:
        """Test _generate_subagents_step creates generator."""
        mock_orchestrator = MagicMock()
        mock_progress = MagicMock()
        mock_task = MagicMock()
        mock_progress.add_task.return_value = mock_task
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_run_async.return_value = {}  # Mock async result (not bool)
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        cli._generate_subagents_step(
            mock_path, "my-project", "python", mock_orchestrator, mock_progress
        )

        mock_generator_class.assert_called()


class TestGenerateProjectFiles:
    """Test project file generation."""

    @patch("start_green_stay_green.cli._generate_with_orchestrator")
    @patch("start_green_stay_green.cli._generate_scripts_step")
    @patch("start_green_stay_green.cli._generate_precommit_step")
    @patch("start_green_stay_green.cli._generate_skills_step")
    def test_generate_project_files_with_orchestrator(
        self,
        mock_skills: Mock,
        mock_precommit: Mock,
        mock_scripts: Mock,
        mock_generate_orch: Mock,
    ) -> None:
        """Test _generate_project_files generates all steps."""
        mock_orchestrator = MagicMock()
        mock_path = MagicMock(spec=Path)

        cli._generate_project_files(
            mock_path,
            "my-project",
            "python",
            mock_orchestrator,
        )

        # Verify generation steps were called
        mock_scripts.assert_called()
        mock_precommit.assert_called()
        mock_skills.assert_called()
        mock_generate_orch.assert_called()

    @patch("start_green_stay_green.cli._generate_scripts_step")
    @patch("start_green_stay_green.cli._generate_precommit_step")
    @patch("start_green_stay_green.cli._generate_skills_step")
    def test_generate_project_files_without_orchestrator(
        self, mock_skills: Mock, mock_precommit: Mock, mock_scripts: Mock
    ) -> None:
        """Test _generate_project_files generates without orchestrator."""
        mock_path = MagicMock(spec=Path)

        cli._generate_project_files(
            mock_path,
            "my-project",
            "python",
            None,
        )

        # Verify generation steps were called
        mock_scripts.assert_called()
        mock_precommit.assert_called()
        mock_skills.assert_called()
