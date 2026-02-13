"""Tests for reference assets (Issue #22: Copy SGSG Assets).

This test file verifies that all required reference assets exist
and are properly structured for use by generators.
"""

from pathlib import Path

import pytest


# Fixture for reference directory
@pytest.fixture
def reference_dir() -> Path:
    """Return path to reference directory."""
    return Path(__file__).parent.parent.parent.parent / "reference"


class TestCIReferences:
    """Test CI workflow references exist for all supported languages."""

    @pytest.fixture
    def ci_dir(self, reference_dir: Path) -> Path:
        """Return path to CI directory."""
        return reference_dir / "ci"

    def test_ci_directory_exists(self, ci_dir: Path) -> None:
        """Test that ci/ directory exists."""
        assert ci_dir.exists()
        assert ci_dir.is_dir()

    def test_all_language_ci_workflows_exist(self, ci_dir: Path) -> None:
        """Test that CI workflows exist for all 10 supported languages."""
        required_workflows = [
            "python.yml",
            "typescript.yml",
            "go.yml",
            "rust.yml",
            "java.yml",
            "csharp.yml",
            "swift.yml",
            "ruby.yml",
            "php.yml",
            "kotlin.yml",
        ]

        for workflow in required_workflows:
            workflow_path = ci_dir / workflow
            assert workflow_path.exists(), f"Missing CI workflow: {workflow}"
            assert workflow_path.is_file()
            assert workflow_path.stat().st_size > 0, f"Empty CI workflow: {workflow}"


class TestScriptsReferences:
    """Test scripts references exist for all supported languages."""

    @pytest.fixture
    def scripts_dir(self, reference_dir: Path) -> Path:
        """Return path to scripts directory."""
        return reference_dir / "scripts"

    def test_scripts_directory_exists(self, scripts_dir: Path) -> None:
        """Test that scripts/ directory exists."""
        assert scripts_dir.exists()
        assert scripts_dir.is_dir()

    def test_all_language_script_directories_exist(self, scripts_dir: Path) -> None:
        """Test that script directories exist for all 10 supported languages."""
        required_languages = [
            "python",
            "typescript",
            "go",
            "rust",
            "java",
            "csharp",
            "swift",
            "ruby",
            "php",
            "kotlin",
        ]

        for language in required_languages:
            language_dir = scripts_dir / language
            assert language_dir.exists(), f"Missing scripts directory: {language}/"
            assert language_dir.is_dir()

    def test_python_scripts_exist(self, scripts_dir: Path) -> None:
        """Test that required Python scripts exist."""
        python_dir = scripts_dir / "python"
        required_scripts = ["test.sh", "lint.sh"]

        for script in required_scripts:
            script_path = python_dir / script
            assert script_path.exists(), f"Missing Python script: {script}"
            assert script_path.is_file()
            assert script_path.stat().st_size > 0, f"Empty Python script: {script}"


class TestSkillsReferences:
    """Test skills references exist and have proper structure."""

    @pytest.fixture
    def skills_dir(self, reference_dir: Path) -> Path:
        """Return path to skills directory."""
        return reference_dir / "skills"

    def test_skills_directory_exists(self, skills_dir: Path) -> None:
        """Test that skills/ directory exists."""
        assert skills_dir.exists()
        assert skills_dir.is_dir()

    def test_all_required_skills_exist(self, skills_dir: Path) -> None:
        """Test that all required skill directories exist with SKILL.md."""
        required_skills = [
            "vibe",
            "concurrency",
            "error-handling",
            "testing",
            "documentation",
            "security",
        ]

        for skill in required_skills:
            skill_dir = skills_dir / skill
            assert skill_dir.is_dir(), f"Missing skill directory: {skill}"
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Missing SKILL.md in: {skill}"
            assert skill_file.stat().st_size > 0, f"Empty SKILL.md in: {skill}"


class TestSubagentsReferences:
    """Test subagent references exist and have proper structure."""

    @pytest.fixture
    def subagents_dir(self, reference_dir: Path) -> Path:
        """Return path to subagents directory."""
        return reference_dir / "subagents"

    def test_subagents_directory_exists(self, subagents_dir: Path) -> None:
        """Test that subagents/ directory exists."""
        assert subagents_dir.exists()
        assert subagents_dir.is_dir()

    def test_subagent_templates_exist(self, subagents_dir: Path) -> None:
        """Test that subagent templates exist."""
        templates_dir = subagents_dir / "templates"
        assert templates_dir.exists()
        assert templates_dir.is_dir()

        required_templates = [
            "level-0-chief-architect.md",
            "level-1-section-orchestrator.md",
            "level-2-module-design.md",
            "level-3-component-specialist.md",
            "level-4-implementation-engineer.md",
            "level-5-junior-engineer.md",
        ]

        for template in required_templates:
            template_path = templates_dir / template
            assert template_path.exists(), f"Missing template: {template}"
            assert template_path.is_file()


class TestPrecommitReferences:
    """Test pre-commit configuration references exist."""

    @pytest.fixture
    def precommit_dir(self, reference_dir: Path) -> Path:
        """Return path to precommit directory."""
        return reference_dir / "precommit"

    def test_precommit_directory_exists(self, precommit_dir: Path) -> None:
        """Test that precommit/ directory exists."""
        assert precommit_dir.exists()
        assert precommit_dir.is_dir()


class TestReferenceStructure:
    """Test overall reference directory structure."""

    def test_maximum_quality_engineering_exists(self, reference_dir: Path) -> None:
        """Test that MAXIMUM_QUALITY_ENGINEERING.md exists."""
        mqe_path = reference_dir / "MAXIMUM_QUALITY_ENGINEERING.md"
        assert mqe_path.exists()
        assert mqe_path.is_file()
        assert mqe_path.stat().st_size > 0

    def test_reference_directory_structure(self, reference_dir: Path) -> None:
        """Test that reference directory has all required subdirectories."""
        required_dirs = ["ci", "scripts", "skills", "subagents", "precommit"]

        for dir_name in required_dirs:
            dir_path = reference_dir / dir_name
            assert dir_path.exists(), f"Missing directory: {dir_name}/"
            assert dir_path.is_dir()
