"""Unit tests for the Phase 5b batch dispatch orchestration.

These tests exercise the submit / resume orchestration in
``ai/batch_dispatch.py`` against mocked
:class:`AIOrchestrator` and :class:`SubagentsGenerator` doubles —
no network, no filesystem (apart from ``tmp_path``). Real CLI
plumbing (typer flags, console rendering) is covered separately in
``tests/test_cli_mocked.py``.
"""

from __future__ import annotations

import dataclasses
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
from start_green_stay_green.ai.batch_dispatch import ResumeOutcome
from start_green_stay_green.ai.batch_dispatch import ResumeStatus
from start_green_stay_green.ai.batch_dispatch import _DEFAULT_POLL_INTERVAL_SECONDS
from start_green_stay_green.ai.batch_dispatch import _agent_name_from_custom_id
from start_green_stay_green.ai.batch_dispatch import _lookup_from_state
from start_green_stay_green.ai.batch_dispatch import _poll_until_terminal
from start_green_stay_green.ai.batch_dispatch import _write_one_agent
from start_green_stay_green.ai.batch_dispatch import _write_results
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


class TestModuleConstants:
    """Pin the exact literal values of module-level constants."""

    def test_batch_target_subagents_is_exact_string(self) -> None:
        """``BATCH_TARGET_SUBAGENTS`` is the literal ``"subagents"``."""
        assert BATCH_TARGET_SUBAGENTS == "subagents"

    def test_default_poll_interval_is_thirty_seconds(self) -> None:
        """Default poll interval is exactly ``30.0`` seconds."""
        assert _DEFAULT_POLL_INTERVAL_SECONDS == 30.0


class TestResumeStatusValues:
    """Pin the exact underlying string of every :class:`ResumeStatus`."""

    def test_no_batch_value(self) -> None:
        """``NO_BATCH`` serialises to ``"no-batch"``."""
        assert ResumeStatus.NO_BATCH.value == "no-batch"

    def test_expired_value(self) -> None:
        """``EXPIRED`` serialises to ``"expired"``."""
        assert ResumeStatus.EXPIRED.value == "expired"

    def test_in_progress_value(self) -> None:
        """``IN_PROGRESS`` serialises to ``"in-progress"``."""
        assert ResumeStatus.IN_PROGRESS.value == "in-progress"

    def test_ended_value(self) -> None:
        """``ENDED`` serialises to ``"ended"``."""
        assert ResumeStatus.ENDED.value == "ended"

    def test_timed_out_value(self) -> None:
        """``TIMED_OUT`` serialises to ``"timed-out"``."""
        assert ResumeStatus.TIMED_OUT.value == "timed-out"


def _set_attr(instance: object, field: str, value: object) -> None:
    """Assign through a runtime field name.

    Lets the frozen-dataclass tests exercise reassignment without a
    static read-only-property error (the attribute name is dynamic) or a
    constant-attribute ``setattr`` ruff finding.
    """
    setattr(instance, field, value)


