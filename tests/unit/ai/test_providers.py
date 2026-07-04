"""Unit tests for the LLMProvider seam introduced in tracer T1 (#381).

Two contracts are pinned here:

* :class:`AnthropicProvider` *is* an :class:`LLMProvider` and is
  instantiable without performing any I/O.
* :class:`AIOrchestrator` delegates every generation call to the
  injected provider verbatim — it adds input validation, nothing
  else — and defaults to an :class:`AnthropicProvider` when none is
  supplied.

The delegation tests use a fully fake provider so they assert the
wiring (which method, which arguments) without any Anthropic SDK or
network involvement.
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import time
from typing import TYPE_CHECKING
from typing import get_args
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import anthropic
from anthropic.types import TextBlock
from anthropic.types import ToolUseBlock
import pytest

from start_green_stay_green.ai.batch import BatchError
from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.provider_selection import ProviderUnavailableError
from start_green_stay_green.ai.providers import AnthropicProvider
from start_green_stay_green.ai.providers import LLMProvider
from start_green_stay_green.ai.providers import OpenAIProvider
from start_green_stay_green.ai.providers import ProviderCapabilities
from start_green_stay_green.ai.providers import UnsupportedCapabilityError
from start_green_stay_green.ai.providers import anthropic_provider
from start_green_stay_green.ai.providers.base import OutputFormat
from start_green_stay_green.ai.providers.outcomes import AttemptOutcome
from start_green_stay_green.ai.providers.outcomes import ToolAttemptOutcome
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import GenerationResult
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.utils.timing import TimingReport
from start_green_stay_green.utils.timing import set_active_report

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Sequence


def _generation_result() -> GenerationResult:
    return GenerationResult(
        content="content",
        format="yaml",
        token_usage=TokenUsage(input_tokens=1, output_tokens=2),
        model="model-x",
        message_id="msg_1",
    )


def _tool_use_result() -> ToolUseResult:
    return ToolUseResult(
        tool_name="report_tuning",
        tool_input={"k": "v"},
        token_usage=TokenUsage(input_tokens=1, output_tokens=2),
        model="model-x",
        message_id="msg_1",
    )


def _spy_provider() -> MagicMock:
    """Return a fake provider whose every method is a recording mock.

    ``spec=LLMProvider`` keeps the fake honest: a typo'd method name on
    the orchestrator would raise instead of silently passing.
    """
    provider = MagicMock(spec=LLMProvider)
    provider.model = "model-x"
    provider.generate = MagicMock(return_value=_generation_result())
    provider.generate_async = AsyncMock(return_value=_generation_result())
    provider.generate_tool_use_async = AsyncMock(return_value=_tool_use_result())
    provider.submit_tool_use_batch = AsyncMock(
        return_value=BatchSubmission(batch_id="b1", custom_ids=["a"], submitted_at="t")
    )
    provider.poll_batch = AsyncMock(
        return_value=BatchPoll(
            batch_id="b1",
            status="ended",
            processing_count=0,
            succeeded_count=1,
            errored_count=0,
        )
    )
    provider.fetch_batch_results = AsyncMock(return_value=BatchResultsBundle())
    provider.aclose = AsyncMock()
    return provider


class TestAnthropicProviderSatisfiesInterface:
    """``AnthropicProvider`` must be a concrete, no-I/O ``LLMProvider``."""

    def test_is_subclass_of_llm_provider(self) -> None:
        """The concrete provider declares the interface as its base."""
        assert issubclass(AnthropicProvider, LLMProvider)

    def test_instance_is_an_llm_provider(self) -> None:
        """An instance satisfies ``isinstance`` against the interface."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        assert isinstance(provider, LLMProvider)

    def test_construction_performs_no_io(self) -> None:
        """Constructing the provider allocates no network client.

        The async client is lazy; the sync client is per-call. So a
        freshly-built provider holds ``None`` for its cached client.
        """
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        assert provider._async_client is None

    def test_model_property_returns_configured_id(self) -> None:
        """``model`` echoes the id passed at construction, exactly."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.OPUS)
        assert provider.model == ModelConfig.OPUS
        assert provider.model != ModelConfig.SONNET

    def test_implements_every_abstract_method(self) -> None:
        """No abstract method is left unimplemented (kills stub mutants)."""
        assert not getattr(AnthropicProvider, "__abstractmethods__", frozenset())

    def test_default_retry_policy_matches_orchestrator_defaults(self) -> None:
        """Default retry knobs match the historical orchestrator values."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        assert provider.max_retries == 3
        assert provider.retry_delay == 1.0

    def test_retry_schedule_is_exponential_and_last_has_no_sleep(self) -> None:
        """``_retry_schedule`` yields exact exponential delays, None last.

        Pins the relocated backoff math: delay = retry_delay * 2**attempt
        for every attempt except the final one, which yields ``None``.
        """
        provider = AnthropicProvider(
            "sk-test",
            model=ModelConfig.SONNET,
            max_retries=3,
            retry_delay=1.0,
        )
        schedule = list(provider._retry_schedule())
        assert schedule == [(0, 1.0), (1, 2.0), (2, 4.0), (3, None)]


class TestLLMProviderInterface:
    """The abstract base cannot be used as a concrete provider."""

    def test_cannot_instantiate_abstract_base(self) -> None:
        """Instantiating the ABC directly raises ``TypeError``."""
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore[abstract]

    def test_interface_declares_expected_capabilities(self) -> None:
        """Every documented capability is an abstract method/property."""
        abstract = LLMProvider.__abstractmethods__
        assert abstract == {
            "model",
            "capabilities",
            "generate",
            "generate_async",
            "generate_tool_use_async",
            "submit_tool_use_batch",
            "poll_batch",
            "fetch_batch_results",
            "aclose",
        }

    def test_async_capabilities_are_coroutines(self) -> None:
        """The async-contract methods are declared ``async def``."""
        for name in (
            "generate_async",
            "generate_tool_use_async",
            "submit_tool_use_batch",
            "poll_batch",
            "fetch_batch_results",
            "aclose",
        ):
            assert inspect.iscoroutinefunction(getattr(LLMProvider, name))


class TestCapabilityAdvertisement:
    """T5 (#389): providers advertise capabilities as one frozen structure.

    The advertisement is the single source of truth for capability
    negotiation: the batch-decline stubs and the orchestrator's
    fallback decision both derive from it.
    """

    def test_anthropic_advertises_batch_supported(self) -> None:
        """Anthropic implements every capability group, batch included."""
        assert AnthropicProvider.capabilities() == ProviderCapabilities(
            provider="anthropic",
            batch=True,
            tool_use=True,
            token_accounting=True,
        )

    def test_openai_advertises_batch_unsupported(self) -> None:
        """OpenAI declines batch but supports tool-use and token telemetry."""
        assert OpenAIProvider.capabilities() == ProviderCapabilities(
            provider="openai",
            batch=False,
            tool_use=True,
            token_accounting=True,
        )

    def test_capabilities_readable_without_an_instance(self) -> None:
        """The advertisement is a classmethod: no construction, no SDK.

        ``green providers`` reads capabilities through the selection
        registry, which must work without any vendor extra installed —
        so the advertisement cannot live on a constructed instance.
        """
        assert OpenAIProvider.capabilities().batch is False
        assert AnthropicProvider.capabilities().batch is True

    def test_capabilities_structure_is_frozen(self) -> None:
        """The advertisement is immutable — callers cannot flip flags."""
        caps = AnthropicProvider.capabilities()
        field_name = "batch"
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(caps, field_name, False)

    def test_decline_helper_derives_error_from_advertisement(self) -> None:
        """The typed decline carries the advertised provider name."""
        with pytest.raises(UnsupportedCapabilityError) as exc:
            OpenAIProvider._raise_unsupported_batch()
        assert exc.value.provider == "openai"
        assert exc.value.capability == "batch tool-use"

    def test_decline_helper_refuses_batch_capable_provider(self) -> None:
        """A batch-capable provider calling the decline helper is a bug."""
        with pytest.raises(RuntimeError, match="advertises batch support"):
            AnthropicProvider._raise_unsupported_batch()

    def test_orchestrator_capabilities_delegates_to_provider(self) -> None:
        """``AIOrchestrator.capabilities`` reads the injected provider's."""
        provider = _spy_provider()
        provider.capabilities = MagicMock(
            return_value=OpenAIProvider.capabilities(),
        )
        orchestrator = AIOrchestrator(api_key="sk-test", provider=provider)
        assert orchestrator.capabilities == OpenAIProvider.capabilities()
        provider.capabilities.assert_called_once_with()

    def test_default_orchestrator_advertises_batch(self) -> None:
        """The zero-config (Anthropic) orchestrator advertises batch."""
        orchestrator = AIOrchestrator(api_key="sk-test")
        assert orchestrator.capabilities.batch is True


