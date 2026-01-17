"""Content tuning system for adapting content to target repository context.

Uses Claude Sonnet to adapt copied content while preserving structure.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError

if TYPE_CHECKING:
    from collections.abc import Sequence


logger = logging.getLogger(__name__)

# Constants for response parsing
_CHANGES_SECTION_PARTS = 2


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

    def _build_tuning_prompt(
        self,
        source_content: str,
        source_context: str,
        target_context: str,
        preserve_sections: Sequence[str] | None = None,
    ) -> str:
        """Build prompt for tuning operation.

        Args:
            source_content: Original content to adapt.
            source_context: Description of source repository.
            target_context: Description of target repository.
            preserve_sections: Sections to leave unchanged.

        Returns:
            Formatted prompt for AI tuning.
        """
        preserve_text = ""
        if preserve_sections:
            sections = ", ".join(f'"{s}"' for s in preserve_sections)
            preserve_text = f"\n\nPRESERVE THESE SECTIONS UNCHANGED: {sections}"

        return f"""Adapt the following content from the source repository \
context to the target repository context.

SOURCE CONTEXT:
{source_context}

TARGET CONTEXT:
{target_context}

REQUIREMENTS:
- Preserve the structure and format of the original content
- Adapt terminology, examples, and references to match target context
- Maintain all section headings and organization
- Keep the same level of detail and completeness
- List all changes made at the end{preserve_text}

CONTENT TO ADAPT:
{source_content}

OUTPUT FORMAT:
Provide the adapted content followed by a CHANGES section listing what was modified.

Example format:
[Adapted content here]

CHANGES:
- Changed "FastAPI" to "Django" in examples
- Updated repository name references
- Adapted script paths
"""

    def _parse_tuning_response(self, response_content: str) -> tuple[str, list[str]]:
        """Parse AI response to extract content and changes.

        Args:
            response_content: Raw response from AI.

        Returns:
            Tuple of (adapted_content, list_of_changes).
        """
        # Split on CHANGES section
        parts = response_content.split("CHANGES:", 1)

        if len(parts) == _CHANGES_SECTION_PARTS:
            content = parts[0].strip()
            changes_text = parts[1].strip()

            # Parse changes (each line starting with - or *)
            changes = []
            for raw_line in changes_text.split("\n"):
                line = raw_line.strip()
                if line.startswith(("-", "*")):
                    changes.append(line.lstrip("-* "))
                elif line:  # Non-empty line without marker
                    changes.append(line)

            return content, changes

        # No CHANGES section found, return full content
        return response_content.strip(), []

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

        # Build prompt and generate
        prompt = self._build_tuning_prompt(
            source_content,
            source_context,
            target_context,
            preserve_sections,
        )

        logger.info(
            "Tuning content (source: %s, target: %s)",
            source_context[:50],
            target_context[:50],
        )

        try:
            result = self.orchestrator.generate(prompt, "markdown")
        except GenerationError:
            logger.exception("Tuning failed")
            raise

        # Parse response
        content, changes = self._parse_tuning_response(result.content)

        logger.info("Tuning complete, %d changes made", len(changes))
        for change in changes:
            logger.debug("Change: %s", change)

        return TuningResult(
            content=content,
            changes=changes,
            dry_run=False,
            token_usage_input=result.token_usage.input_tokens,
            token_usage_output=result.token_usage.output_tokens,
        )
