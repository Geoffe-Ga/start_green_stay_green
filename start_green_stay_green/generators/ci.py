"""CI pipeline generator for target projects.

Generates GitHub Actions workflows customized to target project language
and framework.

Default path: render the deterministic, version-controlled YAML templates
in ``reference/ci/<language>.yml`` through Jinja2, substituting the
project name. The optional Claude-powered path is reserved for the
``green enhance`` flow (Phase 3 of the optimization roadmap) and only
runs when an :class:`AIOrchestrator` is provided.
"""

from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

from jinja2 import Environment
from jinja2 import StrictUndefined
import yaml

from start_green_stay_green.generators.base import BaseGenerator
from start_green_stay_green.utils.yaml_utils import strip_markdown_fences

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator
    from start_green_stay_green.ai.orchestrator import GenerationResult


# Reference CI templates ship with the package. Each ``<language>.yml`` is
# a deterministic baseline that ``green init`` renders without calling
# Claude. The directory is resolved relative to the package root rather
# than CWD so the generator works whether installed or run in-tree.
REFERENCE_CI_DIR = Path(__file__).parent.parent.parent / "reference" / "ci"

# Supported languages and their configurations
LANGUAGE_CONFIGS: dict[str, dict[str, Any]] = {
    "python": {
        "test_framework": "pytest",
        "linters": ["ruff", "pylint", "mypy"],
        "formatters": ["black", "ruff"],
        "security_tools": ["bandit", "pip-audit"],
        "supported_versions": ["3.11", "3.12", "3.13"],
        "package_manager": "pip",
    },
    "typescript": {
        "test_framework": "jest",
        "linters": ["eslint", "tsc"],
        "formatters": ["prettier", "eslint"],
        "security_tools": ["npm_audit", "snyk"],
        "supported_versions": ["18", "20"],
        "package_manager": "npm",
    },
    "go": {
        "test_framework": "go_test",
        "linters": ["golangci-lint"],
        "formatters": ["gofmt"],
        "security_tools": ["gosec"],
        "supported_versions": ["1.21", "1.22"],
        "package_manager": "go_modules",
    },
    "rust": {
        "test_framework": "cargo_test",
        "linters": ["clippy"],
        "formatters": ["rustfmt"],
        "security_tools": ["cargo_audit"],
        "supported_versions": ["1.70", "1.75"],
        "package_manager": "cargo",
    },
    "java": {
        "test_framework": "junit",
        "linters": ["checkstyle"],
        "formatters": ["google-java-format"],
        "security_tools": ["spotbugs"],
        "supported_versions": ["11", "17", "21"],
        "package_manager": "maven",
    },
    "csharp": {
        "test_framework": "xunit",
        "linters": ["roslyn"],
        "formatters": ["dotnet_format"],
        "security_tools": ["security_code_scan"],
        "supported_versions": ["6.0", "8.0"],
        "package_manager": "nuget",
    },
    "ruby": {
        "test_framework": "rspec",
        "linters": ["rubocop"],
        "formatters": ["rubocop"],
        "security_tools": ["brakeman"],
        "supported_versions": ["3.1", "3.2"],
        "package_manager": "bundler",
    },
}


@dataclass(frozen=True)
class CIWorkflow:
    """GitHub Actions workflow configuration.

    Attributes:
        name: Workflow name.
        content: Complete YAML workflow content.
        language: Target programming language.
        is_valid: Whether the workflow YAML is valid.
        error_message: Any validation error message.
    """

    name: str
    content: str
    language: str
    is_valid: bool
    error_message: str | None = None