class TestOrchestratorDefaultsToAnthropicProvider:
    """With no injected provider, the orchestrator builds an Anthropic one."""

    def test_default_provider_is_anthropic(self) -> None:
        """A bare orchestrator wires up an ``AnthropicProvider``."""
        orchestrator = AIOrchestrator(api_key="sk-test")
        assert isinstance(orchestrator._provider, AnthropicProvider)

    def test_default_provider_inherits_model_and_retry_config(self) -> None:
        """Construction args flow through to the default provider."""
        orchestrator = AIOrchestrator(
            api_key="sk-test",
            model=ModelConfig.OPUS,
            max_retries=7,
            retry_delay=2.5,
        )
        provider = orchestrator._provider
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == ModelConfig.OPUS
        assert provider.max_retries == 7
        assert provider.retry_delay == 2.5

    def test_injected_provider_is_used_verbatim(self) -> None:
        """An explicitly injected provider is stored without wrapping."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)
        assert orchestrator._provider is fake


class TestOrchestratorDelegatesToProvider:
    """Each public method forwards to the provider with identical args."""

    def test_generate_delegates(self) -> None:
        """``generate`` validates then forwards to ``provider.generate``."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        result = orchestrator.generate("hello", "yaml")

        fake.generate.assert_called_once_with("hello", "yaml")
        assert result is fake.generate.return_value

    def test_generate_validates_before_delegating(self) -> None:
        """Empty prompt is rejected by the orchestrator, never reaching the provider."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            orchestrator.generate("", "yaml")
        fake.generate.assert_not_called()

    def test_generate_rejects_bad_format_before_delegating(self) -> None:
        """Unsupported format is rejected before the provider is touched."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        with pytest.raises(ValueError, match="Unsupported output format"):
            orchestrator.generate("hi", "xml")  # type: ignore[arg-type]
        fake.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_async_delegates(self) -> None:
        """``generate_async`` forwards to the provider's async method."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        result = await orchestrator.generate_async("hello", "markdown")

        fake.generate_async.assert_awaited_once_with("hello", "markdown")
        assert result is fake.generate_async.return_value

    @pytest.mark.asyncio
    async def test_generate_async_validates_before_delegating(self) -> None:
        """Empty prompt short-circuits before the provider is awaited."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await orchestrator.generate_async("   ", "markdown")
        fake.generate_async.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_generate_tool_use_async_delegates_with_kwargs(self) -> None:
        """Tool-use call forwards system_blocks and tool_schema by keyword."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)
        system_blocks: list[dict[str, object]] = [{"type": "text", "text": "S"}]
        tool_schema: dict[str, object] = {"name": "report_tuning"}

        result = await orchestrator.generate_tool_use_async(
            "msg",
            system_blocks=system_blocks,
            tool_schema=tool_schema,
        )

        fake.generate_tool_use_async.assert_awaited_once_with(
            "msg",
            system_blocks=system_blocks,
            tool_schema=tool_schema,
        )
        assert result is fake.generate_tool_use_async.return_value

    @pytest.mark.asyncio
    async def test_generate_tool_use_async_validates_prompt(self) -> None:
        """Empty tool-use prompt is rejected before delegation."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await orchestrator.generate_tool_use_async(
                "",
                system_blocks=[],
                tool_schema={"name": "x"},
            )
        fake.generate_tool_use_async.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_submit_tool_use_batch_delegates(self) -> None:
        """Batch submit forwards the request sequence unchanged."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)
        requests: Sequence[ToolUseBatchRequest] = [
            ToolUseBatchRequest(
                custom_id="a",
                prompt="p",
                system_blocks=[],
                tool_schema={"name": "x"},
            ),
        ]

        result = await orchestrator.submit_tool_use_batch(requests)

        fake.submit_tool_use_batch.assert_awaited_once_with(requests)
        assert result is fake.submit_tool_use_batch.return_value

    @pytest.mark.asyncio
    async def test_poll_batch_delegates(self) -> None:
        """Poll forwards the batch id unchanged."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        result = await orchestrator.poll_batch("b1")

        fake.poll_batch.assert_awaited_once_with("b1")
        assert result is fake.poll_batch.return_value

    @pytest.mark.asyncio
    async def test_fetch_batch_results_delegates(self) -> None:
        """Fetch forwards the batch id unchanged."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        result = await orchestrator.fetch_batch_results("b1")

        fake.fetch_batch_results.assert_awaited_once_with("b1")
        assert result is fake.fetch_batch_results.return_value

    @pytest.mark.asyncio
    async def test_aclose_delegates(self) -> None:
        """``aclose`` forwards to the provider's ``aclose``."""
        fake = _spy_provider()
        orchestrator = AIOrchestrator(api_key="sk-test", provider=fake)

        await orchestrator.aclose()

        fake.aclose.assert_awaited_once_with()


class TestAttemptOutcomeHelpers:
    """The relocated retry-outcome dataclasses keep their tiny contract."""

    def test_attempt_outcome_holds_result_xor_error(self) -> None:
        """``AttemptOutcome`` carries a result and an error slot."""
        ok = AttemptOutcome(result=_generation_result(), error=None)
        assert ok.result is not None
        assert ok.error is None

        boom = AttemptOutcome(result=None, error=ValueError("x"))
        assert boom.result is None
        assert isinstance(boom.error, ValueError)

    def test_tool_attempt_outcome_holds_result_xor_error(self) -> None:
        """``ToolAttemptOutcome`` mirrors ``AttemptOutcome`` for tool calls."""
        ok = ToolAttemptOutcome(result=_tool_use_result(), error=None)
        assert ok.result is not None
        assert ok.error is None

        boom = ToolAttemptOutcome(result=None, error=RuntimeError("x"))
        assert boom.result is None
        assert isinstance(boom.error, RuntimeError)


