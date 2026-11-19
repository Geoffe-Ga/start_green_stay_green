# Label Quick Reference

How a label-driven issue picker interprets labels. The rules below are the
Ralph fleet's (`scripts/ralph/pick-next.sh`, when the repo has it); if the
repo has no picker, the same vocabulary still tells a human triager what is
ready. When `scripts/ralph/pick-next.sh` exists, its header is the canonical
statement of these rules and wins over this summary. Always run `gh label list` first and reuse an existing label — only
create a new one if nothing fits. There's no bulk label-listing MCP tool; if
`gh` isn't available, use `mcp__github__get_label` to check a specific
candidate name (`mcp__github__list_issue_types` is GitHub's separate "Issue
Types" feature, not labels — it won't help here).

## Type

- `bug` — behavior contradicts spec/expectation
- `feature` — net-new capability or enhancement to existing behavior

## Priority (either vocabulary is honored — prefer the short form)

| Short | Long form | Tier | Use for |
|-------|-----------|------|---------|
| `P0`  | `priority-critical` | 0 | Crash, data loss, security hole, broken auth, prod-down |
| `P1`  | `priority-high`     | 1 | Core user flow broken, no workaround |
| `P2`  | `priority-medium`   | 2 | Degraded behavior with a workaround; well-scoped feature |
| `P3`  | `priority-low`      | 3 | Cosmetic, minor, nice-to-have |

An issue with no priority label defaults to tier 1 (P1) in the picker — so
always apply one explicitly rather than relying on the default.

## Readiness

- `agent-ready` — every template section (`references/report-template.md`)
  is filled with real content; the picker can hand this straight to an agent
  worker. **This label is REQUIRED for pickup.** `pick-next.sh` requires it by
  default (`RALPH_REQUIRE_LABELS`), so an issue without it is invisible to the
  fleet however urgent it looks. Filing without it is filing for a human.
- `needs-spec` — something is missing (reproduction failed, ambiguous scope,
  unverifiable claim). Apply it, and leave `agent-ready` off. It is also in the
  picker's default exclude set, so it stops pickup twice over. A human or a
  grooming pass finishes it, then relabels `agent-ready`.
- `needs-triage` — informational only. It neither admits nor excludes: an issue
  is pickable if it carries `agent-ready` and no excluded label, whatever else
  is on it. Don't rely on `needs-triage` to signal readiness in either
  direction.

## Decomposition

- `epic:<slug>` — applied to an epic issue and every one of its sub-issues.
  The picker's same-epic guard prevents two sub-issues of the same epic from
  running in parallel unless also labeled `parallelizable`.
- `epic` (bare, on the epic issue ONLY, in addition to `epic:<slug>`) — this
  is the literal token `pick-next.sh`'s default `RALPH_EXCLUDE_LABELS`
  matches; the picker's label filtering is exact-match, not prefix-match, so
  `epic:<slug>` alone does NOT trigger the exclusion. Without the bare
  `epic` label, an epic issue is fully pickable despite not being directly
  implementable. Sub-issues must NOT carry the bare `epic` label — only
  `epic:<slug>` — or they'd be excluded too.
- `parallelizable` — overrides the same-epic guard; only apply when repo
  research (Step 2 in SKILL.md) confirms the sub-issues don't touch
  overlapping files, tables, or migrations.

## Coordination

- `solo` — issue must run alone, never alongside any other active worker.
  Use sparingly: migrations, shared-config changes, anything where parallel
  writes would conflict.
- `in-progress` — set by the fleet when work starts; `flare` should never
  apply this manually.

## Labels flare should never apply

`wontfix`, `duplicate`, `invalid`, `question`, `blocked`, `future-work`,
`do-not-auto-merge` — these are triage/lifecycle labels applied by humans or
the backlog-grooming skill after the fact, not at filing time.
