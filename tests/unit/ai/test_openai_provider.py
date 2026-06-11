"""Unit tests for the OpenAI-compatible provider (tracer T3, #385).

Pins the second concrete :class:`LLMProvider` implementation:

* ``OpenAIProvider`` satisfies the full interface with no I/O at
  construction time.
* Completion and tool-use round-trip through the provider-neutral
  request/response types (Anthropic-shaped ``system_blocks`` /
  ``tool_schema`` in, :class:`GenerationResult` /
  :class:`ToolUseResult` out) against a mocked SDK — no live network.
* The base URL for local/OSS OpenAI-compatible servers plumbs through
  from the constructor or ``OPENAI_BASE_URL``.
* Batch capabilities are honestly declared unsupported via the typed
  :class:`UnsupportedCapabilityError`.
* The module imports — and ``build_provider("openai")`` constructs —
  without the optional ``openai`` extra installed; only *using* the
  provider requires it, and then with an actionable install hint.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from start_green_stay_green.ai.batch import ToolUseBatchRequest
from start_green_stay_green.ai.provider_selection import ProviderUnavailableError
from start_green_stay_green.ai.providers import LLMProvider
from start_green_stay_green.ai.providers import OpenAIProvider
from start_green_stay_green.ai.providers import UnsupportedCapabilityError
from start_green_stay_green.ai.providers import openai_provider
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import GenerationResult
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.utils.timing import TimingReport
from start_green_stay_green.utils.timing import set_active_report

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterator

_MODEL = "gpt-5.5"


def _completion_response(
    content: str | None = "hello",
    *,
    cached_tokens: int = 0,
) -> MagicMock:
    """Build a mock Chat Completions response carrying text content."""
    response = MagicMock()
    response.id = "chatcmpl-1"
    response.model = _MODEL
    response.usage.prompt_tokens = 11
    response.usage.completion_tokens = 4
    response.usage.prompt_tokens_details.cached_tokens = cached_tokens
    message = MagicMock()
    message.content = content
    message.tool_calls = None
    choice = MagicMock()
    choice.message = message
    response.choices = [choice]
    return response


def _tool_call_response(
    name: str = "report_tuning",
    arguments: object = '{"k": "v"}',
) -> MagicMock:
    """Build a mock Chat Completions response carrying one tool call."""
    response = _completion_response(content=None)
    call = MagicMock()
    call.function.name = name
    call.function.arguments = arguments
    response.choices[0].message.tool_calls = [call]
    return response


def _sync_client_cls(create: MagicMock) -> tuple[MagicMock, MagicMock]:
    """Build a mock ``OpenAI`` class whose context manager yields a client.

    Returns:
        ``(client_cls, client)`` so tests can assert on both the
        constructor kwargs and the ``create`` call.
    """
    client = MagicMock()
    client.chat.completions.create = create
    client_cls = MagicMock()
    client_cls.return_value.__enter__.return_value = client
    client_cls.return_value.__exit__.return_value = False
    return client_cls, client


def _async_client(create: AsyncMock) -> MagicMock:
    """Build a mock ``AsyncOpenAI`` client with awaitable create/close."""
    client = MagicMock()
    client.chat.completions.create = create
    client.close = AsyncMock()
    return client


def _block_openai_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make resolving the ``openai`` SDK raise ``ModuleNotFoundError``.

    Simulates the optional extra being absent without uninstalling it
    from the test environment, mirroring the Anthropic-extra tests:
    the provider's lazy seam resolves the SDK through
    :func:`importlib.import_module`, so patching that to reject
    ``openai`` faithfully reproduces a missing extra.
    """
    real_import_module: Callable[..., object] = importlib.import_module

    def _fake_import_module(name: str, *args: object, **kwargs: object) -> object:
        if name == "openai" or name.startswith("openai."):
            msg = "No module named 'openai'"
            raise ModuleNotFoundError(msg)
        return real_import_module(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", _fake_import_module)


@pytest.fixture
def active_report() -> Iterator[TimingReport]:
    """Install a fresh ``TimingReport`` for the test, then clear it."""
    report = TimingReport()
    set_active_report(report)
    try:
        yield report
    finally:
        set_active_report(None)


@pytest.fixture
def no_base_url_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure ``OPENAI_BASE_URL`` is unset so tests are hermetic."""
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


class TestOpenAIProviderSatisfiesInterface:
    """``OpenAIProvider`` must be a concrete, no-I/O ``LLMProvider``."""

    def test_is_subclass_of_llm_provider(self) -> None:
        """The provider subclasses the abstract interface."""
        assert issubclass(OpenAIProvider, LLMProvider)

    def test_instance_is_an_llm_provider(self) -> None:
        """A constructed provider satisfies isinstance checks."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        assert isinstance(provider, LLMProvider)

    def test_implements_every_abstract_method(self) -> None:
        """No abstract methods remain unimplemented."""
        assert not OpenAIProvider.__abstractmethods__

    def test_model_property_returns_configured_id(self) -> None:
        """``model`` echoes the constructor argument verbatim."""
        provider = OpenAIProvider("sk-test", model="local-llama")
        assert provider.model == "local-llama"

    def test_construction_performs_no_io(self) -> None:
        """Constructing the provider allocates no network client."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        assert provider._async_client is None

    def test_default_retry_policy_matches_anthropic_provider(self) -> None:
        """Retry defaults stay consistent across providers."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        assert provider.max_retries == 3
        assert provider.retry_delay == 1.0

    def test_retry_schedule_is_exponential_and_last_has_no_sleep(self) -> None:
        """The schedule doubles the delay and ends with ``None``."""
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=2, retry_delay=1.5
        )
        schedule = list(provider._retry_schedule())
        assert schedule == [(0, 1.5), (1, 3.0), (2, None)]


