"""Tests for the ``green init --windows-ci`` opt-in flag (#388).

Covers:

- flag validation: unsupported languages fail fast with an actionable
  message before any file is generated
- plumbing: the flag reaches ``_generate_ci_step`` and flips the
  ``CIGenerator`` Windows leg on
- the default-off contract at the CLI layer: omitting the flag emits a
  ci.yml with no Windows content
- help text discoverability
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import typer
from typer.testing import CliRunner
import yaml

from start_green_stay_green import cli
from start_green_stay_green.generators.ci_windows import WINDOWS_CI_LANGUAGES
from start_green_stay_green.generators.ci_windows import WINDOWS_JOB_ID
from start_green_stay_green.utils.file_writer import FileWriter

if TYPE_CHECKING:
    from pathlib import Path


class TestValidateWindowsCiLanguage:
    """Test the _validate_windows_ci_language helper."""

    def test_flag_off_accepts_every_language(self) -> None:
        """Without the flag no language is rejected."""
        for language in ("python", "swift", "cpp", "kotlin"):
            cli._validate_windows_ci_language(
                windows_ci=False, primary_language=language
            )

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_flag_on_accepts_supported_languages(self, language: str) -> None:
        """Supported languages pass validation with the flag on."""
        cli._validate_windows_ci_language(windows_ci=True, primary_language=language)

    @pytest.mark.parametrize("language", ["swift", "cpp", "kotlin"])
    def test_flag_on_rejects_unsupported_language(self, language: str) -> None:
        """Unsupported languages exit with an actionable message."""
        with pytest.raises(typer.Exit):
            cli._validate_windows_ci_language(
                windows_ci=True, primary_language=language
            )


class TestGenerateCiStepWindowsFlag:
    """Test that the CI step forwards the flag to the generator."""

    def test_windows_ci_emits_quality_windows_job(self, tmp_path: Path) -> None:
        """The step writes a ci.yml containing the Windows job."""
        writer = FileWriter(project_root=tmp_path)
        pass2 = cli._Pass2Options(orchestrator=None, windows_ci=True)
        cli._generate_ci_step(tmp_path, "my-project", "python", pass2, writer)
        content = (tmp_path / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        parsed = yaml.safe_load(content)
        assert WINDOWS_JOB_ID in parsed["jobs"]

    def test_default_emits_no_windows_content(self, tmp_path: Path) -> None:
        """Without the flag the emitted ci.yml has no Windows leg."""
        writer = FileWriter(project_root=tmp_path)
        cli._generate_ci_step(tmp_path, "my-project", "python", None, writer)
        content = (tmp_path / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        assert WINDOWS_JOB_ID not in content
        assert "windows-latest" not in content


class TestInitWindowsCiFlag:
    """Test the end-to-end ``green init --windows-ci`` behaviour."""

    def test_init_rejects_windows_ci_for_unsupported_language(
        self, tmp_path: Path
    ) -> None:
        """swift + --windows-ci fails fast, before generating files."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "sample-swift",
                "-l",
                "swift",
                "-o",
                str(tmp_path),
                "--offline",
                "--no-interactive",
                "--windows-ci",
            ],
        )
        assert result.exit_code != 0
        assert "--windows-ci" in result.output
        assert not (tmp_path / "sample-swift").exists()

    def test_init_windows_ci_writes_windows_leg(self, tmp_path: Path) -> None:
        """Opting in lands the Windows job in the generated ci.yml."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "sample-python",
                "-l",
                "python",
                "-o",
                str(tmp_path),
                "--offline",
                "--no-interactive",
                "--windows-ci",
            ],
        )
        assert result.exit_code == 0, result.output
        ci_file = tmp_path / "sample-python" / ".github" / "workflows" / "ci.yml"
        parsed = yaml.safe_load(ci_file.read_text(encoding="utf-8"))
        job = parsed["jobs"][WINDOWS_JOB_ID]
        assert job["runs-on"] == "windows-latest"

    def test_init_help_documents_windows_ci(self) -> None:
        """--help mentions the flag so users can discover it."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--windows-ci" in result.output
