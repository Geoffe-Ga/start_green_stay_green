"""Integration tests for AI Orchestrator.

Tests the full integration of the orchestrator with mocked Anthropic API,
verifying end-to-end workflows including retry logic, error handling,
and response processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from start_green_stay_green.ai import AIOrchestrator
from start_green_stay_green.ai import GenerationError
from start_green_stay_green.ai import ModelConfig

if TYPE_CHECKING:
    from unittest.mock import Mock


@pytest.fixture
def mock_successful_response() -> Mock:
    """Create mock for successful API response."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="# Test Project\n\nGenerated README")]
    mock_message.usage = MagicMock(input_tokens=150, output_tokens=75)
    mock_message.id = "msg_integration_test"
    mock_message.model = "claude-opus-4-20250514"
    mock_message.stop_reason = "end_turn"
    return mock_message


class TestOrchestratorIntegration:
    """Integration tests for complete orchestrator workflows."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_generation_workflow_completes_successfully(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test complete generation workflow from input to result."""
        orchestrator = AIOrchestrator(api_key="test-key-integration")

        with patch.object(
            orchestrator._client.messages,
            "create",
            return_value=mock_successful_response,
        ):
            result = await orchestrator.generate(
                prompt_template="Generate README for {project} in {language}",
                context={"project": "MyApp", "language": "Python"},
                output_format="markdown",
            )

            assert "Test Project" in result.content
            assert result.format == "markdown"
            assert result.token_usage.input_tokens == 150
            assert result.token_usage.output_tokens == 75
            assert result.token_usage.total_tokens == 225

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_tuning_workflow_adapts_content(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test complete tuning workflow."""
        orchestrator = AIOrchestrator(api_key="test-key-tuning")
        mock_successful_response.content = [
            MagicMock(text="# Adapted Project\n\nPython-specific README"),
        ]

        with patch.object(
            orchestrator._client.messages,
            "create",
            return_value=mock_successful_response,
        ):
            tuned = await orchestrator.tune(
                content="# Generic Project\n\nGeneric README",
                target_context="Python project with pytest and black",
            )

            assert "Adapted" in tuned
            assert tuned != ""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_retry_mechanism_recovers_from_transient_failures(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test retry logic recovers from temporary failures."""
        from anthropic import APITimeoutError

        orchestrator = AIOrchestrator(api_key="test-key-retry")
        call_count = 0

        async def fail_then_succeed(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise APITimeoutError("Simulated timeout")
            return mock_successful_response

        with patch.object(
            orchestrator._client.messages,
            "create",
            side_effect=fail_then_succeed,
        ):
            result = await orchestrator.generate(
                prompt_template="Test retry",
                context={},
                output_format="yaml",
            )

            assert result is not None
            assert call_count == 2  # Failed once, succeeded on retry

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_format_types_in_sequence(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test generating multiple formats sequentially."""
        orchestrator = AIOrchestrator(api_key="test-key-formats")

        formats = ["yaml", "toml", "markdown", "bash"]
        results = []

        with patch.object(
            orchestrator._client.messages,
            "create",
            return_value=mock_successful_response,
        ):
            for fmt in formats:
                result = await orchestrator.generate(
                    prompt_template="Generate config",
                    context={},
                    output_format=fmt,  # type: ignore[arg-type]
                )
                results.append(result)

            assert len(results) == 4
            assert [r.format for r in results] == formats

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_context_injection_with_complex_variables(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test context injection with various variable types."""
        orchestrator = AIOrchestrator(api_key="test-key-context")

        context = {
            "project_name": "MyComplexApp",
            "version": "1.0.0",
            "author": "Test Author",
            "description": "A complex application",
            "language": "Python 3.11",
        }

        template = """
        Create documentation for {project_name} version {version}
        Author: {author}
        Description: {description}
        Language: {language}
        """

        with patch.object(
            orchestrator._client.messages,
            "create",
            return_value=mock_successful_response,
        ):
            result = await orchestrator.generate(
                prompt_template=template,
                context=context,
                output_format="markdown",
            )

            assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_model_switching_between_opus_and_sonnet(
        self,
        mock_successful_response: Mock,
    ) -> None:
        """Test using different models for different operations."""
        orchestrator = AIOrchestrator(
            api_key="test-key-models",
            model=ModelConfig.OPUS,
        )

        with patch.object(
            orchestrator._client.messages,
            "create",
            return_value=mock_successful_response,
        ):
            # Generate with Opus (default)
            result1 = await orchestrator.generate(
                prompt_template="Complex task",
                context={},
                output_format="yaml",
            )

            # Tune with Sonnet
            result2 = await orchestrator.tune(
                content="Content",
                target_context="Python",
            )

            assert result1 is not None
            assert result2 is not None
