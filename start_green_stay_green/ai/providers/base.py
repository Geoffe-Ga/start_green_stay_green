"""Provider-neutral LLM interface.

Defines :class:`LLMProvider`, the contract every concrete provider
(Anthropic today; others later) must satisfy. The interface is split
into five capability groups so callers — and later tracers in the
multi-agent epic — can reason about exactly what a provider offers:

* **auth / lifecycle** — :meth:`~LLMProvider.aclose`.
* **model config** — :attr:`~LLMProvider.model`.
* **sync complete** — :meth:`~LLMProvider.generate`.
* **async complete** — :meth:`~LLMProvider.generate_async`.
* **tool-use** — :meth:`~LLMProvider.generate_tool_use_async`.
* **batch** — :meth:`~LLMProvider.submit_tool_use_batch`,
  :meth:`~LLMProvider.poll_batch`, :meth:`~LLMProvider.fetch_batch_results`.

Every request and response type referenced here lives in
:mod:`start_green_stay_green.ai.types` or
:mod:`start_green_stay_green.ai.batch` and is deliberately
provider-neutral: no ``anthropic`` types leak across this boundary.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Literal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from start_green_stay_green.ai.batch import BatchPoll
    from start_green_stay_green.ai.batch import BatchResultsBundle
    from start_green_stay_green.ai.batch import BatchSubmission
    from start_green_stay_green.ai.batch import ToolUseBatchRequest
    from start_green_stay_green.ai.types import GenerationResult
    from start_green_stay_green.ai.types import ToolUseResult

__all__ = ["LLMProvider", "UnsupportedCapabilityError"]

OutputFormat = Literal["yaml", "toml", "markdown", "bash"]


class UnsupportedCapabilityError(NotImplementedError):
    """A provider does not implement one of the optional capability groups.

    Some capability groups are vendor-specific — the batch group maps
    onto Anthropic's Message Batches API and has no equivalent on
    OpenAI-compatible endpoints. A provider that cannot honestly
    implement a group raises this typed error instead of emulating it
    badly, so callers can catch it and fall back to a per-request
    path. Full capability advertisement/negotiation arrives with
    tracer T5 (#389); this minimal convention is what it will build
    on.

    Subclasses :class:`NotImplementedError` so generic handlers keep
    working, while ``provider`` and ``capability`` stay machine-readable.

    Attributes:
        provider: Registry name of the provider lacking the capability.
        capability: Human-readable name of the missing capability.
    """

    def __init__(self, *, provider: str, capability: str) -> None:
        """Build the error message from the provider/capability pair.

        Args:
            provider: Registry name of the provider (e.g. ``"openai"``).
            capability: Capability group being declined (e.g.
                ``"batch tool-use"``).
        """
        msg = (
            f"The {provider!r} provider does not support {capability}. "
            f"Use a provider that implements this capability (for "
            f"batch tool-use: 'anthropic'), or run the requests "
            f"individually."
        )
        super().__init__(msg)
        self.provider = provider
        self.capability = capability


class LLMProvider(ABC):
    """Abstract contract for a large-language-model backend.

    A provider owns its own client lifecycle, retry policy, model
    selection, and token accounting. Implementations translate the
    provider-neutral request/response dataclasses into whatever shape
    their SDK expects and back again, so no vendor type ever crosses
    this boundary.

    Concrete providers are expected to be cheap to construct and to
    lazily allocate any network clients, so that constructing one
    never performs I/O.
    """

    @property
    @abstractmethod
    def model(self) -> str:
        """Return the model identifier this provider generates with.

        Returns:
            The provider-specific model id (for example an Anthropic
            ``claude-...`` string). Stable for the provider's
            lifetime.
        """

    @abstractmethod
    def generate(self, prompt: str, output_format: OutputFormat) -> GenerationResult:
        """Generate free-form content synchronously.

        Args:
            prompt: Prompt describing what to generate. Must be
                non-empty.
            output_format: Desired output format (``yaml``, ``toml``,
                ``markdown``, or ``bash``).

        Returns:
            A :class:`~start_green_stay_green.ai.types.GenerationResult`
            with the generated content and token telemetry.

        Raises:
            ValueError: If ``prompt`` is empty or ``output_format`` is
                unsupported.
            GenerationError: If generation fails after the provider's
                configured retries, or the response is malformed.
        """

    @abstractmethod
    async def generate_async(
        self,
        prompt: str,
        output_format: OutputFormat,
    ) -> GenerationResult:
        """Async counterpart of :meth:`generate`.

        Implementations should reuse a single long-lived client across
        calls so concurrent requests share a connection pool. Callers
        must ``await`` :meth:`aclose` when finished.

        Args:
            prompt: Prompt describing what to generate. Must be
                non-empty.
            output_format: Desired output format.

        Returns:
            A populated
            :class:`~start_green_stay_green.ai.types.GenerationResult`.

        Raises:
            ValueError: If ``prompt`` is empty or ``output_format`` is
                unsupported.
            GenerationError: If generation fails after retries.
        """

    @abstractmethod
    async def generate_tool_use_async(
        self,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> ToolUseResult:
        """Run a structured (forced tool-use) generation.

        The model is forced to invoke ``tool_schema`` and the parsed
        ``input`` dict is returned, replacing free-form text parsing.

        Args:
            prompt: User-message body (per-call delta). Must be
                non-empty.
            system_blocks: Ordered system-prompt blocks, each a dict in
                the provider's system-block schema. Passed verbatim so
                callers may attach cache-control markers.
            tool_schema: Provider-shaped tool definition with at least
                a non-empty ``name``.

        Returns:
            A :class:`~start_green_stay_green.ai.types.ToolUseResult`
            carrying the parsed ``tool_input`` and token telemetry.

        Raises:
            ValueError: If ``prompt`` is empty.
            GenerationError: If the call fails after retries or the
                response contains no tool-use block.
        """

    @abstractmethod
    async def submit_tool_use_batch(
        self,
        requests: Sequence[ToolUseBatchRequest],
    ) -> BatchSubmission:
        """Submit many tool-use requests as one batch.

        Args:
            requests: One or more batch requests with unique
                ``custom_id`` values.

        Returns:
            A :class:`~start_green_stay_green.ai.batch.BatchSubmission`
            echoing the new batch id and submitted ``custom_id`` order.

        Raises:
            ValueError: If ``requests`` is empty or has duplicate
                ``custom_id`` values.
            GenerationError: If the submission call fails.
        """

    @abstractmethod
    async def poll_batch(self, batch_id: str) -> BatchPoll:
        """Return the current state of an in-flight batch.

        Args:
            batch_id: Identifier returned from
                :meth:`submit_tool_use_batch`.

        Returns:
            A :class:`~start_green_stay_green.ai.batch.BatchPoll`
            snapshot with status and per-state counts.

        Raises:
            ValueError: If ``batch_id`` is empty.
            GenerationError: If the poll call fails.
        """

    @abstractmethod
    async def fetch_batch_results(self, batch_id: str) -> BatchResultsBundle:
        """Stream a finished batch's results into successes and failures.

        Args:
            batch_id: Identifier of an ended batch.

        Returns:
            A :class:`~start_green_stay_green.ai.batch.BatchResultsBundle`
            partitioned by ``custom_id``.

        Raises:
            ValueError: If ``batch_id`` is empty.
            GenerationError: If the call fails or an entry is so
                malformed no ``custom_id`` can be recovered.
        """

    @abstractmethod
    async def aclose(self) -> None:
        """Release any cached network client.

        Must be idempotent: safe to call from a ``finally`` block even
        when no async work was performed.
        """
