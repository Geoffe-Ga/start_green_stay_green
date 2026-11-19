---
name: flare
description: >-
  Fast, one-shot bug or feature reporting: research the repo, write a
  world-class QA/PM ticket, and file it to GitHub Issues with Ralph-ready
  labels in a single turn. Use when the user says "flare this", "file a bug",
  "report this", "open an issue for X", "/flare", or hands you a short bug/idea
  description and wants it turned into a ticket right now. Grounds the report
  in real code (file:line, snippets, git history), applies the 6-component
  prompt-engineering framework so the ticket is directly consumable by the
  Ralph agent fleet, decomposes oversized asks into an epic + sub-issues, and
  dedupes against existing issues before creating anything. Do NOT use for
  automated tool-output-driven maintenance scans (use scan-issue-writer), for
  triaging/closing/grooming the existing backlog (use backlog-grooming), for
  the root-cause-analysis and TDD fix cycle once an issue already exists (use
  bug-squashing-methodology), or for reviewing an open PR's diff (use
  comprehensive-pr-review).
metadata:
  author: Geoff
  version: 1.0.0
---

# Flare

Turn a quick verbal bug/feature report into a filed, agent-ready GitHub issue
— fast. The whole point of `flare` is speed: the user says one sentence, you
do the legwork, an issue lands with a URL. Don't make the user re-explain
what a competent repo search would have told you.

## Instructions

### Step 1 — Capture the report, don't interrogate

Take what the user gave you at face value. Only ask a clarifying question if
something is genuinely blocking (e.g. "the toggle" could mean one of three
different toggles and repo research doesn't disambiguate it). Otherwise:
proceed on your best interpretation and record any assumption explicitly in
the issue body's Context section — an assumption written down is fine; a
silent guess is not, and a blocking question defeats the "fast" promise.

### Step 2 — Repo research (this is what makes the ticket world-class)

Before writing a word of the ticket, ground it in the actual codebase:

- **Locate the code**: Grep/Glob for the feature or symptom (component name,
  route, error string). Identify the exact file(s):line(s) involved.
- **Read the current behavior**: Open the relevant handler/component/model
  and understand what it actually does today, not what the user assumes it
  does.
- **Check history**: `git log -p --follow -- <file>` or `git blame` on the
  suspect lines — was this recently changed? Is there a regression window?
- **Check test coverage**: Does a test already cover this path? If yes and it
  passes, that's evidence for the Context section (or a sign the bug is in
  an untested branch). If no, note the gap — Ralph will need to write one.
- **Dedupe**: Search before you draft, not after.
  ```bash
  gh issue list --search "<keywords>" --state all --limit 20
  ```
  If `gh` isn't available in this session, use `mcp__github__search_issues`
  or `mcp__github__list_issues` instead. Exact or near-exact match → stop,
  report the existing issue number to the user instead of filing a duplicate
  (or add a comment with fresh evidence if the finding has new information).

Spend real effort here — this step is what separates a `flare` ticket from a
one-line vague complaint that sits unpicked-but-unfinished forever.

### Step 3 — Classify

Decide, from the evidence gathered in Step 2:

- **Type**: `bug` (behavior contradicts spec/expectation) or `feature`
  (net-new capability, including enhancements to existing behavior).
- **Severity / priority** (bugs — map to Ralph's priority tiers, see
  `references/label-guide.md`):
  - `P0` — crash, data loss, security hole, broken auth, prod-down.
  - `P1` — a core user flow is broken with no workaround.
  - `P2` — degraded behavior, workaround exists, or a well-scoped feature.
  - `P3` — cosmetic, minor, or nice-to-have.
  - **Backlog inflow moratorium**: if the repo's `CLAUDE.md` declares one
    (e.g. "no new issues about the development loop until X ships"),
    findings in its excluded scope — typically the agent loop itself
    (`scripts/ralph/**` if present), `.github/workflows/**`,
    scan/lint/pre-commit tooling, dependency hygiene — are filed ONLY when
    they break a required check on `main` or block a merge (then use the
    tiers above as normal). Otherwise stop: report the finding to the user
    instead of filing.
- **Size**: Estimate rough LoC/complexity from what Step 2 found. If it looks
  like it exceeds ~300 LoC or spans more than one clearly separable concern
  (e.g. "backend model + API + two screens"), it needs decomposition — see
  Step 4b and `references/decomposition.md`. A single well-scoped bug fix or
  small feature stays one issue.

### Step 4a — Draft a single issue

Fill `references/report-template.md` completely — it follows the
6-component framework (Role / Goal / Context / Output Format / Examples /
Constraints) from the prompt-engineering skill, so an agent (Ralph or any
other worker) can pick it straight off the backlog. No placeholders left unfilled. The
Context section must cite real `file:line` and include an actual code
snippet from Step 2 — not a paraphrase.

