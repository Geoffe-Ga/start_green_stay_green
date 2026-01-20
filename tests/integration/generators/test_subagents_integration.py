"""Integration tests for SubagentsGenerator with real reference agents.

These tests validate that:
1. The reference directory exists with all required files
2. Agent generation works with real reference agents
3. Frontmatter structure is preserved correctly
4. Generated agents have valid structure
"""

from __future__ import annotations

import re

import pytest

from start_green_stay_green.generators.subagents import REFERENCE_AGENTS_DIR
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS
from start_green_stay_green.generators.subagents import SOURCE_AGENT_CONTEXT
from start_green_stay_green.generators.subagents import SubagentsGenerator


def test_reference_directory_exists() -> None:
    """Test that the reference agents directory exists."""
    assert (
        REFERENCE_AGENTS_DIR.exists()
    ), f"Reference directory not found: {REFERENCE_AGENTS_DIR}"
    assert (
        REFERENCE_AGENTS_DIR.is_dir()
    ), f"Reference path is not a directory: {REFERENCE_AGENTS_DIR}"


def test_all_required_agent_files_exist() -> None:
    """Test that all 8 required agent source files exist in reference directory."""
    missing_agents = []
    for agent_name, source_file in REQUIRED_AGENTS.items():
        agent_path = REFERENCE_AGENTS_DIR / source_file
        if not agent_path.exists():
            missing_agents.append(f"{agent_name} (source: {source_file})")

    assert (
        not missing_agents
    ), f"Missing required agent files: {', '.join(missing_agents)}"


def test_agent_files_have_yaml_frontmatter() -> None:
    """Test that all agent files have valid YAML frontmatter."""
    frontmatter_pattern = r"^---\n.*?\n---"

    for agent_name, source_file in REQUIRED_AGENTS.items():
        agent_path = REFERENCE_AGENTS_DIR / source_file
        content = agent_path.read_text()

        match = re.match(frontmatter_pattern, content, re.DOTALL)
        assert match, f"Agent {agent_name} ({source_file}) missing YAML frontmatter"

        # Verify frontmatter contains expected fields
        frontmatter = match.group(0)
        assert (
            "name:" in frontmatter
        ), f"Agent {agent_name} frontmatter missing 'name' field"
        assert (
            "description:" in frontmatter
        ), f"Agent {agent_name} frontmatter missing 'description' field"


def test_subagents_generator_validates_real_directory(mocker) -> None:  # type: ignore[no-untyped-def]
    """Test that SubagentsGenerator successfully validates real reference directory."""
    # Create a mock orchestrator (not used for validation)
    mock_orch = mocker.Mock()

    # This should not raise - validation happens in __init__
    generator = SubagentsGenerator(mock_orch)

    assert generator.reference_dir == REFERENCE_AGENTS_DIR
    assert generator.reference_dir.exists()


@pytest.mark.asyncio
async def test_generate_single_agent_with_real_files(mocker) -> None:  # type: ignore[no-untyped-def]
    """Test generating a single agent using real reference files.

    This test uses real reference files but mocks the ContentTuner
    to avoid requiring an API key in tests.
    """
    # Mock ContentTuner to avoid API calls
    mock_tuner = mocker.AsyncMock()
    mock_tuning_result = mocker.Mock(
        content="# Tuned Chief Architect\n\n## Identity\nTuned content...",
        changes=["Updated for Python web app context"],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = mocker.AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )

    # Create mock orchestrator
    mock_orchestrator = mocker.Mock()

    # Generate one agent using real reference files
    generator = SubagentsGenerator(mock_orchestrator)
    generator.tuner = mock_tuner

    result = await generator.generate_agent(
        "chief-architect",
        "Python web application with Flask",
    )

    # Verify result structure
    assert result.agent_name == "chief-architect"
    assert result.content.startswith("---\n")
    assert "# Tuned Chief Architect" in result.content
    assert result.tuned
    assert result.changes

    # Verify tuner was called with real content from reference file
    mock_tuner.tune.assert_called_once()
    call_args = mock_tuner.tune.call_args
    # Should use SOURCE_AGENT_CONTEXT constant
    assert call_args[1]["source_context"] == SOURCE_AGENT_CONTEXT
    assert "Python web application" in call_args[1]["target_context"]


@pytest.mark.asyncio
async def test_frontmatter_preservation_with_real_files(mocker) -> None:  # type: ignore[no-untyped-def]
    """Test that frontmatter from real reference files is preserved."""
    # Mock ContentTuner
    mock_tuner = mocker.AsyncMock()
    mock_tuning_result = mocker.Mock(
        content="# Tuned Content",
        changes=[],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = mocker.AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)
    generator.tuner = mock_tuner

    # Load real agent to verify frontmatter
    real_agent_path = REFERENCE_AGENTS_DIR / "chief-architect.md"
    real_content = real_agent_path.read_text()
    original_frontmatter = real_content.split("\n---\n")[0] + "\n---"

    # Generate agent
    result = await generator.generate_agent("chief-architect", "test context")

    # Verify frontmatter is preserved from original
    result_frontmatter = result.content.split("\n---\n")[0] + "\n---"
    assert result_frontmatter == original_frontmatter


@pytest.mark.asyncio
async def test_generate_all_agents_with_real_files(mocker) -> None:  # type: ignore[no-untyped-def]
    """Test generating all 8 agents using real reference files."""
    # Mock ContentTuner
    mock_tuner = mocker.AsyncMock()
    mock_tuning_result = mocker.Mock(
        content="# Tuned Content",
        changes=["Change 1"],
        dry_run=False,
        token_usage_input=100,
        token_usage_output=50,
    )
    mock_tuner.tune = mocker.AsyncMock(return_value=mock_tuning_result)

    mocker.patch(
        "start_green_stay_green.ai.tuner.ContentTuner",
        return_value=mock_tuner,
    )

    mock_orchestrator = mocker.Mock()
    generator = SubagentsGenerator(mock_orchestrator)
    generator.tuner = mock_tuner

    # Generate all agents
    results = await generator.generate_all_agents("TypeScript microservices")

    # Verify all 8 agents generated
    assert len(results) == 8
    for agent_name in REQUIRED_AGENTS:
        assert agent_name in results
        assert results[agent_name].agent_name == agent_name
        assert results[agent_name].content.startswith("---\n")
