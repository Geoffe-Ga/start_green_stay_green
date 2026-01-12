"""Unit tests for AI Orchestrator data classes and core functionality."""

import pytest

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
