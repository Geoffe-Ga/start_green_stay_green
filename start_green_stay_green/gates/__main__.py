"""Dispatcher for ``python -m start_green_stay_green.gates <gate>`` (#382).

The one documented cross-platform entry point for every quality gate.
Unknown gates exit 2 with a usage message, matching the bash scripts'
unknown-option contract.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from start_green_stay_green.gates import check_all
from start_green_stay_green.gates import common
from start_green_stay_green.gates import complexity
from start_green_stay_green.gates import coverage
from start_green_stay_green.gates import format as format_gate
from start_green_stay_green.gates import lint
from start_green_stay_green.gates import mutation
from start_green_stay_green.gates import security
from start_green_stay_green.gates import testing
from start_green_stay_green.gates import typecheck

if TYPE_CHECKING:
    from collections.abc import Callable

#: Gate name → entry point. Names match the historical scripts/*.sh.
GATES: dict[str, Callable[[list[str] | None], int]] = {
    "check-all": check_all.main,
    "complexity": complexity.main,
    "coverage": coverage.main,
    "format": format_gate.main,
    "lint": lint.main,
    "mutation": mutation.main,
    "security": security.main,
    "test": testing.main,
    "typecheck": typecheck.main,
}


def _usage_error(message: str) -> None:
    """Print a dispatcher usage error to stderr.

    Args:
        message: Specific error description.
    """
    print(f"Error: {message}", file=sys.stderr)
    print(
        "Usage: python -m start_green_stay_green.gates <gate> [options]",
        file=sys.stderr,
    )
    print(f"Gates: {', '.join(sorted(GATES))}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Dispatch to the requested gate.

    Args:
        argv: Argument vector (None reads sys.argv).

    Returns:
        The gate's exit code, or 2 for dispatcher usage errors.
    """
    common.configure_utf8_output()
    args = sys.argv[1:] if argv is None else argv
    if not args:
        _usage_error("missing gate name")
        return 2
    gate, rest = args[0], args[1:]
    runner = GATES.get(gate)
    if runner is None:
        _usage_error(f"unknown gate: {gate}")
        return 2
    return runner(rest)


if __name__ == "__main__":
    sys.exit(main())
