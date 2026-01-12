"""Unit tests for AI Orchestrator.

Tests for the core AI orchestration system that coordinates generation tasks
using the Anthropic Claude API. Validates prompt construction, context injection,
response handling, error handling, and retry logic.
"""

from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from anthropic import APIError
from anthropic import APITimeoutError
from anthropic import RateLimitError

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import PromptTemplateError
from start_green_stay_green.ai.orchestrator import TokenUsage

if TYPE_CHECKING:
    pass


@pytest.fixture
def api_key() -> str:
    """Return test API key."""
    return "test-api-key-12345"


@pytest.fixture
def orchestrator(api_key: str) -> AIOrchestrator:
    """Create AIOrchestrator instance for testing."""
    return AIOrchestrator(api_key=api_key)


@pytest.fixture
def mock_anthropic_client() -> Mock:
    """Create mock Anthropic client."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Generated content")]
    mock_message.usage = MagicMock(
        input_tokens=100,
        output_tokens=50,
    )
    mock_message.id = "msg_test123"
    mock_message.model = "claude-opus-4-20250514"
    mock_message.stop_reason = "end_turn"

    mock_client.messages.create = AsyncMock(return_value=mock_message)
    return mock_client


class TestAIOrchestrator:
    """Test AIOrchestrator class."""

    def test_orchestrator_init_with_api_key_creates_client(
        self,
        api_key: str,
    ) -> None:
        """Test orchestrator initializes with valid API key."""
        orchestrator = AIOrchestrator(api_key=api_key)
        assert orchestrator.api_key == api_key
        assert orchestrator.default_model == ModelConfig.OPUS

    def test_orchestrator_init_with_custom_model_uses_model(
        self,
        api_key: str,
    ) -> None:
        """Test orchestrator accepts custom model."""
        orchestrator = AIOrchestrator(
            api_key=api_key,
            model=ModelConfig.SONNET,
        )
        assert orchestrator.default_model == ModelConfig.SONNET

    def test_orchestrator_init_with_empty_api_key_raises_value_error(
        self,
    ) -> None:
        """Test orchestrator raises ValueError for empty API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="")

    def test_orchestrator_init_with_whitespace_api_key_raises_value_error(
        self,
    ) -> None:
        """Test orchestrator raises ValueError for whitespace API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="   ")

    @pytest.mark.asyncio
    async def test_generate_with_valid_inputs_returns_result(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test generate() returns GenerationResult with valid inputs."""
        with patch.object(
            orchestrator,
            "_client",
            mock_anthropic_client,
        ):
            result = await orchestrator.generate(
                prompt_template="Generate a {item}",
                context={"item": "README"},
                output_format="markdown",
            )

            assert isinstance(result, GenerationResult)
            assert result.content == "Generated content"
            assert result.format == "markdown"
            assert result.token_usage.input_tokens == 100
            assert result.token_usage.output_tokens == 50
            assert result.model == "claude-opus-4-20250514"

    @pytest.mark.asyncio
    async def test_generate_with_empty_prompt_raises_prompt_template_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Test generate() raises PromptTemplateError for empty prompt."""
        with pytest.raises(
            PromptTemplateError,
            match="Prompt template cannot be empty",
        ):
            await orchestrator.generate(
                prompt_template="",
                context={},
                output_format="yaml",
            )

    @pytest.mark.asyncio
    async def test_generate_with_missing_context_variables_raises_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Test generate() raises error when context variables are missing."""
        with pytest.raises(
            PromptTemplateError,
            match="Missing required context variable",
        ):
            await orchestrator.generate(
                prompt_template="Generate a {item} for {project}",
                context={"item": "README"},  # Missing 'project'
                output_format="markdown",
            )

    @pytest.mark.asyncio
    async def test_generate_with_invalid_format_raises_value_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Test generate() raises ValueError for invalid output format."""
        with pytest.raises(ValueError, match="Invalid output format"):
            await orchestrator.generate(
                prompt_template="Generate content",
                context={},
                output_format="invalid",  # type: ignore[arg-type]
            )

    @pytest.mark.asyncio
    async def test_generate_with_api_timeout_retries_and_raises(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test generate() retries on timeout and eventually raises."""
        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=APITimeoutError("Timeout"),
        )

        with (
            patch.object(orchestrator, "_client", mock_anthropic_client),
            pytest.raises(GenerationError, match="Generation failed after"),
        ):
            await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )

        # Should retry 3 times (default)
        assert mock_anthropic_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_with_rate_limit_retries_with_backoff(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test generate() handles rate limits with exponential backoff."""
        call_count = 0

        async def rate_limit_then_success(*args: Any, **kwargs: Any) -> Mock:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("Rate limit exceeded")
            # Success on third try
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Success")]
            mock_message.usage = MagicMock(input_tokens=10, output_tokens=5)
            mock_message.id = "msg_success"
            mock_message.model = "claude-opus-4-20250514"
            mock_message.stop_reason = "end_turn"
            return mock_message

        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=rate_limit_then_success,
        )

        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )

            assert result.content == "Success"
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_generate_tracks_token_usage_correctly(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test generate() accurately tracks token usage."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.generate(
                prompt_template="Test prompt",
                context={},
                output_format="yaml",
            )

            assert result.token_usage.input_tokens == 100
            assert result.token_usage.output_tokens == 50
            assert result.token_usage.total_tokens == 150

    @pytest.mark.asyncio
    async def test_tune_with_valid_inputs_returns_tuned_content(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test tune() returns tuned content with valid inputs."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Tuned content")]
        mock_message.usage = MagicMock(input_tokens=50, output_tokens=25)
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=mock_message,
        )

        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.tune(
                content="Original content",
                target_context="Python project",
            )

            assert result == "Tuned content"

    @pytest.mark.asyncio
    async def test_tune_uses_sonnet_model_by_default(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test tune() uses Sonnet model by default."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            await orchestrator.tune(
                content="Content",
                target_context="Context",
            )

            call_kwargs = mock_anthropic_client.messages.create.call_args[1]
            assert call_kwargs["model"] == ModelConfig.SONNET

    @pytest.mark.asyncio
    async def test_tune_with_custom_model_uses_specified_model(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test tune() accepts custom model parameter."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            await orchestrator.tune(
                content="Content",
                target_context="Context",
                model=ModelConfig.OPUS,
            )

            call_kwargs = mock_anthropic_client.messages.create.call_args[1]
            assert call_kwargs["model"] == ModelConfig.OPUS

    @pytest.mark.asyncio
    async def test_tune_with_empty_content_raises_value_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Test tune() raises ValueError for empty content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            await orchestrator.tune(
                content="",
                target_context="Context",
            )

    @pytest.mark.asyncio
    async def test_tune_with_empty_context_raises_value_error(
        self,
        orchestrator: AIOrchestrator,
    ) -> None:
        """Test tune() raises ValueError for empty target context."""
        with pytest.raises(ValueError, match="Target context cannot be empty"):
            await orchestrator.tune(
                content="Content",
                target_context="",
            )

    @pytest.mark.asyncio
    async def test_context_injection_formats_variables_correctly(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test context variables are properly injected into prompts."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            await orchestrator.generate(
                prompt_template="Create {item} for {lang} project",
                context={"item": "README", "lang": "Python"},
                output_format="markdown",
            )

            call_args = mock_anthropic_client.messages.create.call_args[1]
            prompt = call_args["messages"][0]["content"]
            assert "README" in prompt
            assert "Python" in prompt

    @pytest.mark.asyncio
    async def test_response_validation_rejects_empty_content(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test response validation rejects empty content."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="")]
        mock_anthropic_client.messages.create = AsyncMock(
            return_value=mock_message,
        )

        with (
            patch.object(orchestrator, "_client", mock_anthropic_client),
            pytest.raises(GenerationError, match="Empty response"),
        ):
            await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )

    @pytest.mark.asyncio
    async def test_api_error_handling_raises_generation_error(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test API errors are wrapped in GenerationError."""
        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=APIError("API Error"),
        )

        with (
            patch.object(orchestrator, "_client", mock_anthropic_client),
            pytest.raises(GenerationError, match="Generation failed"),
        ):
            await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )


