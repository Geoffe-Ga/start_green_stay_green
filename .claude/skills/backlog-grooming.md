# Backlog Grooming Skill

**Category**: Project Management & Issue Tracking
**Last Updated**: 2026-01-27

---

## Purpose

Systematically review recent work, close resolved issues, identify new issues, and maintain a clean, accurate issue backlog that reflects the current state of the project.

---

## Activation

When the user says:
- "Please groom the backlog"
- "Groom the GitHub backlog"
- "Clean up the issue tracker"
- Or similar backlog maintenance requests

---

## Process Overview

Backlog grooming involves:
1. **Review recent work** - Analyze merged PRs for accomplishments
2. **Identify resolved issues** - Find issues that were fixed
3. **Close resolved issues** - With proper references and gratitude
4. **Identify gaps** - Find work done without corresponding issues
5. **Create missing issues** - For future reference and patterns
6. **Avoid duplicates** - Check existing issues before creating
7. **Document progress** - Track grooming work in `/plan/`

---

## Execution Steps

### Step 1: Initialize Progress Tracking

Create a dated progress file in `/plan/`:

```bash
# Create progress tracking file
DATE=$(date +%Y-%m-%d)
PROGRESS_FILE="plan/${DATE}_BACKLOG_GROOMING.md"
```

**File structure:**
```markdown
# Backlog Grooming Session: YYYY-MM-DD

## Parameters
- **PRs Reviewed**: Last N PRs (default: 15)
- **Date Range**: YYYY-MM-DD to YYYY-MM-DD
- **Started**: HH:MM
- **Completed**: HH:MM

## Phase 1: PR Analysis
[Track progress here]

## Phase 2: Issue Resolution
[Track resolved issues]

## Phase 3: Gap Identification
[Track new issues needed]

## Phase 4: Cleanup
[Track closed/updated issues]

## Summary
- PRs analyzed: N
- Issues closed: N
- Issues created: N
- Issues updated: N
```

### Step 2: Fetch Recent PRs

```bash
# Get last N merged PRs with details
gh pr list --state merged --limit 15 --json number,title,mergedAt,body,url,closedAt
```

