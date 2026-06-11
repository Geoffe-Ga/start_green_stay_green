"""Auto-mark all tests in tests/e2e/ as e2e tests."""

from pathlib import Path

import pytest

# Ancestry comparison (instead of matching the substring "/e2e/" in the
# item path) keeps the marker working on Windows, where paths use
# backslashes and the substring never matched (#380).
_SUITE_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add e2e marker to all tests collected from this directory."""
    for item in items:
        if _SUITE_DIR in item.path.resolve().parents:
            item.add_marker(pytest.mark.e2e)
