"""AI generation orchestrator.

Coordinates AI-powered generation tasks using Claude API.
Manages prompt construction, context injection, response handling,
error handling, and retry logic with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from typing import Literal
from typing import TYPE_CHECKING

from anthropic import APIError
from anthropic import APITimeoutError
from anthropic import Anthropic
from anthropic import RateLimitError

if TYPE_CHECKING:
    from anthropic.types import Message

logger = logging.getLogger(__name__)

# Type alias for output formats
OutputFormat = Literal["yaml", "toml", "markdown", "bash"]

# Error messages
_ERR_EMPTY_API_KEY = "API key cannot be empty"
_ERR_EMPTY_PROMPT = "Prompt template cannot be empty"
_ERR_EMPTY_CONTENT = "Content cannot be empty"
_ERR_EMPTY_CONTEXT = "Target context cannot be empty"
_ERR_INVALID_FORMAT = "Invalid output format"
_ERR_MISSING_CONTEXT_VAR = "Missing required context variable"
_ERR_EMPTY_RESPONSE = "Empty response received from API"
_ERR_GENERATION_FAILED = "Generation failed after all retries"
_ERR_API_ERROR = "API error during generation"


class ModelConfig:
    """Claude model configuration constants."""

    OPUS: str = "claude-opus-4-20250514"
    SONNET: str = "claude-sonnet-4-20250514"


class GenerationError(Exception):
    """Raised when AI generation fails."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        """Initialize GenerationError.

        Args:
            message: Error message describing the failure.
            cause: Optional underlying exception that caused this error.
        """
        super().__init__(message)
        self.cause = cause


class PromptTemplateError(Exception):
    """Raised when prompt template is invalid or malformed."""


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for AI generation request.

    Attributes:
        model: Claude model identifier to use. If None, uses orchestrator default.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature (0.0-1.0).
    """

    model: str | None = None
    max_tokens: int = 4096
    temperature: float = 1.0


