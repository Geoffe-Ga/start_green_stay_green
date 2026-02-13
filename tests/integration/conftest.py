"""Auto-mark all tests in tests/integration/ as integration tests."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add integration marker to all tests collected from this directory."""
    for item in items:
        if "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
