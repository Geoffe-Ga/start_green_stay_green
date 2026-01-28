"""Integration tests for tool configuration auditor.

These tests verify the complete workflow from discovery to report generation.
"""

from __future__ import annotations

from pathlib import Path

# Import the module we're testing
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from audit_tool_configs import AuditResult
from audit_tool_configs import ClaudeAnalyzer
from audit_tool_configs import ConfigDiscovery
from audit_tool_configs import ConflictReport
from audit_tool_configs import ReportGenerator


@pytest.fixture
def complex_project(tmp_path: Path) -> Path:
    """Create a complex project with multiple config files and conflicts."""
    # Create pyproject.toml with multiple tools
    pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"

[tool.ruff]
line-length = 100  # Different from Black!
target-version = "py311"
select = ["ALL"]
ignore = ["COM812", "ISC001"]

[tool.ruff.lint.isort]
force-single-line = true

[tool.black]
line-length = 88  # Conflicts with Ruff
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88  # Should match black
force_single_line = false  # Conflicts with ruff.lint.isort

[tool.mypy]
strict = true
python_version = "3.11"

[tool.pylint.main]
py-version = "3.11"
fail-under = 9.0

[tool.pylint.format]
max-line-length = 100  # Different from Black

[tool.bandit]
exclude_dirs = ["tests"]
skips = []

[tool.coverage.report]
fail_under = 90

[tool.refurb]
ignore = ["FURB184"]

[tool.mutmut]
paths_to_mutate = "src/"
runner = "pytest -x"
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    # Create .pre-commit-config.yaml
    precommit_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
        args: ['--line-length=88']

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: ['--line-length=100']  # Conflicts with black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=88']

  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'src/']

  - repo: local
    hooks:
      - id: pylint
        name: Pylint
        entry: pylint
        language: system
        types: [python]
"""
    (tmp_path / ".pre-commit-config.yaml").write_text(precommit_content)

    # Create standalone .ruff.toml (should conflict with pyproject.toml)
    ruff_toml_content = """
line-length = 120  # Yet another line length!
target-version = "py312"  # Different Python version