class TestSyncGenerate:
    """Sync completion maps the Chat Completions response faithfully."""

    @pytest.mark.usefixtures("no_base_url_env")
    def test_returns_mapped_generation_result(self) -> None:
        """Content, token usage, model, and id all round-trip."""
        create = MagicMock(return_value=_completion_response("hi", cached_tokens=3))
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            result = provider.generate("p", "yaml")

        assert isinstance(result, GenerationResult)
        assert result.content == "hi"
        assert result.format == "yaml"
        assert result.token_usage.input_tokens == 11
        assert result.token_usage.output_tokens == 4
        assert result.token_usage.total_tokens == 15
        assert result.cache_read_tokens == 3
        assert result.cache_creation_tokens == 0
        assert result.model == _MODEL
        assert result.message_id == "chatcmpl-1"

    @pytest.mark.usefixtures("no_base_url_env")
    def test_sends_system_and_user_messages(self) -> None:
        """The request carries the format system prompt and the user prompt."""
        create = MagicMock(return_value=_completion_response())
        client_cls, client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("write it", "toml")

        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == _MODEL
        assert kwargs["max_tokens"] == 4096
        assert kwargs["messages"] == [
            {
                "role": "system",
                "content": ("Generate toml output. Follow the instructions precisely."),
            },
            {"role": "user", "content": "write it"},
        ]

    @pytest.mark.usefixtures("no_base_url_env")
    def test_client_receives_api_key(self) -> None:
        """The sync client is constructed with the configured key."""
        create = MagicMock(return_value=_completion_response())
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-local", model=_MODEL)

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("p", "yaml")

        assert (
            client_cls.call_args.kwargs["api_key"]
            == "sk-local"  # pragma: allowlist secret
        )

    @pytest.mark.usefixtures("no_base_url_env")
    def test_missing_text_content_raises(self) -> None:
        """A ``None`` message content is a hard error, not a retry."""
        create = MagicMock(return_value=_completion_response(content=None))
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with (
            patch.object(openai_provider, "OpenAI", client_cls, create=True),
            pytest.raises(GenerationError, match="Expected text content"),
        ):
            provider.generate("p", "yaml")

    @pytest.mark.usefixtures("no_base_url_env")
    def test_empty_choices_raises(self) -> None:
        """A response with no choices is rejected."""
        response = _completion_response()
        response.choices = []
        create = MagicMock(return_value=response)
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with (
            patch.object(openai_provider, "OpenAI", client_cls, create=True),
            pytest.raises(GenerationError, match="no choices"),
        ):
            provider.generate("p", "yaml")

    @pytest.mark.usefixtures("no_base_url_env")
    def test_retries_then_succeeds(self) -> None:
        """A transient failure is retried, then the success returned."""
        create = MagicMock(
            side_effect=[RuntimeError("boom"), _completion_response("ok")],
        )
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=2, retry_delay=0.0
        )

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            result = provider.generate("p", "yaml")

        assert result.content == "ok"
        assert create.call_count == 2

    @pytest.mark.usefixtures("no_base_url_env")
    def test_exhausted_retries_raise_with_cause(
        self, active_report: TimingReport
    ) -> None:
        """Persistent failure raises and records a zero-token call."""
        boom = RuntimeError("always down")
        create = MagicMock(side_effect=boom)
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=0, retry_delay=0.001
        )

        with (
            patch.object(openai_provider, "OpenAI", client_cls, create=True),
            pytest.raises(GenerationError, match="Failed to generate content") as exc,
        ):
            provider.generate("p", "yaml")

        assert exc.value.cause is boom
        assert len(active_report.api_calls) == 1
        assert active_report.api_calls[0].input_tokens == 0

    @pytest.mark.usefixtures("no_base_url_env")
    def test_success_records_token_telemetry(self, active_report: TimingReport) -> None:
        """A successful call records its token counts on the report."""
        create = MagicMock(return_value=_completion_response(cached_tokens=2))
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("p", "yaml")

        assert len(active_report.api_calls) == 1
        record = active_report.api_calls[0]
        assert record.input_tokens == 11
        assert record.output_tokens == 4
        assert record.cache_read_tokens == 2