**For each PR, extract:**
- PR number and title
- Merge date
- Body/description
- Issues mentioned (closes #N, fixes #N, resolves #N)
- Files changed
- Accomplishments/features added

**Document in progress file:**
```markdown
### PR #N: Title
- **Merged**: YYYY-MM-DD
- **Closes**: #X, #Y
- **Accomplishments**:
  - Feature A
  - Bug fix B
  - Documentation C
- **Gaps** (work without issues):
  - Item 1
  - Item 2
```

### Step 3: Analyze Each PR

For each PR, ask:

1. **What issues does it claim to close?**
   - Check PR body for keywords: "closes #N", "fixes #N", "resolves #N"
   - Check commit messages
   - Verify issues actually exist

2. **What work was actually done?**
   - Read PR description
   - Review file changes (use `gh pr diff --name-only`)
   - Identify features, fixes, refactors, docs

3. **Are there discrepancies?**
   - Work done but no issue referenced
   - Issue referenced but not actually resolved
   - Related issues that should be updated

4. **What new issues emerge?**
   - Follow-up work needed
   - Technical debt created
   - Documentation gaps
   - Test coverage gaps

### Step 4: Verify Issue Resolution

For each issue referenced in PRs:

```bash
# Check issue status
gh issue view 123 --json state,title,labels

# Verify if truly resolved
# - Read issue description
# - Compare with PR changes
# - Check if acceptance criteria met
```

**Decision matrix:**
- ✅ **Fully resolved** → Close with comment
- 🔄 **Partially resolved** → Update with progress comment
- ❌ **Not resolved** → Remove from PR's "closes" claim, keep open
- 🔀 **Spawned new work** → Create follow-up issue, close original

### Step 5: Close Resolved Issues

For each fully resolved issue:

```bash
gh issue close 123 --comment "Resolved in PR #456

[Brief description of how it was resolved]

Thank you for reporting this! The fix is now merged and will be available in the next release.

Changes:
- [Key change 1]
- [Key change 2]

Closes via: [PR URL]"
```

**Best practices:**
- Reference the resolving PR number and URL
- Briefly explain the solution
- Show gratitude to reporter (if external)
- Mention when fix will be available
- List key changes made

**Update progress file:**
```markdown
## Phase 2: Issue Resolution

### Closed Issues
- [x] #123 - Issue title → Closed via PR #456
- [x] #124 - Issue title → Closed via PR #457
```

### Step 6: Identify Gaps

Review all work done in PRs and identify:

**Missing issue types:**

1. **Features without issues**
   - New functionality added without tracking issue
   - Create issue for historical record and pattern recognition

2. **Bugs fixed without issues**
   - Bugs discovered and fixed in PR
   - Create issue documenting the bug for future reference

3. **Refactors without context**
   - Code restructuring without explanation
   - Create issue explaining why and what was learned

4. **Documentation added**
   - New docs without corresponding issue
   - Usually OK to skip issue, but note in progress file

5. **Follow-up work identified**
   - TODOs added
   - Technical debt created
   - Performance improvements needed
   - Test coverage gaps

**Document gaps:**
```markdown
## Phase 3: Gap Identification

### Work Done Without Issues
- **PR #456**: Added feature X (no issue)
  - Action: Create retrospective issue for pattern
- **PR #457**: Fixed bug Y (no issue)
  - Action: Create bug documentation issue

### Follow-up Work Needed
- **PR #458**: Added TODO for performance optimization
  - Action: Create performance issue
- **PR #459**: Test coverage gap in module Z
  - Action: Create test improvement issue
```

### Step 7: Check for Duplicates

Before creating any new issue:

```bash
# Search for similar issues
gh issue list --search "keyword" --state all

# Check labels
gh issue list --label "bug" --state open
gh issue list --label "enhancement" --state open
```

**Duplicate detection:**
- Search by keywords from proposed issue
- Check same labels
- Review recently closed issues
- Check if mentioned in other open issues

**If duplicate found:**
- Link to existing issue instead
- Add comment to existing issue if new info
- Update existing issue if it needs refinement

### Step 8: Create Missing Issues

For each gap identified (that's not a duplicate):

```bash
gh issue create --title "Issue title" --body "Description" --label "label1,label2"
```

**Issue template for retrospective issues:**
```markdown
## Context

This issue is created retrospectively to document work completed in PR #N.

## What Was Done

[Description of the work]

## Why It Was Done

[Rationale/problem it solved]

## Related PRs

- #N - [PR title]

## Follow-up

[Any follow-up work needed, or "None"]

---

**Status**: Completed in PR #N
**Documented**: YYYY-MM-DD (retroactive)
```

**Issue template for follow-up work:**
```markdown
## Background

During work on PR #N, we identified the need for [description].

## Problem

[What needs to be addressed]

## Proposed Solution

[If known, describe approach]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Related Issues

- #N - [Original issue/PR]

## Priority

[High/Medium/Low] - [Brief justification]
```

**Update progress file:**
```markdown
## Phase 3: Gap Identification

### New Issues Created
- [ ] #789 - Feature X retrospective → Created
- [ ] #790 - Performance optimization follow-up → Created
- [ ] #791 - Test coverage for module Z → Created
```

### Step 9: Update Related Issues

Some issues may not be closed but need updates:

```bash
gh issue comment 123 --body "Update message"
```

**Update scenarios:**

1. **Partial progress**
   - Issue not fully resolved but progress made
   - Comment with what was done and what remains

2. **Changed requirements**
   - Original issue no longer relevant as stated
   - Update description or close with explanation

3. **Blocked issues**
   - Blocker was removed in recent PR
   - Remove "blocked" label, add comment

4. **Duplicate consolidation**
   - Multiple issues about same thing
   - Close duplicates, consolidate into canonical issue

### Step 10: Finalize Progress File

Complete the summary section:

```markdown
## Summary

### Statistics
- **PRs analyzed**: 15
- **Date range**: 2026-01-20 to 2026-01-27
- **Issues closed**: 8
- **Issues created**: 3
- **Issues updated**: 2
- **Duplicates avoided**: 1

### Issues Closed
1. #123 - Feature request A (PR #456)
2. #124 - Bug fix B (PR #457)
[...]

### Issues Created
1. #789 - Performance optimization follow-up
2. #790 - Test coverage improvement
3. #791 - Documentation gap

### Issues Updated
1. #101 - Updated with progress from PR #458
2. #102 - Removed "blocked" label

## Accomplishments Documented

### Features Added
- Feature A (PR #456)
- Feature B (PR #458)

### Bugs Fixed
- Bug X (PR #457)
- Bug Y (PR #459)

### Improvements
- Refactored module Z (PR #460)
- Improved test coverage (PR #461)

## Backlog Health

**Before grooming:**
- Open issues: N
- Stale issues: N
- Unlabeled issues: N

**After grooming:**
- Open issues: N
- Stale issues: N
- Unlabeled issues: N

**Net change**: -X issues (closed) +Y issues (created) = Z total change

## Notes

[Any observations, patterns, or recommendations]

## Next Grooming

**Recommended**: YYYY-MM-DD (one week from now)
**Trigger**: When 10-15 more PRs have been merged
```

---

## Customization Parameters

Default parameters can be adjusted based on context:

```python
{
    "pr_count": 15,  # Number of recent PRs to review
    "include_open_prs": False,  # Whether to include open PRs
    "days_back": None,  # Alternative: all PRs from last N days
    "close_stale": False,  # Whether to close stale issues (>60 days inactive)
    "labels_to_review": ["bug", "enhancement", "documentation"],
    "require_confirmation": True,  # Ask before closing/creating issues
    "progress_file": "plan/{date}_BACKLOG_GROOMING.md"
}
```

---

## Quality Checks

Before completing grooming:

### ✅ Verification Checklist

- [ ] All referenced issues in merged PRs are either closed or updated
- [ ] All closed issues have a reference to the resolving PR
- [ ] No duplicate issues created
- [ ] All new issues have appropriate labels
- [ ] All new issues have clear descriptions and acceptance criteria
- [ ] Progress file is complete and committed
- [ ] No issues closed without verification of resolution
- [ ] All gaps identified have either an issue or a documented reason for skipping

### ⚠️ Warning Signs

Watch for these patterns:

- **Many PRs without issue references** → Need better issue tracking discipline
- **Many issues half-resolved** → PRs too large, need smaller scopes
- **Many follow-up issues created** → Technical debt accumulating
- **Many duplicates found** → Need better issue search before creating
- **Stale issues accumulating** → Need regular grooming cadence

---

## Best Practices

### DO ✅

1. **Be thorough** - Read each PR description and key file changes
2. **Be grateful** - Thank contributors when closing their issues
3. **Be specific** - Reference exact PR numbers and commit SHAs
4. **Be conservative** - When in doubt, don't close (update instead)
5. **Be consistent** - Use same format for all close/create comments
6. **Document patterns** - Note recurring issues or improvements
7. **Track progress** - Update progress file as you go
8. **Verify resolution** - Check that issue is actually fixed
9. **Link everything** - Connect issues, PRs, and commits
10. **Look forward** - Identify future work and technical debt

### DON'T ❌

1. **Don't rush** - Take time to understand each PR's impact
2. **Don't auto-close** - Just because PR mentions issue doesn't mean it's fully resolved
3. **Don't create duplicates** - Always search first
4. **Don't close without explanation** - Always add context
5. **Don't ignore gaps** - Document work done without issues
6. **Don't skip verification** - Check issue state before acting
7. **Don't forget labels** - New issues need proper categorization
8. **Don't lose context** - Create retrospective issues for undocumented work
9. **Don't hide technical debt** - Create issues for follow-up work
10. **Don't forget gratitude** - Acknowledge contributors

---

## Automation Opportunities

While this skill is currently manual, these steps could be automated:

1. **PR analysis** - Script to extract issues from PR bodies
2. **Duplicate detection** - Semantic search for similar issues
3. **Close suggestions** - List of issues to review for closure
4. **Gap detection** - Compare PR work with issue tracker
5. **Progress tracking** - Auto-generate progress file template
6. **Statistics** - Automated calculation of backlog health metrics

**Note**: Even with automation, human review is essential for quality.

---

## Frequency Recommendations

**Regular grooming schedule:**

- **Weekly**: If >10 PRs per week (keeps backlog fresh)
- **Bi-weekly**: If 5-10 PRs per week (standard pace)
- **Monthly**: If <5 PRs per week (low activity)
- **After milestones**: Always groom after major releases
- **Before planning**: Groom before sprint/iteration planning

**Triggers for ad-hoc grooming:**

- Backlog has >50 open issues
- >10 PRs merged since last grooming
- Preparing for external audit/review
- Onboarding new contributors (clean backlog helps)
- User reports "duplicate issue" multiple times

---

## Success Metrics

A well-groomed backlog has:

- ✅ **>90% of merged PRs** reference issues
- ✅ **<10% of issues** marked as stale
- ✅ **<5% duplicate** issue creation rate
- ✅ **All issues labeled** appropriately
- ✅ **Clear issue state** (no "zombie" issues that appear closed but aren't)
- ✅ **Regular grooming** (weekly/bi-weekly)
- ✅ **Complete history** (work is documented in issues/PRs)

---

## Example Session

```markdown
# Backlog Grooming Session: 2026-01-27

## Parameters
- PRs Reviewed: Last 15
- Date Range: 2026-01-20 to 2026-01-27
- Started: 10:00
- Completed: 11:30

## Phase 1: PR Analysis ✅

Analyzed PRs #450-465:
- 12 PRs referenced issues
- 3 PRs had no issue reference
- 2 PRs partially resolved issues

## Phase 2: Issue Resolution ✅

Closed 8 issues:
- #120 via PR #450
- #121 via PR #451
[...]

## Phase 3: Gap Identification ✅

Created 3 new issues:
- #500 - Performance follow-up
- #501 - Test coverage gap
- #502 - Documentation update

## Phase 4: Cleanup ✅

Updated 2 issues:
- #99 - Progress update
- #100 - Unblocked

## Summary

**Statistics:**
- PRs analyzed: 15
- Issues closed: 8
- Issues created: 3
- Issues updated: 2
- Time spent: 1.5 hours

**Backlog Health:**
- Before: 45 open issues
- After: 40 open issues
- Net change: -5 issues ✅

**Accomplishments:**
- Fixed authentication bug
- Added new export feature
- Improved test coverage to 92%
- Updated documentation

**Next grooming:** 2026-02-03
```

---

## Templates

### Issue Close Comment Template

```markdown
Resolved in PR #XXX

[1-2 sentence description of solution]

Changes made:
- [Change 1]
- [Change 2]

Thank you for [reporting/requesting] this! The fix will be available in [version/release].

Closes via: [PR URL]
```

### Retrospective Issue Template

```markdown
## Context

This retrospective issue documents work completed in PR #XXX.

## What Was Done

[Description]

## Why

[Rationale]

## Related

- PR #XXX
- Issue #XXX (if any)

## Status

✅ Completed in PR #XXX
📅 Documented: YYYY-MM-DD
```

### Follow-up Issue Template

```markdown
## Background

During PR #XXX, we identified: [description]

## Problem

[What needs addressing]

## Proposed Solution

[If known]

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Priority

[High/Medium/Low] - [Why]

## Related

- PR #XXX - Where this was identified
- Issue #XXX - Original work (if any)
```

---

## Troubleshooting

### "Can't find issues referenced in PR"

- Check PR body and individual commit messages
- Look for variations: "close #N", "fix #N", "resolve #N"
- Check if issue was in different repo or moved
- If genuinely missing, create retrospective issue

### "Issue marked closed but seems unresolved"

- Verify by reading issue description and acceptance criteria
- Check PR changes to confirm resolution
- If not actually resolved: reopen issue, add comment explaining
- Remove issue reference from PR if incorrectly claimed

### "Found many duplicates"

- Indicates need for better issue search before creation
- Consolidate duplicates into canonical issue
- Close duplicates with link to canonical
- Consider improving issue search/labels

### "Too many PRs to review"

- Focus on most recent PRs first
- Can split grooming into multiple sessions
- Document stopping point in progress file
- Continue in next session

### "PR work doesn't match any issue category"

- Create retrospective issue for documentation
- May indicate missing issue types/labels
- Review and update issue templates if needed

---

## Resources

- [GitHub CLI Issue Commands](https://cli.github.com/manual/gh_issue)
- [GitHub CLI PR Commands](https://cli.github.com/manual/gh_pr)
- [Issue Linking Keywords](https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue)

---

**Version**: 1.0
**Author**: Claude Sonnet 4.5
**Status**: Active - Use "Please groom the backlog" to activate
