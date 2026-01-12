"""Generator modules for creating project scaffolding components."""

from . import architecture
from . import base
from . import ci
from . import claude_md
from . import github_actions
from . import metrics
from . import precommit
from . import scripts
from . import skills
from . import subagents

__all__ = [
    "architecture",
    "base",
    "ci",
    "claude_md",
    "github_actions",
    "metrics",
    "precommit",
    "scripts",
    "skills",
    "subagents",
]
