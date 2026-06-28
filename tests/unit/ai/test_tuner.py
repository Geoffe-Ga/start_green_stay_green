"""Unit tests for ContentTuner and TuningResult."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationError
from start_green_stay_green.ai.orchestrator import ModelConfig
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.ai.orchestrator import ToolUseResult
from start_green_stay_green.ai.tuner import ContentTuner
from start_green_stay_green.ai.tuner import TuningResult
from start_green_stay_green.ai.tuner import _REPORT_TUNING_TOOL
from start_green_stay_green.ai.tuner import _await_or_offload

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_tool_use_result(  # noqa: PLR0913 — test factory; kw-only args
    *,
    tuned_content: str = "Adapted content",
    changes: list[str] | None = None,
    input_tokens: int = 100,
    output_tokens: int = 50,
    cache_read_tokens: int = 0,
    cache_creation_tokens: int = 0,
) -> ToolUseResult:
    """Build a ``ToolUseResult`` shaped like the orchestrator's real output.

    Centralised so the test suite has exactly one place to update if
    the dataclass gains fields. ``tool_input`` matches the
    ``report_tuning`` schema so the tuner's ``_parse_tool_use_input``
    succeeds without hand-rolling JSON.
    """
    return ToolUseResult(
        tool_name="report_tuning",
        tool_input={
            "tuned_content": tuned_content,
            "changes": list(changes if changes is not None else []),
        },
        token_usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens),
        model=ModelConfig.SONNET,
        message_id="msg_test",
        cache_read_tokens=cache_read_tokens,
        cache_creation_tokens=cache_creation_tokens,
    )


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
        orchestrator = MagicMock(spec=AIOrchestrator)
        tuner = ContentTuner(orchestrator)

        assert tuner.orchestrator is orchestrator
        assert not tuner.dry_run

    def test_content_tuner_init_with_dry_run(self) -> None:
        """Test ContentTuner initializes with dry_run mode."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        assert tuner.dry_run


class TestContentTunerValidation:
    """Test ContentTuner input validation."""

    def test_validate_content_with_empty_string_raises_error(self) -> None:
        """Test _validate_content raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ContentTuner._validate_content("")

    def test_validate_content_with_whitespace_only_raises_error(self) -> None:
        """Test _validate_content raises ValueError for whitespace."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ContentTuner._validate_content("   \n\t  ")

    def test_validate_content_with_valid_content_passes(self) -> None:
        """Test _validate_content passes for valid content."""
        ContentTuner._validate_content("Valid content")

    def test_validate_context_with_empty_string_raises_error(self) -> None:
        """Test _validate_context raises ValueError for empty string."""
        with pytest.raises(ValueError, match="Source context cannot be empty"):
            ContentTuner._validate_context("", "Source context")

    def test_validate_context_with_whitespace_only_raises_error(self) -> None:
        """Test _validate_context raises ValueError for whitespace."""
        with pytest.raises(ValueError, match="Target context cannot be empty"):
            ContentTuner._validate_context("  \n  ", "Target context")

    def test_validate_context_with_valid_context_passes(self) -> None:
        """Test _validate_context passes for valid context."""
        ContentTuner._validate_context("Valid context", "Test")

    def test_validate_content_error_message_is_exact(self) -> None:
        """The empty-content message is exactly ``Content cannot be empty``."""
        with pytest.raises(ValueError, match="empty") as exc:
            ContentTuner._validate_content("")
        assert str(exc.value) == "Content cannot be empty"

    def test_validate_context_error_message_is_exact(self) -> None:
        """The message interpolates the name + exact ``cannot be empty`` tail."""
        with pytest.raises(ValueError, match="empty") as exc:
            ContentTuner._validate_context("", "Source context")
        assert str(exc.value) == "Source context cannot be empty"


