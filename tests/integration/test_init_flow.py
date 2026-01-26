"""Integration tests for full init command flow.

Tests the complete end-to-end initialization workflow including:
- CLI command execution
- Generator orchestration
- File creation
- Output validation
"""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from start_green_stay_green.cli import app

# Check if API key is available for AI-powered generator tests
HAS_API_KEY = bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY"))


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

    @pytest.mark.skipif(not HAS_API_KEY, reason="Requires API key for AI-powered generators")
    def test_init_generates_github_workflows(self, tmp_path: Path) -> None:
        """Test init creates GitHub Actions workflows."""
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

    @pytest.mark.skipif(not HAS_API_KEY, reason="Requires API key for AI-powered generators")
    def test_init_generates_claude_md(self, tmp_path: Path) -> None:
        """Test init creates CLAUDE.md file."""
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
        # Verify exact expected header format (not just any markdown header)
        assert "# Claude Code Project Context" in content
        assert len(content) > 100

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

        # Verify required skills are present
        required_skills = [
            "vibe.md",
            "concurrency.md",
            "error-handling.md",
            "testing.md",
            "documentation.md",
            "security.md",
        ]

        for skill in required_skills:
            skill_file = skills_dir / skill
            assert skill_file.exists(), f"Missing skill: {skill}"
            # Verify skill has content
            content = skill_file.read_text()
            assert len(content) > 100, f"Skill {skill} has insufficient content"

    @pytest.mark.skipif(not HAS_API_KEY, reason="Requires API key for AI-powered generators")
    def test_init_generates_subagents_directory(self, tmp_path: Path) -> None:
        """Test init creates .claude/subagents directory."""
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

    @pytest.mark.skipif(not HAS_API_KEY, reason="Requires API key for AI-powered generators")
    def test_init_generates_architecture_rules(self, tmp_path: Path) -> None:
        """Test init creates architecture enforcement rules."""
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
