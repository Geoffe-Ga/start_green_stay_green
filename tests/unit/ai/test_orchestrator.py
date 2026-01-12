"""Tests for ai.orchestrator module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.ai import orchestrator


class TestOrchestratorModule:
    """Test suite for AI orchestration."""

    def test_orchestrator_module_imports(self) -> None:
        """Test that orchestrator module can be imported."""
        assert orchestrator is not None

    def test_orchestrator_module_has_docstring(self) -> None:
        """Test that orchestrator module has proper documentation."""
        assert orchestrator.__doc__ is not None
        assert "orchestr" in orchestrator.__doc__.lower()

    def test_orchestrator_path_exists(self) -> None:
        """Test that orchestrator module file exists."""
        orch_file = Path("start_green_stay_green/ai/orchestrator.py")
        assert orch_file.exists()

    def test_orchestrator_is_valid_python_module(self) -> None:
        """Test that orchestrator module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.ai.orchestrator"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_orchestrator_can_be_imported_from_package(self) -> None:
        """Test that orchestrator can be imported from ai package."""
        from start_green_stay_green import ai

        assert hasattr(ai, "orchestrator")
