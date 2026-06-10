"""Unit tests for the Phase 5b batch dispatch orchestration.

These tests exercise the submit / resume orchestration in
``ai/batch_dispatch.py`` against mocked
:class:`AIOrchestrator` and :class:`SubagentsGenerator` doubles —
no network, no filesystem (apart from ``tmp_path``). Real CLI
plumbing (typer flags, console rendering) is covered separately in
``tests/test_cli_mocked.py``.
"""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from start_green_stay_green.ai.batch import BatchError
from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.batch_dispatch import BATCH_TARGET_SUBAGENTS
from start_green_stay_green.ai.batch_dispatch import BatchPersistenceContext
from start_green_stay_green.ai.batch_dispatch import BatchSubmitOutcome
from start_green_stay_green.ai.batch_dispatch import BatchWaitConfig
from start_green_stay_green.ai.batch_dispatch import ResumeStatus
from start_green_stay_green.ai.batch_dispatch import _write_one_agent
from start_green_stay_green.ai.batch_dispatch import resume_subagent_batch
from start_green_stay_green.ai.batch_dispatch import submit_subagent_batch
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.generators.subagents import SubagentBatchEntry
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.utils.enhance_state import BatchProgress
from start_green_stay_green.utils.enhance_state import EnhanceState
from start_green_stay_green.utils.enhance_state import load_state

if TYPE_CHECKING:
    from pathlib import Path


def _recent_submitted_at() -> str:
    """Return a non-expired ISO-8601 UTC timestamp for batch fixtures.

    Hard-coding ``2026-05-09T21:00:00+00:00`` was a time-bomb: as soon
    as wall-clock crossed the 24 h SLA window relative to it,
    :meth:`BatchProgress.is_potentially_expired` flipped to ``True``
    and tests that exercise the live batch path started flapping into
    the EXPIRED branch unintentionally. Re-anchoring on
    :func:`datetime.now` per-test makes the expiry guard test only
    when explicitly asserted (via ``patch.object`` of
    ``is_potentially_expired`` itself). The one-hour future anchor
    removes even the theoretical race where test wall time eats into
    the SLA window.
    """
    return (datetime.now(UTC) + timedelta(hours=1)).isoformat()


def _entry(agent_name: str, custom_id: str | None = None) -> SubagentBatchEntry:
    """Tiny factory — keeps each test's setup short and readable."""
    return SubagentBatchEntry(
        agent_name=agent_name,
        custom_id=custom_id or f"subagent:{agent_name}",
        frontmatter=f"---\nname: {agent_name}\n---",
        request=ToolUseBatchRequest(
            custom_id=custom_id or f"subagent:{agent_name}",
            prompt="body",
            system_blocks=[{"type": "text", "text": "S"}],
            tool_schema={"name": "report_tuning", "input_schema": {}},
        ),
    )


def _success(_agent_name: str, content: str = "tuned body") -> ToolUseResult:
    """SDK-shaped tool-use payload for one successful agent tune.

    ``_agent_name`` is unused at the moment but kept on the signature
    so call sites read like the production code (``_success("alpha")``)
    rather than positional ``content``-only — easier to update if the
    factory grows agent-specific fields later.
    """
    return ToolUseResult(
        tool_name="report_tuning",
        tool_input={"tuned_content": content, "changes": ["adapted"]},
        token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        model="claude",
        message_id="msg_abc",
    )


def _fake_generator() -> MagicMock:
    """A ``SubagentsGenerator`` double with the methods the dispatch needs."""
    gen = MagicMock(spec=SubagentsGenerator)
    gen.build_batch_plan.return_value = [
        _entry("alpha"),
        _entry("beta"),
    ]
    # The dispatch re-reads frontmatter at fetch time via the
    # private helpers (see ``_frontmatter_for``).
    # Phase 5b post-feedback: dispatch reads frontmatter through the
    # public ``get_agent_frontmatter`` (no more SLF001 suppressions).
    gen.get_agent_frontmatter.side_effect = lambda name: f"---\nname: {name}\n---"
    return gen


