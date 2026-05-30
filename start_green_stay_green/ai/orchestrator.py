"""AI generation orchestrator.

Coordinates AI-powered generation tasks using Claude API.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
import time
from typing import Final
from typing import Literal
from typing import TYPE_CHECKING
from typing import cast

from anthropic import Anthropic
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock
from anthropic.types import ToolUseBlock

from start_green_stay_green.ai.batch import BatchError
from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.batch import parse_batch_result_entry
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import GenerationResult
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import get_active_report

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Iterable
    from collections.abc import Iterator
    from collections.abc import Sequence

    from anthropic.types.messages.batch_create_params import (
        Request as BatchCreateRequest,
    )

    from start_green_stay_green.utils.timing import TimingReport

# Re-export shared types from ``ai.types`` so existing
# ``from start_green_stay_green.ai.orchestrator import ToolUseResult``
# imports keep working after the Phase-5a relocation. The names
# below look unused locally but ARE the public API surface of this
# module — do not remove without a coordinated migration of every
# downstream call site (and the corresponding tests). The
# back-compat contract is asserted by
# tests/unit/ai/test_orchestrator.py — any removal here without
# that test update will fail import-time mypy in callers.
__all__ = [
    "AIOrchestrator",
    "GenerationError",
    "GenerationResult",
    "ModelConfig",
    "PromptTemplateError",
    "TokenUsage",
    "ToolUseResult",
]


def _count(obj: object, name: str) -> int:
    """Read a count attribute off ``obj``, defaulting to ``0``.

    SDK response objects expose ``request_counts.processing`` etc. as
    plain ``int`` attributes; tests pass ``MagicMock`` doubles. Keeps
    ``poll_batch``'s body short enough to stay grade-A complex.
    """
    return int(getattr(obj, name, 0) or 0)


async def _aiter(
    stream: AsyncIterable[object] | Iterable[object],
) -> AsyncIterator[object]:
    """Yield from an async iterable OR a sync iterable.

    The Anthropic SDK's ``messages.batches.results`` returns an
    async iterator at runtime, but unit tests construct fakes that
    are easier to write as plain lists. Accept both shapes so the
    test seam is wide.

    ``isinstance(stream, AsyncIterable)`` narrows the union for
    mypy on both branches, so neither path needs a ``type: ignore``.
    """
    if isinstance(stream, AsyncIterable):
        async for item in stream:
            yield item
        return
    for item in stream:
        yield item


class PromptTemplateError(Exception):
    """Raised when prompt template is invalid or malformed."""


class ModelConfig:
    """Claude model configuration constants.

    This class provides model identifiers for Claude AI models used
    in generation and tuning operations.
    """

    OPUS: Final[str] = "claude-opus-4-5-20251101"
    SONNET: Final[str] = "claude-sonnet-4-5-20250929"


# Per-call max_tokens for every Claude request the orchestrator
# issues — sync, async, tool-use, and batch alike. Single source of
# truth so a future limit change is one edit instead of four.
_MAX_TOKENS: Final[int] = 4096


@dataclass(frozen=True)
class _AttemptOutcome:
    """Internal helper: success result or captured retryable error."""

    result: GenerationResult | None
    error: Exception | None


@dataclass(frozen=True)
class _ToolAttemptOutcome:
    """Internal helper: ``tool_use`` success or captured retryable error."""

    result: ToolUseResult | None
    error: Exception | None


class AIOrchestrator:
    """Orchestrates AI generation requests using Claude API.

    This class manages API communication, retry logic, and response
    parsing for AI-powered generation tasks.

    Attributes:
        api_key: Claude API key for authentication.
        model: Claude model identifier to use for generation.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_delay: Initial delay in seconds between retry attempts.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = ModelConfig.SONNET,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize AIOrchestrator with configuration.

        Args:
            api_key: Claude API key for authentication.
            model: Claude model identifier. Defaults to SONNET.
            max_retries: Maximum retry attempts. Defaults to 3.
            retry_delay: Initial retry delay in seconds. Defaults to 1.0.

        Raises:
            ValueError: If api_key is empty or parameters are invalid.
        """
        self._validate_api_key(api_key)
        self._validate_retry_params(max_retries, retry_delay)

        self._api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        # Lazily-created long-lived async client. Reusing one client across
        # all calls in an init run lets us share the underlying httpx pool,
        # which matters once Phase 2 fans out subagent tunings concurrently.
        self._async_client: AsyncAnthropic | None = None

    @staticmethod
    def _validate_api_key(api_key: str) -> None:
        """Validate API key is not empty.

        Args:
            api_key: API key to validate.

        Raises:
            ValueError: If API key is empty or only whitespace.
        """
        if not api_key or not api_key.strip():
            msg = "API key cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_retry_params(max_retries: int, retry_delay: float) -> None:
        """Validate retry parameters.

        Args:
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.

        Raises:
            ValueError: If parameters are invalid.
        """
        if max_retries < 0:
            msg = "max_retries must be non-negative"
            raise ValueError(msg)
        if retry_delay <= 0:
            msg = "retry_delay must be positive"
            raise ValueError(msg)

    @staticmethod
    def _validate_prompt(prompt: str) -> None:
        """Validate prompt is not empty.

        Args:
            prompt: Prompt to validate.

        Raises:
            ValueError: If prompt is empty or only whitespace.
        """
        if not prompt or not prompt.strip():
            msg = "Prompt cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_output_format(
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> None:
        """Validate output format is supported.

        Args:
            output_format: Format to validate.

        Raises:
            ValueError: If format is not supported.
        """
        supported_formats = {"yaml", "toml", "markdown", "bash"}
        if output_format not in supported_formats:
            msg = f"Unsupported output format: {output_format}"
            raise ValueError(msg)

    @staticmethod
    def _cache_tokens(usage: object) -> tuple[int, int]:
        """Extract ``(cache_read, cache_creation)`` token counts from ``usage``.

        The Anthropic SDK exposes ``cache_read_input_tokens`` and
        ``cache_creation_input_tokens`` only when prompt caching is
        active *and* the SDK version supports them; both fields can be
        ``None``. Coerce to ``int`` so downstream telemetry never has
        to defend against ``None``.
        """
        return (
            int(getattr(usage, "cache_read_input_tokens", 0) or 0),
            int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
        )

    def _call_api(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Call Claude API and build result.

        Args:
            client: Anthropic API client.
            prompt: Generation prompt.
            output_format: Desired output format.

        Returns:
            GenerationResult with content and metadata.

        Raises:
            GenerationError: If response is invalid.
        """
        response = client.messages.create(
            model=self.model,
            max_tokens=_MAX_TOKENS,
            system=(
                f"Generate {output_format} output. "
                "Follow the instructions precisely."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        # Extract content from response
        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            msg = "Expected TextBlock in response"
            raise GenerationError(msg)

        cache_read, cache_creation = self._cache_tokens(response.usage)
        return GenerationResult(
            content=first_block.text,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_creation,
        )

    def _retry_with_backoff(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Retry API call with exponential backoff (sync).

        Telemetry is recorded by the call site once after the loop
        terminates (success or exhaustion). Failure paths never miss a
        recording because both branches end with ``_record_call``.
        """
        report = get_active_report()
        call_started = time.perf_counter()

        for attempt, sleep_s in self._retry_schedule():
            outcome = self._attempt_sync(client, prompt, output_format)
            if outcome.result is not None:
                self._record_call(report, call_started, attempt, outcome.result)
                return outcome.result
            if sleep_s is None:
                self._record_call(report, call_started, attempt, None)
                msg = "Failed to generate content"
                raise GenerationError(msg, cause=outcome.error) from outcome.error
            time.sleep(sleep_s)

        # ``_retry_schedule`` always yields at least one entry, so this
        # is unreachable; keep mypy/coverage happy.
        msg = "Failed to generate content"
        raise GenerationError(msg)

    def _retry_schedule(self) -> Iterator[tuple[int, float | None]]:
        """Yield ``(attempt_index, sleep_before_next_or_None)`` pairs."""
        for attempt in range(self.max_retries + 1):
            is_last = attempt == self.max_retries
            yield attempt, None if is_last else self.retry_delay * (2**attempt)

    def _attempt_sync(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> _AttemptOutcome:
        """Run one sync attempt; return the result or capture the error."""
        try:
            return _AttemptOutcome(
                result=self._call_api(client, prompt, output_format),
                error=None,
            )
        except GenerationError:
            raise
        except Exception as e:  # noqa: BLE001 — preserved for retry semantics
            return _AttemptOutcome(result=None, error=e)

    @staticmethod
    def _build_api_call_record(
        latency_s: float,
        attempt: int,
        result: GenerationResult | ToolUseResult | None,
    ) -> APICallRecord:
        """Build an ``APICallRecord`` from a result, or zeros for failures.

        Extracted from :meth:`_record_call` to keep the recorder at
        cyclomatic grade A: the four-way ``result and X`` branch chain
        was tipping it into grade B.
        """
        if result is None:
            return APICallRecord(latency_s=latency_s, retries=attempt)
        return APICallRecord(
            latency_s=latency_s,
            retries=attempt,
            input_tokens=result.token_usage.input_tokens,
            output_tokens=result.token_usage.output_tokens,
            cache_read_tokens=result.cache_read_tokens,
            cache_creation_tokens=result.cache_creation_tokens,
        )

    @classmethod
    def _record_call(
        cls,
        report: TimingReport | None,
        start: float,
        attempt: int,
        result: GenerationResult | ToolUseResult | None,
    ) -> None:
        """Record a completed call (success or failure) on the active report.

        Args:
            report: Active timing collector, or ``None`` when telemetry is off.
            start: ``perf_counter`` value captured before the first attempt.
            attempt: Zero-indexed attempt number from
                :meth:`_retry_schedule`. ``attempt=0`` means the first
                try succeeded with no retries; ``attempt=N`` means
                ``N`` retries were used. Stored as ``retries`` on the
                resulting :class:`APICallRecord` because that's the
                telemetry consumer's preferred naming.
            result: Successful :class:`GenerationResult` or
                :class:`ToolUseResult`, or ``None`` when the call
                failed (so token counts default to 0).
        """
        if report is None:
            return
        latency_s = time.perf_counter() - start
        report.record_api_call(cls._build_api_call_record(latency_s, attempt, result))

    def generate(
        self,
        prompt: str,
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Generate content using Claude API (synchronous).

        Args:
            prompt: Prompt describing what to generate.
            output_format: Desired output format (yaml, toml, markdown, bash).

        Returns:
            GenerationResult containing generated content and metadata.

        Raises:
            ValueError: If prompt is empty or format unsupported.
            GenerationError: If API call fails or response invalid.
        """
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)

        # Use context manager to ensure httpx client is properly closed
        with Anthropic(api_key=self._api_key) as client:
            return self._retry_with_backoff(client, prompt, output_format)

    def _get_async_client(self) -> AsyncAnthropic:
        """Return the cached ``AsyncAnthropic`` client, creating it once.

        The check-then-set pattern is *not* thread-safe in the abstract,
        but it is safe under asyncio: there is no ``await`` between the
        ``is None`` check and the assignment, so no other coroutine can
        run between them on the same event loop. This method is only
        ever called from coroutines on a single event loop, never from
        a thread pool, so adding a lock would be over-engineering. Do
        *not* call this from ``ThreadPoolExecutor``.
        """
        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self._api_key)
        return self._async_client

    async def _call_api_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Async counterpart of :meth:`_call_api`."""
        response = await client.messages.create(
            model=self.model,
            max_tokens=_MAX_TOKENS,
            system=(
                f"Generate {output_format} output. "
                "Follow the instructions precisely."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            msg = "Expected TextBlock in response"
            raise GenerationError(msg)

        cache_read, cache_creation = self._cache_tokens(response.usage)
        return GenerationResult(
            content=first_block.text,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_creation,
        )

    async def _retry_with_backoff_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Async retry loop matching the sync semantics of ``_retry_with_backoff``."""
        report = get_active_report()
        call_started = time.perf_counter()

        for attempt, sleep_s in self._retry_schedule():
            outcome = await self._attempt_async(client, prompt, output_format)
            if outcome.result is not None:
                self._record_call(report, call_started, attempt, outcome.result)
                return outcome.result
            if sleep_s is None:
                self._record_call(report, call_started, attempt, None)
                msg = "Failed to generate content"
                raise GenerationError(msg, cause=outcome.error) from outcome.error
            await asyncio.sleep(sleep_s)

        msg = "Failed to generate content"
        raise GenerationError(msg)

    async def _attempt_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        output_format: str,
    ) -> _AttemptOutcome:
        """Run one async attempt; return the result or capture the error."""
        try:
            return _AttemptOutcome(
                result=await self._call_api_async(client, prompt, output_format),
                error=None,
            )
        except GenerationError:
            raise
        except Exception as e:  # noqa: BLE001 — preserved for retry semantics
            return _AttemptOutcome(result=None, error=e)

    async def generate_async(
        self,
        prompt: str,
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Async equivalent of :meth:`generate`.

        Reuses a single long-lived ``AsyncAnthropic`` client per
        orchestrator instance so concurrent calls share the httpx
        connection pool. Callers should ``await`` :meth:`aclose` when
        the orchestrator is no longer needed.
        """
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)

        client = self._get_async_client()
        return await self._retry_with_backoff_async(client, prompt, output_format)

    async def _call_tool_api_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> ToolUseResult:
        """Make one ``tool_use`` API call and return the parsed result.

        Forces the model into the supplied tool via ``tool_choice``,
        then extracts the first :class:`ToolUseBlock` from the
        response. The block's ``input`` (already validated against the
        tool's ``input_schema`` server-side) is the structured payload
        the caller wants.

        Delegates the request-envelope construction to
        :meth:`_tool_request_params` so the sync and batch paths
        share one source of truth — a future change to ``system``,
        ``tool_choice``, or ``max_tokens`` shape lands in one place.
        """
        params = self._tool_request_params(prompt, system_blocks, tool_schema)
        # The Anthropic SDK exposes ``system``, ``tools``, and
        # ``tool_choice`` as deeply-nested TypedDict unions. Threading
        # those through the generic ``dict[str, object]`` shapes we
        # accept from callers would mean re-exporting half the SDK's
        # internal types just to satisfy mypy, with no runtime
        # benefit. The SDK validates the payload server-side; we
        # type-ignore the single call site instead.
        response = await client.messages.create(**params)  # type: ignore[call-overload]

        tool_block = next(
            (b for b in response.content if isinstance(b, ToolUseBlock)),
            None,
        )
        if tool_block is None:
            msg = "Expected ToolUseBlock in response"
            raise GenerationError(msg)
        if not isinstance(tool_block.input, dict):
            msg = "Tool input was not a JSON object"
            raise GenerationError(msg)

        cache_read, cache_creation = self._cache_tokens(response.usage)
        return ToolUseResult(
            tool_name=tool_block.name,
            tool_input=dict(tool_block.input),
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
            cache_read_tokens=cache_read,
            cache_creation_tokens=cache_creation,
        )

    async def _attempt_tool_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> _ToolAttemptOutcome:
        """Run one async ``tool_use`` attempt; capture errors for retry."""
        try:
            result = await self._call_tool_api_async(
                client,
                prompt,
                system_blocks=system_blocks,
                tool_schema=tool_schema,
            )
        except GenerationError:
            raise
        except Exception as e:  # noqa: BLE001 — preserved for retry semantics
            return _ToolAttemptOutcome(result=None, error=e)
        else:
            return _ToolAttemptOutcome(result=result, error=None)

    async def _retry_tool_with_backoff_async(
        self,
        client: AsyncAnthropic,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> ToolUseResult:
        """Async retry loop for the ``tool_use`` path."""
        report = get_active_report()
        call_started = time.perf_counter()

        for attempt, sleep_s in self._retry_schedule():
            outcome = await self._attempt_tool_async(
                client,
                prompt,
                system_blocks=system_blocks,
                tool_schema=tool_schema,
            )
            if outcome.result is not None:
                self._record_call(report, call_started, attempt, outcome.result)
                return outcome.result
            if sleep_s is None:
                self._record_call(report, call_started, attempt, None)
                msg = "Failed to generate content"
                raise GenerationError(msg, cause=outcome.error) from outcome.error
            await asyncio.sleep(sleep_s)

        msg = "Failed to generate content"
        raise GenerationError(msg)

    async def generate_tool_use_async(
        self,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> ToolUseResult:
        """Run a structured (``tool_use``) generation.

        The model is forced to invoke ``tool_schema`` and the parsed
        ``input`` dict is returned to the caller — no free-form text
        parsing required. ``system_blocks`` is passed verbatim to the
        Anthropic API, so callers can attach
        ``cache_control={"type": "ephemeral"}`` to whichever blocks
        should participate in prompt caching.

        Args:
            prompt: User-message body (per-call delta — should NOT
                duplicate content already present in
                ``system_blocks``, otherwise cache-key mismatches will
                defeat the cache).
            system_blocks: Ordered list of system-prompt blocks, each
                a dict matching the Anthropic SDK's system-block
                schema (``{"type": "text", "text": "...",
                "cache_control": {...}}``).
            tool_schema: Anthropic-SDK-shaped tool definition with
                ``name``, ``description``, and ``input_schema`` keys.

        Returns:
            :class:`ToolUseResult` with the parsed ``tool_input`` dict
            and full token / cache telemetry.

        Raises:
            ValueError: If ``prompt`` is empty.
            GenerationError: If the API call fails after retries or
                the response does not contain a tool-use block.
        """
        self._validate_prompt(prompt)
        client = self._get_async_client()
        return await self._retry_tool_with_backoff_async(
            client,
            prompt,
            system_blocks=system_blocks,
            tool_schema=tool_schema,
        )

    async def aclose(self) -> None:
        """Release the cached async client, if any.

        Idempotent. Safe to call from a finally block even when no async
        calls were made.
        """
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None

    async def submit_tool_use_batch(
        self,
        requests: Sequence[ToolUseBatchRequest],
    ) -> BatchSubmission:
        """Submit ``requests`` as a single Message Batches API call.

        Each :class:`ToolUseBatchRequest` is translated into the
        Batches-API request envelope (``custom_id`` + ``params``) and
        the whole list is passed to
        ``client.messages.batches.create``. Returns the batch id and
        an echo of the submitted ``custom_id`` order so callers can
        persist both for a later resume.

        The forced ``tool_choice`` mirrors :meth:`generate_tool_use_async`
        — the model is required to invoke the supplied tool, so the
        result message is guaranteed to contain a
        ``ToolUseBlock``. This keeps the result parser
        (:func:`parse_batch_result_entry`) simple.

        Args:
            requests: One or more :class:`ToolUseBatchRequest`
                payloads. Empty input is rejected (the SDK would reject
                it server-side; failing locally keeps the error close
                to the caller).

        Returns:
            :class:`BatchSubmission` with the new ``batch_id`` and the
            ``custom_id`` echo list.

        Raises:
            ValueError: If ``requests`` is empty or contains duplicate
                ``custom_id`` values.
            GenerationError: If the API call fails.
        """
        custom_ids = self._validate_batch_requests(requests)
        payload = [self._batch_request_envelope(r) for r in requests]
        batch = await self._create_batch(payload)
        return BatchSubmission(
            batch_id=str(getattr(batch, "id", "") or ""),
            custom_ids=list(custom_ids),
            submitted_at=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _validate_batch_requests(
        requests: Sequence[ToolUseBatchRequest],
    ) -> list[str]:
        """Pre-flight validation; returns the ordered ``custom_id`` list."""
        if not requests:
            msg = "submit_tool_use_batch requires at least one request"
            raise ValueError(msg)
        custom_ids = [r.custom_id for r in requests]
        if len(set(custom_ids)) != len(custom_ids):
            msg = "submit_tool_use_batch requests must have unique custom_id values"
            raise ValueError(msg)
        return custom_ids

    async def _create_batch(self, payload: list[dict[str, object]]) -> object:
        """Wrap the SDK call so callers see ``GenerationError`` on failure.

        The SDK signature is
        ``create(*, requests: Iterable[batch_create_params.Request])``.
        We construct each envelope as a ``dict[str, object]`` matching
        the ``Request`` ``TypedDict`` shape (verified by
        ``test_request_envelope_carries_tool_choice_and_system``).
        Mypy cannot prove the dict matches the TypedDict's deeply-nested
        ``MessageCreateParamsNonStreaming`` shape without re-typing the
        ``ToolUseBatchRequest.system_blocks`` chain end-to-end, so we
        use one ``cast()`` at the SDK boundary to assert the contract
        rather than a ``# type: ignore`` to suppress it. ``cast`` is
        documented narrowing; ``type: ignore`` is suppression.
        """
        client = self._get_async_client()
        try:
            return await client.messages.batches.create(
                requests=cast("Iterable[BatchCreateRequest]", payload),
            )
        except Exception as exc:
            msg = "Batch submission failed"
            raise GenerationError(msg, cause=exc) from exc

    async def poll_batch(self, batch_id: str) -> BatchPoll:
        """Return the current state of an in-flight batch.

        Single retrieve call — no internal polling loop. Callers that
        want a blocking wait drive their own sleep/poll cycle (see the
        ADR for why the two-call CLI pattern is preferred over a
        long-running command).

        Args:
            batch_id: Identifier returned from
                :meth:`submit_tool_use_batch`.

        Returns:
            :class:`BatchPoll` with status and per-state counts.

        Raises:
            ValueError: If ``batch_id`` is empty.
            GenerationError: If the API call fails.
        """
        self._require_batch_id(batch_id, "poll_batch")
        batch = await self._retrieve_batch(batch_id)
        return self._batch_poll_from_response(batch_id, batch)

    @staticmethod
    def _batch_poll_from_response(batch_id: str, batch: object) -> BatchPoll:
        """Pull the ``BatchPoll`` snapshot fields off a SDK response object."""
        counts = getattr(batch, "request_counts", None)
        return BatchPoll(
            batch_id=batch_id,
            status=str(getattr(batch, "processing_status", "") or ""),
            processing_count=_count(counts, "processing"),
            succeeded_count=_count(counts, "succeeded"),
            errored_count=_count(counts, "errored"),
            canceled_count=_count(counts, "canceled"),
            expired_count=_count(counts, "expired"),
        )

    async def fetch_batch_results(self, batch_id: str) -> BatchResultsBundle:
        """Stream a finished batch's results into ``(successes, failures)``.

        Calls ``client.messages.batches.results(batch_id)`` and folds
        each entry through :func:`parse_batch_result_entry`. Successes
        land in :attr:`BatchResultsBundle.successes` keyed by
        ``custom_id``; non-success entries (errored, canceled,
        expired) land in :attr:`BatchResultsBundle.failures`.

        Args:
            batch_id: Identifier of an ``ended`` batch.

        Returns:
            :class:`BatchResultsBundle` with per-``custom_id`` results.

        Raises:
            ValueError: If ``batch_id`` is empty.
            GenerationError: If the API call fails or any entry's
                shape is unrecoverably malformed (per-request
                failures do *not* raise — they populate ``failures``).
        """
        self._require_batch_id(batch_id, "fetch_batch_results")
        stream = await self._open_results_stream(batch_id)
        # Collect into local dicts and construct the frozen bundle at
        # the end. Mutating the bundle's fields in-place after
        # construction worked (``frozen=True`` doesn't deep-freeze
        # mutable containers) but read as a contradiction — a reader
        # seeing ``frozen=True`` reasonably expects the object to be
        # fully immutable.
        successes: dict[str, ToolUseResult] = {}
        failures: dict[str, BatchError] = {}
        async for entry in _aiter(stream):
            custom_id, outcome = parse_batch_result_entry(entry)
            if isinstance(outcome, ToolUseResult):
                successes[custom_id] = outcome
            else:
                failures[custom_id] = outcome
        return BatchResultsBundle(successes=successes, failures=failures)

    @staticmethod
    def _require_batch_id(batch_id: str, op: str) -> None:
        """Reject empty/missing ``batch_id`` close to the caller."""
        if not batch_id:
            msg = f"{op} requires a non-empty batch_id"
            raise ValueError(msg)

    async def _retrieve_batch(self, batch_id: str) -> object:
        """Wrap the SDK retrieve so callers see ``GenerationError`` on failure."""
        client = self._get_async_client()
        try:
            return await client.messages.batches.retrieve(batch_id)
        except Exception as exc:
            msg = f"Batch retrieve failed for {batch_id}"
            raise GenerationError(msg, cause=exc) from exc

    async def _open_results_stream(
        self,
        batch_id: str,
    ) -> AsyncIterable[object] | Iterable[object]:
        """Open the batch's result stream as an iterable.

        ``AsyncBatches.results()`` is ``async def`` (a coroutine
        function — *not* an async-generator function); it returns a
        coroutine that resolves to an
        ``AsyncJSONLDecoder[MessageBatchIndividualResponse]``. The
        decoder is itself an async iterable, hence the
        ``await`` then ``async for`` pattern in the caller.
        Verified against ``anthropic`` SDK 0.97.0 by reading
        ``inspect.iscoroutinefunction(AsyncBatches.results)``.

        Returns the iterable shape ``_aiter`` expects directly, so
        callers do not have to cast. SDK errors are remapped to
        :class:`GenerationError` to keep the public surface uniform
        with the sync path.
        """
        client = self._get_async_client()
        try:
            stream = await client.messages.batches.results(batch_id)
        except Exception as exc:
            msg = f"Batch results stream failed for {batch_id}"
            raise GenerationError(msg, cause=exc) from exc
        # The SDK returns an async iterator at runtime; tests pass a
        # plain list via ``AsyncMock``. Both satisfy the union, so
        # the cast is a type-check-only narrowing — no isinstance
        # at runtime.
        return cast("AsyncIterable[object] | Iterable[object]", stream)

    def _batch_request_envelope(
        self,
        request: ToolUseBatchRequest,
    ) -> dict[str, object]:
        """Wrap one :class:`ToolUseBatchRequest` in Batches-API shape.

        The Anthropic Batches API expects a list of
        ``{"custom_id": ..., "params": {...}}`` dicts where ``params``
        is a normal ``messages.create`` body. ``params`` is built by
        :meth:`_tool_request_params` — the same helper
        :meth:`_call_tool_api_async` uses — so sync and batch paths
        cannot drift apart on envelope shape.
        """
        return {
            "custom_id": request.custom_id,
            "params": self._tool_request_params(
                request.prompt,
                request.system_blocks,
                request.tool_schema,
                custom_id=request.custom_id,
            ),
        }

    def _tool_request_params(
        self,
        prompt: str,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
        *,
        custom_id: str = "",
    ) -> dict[str, object]:
        """Build the Anthropic ``messages.create`` body shared by sync + batch.

        Every field here is identical between the two transports —
        a single source of truth so a future change to ``system``,
        ``tool_choice``, ``max_tokens``, or ``messages`` shape lands
        once and applies to both. ``custom_id`` is optional context
        for the validation error (named in the message when present).

        Validates ``tool_schema["name"]`` is non-empty before
        construction; the API would otherwise reject a missing name
        with an opaque HTTP 400 wrapped in a generic
        ``GenerationError``.
        """
        raw_name = tool_schema.get("name")
        if not isinstance(raw_name, str) or not raw_name:
            qualifier = f" for custom_id {custom_id!r}" if custom_id else ""
            msg = f"tool_schema{qualifier} must include a non-empty " "'name' string"
            raise GenerationError(msg)
        return {
            "model": self.model,
            "max_tokens": _MAX_TOKENS,
            "system": list(system_blocks),
            "tools": [tool_schema],
            "tool_choice": {"type": "tool", "name": raw_name},
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }
