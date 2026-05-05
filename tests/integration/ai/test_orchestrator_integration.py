"""Integration tests for AI Orchestrator end-to-end workflows."""

from unittest.mock import MagicMock
from unittest.mock import create_autospec
from unittest.mock import patch

from anthropic.types import TextBlock
import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import TokenUsage


@pytest.mark.integration
class TestOrchestratorEndToEndWorkflows:
    """Test complete orchestrator workflows from initialization to generation."""

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_full_workflow_with_yaml_generation(
        self,
        mock_anthropic: MagicMock,
    ) -> None:
        """Test complete workflow: init → generate yaml → verify result."""
        # Setup complete mock response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "name: test-project\nversion: 1.0.0"

        mock_response = MagicMock()
        mock_response.id = "msg_yaml_test"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 150
        mock_response.usage.output_tokens = 75
        mock_response.model = ModelConfig.OPUS
        mock_client.messages.create.return_value = mock_response

        # Full workflow
        orchestrator = AIOrchestrator(
            api_key="integration-test-key",
            model=ModelConfig.OPUS,
            max_retries=2,
            retry_delay=0.5,
        )

        result = orchestrator.generate(
            prompt="Generate a YAML config for a test project",
            output_format="yaml",
        )

        # Verify complete result structure
        assert isinstance(result, GenerationResult)
        assert result.content == "name: test-project\nversion: 1.0.0"
        assert result.format == "yaml"
        assert isinstance(result.token_usage, TokenUsage)
        assert result.token_usage.input_tokens == 150
        assert result.token_usage.output_tokens == 75
        assert result.token_usage.total_tokens == 225
        assert result.model == ModelConfig.OPUS
        assert result.message_id == "msg_yaml_test"

        # Verify API was called with correct parameters
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == ModelConfig.OPUS
        assert call_kwargs["max_tokens"] == 4096

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_resilience_workflow_with_retry_recovery(
        self,
        mock_anthropic: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """Test resilience: failure → retry → recovery → success."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        # Create successful response
        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "#!/bin/bash\necho 'Success after retry'"

        success_response = MagicMock()
        success_response.id = "msg_retry_success"
        success_response.content = [text_block]
        success_response.usage.input_tokens = 50
        success_response.usage.output_tokens = 25
        success_response.model = ModelConfig.SONNET

        # Simulate failure → retry → success pattern
        mock_client.messages.create.side_effect = [
            Exception("Temporary network error"),
            success_response,
        ]

        orchestrator = AIOrchestrator(
            api_key="resilience-test-key",
            max_retries=3,
            retry_delay=0.1,
        )

        result = orchestrator.generate(
            prompt="Generate a bash script",
            output_format="bash",
        )

        # Verify successful recovery
        assert result.content == "#!/bin/bash\necho 'Success after retry'"
        assert result.format == "bash"
        assert mock_client.messages.create.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("start_green_stay_green.ai.orchestrator.time.sleep")
    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_failure_workflow_max_retries_exhausted(
        self,
        mock_anthropic: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """Test failure handling: persistent errors → max retries → error."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        # Simulate persistent failure
        persistent_error = Exception("Persistent API unavailability")
        mock_client.messages.create.side_effect = persistent_error

        orchestrator = AIOrchestrator(
            api_key="failure-test-key",
            max_retries=2,
            retry_delay=0.05,
        )

        # Verify failure with proper error context
        with pytest.raises(GenerationError) as exc_info:
            orchestrator.generate(
                prompt="This will fail persistently",
                output_format="markdown",
            )

        # Verify error details
        error = exc_info.value
        assert str(error) == "Failed to generate content"
        assert error.cause is persistent_error
        assert mock_client.messages.create.call_count == 3  # 1 + 2 retries
        assert mock_sleep.call_count == 2

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_multiple_format_workflow(
        self,
        mock_anthropic: MagicMock,
    ) -> None:
        """Test generating multiple formats with same orchestrator."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        # Setup responses for different formats
        def create_mock_response(
            content_text: str,
            msg_id: str,
        ) -> MagicMock:
            text_block = create_autospec(TextBlock, instance=True)
            text_block.text = content_text
            response = MagicMock()
            response.id = msg_id
            response.content = [text_block]
            response.usage.input_tokens = 10
            response.usage.output_tokens = 5
            response.model = ModelConfig.SONNET
            return response

        mock_client.messages.create.side_effect = [
            create_mock_response("key: value", "msg_yaml"),
            create_mock_response("[package]\nname = 'test'", "msg_toml"),
            create_mock_response("# Heading\nContent", "msg_md"),
            create_mock_response("#!/bin/bash\necho test", "msg_bash"),
        ]

        orchestrator = AIOrchestrator(api_key="multi-format-key")

        # Generate all supported formats
        formats_and_expected = [
            ("yaml", "key: value"),
            ("toml", "[package]\nname = 'test'"),
            ("markdown", "# Heading\nContent"),
            ("bash", "#!/bin/bash\necho test"),
        ]

        for fmt, expected_content in formats_and_expected:
            result = orchestrator.generate(
                prompt=f"Generate {fmt}",
                output_format=fmt,  # type: ignore[arg-type]
            )
            assert result.format == fmt
            assert result.content == expected_content

        # Verify all formats were generated
        assert mock_client.messages.create.call_count == 4

    @patch("start_green_stay_green.ai.orchestrator.Anthropic")
    def test_configuration_workflow_with_custom_settings(
        self,
        mock_anthropic: MagicMock,
    ) -> None:
        """Test custom configuration: non-default model, retries, delay."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.__enter__.return_value = mock_client

        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "Custom config response"

        mock_response = MagicMock()
        mock_response.id = "msg_custom"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 20
        mock_response.usage.output_tokens = 10
        mock_response.model = ModelConfig.OPUS
        mock_client.messages.create.return_value = mock_response

        # Custom configuration
        orchestrator = AIOrchestrator(
            api_key="custom-config-key",
            model=ModelConfig.OPUS,
            max_retries=5,
            retry_delay=2.5,
        )

        result = orchestrator.generate(
            prompt="Test custom config",
            output_format="toml",
        )

        # Verify custom configuration was used
        assert result.model == ModelConfig.OPUS
        assert orchestrator.max_retries == 5
        assert orchestrator.retry_delay == 2.5

        # Verify API called with custom model
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == ModelConfig.OPUS

    def test_validation_workflow_rejects_invalid_inputs(self) -> None:
        """Test input validation catches errors before API calls."""
        orchestrator = AIOrchestrator(api_key="validation-test-key")

        # Empty prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            orchestrator.generate(prompt="", output_format="yaml")

        # Whitespace prompt
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            orchestrator.generate(prompt="   ", output_format="yaml")

        # Invalid format
        with pytest.raises(ValueError, match="Unsupported output format"):
            orchestrator.generate(
                prompt="Valid prompt",
                output_format="invalid",  # type: ignore[arg-type]
            )


@pytest.mark.integration
class TestOrchestratorAsyncWorkflows:
    """Coverage for the AsyncAnthropic-backed generate_async path."""

    @pytest.mark.asyncio
    @patch("start_green_stay_green.ai.orchestrator.AsyncAnthropic")
    async def test_generate_async_returns_generation_result(
        self,
        mock_async_anthropic: MagicMock,
    ) -> None:
        """End-to-end: generate_async resolves to a populated GenerationResult."""
        # The orchestrator caches a single AsyncAnthropic per instance,
        # so the constructor returns a configured async client.
        mock_client = MagicMock()
        mock_async_anthropic.return_value = mock_client

        text_block = create_autospec(TextBlock, instance=True)
        text_block.text = "{}"

        mock_response = MagicMock()
        mock_response.id = "msg_async_smoke"
        mock_response.content = [text_block]
        mock_response.usage.input_tokens = 12
        mock_response.usage.output_tokens = 7
        mock_response.model = ModelConfig.SONNET

        # ``messages.create`` on AsyncAnthropic is a coroutine; the
        # orchestrator awaits it directly.
        async def _create(**_kwargs: object) -> MagicMock:
            return mock_response

        mock_client.messages.create.side_effect = _create

        # ``aclose`` is awaited from ``AIOrchestrator.aclose``; provide
        # an awaitable so the close path runs cleanly.
        async def _close() -> None:
            return None

        mock_client.close.side_effect = _close

        orchestrator = AIOrchestrator(api_key="async-smoke", retry_delay=0.01)
        try:
            result = await orchestrator.generate_async(
                prompt="hello", output_format="markdown"
            )
        finally:
            await orchestrator.aclose()

        assert isinstance(result, GenerationResult)
        assert result.content == "{}"
        assert result.token_usage.input_tokens == 12
        assert result.token_usage.output_tokens == 7
        # The async client is created exactly once (lazy + cached).
        mock_async_anthropic.assert_called_once_with(api_key="async-smoke")

    @pytest.mark.asyncio
    @patch("start_green_stay_green.ai.orchestrator.AsyncAnthropic")
    async def test_aclose_is_idempotent(
        self,
        mock_async_anthropic: MagicMock,
    ) -> None:
        """``aclose`` may be called repeatedly without raising."""
        mock_client = MagicMock()
        mock_async_anthropic.return_value = mock_client

        async def _close() -> None:
            return None

        mock_client.close.side_effect = _close

        orchestrator = AIOrchestrator(api_key="async-aclose")

        # No async work was done — ``aclose`` is a no-op.
        await orchestrator.aclose()
        await orchestrator.aclose()
        mock_client.close.assert_not_called()

        # Now allocate the client by calling ``_get_async_client`` and
        # close it twice.
        orchestrator._get_async_client()
        await orchestrator.aclose()
        await orchestrator.aclose()
        mock_client.close.assert_called_once()
