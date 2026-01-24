"""Unit tests for ContentTuner and TuningResult."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import create_autospec

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.ai.tuner import ContentTuner
from start_green_stay_green.ai.tuner import TuningResult


class TestTuningResult:
    """Test TuningResult data class."""

    def test_tuning_result_creation_with_all_fields(self) -> None:
        """Test creating TuningResult with all fields."""
        result = TuningResult(
            content="Tuned content",
            changes=["Change 1", "Change 2"],
            dry_run=False,
            token_usage_input=100,
            token_usage_output=50,
        )
        assert result.content == "Tuned content"
        assert result.changes == ["Change 1", "Change 2"]
        assert not result.dry_run
        assert result.token_usage_input == 100
        assert result.token_usage_output == 50

    def test_tuning_result_with_empty_changes(self) -> None:
        """Test TuningResult with empty changes list."""
        result = TuningResult(
            content="Content",
            changes=[],
            dry_run=False,
            token_usage_input=10,
            token_usage_output=5,
        )
        assert not result.changes

    def test_tuning_result_dry_run_mode(self) -> None:
        """Test TuningResult in dry-run mode."""
        result = TuningResult(
            content="Original",
            changes=["[DRY RUN] No changes made"],
            dry_run=True,
            token_usage_input=0,
            token_usage_output=0,
        )
        assert result.dry_run
        assert result.token_usage_input == 0
        assert result.token_usage_output == 0

    def test_tuning_result_is_immutable(self) -> None:
        """Test TuningResult is immutable (frozen dataclass)."""
        result = TuningResult(
            content="Test",
            changes=["Change"],
            dry_run=False,
            token_usage_input=10,
            token_usage_output=5,
        )
        with pytest.raises(AttributeError):
            result.content = "Modified"  # type: ignore[misc]

    def test_tuning_result_exact_token_values(self) -> None:
        """Test TuningResult stores exact token values (kills mutants)."""
        result = TuningResult(
            content="Test",
            changes=[],
            dry_run=False,
            token_usage_input=42,
            token_usage_output=17,
        )
        assert result.token_usage_input == 42
        assert result.token_usage_input != 41
        assert result.token_usage_output == 17
        assert result.token_usage_output != 16


class TestContentTunerInit:
    """Test ContentTuner initialization."""

    def test_content_tuner_init_with_orchestrator(self) -> None:
        """Test ContentTuner initializes with orchestrator."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        assert tuner.orchestrator is orchestrator
        assert not tuner.dry_run

    def test_content_tuner_init_with_dry_run(self) -> None:
        """Test ContentTuner initializes with dry_run mode."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        assert tuner.dry_run


class TestContentTunerValidation:
    """Test ContentTuner input validation."""

    def test_validate_content_with_empty_string_raises_error(self) -> None:
        """Test _validate_content raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ContentTuner._validate_content("")  # noqa: SLF001

    def test_validate_content_with_whitespace_only_raises_error(self) -> None:
        """Test _validate_content raises ValueError for whitespace."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ContentTuner._validate_content("   \n\t  ")  # noqa: SLF001

    def test_validate_content_with_valid_content_passes(self) -> None:
        """Test _validate_content passes for valid content."""
        ContentTuner._validate_content("Valid content")  # noqa: SLF001

    def test_validate_context_with_empty_string_raises_error(self) -> None:
        """Test _validate_context raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Source context cannot be empty"):
            ContentTuner._validate_context("", "Source context")  # noqa: SLF001

    def test_validate_context_with_whitespace_only_raises_error(self) -> None:
        """Test _validate_context raises ValueError for whitespace."""
        with pytest.raises(ValueError, match="Target context cannot be empty"):
            ContentTuner._validate_context("  \n  ", "Target context")  # noqa: SLF001

    def test_validate_context_with_valid_context_passes(self) -> None:
        """Test _validate_context passes for valid context."""
        ContentTuner._validate_context("Valid context", "Test")  # noqa: SLF001


