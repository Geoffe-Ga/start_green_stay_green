"""Tests for reference assets (Issue #22: Copy SGSG Assets).

This test file verifies that all required reference assets exist
and are properly structured for use by generators.
"""

from pathlib import Path
from typing import ClassVar

import pytest
import yaml


# Fixture for reference directory
@pytest.fixture
def reference_dir() -> Path:
    """Return path to reference directory."""
    return Path(__file__).parent.parent.parent.parent / "reference"


class TestCIReferences:
    """Test CI workflow references exist for all supported languages."""

    @pytest.fixture
    def ci_dir(self, reference_dir: Path) -> Path:
        """Return path to CI directory."""
        return reference_dir / "ci"

    def test_ci_directory_exists(self, ci_dir: Path) -> None:
        """Test that ci/ directory exists."""
        assert ci_dir.exists()
        assert ci_dir.is_dir()

    def test_all_language_ci_workflows_exist(self, ci_dir: Path) -> None:
        """Test that CI workflows exist for all 11 supported languages."""
        required_workflows = [
            "python.yml",
            "typescript.yml",
            "go.yml",
            "rust.yml",
            "java.yml",
            "csharp.yml",
            "swift.yml",
            "ruby.yml",
            "php.yml",
            "kotlin.yml",
            "cpp.yml",
        ]

        for workflow in required_workflows:
            workflow_path = ci_dir / workflow
            assert workflow_path.exists(), f"Missing CI workflow: {workflow}"
            assert workflow_path.is_file()
            assert workflow_path.stat().st_size > 0, f"Empty CI workflow: {workflow}"


class TestCIMutationPosture:
    """Mutation-testing CI steps mirror the python.yml posture (#398).

    The python reference workflow runs mutation testing as a step in the
    quality job gated to pushes on main (not per-PR). The TypeScript,
    Go, and Rust workflows must carry the same enforcement posture; the
    declined languages must not grow a half-wired step.
    """

    #: Language → command fragment its mutation step must run.
    MUTATION_COMMANDS: ClassVar[dict[str, str]] = {
        "python": "mutmut run",
        "typescript": "npx stryker run",
        "go": "gremlins unleash",
        "rust": "scripts/mutation.sh",
    }

    @pytest.fixture
    def ci_dir(self, reference_dir: Path) -> Path:
        """Return path to CI directory."""
        return reference_dir / "ci"

    @staticmethod
    def _mutation_steps(workflow_path: Path) -> list[dict]:
        """Return quality-job steps whose name mentions mutation."""
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["quality"]["steps"]
        return [
            step for step in steps if "mutation" in str(step.get("name", "")).lower()
        ]

    @pytest.mark.parametrize("language", sorted(MUTATION_COMMANDS))
    def test_quality_job_has_one_mutation_step(
        self, ci_dir: Path, language: str
    ) -> None:
        """Each implemented language has exactly one mutation step."""
        steps = self._mutation_steps(ci_dir / f"{language}.yml")
        assert len(steps) == 1

    @pytest.mark.parametrize("language", sorted(MUTATION_COMMANDS))
    def test_mutation_step_is_gated_to_main(self, ci_dir: Path, language: str) -> None:
        """The step runs on main pushes only, mirroring python.yml."""
        (step,) = self._mutation_steps(ci_dir / f"{language}.yml")
        assert step["if"] == "github.ref == 'refs/heads/main'"

    @pytest.mark.parametrize("language", sorted(MUTATION_COMMANDS))
    def test_mutation_step_runs_the_language_tool(
        self, ci_dir: Path, language: str
    ) -> None:
        """The step invokes the language's mutation tool."""
        (step,) = self._mutation_steps(ci_dir / f"{language}.yml")
        assert self.MUTATION_COMMANDS[language] in step["run"]

    @pytest.mark.parametrize(
        "language", ["swift", "kotlin", "cpp", "java", "csharp", "ruby", "php"]
    )
    def test_declined_languages_have_no_mutation_step(
        self, ci_dir: Path, language: str
    ) -> None:
        """Declined ecosystems stay honest: no mutation step at all."""
        workflow = yaml.safe_load(
            (ci_dir / f"{language}.yml").read_text(encoding="utf-8")
        )
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                assert "mutation" not in str(step.get("name", "")).lower()


