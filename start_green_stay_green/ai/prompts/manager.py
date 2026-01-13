"""Prompt template manager for loading and rendering templates.

This module provides utilities for managing Jinja2-based prompt templates
including caching, validation, and language-specific rendering.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment
from jinja2 import FileSystemLoader
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

    SUPPORTED_LANGUAGES = {"python", "typescript", "go", "rust", "swift", "java"}
    SUPPORTED_TEMPLATE_TYPES = {
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
            raise PromptTemplateError(
                msg
            )

        self.template_dir = template_dir
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(enabled_extensions=("jinja2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._template_cache: dict[str, Any] = {}

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
        if language and language not in self.SUPPORTED_LANGUAGES:
            msg = (
                f"Unsupported language: {language}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_LANGUAGES))}"
            )
            raise ValueError(
                msg
            )

        # Build template filename with language variant if provided
        if language:
            filename = f"{template_name}.{language}.jinja2"
        else:
            filename = f"{template_name}.jinja2"

        try:
            # Check cache first
            if filename not in self._template_cache:
                self._template_cache[filename] = self._env.get_template(filename)

            template = self._template_cache[filename]
            rendered = template.render(**context)

            if not rendered or not rendered.strip():
                msg = f"Template {filename} rendered to empty content"
                raise PromptTemplateError(
                    msg
                )

            return rendered
        except TemplateNotFound as e:
            msg = f"Prompt template not found: {filename}"
            raise PromptTemplateError(msg) from e
        except Exception as e:
            msg = f"Failed to render template {filename}: {e!s}"
            raise PromptTemplateError(
                msg
            ) from e

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
            return True
        except TemplateNotFound:
            return False

    def clear_cache(self) -> None:
        """Clear the template cache.

        Useful for testing or when templates have been modified.
        """
        self._template_cache.clear()
