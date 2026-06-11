"""Pin the scripts/*.sh wrappers as thin delegates to the gate runner.

The nine converted scripts must contain only venv bootstrap + delegation
(#382): any reappearance of tool invocations in the shell layer would
re-fork the gate logic and break DRY.
"""

from pathlib import Path
import shutil
import subprocess

import pytest

from start_green_stay_green.gates import common
from start_green_stay_green.utils.fs import is_windows

#: script name -> (gate name, legacy tokens that must NOT reappear).
WRAPPERS = {
    "check-all.sh": ("check-all", ["run_check", "lint.sh", "FAILED_CHECKS"]),
    "test.sh": ("test", ["pytest", "PYTEST_ARGS", "flaky_in_ci"]),
    "lint.sh": ("lint", ["ruff"]),
    "format.sh": ("format", ["isort", "black"]),
    "typecheck.sh": ("typecheck", ["mypy"]),
    "security.sh": ("security", ["bandit", "pip-audit", "detect-secrets"]),
    "complexity.sh": ("complexity", ["radon", "xenon"]),
    "coverage.sh": ("coverage", ["pytest", "COVERAGE_THRESHOLD"]),
    "mutation.sh": ("mutation", ["mutmut", "MIN_SCORE", "sqlite3"]),
}


def wrapper_path(script: str) -> Path:
    return common.project_root() / "scripts" / script


def wrapper_text(script: str) -> str:
    return wrapper_path(script).read_text(encoding="utf-8")


class TestDelegation:
    @pytest.mark.parametrize(("script", "spec"), sorted(WRAPPERS.items()))
    def test_wrapper_delegates_to_gate_runner(
        self, script: str, spec: tuple[str, list[str]]
    ) -> None:
        gate, _legacy = spec
        content = wrapper_text(script)
        assert f'python -m start_green_stay_green.gates {gate} "$@"' in content

    @pytest.mark.parametrize(("script", "spec"), sorted(WRAPPERS.items()))
    def test_wrapper_contains_no_legacy_gate_logic(
        self, script: str, spec: tuple[str, list[str]]
    ) -> None:
        _gate, legacy = spec
        content = wrapper_text(script)
        for token in legacy:
            assert (
                token not in content
            ), f"{script} reintroduces legacy logic: {token!r}"

    @pytest.mark.parametrize("script", sorted(WRAPPERS))
    def test_wrapper_bootstraps_venv_via_common_sh(self, script: str) -> None:
        content = wrapper_text(script)
        assert 'source "$SCRIPT_DIR/common.sh"' in content
        assert "ensure_venv || exit 2" in content
        assert "setup_cleanup_trap" in content

    @pytest.mark.parametrize("script", sorted(WRAPPERS))
    def test_wrapper_is_strict_mode_bash(self, script: str) -> None:
        content = wrapper_text(script)
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content

    @pytest.mark.parametrize("script", sorted(WRAPPERS))
    def test_wrapper_is_executable_on_posix(self, script: str) -> None:
        if is_windows():
            pytest.skip("POSIX execute bit does not exist on Windows")
        assert wrapper_path(script).stat().st_mode & 0o111


class TestShellValidity:
    @pytest.mark.parametrize("script", sorted(WRAPPERS))
    def test_bash_syntax(self, script: str) -> None:
        bash = shutil.which("bash")
        if bash is None:
            pytest.skip("bash not available on this platform")
        result = common.run_tool(
            [bash, "-n", str(wrapper_path(script))],
            stdout=subprocess.DEVNULL,
        )
        assert result.returncode == 0, result.stderr

    @pytest.mark.parametrize("script", sorted(WRAPPERS))
    def test_shellcheck(self, script: str) -> None:
        shellcheck = shutil.which("shellcheck")
        if shellcheck is None:
            pytest.skip("shellcheck not available on this platform")
        result = common.run_tool(
            [shellcheck, str(wrapper_path(script))],
            stdout=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stdout
