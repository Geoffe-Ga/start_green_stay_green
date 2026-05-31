"""AI generation orchestrator.

Coordinates AI-powered generation tasks using a pluggable
:class:`~start_green_stay_green.ai.providers.base.LLMProvider`.

As of tracer T1 (#381) this module no longer touches the ``anthropic``
SDK directly: all Anthropic-specific code (client construction, retry
/ backoff, token accounting, the Message Batches API) lives in
:class:`~start_green_stay_green.ai.providers.anthropic_provider.AnthropicProvider`.
``AIOrchestrator`` owns input validation and the public API surface,
then delegates the actual generation to an injected provider — by
default an :class:`AnthropicProvider`, so every existing caller is
unchanged.
"""

from __future__ import annotations

from typing import Final
from typing import Literal
from typing import TYPE_CHECKING

from start_green_stay_green.ai.providers.anthropic_provider import AnthropicProvider
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import GenerationResult
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from start_green_stay_green.ai.batch import BatchPoll
    from start_green_stay_green.ai.batch import BatchResultsBundle
    from start_green_stay_green.ai.batch import BatchSubmission
    from start_green_stay_green.ai.batch import ToolUseBatchRequest
    from start_green_stay_green.ai.providers.base import LLMProvider

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


class PromptTemplateError(Exception):
    """Raised when prompt template is invalid or malformed."""


class ModelConfig:
    """Claude model configuration constants.

    This class provides model identifiers for Claude AI models used
    in generation and tuning operations.
    """

    OPUS: Final[str] = "claude-opus-4-5-20251101"
    SONNET: Final[str] = "claude-sonnet-4-5-20250929"


class AIOrchestrator:
    """Orchestrates AI generation requests via an :class:`LLMProvider`.

    This class owns input validation and the stable public API; the
    actual API communication, retry logic, and response parsing are
    delegated to the injected provider. By default it constructs an
    :class:`AnthropicProvider`, so existing callers that pass only an
    ``api_key`` keep the original Anthropic-backed behavior with no
    changes.

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
        provider: LLMProvider | None = None,
    ) -> None:
        """Initialize AIOrchestrator with configuration.

        Args:
            api_key: Claude API key for authentication.
            model: Claude model identifier. Defaults to SONNET.
            max_retries: Maximum retry attempts. Defaults to 3.
            retry_delay: Initial retry delay in seconds. Defaults to 1.0.
            provider: Optional pre-built :class:`LLMProvider`. When
                omitted (the default), an :class:`AnthropicProvider` is
                constructed from ``api_key``, ``model``, ``max_retries``,
                and ``retry_delay`` so existing callers are unchanged.
                Injecting a provider lets later tracers and tests
                substitute a different backend without touching this
                class.

        Raises:
            ValueError: If api_key is empty or parameters are invalid.
        """
        self._validate_api_key(api_key)
        self._validate_retry_params(max_retries, retry_delay)

        self._api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._provider: LLMProvider = provider or AnthropicProvider(
            api_key,
            model=model,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )

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

    def generate(
        self,
        prompt: str,
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Generate content using the provider (synchronous).

        Args:
            prompt: Prompt describing what to generate.
            output_format: Desired output format (yaml, toml, markdown, bash).

        Returns:
            GenerationResult containing generated content and metadata.

        Raises:
            ValueError: If prompt is empty or format unsupported.
            GenerationError: If generation fails or response invalid.
        """
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)
        return self._provider.generate(prompt, output_format)

    async def generate_async(
        self,
        prompt: str,
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Async equivalent of :meth:`generate`.

        Delegates to the provider, which reuses a single long-lived
        client per orchestrator instance so concurrent calls share the
        connection pool. Callers should ``await`` :meth:`aclose` when
        the orchestrator is no longer needed.
        """
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)
        return await self._provider.generate_async(prompt, output_format)

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
        provider, so callers can attach
        ``cache_control={"type": "ephemeral"}`` to whichever blocks
        should participate in prompt caching.

        Args:
            prompt: User-message body (per-call delta — should NOT
                duplicate content already present in
                ``system_blocks``, otherwise cache-key mismatches will
                defeat the cache).
            system_blocks: Ordered list of system-prompt blocks, each
                a dict matching the provider's system-block
                schema (``{"type": "text", "text": "...",
                "cache_control": {...}}``).
            tool_schema: Provider-shaped tool definition with
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
        return await self._provider.generate_tool_use_async(
            prompt,
            system_blocks=system_blocks,
            tool_schema=tool_schema,
        )

    async def aclose(self) -> None:
        """Release the provider's cached client, if any.

        Idempotent. Safe to call from a finally block even when no async
        calls were made.
        """
        await self._provider.aclose()

    async def submit_tool_use_batch(
        self,
        requests: Sequence[ToolUseBatchRequest],
    ) -> BatchSubmission:
        """Submit ``requests`` as a single Message Batches API call.

        Delegates to the provider. See
        :meth:`LLMProvider.submit_tool_use_batch` for the contract.

        Args:
            requests: One or more :class:`ToolUseBatchRequest`
                payloads. Empty input is rejected.

        Returns:
            :class:`BatchSubmission` with the new ``batch_id`` and the
            ``custom_id`` echo list.

        Raises:
            ValueError: If ``requests`` is empty or contains duplicate
                ``custom_id`` values.
            GenerationError: If the API call fails.
        """
        return await self._provider.submit_tool_use_batch(requests)

    async def poll_batch(self, batch_id: str) -> BatchPoll:
        """Return the current state of an in-flight batch.

        Delegates to the provider. See
        :meth:`LLMProvider.poll_batch` for the contract.

        Args:
            batch_id: Identifier returned from
                :meth:`submit_tool_use_batch`.

        Returns:
            :class:`BatchPoll` with status and per-state counts.

        Raises:
            ValueError: If ``batch_id`` is empty.
            GenerationError: If the API call fails.
        """
        return await self._provider.poll_batch(batch_id)

    async def fetch_batch_results(self, batch_id: str) -> BatchResultsBundle:
        """Stream a finished batch's results into ``(successes, failures)``.

        Delegates to the provider. See
        :meth:`LLMProvider.fetch_batch_results` for the contract.

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
        return await self._provider.fetch_batch_results(batch_id)
