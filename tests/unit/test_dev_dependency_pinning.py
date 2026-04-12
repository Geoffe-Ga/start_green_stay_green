"""Tests for dev dependency version pinning (Issue #280).

Formatting tools like Black are not backwards/forwards compatible
between major versions. If requirements-dev.txt uses a version range
(e.g., >=26.3.1,<27.0.0), local venvs can drift from CI, causing
format-check failures that don't reproduce locally.

This test ensures formatting tools are pinned to exact versions.
"""

from pathlib import Path
import re

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture
def requirements_dev_content() -> str:
    """Return contents of requirements-dev.txt."""
    return (PROJECT_ROOT / "requirements-dev.txt").read_text()


def _parse_requirement_version(content: str, package: str) -> str:
    """Extract the version specifier for a package from requirements content.

    Args:
        content: Full text of a requirements file.
        package: Package name to search for (case-insensitive).

    Returns:
        The full version specifier string (e.g., '==26.3.1' or '>=26.3.1,<27.0.0').

    Raises:
        ValueError: If package is not found in requirements.
    """
    pattern = rf"^{re.escape(package)}([=<>!~][^\s#]+)"
    match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
    if not match:
        msg = f"Package '{package}' not found in requirements"
        raise ValueError(msg)
    return match.group(1)


class TestFormattingToolPinning:
    """Test that formatting tools are pinned to exact versions.

    Black formatting output differs between versions. Using a version
    range allows CI and local environments to diverge, causing spurious
    format-check failures (see Issue #280, PR #279).
    """

    def test_black_is_exactly_pinned(self, requirements_dev_content: str) -> None:
        """Test that Black uses an exact version pin (==)."""
        version_spec = _parse_requirement_version(requirements_dev_content, "black")
        assert version_spec.startswith("=="), (
            f"Black must use exact version pin (==) to prevent CI/local drift. "
            f"Found: black{version_spec}. "
            f"See Issue #280."
        )

    def test_black_pinned_to_26_3_1(self, requirements_dev_content: str) -> None:
        """Test that Black is pinned to 26.3.1 (current CI version)."""
        version_spec = _parse_requirement_version(requirements_dev_content, "black")
        assert version_spec == "==26.3.1", (
            f"Black must be pinned to ==26.3.1 to match CI. "
            f"Found: black{version_spec}. "
            f"See Issue #280."
        )


class TestParseRequirementVersion:
    """Tests for the _parse_requirement_version helper."""

    def test_parses_exact_pin(self) -> None:
        """Test parsing exact version pin."""
        content = "black==26.3.1\n"
        assert _parse_requirement_version(content, "black") == "==26.3.1"

    def test_parses_range_pin(self) -> None:
        """Test parsing range version specifier."""
        content = "black>=26.3.1,<27.0.0\n"
        assert _parse_requirement_version(content, "black") == ">=26.3.1,<27.0.0"

    def test_parses_minimum_pin(self) -> None:
        """Test parsing minimum version specifier."""
        content = "black>=26.3.1\n"
        assert _parse_requirement_version(content, "black") == ">=26.3.1"

    def test_raises_for_missing_package(self) -> None:
        """Test that missing package raises ValueError."""
        content = "ruff>=0.2.0\n"
        with pytest.raises(ValueError, match="not found"):
            _parse_requirement_version(content, "black")

    def test_ignores_comments(self) -> None:
        """Test that comments after version spec are excluded."""
        content = "black==26.3.1  # pinned for CI consistency\n"
        assert _parse_requirement_version(content, "black") == "==26.3.1"
