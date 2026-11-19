<!--
  Canonical issue body template for `flare`-filed reports.

  Follows the 6-component prompt framework (Role / Goal / Context / Output
  Format / Examples / Constraints; see the prompt-engineering skill) because
  every agent-ready issue IS a prompt: an agent worker consumes it directly. An issue missing any
  component gets `needs-spec` instead of `agent-ready` — `needs-spec` is the
  label the Ralph picker's default exclude list actually honors (see
  `flare`'s `references/label-guide.md`).

  Replace every [bracketed] placeholder. Delete whichever of the Bug/Feature
  Context blocks doesn't apply. Leave no placeholder behind.
-->

## Role
You are a [senior backend | senior frontend | full-stack] engineer working in
this codebase, following its existing conventions (TDD via stay-green, the
repo's quality-gate script, its coverage thresholds as stated in CLAUDE.md,
zero lint/type suppressions).

## Goal
[One sentence. Specific, measurable, verifiable. e.g. "Fix streak calculation
so a habit completed same-day (in the user's local timezone) does not reset
the streak to 0, verified by a timezone-boundary test."]

## Context

<!-- BUG reports: fill this block -->
- **Steps to reproduce**:
  1. [Exact step]
  2. [Exact step]
  3. [Observed result]
- **Expected behavior**: [What should happen]
- **Actual behavior**: [What happens instead]
- **Environment**: [Only what was given/inferable — platform, version, data
  state. Do not invent details the report didn't provide.]
- **Severity/impact**: [Who's affected, how badly, any workaround]

<!-- FEATURE reports: fill this block instead -->
- **User story**: As a [user type], I want [capability], so that [benefit].
- **Acceptance criteria**:
  - [ ] [Observable, testable criterion]
  - [ ] [Observable, testable criterion]
  - [ ] [Observable, testable criterion]
- **Design defaults**: [Smallest reasonable default for any open UX/design
  choice, so the implementer isn't blocked — note it's a default, not a mandate]

<!-- Both: always fill this -->
- **File(s)**: `path/to/file.py:120-164`
- **Current behavior in code** (from repo research):
  ```
  [Actual snippet from the file, not a paraphrase]
  ```
- **Relevant history**: [Recent commit/PR that touched this code, if any —
  `git log` or `git blame` findings]
- **Test coverage**: [Existing test that covers/misses this path, file:line]
- **Related**: [Links to related issues/PRs found during dedupe search]
- **Assumptions made**: [Any interpretation you made because the original
  report was ambiguous and asking would have slowed filing down]

## Output Format
A single PR that: (1) adds a failing test first, (2) makes it pass, (3)
passes the repo's quality gate (e.g. `./scripts/check-all.sh`, or the
per-side variant for each side touched in a monorepo) — and (4) references
this issue with "Closes #N".

## Examples
[One concrete before/after sketch grounded in the Context snippet above — the
current buggy/missing behavior vs. the fixed/added version. 5–15 lines.
Enough to disambiguate, not a full spec.]

## Constraints
- Do not change public API signatures unless the Goal requires it
- No lint/type suppressions (max-quality-no-shortcuts): fix root causes
- Scope: this issue only — file follow-up issues for adjacent problems found
  during research instead of scope-creeping this one
- If the finding no longer reproduces at HEAD, close this issue with a
  comment explaining what changed instead of forcing a PR