class TestContentTunerPromptBuilding:
    """Test ContentTuner prompt building."""

    def test_build_tuning_prompt_without_preserve_sections(self) -> None:
        """Test _build_tuning_prompt without preserve sections."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        prompt = tuner._build_tuning_prompt(  # noqa: SLF001
            source_content="# Original\n\nContent here",
            source_context="FastAPI project",
            target_context="Django project",
            preserve_sections=None,
        )

        assert "FastAPI project" in prompt
        assert "Django project" in prompt
        assert "# Original" in prompt
        assert "PRESERVE THESE SECTIONS" not in prompt

    def test_build_tuning_prompt_with_preserve_sections(self) -> None:
        """Test _build_tuning_prompt with preserve sections."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        prompt = tuner._build_tuning_prompt(  # noqa: SLF001
            source_content="Content",
            source_context="Source",
            target_context="Target",
            preserve_sections=["Introduction", "License"],
        )

        assert 'PRESERVE THESE SECTIONS UNCHANGED: "Introduction", "License"' in prompt

    def test_build_tuning_prompt_includes_requirements(self) -> None:
        """Test _build_tuning_prompt includes all requirements."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        prompt = tuner._build_tuning_prompt(  # noqa: SLF001
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        assert "REQUIREMENTS:" in prompt
        assert "Preserve the structure and format" in prompt
        assert "Adapt terminology" in prompt
        assert "OUTPUT FORMAT:" in prompt
        assert "CHANGES:" in prompt


class TestContentTunerResponseParsing:
    """Test ContentTuner response parsing."""

    def test_parse_tuning_response_with_changes_section(self) -> None:
        """Test _parse_tuning_response extracts content and changes."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        response = """# Adapted Content

This is the adapted content.

CHANGES:
- Changed FastAPI to Django
- Updated examples
- Modified paths
"""

        content, changes = tuner._parse_tuning_response(response)  # noqa: SLF001

        assert content == "# Adapted Content\n\nThis is the adapted content."
        assert len(changes) == 3
        assert "Changed FastAPI to Django" in changes
        assert "Updated examples" in changes
        assert "Modified paths" in changes

    def test_parse_tuning_response_with_asterisk_markers(self) -> None:
        """Test _parse_tuning_response handles asterisk markers."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        response = """Content here

CHANGES:
* Change one
* Change two
"""

        _content, changes = tuner._parse_tuning_response(response)  # noqa: SLF001

        assert len(changes) == 2
        assert "Change one" in changes
        assert "Change two" in changes

    def test_parse_tuning_response_without_changes_section(self) -> None:
        """Test _parse_tuning_response when no CHANGES section."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        response = "Just content without changes section"

        content, changes = tuner._parse_tuning_response(response)  # noqa: SLF001

        assert content == "Just content without changes section"
        assert not changes

    def test_parse_tuning_response_with_empty_changes(self) -> None:
        """Test _parse_tuning_response with empty CHANGES section."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        response = """Content

CHANGES:
"""

        content, changes = tuner._parse_tuning_response(response)  # noqa: SLF001

        assert content == "Content"
        assert not changes

    def test_parse_tuning_response_strips_whitespace(self) -> None:
        """Test _parse_tuning_response strips surrounding whitespace."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        response = """

    Content with spaces

CHANGES:
   - Change with spaces
"""

        content, changes = tuner._parse_tuning_response(response)  # noqa: SLF001

        assert content == "Content with spaces"
        assert "Change with spaces" in changes


class TestContentTunerTuneAsync:
    """Test ContentTuner tune method."""

    @pytest.mark.asyncio
    async def test_tune_with_valid_inputs(self) -> None:
        """Test tune() with valid inputs."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="""# Django Project

Adapted content

