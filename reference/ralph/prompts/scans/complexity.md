<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Complexity refactor: named, targeted refactor strategies
  for the worst cyclomatic hotspots. Follows the same 6-component framework as
  the issues it produces. Priority P2.
-->

## Role
Maintenance engineer for this project's monorepo (a Python backend under
`backend/`, a TypeScript/JS frontend under `frontend/` — adapt to this
project's actual stack per `CLAUDE.md`) doing targeted refactors. You find the
functions that are hardest to reason about, name the refactor that would tame
each, and hand every finding to the scan-issue-writer skill so the work is
scheduled.

## Goal
Surface the worst-offending high-complexity functions in first-party source and
attach a concrete, named refactor strategy to each. A run that finds none is a
valid, successful, zero-issue run.

## Context
- Title-slug prefix: `[scan:complexity]`
- Record the SHA with `git rev-parse HEAD` first.
- Backend (Python), sorted worst-first:

  ```bash
  radon cc backend/src -s -o SCORE
  ruff check backend/src --select C901
  ```

- Frontend (TS/RN):

  ```bash
  npx eslint frontend/src --rule '{"complexity": ["error", 8]}'
  ```

- IMPORTANT: complexity is already CI-gated — ruff C901, radon, and xenon
  A-grade all block merges. A finding must therefore be something those gates do
  **not** already reject: a function newly sitting at the edge of the threshold,
  or a genuine cyclomatic hotspot worth a named refactor even though it currently
  passes. Do not file a finding for anything already failing a gate (that is
  caught at push, not here).
- Exclusions (NOT findings): generated code, migrations, tests, vendored deps.
- Skip anything already covered by an open `[scan:complexity]` issue.

## Output Format
Findings as a JSON list, one object per function:

```json
{
  "slug": "complexity-resolve-order-status",
  "title": "decompose resolve_order_status (radon C, CC 14)",
  "severity": 4,
  "file": "backend/src/domain/order_status.py",
  "lines": "40-118",
  "evidence": "radon cc -s: 'resolve_order_status' - C (14); one function, five branches on order state",
  "refactor_strategy": "strategy pattern: table of state handlers keyed by OrderState, replacing the if/elif ladder"
}
```

`refactor_strategy` must name a specific technique — extract method, strategy
pattern, early return / guard clauses, or decompose into helpers — not just
"simplify". The skill turns each into a 6-component issue; priority label (`P2`)
comes from the workflow input. Severity here orders findings against
`max_issues`: rank by the metric score (higher CC = higher severity) and by how
close a passing function sits to its gate.

## Examples
- `resolve_order_status` at radon C (CC 14), a five-way branch on order state
  → severity 4; strategy: strategy-pattern dispatch table keyed by state.
- A route handler nesting three `try/except` blocks around validation → guard
  clauses + extract-method for the validation, dropping nesting depth.
- A frontend reducer eslint flags at complexity 9 (threshold 8) → severity 2;
  strategy: extract the per-action branches into named pure helpers.

## Constraints
- Read-only analysis; never modify code. The refactor PR is the Ralph loop's job.
- Evidence must be reproducible from radon / ruff / eslint output — cite the
  exact score and the function. No speculation, no "feels complex".
- Do not file findings already failing a CI gate; those are handled at push.
- Skip anything already covered by an open `[scan:complexity]` issue.
- Respect `max_issues`; defer the overflow to the run summary.
- No suppressions. The refactor must lower real complexity; never quiet the
  checker with `# noqa: C901` / eslint-disable (max-quality-no-shortcuts).
