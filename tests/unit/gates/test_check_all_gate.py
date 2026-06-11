"""Tests for the check-all gate (port of scripts/check-all.sh)."""

import json
import subprocess
import sys
from typing import Any
from typing import Self

import pytest

from start_green_stay_green.gates import check_all

EXPECTED_SEQUENCE = [
    ("Linting", "lint", ("--check",)),
    ("Formatting", "format", ("--check",)),
    ("Type checking", "typecheck", ()),
    ("Security checks", "security", ()),
    ("Complexity analysis", "complexity", ()),
    ("Unit tests", "test", ("--unit",)),
    ("Coverage report", "coverage", ()),
]


class FakeRun:
    """Recording stand-in for subprocess.run in the sequential path."""

    def __init__(self, failures: tuple[str, ...] | set[str] = ()) -> None:
        self.failures = set(failures)
        self.commands: list[list[str]] = []
        self.kwargs: list[dict[str, Any]] = []

    def __call__(
        self, cmd: list[str], **kwargs: Any
    ) -> subprocess.CompletedProcess[bytes]:
        self.commands.append(cmd)
        self.kwargs.append(kwargs)
        gate = cmd[cmd.index("start_green_stay_green.gates") + 1]
        returncode = 1 if gate in self.failures else 0
        return subprocess.CompletedProcess(args=cmd, returncode=returncode)


class DummyProc:
    """Context-manager Popen stand-in for the parallel path."""

    def __init__(self, returncode: int) -> None:
        self.returncode = returncode

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def wait(self) -> int:
        return self.returncode


class TestGateCommand:
    def test_builds_module_invocation(self) -> None:
        cmd = check_all.gate_command("lint", ("--check",), verbose=False)
        assert cmd == [
            sys.executable,
            "-m",
            "start_green_stay_green.gates",
            "lint",
            "--check",
        ]

    def test_verbose_is_forwarded(self) -> None:
        cmd = check_all.gate_command("test", ("--unit",), verbose=True)
        assert cmd[-1] == "--verbose"


class TestSequentialRun:
    def test_all_checks_run_in_order(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeRun()
        monkeypatch.setattr(subprocess, "run", fake)
        assert check_all.main([]) == 0
        gates = [
            cmd[cmd.index("start_green_stay_green.gates") + 1 :]
            for cmd in fake.commands
        ]
        assert gates == [[gate, *args] for _, gate, args in EXPECTED_SEQUENCE]
        out = capsys.readouterr().out
        assert "=== Running All Quality Checks ===" in out
        for name, _, _ in EXPECTED_SEQUENCE:
            assert f"Running: {name}" in out
            assert f"✓ {name} passed" in out
        assert "Passed: 7" in out
        assert "✓ All quality checks passed!" in out

    def test_failure_reported_and_exits_1(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeRun(failures={"typecheck"})
        monkeypatch.setattr(subprocess, "run", fake)
        assert check_all.main([]) == 1
        captured = capsys.readouterr()
        assert "✗ Type checking failed" in captured.err
        assert "Failed: 1" in captured.out
        assert "Failed checks:" in captured.out
        assert "  ✗ Type checking" in captured.out
        assert "All quality checks passed" not in captured.out

    def test_verbose_propagates_to_children(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake = FakeRun()
        monkeypatch.setattr(subprocess, "run", fake)
        assert check_all.main(["--verbose"]) == 0
        assert all(cmd[-1] == "--verbose" for cmd in fake.commands)
        assert "Execution time:" in capsys.readouterr().out


class TestJsonOutput:
    def test_json_envelope_on_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(subprocess, "run", FakeRun())
        assert check_all.main(["--json"]) == 0
        lines = capsys.readouterr().out.strip().splitlines()
        payload = json.loads(lines[0])
        assert payload["status"] == "pass"
        assert payload["passed"] == 7
        assert payload["failed"] == 0
        assert set(payload["checks"]) == {name for name, _, _ in EXPECTED_SEQUENCE}
        # check-all.sh parity: the final ✓ line prints even in JSON mode.
        assert lines[-1] == "✓ All quality checks passed!"

    def test_json_envelope_on_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(subprocess, "run", FakeRun(failures={"lint", "coverage"}))
        assert check_all.main(["--json"]) == 1
        payload = json.loads(capsys.readouterr().out.strip())
        assert payload["status"] == "fail"
        assert payload["failed"] == 2
        assert payload["checks"]["Linting"] == {"status": "fail"}
        assert payload["checks"]["Formatting"] == {"status": "pass"}


class TestParallelRun:
    def test_parallel_launches_independent_checks(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        launched: list[tuple[list[str], dict[str, Any]]] = []

        def fake_popen(cmd: list[str], **kwargs: Any) -> DummyProc:
            launched.append((cmd, kwargs))
            return DummyProc(0)

        monkeypatch.setattr(subprocess, "Popen", fake_popen)
        sequential = FakeRun()
        monkeypatch.setattr(subprocess, "run", sequential)
        assert check_all.main(["--parallel"]) == 0
        parallel_gates = [
            cmd[cmd.index("start_green_stay_green.gates") + 1]
            for cmd, _kwargs in launched
        ]
        assert parallel_gates == [
            "lint",
            "format",
            "typecheck",
            "security",
            "complexity",
        ]
        sequential_gates = [
            cmd[cmd.index("start_green_stay_green.gates") + 1]
            for cmd in sequential.commands
        ]
        assert sequential_gates == ["test", "coverage"]
        assert "Running checks in parallel mode..." in capsys.readouterr().out

    def test_parallel_failure_detected(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        codes = iter([0, 1, 0, 0, 0])

        def fake_popen(cmd: list[str], **kwargs: Any) -> DummyProc:
            del cmd, kwargs
            return DummyProc(next(codes))

        monkeypatch.setattr(subprocess, "Popen", fake_popen)
        monkeypatch.setattr(subprocess, "run", FakeRun())
        assert check_all.main(["--parallel"]) == 1
        captured = capsys.readouterr()
        assert "✗ Formatting failed" in captured.err
        assert "Failed: 1" in captured.out
