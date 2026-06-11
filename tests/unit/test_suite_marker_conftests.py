"""Tests for the integration/e2e auto-marking conftest hooks.

The original hooks matched the literal substring ``"/integration/"`` in
``str(item.fspath)``, which never matches on Windows where paths use
backslashes — so ``-m "not integration and not e2e"`` would silently run
the integration and e2e suites there (#380). The hooks now compare
pathlib ancestry, which is separator-agnostic.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

from tests.e2e import conftest as e2e_conftest
from tests.integration import conftest as integration_conftest

if TYPE_CHECKING:
    import pytest

_TESTS_DIR = Path(__file__).resolve().parent.parent


class _FakeItem:
    """Minimal stand-in for pytest.Item: a path plus recorded markers."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.markers: list[pytest.MarkDecorator] = []

    def add_marker(self, marker: pytest.MarkDecorator) -> None:
        """Record an added marker."""
        self.markers.append(marker)


def _marker_names(item: _FakeItem) -> list[str]:
    return [m.name for m in item.markers]


class TestIntegrationAutoMark:
    """tests/integration/conftest.py marks exactly its own subtree."""

    def test_marks_items_under_integration_dir(self) -> None:
        """Items below tests/integration/ get the integration marker."""
        item = _FakeItem(_TESTS_DIR / "integration" / "test_init_flow.py")

        integration_conftest.pytest_collection_modifyitems(
            cast("list[pytest.Item]", [item])
        )

        assert _marker_names(item) == ["integration"]

    def test_marks_items_in_nested_subdirectories(self) -> None:
        """Nested files (e.g. generators/) are still marked."""
        item = _FakeItem(
            _TESTS_DIR / "integration" / "generators" / "test_metrics_integration.py"
        )

        integration_conftest.pytest_collection_modifyitems(
            cast("list[pytest.Item]", [item])
        )

        assert _marker_names(item) == ["integration"]

    def test_does_not_mark_unit_tests(self) -> None:
        """Items outside tests/integration/ are left unmarked."""
        item = _FakeItem(_TESTS_DIR / "unit" / "test_baseline.py")

        integration_conftest.pytest_collection_modifyitems(
            cast("list[pytest.Item]", [item])
        )

        assert not item.markers


class TestE2eAutoMark:
    """tests/e2e/conftest.py marks exactly its own subtree."""

    def test_marks_items_under_e2e_dir(self) -> None:
        """Items below tests/e2e/ get the e2e marker."""
        item = _FakeItem(_TESTS_DIR / "e2e" / "test_init_command.py")

        e2e_conftest.pytest_collection_modifyitems(cast("list[pytest.Item]", [item]))

        assert _marker_names(item) == ["e2e"]

    def test_does_not_mark_integration_tests(self) -> None:
        """Items outside tests/e2e/ are left unmarked."""
        item = _FakeItem(_TESTS_DIR / "integration" / "test_init_flow.py")

        e2e_conftest.pytest_collection_modifyitems(cast("list[pytest.Item]", [item]))

        assert not item.markers
