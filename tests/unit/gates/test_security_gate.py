"""Tests for the security gate (port of scripts/security.sh)."""

import json
from pathlib import Path

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.gates import security
from tests.unit.gates.conftest import FakeRunner
from tests.unit.gates.conftest import completed


@pytest.mark.usefixtures("fake_tools")
class TestBandit:
    def test_pass_runs_bandit_then_pip_audit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert security.main([]) == 0
        out = capsys.readouterr().out
        assert "=== Security Checks (Bandit) ===" in out
        assert "=== Security Checks (pip-audit) ===" in out
        assert "✓ Security checks passed" in out
        assert runner.calls[0] == ["/fake/bandit", "-r", "start_green_stay_green/"]

    def test_bandit_failure_skips_pip_audit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(completed(1))
        monkeypatch.setattr(common, "run_tool", runner)
        assert security.main([]) == 1
        assert len(runner.calls) == 1
        assert "✗ Bandit found issues" in capsys.readouterr().err

    def test_missing_tools_exit_2(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["pip-audit"] = ""
        assert security.main([]) == 2
        assert "not installed" in capsys.readouterr().err


@pytest.mark.usefixtures("fake_tools")
class TestPipAudit:
    def test_pip_audit_uses_osv_and_skip_editable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        security.main([])
        audit_cmd = runner.calls[1]
        assert audit_cmd[0] == "/fake/pip-audit"
        assert "--vulnerability-service" in audit_cmd
        assert audit_cmd[audit_cmd.index("--vulnerability-service") + 1] == "osv"
        assert "--skip-editable" in audit_cmd

    def test_retry_after_transient_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),  # bandit
            completed(1, stderr="osv 503\n"),  # first audit
            completed(0),  # retry
        )
        monkeypatch.setattr(common, "run_tool", runner)
        delays: list[int] = []
        monkeypatch.setattr(security, "sleep", delays.append)
        assert security.main([]) == 0
        assert delays == [10]
        err = capsys.readouterr().err
        assert "retrying in 10s" in err
        assert "osv 503" in err

    def test_both_attempts_failing_exits_1_with_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),
            completed(1, stderr="first\n"),
            completed(1, stderr="second\n"),
        )
        monkeypatch.setattr(common, "run_tool", runner)
        monkeypatch.setattr(security, "sleep", lambda _s: None)
        assert security.main([]) == 1
        err = capsys.readouterr().err
        assert "✗ pip-audit failed; stderr follows:" in err
        assert "second" in err

    def test_ignore_file_flags_are_passed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        ignore = tmp_path / security.IGNORE_FILE
        ignore.write_text(
            "# full-line comment\n"
            "GHSA-aaaa-bbbb  # tracked in #999\n"
            "\n"
            "PYSEC-2026-1\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(common, "project_root", lambda: tmp_path)
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        security.main([])
        audit_cmd = runner.calls[1]
        assert audit_cmd.count("--ignore-vuln") == 2
        assert "GHSA-aaaa-bbbb" in audit_cmd
        assert "PYSEC-2026-1" in audit_cmd

    def test_load_ignore_args_missing_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(common, "project_root", lambda: tmp_path)
        assert not security.load_ignore_args()


@pytest.mark.usefixtures("fake_tools")
class TestFullScan:
    def test_full_runs_detect_secrets_and_ignores_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        runner = FakeRunner(
            completed(0),  # bandit
            completed(0),  # pip-audit
            completed(1),  # detect-secrets fails -> still warn-first
        )
        monkeypatch.setattr(common, "run_tool", runner)
        assert security.main(["--full"]) == 0
        assert runner.calls[2] == ["/fake/detect-secrets", "scan", "."]
        assert "=== Comprehensive Security Scan ===" in capsys.readouterr().out

    def test_full_with_missing_detect_secrets_still_passes(
        self, fake_tools: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_tools["detect-secrets"] = ""
        runner = FakeRunner(completed(0))
        monkeypatch.setattr(common, "run_tool", runner)
        assert security.main(["--full"]) == 0
        assert len(runner.calls) == 2

    def test_verbose_prints_progress(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0)))
        assert security.main(["--verbose"]) == 0
        out = capsys.readouterr().out
        assert "Running Bandit security scanner..." in out
        assert "Running pip-audit dependency checker..." in out
        assert "Security check execution time:" in out


@pytest.mark.usefixtures("fake_tools")
class TestSecurityMetrics:
    def test_unknown_when_bandit_missing(
        self, fake_tools: dict[str, str], capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_tools["bandit"] = ""
        assert security.main(["--metrics"]) == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload == {"bandit_issues": None, "status": "unknown"}

    def test_unknown_when_output_empty(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(common, "run_tool", FakeRunner(completed(0, stdout="  ")))
        assert security.main(["--metrics"]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == "unknown"

    def test_unknown_when_output_unparseable(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(0, stdout="not json"))
        )
        assert security.main(["--metrics"]) == 0
        assert json.loads(capsys.readouterr().out)["status"] == "unknown"

    def test_zero_issues_pass(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = json.dumps({"results": []})
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(0, stdout=payload))
        )
        assert security.main(["--metrics"]) == 0
        assert json.loads(capsys.readouterr().out) == {
            "bandit_issues": 0,
            "status": "pass",
        }

    def test_issue_count_fail(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        payload = json.dumps({"results": [{"id": 1}, {"id": 2}, {"id": 3}]})
        monkeypatch.setattr(
            common, "run_tool", FakeRunner(completed(1, stdout=payload))
        )
        assert security.main(["--metrics"]) == 0
        assert json.loads(capsys.readouterr().out) == {
            "bandit_issues": 3,
            "status": "fail",
        }
