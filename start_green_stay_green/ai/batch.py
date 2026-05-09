"""Batch-mode types and helpers for the Anthropic Message Batches API.

Phase 5a of the optimization roadmap. Defines the request/response
dataclasses and the parser that lifts a batch result back into the
existing :class:`ToolUseResult` shape, so batch and sync paths share a
single downstream codepath.

The Batches API submits up to 100k requests per submission, returns
results within 24 h at a 50 % discount versus sync. Per-request token
accounting and failure modes are preserved — batch mode is *cheaper*
parallelism, not consolidation.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class ToolUseBatchRequest:
    """A single ``tool_use`` request bundled into a batch submission.

    Mirrors the inputs :meth:`AIOrchestrator.generate_tool_use_async`
    consumes for a sync call: a per-call user message, the ordered
    system blocks, the forced-tool schema. The added ``custom_id`` is
    what the Anthropic API uses to key the per-request result on the
    way back; callers map it to whatever target identifier they need
    (e.g. ``"subagent:architecture-review"``).

    Attributes:
        custom_id: Caller-chosen identifier, unique within one batch.
            Echoed back in the result so the caller can correlate
            outputs with the originating target.
        prompt: User-message body (per-call delta).
        system_blocks: Ordered list of system-prompt blocks; the same
            shape :meth:`generate_tool_use_async` accepts.
        tool_schema: Anthropic-SDK-shaped tool definition.
    """

    custom_id: str
    prompt: str
    system_blocks: list[dict[str, object]]
    tool_schema: dict[str, object]


@dataclass(frozen=True)
class BatchSubmission:
    """Metadata returned by :meth:`AIOrchestrator.submit_tool_use_batch`.

    Attributes:
        batch_id: Anthropic's identifier for the submission. Persist
            this so a follow-up invocation can resume polling without
            re-submitting.
        custom_ids: The exact list of ``custom_id`` values submitted,
            in order. Lets a caller verify nothing was dropped, and
            lets the resume path know which targets to expect back.
        submitted_at: ISO-8601 UTC timestamp of when the batch was
            accepted by the API. Diagnostic only.
    """

    batch_id: str
    custom_ids: list[str]
    submitted_at: str


@dataclass(frozen=True)
class BatchPoll:
    """Snapshot of an in-flight batch's state.

    Attributes:
        batch_id: The batch this snapshot describes.
        status: Anthropic-defined lifecycle state. ``"in_progress"``
            and ``"canceling"`` mean keep polling; ``"ended"`` means
            results are ready (some may still have errored).
        processing_count: Requests still being processed.
        succeeded_count: Requests that completed with a usable
            response.
        errored_count: Requests that failed for reasons other than
            user cancel or 24 h SLA expiry.
        canceled_count: Requests aborted by an explicit batch
            cancel. Phase 5b reconciliation should leave these alone
            (the user already chose to drop them).
        expired_count: Requests that hit the 24 h SLA without
            completing. Distinct from ``errored`` so the CLI can
            decide to re-submit only the SLA-breach subset rather
            than retrying every failure type uniformly.
    """

    batch_id: str
    status: str
    processing_count: int
    succeeded_count: int
    errored_count: int
    canceled_count: int = 0
    expired_count: int = 0

    @property
    def is_ended(self) -> bool:
        """``True`` when results are ready to fetch."""
        return self.status == "ended"


@dataclass(frozen=True)
class BatchError:
    """Per-request failure stand-in for a missing :class:`ToolUseResult`.

    Returned in place of a result when a single request inside a batch
    failed (the rest of the batch is unaffected). The caller decides
    whether to retry, skip, or abort.

    Attributes:
        custom_id: Echo of the originating request's custom id.
        result_type: Anthropic's result-type label —
            ``"errored"``, ``"canceled"``, or ``"expired"``.
        message: Best-effort diagnostic string lifted from the API
            error body; empty when the API gave none.
    """

    custom_id: str
    result_type: str
    message: str = ""


@dataclass(frozen=True)
class BatchResultsBundle:
    """Successful + failed per-request outcomes from a finished batch.

    Two parallel maps so callers do not have to inspect a union type
    on every lookup. Both keyed by ``custom_id``.

    Attributes:
        successes: ``custom_id`` → :class:`ToolUseResult` for each
            request the model completed.
        failures: ``custom_id`` → :class:`BatchError` for each request
            that errored, was canceled, or expired.
    """

    successes: dict[str, ToolUseResult] = field(default_factory=dict)
    failures: dict[str, BatchError] = field(default_factory=dict)

    @property
    def total(self) -> int:
        """Combined count of successes and failures."""
        return len(self.successes) + len(self.failures)


def parse_batch_result_entry(entry: object) -> tuple[str, ToolUseResult | BatchError]:
    """Lift one streamed result entry into the parallel-map shape.

    The Anthropic SDK returns each entry of
    ``client.messages.batches.results(batch_id)`` as an object with a
    ``custom_id``, a ``result.type`` discriminator, and either
    ``result.message`` (on success) or an error payload. This
    function discriminates on that shape and returns either a
    :class:`ToolUseResult` (success) or a :class:`BatchError`
    (any non-success type).

    Kept separate from :class:`AIOrchestrator` so the parser is unit-
    testable against fakes without touching network code, and so a
    future SDK shape-change is one focused diff.

    Args:
        entry: One element of the streamed batch results. Duck-typed
            against the SDK's ``BatchResult`` shape so this works
            with both real responses and dict-shaped test doubles.

    Returns:
        ``(custom_id, ToolUseResult | BatchError)`` — caller keys the
        appropriate map with the id.

    Raises:
        GenerationError: If the entry is shaped so unexpectedly that
            no useful ``custom_id`` can be recovered. Per-request
            failures (``errored``, etc.) do not raise — they return a
            :class:`BatchError`.
    """
    custom_id = _extract_attr(entry, "custom_id")
    if not isinstance(custom_id, str) or not custom_id:
        msg = "Batch result entry is missing a usable custom_id"
        raise GenerationError(msg)

    result = _extract_attr(entry, "result")
    result_type = _extract_attr(result, "type")
    if not isinstance(result_type, str):
        return custom_id, BatchError(
            custom_id=custom_id,
            result_type="unknown",
            message="Batch result entry is missing result.type",
        )

    if result_type == "succeeded":
        message = _extract_attr(result, "message")
        return custom_id, _tool_use_result_from_message(message)

    return custom_id, BatchError(
        custom_id=custom_id,
        result_type=result_type,
        message=_extract_error_message(result),
    )


def _tool_use_result_from_message(message: object) -> ToolUseResult:
    """Build a :class:`ToolUseResult` from a batch's success ``message``.

    The success-side payload is the same shape as a normal
    ``messages.create`` response, so the lift is mechanical: pull the
    first ``ToolUseBlock``, copy ``input`` and token usage. Cache
    tokens are surfaced when present so batch users see the same
    telemetry sync users get.
    """
    tool_block = _required_tool_block(message)
    tool_input = _required_tool_input(tool_block)
    usage = _extract_attr(message, "usage")
    return ToolUseResult(
        tool_name=str(_extract_attr(tool_block, "name") or ""),
        tool_input=dict(tool_input),
        token_usage=TokenUsage(
            input_tokens=_int_attr(usage, "input_tokens"),
            output_tokens=_int_attr(usage, "output_tokens"),
        ),
        model=str(_extract_attr(message, "model") or ""),
        message_id=str(_extract_attr(message, "id") or ""),
        cache_read_tokens=_int_attr(usage, "cache_read_input_tokens"),
        cache_creation_tokens=_int_attr(usage, "cache_creation_input_tokens"),
    )


def _required_tool_block(message: object) -> object:
    """Return the message's first ``ToolUseBlock`` or raise."""
    content = _extract_attr(message, "content") or []
    block = _first_tool_use_block(content)
    if block is None:
        msg = "Batch result message did not contain a ToolUseBlock"
        raise GenerationError(msg)
    return block


