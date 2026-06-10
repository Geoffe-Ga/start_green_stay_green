"""Tests for scripts/collect_metrics.py - metrics collection logic."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

# Import the module we're testing
import sys
from tempfile import TemporaryDirectory
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
import collect_metrics
from collect_metrics import MetricsCollector
from collect_metrics import main as collect_main

from start_green_stay_green.generators.metrics import ci_status
from start_green_stay_green.generators.metrics import count_ci_jobs
from start_green_stay_green.generators.metrics import count_precommit_hooks
from start_green_stay_green.generators.metrics import precommit_status


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


class TestMutationFromCache:
    """Tests for collect_mutation_from_cache method."""

    def _create_cache(self, cache_path: Path, mutants: list[tuple[str, int]]) -> None:
        """Create a mock .mutmut-cache SQLite database.

        Args:
            cache_path: Path to create the database at
            mutants: List of (status, count) tuples
        """
        conn = sqlite3.connect(str(cache_path))
        try:
            conn.execute("CREATE TABLE Mutant (id INTEGER PRIMARY KEY, status TEXT)")
            mutant_id = 1
            for status, count in mutants:
                for _ in range(count):
                    conn.execute(
                        "INSERT INTO Mutant (id, status) VALUES (?, ?)",
                        (mutant_id, status),
                    )
                    mutant_id += 1
            conn.commit()
        finally:
            conn.close()

    def test_no_cache_returns_null(self) -> None:
        """Test that missing cache file returns null values."""
        collector = MetricsCollector("test", {"mutation_score": 80})
        collector.collect_mutation_from_cache(Path("/nonexistent/.mutmut-cache"))

        assert collector.metrics["mutation_score"] is None
        assert collector.metrics["mutation_status"] == "unknown"

    def test_valid_cache_returns_score(self) -> None:
        """Test that valid cache returns computed mutation score."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / ".mutmut-cache"
            self._create_cache(
                cache_path,
                [("ok_killed", 8), ("bad_survived", 2)],
            )

            collector = MetricsCollector("test", {"mutation_score": 80})
            collector.collect_mutation_from_cache(cache_path)

            assert collector.metrics["mutation_score"] == 80.0
            assert collector.metrics["mutation_status"] == "pass"

    def test_valid_cache_failing_score(self) -> None:
        """Test that cache with low kill rate returns failing status."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / ".mutmut-cache"
            self._create_cache(
                cache_path,
                [("ok_killed", 5), ("bad_survived", 5)],
            )

            collector = MetricsCollector("test", {"mutation_score": 80})
            collector.collect_mutation_from_cache(cache_path)

            assert collector.metrics["mutation_score"] == 50.0
            assert collector.metrics["mutation_status"] == "fail"

    def test_empty_cache_returns_null(self) -> None:
        """Test that cache with no mutants returns null."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / ".mutmut-cache"
            self._create_cache(cache_path, [])

            collector = MetricsCollector("test", {"mutation_score": 80})
            collector.collect_mutation_from_cache(cache_path)

            assert collector.metrics["mutation_score"] is None
            assert collector.metrics["mutation_status"] == "unknown"

    def test_corrupt_cache_returns_unknown(self) -> None:
        """Test that corrupt cache file returns unknown status."""
        with TemporaryDirectory() as tmpdir:
            cache_path = Path(tmpdir) / ".mutmut-cache"
            cache_path.write_text("not a sqlite database")

            collector = MetricsCollector("test", {"mutation_score": 80})
            collector.collect_mutation_from_cache(cache_path)

            assert collector.metrics["mutation_score"] is None
            assert collector.metrics["mutation_status"] == "unknown"


class TestCollectFromScript:
    """Tests for collect_from_script method."""

    def test_valid_json_parsing(self) -> None:
        """Test parsing valid JSON from script stdout."""
        collector = MetricsCollector("test", {})
        expected = {"violations": 0, "status": "pass"}

        with TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "lint.sh"
            script.write_text("#!/bin/bash\n")
            script.chmod(0o755)

            with patch("collect_metrics.subprocess.run") as mock_run:
                mock_run.return_value.stdout = json.dumps(expected)
                mock_run.return_value.returncode = 0

                result = collector.collect_from_script("lint.sh", Path(tmpdir))

        assert result == expected

    def test_invalid_json_returns_none(self) -> None:
        """Test that invalid JSON output returns None."""
        collector = MetricsCollector("test", {})

        with TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "lint.sh"
            script.write_text("#!/bin/bash\n")
            script.chmod(0o755)

            with patch("collect_metrics.subprocess.run") as mock_run:
                mock_run.return_value.stdout = "not json"
                mock_run.return_value.returncode = 0

                result = collector.collect_from_script("lint.sh", Path(tmpdir))

        assert result is None

    def test_missing_script_returns_none(self) -> None:
        """Test that missing script file returns None."""
        collector = MetricsCollector("test", {})

        result = collector.collect_from_script("nonexistent.sh", Path("/nonexistent"))

        assert result is None

    def test_timeout_returns_none(self) -> None:
        """Test that script timeout returns None."""
        collector = MetricsCollector("test", {})

        with TemporaryDirectory() as tmpdir:
            script = Path(tmpdir) / "slow.sh"
            script.write_text("#!/bin/bash\nsleep 999")
            script.chmod(0o755)

            with patch("collect_metrics.subprocess.run") as mock_run:
                mock_run.side_effect = __import__("subprocess").TimeoutExpired(
                    "slow.sh", 300
                )

                result = collector.collect_from_script("slow.sh", Path(tmpdir))

        assert result is None