@dataclass(frozen=True)
class TokenUsage:
    """Token usage information from API response.

    Attributes:
        input_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens in the response.
    """

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used.

        Returns:
            Sum of input and output tokens.
        """
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class GenerationResult:
    """Result of an AI generation task.

    Attributes:
        content: Generated content from the AI.
        format: Output format of the generated content.
        token_usage: Token usage statistics.
        model: Model identifier used for generation.
        message_id: Unique message identifier from API.
    """

    content: str
    format: OutputFormat
    token_usage: TokenUsage
    model: str
    message_id: str


class AIOrchestrator:
    """Coordinates AI-powered generation tasks.

    Manages the complete lifecycle of AI-assisted content generation including
    prompt template processing, context injection, API communication, response
    parsing, error handling, and retry logic with exponential backoff.

    Examples:
        >>> orchestrator = AIOrchestrator(api_key="sk-...")
        >>> result = await orchestrator.generate(
        ...     prompt_template="Create README for {language} project",
        ...     context={"language": "Python"},
        ...     output_format="markdown",
        ... )
        >>> print(result.content)

    Attributes:
        api_key: Anthropic API key for authentication.
        default_model: Default Claude model to use for generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = ModelConfig.OPUS,
        *,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        """Initialize AIOrchestrator.

        Args:
            api_key: Anthropic API key. Cannot be empty or whitespace.
            model: Claude model identifier. Defaults to Opus.
            max_retries: Maximum number of retry attempts for failed requests.
                Defaults to 3.
            initial_retry_delay: Initial delay in seconds before first retry.
                Defaults to 1.0.
            max_retry_delay: Maximum delay in seconds between retries.
                Defaults to 60.0.

        Raises:
            ValueError: If api_key is empty or contains only whitespace.
        """
        if not api_key or not api_key.strip():
            raise ValueError(_ERR_EMPTY_API_KEY)

        self.api_key = api_key
        self.default_model = model
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay
        self._max_retry_delay = max_retry_delay
        self._client = Anthropic(api_key=api_key)

        logger.info(
            "AIOrchestrator initialized with model=%s, max_retries=%d",
            model,
            max_retries,
        )

    async def generate(
        self,
        prompt_template: str,
        context: dict[str, str],
        output_format: OutputFormat,
        *,
        config: GenerationConfig | None = None,
    ) -> GenerationResult:
        """Generate content using AI with injected context.

        Constructs a prompt from the template and context, sends it to the
        Claude API, and returns the parsed result with metadata.

        Args:
            prompt_template: Prompt template with {variable} placeholders.
            context: Dictionary of variables to inject into template.
            output_format: Desired output format (yaml, toml, markdown, bash).
            config: Generation configuration (model, tokens, temperature).
                Defaults to orchestrator settings if not provided.

        Returns:
            GenerationResult containing generated content and metadata.

        Raises:
            PromptTemplateError: If template is empty or context variables missing.
            ValueError: If output_format is not a valid format.
            GenerationError: If generation fails after all retries.

        Examples:
            >>> result = await orchestrator.generate(
            ...     prompt_template="Write {doc_type} for {project}",
            ...     context={"doc_type": "README", "project": "MyApp"},
            ...     output_format="markdown",
            ... )
            >>> assert result.format == "markdown"
            >>> assert "MyApp" in result.content
        """
        # Use default config if not provided
        if config is None:
            config = GenerationConfig()
        # Validate prompt template
        if not prompt_template or not prompt_template.strip():
            raise PromptTemplateError(_ERR_EMPTY_PROMPT)

        # Validate output format
        valid_formats = {"yaml", "toml", "markdown", "bash"}
        if output_format not in valid_formats:
            msg = (
                f"{_ERR_INVALID_FORMAT}: {output_format}. "
                f"Must be one of {valid_formats}"
            )
            raise ValueError(msg)

        # Inject context into template
        try:
            prompt = self._inject_context(prompt_template, context)
        except KeyError as e:
            msg = f"{_ERR_MISSING_CONTEXT_VAR}: {e}"
            raise PromptTemplateError(msg) from e

        # Prepare format-specific instructions
        format_instructions = self._get_format_instructions(output_format)
        full_prompt = f"{prompt}\n\n{format_instructions}"

        # Generate with retry logic
        model_to_use = config.model or self.default_model
        message = await self._generate_with_retry(
            prompt=full_prompt,
            model=model_to_use,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        # Parse and validate response
        content = self._extract_content(message)
        if not content or not content.strip():
            raise GenerationError(_ERR_EMPTY_RESPONSE)

        # Build result
        token_usage = TokenUsage(
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

        result = GenerationResult(
            content=content,
            format=output_format,
            token_usage=token_usage,
            model=message.model,
            message_id=message.id,
        )

        logger.info(
            "Generation successful: model=%s, tokens=%d, format=%s",
            result.model,
            result.token_usage.total_tokens,
            result.format,
        )

        return result

    async def tune(
        self,
        content: str,
        target_context: str,
        model: str = ModelConfig.SONNET,
        *,
        max_tokens: int = 4096,
    ) -> str:
        r"""Lightweight tuning pass to adapt content to specific repo.

        Takes existing content and adapts it to match the target repository's
        context, conventions, and requirements. Uses a lighter model by default
        for cost efficiency.

        Args:
            content: Original content to tune.
            target_context: Description of target repository context.
            model: Model to use for tuning. Defaults to Sonnet.
            max_tokens: Maximum tokens in response. Defaults to 4096.

        Returns:
            Tuned content adapted to target context.

        Raises:
            ValueError: If content or target_context is empty.
            GenerationError: If tuning fails after all retries.

        Examples:
            >>> tuned = await orchestrator.tune(
            ...     content="# Generic README\n...",
            ...     target_context="Python project using pytest and black",
            ... )
            >>> assert "pytest" in tuned or "black" in tuned
        """
        # Validate inputs
        if not content or not content.strip():
            raise ValueError(_ERR_EMPTY_CONTENT)
        if not target_context or not target_context.strip():
            raise ValueError(_ERR_EMPTY_CONTEXT)

        # Construct tuning prompt
        prompt = self._build_tuning_prompt(content, target_context)

        # Generate tuned content
        message = await self._generate_with_retry(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=0.7,  # Lower temperature for more consistent tuning
        )

        # Extract and return tuned content
        tuned_content = self._extract_content(message)

        logger.info(
            "Tuning successful: model=%s, tokens=%d",
            message.model,
            message.usage.input_tokens + message.usage.output_tokens,
        )

        return tuned_content

    def _inject_context(
        self,
        template: str,
        context: dict[str, str],
    ) -> str:
        """Inject context variables into prompt template.

        Args:
            template: Template string with {variable} placeholders.
            context: Dictionary mapping variable names to values.

        Returns:
            Template with all variables replaced by their values.

        Raises:
            KeyError: If template references undefined context variable.
        """
        return template.format(**context)

    def _get_format_instructions(self, output_format: OutputFormat) -> str:
        """Get format-specific instructions for the AI.

        Args:
            output_format: Desired output format.

        Returns:
            Instructions to append to prompt for format compliance.
        """
        instructions = {
            "yaml": (
                "Output must be valid YAML. "
                "Use proper indentation (2 spaces). "
                "Include comments for complex sections."
            ),
            "toml": (
                "Output must be valid TOML. "
                "Use sections appropriately. "
                "Include comments for clarity."
            ),
            "markdown": (
                "Output must be valid Markdown. "
                "Use proper heading hierarchy. "
                "Include code blocks with language tags."
            ),
            "bash": (
                "Output must be a valid bash script. "
                "Include shebang (#!/usr/bin/env bash). "
                "Add error handling (set -euo pipefail). "
                "Include comments explaining each section."
            ),
        }
        return instructions[output_format]

    def _build_tuning_prompt(self, content: str, target_context: str) -> str:
        """Build prompt for content tuning.

        Args:
            content: Original content to tune.
            target_context: Target repository context.

        Returns:
            Formatted tuning prompt.
        """
        return f"""Adapt the following content to match this context: {target_context}

Maintain the core structure and purpose, but adjust:
- Terminology and naming conventions
- Tool and framework references
- Best practices and standards
- Examples and documentation

Original content:
{content}

Provide the tuned content:"""

    async def _generate_with_retry(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> Message:
        """Generate content with retry logic and exponential backoff.

        Args:
            prompt: Full prompt to send to API.
            model: Model identifier to use.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            Message response from API.

        Raises:
            GenerationError: If all retry attempts fail.
        """
        last_error: Exception | None = None
        delay = self._initial_retry_delay

        for attempt in range(self._max_retries):
            try:
                # Call API
                message = await asyncio.to_thread(
                    self._client.messages.create,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                )
            except RateLimitError as e:
                last_error = e
                logger.warning(
                    "Rate limit hit on attempt %d/%d, retrying in %.1fs",
                    attempt + 1,
                    self._max_retries,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._max_retry_delay)

            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    "Timeout on attempt %d/%d, retrying in %.1fs",
                    attempt + 1,
                    self._max_retries,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._max_retry_delay)

            except APIError as e:
                # Don't retry on general API errors
                msg = f"{_ERR_API_ERROR}: {e}"
                raise GenerationError(msg, cause=e) from e
            else:
                # Success - return the message
                return message

        # All retries exhausted
        msg = f"{_ERR_GENERATION_FAILED} after {self._max_retries} attempts"
        raise GenerationError(msg, cause=last_error)

    def _extract_content(self, message: Message) -> str:
        """Extract text content from API message response.

        Args:
            message: Message response from Anthropic API.

        Returns:
            Extracted text content.
        """
        if not message.content:
            return ""

        # Messages can have multiple content blocks; concatenate text blocks
        text_parts = [
            block.text
            for block in message.content
            if hasattr(block, "text")
        ]
        return "".join(text_parts)
