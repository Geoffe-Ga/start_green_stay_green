"""Tests for the ``green init --agent`` target selector (#387).

Covers:

- ``--agent`` value resolution (repeatable + comma-separated, like ``-l``)
- the agent-context emit step (AGENTS.md / CONVENTIONS.md + .aider.conf.yml)
- Pass 2 gating: Claude artifacts are emitted only for the ``claude`` target
- the hard regression: default-target output is byte-identical to an
  explicit ``--agent claude`` run, with no non-Claude files added
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import typer
import yaml

from start_green_stay_green import cli
from start_green_stay_green.utils.file_writer import FileWriter

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_CLI_MODULE = "start_green_stay_green.cli"

_PASS2_STEP_NAMES = (
    "_generate_ci_step",
    "_generate_review_step",
    "_generate_claude_md_step",
    "_generate_architecture_step",
    "_generate_subagents_step",
    "_generate_agent_context_step",
)


@pytest.fixture(name="pass2_mocks")
def fixture_pass2_mocks() -> Iterator[dict[str, MagicMock]]:
    """Patch every Pass 2 step with a MagicMock and yield them by name."""
    mocks = {name: MagicMock() for name in _PASS2_STEP_NAMES}
    with patch.multiple(_CLI_MODULE, **mocks):
        yield mocks


class TestResolveAgentTargets:
    """Test _resolve_agent_targets value handling."""

    def test_default_is_claude(self) -> None:
        """Omitting --agent selects the claude target."""
        assert cli._resolve_agent_targets(None) == ("claude",)

    def test_empty_list_is_claude(self) -> None:
        """An empty list (no flags) selects the claude target."""
        assert cli._resolve_agent_targets([]) == ("claude",)

    def test_single_target(self) -> None:
        """A single explicit target is honoured."""
        assert cli._resolve_agent_targets(["agents-md"]) == ("agents-md",)

    def test_repeated_flags(self) -> None:
        """Repeated --agent flags accumulate."""
        assert cli._resolve_agent_targets(["claude", "agents-md"]) == (
            "claude",
            "agents-md",
        )

    def test_comma_separated(self) -> None:
        """Comma-separated values split like the -l language flag."""
        assert cli._resolve_agent_targets(["claude,aider"]) == ("claude", "aider")

    def test_deduplicates_and_canonical_order(self) -> None:
        """Duplicates collapse; canonical registry order is preserved."""
        assert cli._resolve_agent_targets(["aider", "claude", "aider"]) == (
            "claude",
            "aider",
        )

    def test_case_insensitive(self) -> None:
        """Target names are case-insensitive."""
        assert cli._resolve_agent_targets(["AGENTS-MD"]) == ("agents-md",)

    def test_unknown_target_rejected(self) -> None:
        """An unknown target raises a usage error naming the choices."""
        with pytest.raises(typer.BadParameter, match="cursor"):
            cli._resolve_agent_targets(["cursor"])

    def test_only_separators_rejected(self) -> None:
        """A value that splits to nothing raises a usage error."""
        with pytest.raises(typer.BadParameter, match="at least one"):
            cli._resolve_agent_targets([","])


class TestGenerateAgentContextStep:
    """Test the non-Claude agent-context emit step."""

    def test_claude_only_writes_nothing(self, tmp_path: Path) -> None:
        """The default claude target emits no extra files."""
        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("claude",), None
        )
        assert not list(tmp_path.iterdir())

    def test_agents_md_target_writes_agents_md(self, tmp_path: Path) -> None:
        """The agents-md target writes AGENTS.md at the project root."""
        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("agents-md",), None
        )
        content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
        assert content.startswith("# my-proj — Agent Context\n")
        assert "\r" not in content

    def test_aider_target_writes_conventions_and_conf(self, tmp_path: Path) -> None:
        """The aider target writes CONVENTIONS.md plus .aider.conf.yml."""
        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("aider",), None
        )
        conventions = (tmp_path / "CONVENTIONS.md").read_text(encoding="utf-8")
        assert conventions.startswith("# my-proj — Coding Conventions\n")
        conf = yaml.safe_load(
            (tmp_path / ".aider.conf.yml").read_text(encoding="utf-8")
        )
        assert conf == {"read": "CONVENTIONS.md"}

    def test_multiple_targets_in_one_run(self, tmp_path: Path) -> None:
        """claude + agents-md + aider in one run emits both extra formats."""
        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("claude", "agents-md", "aider"), None
        )
        assert (tmp_path / "AGENTS.md").is_file()
        assert (tmp_path / "CONVENTIONS.md").is_file()
        assert (tmp_path / ".aider.conf.yml").is_file()

    def test_existing_agents_md_preserved_additively(self, tmp_path: Path) -> None:
        """A pre-existing user AGENTS.md is preserved (additive init)."""
        existing = "# my own agents file\n"
        (tmp_path / "AGENTS.md").write_text(existing, encoding="utf-8")
        writer = FileWriter(project_root=tmp_path, console=MagicMock())

        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("agents-md",), writer
        )

        assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8") == existing
        assert writer.skipped == 1

    def test_file_writer_used_for_new_files(self, tmp_path: Path) -> None:
        """New files go through the FileWriter seam (LF-only writes)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock())
        cli._generate_agent_context_step(
            tmp_path, "my-proj", "python", ("aider",), writer
        )
        assert writer.created == 2


