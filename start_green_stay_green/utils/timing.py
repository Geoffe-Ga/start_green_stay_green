"""Timing and telemetry collection for ``green init``.

Provides a ``step_timer`` context manager that records named step durations
and a ``TimingReport`` collector that also accumulates Claude API call
metadata (latency, retries, token usage). The collector is intentionally
process-local: telemetry is only persisted when the user passes a path.

Phase 0 of the optimization roadmap relies on this module to baseline
``green init`` so that subsequent phases can be measured.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field
import json
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@dataclass
class StepTiming:
    """Timing record for a single named step.

    Attributes:
        name: Logical step identifier (matches the CLI status string).
        duration_s: Wall-clock duration in seconds.
        api_calls: Number of API calls dispatched during this step.
    """

    name: str
    duration_s: float
    api_calls: int = 0


@dataclass
class APICallRecord:
    """Telemetry for a single Claude API call.

    Attributes:
        latency_s: Wall-clock duration of the call in seconds.
        retries: Number of retry attempts (0 if first attempt succeeded).
        input_tokens: Tokens billed as input (prompt + cache reads).
        output_tokens: Tokens billed as output.
        cache_read_tokens: Tokens served from prompt cache, if reported.
    """

    latency_s: float
    retries: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


@dataclass
class TimingReport:
    """Process-local collector for step and API telemetry.

    Use ``step_timer`` to record steps and ``record_api_call`` to log
    individual API requests. Steps and API calls are correlated by an
    internal stack: an API call recorded inside a ``step_timer`` block
    counts toward that step's ``api_calls`` total.
    """

    started_at: float = field(default_factory=time.perf_counter)
    steps: list[StepTiming] = field(default_factory=list)
    api_calls: list[APICallRecord] = field(default_factory=list)
    _stack: list[StepTiming] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def begin_step(self, name: str) -> StepTiming:
        """Push a new step onto the active stack and return its record.

        Args:
            name: Logical step identifier.

        Returns:
            The newly created ``StepTiming`` record (still 0 duration).
        """
        record = StepTiming(name=name, duration_s=0.0)
        with self._lock:
            self.steps.append(record)
            self._stack.append(record)
        return record

    def end_step(self, record: StepTiming, duration_s: float) -> None:
        """Mark a step as complete with the given duration.

        Pops everything from the active stack down to and including
        ``record``. This makes the collector resilient to out-of-order
        completion: if a child step's ``__exit__`` is skipped (e.g. its
        ``begin_step`` succeeded but the surrounding context manager
        bailed before ``end_step``), the parent will still be popped
        when its own ``end_step`` runs, instead of leaving a stale
        entry that would mis-attribute later API calls.

        Args:
            record: The record returned by ``begin_step``.
            duration_s: Wall-clock duration in seconds.
        """
        with self._lock:
            record.duration_s = duration_s
            # Pop down to ``record`` (inclusive) if it's in the stack;
            # otherwise leave the stack alone so other in-flight steps
            # are unaffected.
            for index in range(len(self._stack) - 1, -1, -1):
                if self._stack[index] is record:
                    del self._stack[index:]
                    return

    def record_api_call(self, call: APICallRecord) -> None:
        """Record a single API call; attribute it to the active step (if any).

        Args:
            call: Telemetry for the call.
        """
        with self._lock:
            self.api_calls.append(call)
            if self._stack:
                self._stack[-1].api_calls += 1

    @property
    def wall_clock_s(self) -> float:
        """Wall-clock time elapsed since the report was created."""
        return time.perf_counter() - self.started_at

    @property
    def api_seconds(self) -> float:
        """Sum of all API call latencies (NOT wall-clock — sequential or not)."""
        return sum(c.latency_s for c in self.api_calls)

    @property
    def total_input_tokens(self) -> int:
        """Total input tokens across all API calls."""
        return sum(c.input_tokens for c in self.api_calls)

    @property
    def total_output_tokens(self) -> int:
        """Total output tokens across all API calls."""
        return sum(c.output_tokens for c in self.api_calls)

    @property
    def total_cache_read_tokens(self) -> int:
        """Total tokens served from the prompt cache."""
        return sum(c.cache_read_tokens for c in self.api_calls)

    def to_dict(self) -> dict[str, object]:
        """Serialize the report to a JSON-friendly dict."""
        return {
            "wall_clock_s": round(self.wall_clock_s, 4),
            "api_calls": len(self.api_calls),
            "api_seconds": round(self.api_seconds, 4),
            "steps": [
                {
                    "name": s.name,
                    "duration_s": round(s.duration_s, 4),
                    "api_calls": s.api_calls,
                }
                for s in self.steps
            ],
            "tokens": {
                "input": self.total_input_tokens,
                "output": self.total_output_tokens,
                "cache_read": self.total_cache_read_tokens,
            },
        }

    def write_json(self, path: Path) -> None:
        """Write the report as pretty-printed JSON.

        Args:
            path: Destination file path. Parent directories must exist.
        """
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))


_active_report: TimingReport | None = None
_active_lock = threading.Lock()


def get_active_report() -> TimingReport | None:
    """Return the currently active ``TimingReport``, if any."""
    with _active_lock:
        return _active_report


def set_active_report(report: TimingReport | None) -> None:
    """Install ``report`` as the active collector for this process.

    Pass ``None`` to disable collection. Calling this from concurrent
    threads is safe; the most recent caller wins.

    Args:
        report: The report to install, or ``None`` to clear.
    """
    global _active_report  # noqa: PLW0603 — module-level singleton by design
    with _active_lock:
        _active_report = report


@contextmanager
def step_timer(name: str) -> Iterator[StepTiming]:
    """Time a named step and attribute API calls dispatched inside it.

    Args:
        name: Logical step identifier (matches the CLI status string).

    Yields:
        The ``StepTiming`` record for the step, mutated in place.

    Example:
        >>> with step_timer("subagents"):
        ...     run_subagent_generation()  # doctest: +SKIP
    """
    report = get_active_report()
    if report is None:
        # No collector installed — yield a throwaway record so callers
        # can use the same idiom unconditionally.
        record = StepTiming(name=name, duration_s=0.0)
        start = time.perf_counter()
        try:
            yield record
        finally:
            record.duration_s = time.perf_counter() - start
        return

    record = report.begin_step(name)
    start = time.perf_counter()
    try:
        yield record
    finally:
        report.end_step(record, time.perf_counter() - start)
