"""Unit tests for AI Orchestrator data classes and core functionality."""

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import PromptTemplateError
from start_green_stay_green.ai.orchestrator import TokenUsage


class TestTokenUsage:
    """Test TokenUsage data class."""

    def test_token_usage_calculates_total_correctly(self) -> None:
        """Test TokenUsage calculates total tokens correctly."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_token_usage_with_zero_input_tokens(self) -> None:
        """Test TokenUsage handles zero input tokens."""
        usage = TokenUsage(input_tokens=0, output_tokens=50)
        assert usage.total_tokens == 50

    def test_token_usage_with_zero_output_tokens(self) -> None:
        """Test TokenUsage handles zero output tokens."""
        usage = TokenUsage(input_tokens=100, output_tokens=0)
        assert usage.total_tokens == 100

    def test_token_usage_with_all_zero_tokens(self) -> None:
        """Test TokenUsage handles all zero tokens."""
        usage = TokenUsage(input_tokens=0, output_tokens=0)
        assert usage.total_tokens == 0

    def test_token_usage_is_immutable(self) -> None:
        """Test TokenUsage is immutable (frozen dataclass)."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        with pytest.raises(AttributeError):
            usage.input_tokens = 200  # type: ignore[misc]


class TestGenerationResult:
    """Test GenerationResult data class."""

    def test_generation_result_creation_with_all_fields(self) -> None:
        """Test creating GenerationResult with all fields."""
        token_usage = TokenUsage(input_tokens=100, output_tokens=50)
        result = GenerationResult(
            content="Generated YAML content",
            format="yaml",
            token_usage=token_usage,
            model="claude-opus-4-20250514",
            message_id="msg_abc123",
        )
        assert result.content == "Generated YAML content"
        assert result.format == "yaml"
        assert result.token_usage.total_tokens == 150
        assert result.model == "claude-opus-4-20250514"
        assert result.message_id == "msg_abc123"

    def test_generation_result_with_empty_content(self) -> None:
        """Test GenerationResult can have empty content."""
        token_usage = TokenUsage(input_tokens=10, output_tokens=0)
        result = GenerationResult(
            content="",
            format="markdown",
            token_usage=token_usage,
            model="claude-sonnet-4-20250514",
            message_id="msg_def456",
        )
        assert result.content == ""
        assert result.format == "markdown"

    def test_generation_result_is_immutable(self) -> None:
        """Test GenerationResult is immutable (frozen dataclass)."""
        token_usage = TokenUsage(input_tokens=100, output_tokens=50)
        result = GenerationResult(
            content="Test",
            format="yaml",
            token_usage=token_usage,
            model="claude-opus-4-20250514",
            message_id="msg_123",
        )
        with pytest.raises(AttributeError):
            result.content = "Modified"  # type: ignore[misc]


class TestModelConfig:
    """Test ModelConfig constants."""

    def test_model_config_has_opus_constant(self) -> None:
        """Test ModelConfig has OPUS model constant."""
        assert hasattr(ModelConfig, "OPUS")
        assert ModelConfig.OPUS == "claude-opus-4-20250514"

    def test_model_config_has_sonnet_constant(self) -> None:
        """Test ModelConfig has SONNET model constant."""
        assert hasattr(ModelConfig, "SONNET")
        assert ModelConfig.SONNET == "claude-sonnet-4-20250514"

    def test_model_config_constants_are_strings(self) -> None:
        """Test ModelConfig constants are strings."""
        assert isinstance(ModelConfig.OPUS, str)
        assert isinstance(ModelConfig.SONNET, str)


class TestGenerationError:
    """Test GenerationError exception."""

    def test_generation_error_with_message_only(self) -> None:
        """Test creating GenerationError with just a message."""
        error = GenerationError("Generation failed")
        assert str(error) == "Generation failed"
        assert error.cause is None

    def test_generation_error_with_cause(self) -> None:
        """Test creating GenerationError with underlying cause."""
        cause = ValueError("Invalid input")
        error = GenerationError("Generation failed", cause=cause)
        assert str(error) == "Generation failed"
        assert error.cause is cause

    def test_generation_error_is_exception(self) -> None:
        """Test GenerationError inherits from Exception."""
        error = GenerationError("Test error")
        assert isinstance(error, Exception)


class TestPromptTemplateError:
    """Test PromptTemplateError exception."""

    def test_prompt_template_error_with_message(self) -> None:
        """Test creating PromptTemplateError."""
        error = PromptTemplateError("Invalid template")
        assert str(error) == "Invalid template"

    def test_prompt_template_error_is_exception(self) -> None:
        """Test PromptTemplateError inherits from Exception."""
        error = PromptTemplateError("Test error")
        assert isinstance(error, Exception)


class TestAIOrchestrator:
    """Test AIOrchestrator initialization and configuration."""

    def test_orchestrator_initialization_with_valid_api_key(self) -> None:
        """Test AIOrchestrator initializes with valid API key."""
        orchestrator = AIOrchestrator(api_key="test-api-key-123")
        assert orchestrator.api_key == "test-api-key-123"
        assert orchestrator.model == ModelConfig.SONNET

    def test_orchestrator_initialization_with_custom_model(self) -> None:
        """Test AIOrchestrator accepts custom model."""
        orchestrator = AIOrchestrator(
            api_key="test-api-key-123",
            model=ModelConfig.OPUS,
        )
        assert orchestrator.model == ModelConfig.OPUS

    def test_orchestrator_initialization_rejects_empty_api_key(self) -> None:
        """Test AIOrchestrator rejects empty API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="")

    def test_orchestrator_initialization_rejects_whitespace_api_key(self) -> None:
        """Test AIOrchestrator rejects whitespace-only API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="   ")

    def test_orchestrator_initialization_with_retry_parameters(self) -> None:
        """Test AIOrchestrator accepts retry configuration."""
        orchestrator = AIOrchestrator(
            api_key="test-api-key-123",
            max_retries=5,
            retry_delay=2.0,
        )
        assert orchestrator.max_retries == 5
        assert orchestrator.retry_delay == 2.0

    def test_orchestrator_initialization_with_default_retry_parameters(self) -> None:
        """Test AIOrchestrator has sensible retry defaults."""
        orchestrator = AIOrchestrator(api_key="test-api-key-123")
        assert orchestrator.max_retries == 3
        assert orchestrator.retry_delay == 1.0

    def test_orchestrator_initialization_rejects_negative_max_retries(self) -> None:
        """Test AIOrchestrator rejects negative max_retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            AIOrchestrator(api_key="test-api-key-123", max_retries=-1)

    def test_orchestrator_initialization_rejects_negative_retry_delay(self) -> None:
        """Test AIOrchestrator rejects negative retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            AIOrchestrator(api_key="test-api-key-123", retry_delay=-0.5)
