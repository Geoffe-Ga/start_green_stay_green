"""Tests for the shared gate-runner plumbing."""

from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest

from start_green_stay_green.gates import common


class TestThresholds:
    def test_coverage_threshold_is_90(self) -> None:
        assert common.COVERAGE_THRESHOLD == 90

    def test_coverage_threshold_matches_pyproject_fail_under(self) -> None:
        pyproject = (common.project_root() / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert f"fail_under = {common.COVERAGE_THRESHOLD}" in pyproject

    def test_mutation_min_score_is_80(self) -> None:
        assert common.MUTATION_MIN_SCORE == 80

    def test_max_cyclomatic_complexity_is_10(self) -> None:
        assert common.MAX_CYCLOMATIC_COMPLEXITY == 10

    def test_max_complexity_matches_pyproject_mccabe(self) -> None:
        pyproject = (common.project_root() / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        assert f"max-complexity = {common.MAX_CYCLOMATIC_COMPLEXITY}" in pyproject

    def test_min_maintainability_index_is_20(self) -> None:
        assert common.MIN_MAINTAINABILITY_INDEX == 20

    def test_max_complexity_grade_is_a(self) -> None:
        assert common.MAX_COMPLEXITY_GRADE == "A"

    def test_gate_version_matches_scripts(self) -> None:
        assert common.GATE_VERSION == "1.0.0"


class TestProjectRoot:
    def test_project_root_contains_pyproject(self) -> None:
        assert (common.project_root() / "pyproject.toml").is_file()

    def test_project_root_contains_package(self) -> None:
        assert (common.project_root() / "start_green_stay_green").is_dir()

    def test_enter_project_root_changes_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        common.enter_project_root()
        assert Path.cwd() == common.project_root()


class TestResolveTool:
    def test_resolves_tool_next_to_interpreter(self) -> None:
        resolved = common.resolve_tool("pytest")
        assert resolved is not None
        assert Path(resolved).parent == Path(sys.executable).parent

    def test_missing_tool_returns_none(self) -> None:
        assert common.resolve_tool("definitely-not-a-real-tool-382") is None

    def test_windows_layout_uses_exe_suffix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "ruff.exe").write_text("")
        monkeypatch.setattr(common, "is_windows", lambda: True)
        monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
        assert common.resolve_tool("ruff") == str(tmp_path / "ruff.exe")

    def test_falls_back_to_which(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _name: "/from/which")
        assert common.resolve_tool("not-next-to-interpreter") == "/from/which"


class TestRunTool:
    def test_captures_stderr_by_default(self) -> None:
        result = common.run_tool(
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('boom'); sys.exit(3)",
            ]
        )
        assert result.returncode == 3
        assert result.stderr == "boom"
        assert result.stdout is None

    def test_captures_stdout_when_piped(self) -> None:
        result = common.run_tool(
            [sys.executable, "-c", "print('hello')"],
            stdout=subprocess.PIPE,
        )
        assert result.returncode == 0
        assert result.stdout == "hello\n"


class TestStreamTool:
    def test_streams_and_captures_combined_output(
        self, capfd: pytest.CaptureFixture[str]
    ) -> None:
        code = "import sys; print('out'); sys.stderr.write('err\\n'); sys.exit(5)"
        returncode, output = common.stream_tool([sys.executable, "-c", code])
        assert returncode == 5
        assert "out" in output
        assert "err" in output
        captured = capfd.readouterr()
        assert "out" in captured.out


class TestElapsedSeconds:
    def test_zero_for_fresh_stamp(self) -> None:
        assert common.elapsed_seconds(time.monotonic()) == 0

    def test_truncates_to_whole_seconds(self) -> None:
        assert common.elapsed_seconds(time.monotonic() - 5.2) == 5


class TestGateParser:
    def test_version_flag_prints_script_style_version(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        parser = common.gate_parser("lint", "desc")
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["--version"])
        assert excinfo.value.code == 0
        assert capsys.readouterr().out.strip() == "lint version 1.0.0"

    def test_unknown_option_exits_2(self) -> None:
        parser = common.gate_parser("lint", "desc")
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["--bogus"])
        assert excinfo.value.code == 2

    def test_help_exits_0(self) -> None:
        parser = common.gate_parser("lint", "desc")
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["--help"])
        assert excinfo.value.code == 0

    def test_version_flag_can_be_disabled(self) -> None:
        parser = common.gate_parser("mutation", "desc", version_flag=False)
        with pytest.raises(SystemExit) as excinfo:
            parser.parse_args(["--version"])
        assert excinfo.value.code == 2

    def test_verbose_defaults_false(self) -> None:
        parser = common.gate_parser("lint", "desc")
        assert parser.parse_args([]).verbose is False

    def test_verbose_flag(self) -> None:
        parser = common.gate_parser("lint", "desc")
        assert parser.parse_args(["--verbose"]).verbose is True


class TestConfigureUtf8Output:
    def test_ignores_streams_without_reconfigure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class Plain:
            pass

        monkeypatch.setattr(sys, "stdout", Plain())
        monkeypatch.setattr(sys, "stderr", Plain())
        common.configure_utf8_output()  # must not raise

    def test_reconfigures_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[dict[str, str]] = []

        class Reconfigurable:
            def reconfigure(self, **kwargs: str) -> None:
                calls.append(kwargs)

        monkeypatch.setattr(sys, "stdout", Reconfigurable())
        monkeypatch.setattr(sys, "stderr", Reconfigurable())
        common.configure_utf8_output()
        assert calls == [
            {"encoding": "utf-8", "errors": "replace"},
            {"encoding": "utf-8", "errors": "replace"},
        ]
