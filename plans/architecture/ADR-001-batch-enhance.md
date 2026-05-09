# ADR-001 — Batch-Mode `green enhance`

**Status**: Accepted
**Date**: 2026-05-09
**Phase**: 5a (primitives), 5b (CLI wiring — follow-up)

## Context

The Anthropic Message Batches API offers a 50 % discount for
asynchronous bulk submissions (up to 100k requests per submission,
≤24 h SLA). `green enhance` runs N independent per-target tunings
(8 subagents + 0–N skills) — exactly the workload the Batches API
was designed for, and the natural place to surface the discount.

Phase 4 left us with a tuner that already builds its per-call payload
through `_build_system_blocks` + `_build_user_message`, and a state
file (Phase 3c) that already persists per-target completion records.
The two together are 80 % of what a batch path needs; the remaining
20 % is the SDK-level bridge (submit / poll / fetch) and a state
extension for the in-flight batch id.

## Decisions

### D1 — Two-call CLI pattern, not an in-process polling loop

When the user runs `green enhance --batch`:

1. **First invocation**: build per-target requests, call
   `submit_tool_use_batch`, persist the batch id to
   `.claude/.enhance-state.json`, print a one-liner ("submitted, run
   again to fetch"), exit 0.
2. **Second invocation** (any time within ≤24 h): detect the
   in-flight batch from state, call `poll_batch`. If still
   running → print status, exit 0. If `ended` → call
   `fetch_batch_results`, write per-target outputs, mark targets
   completed, clear the batch field, exit 0.

A `--wait` flag (Phase 5b, optional) drives an in-process
`asyncio.sleep(30)` + poll loop for users who want a single blocking
call. The two-call pattern is the **default** because:

- It is friendly to CI (no long-running step waiting on a 50 %-cheaper
  but multi-minute-to-multi-hour API).
- It is naturally idempotent — losing the shell or hitting Ctrl-C
  between submission and fetch is harmless; the state file carries
  the recovery cursor.
- The user-visible mental model is "I submitted; now I'll come back
  and pick it up", which matches how the API actually works.

### D2 — Batch types live in `ai/batch.py`, methods on `AIOrchestrator`

`ai/batch.py` defines the dataclasses (`ToolUseBatchRequest`,
`BatchSubmission`, `BatchPoll`, `BatchError`, `BatchResultsBundle`)
and the per-result parser (`parse_batch_result_entry`).
`AIOrchestrator` keeps the SDK calls (`submit_tool_use_batch`,
`poll_batch`, `fetch_batch_results`).

Why split? The parser and dataclasses are pure-data and unit-testable
without any Anthropic client at all; the SDK calls are integration
concerns. Splitting keeps each side small and lets the parser ship
test doubles (plain dicts) instead of forcing tests to construct SDK
Pydantic models.

The cycle (`orchestrator` needs `ai/batch.py`'s types to declare its
new methods; `ai/batch.py`'s parser builds `ToolUseResult`/`TokenUsage`
from result entries) is broken with a third module:
**`ai/types.py`** holds `GenerationError`, `TokenUsage`,
`GenerationResult`, and `ToolUseResult`. Both `orchestrator` and
`batch` import from `ai.types` at the top level — no lazy imports,
no runtime cycle. `orchestrator.py` re-exports the same names so
existing `from start_green_stay_green.ai.orchestrator import
ToolUseResult` callsites across the codebase keep working.

### D3 — State extension is additive, schema version stays at 1

`EnhanceState` gains an optional `batch: BatchProgress | None` field.
When `None` (or empty `batch_id`), `to_dict` omits the `batch` key
entirely so an existing state file written by a pre-batch CLI is
byte-identical after a no-op round-trip. `from_dict` tolerates a
missing `batch` key (returns `None`) and a malformed one (drops it,
returns `None`) — same philosophy the rest of the loader follows.

A pre-batch reader sees the new `batch` key as an unknown top-level
field and ignores it; the docstring already commits us to that
forward-compat contract. No version bump is required.

### D4 — Per-request failures do not abort the batch reconciliation

`fetch_batch_results` returns a `BatchResultsBundle` with two parallel
maps (`successes` and `failures`) keyed by `custom_id`. The CLI's
resume path can decide per-target whether to retry (Phase 5b) or
report and skip — but a single `errored` request never raises through
the orchestrator, because doing so would leak the cost of all the
sibling `succeeded` requests that the user has already paid for.

## Alternatives Considered

### A1 — Submit + block in one CLI call

A `green enhance --batch` that submits and blocks for the whole batch
to finish was rejected because:

- The 50 % discount comes with the trade-off that the SLA is
  ≤24 h. A blocking CLI invocation can in principle hang for hours.
  Operators routinely kill processes that have not progressed in
  minutes; the batch then leaks (already paid for, never harvested).
- Two-call works trivially in CI; one-call needs a "what if my CI
  step times out?" story that the two-call pattern just does not
  generate.

### A2 — Consolidate all targets into one mega-prompt

Submit one `messages.create` with a prompt that asks the model to
adapt all 8 subagents at once. Rejected because it loses
**per-target token accounting and per-target retry**, both of which
the existing telemetry (Phase 0) and skip-unchanged (Phase 3c) paths
depend on. The Batches API submits N independent requests inside one
submission — that gives us the 50 % discount **without** flattening
the per-request shape.

### A3 — Move batch types into `orchestrator.py`

Originally drafted that way. Reverted because the parser is the
biggest single component (~80 lines), and it is testable without
spinning up any SDK client. Keeping it in its own module makes the
test seam wider.

## Consequences

**Positive**:
- Bulk runs (CI projects, demo repos, batch enhancement of
  multi-language scaffolds) get a 50 % cost reduction.
- The state file becomes the single source of truth for both
  "what was last completed?" and "what is currently in flight?".
- The parser is a thin pure function — easy to unit-test, easy to
  swap if the SDK shape changes.

**Negative**:
- Two-call UX is unfamiliar; users who expect a long-running command
  may run the second invocation too soon and see a status line. The
  `--wait` flag (Phase 5b) covers that case for users who want it.
- Recovery from a state-file corruption between submit and fetch
  costs the user the batch — they pay but cannot retrieve. This
  matches the existing state-file philosophy ("worst case re-tune");
  documenting that explicitly in `green enhance --help` is part of
  Phase 5b.

## Phase 5 Scope

- **5a (this PR)**: orchestrator primitives + tuner request builder
  + state extension + this ADR. No CLI wiring; no user-visible flag.
- **5b (follow-up PR)**: `green enhance --batch` flag, the two-call
  flow, optional `--wait` for in-process polling, README + `--help`
  copy.
