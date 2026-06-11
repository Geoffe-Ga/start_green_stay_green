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

import asyncio
import json
from pathlib import Path
from typing import cast
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from start_green_stay_green import cli
from start_green_stay_green.ai.batch_dispatch import ResumeOutcome
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError as AIGenerationError
from start_green_stay_green.ai.provider_selection import ProviderUnavailableError
from start_green_stay_green.generators.base import SUPPORTED_LANGUAGES
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS
from start_green_stay_green.utils.enhance_state import BatchProgress
from start_green_stay_green.utils.enhance_state import EnhanceState
from start_green_stay_green.utils.enhance_state import load_state
from start_green_stay_green.utils.enhance_state import save_state


def _make_orch_mock(mock_init: Mock) -> MagicMock:
    """Build an ``AIOrchestrator`` mock with ``.model`` populated.

    ``MagicMock(spec=AIOrchestrator)`` does not auto-populate the
    instance attributes set in ``__init__``, so the Phase 3c
    ``state.mark_completed(..., orchestrator.model)`` path fails
    without a value here. Wires the mock onto ``mock_init`` and
    returns it for callers that need to set further attributes.
    """
    orch = MagicMock(spec=AIOrchestrator)
    orch.model = "claude-sonnet-4-5"
    mock_init.return_value = orch
    return orch


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

    def test_validate_output_dir_resolves_path(self) -> None:
        """Test _validate_output_dir resolves path to absolute."""
        mock_path = MagicMock(spec=Path)
        mock_resolved = MagicMock(spec=Path)
        mock_path.resolve.return_value = mock_resolved
        result = cli._validate_output_dir(mock_path)
        assert result == mock_resolved
        mock_path.resolve.assert_called_once()


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
        """Test _get_api_key_with_source returns CLI arg without hitting keyring."""
        with patch(
            "start_green_stay_green.cli.get_api_key_from_keyring"
        ) as mock_keyring:
            key, source = cli._get_api_key_with_source("cli-key", no_interactive=True)
            assert key == "cli-key"
            assert source == "command line"
            mock_keyring.assert_not_called()

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


class TestProviderModelSelection:
    """Test the ``--provider`` / ``--model`` selection wiring in the CLI."""

    def test_lazy_sources_read_provider_specific_env_var(self) -> None:
        """The env-var source honors the per-provider key var name."""
        with (
            patch(
                "start_green_stay_green.cli.get_api_key_from_keyring",
                return_value=None,
            ),
            patch.dict(
                "os.environ",
                {"CUSTOM_KEY_VAR": "custom-env-key"},  # pragma: allowlist secret
                clear=True,
            ),
        ):
            sources = list(cli._lazy_api_key_sources(None, "CUSTOM_KEY_VAR"))
        # Last yielded source is the env var; it must read CUSTOM_KEY_VAR.
        assert sources[-1] == ("custom-env-key", "environment variable")

    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch("start_green_stay_green.cli.build_provider")
    @patch(
        "start_green_stay_green.cli._get_api_key_with_source",
        return_value=("k", "command line"),
    )
    def test_initialize_orchestrator_threads_flags_into_selection(
        self,
        mock_get_key: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_build: Mock,
        mock_orch: Mock,
    ) -> None:
        """Flags resolve to a selection that drives build_provider + orchestrator."""
        with patch.dict("os.environ", {}, clear=True):
            cli._initialize_orchestrator(
                api_key_arg="k",
                no_interactive=True,
                selection_inputs=cli._SelectionInputs(model_flag="model-from-flag"),
            )
        # build_provider receives the resolved provider + model.
        _, build_kwargs = mock_build.call_args
        assert mock_build.call_args.args[0] == "anthropic"
        assert build_kwargs["model"] == "model-from-flag"
        # The orchestrator is constructed with the resolved model + provider.
        _, orch_kwargs = mock_orch.call_args
        assert orch_kwargs["model"] == "model-from-flag"
        assert orch_kwargs["provider"] is mock_build.return_value

    @patch("start_green_stay_green.cli.console")
    def test_initialize_orchestrator_unknown_provider_prints_and_returns_none(
        self, mock_console: Mock
    ) -> None:
        """An unknown ``--provider`` prints an error and yields no orchestrator."""
        with patch.dict("os.environ", {}, clear=True):
            result = cli._initialize_orchestrator(
                api_key_arg="k",
                no_interactive=True,
                selection_inputs=cli._SelectionInputs(provider_flag="does-not-exist"),
            )
        assert result is None
        mock_console.print.assert_called()
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        # The supported set must appear exactly once — the underlying
        # ``ValueError`` already names it, so the CLI must not append a
        # second ``(supported: …)`` copy (regression: #383).
        assert printed.count("Supported providers:") == 1
        assert "(supported:" not in printed

    @patch("start_green_stay_green.cli.console")
    @patch(
        "start_green_stay_green.cli.build_provider",
        side_effect=ProviderUnavailableError("install hint here"),
    )
    @patch(
        "start_green_stay_green.cli._get_api_key_with_source",
        return_value=("k", "command line"),
    )
    def test_initialize_orchestrator_missing_extra_prints_hint(
        self,
        mock_get_key: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_build: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_console: Mock,
    ) -> None:
        """A missing provider extra surfaces the install hint, not a crash."""
        with patch.dict("os.environ", {}, clear=True):
            result = cli._initialize_orchestrator(api_key_arg="k", no_interactive=True)
        assert result is None
        printed = " ".join(str(c) for c in mock_console.print.call_args_list)
        assert "install hint here" in printed

    @patch("start_green_stay_green.cli.build_provider")
    @patch("start_green_stay_green.cli.AIOrchestrator")
    @patch(
        "start_green_stay_green.cli._get_api_key_with_source",
        return_value=("k", "command line"),
    )
    def test_env_var_selects_model_over_default(
        self,
        mock_get_key: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_orch: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_build: Mock,
    ) -> None:
        """``GREEN_LLM_MODEL`` overrides the default model when no flag given."""
        with patch.dict("os.environ", {"GREEN_LLM_MODEL": "env-model"}, clear=True):
            cli._initialize_orchestrator(api_key_arg="k", no_interactive=True)
        assert mock_build.call_args.kwargs["model"] == "env-model"


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
            language=["python"],
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
            language=["python"],
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
                language=["python"],
                api_key=None,
                dry_run=False,
                no_interactive=True,
            )
        assert exc_info.value.code == 1

    @patch("start_green_stay_green.cli._generate_metrics_dashboard_step")
    @patch("start_green_stay_green.cli._generate_project_files")
    def test_init_with_live_dashboard_calls_metrics_step(
        self, mock_generate: Mock, mock_dashboard: Mock, tmp_path: Path
    ) -> None:
        """Test init with enable_live_dashboard=True calls dashboard step."""
        mock_generate.return_value = None
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
            language=["python"],
            api_key=None,
            dry_run=False,
            no_interactive=True,
            enable_live_dashboard=True,
        )
        mock_generate.assert_called()
        mock_dashboard.assert_called_once()

    @patch("start_green_stay_green.cli._generate_metrics_dashboard_step")
    @patch("start_green_stay_green.cli._generate_project_files")
    def test_init_without_live_dashboard_skips_metrics_step(
        self, mock_generate: Mock, mock_dashboard: Mock, tmp_path: Path
    ) -> None:
        """Test init without enable_live_dashboard skips dashboard step."""
        mock_generate.return_value = None
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
            language=["python"],
            api_key=None,
            dry_run=False,
            no_interactive=True,
        )
        mock_generate.assert_called()
        mock_dashboard.assert_not_called()

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
            language=["python"],
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
            language=["python"],
            api_key=None,
            dry_run=True,
            no_interactive=True,
        )
        mock_validate.assert_called_once_with("test-project", mock_path)


