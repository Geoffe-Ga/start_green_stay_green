"""Skills generator for target projects.

Copies skills from reference directory and tunes them for target repository
using ContentTuner to adapt content while preserving structure.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.ai.tuner import ContentTuner
from start_green_stay_green.generators.base import BaseGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


logger = logging.getLogger(__name__)

# Reference skills directory
REFERENCE_SKILLS_DIR = Path(__file__).parent.parent.parent / "reference" / "skills"

# Required skills that must be present
REQUIRED_SKILLS = [
    "vibe.md",
    "concurrency.md",
    "error-handling.md",
    "testing.md",
    "documentation.md",
    "security.md",
]


@dataclass(frozen=True)
class SkillGenerationResult:
    """Result from skill generation.

    Attributes:
        skill_name: Name of the skill file (e.g., "vibe.md").
        content: Generated/tuned skill content.
        tuned: Whether content was tuned (vs just copied).
        changes: List of changes made during tuning.
    """

    skill_name: str
    content: str
    tuned: bool
    changes: list[str]


class SkillsGenerator(BaseGenerator):
    """Generate skills for target repository.

    Copies skills from reference directory and optionally tunes them
    using ContentTuner to adapt content to target repository context.

    When orchestrator is None, falls back to direct copy mode (no AI tuning).

    Attributes:
        orchestrator: Optional AI orchestrator for content generation.
        tuner: Optional content tuner for adapting skills.
            None when orchestrator not available.
        reference_dir: Path to reference skills directory.
        dry_run: Whether to run in dry-run mode (no actual tuning).
    """

    tuner: ContentTuner | None

    def __init__(
        self,
        orchestrator: AIOrchestrator | None,
        *,
        reference_dir: Path | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize SkillsGenerator.

        Args:
            orchestrator: Optional AI orchestrator for generation.
                If None, operates in direct copy mode.
            reference_dir: Custom reference skills directory. Defaults to
                built-in reference/skills/.
            dry_run: Run in dry-run mode (copy without tuning).
        """
        self.orchestrator = orchestrator
        self.reference_dir = reference_dir or REFERENCE_SKILLS_DIR
        self.dry_run = dry_run

        # Only create tuner if orchestrator available
        if self.orchestrator:
            self.tuner = ContentTuner(self.orchestrator, dry_run=dry_run)
        else:
            self.tuner = None
            logger.info("Skills generator initialized without AI (direct copy mode)")

    def _check_directory_exists(self) -> None:
        """Check if reference directory exists.

        Raises:
            FileNotFoundError: If directory doesn't exist.
            ValueError: If path is not a directory.
        """
        if not self.reference_dir.exists():
            msg = f"Reference skills directory not found: {self.reference_dir}"
            raise FileNotFoundError(msg)

        if not self.reference_dir.is_dir():
            msg = f"Reference skills path is not a directory: {self.reference_dir}"
            raise ValueError(msg)

    def _check_required_skills(self) -> None:
        """Check if all required skills are present.

        Raises:
            ValueError: If required skills are missing.
        """
        missing_skills = [
            skill
            for skill in REQUIRED_SKILLS
            if not (self.reference_dir / skill).exists()
        ]

        if missing_skills:
            msg = f"Missing required skills: {', '.join(missing_skills)}"
            raise ValueError(msg)

    def _validate_reference_dir(self) -> None:
        """Validate reference directory exists and contains required skills.

        Raises:
            FileNotFoundError: If reference directory doesn't exist.
            ValueError: If required skills are missing.
        """
        self._check_directory_exists()
        self._check_required_skills()

    def _load_skill(self, skill_name: str) -> str:
        """Load skill content from reference directory.

        Args:
            skill_name: Name of skill file (e.g., "vibe.md").

        Returns:
            Skill content as string.

        Raises:
            FileNotFoundError: If skill file doesn't exist.
        """
        skill_path = self.reference_dir / skill_name
        if not skill_path.exists():
            msg = f"Skill file not found: {skill_path}"
            raise FileNotFoundError(msg)

        logger.info("Loading skill: %s", skill_name)
        return skill_path.read_text()

    async def tune_skill(
        self,
        skill_name: str,
        skill_content: str,
        target_context: str,
    ) -> SkillGenerationResult:
        """Tune skill content for target repository (or direct copy if no AI).

        Args:
            skill_name: Name of skill file.
            skill_content: Original skill content.
            target_context: Description of target repository.

        Returns:
            SkillGenerationResult with tuned content (or original if no AI).
        """
        # Direct copy if no tuner available
        if self.tuner is None:
            logger.info("Copying skill %s (no AI tuning)", skill_name)
            return SkillGenerationResult(
                skill_name=skill_name,
                content=skill_content,  # Original content
                tuned=False,
                changes=[],
            )

        # AI tuning if tuner available
        source_context = "Start Green Stay Green reference repository"
        logger.info("Tuning skill %s for target context", skill_name)

        result = await self.tuner.tune(
            source_content=skill_content,
            source_context=source_context,
            target_context=target_context,
        )

        return SkillGenerationResult(
            skill_name=skill_name,
            content=result.content,
            tuned=not result.dry_run,
            changes=result.changes,
        )

    async def generate_all_skills(
        self,
        target_context: str,
    ) -> dict[str, SkillGenerationResult]:
        """Generate all skills for target repository.

        Args:
            target_context: Description of target repository
                (e.g., "FastAPI microservice for user management").

        Returns:
            Dictionary mapping skill names to SkillGenerationResult.

        Raises:
            FileNotFoundError: If reference directory or skills missing.
            ValueError: If reference directory invalid.

        Examples:
            >>> orchestrator = AIOrchestrator(api_key="...")
            >>> generator = SkillsGenerator(orchestrator)
            >>> results = await generator.generate_all_skills(
            ...     target_context="Django web application"
            ... )
            >>> print(results["vibe.md"].content)
            # Vibe Skill
            ...
        """
        # Validate reference directory
        self._validate_reference_dir()

        results = {}

        for skill_name in REQUIRED_SKILLS:
            # Load skill content
            skill_content = self._load_skill(skill_name)

            # Tune skill
            result = await self.tune_skill(
                skill_name=skill_name,
                skill_content=skill_content,
                target_context=target_context,
            )

            results[skill_name] = result

            logger.info(
                "Generated skill %s (%d changes)",
                skill_name,
                len(result.changes),
            )

        return results

    def generate(self) -> dict[str, Any]:
        """Generate skills synchronously (placeholder for base class).

        This method is required by BaseGenerator but skills generation
        is async. Use generate_all_skills() instead.

        Raises:
            NotImplementedError: Use generate_all_skills() instead.
        """
        msg = "Use generate_all_skills() for async skill generation"
        raise NotImplementedError(msg)
