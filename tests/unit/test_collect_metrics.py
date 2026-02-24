"""Tests for scripts/collect_metrics.py - metrics collection logic."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

# Import the module we're testing
import sys
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from collect_metrics import MetricsCollector
from collect_metrics import main as collect_main


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
        with sqlite3.connect(str(cache_path)) as conn:
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
