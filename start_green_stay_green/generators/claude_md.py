"""CLAUDE.md generator.

Generates CLAUDE.md customized to target project.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

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
        orchestrator: AIOrchestrator,
        *,
        reference_dir: Path | None = None,
        quality_ref_path: Path | None = None,
    ) -> None:
        """Initialize ClaudeMdGenerator.

        Args:
            orchestrator: AI orchestrator for generation.
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
        return claude_md_path.read_text()

    def _load_quality_reference(self) -> str:
        """Load MAXIMUM_QUALITY_ENGINEERING.md reference.

        Returns:
            Content of quality reference file.

        Raises:
            FileNotFoundError: If quality reference file not found.
        """
        return self.quality_ref_path.read_text()

    def _build_generation_prompt(
        self,
        claude_md_reference: str,
        quality_reference: str,
        project_config: dict[str, Any],
    ) -> str:
        """Build prompt for CLAUDE.md generation.

        Args:
            claude_md_reference: Reference CLAUDE.md template.
            quality_reference: MAXIMUM_QUALITY_ENGINEERING.md content.
            project_config: Project configuration with name, language, scripts, skills.

        Returns:
            Formatted prompt for AI generation.
        """
        project_name = project_config.get("project_name", "unknown")
        language = project_config.get("language", "unknown")
        scripts = project_config.get("scripts", [])
        skills = project_config.get("skills", [])

        scripts_text = "\n".join(f"- {script}" for script in scripts)
        skills_text = "\n".join(f"- {skill}" for skill in skills)

        prompt_intro = (
            "Generate a customized CLAUDE.md file for a new project based on "
            "the reference CLAUDE.md template and MAXIMUM QUALITY ENGINEERING "
            "standards."
        )
        return f"""{prompt_intro}

PROJECT CONFIGURATION:
- Project Name: {project_name}
- Language: {language}
- Generated Scripts:
{scripts_text if scripts else "  (none)"}
- Generated Skills:
{skills_text if skills else "  (none)"}

REFERENCE CLAUDE.md TEMPLATE:
{claude_md_reference}

MAXIMUM QUALITY ENGINEERING STANDARDS (for context):
{quality_reference}

REQUIREMENTS:
1. Adapt the reference CLAUDE.md to the target project
2. Replace generic examples with {language}-specific examples
3. Document all generated scripts in the Tool Invocation Patterns section
4. Document all generated skills
5. Maintain the same structure and organization as the reference
6. Preserve all critical principles and quality standards
7. Include project-specific commands for {language}
8. Ensure the output is valid markdown with proper H1 title

OUTPUT FORMAT:
Generate the complete customized CLAUDE.md content as valid markdown.
Start with the H1 title and include all sections from the reference template.
"""

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

    def generate(self, project_config: dict[str, Any]) -> ClaudeMdGenerationResult:
        """Generate customized CLAUDE.md for target project.

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
