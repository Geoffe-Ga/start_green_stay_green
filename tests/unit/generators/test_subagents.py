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
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest

from start_green_stay_green.generators.subagents import REFERENCE_AGENTS_DIR
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS
from start_green_stay_green.generators.subagents import SubagentGenerationResult
from start_green_stay_green.generators.subagents import SubagentsGenerator

if TYPE_CHECKING:
    from pathlib import Path

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