class TestTypesDataclasses:
    """Pin exact defaults, frozen-ness, and arithmetic of ai.types."""

    def test_generation_error_keeps_cause_reference(self) -> None:
        """``GenerationError.cause`` is the exact exception passed in."""
        cause = ValueError("boom")
        error = GenerationError("failed", cause=cause)
        assert error.cause is cause

    def test_generation_error_cause_defaults_to_none(self) -> None:
        """Omitting ``cause`` leaves the attribute as ``None``."""
        assert GenerationError("failed").cause is None

    def test_token_usage_is_frozen(self) -> None:
        """``TokenUsage`` rejects field assignment after construction."""
        usage = TokenUsage(input_tokens=1, output_tokens=2)
        with pytest.raises(dataclasses.FrozenInstanceError, match="input_tokens"):
            usage.input_tokens = 9  # type: ignore[misc]

    def test_total_tokens_is_a_property_returning_an_int(self) -> None:
        """``total_tokens`` is a property, so access yields an ``int``."""
        usage = TokenUsage(input_tokens=5, output_tokens=2)
        total = usage.total_tokens
        assert isinstance(total, int)
        assert total == 7

    def test_total_tokens_sums_input_and_output(self) -> None:
        """``total_tokens`` adds (not subtracts) the two counts."""
        usage = TokenUsage(input_tokens=5, output_tokens=2)
        assert usage.total_tokens == 7
        assert usage.total_tokens != 3

    def test_generation_result_is_frozen(self) -> None:
        """``GenerationResult`` rejects field assignment after construction."""
        result = _generation_result()
        with pytest.raises(dataclasses.FrozenInstanceError, match="content"):
            result.content = "other"  # type: ignore[misc]

    def test_generation_result_cache_token_defaults_are_zero(self) -> None:
        """Both cache-token fields default to exactly ``0`` (int)."""
        result = _generation_result()
        assert result.cache_read_tokens == 0
        assert result.cache_creation_tokens == 0
        assert isinstance(result.cache_read_tokens, int)
        assert isinstance(result.cache_creation_tokens, int)

    def test_tool_use_result_is_frozen(self) -> None:
        """``ToolUseResult`` rejects field assignment after construction."""
        result = _tool_use_result()
        with pytest.raises(dataclasses.FrozenInstanceError, match="tool_name"):
            result.tool_name = "other"  # type: ignore[misc]

    def test_tool_use_result_cache_token_defaults_are_zero(self) -> None:
        """Both cache-token fields default to exactly ``0`` (int)."""
        result = _tool_use_result()
        assert result.cache_read_tokens == 0
        assert result.cache_creation_tokens == 0
        assert isinstance(result.cache_read_tokens, int)
        assert isinstance(result.cache_creation_tokens, int)


class TestOutputFormatLiteral:
    """Pin the exact, ordered membership of the ``OutputFormat`` literal."""

    def test_output_format_members_are_exact(self) -> None:
        """The four allowed formats appear verbatim and in order."""
        assert get_args(OutputFormat) == ("yaml", "toml", "markdown", "bash")


class TestUnsupportedCapabilityErrorMessage:
    """Pin the exact decline message and machine-readable attributes."""

    def test_message_is_exact(self) -> None:
        """The error string is assembled verbatim from provider/capability."""
        error = UnsupportedCapabilityError(
            provider="openai",
            capability="batch tool-use",
        )
        assert str(error) == (
            "The 'openai' provider does not support batch tool-use. "
            "Use a provider that implements this capability (for "
            "batch tool-use: 'anthropic'), or run the requests "
            "individually."
        )

    def test_attributes_are_exact(self) -> None:
        """The provider/capability attributes echo the constructor args."""
        error = UnsupportedCapabilityError(
            provider="openai",
            capability="batch tool-use",
        )
        assert error.provider == "openai"
        assert error.capability == "batch tool-use"

    def test_is_a_not_implemented_error(self) -> None:
        """Subclassing ``NotImplementedError`` keeps generic handlers working."""
        error = UnsupportedCapabilityError(
            provider="openai",
            capability="batch tool-use",
        )
        assert isinstance(error, NotImplementedError)


class TestRaiseUnsupportedBatchRuntimeMessage:
    """Pin the exact RuntimeError text when a batch-capable provider declines."""

    def test_runtime_error_message_is_exact(self) -> None:
        """The programmer-error message is assembled verbatim."""
        with pytest.raises(RuntimeError) as exc:
            AnthropicProvider._raise_unsupported_batch()
        assert str(exc.value) == (
            "provider 'anthropic' advertises batch support; "
            "_raise_unsupported_batch must be unreachable"
        )


class TestLLMProviderDescriptorTypes:
    """Pin the descriptor kinds (property / classmethod) on the ABC."""

    def test_model_is_a_property(self) -> None:
        """``model`` is exposed as a property, not a plain abstract method."""
        descriptor = inspect.getattr_static(LLMProvider, "model")
        assert isinstance(descriptor, property)

    def test_capabilities_is_a_classmethod(self) -> None:
        """``capabilities`` is a classmethod readable without an instance."""
        descriptor = inspect.getattr_static(LLMProvider, "capabilities")
        assert isinstance(descriptor, classmethod)


class TestOutcomesFrozen:
    """The retry-outcome dataclasses are immutable records."""

    def test_attempt_outcome_is_frozen(self) -> None:
        """``AttemptOutcome`` rejects field assignment after construction."""
        outcome = AttemptOutcome(result=_generation_result(), error=None)
        with pytest.raises(dataclasses.FrozenInstanceError, match="error"):
            outcome.error = ValueError("x")  # type: ignore[misc]

    def test_tool_attempt_outcome_is_frozen(self) -> None:
        """``ToolAttemptOutcome`` rejects field assignment after construction."""
        outcome = ToolAttemptOutcome(result=_tool_use_result(), error=None)
        with pytest.raises(dataclasses.FrozenInstanceError, match="error"):
            outcome.error = ValueError("x")  # type: ignore[misc]


def _text_response(text: str, *, model: str = ModelConfig.SONNET) -> MagicMock:
    """Build a mock async response carrying a single text block."""
    response = MagicMock()
    response.id = "msg_async"
    response.model = model
    response.usage.input_tokens = 11
    response.usage.output_tokens = 4
    response.usage.cache_read_input_tokens = 0
    response.usage.cache_creation_input_tokens = 0
    block = MagicMock(spec=TextBlock)
    block.text = text
    response.content = [block]
    return response


def _async_client(create: AsyncMock) -> MagicMock:
    """Build a mock AsyncAnthropic client with awaitable create/close."""
    client = MagicMock()
    client.messages.create = create
    client.close = AsyncMock()
    return client


@pytest.fixture
def active_report() -> Iterator[TimingReport]:
    """Install a fresh ``TimingReport`` for the test, then clear it."""
    report = TimingReport()
    set_active_report(report)
    try:
        yield report
    finally:
        set_active_report(None)