class TestPass2AgentTargetGating:
    """Test that Pass 2 emits Claude artifacts only for the claude target."""

    def test_default_target_runs_claude_steps(
        self, pass2_mocks: dict[str, MagicMock], tmp_path: Path
    ) -> None:
        """The default claude target runs CLAUDE.md + subagents steps."""
        cli._generate_pass2_polish(
            tmp_path,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None),
            None,
        )
        pass2_mocks["_generate_claude_md_step"].assert_called_once()
        pass2_mocks["_generate_subagents_step"].assert_called_once()
        pass2_mocks["_generate_agent_context_step"].assert_called_once()

    def test_non_claude_target_skips_claude_steps(
        self, pass2_mocks: dict[str, MagicMock], tmp_path: Path
    ) -> None:
        """agents-md without claude skips CLAUDE.md + subagents entirely."""
        cli._generate_pass2_polish(
            tmp_path,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None, agent_targets=("agents-md",)),
            None,
        )
        pass2_mocks["_generate_claude_md_step"].assert_not_called()
        pass2_mocks["_generate_subagents_step"].assert_not_called()
        pass2_mocks["_generate_agent_context_step"].assert_called_once()
        # Non-context steps still run regardless of target.
        pass2_mocks["_generate_ci_step"].assert_called_once()
        pass2_mocks["_generate_review_step"].assert_called_once()
        pass2_mocks["_generate_architecture_step"].assert_called_once()

    def test_agent_context_step_receives_targets(
        self, pass2_mocks: dict[str, MagicMock], tmp_path: Path
    ) -> None:
        """The emit step receives the resolved target tuple."""
        targets = ("claude", "aider")
        cli._generate_pass2_polish(
            tmp_path,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None, agent_targets=targets),
            None,
        )
        call_args = pass2_mocks["_generate_agent_context_step"].call_args
        assert (
            targets in call_args.args
            or call_args.kwargs.get("agent_targets") == targets
        )


class TestDefaultTargetByteIdentical:
    """Hard AC: the default target's output equals an explicit claude run."""

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        """Map every file under ``root`` (relative path) to its bytes."""
        return {
            str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    def test_default_equals_explicit_claude_byte_for_byte(self, tmp_path: Path) -> None:
        """Default-target Pass 2 output is byte-identical to --agent claude."""
        default_dir = tmp_path / "default"
        explicit_dir = tmp_path / "explicit"
        default_dir.mkdir()
        explicit_dir.mkdir()

        cli._generate_pass2_polish(
            default_dir,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None),
            None,
        )
        cli._generate_pass2_polish(
            explicit_dir,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None, agent_targets=("claude",)),
            None,
        )

        default_tree = self._tree_bytes(default_dir)
        assert default_tree == self._tree_bytes(explicit_dir)
        assert default_tree  # sanity: the offline path emitted files

    def test_default_target_emits_no_non_claude_files(self, tmp_path: Path) -> None:
        """The default target never adds AGENTS.md / aider files."""
        cli._generate_pass2_polish(
            tmp_path,
            "my-proj",
            "python",
            cli._Pass2Options(orchestrator=None),
            None,
        )
        assert not (tmp_path / "AGENTS.md").exists()
        assert not (tmp_path / "CONVENTIONS.md").exists()
        assert not (tmp_path / ".aider.conf.yml").exists()
        assert (tmp_path / "CLAUDE.md").is_file()
        assert (tmp_path / ".claude" / "agents").is_dir()


class TestDryRunPreviewAgentTargets:
    """Dry-run preview reflects the selected agent targets."""

    @patch(f"{_CLI_MODULE}.console")
    def test_default_preview_unchanged(
        self, mock_console: MagicMock, tmp_path: Path
    ) -> None:
        """The default preview still lists the Claude artifacts."""
        cli._show_dry_run_preview("p", "python", tmp_path)
        printed = "\n".join(
            str(c.args[0]) for c in mock_console.print.call_args_list if c.args
        )
        assert "CLAUDE.md (modular: index + .claude/docs/)" in printed
        assert "AGENTS.md" not in printed

    @patch(f"{_CLI_MODULE}.console")
    def test_non_claude_preview_lists_new_files(
        self, mock_console: MagicMock, tmp_path: Path
    ) -> None:
        """A non-claude selection previews its files, not Claude's."""
        cli._show_dry_run_preview(
            "p", "python", tmp_path, agent_targets=("agents-md", "aider")
        )
        printed = "\n".join(
            str(c.args[0]) for c in mock_console.print.call_args_list if c.args
        )
        assert "AGENTS.md" in printed
        assert "CONVENTIONS.md" in printed
        assert "CLAUDE.md" not in printed
