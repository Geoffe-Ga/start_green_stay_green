"""Base generator class for all component generators.

Provides abstract interface for generating quality control components
customized to target projects and languages.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GenerationConfig:
    """Configuration for generator execution.

    Attributes:
        project_name: Name of the target project.
        language: Programming language (python, typescript, go, rust, etc.).
        output_path: Path where generated files should be written.
        language_config: Language-specific configuration dictionary.
    """

    project_name: str
    language: str
    output_path: Path
    language_config: dict[str, Any]


class BaseGenerator(ABC):
    """Abstract base class for component generators.

    All generators must extend this class and implement the generate()
    method to produce language-specific quality control artifacts.

    Example:
        >>> class MyGenerator(BaseGenerator):
        ...     def generate(self, config: GenerationConfig) -> str:
        ...         return "Generated content"
    """

    @abstractmethod
    def generate(self, config: GenerationConfig) -> str:
        """Generate component content for target project.

        Implementations should produce configuration or content tailored to
        the project's language and requirements specified in config.

        Args:
            config: Generation configuration with language and project details.

        Returns:
            Generated content as a string (typically YAML, TOML, or script).

        Raises:
            ValueError: If configuration is invalid or incomplete.
            NotImplementedError: If language is not supported.
        """
        pass
