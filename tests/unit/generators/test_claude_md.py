"""Unit tests for ClaudeMdGenerator."""

from pathlib import Path
from typing import Any
from unittest.mock import create_autospec

import pytest

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.orchestrator import GenerationResult
from start_green_stay_green.ai.orchestrator import TokenUsage
from start_green_stay_green.generators.claude_md import CLAUDE_DOC_NAMES
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
            "skills": ["vibe", "concurrency"],
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
            "skills": ["concurrency", "error-handling"],
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


class TestClaudeMdGeneratorBaseline:
    """Tests for the deterministic, no-API baseline path (Phase 1)."""

    def test_baseline_renders_without_orchestrator(self) -> None:
        """Baseline path works with no orchestrator at all."""
        generator = ClaudeMdGenerator()  # No orchestrator.

        result = generator.generate_baseline(
            {
                "project_name": "my-cool-app",
                "language": "python",
                "scripts": ["check-all.sh", "test.sh"],
                "skills": ["testing", "security"],
            }
        )

        assert result.token_usage_input == 0
        assert result.token_usage_output == 0
        # Project name was substituted into the H1.
        assert "my-cool-app" in result.content
        # No untouched ``{{PROJECT_NAME}}`` token leaks through for known keys.
        assert "{{PROJECT_NAME}}" not in result.content

    def test_baseline_used_when_orchestrator_is_none(self) -> None:
        """generate() with orchestrator=None falls back to baseline."""
        generator = ClaudeMdGenerator(orchestrator=None)

        result = generator.generate(
            {
                "project_name": "fallback-test",
                "language": "go",
                "scripts": [],
                "skills": [],
            }
        )

        assert result.token_usage_input == 0
        assert "fallback-test" in result.content

    def test_baseline_renders_skills_and_scripts(self) -> None:
        """Baseline substitutes scripts and skills if templates use them."""
        generator = ClaudeMdGenerator()

        result = generator.generate_baseline(
            {
                "project_name": "demo",
                "language": "python",
                "scripts": ["foo.sh", "bar.sh"],
                "skills": ["alpha", "beta"],
            }
        )

        # Reference template doesn't currently use {{SCRIPTS}}/{{SKILLS}}
        # tokens, so we just assert the baseline renders without error.
        assert "# Claude Code Project Context: demo" in result.content