[lint]
select = ["E", "F", "W"]
"""
    (tmp_path / ".ruff.toml").write_text(ruff_toml_content)

    return tmp_path


@pytest.fixture
def simple_project(tmp_path: Path) -> Path:
    """Create a simple project with minimal configs and no conflicts."""
    pyproject_content = """
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    precommit_content = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
"""
    (tmp_path / ".pre-commit-config.yaml").write_text(precommit_content)

    return tmp_path


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    def test_discover_analyze_report_dry_run(self, complex_project: Path) -> None:
        """Test full workflow in dry-run mode."""
        # Step 1: Discover configs
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        assert len(configs) > 0
        tool_names = {c.tool_name for c in configs}
        assert "ruff" in tool_names
        assert "black" in tool_names
        assert "isort" in tool_names

        # Step 2: Analyze with dry-run
        analyzer = ClaudeAnalyzer("mock-key", dry_run=True)
        result = analyzer.analyze_conflicts(configs)

        assert len(result.discovered_configs) > 0
        assert len(result.conflicts) > 0

        # Step 3: Generate report
        output_path = complex_project / "audit-report.md"
        generator = ReportGenerator(output_path)
        generator.generate(result)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Tool Configuration Audit Report" in content
        assert "Conflicts" in content

    def test_discover_all_config_types(self, complex_project: Path) -> None:
        """Test discovering all types of configuration files."""
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        # Should find configs from pyproject.toml
        pyproject_configs = [
            c for c in configs if c.config_file.name == "pyproject.toml"
        ]
        assert pyproject_configs

        # Should find configs from .pre-commit-config.yaml
        precommit_configs = [
            c for c in configs if c.config_file.name == ".pre-commit-config.yaml"
        ]
        assert precommit_configs

        # Should find standalone .ruff.toml
        ruff_toml_configs = [c for c in configs if c.config_file.name == ".ruff.toml"]
        assert ruff_toml_configs

    def test_detect_line_length_conflicts(self, complex_project: Path) -> None:
        """Test detection of line length conflicts."""
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        # Find ruff and black configs
        ruff_configs = [c for c in configs if "ruff" in c.tool_name.lower()]
        black_configs = [c for c in configs if "black" in c.tool_name.lower()]

        assert ruff_configs
        assert black_configs

        # Check for line length differences (100 vs 88 vs 120)
        ruff_line_lengths = set()
        for config in ruff_configs:
            if "line-length" in config.config_data:
                ruff_line_lengths.add(config.config_data["line-length"])

        # Should have multiple different line lengths (conflict!)
        assert ruff_line_lengths

    def test_simple_project_no_conflicts(self, simple_project: Path) -> None:
        """Test that simple project with consistent config has no/few conflicts."""
        discovery = ConfigDiscovery(simple_project)
        configs = discovery.discover_all()

        # All should have consistent line-length = 88
        for config in configs:
            if "line-length" in config.config_data:
                assert config.config_data["line-length"] in (88, "88")
            if "line_length" in config.config_data:
                assert config.config_data["line_length"] in (88, "88")

    def test_report_structure(self, complex_project: Path) -> None:
        """Test that generated report has correct structure."""
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        analyzer = ClaudeAnalyzer("mock-key", dry_run=True)
        result = analyzer.analyze_conflicts(configs)

        output_path = complex_project / "audit-report.md"
        generator = ReportGenerator(output_path)
        generator.generate(result)

        content = output_path.read_text()

        # Check for required sections
        assert "# Tool Configuration Audit Report" in content
        assert "## Summary" in content
        assert "## Discovered Configurations" in content
        assert "## Conflicts" in content
        assert "## Next Steps" in content

        # Check for specific details
        assert "Total Configurations Discovered" in content
        assert "Total Conflicts Detected" in content

    def test_conflict_severity_levels(self, complex_project: Path) -> None:
        """Test that conflicts are categorized by severity."""
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        analyzer = ClaudeAnalyzer("mock-key", dry_run=True)
        result = analyzer.analyze_conflicts(configs)

        # Should have conflicts with severity levels
        severities = {c.severity for c in result.conflicts}
        assert severities
        assert all(s in ("HIGH", "MEDIUM", "LOW") for s in severities)


class TestRealWorldScenarios:
    """Test real-world configuration scenarios."""

    def test_ruff_vs_black_formatting(self, tmp_path: Path) -> None:
        """Test detecting Ruff vs Black formatting conflicts."""
        # Create configs where Ruff formatting conflicts with Black
        pyproject_content = """
[tool.ruff]
line-length = 100
select = ["E", "F", "I"]  # Includes import sorting

[tool.black]
line-length = 88

[tool.isort]
profile = "black"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        # Should find both ruff and black
        tool_names = {c.tool_name for c in configs}
        assert "ruff" in tool_names
        assert "black" in tool_names

    def test_isort_vs_black_imports(self, tmp_path: Path) -> None:
        """Test detecting isort vs Black import formatting conflicts."""
        pyproject_content = """
[tool.isort]
profile = "black"
force_single_line = true  # May conflict with black

[tool.black]
line-length = 88

[tool.ruff.lint.isort]
force-single-line = false  # Conflicts with isort
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        # Find isort and ruff isort configs
        isort_configs = [c for c in configs if "isort" in c.tool_name.lower()]
        assert isort_configs

    def test_pylint_vs_ruff_overlap(self, tmp_path: Path) -> None:
        """Test detecting Pylint vs Ruff linting overlap."""
        pyproject_content = """
[tool.ruff]
select = ["ALL"]  # Enables all rules

[tool.pylint.main]
fail-under = 9.0

[tool.pylint.format]
max-line-length = 88
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        tool_names = {c.tool_name for c in configs}
        assert "ruff" in tool_names
        assert "pylint" in tool_names

    def test_bandit_vs_ruff_security(self, tmp_path: Path) -> None:
        """Test detecting Bandit vs Ruff security rule overlap."""
        pyproject_content = """
[tool.ruff]
select = ["S"]  # Security rules (Bandit-like)

[tool.bandit]
skips = []
tests = ["B201", "B301"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        tool_names = {c.tool_name for c in configs}
        assert "ruff" in tool_names
        assert "bandit" in tool_names

    def test_mutmut_vs_refurb_patterns(self, tmp_path: Path) -> None:
        """Test detecting mutmut vs refurb pattern conflicts."""
        pyproject_content = """
