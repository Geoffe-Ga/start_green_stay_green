"""Unit tests for ClaudeMdGenerator."""

from pathlib import Path
from unittest.mock import create_autospec

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.generators.claude_md import ClaudeMdGenerationResult
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator


class TestClaudeMdGenerationResult:
    """Test ClaudeMdGenerationResult dataclass."""

    def test_claude_md_generation_result_creation(self) -> None:
        """Test creating ClaudeMdGenerationResult with all fields."""
        result = ClaudeMdGenerationResult(
            content="# CLAUDE.md\n\nProject context",
            token_usage_input=1000,
            token_usage_output=500,
        )

        assert result.content == "# CLAUDE.md\n\nProject context"
        assert result.token_usage_input == 1000
        assert result.token_usage_output == 500

    def test_claude_md_generation_result_is_immutable(self) -> None:
        """Test ClaudeMdGenerationResult is immutable."""
        result = ClaudeMdGenerationResult(
            content="content",
            token_usage_input=100,
            token_usage_output=50,
        )

        with pytest.raises(AttributeError):
            result.content = "modified"  # type: ignore[misc]


class TestClaudeMdGeneratorInit:
    """Test ClaudeMdGenerator initialization."""

    def test_claude_md_generator_init_with_defaults(self) -> None:
        """Test ClaudeMdGenerator initialization with default parameters."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ClaudeMdGenerator(orchestrator)

        assert generator.orchestrator is orchestrator
        assert generator.reference_dir.name == "claude"
        assert generator.quality_ref_path.name == "MAXIMUM_QUALITY_ENGINEERING.md"

    def test_claude_md_generator_init_with_custom_reference_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """Test ClaudeMdGenerator with custom reference directory."""
        orchestrator = create_autospec(AIOrchestrator)
        custom_dir = tmp_path / "custom_claude"
        custom_dir.mkdir()
        (custom_dir / "CLAUDE.md").write_text("# Custom CLAUDE.md")

        generator = ClaudeMdGenerator(orchestrator, reference_dir=custom_dir)

        assert generator.reference_dir == custom_dir


class TestClaudeMdGeneratorValidation:
    """Test ClaudeMdGenerator validation methods."""

    def test_validate_reference_dir_missing_directory(self, tmp_path: Path) -> None:
        """Test validation raises error for missing directory."""
        orchestrator = create_autospec(AIOrchestrator)
        nonexistent_dir = tmp_path / "nonexistent"
        generator = ClaudeMdGenerator(orchestrator, reference_dir=nonexistent_dir)

        with pytest.raises(ValueError, match="Reference directory not found"):
            generator._validate_reference_dir()

    def test_validate_reference_dir_not_a_directory(self, tmp_path: Path) -> None:
        """Test validation raises error when path is not a directory."""
        orchestrator = create_autospec(AIOrchestrator)
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a directory")
        generator = ClaudeMdGenerator(orchestrator, reference_dir=file_path)

        with pytest.raises(ValueError, match="not a directory"):
            generator._validate_reference_dir()

    def test_validate_reference_dir_missing_claude_md(self, tmp_path: Path) -> None:
        """Test validation raises error for missing CLAUDE.md file."""
        orchestrator = create_autospec(AIOrchestrator)
        empty_dir = tmp_path / "empty_claude"
        empty_dir.mkdir()
        generator = ClaudeMdGenerator(orchestrator, reference_dir=empty_dir)

        with pytest.raises(ValueError, match=r"CLAUDE\.md not found"):
            generator._validate_reference_dir()

    def test_validate_reference_dir_success(self, tmp_path: Path) -> None:
        """Test validation succeeds with valid reference directory."""
        orchestrator = create_autospec(AIOrchestrator)
        valid_dir = tmp_path / "valid_claude"
        valid_dir.mkdir()
        (valid_dir / "CLAUDE.md").write_text("# CLAUDE.md\n\nContent")

        generator = ClaudeMdGenerator(orchestrator, reference_dir=valid_dir)
        generator._validate_reference_dir()  # Should not raise


class TestClaudeMdGeneratorLoadReferences:
    """Test ClaudeMdGenerator reference loading methods."""

    def test_load_claude_md_reference_success(self, tmp_path: Path) -> None:
        """Test loading CLAUDE.md reference file."""
        orchestrator = create_autospec(AIOrchestrator)
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        claude_md_content = "# CLAUDE.md\n\n## Critical Principles\n\nContent"
        (ref_dir / "CLAUDE.md").write_text(claude_md_content)

        generator = ClaudeMdGenerator(orchestrator, reference_dir=ref_dir)
        content = generator._load_claude_md_reference()

        assert content == claude_md_content

    def test_load_claude_md_reference_file_not_found(self, tmp_path: Path) -> None:
        """Test loading raises FileNotFoundError for missing CLAUDE.md."""
        orchestrator = create_autospec(AIOrchestrator)
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        generator = ClaudeMdGenerator(orchestrator, reference_dir=empty_dir)

        with pytest.raises(FileNotFoundError):
            generator._load_claude_md_reference()

    def test_load_quality_reference_success(self, tmp_path: Path) -> None:
        """Test loading MAXIMUM_QUALITY_ENGINEERING.md reference file."""
        orchestrator = create_autospec(AIOrchestrator)
        quality_content = "# Maximum Quality Engineering\n\nQuality standards"
        quality_path = tmp_path / "MAXIMUM_QUALITY_ENGINEERING.md"
        quality_path.write_text(quality_content)

        generator = ClaudeMdGenerator(orchestrator, quality_ref_path=quality_path)
        content = generator._load_quality_reference()

        assert content == quality_content

    def test_load_quality_reference_file_not_found(self, tmp_path: Path) -> None:
        """Test loading raises FileNotFoundError for missing quality reference."""
        orchestrator = create_autospec(AIOrchestrator)
        nonexistent_path = tmp_path / "nonexistent.md"

        generator = ClaudeMdGenerator(orchestrator, quality_ref_path=nonexistent_path)

        with pytest.raises(FileNotFoundError):
            generator._load_quality_reference()


class TestClaudeMdGeneratorGenerate:
    """Test ClaudeMdGenerator generate method."""

    def test_generate_calls_orchestrator(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generate calls AI orchestrator with correct prompt."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="# Generated CLAUDE.md\n\nCustomized content",
            format="markdown",
            token_usage=TokenUsage(input_tokens=2000, output_tokens=1000),
            model="claude-opus-4-5-20251101",
            message_id="msg_test123",
        )

        # Setup reference files
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text("# Reference CLAUDE.md")
        quality_path = tmp_path / "MAXIMUM_QUALITY_ENGINEERING.md"
        quality_path.write_text("# Quality Standards")

        generator = ClaudeMdGenerator(
            orchestrator,
            reference_dir=ref_dir,
            quality_ref_path=quality_path,
        )

        project_config = {
            "project_name": "test-project",
            "language": "python",
            "scripts": ["lint.sh", "test.sh", "format.sh"],
            "skills": ["vibe.md", "concurrency.md"],
        }

        result = generator.generate(project_config)

        # Verify orchestrator was called
        orchestrator.generate.assert_called_once()
        call_args = orchestrator.generate.call_args
        prompt = call_args[0][0]
        output_format = call_args[0][1]

        # Verify prompt contains required elements
        assert "test-project" in prompt
        assert "python" in prompt
        assert "CLAUDE.md" in prompt
        assert output_format == "markdown"

        # Verify result
        assert result.content == "# Generated CLAUDE.md\n\nCustomized content"
        assert result.token_usage_input == 2000
        assert result.token_usage_output == 1000

    def test_generate_includes_maximum_quality_context(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generate includes MAXIMUM_QUALITY_ENGINEERING.md in prompt."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="# CLAUDE.md",
            format="markdown",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="claude-opus-4-5-20251101",
            message_id="msg_test",
        )

        # Setup with specific quality content
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text("# Reference")
        quality_path = tmp_path / "quality.md"
        quality_content = "# UNIQUE_QUALITY_MARKER\n\nQuality standards here"
        quality_path.write_text(quality_content)

        generator = ClaudeMdGenerator(
            orchestrator,
            reference_dir=ref_dir,
            quality_ref_path=quality_path,
        )

        generator.generate({"project_name": "test", "language": "python"})

        # Verify quality content was included in prompt
        call_args = orchestrator.generate.call_args
        prompt = call_args[0][0]
        assert "UNIQUE_QUALITY_MARKER" in prompt

    def test_generate_includes_project_scripts(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generate includes project-specific scripts in output."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="# CLAUDE.md",
            format="markdown",
            token_usage=TokenUsage(input_tokens=100, output_tokens=50),
            model="claude-opus-4-5-20251101",
            message_id="msg_test",
        )

        # Setup references
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text("# Reference")
        quality_path = tmp_path / "quality.md"
        quality_path.write_text("# Quality")

        generator = ClaudeMdGenerator(
            orchestrator,
            reference_dir=ref_dir,
            quality_ref_path=quality_path,
        )

        config = {
            "project_name": "my-project",
            "language": "typescript",
            "scripts": ["custom-lint.sh", "custom-test.sh"],
        }

        generator.generate(config)

        # Verify scripts are mentioned in prompt
        call_args = orchestrator.generate.call_args
        prompt = call_args[0][0]
        assert "custom-lint.sh" in prompt
        assert "custom-test.sh" in prompt


class TestClaudeMdGeneratorValidateMarkdown:
    """Test ClaudeMdGenerator markdown validation."""

    def test_validate_markdown_with_valid_structure(self) -> None:
        """Test validation passes for valid markdown structure."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ClaudeMdGenerator(orchestrator)

        valid_markdown = """# Project Title

## Section 1

Content here

## Section 2

More content
"""
        # Should not raise
        generator._validate_markdown_structure(valid_markdown)

    def test_validate_markdown_missing_h1_title(self) -> None:
        """Test validation fails if no H1 title."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ClaudeMdGenerator(orchestrator)

        invalid_markdown = """## Section 1

