"""Unit tests for SkillsGenerator."""

from pathlib import Path
from unittest.mock import create_autospec

import pytest
from pytest_mock import MockerFixture

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.ai.tuner import TuningResult
from start_green_stay_green.generators.skills import REQUIRED_SKILLS
from start_green_stay_green.generators.skills import SkillGenerationResult
from start_green_stay_green.generators.skills import SkillsGenerator


class TestSkillGenerationResult:
    """Test SkillGenerationResult dataclass."""

    def test_skill_generation_result_creation(self) -> None:
        """Test creating SkillGenerationResult with all fields."""
        result = SkillGenerationResult(
            skill_name="vibe.md",
            content="# Vibe Skill\n\nContent here",
            tuned=True,
            changes=["Change 1", "Change 2"],
        )

        assert result.skill_name == "vibe.md"
        assert result.content == "# Vibe Skill\n\nContent here"
        assert result.tuned
        assert len(result.changes) == 2

    def test_skill_generation_result_untuned(self) -> None:
        """Test SkillGenerationResult for untuned (copied) content."""
        result = SkillGenerationResult(
            skill_name="testing.md",
            content="Original content",
            tuned=False,
            changes=["[DRY RUN] No changes made"],
        )

        assert not result.tuned
        assert result.content == "Original content"

    def test_skill_generation_result_is_immutable(self) -> None:
        """Test SkillGenerationResult is immutable."""
        result = SkillGenerationResult(
            skill_name="test.md",
            content="content",
            tuned=True,
            changes=[],
        )

        with pytest.raises(AttributeError):
            result.skill_name = "changed.md"  # type: ignore[misc]


class TestSkillsGeneratorInit:
    """Test SkillsGenerator initialization."""

    def test_skills_generator_init_with_defaults(self) -> None:
        """Test SkillsGenerator initialization with default parameters."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = SkillsGenerator(orchestrator)

        assert generator.orchestrator is orchestrator
        assert not generator.dry_run
        assert generator.reference_dir.name == "skills"

    def test_skills_generator_init_with_custom_reference_dir(
        self,
        tmp_path: Path,
    ) -> None:
        """Test SkillsGenerator with custom reference directory."""
        orchestrator = create_autospec(AIOrchestrator)
        custom_dir = tmp_path / "custom_skills"
        custom_dir.mkdir()

        generator = SkillsGenerator(orchestrator, reference_dir=custom_dir)

        assert generator.reference_dir == custom_dir

    def test_skills_generator_init_with_dry_run(self) -> None:
        """Test SkillsGenerator in dry-run mode."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = SkillsGenerator(orchestrator, dry_run=True)

        assert generator.dry_run
        assert generator.tuner is not None
        assert generator.tuner.dry_run


class TestSkillsGeneratorValidation:
    """Test SkillsGenerator validation methods."""

    def test_validate_reference_dir_missing_directory(self, tmp_path: Path) -> None:
        """Test validation raises error for missing directory."""
        orchestrator = create_autospec(AIOrchestrator)
        nonexistent_dir = tmp_path / "nonexistent"
        generator = SkillsGenerator(orchestrator, reference_dir=nonexistent_dir)

        with pytest.raises(
            FileNotFoundError,
            match="Reference skills directory not found",
        ):
            generator._validate_reference_dir()

    def test_validate_reference_dir_not_a_directory(self, tmp_path: Path) -> None:
        """Test validation raises error when path is a file."""
        orchestrator = create_autospec(AIOrchestrator)
        file_path = tmp_path / "skills.txt"
        file_path.write_text("not a directory")
        generator = SkillsGenerator(orchestrator, reference_dir=file_path)

        with pytest.raises(ValueError, match="not a directory"):
            generator._validate_reference_dir()

    def test_validate_reference_dir_missing_required_skills(
        self,
        tmp_path: Path,
    ) -> None:
        """Test validation raises error when required skills are missing."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create only one skill (vibe.md) - missing the others
        (skills_dir / "vibe.md").write_text("# Vibe")

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        with pytest.raises(ValueError, match="Missing required skills"):
            generator._validate_reference_dir()

    def test_validate_reference_dir_success(self, tmp_path: Path) -> None:
        """Test validation passes when all required skills present."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create all required skills
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text(f"# {skill}")

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        # Should not raise
        generator._validate_reference_dir()