class TestGenerationResult:
    """Test GenerationResult data class."""

    def test_generation_result_creation_with_valid_data(self) -> None:
        """Test GenerationResult can be created with valid data."""
        token_usage = TokenUsage(
            input_tokens=100,
            output_tokens=50,
        )
        result = GenerationResult(
            content="Test content",
            format="yaml",
            token_usage=token_usage,
            model="claude-opus-4-20250514",
            message_id="msg_123",
        )

        assert result.content == "Test content"
        assert result.format == "yaml"
        assert result.token_usage.total_tokens == 150
        assert result.model == "claude-opus-4-20250514"
        assert result.message_id == "msg_123"


class TestTokenUsage:
    """Test TokenUsage data class."""

    def test_token_usage_calculates_total_correctly(self) -> None:
        """Test TokenUsage calculates total tokens correctly."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_token_usage_with_zero_tokens(self) -> None:
        """Test TokenUsage handles zero tokens."""
        usage = TokenUsage(input_tokens=0, output_tokens=0)
        assert usage.total_tokens == 0


class TestModelConfig:
    """Test ModelConfig constants."""

    def test_model_config_has_opus_model(self) -> None:
        """Test ModelConfig defines Opus model."""
        assert ModelConfig.OPUS == "claude-opus-4-20250514"

    def test_model_config_has_sonnet_model(self) -> None:
        """Test ModelConfig defines Sonnet model."""
        assert ModelConfig.SONNET == "claude-sonnet-4-20250514"


class TestPromptTemplateLoading:
    """Test prompt template loading functionality."""

    @pytest.mark.asyncio
    async def test_load_template_from_string_succeeds(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test loading prompt template from string."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.generate(
                prompt_template="Simple template",
                context={},
                output_format="yaml",
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_load_template_with_multiple_variables(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test template with multiple context variables."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.generate(
                prompt_template="{a} {b} {c}",
                context={"a": "1", "b": "2", "c": "3"},
                output_format="yaml",
            )
            assert result is not None


class TestErrorHandling:
    """Test error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_retry_logic_respects_max_retries(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test retry logic respects maximum retry count."""
        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=APITimeoutError("Timeout"),
        )

        with (
            patch.object(orchestrator, "_client", mock_anthropic_client),
            pytest.raises(GenerationError),
        ):
            await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )

        assert mock_anthropic_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_increases_delay(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
    ) -> None:
        """Test exponential backoff increases delay between retries."""
        delays: list[float] = []

        async def track_delay(*args: Any, **kwargs: Any) -> None:
            import asyncio
            import time

            current = time.time()
            if delays:
                delay = current - delays[-1]
                delays.append(delay)
            else:
                delays.append(current)
            raise APITimeoutError("Timeout")

        mock_anthropic_client.messages.create = AsyncMock(
            side_effect=track_delay,
        )

        with (
            patch.object(orchestrator, "_client", mock_anthropic_client),
            pytest.raises(GenerationError),
        ):
            await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format="yaml",
            )

        # Verify delays increase (exponential backoff)
        if len(delays) > 2:
            assert delays[2] > delays[1]


class TestOutputFormatValidation:
    """Test output format validation."""

    @pytest.mark.parametrize(
        "format_type",
        ["yaml", "toml", "markdown", "bash"],
    )
    @pytest.mark.asyncio
    async def test_valid_output_formats_accepted(
        self,
        orchestrator: AIOrchestrator,
        mock_anthropic_client: Mock,
        format_type: str,
    ) -> None:
        """Test all valid output formats are accepted."""
        with patch.object(orchestrator, "_client", mock_anthropic_client):
            result = await orchestrator.generate(
                prompt_template="Test",
                context={},
                output_format=format_type,  # type: ignore[arg-type]
            )
            assert result.format == format_type
