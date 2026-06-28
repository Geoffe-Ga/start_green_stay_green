"""Tests for SubagentsGenerator.

Tests cover:
- SubagentGenerationResult dataclass
- SubagentsGenerator initialization and validation
- Agent loading and frontmatter parsing
- Agent body tuning
- Single and batch agent generation
- Error handling
"""

from __future__ import annotations

import asyncio
import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from start_green_stay_green.ai.types import TokenUsage
from start_green_stay_green.ai.types import ToolUseResult
from start_green_stay_green.generators import subagents as subagents_mod
from start_green_stay_green.generators.subagents import DEFAULT_MAX_CONCURRENCY
from start_green_stay_green.generators.subagents import REFERENCE_AGENTS_DIR
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS
from start_green_stay_green.generators.subagents import SOURCE_AGENT_CONTEXT
from start_green_stay_green.generators.subagents import SubagentBatchEntry
from start_green_stay_green.generators.subagents import SubagentGenerationResult
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.generators.subagents import split_frontmatter

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from start_green_stay_green.ai.tuner import TuningResult


# Test data: minimal agent content with frontmatter
SAMPLE_AGENT_CONTENT = """---
name: test-agent
description: Test agent for unit testing
level: 0
phase: Plan
tools: Read,Grep,Glob
model: sonnet
---

# Test Agent

## Identity

This is a test agent.

## Scope

- Test scope item 1
- Test scope item 2

## Workflow

1. Step one
2. Step two

## Skills

| Skill | When to Invoke |
|-------|----------------|
| `test-skill` | When testing |

## Constraints

- Do NOT do bad things
- DO good things
"""


def _set_attr(obj: object, field: str, value: object) -> None:
    """Set an attribute, used to probe frozen-dataclass immutability."""
    setattr(obj, field, value)


# Test Dataclass


def test_subagent_generation_result_dataclass() -> None:
    """Test SubagentGenerationResult dataclass attributes."""
    result = SubagentGenerationResult(
        agent_name="test-agent",
        content="# Agent Content",
        tuned=True,
        changes=["Updated identity section", "Fixed workflow steps"],
    )

    assert result.agent_name == "test-agent"
    assert result.content == "# Agent Content"
    assert result.tuned
    assert result.changes == ["Updated identity section", "Fixed workflow steps"]


def test_subagent_generation_result_frozen() -> None:
    """Test SubagentGenerationResult is immutable."""
    result = SubagentGenerationResult(
        agent_name="test",
        content="content",
        tuned=True,
        changes=[],
    )

    with pytest.raises(AttributeError):
        result.agent_name = "new-name"  # type: ignore[misc]


# Test Initialization and Validation


def test_subagents_generator_init_with_defaults(
    mocker: MockerFixture,
) -> None:
    """Test SubagentsGenerator initialization with default reference directory."""
    # Mock ContentTuner to avoid validation
    mock_tuner = mocker.Mock()
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )

    # Mock validation to avoid filesystem checks
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)

    assert generator.orchestrator is mock_orchestrator
    assert generator.reference_dir == REFERENCE_AGENTS_DIR
    assert not generator.dry_run


