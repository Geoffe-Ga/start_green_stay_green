#!/usr/bin/env python3
"""Tool configuration auditor with Claude API integration.

Detects and resolves conflicts between development tool configurations.

This script:
1. Discovers all tool configurations (pyproject.toml, .pre-commit-config.yaml)
2. Uses Claude API to analyze configurations for conflicts
3. Generates detailed markdown reports with explanations
4. Suggests and applies fixes (with --apply-fixes flag)

Usage:
    python scripts/audit_tool_configs.py [OPTIONS]

Examples:
    # Analyze and generate report
    python scripts/audit_tool_configs.py

    # Dry-run mode (no changes)
    python scripts/audit_tool_configs.py --dry-run

    # Apply fixes automatically
    python scripts/audit_tool_configs.py --apply-fixes

    # Custom output location
    python scripts/audit_tool_configs.py --output audit-report.md

Known conflicts detected:
- Ruff vs Black (line length, formatting rules)
- mutmut vs refurb (mutation detection patterns)
- Ruff vs Bandit (security rule overlap)
- isort vs Black (import formatting)
- Pylint vs Ruff (duplicate linting checks)

Requires:
- anthropic>=0.18.0
- pyyaml>=6.0.0
- toml>=0.10.2
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any
from typing import Final
from typing import cast

try:
    from anthropic import Anthropic
    from anthropic.types import TextBlock
    import toml
    import yaml
except ImportError as e:
    # CLI script legitimately needs to print errors to stderr before logging is set up
    import sys

    sys.stderr.write(f"Error: Missing required dependencies: {e}\n")
    sys.stderr.write("Install with: pip install anthropic pyyaml toml\n")
    sys.exit(1)


# Constants
DEFAULT_OUTPUT: Final[str] = "tool-config-audit-report.md"
MAX_RETRIES: Final[int] = 3
API_MODEL: Final[str] = "claude-sonnet-4-5-20250929"


class AuditorError(Exception):
    """Base exception for auditor errors."""


class ConfigDiscoveryError(AuditorError):
    """Raised when configuration discovery fails."""


class AnalysisError(AuditorError):
    """Raised when Claude API analysis fails."""


@dataclass
class ToolConfig:
    """Represents a discovered tool configuration.

    Attributes:
        tool_name: Name of the tool (e.g., "ruff", "black", "mypy")
        config_file: Path to the configuration file
        config_section: Section within the file (e.g., "tool.ruff")
        config_data: Parsed configuration data
    """

    tool_name: str
    config_file: Path
    config_section: str
    config_data: dict[str, Any]

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ToolConfig(tool={self.tool_name}, "
            f"file={self.config_file.name}, "
            f"section={self.config_section})"
        )


@dataclass
class ConflictReport:
    """Represents a detected configuration conflict.

    Attributes:
        severity: Conflict severity (HIGH, MEDIUM, LOW)
        tools: List of conflicting tool names
        description: Human-readable description of the conflict
        explanation: Detailed explanation of why this is a conflict
        suggestion: Recommended fix or resolution
        affected_configs: List of affected ToolConfig objects
        code_example: Optional code example demonstrating the issue
    """

    severity: str
    tools: list[str]
    description: str
    explanation: str
    suggestion: str
    affected_configs: list[ToolConfig]
    code_example: str | None = None


@dataclass
class AuditResult:
    """Complete audit result.

    Attributes:
        discovered_configs: All discovered tool configurations
        conflicts: Detected conflicts
        bypass_rules: Validation results for bypass rules (noqa, type:ignore)
        token_usage: Token usage from Claude API
        model_used: Claude model identifier
    """

    discovered_configs: list[ToolConfig] = field(default_factory=list)
    conflicts: list[ConflictReport] = field(default_factory=list)
    bypass_rules: dict[str, Any] = field(default_factory=dict)
    token_usage: dict[str, int] = field(default_factory=dict)
    model_used: str = ""


class ConfigDiscovery:
    """Discovers and parses tool configurations."""

    def __init__(self, project_root: Path) -> None:
        """Initialize configuration discovery.

        Args:
            project_root: Root directory of the project to audit
        """
        self.project_root = project_root
        self.configs: list[ToolConfig] = []

    def discover_all(self) -> list[ToolConfig]:
        """Discover all tool configurations in the project.

        Returns:
            List of discovered ToolConfig objects

        Raises:
            ConfigDiscoveryError: If discovery fails
        """
        try:
            self._discover_pyproject_toml()
            self._discover_precommit_config()
            self._discover_other_configs()
        except (OSError, ValueError, KeyError) as e:
            msg = f"Configuration discovery failed: {e}"
            raise ConfigDiscoveryError(msg) from e
        else:
            return self.configs

    def _discover_pyproject_toml(self) -> None:
        """Discover configurations in pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            return

        try:
            with pyproject_path.open("r") as f:
                data = toml.load(f)

            # Handle empty files
            if not data:
                return

            # Extract tool configurations
            if "tool" in data:
                for tool_name, tool_config in data["tool"].items():
                    if isinstance(tool_config, dict):
                        self.configs.append(
                            ToolConfig(
                                tool_name=tool_name,
                                config_file=pyproject_path,
                                config_section=f"tool.{tool_name}",
                                config_data=tool_config,
                            )
                        )
        except (OSError, ValueError, KeyError, toml.TomlDecodeError) as e:
            sys.stderr.write(f"Warning: Failed to parse pyproject.toml: {e}\n")

    def _discover_precommit_config(self) -> None:
        """Discover configurations in .pre-commit-config.yaml."""
        precommit_path = self.project_root / ".pre-commit-config.yaml"
        if not precommit_path.exists():
            return

        try:
            with precommit_path.open("r") as f:
                data = yaml.safe_load(f)

            # Handle empty files (yaml.safe_load returns None)
            if data is None:
                return

            # Extract hook configurations
            if "repos" in data and isinstance(data["repos"], list):
                for repo in data["repos"]:
                    if "hooks" in repo and isinstance(repo["hooks"], list):
                        for hook in repo["hooks"]:
                            hook_id = hook.get("id", "unknown")
                            repo_name = repo.get("repo", "local")
                            section = f"repos.{repo_name}.hooks.{hook_id}"
                            self.configs.append(
                                ToolConfig(
                                    tool_name=f"pre-commit-{hook_id}",
                                    config_file=precommit_path,
                                    config_section=section,
                                    config_data=hook,
                                )
                            )
        except (OSError, ValueError, KeyError, yaml.YAMLError) as e:
            sys.stderr.write(f"Warning: Failed to parse .pre-commit-config.yaml: {e}\n")

    def _discover_other_configs(self) -> None:
        """Discover other configuration files (.ruff.toml, .pylintrc, etc.)."""
        # Add support for standalone config files
        config_files = {
            ".ruff.toml": "ruff",
            ".pylintrc": "pylint",
            ".mypy.ini": "mypy",
            ".bandit": "bandit",
            ".isort.cfg": "isort",
        }

        for filename, tool_name in config_files.items():
            config_path = self.project_root / filename
            if config_path.exists():
                try:
                    # Try to parse based on file type
                    if filename.endswith(".toml"):
                        with config_path.open("r") as f:
                            data = toml.load(f)
                    elif filename.endswith((".ini", "rc")):
                        # For .ini/.rc files, store raw content
                        with config_path.open("r") as f:
                            data = {"raw_content": f.read()}
                    else:
                        continue

                    self.configs.append(
                        ToolConfig(
                            tool_name=tool_name,
                            config_file=config_path,
                            config_section="root",
                            config_data=data,
                        )
                    )
                except (OSError, ValueError, toml.TomlDecodeError) as e:
                    sys.stderr.write(f"Warning: Failed to parse {filename}: {e}\n")