class TestClaudeMdGeneratorModular:
    """Tests for the modular ``.claude/`` tree emission (#397)."""

    @staticmethod
    def _config() -> dict[str, object]:
        """Return a representative project config for modular tests."""
        return {
            "project_name": "modular-demo",
            "language": "python",
            "scripts": ["check-all.sh", "test.sh"],
            "skills": ["testing", "security"],
        }

    def test_doc_names_constant_lists_six_docs(self) -> None:
        """The public doc-name constant enumerates the six split docs."""
        assert CLAUDE_DOC_NAMES == (
            "principles",
            "quality-standards",
            "workflow",
            "testing",
            "tools",
            "troubleshooting",
        )

    def test_write_modular_creates_index_and_docs(self, tmp_path: Path) -> None:
        """write_modular writes the root index plus all six split docs."""
        generator = ClaudeMdGenerator()  # No orchestrator -> baseline index.
        config = self._config()

        result = generator.write_modular(tmp_path, config)

        index = tmp_path / "CLAUDE.md"
        assert index.exists()
        # Substitution happened in the index H1.
        index_text = index.read_text(encoding="utf-8")
        assert "modular-demo" in index_text

        docs_dir = tmp_path / ".claude" / "docs"
        for name in CLAUDE_DOC_NAMES:
            doc = docs_dir / f"{name}.md"
            assert doc.exists(), f"Missing split doc: {name}.md"
            assert doc.read_text(encoding="utf-8").strip(), f"Empty doc: {name}.md"

        # Result reports zero token usage in baseline mode.
        assert result.token_usage_input == 0

    def test_write_modular_index_links_to_each_doc(self, tmp_path: Path) -> None:
        """The index references every split doc (DRY: links, not duplication)."""
        generator = ClaudeMdGenerator()

        generator.write_modular(tmp_path, self._config())

        index_text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        for name in CLAUDE_DOC_NAMES:
            assert (
                f".claude/docs/{name}.md" in index_text
            ), f"Index missing link to {name}.md"

    def test_write_modular_substitutes_tokens_in_docs(self, tmp_path: Path) -> None:
        """Token substitution applies to the split docs, not just the index."""
        generator = ClaudeMdGenerator()

        generator.write_modular(tmp_path, self._config())

        docs_dir = tmp_path / ".claude" / "docs"
        # No known token should leak through into any emitted doc.
        for name in CLAUDE_DOC_NAMES:
            text = (docs_dir / f"{name}.md").read_text(encoding="utf-8")
            assert "{{PROJECT_NAME}}" not in text, f"Unsubstituted token in {name}.md"

    def test_render_docs_returns_all_six_docs(self) -> None:
        """render_docs returns rendered content for every split doc (#387)."""
        generator = ClaudeMdGenerator()

        docs = generator.render_docs(self._config())

        assert set(docs) == set(CLAUDE_DOC_NAMES)
        for name, content in docs.items():
            assert content.strip(), f"Empty rendered doc: {name}"
            assert "{{PROJECT_NAME}}" not in content

    def test_render_docs_matches_render_modular_docs(self) -> None:
        """render_docs is the same content render_modular emits (DRY)."""
        generator = ClaudeMdGenerator()
        config = self._config()

        _index, modular_docs = generator.render_modular(config)

        assert generator.render_docs(config) == modular_docs

    def test_render_docs_missing_docs_dir_raises(self, tmp_path: Path) -> None:
        """render_docs validates the docs directory before rendering."""
        ref_dir = tmp_path / "ref"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text("# Title\n", encoding="utf-8")
        generator = ClaudeMdGenerator(reference_dir=ref_dir)

        with pytest.raises(ValueError, match="docs directory not found"):
            generator.render_docs(self._config())

    def test_write_modular_quality_doc_keeps_required_content(
        self,
        tmp_path: Path,
    ) -> None:
        """No content is dropped: quality doc retains the coverage threshold."""
        generator = ClaudeMdGenerator()

        generator.write_modular(tmp_path, self._config())

        quality = (tmp_path / ".claude" / "docs" / "quality-standards.md").read_text(
            encoding="utf-8"
        )
        assert "90%" in quality
        troubleshooting = (
            tmp_path / ".claude" / "docs" / "troubleshooting.md"
        ).read_text(encoding="utf-8")
        assert "No Shortcuts" in troubleshooting

    def test_write_modular_uses_orchestrator_for_index(
        self,
        tmp_path: Path,
    ) -> None:
        """With an orchestrator, the index is AI-tuned but docs still emitted."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="# Claude Code Project Context: modular-demo\n\nTuned index",
            format="markdown",
            token_usage=TokenUsage(input_tokens=1200, output_tokens=300),
            model="claude-opus-4-5-20251101",
            message_id="msg_modular",
        )
        generator = ClaudeMdGenerator(orchestrator)

        result = generator.write_modular(tmp_path, self._config())

        index_text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
        assert "Tuned index" in index_text
        assert result.token_usage_input == 1200
        # Docs are still written deterministically alongside the tuned index.
        docs_dir = tmp_path / ".claude" / "docs"
        assert (docs_dir / "principles.md").exists()

    def test_validate_reference_dir_missing_docs(self, tmp_path: Path) -> None:
        """Validation fails when the docs subdirectory is absent."""
        ref_dir = tmp_path / "claude"
        ref_dir.mkdir()
        (ref_dir / "CLAUDE.md").write_text("# Index\n")
        generator = ClaudeMdGenerator(reference_dir=ref_dir)

        with pytest.raises(ValueError, match="docs"):
            generator.write_modular(tmp_path / "out", self._config())

    def test_validate_reference_dir_partial_docs(self, tmp_path: Path) -> None:
        """Validation lists the specific split doc(s) that are missing."""
        ref_dir = tmp_path / "claude"
        (ref_dir / "docs").mkdir(parents=True)
        (ref_dir / "CLAUDE.md").write_text("# Index\n")
        # Provide all but one required doc to exercise the partial-missing path.
        for name in CLAUDE_DOC_NAMES[:-1]:
            (ref_dir / "docs" / f"{name}.md").write_text(f"# {name}\n")
        generator = ClaudeMdGenerator(reference_dir=ref_dir)

        with pytest.raises(ValueError, match=r"troubleshooting\.md"):
            generator.write_modular(tmp_path / "out", self._config())


def _make_ref_tree(root: Path, *, with_docs: bool = True) -> Path:
    """Create a valid reference dir (CLAUDE.md plus optional split docs)."""
    ref = root / "claude"
    ref.mkdir(parents=True)
    (ref / "CLAUDE.md").write_text("# Title\n", encoding="utf-8")
    if with_docs:
        docs = ref / "docs"
        docs.mkdir()
        for name in CLAUDE_DOC_NAMES:
            (docs / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    return ref


class TestValidateReferenceDirMessages:
    """Exact error-message assertions for ``_validate_reference_dir``."""

    def test_missing_directory_exact_message(self, tmp_path: Path) -> None:
        """Missing reference dir yields the exact, unwrapped message."""
        missing = tmp_path / "nope"
        generator = ClaudeMdGenerator(reference_dir=missing)

        with pytest.raises(ValueError, match="Reference directory") as exc:
            generator._validate_reference_dir()

        assert str(exc.value) == f"Reference directory not found: {missing}"

    def test_not_a_directory_exact_message(self, tmp_path: Path) -> None:
        """A file (not dir) yields the exact, unwrapped message."""
        path = tmp_path / "file.txt"
        path.write_text("x", encoding="utf-8")
        generator = ClaudeMdGenerator(reference_dir=path)

        with pytest.raises(ValueError, match="not a directory") as exc:
            generator._validate_reference_dir()

        assert str(exc.value) == f"Reference path is not a directory: {path}"

    def test_missing_claude_md_exact_message(self, tmp_path: Path) -> None:
        """Empty dir (no CLAUDE.md) yields the exact, unwrapped message."""
        ref = tmp_path / "claude"
        ref.mkdir()
        generator = ClaudeMdGenerator(reference_dir=ref)

        with pytest.raises(ValueError, match=r"CLAUDE\.md not found") as exc:
            generator._validate_reference_dir()

        assert str(exc.value) == (f"CLAUDE.md not found in reference directory: {ref}")


class TestValidateDocsDirMessages:
    """Exact error-message assertions for ``_validate_docs_dir``."""

    def test_missing_docs_dir_exact_message(self, tmp_path: Path) -> None:
        """Absent docs subdir yields the exact, unwrapped message."""
        ref = _make_ref_tree(tmp_path, with_docs=False)
        generator = ClaudeMdGenerator(reference_dir=ref)

        with pytest.raises(ValueError, match="docs directory not found") as exc:
            generator._validate_docs_dir()

        assert str(exc.value) == (f"Reference docs directory not found: {ref / 'docs'}")

    def test_missing_docs_listed_with_comma_space(self, tmp_path: Path) -> None:
        """Two missing docs are joined by exactly ``', '`` (comma + space)."""
        ref = _make_ref_tree(tmp_path)
        docs = ref / "docs"
        # Remove the last two docs so the join separator is exercised.
        (docs / f"{CLAUDE_DOC_NAMES[-1]}.md").unlink()
        (docs / f"{CLAUDE_DOC_NAMES[-2]}.md").unlink()
        generator = ClaudeMdGenerator(reference_dir=ref)

        with pytest.raises(ValueError, match="Missing reference docs") as exc:
            generator._validate_docs_dir()

        expected = (
            f"Missing reference docs in {docs}: "
            f"{CLAUDE_DOC_NAMES[-2]}.md, {CLAUDE_DOC_NAMES[-1]}.md"
        )
        assert str(exc.value) == expected


class TestMissingDocFiles:
    """Exact-name assertions for ``_missing_doc_files``."""

    def test_returns_dot_md_suffixed_names(self, tmp_path: Path) -> None:
        """Missing docs are returned as ``"<name>.md"`` exactly, no wrapping."""
        docs = tmp_path / "docs"
        docs.mkdir()
        # Provide only the first doc; the rest are reported missing.
        (docs / f"{CLAUDE_DOC_NAMES[0]}.md").write_text("x", encoding="utf-8")

        missing = ClaudeMdGenerator._missing_doc_files(docs)

        expected = [f"{name}.md" for name in CLAUDE_DOC_NAMES[1:]]
        assert missing == expected

    def test_returns_empty_when_all_present(self, tmp_path: Path) -> None:
        """A complete docs dir reports nothing missing."""
        docs = tmp_path / "docs"
        docs.mkdir()
        for name in CLAUDE_DOC_NAMES:
            (docs / f"{name}.md").write_text("x", encoding="utf-8")

        missing = ClaudeMdGenerator._missing_doc_files(docs)

        assert isinstance(missing, list)
        assert not missing


class TestHasH1Title:
    """Exact behaviour of the ``_has_h1_title`` line scanner."""

    def test_h1_on_its_own_line_detected(self) -> None:
        """An H1 line preceded by other lines is found via newline split."""
        generator = ClaudeMdGenerator()

        assert generator._has_h1_title("intro\n# Real Title\nbody") is True

    def test_h2_only_is_not_h1(self) -> None:
        """A document with only an H2 (``## ``) has no H1 title."""
        generator = ClaudeMdGenerator()

        assert generator._has_h1_title("## Section\n\nbody") is False

    def test_single_line_h1_detected(self) -> None:
        """A one-line ``# Title`` (no newline) is still an H1."""
        generator = ClaudeMdGenerator()

        assert generator._has_h1_title("# Title") is True


class TestValidateMarkdownMessages:
    """Exact error-message and boundary assertions for markdown validation."""

    def test_empty_string_exact_message(self) -> None:
        """Empty content yields the exact 'empty' message."""
        generator = ClaudeMdGenerator()

        with pytest.raises(ValueError, match="empty") as exc:
            generator._validate_markdown_structure("")

        assert str(exc.value) == "Generated CLAUDE.md is empty"

    def test_whitespace_only_is_empty(self) -> None:
        """Whitespace-only content is rejected via ``or`` (not ``and``)."""
        generator = ClaudeMdGenerator()

        with pytest.raises(ValueError, match="empty") as exc:
            generator._validate_markdown_structure("   \n\t  ")

        assert str(exc.value) == "Generated CLAUDE.md is empty"

    def test_missing_h1_exact_message(self) -> None:
        """Non-empty content lacking an H1 yields the exact 'missing' message."""
        generator = ClaudeMdGenerator()

        with pytest.raises(ValueError, match="missing H1 title") as exc:
            generator._validate_markdown_structure("## only an h2\n")

        assert str(exc.value) == "Generated CLAUDE.md is missing H1 title"


class TestBaselineSubstitutions:
    """Exact token-map assertions for ``_baseline_substitutions``."""

    def test_defaults_for_missing_keys(self) -> None:
        """Absent keys fall back to the documented defaults, exactly."""
        subs = ClaudeMdGenerator._baseline_substitutions({})

        assert subs["{{PROJECT_NAME}}"] == "your-project"
        assert subs["{{LANGUAGE}}"] == "python"
        assert subs["{{SCRIPTS}}"] == ""
        assert subs["{{SKILLS}}"] == ""

    def test_token_keys_are_double_braced(self) -> None:
        """The map is keyed by the literal ``{{TOKEN}}`` markers."""
        subs = ClaudeMdGenerator._baseline_substitutions({})

        assert set(subs) == {
            "{{PROJECT_NAME}}",
            "{{LANGUAGE}}",
            "{{SCRIPTS}}",
            "{{SKILLS}}",
        }

    def test_callable_on_instance_as_staticmethod(self) -> None:
        """Calling via an instance binds no ``self`` (it is a staticmethod)."""
        generator = ClaudeMdGenerator()

        subs = generator._baseline_substitutions({"project_name": "via-inst"})

        assert subs["{{PROJECT_NAME}}"] == "via-inst"

    def test_provided_values_flow_through(self) -> None:
        """Provided config values reach the map under their real keys."""
        subs = ClaudeMdGenerator._baseline_substitutions(
            {"project_name": "my-app", "language": "rust"},
        )

        assert subs["{{PROJECT_NAME}}"] == "my-app"
        assert subs["{{LANGUAGE}}"] == "rust"

    def test_scripts_joined_with_newline_and_dash(self) -> None:
        """Scripts render as ``- name`` lines joined by newline, exactly."""
        subs = ClaudeMdGenerator._baseline_substitutions(
            {"scripts": ["a.sh", "b.sh"]},
        )

        assert subs["{{SCRIPTS}}"] == "- a.sh\n- b.sh"

    def test_skills_joined_with_newline_and_dash(self) -> None:
        """Skills render as ``- name`` lines joined by newline, exactly."""
        subs = ClaudeMdGenerator._baseline_substitutions(
            {"skills": ["x", "y"]},
        )

        assert subs["{{SKILLS}}"] == "- x\n- y"

    def test_scripts_present_kept_via_or_default(self) -> None:
        """A non-empty scripts list survives the ``or []`` guard intact."""
        subs = ClaudeMdGenerator._baseline_substitutions(
            {"scripts": ["only.sh"]},
        )

        assert subs["{{SCRIPTS}}"] == "- only.sh"

    def test_skills_present_kept_via_or_default(self) -> None:
        """A non-empty skills list survives the ``or []`` guard intact."""
        subs = ClaudeMdGenerator._baseline_substitutions(
            {"skills": ["only"]},
        )

        assert subs["{{SKILLS}}"] == "- only"


class TestRenderBaselineSubstitution:
    """End-to-end token substitution via ``_render_baseline``."""

    def test_all_tokens_substituted_exactly(self) -> None:
        """Each ``{{TOKEN}}`` is replaced and no marker leaks through."""
        template = "P={{PROJECT_NAME}} L={{LANGUAGE}} S={{SCRIPTS}} K={{SKILLS}}"
        config: dict[str, Any] = {
            "project_name": "demo",
            "language": "go",
            "scripts": ["a.sh"],
            "skills": ["t"],
        }

        rendered = ClaudeMdGenerator._render_baseline(template, config)

        assert rendered == "P=demo L=go S=- a.sh K=- t"
        assert "{{PROJECT_NAME}}" not in rendered
        assert "{{SCRIPTS}}" not in rendered
        assert "{{SKILLS}}" not in rendered
        assert "{{LANGUAGE}}" not in rendered

    def test_unknown_token_left_intact(self) -> None:
        """Tokens with no mapping are preserved verbatim for inspection."""
        rendered = ClaudeMdGenerator._render_baseline(
            "keep {{UNKNOWN}} here",
            {"project_name": "p"},
        )

        assert rendered == "keep {{UNKNOWN}} here"


class TestBuildGenerationPromptContext:
    """The prompt context dict feeds the right values into the template."""

    @staticmethod
    def _prompt(config: dict[str, Any]) -> str:
        """Render the tune prompt with marker references for assertions."""
        return ClaudeMdGenerator._build_generation_prompt(
            "REF_MARKER",
            "QUALITY_MARKER",
            config,
        )

    def test_default_project_name_and_language(self) -> None:
        """Missing name/language default to ``unknown`` in the rendered prompt."""
        prompt = self._prompt({})

        assert "Name: unknown" in prompt
        assert "Primary language: unknown" in prompt

    def test_provided_name_and_language(self) -> None:
        """Provided name/language render under their real keys."""
        prompt = self._prompt({"project_name": "acme", "language": "swift"})

        assert "Name: acme" in prompt
        assert "Primary language: swift" in prompt

    def test_scripts_rendered_in_prompt(self) -> None:
        """The ``scripts`` key flows through to the rendered script list."""
        prompt = self._prompt({"scripts": ["unique-script.sh"]})

        assert "unique-script.sh" in prompt

    def test_skills_rendered_in_prompt(self) -> None:
        """The ``skills`` key flows through to the rendered skills list."""
        prompt = self._prompt({"skills": ["unique-skill"]})

        assert "unique-skill" in prompt

    def test_references_embedded_in_prompt(self) -> None:
        """Both reference bodies are embedded under their real keys."""
        prompt = self._prompt({})

        assert "REF_MARKER" in prompt
        assert "QUALITY_MARKER" in prompt


class TestGenerateReferenceFlow:
    """``generate`` must pass the real loaded reference into the prompt."""

    def test_loaded_reference_reaches_prompt(self, tmp_path: Path) -> None:
        """The CLAUDE.md reference content (not None) is sent to the prompt."""
        orchestrator = create_autospec(AIOrchestrator)
        orchestrator.generate.return_value = GenerationResult(
            content="# Tuned\n",
            format="markdown",
            token_usage=TokenUsage(input_tokens=1, output_tokens=1),
            model="claude-opus-4-5-20251101",
            message_id="msg",
        )
        ref = tmp_path / "claude"
        ref.mkdir()
        (ref / "CLAUDE.md").write_text("REFERENCE_SENTINEL", encoding="utf-8")
        quality = tmp_path / "q.md"
        quality.write_text("# Quality", encoding="utf-8")
        generator = ClaudeMdGenerator(
            orchestrator,
            reference_dir=ref,
            quality_ref_path=quality,
        )

        generator.generate({"project_name": "p", "language": "python"})

        prompt = orchestrator.generate.call_args[0][0]
        assert "REFERENCE_SENTINEL" in prompt


class TestWriteModularDirectoryCreation:
    """``write_modular`` mkdir flags create the full nested tree."""

    @staticmethod
    def _config() -> dict[str, Any]:
        """Return a minimal config for modular emission."""
        return {
            "project_name": "p",
            "language": "python",
            "scripts": [],
            "skills": [],
        }

    def test_creates_nested_project_root(self, tmp_path: Path) -> None:
        """A deeply nested, absent project root is created (parents=True)."""
        generator = ClaudeMdGenerator()
        nested = tmp_path / "a" / "b" / "c"

        generator.write_modular(nested, self._config())

        assert (nested / "CLAUDE.md").is_file()
        assert (nested / ".claude" / "docs" / "principles.md").is_file()

    def test_succeeds_when_docs_dir_preexists(self, tmp_path: Path) -> None:
        """A pre-existing docs dir does not error (exist_ok=True)."""
        generator = ClaudeMdGenerator()
        preexisting = tmp_path / ".claude" / "docs"
        preexisting.mkdir(parents=True)

        result = generator.write_modular(tmp_path, self._config())

        assert (preexisting / "principles.md").is_file()
        assert result.token_usage_input == 0
