"""Tests for skills content quality (Issue #23: Verify Skills).

This test file verifies that all skills follow consistent format
and meet quality requirements from SPEC.md.
"""

from pathlib import Path

import pytest


@pytest.fixture
def skills_dir() -> Path:
    """Return path to skills directory."""
    return Path(__file__).parent.parent.parent.parent / "reference" / "skills"


class TestSkillsStructure:
    """Test that all skills have required sections and structure."""

    @pytest.fixture
    def required_skills(self) -> list[str]:
        """Return list of required skills."""
        return [
            "vibe.md",
            "concurrency.md",
            "error-handling.md",
            "testing.md",
            "documentation.md",
            "security.md",
        ]

    def test_all_required_skills_exist(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test that all required skills exist."""
        for skill in required_skills:
            skill_path = skills_dir / skill
            assert skill_path.exists(), f"Missing skill: {skill}"
            assert skill_path.is_file()
            assert skill_path.stat().st_size > 0, f"Empty skill: {skill}"

    def test_vibe_skill_structure(self, skills_dir: Path) -> None:
        """Test vibe.md has required sections."""
        vibe_path = skills_dir / "vibe.md"
        content = vibe_path.read_text()

        # Required sections per SPEC.md
        required_sections = [
            "# Vibe",  # Title
            "## Purpose",  # Purpose section
            "## Principles",  # Principles section
            "## Anti-patterns",  # Anti-patterns section
            "## Examples",  # Examples section
        ]

        for section in required_sections:
            assert section in content, f"vibe.md missing section: {section}"

    def test_concurrency_skill_structure(self, skills_dir: Path) -> None:
        """Test concurrency.md has required sections."""
        concurrency_path = skills_dir / "concurrency.md"
        content = concurrency_path.read_text()

        # Required sections per SPEC.md
        required_sections = [
            "# Concurrency",  # Title
            "## Purpose",  # Purpose section
            "## Principles",  # Principles section
            "## Anti-patterns",  # Anti-patterns section
        ]

        for section in required_sections:
            assert section in content, f"concurrency.md missing section: {section}"

    def test_all_skills_have_title(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have H1 title."""
        for skill in required_skills:
            skill_path = skills_dir / skill
            content = skill_path.read_text()
            lines = content.split("\n")

            # Should have H1 title (starting with # but not ##)
            has_h1 = False
            for line in lines:
                if line.startswith("# ") and not line.startswith("## "):
                    has_h1 = True
                    break

            assert has_h1, f"{skill} missing H1 title"

    def test_all_skills_have_purpose(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have Purpose section."""
        for skill in required_skills:
            skill_path = skills_dir / skill
            content = skill_path.read_text()

            assert (
                "## Purpose" in content or "## Overview" in content
            ), f"{skill} missing Purpose/Overview section"

    def test_all_skills_have_antipatterns(
        self, skills_dir: Path, required_skills: list[str]
    ) -> None:
        """Test all skills have Anti-patterns section."""
        for skill in required_skills:
            skill_path = skills_dir / skill
            content = skill_path.read_text()

            # Should have anti-patterns section (various possible names)
            has_antipatterns = (
                "## Anti-patterns" in content
                or "## Common Mistakes" in content
                or "## Antipatterns" in content
                or "## What Not to Do" in content
            )

            assert has_antipatterns, f"{skill} missing Anti-patterns section"


class TestSkillsQuality:
    """Test skills meet quality requirements."""

    def test_skills_are_not_too_short(self, skills_dir: Path) -> None:
        """Test skills have substantial content (>1000 chars)."""
        required_skills = [
            "vibe.md",
            "concurrency.md",
            "error-handling.md",
            "testing.md",
            "documentation.md",
            "security.md",
        ]

        for skill in required_skills:
            skill_path = skills_dir / skill
            content = skill_path.read_text()

            assert (
                len(content) > 1000
            ), f"{skill} too short ({len(content)} chars, need >1000)"

    def test_skills_have_code_examples(self, skills_dir: Path) -> None:
        """Test skills contain code examples (code blocks)."""
        required_skills = [
            "vibe.md",
            "concurrency.md",
            "error-handling.md",
            "testing.md",
            "documentation.md",
            "security.md",
        ]

        for skill in required_skills:
            skill_path = skills_dir / skill
            content = skill_path.read_text()

            # Check for code blocks (```language or ```)
            has_code_blocks = "```" in content

            assert has_code_blocks, f"{skill} missing code examples"
