"""CI pipeline generator for target projects.

Generates GitHub Actions workflows customized to target project language
and framework. Integrates reference CI configurations and quality standards
from MAXIMUM_QUALITY_ENGINEERING.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

import yaml

from start_green_stay_green.generators.base import BaseGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator
    from start_green_stay_green.ai.orchestrator import GenerationResult

# Supported languages and their configurations
LANGUAGE_CONFIGS: dict[str, dict[str, Any]] = {
    "python": {
        "test_framework": "pytest",
        "linters": ["ruff", "pylint", "mypy"],
        "formatters": ["black", "ruff"],
        "security_tools": ["bandit", "safety"],
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
        orchestrator: AIOrchestrator,
        language: str,
        *,
        framework: str | None = None,
    ) -> None:
        """Initialize CI Generator.

        Args:
            orchestrator: AIOrchestrator instance for generation.
            language: Target language (python, typescript, go, rust, java,
                csharp, ruby).
            framework: Optional framework (e.g., FastAPI, Express, Gin).

        Raises:
            ValueError: If language is not supported.
        """
        super().__init__(orchestrator)

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

    def generate_workflow(self) -> CIWorkflow:
        """Generate customized CI workflow.

        Creates a complete GitHub Actions workflow file adapted to the target
        language and framework. Includes quality checks, testing matrix, coverage
        analysis, and optional mutation testing.

        Returns:
            CIWorkflow with generated YAML content and validation status.

        Raises:
            GenerationError: If AI generation fails or output is invalid.
            ValueError: If validation fails.
        """
        # Build context for AI generation
        language_config = LANGUAGE_CONFIGS[self.language]
        context = self._build_generation_context(language_config)

        # Generate workflow using AI
        result = self._generate_with_ai(context)

        # Validate generated workflow
        return self._validate_and_parse(result.content)


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
        """
        prompt = f"""You are a GitHub Actions CI/CD expert. Generate a production-grade
GitHub Actions workflow file for a {self.language.upper()} project.

Context:
{context}

Generate a complete, valid GitHub Actions workflow in YAML format that:
1. Defines all necessary jobs (quality, test, mutation, security, etc.)
2. Uses appropriate language-specific tools and commands
3. Includes matrix testing for multiple versions
4. Has proper caching for dependencies
5. Uploads artifacts and coverage reports
6. Enforces all quality standards mentioned above
7. Is ready to be saved as .github/workflows/ci.yml

Output ONLY valid YAML - no markdown, no explanations, no code fences.
Start with 'name:' and end with the last workflow configuration line."""

        return self.orchestrator.generate(
            prompt=prompt,
            output_format="yaml",
        )


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
            # Parse YAML to validate structure
            parsed = yaml.safe_load(yaml_content)

            # Basic structure validation
            if not isinstance(parsed, dict):
                msg = "Generated workflow must be a YAML dictionary"
                raise TypeError(msg)  # noqa: TRY301 - Direct validation in parsing context

            if "name" not in parsed:
                msg = "Workflow must have a 'name' field"
                raise ValueError(msg)  # noqa: TRY301 - Direct validation in parsing context

            if "jobs" not in parsed:
                msg = "Workflow must have 'jobs' field"
                raise ValueError(msg)  # noqa: TRY301 - Direct validation in parsing context

            if not isinstance(parsed["jobs"], dict):
                msg = "Jobs must be a dictionary"
                raise TypeError(msg)  # noqa: TRY301 - Direct validation in parsing context

            # Validate required jobs
            required_jobs = {"quality", "test"}
            actual_jobs = set(parsed["jobs"].keys())
            missing_jobs = required_jobs - actual_jobs

            if missing_jobs:
                msg = f"Workflow missing required jobs: {missing_jobs}"
                raise ValueError(msg)  # noqa: TRY301 - Direct validation in parsing context

            # Validate quality job has steps
            quality_job = parsed["jobs"].get("quality", {})
            if "steps" not in quality_job or not quality_job["steps"]:
                msg = "Quality job must have at least one step"
                raise ValueError(msg)  # noqa: TRY301 - Direct validation in parsing context

            # Validate test job has steps and matrix (if applicable)
            test_job = parsed["jobs"].get("test", {})
            if "steps" not in test_job or not test_job["steps"]:
                msg = "Test job must have at least one step"
                raise ValueError(msg)  # noqa: TRY301 - Direct validation in parsing context

            return CIWorkflow(
                name=parsed.get("name", "CI"),
                content=yaml_content,
                language=self.language,
                is_valid=True,
                error_message=None,
            )

        except yaml.YAMLError as e:
            msg = f"Invalid YAML in generated workflow: {e}"
            raise ValueError(msg) from e
        except (KeyError, TypeError, ValueError) as e:
            msg = f"Workflow validation failed: {e}"
            raise ValueError(msg) from e

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
