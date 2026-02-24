"""Integration tests for full init command flow.

Tests the complete end-to-end initialization workflow including:
- CLI command execution
- Generator orchestration
- File creation
- Output validation

All tests use mocked AI orchestrator to avoid calling the real Anthropic API.
See Issue #196 for details.
"""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from start_green_stay_green.cli import app


@pytest.fixture(autouse=True)
def _block_orchestrator_init() -> Generator[None, None, None]:
    """Block real Anthropic API calls for all tests in this module.

    Patches _initialize_orchestrator to return None so no real API calls
    are made. Tests that need AI-generated output use additional stub
    patches on individual generation steps.

    Addresses Issue #196: API key from keyring, env vars, or CLI args
    could cause real API calls during testing.
    """
    with patch(
        "start_green_stay_green.cli._initialize_orchestrator", return_value=None
    ):
        yield


def _stub_ci_step(project_path: Path, _language: str, _orchestrator: object) -> None:
    """Stub CI generation step that writes minimal valid workflow files.

    Args:
        project_path: Target project directory.
        _language: Programming language (unused in stub).
        _orchestrator: Mock orchestrator (unused in stub).
    """
    workflows_dir = project_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    ci_content = "name: CI\non:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
    (workflows_dir / "ci.yml").write_text(ci_content)


def _stub_review_step(project_path: Path, _orchestrator: object) -> None:
    """Stub review generation step that writes a minimal code-review workflow.

    Args:
        project_path: Target project directory.
        _orchestrator: Mock orchestrator (unused in stub).
    """
    workflows_dir = project_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    review_content = "name: Code Review\non:\n  pull_request:\n"
    (workflows_dir / "code-review.yml").write_text(review_content)


def _stub_claude_md_step(
    project_path: Path,
    project_name: str,
    language: str,
    _orchestrator: object,
) -> None:
    """Stub CLAUDE.md generation step that writes minimal content.

    Args:
        project_path: Target project directory.
        project_name: Name of the project.
        language: Programming language.
        _orchestrator: Mock orchestrator (unused in stub).
    """
    (project_path / "CLAUDE.md").write_text(
        f"# Claude Code Project Context: {project_name}\n\nGenerated for {language}.\n"
    )


def _stub_architecture_step(
    project_path: Path,
    project_name: str,
    _language: str,
    _orchestrator: object,
) -> None:
    """Stub architecture generation step that writes minimal rule files.

    Args:
        project_path: Target project directory.
        project_name: Name of the project.
        _language: Programming language (unused in stub).
        _orchestrator: Mock orchestrator (unused in stub).
    """
    arch_dir = project_path / "plans" / "architecture"
    arch_dir.mkdir(parents=True, exist_ok=True)
    linter_cfg = f"[importlinter]\nroot_package = {project_name}\n"
    (arch_dir / ".importlinter").write_text(linter_cfg)
    (arch_dir / "README.md").write_text(f"# Architecture Rules for {project_name}\n")
    run_check = arch_dir / "run-check.sh"
    run_check.write_text("#!/usr/bin/env bash\necho 'Architecture check passed'\n")
    run_check.chmod(0o755)


def _stub_subagents_step(
    project_path: Path,
    project_name: str,
    _language: str,
    _orchestrator: object,
) -> None:
    """Stub subagents generation step that creates the subagents directory.

    Args:
        project_path: Target project directory.
        project_name: Name of the project.
        _language: Programming language (unused in stub).
        _orchestrator: Mock orchestrator (unused in stub).
    """
    subagents_dir = project_path / ".claude" / "subagents"
    subagents_dir.mkdir(parents=True, exist_ok=True)
    (subagents_dir / "README.md").write_text(f"# Subagents for {project_name}\n")