def test_subagents_generator_init_with_custom_dir(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test SubagentsGenerator initialization with custom reference directory."""
    mock_tuner = mocker.Mock()
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    custom_dir = tmp_path / "custom_agents"
    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=custom_dir,
    )

    assert generator.reference_dir == custom_dir


def test_subagents_generator_init_dry_run(
    mocker: MockerFixture,
) -> None:
    """Test SubagentsGenerator initialization with dry_run=True."""
    mock_tuner = mocker.Mock()
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator, dry_run=True)

    assert generator.dry_run


# Test Validation


def test_check_directory_exists_missing_directory(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test _check_directory_exists raises FileNotFoundError for missing directory."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    missing_dir = tmp_path / "nonexistent"
    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=missing_dir,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Reference directory not found",
    ):
        generator._check_directory_exists()


def test_check_directory_exists_not_directory(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test _check_directory_exists raises NotADirectoryError for file path."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    # Create a file, not a directory
    file_path = tmp_path / "not_a_dir.txt"
    file_path.write_text("content")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=file_path,
    )

    with pytest.raises(
        NotADirectoryError,
        match="Reference path is not a directory",
    ):
        generator._check_directory_exists()


def test_check_required_agents_missing_agents(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test _check_required_agents raises FileNotFoundError for missing agents."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    # Create directory but don't add agent files
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
    )

    with pytest.raises(
        FileNotFoundError,
        match="Missing required agent files",
    ):
        generator._check_required_agents()


def test_check_required_agents_all_present(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test _check_required_agents succeeds when all agents present."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    # Create directory and all required agent files
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for source_file in REQUIRED_AGENTS.values():
        (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
    )

    # Should not raise
    generator._check_required_agents()


# Test Loading and Parsing


def test_load_agent_content(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test _load_agent_content loads agent file correctly."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "chief-architect.md").write_text(SAMPLE_AGENT_CONTENT)

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
    )

    content = generator._load_agent_content("chief-architect")
    assert content == SAMPLE_AGENT_CONTENT


def test_parse_frontmatter_valid(
    mocker: MockerFixture,
) -> None:
    """Test _parse_frontmatter extracts frontmatter and body correctly."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)

    frontmatter, body = generator._parse_frontmatter(
        SAMPLE_AGENT_CONTENT,
    )

    # Frontmatter includes --- delimiters
    assert frontmatter.startswith("---\n")
    assert frontmatter.endswith("---")
    assert "name: test-agent" in frontmatter

    # Body starts after frontmatter
    assert body.startswith("\n# Test Agent")
    assert "## Identity" in body


def test_parse_frontmatter_missing(
    mocker: MockerFixture,
) -> None:
    """Test _parse_frontmatter raises ValueError for missing frontmatter."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)

    content_without_frontmatter = """# Agent Content

No frontmatter here."""

    with pytest.raises(
        ValueError,
        match="Agent content missing YAML frontmatter",
    ):
        generator._parse_frontmatter(
            content_without_frontmatter,
        )


# Test Tuning


@pytest.mark.asyncio
async def test_tune_agent_body(
    mocker: MockerFixture,
) -> None:
    """Test _tune_agent_body calls tuner with correct parameters."""
    # Create mock tuner
    mock_tuner = AsyncMock()
    mock_tuning_result: TuningResult = mocker.Mock(
        content="# Tuned Content",
        changes=["Updated scope", "Fixed examples"],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)
    generator.tuner = mock_tuner

    body = "# Agent Body\n\n## Identity\nOriginal content"
    result = await generator._tune_agent_body(
        "chief-architect",
        body,
        "Python web application",
    )

    # Verify tuner was called
    mock_tuner.tune.assert_called_once()
    call_args = mock_tuner.tune.call_args

    assert call_args[1]["source_content"] == body
    assert "Mojo ML research" in call_args[1]["source_context"]
    assert call_args[1]["target_context"] == "Python web application"
    assert "## Identity" in call_args[1]["preserve_sections"]

    # Verify result
    assert result.agent_name == "chief-architect"
    assert result.content == "# Tuned Content"
    assert result.tuned
    assert result.changes == ["Updated scope", "Fixed examples"]


# Test Agent Generation


@pytest.mark.asyncio
async def test_generate_agent_success(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test generate_agent produces complete agent with frontmatter."""
    # Setup agent directory
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "chief-architect.md").write_text(SAMPLE_AGENT_CONTENT)

    # Mock tuner
    mock_tuner = AsyncMock()
    mock_tuning_result: TuningResult = mocker.Mock(
        content="# Tuned Agent Body",
        changes=["Change 1"],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
    )
    generator.tuner = mock_tuner

    result = await generator.generate_agent(
        "chief-architect",
        "Python web app",
    )

    # Result should include frontmatter + tuned body
    assert result.agent_name == "chief-architect"
    assert result.content.startswith("---\n")
    assert "name: test-agent" in result.content
    assert "# Tuned Agent Body" in result.content
    assert result.tuned


@pytest.mark.asyncio
async def test_generate_agent_invalid_name(
    mocker: MockerFixture,
) -> None:
    """Test generate_agent raises ValueError for invalid agent name."""
    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)

    with pytest.raises(
        ValueError,
        match="Invalid agent name: invalid-agent",
    ):
        await generator.generate_agent("invalid-agent", "target context")


