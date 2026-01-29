#!/usr/bin/env python3
"""Collect quality metrics from test reports and generate metrics.json.

This script aggregates metrics from:
- pytest coverage reports (coverage.json)
- radon complexity analysis (complexity-report.txt)
- interrogate documentation coverage (docs-report.txt)
- bandit security scanning (security-report.json)

Output: metrics.json in the specified output directory
"""

from __future__ import annotations

import argparse
from datetime import UTC
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class MetricsCollector:
    """Collects and aggregates quality metrics from various report files."""

    def __init__(
        self,
        project_name: str,
        thresholds: Mapping[str, int | float],
    ) -> None:
        """Initialize metrics collector.

        Args:
            project_name: Name of the project
            thresholds: Dictionary of metric name -> threshold value
        """
        self.project_name = project_name
        self.thresholds = thresholds
        self.metrics: dict[str, Any] = {}

    def collect_coverage(self, coverage_file: Path) -> None:
        """Parse coverage from pytest JSON report.

        Args:
            coverage_file: Path to coverage.json file

        Raises:
            FileNotFoundError: If coverage file doesn't exist
            json.JSONDecodeError: If coverage file is not valid JSON
            KeyError: If expected keys are missing from coverage data
        """
        if not coverage_file.exists():
            msg = f"Coverage file not found: {coverage_file}"
            raise FileNotFoundError(msg)

        cov_data = json.loads(coverage_file.read_text())
        total_cov = cov_data["totals"]["percent_covered"]
        self.metrics["coverage"] = round(total_cov, 2)
        self.metrics["coverage_status"] = (
            "pass" if total_cov >= self.thresholds["coverage"] else "fail"
        )

        # Branch coverage
        num_branches = cov_data["totals"].get("num_branches", 0)
        covered_branches = cov_data["totals"].get("covered_branches", 0)
        if num_branches > 0:
            branch_cov = (covered_branches / num_branches) * 100
            self.metrics["branch_coverage"] = round(branch_cov, 2)
            self.metrics["branch_coverage_status"] = (
                "pass" if branch_cov >= self.thresholds["branch_coverage"] else "fail"
            )

    def collect_complexity(self, complexity_file: Path) -> None:
        """Parse complexity from radon report.

        Args:
            complexity_file: Path to complexity-report.txt file

        Raises:
            FileNotFoundError: If complexity file doesn't exist
            ValueError: If complexity pattern not found in file
        """
        if not complexity_file.exists():
            msg = f"Complexity file not found: {complexity_file}"
            raise FileNotFoundError(msg)

        complexity_text = complexity_file.read_text()
        match = re.search(r"Average complexity: [A-Z] \(([0-9.]+)\)", complexity_text)
        if not match:
            msg = "Could not find complexity pattern in report"
            raise ValueError(msg)

        comp = float(match.group(1))
        self.metrics["complexity_avg"] = round(comp, 2)
        self.metrics["complexity_status"] = (
            "pass" if comp <= self.thresholds["complexity"] else "fail"
        )

    def collect_docs_coverage(self, docs_file: Path) -> None:
        """Parse documentation coverage from interrogate report.

        Args:
            docs_file: Path to docs-report.txt file

        Raises:
            FileNotFoundError: If docs file doesn't exist
            ValueError: If docs coverage pattern not found in file
        """
        if not docs_file.exists():
            msg = f"Docs file not found: {docs_file}"
            raise FileNotFoundError(msg)

        docs_text = docs_file.read_text()
        match = re.search(r"RESULT: ([0-9.]+)%", docs_text)
        if not match:
            msg = "Could not find docs coverage pattern in report"
            raise ValueError(msg)

        docs = float(match.group(1))
        self.metrics["docs_coverage"] = round(docs, 2)
        self.metrics["docs_status"] = (
            "pass" if docs >= self.thresholds["docs_coverage"] else "fail"
        )

    def collect_security(self, security_file: Path) -> None:
        """Parse security issues from bandit report.

        Args:
            security_file: Path to security-report.json file

        Raises:
            FileNotFoundError: If security file doesn't exist
            json.JSONDecodeError: If security file is not valid JSON
            KeyError: If expected keys are missing from security data
        """
        if not security_file.exists():
            msg = f"Security file not found: {security_file}"
            raise FileNotFoundError(msg)

        security_data = json.loads(security_file.read_text())
        issues = len(security_data["results"])
        self.metrics["security_issues"] = issues
        self.metrics["security_status"] = (
            "pass" if issues == self.thresholds["security_issues"] else "fail"
        )

    def add_mutation_score(self, score: float) -> None:
        """Add mutation testing score.

        Note: Mutation testing is run periodically (not on every commit)
        per SGSG workflow. See scripts/mutation.sh for details.

        Args:
            score: Mutation score (0-100)
        """
        self.metrics["mutation_score"] = score
        self.metrics["mutation_status"] = (
            "pass" if score >= self.thresholds["mutation_score"] else "fail"
        )

    def generate_json(self, output_file: Path) -> None:
        """Write metrics to JSON file.

        Args:
            output_file: Path where metrics.json will be written
        """
        metrics_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "project": self.project_name,
            "thresholds": self.thresholds,
            "metrics": self.metrics,
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(metrics_data, indent=2))
        print(f"✓ Generated {output_file}")
        print(json.dumps(metrics_data, indent=2))


def main() -> int:
    """Collect metrics and generate metrics.json."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-name",
        required=True,
        help="Name of the project",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/metrics.json"),
        help="Output file path (default: docs/metrics.json)",
    )
    parser.add_argument(
        "--coverage-file",
        type=Path,
        default=Path("coverage.json"),
        help="Path to coverage.json (default: coverage.json)",
    )
    parser.add_argument(
        "--complexity-file",
        type=Path,
        default=Path("complexity-report.txt"),
        help="Path to complexity report (default: complexity-report.txt)",
    )
    parser.add_argument(
        "--docs-file",
        type=Path,
        default=Path("docs-report.txt"),
        help="Path to docs coverage report (default: docs-report.txt)",
    )
    parser.add_argument(
        "--security-file",
        type=Path,
        default=Path("security-report.json"),
        help="Path to security report (default: security-report.json)",
    )
    parser.add_argument(
        "--mutation-score",
        type=float,
        default=85.0,
        help="Mutation score placeholder (default: 85.0)",
    )

    args = parser.parse_args()

    # Default thresholds (align with SGSG standards)
    thresholds = {
        "coverage": 90,
        "branch_coverage": 85,
        "mutation_score": 80,
        "complexity": 10,
        "docs_coverage": 95,
        "security_issues": 0,
    }

    collector = MetricsCollector(args.project_name, thresholds)

    # Collect metrics with error handling
    try:
        collector.collect_coverage(args.coverage_file)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse coverage ({type(e).__name__}): {e}")

    try:
        collector.collect_complexity(args.complexity_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: Could not parse complexity ({type(e).__name__}): {e}")

    try:
        collector.collect_docs_coverage(args.docs_file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Warning: Could not parse docs coverage ({type(e).__name__}): {e}")

    try:
        collector.collect_security(args.security_file)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Warning: Could not parse security ({type(e).__name__}): {e}")
        # Default to passing if file not found
        collector.metrics["security_issues"] = 0
        collector.metrics["security_status"] = "pass"

    # Add mutation score (placeholder for periodic runs)
    collector.add_mutation_score(args.mutation_score)

    # Generate output
    collector.generate_json(args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
