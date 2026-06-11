"""Tests for the complexity gate (port of scripts/complexity.sh)."""

import json

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import complexity
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed

CLEAN_CC = """
2 blocks (classes, functions, methods) analyzed.
Average complexity: A (4.5)
"""

FAILING_CC = """
start_green_stay_green/cli.py
    C 40:0 monster - C (15)

2 blocks (classes, functions, methods) analyzed.
Average complexity: B (9.0)
"""

CLEAN_MI = """
start_green_stay_green/cli.py - A (80.00)
start_green_stay_green/config.py - B (24.00)
"""

FAILING_MI = """
start_green_stay_green/cli.py - A (80.00)
F start_green_stay_green/awful.py - F (3.00)
"""


class TestGradeDetection:
    def test_summary_and_average_lines_do_not_match(self) -> None:
        assert not complexity._grade_failures(CLEAN_CC)

    def test_shown_block_lines_fail(self) -> None:
        # radon 6 only prints blocks of rank B or worse by default, and a
        # shown function/class line starts with its block-type letter
        # (F/C), so any printed block breaches the gate — exactly the
        # historical complexity.sh grep semantics.
        failures = complexity._grade_failures(FAILING_CC)
        assert len(failures) == 1
        assert "monster" in failures[0]

    def test_function_blocks_shown_by_radon_fail(self) -> None:
        assert complexity._grade_failures("    F 67:0 main - B (6)") == [
            "    F 67:0 main - B (6)"
        ]

    def test_words_starting_with_c_do_not_match(self) -> None:
        assert not complexity._grade_failures("Checking things\nComplexity: ok")


@pytest.mark.usefixtures("fake_tools")
class TestComplexityGate:
    def test_all_checks_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=CLEAN_MI),
            completed(0),  # xenon
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main([]) == 0
        out = capsys.readouterr().out
        assert "✓ Cyclomatic Complexity: All functions ≤ 10" in out
        assert "✓ Maintainability Index: All modules ≥ 20" in out
        assert "✓ Xenon: All complexity metrics grade A" in out
        assert "Passed: 3" in out
        assert "✓ All complexity checks passed (MAXIMUM QUALITY)" in out

    def test_cyclomatic_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=FAILING_CC),
            completed(0, stdout=CLEAN_MI),
            completed(0),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main([]) == 1
        captured = capsys.readouterr()
        assert "✗ Cyclomatic Complexity exceeds threshold (max 10)" in captured.err
        assert "monster" in captured.err
        assert "Failed checks:" in captured.out
        assert "MAXIMUM QUALITY STANDARDS:" in captured.out

    def test_maintainability_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=FAILING_MI),
            completed(0),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main([]) == 1
        assert "✗ Maintainability Index below threshold (min 20)" in (
            capsys.readouterr().err
        )

    def test_xenon_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=CLEAN_MI),
            completed(1),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main([]) == 1
        assert "✗ Xenon complexity checks failed (grade must be A)" in (
            capsys.readouterr().err
        )

    def test_missing_xenon_skips_check(
        self,
        fake_tools: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        fake_tools["xenon"] = ""
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=CLEAN_MI),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main([]) == 0
        captured = capsys.readouterr()
        assert "Warning: xenon not installed" in captured.err
        assert "Xenon not available" in captured.out
        assert "Passed: 2" in captured.out

    def test_missing_radon_exits_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["radon"] = ""
        assert complexity.main([]) == 2
        assert "radon not installed" in capsys.readouterr().err

    def test_verbose_echoes_radon_reports(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=CLEAN_MI),
            completed(0),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Average complexity: A (4.5)" in out
        assert "Execution time:" in out

    def test_xenon_invocation_enforces_grade_a(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout=CLEAN_CC),
            completed(0, stdout=CLEAN_MI),
            completed(0),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        complexity.main([])
        xenon_cmd = runner.calls[2]
        assert xenon_cmd[0] == "/fake/xenon"
        for flag in ("--max-absolute", "--max-modules", "--max-average"):
            assert xenon_cmd[xenon_cmd.index(flag) + 1] == "A"


@pytest.mark.usefixtures("fake_tools")
class TestComplexityMetrics:
    def test_averages_parsed(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0, stdout="Average complexity: A (3.45)"),
            completed(0, stdout=CLEAN_MI),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["cyclomatic_avg"] == 3.45
        assert payload["maintainability_avg"] == 52.0

    def test_nulls_when_unparseable(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0, stdout="garbage"))
        monkeypatch.setattr(common, "run_tool", runner)
        assert complexity.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"cyclomatic_avg": None, "maintainability_avg": None}