class TestSkillsGeneratorLoadSkill:
    """Test SkillsGenerator _load_skill method."""

    def test_load_skill_success(self, tmp_path: Path) -> None:
        """Test loading skill file successfully."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        skill_content = "# Vibe Skill\n\nContent here"
        (skills_dir / "vibe.md").write_text(skill_content)

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)
        loaded_content = generator._load_skill("vibe.md")

        assert loaded_content == skill_content

    def test_load_skill_file_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent skill raises error."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        with pytest.raises(FileNotFoundError, match="Skill file not found"):
            generator._load_skill("nonexistent.md")


class TestSkillsGeneratorTuneSkill:
    """Test SkillsGenerator tune_skill method."""

    @pytest.mark.asyncio
    async def test_tune_skill_success(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ) -> None:
        """Test tuning skill successfully."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        # Mock the tuner.tune method
        mock_tuning_result = TuningResult(
            content="# Tuned Vibe Skill\n\nAdapted content",
            changes=["Changed reference to Django", "Updated examples"],
            dry_run=False,
            token_usage_input=100,
            token_usage_output=50,
        )
        mocker.patch.object(generator.tuner, "tune", return_value=mock_tuning_result)

        result = await generator.tune_skill(
            skill_name="vibe.md",
            skill_content="# Original Vibe Skill",
            target_context="Django web application",
        )

        assert result.skill_name == "vibe.md"
        assert result.content == "# Tuned Vibe Skill\n\nAdapted content"
        assert result.tuned
        assert len(result.changes) == 2
        assert "Changed reference to Django" in result.changes

    @pytest.mark.asyncio
    async def test_tune_skill_dry_run(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ) -> None:
        """Test tuning skill in dry-run mode."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        generator = SkillsGenerator(
            orchestrator,
            reference_dir=skills_dir,
            dry_run=True,
        )

        # Mock the tuner.tune method for dry run
        mock_tuning_result = TuningResult(
            content="# Original Vibe Skill",
            changes=["[DRY RUN] No changes made"],
            dry_run=True,
            token_usage_input=0,
            token_usage_output=0,
        )
        mocker.patch.object(generator.tuner, "tune", return_value=mock_tuning_result)

        result = await generator.tune_skill(
            skill_name="vibe.md",
            skill_content="# Original Vibe Skill",
            target_context="Django web application",
        )

        assert result.skill_name == "vibe.md"
        assert result.content == "# Original Vibe Skill"
        assert not result.tuned
        assert result.changes == ["[DRY RUN] No changes made"]


class TestSkillsGeneratorGenerateAllSkills:
    """Test SkillsGenerator generate_all_skills method."""

    @pytest.mark.asyncio
    async def test_generate_all_skills_success(
        self,
        tmp_path: Path,
        mocker: MockerFixture,
    ) -> None:
        """Test generating all skills successfully."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create all required skills
        for skill in REQUIRED_SKILLS:
            skill_title = skill.replace(".md", "").title()
            (skills_dir / skill).write_text(f"# {skill_title} Skill")

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        # Mock the tuner.tune method
        def mock_tune(
            source_content: str,
            source_context: str,  # noqa: ARG001
            target_context: str,  # noqa: ARG001
        ) -> TuningResult:
            return TuningResult(
                content=source_content + "\n\nTuned content",
                changes=["Adapted to target"],
                dry_run=False,
                token_usage_input=50,
                token_usage_output=25,
            )

        mocker.patch.object(generator.tuner, "tune", side_effect=mock_tune)

        results = await generator.generate_all_skills(
            target_context="FastAPI microservice",
        )

        # Verify all skills generated
        assert len(results) == len(REQUIRED_SKILLS)
        for skill_name in REQUIRED_SKILLS:
            assert skill_name in results
            assert results[skill_name].skill_name == skill_name
            assert results[skill_name].tuned
            assert "Tuned content" in results[skill_name].content

    @pytest.mark.asyncio
    async def test_generate_all_skills_validation_fails(self, tmp_path: Path) -> None:
        """Test generate_all_skills fails when validation fails."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Don't create any skills - validation should fail
        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        with pytest.raises(ValueError, match="Missing required skills"):
            await generator.generate_all_skills(target_context="Test project")


class TestSkillsGeneratorGenerate:
    """Test SkillsGenerator generate method."""

    def test_generate_raises_not_implemented(self) -> None:
        """Test generate() raises NotImplementedError."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = SkillsGenerator(orchestrator)

        with pytest.raises(NotImplementedError, match="Use generate_all_skills"):
            generator.generate()