class TestNewMetricMethods:
    """Tests for new metric collection methods (lint, typecheck, test, complexity)."""

    def test_collect_lint_metrics_success(self) -> None:
        """Test successful lint metrics collection."""
        collector = MetricsCollector("test", {"lint_violations": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"violations": 3, "status": "fail"},
        ):
            collector.collect_lint_metrics(Path("/scripts"))

        assert collector.metrics["lint_violations"] == 3
        assert collector.metrics["lint_status"] == "fail"

    def test_collect_lint_metrics_script_failure(self) -> None:
        """Test lint metrics when script fails."""
        collector = MetricsCollector("test", {"lint_violations": 0})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_lint_metrics(Path("/scripts"))

        assert collector.metrics["lint_violations"] is None
        assert collector.metrics["lint_status"] == "unknown"

    def test_collect_typecheck_metrics_success(self) -> None:
        """Test successful typecheck metrics collection."""
        collector = MetricsCollector("test", {"type_errors": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"errors": 0, "status": "pass"},
        ):
            collector.collect_typecheck_metrics(Path("/scripts"))

        assert collector.metrics["type_errors"] == 0
        assert collector.metrics["typecheck_status"] == "pass"

    def test_collect_typecheck_metrics_with_errors(self) -> None:
        """Test typecheck metrics with errors."""
        collector = MetricsCollector("test", {"type_errors": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"errors": 5, "status": "fail"},
        ):
            collector.collect_typecheck_metrics(Path("/scripts"))

        assert collector.metrics["type_errors"] == 5
        assert collector.metrics["typecheck_status"] == "fail"

    def test_collect_test_metrics_success(self) -> None:
        """Test successful test metrics collection."""
        collector = MetricsCollector("test", {"tests_total": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={
                "tests_total": 150,
                "tests_passed": 148,
                "tests_failed": 0,
                "tests_skipped": 2,
                "duration_seconds": 12.5,
            },
        ):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_total"] == 150
        assert collector.metrics["tests_passed"] == 148
        assert collector.metrics["tests_failed"] == 0
        assert collector.metrics["tests_skipped"] == 2
        assert collector.metrics["tests_status"] == "pass"

    def test_collect_test_metrics_with_failures(self) -> None:
        """Test test metrics with failures."""
        collector = MetricsCollector("test", {"tests_total": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={
                "tests_total": 100,
                "tests_passed": 95,
                "tests_failed": 3,
                "tests_skipped": 2,
                "duration_seconds": 10.0,
            },
        ):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_failed"] == 3
        assert collector.metrics["tests_status"] == "fail"

    def test_collect_test_metrics_script_failure(self) -> None:
        """Test test metrics when script fails."""
        collector = MetricsCollector("test", {"tests_total": 0})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_total"] is None
        assert collector.metrics["tests_status"] == "unknown"

    def test_collect_complexity_from_script_success(self) -> None:
        """Test successful complexity collection from script."""
        collector = MetricsCollector("test", {"complexity": 10, "maintainability": 20})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"cyclomatic_avg": 3.5, "maintainability_avg": 85.2},
        ):
            collector.collect_complexity_from_script(Path("/scripts"))

        assert collector.metrics["complexity_avg"] == 3.5
        assert collector.metrics["complexity_status"] == "pass"
        assert collector.metrics["maintainability_avg"] == 85.2
        assert collector.metrics["maintainability_status"] == "pass"

    def test_collect_complexity_from_script_failing(self) -> None:
        """Test complexity from script with high complexity."""
        collector = MetricsCollector("test", {"complexity": 10, "maintainability": 20})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"cyclomatic_avg": 15.0, "maintainability_avg": 10.0},
        ):
            collector.collect_complexity_from_script(Path("/scripts"))

        assert collector.metrics["complexity_avg"] == 15.0
        assert collector.metrics["complexity_status"] == "fail"
        assert collector.metrics["maintainability_avg"] == 10.0
        assert collector.metrics["maintainability_status"] == "fail"

    def test_collect_complexity_from_script_null_values(self) -> None:
        """Test complexity from script with null values."""
        collector = MetricsCollector("test", {"complexity": 10, "maintainability": 20})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"cyclomatic_avg": None, "maintainability_avg": None},
        ):
            collector.collect_complexity_from_script(Path("/scripts"))

        assert collector.metrics["complexity_avg"] is None
        assert collector.metrics["complexity_status"] == "unknown"
        assert collector.metrics["maintainability_avg"] is None
        assert collector.metrics["maintainability_status"] == "unknown"

    def test_collect_complexity_from_script_failure(self) -> None:
        """Test complexity from script when script fails entirely."""
        collector = MetricsCollector("test", {"complexity": 10, "maintainability": 20})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_complexity_from_script(Path("/scripts"))

        assert collector.metrics["complexity_avg"] is None
        assert collector.metrics["complexity_status"] == "unknown"
        assert collector.metrics["maintainability_avg"] is None
        assert collector.metrics["maintainability_status"] == "unknown"