def _required_tool_input(tool_block: object) -> dict[str, object]:
    """Return the block's ``input`` dict or raise on a non-dict."""
    tool_input = _extract_attr(tool_block, "input")
    if not isinstance(tool_input, dict):
        msg = "Batch ToolUseBlock.input was not a JSON object"
        raise GenerationError(msg)
    return tool_input


def _int_attr(obj: object, name: str) -> int:
    """Read ``name`` off ``obj`` as an int, defaulting to ``0`` when absent."""
    value = _extract_attr(obj, name)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _first_tool_use_block(content: object) -> object | None:
    """Return the first content block that looks like a ``ToolUseBlock``.

    Duck-typed: a block qualifies if ``type == "tool_use"`` (real
    SDK objects, JSON dicts, and test doubles all expose this the
    same way).
    """
    for block in _iter_blocks(content):
        if _extract_attr(block, "type") == "tool_use":
            return block
    return None


def _iter_blocks(content: object) -> Iterable[object]:
    """Iterate over a content payload that might be a list or a single block."""
    if isinstance(content, list):
        return content
    if content is None:
        return []
    return [content]


def _extract_attr(obj: object, name: str) -> object:
    """Read ``name`` from ``obj`` whether it is a dict, an SDK model, or ``None``.

    The Anthropic SDK exposes responses as Pydantic models; tests
    drive this code with plain dicts. ``getattr`` first, ``[]`` next,
    ``None`` if neither — keeps the parser tolerant of either shape
    without conditioning on isinstance everywhere.
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _extract_error_message(result: object) -> str:
    """Best-effort error-string lift from a non-success result entry."""
    error = _extract_attr(result, "error")
    if error is None:
        return ""
    message = _extract_attr(error, "message")
    if isinstance(message, str):
        return message
    return str(error)