class TestSkillsGeneratorIntegration:
    """Integration tests for SkillsGenerator."""

    @pytest.mark.asyncio
    async def test_full_workflow_dry_run(self, tmp_path: Path) -> None:
        """Test full workflow in dry-run mode (no AI calls)."""
        orchestrator = create_autospec(AIOrchestrator)
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create all required skills with realistic content
        for skill in REQUIRED_SKILLS:
            content = f"""# {skill.replace('.md', '').replace('-', ' ').title()} Skill

## Purpose
Guide developers in {skill.replace('.md', '').replace('-', ' ')}.

## Principles
1. Principle one
2. Principle two

## Examples
Example code here
"""
            (skills_dir / skill).write_text(content)

        generator = SkillsGenerator(
            orchestrator,
            reference_dir=skills_dir,
            dry_run=True,
        )

        results = await generator.generate_all_skills(
            target_context="Django e-commerce platform",
        )

        # Verify results
        assert len(results) == len(REQUIRED_SKILLS)

        for skill_name, result in results.items():
            assert result.skill_name == skill_name
            assert not result.tuned  # Dry run = not tuned
            assert "# " in result.content  # Has title
            assert "## Purpose" in result.content
            assert "[DRY RUN]" in result.changes[0]


class TestSkillsGeneratorLoggerBehavior:
    """Test logger behavior in SkillsGenerator to kill mutants."""

    def test_init_without_orchestrator_logs_direct_copy_mode(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info called when initialized without AI."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        generator = SkillsGenerator(
            orchestrator=None,  # No AI
            reference_dir=skills_dir,
        )

        assert generator.tuner is None
        mock_logger.info.assert_called_once_with(
            "Skills generator initialized without AI (direct copy mode)"
        )

    def test_init_with_orchestrator_does_not_log_direct_copy(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info NOT called when initialized with AI."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        orchestrator = mocker.Mock()
        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        generator = SkillsGenerator(
            orchestrator=orchestrator,  # Has AI
            reference_dir=skills_dir,
        )

        assert generator.tuner is not None
        # Should NOT log direct copy mode message
        for call in mock_logger.info.call_args_list:
            assert "direct copy mode" not in str(call)

    def test_load_skill_logs_skill_name(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info called with skill name when loading."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "vibe.md").write_text("# Vibe Skill")

        orchestrator = mocker.Mock()
        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)
        content = generator._load_skill("vibe.md")

        assert content == "# Vibe Skill"
        mock_logger.info.assert_any_call("Loading skill: %s", "vibe.md")

    @pytest.mark.asyncio
    async def test_tune_skill_without_tuner_logs_copy_message(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info called when copying without AI tuning."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        generator = SkillsGenerator(
            orchestrator=None,  # No AI
            reference_dir=skills_dir,
        )

        result = await generator.tune_skill(
            skill_name="vibe.md",
            skill_content="# Original",
            target_context="Target",
        )

        assert not result.tuned
        mock_logger.info.assert_any_call("Copying skill %s (no AI tuning)", "vibe.md")

    @pytest.mark.asyncio
    async def test_tune_skill_with_tuner_logs_tuning_message(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info called when tuning with AI."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        orchestrator = mocker.Mock()
        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        # Mock the tuner's tune method
        mock_tune_result = mocker.Mock()
        mock_tune_result.content = "# Tuned"
        mock_tune_result.changes = ["Change 1"]

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)
        generator.tuner = mocker.Mock()
        generator.tuner.tune = mocker.AsyncMock(return_value=mock_tune_result)  # type: ignore[method-assign]

        await generator.tune_skill(
            skill_name="vibe.md",
            skill_content="# Original",
            target_context="Target Context",
        )

        mock_logger.info.assert_any_call(
            "Tuning skill %s for target context", "vibe.md"
        )

    @pytest.mark.asyncio
    async def test_generate_all_skills_logs_completion(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test logger.info called with skill name and change count."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        # Create all required skills
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text(f"# {skill}")

        orchestrator = mocker.Mock()
        mock_logger = mocker.patch("start_green_stay_green.generators.skills.logger")

        # Mock tuner to return results with changes
        mock_tune_result = mocker.Mock()
        mock_tune_result.content = "# Tuned"
        mock_tune_result.changes = ["Change 1", "Change 2", "Change 3"]

        generator = SkillsGenerator(orchestrator, reference_dir=skills_dir)
        generator.tuner = mocker.Mock()
        generator.tuner.tune = mocker.AsyncMock(return_value=mock_tune_result)  # type: ignore[method-assign]

        await generator.generate_all_skills(target_context="Target")

        # Verify logger called for each skill with change count
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        vibe_log = [
            call for call in log_calls if "vibe.md" in call and "changes" in call
        ]
        assert vibe_log

    @pytest.mark.asyncio
    async def test_tune_skill_without_orchestrator_returns_exact_content(
        self, tmp_path: Path
    ) -> None:
        """Test that no-AI mode returns exact original content."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        generator = SkillsGenerator(
            orchestrator=None,  # No AI
            reference_dir=skills_dir,
        )

        original = "# Original\n\nWith special chars: !@#$%"
        result = await generator.tune_skill(
            skill_name="vibe.md",
            skill_content=original,
            target_context="Target",
        )

        # Verify content is EXACTLY the same
        assert result.content == original
        assert not result.tuned
        assert not result.changes

    @pytest.mark.asyncio
    async def test_tune_skill_none_tuner_branch_vs_has_tuner(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        """Test different code paths for tuner is None vs tuner exists."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        for skill in REQUIRED_SKILLS:
            (skills_dir / skill).write_text("# Skill")

        # Case 1: No tuner (None)
        gen_no_ai = SkillsGenerator(orchestrator=None, reference_dir=skills_dir)
        result_no_ai = await gen_no_ai.tune_skill("vibe.md", "# Content", "Target")
        assert gen_no_ai.tuner is None
        assert not result_no_ai.tuned

        # Case 2: Has tuner
        orchestrator = mocker.Mock()
        gen_with_ai = SkillsGenerator(orchestrator, reference_dir=skills_dir)

        mock_tune_result = mocker.Mock()
        mock_tune_result.content = "# Tuned"
        mock_tune_result.changes = ["Change"]
        gen_with_ai.tuner = mocker.Mock()
        gen_with_ai.tuner.tune = mocker.AsyncMock(return_value=mock_tune_result)  # type: ignore[method-assign]

        result_with_ai = await gen_with_ai.tune_skill("vibe.md", "# Content", "Target")
        assert gen_with_ai.tuner is not None
        assert result_with_ai.content == "# Tuned"  # Tuned version