class TestLanguageValidation:
    """Test CLI language validation against SUPPORTED_LANGUAGES."""

    def test_init_rejects_unsupported_language(self) -> None:
        """Test init exits with error for unsupported language."""
        mock_path = MagicMock(spec=Path)
        with patch("start_green_stay_green.cli.console"):
            with pytest.raises(typer.Exit) as exc_info:
                cli.init(
                    project_name="test-project",
                    output_dir=mock_path,
                    language=["brainfuck"],
                    api_key=None,
                    dry_run=False,
                    no_interactive=True,
                )
            assert exc_info.value.exit_code == 1

    def test_help_text_includes_all_supported_languages(self) -> None:
        """Test CLI help text dynamically lists all supported languages."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["init", "--help"])
        help_text = result.output

        for lang in SUPPORTED_LANGUAGES:
            assert lang in help_text, f"Language '{lang}' missing from help text"

    def test_api_key_flag_hidden_from_init_help(self) -> None:
        """Lock in hidden=True on init's --api-key (regresses if re-exposed)."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--api-key" not in result.output

    def test_api_key_flag_hidden_from_enhance_help(self) -> None:
        """Lock in hidden=True on enhance's --api-key (regresses if re-exposed)."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["enhance", "--help"])
        assert result.exit_code == 0
        assert "--api-key" not in result.output

    @patch("start_green_stay_green.cli._generate_project_files")
    @patch("start_green_stay_green.cli._validate_and_prepare_paths")
    def test_init_accepts_all_supported_languages(
        self, mock_validate: Mock, mock_generate: Mock
    ) -> None:
        """Test init accepts every supported language without error."""
        mock_path = MagicMock(spec=Path)
        mock_validate.return_value = (mock_path, mock_path / "test-project")
        mock_generate.return_value = None

        for lang in SUPPORTED_LANGUAGES:
            cli.init(
                project_name="test-project",
                output_dir=mock_path,
                language=[lang],
                api_key=None,
                dry_run=True,
                no_interactive=True,
            )


class TestMetricsDashboardGeneration:
    """Test metrics dashboard generation functionality."""

    @patch("start_green_stay_green.cli.MetricsGenerator")
    @patch("start_green_stay_green.cli.shutil.copy")
    def test_generate_metrics_dashboard_step_creates_files(
        self,
        mock_shutil_copy: Mock,
        mock_generator_class: Mock,
        tmp_path: Path,
    ) -> None:
        """Test _generate_metrics_dashboard_step creates dashboard and workflow."""
        # Setup mock generator
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        mock_generator_class.count_precommit_hooks.return_value = 31

        # Mock shutil.copy to create a dummy workflow file when called
        def copy_side_effect(_src: Path, dst: Path) -> None:
            # Create parent directory
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Write dummy workflow content
            dst.write_text("name: Metrics\nproject: start-green-stay-green")

        mock_shutil_copy.side_effect = copy_side_effect

        cli._generate_metrics_dashboard_step(
            project_path=tmp_path,
            project_name="test-project",
            language="python",
        )

        # Verify MetricsGenerator was instantiated with correct config
        assert mock_generator_class.called
        config_arg = mock_generator_class.call_args[0][1]
        assert config_arg.project_name == "test-project"
        assert config_arg.language == "python"
        assert config_arg.enable_dashboard is True
        assert config_arg.enable_badges is True

        # Verify dashboard was written
        mock_generator.write_dashboard.assert_called_once()

        # Verify docs directory was created
        assert (tmp_path / "docs").exists()

        # Verify metrics.json was created
        metrics_file = tmp_path / "docs" / "metrics.json"
        assert metrics_file.exists()

        # Verify metrics.json contains project name
        metrics_data = json.loads(metrics_file.read_text())
        assert metrics_data["project"] == "test-project"
        assert "thresholds" in metrics_data
        assert "metrics" in metrics_data

        # Issue #159: fresh projects seed a ci_status entry. No workflows
        # exist when the dashboard step counts jobs, so it degrades to the
        # unknown/no-data status (rendered gray, not red).
        ci_seed = metrics_data["metrics"]["ci_status"]
        assert ci_seed["total_jobs"] == 0
        assert ci_seed["passing_jobs"] == 0
        assert ci_seed["percentage"] == 0.0
        assert ci_seed["status"] == "unknown"

    @patch("start_green_stay_green.cli.shutil.copy")
    @patch("start_green_stay_green.cli.MetricsGenerator")
    def test_generate_metrics_dashboard_creates_workflows_dir(
        self, mock_generator_class: Mock, mock_shutil_copy: Mock, tmp_path: Path
    ) -> None:
        """Test _generate_metrics_dashboard_step creates .github/workflows."""
        # Setup mock generator to avoid instantiation errors
        mock_generator_class.return_value = Mock()
        mock_generator_class.count_precommit_hooks.return_value = 31

        # Mock shutil.copy to create files
        def copy_side_effect(_src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("dummy content")

        mock_shutil_copy.side_effect = copy_side_effect

        cli._generate_metrics_dashboard_step(
            project_path=tmp_path,
            project_name="test-project",
            language="python",
        )

        # Verify .github/workflows directory was created
        workflows_dir = tmp_path / ".github" / "workflows"
        assert workflows_dir.exists()
        assert workflows_dir.is_dir()

    @patch("start_green_stay_green.cli.shutil.copy")
    @patch("start_green_stay_green.cli.MetricsGenerator")
    @patch("start_green_stay_green.cli.console")
    def test_generate_metrics_dashboard_warns_on_missing_workflow(
        self,
        mock_console: Mock,
        mock_generator_class: Mock,
        mock_shutil_copy: Mock,
        tmp_path: Path,
    ) -> None:
        """Test _generate_metrics_dashboard_step warns when workflow missing."""
        # Setup mock generator
        mock_generator_class.return_value = Mock()
        mock_generator_class.count_precommit_hooks.return_value = 31
        # Setup mock copy (not used but required by patch decorator order)
        mock_shutil_copy.return_value = None

        # Mock Path.exists to return False for workflow file
        with patch.object(Path, "exists", return_value=False):
            cli._generate_metrics_dashboard_step(
                project_path=tmp_path,
                project_name="test-project",
                language="python",
            )

        # Verify warning was printed
        assert mock_console.print.called
        warning_calls = [
            call for call in mock_console.print.call_args_list if "Warning" in str(call)
        ]
        assert warning_calls

    @patch("start_green_stay_green.cli.shutil.copy")
    @patch("start_green_stay_green.cli.MetricsGenerator")
    def test_generate_metrics_dashboard_replaces_project_name(
        self, mock_generator_class: Mock, mock_shutil_copy: Mock, tmp_path: Path
    ) -> None:
        """Test _generate_metrics_dashboard_step replaces project name in workflow."""
        # Setup mock generator
        mock_generator_class.return_value = Mock()
        mock_generator_class.count_precommit_hooks.return_value = 31

        # Create source workflow with SGSG project name
        workflow_content = "project: start-green-stay-green\nname: Metrics"

        # Mock shutil.copy to create workflow with SGSG name
        def copy_side_effect(_src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(workflow_content)

        mock_shutil_copy.side_effect = copy_side_effect

        cli._generate_metrics_dashboard_step(
            project_path=tmp_path,
            project_name="my-new-project",
            language="python",
        )

        # Verify workflow content was replaced
        workflow_file = tmp_path / ".github" / "workflows" / "metrics.yml"
        if workflow_file.exists():
            content = workflow_file.read_text()
            assert "my-new-project" in content
            assert "start-green-stay-green" not in content


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
            spec=Path, is_dir=lambda: True
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
        mock_skill_dir = MagicMock(spec=Path)
        mock_skill_dir.is_dir.return_value = False
        mock_ref_dir.__truediv__.return_value = mock_skill_dir

        with (
            patch("start_green_stay_green.cli.REQUIRED_SKILLS", ["missing_skill"]),
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
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_scripts_step(mock_path, "my-project", "python")

        mock_generator_class.assert_called()
        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli.PreCommitGenerator")
    def test_generate_precommit_step_creates_generator(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_precommit_step creates PreCommitGenerator."""
        mock_generator = MagicMock()
        mock_generator.generate.return_value = {
            "content": "# config",
        }
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_precommit_step(mock_path, "my-project", "python")

        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli._copy_reference_skills")
    def test_generate_skills_step_copies_skills(self, mock_copy: Mock) -> None:
        """Test _generate_skills_step copies reference skills."""
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with (
            patch("start_green_stay_green.cli.REQUIRED_SKILLS", []),
            patch("start_green_stay_green.cli.console"),
        ):
            cli._generate_skills_step(mock_path)
            mock_copy.assert_called()

    @patch("start_green_stay_green.cli.CIGenerator")
    def test_generate_ci_step_with_orchestrator(
        self, mock_ci_generator_class: Mock
    ) -> None:
        """Test _generate_ci_step with orchestrator."""
        mock_orchestrator = MagicMock()
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate_workflow.return_value = mock_workflow
        mock_ci_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_ci_step(mock_path, "my-project", "python", mock_orchestrator)

        # ``project_name`` is now threaded through so ``<<% project_name %>>``
        # placeholders in the reference templates render with the real value.
        mock_ci_generator_class.assert_called_with(
            mock_orchestrator, "python", project_name="my-project"
        )

    @patch("start_green_stay_green.cli.CIGenerator")
    def test_generate_ci_step_uses_template_without_orchestrator(
        self, mock_ci_generator_class: Mock
    ) -> None:
        """_generate_ci_step now runs the template path with no orchestrator."""
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate_workflow.return_value = mock_workflow
        mock_ci_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_ci_step(mock_path, "no-orch-project", "python", None)

        mock_ci_generator_class.assert_called_with(
            None, "python", project_name="no-orch-project"
        )
        mock_generator.generate_workflow.assert_called_once()

    @patch("start_green_stay_green.cli.GitHubActionsReviewGenerator")
    def test_generate_review_step_runs_unconditionally(
        self, mock_generator_class: Mock
    ) -> None:
        """_generate_review_step now always renders the template."""
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate.return_value = mock_workflow
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_review_step(mock_path)

        # Generator no longer takes an orchestrator argument.
        mock_generator_class.assert_called_with()
        mock_generator.generate.assert_called_once()

    @patch("start_green_stay_green.cli.GitHubActionsReviewGenerator")
    def test_generate_review_step_uses_default_file_writer(
        self, mock_generator_class: Mock
    ) -> None:
        """_generate_review_step works with the default ``file_writer=None``."""
        mock_generator = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.content = "workflow content"
        mock_generator.generate.return_value = mock_workflow
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            # No file_writer passed — exercises the ``write_text`` branch.
            cli._generate_review_step(mock_path)

        mock_generator.generate.assert_called_once()

    @patch("start_green_stay_green.cli.ClaudeMdGenerator")
    def test_generate_claude_md_step(self, mock_generator_class: Mock) -> None:
        """Test _generate_claude_md_step renders the modular tree."""
        mock_orchestrator = MagicMock()
        mock_generator = MagicMock()
        mock_result = MagicMock()
        mock_result.content = "# CLAUDE.md content"
        mock_generator.render_modular.return_value = (
            mock_result,
            {"principles": "# principles", "tools": "# tools"},
        )
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_claude_md_step(
                mock_path,
                "my-project",
                "python",
                mock_orchestrator,
            )

        mock_generator.render_modular.assert_called_once()

    def test_generate_claude_md_step_writes_modular_tree(self, tmp_path: Path) -> None:
        """_generate_claude_md_step (no writer) emits index + split docs."""
        with patch("start_green_stay_green.cli.console"):
            cli._generate_claude_md_step(
                tmp_path,
                "real-modular-project",
                "python",
                None,  # No orchestrator -> deterministic baseline.
            )

        index = tmp_path / "CLAUDE.md"
        assert index.exists()
        assert "real-modular-project" in index.read_text()
        docs_dir = tmp_path / ".claude" / "docs"
        for name in ("principles", "quality-standards", "troubleshooting"):
            assert (docs_dir / f"{name}.md").exists()

    def test_enhance_claude_md_writes_modular_tree(self, tmp_path: Path) -> None:
        """_enhance_claude_md (real generator, no writer) writes the tree."""
        # ``None`` orchestrator drives the deterministic baseline index so
        # the test needs no live API; the modular tree is still emitted.
        with patch("start_green_stay_green.cli.console"):
            cli._enhance_claude_md(
                cli._EnhanceProjectContext(
                    project_path=tmp_path,
                    project_name="enhanced-project",
                    language="python",
                ),
                cast("AIOrchestrator", None),
                dry_run=False,
                file_writer=None,
            )

        assert (tmp_path / "CLAUDE.md").exists()
        assert (tmp_path / ".claude" / "docs" / "workflow.md").exists()

    def test_enhance_claude_md_dry_run_skips_writes(self, tmp_path: Path) -> None:
        """_enhance_claude_md dry-run renders but writes nothing."""
        with patch("start_green_stay_green.cli.console"):
            cli._enhance_claude_md(
                cli._EnhanceProjectContext(
                    project_path=tmp_path,
                    project_name="dryrun-project",
                    language="python",
                ),
                cast("AIOrchestrator", None),
                dry_run=True,
                file_writer=None,
            )

        assert not (tmp_path / "CLAUDE.md").exists()
        assert not (tmp_path / ".claude" / "docs").exists()

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step creates generator deterministically."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            # The orchestrator parameter has been removed; this private
            # helper now takes only the (path, name, language, writer).
            cli._generate_architecture_step(mock_path, "my-project", "python")

        mock_generator.generate.assert_called()

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_go(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for Go."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "go")

        # Go now has architecture parity: the generator must be invoked.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "go"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_rust(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for Rust."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "rust")

        # Rust now has architecture parity: the generator must be invoked.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "rust"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_swift(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for Swift."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "swift")

        # Swift now has architecture parity: the generator must be invoked.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "swift"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_kotlin(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_architecture_step generates rules for Kotlin."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "kotlin")

        # Kotlin now has architecture parity (#357): the generator runs.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "kotlin"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_cpp(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for C/C++."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "cpp")

        # cpp now has architecture parity (#362): the generator runs.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "cpp"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_java(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for Java."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "java")

        # java now has architecture parity (#367): the generator runs.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "java"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_csharp(
        self, mock_generator_class: Mock
    ) -> None:
        """Test _generate_architecture_step generates rules for C#."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "csharp")

        # csharp now has architecture parity (#370): the generator runs.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "csharp"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_ruby(self, mock_generator_class: Mock) -> None:
        """Test _generate_architecture_step generates rules for Ruby."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "ruby")

        # ruby now has architecture parity (#373): the generator runs.
        mock_generator.generate.assert_called_once()
        assert mock_generator.generate.call_args.kwargs["language"] == "ruby"

    @patch("start_green_stay_green.cli.ArchitectureEnforcementGenerator")
    def test_generate_architecture_step_skips_unsupported(
        self, mock_generator_class: Mock
    ) -> None:
        """Test unsupported languages skip architecture generation."""
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        with patch("start_green_stay_green.cli.console"):
            cli._generate_architecture_step(mock_path, "my-project", "php")

        mock_generator.generate.assert_not_called()

    @patch("start_green_stay_green.cli.run_async")
    @patch("start_green_stay_green.cli.SubagentsGenerator")
    def test_generate_subagents_step(
        self,
        mock_generator_class: Mock,
        mock_run_async: Mock,
    ) -> None:
        """Test _generate_subagents_step creates generator."""
        mock_orchestrator = MagicMock()
        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator
        mock_path = MagicMock(spec=Path)
        mock_path.__truediv__.return_value = MagicMock(spec=Path)

        # ``_generate_subagents_step`` now wraps the gather in
        # ``_run_with_orchestrator_close``, which returns a coroutine.
        # The mocked ``run_async`` never awaits it, so we must close it
        # explicitly to avoid the "coroutine was never awaited" warning.
        def _consume(coro: object) -> dict[str, object]:
            close = getattr(coro, "close", None)
            if callable(close):
                close()
            return {}

        mock_run_async.side_effect = _consume

        with patch("start_green_stay_green.cli.console"):
            cli._generate_subagents_step(
                mock_path,
                "my-project",
                "python",
                mock_orchestrator,
            )

        mock_generator_class.assert_called()


