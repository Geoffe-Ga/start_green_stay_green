"""Tests for async-to-sync bridge utility."""

from __future__ import annotations

import asyncio

import pytest

from start_green_stay_green.utils.async_bridge import run_async


class TestRunAsync:
    """Tests for run_async() function."""

    def test_run_async_executes_coroutine(self) -> None:
        """Test run_async executes async function and returns result."""

        async def async_func() -> str:
            """Return test string."""
            return "result"

        result = run_async(async_func())
        assert result == "result"

    def test_run_async_with_return_value(self) -> None:
        """Test run_async returns correct value from coroutine."""

        async def async_func() -> int:
            """Return test integer."""
            return 42

        result = run_async(async_func())
        assert result == 42

    def test_run_async_with_exception(self) -> None:
        """Test run_async propagates exceptions from coroutine."""

        async def async_func() -> None:
            """Raise test exception."""
            msg = "Test error"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Test error"):
            run_async(async_func())

    def test_run_async_with_async_operations(self) -> None:
        """Test run_async handles actual async operations."""

        async def async_func() -> str:
            """Simulate async operation and return completion status."""
            # Simulate async operation
            await asyncio.sleep(0)
            return "completed"

        result = run_async(async_func())
        assert result == "completed"

    def test_run_async_preserves_return_type(self) -> None:
        """Test run_async preserves type information."""

        async def async_list_func() -> list[int]:
            """Return test list."""
            return [1, 2, 3]

        result = run_async(async_list_func())
        assert result == [1, 2, 3]
