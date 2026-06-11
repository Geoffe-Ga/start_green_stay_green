"""Filesystem utilities.

Cross-platform helpers for file and directory operations. The single
guarded home for marking generated scripts executable: POSIX systems get
``chmod(0o755)``, while Windows — where the executable bit does not
exist and ``Path.chmod`` cannot grant execute permission — is a
deliberate no-op (#380).
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

#: Mode applied to generated scripts on POSIX systems (rwxr-xr-x).
EXECUTABLE_MODE = 0o755


def _is_windows() -> bool:
    """Return True on native Windows.

    A patchable seam rather than an inline ``os.name`` read: tests must
    never monkeypatch the real ``os.name``, because ``pathlib.Path``
    dispatches on it at construction time — patching it to "posix" on a
    Windows runner makes every ``Path()`` call (including ones inside
    pytest plugins during report building) raise NotImplementedError.

    Returns:
        Whether the current platform is native Windows.
    """
    return os.name == "nt"


def make_executable(path: Path) -> None:
    """Mark ``path`` executable (mode 0o755) on POSIX; no-op on Windows.

    Windows has no executable permission bit: scripts run based on their
    file extension and association, and ``chmod`` can only toggle the
    read-only flag. Calling it for the POSIX execute bits is meaningless
    there, so this helper skips the call entirely on ``os.name == "nt"``
    while preserving the exact historical ``chmod(0o755)`` behavior on
    every other platform (#380).

    Args:
        path: File to mark executable. Must already exist on POSIX.

    Raises:
        OSError: If the file does not exist or permissions cannot be
            changed (POSIX only).
    """
    if _is_windows():
        return
    path.chmod(EXECUTABLE_MODE)