class TestContentTunerSystemBlocks:
    """Test the cache-controlled system-block builder."""

    def test_system_blocks_include_both_contexts(self) -> None:
        """Both source and target contexts land in the system prefix."""
        blocks = ContentTuner._build_system_blocks(
            "FastAPI project",
            "Django project",
            preserve_sections=None,
        )
        joined = " ".join(str(b["text"]) for b in blocks)
        assert "FastAPI project" in joined
        assert "Django project" in joined

    def test_system_blocks_include_six_component_headings(self) -> None:
        """The rendered system prompt carries the 6-component framework."""
        blocks = ContentTuner._build_system_blocks(
            "Source", "Target", preserve_sections=None
        )
        joined = " ".join(str(b["text"]) for b in blocks)
        for heading in (
            "## Role",
            "## Goal",
            "## Context",
            "## Output Format",
            "## Examples",
            "## Requirements",
        ):
            assert heading in joined, f"missing {heading} from system prompt"
        # Specific behavioural directives the model must see.
        assert "Preserve the structure and format" in joined
        assert "report_tuning" in joined

    def test_system_blocks_omit_preserve_when_none(self) -> None:
        """No preserve list → no preserve sentence in the rendered prompt."""
        blocks = ContentTuner._build_system_blocks(
            "Source", "Target", preserve_sections=None
        )
        joined = " ".join(str(b["text"]) for b in blocks)
        assert "PRESERVE THESE SECTIONS UNCHANGED" not in joined

    def test_system_blocks_include_preserve_list(self) -> None:
        """Preserve sections are listed in the rendered prompt."""
        blocks = ContentTuner._build_system_blocks(
            "Source",
            "Target",
            preserve_sections=["Introduction", "License"],
        )
        joined = " ".join(str(b["text"]) for b in blocks)
        # Each section appears verbatim, regardless of whether the
        # template renders inline or as a bullet list.
        assert '"Introduction"' in joined
        assert '"License"' in joined
        assert "PRESERVE THESE SECTIONS UNCHANGED" in joined

    def test_last_system_block_is_cache_controlled(self) -> None:
        """Cache marker on the final block caches everything before it.

        Anthropic prompt caching keys on the prefix up to (and
        including) the marked block. A single ``ephemeral`` marker on
        the tail of the system blocks therefore caches the whole
        stable prompt — exactly what Phase 2c needs for back-to-back
        subagent tunes.
        """
        blocks = ContentTuner._build_system_blocks(
            "Source", "Target", preserve_sections=None
        )
        # The cache prefix is a single block by design — splitting it
        # back into two would re-introduce the partition the
        # consolidation removed, so pin the count.
        assert len(blocks) == 1
        # Earlier blocks must not be marked or the cache key partition
        # would leak per-call deltas into the cached prefix.
        for block in blocks[:-1]:
            assert "cache_control" not in block
        assert blocks[-1]["cache_control"] == {"type": "ephemeral"}

    def test_system_block_envelope_keys_are_exact(self) -> None:
        """The single block is ``type=text`` with text + cache_control keys.

        Pins the literal ``"type"`` key and its ``"text"`` value so a
        rename of either (the only block-envelope mutants) is caught.
        """
        blocks = ContentTuner._build_system_blocks(
            "Source", "Target", preserve_sections=None
        )
        block = blocks[0]
        assert block["type"] == "text"
        assert set(block) == {"type", "text", "cache_control"}
        assert isinstance(block["text"], str)

    def test_user_message_contains_only_per_call_delta(self) -> None:
        """The user message holds the source content and nothing else.

        Keeping the user message tiny maximises the proportion of each
        request served from cache. If contexts or instructions leaked
        in here, every per-agent tune would be uncached because the
        per-call delta would force the cache key to differ.
        """
        message = ContentTuner._build_user_message("# Original\n\nBody")
        assert "# Original" in message
        assert "Body" in message
        # Sanity: the system prefix's distinctive markers must NOT appear
        # here — the user message is the per-call delta only.
        assert "## Role" not in message
        assert "## Requirements" not in message
        assert "SOURCE CONTEXT:" not in message

    def test_user_message_is_exact_template(self) -> None:
        """The user message equals the exact ``CONTENT TO ADAPT:`` template."""
        message = ContentTuner._build_user_message("BODY")
        assert message == "CONTENT TO ADAPT:\nBODY"
        assert message.startswith("CONTENT TO ADAPT:\n")


