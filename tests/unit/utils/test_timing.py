"""Unit tests for ``start_green_stay_green.utils.timing``."""

from __future__ import annotations

import asyncio
import json
import time
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.cli import _maybe_collect_timing
from start_green_stay_green.utils.timing import APICallRecord
from start_green_stay_green.utils.timing import StepTiming
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
        assert not report.steps

    def test_aggregate_token_totals(self) -> None:
        report = TimingReport()
        report.record_api_call(
            APICallRecord(
                latency_s=1.0,
                input_tokens=100,
                output_tokens=200,
                cache_read_tokens=50,
                cache_creation_tokens=20,
            )
        )
        report.record_api_call(
            APICallRecord(
                latency_s=2.0,
                input_tokens=300,
                output_tokens=400,
                cache_creation_tokens=10,
            )
        )

        assert report.total_input_tokens == 400
        assert report.total_output_tokens == 600
        assert report.total_cache_read_tokens == 50
        assert report.total_cache_creation_tokens == 30
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
        assert payload["tokens"] == {
            "input": 10,
            "output": 20,
            "cache_read": 0,
            "cache_creation": 0,
        }
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


class TestActiveReportContextIsolation:
    """The active report is a ``ContextVar`` with per-task isolation."""

    @pytest.mark.asyncio
    async def test_concurrent_tasks_see_their_own_active_report(self) -> None:
        """Two concurrent tasks each install and observe a distinct report.

        Because ``set_active_report`` mutates a ``ContextVar``, a value set
        inside one task is invisible to a sibling task running in the same
        event loop. A process-global singleton would let the last writer
        clobber the other task's report, so this fails on the old impl.
        """
        report_a = TimingReport()
        report_b = TimingReport()
        # Barriers force both tasks to interleave: each sets its report,
        # then waits until the other has also set its own before reading.
        both_set = asyncio.Event()
        set_count = 0

        async def _run(report: TimingReport) -> TimingReport | None:
            nonlocal set_count
            set_active_report(report)
            set_count += 1
            if set_count == 2:  # both tasks have written
                both_set.set()
            await both_set.wait()
            # If the report leaked across tasks, we would observe the
            # sibling's report (or whichever wrote last).
            return get_active_report()

        seen_a, seen_b = await asyncio.gather(_run(report_a), _run(report_b))

        assert seen_a is report_a
        assert seen_b is report_b

    @pytest.mark.asyncio
    async def test_spawned_task_inherits_parent_active_report(self) -> None:
        """A task spawned inside an active report inherits it at spawn time.

        This guarantees the Phase 2 ``asyncio.gather`` fan-out still
        attributes API calls dispatched by child tasks to the parent's
        report, because ``ContextVar`` copies the context at task creation.
        """
        parent_report = TimingReport()
        set_active_report(parent_report)

        async def _child() -> TimingReport | None:
            # No explicit set here: the child must inherit the parent's
            # report from the copied context.
            return get_active_report()

        first, second = await asyncio.gather(_child(), _child())

        assert first is parent_report
        assert second is parent_report


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

        assert not list(tmp_path.iterdir())
        assert get_active_report() is None


class TestAPICallRecordDefaults:
    """Exact default values for ``APICallRecord`` optional fields."""

    def test_optional_fields_default_to_zero(self) -> None:
        """Unspecified counters default to exactly 0 (not 1 and not None)."""
        record = APICallRecord(latency_s=1.0)

        assert record.retries == 0
        assert record.retries is not None
        assert record.input_tokens == 0
        assert record.input_tokens is not None
        assert record.output_tokens == 0
        assert record.output_tokens is not None
        assert record.cache_read_tokens == 0
        assert record.cache_creation_tokens == 0


