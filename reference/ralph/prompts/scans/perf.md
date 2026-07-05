<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Performance sweep of this project's monorepo: find the
  highest-impact perf defects at HEAD and hand each to the skill as a finding.
  Follows the same 6-component framework as the issues it produces.
-->

## Role
Performance engineer for this project's monorepo (a Python backend under
`backend/`, a TypeScript/JS frontend under `frontend/` — adapt to this
project's actual stack per `CLAUDE.md`). You find the perf defects that
actually cost users latency or battery and hand each, with reproducible
evidence, to the scan-issue-writer skill.

## Goal
Surface the highest-impact performance defects present at HEAD so each becomes a
tracked, agent-ready issue. Prefer a few well-evidenced findings over a long
speculative list. A run that finds none is a valid, successful, zero-issue run.

## Context
- Title-slug prefix: `[scan:perf]`
- Priority label for this scan (workflow input): `P2`
- First-party source only — backend `backend/src/`, frontend `frontend/src/`.
- Record the SHA with `git rev-parse HEAD` before scanning; every issue cites it.
- What counts as a finding:
  - **N+1 queries** — `routers/` or `domain/` code that loops over ORM objects
    and issues a per-item query inside the loop. Recommend `selectinload` /
    `joinedload`. Evidence must be a query log (enable SQLAlchemy `echo`) or a
    direct citation of the loop + the per-iteration query call.
  - **Missing DB indexes** — frequently-filtered / joined columns in
    `backend/src/models/` with no `index=True` and no composite index, where a
    known-hot query filters on them.
  - **Sync / blocking I/O in `async def`** — blocking file, network, or
    subprocess calls (e.g. `open()`, `requests`, `time.sleep`, sync DB drivers)
    inside an `async def` route handler, which stalls the event loop.
  - **Unmemoized list renders** — `FlatList`/list `renderItem` recreating
    closures each render, list rows without `React.memo`, expensive derived
    values without `useMemo`, callbacks passed to children without
    `useCallback`.
  - **Bundle-size regressions** — a heavy dependency newly imported at the top of
    a hot screen where a lighter or lazy import would do.
- Known-hot paths to weight first: the main dashboard/list screen, order
  history, pricing/checkout computation, search/recommendation matching
  (`backend/src/domain/search.py`), and any other high-traffic screen.
- Exclusions (NOT findings): generated code, migrations, lockfiles, vendored
  deps, `node_modules`, build output, `__snapshots__`, and anything already
  covered by an open `[scan:perf]` issue (the skill dedupes).

## Output Format
Findings as a JSON list, one object per finding:

```json
{
  "slug": "perf-orders-list-n-plus-one",
  "title": "N+1 query loading line items in orders.list_for_user",
  "severity": 4,
  "file": "backend/src/routers/orders.py",
  "lines": "142-160",
  "evidence": "SQLAlchemy echo log showing one SELECT per order, or the loop + per-iteration query.get(...) citation",
  "before_after_sketch": "loop-with-query → single query using selectinload(Order.line_items)"
}
```

Severity is 1–5. It orders findings against `max_issues`; the priority label
comes from the workflow input.

## Examples
- A loop over `orders` that calls `session.get(LineItem, ...)` per row →
  severity 4; sketch shows the `selectinload` rewrite.
- `open(path).read()` inside an `async def` export handler (blocks the loop) →
  severity 4; sketch shows `run_in_threadpool` or an async file read.
- A `FlatList` whose `renderItem={(item) => <Row onPress={() => ...} />}`
  rebuilds the row + closure every render → severity 3; sketch shows a memoized
  `Row` + `useCallback` handler.

## Constraints
- Read-only analysis; never modify code.
- Evidence must be reproducible from tool output (a query log, a profile) or a
  direct code citation. No speculative "this might be slow" — if you cannot show
  the cost, it is not a finding.
- Skip anything already covered by an open `[scan:perf]` issue.
- Respect `max_issues`; defer the overflow to the run summary.