class TestContentTunerToolUseParsing:
    """Test the structured tool_use output parser."""

    def test_parses_well_formed_input(self) -> None:
        """A schema-conformant input → ``(content, changes)``."""
        content, changes = ContentTuner._parse_tool_use_input(
            {
                "tuned_content": "# Adapted",
                "changes": ["Renamed FastAPI", "Updated paths"],
            }
        )
        assert content == "# Adapted"
        assert changes == ["Renamed FastAPI", "Updated paths"]

    def test_empty_changes_is_valid(self) -> None:
        """An empty changes array is valid ("no changes were necessary")."""
        content, changes = ContentTuner._parse_tool_use_input(
            {"tuned_content": "Unchanged", "changes": []}
        )
        assert content == "Unchanged"
        assert not changes

    def test_drops_blank_change_strings(self) -> None:
        """Blank/non-string entries in ``changes`` are silently dropped."""
        _content, changes = ContentTuner._parse_tool_use_input(
            {
                "tuned_content": "Body",
                "changes": ["Real change", "", "  ", 42, None],
            }
        )
        # Whitespace-only and non-string items rejected.
        assert changes == ["Real change"]

    def test_missing_changes_defaults_to_empty(self) -> None:
        """A missing ``changes`` key defaults to ``[]`` rather than crashing."""
        _content, changes = ContentTuner._parse_tool_use_input(
            {"tuned_content": "Body"}
        )
        assert not changes

    def test_non_string_content_raises_generation_error(self) -> None:
        """A bogus ``tuned_content`` type is a hard error, not a silent fallback.

        The schema flags this server-side, but the parser still
        defends against an old SDK or a misuse so the failure is
        loud rather than passing through a confusing ``TypeError``.
        """
        with pytest.raises(GenerationError, match="tuned_content") as exc:
            ContentTuner._parse_tool_use_input({"tuned_content": 42, "changes": []})
        assert str(exc.value) == "report_tuning.tuned_content must be a string"

    def test_non_list_changes_raises_generation_error(self) -> None:
        """Same loud-failure rule for ``changes``."""
        with pytest.raises(GenerationError, match="changes must be a list") as exc:
            ContentTuner._parse_tool_use_input(
                {"tuned_content": "x", "changes": "not a list"}
            )
        assert str(exc.value) == "report_tuning.changes must be a list of strings"

    def test_validate_tool_use_input_is_staticmethod(self) -> None:
        """``_validate_tool_use_input`` stays a staticmethod.

        Removing ``@staticmethod`` turns it into an instance method, so
        calling it via an instance with the single ``tool_input`` dict
        would bind ``self`` and raise ``TypeError``. Pin that it does
        NOT — the static call shape must keep working.
        """
        tuner = ContentTuner(MagicMock(spec=AIOrchestrator))
        content, changes = tuner._validate_tool_use_input(
            {"tuned_content": "ok", "changes": ["c"]}
        )
        assert content == "ok"
        assert changes == ["c"]


class TestReportTuningTool:
    """Smoke tests on the static tool schema."""

    def test_schema_required_fields_locked_in(self) -> None:
        """The schema marks both fields required — a regression here would
        let the model omit ``tuned_content`` and fall through to silent
        text-mode output.
        """
        assert _REPORT_TUNING_TOOL["name"] == "report_tuning"
        schema = _REPORT_TUNING_TOOL["input_schema"]
        assert isinstance(schema, dict)
        assert set(schema["required"]) == {"tuned_content", "changes"}

    def test_tool_description_is_exact(self) -> None:
        """Pin the tool description string verbatim (kills string mutants)."""
        assert _REPORT_TUNING_TOOL["description"] == (
            "Report the tuned content and a bullet list of changes made "
            "while adapting the source content to the target context."
        )

    def test_schema_matches_exact_structure(self) -> None:
        """The whole input_schema dict matches verbatim, keys and values."""
        assert _REPORT_TUNING_TOOL["input_schema"] == {
            "type": "object",
            "properties": {
                "tuned_content": {
                    "type": "string",
                    "description": "The fully adapted content.",
                },
                "changes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Short bullet describing each change made. "
                        "Empty list when no changes were necessary."
                    ),
                },
            },
            "required": ["tuned_content", "changes"],
        }