class TestGenerateProjectFiles:
    """Test project file generation."""

    @patch("start_green_stay_green.cli._generate_pass2_polish")
    @patch("start_green_stay_green.cli._generate_scripts_step")
    @patch("start_green_stay_green.cli._generate_precommit_step")
    @patch("start_green_stay_green.cli._generate_skills_step")
    def test_generate_project_files_with_orchestrator(
        self,
        mock_skills: Mock,
        mock_precommit: Mock,
        mock_scripts: Mock,
        mock_pass2: Mock,
    ) -> None:
        """Test _generate_project_files generates all steps."""
        mock_orchestrator = MagicMock()
        mock_path = MagicMock(spec=Path)

        mock_writer = MagicMock()
        cli._generate_project_files(
            mock_path,
            "my-project",
            ("python",),
            mock_orchestrator,
            mock_writer,
        )

        # Verify generation steps were called
        mock_scripts.assert_called()
        mock_precommit.assert_called()
        mock_skills.assert_called()
        mock_pass2.assert_called()

    @patch("start_green_stay_green.cli._generate_scripts_step")
    @patch("start_green_stay_green.cli._generate_precommit_step")
    @patch("start_green_stay_green.cli._generate_skills_step")
    def test_generate_project_files_without_orchestrator(
        self, mock_skills: Mock, mock_precommit: Mock, mock_scripts: Mock
    ) -> None:
        """Test _generate_project_files generates without orchestrator."""
        mock_path = MagicMock(spec=Path)
        mock_writer = MagicMock()

        cli._generate_project_files(
            mock_path,
            "my-project",
            ("python",),
            None,
            mock_writer,
        )

        # Verify generation steps were called
        mock_scripts.assert_called()
        mock_precommit.assert_called()
        mock_skills.assert_called()


