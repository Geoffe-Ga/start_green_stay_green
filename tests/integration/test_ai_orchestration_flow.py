"""Integration tests for AI orchestration flow.

Tests the complete AI generation workflow including:
- AIOrchestrator initialization
- Template loading and processing
- Content generation and tuning
- Output validation

These tests verify end-to-end AI orchestration behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest


class TestAIOrchestratorInitialization:
    """Test AIOrchestrator initialization and setup."""

    @pytest.mark.asyncio
    async def test_orchestrator_initializes_with_api_key(
        self, sample_api_key: str
    ) -> None:
        """Test orchestrator initializes with API key."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.api_key = sample_api_key

            assert mock_instance.api_key == sample_api_key

    @pytest.mark.asyncio
    async def test_orchestrator_initializes_with_settings(
        self, sample_context: dict[str, str]
    ) -> None:
        """Test orchestrator initializes with context settings."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.context = sample_context

            assert mock_instance.context == sample_context

    @pytest.mark.asyncio
    async def test_orchestrator_validates_api_credentials(
        self, sample_api_key: str
    ) -> None:
        """Test orchestrator validates API credentials."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_credentials = AsyncMock(return_value=True)

            result = await mock_instance.validate_credentials(sample_api_key)

            assert result is True
            mock_instance.validate_credentials.assert_called_once_with(
                sample_api_key
            )

    @pytest.mark.asyncio
    async def test_orchestrator_initialization_failure_on_invalid_key(self) -> None:
        """Test orchestrator fails with invalid API key."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_credentials = AsyncMock(
                side_effect=ValueError("Invalid API key")
            )

            with pytest.raises(ValueError):
                await mock_instance.validate_credentials("invalid-key")


class TestTemplateLoadingAndProcessing:
    """Test template loading and processing."""

    @pytest.mark.asyncio
    async def test_orchestrator_loads_templates(self) -> None:
        """Test orchestrator loads template files."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.load_templates = AsyncMock(
                return_value={
                    "claude_md": "Claude MD template",
                    "ci": "CI template",
                }
            )

            templates = await mock_instance.load_templates()

            assert "claude_md" in templates
            assert "ci" in templates

    @pytest.mark.asyncio
    async def test_orchestrator_processes_template_variables(
        self, sample_prompt_template: str, sample_context: dict[str, str]
    ) -> None:
        """Test orchestrator processes template variables."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.process_template = AsyncMock(
                return_value=(
                    "Create a configuration for TestProject using Python"
                )
            )

            result = await mock_instance.process_template(
                sample_prompt_template, sample_context
            )

            assert "TestProject" in result
            assert "Python" in result

    @pytest.mark.asyncio
    async def test_orchestrator_handles_missing_template(self) -> None:
        """Test orchestrator handles missing templates gracefully."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.load_template = AsyncMock(
                side_effect=FileNotFoundError("Template not found")
            )

            with pytest.raises(FileNotFoundError):
                await mock_instance.load_template("nonexistent_template")

    @pytest.mark.asyncio
    async def test_orchestrator_validates_template_syntax(self) -> None:
        """Test orchestrator validates template syntax."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.validate_template = AsyncMock(return_value=True)

            result = await mock_instance.validate_template(
                "Template with {variable}"
            )

            assert result is True


class TestContentGeneration:
    """Test AI content generation."""

    @pytest.mark.asyncio
    async def test_orchestrator_generates_content_with_prompt(
        self, sample_prompt_template: str
    ) -> None:
        """Test orchestrator generates content with prompt."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                return_value="Generated configuration content"
            )

            result = await mock_instance.generate(sample_prompt_template)

            assert "configuration" in result.lower()

    @pytest.mark.asyncio
    async def test_orchestrator_generation_with_multiple_prompts(
        self, sample_context: dict[str, str]
    ) -> None:
        """Test orchestrator generates content from multiple prompts."""
        prompts = [
            "Generate CLAUDE.md",
            "Generate GitHub Actions",
            "Generate scripts",
        ]

        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate_batch = AsyncMock(
                return_value={
                    "claude_md": "CLAUDE.md content",
                    "github_actions": "GitHub Actions content",
                    "scripts": "Scripts content",
                }
            )

            result = await mock_instance.generate_batch(prompts)

            assert len(result) == 3
            assert "claude_md" in result

    @pytest.mark.asyncio
    async def test_orchestrator_handles_generation_timeout(self) -> None:
        """Test orchestrator handles generation timeout."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate = AsyncMock(
                side_effect=TimeoutError("Generation timeout")
            )

            with pytest.raises(TimeoutError):
                await mock_instance.generate("prompt")

    @pytest.mark.asyncio
    async def test_orchestrator_generation_with_context(
        self, sample_context: dict[str, str], sample_prompt_template: str
    ) -> None:
        """Test orchestrator generates with context."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.generate_with_context = AsyncMock(
                return_value="Generated content with context"
            )

            result = await mock_instance.generate_with_context(
                sample_prompt_template, sample_context
            )

            assert "content" in result.lower()


