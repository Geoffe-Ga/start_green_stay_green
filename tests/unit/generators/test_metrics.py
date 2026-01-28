"""Unit tests for metrics generator.

Tests MetricsGenerator class for quality metrics configuration generation
across multiple languages and configurations.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock

import pytest
import yaml

from start_green_stay_green.generators.metrics import LANGUAGE_TOOLS
from start_green_stay_green.generators.metrics import MetricConfig
from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator
from start_green_stay_green.generators.metrics import STANDARD_METRICS


class TestMetricConfig:
    """Test MetricConfig dataclass."""

    def test_metric_config_creation(self) -> None:
        """Test creating MetricConfig with all fields."""
        config = MetricConfig(
            name="Code Coverage",
            threshold="≥90%",
            tool="pytest-cov",
            enabled=True,
            badge_available=True,
            ci_enforced=True,
        )

        assert config.name == "Code Coverage"
        assert config.threshold == "≥90%"
        assert config.tool == "pytest-cov"
        assert config.enabled
        assert config.badge_available
        assert config.ci_enforced

    def test_metric_config_defaults(self) -> None:
        """Test MetricConfig default values."""
        config = MetricConfig(
            name="Test Metric",
            threshold="≥80%",
            tool="test-tool",
        )

        assert config.enabled
        assert config.badge_available
        assert config.ci_enforced

    def test_metric_config_immutable(self) -> None:
        """Test that MetricConfig is immutable (frozen)."""
        config = MetricConfig(
            name="Test",
            threshold="≥90%",
            tool="tool",
        )

        with pytest.raises(AttributeError):
            config.name = "Changed"  # type: ignore[misc]


class TestMetricsGenerationConfig:
    """Test MetricsGenerationConfig dataclass."""

    def test_config_creation_minimal(self) -> None:
        """Test creating config with minimal required fields."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test-project",
        )

        assert config.language == "python"
        assert config.project_name == "test-project"
        assert config.coverage_threshold == 90
        assert config.mutation_threshold == 80
        assert config.complexity_threshold == 10

    def test_config_creation_custom(self) -> None:
        """Test creating config with custom thresholds."""
        config = MetricsGenerationConfig(
            language="typescript",
            project_name="my-app",
            coverage_threshold=85,
            branch_coverage_threshold=80,
            mutation_threshold=75,
            complexity_threshold=15,
            enable_sonarqube=True,
            enable_badges=False,
            enable_dashboard=False,
        )

        assert config.coverage_threshold == 85
        assert config.branch_coverage_threshold == 80
        assert config.mutation_threshold == 75
        assert config.complexity_threshold == 15
        assert config.enable_sonarqube
        assert not config.enable_badges
        assert not config.enable_dashboard

    def test_config_all_defaults(self) -> None:
        """Test all default values are set correctly."""
        config = MetricsGenerationConfig(
            language="go",
            project_name="go-service",
        )

        assert config.coverage_threshold == 90
        assert config.branch_coverage_threshold == 85
        assert config.mutation_threshold == 80
        assert config.complexity_threshold == 10
        assert config.cognitive_complexity_threshold == 15
        assert config.maintainability_threshold == 20
        assert config.debt_ratio_threshold == 5
        assert config.doc_coverage_threshold == 95
        assert config.dependency_freshness_days == 30
        assert not config.enable_sonarqube
        assert config.enable_badges
        assert config.enable_dashboard


