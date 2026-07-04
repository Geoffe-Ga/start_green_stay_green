"""Tests for the ``green init --with-ralph-loop`` opt-in flag.

Covers:

- plumbing: the flag reaches ``_generate_ralph_loop_step`` and copies the
  Ralph fleet-loop scaffolding
- the default-off contract at the CLI layer: omitting the flag generates
  no Ralph-related paths at all
- help text discoverability
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from typer.testing import CliRunner

from start_green_stay_green import cli
from start_green_stay_green.utils.file_writer import FileWriter

if TYPE_CHECKING:
    from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    """Normalize rich-rendered CLI output for substring assertions."""
    return re.sub(r"[│╭╮╰╯─\s]+", "", _ANSI_RE.sub("", output))


class TestGenerateRalphLoopStep:
    """Test the step function directly (no CLI invocation overhead)."""

    def test_no_op_when_flag_is_false(self, tmp_path: Path) -> None:
        """Without the flag, nothing Ralph-related is written."""
        writer = FileWriter(project_root=tmp_path)
        cli._generate_ralph_loop_step(
            tmp_path, with_ralph_loop=False, file_writer=writer
        )
        assert not (tmp_path / ".claude" / "commands").exists()
        assert not (tmp_path / "scripts" / "ralph").exists()
        assert not (tmp_path / ".github" / "deslop-areas.json").exists()

    def test_copies_scaffolding_when_flag_is_true(self, tmp_path: Path) -> None:
        """With the flag, the fleet loop scaffolding lands on disk."""
        writer = FileWriter(project_root=tmp_path)
        cli._generate_ralph_loop_step(
            tmp_path, with_ralph_loop=True, file_writer=writer
        )
        assert (tmp_path / ".claude" / "commands" / "ralph-tick.md").is_file()
        assert (tmp_path / "scripts" / "ralph" / "fleet.sh").is_file()
        assert (tmp_path / ".github" / "deslop-areas.json").is_file()
        assert (
            tmp_path / ".claude" / "skills" / "scan-issue-writer" / "SKILL.md"
        ).is_file()
        assert (tmp_path / ".claude" / "skills" / "de-slopify" / "SKILL.md").is_file()


class TestInitRalphLoopFlag:
    """Test the end-to-end ``green init --with-ralph-loop`` behaviour."""

    def test_init_default_generates_no_ralph_content(self, tmp_path: Path) -> None:
        """Omitting the flag leaves the project free of any Ralph paths."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "sample-noralph",
                "-l",
                "python",
                "-o",
                str(tmp_path),
                "--offline",
                "--no-interactive",
            ],
        )
        assert result.exit_code == 0, result.output
        project = tmp_path / "sample-noralph"
        assert not (project / ".claude" / "commands").exists()
        assert not (project / "scripts" / "ralph").exists()
        assert not (project / ".github" / "deslop-areas.json").exists()
        assert not (project / ".claude" / "skills" / "de-slopify").exists()

    def test_init_with_ralph_loop_generates_scaffolding(self, tmp_path: Path) -> None:
        """Opting in lands the full Ralph fleet-loop scaffolding."""
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            [
                "init",
                "--project-name",
                "sample-ralph",
                "-l",
                "python",
                "-o",
                str(tmp_path),
                "--offline",
                "--no-interactive",
                "--with-ralph-loop",
            ],
        )
        assert result.exit_code == 0, result.output
        project = tmp_path / "sample-ralph"
        assert (project / ".claude" / "commands" / "ralph-tick.md").is_file()
        assert (project / ".claude" / "agents" / "ralph-worker.md").is_file()
        assert (project / "scripts" / "ralph" / "fleet.sh").is_file()
        assert (project / ".github" / "workflows" / "hopper.yml").is_file()
        assert (project / ".github" / "deslop-areas.json").is_file()
        assert (
            project / ".claude" / "skills" / "scan-issue-writer" / "SKILL.md"
        ).is_file()

    def test_init_help_documents_with_ralph_loop(self) -> None:
        """--help mentions the flag so users can discover it."""
        runner = CliRunner()
        result = runner.invoke(cli.app, ["init", "--help"])
        assert result.exit_code == 0
        assert "--with-ralph-loop" in _plain(result.output)