CHANGES:
- Changed FastAPI to Django
- Updated imports
""",
            format="markdown",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model=ModelConfig.SONNET,
            message_id="msg_123",
        )

        tuner = ContentTuner(orchestrator)
        result = await tuner.tune(
            source_content="# FastAPI Project\n\nOriginal content",
            source_context="FastAPI web service",
            target_context="Django web application",
        )

        assert result.content == "# Django Project\n\nAdapted content"
        assert len(result.changes) == 2
        assert "Changed FastAPI to Django" in result.changes
        assert not result.dry_run
        assert result.token_usage_input == 100
        assert result.token_usage_output == 50

    @pytest.mark.asyncio
    async def test_tune_calls_orchestrator_generate(self) -> None:
        """Test tune() calls orchestrator.generate with correct args."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Adapted\n\nCHANGES:\n- Change",
            format="markdown",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=ModelConfig.SONNET,
            message_id="msg_456",
        )

        tuner = ContentTuner(orchestrator)
        await tuner.tune(
            source_content="Original",
            source_context="Source",
            target_context="Target",
        )

        orchestrator.generate.assert_called_once()
        call_args = orchestrator.generate.call_args
        assert call_args[0][1] == "markdown"  # output_format
        assert "Source" in call_args[0][0]  # prompt contains source context
        assert "Target" in call_args[0][0]  # prompt contains target context

    @pytest.mark.asyncio
    async def test_tune_with_empty_content_raises_error(self) -> None:
        """Test tune() raises ValueError for empty content."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        with pytest.raises(ValueError, match="Content cannot be empty"):
            await tuner.tune(
                source_content="",
                source_context="Source",
                target_context="Target",
            )

    @pytest.mark.asyncio
    async def test_tune_with_empty_source_context_raises_error(self) -> None:
        """Test tune() raises ValueError for empty source context."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        with pytest.raises(ValueError, match="Source context cannot be empty"):
            await tuner.tune(
                source_content="Content",
                source_context="",
                target_context="Target",
            )

    @pytest.mark.asyncio
    async def test_tune_with_empty_target_context_raises_error(self) -> None:
        """Test tune() raises ValueError for empty target context."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        with pytest.raises(ValueError, match="Target context cannot be empty"):
            await tuner.tune(
                source_content="Content",
                source_context="Source",
                target_context="",
            )

    @pytest.mark.asyncio
    async def test_tune_in_dry_run_mode(self) -> None:
        """Test tune() in dry-run mode returns original content."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        result = await tuner.tune(
            source_content="Original content",
            source_context="Source",
            target_context="Target",
        )

        assert result.content == "Original content"
        assert result.dry_run
        assert result.changes == ["[DRY RUN] No changes made"]
        assert result.token_usage_input == 0
        assert result.token_usage_output == 0

        # Orchestrator should not be called in dry-run mode
        orchestrator.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_tune_with_preserve_sections(self) -> None:
        """Test tune() passes preserve_sections to prompt builder."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Adapted\n\nCHANGES:\n- Modified",
            format="markdown",
            token_usage=TokenUsage(input_tokens=20, output_tokens=10),
            model=ModelConfig.SONNET,
            message_id="msg_789",
        )

        tuner = ContentTuner(orchestrator)
        await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
            preserve_sections=["License", "Credits"],
        )

        call_args = orchestrator.generate.call_args
        prompt = call_args[0][0]
        assert 'PRESERVE THESE SECTIONS UNCHANGED: "License", "Credits"' in prompt

    @pytest.mark.asyncio
    async def test_tune_handles_generation_error(self) -> None:
        """Test tune() propagates GenerationError from orchestrator."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.side_effect = GenerationError("API error")

        tuner = ContentTuner(orchestrator)

        with pytest.raises(GenerationError, match="API error"):
            await tuner.tune(
                source_content="Content",
                source_context="Source",
                target_context="Target",
            )

    @pytest.mark.asyncio
    async def test_tune_without_preserve_sections_works(self) -> None:
        """Test tune() works without preserve_sections (default None)."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Result\n\nCHANGES:\n- Done",
            format="markdown",
            token_usage=TokenUsage(input_tokens=5, output_tokens=3),
            model=ModelConfig.SONNET,
            message_id="msg_999",
        )

        tuner = ContentTuner(orchestrator)
        result = await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        assert result.content == "Result"
        assert "Done" in result.changes


class TestContentTunerLoggerBehavior:
    """Test logger behavior in ContentTuner to kill mutants."""

    @pytest.mark.asyncio
    async def test_tune_logs_dry_run_mode(self, mocker: MockerFixture) -> None:
        """Test logger.info called for dry-run mode."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        result = await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        assert result.dry_run
        mock_logger.info.assert_any_call(
            "Dry-run mode: returning original content unchanged"
        )

    @pytest.mark.asyncio
    async def test_tune_logs_tuning_start(self, mocker: MockerFixture) -> None:
        """Test logger.info called when tuning starts."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Result\n\nCHANGES:\n- Done",
            format="markdown",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=ModelConfig.SONNET,
            message_id="msg_123",
        )
        tuner = ContentTuner(orchestrator)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        await tuner.tune(
            source_content="Content",
            source_context="Source Context",
            target_context="Target Context",
        )

        mock_logger.info.assert_any_call(
            "Tuning content (source: %s, target: %s)",
            "Source Context",
            "Target Context",
        )

    @pytest.mark.asyncio
    async def test_tune_logs_exception_on_error(self, mocker: MockerFixture) -> None:
        """Test logger.exception called when tuning fails."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.side_effect = GenerationError("API error")
        tuner = ContentTuner(orchestrator)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        with pytest.raises(GenerationError):
            await tuner.tune(
                source_content="Content",
                source_context="Source",
                target_context="Target",
            )

        mock_logger.exception.assert_called_once_with("Tuning failed")

    @pytest.mark.asyncio
    async def test_tune_logs_completion_with_changes(
        self, mocker: MockerFixture
    ) -> None:
        """Test logger.info called with change count on success."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Result\n\nCHANGES:\n- Change 1\n- Change 2\n- Change 3",
            format="markdown",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=ModelConfig.SONNET,
            message_id="msg_123",
        )
        tuner = ContentTuner(orchestrator)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        result = await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        assert len(result.changes) == 3
        mock_logger.info.assert_any_call(
            "Tuning complete, %d changes made",
            3,
        )

    @pytest.mark.asyncio
    async def test_tune_logs_each_change_at_debug_level(
        self, mocker: MockerFixture
    ) -> None:
        """Test logger.debug called for each change."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="Result\n\nCHANGES:\n- First change\n- Second change",
            format="markdown",
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model=ModelConfig.SONNET,
            message_id="msg_123",
        )
        tuner = ContentTuner(orchestrator)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        # Verify debug called for each change
        assert mock_logger.debug.call_count == 2
        debug_calls = [call[0] for call in mock_logger.debug.call_args_list]
        assert any("Change: %s" in str(call) for call in debug_calls)

    @pytest.mark.asyncio
    async def test_tune_dry_run_does_not_call_orchestrator(self) -> None:
        """Test dry-run mode skips orchestrator.generate call."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        result = await tuner.tune(
            source_content="Original Content",
            source_context="Source",
            target_context="Target",
        )

        # Verify orchestrator.generate was NOT called in dry-run
        orchestrator.generate.assert_not_called()
        assert result.content == "Original Content"
        assert result.dry_run

    @pytest.mark.asyncio
    async def test_tune_dry_run_returns_original_content_exactly(self) -> None:
        """Test dry-run returns exact original content unchanged."""
        orchestrator = create_autospec(AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        original = "# Title\n\nContent with special chars: !@#$%"
        result = await tuner.tune(
            source_content=original,
            source_context="Source",
            target_context="Target",
        )

        # Verify content is EXACTLY the same (not modified)
        assert result.content is original  # Same object reference
        assert result.content == original  # Same value
        assert result.dry_run
        assert result.changes == ["[DRY RUN] No changes made"]
