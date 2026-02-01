"""Integration tests for GitHub Actions Review Generator.

Tests that validate generated workflows are syntactically valid and
contain required GitHub Actions schema elements.
"""

from pathlib import Path
from unittest.mock import create_autospec

import yaml

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator,
)


class TestGitHubActionsIntegration:
    """Integration tests for GitHub Actions workflow generation."""

    def test_generated_workflow_is_valid_yaml(self) -> None:
        """Test generated workflow parses as valid YAML."""
        orchestrator = create_autospec(AIOrchestrator)

        # Use actual project template
        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate(workflow_name="Code Review")

        # Parse as YAML - will raise exception if invalid
        workflow_data = yaml.safe_load(result["workflow_content"])

        # Basic structure validation
        assert isinstance(workflow_data, dict)
        assert "name" in workflow_data
        assert workflow_data["name"] == "Code Review"

    def test_generated_workflow_has_required_github_actions_fields(self) -> None:
        """Test generated workflow contains required GitHub Actions schema fields."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result["workflow_content"])

        # Required top-level fields
        assert "name" in workflow_data
        assert "on" in workflow_data
        assert "jobs" in workflow_data

        # Verify on triggers
        assert "pull_request" in workflow_data["on"]
        assert isinstance(workflow_data["on"]["pull_request"], dict)
        assert "types" in workflow_data["on"]["pull_request"]

        # Verify jobs structure
        assert isinstance(workflow_data["jobs"], dict)
        assert "claude-review" in workflow_data["jobs"]

        job = workflow_data["jobs"]["claude-review"]
        assert "runs-on" in job
        assert "steps" in job
        assert isinstance(job["steps"], list)
        assert len(job["steps"]) > 0

    def test_workflow_has_pull_request_triggers(self) -> None:
        """Test workflow triggers on PR events."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result["workflow_content"])

        pr_triggers = workflow_data["on"]["pull_request"]["types"]
        assert "opened" in pr_triggers
        assert "synchronize" in pr_triggers
        assert "reopened" in pr_triggers

    def test_workflow_uses_claude_code_action_for_security(self) -> None:
        """Test workflow uses Claude Code Action (secure by design).

        The Claude Code Action handles all security concerns internally,
        eliminating the need for manual environment variable handling
        and preventing shell injection vulnerabilities.
        """
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        # Verify uses Claude Code Action (secure by design)
        assert "anthropics/claude-code-action@v1" in result["workflow_content"]

        # Verify no direct shell command usage (Claude Code Action handles this)
        workflow_data = yaml.safe_load(result["workflow_content"])
        steps = workflow_data["jobs"]["claude-review"]["steps"]

        # All steps should either be checkout or Claude Code Action
        for step in steps:
            if "uses" in step:
                assert (
                    "actions/checkout@v4" in step["uses"]
                    or "anthropics/claude-code-action@v1" in step["uses"]
                )

    def test_workflow_references_claude_code_oauth_token_secret(self) -> None:
        """Test workflow references CLAUDE_CODE_OAUTH_TOKEN from secrets.

        The Claude Code Action uses OAuth tokens instead of deprecated API keys
        for improved security and authentication.
        """
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        # Verify CLAUDE_CODE_OAUTH_TOKEN is referenced in workflow content
        assert "CLAUDE_CODE_OAUTH_TOKEN" in result["workflow_content"]
        assert "secrets.CLAUDE_CODE_OAUTH_TOKEN" in result["workflow_content"]

    def test_workflow_uses_claude_code_action_for_review(self) -> None:
        """Test workflow uses Claude Code Action for automated review.

        The Claude Code Action handles review logic internally, including
        posting comments and blocking merges based on review results.
        """
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result["workflow_content"])

        steps = workflow_data["jobs"]["claude-review"]["steps"]

        # Find Claude Code Review step
        claude_review_step = None
        for step in steps:
            if step.get("name") == "Run Claude Code Review":
                claude_review_step = step
                break

        assert claude_review_step is not None, "Claude Code Review step not found"
        assert "uses" in claude_review_step
        assert "anthropics/claude-code-action@v1" in claude_review_step["uses"]

        # Verify step has required inputs
        assert "with" in claude_review_step
        assert "claude_code_oauth_token" in claude_review_step["with"]
        assert "prompt" in claude_review_step["with"]

    def test_workflow_file_can_be_written_and_parsed(
        self,
        tmp_path: Path,
    ) -> None:
        """Test end-to-end: generate, write to file, parse from file."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate(workflow_name="PR Review")

        # Write to file
        output_file = tmp_path / ".github" / "workflows" / "review.yml"
        output_file.parent.mkdir(parents=True)
        output_file.write_text(result["workflow_content"])

        # Verify file exists
        assert output_file.exists()

        # Parse from file
        with output_file.open() as f:
            workflow_from_file = yaml.safe_load(f)

        assert workflow_from_file["name"] == "PR Review"
        assert "on" in workflow_from_file
        assert "jobs" in workflow_from_file
