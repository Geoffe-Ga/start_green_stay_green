"""Shared types for the AI subsystem.

Lives in its own module so :mod:`start_green_stay_green.ai.orchestrator`
and :mod:`start_green_stay_green.ai.batch` can both import these
freely without forming a cycle. ``orchestrator`` is the SDK-bridge
layer; ``batch`` is the pure-data layer over the Batches API; they
both need :class:`ToolUseResult`, :class:`TokenUsage`, and
:class:`GenerationError`, but neither one is a natural home for the
types when the *other* needs to construct them.

Existing callers continue to import these from
``ai.orchestrator`` — that module re-exports each of them for
back-compat.
"""

from __future__ import annotations

from dataclasses import dataclass


class GenerationError(Exception):
    """Raised when AI generation fails.

    Attributes:
        cause: Optional underlying exception that caused this error.
    """

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """Initialize GenerationError.

        Args:
            message: Error message describing the failure.
            cause: Optional underlying exception that caused this error.
        """
        super().__init__(message)
        self.cause = cause


@dataclass(frozen=True)
class TokenUsage:
    """Token usage information from API response.

    Attributes:
        input_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens in the response.
    """

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used.

        Returns:
            Sum of input and output tokens.
        """
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class GenerationResult:
    """Result from AI generation request.

    Attributes:
        content: Generated content from the AI model.
        format: Output format (yaml, toml, markdown, bash).
        token_usage: Token usage statistics for the request.
        cache_read_tokens: Subset of input tokens served from the
            prompt cache. ``0`` when caching is disabled or the
            response did not report this field.
        cache_creation_tokens: Tokens written to the prompt cache on
            this call (billed at a higher rate than reads).
        model: Model identifier used for generation.
        message_id: Unique identifier for the API message.
    """

    content: str
    format: str
    token_usage: TokenUsage
    model: str
    message_id: str
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0


@dataclass(frozen=True)
class ToolUseResult:
    """Result from a structured (``tool_use``) API call.

    The Claude API returns a JSON object validated against the tool's
    ``input_schema``; ``tool_input`` is that object verbatim. Replaces
    free-form text parsing for callers that need typed fields out of
    the model.

    Attributes:
        tool_name: Name of the tool the model invoked.
        tool_input: Parsed JSON input the model passed to the tool.
        token_usage: Token usage statistics for the request.
        cache_read_tokens: Subset of input tokens served from the
            prompt cache.
        cache_creation_tokens: Tokens written to the prompt cache.
        model: Model identifier used for generation.
        message_id: Unique identifier for the API message.
    """

    tool_name: str
    tool_input: dict[str, object]
    token_usage: TokenUsage
    model: str
    message_id: str
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
