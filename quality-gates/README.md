# Quality Gates Configuration

This directory contains JSON configuration files that define quality thresholds and architectural constraints for the Start Green Stay Green project. These files ensure consistent application of quality standards across the codebase and CI/CD pipeline.

## Files Overview

### coverage-thresholds.json

Defines code coverage and documentation coverage requirements.

**Configuration Options:**

- `minimum_coverage` (number): Minimum overall code coverage percentage (default: 90)
- `minimum_branch_coverage` (number): Minimum branch coverage percentage (default: 90)
- `minimum_docstring_coverage` (number): Minimum docstring coverage percentage (default: 95)
- `fail_below_threshold` (boolean): Whether to fail checks if thresholds are not met (default: true)
- `exclude_patterns` (array): Glob patterns for files/directories to exclude from coverage analysis

**Usage:**

Coverage checks are enforced in:
- `scripts/test.sh`: Runs pytest with coverage validation
- `scripts/check-all.sh`: Includes coverage verification as part of full check suite
- CI/CD pipeline: GitHub Actions workflows validate coverage before merge

**Thresholds Explained:**

- **90% Coverage**: All code paths should be tested. Exceptions require issue references.
- **95% Docstring Coverage**: All public APIs must have Google-style docstrings.
- **Exclusions**: Test files, fixtures, and templates are excluded from coverage requirements.

### complexity-limits.json

Defines code complexity constraints to ensure maintainability.

**Configuration Options:**

- `max_cyclomatic_complexity` (number): Maximum cyclomatic complexity per function (default: 10)
- `max_cognitive_complexity` (number): Maximum cognitive complexity per function (default: 15)
- `max_maintainability_index_threshold` (number): Minimum maintainability index (default: 20)
- `max_arguments` (number): Maximum function arguments (default: 5)
- `max_local_variables` (number): Maximum local variables per function (default: 15)
- `max_returns` (number): Maximum return statements per function (default: 6)
- `max_branches` (number): Maximum branch points per function (default: 12)
- `max_statements` (number): Maximum statements per function (default: 50)

**Usage:**

Complexity checks are enforced in:
- `scripts/complexity.sh`: Runs radon and xenon complexity analyzers
- `scripts/check-all.sh`: Includes complexity analysis as part of full check suite
- CI/CD pipeline: Complexity violations fail PR checks

**Thresholds Explained:**

- **Cyclomatic Complexity ≤ 10**: Functions should have at most 10 independent code paths
- **Cognitive Complexity ≤ 15**: Functions should be mentally easy to follow
- **Max Arguments ≤ 5**: Too many arguments indicate poor design; use objects instead
- **Max Statements ≤ 50**: Long functions should be refactored into smaller ones

**When Complexity Is Exceeded:**

1. Refactor the function into smaller, more focused functions
2. Use design patterns (Strategy, Command, etc.) to reduce branching
3. Extract complex logic into helper functions
4. Use data structures to replace multiple arguments

### architecture-rules.json

Defines architectural constraints and import rules to maintain clean separation of concerns.

**Configuration Options:**

- `forbidden_imports` (array): Lists forbidden import patterns with reasons
  - `pattern` (string): Glob pattern of modules that cannot import
  - `from` (string): Glob pattern of modules they cannot import from
  - `reason` (string): Explanation of why this import is forbidden

- `required_structure` (object): Structural requirements for the codebase
  - `test_files_must_have_prefix` (string): Required prefix for test files (default: "test_")
  - `private_modules_must_start_with` (string): Required prefix for private modules (default: "_")
  - `max_file_length_lines` (number): Maximum lines per file (default: 500)

**Usage:**

Architecture rules are checked by:
- Pre-commit hooks: Can validate forbidden imports before commit
- Linters: Custom rules can be added to enforce patterns
- Code review: Architecture violations are flagged in PR reviews
- CI/CD pipeline: Arch violations fail PR checks (future enhancement)

**Current Rules:**

- **Forbidden Import**: `start_green_stay_green.generators.*` from `start_green_stay_green.ai.*`
  - **Reason**: The AI layer should orchestrate generators, not import from them
  - **Impact**: Prevents circular dependencies and maintains clear layer separation
  - **Violation Example**: `from start_green_stay_green.generators import BaseGenerator` in any AI module

**Adding New Rules:**

To add a new architectural constraint:

1. Identify the modules/layers that should not communicate
2. Add a new entry to `forbidden_imports` array
3. Document the reason in the PR
4. Update any relevant linting rules or custom checkers
5. Ensure all CI checks pass with the new rule

## Integration Points

### CI/CD Pipeline

These configuration files are referenced by:

- **GitHub Actions** (`/.github/workflows/ci.yml`): Validates thresholds during CI
- **Pre-commit hooks** (`/.pre-commit-config.yaml`): Can enforce rules before commits
- **Quality scripts** (`/scripts/`): Use thresholds to determine pass/fail criteria

### Code Review

During code review, violations of these thresholds may result in:
- Request for additional tests to increase coverage
- Request to refactor complex functions
- Request to fix architectural violations
- Request to update docstrings for clarity

### Local Development

Developers should check these thresholds regularly:

```bash
# Run full quality check (includes coverage and complexity)
./scripts/check-all.sh

# Check only coverage
./scripts/test.sh

# Check only complexity
./scripts/complexity.sh

# Format and auto-fix issues
./scripts/fix-all.sh
```

## Adjusting Thresholds

**IMPORTANT**: These thresholds represent the MAXIMUM QUALITY ENGINEERING standards. They should only be adjusted when:

1. **Justified by evidence**: Performance analysis, team consensus, or architectural changes
2. **Documented in an issue**: Include rationale and impact analysis
3. **Approved by code review**: Changes require explicit approval
4. **Applied carefully**: Lowering thresholds increases technical debt

**Do NOT:**
- Lower thresholds to make code pass
- Exclude files from coverage to hide untested code
- Ignore complexity warnings
- Create architectural exceptions without documentation

## Maintenance

These files should be reviewed and updated when:

- Project scope changes significantly
- Team quality standards evolve
- New architectural patterns are adopted
- Tool updates introduce new metrics or changes
- Quarterly reviews of project health metrics

Last updated: 2026-01-14