class TestStandardMetrics:
    """Test STANDARD_METRICS constant."""

    def test_has_all_ten_metrics(self) -> None:
        """Test that STANDARD_METRICS contains all 10 metrics."""
        expected_metrics = {
            "code_coverage",
            "branch_coverage",
            "mutation_score",
            "cyclomatic_complexity",
            "cognitive_complexity",
            "maintainability_index",
            "technical_debt_ratio",
            "documentation_coverage",
            "dependency_freshness",
            "security_vulnerabilities",
        }

        assert set(STANDARD_METRICS.keys()) == expected_metrics

    def test_metric_configs_valid(self) -> None:
        """Test that all metric configs are valid MetricConfig instances."""
        for metric_config in STANDARD_METRICS.values():
            assert isinstance(metric_config, MetricConfig)
            assert metric_config.name
            assert metric_config.threshold
            assert metric_config.tool

    def test_code_coverage_metric(self) -> None:
        """Test code coverage metric configuration."""
        metric = STANDARD_METRICS["code_coverage"]
        assert metric.name == "Code Coverage"
        assert metric.threshold == "≥90%"
        assert metric.badge_available
        assert metric.ci_enforced

    def test_mutation_score_metric(self) -> None:
        """Test mutation score metric (periodic, not continuous)."""
        metric = STANDARD_METRICS["mutation_score"]
        assert metric.name == "Mutation Score"
        assert metric.threshold == "≥80%"
        assert not metric.ci_enforced  # Periodic quality gate


class TestLanguageTools:
    """Test LANGUAGE_TOOLS constant."""

    def test_supports_required_languages(self) -> None:
        """Test that all required languages are supported."""
        required_languages = {"python", "typescript", "javascript", "go", "rust"}
        assert required_languages.issubset(set(LANGUAGE_TOOLS.keys()))

    def test_python_tools(self) -> None:
        """Test Python tool mappings."""
        tools = LANGUAGE_TOOLS["python"]
        assert tools["coverage"] == "pytest-cov"
        assert tools["mutation"] == "mutmut"
        assert tools["complexity"] == "radon"
        assert tools["documentation"] == "interrogate"
        assert tools["security"] == "safety"

    def test_typescript_tools(self) -> None:
        """Test TypeScript tool mappings."""
        tools = LANGUAGE_TOOLS["typescript"]
        assert tools["coverage"] == "jest"
        assert tools["mutation"] == "stryker"
        assert tools["complexity"] == "eslint"

    def test_all_languages_have_required_tools(self) -> None:
        """Test that all languages have required tool categories."""
        required_tools = {
            "coverage",
            "mutation",
            "complexity",
            "documentation",
            "security",
        }

        for language, tools in LANGUAGE_TOOLS.items():
            assert required_tools.issubset(
                set(tools.keys())
            ), f"{language} missing tools: {required_tools - set(tools.keys())}"