class TestDataclassFrozenAndDefaults:
    """Pin ``frozen=True`` immutability and exact field defaults."""

    def test_submit_outcome_is_frozen(self) -> None:
        """``BatchSubmitOutcome`` rejects attribute reassignment."""
        outcome = BatchSubmitOutcome(submission=MagicMock(), agent_count=1)
        with pytest.raises(dataclasses.FrozenInstanceError, match="agent_count"):
            _set_attr(outcome, "agent_count", 2)

    def test_wait_config_is_frozen(self) -> None:
        """``BatchWaitConfig`` rejects attribute reassignment."""
        config = BatchWaitConfig()
        with pytest.raises(dataclasses.FrozenInstanceError, match="wait"):
            # Value is irrelevant: the frozen check fires before assignment.
            _set_attr(config, "wait", "ignored")

    def test_persistence_context_is_frozen(self, tmp_path: Path) -> None:
        """``BatchPersistenceContext`` rejects attribute reassignment."""
        ctx = BatchPersistenceContext(state=EnhanceState(), project_path=tmp_path)
        with pytest.raises(dataclasses.FrozenInstanceError, match="project_path"):
            _set_attr(ctx, "project_path", tmp_path)

    def test_resume_outcome_is_frozen(self) -> None:
        """``ResumeOutcome`` rejects attribute reassignment."""
        outcome = ResumeOutcome(status=ResumeStatus.NO_BATCH)
        with pytest.raises(dataclasses.FrozenInstanceError, match="status"):
            _set_attr(outcome, "status", ResumeStatus.ENDED)

    def test_wait_config_defaults_are_exact(self) -> None:
        """``BatchWaitConfig`` defaults: ``wait=False`` with exact numbers."""
        config = BatchWaitConfig()
        # ``is not None`` kills the ``wait = None`` default mutant; the
        # truthiness check pins the real ``False`` default.
        assert config.wait is not None
        assert not config.wait
        assert config.poll_interval == 30.0
        assert config.wait_timeout_seconds == 3600.0

    def test_persistence_context_file_writer_defaults_none(
        self, tmp_path: Path
    ) -> None:
        """``BatchPersistenceContext.file_writer`` defaults to ``None``."""
        ctx = BatchPersistenceContext(state=EnhanceState(), project_path=tmp_path)
        assert ctx.file_writer is None

    def test_resume_outcome_optional_defaults_are_exact(self) -> None:
        """``ResumeOutcome`` optional fields default to None / empty tuples."""
        outcome = ResumeOutcome(status=ResumeStatus.NO_BATCH)
        assert outcome.poll is None
        assert outcome.bundle is None
        assert not outcome.succeeded_agents
        assert not outcome.failed_agents
        assert isinstance(outcome.succeeded_agents, tuple)
        assert isinstance(outcome.failed_agents, tuple)


class TestCheckPrePollGuardComposition:
    """Pin the ``or`` short-circuit in the NO_BATCH pre-poll guard (#1145)."""

    @pytest.mark.asyncio
    async def test_empty_batch_id_returns_no_batch(self, tmp_path: Path) -> None:
        """A recorded batch with a blank id is treated as NO_BATCH."""
        state = EnhanceState()
        # ``has_batch()`` is False (blank id) but ``state.batch`` is not
        # None, so ``or`` returns NO_BATCH while ``and`` would fall
        # through to the poll path.
        state.batch = BatchProgress(
            batch_id="",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()
        orchestrator.poll_batch = AsyncMock()

        outcome = await resume_subagent_batch(
            orchestrator=orchestrator,
            generator=_fake_generator(),
            persistence=BatchPersistenceContext(
                state=state,
                project_path=tmp_path,
            ),
        )

        assert outcome.status == ResumeStatus.NO_BATCH
        orchestrator.poll_batch.assert_not_awaited()


class TestPollUntilTerminalDeadlineBoundary:
    """Pin the strict ``<`` deadline comparison in the wait loop (#1162)."""

    @pytest.mark.asyncio
    async def test_now_equal_to_deadline_stops_immediately(self) -> None:
        """When ``_now() == deadline`` the loop must NOT poll again."""
        orchestrator = MagicMock()
        in_progress = BatchPoll(
            batch_id="b",
            status="in_progress",
            processing_count=1,
            succeeded_count=0,
            errored_count=0,
        )
        orchestrator.poll_batch = AsyncMock(return_value=in_progress)
        # First ``_now()`` sets ``deadline = 100 + 0``; the loop guard
        # then reads ``_now() == 100``: strict ``<`` exits (one poll),
        # ``<=`` would enter the loop and poll a second time.
        with patch(
            "start_green_stay_green.ai.batch_dispatch._now",
            side_effect=[100.0, 100.0],
        ):
            poll = await _poll_until_terminal(
                orchestrator=orchestrator,
                batch_id="b",
                config=BatchWaitConfig(
                    wait=True,
                    poll_interval=0.0,
                    wait_timeout_seconds=0.0,
                ),
            )

        assert poll.status == "in_progress"
        orchestrator.poll_batch.assert_awaited_once()


class TestReconcileMissingBatchGuard:
    """Pin the RuntimeError message when reconcile runs with no batch (#1148/#1149)."""

    @pytest.mark.asyncio
    async def test_raises_with_exact_message(self, tmp_path: Path) -> None:
        """``_reconcile_ended_batch`` raises an exact RuntimeError message.

        Reaches the guard by clearing ``state.batch`` between the
        pre-poll check and reconciliation: ``poll_batch`` reports
        ``ended`` after the guard passed, but a patched ``clear_batch``
        no-op leaves a window where a racing reset surfaces the error.
        """
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={"subagent:alpha": BATCH_TARGET_SUBAGENTS},
        )
        orchestrator = MagicMock()

        async def poll_then_clear(_batch_id: str) -> BatchPoll:
            state.batch = None
            return BatchPoll(
                batch_id="msgbatch_42",
                status="ended",
                processing_count=0,
                succeeded_count=1,
                errored_count=0,
            )

        orchestrator.poll_batch = AsyncMock(side_effect=poll_then_clear)
        orchestrator.fetch_batch_results = AsyncMock()

        with pytest.raises(
            RuntimeError,
            match="_reconcile_ended_batch called without an in-flight batch",
        ) as exc:
            await resume_subagent_batch(
                orchestrator=orchestrator,
                generator=_fake_generator(),
                persistence=BatchPersistenceContext(
                    state=state,
                    project_path=tmp_path,
                ),
            )

        assert str(exc.value).startswith(
            "_reconcile_ended_batch called without an in-flight batch"
        )


