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

import inspect
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from anthropic.types import TextBlock
from anthropic.types import ToolUseBlock
import pytest

from start_green_stay_green.ai.batch import BatchPoll
from start_green_stay_green.ai.batch import BatchResultsBundle
from start_green_stay_green.ai.batch import BatchSubmission
from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.providers import AnthropicProvider
from start_green_stay_green.ai.providers import LLMProvider
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
