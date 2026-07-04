"""Unit tests for the pluggable agent-context renderer (#387).

The agent-context module renders the SAME canonical content (the
``reference/claude/docs/*.md`` split docs plus the reference subagent
role descriptions) into per-assistant formats:

- ``agents-md`` → a single ``AGENTS.md`` (open agent-context convention)
- ``aider``     → ``CONVENTIONS.md`` + ``.aider.conf.yml``

Golden tests use a tiny synthetic reference tree so the expected output
can be asserted byte-for-byte without duplicating the real reference
prose in the repository (DRY). Structural tests run against the real
reference content shipped with the package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import yaml

from start_green_stay_green.generators.agent_context import AGENTS_MD_FILENAME
from start_green_stay_green.generators.agent_context import AGENT_CONTEXT_TARGETS
from start_green_stay_green.generators.agent_context import AIDER_CONF_FILENAME
from start_green_stay_green.generators.agent_context import AIDER_CONVENTIONS_FILENAME
from start_green_stay_green.generators.agent_context import AgentContextContent
from start_green_stay_green.generators.agent_context import AgentRole
from start_green_stay_green.generators.agent_context import DocSection
from start_green_stay_green.generators.agent_context import TARGET_AGENTS_MD
from start_green_stay_green.generators.agent_context import TARGET_AIDER
from start_green_stay_green.generators.agent_context import TARGET_CLAUDE
from start_green_stay_green.generators.agent_context import load_agent_context_content
from start_green_stay_green.generators.agent_context import render_agents_md
from start_green_stay_green.generators.agent_context import render_aider_conf
from start_green_stay_green.generators.agent_context import render_aider_conventions
from start_green_stay_green.generators.agent_context import render_target_files
from start_green_stay_green.generators.claude_md import CLAUDE_DOC_NAMES
from start_green_stay_green.generators.subagents import REQUIRED_AGENTS

if TYPE_CHECKING:
    from pathlib import Path

# ---------------------------------------------------------------------------
# Synthetic reference fixtures (tiny, fully controlled content)
# ---------------------------------------------------------------------------

# Titles must keep the quality-standards stem → "Quality Standards" title
# mapping used by the link-rewrite assertions below.
_SYNTHETIC_TITLES: dict[str, str] = {
    "principles": "Critical Principles",
    "quality-standards": "Quality Standards",
    "workflow": "Development Workflow",
    "testing": "Testing Strategy",
    "tools": "Tool Usage & Code Standards",
    "troubleshooting": "Common Pitfalls & Troubleshooting",
}

_PRINCIPLES_DOC = """\
# Critical Principles

**Navigation**: [← Back](../CLAUDE.md) | [Quality →](quality-standards.md)

---

Always run checks for {{PROJECT_NAME}}.