class TestTimingReportDataclassFields:
    """Internal bookkeeping fields are excluded from ``repr`` and ``eq``."""

    def test_internal_fields_excluded_from_repr(self) -> None:
        """``_stack`` and ``_lock`` never appear in the report ``repr``."""
        text = repr(TimingReport())

        assert "_stack" not in text
        assert "_lock" not in text

    def test_distinct_stacks_do_not_break_equality(self) -> None:
        """Reports compare equal even when their ephemeral stacks differ."""
        left = TimingReport(started_at=0.0)
        right = TimingReport(started_at=0.0)
        # Mutate only the (compare=False) stack on the left.
        left.begin_step("only-on-left")
        # Drop the matching public step so the visible state is identical.
        left.steps.clear()

        assert left == right

    def test_distinct_locks_do_not_break_equality(self) -> None:
        """Two freshly built reports compare equal despite distinct locks."""
        # Each report's default_factory builds its own ``threading.Lock``;
        # if the lock were compared (compare=True) they would be unequal.
        assert TimingReport(started_at=0.0) == TimingReport(started_at=0.0)


class TestBeginStepInitialDuration:
    """``begin_step`` returns a record that starts at zero duration."""

    def test_begin_step_starts_at_zero_duration(self) -> None:
        """A freshly begun step has duration exactly 0.0 until ended."""
        report = TimingReport()

        record = report.begin_step("structure")

        assert record.duration_s == 0.0


class TestEndStepStackManagement:
    """Boundary behaviour of the ``end_step`` stack-popping loop."""

    def test_ending_only_step_clears_stack(self) -> None:
        """Ending the sole active step removes it so later calls re-attribute."""
        report = TimingReport()
        record = report.begin_step("solo")
        report.end_step(record, 0.1)

        # Stack is now empty: a subsequent API call attributes to nothing.
        report.record_api_call(APICallRecord(latency_s=0.5))

        assert report.steps[0].api_calls == 0

    def test_ending_unknown_record_is_a_noop(self) -> None:
        """Ending a record never pushed leaves the (empty) stack untouched."""
        report = TimingReport()
        stray = StepTiming(name="stray", duration_s=0.0)

        # Must not raise even though the stack is empty.
        report.end_step(stray, 0.1)

        assert not report.steps

    def test_ending_middle_step_pops_down_to_it(self) -> None:
        """Ending a mid-stack step discards deeper entries and keeps shallower."""
        report = TimingReport()
        outer = report.begin_step("outer")
        middle = report.begin_step("middle")
        report.begin_step("inner")

        report.end_step(middle, 0.1)

        # Stack is now [outer]: a new API call attributes to ``outer``.
        report.record_api_call(APICallRecord(latency_s=0.5))

        assert outer.api_calls == 1
        assert middle.api_calls == 0

    def test_ending_step_pops_exactly_to_record_not_below(self) -> None:
        """Ending the top step leaves the parent active, not an empty stack."""
        report = TimingReport()
        parent = report.begin_step("parent")
        child = report.begin_step("child")

        report.end_step(child, 0.1)

        # Stack is now [parent]: the API call must attribute to ``parent``.
        report.record_api_call(APICallRecord(latency_s=0.5))

        assert parent.api_calls == 1
        assert child.api_calls == 0


class TestRecordApiCallIncrements:
    """``record_api_call`` accumulates rather than overwriting the count."""

    def test_multiple_calls_increment_step_count(self) -> None:
        """Three API calls in one step yield an ``api_calls`` count of 3."""
        report = TimingReport()
        record = report.begin_step("subagents")
        report.record_api_call(APICallRecord(latency_s=0.1))
        report.record_api_call(APICallRecord(latency_s=0.1))
        report.record_api_call(APICallRecord(latency_s=0.1))
        report.end_step(record, 0.4)

        assert report.steps[0].api_calls == 3


