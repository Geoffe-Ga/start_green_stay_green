"""Unit tests for AI Orchestrator data classes and core functionality."""

from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import create_autospec
from unittest.mock import patch

from anthropic.types import TextBlock
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

    def test_token_usage_input_tokens_exact_value(self) -> None:
        """Test TokenUsage stores exact input_tokens value (kills mutants)."""
        usage = TokenUsage(input_tokens=42, output_tokens=10)
        assert usage.input_tokens == 42
        assert usage.input_tokens != 41
        assert usage.input_tokens != 43

    def test_token_usage_output_tokens_exact_value(self) -> None:
        """Test TokenUsage stores exact output_tokens value (kills mutants)."""
        usage = TokenUsage(input_tokens=10, output_tokens=55)
        assert usage.output_tokens == 55
        assert usage.output_tokens != 54
        assert usage.output_tokens != 56


class TestGenerationResult:
    """Test GenerationResult data class."""

    def test_generation_result_creation_with_all_fields(self) -> None:
        """Test creating GenerationResult with all fields."""
        token_usage = TokenUsage(input_tokens=100, output_tokens=50)
        result = GenerationResult(
            content="Generated YAML content",
            format="yaml",
            token_usage=token_usage,
            model="claude-opus-4-5-20251101",
            message_id="msg_abc123",
        )
        assert result.content == "Generated YAML content"
        assert result.format == "yaml"
        assert result.token_usage.total_tokens == 150
        assert result.model == "claude-opus-4-5-20251101"
        assert result.message_id == "msg_abc123"

    def test_generation_result_with_empty_content(self) -> None:
        """Test GenerationResult can have empty content."""
        token_usage = TokenUsage(input_tokens=10, output_tokens=0)
        result = GenerationResult(
            content="",
            format="markdown",
            token_usage=token_usage,
            model="claude-sonnet-4-5-20250929",
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
            model="claude-opus-4-5-20251101",
            message_id="msg_123",
        )
        with pytest.raises(AttributeError):
            result.content = "Modified"  # type: ignore[misc]


