"""Tests for skills content quality (Issue #23: Verify Skills).

This test file verifies that all skills follow the directory-per-skill
format with YAML frontmatter and consistent section structure.
"""

from pathlib import Path

import pytest

from start_green_stay_green.generators.skills import REQUIRED_SKILLS


@pytest.fixture
def skills_dir() -> Path:
    """Return path to skills directory."""
    return Path(__file__).parent.parent.parent.parent / "reference" / "skills"


class TestSkillsStructure:
    """Test that all skills have required sections and structure."""

    @pytest.fixture
    def required_skills(self) -> list[str]:
        """Return list of required skills."""
        return REQUIRED_SKILLS

    def test_all_required_skills_exist(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test that all required skill directories exist with SKILL.md."""
        for skill in required_skills:
            skill_dir = skills_dir / skill
            assert skill_dir.is_dir(), f"Missing skill directory: {skill}"
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Missing SKILL.md in: {skill}"
            assert skill_file.stat().st_size > 0, f"Empty SKILL.md in: {skill}"

    def test_vibe_skill_structure(self, skills_dir: Path) -> None:
        """Test vibe skill has required sections."""
        vibe_path = skills_dir / "vibe" / "SKILL.md"
        content = vibe_path.read_text()

        required_sections = [
            "# Vibe",
            "## Instructions",
            "## Examples",
            "## Troubleshooting",
        ]

        for section in required_sections:
            assert section in content, f"vibe SKILL.md missing section: {section}"

    def test_concurrency_skill_structure(self, skills_dir: Path) -> None:
        """Test concurrency skill has required sections."""
        concurrency_path = skills_dir / "concurrency" / "SKILL.md"
        content = concurrency_path.read_text()

        required_sections = [
            "# Concurrency",
            "## Instructions",
            "## Examples",
            "## Troubleshooting",
        ]

        for section in required_sections:
            assert (
                section in content
            ), f"concurrency SKILL.md missing section: {section}"

    def test_all_skills_have_title(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have H1 title."""
        for skill in required_skills:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()
            lines = content.split("\n")

            # Should have H1 title (starting with # but not ##)
            has_h1 = False
            for line in lines:
                if line.startswith("# ") and not line.startswith("## "):
                    has_h1 = True
                    break

            assert has_h1, f"{skill} missing H1 title"

    def test_all_skills_have_instructions(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have Instructions section."""
        for skill in required_skills:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()

            assert "## Instructions" in content, f"{skill} missing Instructions section"

    def test_all_skills_have_troubleshooting(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have Troubleshooting section."""
        for skill in required_skills:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()

            assert (
                "## Troubleshooting" in content
            ), f"{skill} missing Troubleshooting section"

    def test_all_skills_have_yaml_frontmatter(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have YAML frontmatter with name and description."""
        for skill in required_skills:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()

            # Check YAML frontmatter delimiters
            assert content.startswith("---"), f"{skill} missing YAML frontmatter start"
            # Find the closing ---
            second_delimiter = content.find("---", 3)
            assert second_delimiter > 3, f"{skill} missing YAML frontmatter end"

            frontmatter = content[3:second_delimiter]
            assert "name:" in frontmatter, f"{skill} missing 'name:' in frontmatter"
            assert (
                "description:" in frontmatter
            ), f"{skill} missing 'description:' in frontmatter"


class TestSkillsQuality:
    """Test skills meet quality requirements."""

    def test_skills_are_not_too_short(self, skills_dir: Path) -> None:
        """Test skills have substantial content (>1000 chars)."""
        for skill in REQUIRED_SKILLS:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()

            assert (
                len(content) > 1000
            ), f"{skill} too short ({len(content)} chars, need >1000)"

    def test_skills_have_code_examples(self, skills_dir: Path) -> None:
        """Test skills contain code examples (code blocks)."""
        for skill in REQUIRED_SKILLS:
            skill_path = skills_dir / skill / "SKILL.md"
            content = skill_path.read_text()

            # Check for code blocks (```language or ```)
            has_code_blocks = "```" in content

            assert has_code_blocks, f"{skill} missing code examples"