class TestScriptsReferences:
    """Test scripts references exist for all supported languages."""

    @pytest.fixture
    def scripts_dir(self, reference_dir: Path) -> Path:
        """Return path to scripts directory."""
        return reference_dir / "scripts"

    def test_scripts_directory_exists(self, scripts_dir: Path) -> None:
        """Test that scripts/ directory exists."""
        assert scripts_dir.exists()
        assert scripts_dir.is_dir()

    def test_all_language_script_directories_exist(self, scripts_dir: Path) -> None:
        """Test that script directories exist for all 10 supported languages."""
        required_languages = [
            "python",
            "typescript",
            "go",
            "rust",
            "java",
            "csharp",
            "swift",
            "ruby",
            "php",
            "kotlin",
        ]

        for language in required_languages:
            language_dir = scripts_dir / language
            assert language_dir.exists(), f"Missing scripts directory: {language}/"
            assert language_dir.is_dir()

    def test_python_scripts_exist(self, scripts_dir: Path) -> None:
        """Test that required Python scripts exist."""
        python_dir = scripts_dir / "python"
        required_scripts = ["test.sh", "lint.sh"]

        for script in required_scripts:
            script_path = python_dir / script
            assert script_path.exists(), f"Missing Python script: {script}"
            assert script_path.is_file()
            assert script_path.stat().st_size > 0, f"Empty Python script: {script}"

    def test_java_lint_script_compiles_before_spotbugs(self, scripts_dir: Path) -> None:
        """The java reference lint script's SpotBugs run is no no-op (#368).

        SpotBugs reads bytecode: a bare ``mvn spotbugs:check`` silently
        passes when target/classes is empty, so the reference script must
        compile within the same invocation — parity with the generated
        scripts/security.sh and reference/ci/java.yml.
        """
        content = (scripts_dir / "java" / "lint.sh").read_text()
        commands = [
            line
            for line in content.splitlines()
            if "spotbugs:check" in line and not line.lstrip().startswith("#")
        ]
        assert commands, "lint.sh must run the SpotBugs gate"
        for command in commands:
            assert "compile" in command
            assert command.index("compile") < command.index("spotbugs:check")

    def test_csharp_lint_script_runs_the_roslyn_analyzers(
        self, scripts_dir: Path
    ) -> None:
        """The csharp reference lint script is more than a format check (#371).

        All Roslyn analysis (CA rules, the CA1502 complexity ceiling,
        SecurityCodeScan) runs inside the compiler, so without a
        ``dotnet build`` the lint gate could never see an analyzer
        finding — parity with the generated scripts/lint.sh and
        reference/ci/csharp.yml, where the build IS the lint gate.
        """
        content = (scripts_dir / "csharp" / "lint.sh").read_text()
        commands = [
            line for line in content.splitlines() if not line.lstrip().startswith("#")
        ]
        assert any("dotnet format --verify-no-changes" in c for c in commands)
        assert any("dotnet build" in c for c in commands)

    def test_csharp_test_script_defers_the_coverage_bound_to_the_csproj(
        self, scripts_dir: Path
    ) -> None:
        """The csharp reference test script never restates the threshold (#371).

        The >=90% Coverlet bound lives in the generated csproj
        (Threshold/ThresholdType/ThresholdStat — its single home);
        ``/p:CollectCoverage=true`` activates the gate without
        duplicating the number, matching reference/ci/csharp.yml and
        the generated scripts/test.sh.
        """
        content = (scripts_dir / "csharp" / "test.sh").read_text()
        commands = [
            line for line in content.splitlines() if not line.lstrip().startswith("#")
        ]
        test_runs = [c for c in commands if "dotnet test" in c]
        assert test_runs, "test.sh must run dotnet test"
        for command in test_runs:
            assert "/p:CollectCoverage=true" in command
            assert "Threshold" not in command

    def test_ruby_lint_script_runs_only_gemfile_backed_tools(
        self, scripts_dir: Path
    ) -> None:
        """The ruby reference lint script invokes no missing gems (#374).

        The generated Gemfile pins RuboCop only for linting — Reek is
        not in the toolchain and Brakeman is Rails-specific (it errors
        on plain-Ruby projects), so invoking either would fail on every
        generated project. RuboCop's full cop set is the lint gate,
        run with --force-exclusion — parity with the generated
        scripts/lint.sh and reference/ci/ruby.yml.
        """
        content = (scripts_dir / "ruby" / "lint.sh").read_text()
        commands = [
            line for line in content.splitlines() if not line.lstrip().startswith("#")
        ]
        assert any("rubocop --force-exclusion" in c for c in commands)
        assert not any("reek" in c for c in commands)
        assert not any("brakeman" in c for c in commands)

    def test_ruby_test_script_defers_the_coverage_bound_to_spec_helper(
        self, scripts_dir: Path
    ) -> None:
        """The ruby reference test script never restates the threshold (#374).

        The >=90% SimpleCov bound lives in spec/spec_helper.rb (its
        single home); COVERAGE=true activates the gate without
        duplicating the number, matching reference/ci/ruby.yml and the
        generated scripts/test.sh. (rspec has no --minimum-coverage
        flag — the pre-#374 invocation restated the threshold through
        an option rspec would reject.)
        """
        content = (scripts_dir / "ruby" / "test.sh").read_text()
        commands = [
            line for line in content.splitlines() if not line.lstrip().startswith("#")
        ]
        test_runs = [c for c in commands if "rspec" in c]
        assert test_runs, "test.sh must run rspec"
        for command in test_runs:
            assert "COVERAGE=true" in command
            assert "minimum-coverage" not in command
            assert "90" not in command


