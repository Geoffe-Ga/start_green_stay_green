# Backlog Grooming — 2026-03-22

## PRs Analyzed

| PR | Title | Merged | Issues Closed |
|----|-------|--------|---------------|
| #259 | Multi-language --language support | 2026-03-22 | #254 |
| #258 | YAML-aware pre-commit merge | 2026-03-22 | #253 |
| #257 | --force and --interactive flags | 2026-03-19 | #252 |
| #255 | Additive green init (skip existing) | 2026-03-19 | #251 |
| #247 | Remove docs.yml and .readthedocs.yml | 2026-03-11 | — |
| #236 | Security hardening audit | 2026-03-11 | #220-#235 |
| #219 | Remove interrogate dependency | 2026-03-11 | #218 |

## Issues Closed This Session

| Issue | Title | Resolution |
|-------|-------|------------|
| #250 | Epic: additive green init | All 4 tracers merged |
| #221-#235 | 15 security hardening issues | Resolved in PR #236, not auto-closed |
| #203 | pip-audit vulnerabilities | Fixed in PR #255 (black upgrade, authlib removal) |

**Total closed: 17 issues**

## Remaining Open Issues (11)

### Active Work
- **#256** — perf(ci): remove --html from coverage.sh (P2, from epic)
- **#193** — bug: TypeScript Prettier formatting OOB (P1)

### Dashboard/Metrics
- **#217** — Re-add Mutation Score and Doc Coverage tiles
- **#206** — Unify threshold computation convention
- **#159** — Add CI Status metric to dashboard
- **#154** — Add Pre-Commit Status metric to dashboard

### Cleanup
- **#202** — Clean up planning/cruft files from project root
- **#201** — Move RCA files to docs/rca/

### Feature Work
- **#200** — Add pip-audit suppression to generated security.sh
- **#131** — Update templates from self-hosting learnings
- **#152** — v1.0.0 release readiness manual testing

## Backlog Health

- **Before**: 28 open issues (17 stale/resolved)
- **After**: 11 open issues (all valid)
- **Improvement**: 60% reduction in open issues
