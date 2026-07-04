"""Auto-mark all tests in tests/integration/ as integration tests."""

from pathlib import Path

import pytest

# Ancestry comparison (instead of matching the substring "/integration/"
# in the item path) keeps the marker working on Windows, where paths use
# backslashes and the substring never matched (#380).
_SUITE_DIR = Path(__file__).resolve().parent


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add integration marker to all tests collected from this directory."""
    for item in items:
        if _SUITE_DIR in item.path.resolve().parents:
            item.add_marker(pytest.mark.integration)
