"""Tests for generators.metrics module."""

from __future__ import annotations

from pathlib import Path

import pytest

from start_green_stay_green.generators import metrics


class TestMetricsGeneratorModule:
    """Test suite for metrics generation."""

    def test_metrics_module_imports(self) -> None:
        """Test that metrics module can be imported."""
        assert metrics is not None

    def test_metrics_module_has_docstring(self) -> None:
        """Test that metrics module has proper documentation."""
        assert metrics.__doc__ is not None
        assert "metric" in metrics.__doc__.lower()

    def test_metrics_path_exists(self) -> None:
        """Test that metrics module file exists."""
        metrics_file = Path("start_green_stay_green/generators/metrics.py")
        assert metrics_file.exists()

    def test_metrics_is_valid_python_module(self) -> None:
        """Test that metrics module is valid Python."""
        import importlib

        spec = importlib.util.find_spec(
            "start_green_stay_green.generators.metrics"
        )
        assert spec is not None
        assert spec.loader is not None

    def test_metrics_can_be_imported_from_package(self) -> None:
        """Test that metrics can be imported from generators package."""
        from start_green_stay_green import generators

        assert hasattr(generators, "metrics")
