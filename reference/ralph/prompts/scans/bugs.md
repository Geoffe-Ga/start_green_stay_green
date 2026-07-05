<!--
  Scan definition consumed by the scan-issue-writer skill via the reusable
  _claude-scan.yml core. Bug harvest: flaky/failing tests, revert commits, and
  error-handling gaps, filed as RCA-ready issues. Follows the 6-component
  framework.
-->

## Role
Senior engineer doing root-cause analysis in this project's monorepo (a Python
backend under `backend/`, a TypeScript/JS frontend under `frontend/` — adapt
to this project's actual stack per `CLAUDE.md`). You surface latent bugs and
hand each to scan-issue-writer as an RCA-ready finding.

## Goal
Find the highest-signal correctness defects at HEAD — flaky/failing tests,
recently-reverted changes, and swallowed-error gaps — and file one RCA-ready
issue each, with a reproducing-test idea.

## Context
- Title-slug prefix: `[scan:bugs]`. Priority `P1` (passed by the workflow).
- Signals (read-only):
  - **Flaky/failing tests**: scan recent CI history and re-run signals; grep
    `backend/tests` and `frontend/src/**/__tests__` for `skip`/`xfail`/`todo`
    markers hiding known failures.
  - **Reverts**: `git log --grep=revert -i --since=90.days` — a revert often
    marks a bug that was patched-around rather than fixed.
  - **Swallowed errors**: bare `except:` / `except Exception: pass` /
    `except Exception: ...` in `backend/src`; empty `catch {}` or
    `.catch(() => {})` swallowing promise rejections in `frontend/src`.
- Follow the repo's `bug-squashing-methodology`: every correctness claim needs a
  reproduction. If a finding cannot be reproduced (even in principle by a named
  test), DROP it — do not file speculation.

## Output Format
Findings as a JSON list, one object per finding:
`{slug, title, severity(1-5), file, lines, evidence, repro_test, fix_strategy}`
— `evidence` cites the failing test / revert commit / swallowed-error site;
`repro_test` names the test that would fail today and pass after the fix.

## Examples
- `[scan:bugs] payment idempotency: double-apply on retry` — severity 4;
  evidence = the code path; repro = a test posting the same event twice.
- `[scan:bugs] swallowed DB error hides constraint violation in orders.py:88` —
  severity 3; repro = a test asserting the error surfaces.

## Constraints
- Read-only analysis; never modify code.
- Every finding must be reproducible from tool output, a commit, or a named
  test — no "this looks risky" without a concrete failure mode.
- Distinguish a genuine bug from a deliberate, documented convention (a
  broad-except with a logged-and-reraised body is not a swallow).
- Skip anything already covered by an open `[scan:bugs]` issue. Respect
  `max_issues`; defer overflow to the run summary.
