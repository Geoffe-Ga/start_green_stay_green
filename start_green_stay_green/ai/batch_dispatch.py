"""Phase 5b: orchestrate ``green enhance --batch`` over the 5a primitives.

Two callable entry points cover the user-visible flow:

* :func:`submit_subagent_batch` — build per-agent
  :class:`ToolUseBatchRequest` payloads, submit via
  :meth:`AIOrchestrator.submit_tool_use_batch`, persist a
  :class:`BatchProgress` record so a later invocation can resume.
* :func:`resume_subagent_batch` — read the persisted
  :class:`BatchProgress`, optionally wait for the batch to end, fetch
  results, write per-agent files, and clear the in-flight record.

The CLI's ``green enhance --batch`` flag chooses between the two by
inspecting :meth:`EnhanceState.has_batch`. The two-call pattern is
documented in :doc:`/plans/architecture/ADR-001-batch-enhance` (D1) —
keeping the CLI imperative makes a state-file corruption recoverable
("just re-run") instead of locked.

This module is intentionally CLI-agnostic: it returns dataclass
verdicts and lets the caller render them. Tests cover the
orchestration logic against mocked
:class:`AIOrchestrator`/:class:`SubagentsGenerator`/:class:`EnhanceState`
without touching the network or the filesystem.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.utils.enhance_state import save_state

if TYPE_CHECKING:
    from pathlib import Path

    from start_green_stay_green.ai.batch import BatchPoll
    from start_green_stay_green.ai.batch import BatchResultsBundle
    from start_green_stay_green.ai.batch import BatchSubmission
    from start_green_stay_green.ai.orchestrator import AIOrchestrator
    from start_green_stay_green.ai.types import ToolUseResult
    from start_green_stay_green.utils.enhance_state import EnhanceState
    from start_green_stay_green.utils.file_writer import FileWriter

__all__ = [
    "BATCH_TARGET_SUBAGENTS",
    "BatchSubmitOutcome",
    "ResumeOutcome",
    "ResumeStatus",
    "resume_subagent_batch",
    "submit_subagent_batch",
]

# Top-level enhance target name that batch mode supports today. Used
# as the value side of :attr:`BatchProgress.custom_id_map` so Phase 6
# CLI logic can map every recovered result back to the right
# ``EnhanceState.completed`` slot.
BATCH_TARGET_SUBAGENTS = "subagents"

# Default poll interval inside ``--wait`` mode. The Anthropic Batches
# API publishes a 24 h SLA; polling more often than every 30 s costs
# rate-limit budget without buying meaningful latency. Tests override
# via the ``poll_interval`` argument.
_DEFAULT_POLL_INTERVAL_SECONDS: float = 30.0


@dataclass(frozen=True)
class BatchSubmitOutcome:
    """What :func:`submit_subagent_batch` reports back to the CLI.

    Attributes:
        submission: The :class:`BatchSubmission` returned by the
            Anthropic API. ``submission.batch_id`` is the resume
            cursor.
        agent_count: How many agents the batch covered. Identical
            to ``len(submission.custom_ids)`` but pulled out for
            readability when rendering CLI status messages.
    """

    submission: BatchSubmission
    agent_count: int


class ResumeStatus:
    """Symbolic outcomes from :func:`resume_subagent_batch`.

    Defined as a plain class with class attributes (rather than
    :class:`enum.Enum`) so callers can compare against bare strings
    in CLI rendering without importing the enum.
    """

    NO_BATCH: str = "no-batch"
    EXPIRED: str = "expired"
    IN_PROGRESS: str = "in-progress"
    ENDED: str = "ended"
    TIMED_OUT: str = "timed-out"


@dataclass(frozen=True)
class BatchWaitConfig:
    """Wait-mode tuning passed to :func:`resume_subagent_batch`.

    Bundles the three parameters that only matter when the user
    runs ``green enhance --batch --wait``: whether to wait at all,
    how often to poll, and the deadline. Grouping them drops
    :func:`resume_subagent_batch`'s parameter count below the
    ``PLR0913`` threshold and lets call sites that don't care
    about wait-mode pass the default.

    Attributes:
        wait: If ``True``, block (with sleeps) until the batch ends
            or :attr:`wait_timeout_seconds` passes.
        poll_interval: Seconds between polls in ``wait`` mode.
            Default 30 s — the API SLA is 24 h so polling more often
            costs rate-limit budget without buying meaningful
            latency.
        wait_timeout_seconds: Maximum total wait. Defaults to
            ``3600`` (one hour); callers wanting to wait the full
            24 h SLA pass ``86400``.
    """

    wait: bool = False
    poll_interval: float = _DEFAULT_POLL_INTERVAL_SECONDS
    wait_timeout_seconds: float = 3600.0


@dataclass(frozen=True)
class ResumeOutcome:
    """What :func:`resume_subagent_batch` reports back to the CLI.

    Attributes:
        status: One of the :class:`ResumeStatus` constants. The CLI
            switches its exit code and rendered message on this.
        poll: Last :class:`BatchPoll` snapshot — ``None`` only on
            ``NO_BATCH``.
        bundle: Per-target results, present iff ``status == ENDED``.
            ``None`` for every other status.
        succeeded_agents: Names of agents whose output landed
            on disk this run. Empty for non-``ENDED`` statuses.
        failed_agents: Names of agents whose batch entry was
            ``errored`` / ``canceled`` / ``expired``. Empty for
            non-``ENDED`` statuses.
    """

    status: str
    poll: BatchPoll | None = None
    bundle: BatchResultsBundle | None = None
    succeeded_agents: tuple[str, ...] = ()
    failed_agents: tuple[str, ...] = ()


async def submit_subagent_batch(
    *,
    orchestrator: AIOrchestrator,
    generator: SubagentsGenerator,
    target_context: str,
    state: EnhanceState,
    project_path: Path,
) -> BatchSubmitOutcome:
    """Submit every required subagent as one Message Batches API call.

    Refuses to submit when an in-flight batch is already recorded —
    :meth:`EnhanceState.start_batch` raises in that case (see
    :class:`BatchStateError`); the CLI must call
    :func:`resume_subagent_batch` first to either pick up or clear the
    prior batch.

    Args:
        orchestrator: Configured :class:`AIOrchestrator`.
        generator: :class:`SubagentsGenerator` that owns the source
            agents and the :class:`ContentTuner`.
        target_context: Human-readable description of the target
            project — flows into every per-agent prompt.
        state: Loaded :class:`EnhanceState`. Mutated in-place to
            record the new batch; the caller persists.
        project_path: Project root, used to write the state file.

    Returns:
        :class:`BatchSubmitOutcome` with the new batch id and the
        agent count.

    Raises:
        GenerationError: If the SDK rejects the submission.
        BatchStateError: If a batch is already in flight.
    """
    plan = generator.build_batch_plan(target_context)
    submission = await orchestrator.submit_tool_use_batch(
        [entry.request for entry in plan],
    )
    custom_id_map = {entry.custom_id: BATCH_TARGET_SUBAGENTS for entry in plan}
    state.start_batch(
        batch_id=submission.batch_id,
        custom_id_map=custom_id_map,
        submitted_at=submission.submitted_at,
    )
    save_state(project_path, state)
    return BatchSubmitOutcome(submission=submission, agent_count=len(plan))


async def resume_subagent_batch(  # noqa: PLR0913 - see #316
    *,
    orchestrator: AIOrchestrator,
    generator: SubagentsGenerator,
    state: EnhanceState,
    project_path: Path,
    file_writer: FileWriter | None = None,
    wait_config: BatchWaitConfig | None = None,
) -> ResumeOutcome:
    """Resume an in-flight batch: poll, optionally wait, fetch, write.

    ``wait_config=None`` or ``wait_config.wait=False`` returns after
    a single poll: callers re-run ``green enhance --batch`` to pick
    up later. ``wait_config.wait=True`` enters a sleep-then-poll
    loop bounded by ``wait_config.wait_timeout_seconds`` — useful in
    CI scripts where a single command should block until results
    land. The CLI surfaces both modes as ``--batch`` and
    ``--batch --wait``.

    Detects an expired batch via
    :meth:`BatchProgress.is_potentially_expired` before polling, so a
    state file that crossed the 24 h SLA is cleared with a clear
    message rather than producing an opaque ``404``.

    Args:
        orchestrator: Configured :class:`AIOrchestrator`.
        generator: :class:`SubagentsGenerator` (used to rebuild
            per-agent files via :meth:`apply_batch_result`).
        state: Loaded :class:`EnhanceState` with an in-flight
            batch record.
        project_path: Project root — the state file is updated
            here on every meaningful state transition.
        file_writer: Optional dry-run-aware writer. ``None`` in
            production; tests inject one.
        wait_config: Wait-mode tuning. ``None`` defaults to a
            single-poll non-blocking check.

    Returns:
        :class:`ResumeOutcome` describing what happened.
    """
    config = wait_config or BatchWaitConfig()
    pre_poll = _check_pre_poll(state, project_path)
    if pre_poll is not None:
        return pre_poll
    # ``_check_pre_poll`` returns ``None`` only when ``state.batch``
    # exists; the second guard re-narrows the union for mypy without
    # an ``assert`` (which Bandit B101 flags).
    if state.batch is None:
        return ResumeOutcome(status=ResumeStatus.NO_BATCH)

    poll = await _poll_until_terminal(
        orchestrator=orchestrator,
        batch_id=state.batch.batch_id,
        config=config,
    )
    if not poll.is_ended:
        return _non_terminal_outcome(poll, waiting=config.wait)

    return await _reconcile_ended_batch(
        orchestrator=orchestrator,
        generator=generator,
        state=state,
        project_path=project_path,
        file_writer=file_writer,
        poll=poll,
    )


def _non_terminal_outcome(poll: BatchPoll, *, waiting: bool) -> ResumeOutcome:
    """Map a non-ended poll to its CLI-facing outcome.

    Extracted so :func:`resume_subagent_batch` stays grade-A under
    xenon — the inline ternary plus the surrounding branches tipped
    it to grade B.
    """
    status = ResumeStatus.TIMED_OUT if waiting else ResumeStatus.IN_PROGRESS
    return ResumeOutcome(status=status, poll=poll)


def _check_pre_poll(
    state: EnhanceState,
    project_path: Path,
) -> ResumeOutcome | None:
    """Pre-poll guards: return a final outcome, or ``None`` to keep going.

    Two conditions short-circuit before we even hit the API:

    * No in-flight batch recorded → ``NO_BATCH``.
    * Recorded batch crossed the 24 h SLA → ``EXPIRED`` (and clear
      the stale record so the next CLI run falls through to submit).
    """
    if not state.has_batch() or state.batch is None:
        return ResumeOutcome(status=ResumeStatus.NO_BATCH)
    if state.batch.is_potentially_expired():
        state.clear_batch()
        save_state(project_path, state)
        return ResumeOutcome(status=ResumeStatus.EXPIRED)
    return None


async def _reconcile_ended_batch(  # noqa: PLR0913 - dispatch glue, see #316
    *,
    orchestrator: AIOrchestrator,
    generator: SubagentsGenerator,
    state: EnhanceState,
    project_path: Path,
    file_writer: FileWriter | None,
    poll: BatchPoll,
) -> ResumeOutcome:
    """Fetch results, write per-agent files, clear batch, build outcome.

    ``state.batch`` is non-``None`` by caller contract (the resume
    flow only reaches here after the pre-poll guard returned). The
    runtime check below is a typed re-narrowing for mypy, not a
    defensive assertion — calling this with no batch is a
    programming error, but raising rather than asserting keeps
    Bandit B101 quiet.
    """
    if state.batch is None:
        msg = "_reconcile_ended_batch called without an in-flight batch"
        raise RuntimeError(msg)
    bundle = await orchestrator.fetch_batch_results(state.batch.batch_id)
    succeeded, failed = _write_results(
        generator=generator,
        bundle=bundle,
        plan_lookup=_lookup_from_state(state),
        target_dir=project_path / ".claude" / "agents",
        file_writer=file_writer,
    )
    state.clear_batch()
    save_state(project_path, state)
    return ResumeOutcome(
        status=ResumeStatus.ENDED,
        poll=poll,
        bundle=bundle,
        succeeded_agents=tuple(succeeded),
        failed_agents=tuple(failed),
    )


async def _poll_until_terminal(
    *,
    orchestrator: AIOrchestrator,
    batch_id: str,
    config: BatchWaitConfig,
) -> BatchPoll:
    """Single poll, or sleep-then-poll until ``ended`` or timeout.

    Extracted from :func:`resume_subagent_batch` so the wait-mode
    state machine is independently unit-testable. The deadline is
    computed once at entry so the per-iteration `_now()` check
    bounds the total wait.

    Note: the deadline check fires *before* the next ``poll_batch``
    call, so a slow API round-trip mid-loop (rate-limit retry,
    network timeout) is not itself bounded — total wall time can
    exceed ``config.wait_timeout_seconds`` by one ``poll_batch``
    RTT. Acceptable for the default 1 h wait window; callers
    needing strict bounding should drive the deadline at a higher
    layer (e.g. ``asyncio.wait_for``).
    """
    poll = await orchestrator.poll_batch(batch_id)
    if not config.wait or poll.is_ended:
        return poll
    deadline = _now() + config.wait_timeout_seconds
    while not poll.is_ended and _now() < deadline:
        await asyncio.sleep(config.poll_interval)
        poll = await orchestrator.poll_batch(batch_id)
    return poll


def _write_results(
    *,
    generator: SubagentsGenerator,
    bundle: BatchResultsBundle,
    plan_lookup: dict[str, str],
    target_dir: Path,
    file_writer: FileWriter | None,
) -> tuple[list[str], list[str]]:
    """Write each ``successes`` entry to disk; tally failures.

    ``plan_lookup`` is ``custom_id → agent_name`` (extracted from
    :attr:`BatchProgress.custom_id_map`'s caller-side mirror). The
    frontmatter is re-loaded from the source files so a state file
    that survives a code change to the source agents still produces
    valid output.

    Returns ``(succeeded_agent_names, failed_agent_names)``. The
    ``failed_agent_names`` list combines three sources, all surfaced
    to the user so the reconciliation summary stays accurate:

    * Per-request failures returned by the API (``bundle.failures``).
    * Successes the API returned that the local source tree could no
      longer write (e.g. the source agent file was deleted between
      submit and fetch — see :func:`_persist_successes`).
    * Successes whose ``custom_id`` did not match any known schema
      — flagged with the synthetic prefix ``"unresolved:"`` so the
      user can file a bug report rather than seeing them silently
      vanish.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    succeeded, locally_failed = _persist_successes(
        bundle=bundle,
        plan_lookup=plan_lookup,
        generator=generator,
        target_dir=target_dir,
        file_writer=file_writer,
    )
    api_failed = [
        name
        for custom_id in bundle.failures
        if (name := _agent_name_from_custom_id(custom_id, plan_lookup)) is not None
    ]
    return succeeded, locally_failed + api_failed


def _persist_successes(
    *,
    bundle: BatchResultsBundle,
    plan_lookup: dict[str, str],
    generator: SubagentsGenerator,
    target_dir: Path,
    file_writer: FileWriter | None,
) -> tuple[list[str], list[str]]:
    """Write each success to disk; return ``(written, locally_failed)``.

    Per-agent failure isolation: if writing one agent fails (source
    file deleted between submit and fetch, custom_id schema we don't
    recognise) the rest still land on disk. The failed entry's name
    flows to the caller's ``failed_agents`` so the user sees an
    accurate count and a retry hint.

    * Unresolved custom IDs (no recognised schema) become
      ``"unresolved:<custom_id>"`` so they are visible rather than
      silently dropped — this catches Phase-6 schema-drift bugs
      early.
    * :class:`FileNotFoundError` from
      :meth:`SubagentsGenerator.get_agent_frontmatter` (raised when
      the source agent file no longer exists at fetch time) is
      caught here, not at :func:`_write_one_agent` — the helper
      stays simple and orchestration owns the failure-tracking.
    """
    written: list[str] = []
    locally_failed: list[str] = []
    for custom_id, tool_result in bundle.successes.items():
        agent_name = _agent_name_from_custom_id(custom_id, plan_lookup)
        if agent_name is None:
            locally_failed.append(f"unresolved:{custom_id}")
            continue
        try:
            _write_one_agent(
                generator=generator,
                agent_name=agent_name,
                tool_result=tool_result,
                target_dir=target_dir,
                file_writer=file_writer,
            )
        except FileNotFoundError:
            # Source file vanished between submit and fetch — log
            # the agent as failed and keep going so siblings still
            # land. The reviewer's per-agent-isolation contract
            # (round-3 review) holds.
            locally_failed.append(agent_name)
            continue
        written.append(agent_name)
    return written, locally_failed


def _write_one_agent(
    *,
    generator: SubagentsGenerator,
    agent_name: str,
    tool_result: ToolUseResult,
    target_dir: Path,
    file_writer: FileWriter | None,
) -> None:
    """Write one agent's tuned content to disk.

    Extracted so :func:`_persist_successes` stays focused on the
    success-iteration loop without an embedded write block. The
    caller already has ``agent_name`` in scope (it's the loop key),
    so this function returns nothing rather than echoing it back —
    avoids the misleading ``-> str`` annotation flagged by review.
    """
    frontmatter = generator.get_agent_frontmatter(agent_name)
    result = SubagentsGenerator.apply_batch_result(
        agent_name=agent_name,
        frontmatter=frontmatter,
        tool_result=tool_result,
    )
    agent_file = target_dir / f"{agent_name}.md"
    if file_writer is not None:
        file_writer.write_file(agent_file, result.content)
    else:
        agent_file.write_text(result.content, encoding="utf-8")


def _lookup_from_state(state: EnhanceState) -> dict[str, str]:
    """Build a ``custom_id → agent_name`` lookup from the state record.

    Phase 5a's :attr:`BatchProgress.custom_id_map` stores
    ``custom_id → top-level target`` (so Phase 5b reconciliation can
    skip targets it does not handle). The agent-level mapping is
    encoded in the ``custom_id`` itself by convention
    (``"subagent:<agent_name>"``); this helper extracts it back.

    Note: passes an explicit empty fallback dict to
    :func:`_agent_name_from_custom_id` because Phase 5b only
    supports the ``subagent:`` id schema. A future phase introducing
    a new id shape (e.g. ``skill:<name>``) should also extend
    :data:`BATCH_TARGET_SUBAGENTS` and thread its own lookup table
    here — silently widening the fallback would route results to
    the wrong target.
    """
    if state.batch is None:
        return {}
    lookup: dict[str, str] = {}
    for custom_id, target in state.batch.custom_id_map.items():
        if target != BATCH_TARGET_SUBAGENTS:
            continue
        agent_name = _agent_name_from_custom_id(custom_id, {})
        if agent_name is not None:
            lookup[custom_id] = agent_name
    return lookup


def _agent_name_from_custom_id(
    custom_id: str,
    fallback_lookup: dict[str, str],
) -> str | None:
    """Return the agent name encoded in a ``subagent:<name>`` custom id.

    Falls back to ``fallback_lookup`` for any unrecognised shape
    (Phase 6 might introduce alternate id schemas). Returns ``None``
    when no name is recoverable — the caller drops the entry rather
    than mis-routing a result.
    """
    prefix = "subagent:"
    if custom_id.startswith(prefix):
        name = custom_id[len(prefix) :]
        return name or None
    return fallback_lookup.get(custom_id)


def _now() -> float:
    """Wall-clock seconds — wrapper so tests can monkey-patch.

    Uses :func:`datetime.now(UTC).timestamp()` rather than
    :func:`time.time` so the same source-of-truth backs every wait
    decision; reduces clock-source surprises during tests.
    """
    return datetime.now(UTC).timestamp()
