"""Content tuning system for adapting content to target repository context.

Uses Claude Sonnet to adapt copied content while preserving structure.
The model is invoked via the ``report_tuning`` tool so the response
arrives as validated JSON (``tuned_content`` + ``changes``) instead of
free-form text — eliminates the previous regex-based ``CHANGES:``
parser. The stable instruction prefix is sent as a cache-controlled
system block so back-to-back per-agent tunes within a single
``green init`` (or ``green enhance``) hit the prompt cache.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING
from typing import TypeVar
from typing import cast

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Callable
    from collections.abc import Sequence

    from start_green_stay_green.ai.orchestrator import ToolUseResult


logger = logging.getLogger(__name__)


# Tool definition for the structured-output path. The model is
# *forced* to invoke this tool (via ``tool_choice``) so the response
# is always a JSON object matching the schema — no regex parsing.
_REPORT_TUNING_TOOL: dict[str, object] = {
    "name": "report_tuning",
    "description": (
        "Report the tuned content and a bullet list of changes made "
        "while adapting the source content to the target context."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "tuned_content": {
                "type": "string",
                "description": "The fully adapted content.",
            },
            "changes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Short bullet describing each change made. "
                    "Empty list when no changes were necessary."
                ),
            },
        },
        "required": ["tuned_content", "changes"],
    },
}


# Generic over the result type so callers get a precise return type back
# instead of a blanket ``Any``.
_T = TypeVar("_T")


async def _await_or_offload(
    call: Callable[..., _T | Awaitable[_T]],
    *args: object,
    **kwargs: object,
) -> _T:
    """Invoke ``call`` and return its result, awaitable or otherwise.

    Two cases, both real:

    * **Async callable** (``asyncio.iscoroutinefunction`` is ``True``):
      call it, await the resulting coroutine. This covers both real
      :class:`anthropic.AsyncAnthropic` paths and :class:`AsyncMock`
      doubles in tests.
    * **Sync callable** (the default for :meth:`AIOrchestrator.generate`):
      offload to a worker thread via :func:`asyncio.to_thread` so a
      hundreds-of-ms HTTP round-trip does not block the event loop while
      sibling tunings wait. Tests using ``MagicMock(spec=AIOrchestrator)``
      land here too — :func:`asyncio.to_thread` happily runs the mock
      and returns the configured value.

    The previous "autospec MagicMock falls through" branch was removed
    when the corresponding tests were migrated from
    ``create_autospec(AIOrchestrator)`` to ``MagicMock(spec=...)``;
    issue #306 closed.
    """
    if asyncio.iscoroutinefunction(call):
        return await cast("Awaitable[_T]", call(*args, **kwargs))
    # Sync path: cast narrows ``T | Awaitable[T]`` to ``T`` for the
    # signature :func:`asyncio.to_thread` expects.
    sync_call = cast("Callable[..., _T]", call)
    return await asyncio.to_thread(sync_call, *args, **kwargs)


@dataclass(frozen=True)
class TuningResult:
    """Result from content tuning operation.

    Attributes:
        content: Tuned content adapted to target context.
        changes: List of changes made during tuning.
        dry_run: Whether this was a dry-run (no actual changes).
        token_usage_input: Number of input tokens used.
        token_usage_output: Number of output tokens used.
    """

    content: str
    changes: list[str]
    dry_run: bool
    token_usage_input: int
    token_usage_output: int


class ContentTuner:
    """Adapts content to fit target repository context.

    Uses Claude Sonnet for cost-efficient content adaptation while
    preserving structure and format.

    Attributes:
        orchestrator: AI orchestrator for API communication.
        dry_run: Whether to run in dry-run mode (no actual changes).
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator,
        *,
        dry_run: bool = False,
    ) -> None:
        """Initialize ContentTuner.

        Args:
            orchestrator: AI orchestrator configured with Sonnet model.
            dry_run: Run in dry-run mode (returns original content).
        """
        self.orchestrator = orchestrator
        self.dry_run = dry_run

    @staticmethod
    def _validate_content(content: str) -> None:
        """Validate content is not empty.

        Args:
            content: Content to validate.

        Raises:
            ValueError: If content is empty or only whitespace.
        """
        if not content or not content.strip():
            msg = "Content cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_context(context: str, context_name: str) -> None:
        """Validate context description is not empty.

        Args:
            context: Context description to validate.
            context_name: Name of the context (for error messages).

        Raises:
            ValueError: If context is empty or only whitespace.
        """
        if not context or not context.strip():
            msg = f"{context_name} cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _build_system_blocks(
        source_context: str,
        target_context: str,
        preserve_sections: Sequence[str] | None,
    ) -> list[dict[str, object]]:
        """Assemble the cache-controlled system blocks for a tune call.

        Why split this off into system blocks (rather than inline into
        the user message)? The Anthropic prompt cache keys on the
        leading prefix of every request. Per-call deltas
        (``source_content``) live in the user message; everything
        stable across the 8 subagent tunes in one ``green init``
        (instructions + source/target context + preserve list) lives
        here so the second-and-later tunes in a session can hit the
        cache.

        The final block carries
        ``cache_control: {"type": "ephemeral"}`` — Anthropic caches
        the prefix up through that block for ~5 minutes.

        Args:
            source_context: Description of the source repository.
            target_context: Description of the target repository.
            preserve_sections: Optional list of section headings the
                model must leave verbatim.

        Returns:
            List of system blocks, ready to pass straight to
            :meth:`AIOrchestrator.generate_tool_use_async`.
        """
        instructions = (
            "You are a content tuner adapting source repository "
            "content to a target repository context. "
            "Always invoke the report_tuning tool with the adapted "
            "content and a list of the changes you made.\n\n"
            "REQUIREMENTS:\n"
            "- Preserve the structure and format of the original content.\n"
            "- Adapt terminology, examples, and references to match the "
            "target context.\n"
            "- Maintain all section headings and organisation.\n"
            "- Keep the same level of detail and completeness.\n"
            "- List every meaningful change in the changes array; "
            "return an empty array when no changes were necessary."
        )
        if preserve_sections:
            sections = ", ".join(f'"{s}"' for s in preserve_sections)
            instructions += f"\n- Leave the following sections unchanged: {sections}."

        context_block = (
            f"SOURCE CONTEXT:\n{source_context}\n\n"
            f"TARGET CONTEXT:\n{target_context}"
        )

        # Mark only the *last* block as cached. Anthropic caches every
        # block up to and including the marked one, so a single marker
        # at the tail caches the full stable prefix.
        return [
            {"type": "text", "text": instructions},
            {
                "type": "text",
                "text": context_block,
                "cache_control": {"type": "ephemeral"},
            },
        ]

    @staticmethod
    def _build_user_message(source_content: str) -> str:
        """Per-call delta: the only part that varies between subagent tunes.

        Kept tiny on purpose so the cache prefix (system blocks) is as
        long as possible relative to the per-call body.
        """
        return f"CONTENT TO ADAPT:\n{source_content}"

    @staticmethod
    def _validate_tool_use_input(
        tool_input: dict[str, object],
    ) -> tuple[str, list[object]]:
        """Validate ``tool_input`` shape and return its two required fields.

        Splits validation off from filtering so the parser stays at
        cyclomatic grade A. The schema enforces both fields at the
        API layer; this catches malformed payloads from an SDK
        version mismatch before they cause a confusing ``TypeError``
        downstream.
        """
        raw_content = tool_input.get("tuned_content")
        if not isinstance(raw_content, str):
            msg = "report_tuning.tuned_content must be a string"
            raise GenerationError(msg)
        raw_changes = tool_input.get("changes", [])
        if not isinstance(raw_changes, list):
            msg = "report_tuning.changes must be a list of strings"
            raise GenerationError(msg)
        return raw_content, raw_changes

    @classmethod
    def _parse_tool_use_input(
        cls,
        tool_input: dict[str, object],
    ) -> tuple[str, list[str]]:
        """Extract ``(tuned_content, changes)`` from the tool's JSON input."""
        raw_content, raw_changes = cls._validate_tool_use_input(tool_input)
        changes = [c for c in raw_changes if isinstance(c, str) and c.strip()]
        return raw_content, changes

    async def tune(
        self,
        source_content: str,
        source_context: str,
        target_context: str,
        preserve_sections: Sequence[str] | None = None,
    ) -> TuningResult:
        r"""Tune content from source to target context.

        Args:
            source_content: Original content to adapt.
            source_context: Description of source repository.
            target_context: Description of target repository.
            preserve_sections: Sections to leave unchanged.

        Returns:
            TuningResult with adapted content and changelog.

        Raises:
            ValueError: If inputs are invalid.
            GenerationError: If AI tuning fails.

        Examples:
            >>> orchestrator = AIOrchestrator(api_key="...", model=ModelConfig.SONNET)
            >>> tuner = ContentTuner(orchestrator)
            >>> result = await tuner.tune(
            ...     source_content="# FastAPI Project\\n...",
            ...     source_context="FastAPI web service",
            ...     target_context="Django web application",
            ... )
            >>> print(result.content)
            # Django Project
            ...
        """
        # Validate inputs
        self._validate_content(source_content)
        self._validate_context(source_context, "Source context")
        self._validate_context(target_context, "Target context")

        # Handle dry-run mode
        if self.dry_run:
            logger.info("Dry-run mode: returning original content unchanged")
            return TuningResult(
                content=source_content,
                changes=["[DRY RUN] No changes made"],
                dry_run=True,
                token_usage_input=0,
                token_usage_output=0,
            )

        system_blocks = self._build_system_blocks(
            source_context, target_context, preserve_sections
        )
        user_message = self._build_user_message(source_content)

        logger.info(
            "Tuning content (source: %s, target: %s)",
            source_context[:50],
            target_context[:50],
        )

        try:
            tool_result: ToolUseResult = await _await_or_offload(
                cast(
                    "Callable[..., Awaitable[ToolUseResult]]",
                    self.orchestrator.generate_tool_use_async,
                ),
                user_message,
                system_blocks=system_blocks,
                tool_schema=_REPORT_TUNING_TOOL,
            )
        except GenerationError:
            logger.exception("Tuning failed")
            raise

        content, changes = self._parse_tool_use_input(tool_result.tool_input)

        logger.info("Tuning complete, %d changes made", len(changes))
        for change in changes:
            logger.debug("Change: %s", change)

        return TuningResult(
            content=content,
            changes=changes,
            dry_run=False,
            token_usage_input=tool_result.token_usage.input_tokens,
            token_usage_output=tool_result.token_usage.output_tokens,
        )