class ClaudeAnalyzer:
    """Analyzes configurations using Claude API."""

    def __init__(
        self, api_key: str, *, dry_run: bool = False
    ) -> None:  # pragma: allowlist secret
        """Initialize Claude analyzer.

        Args:
            api_key: Anthropic API key
            dry_run: If True, skip actual API calls (keyword-only)
        """
        self.api_key = api_key  # pragma: allowlist secret
        self.dry_run = dry_run
        self.client = (
            Anthropic(api_key=api_key) if not dry_run else None
        )  # pragma: allowlist secret

    @staticmethod
    def _validate_response_block(first_block: object) -> None:
        """Validate that response block is TextBlock.

        Args:
            first_block: First block from API response

        Raises:
            AnalysisError: If block is not TextBlock
        """
        if not isinstance(first_block, TextBlock):
            msg = "Expected TextBlock in response"
            raise AnalysisError(msg)

    def analyze_conflicts(self, configs: list[ToolConfig]) -> AuditResult:
        """Analyze configurations for conflicts using Claude API.

        Args:
            configs: List of discovered tool configurations

        Returns:
            AuditResult with detected conflicts

        Raises:
            AnalysisError: If API call fails
        """
        if self.dry_run:
            return self._mock_analysis(configs)

        prompt = self._build_analysis_prompt(configs)

        try:
            # Type narrowing: dry_run check above ensures client is not None here
            response = self.client.messages.create(  # type: ignore[union-attr]
                model=API_MODEL,
                max_tokens=8192,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract content
            first_block = response.content[0]
            self._validate_response_block(first_block)
            # After validation, we know it's a TextBlock
            text_block = cast("TextBlock", first_block)

        except Exception as e:
            msg = f"Claude API analysis failed: {e}"
            raise AnalysisError(msg) from e
        else:
            result = AuditResult(
                discovered_configs=configs,
                token_usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                model_used=response.model,
            )

            # Parse conflicts from response
            result.conflicts = self._parse_conflicts(text_block.text, configs)
            return result

    def _build_analysis_prompt(self, configs: list[ToolConfig]) -> str:
        """Build prompt for Claude API.

        Args:
            configs: List of tool configurations

        Returns:
            Formatted prompt string
        """
        config_summary = self._format_configs_for_prompt(configs)

        return f"""You are a Python development tool configuration expert.
Analyze the following tool configurations and identify conflicts, overlaps,
and inconsistencies.

**Project Tool Configurations:**

{config_summary}

**Known Conflict Categories:**
1. **Formatting conflicts**: Ruff vs Black, isort vs Black
2. **Linting overlaps**: Ruff vs Pylint, Ruff vs Bandit
3. **Code quality**: mutmut vs refurb patterns
4. **Type checking**: MyPy strict mode with other tools

**Analysis Requirements:**

For each conflict found, provide:
1. **Severity**: HIGH, MEDIUM, or LOW
2. **Tools**: Which tools are in conflict
3. **Description**: One-line summary
4. **Explanation**: Detailed explanation of the conflict
5. **Suggestion**: Specific fix with configuration examples
6. **Code Example**: Optional example demonstrating the issue

**Output Format:**

```json
{{
  "conflicts": [
    {{
      "severity": "HIGH",
      "tools": ["tool1", "tool2"],
      "description": "Brief description",
      "explanation": "Detailed explanation of why this conflicts",
      "suggestion": "Specific fix recommendation with config examples",
      "code_example": "Optional code demonstrating the issue"
    }}
  ]
}}
```

Analyze thoroughly and identify all conflicts, even subtle ones.
"""

    def _format_configs_for_prompt(self, configs: list[ToolConfig]) -> str:
        """Format configurations for inclusion in prompt.

        Args:
            configs: List of tool configurations

        Returns:
            Formatted string representation
        """
        lines = []
        for config in configs:
            lines.extend(
                [
                    f"\n### {config.tool_name}",
                    f"**File**: {config.config_file.name}",
                    f"**Section**: {config.config_section}",
                    "**Configuration**:",
                    "```toml",
                ]
            )
            # Simplify config data for prompt
            lines.extend(
                [
                    self._format_config_data(config.config_data),
                    "```",
                ]
            )

        return "\n".join(lines)

    def _format_config_data(self, data: dict[str, Any], indent: int = 0) -> str:
        """Format configuration data as TOML-like string.

        Args:
            data: Configuration data dictionary
            indent: Current indentation level

        Returns:
            Formatted string
        """
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.extend(
                    [
                        f"{prefix}{key} = {{",
                        self._format_config_data(value, indent + 1),
                        f"{prefix}}}",
                    ]
                )
            elif isinstance(value, list):
                lines.append(f"{prefix}{key} = {value}")
            else:
                lines.append(f"{prefix}{key} = {value!r}")

        return "\n".join(lines)

    def _parse_conflicts(
        self, response_text: str, configs: list[ToolConfig]
    ) -> list[ConflictReport]:
        """Parse conflicts from Claude API response.

        Args:
            response_text: Raw response text from Claude
            configs: List of tool configurations for reference

        Returns:
            List of ConflictReport objects
        """
        conflicts: list[ConflictReport] = []

        try:
            # Extract JSON from response (may be wrapped in markdown code blocks)
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                sys.stderr.write("Warning: No JSON found in response\n")
                return conflicts

            json_text = response_text[json_start:json_end]
            data = json.loads(json_text)

            if "conflicts" in data:
                for conflict_data in data["conflicts"]:
                    # Find affected configs
                    tool_names = conflict_data.get("tools", [])
                    affected = [c for c in configs if c.tool_name in tool_names]

                    conflicts.append(
                        ConflictReport(
                            severity=conflict_data.get("severity", "MEDIUM"),
                            tools=tool_names,
                            description=conflict_data.get("description", ""),
                            explanation=conflict_data.get("explanation", ""),
                            suggestion=conflict_data.get("suggestion", ""),
                            affected_configs=affected,
                            code_example=conflict_data.get("code_example"),
                        )
                    )

        except json.JSONDecodeError as e:
            sys.stderr.write(f"Warning: Failed to parse JSON response: {e}\n")
        except (KeyError, TypeError) as e:
            sys.stderr.write(f"Warning: Failed to parse conflicts: {e}\n")

        return conflicts

    def _mock_analysis(self, configs: list[ToolConfig]) -> AuditResult:
        """Mock analysis for dry-run mode.

        Args:
            configs: List of tool configurations

        Returns:
            Mock AuditResult
        """
        return AuditResult(
            discovered_configs=configs,
            conflicts=[
                ConflictReport(
                    severity="HIGH",
                    tools=["ruff", "black"],
                    description="Line length mismatch between Ruff and Black",
                    explanation=(
                        "Ruff and Black both format code but may have "
                        "different line length settings."
                    ),
                    suggestion=(
                        "Ensure both tools use the same line-length setting "
                        "(88 characters)."
                    ),
                    affected_configs=[
                        c for c in configs if c.tool_name in ("ruff", "black")
                    ],
                    code_example=(
                        "# Line length setting\n"
                        "[tool.ruff]\n"
                        "line-length = 88\n\n"
                        "[tool.black]\n"
                        "line-length = 88"
                    ),
                )
            ],
            token_usage={"input_tokens": 0, "output_tokens": 0},
            model_used="mock",
        )


class ReportGenerator:
    """Generates markdown audit reports."""

    def __init__(self, output_path: Path) -> None:
        """Initialize report generator.

        Args:
            output_path: Path to write the report
        """
        self.output_path = output_path

    def generate(self, result: AuditResult) -> None:
        """Generate markdown report from audit result.

        Args:
            result: AuditResult to generate report from
        """
        sections = [
            self._generate_header(result),
            self._generate_summary(result),
            self._generate_discovered_configs(result),
            self._generate_conflicts(result),
            self._generate_footer(),
        ]

        report_content = "\n\n".join(sections)

        with self.output_path.open("w") as f:
            f.write(report_content)

        sys.stdout.write(f"\nAudit report written to: {self.output_path}\n")

    def _generate_header(self, result: AuditResult) -> str:
        """Generate report header."""
        return """# Tool Configuration Audit Report

**Generated by**: Start Green Stay Green Tool Auditor
**Timestamp**: {timestamp}
**Model**: {model}

---
""".format(
            timestamp=self._get_timestamp(),
            model=result.model_used or "N/A",
        )

    def _generate_summary(self, result: AuditResult) -> str:
        """Generate summary section."""
        high = sum(1 for c in result.conflicts if c.severity == "HIGH")
        medium = sum(1 for c in result.conflicts if c.severity == "MEDIUM")
        low = sum(1 for c in result.conflicts if c.severity == "LOW")

        input_tokens = result.token_usage.get("input_tokens", 0)
        output_tokens = result.token_usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens

        return f"""## Summary

- **Total Configurations Discovered**: {len(result.discovered_configs)}
- **Total Conflicts Detected**: {len(result.conflicts)}
  - HIGH Severity: {high}
  - MEDIUM Severity: {medium}
  - LOW Severity: {low}
- **Token Usage**: {input_tokens} input + {output_tokens} output = {total_tokens} total
"""

    def _generate_discovered_configs(self, result: AuditResult) -> str:
        """Generate discovered configurations section."""
        lines = ["## Discovered Configurations\n"]

        # Group by file
        by_file: dict[Path, list[ToolConfig]] = {}
        for config in result.discovered_configs:
            if config.config_file not in by_file:
                by_file[config.config_file] = []
            by_file[config.config_file].append(config)

        for file_path, configs in sorted(by_file.items()):
            lines.append(f"### {file_path.name}\n")
            lines.extend(
                f"- **{config.tool_name}** (`{config.config_section}`)"
                for config in configs
            )

        return "\n".join(lines)

    def _generate_conflicts(self, result: AuditResult) -> str:
        """Generate conflicts section."""
        if not result.conflicts:
            return "## Conflicts\n\nNo conflicts detected. Configuration looks good!"

        lines = ["## Conflicts\n"]

        # Sort by severity
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_conflicts = sorted(
            result.conflicts,
            key=lambda c: (severity_order.get(c.severity, 3), c.description),
        )

        for i, conflict in enumerate(sorted_conflicts, 1):
            lines.extend(
                [
                    f"### Conflict {i}: {conflict.description}\n",
                    f"**Severity**: {conflict.severity}",
                    f"**Tools**: {', '.join(conflict.tools)}",
                    f"\n**Explanation**:\n{conflict.explanation}",
                    f"\n**Suggestion**:\n{conflict.suggestion}",
                ]
            )

            if conflict.code_example:
                lines.append(f"\n**Example**:\n```\n{conflict.code_example}\n```")

            lines.append("\n---\n")

        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """## Next Steps

1. Review HIGH severity conflicts first
2. Apply suggested fixes manually or with `--apply-fixes`
3. Run `pre-commit run --all-files` to verify fixes
4. Re-run audit to confirm resolution

For more information, see the
[Stay Green Workflow](../reference/workflows/stay-green.md).
"""

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp string."""
        return datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")


def get_api_key() -> str:  # pragma: allowlist secret
    """Get Anthropic API key from environment.

    Returns:
        API key string

    Raises:
        AuditorError: If API key not found
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")  # pragma: allowlist secret
    if not api_key:
        msg = (  # pragma: allowlist secret
            "ANTHROPIC_API_KEY environment variable not set. "
            "Set it with: "  # pragma: allowlist secret
            "export ANTHROPIC_API_KEY='your-key-here'"  # pragma: allowlist secret
        )  # pragma: allowlist secret
        raise AuditorError(msg)
    return api_key


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Audit tool configurations for conflicts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and generate report
  %(prog)s

  # Dry-run mode
  %(prog)s --dry-run

  # Apply fixes automatically
  %(prog)s --apply-fixes

  # Custom output location
  %(prog)s --output custom-report.md
""",
    )

    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"Output report path (default: {DEFAULT_OUTPUT})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (skip API calls, use mock data)",
    )

    parser.add_argument(
        "--apply-fixes",
        action="store_true",
        help="Apply fixes automatically (not yet implemented)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()

    try:
        # Get API key
        if not args.dry_run:
            api_key = get_api_key()
        else:
            api_key = "mock-key"  # pragma: allowlist secret
            sys.stdout.write("Running in dry-run mode (no API calls)\n")

        # Discover configurations
        sys.stdout.write(f"Discovering configurations in: {args.project_root}\n")
        discovery = ConfigDiscovery(args.project_root)
        configs = discovery.discover_all()
        sys.stdout.write(f"Discovered {len(configs)} tool configurations\n")

        if args.verbose:
            for config in configs:
                sys.stdout.write(f"  - {config}\n")

        # Analyze with Claude
        sys.stdout.write("Analyzing configurations with Claude API...\n")
        analyzer = ClaudeAnalyzer(api_key, dry_run=args.dry_run)
        result = analyzer.analyze_conflicts(configs)

        sys.stdout.write(
            f"Analysis complete: {len(result.conflicts)} conflicts detected\n"
        )

        # Generate report
        sys.stdout.write(f"Generating report: {args.output}\n")
        generator = ReportGenerator(args.output)
        generator.generate(result)

        # Apply fixes if requested
        if args.apply_fixes:
            sys.stdout.write("\nNote: --apply-fixes not yet implemented\n")
            sys.stdout.write(
                "Please apply fixes manually based on report suggestions\n"
            )

    except AuditorError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\nAborted by user\n")
        return 130
    except (OSError, ValueError) as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        if args.verbose:
            traceback.print_exc()
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
