"""Async-to-sync bridge for running async code in synchronous contexts."""

from __future__ import annotations

import asyncio
from typing import Any
from typing import TYPE_CHECKING
from typing import TypeVar

if TYPE_CHECKING:
    from collections.abc import Coroutine

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run async coroutine in sync context.

    Handles edge cases:
    - Creates new event loop if none exists
    - Uses asyncio.run() for clean execution
    - Proper cleanup after execution

    Args:
        coro: Async coroutine to execute

    Returns:
        Result from coroutine execution

    Raises:
        RuntimeError: If called from within an event loop

    Example:
        >>> async def fetch_data():
        ...     return "data"
        >>> result = run_async(fetch_data())
    """
    try:
        # Check if event loop is already running
        asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running - safe to use asyncio.run()
        return asyncio.run(coro)
    else:
        # Event loop is running - cannot use asyncio.run()
        msg = "run_async() cannot be called from an event loop"
        raise RuntimeError(msg)