class TestAsyncGenerate:
    """Async completion mirrors the sync mapping over a cached client."""

    @pytest.mark.asyncio
    async def test_returns_mapped_generation_result(self) -> None:
        """A successful async call yields a populated result."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(
            AsyncMock(return_value=_completion_response("hello"))
        )
        try:
            result = await provider.generate_async("p", "markdown")
        finally:
            await provider.aclose()

        assert isinstance(result, GenerationResult)
        assert result.content == "hello"
        assert result.format == "markdown"
        assert result.token_usage.input_tokens == 11

    @pytest.mark.asyncio
    async def test_retries_then_succeeds(self) -> None:
        """The async retry loop recovers from a transient failure."""
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=2, retry_delay=0.0
        )
        provider._async_client = _async_client(
            AsyncMock(side_effect=[RuntimeError("boom"), _completion_response("ok")]),
        )
        try:
            result = await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()

        assert result.content == "ok"

    @pytest.mark.asyncio
    async def test_exhausted_retries_raise(self, active_report: TimingReport) -> None:
        """Persistent async failure raises and records a failure call."""
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=0, retry_delay=0.001
        )
        provider._async_client = _async_client(
            AsyncMock(side_effect=RuntimeError("down"))
        )

        try:
            with pytest.raises(GenerationError, match="Failed to generate content"):
                await provider.generate_async("p", "yaml")
        finally:
            await provider.aclose()

        assert len(active_report.api_calls) == 1
        assert active_report.api_calls[0].input_tokens == 0

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("no_base_url_env")
    async def test_async_client_is_created_once_and_reused(self) -> None:
        """The async client is cached across calls (shared pool)."""
        create = AsyncMock(return_value=_completion_response())
        client = _async_client(create)
        client_cls = MagicMock(return_value=client)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with patch.object(openai_provider, "AsyncOpenAI", client_cls, create=True):
            try:
                await provider.generate_async("p", "yaml")
                await provider.generate_async("p", "yaml")
            finally:
                await provider.aclose()

        assert client_cls.call_count == 1
        assert (
            client_cls.call_args.kwargs["api_key"]
            == "sk-test"  # pragma: allowlist secret
        )


class TestToolUse:
    """Tool-use round-trips through the provider-neutral types."""

    @pytest.mark.asyncio
    async def test_tool_use_round_trip(self) -> None:
        """The neutral tool schema and result translate both ways."""
        create = AsyncMock(
            return_value=_tool_call_response(
                "report_tuning", json.dumps({"tuned_content": "x", "changes": []})
            )
        )
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            result = await provider.generate_tool_use_async(
                "tune this",
                system_blocks=[
                    {
                        "type": "text",
                        "text": "You are a tuner.",
                        "cache_control": {"type": "ephemeral"},
                    },
                ],
                tool_schema={
                    "name": "report_tuning",
                    "description": "Report the tuned content.",
                    "input_schema": {
                        "type": "object",
                        "properties": {"tuned_content": {"type": "string"}},
                        "required": ["tuned_content"],
                    },
                },
            )
        finally:
            await provider.aclose()

        assert isinstance(result, ToolUseResult)
        assert result.tool_name == "report_tuning"
        assert result.tool_input == {"tuned_content": "x", "changes": []}
        assert result.token_usage.input_tokens == 11
        assert result.model == _MODEL
        assert result.message_id == "chatcmpl-1"

        kwargs = create.call_args.kwargs
        assert kwargs["tools"] == [
            {
                "type": "function",
                "function": {
                    "name": "report_tuning",
                    "description": "Report the tuned content.",
                    "parameters": {
                        "type": "object",
                        "properties": {"tuned_content": {"type": "string"}},
                        "required": ["tuned_content"],
                    },
                },
            },
        ]
        assert kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "report_tuning"},
        }
        # ``cache_control`` is Anthropic-specific and must not leak into
        # the OpenAI request; the block text becomes the system message.
        assert kwargs["messages"][0] == {
            "role": "system",
            "content": "You are a tuner.",
        }
        assert kwargs["messages"][1] == {"role": "user", "content": "tune this"}

    @pytest.mark.asyncio
    async def test_multiple_system_blocks_are_joined(self) -> None:
        """Several system blocks collapse into one system message."""
        create = AsyncMock(return_value=_tool_call_response())
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            await provider.generate_tool_use_async(
                "p",
                system_blocks=[
                    {"type": "text", "text": "First."},
                    {"type": "text", "text": "Second."},
                ],
                tool_schema={"name": "report_tuning"},
            )
        finally:
            await provider.aclose()

        kwargs = create.call_args.kwargs
        assert kwargs["messages"][0] == {
            "role": "system",
            "content": "First.\n\nSecond.",
        }

    @pytest.mark.asyncio
    async def test_empty_system_blocks_send_no_system_message(self) -> None:
        """No system message is sent when there is nothing to say."""
        create = AsyncMock(return_value=_tool_call_response())
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            await provider.generate_tool_use_async(
                "p",
                system_blocks=[],
                tool_schema={"name": "report_tuning"},
            )
        finally:
            await provider.aclose()

        kwargs = create.call_args.kwargs
        assert kwargs["messages"] == [{"role": "user", "content": "p"}]

    @pytest.mark.asyncio
    async def test_missing_tool_name_raises(self) -> None:
        """A schema without a non-empty name fails before any request."""
        create = AsyncMock(return_value=_tool_call_response())
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            with pytest.raises(GenerationError, match="non-empty 'name'"):
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": ""}
                )
        finally:
            await provider.aclose()
        create.assert_not_called()

    @pytest.mark.asyncio
    async def test_response_without_tool_call_raises(self) -> None:
        """A response lacking tool calls is a hard error."""
        create = AsyncMock(return_value=_completion_response("just text"))
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            with pytest.raises(GenerationError, match="Expected a tool call"):
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": "report_tuning"}
                )
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_invalid_json_arguments_raise_with_cause(self) -> None:
        """Malformed JSON arguments surface as a chained GenerationError."""
        create = AsyncMock(
            return_value=_tool_call_response(arguments="{not json"),
        )
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            with pytest.raises(GenerationError, match="not valid JSON") as exc:
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": "report_tuning"}
                )
        finally:
            await provider.aclose()
        assert isinstance(exc.value.cause, json.JSONDecodeError)

    @pytest.mark.asyncio
    async def test_non_object_json_arguments_raise(self) -> None:
        """A JSON array payload is rejected like Anthropic's non-dict input."""
        create = AsyncMock(
            return_value=_tool_call_response(arguments='["not", "a", "dict"]'),
        )
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            with pytest.raises(GenerationError, match="not a JSON object"):
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": "report_tuning"}
                )
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_non_string_arguments_raise(self) -> None:
        """Arguments that are not a JSON string are rejected."""
        create = AsyncMock(return_value=_tool_call_response(arguments=None))
        provider = OpenAIProvider("sk-test", model=_MODEL)
        provider._async_client = _async_client(create)

        try:
            with pytest.raises(GenerationError, match="not a JSON string"):
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": "report_tuning"}
                )
        finally:
            await provider.aclose()

    @pytest.mark.asyncio
    async def test_tool_use_retries_then_raises_on_exhaustion(self) -> None:
        """The tool-use retry loop raises when retries run out."""
        provider = OpenAIProvider(
            "sk-test", model=_MODEL, max_retries=1, retry_delay=0.0
        )
        provider._async_client = _async_client(
            AsyncMock(side_effect=RuntimeError("down"))
        )

        try:
            with pytest.raises(GenerationError, match="Failed to generate content"):
                await provider.generate_tool_use_async(
                    "p", system_blocks=[], tool_schema={"name": "report_tuning"}
                )
        finally:
            await provider.aclose()


