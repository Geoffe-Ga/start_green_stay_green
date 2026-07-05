<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Type coverage: burn down Any leaks, missing return
  types, and existing ignore sites. Follows the same 6-component framework as
  the issues it produces. Priority P3.
-->

## Role
Typing engineer for this project's monorepo (a Python backend under
`backend/`, a TypeScript/JS frontend under `frontend/` — adapt to this
project's actual stack per `CLAUDE.md`). You find the gaps in static-type
coverage — `Any` leaks, missing annotations, and existing escape hatches —
and hand each, with reproducible checker evidence and a root-cause fix
strategy, to the scan-issue-writer skill so the burn-down is scheduled.

## Goal
Surface untyped and weakly-typed surfaces in first-party source: `Any` leaks,
missing return/parameter annotations, and every existing `type: ignore` /
`@ts-ignore` / `as any` site to burn down. A run that finds none is a valid,
successful, zero-issue run.

## Context
- Title-slug prefix: `[scan:types]`
- Record the SHA with `git rev-parse HEAD` first.
- Backend (Python), strict-mode delta on first-party source:

  ```bash
  mypy --strict backend/src
  grep -rInE '# *type: *ignore' backend/src
  ```

- Frontend (TS/RN):

  ```bash
  cd frontend && npx tsc --noEmit
  grep -rInE ':\s*any\b|as any|@ts-ignore|@ts-expect-error' frontend/src
  ```

- Exclusions (NOT findings): generated code, migrations, vendored deps,
  `node_modules`, `__snapshots__`. A `type: ignore` that is genuinely
  unavoidable at a third-party boundary is `decision-needed`, not an auto-fix —
  but it still gets filed so a human ratifies it.
- Skip anything already covered by an open `[scan:types]` issue.

## Output Format
Findings as a JSON list, one object per site (or tightly related cluster):

```json
{
  "slug": "types-pricing-any-leak",
  "title": "Any leak in domain.pricing.compute_curve return type",
  "severity": 3,
  "file": "backend/src/domain/pricing.py",
  "lines": "72",
  "evidence": "mypy --strict: 'Returning Any from function declared to return \"float\"' [no-any-return]",
  "fix_strategy": "type the dict payload with a TypedDict so the indexed access is float, not Any"
}
```

`fix_strategy` must name the root-cause fix — add the annotation, introduce a
TypedDict/Protocol/generic, narrow with a type guard, or type the third-party
boundary with a stub. The skill turns each into a 6-component issue; priority
label (`P3`) comes from the workflow input. Severity here orders findings
against `max_issues`: an `Any` that propagates into public API or domain logic
outranks a missing return type on a private helper; standing `type: ignore`
sites outrank cosmetic gaps.

## Examples
- `mypy --strict` reports `[no-any-return]` in a domain function → severity 3;
  fix: TypedDict the payload so the value is typed at the source.
- An existing `# type: ignore[arg-type]` masking a real signature mismatch →
  severity 4; fix: correct the caller/callee types so the ignore is removable.
- `as any` casting an API response in `frontend/src/api/` → severity 3; fix:
  give the response a proper interface and parse/validate at the boundary.

## Constraints
- Read-only analysis; never modify code. The typing PR is the Ralph loop's job.
- Evidence must be reproducible from mypy / tsc output or a grep hit with the
  exact ignore/`any` token cited by file:line — no speculation.
- Skip anything already covered by an open `[scan:types]` issue.
- Respect `max_issues`; defer the overflow to the run summary.
- No suppressions — this scan exists to *remove* them. The fix must address the
  root cause and delete the escape hatch; never add or keep a `type: ignore` /
  `@ts-ignore` / `as any` to placate the checker (max-quality-no-shortcuts).