class CIGenerator(BaseGenerator):
    """Generates customized CI/CD pipelines for target projects.

    Supports multiple programming languages and frameworks. Generates comprehensive
    GitHub Actions workflows including multi-version testing, linting, security
    scanning, coverage analysis, and mutation testing.

    Attributes:
        orchestrator: AI orchestrator for generation tasks.
        language: Target programming language.
        framework: Optional target framework (e.g., FastAPI, Django, Spring).
        test_framework: Testing framework for the language.
        supported_versions: List of language versions to test against.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None = None,
        language: str = "python",
        *,
        framework: str | None = None,
        reference_dir: Path | None = None,
    ) -> None:
        """Initialize CI Generator.

        Args:
            orchestrator: Optional AIOrchestrator for the legacy
                Claude-generated path. Default :data:`None` selects the
                deterministic template-based path
                (``generate_workflow_from_template``).
            language: Target language (python, typescript, go, rust, java,
                csharp, ruby).
            framework: Optional framework (e.g., FastAPI, Express, Gin).
            reference_dir: Directory containing ``<language>.yml``
                reference templates. Defaults to ``reference/ci/`` shipped
                with the package.

        Raises:
            ValueError: If language is not supported.
        """
        self.orchestrator = orchestrator

        language = language.lower()
        if language not in LANGUAGE_CONFIGS:
            supported = ", ".join(LANGUAGE_CONFIGS.keys())
            msg = f"Unsupported language: {language}. Supported: {supported}"
            raise ValueError(msg)

        self.language = language
        self.framework = framework
        config = LANGUAGE_CONFIGS[language]
        self.test_framework = config["test_framework"]
        self.supported_versions = config["supported_versions"]
        self.reference_dir = reference_dir or REFERENCE_CI_DIR

    def generate_workflow(self) -> CIWorkflow:
        """Generate a customized CI workflow.

        By default this renders the deterministic ``reference/ci/<language>.yml``
        baseline through Jinja2 (no API call). If an
        :class:`AIOrchestrator` was passed at construction time the legacy
        Claude-generated path is used instead, preserving backward
        compatibility for callers that rely on AI tuning.

        Returns:
            CIWorkflow with generated YAML content and validation status.

        Raises:
            GenerationError: If AI generation fails (orchestrator path).
            ValueError: If validation fails or template missing.
        """
        if self.orchestrator is None:
            return self.generate_workflow_from_template()

        # Build context for AI generation
        language_config = LANGUAGE_CONFIGS[self.language]
        context = self._build_generation_context(language_config)

        # Generate workflow using AI
        result = self._generate_with_ai(context)

        # Validate generated workflow
        return self._validate_and_parse(result.content)

    def generate_workflow_from_template(
        self,
        *,
        project_name: str | None = None,
    ) -> CIWorkflow:
        """Render the deterministic CI template for the configured language.

        Reads ``reference/ci/<language>.yml`` and runs it through Jinja2 so
        callers can substitute the project name (or any future
        placeholders). The reference templates are valid YAML even before
        rendering — Jinja syntax uses the custom delimiters
        ``<<% project_name %>>`` (see the ``Environment`` configuration
        below) so existing GitHub Actions ``${{ … }}`` expressions in
        the templates pass through verbatim. Files without placeholders
        are returned essentially unchanged.

        Args:
            project_name: Optional project name to substitute into any
                ``<<% project_name %>>`` placeholders. ``None`` is
                coerced to ``""`` so the literal string ``"None"`` is
                never baked into the rendered YAML.

        Returns:
            ``CIWorkflow`` with the rendered, validated YAML.

        Raises:
            FileNotFoundError: If no reference template exists for the
                language.
            jinja2.UndefinedError: If a template references a
                placeholder that has not been wired through this
                method's ``render(...)`` kwargs (raised eagerly thanks
                to ``StrictUndefined``).
            ValueError: If the rendered YAML fails structural validation.
        """
        template_path = self.reference_dir / f"{self.language}.yml"
        if not template_path.exists():
            msg = (
                f"No reference CI template for language '{self.language}': "
                f"expected {template_path}"
            )
            raise FileNotFoundError(msg)

        raw = template_path.read_text(encoding="utf-8")

        # The reference YAMLs already contain GitHub Actions ``${{ }}``
        # expressions, which collide with Jinja2's default delimiters.
        # Use custom delimiters (``<<%`` / ``%>>``) so existing templates
        # render unchanged unless a maintainer opts in to a placeholder.
        # autoescape stays off because the rendered output is YAML, not
        # HTML — the Jinja XSS warning does not apply.
        env = Environment(  # nosec B701 — YAML output, no HTML/XSS surface
            variable_start_string="<<%",
            variable_end_string="%>>",
            block_start_string="<%",
            block_end_string="%>",
            comment_start_string="<#",
            comment_end_string="#>",
            autoescape=False,  # noqa: S701 — YAML output
            keep_trailing_newline=True,
            undefined=StrictUndefined,
        )
        # Coerce ``project_name=None`` to "" so a template that references
        # the placeholder does not get the literal string "None" silently
        # baked into the output. ``StrictUndefined`` makes any *other*
        # placeholder added later but not passed here raise loudly at
        # render time instead of silently emitting the empty string.
        rendered = env.from_string(raw).render(
            project_name=project_name or "",
            language=self.language,
        )

        return self._validate_and_parse(rendered)

    def _build_generation_context(
        self,
        language_config: dict[str, Any],
    ) -> str:
        """Build context for AI generation.

        Args:
            language_config: Language-specific configuration.

        Returns:
            Formatted context string for prompt injection.
        """
        versions = ", ".join(language_config["supported_versions"])
        framework_info = f"Framework: {self.framework}" if self.framework else ""

        return f"""