class TestWriteResultsCreatesTargetDir:
    """Pin ``mkdir(exist_ok=True)`` so an existing dir does not raise (#1166)."""

    def test_existing_target_dir_does_not_raise(self, tmp_path: Path) -> None:
        """Writing into an already-present agents dir succeeds."""
        target_dir = tmp_path / ".claude" / "agents"
        target_dir.mkdir(parents=True)  # pre-create so exist_ok matters
        bundle = BatchResultsBundle(
            successes={"subagent:alpha": _success("alpha")},
            failures={},
        )

        succeeded, failed = _write_results(
            generator=_fake_generator(),
            bundle=bundle,
            plan_lookup={"subagent:alpha": "alpha"},
            target_dir=target_dir,
            file_writer=None,
        )

        assert succeeded == ["alpha"]
        assert not failed
        assert (target_dir / "alpha.md").exists()


class TestWriteOneAgentEscapeMessage:
    """Pin the exact two-line path-escape error message (#1184/#1185)."""

    def test_escape_message_names_agent_and_dirs(self, tmp_path: Path) -> None:
        """The ValueError text contains the exact refusal phrasing."""
        target_dir = tmp_path / "agents"
        target_dir.mkdir()

        with pytest.raises(ValueError, match="refusing to write agent") as exc:
            _write_one_agent(
                generator=_fake_generator(),
                agent_name="../escape",
                tool_result=_success("..."),
                target_dir=target_dir,
                file_writer=None,
            )

        message = str(exc.value)
        assert message.startswith("refusing to write agent '../escape': path ")
        assert "escapes target dir" in message
        assert str(target_dir.resolve()) in message
        # endswith (not `in`) kills an XX-wrap of the trailing fragment.
        assert message.endswith(str(target_dir.resolve()))


