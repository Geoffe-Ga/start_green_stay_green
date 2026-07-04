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
from start_green_stay_green.utils.fs import is_windows
from tests.conftest import assert_executable


def _always_posix() -> bool:
    """Pin the POSIX branch of the is_windows seam."""
    return False


def _always_windows() -> bool:
    """Pin the Windows branch of the is_windows seam."""
    return True


class TestIsWindows:
    """Tests for the fs.is_windows platform-detection seam."""

    def test_nt_is_windows(self) -> None:
        """``os.name == "nt"`` is the sole truthy case."""
        assert is_windows("nt")

    def test_posix_is_not_windows(self) -> None:
        """A POSIX identifier is not Windows."""
        assert not is_windows("posix")

    def test_other_platform_string_is_not_windows(self) -> None:
        """Only the exact string "nt" counts as Windows."""
        assert not is_windows("java")

    def test_default_reflects_live_os_name(self) -> None:
        """Called with no argument, it mirrors the real platform."""
        assert is_windows() == (os.name == "nt")


class TestMakeExecutable:
    """Tests for fs.make_executable platform branches."""

    def test_posix_chmods_exactly_0o755(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On POSIX the helper applies exactly mode 0o755."""
        monkeypatch.setattr(fs, "is_windows", _always_posix)
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
        """On Windows the helper never calls chmod."""
        monkeypatch.setattr(fs, "is_windows", _always_windows)
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
        monkeypatch.setattr(fs, "is_windows", _always_posix)

        with pytest.raises(OSError, match="does-not-exist"):
            fs.make_executable(tmp_path / "does-not-exist.sh")
