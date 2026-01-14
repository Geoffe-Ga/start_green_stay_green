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
        self._validate_api_key(api_key)
        self._validate_retry_params(max_retries, retry_delay)

        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @staticmethod
    def _validate_api_key(api_key: str) -> None:
        """Validate API key is not empty.

        Args:
            api_key: API key to validate.

        Raises:
            ValueError: If API key is empty or only whitespace.
        """
        if not api_key or not api_key.strip():
            msg = "API key cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_retry_params(max_retries: int, retry_delay: float) -> None:
        """Validate retry parameters.

        Args:
            max_retries: Maximum number of retries.
            retry_delay: Delay between retries in seconds.

        Raises:
            ValueError: If parameters are invalid.
        """
        if max_retries < 0:
            msg = "max_retries must be non-negative"
            raise ValueError(msg)
        if retry_delay <= 0:
            msg = "retry_delay must be positive"
            raise ValueError(msg)

    @staticmethod
    def _validate_prompt(prompt: str) -> None:
        """Validate prompt is not empty.

        Args:
            prompt: Prompt to validate.

        Raises:
            ValueError: If prompt is empty or only whitespace.
        """
        if not prompt or not prompt.strip():
            msg = "Prompt cannot be empty"
            raise ValueError(msg)

    @staticmethod
    def _validate_output_format(
        output_format: Literal["yaml", "toml", "markdown", "bash"],
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

    def _call_api(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Call Claude API and build result.

        Args:
            client: Anthropic API client.
            prompt: Generation prompt.
            output_format: Desired output format.

        Returns:
            GenerationResult with content and metadata.

        Raises:
            GenerationError: If response is invalid.
        """
        response = client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": f"Generate {output_format} output:\n\n{prompt}",
                },
            ],
        )

        # Extract content from response
        first_block = response.content[0]
        if not isinstance(first_block, TextBlock):
            msg = "Expected TextBlock in response"
            raise GenerationError(msg)

        return GenerationResult(
            content=first_block.text,
            format=output_format,
            token_usage=TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            ),
            model=response.model,
            message_id=response.id,
        )

    def _retry_with_backoff(
        self,
        client: Anthropic,
        prompt: str,
        output_format: str,
    ) -> GenerationResult:
        """Retry API call with exponential backoff.

        Args:
            client: Anthropic API client.
            prompt: Generation prompt.
            output_format: Desired output format.

        Returns:
            GenerationResult on success.

        Raises:
            GenerationError: If all retries exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._call_api(client, prompt, output_format)
            except GenerationError:
                raise
            except Exception as e:  # noqa: BLE001
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2**attempt)
                    time.sleep(delay)
                    continue

        msg = "Failed to generate content"
        raise GenerationError(msg, cause=last_error) from last_error

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
        self._validate_prompt(prompt)
        self._validate_output_format(output_format)

        client = Anthropic(api_key=self.api_key)
        return self._retry_with_backoff(client, prompt, output_format)
