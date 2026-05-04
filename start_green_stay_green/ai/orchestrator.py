"""AI generation orchestrator.

Coordinates AI-powered generation tasks using Claude API.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Final
from typing import Literal
from typing import TYPE_CHECKING

from anthropic import Anthropic
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock

from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import get_active_report

if TYPE_CHECKING:
    from collections.abc import Iterator

    from start_green_stay_green.utils.timing import TimingReport


class GenerationError(Exception):
    """Raised when AI generation fails.

    Attributes:
        cause: Optional underlying exception that caused this error.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """Initialize GenerationError.

        Args:
            message: Error message describing the failure.
            cause: Optional underlying exception that caused this error.
        """
        super().__init__(message)
        self.cause = cause


class PromptTemplateError(Exception):
    """Raised when prompt template is invalid or malformed."""


class ModelConfig:
    """Claude model configuration constants.

    This class provides model identifiers for Claude AI models used
    in generation and tuning operations.
    """

    OPUS: Final[str] = "claude-opus-4-5-20251101"
    SONNET: Final[str] = "claude-sonnet-4-5-20250929"


@dataclass(frozen=True)
class TokenUsage:
    """Token usage information from API response.

    Attributes:
        input_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens in the response.
    """

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used.

        Returns:
            Sum of input and output tokens.
        """
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class GenerationResult:
    """Result from AI generation request.

    Attributes:
        content: Generated content from the AI model.
        format: Output format (yaml, toml, markdown, bash).
        token_usage: Token usage statistics for the request.
        model: Model identifier used for generation.
        message_id: Unique identifier for the API message.
    """

    content: str
    format: str
    token_usage: TokenUsage
    model: str
    message_id: str


@dataclass(frozen=True)
class _AttemptOutcome:
    """Internal helper: success result or captured retryable error."""

    result: GenerationResult | None
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
            max_tokens=4096,
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

        return GenerationResult(
            content=first_block.text,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
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
    def _record_call(
        report: TimingReport | None,
        start: float,
        attempt: int,
        result: GenerationResult | None,
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
            result: Successful :class:`GenerationResult`, or ``None``
                when the call failed (so token counts default to 0).
        """
        if report is None:
            return
        report.record_api_call(
            APICallRecord(
                latency_s=time.perf_counter() - start,
                retries=attempt,
                input_tokens=result.token_usage.input_tokens if result else 0,
                output_tokens=result.token_usage.output_tokens if result else 0,
            )
        )

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
        """Return the cached ``AsyncAnthropic`` client, creating it once."""
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
            max_tokens=4096,
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

        return GenerationResult(
            content=first_block.text,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
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

    async def aclose(self) -> None:
        """Release the cached async client, if any.

        Idempotent. Safe to call from a finally block even when no async
        calls were made.
        """
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None
