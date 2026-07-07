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
import yaml

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


class TestScanWorkflowPermissions:
    """Every scan-*.yml wrapper must grant what _claude-scan.yml needs.

    Reusable-workflow (``workflow_call``) permissions are a CEILING the
    CALLER must explicitly grant -- a caller with no ``permissions:`` block
    gets the org/repo default (usually read-only, no OIDC token), silently
    dropping the callee's own requested ``issues: write`` /
    ``id-token: write``. Every dispatched scan then fails GitHub's
    validation step with ``startup_failure`` and no job logs. Regression
    guard for that (11 of 13 wrappers were missing this block).
    """

    def test_claude_scan_core_requires_issues_and_id_token(
        self, ralph_dir: Path
    ) -> None:
        """Pin down what the callee actually needs, so the assertion below
        stays honest if _claude-scan.yml's own requirements ever change.
        """
        core = yaml.safe_load(
            (ralph_dir / "github" / "workflows" / "_claude-scan.yml").read_text(
                encoding="utf-8"
            )
        )
        core_permissions = core["permissions"]
        assert core_permissions["issues"] == "write"
        assert core_permissions["id-token"] == "write"

    def test_every_scan_wrapper_grants_required_permissions(
        self, ralph_dir: Path
    ) -> None:
        """Every scan-*.yml wrapper declares issues: write + id-token: write."""
        workflows_dir = ralph_dir / "github" / "workflows"
        wrappers = sorted(workflows_dir.glob("scan-*.yml"))
        assert wrappers, "no scan-*.yml wrappers found"

        missing = []
        for path in wrappers:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            permissions = data.get("permissions") or {}
            if permissions.get("issues") != "write" or (
                permissions.get("id-token") != "write"
            ):
                missing.append(path.name)
        assert not missing, (
            "scan wrapper(s) missing issues:write / id-token:write "
            f"permissions: {missing}"
        )


class TestScanWorkflowLayoutDetection:
    """_claude-scan.yml / deslop.yml must not assume a fixed monorepo layout.

    `green init` generates a FLAT, single-language project -- no
    `backend/`/`frontend/` subdirs, no `.nvmrc`. Both workflows are shared
    generic templates, so their install steps must detect what's actually
    present rather than unconditionally reaching for paths that only exist
    in a backend+frontend monorepo (which is what silently broke hedgekit's
    bootstrap).
    """

    def test_claude_scan_core_installs_are_conditional(self, ralph_dir: Path) -> None:
        """The Python/Node install steps are gated by a layout-detection step."""
        content = (
            ralph_dir / "github" / "workflows" / "_claude-scan.yml"
        ).read_text(encoding="utf-8")
        assert "steps.layout.outputs.python" in content
        assert "steps.layout.outputs.node" in content
        # The old unconditional monorepo-subdir paths must be gone.
        assert "backend/requirements.txt" not in content
        assert "frontend/.nvmrc" not in content

    def test_deslop_installs_do_not_hardcode_monorepo_subdirs(
        self, ralph_dir: Path
    ) -> None:
        """deslop.yml's stack-gated installs fall back to the repo root."""
        content = (ralph_dir / "github" / "workflows" / "deslop.yml").read_text(
            encoding="utf-8"
        )
        assert "frontend/.nvmrc" not in content
        # Still stack-gated (that part of the contract is correct)...
        assert "if: matrix.area.stack == 'backend'" in content
        assert "if: matrix.area.stack == 'frontend'" in content
        # ...but the paths themselves must be detected, not hardcoded.
        assert 'reqs_dir="."' in content
        assert 'pkg_dir="."' in content


class TestHopperQueueDepth:
    """hopper.yml's queue-depth measurement must match pick-next.sh's eligibility.

    pick-next.sh's RALPH_REQUIRE_LABELS defaults to empty (agent-ready is
    NOT required by default) -- filtering hopper's queue-depth count on
    ``--label agent-ready`` alone undercounts to zero on a perfectly
    pickable, unlabeled backlog, so hopper can never stand down and keeps
    dispatching scans forever.
    """

    def test_hopper_does_not_filter_on_agent_ready_alone(
        self, ralph_dir: Path
    ) -> None:
        """The old, too-narrow single-label filter must be gone."""
        content = (ralph_dir / "github" / "workflows" / "hopper.yml").read_text(
            encoding="utf-8"
        )
        assert "gh issue list --label agent-ready" not in content
        # The measurement now mirrors pick-next.sh's own require/exclude
        # jq filter (json labels, not a single --label flag).
        assert "--json number,labels" in content

    def test_hopper_exclude_labels_default_matches_pick_next(
        self, ralph_dir: Path
    ) -> None:
        """hopper's default exclude list is byte-identical to pick-next.sh's."""
        hopper_content = (
            ralph_dir / "github" / "workflows" / "hopper.yml"
        ).read_text(encoding="utf-8")
        pick_next_content = (ralph_dir / "scripts" / "pick-next.sh").read_text(
            encoding="utf-8"
        )
        default_excludes = (
            "epic wontfix duplicate invalid question blocked "
            "needs-spec future-work do-not-auto-merge in-progress"
        )
        assert default_excludes in pick_next_content
        # hopper.yml wraps the same string across a YAML folded scalar, so
        # compare with whitespace collapsed rather than requiring one line.
        collapsed = " ".join(hopper_content.split())
        assert default_excludes in collapsed
