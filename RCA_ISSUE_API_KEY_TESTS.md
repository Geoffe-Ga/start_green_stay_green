# RCA: Integration Tests May Call Real Anthropic API

**Date**: 2026-02-21
**Severity**: Medium
**Component**: tests/integration/test_init_flow.py

---

## Problem Statement

Four integration tests in `test_init_flow.py` conditionally call the real Anthropic API
when `ANTHROPIC_API_KEY` is set in the environment. This violates test isolation principles
and can cause unexpected API costs, non-deterministic behavior, and CI flakiness.

## Root Cause

Lines 175, 207, 282, 308 use `@pytest.mark.skipif(not HAS_API_KEY, ...)` to gate tests
that run the full `init` CLI flow including AI-powered generators. When the API key IS
present, these tests call the real Anthropic API without mocking.

**Affected tests**:
- `test_init_generates_github_workflows` (line 175)
- `test_init_generates_claude_md` (line 207)
- `test_init_generates_subagents_directory` (line 282)
- `test_init_generates_architecture_rules` (line 308)

## Analysis

All other test files properly mock `Anthropic` with `@patch`. These 4 tests were
likely written as "optional integration tests" that run when a key is available, but this
pattern is problematic because:

1. **Unpredictable costs**: Any developer/CI with `ANTHROPIC_API_KEY` set incurs charges
2. **Non-deterministic**: API responses vary, making tests flaky
3. **No isolation**: Tests depend on external service availability
4. **Silent activation**: Developers may not realize tests are calling the real API

## Impact

- **Cost**: ~$0.01-0.10 per test run with API key present
- **Reliability**: Tests may fail due to rate limiting, network issues, or API changes
- **CI**: If API key is configured for other purposes, these tests activate silently

## Fix Strategy

**Recommended**: Mock the Anthropic client in these tests so they always run and never
call the real API. Remove the `HAS_API_KEY` skip condition. This is consistent with how
all other test files handle it.

## Prevention

- Add a conftest fixture that auto-patches `Anthropic` for all tests
- Or add a pytest marker `@pytest.mark.requires_real_api` and exclude by default
