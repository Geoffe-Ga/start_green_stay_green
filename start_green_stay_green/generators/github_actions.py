"""GitHub Actions code review generator.

Generates automated PR code review workflow using Claude API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from jinja2 import Environment
from jinja2 import FileSystemLoader

from start_green_stay_green.generators.base import GenerationError
from start_green_stay_green.generators.base import TemplateBasedGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


@dataclass(frozen=True)
class ReviewWorkflowResult:
    """Result from code review workflow generation.

    Attributes:
        workflow_content: Generated GitHub Actions workflow YAML content.
        workflow_path: Target path for workflow file (.github/workflows/review.yml).
    """

    workflow_content: str
    workflow_path: Path


class GitHubActionsReviewGenerator(TemplateBasedGenerator):
    """Generates GitHub Actions workflow for automated PR code review.

    Uses Jinja2 templates to generate GitHub Actions workflow that:
    - Triggers on PR open/update
    - Uses Claude API for code review
    - Enforces strict response format
    - Categorizes issues (Low/Medium/High/Critical)
    - Auto-creates GitHub issues for Low severity
    - Blocks merge for Medium+ severity

    Example:
        >>> generator = GitHubActionsReviewGenerator()  # No orchestrator yet
        >>> result = generator.generate(workflow_name="Code Review")
        >>> print(result["workflow_path"])
        .github/workflows/review.yml
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        *,
        template_path: Path | None = None,
    ) -> None:
        """Initialize GitHub Actions Review Generator.

        Args:
            orchestrator: Optional AI orchestrator for Claude API integration.
                Reserved for future use in Issue #102 (Claude API integration).
                Currently unused - generator only renders workflow templates.
            template_path: Path to Jinja2 template file. If None, uses default
                template at templates/github/code_review.yml.j2.

        Note:
            This is Phase 1 infrastructure. The orchestrator parameter is accepted
            but not yet used. Issue #102 tracks implementation of actual Claude API
            integration in the generated workflow.
        """
        super().__init__(orchestrator=orchestrator)

        if template_path is None:
            project_root = Path(__file__).parent.parent.parent
            template_path = project_root / "templates" / "github" / "code_review.yml.j2"

        self.template_path = template_path

    def _validate_template_exists(self) -> None:
        """Validate that template file exists.

        Raises:
            GenerationError: If template file doesn't exist.
        """
        if not self.template_path.exists():
            msg = f"Template not found: {self.template_path}"
            raise GenerationError(
                msg,
                cause=FileNotFoundError(str(self.template_path)),
            )

    def generate(
        self,
        *,
        workflow_name: str = "Code Review",
    ) -> dict[str, Any]:
        """Generate GitHub Actions code review workflow.

        Creates a GitHub Actions workflow YAML file that:
        - Triggers on pull_request (opened, synchronize, reopened)
        - Uses Claude API for automated code review
        - Enforces structured response format
        - Categorizes issues by severity
        - Creates GitHub issues for Low severity items
        - Blocks merge for Medium/High/Critical issues

        Args:
            workflow_name: Name of the GitHub Actions workflow.
                Defaults to "Code Review".

        Returns:
            Dictionary with keys:
                - workflow_content: Generated YAML content
                - workflow_path: Target path (.github/workflows/review.yml)

        Raises:
            GenerationError: If template file doesn't exist.

        Example:
            >>> result = generator.generate(workflow_name="PR Review")
            >>> output_path = Path(result["workflow_path"])
            >>> output_path.parent.mkdir(parents=True, exist_ok=True)
            >>> output_path.write_text(result["workflow_content"])
        """
        self._validate_template_exists()

        # Load Jinja2 template
        # Note: autoescape=False is safe for YAML templates (no HTML/XSS risk)
        # GitHub Actions expressions use {{ }} which would conflict with autoescape
        template_dir = self.template_path.parent
        template_name = self.template_path.name
        env = Environment(  # nosec B701  # CWE-94: Safe for YAML (no HTML rendering)
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,  # noqa: S701
        )
        template = env.get_template(template_name)

        # Render template
        workflow_content = template.render(
            workflow_name=workflow_name,
        )

        return {
            "workflow_content": workflow_content,
            "workflow_path": Path(".github/workflows/review.yml"),
        }

    def generate_review_workflow(
        self,
        *,
        workflow_name: str = "Code Review",
    ) -> ReviewWorkflowResult:
        """Legacy method for backward compatibility.

        This method wraps generate() and returns ReviewWorkflowResult
        for code that expects the old interface.

        Args:
            workflow_name: Name of the GitHub Actions workflow.

        Returns:
            ReviewWorkflowResult with workflow content and path.

        Raises:
            GenerationError: If template doesn't exist.

        Deprecated:
            Use generate() instead. This method will be removed in v2.0.
        """
        result = self.generate(workflow_name=workflow_name)
        return ReviewWorkflowResult(
            workflow_content=result["workflow_content"],
            workflow_path=result["workflow_path"],
        )
