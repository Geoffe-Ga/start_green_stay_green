"""Subagent profile generator for target repositories.

This module generates subagent profiles by loading reference agents,
tuning them for the target project context, and preserving YAML frontmatter structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.ai.tuner import ContentTuner
from start_green_stay_green.generators.base import BaseGenerator

if TYPE_CHECKING:
    from start_green_stay_green.ai.orchestrator import AIOrchestrator


# Default reference directory (can be overridden)
REFERENCE_AGENTS_DIR = Path(__file__).parent.parent.parent / ".claude" / "agents"

# Source context for tuning: describes the origin of reference agents
# Reference agents were designed for a Mojo ML research project with
# multi-level agent hierarchies and paper implementation workflows
SOURCE_AGENT_CONTEXT = (
    "Mojo ML research project (ml-odyssey) with multi-level "
    "agent hierarchy, paper implementations, and research workflows"
)

# Mapping from required agent names to source agent files
REQUIRED_AGENTS = {
    "chief-architect": "chief-architect.md",
    "quality-reviewer": "code-review-orchestrator.md",
    "test-generator": "test-specialist.md",
    "security-auditor": "security-specialist.md",
    "dependency-checker": "dependency-review-specialist.md",
    "documentation": "documentation-specialist.md",
    "refactorer": "implementation-specialist.md",
    "performance": "performance-specialist.md",
}


@dataclass(frozen=True)
class SubagentGenerationResult:
    """Result of generating a single subagent.

    Attributes:
        agent_name: Name of the generated agent.
        content: Full agent content including YAML frontmatter.
        tuned: Whether content was tuned via ContentTuner.
        changes: List of changes made during tuning.
    """

    agent_name: str
    content: str
    tuned: bool
    changes: list[str]


class SubagentsGenerator(BaseGenerator):
    """Generator for subagent profiles.

    Loads subagent profiles from reference directory, tunes them for
    target project context using ContentTuner, and preserves YAML
    frontmatter structure.

    Example:
        >>> orchestrator = AIOrchestrator(api_key="...")
        >>> generator = SubagentsGenerator(orchestrator)
        >>> results = await generator.generate_all_agents(
        ...     "Python web application with FastAPI"
        ... )
        >>> for name, result in results.items():
        ...     print(f"{name}: {len(result.changes)} changes")
    """

    def __init__(
        self,
        orchestrator: AIOrchestrator,
        *,
        reference_dir: Path | None = None,
        dry_run: bool = False,
    ) -> None:
        """Initialize SubagentsGenerator.

        Args:
            orchestrator: AI orchestrator for content generation.
            reference_dir: Directory containing reference agents.
                Defaults to .claude/agents/ in project root.
            dry_run: If True, skip actual tuning (for testing).
        """
        self.orchestrator = orchestrator
        self.tuner = ContentTuner(orchestrator, dry_run=dry_run)
        self.reference_dir = reference_dir or REFERENCE_AGENTS_DIR
        self.dry_run = dry_run
        self._validate_reference_dir()

    def _check_directory_exists(self) -> None:
        """Check that reference directory exists and is a directory.

        Separated from _check_required_agents to provide clear error messages.
        Directory existence is validated before checking individual files to
        fail fast with the most helpful error message.
        """
        if not self.reference_dir.exists():
            msg = f"Reference directory not found: {self.reference_dir}"
            raise FileNotFoundError(msg)

        if not self.reference_dir.is_dir():
            msg = f"Reference path is not a directory: {self.reference_dir}"
            raise NotADirectoryError(msg)

    def _check_required_agents(self) -> None:
        """Check that all required agent source files exist.

        Separated from _check_directory_exists to provide detailed error
        messages listing all missing files at once (rather than failing on
        first missing file).
        """
        missing_agents = []
        for agent_name, source_file in REQUIRED_AGENTS.items():
            agent_path = self.reference_dir / source_file
            if not agent_path.exists():
                missing_agents.append(f"{agent_name} (source: {source_file})")

        if missing_agents:
            msg = f"Missing required agent files: {', '.join(missing_agents)}"
            raise FileNotFoundError(msg)

    def _validate_reference_dir(self) -> None:
        """Validate that reference directory exists with required agents.

        Runs two-stage validation:
        1. Directory exists and is a directory (fail fast)
        2. All required agent files exist (comprehensive check)
        """
        self._check_directory_exists()
        self._check_required_agents()

    def _load_agent_content(self, agent_name: str) -> str:
        """Load agent content from reference directory.

        Args:
            agent_name: Name of the agent to load.

        Returns:
            Agent content including YAML frontmatter.

        Raises:
            FileNotFoundError: If agent file not found.
        """
        source_file = REQUIRED_AGENTS[agent_name]
        agent_path = self.reference_dir / source_file
        return agent_path.read_text()

    def _parse_frontmatter(self, content: str) -> tuple[str, str]:
        """Parse YAML frontmatter from agent content.

        Args:
            content: Agent content with frontmatter.

        Returns:
            Tuple of (frontmatter, body) where frontmatter includes
            the --- delimiters.

        Raises:
            ValueError: If frontmatter not found or malformed.
        """
        # Match YAML frontmatter pattern:
        # ^(---\n  - Start with --- and newline (captured group 1)
        # .*?      - Match any content (non-greedy)
        # \n---)   - End with newline and --- (end group 1)
        # \n       - Newline after frontmatter
        # (.*)$    - Capture remaining content as body (group 2)
        # re.DOTALL allows . to match newlines
        pattern = r"^(---\n.*?\n---)\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            msg = "Agent content missing YAML frontmatter"
            raise ValueError(msg)

        return match.group(1), match.group(2)

    async def _tune_agent_body(
        self,
        agent_name: str,
        body: str,
        target_context: str,
    ) -> SubagentGenerationResult:
        """Tune agent body content for target context.

        Args:
            agent_name: Name of the agent being tuned.
            body: Agent body content (without frontmatter).
            target_context: Description of target project context.

        Returns:
            Generation result with tuned content.
        """
        # Tune the body content using SOURCE_AGENT_CONTEXT
        tuning_result = await self.tuner.tune(
            source_content=body,
            source_context=SOURCE_AGENT_CONTEXT,
            target_context=target_context,
            preserve_sections=[
                "## Identity",
                "## Scope",
                "## Workflow",
                "## Skills",
                "## Constraints",
            ],
        )

        return SubagentGenerationResult(
            agent_name=agent_name,
            content=tuning_result.content,
            tuned=not self.dry_run,
            changes=tuning_result.changes,
        )

    async def generate_agent(
        self,
        agent_name: str,
        target_context: str,
    ) -> SubagentGenerationResult:
        """Generate a single subagent for target project.

        Args:
            agent_name: Name of the agent to generate.
            target_context: Description of target project context.

        Returns:
            Generation result with full agent content including frontmatter.

        Raises:
            ValueError: If agent_name not in REQUIRED_AGENTS.
            FileNotFoundError: If agent source file not found.
        """
        if agent_name not in REQUIRED_AGENTS:
            valid_names = ", ".join(REQUIRED_AGENTS.keys())
            msg = f"Invalid agent name: {agent_name}. " f"Must be one of: {valid_names}"
            raise ValueError(msg)

        # Load agent content
        content = self._load_agent_content(agent_name)

        # Parse frontmatter and body
        frontmatter, body = self._parse_frontmatter(content)

        # Tune the body content
        result = await self._tune_agent_body(agent_name, body, target_context)

        # Reconstruct full content with frontmatter
        full_content = f"{frontmatter}\n{result.content}"

        return SubagentGenerationResult(
            agent_name=agent_name,
            content=full_content,
            tuned=result.tuned,
            changes=result.changes,
        )

    async def generate_all_agents(
        self,
        target_context: str,
    ) -> dict[str, SubagentGenerationResult]:
        """Generate all required subagents for target project.

        Args:
            target_context: Description of target project context.

        Returns:
            Dictionary mapping agent names to generation results.
        """
        results = {}
        for agent_name in REQUIRED_AGENTS:
            result = await self.generate_agent(agent_name, target_context)
            results[agent_name] = result
        return results

    def generate(self) -> dict[str, Any]:
        """Generate subagents synchronously (not supported).

        This method is required by BaseGenerator abstract interface but
        SubagentsGenerator requires async operations for ContentTuner integration.

        The synchronous interface cannot support async tuning operations,
        so this method raises NotImplementedError to maintain type safety
        while directing users to the correct async interface.

        Use generate_all_agents() for async batch generation or
        generate_agent() for async single agent generation.

        Raises:
            NotImplementedError: Always. Use generate_all_agents() instead.

        See Also:
            generate_all_agents: Async method for generating all agents.
            generate_agent: Async method for generating a single agent.
        """
        msg = (
            "SubagentsGenerator requires async operations. "
            "Use generate_all_agents() or generate_agent() instead."
        )
        raise NotImplementedError(msg)
