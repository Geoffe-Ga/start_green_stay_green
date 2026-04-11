# Backlog Grooming: 2026-04-10

## Scope

Systematic review of recent merged PRs to verify issue closure status,
identify gaps, and file follow-up issues for work surfaced during the
2026-04-07 through 2026-04-11 PR sprint (doc cleanup, dependabot batch
merge, setup-instructions feature).

## PRs Analyzed

Last 20 merged PRs reviewed (#236 through #279):

| PR | Title | Issues Closed | Status |
|---|---|---|---|
| #279 | feat(cli): add language-specific setup instructions | #269 | ✅ verified |
| #278 | fix(ci): allow dependabot in claude-review | #270 | ✅ verified |
| #268 | chore(docs): move RCA files, remove root cruft | #201, #202 | ✅ verified |
| #267 | deps: pytest <10 | — | dependabot |
| #266 | fix(cli): lazy API key source evaluation | #265 | ✅ verified |
| #264 | fix(cli): auto-detect language scripts | #262 | ✅ verified |
| #263 | fix(cli): comma-sep --language, script subdirs | #261, #262 | ✅ verified |
| #260 | docs: additive init epic | — | docs only |
| #259 | feat(cli): multi-language --language | #254 | ✅ verified |
| #258 | feat(generators): YAML-aware pre-commit merge | #253 | ✅ verified |
| #257 | feat(cli): --force and --interactive flags | #252 | ✅ verified |
| #255 | feat(cli): additive init | #251 | ✅ verified |
| #249 | deps: dependency-review-action 3→4 | — | dependabot |
| #248 | deps: download-artifact 4→8 | — | dependabot |
| #247 | fix(ci): remove docs.yml added in error | — | — |
| #246 | deps: keyring <26 | — | dependabot |
| #245 | deps: pytest-randomly <5 | — | dependabot |
| #243 | deps: isort <9 | — | dependabot |
| #242 | deps: refurb <3 | — | dependabot |
| #241 | deps: setup-python 4→6 | — | dependabot |
| #240 | deps: upload-artifact 4→7 | — | dependabot |
| #237 | deps: peaceiris/actions-gh-pages 3→4 | — | dependabot |
| #236 | sec: comprehensive security hardening | #220-#235 (16 issues) | ✅ verified |

## Issue Resolution Verification

All 25 issues referenced in the last 20 merged PRs are properly closed:
- #201, #202, #220-#235, #251, #252, #253, #254, #261, #262, #265, #269, #270, #271

No dangling open issues referenced in merged PRs. ✅

## Gaps Identified — Follow-up Issues Created

Five issues filed for work or concerns surfaced during this PR sprint
that didn't have existing tracking:

| Issue | Title | Source |
|---|---|---|
| #280 | chore(deps): pin Black version to match CI | PR #279 review, extra commit needed |
| #281 | chore(deps): fix pyupgrade/refurb Python 3.14 incompat | Every pre-commit run locally |
| #282 | ci(deps): update actions to Node.js 24 | Every CI run warning |
| #283 | refactor(tests): use pytest.mark.parametrize | PR #279 review |
| #284 | feat(cli): handle non-bash shells in setup instructions | PR #279 review |
| #285 | fix(cli): deduplicate languages in _get_setup_instructions | PR #279 review |

## Statistics

- **PRs analyzed**: 20
- **Issues verified closed**: 25
- **Issues prematurely closed or reopened**: 0
- **Duplicate issues found**: 0
- **New issues created**: 6 (#280–#285)
- **Open issues before grooming**: 10
- **Open issues after grooming**: 15 (3 closed this session: #269, #270, #271; 6 new)

## Open Backlog Snapshot (2026-04-10)

Remaining open issues by priority:

**Bugs (5):**
- #193 (P1-high): Generated TypeScript projects fail Prettier out of the box
- #280: Pin Black version to match CI
- #281: Fix pyupgrade/refurb Python 3.14 incompat
- #282: Update actions to Node.js 24
- #285: Dedup languages in _get_setup_instructions

**Enhancements (10):**
- #131: Update templates from self-hosting
- #152: v1.0.0 release readiness manual testing
- #154, #159: Pre-Commit/CI status dashboard tiles
- #200: pip-audit known-vulnerability suppression
- #206: Unify metrics threshold computation
- #217: Re-add mutation/doc coverage dashboard tiles
- #256: Remove --html from coverage.sh in CI
- #283: pytest.mark.parametrize refactor
- #284: Non-bash shell support in setup instructions

## Observations

1. **Dependabot merge backlog cleared**: The 10 open dependabot PRs that
   had been accumulating were all merged this session (after resolving
   the `workflow` scope auth issue via `gh auth refresh -s workflow`).
2. **Security-critical vulnerabilities fixed**: CVE-2026-32274 in Black
   is now patched (via #242/requirements update), so Bandit/pip-audit
   hooks pass cleanly.
3. **Pre-commit hook health**: 2 of ~30 hooks are broken on Python 3.14
   (pyupgrade, refurb) — filed as #281. Not blocking CI (runs on 3.11/3.12)
   but creates friction for local dev on 3.14.
4. **Claude review coverage improved**: #278 allows dependabot PRs to be
   reviewed automatically, closing a gap where the 10 dependabot PRs had
   been mechanically failing the required `claude-review` check.

## Next Recommended Actions

1. Fix pyupgrade/refurb (#281) — unblocks local pre-commit on Python 3.14
2. Pin Black version (#280) — prevents recurrence of CI/local drift
3. Audit Node.js 20 actions (#282) — June 2026 deadline
4. Address #193 (P1 TypeScript Prettier bug) — has been open since 2026-02-13