class TestAnthropicProviderAsyncPaths:
    """Directly exercise the relocated async generate / retry branches."""

    @pytest.mark.asyncio
    async def test_generate_async_returns_result(self) -> None:
        """A successful async call yields a populated result."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(
            AsyncMock(return_value=_text_response("hello"))
        )
        try:
            result = await provider.generate_async("p", "markdown")
        finally:
            await provider.aclose()

        assert isinstance(result, GenerationResult)
        assert result.content == "hello"
        assert result.token_usage.input_tokens == 11

    @pytest.mark.asyncio
    async def test_generate_async_retries_then_succeeds(self) -> None:
        """Async retry loop sleeps after a failure, then returns success."""
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=2, retry_delay=0.0
        )
        provider._async_client = _async_client(
            AsyncMock(
                side_effect=[RuntimeError("boom"), _text_response("ok")],
            )
        )
        try:
            result = await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()

        assert result.content == "ok"

    @pytest.mark.asyncio
    async def test_generate_async_exhausts_retries_and_raises(
        self, active_report: TimingReport
    ) -> None:
        """Persistent failure raises and records a zero-token failure call."""
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=0, retry_delay=0.001
        )
        boom = RuntimeError("always down")
        provider._async_client = _async_client(AsyncMock(side_effect=boom))

        try:
            with pytest.raises(GenerationError, match="Failed to generate content"):
                await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()

        # The failure path still records one API call with no tokens.
        assert len(active_report.api_calls) == 1
        assert active_report.api_calls[0].input_tokens == 0

    @pytest.mark.asyncio
    async def test_generate_async_non_text_block_raises(self) -> None:
        """A non-TextBlock first block is a hard error on the async path."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        response = MagicMock()
        response.id = "msg_x"
        response.model = ModelConfig.SONNET
        response.usage.input_tokens = 1
        response.usage.output_tokens = 1
        non_text = MagicMock()  # not a TextBlock spec
        response.content = [non_text]
        provider._async_client = _async_client(AsyncMock(return_value=response))

        try:
            with pytest.raises(GenerationError, match="Expected TextBlock"):
                await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_tool_use_non_dict_input_raises(self) -> None:
        """A tool block whose ``input`` is not a dict is rejected."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        response = MagicMock()
        response.id = "msg_x"
        response.model = ModelConfig.SONNET
        response.usage.input_tokens = 1
        response.usage.output_tokens = 1
        response.usage.cache_read_input_tokens = 0
        response.usage.cache_creation_input_tokens = 0
        tool_block = MagicMock(spec=ToolUseBlock)
        tool_block.name = "report_tuning"
        tool_block.input = ["not", "a", "dict"]
        response.content = [tool_block]
        provider._async_client = _async_client(AsyncMock(return_value=response))

        try:
            with pytest.raises(GenerationError, match="not a JSON object"):
                await provider.generate_tool_use_async(
                    "p",
                    system_blocks=[{"type": "text", "text": "S"}],
                    tool_schema={"name": "report_tuning"},
                )
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_tool_use_retries_then_raises_on_exhaustion(self) -> None:
        """The tool-use retry loop sleeps then raises when retries run out."""
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=1, retry_delay=0.0
        )
        provider._async_client = _async_client(
            AsyncMock(side_effect=RuntimeError("down"))
        )

        try:
            with pytest.raises(GenerationError, match="Failed to generate content"):
                await provider.generate_tool_use_async(
                    "p",
                    system_blocks=[{"type": "text", "text": "S"}],
                    tool_schema={"name": "report_tuning"},
                )
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_fetch_batch_results_consumes_true_async_iterable(self) -> None:
        """``_aiter`` handles a genuine async iterator, not just a list.

        The SDK returns an async iterator at runtime; this covers that
        branch of the relocated ``_aiter`` helper.
        """

        async def _stream() -> AsyncIterator[dict[str, object]]:
            yield {
                "custom_id": "a",
                "result": {
                    "type": "succeeded",
                    "message": {
                        "id": "m",
                        "model": "claude",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "report_tuning",
                                "input": {"k": "v"},
                            },
                        ],
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    },
                },
            }

        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        client = MagicMock()
        client.messages.batches.results = AsyncMock(return_value=_stream())
        provider._async_client = client

        bundle = await provider.fetch_batch_results("b1")

        assert set(bundle.successes) == {"a"}
        assert isinstance(bundle.successes["a"], ToolUseResult)


# --------------------------------------------------------------------------- #
# Module-level helpers for the mutation-killing suite below.
# --------------------------------------------------------------------------- #


def _set_attr(obj: object, field: str, value: object) -> None:
    """Assign ``field`` on ``obj`` (defeats mypy read-only frozen checks)."""
    setattr(obj, field, value)


_SYNC_SLEEP = "start_green_stay_green.ai.providers.anthropic_provider.time.sleep"
_ASYNC_SLEEP = "start_green_stay_green.ai.providers.anthropic_provider.asyncio.sleep"


def _usage(
    *,
    input_tokens: int = 11,
    output_tokens: int = 4,
    cache_read: object = 0,
    cache_creation: object = 0,
) -> MagicMock:
    """Build a mock ``usage`` object with explicit token / cache counts."""
    usage = MagicMock()
    usage.input_tokens = input_tokens
    usage.output_tokens = output_tokens
    usage.cache_read_input_tokens = cache_read
    usage.cache_creation_input_tokens = cache_creation
    return usage


def _full_text_response(
    text: str = "hi",
    *,
    model: str = ModelConfig.SONNET,
    message_id: str = "msg_sync",
    usage: MagicMock | None = None,
) -> MagicMock:
    """Build a mock response with one text block and a usage record."""
    response = MagicMock()
    response.id = message_id
    response.model = model
    response.usage = usage if usage is not None else _usage()
    block = MagicMock(spec=TextBlock)
    block.text = text
    response.content = [block]
    return response


def _tool_response(
    *,
    name: str = "report_tuning",
    tool_input: object | None = None,
    model: str = ModelConfig.SONNET,
    message_id: str = "msg_tool",
    usage: MagicMock | None = None,
) -> MagicMock:
    """Build a mock response carrying a single tool-use block."""
    response = MagicMock()
    response.id = message_id
    response.model = model
    response.usage = usage if usage is not None else _usage()
    block = MagicMock(spec=ToolUseBlock)
    block.name = name
    block.input = {"k": "v"} if tool_input is None else tool_input
    response.content = [block]
    return response


def _sync_client_cls(create: MagicMock) -> tuple[MagicMock, MagicMock]:
    """Build a mock ``Anthropic`` class whose context manager yields a client."""
    client = MagicMock()
    client.messages.create = create
    client_cls = MagicMock()
    client_cls.return_value.__enter__.return_value = client
    client_cls.return_value.__exit__.return_value = False
    return client_cls, client


def _batch_client(create: AsyncMock) -> MagicMock:
    """Build a mock async client whose ``batches.create`` is awaitable."""
    client = MagicMock()
    client.messages.batches.create = create
    client.close = AsyncMock()
    return client


def _block_anthropic_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make resolving the ``anthropic`` SDK raise ``ModuleNotFoundError``."""
    real_import_module: Callable[..., object] = importlib.import_module

    def _fake_import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "anthropic" or name.startswith("anthropic."):
            msg = "No module named 'anthropic'"
            raise ModuleNotFoundError(msg)
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)


class TestLazySdkResolution:
    """Pin the PEP 562 ``__getattr__`` seam and the missing-SDK hint."""

    def test_sdk_exports_map_each_name_to_exact_module_and_attr(self) -> None:
        """Every export resolves to the exact (module, attribute) pair."""
        exports = anthropic_provider._SDK_EXPORTS
        assert exports["Anthropic"] == ("anthropic", "Anthropic")
        assert exports["AsyncAnthropic"] == ("anthropic", "AsyncAnthropic")
        assert exports["TextBlock"] == ("anthropic.types", "TextBlock")
        assert exports["ToolUseBlock"] == ("anthropic.types", "ToolUseBlock")

    def test_install_extra_constant_is_exact(self) -> None:
        """The pip extra name is exactly ``anthropic``."""
        assert anthropic_provider._INSTALL_EXTRA == "anthropic"

    def test_getattr_resolves_known_export(self) -> None:
        """A known export name returns the real SDK object."""
        assert anthropic_provider.__getattr__("Anthropic") is anthropic.Anthropic

    def test_getattr_unknown_name_raises_attribute_error(self) -> None:
        """An unknown attribute raises ``AttributeError`` with exact text."""
        with pytest.raises(AttributeError) as exc:
            anthropic_provider.__getattr__("Nope")
        assert str(exc.value) == (
            "module 'start_green_stay_green.ai.providers.anthropic_provider' "
            "has no attribute 'Nope'"
        )

    def test_getattr_unknown_name_message_names_the_attribute(self) -> None:
        """The AttributeError quotes the missing attribute name verbatim."""
        with pytest.raises(AttributeError, match="has no attribute 'Bogus'"):
            anthropic_provider.__getattr__("Bogus")

    def test_getattr_missing_sdk_raises_provider_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing extra surfaces an actionable ``ProviderUnavailableError``."""
        _block_anthropic_import(monkeypatch)
        with pytest.raises(ProviderUnavailableError) as exc:
            anthropic_provider.__getattr__("Anthropic")
        assert str(exc.value) == (
            "The 'anthropic' provider requires an optional dependency "
            "that is not installed. Install it with: "
            "pip install 'start-green-stay-green[anthropic]'"
        )

    def test_missing_sdk_error_chains_original_import_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The original ``ImportError`` is chained as ``__cause__``."""
        _block_anthropic_import(monkeypatch)
        with pytest.raises(ProviderUnavailableError) as exc:
            anthropic_provider.__getattr__("AsyncAnthropic")
        assert isinstance(exc.value.__cause__, ImportError)

    def test_raise_missing_sdk_message_starts_with_provider_phrase(self) -> None:
        """``_raise_missing_sdk`` builds the exact actionable message."""
        original = ImportError("No module named 'anthropic'")
        with pytest.raises(ProviderUnavailableError) as exc:
            anthropic_provider._raise_missing_sdk(original)
        assert str(exc.value).startswith(
            "The 'anthropic' provider requires an optional dependency"
        )
        assert exc.value.__cause__ is original