@pytest.mark.asyncio
async def test_generate_all_agents(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test generate_all_agents generates all required agents."""
    # Setup agent directory
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for source_file in REQUIRED_AGENTS.values():
        (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

    # Mock tuner
    mock_tuner = AsyncMock()
    mock_tuning_result: TuningResult = mocker.Mock(
        content="# Tuned Content",
        changes=["Change 1"],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
    )
    generator.tuner = mock_tuner

    results = await generator.generate_all_agents("Python project")

    # Verify all 8 agents generated
    assert len(results) == 8
    for agent_name in REQUIRED_AGENTS:
        assert agent_name in results
        assert results[agent_name].agent_name == agent_name
        assert results[agent_name].tuned


# Test Dry Run Mode


@pytest.mark.asyncio
async def test_dry_run_mode(
    tmp_path: Path,
    mocker: MockerFixture,
) -> None:
    """Test dry_run mode skips tuning but processes structure."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "chief-architect.md").write_text(SAMPLE_AGENT_CONTENT)

    # Mock tuner for dry run
    mock_tuner = AsyncMock()
    mock_tuning_result: TuningResult = mocker.Mock(
        content="# Original Content",
        changes=[],
        dry_run=True,
        token_usage_input=0,
        token_usage_output=0,
    )
    mock_tuner.tune = AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(
        mock_orchestrator,
        reference_dir=agents_dir,
        dry_run=True,
    )
    generator.tuner = mock_tuner

    result = await generator.generate_agent(
        "chief-architect",
        "target context",
    )

    # Dry run should set tuned=False
    assert not result.tuned
    assert not result.changes


class TestSubagentsParallelism:
    """Verify generate_all_agents fans out concurrently (Phase 2)."""

    @pytest.mark.asyncio
    async def test_generate_all_agents_runs_in_parallel(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ) -> None:
        """All eight agent tunings dispatch before any single one returns."""
        # Populate the reference dir with the eight required agent files.
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        for source_file in REQUIRED_AGENTS.values():
            (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

        # Latch that records each call's start order, then waits until
        # all sibling calls have started before allowing any to return.
        # If the generator were sequential, only the first call would
        # ever start.
        active_calls = 0
        max_active = 0
        gate = asyncio.Event()

        async def slow_tune(*_args: object, **_kwargs: object) -> object:
            nonlocal active_calls, max_active
            active_calls += 1
            max_active = max(max_active, active_calls)
            if active_calls >= len(REQUIRED_AGENTS):
                gate.set()
            await gate.wait()
            active_calls -= 1
            return mocker.Mock(
                content="# tuned body",
                changes=["change"],
                dry_run=False,
                token_usage_input=1,
                token_usage_output=1,
            )

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")

        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
            dry_run=False,
        )
        # Replace the tuner's tune with the latch-instrumented stub.
        generator.tuner = AsyncMock()
        generator.tuner.tune = slow_tune

        results = await generator.generate_all_agents("test-context")

        # The latch only releases ``gate`` once ``active_calls`` reaches
        # ``len(REQUIRED_AGENTS)``, so the gather can only return if every
        # agent was in-flight at the same instant. Asserting the strict
        # equality (rather than a weaker ``>= 2`` lower bound) makes the
        # invariant explicit and would catch a regression where the
        # semaphore was tightened or the gather was serialized.
        assert set(results) == set(REQUIRED_AGENTS)
        assert max_active == len(REQUIRED_AGENTS), (
            f"Expected all {len(REQUIRED_AGENTS)} agents in-flight at once, "
            f"got max_active={max_active}"
        )

    @pytest.mark.asyncio
    async def test_generate_all_agents_respects_semaphore(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ) -> None:
        """The semaphore caps the number of in-flight tunings."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        for source_file in REQUIRED_AGENTS.values():
            (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

        in_flight = 0
        peak = 0
        complete: list[asyncio.Event] = []

        async def staged_tune(*_args: object, **_kwargs: object) -> object:
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            ev = asyncio.Event()
            complete.append(ev)
            # Release one slot at a time once enough tasks queued up.
            if len(complete) >= 2:
                # Signal all stalled siblings to finish in order.
                for waiter in complete:
                    waiter.set()
            await ev.wait()
            in_flight -= 1
            return mocker.Mock(
                content="# t",
                changes=[],
                dry_run=False,
                token_usage_input=1,
                token_usage_output=1,
            )

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
            dry_run=False,
            max_concurrency=2,
        )
        generator.tuner = AsyncMock()
        generator.tuner.tune = staged_tune

        await generator.generate_all_agents("ctx")
        assert peak <= 2


class TestSubagentsBatchPlan:
    """Phase 5b: ``build_batch_plan`` + ``apply_batch_result``."""

    def test_build_batch_plan_yields_one_entry_per_required_agent(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """One :class:`SubagentBatchEntry` per file in REQUIRED_AGENTS."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        for source_file in REQUIRED_AGENTS.values():
            (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
            dry_run=False,
        )

        plan = generator.build_batch_plan("Test target context")

        assert len(plan) == len(REQUIRED_AGENTS)
        assert all(isinstance(e, SubagentBatchEntry) for e in plan)

    def test_build_batch_plan_custom_id_convention(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Custom IDs use the ``subagent:<name>`` shape Phase 5a expects."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        for source_file in REQUIRED_AGENTS.values():
            (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
        )

        plan = generator.build_batch_plan("ctx")
        custom_ids = [entry.custom_id for entry in plan]

        # Each custom_id is unique and prefixed with ``subagent:``.
        assert len(set(custom_ids)) == len(custom_ids)
        for cid in custom_ids:
            assert cid.startswith("subagent:")

    def test_build_batch_plan_captures_frontmatter_per_entry(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Each entry carries its agent's frontmatter for later re-attach."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        for source_file in REQUIRED_AGENTS.values():
            (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
        )

        plan = generator.build_batch_plan("ctx")

        # SAMPLE_AGENT_CONTENT starts with ``---`` and contains ``name:``.
        for entry in plan:
            assert entry.frontmatter.startswith("---")
            assert "name:" in entry.frontmatter

    def test_apply_batch_result_reattaches_frontmatter(self) -> None:
        """``apply_batch_result`` rebuilds ``frontmatter\\nbody``."""
        tool_result = ToolUseResult(
            tool_name="report_tuning",
            tool_input={
                "tuned_content": "# Adapted body\n",
                "changes": ["renamed FastAPI to Django"],
            },
            token_usage=TokenUsage(input_tokens=10, output_tokens=5),
            model="claude",
            message_id="msg_x",
        )

        result = SubagentsGenerator.apply_batch_result(
            agent_name="chief-architect",
            frontmatter="---\nname: chief-architect\n---",
            tool_result=tool_result,
        )

        assert result.agent_name == "chief-architect"
        assert result.tuned
        assert result.content.startswith("---\n")
        assert "# Adapted body" in result.content
        assert "renamed FastAPI to Django" in result.changes

    def test_get_agent_frontmatter_returns_yaml_block_unmodified(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Public sibling of ``apply_batch_result`` for the resume path.

        Replaces two ``noqa: SLF001`` suppressions in
        ``batch_dispatch.py`` (review feedback on PR #315). The
        method must return the YAML frontmatter block byte-equivalent
        to what ``_parse_frontmatter`` would have produced — same
        leading ``---``, same closing delimiter, no body content.
        """
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        (agents_dir / "chief-architect.md").write_text(
            SAMPLE_AGENT_CONTENT, encoding="utf-8"
        )

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
        )

        frontmatter = generator.get_agent_frontmatter("chief-architect")

        assert frontmatter.startswith("---")
        assert "name: test-agent" in frontmatter
        # Closing delimiter present, body NOT included.
        assert frontmatter.rstrip().endswith("---")
        assert "# Test Agent" not in frontmatter

    def test_get_agent_frontmatter_picks_up_local_edits_between_calls(
        self, tmp_path: Path, mocker: MockerFixture
    ) -> None:
        """Re-read semantics: edit on disk → fresh return value.

        ``_frontmatter_for`` (now folded into this method) was
        documented to re-read at fetch time so a frontmatter edit
        between submit and fetch is picked up automatically. This
        test exercises that contract directly — review feedback
        flagged that the docstring claimed this guarantee but no
        test backed it up.
        """
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        agent_file = agents_dir / "chief-architect.md"
        agent_file.write_text(SAMPLE_AGENT_CONTENT, encoding="utf-8")

        mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
        generator = SubagentsGenerator(
            mocker.Mock(),
            reference_dir=agents_dir,
        )

        first = generator.get_agent_frontmatter("chief-architect")

        # Edit the source file's frontmatter in place.
        agent_file.write_text(
            SAMPLE_AGENT_CONTENT.replace(
                "name: test-agent", "name: edited-after-submit"
            ),
            encoding="utf-8",
        )

        second = generator.get_agent_frontmatter("chief-architect")

        assert "name: test-agent" in first
        assert "name: edited-after-submit" in second
        assert first != second


# Mutation-killing tests: module constants


def test_default_max_concurrency_is_eight() -> None:
    """DEFAULT_MAX_CONCURRENCY is exactly 8 (kills 8->9)."""
    assert DEFAULT_MAX_CONCURRENCY == 8


def test_reference_agents_dir_resolves_to_claude_agents() -> None:
    """REFERENCE_AGENTS_DIR ends with .claude/agents under the repo root."""
    actual = REFERENCE_AGENTS_DIR
    assert actual is not None
    assert actual.name == "agents"
    assert actual.parent.name == ".claude"
    repo_root = Path(subagents_mod.__file__).parent.parent.parent
    assert actual == repo_root / ".claude" / "agents"


def test_source_agent_context_exact_text() -> None:
    """SOURCE_AGENT_CONTEXT matches its exact wording (kills string mutants)."""
    assert SOURCE_AGENT_CONTEXT == (
        "Mojo ML research project (ml-odyssey) with multi-level "
        "agent hierarchy, paper implementations, and research workflows"
    )


def test_required_agents_exact_mapping() -> None:
    """REQUIRED_AGENTS maps exact keys to exact source filenames."""
    assert REQUIRED_AGENTS == {
        "chief-architect": "chief-architect.md",
        "quality-reviewer": "code-review-orchestrator.md",
        "test-generator": "test-specialist.md",
        "security-auditor": "security-specialist.md",
        "dependency-checker": "dependency-review-specialist.md",
        "documentation": "documentation-specialist.md",
        "refactorer": "implementation-specialist.md",
        "performance": "performance-specialist.md",
    }


# Mutation-killing tests: split_frontmatter


def test_split_frontmatter_returns_exact_parts() -> None:
    """split_frontmatter splits delimiters from body with exact values."""
    frontmatter, body = split_frontmatter(SAMPLE_AGENT_CONTENT)
    assert frontmatter.startswith("---\n")
    assert frontmatter.endswith("\n---")
    assert body.startswith("\n# Test Agent")


def test_split_frontmatter_missing_message_exact() -> None:
    """Missing frontmatter raises ValueError with the exact message."""
    with pytest.raises(ValueError, match="Agent content missing YAML") as exc:
        split_frontmatter("no frontmatter here")
    assert str(exc.value) == "Agent content missing YAML frontmatter"


# Mutation-killing tests: SubagentBatchEntry frozen


def test_subagent_batch_entry_is_frozen() -> None:
    """SubagentBatchEntry rejects attribute assignment (kills frozen=False)."""
    entry = SubagentBatchEntry(
        agent_name="chief-architect",
        custom_id="subagent:chief-architect",
        frontmatter="---\nname: chief-architect\n---",
        request=object(),  # type: ignore[arg-type]
    )
    with pytest.raises(dataclasses.FrozenInstanceError, match="cannot assign"):
        _set_attr(entry, "agent_name", "other")


# Mutation-killing tests: validation error messages


def _make_generator_no_validate(
    mocker: MockerFixture, reference_dir: Path
) -> SubagentsGenerator:
    """Build a generator with reference-dir validation patched out."""
    mocker.patch("start_green_stay_green.ai.tuner.ContentTuner")
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    return SubagentsGenerator(mocker.Mock(), reference_dir=reference_dir)


def test_check_directory_exists_missing_message_exact(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Missing-directory error message is exact, including the path."""
    missing = tmp_path / "nope"
    generator = _make_generator_no_validate(mocker, missing)
    with pytest.raises(FileNotFoundError, match="Reference directory") as exc:
        generator._check_directory_exists()
    assert str(exc.value) == f"Reference directory not found: {missing}"


def test_check_directory_exists_not_dir_message_exact(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Not-a-directory error message is exact, including the path."""
    file_path = tmp_path / "afile.txt"
    file_path.write_text("x")
    generator = _make_generator_no_validate(mocker, file_path)
    with pytest.raises(NotADirectoryError, match="not a directory") as exc:
        generator._check_directory_exists()
    assert str(exc.value) == f"Reference path is not a directory: {file_path}"


def test_check_required_agents_message_lists_each_missing(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Missing-agents message lists every agent joined with ', '."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    generator = _make_generator_no_validate(mocker, agents_dir)
    with pytest.raises(FileNotFoundError, match="Missing required") as exc:
        generator._check_required_agents()
    expected_parts = [
        f"{name} (source: {src})" for name, src in REQUIRED_AGENTS.items()
    ]
    assert str(exc.value) == (
        f"Missing required agent files: {', '.join(expected_parts)}"
    )


def test_check_required_agents_message_single_missing(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """A single missing agent yields a per-agent 'name (source: file)' entry."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    # Create all but chief-architect.
    for name, src in REQUIRED_AGENTS.items():
        if name != "chief-architect":
            (agents_dir / src).write_text(SAMPLE_AGENT_CONTENT)
    generator = _make_generator_no_validate(mocker, agents_dir)
    with pytest.raises(FileNotFoundError, match="Missing required") as exc:
        generator._check_required_agents()
    assert str(exc.value) == (
        "Missing required agent files: " "chief-architect (source: chief-architect.md)"
    )


# Mutation-killing tests: invalid agent name message


@pytest.mark.asyncio
async def test_generate_agent_invalid_name_message_exact(
    mocker: MockerFixture,
) -> None:
    """Invalid agent name error lists all valid names joined with ', '."""
    mocker.patch("start_green_stay_green.ai.tuner.ContentTuner")
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    generator = SubagentsGenerator(mocker.Mock())
    with pytest.raises(ValueError, match="Invalid agent name") as exc:
        await generator.generate_agent("bogus", "ctx")
    valid = ", ".join(REQUIRED_AGENTS.keys())
    assert str(exc.value) == (f"Invalid agent name: bogus. Must be one of: {valid}")


# Mutation-killing tests: preserve_sections passed to tuner.tune


@pytest.mark.asyncio
async def test_tune_agent_body_passes_exact_preserve_sections(
    mocker: MockerFixture,
) -> None:
    """_tune_agent_body forwards the exact preserve-section heading list."""
    mock_tuner = AsyncMock()
    mock_tuner.tune = AsyncMock(return_value=mocker.Mock(content="# C", changes=[]))
    mocker.patch("start_green_stay_green.ai.tuner.ContentTuner")
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    generator = SubagentsGenerator(mocker.Mock())
    generator.tuner = mock_tuner

    await generator._tune_agent_body("chief-architect", "body", "tgt")

    kwargs = mock_tuner.tune.call_args.kwargs
    assert kwargs["source_content"] == "body"
    assert kwargs["source_context"] == SOURCE_AGENT_CONTEXT
    assert kwargs["target_context"] == "tgt"
    assert kwargs["preserve_sections"] == [
        "## Identity",
        "## Scope",
        "## Workflow",
        "## Skills",
        "## Constraints",
    ]


# Mutation-killing tests: build_batch_plan exact request construction


def _build_plan_with_mock_tuner(
    tmp_path: Path, mocker: MockerFixture
) -> tuple[SubagentsGenerator, list[SubagentBatchEntry], MagicMock]:
    """Build a plan with build_batch_request mocked to capture args."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for source_file in REQUIRED_AGENTS.values():
        (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    generator = SubagentsGenerator(mocker.Mock(), reference_dir=agents_dir)

    def fake_request(*, custom_id: str, **_kw: object) -> object:
        return mocker.Mock(custom_id=custom_id)

    mock_build = mocker.patch.object(
        generator.tuner, "build_batch_request", side_effect=fake_request
    )
    plan = generator.build_batch_plan("Target ctx")
    return generator, plan, mock_build


def test_build_batch_plan_request_kwargs_exact(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """build_batch_plan calls build_batch_request with exact kwargs."""
    _generator, _plan, mock_build = _build_plan_with_mock_tuner(tmp_path, mocker)

    first_call = mock_build.call_args_list[0].kwargs
    assert first_call["custom_id"] == "subagent:chief-architect"
    assert first_call["source_context"] == SOURCE_AGENT_CONTEXT
    assert first_call["target_context"] == "Target ctx"
    assert first_call["preserve_sections"] == [
        "## Identity",
        "## Scope",
        "## Workflow",
        "## Skills",
        "## Constraints",
    ]
    # source_content is the body (no leading frontmatter delimiter).
    assert not first_call["source_content"].startswith("---")
    assert "# Test Agent" in first_call["source_content"]


def test_build_batch_plan_custom_id_from_request(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Entry.custom_id is taken from the request, not recomputed."""
    _generator, plan, _mock = _build_plan_with_mock_tuner(tmp_path, mocker)
    assert plan[0].custom_id == "subagent:chief-architect"
    assert plan[0].agent_name == "chief-architect"
    assert plan[0].frontmatter.startswith("---")


# Mutation-killing tests: apply_batch_result is a staticmethod


def test_apply_batch_result_is_staticmethod() -> None:
    """apply_batch_result is callable off the class without an instance."""
    attr = SubagentsGenerator.__dict__["apply_batch_result"]
    assert isinstance(attr, staticmethod)


def test_apply_batch_result_content_is_frontmatter_then_body() -> None:
    """apply_batch_result builds exactly 'frontmatter\\nbody' and tuned=True."""
    tool_result = ToolUseResult(
        tool_name="report_tuning",
        tool_input={"tuned_content": "BODY", "changes": ["c1"]},
        token_usage=TokenUsage(input_tokens=1, output_tokens=2),
        model="claude",
        message_id="m1",
    )
    result = SubagentsGenerator.apply_batch_result(
        agent_name="performance",
        frontmatter="---\nfm\n---",
        tool_result=tool_result,
    )
    assert result.agent_name == "performance"
    assert result.content == "---\nfm\n---\nBODY"
    assert result.tuned
    assert result.changes == ["c1"]


# Mutation-killing tests: generate_all_agents zip strict ordering


@pytest.mark.asyncio
async def test_generate_all_agents_preserves_required_order(
    tmp_path: Path, mocker: MockerFixture
) -> None:
    """Results dict keys appear in REQUIRED_AGENTS declaration order."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    for source_file in REQUIRED_AGENTS.values():
        (agents_dir / source_file).write_text(SAMPLE_AGENT_CONTENT)
    mock_tuner = AsyncMock()
    mock_tuner.tune = AsyncMock(return_value=mocker.Mock(content="# C", changes=[]))
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    generator = SubagentsGenerator(mocker.Mock(), reference_dir=agents_dir)
    generator.tuner = mock_tuner

    results = await generator.generate_all_agents("ctx")
    assert list(results) == list(REQUIRED_AGENTS)


# Mutation-killing tests: generate() NotImplementedError message


def test_generate_sync_not_implemented_message_exact(
    mocker: MockerFixture,
) -> None:
    """generate() raises NotImplementedError with the exact guidance text."""
    mocker.patch("start_green_stay_green.ai.tuner.ContentTuner")
    mocker.patch.object(SubagentsGenerator, "_validate_reference_dir")
    generator = SubagentsGenerator(mocker.Mock())
    with pytest.raises(NotImplementedError, match="requires async") as exc:
        generator.generate()
    assert str(exc.value) == (
        "SubagentsGenerator requires async operations. "
        "Use generate_all_agents() or generate_agent() instead."
    )