class TestCopyReferenceSubagents:
    """Cover the no-API copy path's error handling."""

    def test_raises_filenotfounderror_when_reference_missing(
        self, tmp_path: Path
    ) -> None:
        """Missing reference agent file surfaces a FileNotFoundError."""
        target_dir = tmp_path / "agents"

        # Patch REFERENCE_AGENTS_DIR to an empty directory so every
        # required source_file is missing.
        empty_ref_dir = tmp_path / "empty"
        empty_ref_dir.mkdir()

        with (
            patch("start_green_stay_green.cli.REFERENCE_AGENTS_DIR", empty_ref_dir),
            pytest.raises(FileNotFoundError, match="Reference subagent not found"),
        ):
            cli._copy_reference_subagents(target_dir)

    def test_writes_utf8_encoded_content(self, tmp_path: Path) -> None:
        """Copied agents are written with explicit UTF-8 encoding."""
        # Build a fake reference dir with a single agent file.
        ref_dir = tmp_path / "ref"
        ref_dir.mkdir()
        # Cover every REQUIRED_AGENTS source_file with a UTF-8 sentinel.
        sentinel = "# Agent: ✓ — non-ASCII\n"

        for src in REQUIRED_AGENTS.values():
            (ref_dir / src).write_text(sentinel, encoding="utf-8")

        target_dir = tmp_path / "agents"
        with patch("start_green_stay_green.cli.REFERENCE_AGENTS_DIR", ref_dir):
            cli._copy_reference_subagents(target_dir)

        # Round-trip through utf-8 decoding.
        for agent_name in REQUIRED_AGENTS:
            target = target_dir / f"{agent_name}.md"
            assert target.exists()
            assert target.read_text(encoding="utf-8") == sentinel

    def test_uses_file_writer_when_provided(self, tmp_path: Path) -> None:
        """The ``file_writer`` branch routes writes through the writer."""
        ref_dir = tmp_path / "ref"
        ref_dir.mkdir()
        sentinel = "# Agent body\n"
        for src in REQUIRED_AGENTS.values():
            (ref_dir / src).write_text(sentinel, encoding="utf-8")

        target_dir = tmp_path / "agents"
        # The FileWriter contract has ``write_file(path, content)``;
        # use a Mock with that signature so the test asserts the
        # public boundary, not implementation details.
        mock_writer = MagicMock()

        with patch("start_green_stay_green.cli.REFERENCE_AGENTS_DIR", ref_dir):
            cli._copy_reference_subagents(target_dir, file_writer=mock_writer)

        # All eight required agents flowed through the writer; no
        # files were created via the direct ``write_text`` fallback.
        assert mock_writer.write_file.call_count == len(REQUIRED_AGENTS)
        for agent_name in REQUIRED_AGENTS:
            assert not (target_dir / f"{agent_name}.md").exists()


class TestRunWithOrchestratorClose:
    """``_run_with_orchestrator_close`` must release the async client.

    The wrapper exists specifically so that a parallel-tuning failure
    inside ``asyncio.gather`` cannot leak the lazily-created
    :class:`AsyncAnthropic` connection pool. The two tests below pin
    that contract: ``aclose`` is called on success, and on failure.
    """

    def test_aclose_called_on_success(self) -> None:
        """When the wrapped coroutine returns normally, aclose runs."""
        orchestrator = MagicMock()
        orchestrator.aclose = MagicMock(return_value=asyncio.sleep(0))

        async def _ok() -> str:
            return "done"

        result = asyncio.run(cli._run_with_orchestrator_close(orchestrator, _ok()))
        assert result == "done"
        orchestrator.aclose.assert_called_once()

    def test_aclose_called_on_exception(self) -> None:
        """When the wrapped coroutine raises, aclose still runs."""
        orchestrator = MagicMock()
        orchestrator.aclose = MagicMock(return_value=asyncio.sleep(0))

        async def _boom() -> str:
            msg = "tuning failed"
            raise RuntimeError(msg)

        with pytest.raises(RuntimeError, match="tuning failed"):
            asyncio.run(cli._run_with_orchestrator_close(orchestrator, _boom()))

        # Even though ``_boom`` raised, the finally block must have
        # called aclose to release the httpx pool.
        orchestrator.aclose.assert_called_once()


class TestValidatePass2Flags:
    """Tests for the ``--offline`` / ``--no-enhance`` / ``--api-key`` validator."""

    def test_offline_alone_is_valid(self) -> None:
        """``--offline`` without conflicting flags passes validation."""
        cli._validate_pass2_flags(offline=True, no_enhance=False, api_key=None)

    def test_no_enhance_alone_is_valid(self) -> None:
        """``--no-enhance`` without conflicting flags passes validation."""
        cli._validate_pass2_flags(offline=False, no_enhance=True, api_key=None)

    def test_no_enhance_with_api_key_is_valid(self) -> None:
        """``--no-enhance`` plus ``--api-key`` is the documented happy path.

        The user has a key (cached for a future ``green enhance``) but
        does not want Pass 2 to run on this init.
        """
        cli._validate_pass2_flags(offline=False, no_enhance=True, api_key="sk-real-key")

    def test_offline_and_no_enhance_together_rejected(self) -> None:
        """Combining ``--offline`` and ``--no-enhance`` is redundant — error out."""
        with patch("start_green_stay_green.cli.console") as mock_console:
            with pytest.raises(typer.Exit) as exc:
                cli._validate_pass2_flags(offline=True, no_enhance=True, api_key=None)
            assert exc.value.exit_code == 1
            mock_console.print.assert_called_once()
            msg = mock_console.print.call_args[0][0]
            assert "redundant" in msg

    def test_offline_with_api_key_rejected(self) -> None:
        """``--offline`` with ``--api-key`` is contradictory — error out."""
        with patch("start_green_stay_green.cli.console") as mock_console:
            with pytest.raises(typer.Exit) as exc:
                cli._validate_pass2_flags(
                    offline=True, no_enhance=False, api_key="sk-real-key"
                )
            assert exc.value.exit_code == 1
            mock_console.print.assert_called_once()
            msg = mock_console.print.call_args[0][0]
            assert "contradictory" in msg