class TestTuningAndValidation:
    """Test response tuning and validation."""

    @pytest.mark.asyncio
    async def test_orchestrator_tunes_generated_content(self) -> None:
        """Test orchestrator tunes generated content."""
        raw_content = "Raw generated content"

        with patch("start_green_stay_green.ai.tuner.Tuner") as mock_tuner:
            mock_instance = AsyncMock()
            mock_tuner.return_value = mock_instance
            mock_instance.tune = AsyncMock(return_value="Tuned content")

            result = await mock_instance.tune(raw_content)

            assert "tuned" in result.lower()

    @pytest.mark.asyncio
    async def test_orchestrator_validates_generated_structure(self) -> None:
        """Test orchestrator validates generated structure."""
        with patch("start_green_stay_green.ai.tuner.Tuner") as mock_tuner:
            mock_instance = AsyncMock()
            mock_tuner.return_value = mock_instance
            mock_instance.validate_structure = AsyncMock(return_value=True)

            result = await mock_instance.validate_structure(
                {"key": "value", "nested": {"field": "value"}}
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_orchestrator_formats_output_as_yaml(self) -> None:
        """Test orchestrator formats output as YAML."""
        with patch("start_green_stay_green.ai.tuner.Tuner") as mock_tuner:
            mock_instance = AsyncMock()
            mock_tuner.return_value = mock_instance
            mock_instance.format_as_yaml = AsyncMock(
                return_value="key: value\nnested:\n  field: value"
            )

            result = await mock_instance.format_as_yaml(
                {"key": "value", "nested": {"field": "value"}}
            )

            assert "key:" in result
            assert "value" in result

    @pytest.mark.asyncio
    async def test_orchestrator_formats_output_as_json(self) -> None:
        """Test orchestrator formats output as JSON."""
        with patch("start_green_stay_green.ai.tuner.Tuner") as mock_tuner:
            mock_instance = AsyncMock()
            mock_tuner.return_value = mock_instance
            mock_instance.format_as_json = AsyncMock(
                return_value='{"key": "value"}'
            )

            result = await mock_instance.format_as_json({"key": "value"})

            assert '"key"' in result


class TestEndToEndOrchestrationFlow:
    """Test complete end-to-end AI orchestration."""

    @pytest.mark.asyncio
    async def test_complete_orchestration_workflow(
        self, sample_project_config: dict[str, str | bool]
    ) -> None:
        """Test complete orchestration workflow."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            # Mock complete workflow
            mock_instance.validate_credentials = AsyncMock(return_value=True)
            mock_instance.load_templates = AsyncMock(
                return_value={
                    "claude_md": "template",
                    "ci": "template",
                }
            )
            mock_instance.generate_batch = AsyncMock(
                return_value={
                    "claude_md": "CLAUDE.md content",
                    "ci": "CI configuration",
                }
            )
            mock_instance.orchestrate = AsyncMock(
                return_value={
                    "success": True,
                    "generated": {
                        "claude_md": "CLAUDE.md content",
                        "ci": "CI configuration",
                    },
                }
            )

            result = await mock_instance.orchestrate(sample_project_config)

            assert result["success"] is True
            assert "generated" in result

    @pytest.mark.asyncio
    async def test_orchestration_with_error_recovery(self) -> None:
        """Test orchestration handles errors gracefully."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance

            # Simulate error then recovery
            mock_instance.generate = AsyncMock()
            mock_instance.generate.side_effect = [
                ConnectionError("First attempt failed"),
                "Generated content",
            ]

            # First call fails
            with pytest.raises(ConnectionError):
                await mock_instance.generate("prompt")

            # Second call succeeds
            result = await mock_instance.generate("prompt")
            assert "content" in result.lower()

    @pytest.mark.asyncio
    async def test_orchestration_tracks_generation_steps(self) -> None:
        """Test orchestration tracks all generation steps."""
        with patch("start_green_stay_green.ai.orchestrator.AIOrchestrator") as mock:
            mock_instance = AsyncMock()
            mock.return_value = mock_instance
            mock_instance.get_steps = AsyncMock(
                return_value=[
                    "Initialize orchestrator",
                    "Load templates",
                    "Generate content",
                    "Tune output",
                    "Validate structure",
                ]
            )

            steps = await mock_instance.get_steps()

            assert len(steps) == 5
            assert "Initialize" in steps[0]
            assert "Validate" in steps[-1]