class TestContentTunerTuneAsync:
    """Test ContentTuner tune method."""

    @pytest.mark.asyncio
    async def test_tune_with_valid_inputs(self) -> None:
        """Test tune() with valid inputs."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="# Django Project\n\nAdapted content",
            changes=["Changed FastAPI to Django", "Updated imports"],
            input_tokens=100,
            output_tokens=50,
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
    async def test_tune_calls_orchestrator_generate_tool_use(self) -> None:
        """tune() calls ``generate_tool_use_async`` with cache-marked blocks."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Adapted",
            changes=["Change"],
            input_tokens=10,
            output_tokens=5,
        )

        tuner = ContentTuner(orchestrator)
        await tuner.tune(
            source_content="Original",
            source_context="Source",
            target_context="Target",
        )

        orchestrator.generate_tool_use_async.assert_called_once()
        positional, keyword = orchestrator.generate_tool_use_async.call_args
        # Per-call user message goes positionally; system blocks +
        # tool schema travel as kwargs.
        assert len(positional) == 1
        prompt_arg = positional[0]
        assert isinstance(prompt_arg, str)
        # The user message must NOT carry the cached prefix content.
        assert "## Role" not in prompt_arg
        assert "## Requirements" not in prompt_arg
        assert "Original" in prompt_arg
        # System blocks must include both contexts and end with a
        # cache_control marker — the cache-hit guarantee for back-to-
        # back tunes hinges on this.
        system_blocks = keyword["system_blocks"]
        joined = " ".join(str(b["text"]) for b in system_blocks)
        assert "Source" in joined
        assert "Target" in joined
        assert system_blocks[-1]["cache_control"] == {"type": "ephemeral"}
        assert keyword["tool_schema"] is _REPORT_TUNING_TOOL

    @pytest.mark.asyncio
    async def test_tune_with_empty_content_raises_error(self) -> None:
        """Test tune() raises ValueError for empty content."""
        orchestrator = MagicMock(spec=AIOrchestrator)
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
        orchestrator = MagicMock(spec=AIOrchestrator)
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
        orchestrator = MagicMock(spec=AIOrchestrator)
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
        orchestrator = MagicMock(spec=AIOrchestrator)
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

        # Orchestrator should not be called in dry-run mode.
        orchestrator.generate_tool_use_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_tune_with_preserve_sections(self) -> None:
        """preserve_sections lands in the cached system blocks."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Adapted",
            changes=["Modified"],
            input_tokens=20,
            output_tokens=10,
        )

        tuner = ContentTuner(orchestrator)
        await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
            preserve_sections=["License", "Credits"],
        )

        keyword = orchestrator.generate_tool_use_async.call_args.kwargs
        joined = " ".join(str(b["text"]) for b in keyword["system_blocks"])
        assert "PRESERVE THESE SECTIONS UNCHANGED" in joined
        assert '"License"' in joined
        assert '"Credits"' in joined

    @pytest.mark.asyncio
    async def test_tune_handles_generation_error(self) -> None:
        """Test tune() propagates GenerationError from orchestrator."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.side_effect = GenerationError("API error")

        tuner = ContentTuner(orchestrator)

        with pytest.raises(GenerationError, match="API error"):
            await tuner.tune(
                source_content="Content",
                source_context="Source",
                target_context="Target",
            )

    @pytest.mark.asyncio
    async def test_tune_without_preserve_sections_works(self) -> None:
        """tune() works without preserve_sections (default None)."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Result",
            changes=["Done"],
            input_tokens=5,
            output_tokens=3,
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
        orchestrator = MagicMock(spec=AIOrchestrator)
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
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Result", changes=["Done"]
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
    async def test_tune_logs_truncate_contexts_to_50_chars(
        self, mocker: MockerFixture
    ) -> None:
        """Long contexts are truncated to exactly 50 chars in the start log."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Result", changes=["Done"]
        )
        tuner = ContentTuner(orchestrator)
        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        # 60-char contexts; chars 0-49 are "a"/"b", char 50 differs so a
        # ``[:51]`` slice would include a 51st char the assertion rejects.
        source = "a" * 50 + "SSSSSSSSSS"
        target = "b" * 50 + "TTTTTTTTTT"
        await tuner.tune(
            source_content="Content",
            source_context=source,
            target_context=target,
        )

        mock_logger.info.assert_any_call(
            "Tuning content (source: %s, target: %s)",
            "a" * 50,
            "b" * 50,
        )

    @pytest.mark.asyncio
    async def test_tune_logs_exception_on_error(self, mocker: MockerFixture) -> None:
        """Test logger.exception called when tuning fails."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.side_effect = GenerationError("API error")
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
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Result",
            changes=["Change 1", "Change 2", "Change 3"],
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
        orchestrator = MagicMock(spec=AIOrchestrator)
        orchestrator.generate_tool_use_async.return_value = _make_tool_use_result(
            tuned_content="Result",
            changes=["First change", "Second change"],
        )
        tuner = ContentTuner(orchestrator)

        mock_logger = mocker.patch("start_green_stay_green.ai.tuner.logger")

        await tuner.tune(
            source_content="Content",
            source_context="Source",
            target_context="Target",
        )

        # Verify debug called for each change with the exact format string.
        assert mock_logger.debug.call_count == 2
        mock_logger.debug.assert_any_call("Change: %s", "First change")
        mock_logger.debug.assert_any_call("Change: %s", "Second change")

    @pytest.mark.asyncio
    async def test_tune_dry_run_does_not_call_orchestrator(self) -> None:
        """Dry-run mode skips orchestrator.generate_tool_use_async."""
        orchestrator = MagicMock(spec=AIOrchestrator)
        tuner = ContentTuner(orchestrator, dry_run=True)

        result = await tuner.tune(
            source_content="Original Content",
            source_context="Source",
            target_context="Target",
        )

        orchestrator.generate_tool_use_async.assert_not_called()
        assert result.content == "Original Content"
        assert result.dry_run

    @pytest.mark.asyncio
    async def test_tune_dry_run_returns_original_content_exactly(self) -> None:
        """Test dry-run returns exact original content unchanged."""
        orchestrator = MagicMock(spec=AIOrchestrator)
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


class TestAwaitOrOffload:
    """Pin the dual sync/async dispatch in ``_await_or_offload``."""

    @pytest.mark.asyncio
    async def test_sync_callable_offloaded_returns_real_value(self) -> None:
        """A plain sync callable is offloaded and its result flows back.

        Guards the sync branch where ``sync_call = cast(..., call)``.
        If that binding were dropped to ``None``, ``asyncio.to_thread``
        would receive ``None`` and raise instead of returning ``(7, 9)``.
        """

        def sync_double(x: int, *, y: int) -> tuple[int, int]:
            return (x, y)

        result = await _await_or_offload(sync_double, 7, y=9)
        assert result == (7, 9)

    @pytest.mark.asyncio
    async def test_async_callable_is_awaited_returns_real_value(self) -> None:
        """A coroutine function is invoked and awaited, not offloaded."""

        async def async_echo(value: str) -> str:
            return value

        result: str = await _await_or_offload(async_echo, "echoed")
        assert result == "echoed"


class TestContentTunerBuildBatchRequest:
    """Pin ``build_batch_request`` builds the same payload ``tune`` sends."""

    @pytest.fixture
    def tuner(self) -> ContentTuner:
        return ContentTuner(MagicMock(spec=AIOrchestrator))

    def test_request_carries_custom_id_prompt_and_tool(
        self,
        tuner: ContentTuner,
    ) -> None:
        """The request envelope keeps every field the orchestrator needs."""
        req = tuner.build_batch_request(
            custom_id="subagent:architecture",
            source_content="# Original\n\nbody",
            source_context="Source repo",
            target_context="Target repo",
        )
        assert req.custom_id == "subagent:architecture"
        assert "Original" in req.prompt
        assert req.tool_schema["name"] == "report_tuning"

    def test_system_blocks_match_what_tune_would_send(
        self,
        tuner: ContentTuner,
    ) -> None:
        """Cache prefix is identical between sync and batch — pin it."""
        req = tuner.build_batch_request(
            custom_id="subagent:a",
            source_content="X",
            source_context="A",
            target_context="B",
        )
        sync_blocks = ContentTuner._build_system_blocks("A", "B", None)
        assert req.system_blocks == sync_blocks

    def test_preserve_sections_flow_through(
        self,
        tuner: ContentTuner,
    ) -> None:
        req = tuner.build_batch_request(
            custom_id="subagent:a",
            source_content="X",
            source_context="A",
            target_context="B",
            preserve_sections=["Identity", "Workflow"],
        )
        joined = " ".join(str(b["text"]) for b in req.system_blocks)
        assert '"Identity"' in joined
        assert '"Workflow"' in joined

    def test_empty_custom_id_rejected(self, tuner: ContentTuner) -> None:
        with pytest.raises(ValueError, match="custom_id cannot be empty") as exc:
            tuner.build_batch_request(
                custom_id="   ",
                source_content="X",
                source_context="A",
                target_context="B",
            )
        assert str(exc.value) == "custom_id cannot be empty"

    def test_input_validation_mirrors_tune(self, tuner: ContentTuner) -> None:
        """Same content / context validation runs on the batch path."""
        with pytest.raises(ValueError, match="Source context") as exc:
            tuner.build_batch_request(
                custom_id="ok",
                source_content="X",
                source_context="",
                target_context="B",
            )
        # The "Source context" label is passed verbatim to the validator.
        assert str(exc.value) == "Source context cannot be empty"

    def test_target_context_label_is_exact(self, tuner: ContentTuner) -> None:
        """The empty target raises with the exact ``Target context`` label."""
        with pytest.raises(ValueError, match="Target context") as exc:
            tuner.build_batch_request(
                custom_id="ok",
                source_content="X",
                source_context="A",
                target_context="",
            )
        assert str(exc.value) == "Target context cannot be empty"


class TestContentTunerParseBatchResult:
    """Pin ``parse_batch_tuning_result`` lifts a batch result correctly."""

    def test_returns_tuning_result_with_content_and_changes(self) -> None:
        tool_result = ToolUseResult(
            tool_name="report_tuning",
            tool_input={
                "tuned_content": "# Adapted\n",
                "changes": ["Renamed FastAPI to Django", "Updated paths"],
            },
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="claude",
            message_id="msg_1",
        )

        result = ContentTuner.parse_batch_tuning_result(tool_result)
        assert result.content == "# Adapted\n"
        assert result.changes == ["Renamed FastAPI to Django", "Updated paths"]
        assert result.token_usage_input == 100
        assert result.token_usage_output == 50
        assert not result.dry_run

    def test_missing_tuned_content_raises_generation_error(self) -> None:
        """A malformed ``tool_input`` (missing ``tuned_content``) raises.

        Pins the negative-path behaviour explicitly — the parser is
        shared with the sync path's ``_parse_tool_use_input``, but a
        future refactor that bypasses the shared validator on the
        batch resume path would silently lose this guard if no
        dedicated test pinned it.
        """
        tool_result = ToolUseResult(
            tool_name="report_tuning",
            tool_input={"changes": []},  # no ``tuned_content``
            token_usage=TokenUsage(input_tokens=1, output_tokens=1),
            model="claude",
            message_id="msg_bad",
        )
        with pytest.raises(GenerationError, match="tuned_content"):
            ContentTuner.parse_batch_tuning_result(tool_result)

    def test_non_list_changes_raises_generation_error(self) -> None:
        """``changes`` must be a list — a string-shaped value is rejected."""
        tool_result = ToolUseResult(
            tool_name="report_tuning",
            tool_input={"tuned_content": "x", "changes": "not a list"},
            token_usage=TokenUsage(input_tokens=1, output_tokens=1),
            model="claude",
            message_id="msg_bad",
        )
        with pytest.raises(GenerationError, match="list of strings"):
            ContentTuner.parse_batch_tuning_result(tool_result)
