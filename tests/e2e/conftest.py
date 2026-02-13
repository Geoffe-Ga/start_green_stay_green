"""Auto-mark all tests in tests/e2e/ as e2e tests."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add e2e marker to all tests collected from this directory."""
    for item in items:
        if "/e2e/" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
