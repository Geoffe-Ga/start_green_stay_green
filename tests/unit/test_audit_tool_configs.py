"""Unit tests for tool configuration auditor.

NOTE: This test suite includes direct testing of private methods (prefixed with _).
This is intentional for unit testing granular internal functionality. While production
code should not access private members, test code legitimately needs to verify
internal implementation details for thorough coverage. All SLF001 warnings in this
file are justified by this testing pattern.
"""

from __future__ import annotations

import json
from pathlib import Path

# Import the module we're testing
import sys
from unittest.mock import Mock
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from anthropic.types import TextBlock
from audit_tool_configs import AnalysisError
from audit_tool_configs import AuditResult
from audit_tool_configs import AuditorError
from audit_tool_configs import ClaudeAnalyzer
from audit_tool_configs import ConfigDiscovery
from audit_tool_configs import ConfigDiscoveryError
from audit_tool_configs import ConflictReport
from audit_tool_configs import ReportGenerator
from audit_tool_configs import ToolConfig
from audit_tool_configs import get_api_key
from audit_tool_configs import main
from audit_tool_configs import parse_args


@pytest.fixture
def sample_project_root(tmp_path: Path) -> Path:
    """Create a sample project structure with configs."""
    # Create pyproject.toml
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

[tool.mypy]
strict = true
python_version = "3.11"
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

  - repo: local
    hooks:
      - id: ruff-check
        name: Ruff
        entry: ruff check
        language: system
"""
    (tmp_path / ".pre-commit-config.yaml").write_text(precommit_content)

    return tmp_path


@pytest.fixture
def sample_configs() -> list[ToolConfig]:
    """Create sample tool configurations for testing."""
    return [
        ToolConfig(
            tool_name="ruff",
            config_file=Path("pyproject.toml"),
            config_section="tool.ruff",
            config_data={
                "line-length": 88,
                "target-version": "py311",
                "select": ["ALL"],
            },
        ),
        ToolConfig(
            tool_name="black",
            config_file=Path("pyproject.toml"),
            config_section="tool.black",
            config_data={
                "line-length": 88,
                "target-version": ["py311"],
            },
        ),
        ToolConfig(
            tool_name="isort",
            config_file=Path("pyproject.toml"),
            config_section="tool.isort",
            config_data={
                "profile": "black",
                "line_length": 88,
            },
        ),
    ]


class TestToolConfig:
    """Tests for ToolConfig dataclass."""

    def test_init(self) -> None:
        """Test ToolConfig initialization."""
        config = ToolConfig(
            tool_name="ruff",
            config_file=Path("pyproject.toml"),
            config_section="tool.ruff",
            config_data={"line-length": 88},
        )

        assert config.tool_name == "ruff"
        assert config.config_file == Path("pyproject.toml")
        assert config.config_section == "tool.ruff"
        assert config.config_data == {"line-length": 88}

    def test_repr(self) -> None:
        """Test ToolConfig string representation."""
        config = ToolConfig(
            tool_name="ruff",
            config_file=Path("pyproject.toml"),
            config_section="tool.ruff",
            config_data={},
        )

        repr_str = repr(config)
        assert "ToolConfig" in repr_str
        assert "ruff" in repr_str
        assert "pyproject.toml" in repr_str


class TestConfigDiscovery:
    """Tests for ConfigDiscovery class."""

    def test_init(self, tmp_path: Path) -> None:
        """Test ConfigDiscovery initialization."""
        discovery = ConfigDiscovery(tmp_path)
        assert discovery.project_root == tmp_path
        assert discovery.configs == []

    def test_discover_pyproject_toml(self, sample_project_root: Path) -> None:
        """Test discovering configurations from pyproject.toml."""
        discovery = ConfigDiscovery(sample_project_root)
        discovery._discover_pyproject_toml()  # noqa: SLF001

        tool_names = {c.tool_name for c in discovery.configs}
        assert "ruff" in tool_names
        assert "black" in tool_names
        assert "isort" in tool_names
        assert "mypy" in tool_names

    def test_discover_pyproject_toml_missing(self, tmp_path: Path) -> None:
        """Test discovering when pyproject.toml doesn't exist."""
        discovery = ConfigDiscovery(tmp_path)
        discovery._discover_pyproject_toml()  # noqa: SLF001

        assert discovery.configs == []

    def test_discover_precommit_config(self, sample_project_root: Path) -> None:
        """Test discovering configurations from .pre-commit-config.yaml."""
        discovery = ConfigDiscovery(sample_project_root)
        discovery._discover_precommit_config()  # noqa: SLF001

        # Should find hooks
        assert len(discovery.configs) > 0
        hook_ids = [c.tool_name for c in discovery.configs]
        assert any("black" in h for h in hook_ids)

    def test_discover_precommit_config_missing(self, tmp_path: Path) -> None:
        """Test discovering when .pre-commit-config.yaml doesn't exist."""
        discovery = ConfigDiscovery(tmp_path)
        discovery._discover_precommit_config()  # noqa: SLF001

        assert discovery.configs == []

    def test_discover_all(self, sample_project_root: Path) -> None:
        """Test discovering all configurations."""
        discovery = ConfigDiscovery(sample_project_root)
        configs = discovery.discover_all()

        assert len(configs) > 0
        assert any(c.tool_name == "ruff" for c in configs)
        assert any(c.tool_name == "black" for c in configs)

    def test_discover_other_configs(self, tmp_path: Path) -> None:
        """Test discovering standalone config files."""
        # Create .ruff.toml
        (tmp_path / ".ruff.toml").write_text("[lint]\nselect = ['E', 'F']\n")

        discovery = ConfigDiscovery(tmp_path)
        discovery._discover_other_configs()  # noqa: SLF001

        ruff_configs = [c for c in discovery.configs if c.tool_name == "ruff"]
        assert len(ruff_configs) == 1

    def test_discover_all_error_handling(self, tmp_path: Path) -> None:
        """Test error handling in discover_all."""
        # Create invalid TOML
        (tmp_path / "pyproject.toml").write_text("invalid toml content [[[")

        discovery = ConfigDiscovery(tmp_path)

        # Should not raise, just print warnings
        configs = discovery.discover_all()
        assert isinstance(configs, list)


