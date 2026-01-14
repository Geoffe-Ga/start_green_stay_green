# CLAUDE.md Best Practices Extraction

**Date**: 2026-01-13
**Purpose**: Extract specific, actionable patterns from analyzed repositories for direct integration into SGSG

---

## 1. Critical Principles Section

**Best From**: specinit
**Impact**: HIGH - Immediate clarity on non-negotiables

### Pattern

```markdown
## Critical Principles

These rules are **non-negotiable** and must be followed without exception:

1. **Use Project Scripts** - Always use `./scripts/*` instead of direct tool invocation
   - ✅ `./scripts/test.sh`
   - ❌ `pytest`

2. **DRY Principle** - Single source of truth, reference don't duplicate
   - ✅ Link to `/reference/workflows/stay-green.md`
   - ❌ Copy workflow documentation into multiple files

3. **No Shortcuts** - Fix root causes, never bypass quality checks
   - ✅ Refactor code to pass complexity checks
   - ❌ Add `# noqa` to suppress linting

4. **Stay Green** - Never request review with failing checks
   - ✅ Wait for all CI jobs to show ✅
   - ❌ Create PR while CI is red

5. **Quality First** - Meet MAXIMUM QUALITY standards, don't lower thresholds
   - ✅ Write tests to reach 90% coverage
   - ❌ Change `fail_under = 70` to pass builds

6. **Operate from Root** - Use relative paths from project root, never `cd`
   - ✅ `./scripts/test.sh tests/unit/ai/test_orchestrator.py`
   - ❌ `cd tests/unit/ai && pytest test_orchestrator.py`

7. **Verify Before Commit** - Run `./scripts/check-all.sh` before every commit
   - ✅ All checks pass (exit code 0)
   - ❌ Skip checks with `--no-verify`
```

### Why It's Better
- Immediately visible at top of document
- Numbered for easy reference ("See Critical Principle #3")
- Examples show correct vs incorrect
- Non-negotiable language sets expectations

### Integration Approach
- Add section immediately after "Project Overview"
- Before "Stay Green Workflow"
- Cross-reference from other sections

---

## 2. Code Examples Pattern

**Best From**: ml-odyssey
**Impact**: HIGH - Concrete guidance over abstract rules

### Pattern: Side-by-Side Correct vs Incorrect

```markdown
### Generator Pattern

❌ **WRONG**: Direct string concatenation
```python
def generate_readme(project_name):
    content = "# " + project_name + "\n\n"
    content += "## Overview\n"
    return content
```

✅ **CORRECT**: Use Jinja2 templates
```python
def generate_readme(project_name: str, language: str) -> str:
    """Generate README using template.

    Args:
        project_name: Name of the project.
        language: Programming language.

    Returns:
        Rendered README content.
    """
    template = self.env.get_template('README.md.j2')
    return template.render(
        project_name=project_name,
        language=language,
    )
```

### Why It's Effective
- Visual contrast makes correct pattern obvious
- Shows not just WHAT but WHY (types, docstrings, separation of concerns)
- Real code, not abstract description

### Integration to SGSG

Add examples for:

1. **Generator Patterns**
   ```python
   # Template loading, rendering, validation
   ```

2. **AI Integration Patterns**
   ```python
   # PromptManager usage, error handling, retry logic
   ```

3. **Testing Patterns**
   ```python
   # Mocking generators, testing AI integration, fixtures
   ```

4. **Template Patterns**
   ```jinja2
   # Variable interpolation, conditionals, loops, filters
   ```

---

## 3. Skills Catalog

**Best From**: ml-odyssey
**Impact**: MEDIUM - Clarifies automation options

### Pattern

```markdown
## Skills & Common Automation

### Available Skills

Claude Code can automate common tasks using these skills:

**Repository Operations**:
- `repo-init` - Initialize new repository structure
- `quality-setup` - Configure quality tools (ruff, mypy, pytest)
- `ci-setup` - Create GitHub Actions workflows

**Code Generation**:
- `generate-component` - Generate new generator component
- `generate-tests` - Create test files for components
- `generate-docs` - Create documentation templates

**Quality Checks**:
- `run-all-checks` - Execute ./scripts/check-all.sh
- `fix-auto-fixable` - Execute ./scripts/fix-all.sh
- `analyze-coverage` - Generate detailed coverage report
- `run-mutation` - Execute mutation tests

**Git Workflows**:
- `create-pr` - Create pull request with proper format
- `rebase-branch` - Rebase feature branch onto main
- `squash-commits` - Squash commits for clean history
- `sync-branch` - Pull latest from main and rebase

**Template Operations**:
- `validate-template` - Validate Jinja2 template syntax
- `render-template` - Render template with test data
- `lint-templates` - Check template best practices
```

### Why It's Effective
- Quick reference for AI agents
- Grouped by category
- Clear naming convention (verb-noun)
- Shows what's automatable

### Integration to SGSG
- Add after "AI Subagent Guidelines" section
- Start with 10-15 core skills
- Expand as patterns emerge

---

## 4. Testing Strategy Enhancement

**Best From**: wrist-arcana
**Impact**: HIGH - Makes testing requirements actionable

### Pattern

```markdown
## Testing Strategy

### Test Organization

```
tests/
├── unit/              # Fast, isolated tests
│   ├── ai/
│   │   ├── test_orchestrator.py
│   │   └── test_tuner.py
│   ├── generators/
│   │   ├── test_ci.py
│   │   └── test_scripts.py
│   └── utils/
├── integration/       # Component interaction tests
│   ├── test_generator_integration.py
│   └── test_ai_config_flow.py
└── e2e/              # End-to-end workflow tests
    └── test_full_generation_flow.py
```

### Test Structure: Arrange-Act-Assert

```python
def test_generator_creates_valid_config():
    """Test generator creates valid configuration file."""
    # Arrange
    generator = CIGenerator(language="python")
    target_path = tmp_path / "config"

    # Act
    result = generator.generate(target_path)

    # Assert
    assert result.success
    assert (target_path / ".github" / "workflows" / "ci.yml").exists()
    config = yaml.safe_load((target_path / ".github" / "workflows" / "ci.yml").read_text())
    assert config["jobs"]["test"]["runs-on"] == "ubuntu-latest"
```

### Mocking Patterns

**Mock AI Orchestrator**:
```python
@pytest.fixture
def mock_orchestrator(mocker):
    """Mock AI orchestrator for generator tests."""
    mock = mocker.Mock(spec=AIOrchestrator)
    mock.generate.return_value = GenerationResult(
        content="# Generated Content",
        format="markdown",
        token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-5-20250929",
        message_id="msg_123",
    )
    return mock
```

**Mock Template Environment**:
```python
@pytest.fixture
def mock_template_env(tmp_path):
    """Mock Jinja2 environment with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create test template
    (templates_dir / "test.j2").write_text("# {{ title }}")

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    return env
```

### Coverage Targets by Component

| Component Type | Minimum Coverage | Rationale |
|----------------|------------------|-----------|
| Generators | 95%+ | Core functionality, must be reliable |
| AI Integration | 90%+ | Critical path, complex logic |
| Utilities | 90%+ | Widely reused, bugs multiply |
| CLI | 80%+ | User-facing, important but UI-heavy |
| Templates | N/A | Tested via integration tests |

### Property-Based Testing

Use Hypothesis for generators:

```python
from hypothesis import given, strategies as st

@given(
    language=st.sampled_from(["python", "typescript", "go", "rust"]),
    project_name=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="/")),
)
def test_generator_handles_valid_inputs(language, project_name):
    """Test generator handles all valid language/name combinations."""
    generator = BaseGenerator(language=language)
    result = generator.validate_project_name(project_name)
    assert result.is_valid or result.error_message  # Either valid or has error
```
```

### Why It's Better
- Concrete examples show HOW to test
- AAA pattern makes tests readable
- Mock patterns solve common problems
- Coverage targets justify effort
- Property-based testing catches edge cases

### Integration to SGSG
- Replace current "Testing Requirements" section
- Add to "Development Workflow" or create dedicated section
- Include in generators template

---

## 5. Security Guidelines

**Best From**: specinit
**Impact**: HIGH - Essential for tool that generates repos

### Pattern

```markdown
## Security Guidelines

### API Key Handling

**NEVER** store API keys in:
- ❌ Environment variables (`.env` files)
- ❌ Configuration files (hardcoded)
- ❌ Code files (constants)

**ALWAYS** use OS keyring:
```python
import keyring

# Store API key
keyring.set_password("sgsg", "claude_api_key", api_key)

# Retrieve API key
api_key = keyring.get_password("sgsg", "claude_api_key")
if not api_key:
    raise ValueError("Claude API key not found in keyring")
```

### Path Validation

**NEVER** trust user-provided paths without validation:

```python
# ❌ WRONG: Path traversal vulnerability
def create_file(user_path: str, content: str):
    with open(user_path, 'w') as f:
        f.write(content)  # User could pass "../../etc/passwd"
```

**ALWAYS** validate and resolve paths:

```python
# ✅ CORRECT: Validate path is within allowed directory
from pathlib import Path

def create_file(user_path: str, content: str, base_dir: Path):
    """Create file with path traversal protection."""
    target = (base_dir / user_path).resolve()

    # Ensure resolved path is within base directory
    if not target.is_relative_to(base_dir):
        raise ValueError(f"Path traversal detected: {user_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
```

### Subprocess Safety

**NEVER** use `shell=True`:

```python
# ❌ WRONG: Shell injection vulnerability
subprocess.run(f"git clone {user_repo}", shell=True)
```

**ALWAYS** use list form without shell:

```python
# ✅ CORRECT: No shell injection possible
subprocess.run(["git", "clone", user_repo], check=True)
```

### Input Validation

**NEVER** assume user input is valid:

```python
# ❌ WRONG: No validation
def generate_project(name: str):
    subprocess.run(["mkdir", name])  # Name could be malicious
```

**ALWAYS** validate input:

```python
# ✅ CORRECT: Validate project name
import re

def validate_project_name(name: str) -> bool:
    """Validate project name is safe."""
    # Only allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError(f"Invalid project name: {name}")
    if len(name) > 100:
        raise ValueError("Project name too long")
    return True

def generate_project(name: str):
    validate_project_name(name)
    subprocess.run(["mkdir", name], check=True)
```
```

### Why It's Critical
- SGSG generates repos with user input
- Path traversal = serious security issue
- API keys in generated code = bad practice
- Shell injection = critical vulnerability

### Integration to SGSG
- Add new "Security Guidelines" section after "Quality Standards"
- Reference from "Generator Pattern" examples
- Include in template for generated repos

---

## 6. Most Common Mistakes Section

**Best From**: ml-odyssey (64+ patterns analysis)
**Impact**: MEDIUM - Prevents recurring issues

### Pattern

```markdown
## Most Common Mistakes

Based on analysis of 50+ PRs, these are the most frequent mistakes:

### 1. Skipping Local Quality Checks (35%)

**The Mistake**:
```bash
# Committing without running checks
git add .
git commit -m "feat: add feature"
git push
# CI fails with linting errors
```

**The Fix**:
```bash
# ALWAYS run checks before committing
./scripts/check-all.sh
# Only commit if exit code is 0
git add .
git commit -m "feat: add feature (#123)"
```

**Why It Happens**: Impatience, assuming "it's just a small change"
**Prevention**: Add pre-commit hook to enforce checks

---

### 2. Lowering Quality Thresholds (25%)

**The Mistake**:
```toml
# In pyproject.toml
[tool.coverage.report]
fail_under = 70  # Changed from 90 to make build pass
```

**The Fix**:
```python
# Write tests to reach 90% coverage
def test_edge_case_handling():
    """Test previously uncovered edge case."""
    result = process_edge_case(unusual_input)
    assert result.is_valid()
```

**Why It Happens**: Pressure to merge quickly, thinking "I'll add tests later"
**Prevention**: Treat thresholds as immutable, add tests first

---

### 3. Using Direct Tool Invocation (20%)

**The Mistake**:
```bash
# Running tools directly
ruff check .
pytest tests/
mypy start_green_stay_green/
```

**The Fix**:
```bash
# Use project scripts
./scripts/lint.sh
./scripts/test.sh
./scripts/lint.sh  # mypy runs as part of lint.sh
```

**Why It Happens**: Muscle memory from other projects, not reading docs
**Prevention**: Tool Invocation Patterns section, prominent reminder

---

### 4. Commenting Out Failing Tests (15%)

**The Mistake**:
```python
# def test_important_feature():
#     """This test fails, commenting out for now."""
#     result = process_data(input)
#     assert result.is_valid()
```

**The Fix**:
```python
@pytest.mark.skip(reason="Issue #123: Waiting for API endpoint")
def test_important_feature():
    """Test important feature works correctly."""
    result = process_data(input)
    assert result.is_valid()
```

**Why It Happens**: Test fails, don't know how to fix, want to unblock PR
**Prevention**: Require skip reason with issue number, enforce in code review

---

### 5. Adding # noqa Without Justification (5%)

**The Mistake**:
```python
long_variable_name_that_exceeds_line_limit = function_call(arg1, arg2, arg3)  # noqa: E501
```

**The Fix**:
```python
# Option 1: Refactor to fix the issue
long_name = function_call(
    arg1, arg2, arg3
)

# Option 2: If truly unavoidable, justify
api_url = "https://very-long-api-endpoint.com/..."  # noqa: E501  # Issue #42: API URL from spec
```

**Why It Happens**: Easier to suppress than fix, don't understand rule
**Prevention**: Require issue number for all noqa comments

---

### Summary Table

| Mistake | Frequency | Fix Time | Impact |
|---------|-----------|----------|--------|
| Skip local checks | 35% | 5 min | High (CI failures) |
| Lower thresholds | 25% | 30 min | High (technical debt) |
| Direct tools | 20% | 2 min | Low (inconsistency) |
| Comment tests | 15% | 15 min | Medium (reduced coverage) |
| Unjustified noqa | 5% | 5 min | Low (code quality) |
```

### Why It's Effective
- Quantifies frequency (helps prioritize learning)
- Shows mistake → fix → why → prevention
- Summary table for quick reference
- Based on real PR data, not hypothetical

### Integration to SGSG
- Add section after "No Shortcuts Allowed"
- Update based on actual SGSG PR history
- Cross-reference from "Development Workflow"

---

## 7. Visual Workflow Diagrams

**Best From**: SGSG (Stay Green), enhanced with ml-odyssey's table patterns
**Impact**: MEDIUM - Visual learners benefit

### Pattern: ASCII Workflow Diagram

```markdown
## Stay Green Workflow (Visual)

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT CYCLE                            │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ Write Code   │
  │ Write Tests  │
  └──────┬───────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ GATE 1: Local Pre-Commit                      │
│ ┌────────────────────────────────────────────┐ │
│ │ ./scripts/check-all.sh                     │ │
│ │  • Formatting ✓                           │ │
│ │  • Linting ✓                              │ │
│ │  • Types ✓                                │ │
│ │  • Security ✓                             │ │
│ │  • Complexity ✓                           │ │
│ │  • Tests ✓                                │ │
│ │  • Coverage ≥90% ✓                        │ │
│ └────────────────────────────────────────────┘ │
│   Exit 0 required to proceed                   │
└──────────────┬─────────────────────────────────┘
               │ PASS
               ▼
         git push
               │
               ▼
┌────────────────────────────────────────────────┐
│ GATE 2: CI Pipeline                           │
│ ┌────────────────────────────────────────────┐ │
│ │ GitHub Actions                             │ │
│ │  • quality job ✓                          │ │
│ │  • test (3.11) ✓                          │ │
│ │  • test (3.12) ✓                          │ │
│ └────────────────────────────────────────────┘ │
│   All jobs must show ✅                        │
└──────────────┬─────────────────────────────────┘
               │ PASS
               ▼
┌────────────────────────────────────────────────┐
│ GATE 3: Mutation Testing                      │
│ ┌────────────────────────────────────────────┐ │
│ │ ./scripts/mutation.sh                      │ │
│ │  • Score: 82% ✓ (≥80% required)           │ │
│ │  • Killed: 156 / 190 mutants              │ │
│ └────────────────────────────────────────────┘ │
└──────────────┬─────────────────────────────────┘
               │ PASS
               ▼
┌────────────────────────────────────────────────┐
│ GATE 4: Code Review                           │
│ ┌────────────────────────────────────────────┐ │
│ │ Claude/Human Review                        │ │
│ │  • Architecture ✓                         │ │
│ │  • Patterns ✓                             │ │
│ │  • Quality ✓                              │ │
│ │  • Documentation ✓                        │ │
│ │  • LGTM ✓                                 │ │
│ └────────────────────────────────────────────┘ │
└──────────────┬─────────────────────────────────┘
               │ LGTM
               ▼
         ┌─────────┐
         │  MERGE  │
         └─────────┘

┌────────────────────────┐
│ Fix Issues Locally     │◀──┐
│ Re-run Gate 1          │   │
└────────┬───────────────┘   │
         │                   │
         └───────────────────┘
         (Loop back on failure)
```
```

### Pattern: Comparison Table

```markdown
### Quality Gates Comparison

| Gate | What | Duration | Failure Rate | Cost of Failure |
|------|------|----------|--------------|-----------------|
| Gate 1 | Local checks | 30s | 5% | 30s (immediate feedback) |
| Gate 2 | CI pipeline | 2min | 15% | 5min (CI + fix + rerun) |
| Gate 3 | Mutation | 5min | 10% | 15min (analysis + tests) |
| Gate 4 | Review | varies | 20% | Hours (human/AI feedback) |

**Key Insight**: Gate 1 has lowest failure rate because it catches issues earliest. Fix time increases exponentially with each gate.
```

### Why It's Effective
- Visual learners grasp workflow immediately
- Shows feedback loops
- Table quantifies costs (motivates running Gate 1)
- ASCII art works in plain text

### Integration to SGSG
- Enhance existing Stay Green documentation
- Add tables showing metrics
- Include in /reference/workflows/stay-green.md

---

## 8. Pre-Flight Checklist

**Best From**: ml-odyssey
**Impact**: MEDIUM - Prevents common oversights

### Pattern

```markdown
## Pre-Commit Checklist

Run through this checklist before every commit:

### Code Quality
- [ ] All functions have type hints
- [ ] All public APIs have Google-style docstrings
- [ ] No `# type: ignore` without issue reference
- [ ] No `# noqa` without issue reference
- [ ] No `# TODO` without issue reference
- [ ] No `print()` statements (use logging)
- [ ] No hardcoded paths or API keys

### Testing
- [ ] All new functions have unit tests
- [ ] Edge cases covered
- [ ] Error paths tested
- [ ] `./scripts/test.sh` passes (exit 0)
- [ ] Coverage ≥90% maintained

### Documentation
- [ ] Docstrings added for new public APIs
- [ ] CHANGELOG.md updated (if user-facing)
- [ ] README.md updated (if feature)
- [ ] Related documentation updated

### Quality Checks
- [ ] `./scripts/check-all.sh` passes (exit 0)
- [ ] All files formatted (`./scripts/format.sh`)
- [ ] No linting errors
- [ ] No type errors
- [ ] No security issues
- [ ] Complexity ≤10 per function

### Git
- [ ] Commit message follows Conventional Commits
- [ ] Issue number in commit message
- [ ] Branch named `feature/<issue>-<desc>`
- [ ] No merge commits (rebase instead)

### Before Creating PR
- [ ] All of the above ✅
- [ ] Pushed to feature branch
- [ ] CI pipeline is green
- [ ] Ready for review
```

### Why It's Effective
- Checkbox format is actionable
- Covers all common oversights
- Can be copied into PR template
- Encourages thoroughness

### Integration to SGSG
- Add to "Development Workflow" section
- Include in PR template
- Reference from "Stay Green Workflow"

---

## 9. Delegation Patterns

**Best From**: ml-odyssey
**Impact**: LOW (nice-to-have) - Clarifies when to use agents

### Pattern

```markdown
## Agent & Skill Delegation Patterns

### Pattern 1: Direct Delegation

Agent needs specific automation:

```markdown
Use the `run-all-checks` skill to validate code quality:
- **Invoke when**: Before creating PR
- **The skill handles**: Running ./scripts/check-all.sh and parsing output
```

### Pattern 2: Conditional Delegation

Agent decides based on conditions:

```markdown
If coverage < 90%:
  - Use the `analyze-coverage` skill to identify gaps
  - Add tests for uncovered lines
  - Use the `run-all-checks` skill to verify
Otherwise:
  - Proceed to create PR
```

### Pattern 3: Multi-Skill Workflow

Agent orchestrates multiple skills:

```markdown
To implement new generator:
1. Use the `generate-component` skill to create boilerplate
2. Use the `generate-tests` skill to create test structure
3. Implement the generator logic manually
4. Use the `run-all-checks` skill to validate
5. Use the `create-pr` skill to submit for review
```

### Pattern 4: Escalation

When to escalate to different agent level:

```markdown
L5 Junior Engineer encounters issue:
  → Escalate to L4 Implementation Engineer if:
    - Complexity exceeds simple function implementation
    - Integration with multiple components required
    - Architecture decision needed

L4 Implementation Engineer encounters issue:
  → Escalate to L3 Component Specialist if:
    - Affects component interface design
    - Requires coordination across multiple modules

L3 Component Specialist encounters issue:
  → Escalate to L2 Module Design Agent if:
    - Affects module boundaries
    - Requires API design changes
```
```

### Why It's Effective
- Shows when to automate vs manual work
- Clarifies agent hierarchy
- Prevents over-automation
- Prevents under-automation

### Integration to SGSG
- Add to "AI Subagent Guidelines" section
- Keep patterns simple (4-5 total)
- Focus on common scenarios

---

## 10. Structural Organization

**Best From**: wrist-arcana (10 clear sections)
**Impact**: HIGH - Makes navigation effortless

### Recommended Structure for SGSG

```markdown
# Claude Code Project Context: Start Green Stay Green

## 1. Critical Principles
[5-7 non-negotiable rules - added from specinit]

## 2. Project Overview
[Current content - keep as-is]

## 3. Stay Green Workflow
[Current content - enhance with diagrams]

## 4. Architecture
### 4.1 Core Philosophy
### 4.2 Component Structure
### 4.3 Design Patterns
[Current "Architecture" section]

## 5. Quality Standards
### 5.1 Code Quality Requirements
### 5.2 Enforcement Mechanisms
### 5.3 Security Guidelines (NEW)
[Combine current quality sections]

## 6. Development Workflow
### 6.1 Branch Strategy
### 6.2 Commit Conventions
### 6.3 PR Process
### 6.4 Code Review Checklist
[Current workflow content]

## 7. Testing Strategy
### 7.1 Test Organization
### 7.2 Test Structure (AAA Pattern)
### 7.3 Mocking Patterns (NEW)
### 7.4 Coverage Targets
### 7.5 Mutation Testing
[Enhanced with wrist-arcana patterns]

## 8. Tool Usage & Scripts
### 8.1 Tool Invocation Patterns
### 8.2 Common Commands
### 8.3 Skills Catalog (NEW)
[Current "Tool Invocation Patterns"]

## 9. Code Standards
### 9.1 Python Code Style
### 9.2 Generator Patterns (NEW with examples)
### 9.3 AI Integration Patterns (NEW with examples)
### 9.4 Template Patterns (NEW with examples)
### 9.5 Docstring Format
[Current code standards + new examples]

## 10. Common Pitfalls & Troubleshooting
### 10.1 No Shortcuts Policy
### 10.2 Forbidden Patterns
### 10.3 Most Common Mistakes (NEW)
### 10.4 Troubleshooting Guide
[Combine current pitfalls sections]

## Appendix A: Skills Catalog
[Full list of automation skills]

## Appendix B: Agent Hierarchy
[Current subagent list]

## Appendix C: External References
[Current references]
```

### Why It's Better
- Clear 10-section structure (like wrist-arcana)
- Logical flow: Principles → Overview → Workflow → Standards → Details
- Numbered sections easy to reference
- NEW sections clearly marked
- Appendices for reference material

---

## Implementation Priority Matrix

| Best Practice | Impact | Effort | Priority | Phase |
|---------------|--------|--------|----------|-------|
| Critical Principles Section | HIGH | LOW | P0 | 4 |
| Structural Reorganization | HIGH | MEDIUM | P0 | 4 |
| Code Examples | HIGH | HIGH | P0 | 4 |
| Security Guidelines | HIGH | MEDIUM | P0 | 4 |
| Testing Strategy Enhancement | HIGH | MEDIUM | P1 | 4 |
| Skills Catalog | MEDIUM | MEDIUM | P1 | 4 |
| Most Common Mistakes | MEDIUM | LOW | P1 | 4 |
| Pre-Flight Checklist | MEDIUM | LOW | P2 | 4 |
| Visual Diagrams | MEDIUM | MEDIUM | P2 | 5 |
| Delegation Patterns | LOW | LOW | P2 | 5 |

**Priority Legend**:
- P0: Must have (Phase 4)
- P1: Should have (Phase 4)
- P2: Nice to have (Phase 5)

---

## Next Steps

1. **Phase 3**: Create detailed enhancement plan with specific changes
2. **Phase 4**: Implement P0 and P1 items
3. **Phase 5**: Validate with AI agents, implement P2 items

**Estimated Implementation Time**: 6-8 hours for P0 + P1 items
