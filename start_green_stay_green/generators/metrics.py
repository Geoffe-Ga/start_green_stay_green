"""Quality metrics dashboard generator.

Generates quality metrics tracking configuration per MAXIMUM_QUALITY_ENGINEERING.md
Part 9.1. Supports code coverage, mutation testing, complexity analysis, and more
across multiple programming languages.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import html
import logging
from pathlib import Path
import re
from typing import Any
from typing import TYPE_CHECKING

import yaml

from start_green_stay_green.generators.base import BaseGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


logger = logging.getLogger(__name__)

# Constants
MAX_PERCENTAGE_THRESHOLD = 100

# Security: Project name validation pattern (alphanumeric, hyphens, underscores only)
PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Security: Dangerous paths that should never be used as output directories
DANGEROUS_PATHS = {
    "/etc",
    "/sys",
    "/proc",
    "/dev",
    "/boot",
    "/root",
    "/bin",
    "/sbin",
    "/usr/bin",
    "/usr/sbin",
    "/var/run",
    "/var/log",
    "~/.ssh",
    "~/.gnupg",
    "/home/.ssh",
    "/Users/.ssh",
}


@dataclass(frozen=True)
class MetricConfig:
    """Configuration for a single quality metric.

    Attributes:
        name: Metric name (e.g., "Code Coverage").
        threshold: Quality threshold (e.g., "≥90%").
        tool: Tool used to measure (e.g., "pytest-cov").
        enabled: Whether metric is enabled for this project.
        badge_available: Whether GitHub badge can be generated.
        ci_enforced: Whether CI should enforce threshold.
    """

    name: str
    threshold: str
    tool: str
    enabled: bool = True
    badge_available: bool = True
    ci_enforced: bool = True


@dataclass
class MetricsGenerationConfig:
    """Configuration for metrics generation.

    Attributes:
        language: Target programming language.
        project_name: Name of the project.
        coverage_threshold: Code coverage threshold (0-100).
        branch_coverage_threshold: Branch coverage threshold (0-100).
        mutation_threshold: Mutation score threshold (0-100).
        complexity_threshold: Max cyclomatic complexity per function.
        cognitive_complexity_threshold: Max cognitive complexity.
        maintainability_threshold: Min maintainability index.
        debt_ratio_threshold: Max technical debt ratio (0-100).
        doc_coverage_threshold: Documentation coverage threshold (0-100).
        dependency_freshness_days: Max dependency age in days.
        enable_sonarqube: Whether to generate SonarQube config.
        enable_badges: Whether to generate GitHub badges.
        enable_dashboard: Whether to generate dashboard template.
    """

    language: str
    project_name: str
    coverage_threshold: int = 90
    branch_coverage_threshold: int = 85
    mutation_threshold: int = 80
    complexity_threshold: int = 10
    cognitive_complexity_threshold: int = 15
    maintainability_threshold: int = 20
    debt_ratio_threshold: int = 5
    doc_coverage_threshold: int = 95
    dependency_freshness_days: int = 30
    enable_sonarqube: bool = False
    enable_badges: bool = True
    enable_dashboard: bool = True


@dataclass
class MetricsGenerationResult:
    """Result from metrics generation.

    Attributes:
        metrics_config: Generated metrics configuration.
        sonarqube_config: SonarQube configuration (if enabled).
        badges: List of GitHub badge markdown strings.
        dashboard_template: Dashboard HTML template (if enabled).
        ci_config: CI integration snippets.
    """

    metrics_config: dict[str, Any]
    sonarqube_config: str | None = None
    badges: list[str] = field(default_factory=list)
    dashboard_template: str | None = None
    ci_config: dict[str, Any] = field(default_factory=dict)


# Metric definitions per MAXIMUM_QUALITY_ENGINEERING.md Part 9.1
STANDARD_METRICS = {
    "code_coverage": MetricConfig(
        name="Code Coverage",
        threshold="≥90%",
        tool="pytest-cov / jest",
        badge_available=True,
        ci_enforced=True,
    ),
    "branch_coverage": MetricConfig(
        name="Branch Coverage",
        threshold="≥85%",
        tool="pytest-cov / jest",
        badge_available=True,
        ci_enforced=True,
    ),
    "mutation_score": MetricConfig(
        name="Mutation Score",
        threshold="≥80%",
        tool="mutmut / stryker",
        badge_available=False,
        ci_enforced=False,  # Periodic quality gate, not continuous
    ),
    "cyclomatic_complexity": MetricConfig(
        name="Cyclomatic Complexity",
        threshold="≤10",
        tool="radon / eslint",
        badge_available=False,
        ci_enforced=True,
    ),
    "cognitive_complexity": MetricConfig(
        name="Cognitive Complexity",
        threshold="≤15",
        tool="sonarqube",
        badge_available=False,
        ci_enforced=False,
    ),
    "maintainability_index": MetricConfig(
        name="Maintainability Index",
        threshold="≥20",
        tool="radon",
        badge_available=False,
        ci_enforced=True,
    ),
    "technical_debt_ratio": MetricConfig(
        name="Technical Debt Ratio",
        threshold="≤5%",
        tool="sonarqube",
        badge_available=True,
        ci_enforced=False,
    ),
    "documentation_coverage": MetricConfig(
        name="Documentation Coverage",
        threshold="≥95%",
        tool="interrogate",
        badge_available=True,
        ci_enforced=True,
    ),
    "dependency_freshness": MetricConfig(
        name="Dependency Freshness",
        threshold="≤30 days",
        tool="npm-check-updates / pip-audit",
        badge_available=False,
        ci_enforced=False,
    ),
    "security_vulnerabilities": MetricConfig(
        name="Security Vulnerabilities",
        threshold="0 critical/high",
        tool="safety / npm audit",
        badge_available=True,
        ci_enforced=True,
    ),
}


# Language-specific tool mappings
LANGUAGE_TOOLS: dict[str, dict[str, str]] = {
    "python": {
        "coverage": "pytest-cov",
        "mutation": "mutmut",
        "complexity": "radon",
        "documentation": "interrogate",
        "security": "safety",
        "dependency_check": "pip-audit",
    },
    "typescript": {
        "coverage": "jest",
        "mutation": "stryker",
        "complexity": "eslint",
        "documentation": "typedoc",
        "security": "npm audit",
        "dependency_check": "npm-check-updates",
    },
    "javascript": {
        "coverage": "jest",
        "mutation": "stryker",
        "complexity": "eslint",
        "documentation": "jsdoc",
        "security": "npm audit",
        "dependency_check": "npm-check-updates",
    },
    "go": {
        "coverage": "go test -cover",
        "mutation": "go-mutesting",
        "complexity": "gocyclo",
        "documentation": "godoc",
        "security": "gosec",
        "dependency_check": "go list -u -m all",
    },
    "rust": {
        "coverage": "cargo-tarpaulin",
        "mutation": "cargo-mutants",
        "complexity": "cargo-clippy",
        "documentation": "rustdoc",
        "security": "cargo-audit",
        "dependency_check": "cargo-outdated",
    },
}


class MetricsGenerator(BaseGenerator):
    """Generate quality metrics tracking configuration.

    Creates comprehensive quality metrics dashboard configuration including:
    - Metrics tracking for 10 quality dimensions
    - SonarQube configuration (optional)
    - GitHub badge generation
    - Dashboard HTML template
    - CI integration configuration

    Attributes:
        orchestrator: Optional AI orchestrator for customization.
        config: Configuration for metrics generation.
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator | None,
        config: MetricsGenerationConfig,
    ) -> None:
        """Initialize MetricsGenerator.

        Args:
            orchestrator: Optional AI orchestrator for generation.
            config: Configuration for metrics generation.

        Raises:
            ValueError: If configuration is invalid.
        """
        self.orchestrator = orchestrator
        self.config = config
        self._validate_config()

    def _validate_threshold(self, value: int, name: str) -> None:
        """Validate a threshold value is within valid range.

        Args:
            value: Threshold value to validate
            name: Name of threshold for error messages

        Raises:
            ValueError: If threshold is out of range.
        """
        if not 0 <= value <= MAX_PERCENTAGE_THRESHOLD:
            msg = f"{name} threshold must be between 0 and {MAX_PERCENTAGE_THRESHOLD}"
            raise ValueError(msg)

    def _validate_non_negative(self, value: int, name: str) -> None:
        """Validate that a value is non-negative.

        Args:
            value: Value to validate
            name: Name of value for error messages

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            msg = f"{name} must be non-negative (got {value})"
            raise ValueError(msg)

    def _validate_project_name(self, project_name: str) -> None:
        """Validate project name for security (prevent injection attacks).

        Args:
            project_name: Project name to validate

        Raises:
            ValueError: If project name contains invalid characters.
        """
        if not PROJECT_NAME_PATTERN.match(project_name):
            msg = (
                f"Invalid project name '{project_name}'. "
                "Project names must contain only alphanumeric characters, "
                "hyphens, and underscores."
            )
            raise ValueError(msg)

    def _validate_output_dir(self, output_dir: Path) -> None:
        """Validate output directory to prevent path traversal attacks.

        Args:
            output_dir: Output directory to validate

        Raises:
            ValueError: If output directory is a dangerous system path.
        """
        # Resolve to absolute path
        resolved_path = output_dir.resolve()
        resolved_str = str(resolved_path)

        # Check against dangerous paths
        for dangerous_path in DANGEROUS_PATHS:
            dangerous_resolved = Path(dangerous_path).expanduser().resolve()
            if (
                resolved_path == dangerous_resolved
                or str(dangerous_resolved) in resolved_str
            ):
                msg = (
                    f"Output directory '{output_dir}' resolves to dangerous "
                    f"system path '{resolved_path}'. "
                    "Cannot write to system directories."
                )
                raise ValueError(msg)

    def _validate_config(self) -> None:
        """Validate metrics generation configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        if not self.config.language:
            msg = "Language cannot be empty"
            raise ValueError(msg)

        if not self.config.project_name:
            msg = "Project name cannot be empty"
            raise ValueError(msg)

        # Security: Validate project name (prevent injection)
        self._validate_project_name(self.config.project_name)

        if self.config.language not in LANGUAGE_TOOLS:
            msg = f"Unsupported language: {self.config.language}"
            raise ValueError(msg)

        # Validate percentage-based threshold ranges (0-100)
        self._validate_threshold(self.config.coverage_threshold, "Coverage")
        self._validate_threshold(
            self.config.branch_coverage_threshold, "Branch coverage"
        )
        self._validate_threshold(self.config.mutation_threshold, "Mutation")
        self._validate_threshold(
            self.config.debt_ratio_threshold, "Technical debt ratio"
        )
        self._validate_threshold(
            self.config.doc_coverage_threshold, "Documentation coverage"
        )

        # Validate non-percentage thresholds (must be non-negative)
        self._validate_non_negative(
            self.config.complexity_threshold, "Cyclomatic complexity threshold"
        )
        self._validate_non_negative(
            self.config.cognitive_complexity_threshold,
            "Cognitive complexity threshold",
        )
        self._validate_non_negative(
            self.config.maintainability_threshold, "Maintainability index threshold"
        )
        self._validate_non_negative(
            self.config.dependency_freshness_days, "Dependency freshness days"
        )

    def _get_tool_for_language(self, metric_type: str) -> str:
        """Get appropriate tool for language and metric type.

        Args:
            metric_type: Type of metric (coverage, mutation, etc.).

        Returns:
            Tool name for the specified metric type.
        """
        tools = LANGUAGE_TOOLS.get(self.config.language, {})
        return tools.get(metric_type, "unknown")

    def _generate_metrics_config(self) -> dict[str, Any]:
        """Generate metrics configuration dictionary.

        Returns:
            Metrics configuration with all thresholds and tools.
        """
        return {
            "project": self.config.project_name,
            "language": self.config.language,
            "metrics": {
                "code_coverage": {
                    "enabled": True,
                    "threshold": self.config.coverage_threshold,
                    "tool": self._get_tool_for_language("coverage"),
                    "enforce_in_ci": True,
                },
                "branch_coverage": {
                    "enabled": True,
                    "threshold": self.config.branch_coverage_threshold,
                    "tool": self._get_tool_for_language("coverage"),
                    "enforce_in_ci": True,
                },
                "mutation_score": {
                    "enabled": True,
                    "threshold": self.config.mutation_threshold,
                    "tool": self._get_tool_for_language("mutation"),
                    "enforce_in_ci": False,  # Periodic quality gate
                    "notes": "Run periodically for critical infrastructure",
                },
                "cyclomatic_complexity": {
                    "enabled": True,
                    "threshold": self.config.complexity_threshold,
                    "tool": self._get_tool_for_language("complexity"),
                    "enforce_in_ci": True,
                },
                "cognitive_complexity": {
                    "enabled": self.config.enable_sonarqube,
                    "threshold": self.config.cognitive_complexity_threshold,
                    "tool": "sonarqube",
                    "enforce_in_ci": False,
                },
                "maintainability_index": {
                    "enabled": self.config.language == "python",
                    "threshold": self.config.maintainability_threshold,
                    "tool": "radon",
                    "enforce_in_ci": True,
                },
                "technical_debt_ratio": {
                    "enabled": self.config.enable_sonarqube,
                    "threshold": self.config.debt_ratio_threshold,
                    "tool": "sonarqube",
                    "enforce_in_ci": False,
                },
                "documentation_coverage": {
                    "enabled": True,
                    "threshold": self.config.doc_coverage_threshold,
                    "tool": self._get_tool_for_language("documentation"),
                    "enforce_in_ci": True,
                },
                "dependency_freshness": {
                    "enabled": True,
                    "threshold_days": self.config.dependency_freshness_days,
                    "tool": self._get_tool_for_language("dependency_check"),
                    "enforce_in_ci": False,
                },
                "security_vulnerabilities": {
                    "enabled": True,
                    "threshold": "0 critical/high",
                    "tool": self._get_tool_for_language("security"),
                    "enforce_in_ci": True,
                },
            },
        }

    def _generate_sonarqube_config(self) -> str | None:
        """Generate SonarQube configuration.

        Returns:
            SonarQube properties file content, or None if not enabled.
        """
        if not self.config.enable_sonarqube:
            return None

        config = [
            f"sonar.projectKey={self.config.project_name}",
            f"sonar.projectName={self.config.project_name}",
            "sonar.projectVersion=1.0",
            "",
            "# Source directories",
            "sonar.sources=.",
            "",
            "# Coverage",
            f"sonar.coverage.threshold={self.config.coverage_threshold}",
            "",
            "# Complexity thresholds",
            f"sonar.complexity.threshold={self.config.complexity_threshold}",
            f"sonar.cognitive.complexity.threshold="
            f"{self.config.cognitive_complexity_threshold}",
            "",
            "# Technical debt",
            f"sonar.debt.ratio.threshold={self.config.debt_ratio_threshold}",
            "",
        ]

        # Language-specific settings
        if self.config.language == "python":
            config.extend(
                [
                    "# Python settings",
                    "sonar.language=py",
                    "sonar.python.coverage.reportPaths=coverage.xml",
                    "sonar.python.version=3.11,3.12",
                ]
            )
        elif self.config.language in ("typescript", "javascript"):
            config.extend(
                [
                    "# JavaScript/TypeScript settings",
                    "sonar.language=js",
                    "sonar.javascript.lcov.reportPaths=coverage/lcov.info",
                ]
            )

        return "\n".join(config)

    def _generate_badges(self) -> list[str]:
        """Generate GitHub badge markdown strings.

        Returns:
            List of badge markdown strings for README.md.
        """
        if not self.config.enable_badges:
            return []

        project = self.config.project_name
        badges = []

        # Coverage badge
        badges.append(
            f"![Coverage](https://img.shields.io/codecov/c/github/{project}"
            f"?label=Coverage&threshold={self.config.coverage_threshold}%25)"
        )

        # Documentation badge (Python)
        if self.config.language == "python":
            badges.append(
                f"![Docs](https://img.shields.io/badge/docs-"
                f"{self.config.doc_coverage_threshold}%25-brightgreen)"
            )

        # Security and Quality badges
        badges.extend(
            [
                "![Security](https://img.shields.io/badge/security-passing-brightgreen)",
                "![Quality](https://img.shields.io/badge/quality-maximum-brightgreen)",
            ]
        )

        # SonarQube badge (if enabled)
        if self.config.enable_sonarqube:
            badges.append(
                f"![SonarQube](https://sonarcloud.io/api/project_badges/measure"
                f"?project={project}&metric=alert_status)"
            )

        return badges

    def _generate_dashboard_template(self) -> str | None:
        """Generate HTML dashboard template.

        Returns:
            HTML template for metrics dashboard, or None if not enabled.
        """
        if not self.config.enable_dashboard:
            return None

        # Security: HTML-escape project name to prevent XSS
        safe_project_name = html.escape(self.config.project_name)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_project_name} - Quality Metrics Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto',
                         'Helvetica', 'Arial', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: #58a6ff;
        }}
        .subtitle {{
            color: #8b949e;
            margin-bottom: 2rem;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .metric-card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 1.5rem;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-2px);
            border-color: #58a6ff;
        }}
        .metric-name {{
            font-size: 0.875rem;
            color: #8b949e;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 0.5rem;
        }}
        .metric-threshold {{
            font-size: 0.875rem;
            color: #8b949e;
        }}
        .metric-status {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 0.5rem;
        }}
        .status-pass {{
            background: #238636;
            color: #fff;
        }}
        .status-warn {{
            background: #9e6a03;
            color: #fff;
        }}
        .status-fail {{
            background: #da3633;
            color: #fff;
        }}
        .footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #30363d;
            color: #8b949e;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{safe_project_name}</h1>
        <p class="subtitle">Quality Metrics Dashboard</p>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-name">Code Coverage</div>
                <div class="metric-value" id="coverage-value">--</div>
                <div class="metric-threshold">
                    Threshold: ≥{self.config.coverage_threshold}%
                </div>
                <div class="metric-status status-pass" id="coverage-status">
                    PASSING
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-name">Branch Coverage</div>
                <div class="metric-value" id="branch-value">--</div>
                <div class="metric-threshold">
                    Threshold: ≥{self.config.branch_coverage_threshold}%
                </div>
                <div class="metric-status status-pass" id="branch-status">PASSING</div>
            </div>

            <div class="metric-card">
                <div class="metric-name">Mutation Score</div>
                <div class="metric-value" id="mutation-value">--</div>
                <div class="metric-threshold">
                    Threshold: ≥{self.config.mutation_threshold}%
                </div>
                <div class="metric-status status-pass" id="mutation-status">
                    PASSING
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-name">Cyclomatic Complexity</div>
                <div class="metric-value" id="complexity-value">--</div>
                <div class="metric-threshold">
                    Threshold: ≤{self.config.complexity_threshold}
                </div>
                <div class="metric-status status-pass" id="complexity-status">
                    PASSING
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-name">Documentation Coverage</div>
                <div class="metric-value" id="docs-value">--</div>
                <div class="metric-threshold">
                    Threshold: ≥{self.config.doc_coverage_threshold}%
                </div>
                <div class="metric-status status-pass" id="docs-status">PASSING</div>
            </div>

            <div class="metric-card">
                <div class="metric-name">Security Issues</div>
                <div class="metric-value" id="security-value">--</div>
                <div class="metric-threshold">Threshold: 0 critical/high</div>
                <div class="metric-status status-pass" id="security-status">
                    PASSING
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Start Green Stay Green</p>
            <p>Last updated: <span id="last-updated">--</span></p>
        </div>
    </div>

    <script>
        // Production workflow: Fetch metrics from CI artifacts
        // Supports: local metrics.json, GitHub Pages, or GitHub Actions artifacts

        async function loadMetrics() {{
            try {{
                // Try to load from local metrics.json (same directory as dashboard)
                const response = await fetch('metrics.json');
                if (!response.ok) {{
                    throw new Error(`HTTP ${{response.status}}`);
                }}

                const data = await response.json();
                updateDashboard(data);
            }} catch (error) {{
                console.warn('Could not load metrics.json:', error.message);
                // Fallback: Show placeholder or error state
                updatePlaceholder();
            }}
        }}

        function updateDashboard(data) {{
            const metrics = data.metrics;
            const thresholds = data.thresholds;

            // Update timestamp
            document.getElementById('last-updated').textContent =
                new Date(data.timestamp).toLocaleString();

            // Coverage
            if (metrics.coverage !== undefined) {{
                updateMetric('coverage', metrics.coverage, '%',
                    metrics.coverage >= thresholds.coverage);
            }}

            // Branch Coverage
            if (metrics.branch_coverage !== undefined) {{
                updateMetric('branch', metrics.branch_coverage, '%',
                    metrics.branch_coverage >= thresholds.branch_coverage);
            }}

            // Mutation Score
            if (metrics.mutation_score !== undefined) {{
                updateMetric('mutation', metrics.mutation_score, '%',
                    metrics.mutation_score >= thresholds.mutation_score);
            }}

            // Complexity
            if (metrics.complexity_avg !== undefined) {{
                if (metrics.complexity_avg === null) {{
                    document.getElementById('complexity-value').textContent = 'N/A';
                    updateStatus('complexity', 'NO DATA', false);
                }} else {{
                    updateMetric('complexity', metrics.complexity_avg, '',
                        metrics.complexity_avg <= thresholds.complexity);
                }}
            }}

            // Documentation
            if (metrics.docs_coverage !== undefined) {{
                if (metrics.docs_coverage === null) {{
                    document.getElementById('docs-value').textContent = 'N/A';
                    updateStatus('docs', 'NO DATA', false);
                }} else {{
                    updateMetric('docs', metrics.docs_coverage, '%',
                        metrics.docs_coverage >= thresholds.docs_coverage);
                }}
            }}

            // Security
            if (metrics.security_issues !== undefined) {{
                const elem = document.getElementById('security-value');
                elem.textContent = metrics.security_issues;
                updateStatus('security',
                    metrics.security_issues === 0 ? 'PASSING' : 'FAILING',
                    metrics.security_issues === 0);
            }}
        }}

        function updateMetric(name, value, suffix, passing) {{
            const elem = document.getElementById(`${{name}}-value`);
            elem.textContent = value.toFixed(2) + suffix;
            updateStatus(name, passing ? 'PASSING' : 'FAILING', passing);
        }}

        function updateStatus(name, text, passing) {{
            const elem = document.getElementById(`${{name}}-status`);
            elem.textContent = text;
            const statusClass = passing ? 'status-pass' : 'status-fail';
            elem.className = 'metric-status ' + statusClass;
        }}

        function updatePlaceholder() {{
            // Show friendly message when metrics.json is not available
            document.getElementById('last-updated').textContent = 'No data available';
            const statusElements = document.querySelectorAll('.metric-status');
            statusElements.forEach(elem => {{
                elem.textContent = 'NO DATA';
                elem.className = 'metric-status status-warn';
            }});
        }}

        // Load metrics on page load
        document.addEventListener('DOMContentLoaded', loadMetrics);
    </script>