See [Quality Standards](quality-standards.md) and
[Forbidden Patterns](quality-standards.md#2-forbidden-patterns).

---

**Navigation**: [← Back](../CLAUDE.md) | [Quality →](quality-standards.md)
"""


@pytest.fixture(name="reference_dir")
def fixture_reference_dir(tmp_path: Path) -> Path:
    """Create a synthetic ``reference/claude``-style tree."""
    ref_dir = tmp_path / "reference-claude"
    docs_dir = ref_dir / "docs"
    docs_dir.mkdir(parents=True)
    (ref_dir / "CLAUDE.md").write_text(
        "# Claude Code Project Context: {{PROJECT_NAME}}\n",
        encoding="utf-8",
    )
    (docs_dir / "principles.md").write_text(_PRINCIPLES_DOC, encoding="utf-8")
    for stem in CLAUDE_DOC_NAMES:
        if stem == "principles":
            continue
        (docs_dir / f"{stem}.md").write_text(
            f"# {_SYNTHETIC_TITLES[stem]}\n\nBody for {{{{PROJECT_NAME}}}}.\n",
            encoding="utf-8",
        )
    return ref_dir


@pytest.fixture(name="agents_dir")
def fixture_agents_dir(tmp_path: Path) -> Path:
    """Create a synthetic reference agents dir with all required agents."""
    agents_dir = tmp_path / "reference-agents"
    agents_dir.mkdir()
    for agent_name, source_file in REQUIRED_AGENTS.items():
        (agents_dir / source_file).write_text(
            f"---\nname: {agent_name}\ndescription: Focus of {agent_name}.\n---\n\n"
            f"# {agent_name}\n",
            encoding="utf-8",
        )
    return agents_dir


@pytest.fixture(name="synthetic_content")
def fixture_synthetic_content(
    reference_dir: Path,
    agents_dir: Path,
) -> AgentContextContent:
    """Load the shared content from the synthetic reference tree."""
    return load_agent_context_content(
        {"project_name": "golden-proj", "language": "python"},
        reference_dir=reference_dir,
        agents_dir=agents_dir,
    )


def _expected_roles_rows() -> str:
    """Build the expected roles table rows from REQUIRED_AGENTS order."""
    return "\n".join(f"| `{name}` | Focus of {name}. |" for name in REQUIRED_AGENTS)


def _expected_folded_sections() -> str:
    """Expected folded body shared by AGENTS.md and CONVENTIONS.md."""
    principles = (
        "## Critical Principles\n"
        "\n"
        "---\n"
        "\n"
        "Always run checks for golden-proj.\n"
        "\n"
        "See [Quality Standards](#quality-standards) and\n"
        "[Forbidden Patterns](#2-forbidden-patterns).\n"
        "\n"
        "---\n"
    )
    others = "\n".join(
        f"## {_SYNTHETIC_TITLES[stem]}\n\nBody for golden-proj.\n"
        for stem in CLAUDE_DOC_NAMES
        if stem != "principles"
    )
    return f"{principles}\n{others}"


# ---------------------------------------------------------------------------
# Target constants
# ---------------------------------------------------------------------------


class TestTargetConstants:
    """The target registry exposes the three supported targets."""

    def test_targets_tuple_lists_claude_first(self) -> None:
        """Claude is the default target and listed first."""
        assert AGENT_CONTEXT_TARGETS == ("claude", "agents-md", "aider")

    def test_target_constants_match_registry(self) -> None:
        """The named constants are the registry entries."""
        assert TARGET_CLAUDE == "claude"
        assert TARGET_AGENTS_MD == "agents-md"
        assert TARGET_AIDER == "aider"

    def test_filenames(self) -> None:
        """Emitted filenames match the documented per-target layouts."""
        assert AGENTS_MD_FILENAME == "AGENTS.md"
        assert AIDER_CONVENTIONS_FILENAME == "CONVENTIONS.md"
        assert AIDER_CONF_FILENAME == ".aider.conf.yml"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class TestLoadAgentContextContent:
    """Tests for the shared-content loader."""

    def test_sections_follow_doc_name_order(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Sections come back in CLAUDE_DOC_NAMES order."""
        assert tuple(s.stem for s in synthetic_content.sections) == CLAUDE_DOC_NAMES

    def test_section_titles_parsed_from_h1(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Each section title is the doc's H1 text."""
        titles = {s.stem: s.title for s in synthetic_content.sections}
        assert titles == _SYNTHETIC_TITLES

    def test_tokens_substituted(self, synthetic_content: AgentContextContent) -> None:
        """``{{PROJECT_NAME}}`` tokens are substituted in section bodies."""
        for section in synthetic_content.sections:
            assert "{{PROJECT_NAME}}" not in section.body
            assert "golden-proj" in section.body

    def test_roles_follow_required_agents_order(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Roles come back in REQUIRED_AGENTS declaration order."""
        assert tuple(r.name for r in synthetic_content.roles) == tuple(REQUIRED_AGENTS)

    def test_role_descriptions_from_frontmatter(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Role descriptions are read from the agent YAML frontmatter."""
        first = synthetic_content.roles[0]
        assert first.description == f"Focus of {first.name}."

    def test_missing_agent_file_raises(
        self, reference_dir: Path, agents_dir: Path
    ) -> None:
        """A missing reference agent file fails fast."""
        (agents_dir / next(iter(REQUIRED_AGENTS.values()))).unlink()
        with pytest.raises(FileNotFoundError, match="Reference subagent not found"):
            load_agent_context_content(
                {"project_name": "p", "language": "python"},
                reference_dir=reference_dir,
                agents_dir=agents_dir,
            )

    def test_agent_without_description_raises(
        self, reference_dir: Path, agents_dir: Path
    ) -> None:
        """An agent frontmatter without a description fails fast."""
        source_file = next(iter(REQUIRED_AGENTS.values()))
        (agents_dir / source_file).write_text(
            "---\nname: x\n---\nbody\n", encoding="utf-8"
        )
        with pytest.raises(ValueError, match="description"):
            load_agent_context_content(
                {"project_name": "p", "language": "python"},
                reference_dir=reference_dir,
                agents_dir=agents_dir,
            )

    def test_doc_without_h1_raises(self, reference_dir: Path, agents_dir: Path) -> None:
        """A reference doc that does not start with an H1 fails fast."""
        (reference_dir / "docs" / "workflow.md").write_text(
            "no heading here\n", encoding="utf-8"
        )
        with pytest.raises(ValueError, match="workflow"):
            load_agent_context_content(
                {"project_name": "p", "language": "python"},
                reference_dir=reference_dir,
                agents_dir=agents_dir,
            )


# ---------------------------------------------------------------------------
# Golden outputs (synthetic reference tree, full-file assertions)
# ---------------------------------------------------------------------------


class TestAgentsMdGolden:
    """Full-file golden assertions for the agents-md target."""

    def test_agents_md_golden(self, synthetic_content: AgentContextContent) -> None:
        """AGENTS.md renders byte-for-byte as specified."""
        expected = (
            "# golden-proj — Agent Context\n"
            "\n"
            "**Primary language**: python\n"
            "\n"
            "> Generated by Start Green Stay Green. This file follows the\n"
            "> AGENTS.md open agent-context convention: a single Markdown file\n"
            "> at the repository root that coding agents read for project\n"
            "> context. Every section below is rendered from the same canonical\n"
            "> content as the other generated agent-context formats.\n"
            "\n"
            "---\n"
            "\n"
            "## Agent Roles\n"
            "\n"
            "Specialist roles for structuring AI-assisted work on this project.\n"
            "When the `claude` context target is also generated, each role ships\n"
            "as a Claude Code subagent profile under `.claude/agents/`.\n"
            "\n"
            "| Role | Focus |\n"
            "| --- | --- |\n"
            f"{_expected_roles_rows()}\n"
            "\n"
            "---\n"
            "\n"
            f"{_expected_folded_sections()}"
        )
        assert render_agents_md(synthetic_content) == expected

    def test_agents_md_has_no_navigation_lines(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Per-doc navigation chrome is stripped from the folded file."""
        assert "**Navigation**" not in render_agents_md(synthetic_content)

    def test_agents_md_has_no_doc_file_links(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """Intra-tree ``*.md`` links are rewritten to in-file anchors."""
        rendered = render_agents_md(synthetic_content)
        for stem in CLAUDE_DOC_NAMES:
            assert f"({stem}.md" not in rendered
        assert "(../CLAUDE.md)" not in rendered


class TestAiderGolden:
    """Full-file golden assertions for the aider target."""

    def test_conventions_md_golden(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """CONVENTIONS.md renders byte-for-byte as specified."""
        expected = (
            "# golden-proj — Coding Conventions\n"
            "\n"
            "**Primary language**: python\n"
            "\n"
            "> Generated by Start Green Stay Green for AI pair-programming\n"
            "> assistants. Aider loads this file into every chat via the\n"
            "> generated `.aider.conf.yml` (`read: CONVENTIONS.md`). Every\n"
            "> section below is rendered from the same canonical content as\n"
            "> the other generated agent-context formats.\n"
            "\n"
            "---\n"
            "\n"
            f"{_expected_folded_sections()}"
        )
        assert render_aider_conventions(synthetic_content) == expected

    def test_aider_conf_golden(self) -> None:
        """.aider.conf.yml renders byte-for-byte as specified."""
        expected = (
            "# Generated by Start Green Stay Green.\n"
            "# Loads the shared project conventions into every aider chat.\n"
            "# Reference: https://aider.chat/docs/usage/conventions.html\n"
            "read: CONVENTIONS.md\n"
        )
        assert render_aider_conf() == expected

    def test_aider_conf_is_valid_yaml_reading_conventions(self) -> None:
        """The generated aider config parses and points at CONVENTIONS.md."""
        parsed = yaml.safe_load(render_aider_conf())
        assert parsed == {"read": "CONVENTIONS.md"}


# ---------------------------------------------------------------------------
# Target registry dispatch
# ---------------------------------------------------------------------------


class TestRenderTargetFiles:
    """Tests for the per-target file map dispatch."""

    def test_agents_md_target_emits_single_file(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """agents-md emits exactly AGENTS.md."""
        files = render_target_files(TARGET_AGENTS_MD, synthetic_content)
        assert set(files) == {AGENTS_MD_FILENAME}
        assert files[AGENTS_MD_FILENAME] == render_agents_md(synthetic_content)

    def test_aider_target_emits_two_files(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """aider emits CONVENTIONS.md plus .aider.conf.yml."""
        files = render_target_files(TARGET_AIDER, synthetic_content)
        assert set(files) == {AIDER_CONVENTIONS_FILENAME, AIDER_CONF_FILENAME}

    def test_claude_target_rejected(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """claude has no standalone emitter (existing generators own it)."""
        with pytest.raises(ValueError, match="claude"):
            render_target_files(TARGET_CLAUDE, synthetic_content)

    def test_unknown_target_rejected(
        self, synthetic_content: AgentContextContent
    ) -> None:
        """An unknown target name fails fast."""
        with pytest.raises(ValueError, match="cursor"):
            render_target_files("cursor", synthetic_content)


# ---------------------------------------------------------------------------
# Real reference content (structural invariants + determinism)
# ---------------------------------------------------------------------------


@pytest.fixture(name="real_content", scope="module")
def fixture_real_content() -> AgentContextContent:
    """Load the shared content from the real packaged reference tree."""
    return load_agent_context_content(
        {"project_name": "real-proj", "language": "python"},
    )


class TestRealReferenceRendering:
    """Render the real reference content and assert invariants."""

    def test_deterministic_byte_identical(
        self, real_content: AgentContextContent
    ) -> None:
        """Two renders of the same content are byte-identical."""
        assert render_agents_md(real_content) == render_agents_md(real_content)
        assert render_aider_conventions(real_content) == render_aider_conventions(
            real_content
        )

    def test_agents_md_contains_all_section_titles(
        self, real_content: AgentContextContent
    ) -> None:
        """Every reference doc is folded in as an H2 section."""
        rendered = render_agents_md(real_content)
        for section in real_content.sections:
            assert f"\n## {section.title}\n" in rendered

    def test_agents_md_contains_all_roles(
        self, real_content: AgentContextContent
    ) -> None:
        """Every required agent appears in the roles table."""
        rendered = render_agents_md(real_content)
        for name in REQUIRED_AGENTS:
            assert f"| `{name}` |" in rendered

    def test_no_unsubstituted_tokens(self, real_content: AgentContextContent) -> None:
        """No ``{{TOKEN}}`` placeholders leak into the output."""
        assert "{{PROJECT_NAME}}" not in render_agents_md(real_content)
        assert "{{PROJECT_NAME}}" not in render_aider_conventions(real_content)

    def test_no_navigation_or_doc_links_leak(
        self, real_content: AgentContextContent
    ) -> None:
        """Navigation chrome and intra-tree doc links never leak."""
        for rendered in (
            render_agents_md(real_content),
            render_aider_conventions(real_content),
        ):
            assert "**Navigation**" not in rendered
            assert "(../CLAUDE.md)" not in rendered
            for stem in CLAUDE_DOC_NAMES:
                assert f"({stem}.md" not in rendered

    def test_lf_only_output(self, real_content: AgentContextContent) -> None:
        """Rendered content never contains CR characters."""
        assert "\r" not in render_agents_md(real_content)
        assert "\r" not in render_aider_conventions(real_content)
        assert "\r" not in render_aider_conf()

    def test_fragment_links_rewritten_to_anchors(
        self, real_content: AgentContextContent
    ) -> None:
        """A known cross-doc fragment link survives as a bare anchor."""
        # troubleshooting.md links to quality-standards.md#2-forbidden-patterns
        assert "(#2-forbidden-patterns)" in render_agents_md(real_content)


# ---------------------------------------------------------------------------
# Dataclass shape
# ---------------------------------------------------------------------------


class TestDataclasses:
    """The content records are immutable value objects."""

    def test_doc_section_is_frozen_value_object(self) -> None:
        """DocSection is a frozen (hashable) dataclass with value equality."""
        section = DocSection(stem="principles", title="T", body="b")
        assert section == DocSection(stem="principles", title="T", body="b")
        assert hash(section) == hash(DocSection(stem="principles", title="T", body="b"))

    def test_agent_role_is_frozen_value_object(self) -> None:
        """AgentRole is a frozen (hashable) dataclass with value equality."""
        role = AgentRole(name="r", description="d")
        assert role == AgentRole(name="r", description="d")
        assert hash(role) == hash(AgentRole(name="r", description="d"))