class TestCollectDocsMetrics:
    """Issue #217: docs coverage in script mode via metrics-docs.sh."""

    def test_collect_docs_metrics_success(self) -> None:
        """Docs coverage from the script payload computes a pass status."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"docs_coverage_pct": 96.5},
        ) as mock_script:
            collector.collect_docs_metrics(Path("/scripts"), Path("/missing.txt"))

        mock_script.assert_called_once_with("metrics-docs.sh", Path("/scripts"))
        assert collector.metrics["docs_coverage"] == 96.5
        assert collector.metrics["docs_status"] == "pass"

    def test_collect_docs_metrics_below_threshold(self) -> None:
        """Docs coverage below the threshold computes a fail status."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"docs_coverage_pct": 92.0},
        ):
            collector.collect_docs_metrics(Path("/scripts"), Path("/missing.txt"))

        assert collector.metrics["docs_coverage"] == 92.0
        assert collector.metrics["docs_status"] == "fail"

    def test_collect_docs_metrics_script_failure_no_file(self) -> None:
        """Script failure with no report file degrades to unknown."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_docs_metrics(Path("/scripts"), Path("/missing.txt"))

        assert collector.metrics["docs_coverage"] is None
        assert collector.metrics["docs_status"] == "unknown"

    def test_collect_docs_metrics_missing_pct_key_is_unknown(self) -> None:
        """A payload without docs_coverage_pct yields unknown, not pass."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"status": "pass"},
        ):
            collector.collect_docs_metrics(Path("/scripts"), Path("/missing.txt"))

        assert collector.metrics["docs_coverage"] is None
        assert collector.metrics["docs_status"] == "unknown"

    def test_collect_docs_metrics_falls_back_to_report_file(self) -> None:
        """Script failure falls back to a pre-generated docs report file."""
        with TemporaryDirectory() as tmpdir:
            docs_file = Path(tmpdir) / "docs-report.txt"
            docs_file.write_text("RESULT: 97.5%")
            collector = MetricsCollector("test", {"docs_coverage": 95})

            with patch.object(collector, "collect_from_script", return_value=None):
                collector.collect_docs_metrics(Path("/scripts"), docs_file)

            assert collector.metrics["docs_coverage"] == 97.5
            assert collector.metrics["docs_status"] == "pass"

    def test_collect_docs_metrics_fallback_unparseable_file_is_unknown(self) -> None:
        """Script failure plus an unparseable report file yields unknown."""
        with TemporaryDirectory() as tmpdir:
            docs_file = Path(tmpdir) / "docs-report.txt"
            docs_file.write_text("no coverage data here")
            collector = MetricsCollector("test", {"docs_coverage": 95})

            with patch.object(collector, "collect_from_script", return_value=None):
                collector.collect_docs_metrics(Path("/scripts"), docs_file)

            assert collector.metrics["docs_coverage"] is None
            assert collector.metrics["docs_status"] == "unknown"

    def test_collect_docs_metrics_threshold_boundary(self) -> None:
        """Coverage exactly at the threshold passes (>= comparison)."""
        collector = MetricsCollector("test", {"docs_coverage": 95})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"docs_coverage_pct": 95.0},
        ):
            collector.collect_docs_metrics(Path("/scripts"), Path("/missing.txt"))

        assert collector.metrics["docs_coverage"] == 95.0
        assert collector.metrics["docs_status"] == "pass"


