"""Tests for dependency checker subagent (Issue #24).

This test file verifies that the dependency checker subagent
meets all requirements from SPEC.md Issue 3.5 and 5.3.
"""

from pathlib import Path

import pytest


@pytest.fixture
def subagents_dir() -> Path:
    """Return path to subagents directory."""
    return Path(__file__).parent.parent.parent.parent / "reference" / "subagents"


@pytest.fixture
def dependency_checker_path(subagents_dir: Path) -> Path:
    """Return path to dependency-checker.md."""
    return subagents_dir / "dependency-checker.md"


class TestDependencyCheckerExists:
    """Test that dependency checker file exists."""

    def test_dependency_checker_exists(self, dependency_checker_path: Path) -> None:
        """Test that dependency-checker.md exists."""
        assert dependency_checker_path.exists(), "dependency-checker.md not found"
        assert dependency_checker_path.is_file()
        assert (
            dependency_checker_path.stat().st_size > 0
        ), "dependency-checker.md is empty"


class TestDependencyCheckerStructure:
    """Test that dependency checker has required sections."""

    @pytest.fixture
    def content(self, dependency_checker_path: Path) -> str:
        """Return content of dependency-checker.md."""
        return dependency_checker_path.read_text()

    def test_has_title(self, content: str) -> None:
        """Test that file has H1 title."""
        assert "# Dependency Checker" in content or "# Dependency-Checker" in content

    def test_has_role_section(self, content: str) -> None:
        """Test that file has Role section."""
        assert "## Role" in content

    def test_has_checks_section(self, content: str) -> None:
        """Test that file has Checks section."""
        assert "## Checks" in content or "## Mandatory Checks" in content

    def test_has_response_format_section(self, content: str) -> None:
        """Test that file has Response Format section."""
        assert "## Response Format" in content

    def test_has_examples_section(self, content: str) -> None:
        """Test that file has Examples section."""
        assert "## Examples" in content or "## Example" in content

    def test_has_ci_integration_section(self, content: str) -> None:
        """Test that file has CI integration section."""
        assert (
            "## CI Integration" in content
            or "## Integration" in content
            or "## CI" in content
        )


class TestDependencyCheckerContent:
    """Test that dependency checker has required content."""

    @pytest.fixture
    def content(self, dependency_checker_path: Path) -> str:
        """Return content of dependency-checker.md."""
        return dependency_checker_path.read_text()

    def test_has_all_8_mandatory_checks(self, content: str) -> None:
        """Test that all 8 mandatory checks from SPEC.md are documented."""
        required_checks = [
            "trusted",  # Package source is trusted
            "recent commit",  # Package has recent commits
            "download",  # Package has reasonable download count
            "vulnerabilit",  # No known vulnerabilities (CVE)
            "license",  # License is compatible
            "size",  # Package size is reasonable
            "install script",  # No suspicious install scripts
            "transitive",  # Transitive dependencies reviewed
        ]

        content_lower = content.lower()
        for check in required_checks:
            assert (
                check in content_lower
            ), f"Missing required check: {check} (from SPEC.md Issue 3.5)"

    def test_has_response_format_types(self, content: str) -> None:
        """Test that all 3 response types are documented."""
        required_responses = ["APPROVED", "REJECTED", "REVIEW_NEEDED"]

        for response_type in required_responses:
            assert (
                response_type in content
            ), f"Missing response type: {response_type}"

    def test_has_supply_chain_mention(self, content: str) -> None:
        """Test that supply chain security is mentioned."""
        content_lower = content.lower()
        assert (
            "supply chain" in content_lower
        ), "Missing supply chain security mention"

    def test_has_code_examples(self, content: str) -> None:
        """Test that file contains code examples."""
        assert "```" in content, "Missing code examples"

    def test_is_substantial(self, content: str) -> None:
        """Test that file has substantial content (>2000 chars)."""
        assert (
            len(content) > 2000
        ), f"Content too short ({len(content)} chars, need >2000)"
