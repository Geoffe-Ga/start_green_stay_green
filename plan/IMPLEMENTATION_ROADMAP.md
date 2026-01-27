# Start Green Stay Green - Implementation Roadmap

**Last Updated:** 2026-01-27
**Status:** Active Development - Final Phase
**Current Phase:** Phase 4 (Polish & Documentation)

---

## Table of Contents

- [Overview](#overview)
- [Current Status](#current-status)
- [Critical Path Analysis](#critical-path-analysis)
- [Implementation Phases](#implementation-phases)
  - [Phase 1: Quality Foundation](#phase-1-quality-foundation-weeks-1-2) - COMPLETE
  - [Phase 2: Content Generators](#phase-2-content-generators-weeks-3-4) - COMPLETE
  - [Phase 3: CLI & Integration](#phase-3-cli--integration-weeks-5-6) - COMPLETE
  - [Phase 4: Polish & Documentation](#phase-4-polish--documentation-week-7) - IN PROGRESS
- [Issue Dependency Graph](#issue-dependency-graph)
- [Risk Management](#risk-management)
- [Success Metrics](#success-metrics)

---

## Overview

This document outlines the strategic approach to completing the Start Green Stay Green project. The roadmap is organized into 4 phases, each building on the previous phase's deliverables.

**Project Goal:** Build a meta-tool that generates quality-controlled, AI-ready repositories with enterprise-grade quality controls pre-configured.

**Philosophy:** Maximum Quality Engineering - ship green on all checks with zero outstanding issues.

---

## Current Status

### ✅ Completed Work

#### Core AI Infrastructure (Phase 1)
- ✅ AIOrchestrator implemented with retry logic
- ✅ Prompt management system (manager.py - 86.2% mutation score)
- ✅ Token usage tracking
- ✅ Error handling and validation
- ✅ Claude Code Review workflow (issues #36, #37, #81, #82)
- ✅ Content Tuner (tuner.py - 81.7% mutation score)

#### Quality Infrastructure (Phase 1)
- ✅ Complete pre-commit hooks (32 hooks)
- ✅ CI pipeline with all checks
- ✅ Scripts for formatting, linting, testing
- ✅ Coverage tracking (97%+)
- ✅ Security scanning (bandit, safety, detect-secrets)
- ✅ 3-Gate Workflow System (local, CI, code review)
- ✅ Mutation testing moved to periodic quality check (not continuous)

#### Reference Assets (Phase 1) - Issue #22
- ✅ MAXIMUM_QUALITY_ENGINEERING.md
- ✅ Reference CLAUDE.md
- ✅ Reference scripts
- ✅ Reference workflows (stay-green.md)
- ✅ All unit tests for reference file loading

#### Skills Content (Phase 1) - Issue #23
- ✅ vibe.md - Coding style and tone
- ✅ concurrency.md - Async/threading patterns
- ✅ documentation.md - Documentation standards
- ✅ error-handling.md - Error handling patterns
- ✅ security.md - Security best practices
- ✅ testing.md - Testing patterns
- ✅ mutation-testing.md - Mutation testing guide

#### Subagent Profiles (Phase 1) - Issue #24
- ✅ dependency-checker.md - Package verification subagent
- ✅ Complete subagent hierarchy (Level 0-5)
- ✅ Agent templates for all levels
- ✅ Delegation rules and guidelines
- ✅ Verification checklists

#### Content Generators (Phase 2)
- ✅ Issue #9: Tuning Pass System (tuner.py - 81.7%)
- ✅ Issue #13: Skills Generator (skills.py - 85.5%)
- ✅ Issue #14: Subagents Generator (subagents.py)
- ✅ Issue #15: CLAUDE.md Generator (claude_md.py)
- ✅ Issue #17: Metrics Dashboard (metrics.py)
- ✅ Issue #18: Architecture Enforcement (architecture.py)
- ✅ Base generator infrastructure (base.py)
- ✅ Pre-commit generator (precommit.py)
- ✅ CI generator (ci.py)
- ✅ Scripts generator (scripts.py)

#### CLI & Integration (Phase 3)
- ✅ Issue #19: CLI Framework (Typer + Rich)
- ✅ Issue #20: Init Command (full interactive flow)
- ✅ Issue #21: GitHub Integration (808 lines, 45 tests)
  - GitHubClient class with full API coverage
  - Repository creation, branch protection
  - Issue creation from SPEC.md parsing
  - Label and milestone management
  - Secure token handling with retry logic
- ✅ Issue #16: GitHub Actions Review (github_actions.py)

#### Credentials & Security
- ✅ Keyring integration (credentials.py - 94.1% mutation score)
- ✅ Secure API key management
- ✅ Environment variable fallback

### 🔄 Current Work

#### Issue #62: Mutation Testing Coverage (cli.py Focus)

**Status**: cli.py at 48.9%, targeting 80%

**Mutation Score Summary**:
| File | Score | Status |
|------|-------|--------|
| cli.py | 48.9% | ❌ CRITICAL - In Progress |
| credentials.py | 94.1% | ✅ EXCELLENT |
| tuner.py | 81.7% | ✅ PASSING |
| skills.py | 85.5% | ✅ PASSING |
| manager.py | 86.2% | ✅ PASSING |

**Plan**: Kill ~72 of 118 surviving mutants in cli.py through:
1. Validation logic tests (project name, output dir)
2. Parameter resolution tests
3. API key handling tests
4. Init command integration tests

**Estimated Effort**: 7-10 hours of focused test development

### 📋 Remaining Work

#### Phase 4: Polish & Documentation
- 🔄 Issue #62: cli.py mutation testing (48.9% → 80%)
- 📋 Issue #25: Unit Tests for Generators (comprehensive coverage)
- 📋 Issue #26: Integration Tests (E2E scenarios)
- 📋 Issue #27: README Documentation
- 📋 Issue #28: API Documentation

---

## Critical Path Analysis

The project has made significant progress. The remaining critical path:

```
Issue #62 (cli.py Mutation Testing) [IN PROGRESS]
    ↓
├── Issue #25 (Unit Tests Completion) [PENDING]
│       ↓
├── Issue #26 (Integration Tests) [PENDING]
│       ↓
└── Issue #27 (README) [PENDING]
        ↓
    Issue #28 (API Docs) [PENDING]
        ↓
    🎉 SHIP v1.0.0 🎉
```

**Remaining Duration:** ~1-2 weeks

---

## Implementation Phases

### Phase 1: Quality Foundation (Weeks 1-2) - ✅ COMPLETE

**Goal:** Establish unshakeable quality baseline.

**Deliverables:**
- ✅ 32 pre-commit hooks configured and passing
- ✅ CI pipeline with quality, test, and security jobs
- ✅ Reference assets library (skills, subagents, workflows)
- ✅ 3-gate workflow system documented
- ✅ Mutation testing framework (periodic quality check)

**Note on Mutation Testing:**
The 3-gate workflow system now treats mutation testing as a **periodic quality check** for critical infrastructure, not a continuous gate. This change was made to preserve developer flow state while maintaining test effectiveness for high-risk code.

---

### Phase 2: Content Generators (Weeks 3-4) - ✅ COMPLETE

**Goal:** Implement the AI-powered generation system.

**Deliverables:**
- ✅ ContentTuner (Sonnet-based adaptation)
- ✅ SkillsGenerator (language-specific skills)
- ✅ SubagentsGenerator (8 subagent profiles)
- ✅ ClaudeMdGenerator (MAXIMUM_QUALITY integration)
- ✅ ArchitectureEnforcementGenerator
- ✅ MetricsGenerator
- ✅ PreCommitGenerator
- ✅ CIGenerator
- ✅ ScriptsGenerator

---

### Phase 3: CLI & Integration (Weeks 5-6) - ✅ COMPLETE

**Goal:** Make the tool usable with polished CLI and GitHub integration.

**Deliverables:**
- ✅ CLI Framework (Typer + Rich)
  - `green --help`
  - `green version`
  - `green init [options]`
- ✅ Init Command (full interactive flow)
  - Project name validation
  - Language selection
  - Config file support
  - Dry-run mode
  - Directory creation
  - File generation orchestration
- ✅ GitHub Integration
  - Repository creation via API
  - Branch protection configuration
  - Issue creation from SPEC.md
  - Label and milestone management
  - Secure token handling (keyring + env var)

---

### Phase 4: Polish & Documentation (Week 7) - 🔄 IN PROGRESS

**Goal:** Ship-ready product with excellent documentation.

#### In Progress

**Issue #62: cli.py Mutation Testing (48.9% → 80%)**

Detailed test implementation plan created:
- Phase 1: Validation logic tests (14 tests)
- Phase 2: Parameter resolution tests (10 tests)
- Phase 3: API key handling tests (9 tests)
- Phase 4: Init command tests (18 tests)

**Reference:** `plans/2026-01-26_MUTANT_EXTERMINATION_PLAN_CLI.md`

#### Pending

**Issue #25: Unit Tests for Generators** (2 days)
- Each generator in `tests/unit/generators/`
- Mock AI responses
- 90%+ coverage target

**Issue #26: Integration Tests** (2 days)
- Full init flow (mocked AI)
- GitHub integration (mocked API)
- Generated output validation

**Issue #27: README Documentation** (2 days)
1. Project Overview
2. Installation (PyPI + source)
3. Quick Start Guide
4. Full Command Reference
5. Configuration Options
6. Examples
7. Contributing Guidelines
8. License (MIT)

**Issue #28: API Documentation** (2 days)
- pdoc configuration
- All public modules documented
- HTML docs generated

---

## Issue Dependency Graph

### Visualization

```
                                    ┌─────────────────────────────┐
                                    │   PHASE 1-3: COMPLETE ✅    │
                                    │ (All infrastructure done)   │
                                    └──────────────┬──────────────┘
                                                   │
                                                   v
                                    ┌─────────────────────────────┐
                                    │ Issue #62 (cli.py Mutation) │
                                    │     🔄 IN PROGRESS          │
                                    │     48.9% → 80%             │
                                    └──────────────┬──────────────┘
                                                   │
                        +─────────────────────────+─────────────────────────+
                        │                         │                         │
                        v                         v                         v
              ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
              │ Issue #25 (Tests)│       │ Issue #26 (E2E) │       │ Issue #27 (README)│
              │     [P0]        │       │     [P1]        │       │     [P0]        │
              └────────┬────────┘       └────────┬────────┘       └────────┬────────┘
                       │                         │                         │
                       +─────────────────────────+─────────────────────────+
                                                 │
                                                 v
                                    ┌─────────────────────────────┐
                                    │   Issue #28 (API Docs)      │
                                    │         [P2]                │
                                    └──────────────┬──────────────┘
                                                   │
                                                   v
                                            🎉 SHIP v1.0.0 🎉
```

### Completed Issues Summary

| Issue | Title | Status | Completion Date |
|-------|-------|--------|-----------------|
| #22 | Copy SGSG Assets | ✅ COMPLETE | Jan 2026 |
| #23 | Create Missing Skills | ✅ COMPLETE | Jan 2026 |
| #24 | Dependency Checker Subagent | ✅ COMPLETE | Jan 2026 |
| #9 | Tuning Pass System | ✅ COMPLETE | Jan 2026 |
| #13 | Skills Generator | ✅ COMPLETE | Jan 2026 |
| #14 | Subagents Generator | ✅ COMPLETE | Jan 2026 |
| #15 | CLAUDE.md Generator | ✅ COMPLETE | Jan 2026 |
| #17 | Metrics Dashboard | ✅ COMPLETE | Jan 2026 |
| #18 | Architecture Enforcement | ✅ COMPLETE | Jan 2026 |
| #19 | CLI Framework | ✅ COMPLETE | Jan 2026 |
| #20 | Init Command | ✅ COMPLETE | Jan 2026 |
| #21 | GitHub Integration | ✅ COMPLETE | Jan 2026 |
| #16 | GitHub Actions Review | ✅ COMPLETE | Jan 2026 |

### Remaining Issues

| Issue | Title | Priority | Status | Est. Time |
|-------|-------|----------|--------|-----------|
| #62 | cli.py Mutation Testing | P1-high | 🔄 IN PROGRESS | 7-10 hours |
| #25 | Unit Tests Generators | P0-critical | 📋 PENDING | 2 days |
| #26 | Integration Tests | P1-high | 📋 PENDING | 2 days |
| #27 | README | P0-critical | 📋 PENDING | 2 days |
| #28 | API Documentation | P2-medium | 📋 PENDING | 2 days |

---

## Risk Management

### Resolved Risks

#### 1. Mutation Testing (Issue #62) - PARTIALLY MITIGATED
**Original Risk:** Killing 276 mutants might take longer than 1 week.

**Resolution:**
- Most files now pass 80% threshold
- Only cli.py remains (48.9%)
- Detailed improvement plan created
- 3-gate workflow removes mutation from continuous blocking

#### 2. AI Token Costs - MITIGATED
**Resolution:**
- Sonnet used for tuning (cost-efficient)
- Mock responses in tests
- Token usage tracking implemented

#### 3. GitHub Integration Complexity - RESOLVED
**Resolution:**
- GitHubClient fully implemented (808 lines)
- 45 comprehensive tests
- Retry logic for transient failures
- Proper error handling

### Remaining Risks

#### 1. cli.py Mutation Testing
**Risk:** 118 surviving mutants in cli.py

**Mitigation:**
- Detailed 4-phase test implementation plan
- Focus on high-value logic mutations
- Estimated 51 new tests needed

**Contingency:** Accept 75% if 80% proves unreachable within time budget.

#### 2. Time Estimates
**Risk:** Documentation might take longer than estimated.

**Mitigation:**
- P2 issues can be deferred to v1.1
- Core functionality complete

---

## Success Metrics

### MVP (v1.0.0) Release Criteria

**Quality Metrics:**
- [x] Test coverage ≥ 90% (currently 97%+)
- [ ] Mutation score ≥ 80% (cli.py in progress)
- [x] Pylint score ≥ 9.0
- [x] All pre-commit hooks pass (32 hooks)
- [x] Zero security vulnerabilities
- [x] Documentation coverage ≥ 95%

**Feature Completeness:**
- [x] All P0 issues closed (#15, #19, #20, #22)
- [x] Most P1 issues closed (#9, #13, #14, #16, #21, #23, #24)
- [x] P2 issues implemented (#17)
- [ ] Final testing and documentation (#25, #26, #27, #28)

**User Experience:**
- [x] `green init` works end-to-end
- [x] Generated project passes all checks
- [ ] Documentation complete and clear
- [x] Error messages helpful
- [ ] Examples tested and working

**Performance:**
- [x] Full generation < 2 minutes (basic project)
- [x] Token usage optimized

---

## Timeline Summary

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| **Phase 1: Quality Foundation** | 2 weeks | ✅ COMPLETE | Reference assets, 3-gate workflow |
| **Phase 2: Content Generators** | 2 weeks | ✅ COMPLETE | All generators implemented |
| **Phase 3: CLI & Integration** | 2 weeks | ✅ COMPLETE | CLI, GitHub integration |
| **Phase 4: Polish & Docs** | 1 week | 🔄 IN PROGRESS | Testing, documentation |
| **TOTAL** | **~7 weeks** | **~85% Complete** | **v1.0.0 nearly ready** |

**Remaining Work:** 1-2 weeks for:
- cli.py mutation testing (7-10 hours)
- Final testing and documentation (4-6 days)

---

## Next Steps

### Immediate Actions (This Week)

1. **Complete cli.py Mutation Testing**
   - Follow `plans/2026-01-26_MUTANT_EXTERMINATION_PLAN_CLI.md`
   - Implement 51 targeted tests
   - Achieve ≥80% mutation score

2. **Verify All Quality Gates**
   ```bash
   pre-commit run --all-files
   ./scripts/mutation.sh --paths-to-mutate start_green_stay_green/cli.py
   ```

3. **Create PR for Mutation Testing**
   - Branch: `test/final-mutation-killers`
   - All gates passing before review

### This Week Goals

- [ ] cli.py mutation score ≥80%
- [ ] All pre-commit hooks passing
- [ ] CI pipeline green
- [ ] PR ready for review

### Following Week Goals

- [ ] Complete Issue #25 (Unit Tests)
- [ ] Complete Issue #26 (Integration Tests)
- [ ] Complete Issue #27 (README)
- [ ] Complete Issue #28 (API Docs)
- [ ] Release v1.0.0

---

## Appendix: Issue Quick Reference

### Completed Issues (13 total)

| Issue | Title | Priority | Status |
|-------|-------|----------|--------|
| #22 | Copy SGSG Assets | P0-critical | ✅ COMPLETE |
| #9 | Tuning Pass System | P1-high | ✅ COMPLETE |
| #13 | Skills Generator | P1-high | ✅ COMPLETE |
| #23 | Missing Skills | P1-high | ✅ COMPLETE |
| #14 | Subagents Generator | P1-high | ✅ COMPLETE |
| #24 | Dependency Checker | P1-high | ✅ COMPLETE |
| #15 | CLAUDE.md Generator | P0-critical | ✅ COMPLETE |
| #19 | CLI Framework | P0-critical | ✅ COMPLETE |
| #20 | Init Command | P0-critical | ✅ COMPLETE |
| #21 | GitHub Integration | P1-high | ✅ COMPLETE |
| #16 | GitHub Actions Review | P1-high | ✅ COMPLETE |
| #18 | Architecture Enforcement | P1-high | ✅ COMPLETE |
| #17 | Metrics Dashboard | P2-medium | ✅ COMPLETE |

### Remaining Issues (5 total)

| Issue | Title | Priority | Estimate | Status |
|-------|-------|----------|----------|--------|
| #62 | Mutation Testing (cli.py) | P1-high | 7-10 hours | 🔄 IN PROGRESS |
| #25 | Unit Tests Generators | P0-critical | 2 days | 📋 PENDING |
| #26 | Integration Tests | P1-high | 2 days | 📋 PENDING |
| #27 | README | P0-critical | 2 days | 📋 PENDING |
| #28 | API Documentation | P2-medium | 2 days | 📋 PENDING |

---

## Appendix: Recent Changes

### Workflow Updates (January 2026)

**3-Gate Workflow System**: The development workflow has been updated from 4 gates to 3 gates:
1. **Gate 1**: Local pre-commit (32 hooks)
2. **Gate 2**: CI pipeline green
3. **Gate 3**: Code review LGTM

**Mutation Testing**: Moved from continuous enforcement to periodic quality check for critical infrastructure. This preserves developer flow state while maintaining test effectiveness for high-risk code.

**Reference**: `reference/workflows/stay-green.md`

### GitHub Integration (January 2026)

**Issue #21 Completed**: Full GitHubClient implementation with:
- 808 lines of production code
- 45 comprehensive tests
- Repository, issue, label, milestone management
- Branch protection configuration
- SPEC.md parsing for issue generation
- Retry logic and secure token handling

**Reference**: `GITHUB_INTEGRATION_IMPLEMENTATION.md`

---

**End of Roadmap**

_This is a living document. Update as issues are completed and new information emerges._