class TestWallClockComputation:
    """``wall_clock_s`` is elapsed time, computed by subtraction."""

    def test_wall_clock_is_elapsed_difference(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Wall clock equals now minus start, not their sum."""
        report = TimingReport(started_at=100.0)
        monkeypatch.setattr(time, "perf_counter", lambda: 103.0)

        # Subtraction -> 3.0; the ``+`` mutant would yield 203.0.
        assert report.wall_clock_s == pytest.approx(3.0)


class TestToDictRoundingAndKeys:
    """Exact keys and 4-decimal rounding in ``to_dict``."""

    def test_payload_uses_exact_top_level_keys(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The serialized payload exposes the canonical key names."""
        report = TimingReport(started_at=0.0)
        monkeypatch.setattr(time, "perf_counter", lambda: 1.0)

        payload = report.to_dict()

        assert "wall_clock_s" in payload
        assert "api_seconds" in payload
        # The mutated ``XX..XX`` keys would be absent under these exact names.
        assert set(payload) == {
            "wall_clock_s",
            "api_calls",
            "api_seconds",
            "steps",
            "tokens",
        }

    def test_step_dict_uses_exact_duration_key(self) -> None:
        """Each step entry carries a literal ``duration_s`` key."""
        report = TimingReport()
        record = report.begin_step("ci")
        report.end_step(record, 0.2)

        steps = report.to_dict()["steps"]
        assert isinstance(steps, list)
        step = steps[0]
        assert isinstance(step, dict)

        assert "duration_s" in step
        assert set(step) == {"name", "duration_s", "api_calls"}

    def test_wall_clock_rounds_to_four_decimals(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``wall_clock_s`` is rounded to 4 decimals, not 5."""
        report = TimingReport(started_at=0.0)
        monkeypatch.setattr(time, "perf_counter", lambda: 0.123456789)

        assert report.to_dict()["wall_clock_s"] == 0.1235

    def test_api_seconds_rounds_to_four_decimals(self) -> None:
        """``api_seconds`` is rounded to 4 decimals, not 5."""
        report = TimingReport()
        report.record_api_call(APICallRecord(latency_s=0.123456789))

        assert report.to_dict()["api_seconds"] == 0.1235

    def test_step_duration_rounds_to_four_decimals(self) -> None:
        """A step's ``duration_s`` is rounded to 4 decimals, not 5."""
        report = TimingReport()
        record = report.begin_step("structure")
        report.end_step(record, 0.123456789)

        steps = report.to_dict()["steps"]
        assert isinstance(steps, list)
        step = steps[0]
        assert isinstance(step, dict)
        assert step["duration_s"] == 0.1235


class TestWriteJsonFormatting:
    """``write_json`` pins indent=2 and sorted keys."""

    def test_json_is_indented_two_spaces(self, tmp_path: Path) -> None:
        """The written JSON uses a two-space indent for nested keys."""
        report = TimingReport(started_at=0.0)
        out = tmp_path / "report.json"
        report.write_json(out)

        text = out.read_text(encoding="utf-8")
        # Top-level keys are indented by exactly two spaces (indent=3 mutant
        # would produce three) and never by three.
        assert '\n  "api_calls":' in text
        assert '\n   "api_calls":' not in text

    def test_json_keys_are_sorted(self, tmp_path: Path) -> None:
        """Top-level keys appear in sorted order in the written JSON."""
        report = TimingReport(started_at=0.0)
        out = tmp_path / "report.json"
        report.write_json(out)

        text = out.read_text(encoding="utf-8")
        keys = [
            line.strip().split('"')[1]
            for line in text.splitlines()
            if line.startswith('  "')
        ]

        assert keys == sorted(keys)
        assert keys == [
            "api_calls",
            "api_seconds",
            "steps",
            "tokens",
            "wall_clock_s",
        ]


class TestStepTimerDurationComputation:
    """``step_timer`` records duration via subtraction, starting at zero."""

    def test_no_report_record_starts_at_zero_inside_block(self) -> None:
        """Without a report, the yielded record reads 0.0 before exit."""
        with step_timer("noop") as record:
            # Initial duration is exactly 0.0 inside the block (the ``1.0``
            # mutant would be observable here before the finally overwrites).
            assert record.duration_s == 0.0

    def test_no_report_duration_is_elapsed_difference(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without a report, recorded duration is end minus start."""
        clock = iter([10.0, 13.0])
        monkeypatch.setattr(time, "perf_counter", lambda: next(clock))

        with step_timer("noop") as record:
            pass

        # 13.0 - 10.0 == 3.0; the ``+`` mutant would give 23.0.
        assert record.duration_s == pytest.approx(3.0)

    def test_with_report_duration_is_elapsed_difference(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With a report, the ended step's duration is end minus start."""
        report = TimingReport(started_at=0.0)
        set_active_report(report)
        clock = iter([10.0, 13.0])
        monkeypatch.setattr(time, "perf_counter", lambda: next(clock))

        with step_timer("structure"):
            pass

        # 13.0 - 10.0 == 3.0; the ``+`` mutant would give 23.0.
        assert report.steps[0].duration_s == pytest.approx(3.0)
