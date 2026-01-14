"""AI generation orchestrator.

Coordinates AI-powered generation tasks using Claude API.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Final
from typing import Literal

from anthropic import Anthropic
from anthropic.types import TextBlock


class GenerationError(Exception):
    """Raised when AI generation fails.

    Attributes:
        cause: Optional underlying exception that caused this error.
    """

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


class ModelConfig:
    """Claude model configuration constants.

    This class provides model identifiers for Claude AI models used
    in generation and tuning operations.
    """

    OPUS: Final[str] = "claude-opus-4-5-20251101"
    SONNET: Final[str] = "claude-sonnet-4-5-20250929"


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
    """Result from AI generation request.

    Attributes:
        content: Generated content from the AI model.
        format: Output format (yaml, toml, markdown, bash).
        token_usage: Token usage statistics for the request.
        model: Model identifier used for generation.
        message_id: Unique identifier for the API message.
    """

    content: str
    format: str
    token_usage: TokenUsage
    model: str
    message_id: str


class AIOrchestrator:
    """Orchestrates AI generation requests using Claude API.

    This class manages API communication, retry logic, and response
    parsing for AI-powered generation tasks.

    Attributes:
        api_key: Claude API key for authentication.
        model: Claude model identifier to use for generation.
        max_retries: Maximum number of retry attempts for failed requests.
        retry_delay: Initial delay in seconds between retry attempts.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model: str = ModelConfig.SONNET,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize AIOrchestrator with configuration.

        Args:
            api_key: Claude API key for authentication.
            model: Claude model identifier. Defaults to SONNET.
            max_retries: Maximum retry attempts. Defaults to 3.
            retry_delay: Initial retry delay in seconds. Defaults to 1.0.

        Raises:
            ValueError: If api_key is empty or parameters are invalid.
        """
        if not api_key or not api_key.strip():
            msg = "API key cannot be empty"
            raise ValueError(msg)
        if max_retries < 0:
            msg = "max_retries must be non-negative"
            raise ValueError(msg)
        if retry_delay <= 0:
            msg = "retry_delay must be positive"
            raise ValueError(msg)

        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _validate_prompt(self, prompt: str) -> None:
        """Validate prompt is not empty.

        Args:
            prompt: Prompt to validate.

        Raises:
            ValueError: If prompt is empty or whitespace-only.
        """
        if not prompt or not prompt.strip():
            msg = "Prompt cannot be empty"
            raise ValueError(msg)

    def _validate_output_format(
        self,
        output_format: str,
    ) -> None:
        """Validate output format is supported.

        Args:
            output_format: Format to validate.

        Raises:
            ValueError: If format is not supported.
        """
        supported_formats = {"yaml", "toml", "markdown", "bash"}
        if output_format not in supported_formats:
            msg = f"Unsupported output format: {output_format}"
            raise ValueError(msg)

    def _extract_content_from_response(self, response: object) -> str:
        """Extract text content from API response.

        Args:
            response: Response object from Claude API.

        Returns:
            Text content from response.

        Raises:
            GenerationError: If response format is invalid.
        """
        first_block = response.content[0]  # type: ignore[index]
        if not isinstance(first_block, TextBlock):
            msg = "Expected TextBlock in response"
            raise GenerationError(msg)
        return first_block.text

    def _build_generation_result(
        self,
        response: object,
        output_format: str,
        content: str,
    ) -> GenerationResult:
        """Build GenerationResult from API response.

        Args:
            response: Response object from Claude API.
            output_format: Output format used.
            content: Generated content text.

        Returns:
            GenerationResult with all metadata.
        """
        return GenerationResult(
            content=content,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,  # type: ignore[attr-defined]
                output_tokens=response.usage.output_tokens,  # type: ignore[attr-defined]
            ),
            model=response.model,  # type: ignore[attr-defined]
            message_id=response.id,  # type: ignore[attr-defined]
        )

    def _make_api_call(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> object:
        """Make API call to Claude.

        Args:
            client: Anthropic client instance.
            prompt: Prompt to send.
            output_format: Desired output format.

        Returns:
            API response object.
        """
        return client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate {output_format} output:\n\n{prompt}",
                },
            ],
        )

    def _handle_retry_backoff(self, attempt: int) -> None:
        """Sleep with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed).
        """
        delay = self.retry_delay * (2**attempt)
        time.sleep(delay)

    def generate(
        self,
        prompt: str,
        output_format: Literal["yaml", "toml", "markdown", "bash"],
    ) -> GenerationResult:
        """Generate content using Claude API.

        Args:
            prompt: Prompt describing what to generate.
            output_format: Desired output format (yaml, toml, markdown, bash).

        Returns:
            GenerationResult containing generated content and metadata.

        Raises:
            ValueError: If prompt is empty or format unsupported.
            GenerationError: If API call fails or response invalid.
        """
        # Validate inputs
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)

        # Retry loop with exponential backoff
        client = Anthropic(api_key=self.api_key)
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._make_api_call(client, prompt, output_format)
                content = self._extract_content_from_response(response)
                return self._build_generation_result(
                    response,
                    output_format,
                    content,
                )

            except GenerationError:
                # Re-raise GenerationError directly without wrapping
                raise
            except Exception as e:  # noqa: BLE001
                last_error = e
                # If we haven't exhausted retries, sleep and try again
                if attempt < self.max_retries:
                    self._handle_retry_backoff(attempt)
                    continue

        # All retries exhausted
        msg = "Failed to generate content"
        raise GenerationError(msg, cause=last_error) from last_error
