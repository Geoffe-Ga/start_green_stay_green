"""Tests for utils.fs module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.utils import fs


class TestFsModule:
    """Test suite for filesystem utilities."""

    def test_fs_module_imports(self) -> None:
        """Test that fs module can be imported."""
        assert fs is not None

    def test_fs_module_has_docstring(self) -> None:
        """Test that fs module has proper documentation."""
        assert fs.__doc__ is not None
        assert "filesystem" in fs.__doc__.lower()

    def test_fs_path_exists(self) -> None:
        """Test that fs module file exists."""
        fs_file = Path("start_green_stay_green/utils/fs.py")
        assert fs_file.exists()

    def test_fs_is_valid_python_module(self) -> None:
        """Test that fs module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.utils.fs"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_fs_can_be_imported_from_package(self) -> None:
        """Test that fs can be imported from utils package."""
        from start_green_stay_green import utils

        assert hasattr(utils, "fs")