class TestPersistSuccessesContinuesPastFailures:
    """Pin ``continue`` (not ``break``) on per-agent failures (#1176/#1177)."""

    @pytest.mark.asyncio
    async def test_unresolved_id_before_good_id_still_writes_good(
        self, tmp_path: Path
    ) -> None:
        """An unresolved custom_id must not abort processing of siblings."""
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
                status="ended",
                processing_count=0,
                succeeded_count=2,
                errored_count=0,
            )
        )
        # Iteration order: rogue (unresolved → continue) then alpha.
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={
                    "rogue:unknown": _success("rogue"),
                    "subagent:alpha": _success("alpha"),
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

        # ``break`` would drop alpha entirely; ``continue`` keeps it.
        assert outcome.succeeded_agents == ("alpha",)
        assert outcome.failed_agents == ("unresolved:rogue:unknown",)

    @pytest.mark.asyncio
    async def test_missing_source_before_good_id_still_writes_good(
        self, tmp_path: Path
    ) -> None:
        """A FileNotFoundError on one agent must not abort the next."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=_recent_submitted_at(),
            custom_id_map={
                "subagent:beta": BATCH_TARGET_SUBAGENTS,
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
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
        # beta first (raises → continue), then alpha (writes).
        orchestrator.fetch_batch_results = AsyncMock(
            return_value=BatchResultsBundle(
                successes={
                    "subagent:beta": _success("beta"),
                    "subagent:alpha": _success("alpha"),
                },
                failures={},
            )
        )
        gen = _fake_generator()

        def selective_frontmatter(name: str) -> str:
            if name == "beta":
                msg = "vanished"
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

        # ``break`` would drop alpha; ``continue`` keeps it written.
        assert outcome.succeeded_agents == ("alpha",)
        assert outcome.failed_agents == ("beta",)


class TestLookupFromState:
    """Pin every branch of the custom_id -> agent_name lookup builder."""

    def test_empty_when_no_batch(self) -> None:
        """No in-flight batch yields an empty lookup (#1191)."""
        result = _lookup_from_state(EnhanceState())
        assert isinstance(result, dict)
        assert not result

    def test_maps_subagent_ids_to_agent_names(self) -> None:
        """Subagent-target ids resolve to their encoded agent name."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="b",
            submitted_at=_recent_submitted_at(),
            custom_id_map={
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
                "subagent:beta": BATCH_TARGET_SUBAGENTS,
            },
        )
        assert _lookup_from_state(state) == {
            "subagent:alpha": "alpha",
            "subagent:beta": "beta",
        }

    def test_skips_non_subagent_targets(self) -> None:
        """Entries for other targets are filtered out (#1193/#1194)."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="b",
            submitted_at=_recent_submitted_at(),
            # ``other`` must be skipped; ``alpha`` kept. A ``break``
            # mutation would stop at the first non-match.
            custom_id_map={
                "subagent:other-target": "skills",
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
            },
        )
        assert _lookup_from_state(state) == {"subagent:alpha": "alpha"}

    def test_drops_unresolvable_subagent_id(self) -> None:
        """A subagent-target id with no recoverable name is dropped (#1196)."""
        state = EnhanceState()
        state.batch = BatchProgress(
            batch_id="b",
            submitted_at=_recent_submitted_at(),
            # ``subagent:`` with an empty name → None → excluded, while
            # the real one is retained with its true name (not None).
            custom_id_map={
                "subagent:": BATCH_TARGET_SUBAGENTS,
                "subagent:alpha": BATCH_TARGET_SUBAGENTS,
            },
        )
        assert _lookup_from_state(state) == {"subagent:alpha": "alpha"}


class TestAgentNameFromCustomId:
    """Pin the ``subagent:`` prefix parsing and fallback behaviour."""

    def test_strips_subagent_prefix(self) -> None:
        """``subagent:alpha`` resolves to ``alpha``."""
        assert _agent_name_from_custom_id("subagent:alpha", {}) == "alpha"

    def test_empty_name_returns_none(self) -> None:
        """A bare ``subagent:`` prefix yields ``None``, not ``""``."""
        assert _agent_name_from_custom_id("subagent:", {}) is None

    def test_unknown_shape_uses_fallback(self) -> None:
        """An unrecognised id consults the fallback lookup."""
        assert _agent_name_from_custom_id("x:y", {"x:y": "mapped"}) == "mapped"

    def test_unknown_shape_without_fallback_returns_none(self) -> None:
        """An unrecognised id absent from the fallback yields ``None``."""
        assert _agent_name_from_custom_id("x:y", {}) is None