class TestOfflineAndNoEnhanceFlags:
    """End-to-end behaviour of the two new init flags."""

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_offline_skips_orchestrator_initialization(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """``--offline`` short-circuits before ``_initialize_orchestrator``."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "offline-smoke",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--offline",
                "--no-interactive",
            ],
        )

        # ``runner.invoke`` swallows exceptions by default, so a broken
        # ``--offline`` path could still leave ``mock_init_orch.assert_
        # not_called()`` passing. Anchor the test on a successful exit
        # first so a regression that crashes mid-init fails loudly.
        assert result.exit_code == 0, result.stdout

        # The point of --offline: the API-key resolution helper is
        # never called, so a missing keyring or no env var cannot cause
        # surprise prompts or warnings.
        mock_init_orch.assert_not_called()

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_no_enhance_resolves_key_but_drops_orchestrator(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """``--no-enhance`` calls ``_initialize_orchestrator`` and discards it."""
        # Stand up a fake orchestrator so the helper "succeeds".
        mock_init_orch.return_value = MagicMock(spec=AIOrchestrator)

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "no-enhance-smoke",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-enhance",
                "--no-interactive",
            ],
        )

        # Key was resolved (Pass 2 is skipped, but the key is "kept"
        # for a future ``green enhance``).
        assert result.exit_code == 0
        mock_init_orch.assert_called_once()
        # The on-screen hint about ``green enhance`` should fire.
        assert "green enhance" in result.stdout

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_no_enhance_with_no_api_key_prints_actionable_hint(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """``--no-enhance`` without an API key still tells the user what happened.

        Regression test for the silent-feedback bug: without this
        branch the user sees neither the legacy "AI features disabled"
        block (suppressed by ``--no-enhance``) nor the
        "run ``green enhance`` later" hint, leaving them with no idea
        what their flag did.
        """
        mock_init_orch.return_value = None  # Simulate no key found.

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "no-enhance-no-key",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-enhance",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        mock_init_orch.assert_called_once()
        # Specifically the "no API key found" branch — separate string
        # from the key-found branch so a future refactor that collapses
        # them is loud.
        assert "no API key found" in result.stdout
        # And the actionable next-step pointer.
        assert "ANTHROPIC_API_KEY" in result.stdout

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_no_enhance_with_explicit_api_key_is_documented_happy_path(
        self, mock_init_orch: Mock, tmp_path: Path
    ) -> None:
        """``--no-enhance --api-key X`` is the documented "tune later" combo."""
        mock_init_orch.return_value = MagicMock(spec=AIOrchestrator)

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "no-enhance-with-key",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-enhance",
                "--api-key",
                "sk-test-key",
                "--no-interactive",
            ],
        )

        # Validator accepts the combo (no exit 1) and the helper is
        # called with the explicit key.
        assert result.exit_code == 0
        mock_init_orch.assert_called_once()
        # The key-found branch ran (not the no-key branch).
        assert "run `green enhance`" in result.stdout
        assert "no API key found" not in result.stdout

    def test_offline_and_no_enhance_together_exits(self, tmp_path: Path) -> None:
        """Validator surfaces conflict with exit code 1."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "conflict",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--offline",
                "--no-enhance",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 1
        assert "redundant" in result.stdout

    def test_offline_with_api_key_together_exits(self, tmp_path: Path) -> None:
        """Validator surfaces ``--offline --api-key`` conflict at the CLI layer.

        The validator unit test (``TestValidatePass2Flags
        .test_offline_with_api_key_rejected``) covers the validator
        in isolation, but typer's option-parsing layer is its own
        moving part. The symmetric ``--offline --no-enhance`` test
        above exercises the same path end-to-end; this test is the
        missing counterpart that locks the ``--offline --api-key``
        wiring all the way from CLI argv to the validator's exit-1
        path.
        """
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "conflict",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--offline",
                "--api-key",
                "sk-test-key",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 1
        assert "contradictory" in result.stdout


class TestEnhanceDetectionHelpers:
    """Cover the auto-detection helpers used by ``green enhance``."""

    def test_detect_project_name_reads_h1(self, tmp_path: Path) -> None:
        """``_detect_project_name`` parses the ``Claude Code Project Context`` H1."""
        (tmp_path / "CLAUDE.md").write_text(
            "# Claude Code Project Context: my-cool-app\n\nrest of file...\n",
            encoding="utf-8",
        )
        assert cli._detect_project_name(tmp_path) == "my-cool-app"

    def test_detect_project_name_returns_none_without_claude_md(
        self, tmp_path: Path
    ) -> None:
        """Missing CLAUDE.md returns ``None`` (caller falls back to --project-name)."""
        assert cli._detect_project_name(tmp_path) is None

    def test_detect_project_name_returns_none_for_unmatched_h1(
        self, tmp_path: Path
    ) -> None:
        """Different H1 → ``None`` so we don't grab the wrong string."""
        (tmp_path / "CLAUDE.md").write_text(
            "# Some Other Title\n\n",
            encoding="utf-8",
        )
        assert cli._detect_project_name(tmp_path) is None

    def test_detect_project_language_python(self, tmp_path: Path) -> None:
        """``pyproject.toml`` → python."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        assert cli._detect_project_language(tmp_path) == "python"

    def test_detect_project_language_typescript(self, tmp_path: Path) -> None:
        """``package.json`` → typescript."""
        (tmp_path / "package.json").write_text("{}")
        assert cli._detect_project_language(tmp_path) == "typescript"

    def test_detect_project_language_kotlin(self, tmp_path: Path) -> None:
        """``settings.gradle.kts`` → kotlin (#356)."""
        (tmp_path / "settings.gradle.kts").write_text('rootProject.name = "x"\n')
        assert cli._detect_project_language(tmp_path) == "kotlin"

    def test_detect_project_language_groovy_gradle_stays_java(
        self, tmp_path: Path
    ) -> None:
        """A Groovy ``build.gradle`` (no .kts) still detects as java."""
        (tmp_path / "build.gradle").write_text("apply plugin: 'java'\n")
        assert cli._detect_project_language(tmp_path) == "java"

    def test_detect_project_language_cpp_tizen_manifest(self, tmp_path: Path) -> None:
        """``tizen-manifest.xml`` → cpp (#361)."""
        (tmp_path / "tizen-manifest.xml").write_text("<manifest/>\n")
        assert cli._detect_project_language(tmp_path) == "cpp"

    def test_detect_project_language_cpp_conanfile(self, tmp_path: Path) -> None:
        """``conanfile.txt`` → cpp (#361)."""
        (tmp_path / "conanfile.txt").write_text("[requires]\n")
        assert cli._detect_project_language(tmp_path) == "cpp"

    def test_detect_project_language_cpp_cmakelists(self, tmp_path: Path) -> None:
        """``CMakeLists.txt`` alone → cpp (#361)."""
        (tmp_path / "CMakeLists.txt").write_text("project(x)\n")
        assert cli._detect_project_language(tmp_path) == "cpp"

    def test_detect_project_language_cmakelists_never_shadows_others(
        self, tmp_path: Path
    ) -> None:
        """A Rust project vendoring CMake still detects as rust.

        CMakeLists.txt shows up inside other ecosystems' projects (native
        build scripts, vendored deps), so every more specific probe must
        win over the cpp fallback.
        """
        (tmp_path / "CMakeLists.txt").write_text("project(x)\n")
        (tmp_path / "Cargo.toml").write_text("[package]\n")
        assert cli._detect_project_language(tmp_path) == "rust"

    def test_detect_project_language_returns_none_for_empty(
        self, tmp_path: Path
    ) -> None:
        """No probe matches → ``None``."""
        assert cli._detect_project_language(tmp_path) is None


class TestEnhanceTargetResolution:
    """Cover ``_resolve_enhance_targets`` and ``_validate_enhance_target``."""

    def test_no_targets_means_all(self) -> None:
        """``None`` (no flag) selects every canonical target."""
        assert cli._resolve_enhance_targets(None) == cli._ENHANCE_TARGETS

    def test_empty_list_means_all(self) -> None:
        """An empty list also means "all" — shouldn't deselect everything."""
        assert cli._resolve_enhance_targets([]) == cli._ENHANCE_TARGETS

    def test_repeated_flag(self) -> None:
        """``--targets claude-md --targets subagents`` → both, in canonical order."""
        assert cli._resolve_enhance_targets(["claude-md", "subagents"]) == (
            "claude-md",
            "subagents",
        )

    def test_comma_separated(self) -> None:
        """``--targets claude-md,subagents`` → both, in canonical order."""
        assert cli._resolve_enhance_targets(["claude-md,subagents"]) == (
            "claude-md",
            "subagents",
        )

    def test_canonical_ordering(self) -> None:
        """Order in input is irrelevant; canonical order wins."""
        assert cli._resolve_enhance_targets(["subagents", "claude-md"]) == (
            "claude-md",
            "subagents",
        )

    def test_deduplicates(self) -> None:
        """Duplicate targets are squashed."""
        assert cli._resolve_enhance_targets(["claude-md", "claude-md,claude-md"]) == (
            "claude-md",
        )

    def test_unknown_target_raises(self) -> None:
        """An unknown target surfaces a typer.BadParameter."""
        with pytest.raises(typer.BadParameter, match="unknown target"):
            cli._resolve_enhance_targets(["bogus"])


class TestEnhanceCommand:
    """End-to-end CLI tests for the new ``enhance`` command."""

    @staticmethod
    def _flat(text: str) -> str:
        """Collapse whitespace so substring checks survive Rich line-wrapping."""
        return " ".join(text.split())

    @staticmethod
    def _make_project(tmp_path: Path, *, name: str, language: str) -> Path:
        """Build a minimal green-init-shaped directory layout."""
        project = tmp_path / name
        project.mkdir()
        (project / "CLAUDE.md").write_text(
            f"# Claude Code Project Context: {name}\n\nbaseline content.\n",
            encoding="utf-8",
        )
        # Drop a marker file so language detection works without flags.
        if language == "python":
            (project / "pyproject.toml").write_text("[project]\nname='x'\n")
        elif language == "typescript":
            (project / "package.json").write_text("{}")
        # Pre-create the subagents dir so the writer doesn't have to
        # mkdir during the test (mirrors real init output).
        (project / ".claude" / "agents").mkdir(parents=True)
        return project

    def test_missing_path_exits(self, tmp_path: Path) -> None:
        """Non-existent path exits 1 with an actionable message."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(tmp_path / "does-not-exist")],
        )
        assert result.exit_code == 1
        assert "does not exist" in self._flat(result.stdout)

    def test_path_is_a_file_exits(self, tmp_path: Path) -> None:
        """Pointing at a file (not directory) exits 1."""
        a_file = tmp_path / "looks-like-a-project"
        a_file.write_text("not a directory")
        runner = CliRunner()
        result = runner.invoke(cli.app, ["enhance", str(a_file)])
        assert result.exit_code == 1
        assert "is not a directory" in self._flat(result.stdout)

    def test_directory_without_claude_md_exits(self, tmp_path: Path) -> None:
        """Empty directory without CLAUDE.md exits 1 with the actionable hint."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["enhance", str(tmp_path)])
        assert result.exit_code == 1
        assert "does not look like a green-init project" in self._flat(result.stdout)

    def test_unknown_target_exits(self, tmp_path: Path) -> None:
        """``--targets bogus`` exits non-zero before any API call."""
        project = self._make_project(tmp_path, name="proj", language="python")
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--targets", "bogus"],
        )
        assert result.exit_code != 0
        # ``typer.BadParameter`` writes to stderr; CliRunner.output
        # mixes both streams while .stdout omits stderr.
        assert "unknown target" in self._flat(result.output)

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_no_api_key_exits_with_actionable_message(
        self, mock_init: Mock, tmp_path: Path
    ) -> None:
        """``enhance`` cannot run without a key — fail loudly, don't no-op."""
        mock_init.return_value = None  # No key available.
        project = self._make_project(tmp_path, name="needs-key", language="python")
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--no-interactive"],
        )
        assert result.exit_code == 1
        flat = self._flat(result.stdout)
        # ``enhance`` now accepts ``--provider``/``--model``, so the
        # no-key message must be provider-neutral (regression: #383).
        assert "requires an API key for the selected provider" in flat
        assert "Anthropic API key" not in flat
        assert "ANTHROPIC_API_KEY" in flat

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_omits_config_tier_by_design(
        self,
        mock_init: Mock,
        mock_claude: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """``enhance`` intentionally has no config-file tier (see #396).

        Unlike ``green init`` (4 tiers), ``enhance`` has no ``--config``
        flag and loads no config file, so it deliberately wires only
        CLI flag > env > built-in default. The selection inputs it builds
        must therefore carry ``config_data is None`` — the config tier is
        a no-op here. Tracked for future wiring as issue #396.
        """
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path, name="no-config", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--model", "Flag-Model", "--no-interactive"],
        )

        assert result.exit_code == 0, result.stdout
        selection_inputs = mock_init.call_args.kwargs["selection_inputs"]
        # The config tier is omitted by design: enhance has no config input.
        assert selection_inputs.config_data is None
        # The CLI ``--model`` flag still flows through (case preserved).
        assert selection_inputs.model_flag == "Flag-Model"

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_default_runs_every_target(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """No ``--targets`` flag → both helpers are invoked."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path, name="full", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--no-interactive"],
        )

        assert result.exit_code == 0, result.stdout
        mock_claude.assert_called_once()
        mock_subagents.assert_called_once()

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_targets_claude_md_skips_subagents(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """``--targets claude-md`` runs only that target."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path, name="claude-only", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--targets",
                "claude-md",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0, result.stdout
        mock_claude.assert_called_once()
        mock_subagents.assert_not_called()

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_dry_run_propagates_to_helpers(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """``--dry-run`` flows through to every target helper."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path, name="preview", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--dry-run", "--no-interactive"],
        )

        assert result.exit_code == 0, result.stdout
        # Both helpers receive ``dry_run=True``.
        assert mock_claude.call_args.kwargs["dry_run"] is True
        assert mock_subagents.call_args.kwargs["dry_run"] is True
        assert "Dry run complete" in result.stdout

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_explicit_overrides_skip_detection(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """``-n`` and ``-l`` win over auto-detection from the project."""
        _make_orch_mock(mock_init)
        # Make the project look like Python + name="auto-name", but
        # override both at the CLI.
        project = self._make_project(tmp_path, name="auto-name", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--project-name",
                "explicit-name",
                "--language",
                "typescript",
                "--targets",
                "claude-md",
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0, result.stdout
        # The helper was called with the *explicit* values, not the
        # auto-detected ones.
        call = mock_claude.call_args
        # positional args: (project: _EnhanceProjectContext, orchestrator)
        assert call.args[0].project_name == "explicit-name"
        assert call.args[0].language == "typescript"

    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_unknown_language_in_override_exits(
        self, mock_init: Mock, tmp_path: Path
    ) -> None:
        """``-l cobol`` is rejected before any API call."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path, name="bad-lang", language="python")

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--language",
                "cobol",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 1
        assert "Unsupported language" in self._flat(result.stdout)


class TestEnhanceSkipUnchanged:
    """Phase 3c — ``green enhance`` skips targets whose source hash matches state."""

    @staticmethod
    def _make_project(tmp_path: Path) -> Path:
        project = tmp_path / "phase-3c-project"
        project.mkdir()
        (project / "CLAUDE.md").write_text(
            "# Claude Code Project Context: phase-3c-project\n", encoding="utf-8"
        )
        (project / "pyproject.toml").write_text("[project]\nname='x'\n")
        (project / ".claude" / "agents").mkdir(parents=True)
        return project

    @staticmethod
    def _flat(text: str) -> str:
        return " ".join(text.split())

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_state_file_written_after_first_enhance(
        self,
        mock_init: Mock,
        mock_claude: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """First enhance run writes ``.claude/.enhance-state.json`` for both targets."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)

        runner = CliRunner()
        result = runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])

        assert result.exit_code == 0, result.stdout

        state = load_state(project)
        assert "claude-md" in state.completed
        assert "subagents" in state.completed
        # Model name is recorded for diagnostics.
        assert state.completed["claude-md"].model == "claude-sonnet-4-5"

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_unchanged_target_is_skipped(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """Second enhance with no input change skips both target helpers."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)

        runner = CliRunner()
        # First run — both targets execute, state is written.
        first = runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])
        assert first.exit_code == 0
        assert mock_claude.call_count == 1
        assert mock_subagents.call_count == 1

        # Second run — no source changed → both helpers skipped.
        mock_claude.reset_mock()
        mock_subagents.reset_mock()
        second = runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])

        assert second.exit_code == 0, second.stdout
        mock_claude.assert_not_called()
        mock_subagents.assert_not_called()
        flat = self._flat(second.stdout)
        assert "CLAUDE.md unchanged" in flat
        assert "Subagents unchanged" in flat

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_force_overrides_skip(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """``--force`` re-tunes even when the source hash matches."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)

        runner = CliRunner()
        # Seed state with a successful first run.
        runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])
        mock_claude.reset_mock()
        mock_subagents.reset_mock()

        # Capture the seeded state's last_run timestamp so we can
        # verify the force run actually rewrites the record (not just
        # re-invokes the helpers).
        seeded_state = load_state(project)
        seeded_last_run = seeded_state.last_run
        seeded_claude_ts = seeded_state.completed["claude-md"].timestamp

        # --force → skip is bypassed AND state is updated.
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--no-interactive", "--force"],
        )
        assert result.exit_code == 0
        assert mock_claude.call_count == 1
        assert mock_subagents.call_count == 1

        # The PR description's claim ("forced re-tunes produce an
        # idempotent state file") only holds if mark_completed runs
        # on the force path. Verify by reading the state file after
        # the force run and asserting both records are present and
        # carry refreshed timestamps.
        post_force = load_state(project)
        assert "claude-md" in post_force.completed
        assert "subagents" in post_force.completed
        assert post_force.completed["claude-md"].model == "claude-sonnet-4-5"
        assert post_force.completed["subagents"].model == "claude-sonnet-4-5"
        # Timestamps moved forward — rules out the silent "we ran
        # the helpers but forgot to mark_completed" regression.
        assert post_force.last_run >= seeded_last_run
        assert post_force.completed["claude-md"].timestamp >= seeded_claude_ts

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_changed_overrides_skip(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """Project name change → CLAUDE.md hash differs → re-tune fires."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)

        runner = CliRunner()
        # Seed state with the auto-detected project name.
        runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])
        mock_claude.reset_mock()
        mock_subagents.reset_mock()

        # Override the project name → both target hashes change.
        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--project-name",
                "renamed-project",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        assert mock_claude.call_count == 1
        assert mock_subagents.call_count == 1

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_dry_run_does_not_persist_state(
        self,
        mock_init: Mock,
        mock_claude: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """``--dry-run`` runs the helpers but doesn't claim a tune happened."""
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--dry-run", "--no-interactive"],
        )

        assert result.exit_code == 0
        # The state file must not exist after a dry run; otherwise the
        # next real run would skip these targets thinking they're up
        # to date when no actual write happened.
        state_file = project / ".claude" / ".enhance-state.json"
        assert not state_file.exists(), state_file.read_text(encoding="utf-8")

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_dry_run_after_seeded_state_leaves_file_untouched(
        self,
        mock_init: Mock,
        mock_claude: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """A dry run after a real run preserves the existing state file.

        Catches a regression where dry-run logic might bump the
        ``last_run`` timestamp or otherwise rewrite the file even
        though no tune actually happened.
        """
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)
        runner = CliRunner()

        # Seed real state.
        runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])
        state_file = project / ".claude" / ".enhance-state.json"
        seeded_bytes = state_file.read_bytes()

        # Dry run after seeded state — file must be byte-identical.
        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--dry-run", "--no-interactive"],
        )
        assert result.exit_code == 0
        assert state_file.read_bytes() == seeded_bytes

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_force_dry_run_combo_does_not_persist_state(
        self,
        mock_init: Mock,
        mock_claude: Mock,
        mock_subagents: Mock,
        tmp_path: Path,
    ) -> None:
        """``--force --dry-run`` invokes helpers but leaves state on disk untouched.

        Both flags are independently respected: ``--force`` bypasses
        the skip so the helpers run; ``--dry-run`` short-circuits
        ``_persist_enhance_state`` so no write happens.
        """
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)
        runner = CliRunner()

        runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])
        state_file = project / ".claude" / ".enhance-state.json"
        seeded_bytes = state_file.read_bytes()
        mock_claude.reset_mock()
        mock_subagents.reset_mock()

        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--force",
                "--dry-run",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0
        # ``--force`` ran the helpers…
        assert mock_claude.call_count == 1
        assert mock_subagents.call_count == 1
        # …but ``--dry-run`` left the state file byte-identical.
        assert state_file.read_bytes() == seeded_bytes

    @patch("start_green_stay_green.cli._enhance_subagents")
    @patch("start_green_stay_green.cli._enhance_claude_md")
    @patch("start_green_stay_green.cli._initialize_orchestrator")
    def test_persist_skipped_when_every_target_is_skipped(
        self,
        mock_init: Mock,
        mock_claude: Mock,  # noqa: ARG002 — kept for @patch ordering
        mock_subagents: Mock,  # noqa: ARG002 — kept for @patch ordering
        tmp_path: Path,
    ) -> None:
        """A run where every target is skipped never calls ``save_state``.

        Pairs with ``test_unchanged_target_is_skipped`` but asserts
        the implementation detail directly: no spurious ``last_run``
        bumps from no-op invocations.
        """
        _make_orch_mock(mock_init)
        project = self._make_project(tmp_path)
        runner = CliRunner()

        # Seed state (real ``save_state``).
        runner.invoke(cli.app, ["enhance", str(project), "--no-interactive"])

        # Second run — every target skipped. Patch ``save_state`` only
        # for this invocation so the seed actually persisted.
        with patch("start_green_stay_green.cli.save_state") as mock_save:
            result = runner.invoke(
                cli.app, ["enhance", str(project), "--no-interactive"]
            )
        assert result.exit_code == 0
        mock_save.assert_not_called()


