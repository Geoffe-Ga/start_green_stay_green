"""CLAUDE.md generator.

Generates CLAUDE.md customized to target project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.ai.prompts.manager import get_default_manager

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass(frozen=True)
class ClaudeMdGenerationResult:
    """Result from CLAUDE.md generation operation.

    Attributes:
        content: Generated CLAUDE.md content.
        token_usage_input: Number of input tokens used.
        token_usage_output: Number of output tokens used.
    """

    content: str
    token_usage_input: int
    token_usage_output: int


class ClaudeMdGenerator:
    """Generates CLAUDE.md customized to target project.

    Uses AI orchestrator to generate project-specific CLAUDE.md based on
    reference templates and quality standards.

    Attributes:
        orchestrator: AI orchestrator for content generation.
        reference_dir: Directory containing CLAUDE.md reference template.
        quality_ref_path: Path to MAXIMUM_QUALITY_ENGINEERING.md.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        *,
        reference_dir: Path | None = None,
        quality_ref_path: Path | None = None,
    ) -> None:
        """Initialize ClaudeMdGenerator.

        Args:
            orchestrator: Optional AI orchestrator. When ``None``, only the
                deterministic ``generate_baseline`` path is available.
            reference_dir: Directory with CLAUDE.md reference
                (default: reference/claude).
            quality_ref_path: Path to quality reference
                (default: reference/MAXIMUM_QUALITY_ENGINEERING.md).
        """
        self.orchestrator = orchestrator

        if reference_dir is None:
            # Default to reference/claude relative to project root
            project_root = Path(__file__).parent.parent.parent
            reference_dir = project_root / "reference" / "claude"

        if quality_ref_path is None:
            # Default to reference/MAXIMUM_QUALITY_ENGINEERING.md
            project_root = Path(__file__).parent.parent.parent
            quality_ref_path = (
                project_root / "reference" / "MAXIMUM_QUALITY_ENGINEERING.md"
            )

        self.reference_dir = reference_dir
        self.quality_ref_path = quality_ref_path

    def _validate_reference_dir(self) -> None:
        """Validate reference directory exists and contains CLAUDE.md.

        Raises:
            ValueError: If reference directory is invalid or CLAUDE.md missing.
        """
        if not self.reference_dir.exists():
            msg = f"Reference directory not found: {self.reference_dir}"
            raise ValueError(msg)

        if not self.reference_dir.is_dir():
            msg = f"Reference path is not a directory: {self.reference_dir}"
            raise ValueError(msg)

        claude_md_path = self.reference_dir / "CLAUDE.md"
        if not claude_md_path.exists():
            msg = f"CLAUDE.md not found in reference directory: {self.reference_dir}"
            raise ValueError(msg)

    def _load_claude_md_reference(self) -> str:
        """Load CLAUDE.md reference template.

        Returns:
            Content of CLAUDE.md reference file.

        Raises:
            FileNotFoundError: If CLAUDE.md reference file not found.
        """
        claude_md_path = self.reference_dir / "CLAUDE.md"
        return claude_md_path.read_text(encoding="utf-8")

    def _load_quality_reference(self) -> str:
        """Load MAXIMUM_QUALITY_ENGINEERING.md reference.

        Returns:
            Content of quality reference file.

        Raises:
            FileNotFoundError: If quality reference file not found.
        """
        return self.quality_ref_path.read_text(encoding="utf-8")

    @staticmethod
    def _build_generation_prompt(
        claude_md_reference: str,
        quality_reference: str,
        project_config: dict[str, Any],
    ) -> str:
        """Render the ``claude_md_tune`` prompt template.

        The 6-component prompt body lives in
        ``start_green_stay_green/ai/prompts/templates/claude_md_tune.jinja2``;
        this method supplies the context dict.

        Args:
            claude_md_reference: Reference CLAUDE.md template.
            quality_reference: ``MAXIMUM_QUALITY_ENGINEERING.md`` content.
            project_config: Project configuration with ``project_name``,
                ``language``, ``scripts``, ``skills``.

        Returns:
            Fully rendered prompt ready for ``orchestrator.generate``.
        """
        return get_default_manager().render(
            "claude_md_tune",
            {
                "project_name": project_config.get("project_name", "unknown"),
                "language": project_config.get("language", "unknown"),
                "scripts": list(project_config.get("scripts") or []),
                "skills": list(project_config.get("skills") or []),
                "claude_md_reference": claude_md_reference,
                "quality_reference": quality_reference,
            },
        )

    @staticmethod
    def _has_h1_title(content: str) -> bool:
        """Check if content has an H1 title.

        Args:
            content: Markdown content to check.

        Returns:
            True if content has H1 title, False otherwise.
        """
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                return True
        return False

    def _validate_markdown_structure(self, content: str) -> None:
        """Validate generated markdown has proper structure.

        Args:
            content: Generated markdown content to validate.

        Raises:
            ValueError: If markdown structure is invalid.
        """
        if not content or not content.strip():
            msg = "Generated CLAUDE.md is empty"
            raise ValueError(msg)

        if not self._has_h1_title(content):
            msg = "Generated CLAUDE.md is missing H1 title"
            raise ValueError(msg)

    @staticmethod
    def _baseline_substitutions(project_config: dict[str, Any]) -> dict[str, str]:
        """Build the token → replacement map for ``_render_baseline``."""
        scripts = project_config.get("scripts") or []
        skills = project_config.get("skills") or []
        return {
            "{{PROJECT_NAME}}": str(project_config.get("project_name", "your-project")),
            "{{LANGUAGE}}": str(project_config.get("language", "python")),
            "{{SCRIPTS}}": "\n".join(f"- {s}" for s in scripts),
            "{{SKILLS}}": "\n".join(f"- {s}" for s in skills),
        }

    @classmethod
    def _render_baseline(
        cls,
        reference: str,
        project_config: dict[str, Any],
    ) -> str:
        """Substitute ``{{PLACEHOLDER}}`` tokens in the reference template.

        The reference CLAUDE.md uses double-brace tokens like
        ``{{PROJECT_NAME}}``. This is a deterministic, dependency-free
        substitution: unknown tokens are left intact so the resulting file
        is always inspectable for "what was the user supposed to fill in?".
        """
        rendered = reference
        for token, value in cls._baseline_substitutions(project_config).items():
            rendered = rendered.replace(token, value)
        return rendered

    def generate_baseline(
        self,
        project_config: dict[str, Any],
    ) -> ClaudeMdGenerationResult:
        """Render a CLAUDE.md baseline without any API calls.

        This is the fast, deterministic path used by Pass 1 of the new
        two-pass init. The result is a complete, valid CLAUDE.md based on
        the reference template with ``{{PROJECT_NAME}}``-style tokens
        substituted.

        Args:
            project_config: Project configuration with keys
                ``project_name``, ``language``, ``scripts``, ``skills``.

        Returns:
            ``ClaudeMdGenerationResult`` with zero token usage.

        Raises:
            ValueError: If the rendered baseline lacks a valid H1 title.
            FileNotFoundError: If reference files are missing.
        """
        self._validate_reference_dir()
        reference = self._load_claude_md_reference()
        rendered = self._render_baseline(reference, project_config)
        self._validate_markdown_structure(rendered)
        return ClaudeMdGenerationResult(
            content=rendered,
            token_usage_input=0,
            token_usage_output=0,
        )

    def generate(self, project_config: dict[str, Any]) -> ClaudeMdGenerationResult:
        """Generate customized CLAUDE.md for target project.

        When an orchestrator is configured this dispatches to the legacy
        AI-tuned path. Otherwise it falls back to ``generate_baseline``,
        guaranteeing a complete file in offline mode.

        Args:
            project_config: Project configuration dictionary with keys:
                - project_name: Name of the target project
                - language: Programming language
                - scripts: List of generated script names
                - skills: List of generated skill names

        Returns:
            ClaudeMdGenerationResult with generated content and token usage.

        Raises:
            ValueError: If reference files are invalid.
            FileNotFoundError: If reference files are missing.
        """
        if self.orchestrator is None:
            return self.generate_baseline(project_config)

        # Validate and load references
        self._validate_reference_dir()
        claude_md_reference = self._load_claude_md_reference()
        quality_reference = self._load_quality_reference()

        # Build prompt and generate
        prompt = self._build_generation_prompt(
            claude_md_reference,
            quality_reference,
            project_config,
        )

        result = self.orchestrator.generate(prompt, "markdown")

        # Validate generated content
        self._validate_markdown_structure(result.content)

        return ClaudeMdGenerationResult(
            content=result.content,
            token_usage_input=result.token_usage.input_tokens,
            token_usage_output=result.token_usage.output_tokens,
        )
