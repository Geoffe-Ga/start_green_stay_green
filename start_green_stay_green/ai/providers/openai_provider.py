"""OpenAI-compatible :class:`LLMProvider` implementation (tracer T3, #385).

Second concrete provider behind the seam tracer T1 (#381) introduced,
mapping the provider-neutral request/response types onto the OpenAI
Chat Completions API (``chat.completions.create`` with function
tools). Because the request shape is the de-facto standard for
local/OSS inference servers (Ollama, vLLM, LM Studio, llama.cpp,
…), one **base URL override** makes this provider cover all of them:

* Pass ``base_url=...`` to the constructor, or set the
  ``OPENAI_BASE_URL`` environment variable (the constructor argument
  wins). Unset, the SDK's default ``https://api.openai.com/v1`` is
  used.
* The API key is resolved by the selection layer from
  ``OPENAI_API_KEY``. Local servers usually ignore it, so any
  non-empty dummy value (e.g. ``OPENAI_API_KEY=local``) is fine.

Like the Anthropic provider, the ``openai`` SDK is an *optional*
install extra (``pip install 'start-green-stay-green[openai]'``).
Every SDK reference is imported lazily through the module
:func:`__getattr__` seam — never at module import time — so
``import start_green_stay_green`` and ``green --help`` work without
the extra installed; a missing extra surfaces as an actionable
:class:`~start_green_stay_green.ai.provider_selection.ProviderUnavailableError`
when a generation method first runs.

Capability notes:

* **Batch** is Anthropic-specific (Message Batches API); the three
  batch methods honestly decline with a typed
  :class:`~start_green_stay_green.ai.providers.base.UnsupportedCapabilityError`
  (capability negotiation/fallback is tracer T5, #389).
* **Caching telemetry**: OpenAI prompt caching is automatic and only
  reports *read* hits (``usage.prompt_tokens_details.cached_tokens``);
  there is no cache-write count, so ``cache_creation_tokens`` is
  always ``0``. The Anthropic-specific ``cache_control`` markers on
  system blocks are dropped during translation.
* **Stop reasons** are not part of the neutral result types (the
  orchestrator consumes content/tool-input, token usage, model, and
  message id only); the forced ``tool_choice`` guarantees a tool call
  on the structured path, mirroring the Anthropic contract.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Final
from typing import Never
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

from start_green_stay_green.ai.providers.base import LLMProvider
from start_green_stay_green.ai.providers.base import OutputFormat
from start_green_stay_green.ai.providers.base import UnsupportedCapabilityError
from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.ai.types import GenerationResult
from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import get_active_report

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from collections.abc import Iterator
    from collections.abc import Sequence

    from openai import AsyncOpenAI
    from openai import OpenAI

    from start_green_stay_green.ai.batch import BatchPoll
    from start_green_stay_green.ai.batch import BatchResultsBundle
    from start_green_stay_green.ai.batch import BatchSubmission
    from start_green_stay_green.ai.batch import ToolUseBatchRequest
    from start_green_stay_green.utils.timing import TimingReport

__all__ = ["OpenAIProvider"]

# ``pip`` extra that installs the SDK; named in the missing-dependency
# hint so users can copy/paste the fix.
_INSTALL_EXTRA: Final[str] = "openai"

# Registry name of this provider, echoed in capability errors.
_PROVIDER_NAME: Final[str] = "openai"

# Environment variable supplying the endpoint override for local/OSS
# OpenAI-compatible servers (e.g. ``http://localhost:11434/v1`` for
# Ollama). A constructor ``base_url`` argument takes precedence.
ENV_BASE_URL: Final[str] = "OPENAI_BASE_URL"

# Per-call max_tokens for every request this provider issues — same
# value the Anthropic provider uses, so swapping providers does not
# silently change output budgets. ``max_tokens`` (not the newer
# ``max_completion_tokens``) is used deliberately: it is the field
# local/OSS OpenAI-compatible servers universally accept.
_MAX_TOKENS: Final[int] = 4096

# Names this module exposes lazily from the ``openai`` SDK via
# :func:`__getattr__`. Resolved on first *attribute* access
# (``openai_provider.OpenAI``) rather than at import time, so the
# module imports without the optional extra. ``unittest.mock.patch``
# targets these exact attribute paths, so the lazy seam is also the
# test seam.
_SDK_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "OpenAI": ("openai", "OpenAI"),
    "AsyncOpenAI": ("openai", "AsyncOpenAI"),
}

# Retry loops are generic over the two neutral result types so the
# free-form and tool-use paths share one driver instead of three
# near-identical copies.
_ResultT = TypeVar("_ResultT", GenerationResult, ToolUseResult)


def _raise_missing_sdk(exc: ImportError) -> Never:
    """Re-raise an SDK ``ImportError`` as an actionable error.

    The ``openai`` SDK is an optional install extra. When a provider
    method needs it but it is absent, surface a
    :class:`~start_green_stay_green.ai.provider_selection.ProviderUnavailableError`
    carrying a ``pip install`` hint instead of a bare "No module named
    'openai'". The triggering :class:`ImportError` is chained.

    Args:
        exc: The original import failure.

    Raises:
        ProviderUnavailableError: Always.
    """
    from start_green_stay_green.ai.provider_selection import (  # noqa: PLC0415 — lazy to avoid an import cycle
        ProviderUnavailableError,
    )

    msg = (
        f"The {_INSTALL_EXTRA!r} provider requires an optional dependency "
        f"that is not installed. Install it with: "
        f"pip install 'start-green-stay-green[{_INSTALL_EXTRA}]'"
    )
    raise ProviderUnavailableError(msg) from exc


def __getattr__(name: str) -> object:
    """Lazily resolve SDK names off the optional ``openai`` extra.

    Implements PEP 562 module-level attribute access so
    ``openai_provider.OpenAI`` (and the other entries in
    :data:`_SDK_EXPORTS`) import the SDK on first use rather than at
    module import time. A missing extra is reported as an actionable
    :class:`ProviderUnavailableError`, never a raw :class:`ImportError`.

    Args:
        name: The attribute being accessed on the module.

    Returns:
        The requested SDK object.

    Raises:
        AttributeError: If ``name`` is not a known SDK export.
        ProviderUnavailableError: If the SDK extra is not installed.
    """
    target = _SDK_EXPORTS.get(name)
    if target is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    module_name, attr = target
    from importlib import (  # noqa: PLC0415 — lazy, keeps import cost off hot path
        import_module,
    )

    try:
        module = import_module(module_name)
    except ImportError as exc:
        _raise_missing_sdk(exc)
    return getattr(module, attr)


def _sdk_attr(name: str) -> object:
    """Fetch an SDK export off *this module*, honoring any test patch.

    Reading through ``sys.modules[__name__]`` means a
    ``unittest.mock.patch("...openai_provider.OpenAI")`` (which sets
    the attribute in the module ``__dict__``) is found first, and
    otherwise :func:`__getattr__` resolves the real SDK lazily. This
    keeps the lazy-import seam and the test seam one and the same.
    """
    return getattr(sys.modules[__name__], name)


def _usage_tokens(usage: object) -> TokenUsage:
    """Map the Chat Completions ``usage`` object to :class:`TokenUsage`.

    ``usage`` can be ``None`` (some compatible servers omit it) and
    its counts can be ``None``; coerce to ``int`` so downstream
    telemetry never has to defend against missing fields.
    """
    return TokenUsage(
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
    )


def _cached_tokens(usage: object) -> int:
    """Extract the prompt-cache *read* count from ``usage``.

    OpenAI reports automatic cache hits as
    ``usage.prompt_tokens_details.cached_tokens``; both levels can be
    ``None``/absent (older SDKs, local servers). There is no
    cache-*write* counterpart on this API.
    """
    details = getattr(usage, "prompt_tokens_details", None)
    return int(getattr(details, "cached_tokens", 0) or 0)


def _first_message(response: object) -> object:
    """Return ``response.choices[0].message`` or raise on an empty list.

    Args:
        response: A Chat Completions response (or test double).

    Returns:
        The first choice's message object.

    Raises:
        GenerationError: If the response carries no choices.
    """
    choices = list(getattr(response, "choices", None) or [])
    if not choices:
        msg = "Response contained no choices"
        raise GenerationError(msg)
    return choices[0].message


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible SDK implementation of :class:`LLMProvider`.

    Construction is cheap and performs no I/O: the sync client is
    created per-call inside a context manager, and the async client is
    allocated lazily and cached for reuse across concurrent calls —
    the same lifecycle contract as the Anthropic provider.

    Attributes:
        model: Model identifier used for every request (an OpenAI id
            such as ``gpt-5.5``, or whatever the local server hosts).
        max_retries: Maximum number of retry attempts for failed
            requests.
        retry_delay: Initial delay in seconds between retry attempts
            (doubled each retry).
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        base_url: str | None = None,
    ) -> None:
        """Initialize the provider with credentials and retry policy.

        Args:
            api_key: API key for authentication (read from
                ``OPENAI_API_KEY`` by the selection layer). Local
                OpenAI-compatible servers usually ignore it, so a
                dummy non-empty value works there.
            model: Model identifier to generate with.
            max_retries: Maximum retry attempts. Defaults to 3.
            retry_delay: Initial retry delay in seconds. Defaults to
                1.0.
            base_url: Optional endpoint override for local/OSS
                OpenAI-compatible servers. Falls back to the
                ``OPENAI_BASE_URL`` environment variable, then to the
                SDK default endpoint.
        """
        self._api_key = api_key
        self._model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._base_url = base_url
        # Lazily-created long-lived async client; one shared httpx pool
        # across all async calls, mirroring AnthropicProvider.
        self._async_client: AsyncOpenAI | None = None

    @property
    def model(self) -> str:
        """Return the model identifier this provider generates with."""
        return self._model

    def _resolve_base_url(self) -> str | None:
        """Resolve the endpoint override: constructor arg, then env, then SDK.

        Returns:
            The base URL to pass to the SDK client, or ``None`` to use
            the SDK's default OpenAI endpoint. A blank environment
            value is treated as unset.
        """
        return self._base_url or os.environ.get(ENV_BASE_URL) or None

    # ------------------------------ retry core ------------------------------
    def _retry_schedule(self) -> Iterator[tuple[int, float | None]]:
        """Yield ``(attempt_index, sleep_before_next_or_None)`` pairs.

        Same exponential schedule as the Anthropic provider so swapping
        providers does not change retry behavior.
        """
        for attempt in range(self.max_retries + 1):
            is_last = attempt == self.max_retries
            yield attempt, None if is_last else self.retry_delay * (2**attempt)

    @staticmethod
    def _capture(
        attempt: Callable[[], _ResultT],
    ) -> tuple[_ResultT | None, Exception | None]:
        """Run one sync attempt; return the result or capture the error.

        :class:`GenerationError` (a malformed response) propagates
        immediately — only transport-level failures are retryable,
        matching the Anthropic provider's semantics.
        """
        try:
            return attempt(), None
        except GenerationError:
            raise
        except Exception as e:  # noqa: BLE001 — preserved for retry semantics
            return None, e

    @staticmethod
    async def _capture_async(
        attempt: Callable[[], Awaitable[_ResultT]],
    ) -> tuple[_ResultT | None, Exception | None]:
        """Async counterpart of :meth:`_capture`."""
        try:
            return await attempt(), None
        except GenerationError:
            raise
        except Exception as e:  # noqa: BLE001 — preserved for retry semantics
            return None, e

    def _retry_sync(self, attempt: Callable[[], _ResultT]) -> _ResultT:
        """Drive ``attempt`` through the retry schedule (sync).

        Telemetry is recorded exactly once per logical call — on the
        successful attempt or on exhaustion — never per retry.

        Args:
            attempt: Zero-argument callable performing one API call.

        Returns:
            The first successful result.

        Raises:
            GenerationError: When every attempt failed; the last
                transport error is chained as ``cause``.
        """
        report = get_active_report()
        call_started = time.perf_counter()

        for attempt_index, sleep_s in self._retry_schedule():
            result, error = self._capture(attempt)
            if result is not None:
                self._record_call(report, call_started, attempt_index, result)
                return result
            if sleep_s is None:
                self._record_call(report, call_started, attempt_index, None)
                msg = "Failed to generate content"
                raise GenerationError(msg, cause=error) from error
            time.sleep(sleep_s)

        # ``_retry_schedule`` always yields at least one entry, so this
        # is unreachable; keep mypy happy with an explicit terminal.
        msg = "Failed to generate content"
        raise GenerationError(msg)

    async def _retry_async(
        self,
        attempt: Callable[[], Awaitable[_ResultT]],
    ) -> _ResultT:
        """Async counterpart of :meth:`_retry_sync`.

        Args:
            attempt: Zero-argument coroutine factory performing one
                API call.

        Returns:
            The first successful result.

        Raises:
            GenerationError: When every attempt failed; the last
                transport error is chained as ``cause``.
        """
        report = get_active_report()
        call_started = time.perf_counter()

        for attempt_index, sleep_s in self._retry_schedule():
            result, error = await self._capture_async(attempt)
            if result is not None:
                self._record_call(report, call_started, attempt_index, result)
                return result
            if sleep_s is None:
                self._record_call(report, call_started, attempt_index, None)
                msg = "Failed to generate content"
                raise GenerationError(msg, cause=error) from error
            await asyncio.sleep(sleep_s)

        msg = "Failed to generate content"
        raise GenerationError(msg)

    @staticmethod
    def _build_api_call_record(
        latency_s: float,
        attempt: int,
        result: GenerationResult | ToolUseResult | None,
    ) -> APICallRecord:
        """Build an ``APICallRecord`` from a result, or zeros for failures."""
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
            report: Active timing collector, or ``None`` when telemetry
                is off.
            start: ``perf_counter`` value captured before the first
                attempt.
            attempt: Zero-indexed attempt number (stored as
                ``retries`` on the record).
            result: Successful result, or ``None`` when the call failed
                (token counts default to 0).
        """
        if report is None:
            return
        latency_s = time.perf_counter() - start
        report.record_api_call(cls._build_api_call_record(latency_s, attempt, result))

    # --------------------------- request building ---------------------------
    def _completion_params(self, prompt: str, output_format: str) -> dict[str, object]:
        """Build the ``chat.completions.create`` body for free-form output.

        Same system instruction the Anthropic provider sends, expressed
        as the OpenAI ``system`` role message.
        """
        return {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Generate {output_format} output. "
                        "Follow the instructions precisely."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

    @staticmethod
    def _system_text(system_blocks: list[dict[str, object]]) -> str:
        """Collapse Anthropic-shaped system blocks into one system string.

        Callers pass system prompts in the neutral (Anthropic-shaped)
        block list: ``{"type": "text", "text": ..., "cache_control":
        {...}}``. OpenAI has a single ``system`` message and caches
        prompts automatically, so the block *texts* are joined with
        blank lines and the ``cache_control`` markers are dropped.
        """
        texts = [
            text
            for block in system_blocks
            if isinstance(text := block.get("text"), str) and text
        ]
        return "\n\n".join(texts)

    def _tool_request_params(
        self,
        prompt: str,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> dict[str, object]:
        """Build the forced-tool ``chat.completions.create`` body.

        Translates the neutral (Anthropic-shaped) tool definition —
        ``name`` / ``description`` / ``input_schema`` — into an OpenAI
        function tool, and forces its invocation via ``tool_choice``
        so the response is guaranteed to contain a tool call
        (mirroring the Anthropic ``tool_choice`` contract).

        Args:
            prompt: User-message body (per-call delta).
            system_blocks: Neutral system-prompt blocks; collapsed via
                :meth:`_system_text`.
            tool_schema: Neutral tool definition with at least a
                non-empty ``name``.

        Returns:
            Keyword arguments for ``chat.completions.create``.

        Raises:
            GenerationError: If ``tool_schema`` lacks a non-empty
                ``name`` (failing locally beats an opaque HTTP 400).
        """
        raw_name = self._validate_tool_name(tool_schema)
        return {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "messages": self._chat_messages(prompt, system_blocks),
            "tools": [
                {
                    "type": "function",
                    "function": self._function_definition(raw_name, tool_schema),
                },
            ],
            "tool_choice": {"type": "function", "function": {"name": raw_name}},
        }

    @staticmethod
    def _validate_tool_name(tool_schema: dict[str, object]) -> str:
        """Return the schema's tool name, rejecting missing/blank names.

        Args:
            tool_schema: Neutral tool definition.

        Returns:
            The non-empty ``name`` string.

        Raises:
            GenerationError: If the name is missing, blank, or not a
                string.
        """
        raw_name = tool_schema.get("name")
        if not isinstance(raw_name, str) or not raw_name:
            msg = "tool_schema must include a non-empty 'name' string"
            raise GenerationError(msg)
        return raw_name

    @staticmethod
    def _function_definition(
        name: str,
        tool_schema: dict[str, object],
    ) -> dict[str, object]:
        """Translate the neutral tool schema into an OpenAI function body.

        ``description`` and ``input_schema`` (→ ``parameters``) are
        carried over when present; absent optional keys are simply
        omitted rather than sent as ``None``.
        """
        function: dict[str, object] = {"name": name}
        description = tool_schema.get("description")
        if isinstance(description, str) and description:
            function["description"] = description
        parameters = tool_schema.get("input_schema")
        if parameters is not None:
            function["parameters"] = parameters
        return function

    def _chat_messages(
        self,
        prompt: str,
        system_blocks: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        """Build the chat message list: optional system text, then the user turn."""
        messages: list[dict[str, object]] = []
        system_text = self._system_text(system_blocks)
        if system_text:
            messages.append({"role": "system", "content": system_text})
        messages.append({"role": "user", "content": prompt})
        return messages

    # --------------------------- response mapping ---------------------------
    def _result_from_completion(
        self,
        response: object,
        output_format: str,
    ) -> GenerationResult:
        """Map a Chat Completions response to :class:`GenerationResult`.

        Args:
            response: The SDK response object (or test double).
            output_format: Format echoed onto the result.

        Returns:
            A populated :class:`GenerationResult`.

        Raises:
            GenerationError: If the response has no choices or no text
                content.
        """
        message = _first_message(response)
        content = getattr(message, "content", None)
        if not isinstance(content, str) or not content:
            msg = "Expected text content in response"
            raise GenerationError(msg)
        usage = getattr(response, "usage", None)
        return GenerationResult(
            content=content,
            format=output_format,
            token_usage=_usage_tokens(usage),
            model=str(getattr(response, "model", "") or ""),
            message_id=str(getattr(response, "id", "") or ""),
            cache_read_tokens=_cached_tokens(usage),
            # OpenAI prompt caching is automatic and reports reads only;
            # there is no cache-write count on this API.
            cache_creation_tokens=0,
        )

    def _tool_result_from_completion(self, response: object) -> ToolUseResult:
        """Map a forced-tool Chat Completions response to :class:`ToolUseResult`.

        Args:
            response: The SDK response object (or test double).

        Returns:
            A populated :class:`ToolUseResult` with the parsed
            ``tool_input`` dict.

        Raises:
            GenerationError: If the response carries no tool call or
                its arguments are not a JSON object.
        """
        call = self._first_tool_call(_first_message(response))
        function = getattr(call, "function", None)
        usage = getattr(response, "usage", None)
        return ToolUseResult(
            tool_name=str(getattr(function, "name", "") or ""),
            tool_input=self._parse_tool_arguments(
                getattr(function, "arguments", None),
            ),
            token_usage=_usage_tokens(usage),
            model=str(getattr(response, "model", "") or ""),
            message_id=str(getattr(response, "id", "") or ""),
            cache_read_tokens=_cached_tokens(usage),
            cache_creation_tokens=0,
        )

    @staticmethod
    def _first_tool_call(message: object) -> object:
        """Return the message's first tool call, or raise if there is none.

        The forced ``tool_choice`` makes a missing tool call a
        provider/protocol error, mirroring Anthropic's "Expected
        ToolUseBlock" check.

        Args:
            message: The first choice's message object.

        Returns:
            The first entry of ``message.tool_calls``.

        Raises:
            GenerationError: If the message carries no tool calls.
        """
        tool_calls = list(getattr(message, "tool_calls", None) or [])
        if not tool_calls:
            msg = "Expected a tool call in response"
            raise GenerationError(msg)
        return tool_calls[0]

    @staticmethod
    def _parse_tool_arguments(raw: object) -> dict[str, object]:
        """Parse the tool call's JSON ``arguments`` string into a dict.

        Unlike Anthropic (which returns ``input`` pre-parsed), OpenAI
        delivers tool arguments as a JSON *string* that may be
        malformed; every failure mode maps to :class:`GenerationError`
        so callers see one error surface across providers.

        Args:
            raw: The ``function.arguments`` payload.

        Returns:
            The parsed JSON object.

        Raises:
            GenerationError: If ``raw`` is not a string, not valid
                JSON, or not a JSON object.
        """
        if not isinstance(raw, str):
            msg = "Tool arguments were not a JSON string"
            raise GenerationError(msg)
        try:
            parsed: object = json.loads(raw)
        except json.JSONDecodeError as exc:
            msg = "Tool arguments were not valid JSON"
            raise GenerationError(msg, cause=exc) from exc
        if not isinstance(parsed, dict):
            msg = "Tool input was not a JSON object"
            raise GenerationError(msg)
        return cast("dict[str, object]", parsed)

    # ------------------------------ sync complete ----------------------------
    def generate(self, prompt: str, output_format: OutputFormat) -> GenerationResult:
        """Generate content via the Chat Completions API (synchronous).

        Args:
            prompt: Prompt describing what to generate.
            output_format: Desired output format (yaml, toml, markdown,
                bash).

        Returns:
            GenerationResult containing generated content and metadata.

        Raises:
            GenerationError: If the API call fails after retries or
                the response is malformed.
            ProviderUnavailableError: If the ``openai`` extra is not
                installed.
        """
        # Resolve the SDK client lazily through the module __getattr__
        # seam so the module imports without the optional extra; a
        # missing extra becomes an actionable ProviderUnavailableError.
        client_cls = cast("type[OpenAI]", _sdk_attr("OpenAI"))

        with client_cls(
            api_key=self._api_key,
            base_url=self._resolve_base_url(),
        ) as client:
            return self._retry_sync(
                lambda: self._call_api(client, prompt, output_format),
            )

    def _call_api(
        self,
        client: OpenAI,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Make one sync Chat Completions call and map the response.

        The SDK method is typed against deeply-nested TypedDict unions;
        the request body is built as plain dicts (pinned by tests), so
        a single documented ``cast`` at the SDK boundary asserts the
        contract instead of a ``type: ignore`` suppressing it.
        """
        create = cast(
            "Callable[..., object]",
            client.chat.completions.create,
        )
        response = create(**self._completion_params(prompt, output_format))
        return self._result_from_completion(response, output_format)

    # ----------------------------- async complete ----------------------------
    def _get_async_client(self) -> AsyncOpenAI:
        """Return the cached ``AsyncOpenAI`` client, creating it once.

        Safe under asyncio for the same reason as the Anthropic
        provider: no ``await`` between the check and the assignment.
        Do *not* call this from a thread pool.
        """
        if self._async_client is None:
            async_cls = cast("type[AsyncOpenAI]", _sdk_attr("AsyncOpenAI"))
            self._async_client = async_cls(
                api_key=self._api_key,
                base_url=self._resolve_base_url(),
            )
        return self._async_client

    async def generate_async(
        self,
        prompt: str,
        output_format: OutputFormat,
    ) -> GenerationResult:
        """Async equivalent of :meth:`generate`.

        Reuses a single long-lived ``AsyncOpenAI`` client per provider
        instance so concurrent calls share the httpx connection pool.
        Callers should ``await`` :meth:`aclose` when finished.

        Args:
            prompt: Prompt describing what to generate.
            output_format: Desired output format.

        Returns:
            A populated :class:`GenerationResult`.

        Raises:
            GenerationError: If the API call fails after retries or
                the response is malformed.
        """
        client = self._get_async_client()
        return await self._retry_async(
            lambda: self._call_api_async(client, prompt, output_format),
        )

    async def _call_api_async(
        self,
        client: AsyncOpenAI,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Async counterpart of :meth:`_call_api`."""
        create = cast(
            "Callable[..., Awaitable[object]]",
            client.chat.completions.create,
        )
        response = await create(**self._completion_params(prompt, output_format))
        return self._result_from_completion(response, output_format)

    # -------------------------------- tool use -------------------------------
    async def generate_tool_use_async(
        self,
        prompt: str,
        *,
        system_blocks: list[dict[str, object]],
        tool_schema: dict[str, object],
    ) -> ToolUseResult:
        """Run a structured (forced tool-use) generation.

        The neutral tool definition is translated to an OpenAI function
        tool, its invocation is forced via ``tool_choice``, and the
        returned JSON ``arguments`` are parsed into the neutral
        :class:`ToolUseResult` — so callers see exactly the contract
        the Anthropic provider honors.

        Args:
            prompt: User-message body (per-call delta).
            system_blocks: Neutral system-prompt blocks. Anthropic
                ``cache_control`` markers are accepted and dropped
                (OpenAI caches prompts automatically).
            tool_schema: Neutral tool definition with ``name``,
                ``description``, and ``input_schema`` keys.

        Returns:
            :class:`ToolUseResult` with the parsed ``tool_input`` dict
            and token telemetry.

        Raises:
            GenerationError: If the call fails after retries, the
                schema lacks a name, or the response carries no
                parseable tool call.
        """
        client = self._get_async_client()
        params = self._tool_request_params(prompt, system_blocks, tool_schema)
        return await self._retry_async(
            lambda: self._call_tool_api_async(client, params),
        )

    async def _call_tool_api_async(
        self,
        client: AsyncOpenAI,
        params: dict[str, object],
    ) -> ToolUseResult:
        """Make one forced-tool call and map the response.

        Args:
            client: The cached async client.
            params: Pre-built request body from
                :meth:`_tool_request_params`.

        Returns:
            The mapped :class:`ToolUseResult`.
        """
        create = cast(
            "Callable[..., Awaitable[object]]",
            client.chat.completions.create,
        )
        response = await create(**params)
        return self._tool_result_from_completion(response)

    # -------------------------------- lifecycle ------------------------------
    async def aclose(self) -> None:
        """Release the cached async client, if any.

        Idempotent. Safe to call from a finally block even when no
        async calls were made.
        """
        if self._async_client is not None:
            await self._async_client.close()
            self._async_client = None

    # ---------------------------------- batch --------------------------------
    async def submit_tool_use_batch(
        self,
        requests: Sequence[ToolUseBatchRequest],
    ) -> BatchSubmission:
        """Decline batch submission: there is no OpenAI-compatible batch seam.

        The batch capability group maps onto Anthropic's Message
        Batches API; emulating it with fan-out requests would silently
        change cost and durability semantics, so this provider
        declines honestly (capability negotiation/fallback is tracer
        T5, #389). The interface's input contract is still honored
        first so callers get the most specific error.

        Args:
            requests: Validated for emptiness, then declined.

        Raises:
            ValueError: If ``requests`` is empty (per the interface).
            UnsupportedCapabilityError: For every non-empty submission.
        """
        if not requests:
            msg = "submit_tool_use_batch requires at least one request"
            raise ValueError(msg)
        raise UnsupportedCapabilityError(
            provider=_PROVIDER_NAME,
            capability="batch tool-use",
        )

    async def poll_batch(self, batch_id: str) -> BatchPoll:
        """Decline batch polling; see :meth:`submit_tool_use_batch`.

        Args:
            batch_id: Validated for emptiness, then declined.

        Raises:
            ValueError: If ``batch_id`` is empty (per the interface).
            UnsupportedCapabilityError: For every non-empty id.
        """
        if not batch_id:
            msg = "poll_batch requires a non-empty batch_id"
            raise ValueError(msg)
        raise UnsupportedCapabilityError(
            provider=_PROVIDER_NAME,
            capability="batch tool-use",
        )

    async def fetch_batch_results(self, batch_id: str) -> BatchResultsBundle:
        """Decline batch fetching; see :meth:`submit_tool_use_batch`.

        Args:
            batch_id: Validated for emptiness, then declined.

        Raises:
            ValueError: If ``batch_id`` is empty (per the interface).
            UnsupportedCapabilityError: For every non-empty id.
        """
        if not batch_id:
            msg = "fetch_batch_results requires a non-empty batch_id"
            raise ValueError(msg)
        raise UnsupportedCapabilityError(
            provider=_PROVIDER_NAME,
            capability="batch tool-use",
        )
