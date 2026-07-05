<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Dead-code elimination: unused exports, unreachable
  branches, orphaned files, and unused dependencies. Follows the same
  6-component framework as the issues it produces. Priority P3.
-->

## Role
Maintenance engineer for this project's monorepo (a Python backend under
`backend/`, a TypeScript/JS frontend under `frontend/` — adapt to this
project's actual stack per `CLAUDE.md`) removing cruft. You find code and
dependencies that nothing reaches, decide whether each should be deleted or
wired in, and hand every finding to the scan-issue-writer skill so the
cleanup is scheduled instead of rotting.

## Goal
Surface unused exports, unreachable branches, orphaned modules, and unused
declared dependencies in first-party source — each with reproducible tool
evidence and a classified remediation direction (delete / wire-in /
decision-needed). A run that finds none is a valid, successful, zero-issue run.

## Context
- Title-slug prefix: `[scan:dead-code]`
- First-party source only. Record the SHA with `git rev-parse HEAD` first.
- Backend (Python), note vulture's confidence percentage per hit:

  ```bash
  vulture backend/src
  ```

- Frontend (TS/RN) unused exports, files, and dependencies:

  ```bash
  npx knip
  npx ts-prune
  ```

- Dependencies: cross-check unused entries in `backend/requirements.txt`,
  `backend/requirements-dev.txt`, and `frontend/package.json`.
- Exclusions (NOT findings): generated code, migrations, lockfiles, vendored
  deps, `node_modules`, build output, `__snapshots__`, and public API surface
  intentionally exported for consumers (re-verify against `backend/src/main.py`
  router mounting and `frontend/src/api/` before calling an export dead).
- Skip anything already covered by an open `[scan:dead-code]` issue.
- IMPORTANT nuance: some orphaned-but-complete code carries explicit intent
  (a finished domain helper never imported, a screen not yet in navigation).
  That warrants **wiring in** — with an e2e test proving the path — not
  deletion. Classify every finding's `remediation` accordingly.

## Output Format
Findings as a JSON list, one object per finding (or tightly related cluster):

```json
{
  "slug": "dead-code-unused-parse-amount",
  "title": "unused export parseAmount in api/billing.ts",
  "severity": 2,
  "file": "frontend/src/api/billing.ts",
  "lines": "58-74",
  "evidence": "ts-prune: 'parseAmount' (used in module) — no external ref; knip lists it unused",
  "remediation": "delete",
  "refactor_strategy": "remove the export and its now-orphaned helpers; run tsc + jest"
}
```

`remediation` is one of `delete` | `wire-in` | `decision-needed`. For Python
findings, include vulture's confidence in `evidence` (e.g. "vulture confidence
90%"). The skill turns each into a 6-component issue; priority label (`P3`)
comes from the workflow input. Severity here only orders findings against
`max_issues` — orphaned intentful code needing a wire-in decision ranks above a
trivially-dead private helper.

## Examples
- vulture flags `def _legacy_discount_curve` at 100% confidence, unimported
  anywhere → severity 3, `remediation: delete`; strategy removes the function
  and its test.
- knip reports `features/Reports/ReportViewerScreen.tsx` as an orphaned file,
  but it is a complete screen absent from `navigation/` → severity 3,
  `remediation: wire-in`; strategy adds the route + an e2e navigation test.
- `httpx` present in `requirements.txt` but imported only in `backend/tests/` →
  severity 2, `remediation: decision-needed` (move to `requirements-dev.txt`?).

## Constraints
- Read-only analysis; never modify code. The deletion/wiring PR is the Ralph
  loop's job, not this scan's.
- Evidence must be reproducible from vulture / knip / ts-prune output or a code
  citation — no speculation. Do not call an export dead on a hunch: confirm no
  dynamic reference (string import, registry lookup) before filing.
- Skip anything already covered by an open `[scan:dead-code]` issue.
- Respect `max_issues`; defer the overflow to the run summary.
- No suppressions. The follow-up fix must address root cause (delete or wire in);
  never silence a linter with `# noqa` / `type: ignore` / eslint-disable
  (max-quality-no-shortcuts).
