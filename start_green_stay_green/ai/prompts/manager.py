"""Prompt template manager for loading and rendering templates.

This module provides utilities for managing Jinja2-based prompt templates
including caching, validation, and language-specific rendering.
"""

import logging
from pathlib import Path
from typing import Any
from typing import ClassVar

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Template
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape

logger = logging.getLogger(__name__)


class PromptTemplateError(Exception):
    """Raised when prompt template operations fail."""


class PromptManager:
    """Manages loading and rendering prompt templates.

    This class provides a unified interface for loading Jinja2 templates
    from the prompts directory, caching them, and rendering with context.
    Supports language-specific template selection.
    """

    SUPPORTED_LANGUAGES: ClassVar[set[str]] = {
        "python",
        "typescript",
        "go",
        "rust",
        "swift",
        "java",
    }
    SUPPORTED_TEMPLATE_TYPES: ClassVar[set[str]] = {
        "ci_cd",
        "precommit",
        "quality_scripts",
        "claude_md",
        "project_scaffolding",
    }

    def __init__(self, template_dir: Path | None = None) -> None:
        """Initialize the PromptManager.

        Args:
            template_dir: Root directory containing prompt templates.
                If None, uses the package prompts directory.

        Raises:
            PromptTemplateError: If template directory doesn't exist.
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        if not template_dir.exists():
            msg = f"Prompt template directory not found: {template_dir}"
            raise PromptTemplateError(msg)

        self.template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(enabled_extensions=("jinja2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._template_cache: dict[str, Template] = {}

    def _validate_language(self, language: str) -> None:
        """Validate language is supported."""
        if language not in self.SUPPORTED_LANGUAGES:
            msg = (
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_LANGUAGES))}"
            )
            raise ValueError(msg)

    def _build_filename(self, template_name: str, language: str | None) -> str:
        """Build template filename with optional language variant."""
        if language:
            return f"{template_name}.{language}.jinja2"
        return f"{template_name}.jinja2"

    def _get_or_load_template(self, filename: str) -> Template:
        """Get template from cache or load it."""
        if filename not in self._template_cache:
            self._template_cache[filename] = self._env.get_template(filename)
        return self._template_cache[filename]

    def _validate_rendered_content(self, rendered: str, filename: str) -> None:
        """Validate rendered content is not empty."""
        if not rendered or not rendered.strip():
            msg = f"Template {filename} rendered to empty content"
            raise PromptTemplateError(msg)

    def render(
        self,
        template_name: str,
        context: dict[str, Any],
        *,
        language: str | None = None,
    ) -> str:
        """Render a prompt template with the given context.

        Args:
            template_name: Name of the template to render (without .jinja2).
            context: Dictionary of variables to pass to the template.
            language: Optional language variant (python, typescript, go, rust).

        Returns:
            Rendered template as string.

        Raises:
            PromptTemplateError: If template not found or rendering fails.
            ValueError: If language is not supported.
        """
        if language:
            self._validate_language(language)

        filename = self._build_filename(template_name, language)

        try:
            template = self._get_or_load_template(filename)
            rendered = template.render(**context)
            self._validate_rendered_content(rendered, filename)
            return rendered  # noqa: TRY300
        except TemplateNotFound as e:
            msg = f"Prompt template not found: {filename}"
            raise PromptTemplateError(msg) from e
        except Exception as e:
            msg = f"Failed to render template {filename}: {e!s}"
            raise PromptTemplateError(msg) from e

    def get_available_templates(self) -> list[str]:
        """Get list of available template names.

        Returns:
            List of available template base names (without extensions).
        """
        templates = set()
        for template_file in self.template_dir.glob("*.jinja2"):
            # Extract base name, removing language suffix if present
            parts = template_file.stem.split(".")
            base_name = parts[0]
            templates.add(base_name)
        return sorted(templates)

    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and is renderable.

        Args:
            template_name: Name of the template to validate.

        Returns:
            True if template exists and is valid.
        """
        try:
            filename = f"{template_name}.jinja2"
            self._env.get_template(filename)
            return True  # noqa: TRY300 - Boolean validation pattern, clear intent
        except TemplateNotFound:
            return False

    def clear_cache(self) -> None:
        """Clear the template cache.

        Useful for testing or when templates have been modified.
        """
        self._template_cache.clear()