class TestSubmitSubagentBatch:
    """Submit path: build plan → submit → persist state."""

    @pytest.mark.asyncio
    async def test_submits_one_request_per_planned_agent(self, tmp_path: Path) -> None:
        orchestrator = MagicMock()
        orchestrator.submit_tool_use_batch = AsyncMock(
            return_value=BatchSubmission(
                batch_id="msgbatch_42",
                custom_ids=["subagent:alpha", "subagent:beta"],
                submitted_at="2026-05-09T22:00:00+00:00",
            )
        )
        generator = _fake_generator()
        state = EnhanceState()

        outcome = await submit_subagent_batch(
            orchestrator=orchestrator,
            generator=generator,
            target_context="Test project",
            state=state,
            project_path=tmp_path,
        )

        assert isinstance(outcome, BatchSubmitOutcome)
        assert outcome.agent_count == 2
        assert outcome.submission.batch_id == "msgbatch_42"
        # The orchestrator received the entry's request payload, in order.
        sent = orchestrator.submit_tool_use_batch.await_args.args[0]
        assert [r.custom_id for r in sent] == [
            "subagent:alpha",
            "subagent:beta",
        ]

    @pytest.mark.asyncio
    async def test_persists_state_with_custom_id_map_pointing_at_subagents(
        self, tmp_path: Path
    ) -> None:
        """Phase 5a contract: ``custom_id_map[custom_id] == "subagents"``."""
        orchestrator = MagicMock()
        orchestrator.submit_tool_use_batch = AsyncMock(
            return_value=BatchSubmission(
                batch_id="msgbatch_42",
                custom_ids=["subagent:alpha", "subagent:beta"],
                submitted_at="2026-05-09T22:00:00+00:00",
            )
        )
        state = EnhanceState()

        await submit_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            target_context="Test project",
            state=state,
            project_path=tmp_path,
        )

        assert state.has_batch()
        assert state.batch is not None
        assert state.batch.batch_id == "msgbatch_42"
        assert state.batch.custom_id_map == {
            "subagent:alpha": BATCH_TARGET_SUBAGENTS,
            "subagent:beta": BATCH_TARGET_SUBAGENTS,
        }

        # The state file was actually written so a re-run can resume.
        on_disk = load_state(tmp_path)
        assert on_disk.has_batch()
        assert on_disk.batch is not None
        assert on_disk.batch.batch_id == "msgbatch_42"


