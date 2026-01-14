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

    Attributes:
        orchestrator: AI orchestrator for generation tasks.

    Example:
        >>> class MyGenerator(BaseGenerator):
        ...     def __init__(self, orchestrator: AIOrchestrator) -> None:
        ...         super().__init__(orchestrator)
        ...
        ...     def generate(self) -> dict[str, Any]:
        ...         return {"generated": "content"}
    """

    def __init__(self, orchestrator: AIOrchestrator) -> None:
        """Initialize generator with AI orchestrator.

        Args:
            orchestrator: AIOrchestrator instance for AI-powered generation.
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
