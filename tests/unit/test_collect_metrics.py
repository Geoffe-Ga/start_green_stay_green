"""Tests for scripts/collect_metrics.py - metrics collection logic."""

from __future__ import annotations

import json
from pathlib import Path

# Import the module we're testing
import sys
from tempfile import TemporaryDirectory

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from collect_metrics import MetricsCollector


class TestMetricsCollector:
    """Tests for MetricsCollector class."""

    def test_init(self) -> None:
        """Test MetricsCollector initialization."""
        thresholds = {"coverage": 90, "complexity": 10}
        collector = MetricsCollector("test-project", thresholds)

        assert collector.project_name == "test-project"
        assert collector.thresholds == thresholds
        assert collector.metrics == {}

    def test_collect_coverage_success(self) -> None:
        """Test successful coverage collection."""
        with TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / "coverage.json"
            cov_file.write_text(
                json.dumps(
                    {
                        "totals": {
                            "percent_covered": 92.5,
                            "num_branches": 100,
                            "covered_branches": 88,
                        }
                    }
                )
            )

            collector = MetricsCollector(
                "test", {"coverage": 90, "branch_coverage": 85}
            )
            collector.collect_coverage(cov_file)

            assert collector.metrics["coverage"] == 92.5
            assert collector.metrics["coverage_status"] == "pass"
            assert collector.metrics["branch_coverage"] == 88.0
            assert collector.metrics["branch_coverage_status"] == "pass"

    def test_collect_coverage_below_threshold(self) -> None:
        """Test coverage below threshold."""
        with TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / "coverage.json"
            cov_file.write_text(
                json.dumps(
                    {
                        "totals": {
                            "percent_covered": 85.0,
                            "num_branches": 0,
                            "covered_branches": 0,
                        }
                    }
                )
            )

            collector = MetricsCollector("test", {"coverage": 90})
            collector.collect_coverage(cov_file)

            assert collector.metrics["coverage"] == 85.0
            assert collector.metrics["coverage_status"] == "fail"

    def test_collect_coverage_file_not_found(self) -> None:
        """Test coverage collection with missing file."""
        collector = MetricsCollector("test", {"coverage": 90})

        with pytest.raises(FileNotFoundError, match="Coverage file not found"):
            collector.collect_coverage(Path("/nonexistent/coverage.json"))

    def test_collect_coverage_invalid_json(self) -> None:
        """Test coverage collection with invalid JSON."""
        with TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / "coverage.json"
            cov_file.write_text("not valid json")

            collector = MetricsCollector("test", {"coverage": 90})

            with pytest.raises(json.JSONDecodeError):
                collector.collect_coverage(cov_file)

    def test_collect_coverage_missing_keys(self) -> None:
        """Test coverage collection with missing required keys."""
        with TemporaryDirectory() as tmpdir:
            cov_file = Path(tmpdir) / "coverage.json"
            cov_file.write_text(json.dumps({"invalid": "structure"}))

            collector = MetricsCollector("test", {"coverage": 90})

            with pytest.raises(KeyError):
                collector.collect_coverage(cov_file)

    def test_collect_complexity_success(self) -> None:
        """Test successful complexity collection."""
        with TemporaryDirectory() as tmpdir:
            comp_file = Path(tmpdir) / "complexity.txt"
            comp_file.write_text(
                "Some output\nAverage complexity: A (4.5)\nMore output"
            )

            collector = MetricsCollector("test", {"complexity": 10})
            collector.collect_complexity(comp_file)

            assert collector.metrics["complexity_avg"] == 4.5
            assert collector.metrics["complexity_status"] == "pass"

    def test_collect_complexity_above_threshold(self) -> None:
        """Test complexity above threshold."""
        with TemporaryDirectory() as tmpdir:
            comp_file = Path(tmpdir) / "complexity.txt"
            comp_file.write_text("Average complexity: C (12.3)")

            collector = MetricsCollector("test", {"complexity": 10})
            collector.collect_complexity(comp_file)

            assert collector.metrics["complexity_avg"] == 12.3
            assert collector.metrics["complexity_status"] == "fail"

    def test_collect_complexity_file_not_found(self) -> None:
        """Test complexity collection with missing file."""
        collector = MetricsCollector("test", {"complexity": 10})

        with pytest.raises(FileNotFoundError, match="Complexity file not found"):
            collector.collect_complexity(Path("/nonexistent/complexity.txt"))

    def test_collect_complexity_pattern_not_found(self) -> None:
        """Test complexity collection with invalid pattern."""
        with TemporaryDirectory() as tmpdir:
            comp_file = Path(tmpdir) / "complexity.txt"
            comp_file.write_text("No complexity data here")

            collector = MetricsCollector("test", {"complexity": 10})

            with pytest.raises(ValueError, match="Could not find complexity pattern"):
                collector.collect_complexity(comp_file)

    def test_collect_docs_coverage_success(self) -> None:
        """Test successful docs coverage collection."""
        with TemporaryDirectory() as tmpdir:
            docs_file = Path(tmpdir) / "docs.txt"
            docs_file.write_text("Some output\nRESULT: 96.5%\nMore output")

            collector = MetricsCollector("test", {"docs_coverage": 95})
            collector.collect_docs_coverage(docs_file)

            assert collector.metrics["docs_coverage"] == 96.5
            assert collector.metrics["docs_status"] == "pass"

    def test_collect_docs_coverage_below_threshold(self) -> None:
        """Test docs coverage below threshold."""
        with TemporaryDirectory() as tmpdir:
            docs_file = Path(tmpdir) / "docs.txt"
            docs_file.write_text("RESULT: 92.0%")

            collector = MetricsCollector("test", {"docs_coverage": 95})
            collector.collect_docs_coverage(docs_file)

            assert collector.metrics["docs_coverage"] == 92.0
            assert collector.metrics["docs_status"] == "fail"

    def test_collect_docs_coverage_file_not_found(self) -> None:
        """Test docs coverage collection with missing file."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with pytest.raises(FileNotFoundError, match="Docs file not found"):
            collector.collect_docs_coverage(Path("/nonexistent/docs.txt"))

    def test_collect_docs_coverage_pattern_not_found(self) -> None:
        """Test docs coverage collection with invalid pattern."""
        with TemporaryDirectory() as tmpdir:
            docs_file = Path(tmpdir) / "docs.txt"
            docs_file.write_text("No docs coverage data here")

            collector = MetricsCollector("test", {"docs_coverage": 95})

            with pytest.raises(
                ValueError, match="Could not find docs coverage pattern"
            ):
                collector.collect_docs_coverage(docs_file)

    def test_collect_security_success_no_issues(self) -> None:
        """Test successful security collection with no issues."""
        with TemporaryDirectory() as tmpdir:
            sec_file = Path(tmpdir) / "security.json"
            sec_file.write_text(json.dumps({"results": []}))

            collector = MetricsCollector("test", {"security_issues": 0})
            collector.collect_security(sec_file)

            assert collector.metrics["security_issues"] == 0
            assert collector.metrics["security_status"] == "pass"

    def test_collect_security_with_issues(self) -> None:
        """Test security collection with issues found."""
        with TemporaryDirectory() as tmpdir:
            sec_file = Path(tmpdir) / "security.json"
            sec_file.write_text(
                json.dumps(
                    {
                        "results": [
                            {"issue": "SQL injection"},
                            {"issue": "XSS vulnerability"},
                        ]
                    }
                )
            )

            collector = MetricsCollector("test", {"security_issues": 0})
            collector.collect_security(sec_file)

            assert collector.metrics["security_issues"] == 2
            assert collector.metrics["security_status"] == "fail"

    def test_collect_security_file_not_found(self) -> None:
        """Test security collection with missing file."""
        collector = MetricsCollector("test", {"security_issues": 0})

        with pytest.raises(FileNotFoundError, match="Security file not found"):
            collector.collect_security(Path("/nonexistent/security.json"))

    def test_collect_security_invalid_json(self) -> None:
        """Test security collection with invalid JSON."""
        with TemporaryDirectory() as tmpdir:
            sec_file = Path(tmpdir) / "security.json"
            sec_file.write_text("not valid json")

            collector = MetricsCollector("test", {"security_issues": 0})

            with pytest.raises(json.JSONDecodeError):
                collector.collect_security(sec_file)

    def test_add_mutation_score_passing(self) -> None:
        """Test adding passing mutation score."""
        collector = MetricsCollector("test", {"mutation_score": 80})
        collector.add_mutation_score(85.0)

        assert collector.metrics["mutation_score"] == 85.0
        assert collector.metrics["mutation_status"] == "pass"

    def test_add_mutation_score_failing(self) -> None:
        """Test adding failing mutation score."""
        collector = MetricsCollector("test", {"mutation_score": 80})
        collector.add_mutation_score(75.0)

        assert collector.metrics["mutation_score"] == 75.0
        assert collector.metrics["mutation_status"] == "fail"

    def test_generate_json_success(self) -> None:
        """Test JSON generation."""
        with TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "metrics.json"

            thresholds = {
                "coverage": 90,
                "branch_coverage": 85,
                "mutation_score": 80,
                "complexity": 10,
                "docs_coverage": 95,
                "security_issues": 0,
            }
            collector = MetricsCollector("test-project", thresholds)
            collector.metrics = {
                "coverage": 92.5,
                "coverage_status": "pass",
                "security_issues": 0,
                "security_status": "pass",
            }

            collector.generate_json(output_file)

            assert output_file.exists()
            data = json.loads(output_file.read_text())

            assert data["project"] == "test-project"
            assert data["thresholds"] == thresholds
            assert data["metrics"]["coverage"] == 92.5
            assert data["metrics"]["coverage_status"] == "pass"
            assert "timestamp" in data

    def test_generate_json_creates_parent_dirs(self) -> None:
        """Test JSON generation creates parent directories."""
        with TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "level1" / "level2" / "metrics.json"

            collector = MetricsCollector("test", {})
            collector.generate_json(output_file)

            assert output_file.exists()
            assert output_file.parent.exists()

    def test_generate_json_with_null_metrics(self) -> None:
        """Test JSON generation handles null metric values (Issue #153)."""
        with TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "metrics.json"

            thresholds = {
                "coverage": 90,
                "complexity": 10,
                "docs_coverage": 95,
            }
            collector = MetricsCollector("test-project", thresholds)
            # Simulate what happens when parsing fails
            collector.metrics = {
                "coverage": 92.5,
                "coverage_status": "pass",
                "complexity_avg": None,  # Failed to parse
                "complexity_status": "unknown",
                "docs_coverage": None,  # Failed to parse
                "docs_status": "unknown",
            }

            collector.generate_json(output_file)

            assert output_file.exists()
            data = json.loads(output_file.read_text())

            # Verify null values are preserved in JSON
            assert data["metrics"]["complexity_avg"] is None
            assert data["metrics"]["docs_coverage"] is None
            # Dashboard should handle these nulls gracefully


class TestMetricsCollectorIntegration:
    """Integration tests for complete metrics collection workflow."""

    def test_full_workflow_all_passing(self) -> None:
        """Test complete workflow with all metrics passing."""
        with TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # Create mock report files
            (tmpdir / "coverage.json").write_text(
                json.dumps(
                    {
                        "totals": {
                            "percent_covered": 92.5,
                            "num_branches": 100,
                            "covered_branches": 90,
                        }
                    }
                )
            )
            (tmpdir / "complexity.txt").write_text("Average complexity: A (4.5)")
            (tmpdir / "docs.txt").write_text("RESULT: 96.5%")
            (tmpdir / "security.json").write_text(json.dumps({"results": []}))

            # Collect all metrics
            thresholds = {
                "coverage": 90,
                "branch_coverage": 85,
                "mutation_score": 80,
                "complexity": 10,
                "docs_coverage": 95,
                "security_issues": 0,
            }
            collector = MetricsCollector("test-project", thresholds)

            collector.collect_coverage(tmpdir / "coverage.json")
            collector.collect_complexity(tmpdir / "complexity.txt")
            collector.collect_docs_coverage(tmpdir / "docs.txt")
            collector.collect_security(tmpdir / "security.json")
            collector.add_mutation_score(85.0)

            # Generate output
            output_file = tmpdir / "metrics.json"
            collector.generate_json(output_file)

            # Verify output
            data = json.loads(output_file.read_text())
            assert data["metrics"]["coverage"] == 92.5
            assert data["metrics"]["coverage_status"] == "pass"
            assert data["metrics"]["branch_coverage"] == 90.0
            assert data["metrics"]["branch_coverage_status"] == "pass"
            assert data["metrics"]["complexity_avg"] == 4.5
            assert data["metrics"]["complexity_status"] == "pass"
            assert data["metrics"]["docs_coverage"] == 96.5
            assert data["metrics"]["docs_status"] == "pass"
            assert data["metrics"]["security_issues"] == 0
            assert data["metrics"]["security_status"] == "pass"
            assert data["metrics"]["mutation_score"] == 85.0
            assert data["metrics"]["mutation_status"] == "pass"

    def test_partial_metrics_collection(self) -> None:
        """Test workflow when some report files are missing."""
        with TemporaryDirectory() as tmpdir_str:
            tmpdir = Path(tmpdir_str)

            # Only create coverage file
            (tmpdir / "coverage.json").write_text(
                json.dumps({"totals": {"percent_covered": 92.5, "num_branches": 0}})
            )

            collector = MetricsCollector("test", {"coverage": 90})

            # Should not raise - only collect available metrics
            collector.collect_coverage(tmpdir / "coverage.json")

            # Other collections should raise
            with pytest.raises(FileNotFoundError):
                collector.collect_complexity(tmpdir / "complexity.txt")

            assert "coverage" in collector.metrics
            assert "complexity_avg" not in collector.metrics
