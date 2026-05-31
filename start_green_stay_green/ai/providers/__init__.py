"""LLM provider abstraction for the AI subsystem.

Introduced in tracer T1 of the multi-agent epic (#381). The
:class:`~start_green_stay_green.ai.providers.base.LLMProvider`
interface is the seam every later tracer depends on: it decouples
:class:`~start_green_stay_green.ai.orchestrator.AIOrchestrator` from
any single SDK. :class:`AnthropicProvider` is the only concrete
implementation today and contains *all* Anthropic-specific code
(client construction, retry/backoff, token accounting, the Message
Batches API).

The orchestrator depends on the interface, not on the ``anthropic``
package, so a future provider (a second vendor, a local model, a
fake for tests) can be slotted in without touching orchestration
logic.
"""

from __future__ import annotations

from start_green_stay_green.ai.providers.anthropic_provider import AnthropicProvider
from start_green_stay_green.ai.providers.base import LLMProvider

__all__ = [
    "AnthropicProvider",
    "LLMProvider",
]
