"""LLM provider abstraction for the AI subsystem.

Introduced in tracer T1 of the multi-agent epic (#381). The
:class:`~start_green_stay_green.ai.providers.base.LLMProvider`
interface is the seam every later tracer depends on: it decouples
:class:`~start_green_stay_green.ai.orchestrator.AIOrchestrator` from
any single SDK. Two concrete implementations exist:

* :class:`AnthropicProvider` (tracer T1, #381) — contains *all*
  Anthropic-specific code (client construction, retry/backoff, token
  accounting, the Message Batches API).
* :class:`OpenAIProvider` (tracer T3, #385) — maps the same neutral
  types onto the OpenAI Chat Completions API, and via its base-URL
  override onto any local/OSS OpenAI-compatible server. Batch is
  declined with :class:`UnsupportedCapabilityError`.

Each provider advertises which optional capability groups it
implements via a frozen :class:`ProviderCapabilities` record (tracer
T5, #389) readable from the class itself — no instance, no vendor SDK
— so orchestration code negotiates features (e.g. falling back from
batch to sequential calls) instead of crashing on a typed decline.

The orchestrator depends on the interface, not on any vendor package
— each SDK is an optional install extra imported lazily inside its
provider module — so further providers (another vendor, a fake for
tests) can be slotted in without touching orchestration logic.
"""

from __future__ import annotations

from start_green_stay_green.ai.providers.anthropic_provider import AnthropicProvider
from start_green_stay_green.ai.providers.base import LLMProvider
from start_green_stay_green.ai.providers.base import ProviderCapabilities
from start_green_stay_green.ai.providers.base import UnsupportedCapabilityError
from start_green_stay_green.ai.providers.openai_provider import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "LLMProvider",
    "OpenAIProvider",
    "ProviderCapabilities",
    "UnsupportedCapabilityError",
]
