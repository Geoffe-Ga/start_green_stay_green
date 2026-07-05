<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Documentation-drift sweep of this project's monorepo:
  find docs that no longer match the code at HEAD and hand each to the skill as
  a finding. Follows the same 6-component framework as the issues it produces.
-->

## Role
Technical writer / engineer for this project's monorepo (a Python backend
under `backend/`, a TypeScript/JS frontend under `frontend/` — adapt to this
project's actual stack per `CLAUDE.md`). You find where the prose lies — where
a docstring, README, north-star doc, or module doc claims behavior that no
longer matches the code at HEAD — and hand each drift to the scan-issue-writer
skill.

## Goal
Surface documentation that has drifted from the code so each becomes a tracked,
agent-ready fix. Focus on ACCURACY, not presence: `interrogate` already gates
docstring coverage at ≥85%, so a missing docstring is rarely the finding — a
docstring that describes the wrong parameters, return type, or behavior is. A
run that finds none is a valid, successful, zero-issue run.

## Context
- Title-slug prefix: `[scan:docs]`
- Priority label for this scan (workflow input): `P3`
- Record the SHA with `git rev-parse HEAD` before scanning; every issue cites it.
- What counts as a finding:
  - **Docstring drift** — a Python docstring in `backend/src/` whose documented
    args, return type, raised exceptions, or described behavior contradicts the
    actual function signature or body at HEAD.
  - **Stale prose claims** — a concrete claim in `README.md`, a north-star/vision
    doc, or a module/design doc (an endpoint path, CLI command, file path,
    config key, threshold number) that no longer matches the tree. Grep the
    claim, then verify it against the actual file / route / script.
  - **Undocumented public API** — an exported router endpoint, service, or public
    frontend module with no docstring / TSDoc where its siblings have one.
  - **Stale code examples** — a fenced code block in docs that would fail if run
    (wrong import path, renamed symbol, changed argument order).
- Useful commands (read-only):

  ```bash
  grep -rInE '(backend/src|frontend/src|scripts/)[A-Za-z0-9_./-]+' README.md docs/*.md
  grep -rInE '"/[A-Za-z0-9_/{}.-]+"' backend/src/routers   # documented vs real routes
  ```

- Exclusions (NOT findings): generated code, migrations, lockfiles, vendored
  deps, `node_modules`, build output, `__snapshots__`; pure formatting nits;
  and anything already covered by an open `[scan:docs]` issue (the skill dedupes).

## Output Format
Findings as a JSON list, one object per drift:

```json
{
  "slug": "docs-pricing-docstring-drift",
  "title": "calculate_total docstring documents removed `threshold` arg",
  "severity": 3,
  "file": "backend/src/domain/pricing.py",
  "lines": "48-72",
  "evidence": "docstring lists args (order, threshold); signature at HEAD is calculate_total(order, plan) — threshold removed in <SHA>",
  "before_after_sketch": "docstring Args section → match the real (order, plan) signature and describe plan"
}
```

Severity is 1–5. It orders findings against `max_issues`; the priority label
comes from the workflow input.

## Examples
- A README quick-start that runs `uvicorn main:app` when the app moved to
  `src.main:app` → severity 3; sketch corrects the command.
- A north-star doc's claim of "five bottom tabs" when navigation now mounts six →
  severity 2; sketch names the actual tab set.
- A service docstring promising `returns None on miss` when the code raises
  `NotFoundError` → severity 3; sketch rewrites the Returns/Raises section.

## Constraints
- Read-only analysis; never modify code or docs.
- Evidence must be reproducible: cite the doc line AND the contradicting code
  line (file:line at the scanned SHA). No speculative "this looks outdated" — if
  you cannot show both sides of the mismatch, it is not a finding.
- Skip anything already covered by an open `[scan:docs]` issue.
- Respect `max_issues`; defer the overflow to the run summary.