class TestEnhanceSourceHashes:
    """Hash determinism + sensitivity for the per-target hash helpers."""

    def test_claude_md_hash_changes_with_project_name(self) -> None:
        a = cli._compute_target_source_hash("claude-md", "alpha", "python")
        b = cli._compute_target_source_hash("claude-md", "beta", "python")
        assert a != b

    def test_claude_md_hash_changes_with_language(self) -> None:
        a = cli._compute_target_source_hash("claude-md", "alpha", "python")
        b = cli._compute_target_source_hash("claude-md", "alpha", "go")
        assert a != b

    def test_claude_md_hash_is_deterministic(self) -> None:
        a = cli._compute_target_source_hash("claude-md", "alpha", "python")
        b = cli._compute_target_source_hash("claude-md", "alpha", "python")
        assert a == b
        assert a.startswith("sha256:")

    def test_subagents_hash_changes_with_project_name(self) -> None:
        a = cli._compute_target_source_hash("subagents", "alpha", "python")
        b = cli._compute_target_source_hash("subagents", "beta", "python")
        assert a != b

    def test_subagents_hash_is_deterministic(self) -> None:
        a = cli._compute_target_source_hash("subagents", "alpha", "python")
        b = cli._compute_target_source_hash("subagents", "alpha", "python")
        assert a == b

    def test_unknown_target_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown target"):
            cli._compute_target_source_hash("bogus", "alpha", "python")

    def test_target_namespace_separation(self) -> None:
        """Two targets with same metadata must hash differently — no collisions."""
        a = cli._compute_target_source_hash("claude-md", "alpha", "python")
        b = cli._compute_target_source_hash("subagents", "alpha", "python")
        assert a != b


