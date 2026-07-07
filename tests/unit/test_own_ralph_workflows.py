"""Content tests for THIS repo's own live ``.github/workflows/`` Ralph scans.

Companion to ``tests/unit/reference/test_ralph_loop_content.py``, which
covers the generic ``reference/ralph/`` template consumed by downstream
``--with-ralph-loop`` projects. This file covers SGSG's own adopted copy
under ``.github/workflows/`` -- confirmed byte-identical to the pre-fix
template for these exact files, so it carried the identical bugs and needs
the identical regression coverage, independently of the template.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


class TestOwnScanWorkflowPermissions:
    """Every live scan-*.yml wrapper must grant what _claude-scan.yml needs.

    Reusable-workflow (``workflow_call``) permissions are a CEILING the
    caller must explicitly grant -- a caller with no ``permissions:`` block
    gets the org/repo default (usually read-only, no OIDC token), silently
    dropping the callee's own requested ``issues: write`` /
    ``id-token: write``. Every dispatched scan then fails GitHub's
    validation step with ``startup_failure`` and no job logs. This repo's
    own scan-*.yml files were confirmed byte-identical to the pre-fix
    reference template (11 of 12 missing this block).
    """

    def test_claude_scan_core_requires_issues_and_id_token(self) -> None:
        """Pin down what the callee needs, so the assertion below stays honest."""
        core = yaml.safe_load(
            (WORKFLOWS_DIR / "_claude-scan.yml").read_text(encoding="utf-8")
        )
        core_permissions = core["permissions"]
        assert core_permissions["issues"] == "write"
        assert core_permissions["id-token"] == "write"

    def test_every_scan_wrapper_grants_required_permissions(self) -> None:
        """Every live scan-*.yml wrapper declares issues:write + id-token:write."""
        wrappers = sorted(WORKFLOWS_DIR.glob("scan-*.yml"))
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


class TestOwnHopperQueueDepth:
    """hopper.yml's queue-depth measurement must match pick-next.sh's eligibility.

    scripts/ralph/pick-next.sh's RALPH_REQUIRE_LABELS defaults to empty
    (agent-ready is NOT required by default) -- filtering hopper's
    queue-depth count on ``--label agent-ready`` alone undercounts to zero
    on a perfectly pickable, unlabeled backlog, so hopper can never stand
    down and keeps dispatching scans forever.
    """

    def test_hopper_does_not_filter_on_agent_ready_alone(self) -> None:
        """The old, too-narrow single-label filter must be gone."""
        content = (WORKFLOWS_DIR / "hopper.yml").read_text(encoding="utf-8")
        assert "gh issue list --label agent-ready" not in content
        assert "--json number,labels" in content

    def test_hopper_exclude_labels_default_matches_pick_next(self) -> None:
        """hopper's default exclude list is byte-identical to pick-next.sh's.

        Note: SGSG's own scripts/ralph/pick-next.sh omits a bare "epic"
        from its default exclude list (unlike the generic template),
        since SGSG excludes epics by TITLE prefix instead -- an
        epic:<name> label is applied to BOTH the umbrella issue and its
        children, so the label alone can't distinguish them.
        """
        hopper_content = (WORKFLOWS_DIR / "hopper.yml").read_text(encoding="utf-8")
        pick_next_path = REPO_ROOT / "scripts" / "ralph" / "pick-next.sh"
        pick_next_content = pick_next_path.read_text(encoding="utf-8")

        exclude_line = next(
            line
            for line in pick_next_content.splitlines()
            if line.strip().startswith("EXCLUDE_LABELS=")
        )
        default_excludes = (
            "wontfix duplicate invalid question blocked "
            "needs-spec future-work do-not-auto-merge in-progress"
        )
        assert default_excludes in exclude_line
        assert "epic " not in exclude_line
        assert not exclude_line.strip().endswith("epic")

        collapsed = " ".join(hopper_content.split())
        assert default_excludes in collapsed