class TestResumeSubagentBatchNoOp:
    """Resume path: degenerate cases — no batch, expired batch."""

    @pytest.mark.asyncio
    async def test_returns_no_batch_when_state_is_empty(self, tmp_path: Path) -> None:
        orchestrator = MagicMock()
        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=EnhanceState(),
                project_path=tmp_path,
            ),
        )
        assert outcome.status == ResumeStatus.NO_BATCH
        # Did NOT call the SDK — no in-flight batch to poll.
        assert not orchestrator.method_calls

    @pytest.mark.asyncio
    async def test_clears_expired_batch_and_persists(self, tmp_path: Path) -> None:
        """A 25 h-old batch is cleared without touching the API."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_old",
            submitted_at="2026-05-08T00:00:00+00:00",  # ~24 h ago
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )

        # Force ``is_potentially_expired`` to return True by patching
        # the BatchProgress instance method.
        with patch.object(BatchProgress, "is_potentially_expired", return_value=True):
            orchestrator = MagicMock()
            outcome = await resume_subagent_batch(
                orchestrator=orchestrator,
                generator=_fake_generator(),
                persistence=BatchPersistenceContext(
                    state=state,
                    project_path=tmp_path,
                ),
            )

        assert outcome.status == ResumeStatus.EXPIRED
        assert state.batch is None  # cleared
        assert not load_state(tmp_path).has_batch()
        # No SDK calls — expiry check beats the poll.
        assert not orchestrator.method_calls


class TestResumeSubagentBatchInProgress:
    """Resume path: batch still running."""

    @pytest.mark.asyncio
    async def test_returns_in_progress_without_fetching(self, tmp_path: Path) -> None:
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="in_progress",
                processing_count=1,
                succeeded_count=0,
                errored_count=0,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock()

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.status == ResumeStatus.IN_PROGRESS
        assert outcome.poll is not None
        assert outcome.poll.processing_count == 1
        # Did NOT fetch — fetch only fires on ``ended``.
        orchestrator.fetch_batch_results.assert_not_awaited()
        # State retains the in-flight batch so a later run can resume.
        assert state.has_batch()


class TestResumeSubagentBatchEnded:
    """Resume path: batch ``ended`` → fetch + write + clear."""

    @pytest.mark.asyncio
    async def test_writes_per_agent_files_and_clears_state(
        self, tmp_path: Path
    ) -> None:
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
                "subagent:beta": BATCH_TARGET_SUBAGENTS,
            },
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="ended",
                processing_count=0,
                succeeded_count=2,
                errored_count=0,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={
                    "subagent:alpha": _success("alpha", "alpha tuned"),
                    "subagent:beta": _success("beta", "beta tuned"),
                },
                failures={},
            )
        )

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.status == ResumeStatus.ENDED
        assert outcome.succeeded_agents == ("alpha", "beta")
        assert not outcome.failed_agents
        # Files written.
        agents_dir = tmp_path / ".claude" / "agents"
        assert (agents_dir / "alpha.md").read_text(encoding="utf-8")
        assert "alpha tuned" in (agents_dir / "alpha.md").read_text(encoding="utf-8")
        # Batch cleared from state and from disk.
        assert not state.has_batch()
        assert not load_state(tmp_path).has_batch()

    @pytest.mark.asyncio
    async def test_partitions_failures_separately(self, tmp_path: Path) -> None:
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
                "subagent:beta": BATCH_TARGET_SUBAGENTS,
            },
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="ended",
                processing_count=0,
                succeeded_count=1,
                errored_count=1,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={"subagent:alpha": _success("alpha")},
                failures={
                    "subagent:beta": BatchError(
                        custom_id="subagent:beta",
                        result_type="errored",
                        message="upstream",
                    )
                },
            )
        )

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.succeeded_agents == ("alpha",)
        assert outcome.failed_agents == ("beta",)
        # Only the succeeded agent's file is written.
        agents_dir = tmp_path / ".claude" / "agents"
        assert (agents_dir / "alpha.md").exists()
        assert not (agents_dir / "beta.md").exists()


class TestResumeSubagentBatchWaitMode:
    """Resume path: ``--wait`` polls in-process until ended or timeout."""

    @pytest.mark.asyncio
    async def test_wait_polls_until_ended(self, tmp_path: Path) -> None:
        """Two ``in_progress`` polls then ``ended`` → fetch fires."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            side_effect=[
                BatchPoll(
                    batch_id="msgbatch_42",
                    status="in_progress",
                    processing_count=1,
                    succeeded_count=0,
                    errored_count=0,
                ),
                BatchPoll(
                    batch_id="msgbatch_42",
                    status="in_progress",
                    processing_count=1,
                    succeeded_count=0,
                    errored_count=0,
                ),
                BatchPoll(
                    batch_id="msgbatch_42",
                    status="ended",
                    processing_count=0,
                    succeeded_count=1,
                    errored_count=0,
                ),
            ]
        )
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={"subagent:alpha": _success("alpha")},
                failures={},
            )
        )

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
            wait_config=BatchWaitConfig(
                wait=True,
                poll_interval=0.0,  # tight loop for test speed
                wait_timeout_seconds=10.0,
            ),
        )

        assert outcome.status == ResumeStatus.ENDED
        # Three polls (two in-progress + one ended), one fetch.
        assert orchestrator.poll_batch.await_count == 3
        orchestrator.fetch_batch_results.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_wait_times_out_when_batch_never_ends(self, tmp_path: Path) -> None:
        """Wait deadline exceeded → ``TIMED_OUT`` without fetching."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="in_progress",
                processing_count=1,
                succeeded_count=0,
                errored_count=0,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock()

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
            wait_config=BatchWaitConfig(
                wait=True,
                poll_interval=0.0,
                wait_timeout_seconds=-1.0,  # already past → exit after one poll
            ),
        )

        assert outcome.status == ResumeStatus.TIMED_OUT
        orchestrator.fetch_batch_results.assert_not_awaited()
        # State retains the in-flight batch so a future run can resume.
        assert state.has_batch()


class TestResumeSubagentBatchErrorPropagation:
    """Resume path: SDK errors mid-wait must preserve in-flight state."""

    @pytest.mark.asyncio
    async def test_poll_raises_mid_wait_loop_preserves_state(
        self, tmp_path: Path
    ) -> None:
        """Round-2 review observation: an SDK error mid-wait must NOT
        clear the in-flight batch — a re-run needs the ``batch_id``.

        Pins the contract that ``state.clear_batch`` only fires after
        a successful ``ENDED`` reconciliation, never before.
        """
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        # First poll succeeds (in-progress); second raises.
        orchestrator.poll_batch = AsyncMock(
            side_effect=[
                BatchPoll(
                    batch_id="msgbatch_42",
                    status="in_progress",
                    processing_count=1,
                    succeeded_count=0,
                    errored_count=0,
                ),
                GenerationError("simulated rate-limit during poll"),
            ]
        )
        orchestrator.fetch_batch_results = AsyncMock()

        with pytest.raises(GenerationError, match="rate-limit"):
            await resume_subagent_batch(
                orchestrator=orchestrator,
                generator=_fake_generator(),
                persistence=BatchPersistenceContext(
                    state=state,
                    project_path=tmp_path,
                ),
                wait_config=BatchWaitConfig(
                    wait=True,
                    poll_interval=0.0,
                    wait_timeout_seconds=10.0,
                ),
            )

        # Critical: in-memory in-flight record survives so a future
        # call (after the user fixes their API issue and re-runs) can
        # resume. We do NOT assert on-disk state here — the contract
        # is that ``save_state`` only fires on a *successful* status
        # transition (EXPIRED clear, or ENDED reconciliation), so the
        # raised path leaves the disk untouched. That's the desired
        # behaviour: the original submit path's persisted state is
        # still on disk from when the batch was first submitted.
        assert state.has_batch()
        assert state.batch is not None
        assert state.batch.batch_id == "msgbatch_42"
        # Did NOT fetch — the second poll never returned ``ended``.
        orchestrator.fetch_batch_results.assert_not_awaited()


class TestResumeSubagentBatchPartialFailureIsolation:
    """Round-3 review: per-agent isolation for local write failures.

    The PR documents per-agent failure isolation in the README. The
    round-3 reviewer flagged two paths where that contract leaked:
    a missing source file would abort the whole loop, and an
    unresolvable ``custom_id`` would silently vanish from both
    ``succeeded`` and ``failed_agents``. Both now route through the
    ``locally_failed`` partition.
    """

    @pytest.mark.asyncio
    async def test_missing_source_file_does_not_abort_other_agents(
        self, tmp_path: Path
    ) -> None:
        """Source file deleted between submit and fetch → only that
        agent fails; siblings still land on disk."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
                "subagent:beta": BATCH_TARGET_SUBAGENTS,
            },
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="ended",
                processing_count=0,
                succeeded_count=2,
                errored_count=0,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={
                    "subagent:alpha": _success("alpha"),
                    "subagent:beta": _success("beta"),
                },
                failures={},
            )
        )
        # Simulate beta's source file having been deleted between
        # submit and fetch by making get_agent_frontmatter raise.
        gen = _fake_generator()

        def selective_frontmatter(name: str) -> str:
            if name == "beta":
                msg = "source file vanished between submit and fetch"
                raise FileNotFoundError(msg)
            return f"---\nname: {name}\n---"

        gen.get_agent_frontmatter.side_effect = selective_frontmatter

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=gen,
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.status == ResumeStatus.ENDED
        # Alpha landed; beta is in failed_agents — isolation held.
        assert outcome.succeeded_agents == ("alpha",)
        assert outcome.failed_agents == ("beta",)
        agents_dir = tmp_path / ".claude" / "agents"
        assert (agents_dir / "alpha.md").exists()
        assert not (agents_dir / "beta.md").exists()

    @pytest.mark.asyncio
    async def test_unresolved_custom_id_surfaces_in_failed_agents(
        self, tmp_path: Path
    ) -> None:
        """A custom_id with no known schema lands in ``failed_agents``
        with an ``unresolved:`` prefix — never silently dropped."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            # Recorded mapping covers only alpha; the rogue custom_id
            # below isn't in the map and uses a schema we don't know.
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock(
            return_value=BatchPoll(
                batch_id="msgbatch_42",
                status="ended",
                processing_count=0,
                succeeded_count=2,
                errored_count=0,
            )
        )
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={
                    "subagent:alpha": _success("alpha"),
                    "rogue:unknown-shape": _success("rogue"),
                },
                failures={},
            )
        )

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.status == ResumeStatus.ENDED
        assert outcome.succeeded_agents == ("alpha",)
        # The rogue custom_id is surfaced rather than silently
        # dropped — synthetic prefix flags the schema-drift bug.
        assert outcome.failed_agents == ("unresolved:rogue:unknown-shape",)


class TestWriteOneAgentPathContainment:
    """Defense-in-depth: ``_write_one_agent`` rejects path-traversal names (#317)."""

    def test_rejects_dotdot_traversal_outside_target_dir(self, tmp_path: Path) -> None:
        """An ``agent_name`` containing ``..`` separators must raise rather
        than write outside ``target_dir``. The guard is defense-in-depth:
        today the name comes from a code-defined ``REQUIRED_AGENTS`` map,
        but a future phase widening the input to user-supplied custom IDs
        (e.g. ``skill:<name>``) could otherwise allow filesystem escape.
        See issue #317.
        """
        target_dir = tmp_path / "agents"
        target_dir.mkdir()
        sentinel = tmp_path / "escape.md"
        assert not sentinel.exists()

        with pytest.raises(ValueError, match="escapes target dir"):
            _write_one_agent(
                generator=_fake_generator(),
                agent_name="../escape",
                tool_result=_success("..."),
                target_dir=target_dir,
                file_writer=None,
            )
        # The guard is the only thing standing between the malicious
        # name and the filesystem, so prove the file was not written.
        assert not sentinel.exists()

    def test_accepts_normal_agent_name(self, tmp_path: Path) -> None:
        """Sanity check: a plain alphanumeric agent name still writes
        through the guard without raising."""
        target_dir = tmp_path / "agents"
        target_dir.mkdir()

        _write_one_agent(
            generator=_fake_generator(),
            agent_name="implementation-engineer",
            tool_result=_success("body"),
            target_dir=target_dir,
            file_writer=None,
        )

        assert (target_dir / "implementation-engineer.md").exists()