</body>
</html>
"""

    def _generate_ci_integration(self) -> dict[str, Any]:
        """Generate CI integration configuration snippets.

        Returns:
            Dictionary with CI integration examples for various platforms.
        """
        ci_config = {
            "github_actions": {
                "coverage_check": {
                    "name": "Coverage Check",
                    "run": f"pytest --cov --cov-fail-under="
                    f"{self.config.coverage_threshold}",
                },
                "complexity_check": {
                    "name": "Complexity Check",
                    "run": f"radon cc -n {self.config.complexity_threshold} .",
                },
                "docs_check": {
                    "name": "Documentation Check",
                    "run": f"interrogate --fail-under="
                    f"{self.config.doc_coverage_threshold}",
                },
            },
        }

        if self.config.language == "python":
            ci_config["github_actions"]["mutation_check"] = {
                "name": "Mutation Testing",
                "run": f"mutmut run --paths-to-mutate=. && "
                f"mutmut results --score-threshold={self.config.mutation_threshold}",
                "notes": "Run periodically, not on every commit",
            }

        return ci_config

    def generate(self) -> dict[str, Any]:
        """Generate complete metrics tracking configuration.

        Returns:
            Dictionary containing all generated metrics artifacts:
            - metrics_config: Core metrics configuration
            - sonarqube_config: SonarQube properties (if enabled)
            - badges: GitHub badge markdown
            - dashboard_template: HTML dashboard (if enabled)
            - ci_config: CI integration snippets

        Raises:
            ValueError: If configuration is invalid.
        """
        logger.info(
            "Generating metrics configuration for %s (%s)",
            self.config.project_name,
            self.config.language,
        )

        result = MetricsGenerationResult(
            metrics_config=self._generate_metrics_config(),
            sonarqube_config=self._generate_sonarqube_config(),
            badges=self._generate_badges(),
            dashboard_template=self._generate_dashboard_template(),
            ci_config=self._generate_ci_integration(),
        )

        logger.info(
            "Generated metrics config with %d badges and %s dashboard",
            len(result.badges),
            "enabled" if result.dashboard_template else "disabled",
        )

        return {
            "metrics_config": result.metrics_config,
            "sonarqube_config": result.sonarqube_config,
            "badges": result.badges,
            "dashboard_template": result.dashboard_template,
            "ci_config": result.ci_config,
        }

    def write_metrics_config(self, output_dir: Path) -> Path:
        """Write metrics configuration to YAML file.

        Args:
            output_dir: Directory where config file will be written.

        Returns:
            Path to written metrics.yml file.

        Raises:
            ValueError: If output_dir is a dangerous system path.
            OSError: If file cannot be written.
        """
        # Security: Validate output directory
        self._validate_output_dir(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        config_path = output_dir / "metrics.yml"

        result = self.generate()
        config_path.write_text(yaml.dump(result["metrics_config"], sort_keys=False))

        logger.info("Wrote metrics config to %s", config_path)
        return config_path

    def write_sonarqube_config(self, output_dir: Path) -> Path | None:
        """Write SonarQube properties file.

        Args:
            output_dir: Directory where properties file will be written.

        Returns:
            Path to sonar-project.properties, or None if not enabled.

        Raises:
            ValueError: If output_dir is a dangerous system path.
            OSError: If file cannot be written.
        """
        if not self.config.enable_sonarqube:
            return None

        # Security: Validate output directory
        self._validate_output_dir(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        sonar_path = output_dir / "sonar-project.properties"

        result = self.generate()
        if result["sonarqube_config"]:
            sonar_path.write_text(result["sonarqube_config"])
            logger.info("Wrote SonarQube config to %s", sonar_path)
            return sonar_path

        return None

    def write_dashboard(self, output_dir: Path) -> Path | None:
        """Write dashboard HTML template.

        Args:
            output_dir: Directory where dashboard will be written.

        Returns:
            Path to dashboard.html, or None if not enabled.

        Raises:
            ValueError: If output_dir is a dangerous system path.
            OSError: If file cannot be written.
        """
        if not self.config.enable_dashboard:
            return None

        # Security: Validate output directory
        self._validate_output_dir(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        dashboard_path = output_dir / "dashboard.html"

        result = self.generate()
        if result["dashboard_template"]:
            dashboard_path.write_text(result["dashboard_template"])
            logger.info("Wrote dashboard template to %s", dashboard_path)
            return dashboard_path

        return None

    def write_badges(self, output_dir: Path) -> Path:
        """Write badges to markdown file.

        Args:
            output_dir: Directory where badges file will be written.

        Returns:
            Path to badges.md file.

        Raises:
            ValueError: If output_dir is a dangerous system path.
            OSError: If file cannot be written.
        """
        # Security: Validate output directory
        self._validate_output_dir(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        badges_path = output_dir / "badges.md"

        result = self.generate()
        badges_content = "# Quality Badges\n\n" + "\n".join(result["badges"])
        badges_path.write_text(badges_content)

        logger.info("Wrote %d badges to %s", len(result["badges"]), badges_path)
        return badges_path

    def write_all(self, output_dir: Path) -> dict[str, Path]:
        """Write all metrics artifacts to output directory.

        Args:
            output_dir: Root directory for all outputs.

        Returns:
            Dictionary mapping artifact names to their paths.

        Raises:
            OSError: If files cannot be written.
        """
        artifacts: dict[str, Path] = {}

        # Write metrics config
        artifacts["metrics"] = self.write_metrics_config(output_dir)

        # Write optional artifacts
        sonar_path = self.write_sonarqube_config(output_dir)
        if sonar_path:
            artifacts["sonarqube"] = sonar_path

        dashboard_path = self.write_dashboard(output_dir)
        if dashboard_path:
            artifacts["dashboard"] = dashboard_path

        if self.config.enable_badges:
            artifacts["badges"] = self.write_badges(output_dir)

        logger.info("Wrote %d metrics artifacts to %s", len(artifacts), output_dir)
        return artifacts
