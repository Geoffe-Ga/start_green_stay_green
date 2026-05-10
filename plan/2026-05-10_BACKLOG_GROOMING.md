# Backlog Grooming: 2026-05-10

## Scope

Systematic review of the 38 PRs merged since the last grooming (#286,
2026-04-10) — covering the dependency-batch cleanup, the Phase 0–5b
claude-init optimization roadmap, and the Phase 6 follow-up trio
(#321 / #323 / #324) that closes out the optimization work and ships
the `v1.0.0` release.

## PRs Analyzed

PRs #287 → #324 (38 PRs total). Roadmap groupings:

### Dependency hygiene (Apr 2026)

| PR  | Title                                                                | Issues Closed | Status        |
| --- | -------------------------------------------------------------------- | ------------- | ------------- |
| #287 | fix(typescript): restrict Prettier scope                             | #193          | ✅ closed this grooming |
| #288 | fix(cli): deduplicate languages in `_get_setup_instructions`         | #285          | ✅ closed this grooming |
| #289 | fix(deps): pin Black to ==26.3.1                                     | #280          | ✅ closed this grooming |
| #290 | fix(deps): upgrade pyupgrade + refurb for Python 3.14 compat         | #281          | ✅ closed this grooming |
| #291 | ci(deps): actions/checkout 4→6                                       | —             | dependabot    |
| #292 | ci(deps): actions/github-script 7→9                                  | —             | dependabot    |
| #293 | fix(deps): consolidate 8 dependabot updates                          | —             | rollup        |
| #294 | chore: consolidate three `claude/` directories into `.claude/`       | —             | cleanup       |
| #295 | refactor(tests): address PR #287 review feedback (DRY)               | —             | follow-up to #287 |
| #301 | fix(ci): ignore pip CVE-2026-3219 (no fix available)                 | #302          | ✅ already closed |
| #303 | feat(skills): import 3 new skills from well-worn-tools               | —             | skill import  |

### Optimization roadmap (Phases 0–5b, Apr–May 2026)

| PR  | Title                                                                | Issues Closed | Status        |
| --- | -------------------------------------------------------------------- | ------------- | ------------- |
| #304 | docs(plans): add roadmap to optimize Claude usage in green init      | —             | docs only     |
| #305 | perf(init): execute Phases 0-2 of optimization roadmap               | #306          | ✅ already closed |
| #308 | feat(init): Phase 3a — two-pass split + `--offline`/`--no-enhance`    | —             | no tracking issue (roadmap-driven) |
| #309 | feat(cli): Phase 3b — `green enhance` command                        | —             | same          |
| #310 | feat(cli): Phase 3c — `.enhance-state.json` resume                   | —             | same          |
| #311 | feat(ai): Phase 2c — prompt caching + `tool_use` structured output   | —             | same          |
| #312 | feat(prompts): Phase 4 — 6-component templates                       | —             | same          |
| #313 | feat(batch): Phase 5a — Batches API primitives + ADR                 | —             | same          |
| #314 | feat(skills): import `await-claude-review` helper                    | —             | skill import  |
| #315 | feat(batch): Phase 5b — `green enhance --batch` CLI wiring           | —             | spawned #316–#319 |

### Phase 6 — release polish + follow-ups (May 2026)

| PR  | Title                                                                | Issues Closed | Status        |
| --- | -------------------------------------------------------------------- | ------------- | ------------- |
| #320 | feat: import iteration-trigger workflow from well-worn-tools         | —             | infra import  |
| #321 | docs(release): Phase 6a — README AI section + CHANGELOG + v1.0.0     | —             | release polish |
| #322 | docs(review): Phase-6a round-2 follow-ups                            | —             | review polish |
| #323 | feat(cli): Phase 6b — path-containment guard + first-run `--wait` warning | #317, #319 | ✅ closed by PR keywords |
| #324 | refactor: Phase 6c — `ResumeStatus` → `StrEnum` + drop two PLR0913 noqas | #316, #318 | ✅ closed by PR keywords |

## Issue Resolution Verification

### Stale-open (resolved by merged PR but never closed) — 4 items

These issues had `(#NNN)` in the resolving PR's *title* but no `Closes #N`
keyword in the PR body, so GitHub did not auto-close them. Closed this
grooming session with referencing comments + `state_reason: completed`.

| Issue | Resolved by | Action |
| ----- | ----------- | ------ |
| #193 — TypeScript Prettier scope (P1) | PR #287 (+ #295 follow-up) | ✅ closed with comment |
| #280 — Pin Black version             | PR #289                    | ✅ closed with comment |
| #281 — pyupgrade/refurb 3.14 compat  | PR #290                    | ✅ closed with comment |
| #285 — Deduplicate languages         | PR #288                    | ✅ closed with comment |

### Auto-closed correctly via PR `Closes #N` keywords — 4 items

No grooming action needed; verified state.

| Issue | Resolved by | Status |
| ----- | ----------- | ------ |
| #316 — drop PLR0913 noqas            | PR #324 | ✅ closed completed |
| #317 — path-containment guard        | PR #323 | ✅ closed completed |
| #318 — `ResumeStatus` → `StrEnum`    | PR #324 | ✅ closed completed |
| #319 — `--wait` no-op on first-run   | PR #323 | ✅ closed completed |

### Closed prior to this grooming

| Issue | Resolved by | Note |
| ----- | ----------- | ---- |
| #269 — language-specific setup instructions | PR #279 | already closed |
| #270 — dependabot in claude-review          | PR #278 | already closed |
| #271 — gh workflow scope                    | manual  | already closed |
| #302 — pip CVE-2026-3219 tracking           | PR #301 | already closed |
| #306 — migrate ContentTuner tests off `create_autospec` | PR #305 | already closed |

## New Issues Filed

Two follow-ups opened this grooming for work surfaced during the
Phase-6 sprint:

### #325 — polish: Phase 6c review nits

**Labels**: `documentation`, `tech-debt`, `good-first-issue`

Rollup of the three explicitly-non-blocking polish items the PR #324
round-1 reviewer flagged:

1. Stale comment on `_BATCH_OUTCOME_STATIC` in `cli.py` — predates
   the `match` refactor; references a "silent drop" risk that no
   longer exists.
2. `BatchPersistenceContext` docstring — could call out the mutable
   `state` field (`frozen=True` prevents reassignment, not mutation).
3. `_recent_submitted_at()` helper — could future-anchor with
   `+ timedelta(hours=1)` to eliminate a theoretical (extremely
   unlikely) wall-time race.

### #326 — refactor(cli): extend `_EnhanceProjectContext` to drop 4 more PLR0913 noqas

**Labels**: `enhancement`, `tech-debt`, `refactor`

Issue #316 deferred a wider-scope context-dataclass refactor. After
PR #324, four module-private functions in `cli.py` still carry
`# noqa: PLR0913` directives that the same `_EnhanceProjectContext`
could clean up:

- `_enhance_claude_md`
- `_enhance_subagents`
- `_dispatch_enhance_targets`
- `_run_enhance_pipeline`

Top-level `init` and `enhance` typer commands stay flagged — their
parameter lists are user-facing CLI interfaces, not glue.

## Out-of-Scope Observations (Not Filed)

### Wake-mechanism reliability (`subscribe_pr_activity`)

During this conversation, `mcp__github__subscribe_pr_activity` dropped
events silently on PRs #321 round-2 (`COMMENTS` verdict) and #322
round-1 (`LGTM` verdict + iteration-trigger comment). Both events
were within seconds of subscribing and within the deliverable set per
the documented contract. Per user direction
(*"Let's skip this skill business. Maybe Anthropic will make a change
in Claude code on mobile that keeps the harness wakeable by events
from GH"*), not filing as a project issue — it's a Claude Code /
MCP-server reliability concern, not a `start_green_stay_green`
project concern.

### Pre-existing time-bomb test fixtures (fixed retroactively in PR #324)

Eight tests in `tests/unit/ai/test_batch_dispatch.py` had a hard-coded
`submitted_at="2026-05-09T21:00:00+00:00"` that flipped from "live"
to "expired" at wall-clock `2026-05-10T21:00:00`. Confirmed
independently broken on `main` HEAD before PR #324. Fixed in-place
by PR #324 (new `_recent_submitted_at()` helper); no retroactive
issue filed since the fix is already in `main`.

## Statistics

| Metric                          | Value |
| ------------------------------- | ----- |
| PRs analyzed                    | 38    |
| Issues closed this session      | 4     |
| Issues opened this session      | 2     |
| Issues already closed correctly | 9     |
| Duplicate issues found          | 0     |
| Open backlog before grooming    | 16    |
| Open backlog after grooming     | 14    |

## Backlog Health

### Before grooming

- 16 open issues; 4 of them resolved by code already on `main` but
  never marked closed (`#193`, `#280`, `#281`, `#285`).
- Roadmap PRs (#308–#315) merged without a parent tracking issue —
  expected for a roadmap-driven workstream documented in
  `plans/2026-05-03-claude-init-optimization-roadmap.md`.
- No follow-up issues yet for PR #324 polish items.

### After grooming

- 14 open issues. 0 known-resolved-but-open issues remain.
- 2 new, well-scoped follow-up issues (#325 polish nit rollup, #326
  wider context refactor) capture deferred work.
- Phase-6 follow-up issues (#316–#319) all closed and the wave is
  done — `v1.0.0` shipped via PR #321.

### Health snapshot — open issues by theme

| Theme                          | Count | Notes |
| ------------------------------ | ----- | ----- |
| Tech-debt / refactor           | 4     | #307, #325, #326, #283 |
| Dashboard / metrics            | 4     | #154, #159, #206, #217 |
| Generators (multi-language)    | 2     | #131, #200 |
| Generators bugs                | 0     | (#193 cleared) |
| Setup-instructions polish      | 2     | #283, #284 |
| Performance                    | 1     | #256 |
| Release readiness              | 1     | #152 |
| CI/deps                        | 0     | (#280, #281, #282 — wait, #282 still open: actions Node 24) |

Correcting the CI/deps count: #282 (`ci(deps): update actions to
Node.js 24 compatible versions`) is still open and unresolved by the
recent dependabot wave — node-action-runtime work. Not a regression;
genuine outstanding item.

## Recommendations

Nothing blocking. Suggested next priorities in order of payoff:

1. **#325 polish nits** — tiny single-PR rollup; clears the PR #324
   round-1 review noise. `good-first-issue`.
2. **#326 wider context refactor** — 30-min surgical refactor;
   drops 4 more `noqa: PLR0913` directives. Pairs naturally with #325.
3. **#282 Node.js 24 actions** — keeps CI on supported runtime; small
   YAML diff.
4. **#152 v1.0.0 release readiness manual testing plan** — now that
   `v1.0.0` shipped via PR #321, run the manual testing plan and
   close.

Items beyond these are enhancement-flavoured and can be triaged in
the next grooming session.

---

**Session metadata**

- Date: 2026-05-10
- Performed by: Claude Code (via `/backlog-grooming` skill)
- Tools: `mcp__github__*` only (no `gh` CLI; per project instructions)
- Last grooming: 2026-04-10 (`plan/2026-04-10_BACKLOG_GROOMING.md`)
