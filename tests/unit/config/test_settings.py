"""Tests for config.settings module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.config import settings

if TYPE_CHECKING:
    from unittest.mock import MagicMock


class TestSettingsModule:
    """Test suite for global settings management."""

    def test_settings_module_imports(self) -> None:
        """Test that settings module can be imported."""
        assert settings is not None

    def test_settings_module_has_docstring(self) -> None:
        """Test that settings module has proper documentation."""
        assert settings.__doc__ is not None
        assert "settings" in settings.__doc__.lower()

    def test_settings_path_exists(self) -> None:
        """Test that settings module file exists."""
        settings_file = Path(
            "start_green_stay_green/config/settings.py"
        )
        assert settings_file.exists()

    def test_settings_is_valid_python_module(self) -> None:
        """Test that settings module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.config.settings"
        )
        assert spec is not None
        assert spec.loader is not None
