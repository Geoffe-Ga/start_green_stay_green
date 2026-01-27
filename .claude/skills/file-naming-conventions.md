# File Naming Conventions

**Category**: Documentation Standards
**Last Updated**: 2026-01-26

---

## Core Principle

**Always prefix dated documents with ISO 8601 date format (YYYY-MM-DD) for natural chronological sorting.**

---

## Convention Rules

### 1. Date-Prefixed Documents

**Format**: `YYYY-MM-DD_DESCRIPTIVE_NAME.ext`

**Rationale**:
- Alphabetical sorting = chronological sorting
- Easy to find most recent/oldest files
- Consistent, unambiguous ordering
- Scales across years without reorganization

**Examples**:
```
✅ CORRECT:
2026-01-26_MUTANT_EXTERMINATION_PLAN_CLI.md
2026-01-25_MUTATION_TESTING_STATUS.md
2026-01-20_ARCHITECTURE_DECISION_RECORD.md

❌ INCORRECT:
MUTANT_EXTERMINATION_PLAN_CLI_2026-01-26.md
mutation_testing_status_01-26-2026.md
Architecture_Decision_Record.md
```

### 2. Document Types Requiring Date Prefixes

**Always use date prefixes for**:
- Analysis reports
- Status reports
- Plans and strategies
- Meeting notes
- Decision records
- Changelogs
- Progress updates
- Retrospectives
- Any time-sensitive documentation

### 3. Document Types NOT Requiring Date Prefixes

**Skip date prefixes for**:
- Permanent reference documentation (README.md, CONTRIBUTING.md)
- Configuration files (.gitignore, pyproject.toml)
- Source code files
- Test files
- Templates
- Specifications (unless versioned by date)
- General guides and tutorials

---

## Naming Components

### Date Component: `YYYY-MM-DD`
- Always 4-digit year
- Always 2-digit month (01-12)
- Always 2-digit day (01-31)
- Use hyphens as separators

### Separator: `_` (underscore)
- Single underscore between date and description
- Use underscores (not hyphens) within descriptive name

### Descriptive Name
- ALL_CAPS for major documents (plans, reports, specifications)
- lowercase_with_underscores for supporting documents (notes, drafts)
- Be descriptive but concise
- Use common abbreviations where clear (CLI, API, DB)

---

## Directory-Specific Conventions

### `/plans/` Directory
**Format**: `YYYY-MM-DD_PLAN_NAME.md`

**Examples**:
```
2026-01-26_MUTANT_EXTERMINATION_PLAN_CLI.md
2026-01-26_MUTATION_TESTING_CLEANUP_AND_IMPROVEMENT.md
2026-01-20_FEATURE_IMPLEMENTATION_STRATEGY.md
```

### `/docs/` or `/reference/` Directories
**Format**: Depends on document type

**Time-sensitive** (use date prefix):
```
2026-01-15_QUARTERLY_REVIEW.md
2026-01-01_MIGRATION_GUIDE_V2.md
```

**Timeless** (no date prefix):
```
API_REFERENCE.md
ARCHITECTURE.md
USER_GUIDE.md
```

### `/analysis/` or `/reports/` Directories
**Format**: `YYYY-MM-DD_ANALYSIS_NAME.md` (always date-prefixed)

**Examples**:
```
2026-01-26_mutation_analysis_cli.md
2026-01-25_performance_analysis_database.md
2026-01-20_security_audit_report.md
```

---

## Versioning vs Dating

### When to Use Dates
**Use dates when**: Document represents a point-in-time snapshot, analysis, or plan

**Example**: `2026-01-26_SPRINT_RETROSPECTIVE.md`

### When to Use Versions
**Use versions when**: Document is iteratively updated and version matters more than date

**Example**: `API_SPEC_v3.md` or `ARCHITECTURE_v2.1.md`

### Combined Approach
For major versioned documents with significant updates:

**Format**: `YYYY-MM-DD_DOCUMENT_NAME_vX.Y.md`

**Example**: `2026-01-26_API_SPECIFICATION_v3.0.md`

---

## Multiple Documents Same Day

When creating multiple related documents on the same day:

### Option 1: Descriptive Disambiguation
```
2026-01-26_MUTATION_ANALYSIS_CLI.md
2026-01-26_MUTATION_ANALYSIS_CREDENTIALS.md
2026-01-26_MUTATION_ANALYSIS_TUNER.md
```

### Option 2: Sequential Numbering
```
2026-01-26_01_INITIAL_ANALYSIS.md
2026-01-26_02_DETAILED_FINDINGS.md
2026-01-26_03_RECOMMENDATIONS.md
```

### Option 3: Hierarchical Naming
```
2026-01-26_MUTATION_TESTING_STATUS.md
2026-01-26_MUTATION_TESTING_CLEANUP_AND_IMPROVEMENT.md
```

---

## Special Cases

### Ongoing Documents (Living Documents)
For documents continuously updated without discrete versions:

**Option A**: Date of last major update
```
2026-01-26_PROJECT_ROADMAP.md  # Updated quarterly
```

**Option B**: No date (for truly evergreen docs)
```
PROJECT_ROADMAP.md  # Update in place
```

### Log Files and Artifacts
**Format**: `YYYY-MM-DD_type_identifier.log`

**Examples**:
```
2026-01-26_mutation_cli.log
2026-01-26_test_run_results.log
2026-01-26_benchmark_results.json
```

---

## Implementation Checklist

When creating a new dated document:

- [ ] Start with ISO 8601 date: YYYY-MM-DD
- [ ] Add single underscore separator
- [ ] Use descriptive, clear name
- [ ] Choose appropriate case (ALL_CAPS for major docs)
- [ ] Verify date is correct (today's date for new documents)
- [ ] Check for naming conflicts (if same day, disambiguate)
- [ ] Place in appropriate directory
- [ ] Update any index or table of contents

---

## Automation and Tooling

### Creating Dated Files
```bash
# Quick alias for bash/zsh
alias newplan='touch "$(date +%Y-%m-%d)_PLAN_NAME.md"'

# Python helper
from datetime import date
filename = f"{date.today().isoformat()}_MY_DOCUMENT.md"
```

### Finding Recent Files
```bash
# List most recent plans
ls -1 plans/ | sort -r | head -10

# Find all documents from specific month
ls plans/2026-01-*.md

# Find all documents from specific day
ls plans/2026-01-26*.md
```

---

## Benefits Summary

1. **Natural Sorting**: Alphabetical = chronological
2. **Easy Navigation**: Recent files cluster together
3. **Quick Filtering**: Date-based searches work naturally
4. **Consistency**: Same pattern across all time-sensitive docs
5. **Future-Proof**: Scales indefinitely without reorganization
6. **Unambiguous**: ISO 8601 is internationally recognized
7. **Tool-Friendly**: Works with all file systems and tools

---

## Anti-Patterns to Avoid

❌ **Month-Day-Year**: `01-26-2026` (doesn't sort chronologically)
❌ **Named Months**: `January-26-2026` (harder to parse, doesn't sort)
❌ **Abbreviated Years**: `26-01-26` (ambiguous, doesn't scale)
❌ **Spaces in Names**: `2026 01 26 Plan.md` (causes shell issues)
❌ **Mixed Separators**: `2026-01_26-PLAN.md` (inconsistent)
❌ **Date Suffixes**: `PLAN_2026-01-26.md` (doesn't sort chronologically)

---

**Remember**: When in doubt, put the date first!

---

**Version**: 1.0
**Author**: Claude Sonnet 4.5
**Status**: Active Convention