class TestUnifiedThresholdConvention:
    """Issue #206: Python owns status computation via the thresholds dict.

    Shell scripts emit raw numbers (and a legacy ``status`` field); the
    collector must ignore any script-provided status and recompute pass/fail
    from ``self.thresholds`` so threshold changes propagate everywhere.
    """

    def test_lint_status_ignores_script_status_field(self) -> None:
        """Lint status comes from the threshold, not the script's status."""
        collector = MetricsCollector("test", {"lint_violations": 5})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"violations": 3, "status": "fail"},
        ):
            collector.collect_lint_metrics(Path("/scripts"))

        assert collector.metrics["lint_violations"] == 3
        assert collector.metrics["lint_status"] == "pass"

    @pytest.mark.parametrize(
        ("threshold", "expected"),
        [(0, "fail"), (2, "fail"), (3, "pass"), (10, "pass")],
    )
    def test_lint_threshold_change_flips_status(
        self, threshold: int, expected: str
    ) -> None:
        """Changing the lint threshold changes the computed status."""
        collector = MetricsCollector("test", {"lint_violations": threshold})

        with patch.object(
            collector, "collect_from_script", return_value={"violations": 3}
        ):
            collector.collect_lint_metrics(Path("/scripts"))

        assert collector.metrics["lint_status"] == expected

    def test_lint_missing_raw_value_is_unknown(self) -> None:
        """A payload without a raw count yields unknown, not a trusted pass."""
        collector = MetricsCollector("test", {"lint_violations": 0})

        with patch.object(
            collector, "collect_from_script", return_value={"status": "pass"}
        ):
            collector.collect_lint_metrics(Path("/scripts"))

        assert collector.metrics["lint_violations"] is None
        assert collector.metrics["lint_status"] == "unknown"

    def test_typecheck_status_ignores_script_status_field(self) -> None:
        """Typecheck status comes from the threshold, not the script."""
        collector = MetricsCollector("test", {"type_errors": 10})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"errors": 5, "status": "fail"},
        ):
            collector.collect_typecheck_metrics(Path("/scripts"))

        assert collector.metrics["type_errors"] == 5
        assert collector.metrics["typecheck_status"] == "pass"

    @pytest.mark.parametrize(
        ("threshold", "expected"),
        [(0, "fail"), (5, "pass")],
    )
    def test_typecheck_threshold_change_flips_status(
        self, threshold: int, expected: str
    ) -> None:
        """Changing the type-error threshold changes the computed status."""
        collector = MetricsCollector("test", {"type_errors": threshold})

        with patch.object(collector, "collect_from_script", return_value={"errors": 5}):
            collector.collect_typecheck_metrics(Path("/scripts"))

        assert collector.metrics["typecheck_status"] == expected

    def test_typecheck_missing_raw_value_is_unknown(self) -> None:
        """A payload without a raw count yields unknown, not a trusted pass."""
        collector = MetricsCollector("test", {"type_errors": 0})

        with patch.object(
            collector, "collect_from_script", return_value={"status": "pass"}
        ):
            collector.collect_typecheck_metrics(Path("/scripts"))

        assert collector.metrics["type_errors"] is None
        assert collector.metrics["typecheck_status"] == "unknown"

    def test_security_metrics_ignores_script_status_field(self) -> None:
        """Security status comes from the threshold, not the script."""
        collector = MetricsCollector("test", {"security_issues": 5})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"bandit_issues": 3, "status": "fail"},
        ):
            collector.collect_security_metrics(Path("/scripts"))

        assert collector.metrics["security_issues"] == 3
        assert collector.metrics["security_status"] == "pass"

    @pytest.mark.parametrize(
        ("threshold", "expected"),
        [(0, "fail"), (2, "pass")],
    )
    def test_security_threshold_change_flips_status(
        self, threshold: int, expected: str
    ) -> None:
        """Changing the security threshold changes the computed status."""
        collector = MetricsCollector("test", {"security_issues": threshold})

        with patch.object(
            collector, "collect_from_script", return_value={"bandit_issues": 2}
        ):
            collector.collect_security_metrics(Path("/scripts"))

        assert collector.metrics["security_status"] == expected

    def test_security_metrics_null_issues_is_unknown(self) -> None:
        """A null bandit_issues payload (scan failed) yields unknown."""
        collector = MetricsCollector("test", {"security_issues": 0})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"bandit_issues": None, "status": "unknown"},
        ):
            collector.collect_security_metrics(Path("/scripts"))

        assert collector.metrics["security_issues"] is None
        assert collector.metrics["security_status"] == "unknown"

    def test_security_metrics_script_failure_is_unknown(self) -> None:
        """A failed security script run yields unknown status."""
        collector = MetricsCollector("test", {"security_issues": 0})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_security_metrics(Path("/scripts"))

        assert collector.metrics["security_issues"] is None
        assert collector.metrics["security_status"] == "unknown"

    def test_file_mode_security_threshold_propagates(self) -> None:
        """File-mode security uses <= threshold, so raising it passes."""
        with TemporaryDirectory() as tmpdir:
            sec_file = Path(tmpdir) / "security.json"
            sec_file.write_text(
                json.dumps({"results": [{"issue": "a"}, {"issue": "b"}]})
            )

            collector = MetricsCollector("test", {"security_issues": 5})
            collector.collect_security(sec_file)

            assert collector.metrics["security_issues"] == 2
            assert collector.metrics["security_status"] == "pass"

    def test_tests_status_ignores_script_status_field(self) -> None:
        """Test status is recomputed from raw counts, not trusted."""
        collector = MetricsCollector("test", {})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={
                "tests_total": 100,
                "tests_passed": 97,
                "tests_failed": 3,
                "tests_skipped": 0,
                "status": "pass",
            },
        ):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_status"] == "fail"

    def test_tests_zero_collected_is_unknown(self) -> None:
        """Zero collected tests (broken suite) yields unknown, not pass."""
        collector = MetricsCollector("test", {})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={
                "tests_total": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
            },
        ):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_status"] == "unknown"

    def test_tests_missing_raw_counts_is_unknown(self) -> None:
        """A payload without raw counts yields unknown status."""
        collector = MetricsCollector("test", {})

        with patch.object(
            collector, "collect_from_script", return_value={"status": "pass"}
        ):
            collector.collect_test_metrics(Path("/scripts"))

        assert collector.metrics["tests_total"] is None
        assert collector.metrics["tests_status"] == "unknown"

    def test_coverage_metrics_threshold_propagates(self) -> None:
        """Script-mode coverage status follows the thresholds dict."""
        collector = MetricsCollector("test", {"coverage": 80, "branch_coverage": 95})

        with patch.object(
            collector,
            "collect_from_script",
            return_value={"coverage_pct": 85.0, "branch_coverage_pct": 90.0},
        ):
            collector.collect_coverage_metrics(Path("/scripts"))

        assert collector.metrics["coverage"] == 85.0
        assert collector.metrics["coverage_status"] == "pass"
        assert collector.metrics["branch_coverage"] == 90.0
        assert collector.metrics["branch_coverage_status"] == "fail"

    def test_coverage_metrics_null_values_are_unknown(self) -> None:
        """Missing coverage numbers yield unknown statuses."""
        collector = MetricsCollector("test", {"coverage": 90, "branch_coverage": 85})

        with patch.object(collector, "collect_from_script", return_value={}):
            collector.collect_coverage_metrics(Path("/scripts"))

        assert collector.metrics["coverage"] is None
        assert collector.metrics["coverage_status"] == "unknown"
        assert collector.metrics["branch_coverage"] is None
        assert collector.metrics["branch_coverage_status"] == "unknown"

    def test_coverage_metrics_script_failure_is_unknown(self) -> None:
        """A failed coverage script run yields unknown statuses."""
        collector = MetricsCollector("test", {"coverage": 90, "branch_coverage": 85})

        with patch.object(collector, "collect_from_script", return_value=None):
            collector.collect_coverage_metrics(Path("/scripts"))

        assert collector.metrics["coverage"] is None
        assert collector.metrics["coverage_status"] == "unknown"

    def test_default_thresholds_contains_only_active_keys(self) -> None:
        """Every default threshold key drives at least one status."""
        thresholds = collect_metrics._default_thresholds()

        assert set(thresholds) == {
            "coverage",
            "branch_coverage",
            "mutation_score",
            "complexity",
            "docs_coverage",
            "security_issues",
            "maintainability",
            "lint_violations",
            "type_errors",
        }