class TestClaudeAnalyzer:
    """Tests for ClaudeAnalyzer class."""

    def test_init(self) -> None:
        """Test ClaudeAnalyzer initialization."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)  # pragma: allowlist secret
        assert analyzer.api_key == "test-key"  # pragma: allowlist secret
        assert analyzer.dry_run is True
        assert analyzer.client is None

    def test_init_with_client(self) -> None:
        """Test ClaudeAnalyzer initialization with real client."""
        with patch("audit_tool_configs.Anthropic"):
            analyzer = ClaudeAnalyzer("test-key", dry_run=False)
            assert analyzer.client is not None

    def test_mock_analysis(self, sample_configs: list[ToolConfig]) -> None:
        """Test mock analysis in dry-run mode."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        result = analyzer._mock_analysis(sample_configs)  # noqa: SLF001

        assert isinstance(result, AuditResult)
        assert result.discovered_configs == sample_configs
        assert len(result.conflicts) > 0
        assert result.model_used == "mock"

    def test_analyze_conflicts_dry_run(self, sample_configs: list[ToolConfig]) -> None:
        """Test analyze_conflicts in dry-run mode."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        result = analyzer.analyze_conflicts(sample_configs)

        assert isinstance(result, AuditResult)
        assert len(result.discovered_configs) == len(sample_configs)

    @patch("audit_tool_configs.Anthropic")
    def test_analyze_conflicts_real(
        self, mock_anthropic: Mock, sample_configs: list[ToolConfig]
    ) -> None:
        """Test analyze_conflicts with mocked API."""
        # Mock API response with proper TextBlock
        text_content = json.dumps(
            {
                "conflicts": [
                    {
                        "severity": "HIGH",
                        "tools": ["ruff", "black"],
                        "description": "Test conflict",
                        "explanation": "Test explanation",
                        "suggestion": "Test suggestion",
                    }
                ]
            }
        )
        mock_text_block = TextBlock(type="text", text=text_content)

        mock_response = Mock()
        mock_response.content = [mock_text_block]
        mock_response.usage = Mock(input_tokens=100, output_tokens=200)
        mock_response.model = "claude-sonnet-4-5-20250929"

        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        analyzer = ClaudeAnalyzer("test-key", dry_run=False)
        result = analyzer.analyze_conflicts(sample_configs)

        assert len(result.conflicts) == 1
        assert result.conflicts[0].severity == "HIGH"
        assert result.token_usage["input_tokens"] == 100
        assert result.token_usage["output_tokens"] == 200

    def test_build_analysis_prompt(self, sample_configs: list[ToolConfig]) -> None:
        """Test building analysis prompt."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        prompt = analyzer._build_analysis_prompt(sample_configs)  # noqa: SLF001

        assert "ruff" in prompt.lower()
        assert "black" in prompt.lower()
        assert "conflicts" in prompt.lower()
        assert "json" in prompt.lower()

    def test_format_configs_for_prompt(self, sample_configs: list[ToolConfig]) -> None:
        """Test formatting configs for prompt."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        formatted = analyzer._format_configs_for_prompt(sample_configs)  # noqa: SLF001

        assert "ruff" in formatted
        assert "black" in formatted
        assert "line-length" in formatted or "line_length" in formatted

    def test_format_config_data(self) -> None:
        """Test formatting config data."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        data = {"key1": "value1", "key2": {"nested": "value2"}}

        formatted = analyzer._format_config_data(data)  # noqa: SLF001

        assert "key1" in formatted
        assert "value1" in formatted
        assert "nested" in formatted

    def test_parse_conflicts_valid_json(self, sample_configs: list[ToolConfig]) -> None:
        """Test parsing conflicts from valid JSON response."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)

        response_text = json.dumps(
            {
                "conflicts": [
                    {
                        "severity": "HIGH",
                        "tools": ["ruff", "black"],
                        "description": "Line length mismatch",
                        "explanation": "Different settings",
                        "suggestion": "Use same value",
                        "code_example": "line-length = 88",
                    }
                ]
            }
        )

        conflicts = analyzer._parse_conflicts(  # noqa: SLF001
            response_text, sample_configs
        )

        assert len(conflicts) == 1
        assert conflicts[0].severity == "HIGH"
        assert conflicts[0].tools == ["ruff", "black"]
        assert conflicts[0].code_example == "line-length = 88"

    def test_parse_conflicts_markdown_wrapped(
        self, sample_configs: list[ToolConfig]
    ) -> None:
        """Test parsing conflicts from markdown-wrapped JSON."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)

        response_text = """
Here is the analysis:

```json
{
  "conflicts": [
    {
      "severity": "MEDIUM",
      "tools": ["isort", "black"],
      "description": "Import sorting conflict",
      "explanation": "Both sort imports",
      "suggestion": "Use isort profile"
    }
  ]
}
```

Hope this helps!
"""

        conflicts = analyzer._parse_conflicts(  # noqa: SLF001
            response_text, sample_configs
        )

        assert len(conflicts) == 1
        assert conflicts[0].severity == "MEDIUM"

    def test_parse_conflicts_invalid_json(
        self, sample_configs: list[ToolConfig]
    ) -> None:
        """Test parsing conflicts from invalid JSON."""
        analyzer = ClaudeAnalyzer("test-key", dry_run=True)
        response_text = "Not valid JSON at all"

        conflicts = analyzer._parse_conflicts(  # noqa: SLF001
            response_text, sample_configs
        )

        assert conflicts == []

    @patch("audit_tool_configs.Anthropic")
    def test_analyze_conflicts_api_error(
        self, mock_anthropic: Mock, sample_configs: list[ToolConfig]
    ) -> None:
        """Test analyze_conflicts with API error."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API error")
        mock_anthropic.return_value = mock_client

        analyzer = ClaudeAnalyzer("test-key", dry_run=False)

        with pytest.raises(AnalysisError):
            analyzer.analyze_conflicts(sample_configs)


class TestConflictReport:
    """Tests for ConflictReport dataclass."""

    def test_init(self, sample_configs: list[ToolConfig]) -> None:
        """Test ConflictReport initialization."""
        report = ConflictReport(
            severity="HIGH",
            tools=["ruff", "black"],
            description="Test conflict",
            explanation="Test explanation",
            suggestion="Test suggestion",
            affected_configs=sample_configs[:2],
            code_example="test code",
        )

        assert report.severity == "HIGH"
        assert report.tools == ["ruff", "black"]
        assert len(report.affected_configs) == 2
        assert report.code_example == "test code"


class TestAuditResult:
    """Tests for AuditResult dataclass."""

    def test_init_defaults(self) -> None:
        """Test AuditResult with default values."""
        result = AuditResult()

        assert result.discovered_configs == []
        assert result.conflicts == []
        assert result.bypass_rules == {}
        assert result.token_usage == {}
        assert result.model_used == ""

    def test_init_with_data(self, sample_configs: list[ToolConfig]) -> None:
        """Test AuditResult with data."""
        conflicts = [
            ConflictReport(
                severity="HIGH",
                tools=["ruff", "black"],
                description="Test",
                explanation="Test",
                suggestion="Test",
                affected_configs=[],
            )
        ]

        result = AuditResult(
            discovered_configs=sample_configs,
            conflicts=conflicts,
            token_usage={"input_tokens": 100, "output_tokens": 200},
            model_used="test-model",
        )

        assert len(result.discovered_configs) == len(sample_configs)
        assert len(result.conflicts) == 1
        assert result.token_usage["input_tokens"] == 100
        assert result.model_used == "test-model"


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_init(self, tmp_path: Path) -> None:
        """Test ReportGenerator initialization."""
        output_path = tmp_path / "report.md"
        generator = ReportGenerator(output_path)

        assert generator.output_path == output_path

    def test_generate(self, tmp_path: Path, sample_configs: list[ToolConfig]) -> None:
        """Test generating report."""
        output_path = tmp_path / "report.md"
        generator = ReportGenerator(output_path)

        result = AuditResult(
            discovered_configs=sample_configs,
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Test conflict",
                    explanation="Test explanation",
                    suggestion="Test suggestion",
                    affected_configs=sample_configs[:2],
                )
            ],
            token_usage={"input_tokens": 100, "output_tokens": 200},
            model_used="test-model",
        )

        generator.generate(result)

        assert output_path.exists()
        content = output_path.read_text()
        assert "Tool Configuration Audit Report" in content
        assert "Test conflict" in content

    def test_generate_header(self, tmp_path: Path) -> None:
        """Test generating report header."""
        generator = ReportGenerator(tmp_path / "report.md")
        result = AuditResult(model_used="test-model")

        header = generator._generate_header(result)  # noqa: SLF001

        assert "Tool Configuration Audit Report" in header
        assert "test-model" in header

    def test_generate_summary(
        self, tmp_path: Path, sample_configs: list[ToolConfig]
    ) -> None:
        """Test generating summary section."""
        generator = ReportGenerator(tmp_path / "report.md")
        result = AuditResult(
            discovered_configs=sample_configs,
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Test",
                    explanation="Test",
                    suggestion="Test",
                    affected_configs=[],
                ),
                ConflictReport(
                    severity="MEDIUM",
                    tools=["isort", "black"],
                    description="Test",
                    explanation="Test",
                    suggestion="Test",
                    affected_configs=[],
                ),
            ],
            token_usage={"input_tokens": 100, "output_tokens": 200},
        )

        summary = generator._generate_summary(result)  # noqa: SLF001

        assert "Summary" in summary
        assert "3" in summary  # 3 configs
        assert "2" in summary  # 2 conflicts
        assert "300" in summary  # total tokens

    def test_generate_discovered_configs(
        self, tmp_path: Path, sample_configs: list[ToolConfig]
    ) -> None:
        """Test generating discovered configs section."""
        generator = ReportGenerator(tmp_path / "report.md")
        result = AuditResult(discovered_configs=sample_configs)

        section = generator._generate_discovered_configs(result)  # noqa: SLF001

        assert "Discovered Configurations" in section
        assert "ruff" in section
        assert "black" in section

    def test_generate_conflicts(
        self, tmp_path: Path, sample_configs: list[ToolConfig]
    ) -> None:
        """Test generating conflicts section."""
        generator = ReportGenerator(tmp_path / "report.md")
        result = AuditResult(
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Test conflict",
                    explanation="This is a test",
                    suggestion="Fix it this way",
                    affected_configs=sample_configs[:2],
                    code_example="line-length = 88",
                )
            ]
        )

        section = generator._generate_conflicts(result)  # noqa: SLF001

        assert "Conflicts" in section
        assert "HIGH" in section
        assert "Test conflict" in section
        assert "line-length = 88" in section

    def test_generate_conflicts_empty(self, tmp_path: Path) -> None:
        """Test generating conflicts section with no conflicts."""
        generator = ReportGenerator(tmp_path / "report.md")
        result = AuditResult(conflicts=[])

        section = generator._generate_conflicts(result)  # noqa: SLF001

        assert "Conflicts" in section
        assert "No conflicts detected" in section

    def test_generate_footer(self, tmp_path: Path) -> None:
        """Test generating report footer."""
        generator = ReportGenerator(tmp_path / "report.md")

        footer = generator._generate_footer()  # noqa: SLF001

        assert "Next Steps" in footer
        assert "pre-commit" in footer


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting API key from environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
        api_key = get_api_key()

        assert api_key == "test-key-123"  # pragma: allowlist secret

    def test_get_api_key_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting API key when not set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(AuditorError):
            get_api_key()

    def test_parse_args_defaults(self) -> None:
        """Test parsing args with defaults."""
        with patch("sys.argv", ["audit_tool_configs.py"]):
            args = parse_args()

            assert args.project_root == Path.cwd()
            assert args.output == Path("tool-config-audit-report.md")
            assert args.dry_run is False
            assert args.apply_fixes is False
            assert args.verbose is False

    def test_parse_args_custom(self, tmp_path: Path) -> None:
        """Test parsing args with custom values."""
        test_root = tmp_path / "test"
        with patch(
            "sys.argv",
            [
                "audit_tool_configs.py",
                "--project-root",
                str(test_root),
                "--output",
                "custom.md",
                "--dry-run",
                "--verbose",
            ],
        ):
            args = parse_args()

            assert args.project_root == test_root
            assert args.output == Path("custom.md")
            assert args.dry_run is True
            assert args.verbose is True


class TestMainFunction:
    """Tests for main function."""

    @patch("audit_tool_configs.ReportGenerator")
    @patch("audit_tool_configs.ClaudeAnalyzer")
    @patch("audit_tool_configs.ConfigDiscovery")
    def test_main_dry_run(
        self,
        mock_discovery: Mock,
        mock_analyzer: Mock,
        mock_report_gen: Mock,
    ) -> None:
        """Test main function in dry-run mode."""
        # Setup mocks
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_all.return_value = []
        mock_discovery.return_value = mock_discovery_instance

        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze_conflicts.return_value = AuditResult()
        mock_analyzer.return_value = mock_analyzer_instance

        mock_report_gen_instance = Mock()
        mock_report_gen.return_value = mock_report_gen_instance

        # Run main with patched argv
        with patch("sys.argv", ["audit_tool_configs.py", "--dry-run"]):
            exit_code = main()

        assert exit_code == 0
        mock_discovery_instance.discover_all.assert_called_once()
        mock_analyzer_instance.analyze_conflicts.assert_called_once()
        mock_report_gen_instance.generate.assert_called_once()

    @patch("audit_tool_configs.get_api_key")
    @patch("sys.argv", ["audit_tool_configs.py"])
    def test_main_missing_api_key(self, mock_get_api_key: Mock) -> None:
        """Test main function with missing API key."""
        mock_get_api_key.side_effect = AuditorError("API key not found")

        exit_code = main()

        assert exit_code == 1

    @patch("sys.argv", ["audit_tool_configs.py", "--dry-run"])
    @patch("audit_tool_configs.ConfigDiscovery")
    def test_main_keyboard_interrupt(self, mock_discovery: Mock) -> None:
        """Test main function with keyboard interrupt."""
        mock_discovery.side_effect = KeyboardInterrupt()

        exit_code = main()

        assert exit_code == 130


class TestExceptions:
    """Tests for custom exceptions."""

    def test_auditor_error(self) -> None:
        """Test AuditorError exception."""
        error = AuditorError("Test error")
        assert str(error) == "Test error"

    def test_config_discovery_error(self) -> None:
        """Test ConfigDiscoveryError exception."""
        error = ConfigDiscoveryError("Discovery failed")
        assert str(error) == "Discovery failed"

    def test_analysis_error(self) -> None:
        """Test AnalysisError exception."""
        error = AnalysisError("Analysis failed")
        assert str(error) == "Analysis failed"
