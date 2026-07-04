"""Tests for the typecheck gate (port of scripts/typecheck.sh)."""

import json

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import typecheck
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed


@pytest.mark.usefixtures("fake_tools")
class TestTypecheck:
    def test_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert typecheck.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Type Checking (MyPy) ===" in out
        assert "✓ Type checks passed" in out
        assert runner.calls == [["/fake/mypy", "."]]

    def test_failure_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert typecheck.main([]) == 1
        assert "✗ Type checking failed" in capsys.readouterr().err

    def test_missing_mypy_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["mypy"] = ""
        assert typecheck.main([]) == 2
        assert "mypy is not installed" in capsys.readouterr().err

    def test_verbose_prints_timings(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert typecheck.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Running MyPy type checker..." in out
        assert "Type check execution time:" in out
        assert "Total execution time:" in out


@pytest.mark.usefixtures("fake_tools")
class TestTypecheckMetrics:
    def test_counts_error_lines(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output = (
            "cli.py:1: error: bad thing  [misc]\n"
            "cli.py:9: note: see above\n"
            "other.py:2: error: worse thing  [misc]\n"
        )
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1, stdout=output)))
        assert typecheck.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"errors": 2, "status": "fail"}

    def test_clean_run_reports_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common,
            "run_tool",
            FakeRunner(completed(0, stdout="Success: no issues found\n")),
        )
        assert typecheck.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"errors": 0, "status": "pass"}
