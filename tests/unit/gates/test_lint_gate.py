"""Tests for the lint gate (port of scripts/lint.sh)."""

import json

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import lint
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed


@pytest.mark.usefixtures("fake_tools")
class TestLintCheck:
    def test_passing_check(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert lint.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Linting (Ruff) ===" in out
        assert "✓ Linting checks passed" in out
        assert runner.calls == [["/fake/ruff", "check", "."]]

    def test_check_flag_is_accepted_noop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert lint.main(["--check"]) == 0
        assert runner.calls == [["/fake/ruff", "check", "."]]

    def test_fix_mode_appends_fix_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert lint.main(["--fix"]) == 0
        assert runner.calls == [["/fake/ruff", "check", ".", "--fix"]]

    def test_failure_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert lint.main([]) == 1
        assert "✗ Linting checks failed" in capsys.readouterr().err

    def test_missing_ruff_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["ruff"] = ""
        assert lint.main([]) == 2
        assert "ruff is not installed" in capsys.readouterr().err

    def test_unknown_option_exits_2(self) -> None:
        with pytest.raises(SystemExit) as excinfo:
            lint.main(["--bogus"])
        assert excinfo.value.code == 2

    def test_verbose_prints_progress_and_timing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert lint.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Checking for linting issues..." in out
        assert "Lint execution time:" in out

    def test_verbose_fix_message(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert lint.main(["--verbose", "--fix"]) == 0
        assert "Fixing linting issues..." in capsys.readouterr().out


@pytest.mark.usefixtures("fake_tools")
class TestLintJson:
    def test_json_pass_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert lint.main(["--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "pass"
        assert payload["duration_seconds"] >= 0
        assert payload["lint_duration"] >= 0

    def test_json_fail_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert lint.main(["--json"]) == 1
        assert json.loads(capsys.readouterr().out)["status"] == "fail"

    def test_json_suppresses_headers(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        lint.main(["--json"])
        assert "=== Linting" not in capsys.readouterr().out


@pytest.mark.usefixtures("fake_tools")
class TestLintMetrics:
    def test_violations_counted_from_ruff_json(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ruff_json = json.dumps([{"code": "E501"}, {"code": "F401"}])
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(1, stdout=ruff_json))
        )
        assert lint.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"violations": 2, "status": "fail"}

    def test_clean_run_reports_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0, stdout="[]")))
        assert lint.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"violations": 0, "status": "pass"}

    def test_unparseable_output_defaults_to_zero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(2, stdout="not json"))
        )
        assert lint.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"violations": 0, "status": "pass"}

    def test_metrics_requests_json_output_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner = FakeRunner(completed(0, stdout="[]"))
        monkeypatch.setattr(common, "run_tool", runner)
        lint.main(["--metrics"])
        assert runner.calls == [["/fake/ruff", "check", ".", "--output-format=json"]]


class TestLintRealInvocation:
    def test_real_metrics_run_emits_valid_json(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Cheap real ruff invocation pinning the end-to-end metrics path."""
        assert lint.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert set(payload) == {"violations", "status"}
