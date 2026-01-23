"""Base generator class for all component generators.

Provides abstract interface for AI-powered component generation with
orchestrator support for generating quality control artifacts.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


class BaseGenerator(ABC):
    """Abstract base class for AI-powered component generators.

    All generators must extend this class and implement the generate()
    method to produce quality control artifacts using AI orchestration.

    Generators can work with or without an orchestrator:
    - With orchestrator: AI-powered customization and tuning
    - Without orchestrator: Template-based or direct copy mode

    Attributes:
        orchestrator: Optional AI orchestrator for generation tasks.
            None indicates graceful degradation to template mode.

    Example:
        >>> class MyGenerator(BaseGenerator):
        ...     def __init__(self, orchestrator: AIOrchestrator | None) -> None:
        ...         super().__init__(orchestrator)
        ...
        ...     def generate(self) -> dict[str, Any]:
        ...         if self.orchestrator:
        ...             return self._generate_with_ai()
        ...         return self._generate_template()
    """

    def __init__(self, orchestrator: AIOrchestrator | None) -> None:
        """Initialize generator with optional AI orchestrator.

        Args:
            orchestrator: Optional AIOrchestrator instance for AI-powered
                generation. If None, generator falls back to template mode.
        """
        self.orchestrator = orchestrator

    @abstractmethod
    def generate(self) -> dict[str, Any]:
        """Generate component content using AI orchestration.

        Implementations should use self.orchestrator to generate content
        tailored to the target project's language and requirements.

        Returns:
            Generated content as a dictionary with component-specific structure.

        Raises:
            GenerationError: If AI generation fails.
            ValueError: If configuration is invalid or incomplete.
            NotImplementedError: If language is not supported.
        """