class TestConstants:
    """Pin numeric / capability constants survivors mutate off-by-one."""

    def test_max_tokens_is_exactly_4096(self) -> None:
        """The shared per-call max_tokens is exactly 4096."""
        assert anthropic_provider._MAX_TOKENS == 4096

    def test_provider_name_constant_is_anthropic(self) -> None:
        """The registry name constant is exactly ``anthropic``."""
        assert anthropic_provider._PROVIDER_NAME == "anthropic"

    def test_init_stores_api_key_verbatim(self) -> None:
        """The constructor stores the api key as-is for client creation."""
        provider = AnthropicProvider("sk-secret", model=ModelConfig.SONNET)
        assert provider._api_key == "sk-secret"  # pragma: allowlist secret


class TestCountHelper:
    """Pin ``_count`` defaulting and falsy-coercion behavior."""

    def test_count_reads_attribute_value(self) -> None:
        """A present positive count is returned as an int."""
        obj = MagicMock()
        obj.processing = 5
        assert anthropic_provider._count(obj, "processing") == 5

    def test_count_missing_attribute_defaults_to_zero(self) -> None:
        """A missing attribute defaults to exactly 0, not 1."""

        class _Empty:
            pass

        assert anthropic_provider._count(_Empty(), "processing") == 0

    def test_count_none_value_coerces_to_zero(self) -> None:
        """A ``None`` count coerces to 0 (the ``or 0`` arm)."""
        obj = MagicMock()
        obj.processing = None
        assert anthropic_provider._count(obj, "processing") == 0


class TestCacheTokens:
    """Pin ``_cache_tokens`` attribute names, order, and zero defaulting."""

    def test_returns_read_then_creation_in_order(self) -> None:
        """The tuple is (cache_read, cache_creation), in that exact order."""
        usage = _usage(cache_read=7, cache_creation=3)
        assert AnthropicProvider._cache_tokens(usage) == (7, 3)

    def test_read_uses_cache_read_input_tokens_attribute(self) -> None:
        """``cache_read`` is sourced from ``cache_read_input_tokens`` only."""

        class _Usage:
            cache_read_input_tokens = 9
            cache_creation_input_tokens = 0

        assert AnthropicProvider._cache_tokens(_Usage()) == (9, 0)

    def test_creation_uses_cache_creation_input_tokens_attribute(self) -> None:
        """``cache_creation`` is sourced from ``cache_creation_input_tokens``."""

        class _Usage:
            cache_read_input_tokens = 0
            cache_creation_input_tokens = 5

        assert AnthropicProvider._cache_tokens(_Usage()) == (0, 5)

    def test_missing_attributes_default_to_zero(self) -> None:
        """Absent cache attributes default to exactly (0, 0)."""

        class _Empty:
            pass

        assert AnthropicProvider._cache_tokens(_Empty()) == (0, 0)

    def test_none_values_coerce_to_zero(self) -> None:
        """``None`` cache counts coerce to 0 via the ``or 0`` arms."""
        usage = _usage(cache_read=None, cache_creation=None)
        assert AnthropicProvider._cache_tokens(usage) == (0, 0)


class TestSyncGenerateRequest:
    """Pin the exact request envelope and response mapping of sync generate."""

    def test_request_kwargs_are_exact(self) -> None:
        """``messages.create`` receives the exact model/tokens/system/messages."""
        create = MagicMock(return_value=_full_text_response())
        client_cls, client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.OPUS)

        with patch.object(anthropic_provider, "Anthropic", client_cls, create=True):
            provider.generate("write it", "toml")

        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == ModelConfig.OPUS
        assert kwargs["max_tokens"] == 4096
        assert kwargs["system"] == (
            "Generate toml output. Follow the instructions precisely."
        )
        assert kwargs["messages"] == [{"role": "user", "content": "write it"}]

    def test_system_prompt_embeds_output_format(self) -> None:
        """The system prompt carries the requested format verbatim."""
        create = MagicMock(return_value=_full_text_response())
        client_cls, client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)

        with patch.object(anthropic_provider, "Anthropic", client_cls, create=True):
            provider.generate("p", "bash")

        assert client.messages.create.call_args.kwargs["system"] == (
            "Generate bash output. Follow the instructions precisely."
        )

    def test_sync_client_constructed_with_api_key(self) -> None:
        """The sync client is built with the configured api key."""
        create = MagicMock(return_value=_full_text_response())
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-local", model=ModelConfig.SONNET)

        with patch.object(anthropic_provider, "Anthropic", client_cls, create=True):
            provider.generate("p", "yaml")

        assert (
            client_cls.call_args.kwargs["api_key"]
            == "sk-local"  # pragma: allowlist secret
        )

    def test_response_maps_to_generation_result_fields(self) -> None:
        """Every response field maps to the matching result field exactly."""
        usage = _usage(
            input_tokens=11,
            output_tokens=4,
            cache_read=6,
            cache_creation=2,
        )
        response = _full_text_response(
            "the-body", model="claude-x", message_id="msg_42", usage=usage
        )
        create = MagicMock(return_value=response)
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)

        with patch.object(anthropic_provider, "Anthropic", client_cls, create=True):
            result = provider.generate("p", "yaml")

        assert result.content == "the-body"
        assert result.format == "yaml"
        assert result.token_usage.input_tokens == 11
        assert result.token_usage.output_tokens == 4
        assert result.model == "claude-x"
        assert result.message_id == "msg_42"
        assert result.cache_read_tokens == 6
        assert result.cache_creation_tokens == 2

    def test_uses_first_content_block(self) -> None:
        """The text is taken from ``content[0]``, not a later index."""
        first = MagicMock(spec=TextBlock)
        first.text = "first"
        second = MagicMock(spec=TextBlock)
        second.text = "second"
        response = _full_text_response()
        response.content = [first, second]
        create = MagicMock(return_value=response)
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)

        with patch.object(anthropic_provider, "Anthropic", client_cls, create=True):
            result = provider.generate("p", "yaml")

        assert result.content == "first"

    def test_non_text_first_block_raises_exact_message(self) -> None:
        """A non-TextBlock first block raises with the exact error text."""
        response = MagicMock()
        response.usage = _usage()
        response.content = [MagicMock()]
        create = MagicMock(return_value=response)
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)

        with (
            patch.object(anthropic_provider, "Anthropic", client_cls, create=True),
            pytest.raises(GenerationError) as exc,
        ):
            provider.generate("p", "yaml")
        assert str(exc.value) == "Expected TextBlock in response"

    def test_missing_sdk_propagates_provider_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing extra surfaces as ``ProviderUnavailableError`` from generate."""
        _block_anthropic_import(monkeypatch)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(ProviderUnavailableError, match="requires an optional"):
            provider.generate("p", "yaml")


class TestSyncRetryAndRecording:
    """Pin sync retry counts, backoff sleeps, and telemetry recording."""

    def test_sleeps_exact_backoff_sequence_then_succeeds(
        self, active_report: TimingReport
    ) -> None:
        """Two failures sleep the exact 1s, 2s backoff then a success records."""
        create = MagicMock(
            side_effect=[
                RuntimeError("a"),
                RuntimeError("b"),
                _full_text_response("ok"),
            ]
        )
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=3, retry_delay=1.0
        )

        with (
            patch.object(anthropic_provider, "Anthropic", client_cls, create=True),
            patch(_SYNC_SLEEP) as sleep,
        ):
            result = provider.generate("p", "yaml")

        assert result.content == "ok"
        assert create.call_count == 3
        assert [c.args[0] for c in sleep.call_args_list] == [1.0, 2.0]
        assert active_report.api_calls[0].retries == 2

    def test_exhausts_retries_and_records_failure(
        self, active_report: TimingReport
    ) -> None:
        """All attempts fail: raise exact message and record zero-token call."""
        create = MagicMock(side_effect=RuntimeError("down"))
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=2, retry_delay=0.0
        )

        with (
            patch.object(anthropic_provider, "Anthropic", client_cls, create=True),
            patch(_SYNC_SLEEP),
            pytest.raises(GenerationError) as exc,
        ):
            provider.generate("p", "yaml")

        assert str(exc.value) == "Failed to generate content"
        assert create.call_count == 3
        assert len(active_report.api_calls) == 1
        assert active_report.api_calls[0].input_tokens == 0
        assert active_report.api_calls[0].retries == 2

    def test_first_attempt_success_does_not_sleep(
        self, active_report: TimingReport
    ) -> None:
        """A first-try success makes no retries and zero sleeps."""
        create = MagicMock(return_value=_full_text_response("ok"))
        client_cls, _client = _sync_client_cls(create)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)

        with (
            patch.object(anthropic_provider, "Anthropic", client_cls, create=True),
            patch(_SYNC_SLEEP) as sleep,
        ):
            provider.generate("p", "yaml")

        assert create.call_count == 1
        sleep.assert_not_called()
        assert active_report.api_calls[0].retries == 0


class TestRecordCallBuilder:
    """Pin ``_build_api_call_record`` / ``_record_call`` field math."""

    def test_failure_record_has_zero_tokens_and_attempt_retries(self) -> None:
        """A ``None`` result yields a record with retries=attempt, zero tokens."""
        record = AnthropicProvider._build_api_call_record(0.5, 2, None)
        assert record.retries == 2
        assert record.input_tokens == 0
        assert record.output_tokens == 0
        assert record.cache_read_tokens == 0
        assert record.cache_creation_tokens == 0

    def test_success_record_copies_token_usage(self) -> None:
        """A success record mirrors the result's token and cache counts."""
        result = GenerationResult(
            content="c",
            format="yaml",
            token_usage=TokenUsage(input_tokens=8, output_tokens=3),
            model="m",
            message_id="id",
            cache_read_tokens=4,
            cache_creation_tokens=1,
        )
        record = AnthropicProvider._build_api_call_record(1.0, 1, result)
        assert record.retries == 1
        assert record.input_tokens == 8
        assert record.output_tokens == 3
        assert record.cache_read_tokens == 4
        assert record.cache_creation_tokens == 1

    def test_record_call_noop_when_report_is_none(self) -> None:
        """A ``None`` report records nothing (no exception, no append)."""
        AnthropicProvider._record_call(None, 0.0, 0, None)

    def test_record_call_latency_is_nonnegative_elapsed(
        self, active_report: TimingReport
    ) -> None:
        """Recorded latency is end-minus-start, never negative."""
        start = time.perf_counter()
        AnthropicProvider._record_call(active_report, start, 0, None)
        assert active_report.api_calls[0].latency_s >= 0.0


