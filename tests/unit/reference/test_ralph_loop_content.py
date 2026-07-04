"""Content tests for the ``reference/ralph/`` Ralph fleet-loop tree.

Mirrors ``test_skills_content.py``: every file the ``ralph_loop`` generator's
manifest declares must exist and be non-empty, and the renamed ``ralph-*``
specialist agents must be internally consistent (no stray references to the
pre-rename bare names that would collide with this repo's own, unrelated
agents of the same names).
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest

from start_green_stay_green.generators.ralph_loop import RALPH_LOOP_FILES
from start_green_stay_green.generators.ralph_loop import RALPH_LOOP_SKILLS
from start_green_stay_green.generators.ralph_loop import RALPH_LOOP_TREES

# The bare specialist names every ralph-* agent file was renamed from. A
# stray occurrence in the renamed tree means a cross-reference was missed
# and would collide with this repo's own unrelated agents of these names.
_BARE_SPECIALIST_NAMES = (
    "chief-architect",
    "code-review-orchestrator",
    "dependency-review-specialist",
    "documentation-specialist",
    "implementation-specialist",
    "performance-specialist",
    "security-specialist",
    "test-specialist",
)
_BARE_NAME_ALTERNATION = "|".join(re.escape(n) for n in _BARE_SPECIALIST_NAMES)
_BARE_NAME_RE = re.compile(r"(?<![\w-])(" + _BARE_NAME_ALTERNATION + r")(?![\w-])")


@pytest.fixture
def ralph_dir() -> Path:
    """Return the path to ``reference/ralph/``."""
    return Path(__file__).parent.parent.parent.parent / "reference" / "ralph"


@pytest.fixture
def skills_dir() -> Path:
    """Return the path to ``reference/skills/``."""
    return Path(__file__).parent.parent.parent.parent / "reference" / "skills"


class TestRalphLoopTreesExist:
    """Every tree the generator's manifest declares exists and is populated."""

    def test_every_tree_exists_and_non_empty(self, ralph_dir: Path) -> None:
        """Each ``RALPH_LOOP_TREES`` source subtree exists with >=1 file."""
        for subtree, _target in RALPH_LOOP_TREES:
            source_dir = ralph_dir / subtree
            assert source_dir.is_dir(), f"Missing reference/ralph/{subtree}"
            files = [p for p in source_dir.rglob("*") if p.is_file()]
            assert files, f"reference/ralph/{subtree} has no files"

    def test_every_file_exists_and_non_empty(self, ralph_dir: Path) -> None:
        """Each ``RALPH_LOOP_FILES`` source file exists and is non-empty."""
        for source_rel, _target_rel in RALPH_LOOP_FILES:
            source_file = ralph_dir / source_rel
            assert source_file.is_file(), f"Missing reference/ralph/{source_rel}"
            assert source_file.stat().st_size > 0, f"Empty reference/ralph/{source_rel}"

    def test_required_skills_exist(self, skills_dir: Path) -> None:
        """Each ``RALPH_LOOP_SKILLS`` directory exists under reference/skills/."""
        for skill_name in RALPH_LOOP_SKILLS:
            skill_dir = skills_dir / skill_name
            assert skill_dir.is_dir(), f"Missing reference/skills/{skill_name}"
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.is_file(), f"Missing SKILL.md in {skill_name}"
            assert skill_file.stat().st_size > 0, f"Empty SKILL.md in {skill_name}"


class TestRalphAgentRename:
    """The ralph-* renamed specialist taxonomy has no stray bare references."""

    def test_agents_directory_has_no_stray_bare_names(self, ralph_dir: Path) -> None:
        """No ``.md`` under reference/ralph/agents/ references a bare name."""
        agents_dir = ralph_dir / "agents"
        assert agents_dir.is_dir()
        offenders = []
        for path in sorted(agents_dir.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in _BARE_NAME_RE.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                offenders.append(f"{path.name}:{line_no}: {match.group(0)}")
        assert not offenders, "stray bare specialist name(s):\n" + "\n".join(offenders)

    def test_commands_and_scripts_have_no_stray_bare_names(
        self, ralph_dir: Path
    ) -> None:
        """ralph-tick.md and PROMPT.md reference only the renamed agents."""
        candidates = [
            ralph_dir / "commands" / "ralph-tick.md",
            ralph_dir / "scripts" / "PROMPT.md",
        ]
        offenders = []
        for path in candidates:
            assert path.is_file(), f"missing {path}"
            text = path.read_text(encoding="utf-8")
            for match in _BARE_NAME_RE.finditer(text):
                line_no = text[: match.start()].count("\n") + 1
                offenders.append(f"{path.name}:{line_no}: {match.group(0)}")
        assert not offenders, "stray bare specialist name(s):\n" + "\n".join(offenders)

    def test_ralph_worker_delegates_to_renamed_specialists(
        self, ralph_dir: Path
    ) -> None:
        """ralph-worker.md's frontmatter names only ralph-* specialists."""
        content = (ralph_dir / "agents" / "ralph-worker.md").read_text(encoding="utf-8")
        for name in _BARE_SPECIALIST_NAMES:
            assert f"ralph-{name}" in content, f"ralph-worker.md missing ralph-{name}"
