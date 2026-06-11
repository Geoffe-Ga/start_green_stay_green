"""Tests for the opt-in Windows CI leg in generated workflows (#388).

Covers the final tracer of the windows-compat epic (#378):

- ``render_windows_job`` / ``append_windows_job`` building blocks
- ``CIGenerator(windows_ci=True)`` emitting a parse-valid
  ``quality-windows`` job that runs gates the #386 way
  (``bash scripts/<gate>.sh`` through Git Bash)
- the default-off contract: no Windows content unless opted in, and
  the existing jobs are untouched when opting in
- drift protection: every gate the Windows leg invokes is a script the
  scripts generator actually emits, and every action version the leg
  references is already pinned by the language's base template
- execution: the exact gate scripts the Windows leg invokes run under
  ``bash <path>`` — on this repo's own Windows CI leg (#380) that is
  real Git Bash on windows-latest

Honest scope note: these tests prove the generated Windows leg is
structurally valid and that its gate invocations execute under (Git)
Bash against a freshly generated scaffold. They cannot run GitHub
Actions itself, so "the leg passes on a real windows-latest runner with
the full language toolchain" is demonstrated only to the extent this
repository's own Windows CI executes these tests.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

import pytest
import yaml

from start_green_stay_green.generators import ci_windows
from start_green_stay_green.generators.ci import CIGenerator
from start_green_stay_green.generators.ci import LANGUAGE_CONFIGS
from start_green_stay_green.generators.ci_windows import WINDOWS_CI_LANGUAGES
from start_green_stay_green.generators.ci_windows import WINDOWS_GATES
from start_green_stay_green.generators.ci_windows import WINDOWS_JOB_ID
from start_green_stay_green.generators.ci_windows import append_windows_job
from start_green_stay_green.generators.ci_windows import render_windows_job
from start_green_stay_green.generators.scripts import ScriptConfig
from start_green_stay_green.generators.scripts import ScriptsGenerator

#: Languages CIGenerator supports but the Windows leg deliberately
#: excludes (toolchain not viable on windows-latest — see module docs).
UNSUPPORTED_WINDOWS_LANGUAGES = ("swift", "cpp", "kotlin")


def _generate_content(language: str, *, windows_ci: bool) -> str:
    """Render the deterministic workflow for ``language``."""
    generator = CIGenerator(language=language, project_name="sample-project")
    return generator.generate_workflow(windows_ci=windows_ci).content


def _windows_job(language: str) -> dict[str, Any]:
    """Parse the opt-in workflow and return the Windows job mapping."""
    parsed = yaml.safe_load(_generate_content(language, windows_ci=True))
    job = parsed["jobs"][WINDOWS_JOB_ID]
    assert isinstance(job, dict)
    return job


class TestWindowsLegRegistry:
    """Test the supported-language registry and its gate table."""

    def test_supported_languages_are_a_strict_subset_of_ci_languages(self) -> None:
        """Every Windows-leg language has a CI generator config."""
        assert set(WINDOWS_CI_LANGUAGES) < set(LANGUAGE_CONFIGS)

    def test_excluded_languages_are_not_in_registry(self) -> None:
        """swift/cpp/kotlin are deliberately excluded (see module docs)."""
        for language in UNSUPPORTED_WINDOWS_LANGUAGES:
            assert language not in WINDOWS_CI_LANGUAGES

    def test_every_supported_language_has_gates(self) -> None:
        """The gate table covers exactly the supported languages."""
        assert set(WINDOWS_GATES) == set(WINDOWS_CI_LANGUAGES)
        for gates in WINDOWS_GATES.values():
            assert gates, "every Windows leg must run at least one gate"

    def test_gates_are_shell_scripts(self) -> None:
        """Each configured gate is a ``.sh`` script name."""
        for gates in WINDOWS_GATES.values():
            for gate in gates:
                assert gate.endswith(".sh")


class TestRenderWindowsJob:
    """Test the standalone Windows job renderer."""

    @pytest.mark.parametrize("language", UNSUPPORTED_WINDOWS_LANGUAGES)
    def test_unsupported_language_raises_value_error(self, language: str) -> None:
        """Unsupported languages fail fast with the supported list."""
        with pytest.raises(ValueError, match="python"):
            render_windows_job(language)

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_rendering_is_deterministic(self, language: str) -> None:
        """Two renders produce identical bytes (reproducible generation)."""
        assert render_windows_job(language) == render_windows_job(language)

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_rendered_job_uses_lf_only(self, language: str) -> None:
        """No CR bytes — CRLF would break bash and YAML round-trips."""
        assert "\r" not in render_windows_job(language)

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_rendered_job_never_writes_github_env(self, language: str) -> None:
        """No GITHUB_ENV/GITHUB_PATH writes (env-injection guardrail)."""
        block = render_windows_job(language)
        assert "GITHUB_ENV" not in block
        assert "GITHUB_PATH" not in block

    def test_append_attaches_job_under_jobs(self) -> None:
        """append_windows_job lands the job inside the jobs mapping."""
        base = (
            "name: CI\n"
            "on:\n"
            "  push:\n"
            "jobs:\n"
            "  quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
        )
        merged = yaml.safe_load(append_windows_job(base, "python"))
        assert WINDOWS_JOB_ID in merged["jobs"]
        assert "quality" in merged["jobs"]

    def test_append_wraps_yaml_parse_errors_as_value_error(self) -> None:
        """A workflow the job cannot syntactically extend fails loudly.

        Flow-style ``jobs`` mappings cannot take an appended block key,
        so the merged document does not parse; the YAML error surfaces
        as a ValueError naming the operation.
        """
        base = "name: CI\njobs: {quality: {steps: [{uses: x}]}}\n"
        with pytest.raises(ValueError, match="invalid YAML"):
            append_windows_job(base, "python")

    def test_append_rejects_yaml_where_jobs_is_not_last(self) -> None:
        """If the job cannot attach under jobs, fail loudly, not silently."""
        base = (
            "name: CI\n"
            "jobs:\n"
            "  quality:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "permissions:\n"
            "  contents: read\n"
        )
        with pytest.raises(ValueError, match="jobs"):
            append_windows_job(base, "python")


class TestDefaultOffContract:
    """Test that default output carries no Windows leg at all."""

    @pytest.mark.parametrize("language", sorted(LANGUAGE_CONFIGS))
    def test_default_output_has_no_windows_content(self, language: str) -> None:
        """Without the flag, no Windows job or runner appears."""
        content = _generate_content(language, windows_ci=False)
        assert WINDOWS_JOB_ID not in content
        assert "windows-latest" not in content

    @pytest.mark.parametrize("language", sorted(LANGUAGE_CONFIGS))
    def test_explicit_false_matches_default_byte_for_byte(self, language: str) -> None:
        """``windows_ci=False`` is byte-identical to omitting the flag."""
        default = CIGenerator(
            language=language, project_name="sample-project"
        ).generate_workflow()
        assert _generate_content(language, windows_ci=False) == default.content

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_opt_in_only_adds_the_windows_job(self, language: str) -> None:
        """Opting in leaves every existing job byte-equal (minimal diff)."""
        off = yaml.safe_load(_generate_content(language, windows_ci=False))
        on = yaml.safe_load(_generate_content(language, windows_ci=True))
        on_jobs = dict(on["jobs"])
        on_jobs.pop(WINDOWS_JOB_ID)
        assert on_jobs == off["jobs"]
        for key in off:
            if key == "jobs":
                continue
            assert on[key] == off[key]

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_opt_in_content_is_prefix_extended(self, language: str) -> None:
        """The opt-in output starts with the unmodified default output."""
        off = _generate_content(language, windows_ci=False)
        on = _generate_content(language, windows_ci=True)
        assert on.startswith(off.rstrip("\n"))


class TestOptInWindowsJobStructure:
    """Parse-validate the emitted Windows job for every language."""

    @pytest.mark.parametrize("language", UNSUPPORTED_WINDOWS_LANGUAGES)
    def test_generator_rejects_unsupported_language(self, language: str) -> None:
        """generate_workflow fails fast for legs without Windows support."""
        generator = CIGenerator(language=language, project_name="sample-project")
        with pytest.raises(ValueError, match="windows"):
            generator.generate_workflow(windows_ci=True)

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_workflow_parses_and_validates(self, language: str) -> None:
        """The opt-in workflow is valid per the generator's own checks."""
        generator = CIGenerator(language=language, project_name="sample-project")
        workflow = generator.generate_workflow(windows_ci=True)
        assert workflow.is_valid
        assert workflow.error_message is None

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_job_runs_on_windows_latest(self, language: str) -> None:
        """The leg targets windows-latest."""
        assert _windows_job(language)["runs-on"] == "windows-latest"

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_job_needs_quality_and_is_time_capped(self, language: str) -> None:
        """The leg is gated behind the Linux quality job and time-capped."""
        job = _windows_job(language)
        assert job["needs"] == "quality"
        assert job["timeout-minutes"] == 30

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_first_step_forces_lf_before_checkout(self, language: str) -> None:
        """autocrlf=false is configured before the checkout step runs."""
        steps = _windows_job(language)["steps"]
        assert "core.autocrlf false" in steps[0]["run"]
        assert "core.eol lf" in steps[0]["run"]
        assert steps[1]["uses"].startswith("actions/checkout@")

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_gate_steps_invoke_scripts_through_git_bash(self, language: str) -> None:
        """Every configured gate runs as ``bash scripts/<gate>`` with
        ``shell: bash`` (the #386-documented Windows invocation)."""
        steps = _windows_job(language)["steps"]
        gate_runs = [
            step
            for step in steps
            if str(step.get("run", "")).startswith("bash scripts/")
        ]
        assert [s["run"] for s in gate_runs] == [
            f"bash scripts/{gate}" for gate in WINDOWS_GATES[language]
        ]
        for step in gate_runs:
            assert step["shell"] == "bash"

    def test_python_leg_enables_utf8_mode(self) -> None:
        """The python leg sets PYTHONUTF8=1 (cp1252 vs UTF-8 content)."""
        assert _windows_job("python")["env"]["PYTHONUTF8"] == "1"

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_action_versions_reuse_base_template_pins(self, language: str) -> None:
        """Every action the leg uses is already pinned by the language's
        base template — the leg never invents a new version."""
        base = _generate_content(language, windows_ci=False)
        for step in _windows_job(language)["steps"]:
            uses = step.get("uses")
            if uses is not None:
                assert uses in base, uses

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_gates_match_scripts_the_generator_emits(self, language: str) -> None:
        """Drift protection: each invoked gate is an emitted script."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(language=language, package_name="my_package")
            scripts = ScriptsGenerator(
                Path(tmpdir) / "scripts", config, project_root=Path(tmpdir)
            ).generate()
        for gate in WINDOWS_GATES[language]:
            assert gate in scripts


class TestWindowsGateExecution:
    """Execute the exact gate scripts the Windows leg invokes.

    Mirrors the #386 execution tests: on this repository's own Windows
    CI leg these run under real Git Bash on windows-latest, proving the
    ``bash scripts/<gate>.sh`` invocation the generated workflow emits
    executes against a fresh scaffold. ``--help`` keeps the run
    toolchain-independent; it does not prove a full gate pass with the
    language toolchain installed.
    """

    @pytest.mark.parametrize("language", WINDOWS_CI_LANGUAGES)
    def test_windows_leg_gate_invocations_execute_under_bash(
        self, language: str
    ) -> None:
        """``bash <gate> --help`` exits 0 for every invoked gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ScriptConfig(language=language, package_name="my_package")
            scripts = ScriptsGenerator(
                Path(tmpdir) / "scripts", config, project_root=Path(tmpdir)
            ).generate()

            bash = shutil.which("bash")
            assert bash is not None, "bash not found on PATH"
            for gate in WINDOWS_GATES[language]:
                result = subprocess.run(  # noqa: S603  # Issue #388: bash on generated content, no untrusted input
                    [bash, str(scripts[gate]), "--help"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                assert result.returncode == 0, result.stderr
                assert "Usage" in result.stdout


class TestModuleDocumentation:
    """Test the honesty notes the module must carry."""

    def test_module_documents_excluded_languages(self) -> None:
        """The module docstring explains every exclusion."""
        doc = ci_windows.__doc__
        assert doc is not None
        for language in UNSUPPORTED_WINDOWS_LANGUAGES:
            assert language in doc
