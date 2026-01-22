"""Unit tests for GitHub Actions Code Review Generator."""

from pathlib import Path
from unittest.mock import create_autospec

import pytest
import yaml

from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator,
)
from start_green_stay_green.generators.github_actions import ReviewWorkflowResult


class TestReviewWorkflowResult:
    """Test ReviewWorkflowResult dataclass."""

    def test_review_workflow_result_is_frozen(self) -> None:
        """Test ReviewWorkflowResult is immutable."""
        result = ReviewWorkflowResult(
            workflow_content="name: Review",
            workflow_path=Path(".github/workflows/review.yml"),
        )

        with pytest.raises(AttributeError):
            result.workflow_content = "different"  # type: ignore[misc]


class TestGitHubActionsReviewGeneratorInit:
    """Test GitHubActionsReviewGenerator initialization."""

    def test_init_with_orchestrator(self) -> None:
        """Test initialization with AI orchestrator."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = GitHubActionsReviewGenerator(orchestrator)

        assert generator.orchestrator is orchestrator

    def test_init_sets_default_template_path(self) -> None:
        """Test initialization sets default template path."""
        orchestrator = create_autospec(AIOrchestrator)
        generator = GitHubActionsReviewGenerator(orchestrator)

        assert generator.template_path is not None
        assert generator.template_path.name == "code_review.yml.j2"

    def test_init_with_custom_template_path(self) -> None:
        """Test initialization with custom template path."""
        orchestrator = create_autospec(AIOrchestrator)
        custom_path = Path("/custom/template.yml.j2")

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=custom_path,
        )

        assert generator.template_path == custom_path


class TestGitHubActionsReviewGeneratorValidation:
    """Test GitHubActionsReviewGenerator validation methods."""

    def test_validate_template_exists_raises_if_missing(
        self,
        tmp_path: Path,
    ) -> None:
        """Test validation raises if template file doesn't exist."""
        orchestrator = create_autospec(AIOrchestrator)
        missing_template = tmp_path / "missing.yml.j2"

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=missing_template,
        )

        with pytest.raises(FileNotFoundError, match=r"Template not found"):
            generator._validate_template_exists()  # noqa: SLF001

    def test_validate_template_exists_passes_if_present(
        self,
        tmp_path: Path,
    ) -> None:
        """Test validation passes if template exists."""
        orchestrator = create_autospec(AIOrchestrator)
        template_file = tmp_path / "template.yml.j2"
        template_file.write_text("name: {{ workflow_name }}")

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        # Should not raise
        generator._validate_template_exists()  # noqa: SLF001


class TestGitHubActionsReviewGeneratorWorkflowGeneration:
    """Test GitHubActionsReviewGenerator workflow generation."""

    def test_generate_creates_workflow_yaml(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generate creates valid GitHub Actions YAML."""
        orchestrator = create_autospec(AIOrchestrator)

        # Create minimal template
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: {{ workflow_name }}
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate(workflow_name="Code Review")

        # Verify result structure
        assert isinstance(result, ReviewWorkflowResult)
        assert result.workflow_content
        assert result.workflow_path.name == "review.yml"

        # Verify valid YAML
        workflow_data = yaml.safe_load(result.workflow_content)
        assert workflow_data["name"] == "Code Review"

    def test_generate_includes_pr_triggers(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated workflow triggers on PR open/update."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize, reopened]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        workflow_data = yaml.safe_load(result.workflow_content)
        assert "pull_request" in workflow_data["on"]
        pr_types = workflow_data["on"]["pull_request"]["types"]
        assert "opened" in pr_types
        assert "synchronize" in pr_types

    def test_generate_includes_claude_api_usage(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated workflow includes Claude API integration."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    env:
      CLAUDE_API_KEY: {% raw %}${{ secrets.CLAUDE_API_KEY }}{% endraw %}
    steps:
      - uses: actions/checkout@v4
      - name: Run Review
        run: echo "Review with Claude"
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        # Check for Claude API key reference
        assert "CLAUDE_API_KEY" in result.workflow_content
        assert "secrets.CLAUDE_API_KEY" in result.workflow_content

    def test_generate_includes_response_format_template(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated workflow includes response format template."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Review
        run: |
          # Response Format:
          # ## Code Review Results
          # ### Status: [LGTM | CHANGES_REQUESTED]
          # ### Issues Found
          # #### Critical (Block Merge)
          # #### High (Block Merge)
          # #### Medium (Block Merge)
          # #### Low (Create GitHub Issue for Future PR)
          echo "Review"
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        # Check for response format keywords
        assert "Code Review Results" in result.workflow_content
        assert "LGTM | CHANGES_REQUESTED" in result.workflow_content
        assert "Critical (Block Merge)" in result.workflow_content
        assert "High (Block Merge)" in result.workflow_content
        assert "Medium (Block Merge)" in result.workflow_content
        assert "Low (Create GitHub Issue" in result.workflow_content

    def test_generate_includes_merge_blocking_logic(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated workflow blocks merge for Medium+ issues."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Block if issues
        run: |
          if [[ "$STATUS" == "CHANGES_REQUESTED" ]]; then
            exit 1  # Block merge
          fi
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        # Check for merge blocking logic
        assert "exit 1" in result.workflow_content
        assert "CHANGES_REQUESTED" in result.workflow_content


class TestGitHubActionsReviewGeneratorIssueCategorization:
    """Test issue categorization in generated workflows."""

    def test_generate_supports_four_severity_levels(
        self,
        tmp_path: Path,
    ) -> None:
        """Test workflow supports Critical/High/Medium/Low severity."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Categorize
        run: |
          # Critical, High, Medium block merge
          # Low creates GitHub issue
          echo "Categorize"
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        content = result.workflow_content
        assert "Critical" in content
        assert "High" in content
        assert "Medium" in content
        assert "Low" in content

    def test_generate_includes_github_issue_creation_for_low(
        self,
        tmp_path: Path,
    ) -> None:
        """Test workflow creates GitHub issues for Low severity."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text(
            """name: Code Review
"on":
  pull_request:
    types: [opened, synchronize]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Create issues for Low
        run: |
          gh issue create --title "Low severity" --body "Details"
"""
        )

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        # Check for gh issue create command
        assert "gh issue create" in result.workflow_content


class TestGitHubActionsReviewGeneratorOutputPath:
    """Test workflow output path generation."""

    def test_generate_returns_correct_output_path(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generate returns .github/workflows/review.yml path."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text("name: Review")

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        assert result.workflow_path == Path(".github/workflows/review.yml")

    def test_generate_workflow_can_be_written_to_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated workflow can be written to file system."""
        orchestrator = create_autospec(AIOrchestrator)

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "code_review.yml.j2"
        template_file.write_text("name: Test Workflow")

        generator = GitHubActionsReviewGenerator(
            orchestrator,
            template_path=template_file,
        )

        result = generator.generate()

        # Write to file
        output_path = tmp_path / result.workflow_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.workflow_content)

        # Verify file exists and is valid YAML
        assert output_path.exists()
        workflow_data = yaml.safe_load(output_path.read_text())
        assert workflow_data["name"] == "Test Workflow"