class TestInitFlowIntegration:
    """Test complete init flow end-to-end."""

    def test_init_creates_project_directory(self, tmp_path: Path) -> None:
        """Test init command creates project directory."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-integration-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        project_path = tmp_path / "test-integration-project"
        assert project_path.exists()
        assert project_path.is_dir()

    def test_init_generates_scripts_directory(self, tmp_path: Path) -> None:
        """Test init creates scripts directory with quality scripts."""
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-scripts-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-scripts-project"
        scripts_dir = project_path / "scripts"

        assert scripts_dir.exists()
        assert scripts_dir.is_dir()

        expected_scripts = [
            "check-all.sh",
            "test.sh",
            "lint.sh",
            "format.sh",
            "security.sh",
            "mutation.sh",
            "fix-all.sh",
        ]

        for script_name in expected_scripts:
            script_path = scripts_dir / script_name
            assert script_path.exists(), f"Missing script: {script_name}"
            # Check executable permissions (owner, group, or other can execute)
            mode = script_path.stat().st_mode
            assert (
                mode & 0o111
            ), f"Script {script_name} not executable: permissions={mode:#o}"

    def test_init_generates_mutation_script_with_correct_content(
        self, tmp_path: Path
    ) -> None:
        """Test init creates mutation.sh with proper content.

        Addresses Claude Code Review HIGH issue: Integration test should verify
        mutation.sh content specifically, not just existence.
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-mutation-content",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-mutation-content"
        mutation_script = project_path / "scripts" / "mutation.sh"

        assert mutation_script.exists()
        content = mutation_script.read_text()

        # Verify critical mutation testing content
        assert "mutmut run" in content
        assert "mutmut results" in content
        assert "MIN_SCORE=80" in content
        assert "80% minimum mutation score" in content
        assert "MAXIMUM QUALITY" in content

        # Verify bash safety
        assert "set -euo pipefail" in content

        # Verify package name interpolation
        # (test-mutation-content → test_mutation_content)
        assert "test_mutation_content" in content

        # Verify help documentation
        assert "--help" in content
        assert "Usage:" in content
        assert "EXIT CODES:" in content

    def test_init_generates_precommit_config(self, tmp_path: Path) -> None:
        """Test init creates .pre-commit-config.yaml with proper content.

        Addresses Issue #106: PreCommitGenerator integration (Part 2/8).
        """
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-precommit-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0

        project_path = tmp_path / "test-precommit-project"
        precommit_config = project_path / ".pre-commit-config.yaml"

        assert precommit_config.exists()
        content = precommit_config.read_text()

        # Verify header comment
        assert "Pre-commit hooks configuration" in content
        assert "test-precommit-project" in content

        # Verify critical hooks are present
        assert "pre-commit-hooks" in content
        assert "ruff" in content or "eslint" in content  # Language-specific linter
        assert "repos:" in content
        assert "hooks:" in content

    @patch("start_green_stay_green.cli._generate_review_step", _stub_review_step)
    @patch("start_green_stay_green.cli._generate_ci_step", _stub_ci_step)
    def test_init_generates_github_workflows(self, tmp_path: Path) -> None:
        """Test init creates GitHub Actions workflows.

        Uses stub generators to avoid calling real Anthropic API (#196).
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-workflows-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-workflows-project"
        workflows_dir = project_path / ".github" / "workflows"

        assert workflows_dir.exists()
        assert workflows_dir.is_dir()

        expected_workflows = ["ci.yml", "code-review.yml"]

        for workflow_name in expected_workflows:
            workflow_path = workflows_dir / workflow_name
            assert workflow_path.exists(), f"Missing workflow: {workflow_name}"

    @patch("start_green_stay_green.cli._generate_claude_md_step", _stub_claude_md_step)
    def test_init_generates_claude_md(self, tmp_path: Path) -> None:
        """Test init creates CLAUDE.md file.

        Uses stub generator to avoid calling real Anthropic API (#196).
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-claude-md-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-claude-md-project"
        claude_md = project_path / "CLAUDE.md"

        assert claude_md.exists()

        content = claude_md.read_text()
        assert "# Claude Code Project Context" in content
        assert len(content) > 10

    def test_init_generates_skills_directory(self, tmp_path: Path) -> None:
        """Test init creates .claude/skills directory with skill files.

        Addresses Issue #106: SkillsGenerator integration (Part 3/8).
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-skills-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-skills-project"
        skills_dir = project_path / ".claude" / "skills"

        assert skills_dir.exists()
        assert skills_dir.is_dir()

        # Verify required skills are present (directory-per-skill format)
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
            # Verify skill has content
            content = skill_file.read_text()
            assert len(content) > 100, f"Skill {skill} has insufficient content"

    @patch(
        "start_green_stay_green.cli._generate_subagents_step",
        _stub_subagents_step,
    )
    def test_init_generates_subagents_directory(self, tmp_path: Path) -> None:
        """Test init creates .claude/subagents directory.

        Uses stub generator to avoid calling real Anthropic API (#196).
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-subagents-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-subagents-project"
        subagents_dir = project_path / ".claude" / "subagents"

        assert subagents_dir.exists()
        assert subagents_dir.is_dir()

    @patch(
        "start_green_stay_green.cli._generate_architecture_step",
        _stub_architecture_step,
    )
    def test_init_generates_architecture_rules(self, tmp_path: Path) -> None:
        """Test init creates architecture enforcement rules.

        Uses stub generator to avoid calling real Anthropic API (#196).
        """
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-architecture-project",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        project_path = tmp_path / "test-architecture-project"
        arch_dir = project_path / "plans" / "architecture"

        assert arch_dir.exists()
        assert (arch_dir / ".importlinter").exists()
        assert (arch_dir / "README.md").exists()
        assert (arch_dir / "run-check.sh").exists()


class TestFullIntegrationFlow:
    """Test complete integration from CLI to file generation."""

    def test_init_success_message_displayed(self, tmp_path: Path) -> None:
        """Test init displays success message upon completion."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-success-msg",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--no-interactive",
            ],
        )

        assert result.exit_code == 0
        # More specific assertion to catch format regressions
        assert "Project generated successfully at:" in result.stdout

    def test_init_dry_run_does_not_create_directory(self, tmp_path: Path) -> None:
        """Test dry-run mode shows preview without creating files."""
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-dry-run",
                "--language",
                "python",
                "--output-dir",
                str(tmp_path),
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        # Verify specific dry-run output structure
        assert "Dry Run Mode" in result.stdout
        assert "Preview only" in result.stdout
        assert not (tmp_path / "test-dry-run").exists()

    def test_init_respects_output_directory(self, tmp_path: Path) -> None:
        """Test init creates project in specified output directory."""
        output_dir = tmp_path / "custom" / "path"
        runner = CliRunner()
        runner.invoke(
            app,
            [
                "init",
                "--project-name",
                "test-custom-dir",
                "--language",
                "python",
                "--output-dir",
                str(output_dir),
                "--no-interactive",
            ],
        )

        project_path = output_dir / "test-custom-dir"
        assert project_path.exists()
        assert project_path.is_dir()