Language: {self.language.upper()}
{framework_info}
Test Framework: {language_config['test_framework']}
Linters: {', '.join(language_config['linters'])}
Security Tools: {', '.join(language_config['security_tools'])}
Supported Versions: {versions}
Package Manager: {language_config['package_manager']}

Quality Standards:
- Code Coverage: ≥90% minimum
- Branch Coverage: ≥85% minimum
- Mutation Score: ≥80% minimum (on main branch)
- Docstring/Comment Coverage: ≥95%
- No critical/high security vulnerabilities
- All linters must pass
- All tests must pass
- Type checking must pass (if applicable)

The CI workflow MUST:
1. Run linting and formatting checks
2. Run type checking (if applicable)
3. Run tests with coverage measurement
4. Run security scans
5. Support matrix testing for multiple language versions
6. Cache dependencies to speed up runs
7. Upload coverage reports
8. Run mutation testing on main branch only
9. Have clear job names and step descriptions
10. Use appropriate GitHub Actions
"""

    def _generate_with_ai(self, context: str) -> GenerationResult:
        """Generate workflow using AI orchestrator.

        Args:
            context: Context information for generation.

        Returns:
            GenerationResult with workflow YAML content.

        Raises:
            GenerationError: If generation fails.
            ValueError: If orchestrator is None.
        """
        if self.orchestrator is None:
            msg = "AI orchestrator required for generate_with_ai()"
            raise ValueError(msg)

        prompt = f"""You are a GitHub Actions CI/CD expert. Generate a production-grade
GitHub Actions workflow file for a {self.language.upper()} project.

Context:
{context}

Generate a complete, valid GitHub Actions workflow in YAML format that:
1. MUST define a 'quality' job with linting, security checks, tests, coverage
2. Can optionally include additional jobs (complexity, build, mutation, etc.)
3. Uses appropriate language-specific tools and commands
4. Includes matrix testing for multiple versions
5. Has proper caching for dependencies
6. Uploads artifacts and coverage reports
7. Enforces all quality standards mentioned above
8. Is ready to be saved as .github/workflows/ci.yml

IMPORTANT: The 'quality' job is REQUIRED and must include test execution.
Additional jobs like 'test', 'mutation', 'complexity', 'build' are OPTIONAL.

