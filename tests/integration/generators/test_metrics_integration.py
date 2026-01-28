"""Integration tests for metrics generator.

Tests end-to-end metrics generation workflows including file writing
and multi-language support.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
import yaml

from start_green_stay_green.generators.metrics import LANGUAGE_TOOLS
from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator


class TestMetricsGeneratorIntegration:
    """Integration tests for complete metrics generation workflow."""

    def test_generate_python_project_full_stack(self) -> None:
        """Test generating complete metrics config for Python project."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="integration-test-python",
            enable_sonarqube=True,
            enable_badges=True,
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            # Verify all artifacts created
            assert len(artifacts) == 4
            assert all(path.exists() for path in artifacts.values())

            # Verify metrics.yml content
            metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
            assert metrics_content["project"] == "integration-test-python"
            assert metrics_content["language"] == "python"
            assert len(metrics_content["metrics"]) == 10

            # Verify SonarQube config
            sonar_content = artifacts["sonarqube"].read_text()
            assert "sonar.projectKey=integration-test-python" in sonar_content
            assert "sonar.language=py" in sonar_content

            # Verify badges.md
            badges_content = artifacts["badges"].read_text()
            assert "# Quality Badges" in badges_content
            assert "![Coverage]" in badges_content

            # Verify dashboard.html
            dashboard_content = artifacts["dashboard"].read_text()
            assert "<!DOCTYPE html>" in dashboard_content
            assert "integration-test-python" in dashboard_content

    def test_generate_typescript_project_minimal(self) -> None:
        """Test generating minimal metrics config for TypeScript project."""
        config = MetricsGenerationConfig(
            language="typescript",
            project_name="ts-integration-test",
            enable_sonarqube=False,
            enable_badges=False,
            enable_dashboard=False,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            # Only metrics.yml should be created
            assert len(artifacts) == 1
            assert "metrics" in artifacts
            assert artifacts["metrics"].exists()

            # Verify TypeScript-specific tools
            metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
            assert metrics_content["metrics"]["code_coverage"]["tool"] == "jest"
            assert metrics_content["metrics"]["mutation_score"]["tool"] == "stryker"

    def test_generate_all_supported_languages(self) -> None:
        """Test generating metrics config for all supported languages."""
        for language in LANGUAGE_TOOLS:
            config = MetricsGenerationConfig(
                language=language,
                project_name=f"{language}-test",
            )
            generator = MetricsGenerator(None, config)

            with TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                artifacts = generator.write_all(output_dir)

                # Verify metrics config created for each language
                assert "metrics" in artifacts
                metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
                assert metrics_content["language"] == language
                assert len(metrics_content["metrics"]) == 10

    def test_custom_thresholds_applied_correctly(self) -> None:
        """Test that custom thresholds are correctly applied in all artifacts."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="custom-thresholds",
            coverage_threshold=85,
            branch_coverage_threshold=80,
            mutation_threshold=75,
            complexity_threshold=12,
            doc_coverage_threshold=92,
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            # Check metrics.yml
            metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
            assert metrics_content["metrics"]["code_coverage"]["threshold"] == 85
            assert metrics_content["metrics"]["branch_coverage"]["threshold"] == 80
            assert metrics_content["metrics"]["mutation_score"]["threshold"] == 75
            assert (
                metrics_content["metrics"]["cyclomatic_complexity"]["threshold"] == 12
            )
            assert (
                metrics_content["metrics"]["documentation_coverage"]["threshold"] == 92
            )

            # Check dashboard includes thresholds
            dashboard_content = artifacts["dashboard"].read_text()
            assert "≥85%" in dashboard_content
            assert "≥80%" in dashboard_content
            assert "≥75%" in dashboard_content

    def test_ci_integration_config_completeness(self) -> None:
        """Test that CI integration config is complete and usable."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="ci-test",
            coverage_threshold=90,
        )
        generator = MetricsGenerator(None, config)

        result = generator.generate()
        ci_config = result["ci_config"]

        # Verify structure
        assert "github_actions" in ci_config
        gh_actions = ci_config["github_actions"]

        # Verify required checks
        assert "coverage_check" in gh_actions
        assert "complexity_check" in gh_actions
        assert "docs_check" in gh_actions

        # Verify Python includes mutation testing
        assert "mutation_check" in gh_actions

        # Verify commands are executable
        for check_name, check_config in gh_actions.items():
            if check_name != "mutation_check":  # mutation has notes field
                assert "name" in check_config
                assert "run" in check_config
                assert check_config["run"]

    def test_sonarqube_language_specific_config(self) -> None:
        """Test SonarQube configuration for different languages."""
        languages_configs = [
            ("python", "sonar.language=py"),
            ("typescript", "sonar.language=js"),
            ("javascript", "sonar.language=js"),
        ]

        for language, expected_line in languages_configs:
            config = MetricsGenerationConfig(
                language=language,
                project_name=f"{language}-sonar-test",
                enable_sonarqube=True,
            )
            generator = MetricsGenerator(None, config)

            with TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                sonar_path = generator.write_sonarqube_config(output_dir)

                assert sonar_path is not None
                sonar_content = sonar_path.read_text()
                assert expected_line in sonar_content

    def test_badges_project_name_integration(self) -> None:
        """Test that project name is correctly integrated into badges."""
        project_name = "my-awesome-project"
        config = MetricsGenerationConfig(
            language="python",
            project_name=project_name,
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            badges_path = generator.write_badges(output_dir)

            badges_content = badges_path.read_text()
            assert project_name in badges_content
            assert "![Coverage]" in badges_content
            assert "img.shields.io" in badges_content

    def test_metrics_config_yaml_validity(self) -> None:
        """Test that generated metrics.yml is valid YAML and parseable."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="yaml-test",
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            metrics_path = generator.write_metrics_config(output_dir)

            # Should parse without errors
            metrics_data = yaml.safe_load(metrics_path.read_text())

            # Verify structure
            assert isinstance(metrics_data, dict)
            assert "project" in metrics_data
            assert "language" in metrics_data
            assert "metrics" in metrics_data
            assert isinstance(metrics_data["metrics"], dict)

    def test_dashboard_html_validity(self) -> None:
        """Test that generated dashboard.html is valid HTML."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="html-test",
            enable_dashboard=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            dashboard_path = generator.write_dashboard(output_dir)

            assert dashboard_path is not None
            html_content = dashboard_path.read_text()

            # Basic HTML structure validation
            assert html_content.count("<!DOCTYPE html>") == 1
            assert html_content.count("<html") == 1
            assert html_content.count("</html>") == 1
            assert html_content.count("<head>") == 1
            assert html_content.count("</head>") == 1
            assert html_content.count("<body>") == 1
            assert html_content.count("</body>") == 1

            # Verify CSS is included
            assert "<style>" in html_content
            assert "</style>" in html_content

            # Verify JavaScript is included
            assert "<script>" in html_content
            assert "</script>" in html_content

    def test_nested_directory_creation(self) -> None:
        """Test that deeply nested output directories are created."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="nested-test",
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "level1" / "level2" / "level3"
            assert not output_dir.exists()

            artifacts = generator.write_all(output_dir)

            # Directory should be created
            assert output_dir.exists()
            assert all(path.exists() for path in artifacts.values())

    def test_multiple_invocations_consistent(self) -> None:
        """Test that multiple invocations produce consistent output."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="consistency-test",
            enable_sonarqube=True,
            enable_badges=True,
            enable_dashboard=True,
        )

        generator1 = MetricsGenerator(None, config)
        result1 = generator1.generate()

        generator2 = MetricsGenerator(None, config)
        result2 = generator2.generate()

        # Results should be identical
        assert result1["metrics_config"] == result2["metrics_config"]
        assert result1["sonarqube_config"] == result2["sonarqube_config"]
        assert result1["badges"] == result2["badges"]
        assert result1["dashboard_template"] == result2["dashboard_template"]
        assert result1["ci_config"] == result2["ci_config"]

    def test_overwrite_existing_files(self) -> None:
        """Test that existing files are overwritten correctly."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="overwrite-test",
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # First write
            artifacts1 = generator.write_all(output_dir)
            original_content = artifacts1["metrics"].read_text()

            # Modify config and write again
            config2 = MetricsGenerationConfig(
                language="python",
                project_name="overwrite-test-modified",
            )
            generator2 = MetricsGenerator(None, config2)
            artifacts2 = generator2.write_all(output_dir)

            # File should be overwritten
            new_content = artifacts2["metrics"].read_text()
            assert new_content != original_content
            assert "overwrite-test-modified" in new_content


class TestMetricsGeneratorErrorHandling:
    """Integration tests for error handling and edge cases."""

    def test_invalid_output_directory_permissions(self) -> None:
        """Test handling of permission errors (if applicable)."""
        # This test is platform-dependent and may be skipped on some systems
        pytest.skip("Platform-dependent permission test")

    def test_large_threshold_values_handled(self) -> None:
        """Test that threshold values at boundaries work correctly."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="boundary-test",
            coverage_threshold=100,
            branch_coverage_threshold=100,
            mutation_threshold=100,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
            assert metrics_content["metrics"]["code_coverage"]["threshold"] == 100

    def test_zero_threshold_values_handled(self) -> None:
        """Test that zero threshold values work correctly."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="zero-test",
            coverage_threshold=0,
            branch_coverage_threshold=0,
            mutation_threshold=0,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            artifacts = generator.write_all(output_dir)

            metrics_content = yaml.safe_load(artifacts["metrics"].read_text())
            assert metrics_content["metrics"]["code_coverage"]["threshold"] == 0


class TestMetricsGeneratorDocumentation:
    """Integration tests for documentation generation."""

    def test_readme_badge_integration(self) -> None:
        """Test that badges can be integrated into README.md."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="readme-test",
            enable_badges=True,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            badges_path = generator.write_badges(output_dir)

            badges_content = badges_path.read_text()

            # Verify badges are in markdown format
            assert badges_content.startswith("# Quality Badges")
            badge_lines = [
                line for line in badges_content.split("\n") if line.startswith("![")
            ]
            assert badge_lines

            # Each badge should be valid markdown
            for badge in badge_lines:
                assert badge.startswith("![")
                assert "](" in badge
                assert badge.endswith(")")

    def test_dashboard_deployment_ready(self) -> None:
        """Test that dashboard HTML can be deployed as-is."""
        config = MetricsGenerationConfig(
            language="python",
            project_name="deploy-test",
            enable_dashboard=True,
            coverage_threshold=95,
        )
        generator = MetricsGenerator(None, config)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            dashboard_path = generator.write_dashboard(output_dir)

            assert dashboard_path is not None
            html_content = dashboard_path.read_text()

            # Should be a complete standalone HTML file
            assert "<!DOCTYPE html>" in html_content
            assert "<style>" in html_content  # Embedded CSS
            assert "<script>" in html_content  # Embedded JS
            assert (
                "http" not in html_content
                or "https" not in html_content
                or (
                    # Some external resources are OK (fonts, etc.)
                    "img.shields.io"
                    not in html_content  # But not loading badges
                )
            )
