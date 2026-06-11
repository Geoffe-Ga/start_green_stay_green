"""Tests for the test gate (port of scripts/test.sh)."""

import argparse
import json

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import mutation
from start_green_stay_green.gates import testing
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed


def make_args(**overrides: object) -> argparse.Namespace:
    defaults = {
        "test_type": "unit",
        "ci": False,
        "coverage": False,
        "mutation": False,
        "json_output": False,
        "metrics": False,
        "verbose": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


@pytest.mark.usefixtures("fake_tools")
class TestMarkerExpressions:
    def test_unit_default(self) -> None:
        args = testing.build_pytest_args(make_args(), None)
        assert args[:3] == ["-v", "-m", "not integration and not e2e"]

    def test_unit_ci(self) -> None:
        args = testing.build_pytest_args(make_args(ci=True), None)
        assert args[2] == "not integration and not e2e and not flaky_in_ci"

    def test_integration(self) -> None:
        args = testing.build_pytest_args(make_args(test_type="integration"), None)
        assert args[2] == "integration"

    def test_integration_ci(self) -> None:
        args = testing.build_pytest_args(
            make_args(test_type="integration", ci=True), None
        )
        assert args[2] == "integration and not flaky_in_ci"

    def test_e2e_ci(self) -> None:
        args = testing.build_pytest_args(make_args(test_type="e2e", ci=True), None)
        assert args[2] == "e2e and not flaky_in_ci"

    def test_all_has_no_marker(self) -> None:
        args = testing.build_pytest_args(make_args(test_type="all"), None)
        assert "-m" not in args

    def test_all_ci_excludes_flaky(self) -> None:
        args = testing.build_pytest_args(make_args(test_type="all", ci=True), None)
        assert args[2] == "not flaky_in_ci"

    def test_coverage_flags_pin_threshold(self) -> None:
        args = testing.build_pytest_args(make_args(coverage=True), None)
        assert "--cov=start_green_stay_green" in args
        assert "--cov-branch" in args
        assert f"--cov-fail-under={common.COVERAGE_THRESHOLD}" in args
        assert "--cov-fail-under=90" in args

    def test_json_report_flags(self) -> None:
        args = testing.build_pytest_args(
            make_args(json_output=True), "pytest-report.json"
        )
        assert "--json-report" in args
        assert "--json-report-file=pytest-report.json" in args


@pytest.mark.usefixtures("fake_tools")
class TestSummaryParsing:
    def test_all_passed(self) -> None:
        summary = testing.parse_pytest_summary("250 passed in 12.34s")
        assert summary == {
            "tests_total": 250,
            "tests_passed": 250,
            "tests_failed": 0,
            "tests_skipped": 0,
            "duration_seconds": 12.34,
            "status": "pass",
        }

    def test_failures_reported(self) -> None:
        summary = testing.parse_pytest_summary("2 failed, 8 passed in 3.5s")
        assert summary["tests_total"] == 10
        assert summary["tests_failed"] == 2
        assert summary["status"] == "fail"

    def test_skips_counted(self) -> None:
        summary = testing.parse_pytest_summary("4 skipped in 1.0s")
        assert summary["tests_total"] == 4
        assert summary["tests_skipped"] == 4
        assert summary["status"] == "pass"

    def test_empty_output_is_unknown(self) -> None:
        summary = testing.parse_pytest_summary("")
        assert summary["status"] == "unknown"
        assert summary["tests_total"] == 0

    def test_no_tests_collected_is_unknown(self) -> None:
        summary = testing.parse_pytest_summary("no tests ran in 0.01s")
        assert summary["status"] == "unknown"

    def test_missing_duration_defaults_to_zero(self) -> None:
        summary = testing.parse_pytest_summary("3 passed")
        assert summary["duration_seconds"] == 0.0


@pytest.mark.usefixtures("fake_tools")
class TestTestGateRun:
    def test_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert testing.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Running Unit Tests ===" in out
        assert "✓ Tests passed" in out
        cmd = runner.calls[0]
        assert cmd[0] == "/fake/pytest"
        assert cmd[1] == "-v"
        assert cmd[-1] == "tests/"

    def test_ci_mode_announced(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert testing.main(["--ci"]) == 0
        assert "CI mode: Skipping flaky_in_ci tests" in capsys.readouterr().out

    def test_coverage_announced(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert testing.main(["--coverage"]) == 0
        assert "Coverage enabled" in capsys.readouterr().out

    def test_failure_surfaces_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(1, stderr="KABOOM\n"))
        )
        assert testing.main([]) == 1
        err = capsys.readouterr().err
        assert "✗ Tests failed" in err
        assert "=== Pytest stderr output ===" in err
        assert "KABOOM" in err

    def test_missing_pytest_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["pytest"] = ""
        assert testing.main([]) == 2
        assert "pytest is not installed" in capsys.readouterr().err

    def test_json_pass_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert testing.main(["--json"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "pass"
        assert "test_duration" in payload

    def test_json_fail_envelope(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert testing.main(["--json"]) == 1
        assert json.loads(capsys.readouterr().out)["status"] == "fail"

    def test_verbose_echoes_pytest_args(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert testing.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Running pytest with args: -v -m" in out
        assert "Test execution time:" in out

    def test_last_test_type_flag_wins(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert testing.main(["--unit", "--integration"]) == 0
        assert "=== Running Integration Tests ===" in capsys.readouterr().out


@pytest.mark.usefixtures("fake_tools")
class TestMutationChain:
    def test_mutation_failure_fails_gate(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        monkeypatch.setattr(mutation, "main", lambda _argv: 1)
        assert testing.main(["--mutation"]) == 1
        captured = capsys.readouterr()
        assert "=== Running Mutation Tests ===" in captured.out
        assert "✗ Mutation tests failed" in captured.err

    def test_mutation_pass_keeps_gate_green(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        calls: list[list[str] | None] = []

        def fake_mutation(argv: list[str] | None) -> int:
            calls.append(argv)
            return 0

        monkeypatch.setattr(mutation, "main", fake_mutation)
        assert testing.main(["--mutation"]) == 0
        assert calls == [[]]

    def test_no_mutation_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        monkeypatch.setattr(
            mutation,
            "main",
            lambda _argv: pytest.fail("mutation gate must not run without --mutation"),
        )
        assert testing.main([]) == 0


@pytest.mark.usefixtures("fake_tools")
class TestTestMetrics:
    def test_metrics_parses_pytest_output(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0, stdout="7 passed in 2.5s"))
        monkeypatch.setattr(common, "run_tool", runner)
        assert testing.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["tests_passed"] == 7
        assert payload["status"] == "pass"
        cmd = runner.calls[0]
        assert "-o" in cmd
        assert "addopts=" in cmd