class TestMetricsGeneratorInit:
    """Test MetricsGenerator initialization."""

    def test_init_with_orchestrator(self) -> None:
        """Test initializing generator with orchestrator."""
        orchestrator = Mock()
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )

        generator = MetricsGenerator(orchestrator, config)

        assert generator.orchestrator is orchestrator
        assert generator.config is config

    def test_init_without_orchestrator(self) -> None:
        """Test initializing generator without orchestrator."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )

        generator = MetricsGenerator(None, config)

        assert generator.orchestrator is None
        assert generator.config is config

    def test_init_validates_empty_language(self) -> None:
        """Test that empty language raises ValueError."""
        config = MetricsGenerationConfig(
            language="",
            project_name="test",
        )

        with pytest.raises(ValueError, match="Language cannot be empty"):
            MetricsGenerator(None, config)

    def test_init_validates_empty_project_name(self) -> None:
        """Test that empty project name raises ValueError."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="",
        )

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            MetricsGenerator(None, config)

    def test_init_validates_unsupported_language(self) -> None:
        """Test that unsupported language raises ValueError."""
        config = MetricsGenerationConfig(
            language="cobol",
            project_name="legacy-app",
        )

        with pytest.raises(ValueError, match="Unsupported language: cobol"):
            MetricsGenerator(None, config)

    def test_init_validates_coverage_threshold_bounds(self) -> None:
        """Test that coverage threshold must be 0-100."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=101,
        )

        with pytest.raises(
            ValueError, match="Coverage threshold must be between 0 and 100"
        ):
            MetricsGenerator(None, config)

        config_negative = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=-1,
        )

        with pytest.raises(
            ValueError, match="Coverage threshold must be between 0 and 100"
        ):
            MetricsGenerator(None, config_negative)

    def test_init_validates_branch_coverage_threshold(self) -> None:
        """Test branch coverage threshold validation."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            branch_coverage_threshold=150,
        )

        with pytest.raises(
            ValueError,
            match="Branch coverage threshold must be between 0 and 100",
        ):
            MetricsGenerator(None, config)

    def test_init_validates_mutation_threshold(self) -> None:
        """Test mutation threshold validation."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            mutation_threshold=200,
        )

        with pytest.raises(
            ValueError, match="Mutation threshold must be between 0 and 100"
        ):
            MetricsGenerator(None, config)


class TestMetricsGeneratorToolSelection:
    """Test tool selection for different languages."""

    def test_get_python_tools(self) -> None:
        """Test getting tools for Python projects."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="py-app",
        )
        generator = MetricsGenerator(None, config)

        assert generator._get_tool_for_language("coverage") == "pytest-cov"
        assert generator._get_tool_for_language("mutation") == "mutmut"
        assert generator._get_tool_for_language("complexity") == "radon"
        assert generator._get_tool_for_language("security") == "safety"

    def test_get_typescript_tools(self) -> None:
        """Test getting tools for TypeScript projects."""
        config = MetricsGenerationConfig(
            language="typescript",
            project_name="ts-app",
        )
        generator = MetricsGenerator(None, config)

        assert generator._get_tool_for_language("coverage") == "jest"
        assert generator._get_tool_for_language("mutation") == "stryker"
        assert generator._get_tool_for_language("complexity") == "eslint"

    def test_get_go_tools(self) -> None:
        """Test getting tools for Go projects."""
        config = MetricsGenerationConfig(
            language="go",
            project_name="go-service",
        )
        generator = MetricsGenerator(None, config)

        assert generator._get_tool_for_language("coverage") == "go test -cover"
        assert generator._get_tool_for_language("mutation") == "go-mutesting"

    def test_get_unknown_tool_returns_unknown(self) -> None:
        """Test that unknown metric type returns 'unknown'."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        assert generator._get_tool_for_language("nonexistent") == "unknown"


class TestMetricsConfigGeneration:
    """Test metrics configuration generation."""

    def test_generate_metrics_config_structure(self) -> None:
        """Test that generated config has correct structure."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test-project",
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()

        assert "project" in metrics_config
        assert "language" in metrics_config
        assert "metrics" in metrics_config
        assert metrics_config["project"] == "test-project"
        assert metrics_config["language"] == "python"

    def test_generate_metrics_config_all_metrics(self) -> None:
        """Test that all 10 metrics are in generated config."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()
        metrics = metrics_config["metrics"]

        expected_metrics = {
            "code_coverage",
            "branch_coverage",
            "mutation_score",
            "cyclomatic_complexity",
            "cognitive_complexity",
            "maintainability_index",
            "technical_debt_ratio",
            "documentation_coverage",
            "dependency_freshness",
            "security_vulnerabilities",
        }

        assert set(metrics.keys()) == expected_metrics

    def test_generate_metrics_config_thresholds(self) -> None:
        """Test that custom thresholds are applied."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=85,
            branch_coverage_threshold=80,
            mutation_threshold=75,
            complexity_threshold=15,
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()
        metrics = metrics_config["metrics"]

        assert metrics["code_coverage"]["threshold"] == 85
        assert metrics["branch_coverage"]["threshold"] == 80
        assert metrics["mutation_score"]["threshold"] == 75
        assert metrics["cyclomatic_complexity"]["threshold"] == 15

    def test_generate_metrics_config_ci_enforcement(self) -> None:
        """Test CI enforcement flags are set correctly."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()
        metrics = metrics_config["metrics"]

        # Should be enforced in CI
        assert metrics["code_coverage"]["enforce_in_ci"]
        assert metrics["branch_coverage"]["enforce_in_ci"]
        assert metrics["cyclomatic_complexity"]["enforce_in_ci"]
        assert metrics["documentation_coverage"]["enforce_in_ci"]

        # Should NOT be enforced in CI (periodic only)
        assert not metrics["mutation_score"]["enforce_in_ci"]
        assert not metrics["cognitive_complexity"]["enforce_in_ci"]

    def test_generate_metrics_config_language_specific_tools(self) -> None:
        """Test that language-specific tools are selected."""
        config = MetricsGenerationConfig(
            language="typescript",
            project_name="ts-app",
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()
        metrics = metrics_config["metrics"]

        assert metrics["code_coverage"]["tool"] == "jest"
        assert metrics["mutation_score"]["tool"] == "stryker"


class TestSonarQubeGeneration:
    """Test SonarQube configuration generation."""

    def test_sonarqube_disabled_returns_none(self) -> None:
        """Test that SonarQube config is None when disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=False,
        )
        generator = MetricsGenerator(None, config)

        sonar_config = generator._generate_sonarqube_config()

        assert sonar_config is None

    def test_sonarqube_enabled_returns_config(self) -> None:
        """Test that SonarQube config is generated when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="my-project",
            enable_sonarqube=True,
        )
        generator = MetricsGenerator(None, config)

        sonar_config = generator._generate_sonarqube_config()

        assert sonar_config is not None
        assert "sonar.projectKey=my-project" in sonar_config
        assert "sonar.projectName=my-project" in sonar_config

    def test_sonarqube_includes_thresholds(self) -> None:
        """Test that SonarQube config includes all thresholds."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=True,
            coverage_threshold=85,
            complexity_threshold=12,
            cognitive_complexity_threshold=18,
            debt_ratio_threshold=3,
        )
        generator = MetricsGenerator(None, config)

        sonar_config = generator._generate_sonarqube_config()

        assert sonar_config is not None
        assert "sonar.coverage.threshold=85" in sonar_config
        assert "sonar.complexity.threshold=12" in sonar_config
        assert "sonar.cognitive.complexity.threshold=18" in sonar_config
        assert "sonar.debt.ratio.threshold=3" in sonar_config

    def test_sonarqube_python_specific_config(self) -> None:
        """Test Python-specific SonarQube configuration."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="py-app",
            enable_sonarqube=True,
        )
        generator = MetricsGenerator(None, config)

        sonar_config = generator._generate_sonarqube_config()

        assert sonar_config is not None
        assert "sonar.language=py" in sonar_config
        assert "sonar.python.coverage.reportPaths=coverage.xml" in sonar_config
        assert "sonar.python.version=3.11,3.12" in sonar_config

    def test_sonarqube_typescript_specific_config(self) -> None:
        """Test TypeScript-specific SonarQube configuration."""
        config = MetricsGenerationConfig(
            language="typescript",
            project_name="ts-app",
            enable_sonarqube=True,
        )
        generator = MetricsGenerator(None, config)

        sonar_config = generator._generate_sonarqube_config()

        assert sonar_config is not None
        assert "sonar.language=js" in sonar_config
        assert "sonar.javascript.lcov.reportPaths=coverage/lcov.info" in sonar_config


class TestBadgeGeneration:
    """Test GitHub badge generation."""

    def test_badges_disabled_returns_empty_list(self) -> None:
        """Test that badges are empty when disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_badges=False,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        assert not badges

    def test_badges_enabled_returns_list(self) -> None:
        """Test that badges are generated when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="my-project",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        assert badges
        assert all(badge.startswith("![") for badge in badges)

    def test_badges_include_coverage(self) -> None:
        """Test that coverage badge is included."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test-project",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        coverage_badges = [b for b in badges if "Coverage" in b]
        assert coverage_badges

    def test_badges_include_security(self) -> None:
        """Test that security badge is included."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        security_badges = [b for b in badges if "Security" in b or "security" in b]
        assert security_badges

    def test_badges_python_includes_docs(self) -> None:
        """Test that Python projects include docs badge."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="py-app",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        docs_badges = [b for b in badges if "Docs" in b or "docs" in b]
        assert docs_badges

    def test_badges_sonarqube_when_enabled(self) -> None:
        """Test that SonarQube badge is included when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_badges=True,
            enable_sonarqube=True,
        )
        generator = MetricsGenerator(None, config)

        badges = generator._generate_badges()

        sonar_badges = [b for b in badges if "SonarQube" in b or "sonarcloud" in b]
        assert sonar_badges


class TestDashboardGeneration:
    """Test dashboard HTML template generation."""

    def test_dashboard_disabled_returns_none(self) -> None:
        """Test that dashboard is None when disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=False,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is None

    def test_dashboard_enabled_returns_html(self) -> None:
        """Test that dashboard HTML is generated when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="my-project",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is not None
        assert "<!DOCTYPE html>" in dashboard
        assert "<html" in dashboard
        assert "</html>" in dashboard

    def test_dashboard_includes_project_name(self) -> None:
        """Test that dashboard includes project name."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="awesome-project",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is not None
        assert "awesome-project" in dashboard

    def test_dashboard_includes_thresholds(self) -> None:
        """Test that dashboard displays configured thresholds."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=True,
            coverage_threshold=85,
            branch_coverage_threshold=80,
            mutation_threshold=75,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is not None
        assert "≥85%" in dashboard  # coverage
        assert "≥80%" in dashboard  # branch coverage
        assert "≥75%" in dashboard  # mutation

    def test_dashboard_has_metric_cards(self) -> None:
        """Test that dashboard has metric card structure."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is not None
        assert "metric-card" in dashboard
        assert "metric-name" in dashboard
        assert "metric-value" in dashboard
        assert "metric-threshold" in dashboard

    def test_dashboard_includes_css_styling(self) -> None:
        """Test that dashboard includes CSS styling."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        dashboard = generator._generate_dashboard_template()

        assert dashboard is not None
        assert "<style>" in dashboard
        assert "</style>" in dashboard
        assert "grid" in dashboard  # CSS grid layout


class TestCIIntegration:
    """Test CI integration configuration generation."""

    def test_ci_config_includes_github_actions(self) -> None:
        """Test that CI config includes GitHub Actions."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        ci_config = generator._generate_ci_integration()

        assert "github_actions" in ci_config

    def test_ci_config_includes_coverage_check(self) -> None:
        """Test that CI config includes coverage check."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=85,
        )
        generator = MetricsGenerator(None, config)

        ci_config = generator._generate_ci_integration()

        coverage_check = ci_config["github_actions"]["coverage_check"]
        assert coverage_check["name"] == "Coverage Check"
        assert "85" in coverage_check["run"]

    def test_ci_config_includes_complexity_check(self) -> None:
        """Test that CI config includes complexity check."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            complexity_threshold=12,
        )
        generator = MetricsGenerator(None, config)

        ci_config = generator._generate_ci_integration()

        complexity_check = ci_config["github_actions"]["complexity_check"]
        assert "12" in complexity_check["run"]

    def test_ci_config_python_includes_mutation(self) -> None:
        """Test that Python CI config includes mutation testing."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="py-app",
        )
        generator = MetricsGenerator(None, config)

        ci_config = generator._generate_ci_integration()

        assert "mutation_check" in ci_config["github_actions"]
        mutation_check = ci_config["github_actions"]["mutation_check"]
        assert "mutmut" in mutation_check["run"]
        assert "periodic" in mutation_check["notes"].lower()


class TestGenerateMethod:
    """Test main generate() method."""

    def test_generate_returns_complete_result(self) -> None:
        """Test that generate() returns all expected artifacts."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()

        assert "metrics_config" in result
        assert "sonarqube_config" in result
        assert "badges" in result
        assert "dashboard_template" in result
        assert "ci_config" in result

    def test_generate_metrics_config_is_dict(self) -> None:
        """Test that metrics_config is a dictionary."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()

        assert isinstance(result["metrics_config"], dict)
        assert "project" in result["metrics_config"]
        assert "language" in result["metrics_config"]
        assert "metrics" in result["metrics_config"]

    def test_generate_with_all_features_enabled(self) -> None:
        """Test generate() with all features enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="full-featured",
            enable_sonarqube=True,
            enable_badges=True,
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()

        assert result["sonarqube_config"] is not None
        assert result["badges"]
        assert result["dashboard_template"] is not None
        assert result["ci_config"]

    def test_generate_with_features_disabled(self) -> None:
        """Test generate() with optional features disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="minimal",
            enable_sonarqube=False,
            enable_badges=False,
            enable_dashboard=False,
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()

        assert result["sonarqube_config"] is None
        assert result["badges"] == []
        assert result["dashboard_template"] is None
        assert result["metrics_config"] is not None  # Always present


class TestFileWriting:
    """Test file writing methods."""

    def test_write_metrics_config(self) -> None:
        """Test writing metrics config to YAML file."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_metrics_config(output_dir)

            assert result_path.exists()
            assert result_path.name == "metrics.yml"

            # Verify YAML is valid
            content = yaml.safe_load(result_path.read_text())
            assert content["project"] == "test"
            assert content["language"] == "python"

    def test_write_sonarqube_config_enabled(self) -> None:
        """Test writing SonarQube config when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_sonarqube_config(output_dir)

            assert result_path is not None
            assert result_path.exists()
            assert result_path.name == "sonar-project.properties"

            content = result_path.read_text()
            assert "sonar.projectKey=test" in content

    def test_write_sonarqube_config_disabled(self) -> None:
        """Test that SonarQube config is not written when disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=False,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_sonarqube_config(output_dir)

            assert result_path is None

    def test_write_dashboard_enabled(self) -> None:
        """Test writing dashboard when enabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_dashboard(output_dir)

            assert result_path is not None
            assert result_path.exists()
            assert result_path.name == "dashboard.html"

            content = result_path.read_text()
            assert "<!DOCTYPE html>" in content

    def test_write_dashboard_disabled(self) -> None:
        """Test that dashboard is not written when disabled."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_dashboard=False,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_dashboard(output_dir)

            assert result_path is None

    def test_write_badges(self) -> None:
        """Test writing badges to markdown file."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result_path = generator.write_badges(output_dir)

            assert result_path.exists()
            assert result_path.name == "badges.md"

            content = result_path.read_text()
            assert "# Quality Badges" in content
            assert "![" in content  # Badge markdown syntax

    def test_write_all(self) -> None:
        """Test writing all artifacts at once."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=True,
            enable_badges=True,
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            # Check all expected artifacts
            assert "metrics" in artifacts
            assert "sonarqube" in artifacts
            assert "badges" in artifacts
            assert "dashboard" in artifacts

            # Verify files exist
            assert artifacts["metrics"].exists()
            assert artifacts["sonarqube"].exists()
            assert artifacts["badges"].exists()
            assert artifacts["dashboard"].exists()

    def test_write_all_minimal(self) -> None:
        """Test write_all with minimal configuration."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="minimal",
            enable_sonarqube=False,
            enable_badges=False,
            enable_dashboard=False,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            # Only metrics config should be present
            assert "metrics" in artifacts
            assert "sonarqube" not in artifacts
            assert "badges" not in artifacts
            assert "dashboard" not in artifacts

            assert artifacts["metrics"].exists()

    def test_write_creates_output_directory(self) -> None:
        """Test that write methods create output directory if missing."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "path"
            assert not output_dir.exists()

            result_path = generator.write_metrics_config(output_dir)

            assert output_dir.exists()
            assert result_path.exists()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_thresholds(self) -> None:
        """Test that zero thresholds are valid."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=0,
            branch_coverage_threshold=0,
            mutation_threshold=0,
        )

        generator = MetricsGenerator(None, config)
        metrics_config = generator._generate_metrics_config()

        assert metrics_config["metrics"]["code_coverage"]["threshold"] == 0
        assert metrics_config["metrics"]["branch_coverage"]["threshold"] == 0

    def test_hundred_percent_thresholds(self) -> None:
        """Test that 100% thresholds are valid."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="perfect",
            coverage_threshold=100,
            branch_coverage_threshold=100,
            mutation_threshold=100,
        )

        generator = MetricsGenerator(None, config)
        metrics_config = generator._generate_metrics_config()

        assert metrics_config["metrics"]["code_coverage"]["threshold"] == 100

    def test_special_characters_in_project_name(self) -> None:
        """Test project names with special characters."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="my-cool_project.v2",
        )

        generator = MetricsGenerator(None, config)
        result = generator.generate()

        assert result["metrics_config"]["project"] == "my-cool_project.v2"

    def test_all_languages_generate_valid_config(self) -> None:
        """Test that all supported languages generate valid configs."""
        for language in LANGUAGE_TOOLS:
            config = MetricsGenerationConfig(
                language=language,
                project_name="test",
            )

            generator = MetricsGenerator(None, config)
            result = generator.generate()

            assert result["metrics_config"]["language"] == language
            assert len(result["metrics_config"]["metrics"]) == 10


class TestMutationKillers:
    """Dedicated tests to kill mutation testing survivors.

    These tests ensure exact value assertions and comprehensive boundary testing.
    """

    def test_exact_validation_error_messages(self) -> None:
        """Test exact error messages for validation failures."""
        # Empty language
        config = MetricsGenerationConfig(language="", project_name="test")
        with pytest.raises(ValueError, match="Language cannot be empty"):
            MetricsGenerator(None, config)

        # Empty project name
        config2 = MetricsGenerationConfig(language="python", project_name="")
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            MetricsGenerator(None, config2)

        # Unsupported language
        config3 = MetricsGenerationConfig(language="fortran", project_name="test")
        with pytest.raises(ValueError, match="Unsupported language: fortran"):
            MetricsGenerator(None, config3)

    def test_threshold_boundary_values(self) -> None:
        """Test exact boundary values for thresholds."""
        # Valid boundaries: 0 and 100
        config_min = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=0,
            branch_coverage_threshold=0,
            mutation_threshold=0,
        )
        generator_min = MetricsGenerator(None, config_min)
        assert generator_min.config.coverage_threshold == 0

        config_max = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=100,
            branch_coverage_threshold=100,
            mutation_threshold=100,
        )
        generator_max = MetricsGenerator(None, config_max)
        assert generator_max.config.coverage_threshold == 100

        # Test invalid threshold of negative one
        config_neg = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=-1,
        )
        with pytest.raises(
            ValueError, match="Coverage threshold must be between 0 and 100"
        ):
            MetricsGenerator(None, config_neg)

        # Test invalid threshold of one hundred and one
        config_over = MetricsGenerationConfig(
            language="python",
            project_name="test",
            coverage_threshold=101,
        )
        with pytest.raises(
            ValueError, match="Coverage threshold must be between 0 and 100"
        ):
            MetricsGenerator(None, config_over)

    def test_get_tool_exact_return_values(self) -> None:
        """Test exact return values from _get_tool_for_language."""
        config = MetricsGenerationConfig(language="python", project_name="test")
        generator = MetricsGenerator(None, config)

        # Exact tool names
        assert generator._get_tool_for_language("coverage") == "pytest-cov"
        assert generator._get_tool_for_language("mutation") == "mutmut"
        assert generator._get_tool_for_language("complexity") == "radon"
        assert generator._get_tool_for_language("documentation") == "interrogate"
        assert generator._get_tool_for_language("security") == "safety"
        assert generator._get_tool_for_language("dependency_check") == "pip-audit"

        # Unknown returns exactly "unknown"
        assert generator._get_tool_for_language("nonexistent") == "unknown"
        assert generator._get_tool_for_language("") == "unknown"

    def test_boolean_flags_exact_values(self) -> None:
        """Test boolean flags have exact True/False values."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=True,
            enable_badges=False,
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        metrics_config = generator._generate_metrics_config()

        # Test exact boolean values
        assert metrics_config["metrics"]["code_coverage"]["enforce_in_ci"]
        assert not metrics_config["metrics"]["mutation_score"]["enforce_in_ci"]
        assert metrics_config["metrics"]["cognitive_complexity"]["enabled"]
        assert metrics_config["metrics"]["maintainability_index"]["enabled"]

    def test_none_vs_empty_string_vs_false(self) -> None:
        """Test distinction between None, empty string, and False."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="test",
            enable_sonarqube=False,
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()

        # SonarQube disabled should be None (not empty string or False)
        assert result["sonarqube_config"] is None
        assert result["sonarqube_config"] != ""
        assert result["sonarqube_config"] is not False

        # Badges should be list (not None)
        assert result["badges"] is not None
        assert isinstance(result["badges"], list)