class TestReferenceFileWarning:
    """``_read_reference_or_warn`` returns "" + prints when file missing."""

    def test_missing_file_prints_warning_and_returns_empty(
        self, tmp_path: Path
    ) -> None:
        """Broken-install case: missing ref → warning + empty string.

        Regression test for the silent-empty-hash issue: if a
        reference file vanishes (moved submodule, partial install)
        the helper must surface that to the user instead of silently
        baking the empty hash into the state file and permanently
        suppressing future re-tunes.
        """
        missing = tmp_path / "nope.md"
        with patch("start_green_stay_green.cli.console") as mock_console:
            result = cli._read_reference_or_warn(missing, "test label")

        assert result == ""
        mock_console.print.assert_called_once()
        # The warning names the file label so a user can tell which
        # of the several refs is broken.
        printed = mock_console.print.call_args[0][0]
        assert "test label" in printed
        assert "missing" in printed.lower()

    def test_present_file_returns_contents_silently(self, tmp_path: Path) -> None:
        """The happy path stays silent — no warning when the file exists."""
        path = tmp_path / "ref.md"
        path.write_text("hello\n", encoding="utf-8")
        with patch("start_green_stay_green.cli.console") as mock_console:
            result = cli._read_reference_or_warn(path, "test label")

        assert result == "hello\n"
        mock_console.print.assert_not_called()


