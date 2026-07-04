"""Tests for the Ralph fleet-loop generator (opt-in ``--with-ralph-loop``).

Mirrors ``test_cli_mocked.py``'s ``_copy_reference_skills``/
``_copy_reference_subagents`` tests: patch the module-level reference-dir
constants to point at throwaway fixtures so these tests never depend on
(or are broken by future edits to) the real ``reference/ralph/`` tree.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from start_green_stay_green.generators import ralph_loop
from start_green_stay_green.utils.file_writer import FileWriter

if TYPE_CHECKING:
    from pathlib import Path


def _write(path: Path, content: str = "content") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def fake_ralph_dir(tmp_path: Path) -> Path:
    """Build a minimal, valid ``reference/ralph/`` fixture tree."""
    root = tmp_path / "ref-ralph"
    _write(root / "agents" / "ralph-worker.md")
    _write(root / "commands" / "ralph-tick.md")
    _write(root / "scripts" / "fleet.sh")
    _write(root / "github" / "workflows" / "hopper.yml")
    _write(root / "prompts" / "scans" / "todo.md")
    _write(root / "github" / "deslop-areas.json", "[]")
    return root


@pytest.fixture
def fake_skills_dir(tmp_path: Path) -> Path:
    """Build a minimal ``reference/skills/`` fixture with the required skills."""
    root = tmp_path / "ref-skills"
    _write(root / "scan-issue-writer" / "SKILL.md")
    _write(root / "de-slopify" / "SKILL.md")
    _write(root / "discord-ralph-recap" / "SKILL.md")
    return root


@pytest.fixture(autouse=True)
def _patch_reference_dirs(
    monkeypatch: pytest.MonkeyPatch,
    fake_ralph_dir: Path,
    fake_skills_dir: Path,
) -> None:
    monkeypatch.setattr(ralph_loop, "REFERENCE_RALPH_DIR", fake_ralph_dir)
    monkeypatch.setattr(ralph_loop, "REFERENCE_SKILLS_DIR", fake_skills_dir)


class TestCopyRalphLoopNoWriter:
    """Direct-copy path (``file_writer=None``, mirrors dry-run/no-API mode)."""

    def test_copies_every_tree(self, tmp_path: Path) -> None:
        target = tmp_path / "project"
        ralph_loop.copy_ralph_loop(target)

        assert (target / ".claude" / "agents" / "ralph-worker.md").is_file()
        assert (target / ".claude" / "commands" / "ralph-tick.md").is_file()
        assert (target / "scripts" / "ralph" / "fleet.sh").is_file()
        assert (target / ".github" / "workflows" / "hopper.yml").is_file()
        assert (target / "prompts" / "scans" / "todo.md").is_file()

    def test_copies_the_single_file(self, tmp_path: Path) -> None:
        target = tmp_path / "project"
        ralph_loop.copy_ralph_loop(target)

        deslop_areas = target / ".github" / "deslop-areas.json"
        assert deslop_areas.is_file()
        assert deslop_areas.read_text(encoding="utf-8") == "[]"

    def test_copies_required_skills(self, tmp_path: Path) -> None:
        target = tmp_path / "project"
        ralph_loop.copy_ralph_loop(target)

        assert (
            target / ".claude" / "skills" / "scan-issue-writer" / "SKILL.md"
        ).is_file()
        assert (target / ".claude" / "skills" / "de-slopify" / "SKILL.md").is_file()
        assert (
            target / ".claude" / "skills" / "discord-ralph-recap" / "SKILL.md"
        ).is_file()

    def test_raises_when_a_tree_is_missing(
        self, tmp_path: Path, fake_ralph_dir: Path
    ) -> None:
        shutil.rmtree(fake_ralph_dir / "commands")
        with pytest.raises(FileNotFoundError, match="commands"):
            ralph_loop.copy_ralph_loop(tmp_path / "project")

    def test_raises_when_the_single_file_is_missing(
        self, tmp_path: Path, fake_ralph_dir: Path
    ) -> None:
        (fake_ralph_dir / "github" / "deslop-areas.json").unlink()
        with pytest.raises(FileNotFoundError, match="deslop-areas"):
            ralph_loop.copy_ralph_loop(tmp_path / "project")

    def test_raises_when_a_required_skill_is_missing(
        self, tmp_path: Path, fake_skills_dir: Path
    ) -> None:
        shutil.rmtree(fake_skills_dir / "de-slopify")
        with pytest.raises(FileNotFoundError, match="de-slopify"):
            ralph_loop.copy_ralph_loop(tmp_path / "project")


class TestCopyRalphLoopWithFileWriter:
    """FileWriter path (real ``green init`` behavior: additive, conflict-safe)."""

    def test_uses_file_writer_for_trees_and_files(self, tmp_path: Path) -> None:
        target = tmp_path / "project"
        writer = FileWriter(project_root=target)

        ralph_loop.copy_ralph_loop(target, file_writer=writer)

        assert (target / ".claude" / "commands" / "ralph-tick.md").is_file()
        assert (target / ".github" / "deslop-areas.json").is_file()
        assert writer.created > 0

    def test_refuses_to_silently_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Matches distribute-skills' own overwrite-refusal contract."""
        target = tmp_path / "project"
        existing = target / ".claude" / "commands" / "ralph-tick.md"
        _write(existing, "user's own content")

        writer = FileWriter(project_root=target)
        ralph_loop.copy_ralph_loop(target, file_writer=writer)

        # FileWriter's default (non-force) mode must not clobber user content.
        assert existing.read_text(encoding="utf-8") == "user's own content"

    def test_dispatches_via_copy_tree_and_write_file(self, tmp_path: Path) -> None:
        """Confirms the FileWriter API surface used, not just end state."""
        target = tmp_path / "project"
        writer = Mock(spec=FileWriter)

        ralph_loop.copy_ralph_loop(target, file_writer=writer)

        assert writer.copy_tree.call_count == len(ralph_loop.RALPH_LOOP_TREES) + len(
            ralph_loop.RALPH_LOOP_SKILLS
        )
        assert writer.write_file.call_count == len(ralph_loop.RALPH_LOOP_FILES)
