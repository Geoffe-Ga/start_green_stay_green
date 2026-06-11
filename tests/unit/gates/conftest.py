"""Fixtures for gate runner tests."""

from collections.abc import Generator
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest

from start_green_stay_green.gates import common


@pytest.fixture(autouse=True)
def restore_cwd() -> Generator[None, None, None]:
    """Restore the working directory after each test.

    Every gate calls ``common.enter_project_root()``, which chdirs; tests
    that patch ``project_root`` to a tmp dir must not leak that cwd.

    Yields:
        None.
    """
    original = Path.cwd()
    yield
    os.chdir(original)


def completed(
    returncode: int = 0,
    stdout: str | None = None,
    stderr: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Build a canned CompletedProcess for run_tool fakes.

    Args:
        returncode: Exit code to report.
        stdout: Captured stdout, if any.
        stderr: Captured stderr, if any.

    Returns:
        A CompletedProcess with the given fields.
    """
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


class FakeRunner:
    """Recording stand-in for ``common.run_tool``."""

    def __init__(self, *results: subprocess.CompletedProcess[str]) -> None:
        """Store the canned results to return in order.

        Args:
            *results: One CompletedProcess per expected invocation; the
                last one repeats if more calls arrive.
        """
        self.results = list(results)
        self.calls: list[list[str]] = []
        self.kwargs: list[dict[str, Any]] = []

    def __call__(
        self, cmd: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        """Record the invocation and pop the next canned result.

        Args:
            cmd: Tool argument vector.
            **kwargs: Stream dispositions passed by the gate.

        Returns:
            The next canned CompletedProcess.
        """
        self.calls.append(cmd)
        self.kwargs.append(kwargs)
        if len(self.results) > 1:
            return self.results.pop(0)
        return self.results[0]


@pytest.fixture
def fake_tools(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Resolve every tool to a predictable fake path.

    Args:
        monkeypatch: Pytest patching fixture.

    Returns:
        Mutable mapping a test may edit (set a value to "" to simulate
        a missing tool).
    """
    paths: dict[str, str] = {}

    def resolver(name: str) -> str | None:
        configured = paths.get(name, f"/fake/{name}")
        return configured or None

    monkeypatch.setattr(common, "resolve_tool", resolver)
    return paths