class TestSkillsReferences:
    """Test skills references exist and have proper structure."""

    @pytest.fixture
    def skills_dir(self, reference_dir: Path) -> Path:
        """Return path to skills directory."""
        return reference_dir / "skills"

    def test_skills_directory_exists(self, skills_dir: Path) -> None:
        """Test that skills/ directory exists."""
        assert skills_dir.exists()
        assert skills_dir.is_dir()

    def test_all_required_skills_exist(self, skills_dir: Path) -> None:
        """Test that all required skill directories exist with SKILL.md."""
        required_skills = [
            "vibe",
            "concurrency",
            "error-handling",
            "testing",
            "documentation",
            "security",
        ]

        for skill in required_skills:
            skill_dir = skills_dir / skill
            assert skill_dir.is_dir(), f"Missing skill directory: {skill}"
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"Missing SKILL.md in: {skill}"
            assert skill_file.stat().st_size > 0, f"Empty SKILL.md in: {skill}"


class TestSubagentsReferences:
    """Test subagent references exist and have proper structure."""

    @pytest.fixture
    def subagents_dir(self, reference_dir: Path) -> Path:
        """Return path to subagents directory."""
        return reference_dir / "subagents"

    def test_subagents_directory_exists(self, subagents_dir: Path) -> None:
        """Test that subagents/ directory exists."""
        assert subagents_dir.exists()
        assert subagents_dir.is_dir()

    def test_subagent_templates_exist(self, subagents_dir: Path) -> None:
        """Test that subagent templates exist."""
        templates_dir = subagents_dir / "templates"
        assert templates_dir.exists()
        assert templates_dir.is_dir()

        required_templates = [
            "level-0-chief-architect.md",
            "level-1-section-orchestrator.md",
            "level-2-module-design.md",
            "level-3-component-specialist.md",
            "level-4-implementation-engineer.md",
            "level-5-junior-engineer.md",
        ]

        for template in required_templates:
            template_path = templates_dir / template
            assert template_path.exists(), f"Missing template: {template}"
            assert template_path.is_file()


class TestPrecommitReferences:
    """Test pre-commit configuration references exist."""

    @pytest.fixture
    def precommit_dir(self, reference_dir: Path) -> Path:
        """Return path to precommit directory."""
        return reference_dir / "precommit"

    def test_precommit_directory_exists(self, precommit_dir: Path) -> None:
        """Test that precommit/ directory exists."""
        assert precommit_dir.exists()
        assert precommit_dir.is_dir()


class TestReferenceStructure:
    """Test overall reference directory structure."""

    def test_maximum_quality_engineering_exists(self, reference_dir: Path) -> None:
        """Test that MAXIMUM_QUALITY_ENGINEERING.md exists."""
        mqe_path = reference_dir / "MAXIMUM_QUALITY_ENGINEERING.md"
        assert mqe_path.exists()
        assert mqe_path.is_file()
        assert mqe_path.stat().st_size > 0

    def test_reference_directory_structure(self, reference_dir: Path) -> None:
        """Test that reference directory has all required subdirectories."""
        required_dirs = ["ci", "scripts", "skills", "subagents", "precommit"]

        for dir_name in required_dirs:
            dir_path = reference_dir / dir_name
            assert dir_path.exists(), f"Missing directory: {dir_name}/"
            assert dir_path.is_dir()
