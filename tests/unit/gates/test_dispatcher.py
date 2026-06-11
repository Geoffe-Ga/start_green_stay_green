"""Tests for the ``python -m start_green_stay_green.gates`` dispatcher."""

import subprocess
import sys

import pytest

from start_green_stay_green.gates import __main__ as dispatcher
from start_green_stay_green.gates import check_all
from start_green_stay_green.gates import common
from start_green_stay_green.gates import complexity
from start_green_stay_green.gates import coverage
from start_green_stay_green.gates import format as format_gate
from start_green_stay_green.gates import lint
from start_green_stay_green.gates import mutation
from start_green_stay_green.gates import security
from start_green_stay_green.gates import testing
from start_green_stay_green.gates import typecheck

EXPECTED_GATES = {
    "check-all": check_all.main,
    "complexity": complexity.main,
    "coverage": coverage.main,
    "format": format_gate.main,
    "lint": lint.main,
    "mutation": mutation.main,
    "security": security.main,
    "test": testing.main,
    "typecheck": typecheck.main,
}


class TestDispatch:
    def test_gate_registry_is_complete(self) -> None:
        assert dispatcher.GATES == EXPECTED_GATES

    def test_missing_gate_name_exits_2(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert dispatcher.main([]) == 2
        err = capsys.readouterr().err
        assert "Error: missing gate name" in err
        assert "Usage: python -m start_green_stay_green.gates" in err

    def test_unknown_gate_exits_2_and_lists_gates(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert dispatcher.main(["bogus"]) == 2
        err = capsys.readouterr().err
        assert "Error: unknown gate: bogus" in err
        assert "check-all" in err
        assert "mutation" in err

    def test_dispatches_remaining_args_to_gate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        received: list[list[str] | None] = []

        def stub(argv: list[str] | None) -> int:
            received.append(argv)
            return 7

        monkeypatch.setitem(dispatcher.GATES, "lint", stub)
        assert dispatcher.main(["lint", "--check", "--json"]) == 7
        assert received == [["--check", "--json"]]

    def test_reads_sys_argv_when_argv_is_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["gates", "no-such-gate"])
        assert dispatcher.main(None) == 2

    def test_real_module_invocation_unknown_gate(self) -> None:
        result = common.run_tool(
            [sys.executable, "-m", "start_green_stay_green.gates", "bogus"],
            stdout=subprocess.DEVNULL,
        )
        assert result.returncode == 2
        assert "unknown gate" in (result.stderr or "")

    def test_real_module_invocation_version(self) -> None:
        result = common.run_tool(
            [sys.executable, "-m", "start_green_stay_green.gates", "lint", "--version"],
            stdout=subprocess.PIPE,
        )
        assert result.returncode == 0
        assert (result.stdout or "").strip() == "lint version 1.0.0"