class TestAsyncGenerateRequest:
    """Pin the async request envelope and response mapping."""

    @pytest.mark.asyncio
    async def test_request_kwargs_are_exact(self) -> None:
        """Async ``messages.create`` receives the exact request envelope."""
        create = AsyncMock(return_value=_full_text_response())
        provider = AnthropicProvider("sk-test", model=ModelConfig.OPUS)
        provider._async_client = _async_client(create)
        try:
            await provider.generate_async("write it", "toml")
        finally:
            await provider.aclose()

        kwargs = create.call_args.kwargs
        assert kwargs["model"] == ModelConfig.OPUS
        assert kwargs["max_tokens"] == 4096
        assert kwargs["system"] == (
            "Generate toml output. Follow the instructions precisely."
        )
        assert kwargs["messages"] == [{"role": "user", "content": "write it"}]

    @pytest.mark.asyncio
    async def test_response_maps_all_fields(self) -> None:
        """Async response fields map onto the result fields exactly."""
        usage = _usage(input_tokens=11, output_tokens=4, cache_read=6, cache_creation=2)
        response = _full_text_response(
            "body", model="claude-y", message_id="msg_99", usage=usage
        )
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(AsyncMock(return_value=response))
        try:
            result = await provider.generate_async("p", "markdown")
        finally:
            await provider.aclose()

        assert result.content == "body"
        assert result.format == "markdown"
        assert result.token_usage.input_tokens == 11
        assert result.token_usage.output_tokens == 4
        assert result.model == "claude-y"
        assert result.message_id == "msg_99"
        assert result.cache_read_tokens == 6
        assert result.cache_creation_tokens == 2

    @pytest.mark.asyncio
    async def test_non_text_block_raises_exact_message(self) -> None:
        """A non-TextBlock first block raises the exact async error text."""
        response = MagicMock()
        response.usage = _usage()
        response.content = [MagicMock()]
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(AsyncMock(return_value=response))
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()
        assert str(exc.value) == "Expected TextBlock in response"

    @pytest.mark.asyncio
    async def test_async_retry_sleeps_then_records_one_call(
        self, active_report: TimingReport
    ) -> None:
        """Async retry sleeps then succeeds, recording retries=1."""
        create = AsyncMock(
            side_effect=[RuntimeError("boom"), _full_text_response("ok")]
        )
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=2, retry_delay=3.0
        )
        provider._async_client = _async_client(create)
        with patch(_ASYNC_SLEEP, AsyncMock()) as sleep:
            try:
                result = await provider.generate_async("p", "yaml")
            finally:
                await provider.aclose()

        assert result.content == "ok"
        assert create.await_count == 2
        assert [c.args[0] for c in sleep.call_args_list] == [3.0]
        assert active_report.api_calls[0].retries == 1


