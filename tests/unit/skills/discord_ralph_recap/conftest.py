"""Load the discord-ralph-recap skill's scripts as importable modules.

``recap.py`` and ``stats.py`` live under ``.claude/skills/discord-ralph-recap/
scripts/`` — outside the ``start_green_stay_green`` package — so they are
loaded directly from disk via ``importlib`` rather than imported normally.
Scoped to this test package only; does not touch the project-wide
``tests/conftest.py``.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[4]
RALPH_RECAP_SCRIPTS_DIR = (
    REPO_ROOT / ".claude" / "skills" / "discord-ralph-recap" / "scripts"
)


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        msg = f"could not build import spec for {path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ralph_stats = _load("sgsg_ralph_recap_stats", RALPH_RECAP_SCRIPTS_DIR / "stats.py")

# recap.py does a bare `import stats` (a sibling-module import, since both
# scripts live side by side in the skill's scripts/ dir) - put that directory
# on sys.path first so the import resolves before loading recap.py itself.
if str(RALPH_RECAP_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(RALPH_RECAP_SCRIPTS_DIR))
ralph_recap = _load("sgsg_ralph_recap", RALPH_RECAP_SCRIPTS_DIR / "recap.py")