Output ONLY valid YAML - no markdown, no explanations, no code fences.
Start with 'name:' and end with the last workflow configuration line."""

        return self.orchestrator.generate(
            prompt=prompt,
            output_format="yaml",
        )

    def _validate_structure(self, parsed: dict[str, Any]) -> None:
        """Validate basic workflow structure.

        Args:
            parsed: Parsed YAML content as dictionary.

        Raises:
            TypeError: If parsed content is not a dictionary.
        """
        if not isinstance(parsed, dict):
            msg = "Generated workflow must be a YAML dictionary"
            raise TypeError(msg)

    def _validate_name_field(self, parsed: dict[str, Any]) -> None:
        """Validate workflow has name field.

        Args:
            parsed: Parsed YAML content.

        Raises:
            ValueError: If 'name' field is missing.
        """
        if "name" not in parsed:
            msg = "Workflow must have a 'name' field"
            raise ValueError(msg)

    def _validate_jobs_field(self, parsed: dict[str, Any]) -> None:
        """Validate workflow has jobs field.

        Args:
            parsed: Parsed YAML content.

        Raises:
            ValueError: If 'jobs' field is missing.
        """
        if "jobs" not in parsed:
            msg = "Workflow must have 'jobs' field"
            raise ValueError(msg)

    def _validate_jobs_type(self, parsed: dict[str, Any]) -> None:
        """Validate jobs field is a dictionary.

        Args:
            parsed: Parsed YAML content.

        Raises:
            TypeError: If jobs field is not a dictionary.
        """
        if not isinstance(parsed["jobs"], dict):
            msg = "Jobs must be a dictionary"
            raise TypeError(msg)

    def _validate_required_jobs(self, parsed: dict[str, Any]) -> None:
        """Validate required jobs are present.

        Args:
            parsed: Parsed YAML content.

        Raises:
            ValueError: If required jobs are missing.

        Note:
            Only requires 'quality' job. The 'test' job is optional as tests
            can be run within the quality job (as in reference/ci/python.yml).
            This matches the pattern used in reference CI workflows.
        """
        required_jobs = {"quality"}
        actual_jobs = set(parsed["jobs"].keys())
        missing_jobs = required_jobs - actual_jobs
        if missing_jobs:
            msg = f"Workflow missing required jobs: {missing_jobs}"
            raise ValueError(msg)

    def _validate_quality_job(self, parsed: dict[str, Any]) -> None:
        """Validate quality job has steps.

        Args:
            parsed: Parsed YAML content.

        Raises:
            ValueError: If quality job has no steps.
        """
        quality_job = parsed["jobs"].get("quality", {})
        if "steps" not in quality_job or not quality_job["steps"]:
            msg = "Quality job must have at least one step"
            raise ValueError(msg)

    def _validate_test_job(self, parsed: dict[str, Any]) -> None:
        """Validate test job has steps if present.

        Args:
            parsed: Parsed YAML content.

        Raises:
            ValueError: If test job exists but has no steps.

        Note:
            Test job is optional (Issue #165). Only validates if present.
        """
        test_job = parsed["jobs"].get("test")
        # Only validate if test job exists and has no steps
        if test_job is not None and ("steps" not in test_job or not test_job["steps"]):
            msg = "Test job must have at least one step"
            raise ValueError(msg)

    def _validate_and_parse(self, yaml_content: str) -> CIWorkflow:
        """Validate and parse generated YAML workflow.

        Args:
            yaml_content: Raw YAML content from generation.

        Returns:
            CIWorkflow with validation results.

        Raises:
            ValueError: If YAML is invalid.
        """
        try:
            # Strip markdown fences if present (AI sometimes adds them)
            clean_yaml = strip_markdown_fences(yaml_content)

            # Parse YAML to validate structure - use StringIO for cleanup
            with io.StringIO(clean_yaml) as yaml_stream:
                parsed = yaml.safe_load(yaml_stream)

            # Run all validations
            self._validate_structure(parsed)
            self._validate_name_field(parsed)
            self._validate_jobs_field(parsed)
            self._validate_jobs_type(parsed)
            self._validate_required_jobs(parsed)
            self._validate_quality_job(parsed)
            self._validate_test_job(parsed)

        except yaml.YAMLError as e:
            msg = f"Invalid YAML in generated workflow: {e}"
            raise ValueError(msg) from e
        except (KeyError, TypeError, ValueError) as e:
            msg = f"Workflow validation failed: {e}"
            raise ValueError(msg) from e
        else:
            return CIWorkflow(
                name=parsed.get("name", "CI"),
                content=clean_yaml,
                language=self.language,
                is_valid=True,
                error_message=None,
            )

    def generate(self) -> dict[str, Any]:
        """Generate complete CI infrastructure.

        This is the main entry point for BaseGenerator interface.
        Generates workflow and returns as dictionary.

        Returns:
            Dictionary with 'workflow' key containing CIWorkflow.

        Raises:
            GenerationError: If generation fails.
        """
        workflow = self.generate_workflow()

        return {
            "workflow": workflow,
            "language": self.language,
            "framework": self.framework,
        }

    @staticmethod
    def get_supported_languages() -> list[str]:
        """Get list of supported languages.

        Returns:
            List of supported language identifiers.
        """
        return sorted(LANGUAGE_CONFIGS.keys())

    @staticmethod
    def get_language_config(language: str) -> dict[str, Any]:
        """Get configuration for a specific language.

        Args:
            language: Language identifier (python, typescript, go, etc.).

        Returns:
            Language configuration dictionary.

        Raises:
            ValueError: If language is not supported.
        """
        language = language.lower()
        if language not in LANGUAGE_CONFIGS:
            msg = f"Unsupported language: {language}"
            raise ValueError(msg)

        return LANGUAGE_CONFIGS[language].copy()