class TestAsyncClientCaching:
    """Pin lazy creation and idempotent close of the async client."""

    def test_async_client_constructed_with_api_key(self) -> None:
        """The lazily-built async client is constructed with the api key."""
        async_cls = MagicMock()
        provider = AnthropicProvider("sk-async", model=ModelConfig.SONNET)
        with patch.object(anthropic_provider, "AsyncAnthropic", async_cls, create=True):
            client = provider._get_async_client()

        assert (
            async_cls.call_args.kwargs["api_key"]
            == "sk-async"  # pragma: allowlist secret
        )
        assert client is async_cls.return_value

    def test_async_client_is_cached_across_calls(self) -> None:
        """The async client is created once and reused on later calls."""
        async_cls = MagicMock()
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with patch.object(anthropic_provider, "AsyncAnthropic", async_cls, create=True):
            first = provider._get_async_client()
            second = provider._get_async_client()

        assert first is second
        assert async_cls.call_count == 1

    @pytest.mark.asyncio
    async def test_aclose_closes_and_clears_client(self) -> None:
        """``aclose`` awaits the client's close and resets the cache to None."""
        close = AsyncMock()
        client = MagicMock()
        client.close = close
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = client

        await provider.aclose()

        close.assert_awaited_once_with()
        assert provider._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_is_noop_when_no_client(self) -> None:
        """``aclose`` with no client neither raises nor sets a truthy value."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        await provider.aclose()
        assert provider._async_client is None


class TestToolUseRequestAndMapping:
    """Pin the tool-use request envelope and response mapping."""

    @pytest.mark.asyncio
    async def test_request_envelope_is_exact(self) -> None:
        """The tool-use call passes the exact model/tokens/system/tools/choice."""
        create = AsyncMock(return_value=_tool_response())
        provider = AnthropicProvider("sk-test", model=ModelConfig.OPUS)
        provider._async_client = _async_client(create)
        system_blocks: list[dict[str, object]] = [{"type": "text", "text": "S"}]
        tool_schema: dict[str, object] = {"name": "report_tuning", "x": 1}
        try:
            await provider.generate_tool_use_async(
                "do it", system_blocks=system_blocks, tool_schema=tool_schema
            )
        finally:
            await provider.aclose()

        kwargs = create.call_args.kwargs
        assert kwargs["model"] == ModelConfig.OPUS
        assert kwargs["max_tokens"] == 4096
        assert kwargs["system"] == [{"type": "text", "text": "S"}]
        assert kwargs["tools"] == [{"name": "report_tuning", "x": 1}]
        assert kwargs["tool_choice"] == {"type": "tool", "name": "report_tuning"}
        assert kwargs["messages"] == [{"role": "user", "content": "do it"}]

    @pytest.mark.asyncio
    async def test_response_maps_to_tool_use_result(self) -> None:
        """The tool block maps onto every ToolUseResult field exactly."""
        usage = _usage(input_tokens=7, output_tokens=2, cache_read=5, cache_creation=1)
        response = _tool_response(
            name="report_tuning",
            tool_input={"a": 1},
            model="claude-z",
            message_id="msg_t",
            usage=usage,
        )
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(AsyncMock(return_value=response))
        try:
            result = await provider.generate_tool_use_async(
                "p",
                system_blocks=[{"type": "text", "text": "S"}],
                tool_schema={"name": "report_tuning"},
            )
        finally:
            await provider.aclose()

        assert result.tool_name == "report_tuning"
        assert result.tool_input == {"a": 1}
        assert result.token_usage.input_tokens == 7
        assert result.token_usage.output_tokens == 2
        assert result.model == "claude-z"
        assert result.message_id == "msg_t"
        assert result.cache_read_tokens == 5
        assert result.cache_creation_tokens == 1

    @pytest.mark.asyncio
    async def test_no_tool_block_raises_exact_message(self) -> None:
        """A response without a tool-use block raises the exact error text."""
        response = MagicMock()
        response.usage = _usage()
        response.content = [MagicMock(spec=TextBlock)]
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(AsyncMock(return_value=response))
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.generate_tool_use_async(
                    "p",
                    system_blocks=[{"type": "text", "text": "S"}],
                    tool_schema={"name": "report_tuning"},
                )
        finally:
            await provider.aclose()
        assert str(exc.value) == "Expected ToolUseBlock in response"

    @pytest.mark.asyncio
    async def test_non_dict_input_raises_exact_message(self) -> None:
        """A non-dict tool ``input`` raises the exact error text."""
        response = _tool_response(tool_input=["not", "a", "dict"])
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _async_client(AsyncMock(return_value=response))
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.generate_tool_use_async(
                    "p",
                    system_blocks=[{"type": "text", "text": "S"}],
                    tool_schema={"name": "report_tuning"},
                )
        finally:
            await provider.aclose()
        assert str(exc.value) == "Tool input was not a JSON object"

    @pytest.mark.asyncio
    async def test_tool_retry_sleeps_then_records(
        self, active_report: TimingReport
    ) -> None:
        """Tool-use retry sleeps the exact delay then records retries=1."""
        create = AsyncMock(side_effect=[RuntimeError("x"), _tool_response()])
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=2, retry_delay=5.0
        )
        provider._async_client = _async_client(create)
        with patch(_ASYNC_SLEEP, AsyncMock()) as sleep:
            try:
                await provider.generate_tool_use_async(
                    "p",
                    system_blocks=[{"type": "text", "text": "S"}],
                    tool_schema={"name": "report_tuning"},
                )
            finally:
                await provider.aclose()

        assert [c.args[0] for c in sleep.call_args_list] == [5.0]
        assert active_report.api_calls[0].retries == 1

    @pytest.mark.asyncio
    async def test_tool_retry_exhaustion_raises_exact_message(self) -> None:
        """Exhausted tool-use retries raise the exact failure message."""
        create = AsyncMock(side_effect=RuntimeError("down"))
        provider = AnthropicProvider(
            "sk-test", model=ModelConfig.SONNET, max_retries=1, retry_delay=0.0
        )
        provider._async_client = _async_client(create)
        with patch(_ASYNC_SLEEP, AsyncMock()):
            try:
                with pytest.raises(GenerationError) as exc:
                    await provider.generate_tool_use_async(
                        "p",
                        system_blocks=[{"type": "text", "text": "S"}],
                        tool_schema={"name": "report_tuning"},
                    )
            finally:
                await provider.aclose()
        assert str(exc.value) == "Failed to generate content"
        assert create.await_count == 2


class TestToolRequestParams:
    """Pin ``_tool_request_params`` body shape and name validation."""

    def test_body_has_exact_keys_and_values(self) -> None:
        """The body carries the exact 6 keys with exact values."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.OPUS)
        system_blocks: list[dict[str, object]] = [{"type": "text", "text": "S"}]
        params = provider._tool_request_params(
            "the-prompt", system_blocks, {"name": "report_tuning"}
        )
        assert set(params) == {
            "model",
            "max_tokens",
            "system",
            "tools",
            "tool_choice",
            "messages",
        }
        assert params["model"] == ModelConfig.OPUS
        assert params["max_tokens"] == 4096
        assert params["system"] == [{"type": "text", "text": "S"}]
        assert params["tools"] == [{"name": "report_tuning"}]
        assert params["tool_choice"] == {"type": "tool", "name": "report_tuning"}
        assert params["messages"] == [{"role": "user", "content": "the-prompt"}]

    def test_system_is_a_copy_not_the_caller_list(self) -> None:
        """``system`` is a defensive copy, decoupled from the caller's list."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        original: list[dict[str, object]] = [{"type": "text", "text": "S"}]
        params = provider._tool_request_params("p", original, {"name": "report_tuning"})
        assert params["system"] == original
        assert params["system"] is not original

    def test_missing_name_raises_without_custom_id_qualifier(self) -> None:
        """A missing tool name raises the exact unqualified error message."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(GenerationError) as exc:
            provider._tool_request_params("p", [], {})
        assert str(exc.value) == ("tool_schema must include a non-empty 'name' string")

    def test_empty_name_string_is_rejected(self) -> None:
        """An empty-string name is rejected (the ``not raw_name`` arm)."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(GenerationError, match="non-empty"):
            provider._tool_request_params("p", [], {"name": ""})

    def test_non_string_name_is_rejected(self) -> None:
        """A non-string name is rejected (the isinstance arm)."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        bad_schema: dict[str, object] = {"name": 123}
        with pytest.raises(GenerationError, match="non-empty"):
            provider._tool_request_params("p", [], bad_schema)

    def test_missing_name_with_custom_id_names_it(self) -> None:
        """A custom_id qualifier is included in the error message verbatim."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(GenerationError) as exc:
            provider._tool_request_params("p", [], {}, custom_id="req-7")
        assert str(exc.value) == (
            "tool_schema for custom_id 'req-7' must include a non-empty "
            "'name' string"
        )


class TestBatchRequestEnvelope:
    """Pin the Batches-API envelope shape for a single request."""

    def test_envelope_has_custom_id_and_params_keys(self) -> None:
        """The envelope wraps the request in exactly custom_id + params."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        request = ToolUseBatchRequest(
            custom_id="req-1",
            prompt="p",
            system_blocks=[{"type": "text", "text": "S"}],
            tool_schema={"name": "report_tuning"},
        )
        envelope = provider._batch_request_envelope(request)
        assert set(envelope) == {"custom_id", "params"}
        assert envelope["custom_id"] == "req-1"
        params = envelope["params"]
        assert isinstance(params, dict)
        assert params["tool_choice"] == {"type": "tool", "name": "report_tuning"}
        assert params["messages"] == [{"role": "user", "content": "p"}]


