"""Mock-based tests for CLI module - fast, no CliRunner.

This module replaces the slow CliRunner-based tests with fast mock-based tests.
Tests CLI behavior by mocking dependencies instead of running full CLI.
"""

import json
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
import typer

from start_green_stay_green import cli


class TestVersionCommand:
    """Test version-related functionality."""

    def test_get_version_returns_version_string(self) -> None:
        """Test get_version returns __version__."""
        version = cli.get_version()
        assert isinstance(version, str)
        assert version


class TestConfigLoading:
    """Test configuration file loading."""

    def test_load_config_file_raises_on_missing_file(self, tmp_path: Path) -> None:
        """Test load_config_file raises FileNotFoundError for missing file."""
        non_existent_path = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            cli.load_config_file(non_existent_path)

    def test_load_config_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Test load_config_file returns empty dict (stub implementation)."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("key: value\n")
        result = cli.load_config_file(config_file)
        assert not result


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

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_loads_when_config_provided(
        self, mock_load: Mock, tmp_path: Path
    ) -> None:
        """Test _load_config_if_specified calls load_config_file."""
        mock_load.return_value = {}
        config_path = tmp_path / "config.yaml"
        cli._load_config_if_specified(config_path, verbose=False)
        mock_load.assert_called_once_with(config_path)

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_does_nothing_when_none(
        self, mock_load: Mock
    ) -> None:
        """Test _load_config_if_specified does nothing when config is None."""
        cli._load_config_if_specified(None, verbose=False)
        mock_load.assert_not_called()

    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_exits_on_file_not_found(
        self, mock_load: Mock, tmp_path: Path
    ) -> None:
        """Test _load_config_if_specified exits when config file not found."""
        mock_load.side_effect = FileNotFoundError("Not found")
        config_path = tmp_path / "config.yaml"
        with pytest.raises(typer.Exit) as exc_info:
            cli._load_config_if_specified(config_path, verbose=False)
        assert exc_info.value.exit_code == 1

    @patch("start_green_stay_green.cli.console")
    @patch("start_green_stay_green.cli.load_config_file")
    def test_load_config_if_specified_prints_verbose_message(
        self, mock_load: Mock, mock_console: Mock, tmp_path: Path
    ) -> None:
        """Test _load_config_if_specified prints message in verbose mode."""
        mock_load.return_value = {}
        config_path = tmp_path / "config.yaml"
        cli._load_config_if_specified(config_path, verbose=True)
        assert mock_console.print.call_count == 1


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


class TestOutputDirValidation:
    """Test output directory validation."""

    def test_validate_output_dir_accepts_path(self, tmp_path: Path) -> None:
        """Test _validate_output_dir accepts valid path."""
        # Function accepts Path | None and returns Path
        result = cli._validate_output_dir(tmp_path)
        assert isinstance(result, Path)


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


class TestInitCommand:
    """Test init command execution."""

    @patch("start_green_stay_green.cli._show_dry_run_preview")
    def test_init_dry_run_shows_preview(
        self, mock_preview: Mock, tmp_path: Path
    ) -> None:
        """Test init with dry_run=True shows preview."""
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
            language="python",
            api_key=None,
            dry_run=True,
            no_interactive=True,
        )
        mock_preview.assert_called_once()

    @patch("start_green_stay_green.cli._generate_project_files")
    def test_init_generates_files_when_not_dry_run(
        self, mock_generate: Mock, tmp_path: Path
    ) -> None:
        """Test init with dry_run=False calls generate."""
        mock_generate.return_value = None
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
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

    @patch("start_green_stay_green.cli._generate_project_files")
    def test_init_with_live_dashboard_passes_flag(
        self, mock_generate: Mock, tmp_path: Path
    ) -> None:
        """Test init with enable_live_dashboard=True passes flag to generator."""
        mock_generate.return_value = None
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
            language="python",
            api_key=None,
            dry_run=False,
            no_interactive=True,
            enable_live_dashboard=True,
        )
        # Verify enable_live_dashboard was passed to _generate_project_files
        assert mock_generate.called
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs["enable_live_dashboard"] is True

    @patch("start_green_stay_green.cli._generate_project_files")
    def test_init_without_live_dashboard_defaults_false(
        self, mock_generate: Mock, tmp_path: Path
    ) -> None:
        """Test init without enable_live_dashboard defaults to False."""
        mock_generate.return_value = None
        cli.init(
            project_name="test-project",
            output_dir=tmp_path,
            language="python",
            api_key=None,
            dry_run=False,
            no_interactive=True,
        )
        # Verify enable_live_dashboard defaults to False
        assert mock_generate.called
        call_kwargs = mock_generate.call_args[1]
        assert call_kwargs.get("enable_live_dashboard", False) is False


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

        # Mock shutil.copy to create a dummy workflow file when called
        def copy_side_effect(_src: Path, dst: Path) -> None:
            # Create parent directory
            dst.parent.mkdir(parents=True, exist_ok=True)
            # Write dummy workflow content
            dst.write_text("name: Metrics\nproject: start-green-stay-green")

        mock_shutil_copy.side_effect = copy_side_effect

        # Create progress bar
        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            cli._generate_metrics_dashboard_step(
                project_path=tmp_path,
                project_name="test-project",
                language="python",
                progress=progress,
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

    @patch("start_green_stay_green.cli.shutil.copy")
    @patch("start_green_stay_green.cli.MetricsGenerator")
    def test_generate_metrics_dashboard_creates_workflows_dir(
        self, mock_generator_class: Mock, mock_shutil_copy: Mock, tmp_path: Path
    ) -> None:
        """Test _generate_metrics_dashboard_step creates .github/workflows."""
        # Setup mock generator to avoid instantiation errors
        mock_generator_class.return_value = Mock()

        # Mock shutil.copy to create files
        def copy_side_effect(_src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text("dummy content")

        mock_shutil_copy.side_effect = copy_side_effect

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            cli._generate_metrics_dashboard_step(
                project_path=tmp_path,
                project_name="test-project",
                language="python",
                progress=progress,
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
        # Setup mock copy (not used but required by patch decorator order)
        mock_shutil_copy.return_value = None

        # Mock Path.exists to return False for workflow file
        with (
            patch.object(Path, "exists", return_value=False),
            Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress,
        ):
            cli._generate_metrics_dashboard_step(
                project_path=tmp_path,
                project_name="test-project",
                language="python",
                progress=progress,
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

        # Create source workflow with SGSG project name
        workflow_content = "project: start-green-stay-green\nname: Metrics"

        # Mock shutil.copy to create workflow with SGSG name
        def copy_side_effect(_src: Path, dst: Path) -> None:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(workflow_content)

        mock_shutil_copy.side_effect = copy_side_effect

        with Progress(SpinnerColumn(), TextColumn("{task.description}")) as progress:
            cli._generate_metrics_dashboard_step(
                project_path=tmp_path,
                project_name="my-new-project",
                language="python",
                progress=progress,
            )

        # Verify workflow content was replaced
        workflow_file = tmp_path / ".github" / "workflows" / "metrics.yml"
        if workflow_file.exists():
            content = workflow_file.read_text()
            assert "my-new-project" in content
            assert "start-green-stay-green" not in content