For a **bug**, the Goal is the fix, and Context must include: exact
reproduction steps, expected vs. actual behavior, and environment info (only
if given or inferable — don't invent versions/platforms).

For a **feature**, the Goal is the capability, and Context must include: the
user story ("as a ..., I want ..., so that ..."), acceptance criteria as a
checklist, and — if the request implies a design or UX choice — the smallest
reasonable default so Ralph isn't blocked waiting on a decision.

### Step 4b — Decompose oversized asks into an epic

If Step 3 flagged this as too big for one issue, follow
`references/decomposition.md`: create one epic issue (context + the overall
goal, labeled with both the bare `epic` label AND `epic:<slug>` — the bare
`epic` token is what actually keeps it out of the picker; `epic:<slug>`
alone does not, since a label-driven picker such as
`scripts/ralph/pick-next.sh` matches labels exactly, not by prefix)
and 2–5 atomized sub-issues (~300 LoC each, each independently agent-ready,
labeled `epic:<slug>` only — never the bare `epic` label, or they'd be
excluded too), linked to the epic via `mcp__github__sub_issue_write` (or
`gh issue edit --add-...` sub-issue linking where available). Mark
sub-issues `parallelizable` only if Step 2's research confirms they don't
touch overlapping files/tables.

### Step 5 — Label per the picker's vocabulary

See `references/label-guide.md` for the full set (written for the Ralph
picker; if the repo uses different readiness or priority labels, map onto
whatever `gh label list` shows). At minimum apply:

- Type: `bug` or `feature`
- Priority: `P0`–`P3`
- Readiness: `agent-ready` if every template section is filled with real
  content, otherwise `needs-spec`. In a repo running the Ralph fleet,
  `scripts/ralph/pick-next.sh` REQUIRES `agent-ready` by default, so this is
  the label that decides whether the fleet ever sees the issue: without it nothing is auto-picked, and an incomplete issue stays out
  by simply not earning it. `needs-triage` decides nothing either way — see
  `references/label-guide.md`.
- `epic:<slug>` on the epic issue and all its sub-issues, if decomposed, PLUS
  the bare `epic` label on the epic issue only (see Step 4b — `epic:<slug>`
  alone does not exclude it from the picker; the bare `epic` token does)
- `solo` only if the change cannot safely run alongside parallel Ralph
  workers (e.g. touches a migration or shared config every other issue also
  touches)

Check `gh label list` first — reuse an existing label; only create a new one
if nothing fits, per this repo's git-workflow skill. There's no bulk
label-listing MCP tool; if `gh` isn't available, use
`mcp__github__get_label` to check a specific candidate name, or infer the
label set from labels already attached to issues returned by
`mcp__github__list_issues`.

### Step 6 — File it

```bash
gh issue create --title "type(scope): specific, searchable title" \
  --body-file /tmp/flare-issue.md \
  --label "bug,P1,agent-ready"
```

If `gh` isn't available, use `mcp__github__issue_write` (action `create`)
with the same title/body/labels. Title format: conventional-commit-style
`type(scope): what's actually wrong or wanted` — specific enough that a
title-only skim tells a maintainer what happened, not just "bug in settings".

### Step 7 — Report back, fast

Reply with the issue number, URL, and a one-line summary of what you filed
(and, if decomposed, the epic URL plus each sub-issue URL). Nothing else —
the user asked for speed, not a recap of your research process.

## Examples

### Example 1 — Quick bug report
User: "flare — the habit streak resets to 0 even when I complete it same day"

1. Grep for streak logic → `src/domain/streaks.py:40-78`, find the
   date-comparison bug (naive `date.today()` vs stored UTC timestamp).
   Confirm no timezone test exists.
2. Dedupe search: no match.
3. Classify: `bug`, `P1` (core flow broken, no workaround), single issue.
4. Draft with Context citing the exact comparison at `streaks.py:63`,
   snippet included, repro steps, expected vs actual.
5. Label `bug,P1,agent-ready`.
6. File, reply with issue URL in one line.

### Example 2 — Oversized feature ask
User: "flare — add a leaderboard for weekly streaks across all users"

Research shows this needs a new backend aggregation endpoint, a new DB
query/index, a new frontend screen, and navigation wiring — four separable
concerns, no existing scaffolding. Create epic `epic:weekly-leaderboard`
("Weekly streak leaderboard") plus four sub-issues (backend aggregation
endpoint, frontend leaderboard screen, navigation entry, opt-out privacy
setting), each `agent-ready`, each labeled `epic:weekly-leaderboard`, backend
and frontend sub-issues marked `parallelizable` since they don't share files.

### Example 3 — Duplicate caught
User: "flare — journal entries lose formatting on save"

Dedupe search turns up open issue #212 with the identical repro. Reply with
"Already tracked in #212 — added a comment with today's reproduction" instead
of filing a new issue.

## Troubleshooting

### Can't tell if it's a bug or a feature
If current behavior matches what the code was clearly designed to do, but
the user wants it to do something else, it's a `feature` (or `enhancement`),
not a `bug`. Say so in the ticket rather than mislabeling for urgency.

### Repo research turns up nothing
If Grep/Glob find no related code at all (genuinely new capability, not a
missed regression), say so plainly in Context instead of forcing an
in-code reference — don't fabricate a file:line.

### `gh` is unavailable or unauthenticated
Use the GitHub MCP equivalents throughout: `mcp__github__search_issues` /
`mcp__github__list_issues` for dedupe, `mcp__github__get_label` to check a
label, `mcp__github__issue_write` to file, `mcp__github__sub_issue_write` to
link sub-issues. If neither works, write the finished body to a file and
hand the user the path plus the exact `gh issue create` command to run.

### User's report doesn't reproduce
State that in Context: what you tried, what you expected, what actually
happened when you checked. File it as `needs-spec` (not `agent-ready`) rather
than guessing at a root cause you didn't verify — withholding `agent-ready` is
what keeps the picker from auto-assigning it, and `needs-spec` says why.
