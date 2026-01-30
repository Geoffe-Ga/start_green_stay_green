"""Pytest configuration and fixtures for test suite.

This module provides:
- Working directory cleanliness checks
- Common test fixtures
- Test isolation enforcement
"""

from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def verify_no_test_artifacts_in_working_directory() -> Generator[None, None, None]:
    """Verify no test artifacts are created in the project working directory.

    This fixture runs before and after the entire test session to ensure
    that tests don't pollute the working directory with artifacts like
    test-project/ or other generated directories.

    Addresses Issue #112: Test artifacts polluting working directory.

    Yields:
        None: Allows tests to run, then verifies cleanliness afterward.

    Raises:
        AssertionError: If test artifacts are found in working directory after tests.
    """
    # Get project root (parent of tests/)
    project_root = Path(__file__).parent.parent

    # Artifact patterns to check for
    artifact_patterns = [
        "test-project",
        "*-project",
        "test-*-project",
    ]

    def find_artifacts() -> list[Path]:
        """Find test artifacts in project root.

        Returns:
            List of Path objects for found artifacts.
        """
        artifacts: list[Path] = []
        for pattern in artifact_patterns:
            artifacts.extend(project_root.glob(pattern))
        return artifacts

    # Before tests: Record initial state (don't fail, just note)
    initial_artifacts = find_artifacts()
    if initial_artifacts:
        print(  # noqa: T201
            f"\n⚠️  Warning: Found existing test artifacts before tests: "
            f"{[a.name for a in initial_artifacts]}"
        )

    # Run all tests
    yield

    # After tests: Verify no new artifacts created
    final_artifacts = find_artifacts()

    # Filter out artifacts that existed before tests
    new_artifacts = [a for a in final_artifacts if a not in initial_artifacts]

    if new_artifacts:
        artifact_names = [a.name for a in new_artifacts]
        pytest.fail(
            f"Test artifacts found in working directory: {artifact_names}\n"
            f"Tests must use tmp_path fixture and --output-dir parameter.\n"
            f"See Issue #112 for details."
        )


@pytest.fixture
def clean_working_directory() -> Generator[Path, None, None]:
    """Provide current working directory and verify it stays clean.

    This fixture can be used by tests that need to verify working directory
    isolation. It captures the initial working directory state and ensures
    no test artifacts are created there.

    Yields:
        Path: Current working directory.

    Raises:
        AssertionError: If test creates artifacts in working directory.
    """
    cwd = Path.cwd()
    initial_items = set(cwd.iterdir())

    yield cwd

    # After test: Check for new project directories
    final_items = set(cwd.iterdir())
    new_items = final_items - initial_items

    # Filter for project-like directories
    project_dirs = [
        item
        for item in new_items
        if item.is_dir()
        and ("project" in item.name.lower() or item.name.startswith("test-"))
    ]

    if project_dirs:
        project_names = [d.name for d in project_dirs]
        pytest.fail(
            f"Test created artifacts in working directory: {project_names}\n"
            f"Use tmp_path fixture instead."
        )
