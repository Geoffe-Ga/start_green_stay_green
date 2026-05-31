"""Internal retry-attempt outcome helpers for LLM providers.

A provider's retry loop runs one attempt, then either returns the
result or remembers the error to retry. These two frozen dataclasses
carry that "success result OR captured retryable error" pair for the
free-form and tool-use paths respectively. They are provider-neutral
(no ``anthropic`` types) so any future provider can reuse the same
retry plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from start_green_stay_green.ai.types import GenerationResult
    from start_green_stay_green.ai.types import ToolUseResult

__all__ = ["AttemptOutcome", "ToolAttemptOutcome"]


@dataclass(frozen=True)
class AttemptOutcome:
    """One free-form attempt: a success result or a captured error."""

    result: GenerationResult | None
    error: Exception | None


@dataclass(frozen=True)
class ToolAttemptOutcome:
    """One ``tool_use`` attempt: a success result or a captured error."""

    result: ToolUseResult | None
    error: Exception | None
