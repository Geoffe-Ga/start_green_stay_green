"""Unit tests for ``start_green_stay_green.utils.timing``."""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import TimingReport
from start_green_stay_green.utils.timing import get_active_report
from start_green_stay_green.utils.timing import set_active_report
from start_green_stay_green.utils.timing import step_timer


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
