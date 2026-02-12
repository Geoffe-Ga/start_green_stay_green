"""Base generator classes and exceptions for component generation.

Provides abstract interfaces for both template-based and AI-powered generation
with clean dependency injection patterns.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from start_green_stay_green.ai.orchestrator import AIOrchestrator

# Single source of truth for all supported languages across generators
SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "python",
    "typescript",
    "go",
    "rust",
    "java",
    "csharp",
    "ruby",
)


def validate_language(language: str) -> None:
    """Validate that a language is supported.

    Args:
        language: Language string to validate.

    Raises:
        ValueError: If the language is not in SUPPORTED_LANGUAGES.
    """
    if language not in SUPPORTED_LANGUAGES:
        supported = ", ".join(SUPPORTED_LANGUAGES)
        msg = (
            f"Unsupported language: '{language}'. " f"Supported languages: {supported}"
        )
        raise ValueError(msg)


class GenerationError(Exception):
    """Base exception for generation failures.

    Raised when a generator cannot complete its operation due to
    validation failures, missing dependencies, or other errors.

    Attributes:
        message: Human-readable error description
        cause: Optional underlying exception that caused this error
    """

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        """Initialize generation error.

        Args:
            message: Error description
            cause: Optional underlying exception
        """
        super().__init__(message)
        self.message = message
        self.cause = cause


class AIGenerationError(GenerationError):
    """Exception for AI-specific generation failures.

    Raised when AI orchestration fails (API errors, timeout, etc.)
    """


class BaseGenerator(ABC):
    """Minimal abstract base class for all generators.

    Defines only the essential interface that all generators must implement.
    Subclasses define their own initialization requirements.

    Example:
        >>> class MyGenerator(BaseGenerator):
        ...     def generate(self) -> dict[str, Any]:
        ...         return {"content": "generated output"}
    """

    @abstractmethod
    def generate(self) -> dict[str, Any]:
        """Generate component content.

        Returns:
            Generated content as a dictionary with component-specific structure

        Raises:
            GenerationError: If generation fails
            ValueError: If configuration is invalid
        """


class TemplateBasedGenerator(BaseGenerator):
    """Base class for Jinja2 template-based generators.

    Provides common functionality for generators that use Jinja2 templates,
    with optional AI orchestration support.

    Attributes:
        orchestrator: Optional AI orchestrator for enhanced generation.
            If None, generator uses pure template-based generation.
        template_dir: Base directory containing Jinja2 templates

    Example:
        >>> class MyTemplateGenerator(TemplateBasedGenerator):
        ...     def __init__(self, orchestrator: AIOrchestrator | None = None):
        ...         super().__init__(orchestrator, Path("templates/my_component"))
        ...
        ...     def generate(self) -> dict[str, Any]:
        ...         # Use self.orchestrator if available for AI enhancement
        ...         return {"content": self._render_template("template.j2")}
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        template_dir: Path | None = None,
    ) -> None:
        """Initialize template-based generator.

        Args:
            orchestrator: Optional AI orchestrator for enhanced generation.
                If None, uses pure template-based generation.
            template_dir: Optional base directory for templates.
                If None, subclass should define its own template management.
        """
        self.orchestrator = orchestrator
        self.template_dir = template_dir

    def _validate_template_path(self, template_name: str) -> Path:
        """Validate that a template file exists.

        Args:
            template_name: Name of template file relative to template_dir

        Returns:
            Absolute path to validated template file

        Raises:
            GenerationError: If template_dir not set or template doesn't exist
        """
        if self.template_dir is None:
            msg = "Template directory not configured for this generator"
            raise GenerationError(msg)

        template_path = self.template_dir / template_name
        if not template_path.exists():
            msg = f"Template not found: {template_path}"
            raise GenerationError(
                msg,
                cause=FileNotFoundError(str(template_path)),
            )

        return template_path
