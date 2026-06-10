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


# Names of the split documentation files emitted under ``.claude/docs/``.
# Order is significant: it mirrors the index links and the on-repo
# ``.claude/docs/`` layout of Start Green Stay Green itself (#397).
CLAUDE_DOC_NAMES: tuple[str, ...] = (
    "principles",
    "quality-standards",
    "workflow",
    "testing",
    "tools",
    "troubleshooting",
)


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

    @staticmethod
    def _missing_doc_files(docs_dir: Path) -> list[str]:
        """Return the names of required split docs absent from ``docs_dir``."""
        return [
            f"{name}.md"
            for name in CLAUDE_DOC_NAMES
            if not (docs_dir / f"{name}.md").is_file()
        ]

    def _validate_docs_dir(self) -> None:
        """Validate the modular ``docs/`` subdirectory and its split files.

        Raises:
            ValueError: If the docs directory or any required split doc
                (see :data:`CLAUDE_DOC_NAMES`) is missing.
        """
        docs_dir = self.reference_dir / "docs"
        if not docs_dir.is_dir():
            msg = f"Reference docs directory not found: {docs_dir}"
            raise ValueError(msg)

        missing = self._missing_doc_files(docs_dir)
        if missing:
            msg = f"Missing reference docs in {docs_dir}: {', '.join(missing)}"
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

    def _load_doc_reference(self, name: str) -> str:
        """Load a single split-doc reference template.

        Args:
            name: Doc stem (one of :data:`CLAUDE_DOC_NAMES`).

        Returns:
            Content of ``reference/claude/docs/<name>.md``.

        Raises:
            FileNotFoundError: If the doc file is missing.
        """
        doc_path = self.reference_dir / "docs" / f"{name}.md"
        return doc_path.read_text(encoding="utf-8")

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

    def _render_docs(self, project_config: dict[str, Any]) -> dict[str, str]:
        """Render the six split docs with token substitution.

        Each doc is rendered with the same deterministic ``{{TOKEN}}``
        substitution used for the index, so project-specific values (e.g.
        ``{{PROJECT_NAME}}`` in the security examples) are filled in.

        Args:
            project_config: Project configuration (see :meth:`write_modular`).

        Returns:
            Mapping of doc stem (e.g. ``"principles"``) to rendered content.
        """
        return {
            name: self._render_baseline(
                self._load_doc_reference(name),
                project_config,
            )
            for name in CLAUDE_DOC_NAMES
        }

    def render_modular(
        self,
        project_config: dict[str, Any],
    ) -> tuple[ClaudeMdGenerationResult, dict[str, str]]:
        """Render the modular tree without writing anything to disk.

        Produces the index content (AI-tuned when an orchestrator is
        configured, deterministic baseline otherwise) and the rendered
        split docs. Callers decide how to persist them (e.g. via a
        conflict-aware ``FileWriter``).

        Args:
            project_config: Project configuration with keys
                ``project_name``, ``language``, ``scripts``, ``skills``.

        Returns:
            A ``(index_result, docs)`` tuple where ``docs`` maps each doc
            stem in :data:`CLAUDE_DOC_NAMES` to its rendered content.

        Raises:
            ValueError: If reference files or the docs directory are invalid.
            FileNotFoundError: If reference files are missing.
        """
        self._validate_reference_dir()
        self._validate_docs_dir()
        index_result = self.generate(project_config)
        docs = self._render_docs(project_config)
        return index_result, docs

    def write_modular(
        self,
        project_root: Path,
        project_config: dict[str, Any],
    ) -> ClaudeMdGenerationResult:
        """Emit the modular ``.claude/`` CLAUDE.md tree into a project.

        Writes the index ``CLAUDE.md`` (a quick-reference that links to the
        split docs) at ``project_root`` plus the six split docs under
        ``project_root/.claude/docs/``. The index is produced by
        :meth:`generate` (AI-tuned when an orchestrator is configured,
        deterministic baseline otherwise); the docs are always emitted
        deterministically with token substitution so no content is lost.

        Args:
            project_root: Target project root directory.
            project_config: Project configuration with keys
                ``project_name``, ``language``, ``scripts``, ``skills``.

        Returns:
            ``ClaudeMdGenerationResult`` for the index (token usage reflects
            the index generation; doc emission is deterministic, zero-cost).

        Raises:
            ValueError: If reference files or the docs directory are invalid.
            FileNotFoundError: If reference files are missing.
        """
        index_result, docs = self.render_modular(project_config)

        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "CLAUDE.md").write_text(
            index_result.content,
            encoding="utf-8",
        )
        docs_dir = project_root / ".claude" / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        for name, content in docs.items():
            (docs_dir / f"{name}.md").write_text(content, encoding="utf-8")

        return index_result
