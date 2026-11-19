---
name: comprehensive-pr-review
description: >-
  Structured 10-section PR review covering security, quality, testing,
  and documentation. Use when reviewing pull requests, evaluating code
  changes, or doing code review. Produces verdicts with specific references.
  Do NOT use for backlog grooming or issue triage (use backlog-grooming),
  issue-first development workflow and PR creation (use git-workflow), or
  iterating on a review's feedback as the PR author (use address-feedback).
metadata:
  author: Geoff
  version: 1.1.0
---

# Comprehensive PR Review

Structured code review evaluating PRs across security, quality, testing, documentation, and project compliance.

## Instructions

### Step 1: Summarize the PR
Brief overview of what the PR does (2-3 sentences).

### Step 2: Identify Strengths
What is done well: good design decisions, well-written code, comprehensive tests, clear documentation, proper error handling.

### Step 3: Security Review
Flag security issues with severity:
- **BLOCKING**: Must fix before merge (injection, auth bypass, secrets exposure)
- **HIGH**: Should fix soon (missing input validation, weak crypto)
- **LOW**: Nice to have (hardening, defense-in-depth)

### Step 4: Identify Problems
Critical issues blocking merge: bugs, incorrect logic, failing tests, missing required features.

### Step 5: Evaluate Code Quality
Non-blocking improvements: readability, naming, organization, complexity.

### Step 6: Check Project Compliance
Verify against project standards (adjust to project's CLAUDE.md):
- Test coverage meets threshold
- Docstring coverage meets threshold
- Linting rules pass
- Type checking passes
- No forbidden patterns
- Conventional commits used

### Step 7: Assess Testing
- Test coverage adequate?
- Edge cases covered?
- Integration tests included?

### Step 8: Review Documentation
- Docstrings complete?
- README updated if needed?
- Examples provided for new APIs?

### Step 9: List Requests
Medium-priority suggestions that would improve the PR.

### Step 10: Deliver Verdict
- **LGTM** - Ready to merge; nothing further worth tracking
- **CHANGES_REQUESTED** - Must fix blocking issues. This is the **only** verdict that sends the author back into a fix loop
- **COMMENTS** - Signed off with non-blocking suggestions; can merge as-is. The author does **not** iterate on a `COMMENTS` verdict: `address-feedback` files each actionable item as a follow-up issue labelled `P0`–`P3` by severity, then merges. So state each suggestion's severity plainly (cite `file:line`) — it sets the issue's priority. Anything that must change before merge is `CHANGES_REQUESTED`, not `COMMENTS`

Include reasoning with specific file:line references. If you have non-blocking suggestions you want tracked, choose `COMMENTS` rather than `LGTM` — suggestions under an `LGTM` are not filed anywhere.

#### Verdict Line Format (load-bearing)

End the review comment with a single canonical line so downstream automation (`address-feedback`, `await-claude-review`) can parse it deterministically:

```
## Verdict: LGTM
## Verdict: CHANGES_REQUESTED
## Verdict: COMMENTS
```

`await-claude-review` matches this regex (case-insensitive):

```
^\s*(?:##\s+|\*\*)?Verdict[:*\s]+(LGTM|CHANGES_REQUESTED|COMMENTS)
```

Use exactly one of the three values. Don't paraphrase ("looks good to me", "approving") or invent a fourth value: the parser refuses to infer a verdict from prose, consumers treat any value other than an exact `LGTM` or `COMMENTS` as a refusal, and the merge gate will block.

### Step 11 (Iterative Reviewer): Wait for the Author's Response

When you've delivered `CHANGES_REQUESTED` and want to follow the iteration without polling, delegate to `await-claude-review`. It subscribes to PR activity (comments + CI failures — the webhook does **not** deliver CI passes) and wakes the session on the next push's verdict comment. End the turn after subscribing. Do not wait after `LGTM` or `COMMENTS` — neither produces another push to review.

## Examples

### Example 1: Sign-off with Suggestions (COMMENTS)

```markdown
## Summary
Adds user search endpoint with partial name/email matching.

## Strengths
- Clean separation of concerns (router -> service -> repository)
- Parameterized SQL queries prevent injection
- Good test coverage (94%)

## Security Concerns
None identified.

## Problems
None blocking.

## Code Quality
- (minor) Consider extracting the search query builder into its own method (src/services/search.py:40)
- (moderate) `search_users` has no `limit` parameter, so a broad query returns every row (src/services/search.py:22)

## Verdict: COMMENTS
Well-structured PR with good test coverage. Suggestions are non-blocking and
can be tracked as follow-up issues.
```

### Example 2: Changes Requested

```markdown
## Summary
Adds file upload endpoint for user avatars.

## Security Concerns
- BLOCKING: No file type validation - allows arbitrary file upload (src/api/upload.py:23)
- HIGH: No file size limit - potential DoS vector (src/api/upload.py:15)

## Problems
- Missing error handling for disk full scenario (src/services/storage.py:45)
- Test doesn't verify file content, only status code (tests/test_upload.py:30)

## Verdict: CHANGES_REQUESTED
Security concerns must be addressed before merge. Add file type whitelist
and size limit validation.
```

## Troubleshooting

### Error: PR is too large to review effectively
- Ask the author to split into smaller PRs
- Focus on the most critical files first (API surface, security-sensitive code)
- Use `gh pr diff --name-only` to prioritize which files to review

### Error: Unclear what the PR is supposed to do
- Check for linked issues or a description
- Ask the author to add context before reviewing
- Review the test names - they often describe intended behavior
