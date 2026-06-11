"""Cross-platform quality-gate runner (#382, windows-compat epic #378).

This package is the single home for the repo's own quality-gate logic.
Every gate (``check-all``, ``test``, ``lint``, ``format``, ``typecheck``,
``security``, ``complexity``, ``coverage``, ``mutation``) runs identically
on Windows, macOS, and Linux via::

    python -m start_green_stay_green.gates <gate> [options]

The historical ``scripts/*.sh`` entry points survive as thin POSIX
delegates: they bootstrap a virtualenv (``scripts/common.sh``) and exec
this runner, so existing muscle memory, pre-commit hooks, and CI jobs
keep working unchanged on POSIX.

Architectural decision — why a ``python -m`` module runner
==========================================================

Three options were considered for the cross-platform runner:

1. **Python module runner (chosen)** — ``python -m
   start_green_stay_green.gates <gate>``. Zero new dependencies, reuses
   the package's existing ``utils.fs.is_windows`` seam (#380), is fully
   testable with the existing pytest/coverage infrastructure, and keeps
   gate logic in exactly one importable place. Tool discovery resolves
   console scripts relative to ``sys.executable`` (``Scripts/`` on
   Windows, ``bin/`` on POSIX) with a ``shutil.which`` fallback, so no
   gate ever assumes bash or a POSIX venv layout.
2. **Nox** — adds a runtime dependency and a session/venv model that
   mismatches this repo's single-venv, pre-commit-driven workflow; gates
   would still need custom Python for parsing tool output (radon grades,
   mutmut cache), so Nox buys orchestration the repo does not need.
3. **Duplicated PowerShell scripts** — violates DRY by construction:
   every gate would exist twice (bash + PowerShell) and the pair would
   inevitably diverge, which is the exact failure mode #382 exists to
   prevent.

Thresholds (coverage 90, mutation score 80, complexity grades) live in
:mod:`start_green_stay_green.gates.common` as the single in-package
source, mirroring the user-editable values in ``pyproject.toml``.
"""