class TestCollectPrecommitStatus:
    """Tests for pre-commit status collection (Issue #154)."""

    def _write_config(self, path: Path, hook_count: int) -> Path:
        """Write a .pre-commit-config.yaml with ``hook_count`` hooks."""
        config_path = path / ".pre-commit-config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "repos": [
                        {
                            "repo": "local",
                            "hooks": [{"id": f"hook-{i}"} for i in range(hook_count)],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return config_path

    def test_collect_precommit_status_counts_hooks(self) -> None:
        """Pre-commit status records total/passing/percentage from config."""
        with TemporaryDirectory() as tmpdir:
            config_path = self._write_config(Path(tmpdir), 32)
            collector = MetricsCollector("test", {})

            collector.collect_precommit_status(config_path)

            status = collector.metrics["precommit_status"]
            assert status["total_hooks"] == 32
            assert status["passing_hooks"] == 32
            assert status["percentage"] == 100.0
            assert status["status"] == "passing"

    def test_collect_precommit_status_missing_config(self) -> None:
        """Missing config degrades to zero hooks and unknown status."""
        collector = MetricsCollector("test", {})

        collector.collect_precommit_status(Path("/nonexistent/.pre-commit-config.yaml"))

        status = collector.metrics["precommit_status"]
        assert status["total_hooks"] == 0
        assert status["passing_hooks"] == 0
        assert status["percentage"] == 0.0
        assert status["status"] == "unknown"

    def test_collect_precommit_status_malformed_yaml(self) -> None:
        """Malformed YAML degrades to unknown status without raising."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".pre-commit-config.yaml"
            config_path.write_text("repos: [unterminated", encoding="utf-8")
            collector = MetricsCollector("test", {})

            collector.collect_precommit_status(config_path)

            status = collector.metrics["precommit_status"]
            assert status["total_hooks"] == 0
            assert status["status"] == "unknown"

    def test_collect_precommit_status_ignores_malformed_repos(self) -> None:
        """Non-dict repos and hookless repos contribute zero hooks."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".pre-commit-config.yaml"
            config_path.write_text(
                yaml.dump(
                    {
                        "repos": [
                            "not-a-mapping",
                            {"repo": "no-hooks"},
                            {"repo": "valid", "hooks": [{"id": "a"}, {"id": "b"}]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            collector = MetricsCollector("test", {})

            collector.collect_precommit_status(config_path)

            status = collector.metrics["precommit_status"]
            assert status["total_hooks"] == 2
            assert status["status"] == "passing"

    def test_collect_precommit_status_non_mapping_top_level(self) -> None:
        """A top-level YAML list yields zero hooks and unknown status."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".pre-commit-config.yaml"
            config_path.write_text("- a\n- b\n", encoding="utf-8")
            collector = MetricsCollector("test", {})

            collector.collect_precommit_status(config_path)

            assert collector.metrics["precommit_status"]["total_hooks"] == 0

    def test_uses_canonical_package_hook_counter(self) -> None:
        """collect_metrics imports the canonical hook counter (no duplication).

        Issue #154 DRY consolidation: the hook-counting helpers must live only
        in ``start_green_stay_green.generators.metrics``. ``collect_metrics``
        must import and reuse that canonical ``count_precommit_hooks`` rather
        than redefining its own ``_load_precommit_repos`` / ``_repo_hook_count``
        / ``_count_precommit_hooks`` copies.
        """
        # The duplicated private helpers must be gone from the script module.
        assert not hasattr(collect_metrics, "_load_precommit_repos")
        assert not hasattr(collect_metrics, "_repo_hook_count")
        assert not hasattr(collect_metrics, "_count_precommit_hooks")
        # The script re-exports the canonical helper (same object), so
        # collected status matches the canonical count for the same config.
        assert collect_metrics.__dict__["count_precommit_hooks"] is (
            count_precommit_hooks
        )
        with TemporaryDirectory() as tmpdir:
            config_path = self._write_config(Path(tmpdir), 7)
            collector = MetricsCollector("test", {})

            collector.collect_precommit_status(config_path)

            assert collector.metrics["precommit_status"]["total_hooks"] == (
                count_precommit_hooks(config_path)
            )

    def test_collect_precommit_status_delegates_to_shared_builder(self) -> None:
        """The status dict is built by the canonical ``precommit_status`` helper.

        Issue #154 DRY consolidation: ``collect_precommit_status`` must not
        re-derive ``has_hooks``/``passing_hooks``/``percentage``/``status``;
        it must delegate dict construction to the shared
        ``precommit_status`` builder in the metrics generator module.
        """
        with TemporaryDirectory() as tmpdir:
            config_path = self._write_config(Path(tmpdir), 13)
            collector = MetricsCollector("test", {})

            with patch.object(
                collect_metrics,
                "precommit_status",
                wraps=precommit_status,
            ) as spy:
                collector.collect_precommit_status(config_path)

            spy.assert_called_once_with(13)
            assert collector.metrics["precommit_status"] == precommit_status(13)


class TestCollectCIStatus:
    """Tests for ``collect_ci_status`` on MetricsCollector (Issue #159)."""

    def _write_workflow(self, path: Path, name: str, job_ids: list[str]) -> Path:
        """Write a workflow file declaring the given job ids.

        Args:
            path: Directory to write the workflow into.
            name: Workflow filename (e.g., ``ci.yml``).
            job_ids: Job identifiers for the ``jobs`` mapping.

        Returns:
            Path to the written workflow file.
        """
        workflow_path = path / name
        workflow_path.write_text(
            yaml.dump({"jobs": {job_id: {} for job_id in job_ids}}),
            encoding="utf-8",
        )
        return workflow_path

    def _clear_github_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Remove GitHub Actions env vars so the static fallback is used.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
        """
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    def test_static_fallback_counts_jobs_with_unknown_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without API env vars, jobs are counted statically as unknown."""
        self._clear_github_env(monkeypatch)
        with TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir)
            self._write_workflow(workflows, "ci.yml", ["lint", "test"])
            self._write_workflow(workflows, "release.yml", ["publish"])
            collector = MetricsCollector("test", {})

            collector.collect_ci_status(workflows)

            status = collector.metrics["ci_status"]
            assert status["total_jobs"] == 3
            assert status["passing_jobs"] == 0
            assert status["percentage"] == 0.0
            assert status["status"] == "unknown"
            assert "run_url" not in status

    def test_missing_workflows_dir_degrades_to_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A missing workflows directory yields total 0 and unknown status."""
        self._clear_github_env(monkeypatch)
        collector = MetricsCollector("test", {})

        collector.collect_ci_status(Path("/nonexistent/.github/workflows"))

        status = collector.metrics["ci_status"]
        assert status["total_jobs"] == 0
        assert status["status"] == "unknown"

    def test_malformed_workflow_yaml_never_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed workflow YAML degrades gracefully instead of raising."""
        self._clear_github_env(monkeypatch)
        with TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir)
            (workflows / "broken.yml").write_text(
                "jobs: [unterminated", encoding="utf-8"
            )
            collector = MetricsCollector("test", {})

            collector.collect_ci_status(workflows)

            status = collector.metrics["ci_status"]
            assert status["total_jobs"] == 0
            assert status["status"] == "unknown"

    def test_api_path_counts_job_conclusions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With API env vars, job conclusions from the latest run are counted."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        payloads = {
            "/repos/owner/repo/actions/runs"
            "?branch=main&status=completed&per_page=1": {
                "workflow_runs": [
                    {
                        "id": 42,
                        "html_url": "https://github.com/owner/repo/actions/runs/42",
                    }
                ]
            },
            "/repos/owner/repo/actions/runs/42/jobs?per_page=100": {
                "jobs": [
                    {"conclusion": "success"},
                    {"conclusion": "success"},
                    {"conclusion": "failure"},
                ]
            },
        }

        with patch.object(
            collect_metrics,
            "_github_api_json",
            side_effect=lambda path, _token: payloads[path],
        ):
            collector = MetricsCollector("test", {})
            collector.collect_ci_status(Path("/nonexistent"))

        status = collector.metrics["ci_status"]
        assert status["total_jobs"] == 3
        assert status["passing_jobs"] == 2
        assert status["percentage"] == pytest.approx(66.67, abs=0.01)
        assert status["status"] == "failing"
        assert status["run_url"] == "https://github.com/owner/repo/actions/runs/42"

    def test_api_all_passing_yields_passing_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All-success job conclusions yield a 100% passing status."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        def fake_api(path: str, _token: str) -> dict[str, object]:
            if "/jobs" in path:
                return {"jobs": [{"conclusion": "success"}] * 7}
            return {
                "workflow_runs": [
                    {
                        "id": 7,
                        "html_url": "https://github.com/owner/repo/actions/runs/7",
                    }
                ]
            }

        with patch.object(collect_metrics, "_github_api_json", side_effect=fake_api):
            collector = MetricsCollector("test", {})
            collector.collect_ci_status(Path("/nonexistent"))

        status = collector.metrics["ci_status"]
        assert status["total_jobs"] == 7
        assert status["passing_jobs"] == 7
        assert status["percentage"] == 100.0
        assert status["status"] == "passing"

    def test_api_skipped_jobs_excluded_from_denominator(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skipped jobs do not count against the passing percentage.

        A conditionally-skipped job (e.g. a deploy gated on a branch
        condition) must not drag an otherwise all-green run below 100%.
        """
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        def fake_api(path: str, _token: str) -> dict[str, object]:
            if "/jobs" in path:
                return {
                    "jobs": [
                        {"conclusion": "success"},
                        {"conclusion": "success"},
                        {"conclusion": "skipped"},
                    ]
                }
            return {
                "workflow_runs": [
                    {
                        "id": 9,
                        "html_url": "https://github.com/owner/repo/actions/runs/9",
                    }
                ]
            }

        with patch.object(collect_metrics, "_github_api_json", side_effect=fake_api):
            collector = MetricsCollector("test", {})
            collector.collect_ci_status(Path("/nonexistent"))

        status = collector.metrics["ci_status"]
        assert status["total_jobs"] == 2
        assert status["passing_jobs"] == 2
        assert status["percentage"] == 100.0
        assert status["status"] == "passing"

    def test_api_all_jobs_skipped_degrades_to_unknown(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A run where every job was skipped yields an unknown status."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        def fake_api(path: str, _token: str) -> dict[str, object]:
            if "/jobs" in path:
                return {"jobs": [{"conclusion": "skipped"}] * 2}
            return {"workflow_runs": [{"id": 9}]}

        with patch.object(collect_metrics, "_github_api_json", side_effect=fake_api):
            collector = MetricsCollector("test", {})
            collector.collect_ci_status(Path("/nonexistent"))

        status = collector.metrics["ci_status"]
        assert status["total_jobs"] == 0
        assert status["status"] == "unknown"

    def test_token_with_embedded_whitespace_is_rejected(self) -> None:
        """A token containing whitespace never reaches the HTTP layer.

        ``http.client`` does not sanitize header values; rejecting
        whitespace-bearing tokens closes the header-injection path.
        """
        with patch("http.client.HTTPSConnection") as mock_connection:
            result = collect_metrics._github_api_json(
                "/repos/owner/repo/actions/runs", "bad\ntoken: injected"
            )

        assert result is None
        mock_connection.assert_not_called()

    def test_token_surrounding_whitespace_is_stripped(self) -> None:
        """Leading/trailing whitespace on the token is stripped, not fatal."""
        response = Mock()
        response.status = 200
        response.read.return_value = b'{"ok": true}'
        connection = Mock()
        connection.getresponse.return_value = response

        with patch("http.client.HTTPSConnection", return_value=connection):
            result = collect_metrics._github_api_json("/path", "  good-token\n")

        assert result == {"ok": True}
        headers = connection.request.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer good-token"

    def test_api_failure_falls_back_to_static_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An API error falls back to the static workflow count, never raising."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        with TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir)
            self._write_workflow(workflows, "ci.yml", ["lint", "test"])

            with patch.object(collect_metrics, "_github_api_json", return_value=None):
                collector = MetricsCollector("test", {})
                collector.collect_ci_status(workflows)

            status = collector.metrics["ci_status"]
            assert status["total_jobs"] == 2
            assert status["status"] == "unknown"

    def test_api_empty_runs_falls_back_to_static_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No completed runs on main falls back to the static count."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")

        with TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir)
            self._write_workflow(workflows, "ci.yml", ["lint"])

            with patch.object(
                collect_metrics,
                "_github_api_json",
                return_value={"workflow_runs": []},
            ):
                collector = MetricsCollector("test", {})
                collector.collect_ci_status(workflows)

            status = collector.metrics["ci_status"]
            assert status["total_jobs"] == 1
            assert status["status"] == "unknown"

    def test_invalid_repository_env_falls_back_to_static(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A malformed GITHUB_REPOSITORY skips the API path entirely."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_REPOSITORY", "not a repo slug!")

        with patch.object(collect_metrics, "_github_api_json") as mock_api:
            collector = MetricsCollector("test", {})
            collector.collect_ci_status(Path("/nonexistent"))

        mock_api.assert_not_called()
        assert collector.metrics["ci_status"]["status"] == "unknown"

    def test_uses_canonical_package_job_counter(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """collect_metrics imports the canonical CI helpers (no duplication).

        Issue #159 DRY: the job-counting and status-building helpers live
        only in ``start_green_stay_green.generators.metrics``;
        ``collect_metrics`` reuses the same objects instead of redefining
        them.
        """
        assert collect_metrics.__dict__["count_ci_jobs"] is count_ci_jobs
        assert collect_metrics.__dict__["ci_status"] is ci_status

        self._clear_github_env(monkeypatch)
        with TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir)
            self._write_workflow(workflows, "ci.yml", ["a", "b", "c"])
            collector = MetricsCollector("test", {})

            collector.collect_ci_status(workflows)

            assert collector.metrics["ci_status"]["total_jobs"] == (
                count_ci_jobs(workflows)
            )


class TestMainScriptMode:
    """Tests for main() with --metrics-mode script."""

    def test_main_script_mode_calls_scripts(self) -> None:
        """Test that script mode calls quality scripts."""
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "metrics.json"
            docs_file = Path(tmpdir) / "docs.txt"
            docs_file.write_text("RESULT: 96.5%")

            with (
                patch(
                    "sys.argv",
                    [
                        "collect_metrics.py",
                        "--project-name",
                        "test",
                        "--output",
                        str(output),
                        "--metrics-mode",
                        "script",
                        "--scripts-dir",
                        tmpdir,
                        "--docs-file",
                        str(docs_file),
                    ],
                ),
                patch.object(
                    MetricsCollector,
                    "collect_from_script",
                    return_value=None,
                ),
            ):
                result = collect_main()

            assert result == 0
            assert output.exists()
            data = json.loads(output.read_text())
            # Security failure should report "unknown", not "pass"
            assert data["metrics"]["security_status"] == "unknown"
            assert data["metrics"]["security_issues"] is None
            # Docs coverage falls back to the report file when the
            # metrics-docs.sh script yields no data (Issue #217)
            assert data["metrics"]["docs_coverage"] == 96.5
            assert data["metrics"]["docs_status"] == "pass"

    def test_main_file_mode_backward_compat(self) -> None:
        """Test that file mode remains backward compatible."""
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "metrics.json"

            with patch(
                "sys.argv",
                [
                    "collect_metrics.py",
                    "--project-name",
                    "test",
                    "--output",
                    str(output),
                    "--metrics-mode",
                    "file",
                ],
            ):
                result = collect_main()

            assert result == 0
            assert output.exists()

    def test_main_mutation_score_override(self) -> None:
        """Test that explicit --mutation-score overrides cache reading."""
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "metrics.json"

            with patch(
                "sys.argv",
                [
                    "collect_metrics.py",
                    "--project-name",
                    "test",
                    "--output",
                    str(output),
                    "--mutation-score",
                    "92.5",
                ],
            ):
                result = collect_main()

            assert result == 0
            data = json.loads(output.read_text())
            assert data["metrics"]["mutation_score"] == 92.5
            assert data["metrics"]["mutation_status"] == "pass"

    def test_main_no_mutation_score_reads_cache(self) -> None:
        """Test that omitting --mutation-score reads from cache."""
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "metrics.json"

            with (
                patch(
                    "sys.argv",
                    [
                        "collect_metrics.py",
                        "--project-name",
                        "test",
                        "--output",
                        str(output),
                    ],
                ),
                patch.object(
                    MetricsCollector,
                    "collect_mutation_from_cache",
                    autospec=True,
                ) as mock_cache,
            ):

                def _set_unknown(self: MetricsCollector, _cache_path: Path) -> None:
                    self.metrics["mutation_score"] = None
                    self.metrics["mutation_status"] = "unknown"

                mock_cache.side_effect = _set_unknown
                result = collect_main()

            assert result == 0
            data = json.loads(output.read_text())
            assert data["metrics"]["mutation_score"] is None
            assert data["metrics"]["mutation_status"] == "unknown"
