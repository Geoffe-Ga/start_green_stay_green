"""Unit tests for AI Orchestrator data classes and core functionality."""

import pytest

from start_green_stay_green.ai.orchestrator import GenerationResult
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
