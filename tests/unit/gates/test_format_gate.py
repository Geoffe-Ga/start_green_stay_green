"""Tests for the format gate (port of scripts/format.sh)."""

import json

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import format as format_gate
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed


@pytest.mark.usefixtures("fake_tools")
class TestFormatCheckMode:
    def test_check_is_default_and_runs_isort_then_black(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert format_gate.main([]) == 0
        assert runner.calls == [
            ["/fake/isort", "--check", "."],
            ["/fake/black", "--check", "."],
        ]
        out = capsys.readouterr().out
        assert "=== Formatting (Black + isort) ===" in out
        assert "✓ Code formatting check passed" in out

    def test_explicit_check_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert format_gate.main(["--check"]) == 0
        assert runner.calls[0] == ["/fake/isort", "--check", "."]

    def test_fix_mode_overrides_check(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert format_gate.main(["--fix", "--check"]) == 0
        assert runner.calls == [
            ["/fake/isort", "."],
            ["/fake/black", "."],
        ]
        assert "✓ Code formatted successfully" in capsys.readouterr().out


@pytest.mark.usefixtures("fake_tools")
class TestFormatFailures:
    def test_isort_failure_stops_before_black(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(1))
        monkeypatch.setattr(common, "run_tool", runner)
        assert format_gate.main([]) == 1
        assert len(runner.calls) == 1
        assert "✗ isort failed" in capsys.readouterr().err

    def test_black_failure_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0), completed(1))
        monkeypatch.setattr(common, "run_tool", runner)
        assert format_gate.main([]) == 1
        assert len(runner.calls) == 2
        assert "✗ Black failed" in capsys.readouterr().err

    def test_missing_tools_exit_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["black"] = ""
        assert format_gate.main([]) == 2
        assert "not installed" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_tools")
class TestFormatOutput:
    def test_json_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert format_gate.main(["--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "pass"
        assert "format_duration" in payload

    def test_json_suppresses_failure_message(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert format_gate.main(["--json"]) == 1
        assert "✗" not in capsys.readouterr().err

    def test_verbose_announces_each_formatter(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert format_gate.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Running isort..." in out
        assert "Running Black..." in out
        assert "Format execution time:" in out
