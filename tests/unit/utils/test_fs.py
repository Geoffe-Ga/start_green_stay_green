"""Tests for start_green_stay_green.utils.fs cross-platform helpers.

The ``make_executable`` helper is the single guarded home for the
``chmod(0o755)`` calls that raise or are meaningless on Windows (#380).
Both platform branches are tested hermetically by monkeypatching
``os.name`` and ``Path.chmod``; one real-filesystem test pins the POSIX
end state.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from start_green_stay_green.utils import fs
from tests.conftest import assert_executable


class TestMakeExecutable:
    """Tests for fs.make_executable platform branches."""

    def test_posix_chmods_exactly_0o755(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On POSIX the helper applies exactly mode 0o755."""
        monkeypatch.setattr(os, "name", "posix")
        target = tmp_path / "script.sh"
        target.write_text("#!/bin/sh\n", encoding="utf-8")
        recorded: list[int] = []

        def record_chmod(_self: Path, mode: int) -> None:
            recorded.append(mode)

        monkeypatch.setattr(Path, "chmod", record_chmod)

        fs.make_executable(target)

        assert recorded == [0o755]

    def test_windows_is_a_noop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On Windows (os.name == "nt") the helper never calls chmod."""
        monkeypatch.setattr(os, "name", "nt")
        target = tmp_path / "script.sh"
        target.write_text("#!/bin/sh\n", encoding="utf-8")

        def forbid_chmod(_self: Path, _mode: int) -> None:
            msg = "chmod must not be called on Windows"
            raise AssertionError(msg)

        monkeypatch.setattr(Path, "chmod", forbid_chmod)

        fs.make_executable(target)  # Must not raise.

    def test_real_file_ends_up_executable(self, tmp_path: Path) -> None:
        """End-to-end: the file is executable afterwards (POSIX-checked)."""
        target = tmp_path / "script.sh"
        target.write_text("#!/bin/sh\n", encoding="utf-8")

        fs.make_executable(target)

        assert_executable(target)

    def test_executable_mode_constant_is_0o755(self) -> None:
        """The module-level mode constant stays rwxr-xr-x."""
        assert fs.EXECUTABLE_MODE == 0o755

    def test_missing_file_raises_on_posix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POSIX behavior is unchanged: chmod on a missing path raises."""
        monkeypatch.setattr(os, "name", "posix")

        with pytest.raises(OSError, match="does-not-exist"):
            fs.make_executable(tmp_path / "does-not-exist.sh")
