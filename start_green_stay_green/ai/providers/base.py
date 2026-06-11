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

Which optional groups a provider actually implements is advertised by
:meth:`~LLMProvider.capabilities`, a frozen
:class:`ProviderCapabilities` record readable from the class itself —
no instance, no vendor SDK. The advertisement is the single source of
truth for capability negotiation: providers that decline a group raise
:class:`UnsupportedCapabilityError` *derived from* the advertisement
(see :meth:`~LLMProvider._raise_unsupported_batch`), and orchestration
code consults the same advertisement to fall back gracefully.

Every request and response type referenced here lives in
:mod:`start_green_stay_green.ai.types` or
:mod:`start_green_stay_green.ai.batch` and is deliberately
provider-neutral: no ``anthropic`` types leak across this boundary.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Final
from typing import Literal
from typing import Never
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from start_green_stay_green.ai.batch import BatchPoll
    from start_green_stay_green.ai.batch import BatchResultsBundle
    from start_green_stay_green.ai.batch import BatchSubmission
    from start_green_stay_green.ai.batch import ToolUseBatchRequest
    from start_green_stay_green.ai.types import GenerationResult
    from start_green_stay_green.ai.types import ToolUseResult

__all__ = ["LLMProvider", "ProviderCapabilities", "UnsupportedCapabilityError"]

OutputFormat = Literal["yaml", "toml", "markdown", "bash"]

# Human-readable name of the batch capability group, echoed in every
# typed batch decline. Single-sourced here so the error text and the
# ``capability`` attribute can never drift between providers.
_BATCH_CAPABILITY: Final[str] = "batch tool-use"


@dataclass(frozen=True)
class ProviderCapabilities:
    """Machine-readable advertisement of a provider's capability groups.

    The single source of truth for capability negotiation (tracer T5,
    #389): the batch-decline stubs
    (:meth:`LLMProvider._raise_unsupported_batch`) and the
    orchestrator/CLI batch-fallback decision both derive from this
    structure, so flipping a flag here is the only change needed when
    a provider gains or loses a capability.

    Attributes:
        provider: Registry name of the advertising provider (e.g.
            ``"anthropic"``). Echoed into capability errors and the
            ``green providers`` listing.
        batch: Whether the batch group (submit / poll / fetch — the
            shape of Anthropic's Message Batches API) is implemented.
        tool_use: Whether forced tool-use (structured) generation is
            implemented.
        token_accounting: Whether token-usage telemetry is reported on
            generation results.
    """

    provider: str
    batch: bool
    tool_use: bool
    token_accounting: bool


class UnsupportedCapabilityError(NotImplementedError):
    """A provider does not implement one of the optional capability groups.

    Some capability groups are vendor-specific — the batch group maps
    onto Anthropic's Message Batches API and has no equivalent on
    OpenAI-compatible endpoints. A provider that cannot honestly
    implement a group raises this typed error instead of emulating it
    badly, so callers can catch it and fall back to a per-request
    path. The decision to decline derives from the provider's
    :class:`ProviderCapabilities` advertisement (see
    :meth:`LLMProvider._raise_unsupported_batch`), so the two cannot
    drift apart.

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

    @classmethod
    @abstractmethod
    def capabilities(cls) -> ProviderCapabilities:
        """Return this provider's capability advertisement.

        A classmethod (not a property) so callers — notably the
        selection registry behind ``green providers`` — can read
        capabilities without constructing a provider instance and
        without the vendor SDK installed (provider modules import
        their SDKs lazily).

        Returns:
            The frozen :class:`ProviderCapabilities` advertisement.
            Stable for the lifetime of the class.
        """

    @classmethod
    def _raise_unsupported_batch(cls) -> Never:
        """Raise the typed batch decline derived from :meth:`capabilities`.

        Providers advertising ``batch=False`` call this from their
        batch-group method stubs, so both the decision to decline and
        the provider name in the error come from the advertisement —
        a single source of truth with no per-stub strings to drift.

        Raises:
            UnsupportedCapabilityError: Always, when the advertisement
                says ``batch=False``.
            RuntimeError: If called by a provider advertising batch
                support — the advertisement and the implementation
                disagree, which is a programming error.
        """
        caps = cls.capabilities()
        if caps.batch:
            msg = (
                f"provider {caps.provider!r} advertises batch support; "
                f"_raise_unsupported_batch must be unreachable"
            )
            raise RuntimeError(msg)
        raise UnsupportedCapabilityError(
            provider=caps.provider,
            capability=_BATCH_CAPABILITY,
        )

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