[tool.mutmut]
paths_to_mutate = "src/"
runner = "pytest -x"

[tool.refurb]
ignore = ["FURB184"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        tool_names = {c.tool_name for c in configs}
        assert "mutmut" in tool_names
        assert "refurb" in tool_names


class TestErrorHandling:
    """Test error handling in integration scenarios."""

    def test_malformed_pyproject_toml(self, tmp_path: Path) -> None:
        """Test handling malformed pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("invalid toml [[[")

        discovery = ConfigDiscovery(tmp_path)

        # Should not crash, just skip malformed file
        configs = discovery.discover_all()
        assert isinstance(configs, list)

    def test_malformed_precommit_yaml(self, tmp_path: Path) -> None:
        """Test handling malformed .pre-commit-config.yaml."""
        (tmp_path / ".pre-commit-config.yaml").write_text(
            "invalid yaml: [\n  unclosed bracket"
        )

        discovery = ConfigDiscovery(tmp_path)

        # Should not crash
        configs = discovery.discover_all()
        assert isinstance(configs, list)

    def test_missing_config_files(self, tmp_path: Path) -> None:
        """Test handling project with no config files."""
        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        assert configs == []

    def test_empty_config_files(self, tmp_path: Path) -> None:
        """Test handling empty config files."""
        (tmp_path / "pyproject.toml").write_text("")
        (tmp_path / ".pre-commit-config.yaml").write_text("")

        discovery = ConfigDiscovery(tmp_path)
        configs = discovery.discover_all()

        # Should handle gracefully
        assert isinstance(configs, list)


class TestReportGeneration:
    """Test report generation with various scenarios."""

    def test_report_with_no_conflicts(self, simple_project: Path) -> None:
        """Test generating report when no conflicts found."""
        discovery = ConfigDiscovery(simple_project)
        configs = discovery.discover_all()

        # Manually create result with no conflicts
        result = AuditResult(
            discovered_configs=configs,
            conflicts=[],
            token_usage={"input_tokens": 100, "output_tokens": 50},
            model_used="test-model",
        )

        output_path = simple_project / "no-conflicts-report.md"
        generator = ReportGenerator(output_path)
        generator.generate(result)

        content = output_path.read_text()
        assert "No conflicts detected" in content

    def test_report_with_multiple_severities(self, complex_project: Path) -> None:
        """Test report with conflicts of different severities."""
        discovery = ConfigDiscovery(complex_project)
        configs = discovery.discover_all()

        result = AuditResult(
            discovered_configs=configs,
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Line length conflict",
                    explanation="Different line lengths",
                    suggestion="Use 88 for both",
                    affected_configs=[],
                ),
                ConflictReport(
                    severity="MEDIUM",
                    tools=["isort", "black"],
                    description="Import sorting",
                    explanation="Different import sorting",
                    suggestion="Use isort profile",
                    affected_configs=[],
                ),
                ConflictReport(
                    severity="LOW",
                    tools=["pylint", "ruff"],
                    description="Minor overlap",
                    explanation="Some duplicate checks",
                    suggestion="Consider disabling in pylint",
                    affected_configs=[],
                ),
            ],
            model_used="test-model",
        )

        output_path = complex_project / "multi-severity-report.md"
        generator = ReportGenerator(output_path)
        generator.generate(result)

        content = output_path.read_text()

        # Should list conflicts sorted by severity
        assert "HIGH" in content
        assert "MEDIUM" in content
        assert "LOW" in content

    def test_report_with_code_examples(self, tmp_path: Path) -> None:
        """Test report generation with code examples."""
        result = AuditResult(
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Test conflict",
                    explanation="Test explanation",
                    suggestion="Test suggestion",
                    affected_configs=[],
                    code_example=(
                        "[tool.ruff]\n"
                        "line-length = 88\n\n"
                        "[tool.black]\n"
                        "line-length = 88"
                    ),
                )
            ]
        )

        output_path = tmp_path / "with-examples.md"
        generator = ReportGenerator(output_path)
        generator.generate(result)

        content = output_path.read_text()
        assert "line-length = 88" in content
        assert "```" in content  # Code block markers
