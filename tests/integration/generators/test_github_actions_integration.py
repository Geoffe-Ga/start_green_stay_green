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
        workflow_data = yaml.safe_load(result.workflow_content)

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

        workflow_data = yaml.safe_load(result.workflow_content)

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
        assert "review" in workflow_data["jobs"]

        job = workflow_data["jobs"]["review"]
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

        workflow_data = yaml.safe_load(result.workflow_content)

        pr_triggers = workflow_data["on"]["pull_request"]["types"]
        assert "opened" in pr_triggers
        assert "synchronize" in pr_triggers
        assert "reopened" in pr_triggers

    def test_workflow_uses_environment_variables_for_security(self) -> None:
        """Test workflow uses environment variables to prevent injection."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        # Verify environment variable usage (prevents shell injection)
        assert "env:" in result.workflow_content
        assert "BASE_REF:" in result.workflow_content
        assert "${BASE_REF}" in result.workflow_content

        # Verify direct interpolation is NOT used in shell commands
        # (this would be a shell injection vulnerability)
        assert "origin/${{" not in result.workflow_content

    def test_workflow_references_claude_api_key_secret(self) -> None:
        """Test workflow references CLAUDE_API_KEY from secrets."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result.workflow_content)

        # Verify secrets.CLAUDE_API_KEY is referenced
        review_job = workflow_data["jobs"]["review"]
        assert "env" in review_job
        assert "CLAUDE_API_KEY" in review_job["env"]

    def test_workflow_has_merge_blocking_step(self) -> None:
        """Test workflow includes step that blocks merge on issues."""
        orchestrator = create_autospec(AIOrchestrator)

        project_root = Path(__file__).parent.parent.parent.parent
        template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_path,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result.workflow_content)

        steps = workflow_data["jobs"]["review"]["steps"]

        # Find merge blocking step
        blocking_step = None
        for step in steps:
            if "Block merge" in step.get("name", ""):
                blocking_step = step
                break

        assert blocking_step is not None, "Merge blocking step not found"
        assert "if" in blocking_step
        assert "CHANGES_REQUESTED" in blocking_step["if"]

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
        output_file.write_text(result.workflow_content)

        # Verify file exists
        assert output_file.exists()

        # Parse from file
        with output_file.open() as f:
            workflow_from_file = yaml.safe_load(f)

        assert workflow_from_file["name"] == "PR Review"
        assert "on" in workflow_from_file
        assert "jobs" in workflow_from_file
