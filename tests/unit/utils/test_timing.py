"""Unit tests for ``start_green_stay_green.utils.timing``."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.cli import _maybe_collect_timing
from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import TimingReport
from start_green_stay_green.utils.timing import get_active_report
from start_green_stay_green.utils.timing import set_active_report
from start_green_stay_green.utils.timing import step_timer

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class _BoomError(RuntimeError):
    """Sentinel exception used by ``TestMaybeCollectTimingExceptionPath``."""


@pytest.fixture(autouse=True)
def _reset_active_report() -> Iterator[None]:
    """Make sure tests cannot leak the active report into each other."""
    set_active_report(None)
    yield
    set_active_report(None)


class TestTimingReport:
    """Tests for the ``TimingReport`` collector."""

    def test_begin_and_end_step_records_duration(self) -> None:
        report = TimingReport()
        record = report.begin_step("structure")
        report.end_step(record, 0.42)

        assert len(report.steps) == 1
        assert report.steps[0].name == "structure"
        assert report.steps[0].duration_s == pytest.approx(0.42)

    def test_record_api_call_attributes_to_active_step(self) -> None:
        report = TimingReport()
        record = report.begin_step("subagents")
        report.record_api_call(
            APICallRecord(
                latency_s=1.5,
                retries=0,
                input_tokens=100,
                output_tokens=200,
            )
        )
        report.end_step(record, 1.6)

        assert report.steps[0].api_calls == 1
        assert report.api_calls[0].input_tokens == 100
        assert report.api_calls[0].output_tokens == 200

    def test_api_call_outside_step_still_recorded_globally(self) -> None:
        report = TimingReport()
        report.record_api_call(APICallRecord(latency_s=0.5))

        assert len(report.api_calls) == 1
        assert report.steps == []

    def test_aggregate_token_totals(self) -> None:
        report = TimingReport()
        report.record_api_call(
            APICallRecord(
                latency_s=1.0,
                input_tokens=100,
                output_tokens=200,
                cache_read_tokens=50,
            )
        )
        report.record_api_call(
            APICallRecord(
                latency_s=2.0,
                input_tokens=300,
                output_tokens=400,
            )
        )

        assert report.total_input_tokens == 400
        assert report.total_output_tokens == 600
        assert report.total_cache_read_tokens == 50
        assert report.api_seconds == pytest.approx(3.0)

    def test_to_dict_shape(self) -> None:
        report = TimingReport()
        record = report.begin_step("ci")
        report.record_api_call(
            APICallRecord(latency_s=0.5, input_tokens=10, output_tokens=20)
        )
        report.end_step(record, 0.6)

        payload = report.to_dict()

        assert payload["api_calls"] == 1
        assert payload["tokens"] == {"input": 10, "output": 20, "cache_read": 0}
        steps = payload["steps"]
        assert isinstance(steps, list)
        assert steps[0]["name"] == "ci"
        assert steps[0]["api_calls"] == 1

    def test_write_json_round_trip(self, tmp_path: Path) -> None:
        report = TimingReport()
        record = report.begin_step("readme")
        report.end_step(record, 0.1)

        out = tmp_path / "report.json"
        report.write_json(out)

        loaded = json.loads(out.read_text())
        assert loaded["steps"][0]["name"] == "readme"


class TestStepTimerContext:
    """Tests for the ``step_timer`` context manager."""

    def test_step_timer_without_active_report_runs_silently(self) -> None:
        # No report installed; step_timer must still work.
        with step_timer("noop") as record:
            time.sleep(0.001)
        assert record.duration_s > 0
        assert get_active_report() is None

    def test_step_timer_with_active_report_records_step(self) -> None:
        report = TimingReport()
        set_active_report(report)

        with step_timer("structure"):
            time.sleep(0.001)

        assert len(report.steps) == 1
        assert report.steps[0].name == "structure"
        assert report.steps[0].duration_s > 0

    def test_nested_step_timers_attribute_to_innermost(self) -> None:
        report = TimingReport()
        set_active_report(report)

        with step_timer("outer"), step_timer("inner"):
            report.record_api_call(APICallRecord(latency_s=0.1))

        # Both steps recorded; the API call belongs to ``inner``.
        names = [s.name for s in report.steps]
        assert names == ["outer", "inner"]
        outer = next(s for s in report.steps if s.name == "outer")
        inner = next(s for s in report.steps if s.name == "inner")
        assert inner.api_calls == 1
        assert outer.api_calls == 0

    def test_step_timer_records_duration_on_exception(self) -> None:
        report = TimingReport()
        set_active_report(report)

        def _explode() -> None:
            with step_timer("explodes"):
                msg = "boom"
                raise RuntimeError(msg)

        with pytest.raises(RuntimeError, match="boom"):
            _explode()

        assert report.steps[0].name == "explodes"
        assert report.steps[0].duration_s >= 0


class TestMaybeCollectTimingExceptionPath:
    """The `_maybe_collect_timing` cm in cli.py must persist on exception."""

    @staticmethod
    def _explode_with_step(report_path: Path) -> None:
        """Helper that records a step then raises, for the persistence test."""
        with _maybe_collect_timing(report_path):
            # Record at least one step before the failure so the
            # written JSON has something to verify.
            with step_timer("structure"):
                pass
            msg = "boom"
            raise _BoomError(msg)

    @staticmethod
    def _explode_bare() -> None:
        """Helper that raises inside a no-op _maybe_collect_timing block."""
        with _maybe_collect_timing(None):
            msg = "bare"
            raise ValueError(msg)

    def test_exception_inside_block_still_writes_report(self, tmp_path: Path) -> None:
        """If the wrapped block raises, the partial timing report is still written."""
        report_path = tmp_path / "reports" / "partial.json"

        with pytest.raises(_BoomError, match="boom"):
            self._explode_with_step(report_path)

        # The finally block must have executed: report exists,
        # active-report singleton is cleared.
        assert report_path.exists(), "partial timing report not persisted"
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        assert isinstance(payload["steps"], list)
        names = [s["name"] for s in payload["steps"]]
        assert "structure" in names
        assert get_active_report() is None

    def test_no_path_is_a_no_op(self, tmp_path: Path) -> None:
        """When timing_json is None the cm leaves no side effects."""
        # No file is created; no report is installed; the exception
        # propagates exactly like a plain block.
        with pytest.raises(ValueError, match="bare"):
            self._explode_bare()

        assert list(tmp_path.iterdir()) == []
        assert get_active_report() is None
