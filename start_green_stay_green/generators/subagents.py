"""Subagent profile generator for target repositories.

This module generates subagent profiles by loading reference agents,
tuning them for the target project context, and preserving YAML frontmatter structure.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.ai.tuner import ContentTuner
from start_green_stay_green.generators.base import BaseGenerator

# Bounded concurrency keeps us under Anthropic's per-tier rate limits even
# when the user has eight subagents (or more, post-Phase 3) to tune.
DEFAULT_MAX_CONCURRENCY = 8

if TYPE_CHECKING:
    from start_green_stay_green.ai.batch import ToolUseBatchRequest
    from start_green_stay_green.ai.orchestrator import AIOrchestrator
    from start_green_stay_green.ai.types import ToolUseResult


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


@dataclass(frozen=True)
class SubagentBatchEntry:
    """One per-agent slot in a Phase 5b batch submission.

    Lets the submit and resume halves of ``green enhance --batch``
    travel through the orchestrator with everything they need: the
    Anthropic-side request payload, the agent name (so the result
    file knows where to land), and the original YAML frontmatter
    (so :meth:`SubagentsGenerator.apply_batch_result` can rebuild
    the full agent file once results arrive).

    Attributes:
        agent_name: Logical name (e.g. ``"chief-architect"``).
        custom_id: Anthropic ``custom_id`` for this request — by
            convention ``"subagent:<agent_name>"``. Echoes back in
            :attr:`BatchResultsBundle.successes` keyed by this id.
        frontmatter: YAML frontmatter parsed off the source agent
            file, captured here so it can be re-prepended to the
            tuned body when the batch result arrives.
        request: :class:`ToolUseBatchRequest` ready for
            :meth:`AIOrchestrator.submit_tool_use_batch`.
    """

    agent_name: str
    custom_id: str
    frontmatter: str
    request: ToolUseBatchRequest


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
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    ) -> None:
        """Initialize SubagentsGenerator.

        Args:
            orchestrator: AI orchestrator for content generation.
            reference_dir: Directory containing reference agents.
                Defaults to .claude/agents/ in project root.
            dry_run: If True, skip actual tuning (for testing).
            max_concurrency: Upper bound on concurrent agent tunings.
                ``asyncio.Semaphore`` enforces this so a slow network or
                tight Anthropic rate limit does not produce burst-failures.
        """
        self.orchestrator = orchestrator
        self.tuner = ContentTuner(orchestrator, dry_run=dry_run)
        self.reference_dir = reference_dir or REFERENCE_AGENTS_DIR
        self.dry_run = dry_run
        self.max_concurrency = max_concurrency
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
        """Generate every required subagent concurrently.

        Each agent is tuned in its own task; ``asyncio.gather`` waits for
        all of them. A bounded ``Semaphore`` keeps the in-flight count at
        or below ``self.max_concurrency`` so we don't trip the Anthropic
        rate limiter.

        Args:
            target_context: Description of target project context.

        Returns:
            Dictionary mapping agent names to generation results, in the
            order declared in :data:`REQUIRED_AGENTS`.
        """
        agent_names = list(REQUIRED_AGENTS)
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _run_one(name: str) -> SubagentGenerationResult:
            async with semaphore:
                return await self.generate_agent(name, target_context)

        results_list = await asyncio.gather(
            *(_run_one(name) for name in agent_names),
        )
        return dict(zip(agent_names, results_list, strict=True))

    def build_batch_plan(
        self,
        target_context: str,
    ) -> list[SubagentBatchEntry]:
        """Render every required subagent as a per-call batch request.

        The Phase 5b ``green enhance --batch`` flow submits all
        subagents in one Anthropic Message Batches API call. This
        helper does the per-agent prep — load source content, parse
        out the YAML frontmatter, build a
        :class:`ToolUseBatchRequest` via the tuner — and returns one
        entry per agent. The frontmatter is captured alongside each
        request so :meth:`apply_batch_result` can reconstruct the
        full agent file once the batch returns.

        Args:
            target_context: Description of target project context.

        Returns:
            List of :class:`SubagentBatchEntry` records, in the order
            declared in :data:`REQUIRED_AGENTS`.
        """
        plan: list[SubagentBatchEntry] = []
        for agent_name in REQUIRED_AGENTS:
            content = self._load_agent_content(agent_name)
            frontmatter, body = self._parse_frontmatter(content)
            request = self.tuner.build_batch_request(
                custom_id=f"subagent:{agent_name}",
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
            plan.append(
                SubagentBatchEntry(
                    agent_name=agent_name,
                    custom_id=request.custom_id,
                    frontmatter=frontmatter,
                    request=request,
                )
            )
        return plan

    @staticmethod
    def apply_batch_result(
        agent_name: str,
        frontmatter: str,
        tool_result: ToolUseResult,
    ) -> SubagentGenerationResult:
        """Reconstruct a finished subagent file from a batch result.

        Lifts the ``tool_use`` payload via
        :meth:`ContentTuner.parse_batch_tuning_result` (same parser
        the sync path uses) and re-attaches the original frontmatter
        so the resulting file is byte-equivalent to what
        :meth:`generate_agent` would have produced.

        Args:
            agent_name: Name of the agent the result is for.
            frontmatter: YAML frontmatter captured by
                :meth:`build_batch_plan`.
            tool_result: One entry from
                :attr:`BatchResultsBundle.successes`.

        Returns:
            :class:`SubagentGenerationResult` ready to write to disk.
        """
        tuning_result = ContentTuner.parse_batch_tuning_result(tool_result)
        return SubagentGenerationResult(
            agent_name=agent_name,
            content=f"{frontmatter}\n{tuning_result.content}",
            tuned=True,
            changes=tuning_result.changes,
        )

    def get_agent_frontmatter(self, agent_name: str) -> str:
        """Re-read the source agent's YAML frontmatter at fetch time.

        Public sibling of :meth:`apply_batch_result` for the Phase 5b
        batch resume path. The dispatch in
        :mod:`start_green_stay_green.ai.batch_dispatch` calls this
        rather than reaching into the private ``_load_agent_content``
        / ``_parse_frontmatter`` helpers — the frontmatter capture is
        intentionally re-read (not persisted in the state file) so a
        local edit to the source agent between submit and fetch is
        picked up automatically.

        Args:
            agent_name: Name of the agent (must be a
                :data:`REQUIRED_AGENTS` key).

        Returns:
            The YAML frontmatter block, terminating delimiter
            included — ready to prepend to a tuned body.

        Raises:
            FileNotFoundError: If the source agent file is missing
                (raised by :meth:`_load_agent_content`).
            ValueError: If the source file lacks a frontmatter block
                (raised by :meth:`_parse_frontmatter`).
        """
        content = self._load_agent_content(agent_name)
        frontmatter, _ = self._parse_frontmatter(content)
        return frontmatter

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
