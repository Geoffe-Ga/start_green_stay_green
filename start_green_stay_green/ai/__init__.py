"""AI orchestration layer for content generation.

This module provides the core AI orchestration functionality for generating
quality infrastructure components using Claude API. It handles prompt
construction, context injection, response parsing, and error handling.

Main Components:
    - AIOrchestrator: Main orchestration class for AI-powered generation
    - GenerationResult: Result container with content and metadata
    - TokenUsage: Token usage tracking and reporting
    - ModelConfig: Claude model configuration constants

Exceptions:
    - GenerationError: Raised when AI generation fails
    - PromptTemplateError: Raised for invalid prompt templates

Examples:
    >>> from start_green_stay_green.ai import AIOrchestrator
    >>> orchestrator = AIOrchestrator(api_key="sk-...")
    >>> result = await orchestrator.generate(
    ...     prompt_template="Create README for {language}",
    ...     context={"language": "Python"},
    ...     output_format="markdown",
    ... )
"""

from __future__ import annotations

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import OutputFormat
from start_green_stay_green.ai.orchestrator import PromptTemplateError
from start_green_stay_green.ai.orchestrator import TokenUsage

__all__ = [
    "AIOrchestrator",
    "GenerationError",
    "GenerationResult",
    "ModelConfig",
    "OutputFormat",
    "PromptTemplateError",
    "TokenUsage",
]