class TestEnhanceDispatchAssertion:
    """The import-time guard that catches typos in ``_ENHANCE_DISPATCH``."""

    def test_assert_raises_when_helper_is_undefined(self) -> None:
        """A typo'd helper name in the table is caught at import time."""
        bogus = cli._EnhanceTargetSpec(
            skip_message="[dim]nope[/dim]",
            helper_name="_does_not_exist",
            hash_helper_name="_hash_claude_md_inputs",
        )
        with (
            patch.dict(cli._ENHANCE_DISPATCH, {"bogus": bogus}, clear=False),
            pytest.raises(RuntimeError, match="undefined helper"),
        ):
            cli._assert_enhance_dispatch_intact()

    def test_assert_raises_when_hash_helper_is_undefined(self) -> None:
        """The guard also catches typos in ``hash_helper_name``."""
        bogus = cli._EnhanceTargetSpec(
            skip_message="[dim]nope[/dim]",
            helper_name="_enhance_claude_md",
            hash_helper_name="_does_not_exist",
        )
        with (
            patch.dict(cli._ENHANCE_DISPATCH, {"bogus": bogus}, clear=False),
            pytest.raises(RuntimeError, match="undefined helper"),
        ):
            cli._assert_enhance_dispatch_intact()


class TestEnhanceBatchCLI:
    """Phase 5b: ``green enhance --batch`` flag wiring."""

    @staticmethod
    def _flat(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _make_project(tmp_path: Path, *, name: str = "proj") -> Path:
        project = tmp_path / name
        project.mkdir()
        (project / "CLAUDE.md").write_text(
            f"# Claude Code Project Context: {name}\n\nbaseline.\n",
            encoding="utf-8",
        )
        (project / "pyproject.toml").write_text("[project]\nname='x'\n")
        (project / ".claude" / "agents").mkdir(parents=True)
        return project

    def test_batch_with_claude_md_target_exits_with_clear_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--batch --targets claude-md`` is rejected before any API call.

        Phase 5a primitives only handle ``tool_use`` requests; the
        sync claude-md path uses free-text generation. Failing fast
        keeps the user model honest.
        """
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            cli.app,
            [
                "enhance",
                str(project),
                "--batch",
                "--targets",
                "claude-md",
            ],
        )

        assert result.exit_code == 1
        flat = self._flat(result.stdout)
        assert "--batch does not support targets claude-md" in flat
        # Suggests the working invocation rather than just erroring.
        assert "--targets subagents" in flat

    def test_wait_without_batch_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--wait`` only makes sense paired with ``--batch``."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)
        runner = CliRunner()

        result = runner.invoke(
            cli.app,
            ["enhance", str(project), "--wait"],
        )

        assert result.exit_code == 1
        assert "--wait only applies in --batch mode" in self._flat(result.stdout)

    def test_batch_dry_run_short_circuits_without_calling_api(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``--batch --dry-run`` prints a notice and does NOT submit."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)
        # Patch the dispatch helpers so a slip would be loud.
        with (
            mock.patch("start_green_stay_green.cli.submit_subagent_batch") as submit,
            mock.patch("start_green_stay_green.cli.resume_subagent_batch") as resume,
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli.app,
                [
                    "enhance",
                    str(project),
                    "--batch",
                    "--targets",
                    "subagents",
                    "--dry-run",
                ],
            )

        assert result.exit_code == 0
        assert "--dry-run with --batch" in self._flat(result.stdout)
        submit.assert_not_called()
        resume.assert_not_called()

    def test_first_run_batch_with_wait_warns_no_op(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``green enhance --batch --wait`` on first-run prints a no-op warning.

        Issue #319: the submit branch silently ignored ``--wait``
        because the submit call itself never blocks (ADR-001 two-call
        contract). The user is told upfront so they know to pass
        ``--wait`` again on the resume call.
        """
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)

        fake_outcome = mock.MagicMock()
        fake_outcome.submission.batch_id = "msgbatch_first_run"
        fake_outcome.agent_count = 7

        with mock.patch(
            "start_green_stay_green.cli.submit_subagent_batch",
            new=mock.AsyncMock(return_value=fake_outcome),
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli.app,
                [
                    "enhance",
                    str(project),
                    "--batch",
                    "--targets",
                    "subagents",
                    "--wait",
                ],
            )

        assert result.exit_code == 0, result.stdout
        flat = self._flat(result.stdout)
        assert "--wait has no effect on the first --batch call" in flat
        # The success message still surfaces — warning is additive.
        assert "Submitted batch" in flat
        assert "msgbatch_first_run" in flat

    def test_batch_submit_api_error_exits_cleanly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``AIGenerationError`` from submit → exit 1 + clear message.

        Review feedback (PR #315): the docstring of
        :func:`submit_subagent_batch` lists ``GenerationError`` as a
        documented raise, but the CLI lacked a handler so a real
        SDK-side failure produced an uncaught traceback. This test
        pins the post-feedback behaviour: human-readable error, exit
        code 1, no stack trace bleeding to stdout.
        """
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)

        # ``submit_subagent_batch`` raises before any state is written
        # so there's no in-flight batch on disk after the run.
        with mock.patch(
            "start_green_stay_green.cli.submit_subagent_batch",
            side_effect=AIGenerationError("Anthropic API rejected the batch (mocked)"),
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli.app,
                [
                    "enhance",
                    str(project),
                    "--batch",
                    "--targets",
                    "subagents",
                ],
            )

        assert result.exit_code == 1
        flat = self._flat(result.stdout)
        assert "Batch API call failed" in flat
        # Original error message survives so the user sees what went wrong.
        assert "Anthropic API rejected the batch (mocked)" in flat
        # No raw traceback in user-facing output.
        assert "Traceback" not in result.stdout

    def test_batch_resume_api_error_exits_cleanly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``AIGenerationError`` from resume → exit 1 + clear message."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        project = self._make_project(tmp_path)
        # Pre-seed an in-flight batch so the resume branch is taken.
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_pre_seeded",
            submitted_at="2026-05-09T22:00:00+00:00",
            custom_id_map={"subagent:alpha": "subagents"},
        )
        save_state(project, state)

        with mock.patch(
            "start_green_stay_green.cli.resume_subagent_batch",
            side_effect=AIGenerationError("poll failed (mocked)"),
        ):
            runner = CliRunner()
            result = runner.invoke(
                cli.app,
                [
                    "enhance",
                    str(project),
                    "--batch",
                    "--targets",
                    "subagents",
                ],
            )

        assert result.exit_code == 1
        flat = self._flat(result.stdout)
        assert "Batch API call failed" in flat
        assert "poll failed (mocked)" in flat

    def test_render_unknown_status_fails_loudly(self) -> None:
        """An out-of-enum status must fail loudly rather than silently
        rendering as ``ENDED``.

        Phase 6c migrated :class:`ResumeStatus` to :class:`enum.StrEnum`
        and the dispatcher to a ``match`` statement with
        :func:`typing.assert_never` — so a future member added without
        updating ``_render_batch_resume_outcome`` is caught at mypy
        time, not just at runtime. The runtime guard remains as
        defense-in-depth: type checkers can be silenced or skipped, so
        an out-of-enum value reaching the dispatcher still raises
        ``AssertionError`` from ``assert_never`` rather than producing
        a misleading "0 written, 0 failed" line.
        """
        # ``# type: ignore[arg-type]`` is exactly how a future
        # forgotten-case bug would manifest — a developer might silence
        # mypy here without realising the dispatcher hasn't been
        # extended. The runtime guard catches it anyway.
        bad = ResumeOutcome(status="bogus-status")  # type: ignore[arg-type]

        with pytest.raises(AssertionError, match="unreachable"):
            cli._render_batch_resume_outcome(bad)