class TestModelConfig:
    """Test ModelConfig constants."""

    def test_model_config_has_opus_constant(self) -> None:
        """Test ModelConfig has OPUS model constant."""
        assert hasattr(ModelConfig, "OPUS")
        assert ModelConfig.OPUS == "claude-opus-4-5-20251101"

    def test_model_config_has_sonnet_constant(self) -> None:
        """Test ModelConfig has SONNET model constant."""
        assert hasattr(ModelConfig, "SONNET")
        assert ModelConfig.SONNET == "claude-sonnet-4-5-20250929"

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

    def test_orchestrator_stores_exact_api_key_value(self) -> None:
        """Test AIOrchestrator stores exact API key value (kills mutants).

        This test verifies the exact API key is stored, killing mutants that
        might truncate, modify, or hash the key incorrectly.
        """
        test_key = "test-api-key-with-special-chars-123!@#"
        orchestrator = AIOrchestrator(api_key=test_key)
        # Verify exact key is stored (not truncated or modified)
        assert orchestrator.api_key == test_key
        # Verify it's a string type
        assert isinstance(orchestrator.api_key, str)
        # Verify length is preserved
        assert len(orchestrator.api_key) == len(test_key)
        # Verify special characters are preserved
        assert "!" in orchestrator.api_key
        assert "@" in orchestrator.api_key

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

    def test_orchestrator_stores_exact_max_retries_value(self) -> None:
        """Test AIOrchestrator stores exact max_retries value (kills mutants).

        This test verifies the exact value is stored, killing mutants that
        might change == to !=, or >= to >, or subtract/add values.
        """
        orchestrator = AIOrchestrator(api_key="test-api-key-123", max_retries=5)
        # Verify exact value (not just >= or <=)
        assert orchestrator.max_retries == 5
        # Boundary check: not greater than
        assert not orchestrator.max_retries > 5
        # Boundary check: not less than
        assert not orchestrator.max_retries < 5

    def test_orchestrator_initialization_rejects_negative_max_retries(self) -> None:
        """Test AIOrchestrator rejects negative max_retries."""
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            AIOrchestrator(api_key="test-api-key-123", max_retries=-1)

    def test_orchestrator_initialization_rejects_negative_retry_delay(self) -> None:
        """Test AIOrchestrator rejects negative retry_delay."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            AIOrchestrator(api_key="test-api-key-123", retry_delay=-0.5)

    def test_orchestrator_stores_exact_retry_delay_value(self) -> None:
        """Test AIOrchestrator stores exact retry_delay value (kills mutants).

        This test verifies the exact value is stored, killing mutants that
        might change == to !=, or >= to >, or subtract/add to the value.
        """
        orchestrator = AIOrchestrator(api_key="test-api-key-123", retry_delay=3.5)
        # Verify exact value (not just >= or <=)
        assert orchestrator.retry_delay == 3.5
        # Boundary check: not greater than
        assert not orchestrator.retry_delay > 3.5
        # Boundary check: not less than
        assert not orchestrator.retry_delay < 3.5
        # Verify it's a float, not accidentally converted to int
        assert isinstance(orchestrator.retry_delay, float)

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_with_valid_prompt_returns_result(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate returns GenerationResult with valid prompt."""
        # Setup mock API response
        mock_client = mock_anthropic.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.id = "msg_test123"

        # Create a proper TextBlock mock
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Generated YAML content"
        mock_response.content = [text_block]

        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.model = ModelConfig.SONNET
        mock_client.messages.create.return_value = mock_response

        result = AIOrchestrator(api_key="test-api-key").generate(
            prompt="Generate test config",
            output_format="yaml",
        )

        assert isinstance(result, GenerationResult)
        assert result.content == "Generated YAML content"
        assert result.format == "yaml"
        assert result.token_usage.input_tokens == 100
        assert result.token_usage.output_tokens == 50
        assert result.model == ModelConfig.SONNET
        assert result.message_id == "msg_test123"

    def test_generate_with_empty_prompt_raises_error(self) -> None:
        """Test generate rejects empty prompt."""
        orchestrator = AIOrchestrator(api_key="test-api-key")
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            orchestrator.generate(prompt="", output_format="yaml")

    def test_generate_with_whitespace_prompt_raises_error(self) -> None:
        """Test generate rejects whitespace-only prompt."""
        orchestrator = AIOrchestrator(api_key="test-api-key")
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            orchestrator.generate(prompt="   ", output_format="yaml")

    def test_generate_with_unsupported_format_raises_error(self) -> None:
        """Test generate rejects unsupported output format."""
        orchestrator = AIOrchestrator(api_key="test-api-key")
        with pytest.raises(ValueError, match="Unsupported output format"):
            orchestrator.generate(
                prompt="Generate config",
                output_format="invalid_format",  # type: ignore[arg-type]
            )

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_supports_all_output_formats(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate accepts all supported output formats."""
        # Setup mock API response
        mock_client = mock_anthropic.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.id = "msg_test123"

        # Create a proper TextBlock mock
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "content"
        mock_response.content = [text_block]

        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET
        mock_client.messages.create.return_value = mock_response

        orchestrator = AIOrchestrator(api_key="test-api-key")

        # All these should succeed
        for fmt in ("yaml", "toml", "markdown", "bash"):
            result = orchestrator.generate(
                prompt="Generate content",
                output_format=fmt,
            )
            assert result.format == fmt

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_api_error_raises_generation_error(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate wraps API errors in GenerationError."""
        # Setup mock to raise an exception
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        api_error = Exception("API connection failed")
        mock_client.messages.create.side_effect = api_error

        orchestrator = AIOrchestrator(api_key="test-api-key")

        with pytest.raises(GenerationError, match="Failed to generate content"):
            orchestrator.generate(prompt="Generate config", output_format="yaml")

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_creates_client_with_api_key(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate initializes Anthropic client with API key."""
        # Setup mock API response
        mock_client = mock_anthropic.return_value = MagicMock()
        mock_response = MagicMock()
        mock_response.id = "msg_test123"

        # Create a proper TextBlock mock
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "content"
        mock_response.content = [text_block]

        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET
        mock_client.messages.create.return_value = mock_response

        orchestrator = AIOrchestrator(api_key="my-secret-key")
        orchestrator.generate(prompt="Test prompt", output_format="yaml")

        # Verify Anthropic was called with correct API key
        mock_anthropic.assert_called_once_with(api_key="my-secret-key")

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_retries_on_failure(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test generate retries on API failures."""
        # Setup mock to fail twice, then succeed
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create successful response
        mock_response = MagicMock()
        mock_response.id = "msg_success"
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Success after retries"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET

        # Fail twice, then succeed
        mock_client.messages.create.side_effect = [
            Exception("Temporary API error"),
            Exception("Another temporary error"),
            mock_response,
        ]

        result = AIOrchestrator(api_key="test-key", max_retries=3).generate(
            prompt="Test", output_format="yaml"
        )

        # Should succeed after retries
        assert result.content == "Success after retries"
        # Should have called API 3 times (2 failures + 1 success)
        assert mock_client.messages.create.call_count == 3
        # Should have slept twice (after each failure)
        assert mock_sleep.call_count == 2

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_exponential_backoff(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test generate uses exponential backoff for retries."""
        # Setup mock to fail twice, then succeed
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.id = "msg_success"
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Success"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET

        mock_client.messages.create.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            mock_response,
        ]

        orchestrator = AIOrchestrator(
            api_key="test-key",
            max_retries=3,
            retry_delay=1.0,
        )
        orchestrator.generate(prompt="Test", output_format="yaml")

        # Verify exponential backoff: 1.0, 2.0 seconds
        mock_sleep.assert_has_calls([call(1.0), call(2.0)])

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_max_retries_exceeded(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test generate raises error when max retries exceeded."""
        # Setup mock to always fail
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Persistent API error")

        orchestrator = AIOrchestrator(api_key="test-key", max_retries=2)

        with pytest.raises(GenerationError, match="Failed to generate content"):
            orchestrator.generate(prompt="Test", output_format="yaml")

        # Should have tried 3 times (initial + 2 retries)
        assert mock_client.messages.create.call_count == 3
        # Should have slept 2 times (after first 2 failures)
        assert mock_sleep.call_count == 2

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_no_retry_on_success(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate does not retry on immediate success."""
        # Setup mock to succeed immediately
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.id = "msg_success"
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Immediate success"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET
        mock_client.messages.create.return_value = mock_response

        result = AIOrchestrator(api_key="test-key", max_retries=3).generate(
            prompt="Test", output_format="yaml"
        )

        # Should succeed immediately
        assert result.content == "Immediate success"
        # Should have called API only once
        mock_client.messages.create.assert_called_once()


class TestMutationKillers:
    """Targeted tests to kill specific mutations and achieve 80%+ mutation score.

    These tests explicitly verify exact values, boundary conditions, and
    arithmetic operations to ensure mutations are caught.
    """

    def test_token_usage_total_tokens_exact_sum(self) -> None:
        """Test total_tokens is EXACTLY input_tokens + output_tokens.

        Kills mutations: + → -, + → *, + → /
        """
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150
        assert usage.total_tokens == usage.input_tokens + usage.output_tokens
        assert usage.total_tokens != usage.input_tokens - usage.output_tokens
        assert usage.total_tokens != usage.input_tokens * usage.output_tokens

    def test_token_usage_total_tokens_edge_cases(self) -> None:
        """Test total_tokens with zero and boundary values.

        Kills mutations in edge case handling.
        """
        # Zero inputs
        usage_zero = TokenUsage(input_tokens=0, output_tokens=0)
        assert usage_zero.total_tokens == 0

        # One zero
        usage_one_zero = TokenUsage(input_tokens=100, output_tokens=0)
        assert usage_one_zero.total_tokens == 100

        # Large values
        usage_large = TokenUsage(input_tokens=10000, output_tokens=5000)
        assert usage_large.total_tokens == 15000

    def test_orchestrator_init_max_retries_zero_is_valid(self) -> None:
        """Test max_retries=0 is valid (no retries, single attempt).

        Kills mutations: < 0 → <= 0
        """
        orchestrator = AIOrchestrator(api_key="test-key", max_retries=0)
        assert orchestrator.max_retries == 0

    def test_orchestrator_init_max_retries_negative_raises(self) -> None:
        """Test max_retries < 0 raises ValueError.

        Ensures boundary condition is correct: < 0, not <= 0.
        """
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            AIOrchestrator(api_key="test-key", max_retries=-1)

    def test_orchestrator_init_retry_delay_zero_raises(self) -> None:
        """Test retry_delay=0.0 raises ValueError.

        Kills mutations: <= 0 → < 0
        """
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            AIOrchestrator(api_key="test-key", retry_delay=0.0)

    def test_orchestrator_init_retry_delay_negative_raises(self) -> None:
        """Test retry_delay < 0 raises ValueError."""
        with pytest.raises(ValueError, match="retry_delay must be positive"):
            AIOrchestrator(api_key="test-key", retry_delay=-0.5)

    def test_orchestrator_init_retry_delay_very_small_positive_valid(
        self,
    ) -> None:
        """Test very small positive retry_delay is valid.

        Ensures boundary is > 0, not >= some minimum.
        """
        orchestrator = AIOrchestrator(api_key="test-key", retry_delay=0.001)
        assert orchestrator.retry_delay == 0.001

    def test_orchestrator_init_api_key_empty_string_raises(self) -> None:
        """Test empty string api_key raises ValueError."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="")

    def test_orchestrator_init_api_key_whitespace_only_raises(self) -> None:
        """Test whitespace-only api_key raises ValueError.

        Kills mutations: or → and in validation logic.
        """
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="   ")

        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="\t\n  ")

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_retry_delay_exact_exponential_backoff(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test retry delays follow EXACT exponential backoff formula.

        Kills mutations:
        - 2**attempt → 2*attempt (exponential to linear)
        - retry_delay * X → retry_delay / X
        - 2**attempt → 2**(attempt+1) or 2**(attempt-1)
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Setup to fail 3 times then succeed
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Success"
        success_response = MagicMock()
        success_response.id = "msg_success"
        success_response.content = [text_block]
        success_response.usage.input_tokens = 10
        success_response.usage.output_tokens = 5
        success_response.model = ModelConfig.SONNET

        mock_client.messages.create.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            Exception("Error 3"),
            success_response,
        ]

        result = AIOrchestrator(
            api_key="test-key",
            max_retries=3,
            retry_delay=1.0,
        ).generate(prompt="Test", output_format="yaml")

        assert result.content == "Success"

        # Verify EXACT sleep delays: retry_delay * (2 ** attempt)
        # Attempt 0 fails → sleep 1.0 * (2**0) = 1.0
        # Attempt 1 fails → sleep 1.0 * (2**1) = 2.0
        # Attempt 2 fails → sleep 1.0 * (2**2) = 4.0
        # Attempt 3 succeeds → no sleep
        assert mock_sleep.call_count == 3
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls == [
            1.0,
            2.0,
            4.0,
        ], f"Expected [1.0, 2.0, 4.0] but got {sleep_calls}"

        # Verify these are NOT linear backoff (would be [1.0, 2.0, 3.0])
        assert sleep_calls != [1.0, 2.0, 3.0]

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_retry_count_exact(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test retry count is EXACTLY max_retries, not max_retries±1.

        Kills mutations: max_retries + 1 → max_retries, + 1 → + 0, + 1 → + 2
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Always fail to exhaust retries
        mock_client.messages.create.side_effect = Exception("Persistent error")

        orchestrator = AIOrchestrator(
            api_key="test-key",
            max_retries=2,
            retry_delay=0.1,
        )

        with pytest.raises(GenerationError):
            orchestrator.generate(prompt="Test", output_format="yaml")

        # Should try exactly (max_retries + 1) times: 1 initial + 2 retries = 3
        assert mock_client.messages.create.call_count == 3

        # Should sleep exactly max_retries times (after each failure except last)
        assert mock_sleep.call_count == 2

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_with_max_retries_zero(
        self,
        mock_anthropic: Mock,
        mock_sleep: Mock,
    ) -> None:
        """Test max_retries=0 means single attempt with no retries.

        Kills mutations in retry loop boundary condition.
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Immediate failure")

        orchestrator = AIOrchestrator(
            api_key="test-key",
            max_retries=0,
            retry_delay=1.0,
        )

        with pytest.raises(GenerationError):
            orchestrator.generate(prompt="Test", output_format="yaml")

        # Should try exactly once (no retries)
        assert mock_client.messages.create.call_count == 1
        # Should never sleep (no retries)
        mock_sleep.assert_not_called()

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_with_non_text_block_raises(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test generate raises GenerationError with non-TextBlock content.

        Kills mutations: not isinstance → isinstance
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create response with non-TextBlock content (e.g., ImageBlock)
        mock_response = MagicMock()
        mock_response.id = "msg_invalid"
        # Simulate a different block type (not TextBlock)
        non_text_block = MagicMock()
        non_text_block.__class__.__name__ = "ImageBlock"
        mock_response.content = [non_text_block]
        mock_client.messages.create.return_value = mock_response

        orchestrator = AIOrchestrator(api_key="test-key")

        with pytest.raises(
            GenerationError,
            match="Expected TextBlock in response",
        ):
            orchestrator.generate(prompt="Test", output_format="yaml")

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generation_result_fields_exact_values(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test GenerationResult contains exact expected values for all fields.

        Kills mutations in field assignments and response parsing.
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Test YAML content"

        mock_response = MagicMock()
        mock_response.id = "msg_exact_test"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 123
        mock_response.usage.output_tokens = 456
        mock_response.model = ModelConfig.OPUS
        mock_client.messages.create.return_value = mock_response

        result = AIOrchestrator(
            api_key="test-key",
            model=ModelConfig.OPUS,
        ).generate(prompt="Generate test", output_format="yaml")

        # Verify EXACT field values
        assert result.content == "Test YAML content"
        assert result.format == "yaml"
        assert result.message_id == "msg_exact_test"
        assert result.model == ModelConfig.OPUS
        assert isinstance(result.token_usage, TokenUsage)
        assert result.token_usage.input_tokens == 123
        assert result.token_usage.output_tokens == 456
        assert result.token_usage.total_tokens == 579  # 123 + 456

    def test_generation_error_with_cause_preserves_exception(self) -> None:
        """Test GenerationError.cause preserves original exception.

        Kills mutations that remove exception chaining.
        """
        original_error = ValueError("Original error message")
        generation_error = GenerationError(
            "Failed to generate",
            cause=original_error,
        )

        assert generation_error.cause is original_error
        assert str(generation_error) == "Failed to generate"

    def test_generation_error_without_cause(self) -> None:
        """Test GenerationError can be created without cause."""
        error = GenerationError("Simple error")
        assert error.cause is None
        assert str(error) == "Simple error"

    def test_model_config_values_exact(self) -> None:
        """Test ModelConfig constants have exact expected values.

        Kills mutations in string constants.
        """
        assert ModelConfig.OPUS == "claude-opus-4-5-20251101"
        assert ModelConfig.SONNET == "claude-sonnet-4-5-20250929"

        # Verify they're different
        assert ModelConfig.OPUS != ModelConfig.SONNET

        # Verify format pattern
        assert "claude-opus" in ModelConfig.OPUS
        assert "claude-sonnet" in ModelConfig.SONNET

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_prompt_format_in_api_call(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test prompt is formatted correctly in API call.

        Kills mutations in prompt string formatting.
        """
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Response"
        mock_response = MagicMock()
        mock_response.id = "msg_prompt_test"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5
        mock_response.model = ModelConfig.SONNET
        mock_client.messages.create.return_value = mock_response

        orchestrator = AIOrchestrator(api_key="test-key")
        orchestrator.generate(
            prompt="Create config",
            output_format="toml",
        )

        # Verify API was called with correctly formatted prompt
        call_kwargs = mock_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        expected_content = "Generate toml output:\n\nCreate config"
        assert messages[0]["content"] == expected_content

    def test_init_api_key_empty_exact_error_message(self) -> None:
        """Test exact error message for empty API key.

        Kills mutation: error message string → "XXerror messageXX"
        Location: orchestrator.py:124
        """
        with pytest.raises(ValueError, match="API key cannot be empty") as exc_info:
            AIOrchestrator(api_key="")

        assert str(exc_info.value) == "API key cannot be empty"
        assert "API key" in str(exc_info.value)
        assert "empty" in str(exc_info.value)

    def test_init_max_retries_negative_exact_error_message(self) -> None:
        """Test exact error message for negative max_retries.

        Kills mutation: error message string → "XXerror messageXX"
        Location: orchestrator.py:127
        """
        with pytest.raises(
            ValueError, match="max_retries must be non-negative"
        ) as exc_info:
            AIOrchestrator(api_key="test-key", max_retries=-1)

        assert str(exc_info.value) == "max_retries must be non-negative"
        assert "max_retries" in str(exc_info.value)
        assert "non-negative" in str(exc_info.value)

    def test_init_retry_delay_zero_exact_error_message(self) -> None:
        """Test exact error message for zero/negative retry_delay.

        Kills mutation: error message string → "XXerror messageXX"
        Location: orchestrator.py:130
        """
        with pytest.raises(
            ValueError, match="retry_delay must be positive"
        ) as exc_info:
            AIOrchestrator(api_key="test-key", retry_delay=0.0)

        assert str(exc_info.value) == "retry_delay must be positive"
        assert "retry_delay" in str(exc_info.value)
        assert "positive" in str(exc_info.value)

    def test_generate_empty_prompt_exact_error_message(self) -> None:
        """Test exact error message for empty prompt.

        Kills mutation: error message string → "XXerror messageXX"
        Location: orchestrator.py:158
        """
        orchestrator = AIOrchestrator(api_key="test-key")

        with pytest.raises(ValueError, match="Prompt cannot be empty") as exc_info:
            orchestrator.generate(prompt="", output_format="yaml")

        assert str(exc_info.value) == "Prompt cannot be empty"
        assert "Prompt" in str(exc_info.value)
        assert "empty" in str(exc_info.value)

    def test_generate_non_text_block_exact_error_message(self) -> None:
        """Test exact error message for non-TextBlock response.

        Kills mutation: error message string → "XXerror messageXX"
        Location: orchestrator.py:186
        """
        with patch(
            "start_green_stay_green.ai.orchestrator.Anthropic"
        ) as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            # Create response with non-TextBlock content
            mock_response = MagicMock()
            mock_response.id = "msg_invalid"
            non_text_block = MagicMock()
            non_text_block.__class__.__name__ = "ImageBlock"
            mock_response.content = [non_text_block]
            mock_client.messages.create.return_value = mock_response

            orchestrator = AIOrchestrator(api_key="test-key")

            with pytest.raises(GenerationError) as exc_info:
                orchestrator.generate(prompt="Test", output_format="yaml")

            assert str(exc_info.value) == "Expected TextBlock in response"
            assert "TextBlock" in str(exc_info.value)
            assert "response" in str(exc_info.value)

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_generate_last_error_initialized_to_none_not_empty_string(
        self,
        mock_anthropic: Mock,
    ) -> None:
        """Test last_error is initialized to None, not empty string.

        Kills mutation: last_error = None → last_error = ""
        Location: orchestrator.py:168

        Note: This test verifies that when an error occurs, the cause is properly
        set to the exception. Combined with success path tests, this ensures
        last_error starts as None (not "").
        """
        # Setup mock to fail all attempts
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        test_exception = ValueError("Test error")
        mock_client.messages.create.side_effect = test_exception

        orchestrator = AIOrchestrator(api_key="test-key", max_retries=0)

        with pytest.raises(GenerationError) as exc_info:
            orchestrator.generate(prompt="Test", output_format="yaml")

        # Verify the cause is the exception, not an empty string
        # This test kills the mutation: last_error = None → last_error = ""
        assert exc_info.value.cause is test_exception
        assert exc_info.value.cause is not None
        assert isinstance(exc_info.value.cause, Exception)
        # If last_error was initialized to "", it wouldn't work as Exception type
        assert not isinstance(exc_info.value.cause, str)