class TestBaseURL:
    """The endpoint override plumbs through for local/OSS servers."""

    def test_constructor_base_url_reaches_sync_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit ``base_url`` wins over the environment."""
        monkeypatch.setenv("OPENAI_BASE_URL", "http://env.example/v1")
        create = MagicMock(return_value=_completion_response())
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider(
            "sk-local", model="llama3", base_url="http://localhost:11434/v1"
        )

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("p", "yaml")

        assert client_cls.call_args.kwargs["base_url"] == "http://localhost:11434/v1"

    def test_env_base_url_used_when_constructor_omits_it(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``OPENAI_BASE_URL`` applies when no explicit override is given."""
        monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
        create = MagicMock(return_value=_completion_response())
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-local", model="llama3")

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("p", "yaml")

        assert client_cls.call_args.kwargs["base_url"] == "http://localhost:8000/v1"

    @pytest.mark.usefixtures("no_base_url_env")
    def test_default_base_url_is_none(self) -> None:
        """Without any override the SDK default endpoint is used."""
        create = MagicMock(return_value=_completion_response())
        client_cls, _client = _sync_client_cls(create)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with patch.object(openai_provider, "OpenAI", client_cls, create=True):
            provider.generate("p", "yaml")

        assert client_cls.call_args.kwargs["base_url"] is None

    @pytest.mark.asyncio
    async def test_base_url_reaches_async_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The cached async client honors the same override."""
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        create = AsyncMock(return_value=_completion_response())
        client = _async_client(create)
        client_cls = MagicMock(return_value=client)
        provider = OpenAIProvider(
            "sk-local", model="llama3", base_url="http://localhost:1234/v1"
        )

        with patch.object(openai_provider, "AsyncOpenAI", client_cls, create=True):
            try:
                await provider.generate_async("p", "yaml")
            finally:
                await provider.aclose()

        assert client_cls.call_args.kwargs["base_url"] == "http://localhost:1234/v1"


class TestBatchUnsupported:
    """Batch is Anthropic-specific; this provider declines it honestly."""

    @pytest.mark.asyncio
    async def test_submit_tool_use_batch_raises_typed_error(self) -> None:
        """Submitting a batch raises the typed capability error."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        request = ToolUseBatchRequest(
            custom_id="a",
            prompt="p",
            system_blocks=[],
            tool_schema={"name": "report_tuning"},
        )
        with pytest.raises(UnsupportedCapabilityError, match="batch"):
            await provider.submit_tool_use_batch([request])

    @pytest.mark.asyncio
    async def test_poll_batch_raises_typed_error(self) -> None:
        """Polling a batch raises the typed capability error."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        with pytest.raises(UnsupportedCapabilityError, match="batch"):
            await provider.poll_batch("b1")

    @pytest.mark.asyncio
    async def test_fetch_batch_results_raises_typed_error(self) -> None:
        """Fetching batch results raises the typed capability error."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        with pytest.raises(UnsupportedCapabilityError, match="batch"):
            await provider.fetch_batch_results("b1")

    @pytest.mark.asyncio
    async def test_error_names_provider_and_capability(self) -> None:
        """The error is introspectable for T5 capability negotiation."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        with pytest.raises(UnsupportedCapabilityError) as exc:
            await provider.poll_batch("b1")
        assert exc.value.provider == "openai"
        assert exc.value.capability == "batch tool-use"
        assert "openai" in str(exc.value)

    def test_error_is_a_not_implemented_error(self) -> None:
        """Callers catching ``NotImplementedError`` still catch it."""
        assert issubclass(UnsupportedCapabilityError, NotImplementedError)

    @pytest.mark.asyncio
    async def test_empty_batch_submission_raises_value_error(self) -> None:
        """The interface's input contract is honored before declining."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        with pytest.raises(ValueError, match="at least one request"):
            await provider.submit_tool_use_batch([])

    @pytest.mark.asyncio
    async def test_empty_batch_id_raises_value_error(self) -> None:
        """Empty ids fail with the interface's ValueError, not the decline."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        with pytest.raises(ValueError, match="poll_batch requires"):
            await provider.poll_batch("")
        with pytest.raises(ValueError, match="fetch_batch_results requires"):
            await provider.fetch_batch_results("")


class TestMissingExtra:
    """The ``openai`` package is optional; absence is reported actionably."""

    def test_generate_without_extra_raises_install_hint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Using the provider without the SDK yields a pip install hint."""
        _block_openai_import(monkeypatch)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with pytest.raises(ProviderUnavailableError) as exc:
            provider.generate("hello", "yaml")

        message = str(exc.value)
        assert "pip install" in message
        assert "openai" in message
        assert isinstance(exc.value.__cause__, ImportError)

    @pytest.mark.asyncio
    async def test_generate_async_without_extra_raises_install_hint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The async path reports the missing extra the same way."""
        _block_openai_import(monkeypatch)
        provider = OpenAIProvider("sk-test", model=_MODEL)

        with pytest.raises(ProviderUnavailableError, match="pip install"):
            await provider.generate_async("hello", "yaml")

    def test_unknown_module_attribute_raises_attribute_error(self) -> None:
        """The lazy seam only resolves known SDK exports."""
        with pytest.raises(AttributeError, match="has no attribute"):
            _ = openai_provider.NotAnExport

    def test_core_imports_cleanly_with_openai_absent(self) -> None:
        """Importing the package and building the provider needs no SDK.

        Runs in a subprocess with a meta-path finder that blocks the
        ``openai`` package entirely, proving the module performs no
        top-level SDK import (hermetic — no network involved).
        """
        code = (
            "import sys\n"
            "import importlib.abc\n"
            "class _Block(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name == 'openai' or name.startswith('openai.'):\n"
            "            raise ModuleNotFoundError(name)\n"
            "        return None\n"
            "sys.meta_path.insert(0, _Block())\n"
            "import start_green_stay_green\n"
            "from start_green_stay_green.ai.provider_selection import "
            "build_provider\n"
            "provider = build_provider('openai', api_key='dummy', model='m')\n"
            "print(provider.model)\n"
        )
        completed = subprocess.run(  # noqa: S603 — fixed argv, our interpreter
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == "m"


class TestAclose:
    """Lifecycle: the cached async client is released idempotently."""

    @pytest.mark.asyncio
    async def test_aclose_without_client_is_safe(self) -> None:
        """``aclose`` is a no-op when no async work happened."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        await provider.aclose()
        assert provider._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_closes_and_clears_cached_client(self) -> None:
        """``aclose`` closes the cached client and forgets it."""
        provider = OpenAIProvider("sk-test", model=_MODEL)
        client = _async_client(AsyncMock())
        provider._async_client = client

        await provider.aclose()
        await provider.aclose()  # idempotent

        client.close.assert_awaited_once()
        assert provider._async_client is None
