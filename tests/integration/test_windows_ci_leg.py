"""Integration tests for the opt-in Windows CI leg (#388).

Generates a real sample project with ``green init --windows-ci`` and
then executes, on the current machine, the exact gate invocations the
generated ``quality-windows`` job declares (``bash scripts/<gate>.sh``).

What this proves — and what it does not:

* On this repository's own Windows CI leg (#380), these tests run on a
  real ``windows-latest`` runner under real Git Bash with the python
  toolchain (ruff, pytest) installed — so a passing run demonstrates
  that a freshly generated python sample passes the same gate commands
  its generated Windows CI job would run, on the same runner image and
  shell that job targets.
* It does NOT execute GitHub Actions itself: runner provisioning steps
  (checkout, setup-python, dependency install) are exercised only by
  this repository's own workflow, not the generated one. Structural
  validity of the generated job is covered by the unit suite
  (``tests/unit/generators/test_ci_windows.py``).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import TYPE_CHECKING

from typer.testing import CliRunner
import yaml

from start_green_stay_green.cli import app
from start_green_stay_green.generators.ci_windows import WINDOWS_GATES
from start_green_stay_green.generators.ci_windows import WINDOWS_JOB_ID

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _init_python_project(tmp_path: Path) -> Path:
    """Scaffold a python sample with the Windows leg opted in."""
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "init",
            "--project-name",
            "sample-windows",
            "-l",
            "python",
            "-o",
            str(tmp_path),
            "--offline",
            "--no-interactive",
            "--windows-ci",
        ],
    )
    assert result.exit_code == 0, result.output
    return tmp_path / "sample-windows"


def _windows_gate_commands(project: Path) -> list[str]:
    """Extract the Windows job's gate commands from the generated ci.yml."""
    ci_file = project / ".github" / "workflows" / "ci.yml"
    parsed = yaml.safe_load(ci_file.read_text(encoding="utf-8"))
    job = parsed["jobs"][WINDOWS_JOB_ID]
    return [
        step["run"]
        for step in job["steps"]
        if str(step.get("run", "")).startswith("bash scripts/")
    ]


class TestGeneratedSamplePassesWindowsGates:
    """Run the generated sample's Windows gate commands for real."""

    def test_windows_leg_gates_pass_on_fresh_python_sample(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every gate the generated Windows job invokes exits 0.

        The commands executed here are read out of the generated
        workflow itself (not re-stated), so the test cannot drift from
        what the Windows leg actually runs. Requires ruff and pytest on
        PATH — both ship in this repository's requirements-dev.txt, on
        every CI leg including windows-latest.
        """
        project = _init_python_project(tmp_path)
        commands = _windows_gate_commands(project)
        assert commands == [f"bash scripts/{gate}" for gate in WINDOWS_GATES["python"]]

        bash = shutil.which("bash")
        assert bash is not None, "bash not found on PATH"
        # The generated job runs from the project root; mirror that.
        monkeypatch.chdir(project)
        for command in commands:
            script = command.removeprefix("bash ")
            result = subprocess.run(  # noqa: S603  # Issue #388: bash on generated content, no untrusted input
                [bash, script],
                capture_output=True,
                text=True,
                check=False,
            )
            assert (
                result.returncode == 0
            ), f"{command} failed:\n{result.stdout}\n{result.stderr}"