No H1 title
"""
        with pytest.raises(ValueError, match="missing H1 title"):
            generator._validate_markdown_structure(invalid_markdown)

    def test_validate_markdown_empty_content(self) -> None:
        """Test validation fails for empty content."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = ClaudeMdGenerator(orchestrator)

        with pytest.raises(ValueError, match="empty"):
            generator._validate_markdown_structure("")


class TestClaudeMdGeneratorIntegration:
    """Integration tests for ClaudeMdGenerator full workflow."""

    def test_full_workflow(
        self,
        tmp_path: Path,
    ) -> None:
        """Test complete CLAUDE.md generation workflow."""
        orchestrator = create_autospec(AIOrchestrator)
        generated_content = (
            "# My Project CLAUDE.md\n\n## Critical Principles\n\nCustom content"
        )
        orchestrator.generate.return_value = GenerationResult(
            content=generated_content,
            format="markdown",
            token_usage=TokenUsage(input_tokens=3000, output_tokens=1500),
            model="claude-opus-4-5-20251101",
            message_id="msg_integration",
        )

        # Setup complete reference environment
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text(
            "# Reference CLAUDE.md\n\n## Principles\n\nTemplate"
        )
        quality_path = tmp_path / "MAXIMUM_QUALITY_ENGINEERING.md"
        quality_path.write_text("# Maximum Quality Engineering\n\nStandards")

        generator = ClaudeMdGenerator(
            orchestrator,
            reference_dir=ref_dir,
            quality_ref_path=quality_path,
        )

        config = {
            "project_name": "awesome-project",
            "language": "rust",
            "scripts": ["cargo-lint.sh", "cargo-test.sh"],
            "skills": ["concurrency.md", "error-handling.md"],
        }

        result = generator.generate(config)

        # Verify result structure
        assert "# My Project CLAUDE.md" in result.content
        assert result.token_usage_input == 3000
        assert result.token_usage_output == 1500

        # Verify orchestrator was called with complete context
        call_args = orchestrator.generate.call_args
        prompt = call_args[0][0]
        assert "awesome-project" in prompt
        assert "rust" in prompt