class TestSubmitToolUseBatch:
    """Pin batch validation, envelope assembly, and submission mapping."""

    def _request(self, custom_id: str) -> ToolUseBatchRequest:
        return ToolUseBatchRequest(
            custom_id=custom_id,
            prompt="p",
            system_blocks=[],
            tool_schema={"name": "report_tuning"},
        )

    @pytest.mark.asyncio
    async def test_submits_envelopes_and_echoes_custom_ids(self) -> None:
        """The SDK receives one envelope per request; ids are echoed in order."""
        batch = MagicMock()
        batch.id = "batch_abc"
        create = AsyncMock(return_value=batch)
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _batch_client(create)
        requests = [self._request("a"), self._request("b")]
        try:
            result = await provider.submit_tool_use_batch(requests)
        finally:
            await provider.aclose()

        sent = create.call_args.kwargs["requests"]
        assert [e["custom_id"] for e in sent] == ["a", "b"]
        assert result.batch_id == "batch_abc"
        assert result.custom_ids == ["a", "b"]

    @pytest.mark.asyncio
    async def test_returned_custom_ids_are_a_copy(self) -> None:
        """The echoed custom_ids list is a copy, not the validator's list."""
        batch = MagicMock()
        batch.id = "b"
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _batch_client(AsyncMock(return_value=batch))
        requests = [self._request("a")]
        try:
            result = await provider.submit_tool_use_batch(requests)
        finally:
            await provider.aclose()
        assert result.custom_ids == ["a"]

    def test_validate_empty_requests_raises_exact_message(self) -> None:
        """Empty input raises the exact at-least-one-request message."""
        with pytest.raises(ValueError, match="at least one request") as exc:
            AnthropicProvider._validate_batch_requests([])
        assert str(exc.value) == ("submit_tool_use_batch requires at least one request")

    def test_validate_duplicate_ids_raises_exact_message(self) -> None:
        """Duplicate custom_ids raise the exact uniqueness message."""
        requests = [self._request("dup"), self._request("dup")]
        with pytest.raises(ValueError, match="unique custom_id values") as exc:
            AnthropicProvider._validate_batch_requests(requests)
        assert str(exc.value) == (
            "submit_tool_use_batch requests must have unique custom_id values"
        )

    def test_validate_returns_ordered_custom_ids(self) -> None:
        """Validation returns the custom_ids in submission order."""
        requests = [self._request("x"), self._request("y"), self._request("z")]
        assert AnthropicProvider._validate_batch_requests(requests) == ["x", "y", "z"]

    @pytest.mark.asyncio
    async def test_sdk_failure_becomes_generation_error(self) -> None:
        """An SDK error during create is remapped to the exact message."""
        create = AsyncMock(side_effect=RuntimeError("nope"))
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _batch_client(create)
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.submit_tool_use_batch([self._request("a")])
        finally:
            await provider.aclose()
        assert str(exc.value) == "Batch submission failed"

    @pytest.mark.asyncio
    async def test_missing_batch_id_defaults_to_empty_string(self) -> None:
        """A batch object lacking ``id`` yields an empty batch_id string."""

        class _NoId:
            pass

        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = _batch_client(AsyncMock(return_value=_NoId()))
        try:
            result = await provider.submit_tool_use_batch([self._request("a")])
        finally:
            await provider.aclose()
        assert isinstance(result.batch_id, str)
        assert not result.batch_id


class TestPollBatch:
    """Pin batch_id validation and the poll-snapshot field mapping."""

    @pytest.mark.asyncio
    async def test_empty_batch_id_raises_exact_message(self) -> None:
        """An empty batch id raises the exact poll_batch message."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(ValueError, match="non-empty batch_id") as exc:
            await provider.poll_batch("")
        assert str(exc.value) == "poll_batch requires a non-empty batch_id"

    @pytest.mark.asyncio
    async def test_poll_maps_status_and_each_count(self) -> None:
        """Each per-state count and the status map to the exact field."""
        batch = MagicMock()
        batch.processing_status = "in_progress"
        batch.request_counts.processing = 1
        batch.request_counts.succeeded = 2
        batch.request_counts.errored = 3
        batch.request_counts.canceled = 4
        batch.request_counts.expired = 5
        client = MagicMock()
        client.messages.batches.retrieve = AsyncMock(return_value=batch)
        client.close = AsyncMock()
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = client
        try:
            poll = await provider.poll_batch("b1")
        finally:
            await provider.aclose()

        assert poll.batch_id == "b1"
        assert poll.status == "in_progress"
        assert poll.processing_count == 1
        assert poll.succeeded_count == 2
        assert poll.errored_count == 3
        assert poll.canceled_count == 4
        assert poll.expired_count == 5

    def test_poll_from_response_defaults_missing_status_to_empty(self) -> None:
        """A response without ``processing_status`` yields an empty status."""

        class _NoStatus:
            request_counts = None

        poll = AnthropicProvider._batch_poll_from_response("b1", _NoStatus())
        assert isinstance(poll.status, str)
        assert not poll.status
        assert poll.processing_count == 0
        assert poll.succeeded_count == 0

    @pytest.mark.asyncio
    async def test_retrieve_failure_becomes_generation_error(self) -> None:
        """An SDK retrieve error is remapped to the exact message."""
        client = MagicMock()
        client.messages.batches.retrieve = AsyncMock(side_effect=RuntimeError("x"))
        client.close = AsyncMock()
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = client
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.poll_batch("b1")
        finally:
            await provider.aclose()
        assert str(exc.value) == "Batch retrieve failed for b1"


class TestFetchBatchResults:
    """Pin batch_id validation, success/failure routing, and stream errors."""

    @pytest.mark.asyncio
    async def test_empty_batch_id_raises_exact_message(self) -> None:
        """An empty batch id raises the exact fetch_batch_results message."""
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        with pytest.raises(ValueError, match="non-empty batch_id") as exc:
            await provider.fetch_batch_results("")
        assert str(exc.value) == ("fetch_batch_results requires a non-empty batch_id")

    @pytest.mark.asyncio
    async def test_successes_and_failures_routed_by_custom_id(self) -> None:
        """Success entries land in successes; non-success in failures."""
        stream = [
            {
                "custom_id": "ok",
                "result": {
                    "type": "succeeded",
                    "message": {
                        "id": "m",
                        "model": "claude",
                        "content": [
                            {
                                "type": "tool_use",
                                "name": "report_tuning",
                                "input": {"k": "v"},
                            }
                        ],
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    },
                },
            },
            {
                "custom_id": "bad",
                "result": {"type": "errored", "error": {"message": "boom"}},
            },
        ]
        client = MagicMock()
        client.messages.batches.results = AsyncMock(return_value=stream)
        client.close = AsyncMock()
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = client
        try:
            bundle = await provider.fetch_batch_results("b1")
        finally:
            await provider.aclose()

        assert set(bundle.successes) == {"ok"}
        assert set(bundle.failures) == {"bad"}
        assert isinstance(bundle.successes["ok"], ToolUseResult)
        assert isinstance(bundle.failures["bad"], BatchError)

    @pytest.mark.asyncio
    async def test_results_stream_failure_becomes_generation_error(self) -> None:
        """An SDK results error is remapped to the exact message."""
        client = MagicMock()
        client.messages.batches.results = AsyncMock(side_effect=RuntimeError("x"))
        client.close = AsyncMock()
        provider = AnthropicProvider("sk-test", model=ModelConfig.SONNET)
        provider._async_client = client
        try:
            with pytest.raises(GenerationError) as exc:
                await provider.fetch_batch_results("b1")
        finally:
            await provider.aclose()
        assert str(exc.value) == "Batch results stream failed for b1"
