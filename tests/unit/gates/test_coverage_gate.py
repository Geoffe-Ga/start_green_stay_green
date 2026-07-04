"""Tests for the coverage gate (port of scripts/coverage.sh)."""

import json
from pathlib import Path

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import coverage
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed

REPORT_OK = """
Name                Stmts   Miss Branch BrPart    Cover   Missing
---------------------------------------------------------------
pkg/a.py              100      1     20      1   97.50%   12
---------------------------------------------------------------
TOTAL                 100      1     20      1   97.50%
"""

REPORT_LOW = REPORT_OK.replace("97.50%", "85.00%")


@pytest.mark.usefixtures("fake_tools")
class TestParseTotalPercent:
    def test_parses_total_row(self) -> None:
        assert coverage._parse_total_percent(REPORT_OK) == 97.5

    def test_missing_total_returns_none(self) -> None:
        assert coverage._parse_total_percent("no totals here") is None

    def test_unparseable_percent_returns_none(self) -> None:
        assert coverage._parse_total_percent("TOTAL a b junk") is None


@pytest.mark.usefixtures("fake_tools")
class TestCheckThreshold:
    def test_meets_threshold(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(0, stdout=REPORT_OK))
        )
        assert coverage.check_threshold() == 0

    def test_below_threshold_fails(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(0, stdout=REPORT_LOW))
        )
        assert coverage.check_threshold() == 1
        assert "below threshold of 90%" in capsys.readouterr().err

    def test_unparseable_report_fails_loudly(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(0, stdout="garbage"))
        )
        assert coverage.check_threshold() == 2
        assert "Could not parse coverage report" in capsys.readouterr().err

    def test_missing_coverage_tool_skips(self, fake_tools: dict[str, str]) -> None:
        fake_tools["coverage"] = ""
        assert coverage.check_threshold() == 0


@pytest.mark.usefixtures("fake_tools")
class TestCoverageGate:
    def test_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),  # pytest
            completed(0, stdout=REPORT_OK),  # coverage report
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert coverage.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Generating Coverage Report ===" in out
        assert "✓ Coverage report generated" in out
        pytest_cmd = runner.calls[0]
        assert pytest_cmd[0] == "/fake/pytest"
        assert "not integration and not e2e" in pytest_cmd
        assert "--cov=start_green_stay_green" in pytest_cmd

    def test_html_mode(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),
            completed(0, stdout=REPORT_OK),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert coverage.main(["--html"]) == 0
        out = capsys.readouterr().out
        assert "Generating HTML coverage report..." in out
        assert "✓ HTML coverage report generated in htmlcov/index.html" in out
        assert "--cov-report=html" in runner.calls[0]

    def test_pytest_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert coverage.main([]) == 1
        assert "✗ Coverage generation failed" in capsys.readouterr().err

    def test_below_threshold_fails_gate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = FakeRunner(
            completed(0),
            completed(0, stdout=REPORT_LOW),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert coverage.main([]) == 1

    def test_missing_pytest_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["pytest"] = ""
        assert coverage.main([]) == 2
        assert "pytest is not installed" in capsys.readouterr().err

    def test_verbose_prints_timings(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),
            completed(0, stdout=REPORT_OK),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert coverage.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Running pytest with coverage..." in out
        assert "Coverage check completed in" in out
        assert "Coverage execution time:" in out


@pytest.mark.usefixtures("fake_tools")
class TestCoverageMetrics:
    def test_metrics_from_coverage_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(common, "project_root", lambda: tmp_path)
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        (tmp_path / "coverage.json").write_text(
            json.dumps(
                {
                    "totals": {
                        "percent_covered": 96.789,
                        "num_branches": 200,
                        "covered_branches": 150,
                    }
                }
            ),
            encoding="utf-8",
        )
        assert coverage.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"coverage_pct": 96.79, "branch_coverage_pct": 75.0}

    def test_metrics_without_branches(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(common, "project_root", lambda: tmp_path)
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        (tmp_path / "coverage.json").write_text(
            json.dumps({"totals": {"percent_covered": 91.0}}),
            encoding="utf-8",
        )
        assert coverage.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"coverage_pct": 91.0, "branch_coverage_pct": None}

    def test_metrics_unknown_when_report_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(common, "project_root", lambda: tmp_path)
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(1)))
        assert coverage.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["status"] == "unknown"
        assert payload["coverage_pct"] is None
