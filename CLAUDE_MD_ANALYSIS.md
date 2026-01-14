# CLAUDE.md Cross-Repository Analysis

**Date**: 2026-01-13
**Analyzed Repositories**: WavelengthWatch, specinit, wrist-arcana, ml-odyssey, start_green_stay_green (SGSG)

---

## Executive Summary

This analysis compares CLAUDE.md files across 5 repositories to identify best practices, unique patterns, and opportunities to enhance SGSG's CLAUDE.md. The analysis reveals that **each repository has evolved unique strengths** based on their domain and maturity:

- **ml-odyssey**: Most sophisticated agent hierarchy, extensive Mojo guidelines, skills catalog
- **wrist-arcana**: Best structural organization (10 clear sections), comprehensive testing strategy
- **specinit**: Clearest "Critical Rules" section, excellent security guidance
- **WavelengthWatch**: Strong anti-pattern documentation, subsystem organization
- **SGSG**: Best quality enforcement documentation, Stay Green workflow, DRY architecture

---

## Repository Comparison Matrix

| Feature/Section | SGSG | WavelengthWatch | specinit | wrist-arcana | ml-odyssey |
|-----------------|------|-----------------|----------|--------------|------------|
| **Critical Rules Section** | ⚠️ Embedded | ✅ Present | ✅ Strong (5 rules) | ✅ Emphasized | ✅ Present |
| **Quality Standards** | ✅ Comprehensive | ⚠️ Basic | ⚠️ Basic | ✅ Detailed | ✅ Extensive |
| **Workflow Definition** | ✅ Stay Green (4 gates) | ⚠️ Basic | ⚠️ Basic | ✅ TDD workflow | ✅ 5-phase |
| **Agent Guidance** | ⚠️ Present | ⚠️ Basic | ✅ Claude-specific | ⚠️ Basic | ✅ Hierarchical (82 skills) |
| **Tool Invocation** | ✅ Scripts preferred | ✅ Never cd | ✅ Use scripts | ✅ Never cd | ✅ Skills delegation |
| **Anti-Patterns** | ✅ "No Shortcuts" | ✅ Present | ⚠️ Limited | ✅ 7 critical | ✅ 64+ patterns |
| **Testing Strategy** | ⚠️ Basic | ⚠️ Basic | ✅ Class-based | ✅ Comprehensive | ✅ TDD-focused |
| **Security Guidance** | ⚠️ Basic | ❌ None | ✅ API keys, paths | ❌ None | ⚠️ Limited |
| **Code Examples** | ⚠️ Limited | ⚠️ Limited | ✅ Present | ✅ Extensive | ✅ Extensive |
| **Visual Elements** | ✅ Diagrams | ❌ None | ❌ None | ✅ ASCII art | ✅ Tables |
| **Quick Reference** | ✅ Checklists | ⚠️ Commands | ⚠️ Commands | ⚠️ Commands | ✅ Tables |
| **Navigation Aids** | ⚠️ Sections | ⚠️ Basic | ⚠️ Basic | ⚠️ Basic | ✅ References |
| **Domain-Specific** | ✅ Generators | ✅ watchOS | ✅ CLI tools | ✅ watchOS | ✅ ML/Mojo |

**Legend**: ✅ Strong | ⚠️ Present but could improve | ❌ Missing

---

## Unique Strengths by Repository

### SGSG (Start Green Stay Green)

**Standout Features**:
1. **Stay Green Workflow** - 4-gate process (Local → CI → Mutation → Review)
2. **MAXIMUM QUALITY Philosophy** - Detailed enforcement and mindset documentation
3. **DRY Architecture** - Single source of truth pattern with references
4. **No Shortcuts Policy** - Comprehensive "Forbidden Patterns" section
5. **Tool Invocation Patterns** - Detailed "Never DO / Always DO" tables

**Gaps**:
- Missing explicit "Critical Rules" callout section (rules are embedded throughout)
- Limited security guidance compared to specinit
- Could improve code examples (less than wrist-arcana/ml-odyssey)
- No skills catalog (ml-odyssey has 82 skills)

---

### WavelengthWatch (watchOS App)

**Standout Features**:
1. **Subsystem Organization** - Clear separation (Setup, Backend, Frontend, Hooks)
2. **Critical Command Guidelines** - Explicit "avoid cd, use paths" pattern
3. **Development Guidelines** - "Always fix issues properly, never use shortcuts"
4. **Practical Focus** - Emphasizes real-world development commands

**Unique Patterns**:
- Command organization by subsystem (backend vs frontend)
- Explicit iPhone vs Watch simulator warnings
- Deployment status tracking

**What SGSG Could Adopt**:
- Subsystem-based command organization (generators, CI, tests, quality)
- More explicit "Critical Guidelines" section at top

---

### specinit (CLI Tool Generator)

**Standout Features**:
1. **5 Critical Non-Negotiable Principles** - Clear, numbered, at the top
2. **Security Guidance** - API keys, path validation, subprocess safety
3. **Claude-Specific Guidance** - How to use tools, format responses
4. **Testing Conventions** - Class-based organization, AAA pattern
5. **Complexity Thresholds** - World-class standards documented

**Unique Patterns**:
```markdown
## Critical Rules (5 Non-Negotiable Principles)

1. No shortcuts when fixing tests—address root causes
2. Use project scripts rather than running tools directly
3. Operate from project root; never cd
4. Verify completion by running checks
5. Avoid blocking CI monitoring commands
```

**What SGSG Could Adopt**:
- Numbered "Critical Rules" section at the very top
- Security guidance section (API keys, path validation)
- Claude-specific tool usage guidance
- Class-based test organization conventions

---

### wrist-arcana (watchOS Tarot App)

**Standout Features**:
1. **Clear 10-Section Structure** - Well-organized, easy to navigate
2. **Code Examples Throughout** - SwiftData, crypto, storage monitoring
3. **Testing Strategy Section** - Mock patterns, AAA structure, UI tests
4. **Performance Targets** - Specific metrics (<100ms card draw)
5. **Accessibility Requirements** - Labels on interactive elements
6. **7 Critical Anti-Patterns** - Explicitly enumerated

**Unique Patterns**:
```markdown
## Testing Strategy
- Mock patterns for protocol-based dependencies
- Arrange-Act-Assert structure
- UI test examples with assertions
```

**What SGSG Could Adopt**:
- Code examples for common patterns (generator patterns, AI usage)
- Performance targets (generation time, API latency)
- Accessibility considerations (if applicable to generated UIs)
- Numbered anti-patterns list (currently scattered in SGSG)

---

### ml-odyssey (ML Research Platform)

**Standout Features**:
1. **Hierarchical Agent System** - 6 levels, 44 agents, clear roles
2. **82 Skills Catalog** - Across 11 categories with descriptions
3. **Mojo Syntax Standards** - Comprehensive v0.25.7+ guidelines
4. **64+ Test Failure Patterns** - Systematic analysis from real PRs
5. **5-Phase Workflow** - Plan → [Test|Impl|Package] → Cleanup
6. **Zero-Warnings Policy** - Compiler as source of truth
7. **Skill Delegation Patterns** - 5 standard patterns documented

**Unique Patterns**:

**Agent Hierarchy** (6 levels):
```markdown
L0: Chief Architect (Opus)
L1: Section Orchestrators (Sonnet)
L2: Module Design Agents (Sonnet)
L3: Component Specialists (Sonnet)
L4: Implementation/Test Engineers (Sonnet)
L5: Junior Engineers (Haiku)
```

**Skills Catalog** (82 skills in 11 categories):
- GitHub (9 skills): gh-review-pr, gh-create-pr-linked, etc.
- Worktree (4 skills): worktree-create, worktree-cleanup, etc.
- Mojo (10 skills): mojo-format, mojo-test-runner, etc.
- Phase Workflow (5 skills): phase-plan-generate, etc.
- Agent System (5 skills): agent-validate-config, etc.
- Documentation (4 skills): doc-generate-adr, etc.
- CI/CD (6 skills): ci-run-precommit, etc.
- [and 5 more categories...]

**Mojo Anti-Patterns** (from 64+ test failures):
```markdown
1. Ownership Violations (40% of failures)
   - Never pass temporary expressions to functions
   - Never mark structs ImplicitlyCopyable with List fields

2. Constructor Signatures (25% of failures)
   - Never use mut self in __init__
   - Always use out self for constructors

3. Uninitialized Data (20% of failures)
   - Never assign to list indices without appending
   [etc...]
```

**What SGSG Could Adopt**:
- Skills catalog pattern (even if smaller - 10-20 skills)
- Language-specific syntax standards section (for Python generators)
- Compiler/tool as source of truth principle
- Systematic failure pattern documentation
- Pre-flight checklist before committing
- Shared reference files pattern (`.claude/shared/`)

---

## Comparative Analysis by Element

### 1. Critical Rules / Principles

**Best Implementation**: **specinit** (clearest, numbered, at top)

**specinit Approach**:
```markdown
## Critical Rules (5 Non-Negotiable Principles)

1. No shortcuts when fixing tests—always address root causes
2. Use project scripts (`./scripts/`) rather than running tools directly
3. Operate from project root; never `cd` into subdirectories
4. Verify completion by running checks
5. Avoid blocking CI monitoring commands
```

**SGSG Current State**:
- Has "No Shortcuts Allowed" section (buried mid-document)
- Has "Tool Invocation Patterns" section
- Rules scattered across multiple sections

**Recommendation**:
- Add "Critical Principles" section at the very top (after Project Overview)
- Number the principles (5-7 maximum)
- Include: DRY, Use Scripts, No Shortcuts, Stay Green, Quality First

---

### 2. Agent Guidance / Subagent Patterns

**Best Implementation**: **ml-odyssey** (most sophisticated)

**ml-odyssey Approach**:
```markdown
## Working with Agents

### Agent Hierarchy
See agents/hierarchy.md for:
- 6-level hierarchy (L0 Chief → L5 Junior)
- Model assignments (Opus, Sonnet, Haiku)
- All 44 agents with roles

### Key Agent Principles
1. Always start with orchestrators
2. All outputs posted as GitHub issue comments
3. Link all PRs to issues
4. Minimal changes only
5. No scope creep
6. Reply to each review comment
7. Delegate to skills

### Skill Delegation Patterns
**Pattern 1: Direct Delegation**
**Pattern 2: Conditional Delegation**
**Pattern 3: Multi-Skill Workflow**
[etc...]

**Available Skills** (82 total across 11 categories)
[detailed catalog...]
```

**SGSG Current State**:
- Has "AI Subagent Guidelines" section
- Lists available subagents (29 agents)
- Includes execution strategy (parallel preference)
- Missing: skill catalog, delegation patterns

**Recommendation**:
- Add "Skills Catalog" section with common automation tasks
- Document delegation patterns (when to use which agent/skill)
- Add examples of multi-agent workflows

---

### 3. Tool Invocation Patterns

**Best Implementation**: **SGSG** (most comprehensive tables)

**SGSG Approach**:
```markdown
| Task | ❌ NEVER DO THIS | ✅ ALWAYS DO THIS |
|------|------------------|-------------------|
| Format code | `black .` | `./scripts/format.sh` |
| Run tests | `pytest` | `./scripts/test.sh` |
[etc...]
```

**All Repos Emphasize**: Use scripts, not direct tool invocation

**What Others Add**:
- **WavelengthWatch**: "Never use cd" prominently featured
- **specinit**: "Prefer file reading tools over bash" (Claude-specific)
- **ml-odyssey**: Skills catalog for automation

**Recommendation**:
- SGSG's approach is already best-in-class
- Could add "Skills Catalog" for common automation tasks

---

### 4. Quality Standards / Enforcement

**Best Implementation**: **SGSG** (most detailed thresholds + enforcement)

**SGSG Approach**:
```markdown
## Quality Standards

### Code Quality Requirements
- Test Coverage: 90% minimum
- Docstring Coverage: 95% minimum
- Mutation Score: 80% minimum
- Cyclomatic Complexity: ≤10 per function
- Pylint Score: 9.0+

### Enforcement
- scripts/check-all.sh validates all
- CI pipeline enforces via GitHub Actions
- Stay Green workflow ensures compliance
```

**What Others Add**:
- **specinit**: "World-class standards" language
- **wrist-arcana**: Performance targets (<100ms)
- **ml-odyssey**: Zero-warnings policy

**Recommendation**:
- Add performance targets for generation workflows
- Add "Zero-Warnings Policy" section
- Consider "World-Class Standards" framing

---

### 5. Testing Strategy

**Best Implementation**: **wrist-arcana** (most comprehensive section)

**wrist-arcana Approach**:
```markdown
## Testing Strategy

### Test Types
1. Unit Tests: Protocol mocks, isolated
2. UI Tests: User flow verification
3. Integration Tests: Component interaction

### Test Organization
- Arrange-Act-Assert pattern
- Protocol-based mocking
- Descriptive test names

### Mock Patterns
[Code examples of mocking patterns]

### UI Test Examples
[Code examples with assertions]

### Coverage Targets
- 50% minimum overall
- 95%+ for models/ViewModels
- Lower for SwiftUI views (hard to test)
```

**SGSG Current State**:
- Has "Testing Requirements" section
- Lists test types (unit, integration, E2E, property-based, mutation)
- Has test organization structure
- Missing: code examples, mock patterns, detailed AAA guidance

**Recommendation**:
- Add code examples for common test patterns
- Add mocking guidance (generators, AI integration)
- Document AAA pattern more explicitly
- Add coverage targets per component type

---

### 6. Security Guidance

**Best Implementation**: **specinit** (only repo with dedicated section)

**specinit Approach**:
```markdown
## Security Guidance

- API keys must use OS keyring, never environment variables or files
- Path handling requires validation to prevent traversal attacks
- Subprocess calls must use list form without shell execution
```

**SGSG Current State**:
- Security checks mentioned (bandit, safety)
- No dedicated security guidance section
- No API key handling guidelines

**Recommendation**:
- Add "Security Guidelines" section
- Document API key handling (for generated repos)
- Path validation patterns
- Subprocess safety (relevant for generators)

---

### 7. Anti-Patterns / Forbidden Patterns

**Best Implementation**: **SGSG** (most comprehensive "No Shortcuts")

**Comparative Approaches**:

**SGSG**: Detailed "No Shortcuts Allowed" with examples
**wrist-arcana**: "7 Critical Anti-Patterns" enumerated
**ml-odyssey**: "64+ Test Failure Patterns" systematically documented

**SGSG's Strength**: Emphasizes *why* shortcuts are bad
**ml-odyssey's Strength**: Quantifies patterns from real failures

**Recommendation**:
- Keep SGSG's approach
- Add numbered list for quick reference
- Consider "Most Common Mistakes" section (top 10)

---

### 8. Code Examples

**Best Implementation**: **ml-odyssey** and **wrist-arcana** (tie)

**ml-odyssey Examples**:
- Mojo syntax patterns (dozens of examples)
- Correct vs incorrect side-by-side
- Real-world failure cases

**wrist-arcana Examples**:
- SwiftData setup
- Crypto randomization
- Storage monitoring
- UI test assertions

**SGSG Current State**:
- Limited code examples
- Has docstring format example
- Has Python style example
- Missing: generator patterns, AI usage, templating

**Recommendation**:
- Add generator pattern examples
- Add AI orchestration examples
- Add Jinja2 templating examples
- Show correct vs incorrect patterns

---

### 9. Workflow Definition

**Best Implementation**: **SGSG** (Stay Green is most rigorous)

**Comparative Workflows**:

**SGSG**: Stay Green (4 gates)
```
Gate 1: Local Pre-Commit (check-all.sh)
Gate 2: CI Pipeline (all jobs pass)
Gate 3: Mutation Testing (80%+)
Gate 4: Code Review (LGTM)
```

**wrist-arcana**: TDD Workflow
```
Red → Green → Refactor
Coverage thresholds enforced
```

**ml-odyssey**: 5-Phase Workflow
```
Plan → [Test | Implementation | Package] → Cleanup
```

**Strengths**:
- **SGSG**: Most rigorous, prevents premature reviews
- **wrist-arcana**: Emphasizes TDD cycle
- **ml-odyssey**: Parallel execution, packaging phase

**Recommendation**:
- Keep Stay Green as primary workflow
- Add TDD cycle as sub-workflow within Gate 1
- Consider packaging phase for SGSG itself (when shipping)

---

### 10. Navigation & Structure

**Best Implementation**: **wrist-arcana** (clearest structure)

**wrist-arcana Structure** (10 sections):
```markdown
1. Project Overview
2. Repository Directory Overview
3. Build and Test Commands
4. Architecture Overview
5. Project Structure
6. Development Workflow
7. Code Quality Standards
8. Critical Implementation Details
9. Testing Strategy
10. Performance, Accessibility, Pitfalls, Troubleshooting
```

**SGSG Structure** (many sections, less clear hierarchy):
- The Maximum Quality Engineering Mindset
- Stay Green Workflow
- Architecture
- Development Workflow
- Quality Standards
- Forbidden Patterns
- No Shortcuts
- Tool Invocation Patterns
- Testing Requirements
- [many more...]

**Recommendation**:
- Reorganize SGSG CLAUDE.md into 8-10 clear sections
- Add table of contents
- Group related content (all quality in one section, all testing in one)

---

## Extracted Best Practices

### Section Organization

**Best Pattern**: Numbered top-level sections with clear hierarchy (wrist-arcana)

**Why it's better**: Easy to scan, jump to relevant section, reference in discussions

**Integration to SGSG**:
```markdown
# Claude Code Project Context: Start Green Stay Green

## 1. Critical Principles (NEW)
[5-7 non-negotiable rules]

## 2. Project Overview
[Existing content]

## 3. Stay Green Workflow
[Existing content]

## 4. Architecture & Structure
[Combine existing sections]

## 5. Quality Standards
[Combine all quality content]

## 6. Development Workflow
[Existing content]

## 7. Testing Strategy (ENHANCED)
[Add code examples, AAA pattern]

## 8. Security Guidelines (NEW)
[Add API keys, path validation]

## 9. Tool Usage & Scripts
[Existing tool invocation content]

## 10. Common Pitfalls & Troubleshooting
[Combine No Shortcuts + FAQ]
```

---

### Agent Guidance Phrasing

**Best Pattern**: Skills catalog + delegation patterns (ml-odyssey)

**Why it's effective**: Clear automation options, reusable patterns

**Integration to SGSG**:
```markdown
## AI Subagent & Skills Catalog

### Available Subagents (29 agents)
[Existing list, keep current format]

### Common Skills & Automation

**Repository Setup**:
- `repo-init`: Initialize repository structure
- `quality-setup`: Configure quality tools
- `ci-setup`: Create GitHub Actions workflows

**Code Generation**:
- `generate-component`: Generate new component boilerplate
- `generate-tests`: Create test files for components
- `generate-docs`: Create documentation templates

**Quality Checks**:
- `run-all-checks`: Execute ./scripts/check-all.sh
- `fix-auto-fixable`: Execute ./scripts/fix-all.sh
- `analyze-coverage`: Generate coverage report

**Git Workflows**:
- `create-pr`: Create pull request with proper format
- `rebase-branch`: Rebase onto main
- `squash-commits`: Squash commits for clean history
```

---

### Code Standards

**Best Pattern**: ❌ WRONG / ✅ CORRECT side-by-side (ml-odyssey)

**Why it's effective**: Visual contrast makes correct pattern obvious

**Integration to SGSG**:
```markdown
## Python Code Standards

### Generator Pattern

❌ **WRONG**: Direct string concatenation
```python
def generate_config(name):
    return "name: " + name + "\ntype: project"
```

✅ **CORRECT**: Use Jinja2 templates
```python
def generate_config(name: str) -> str:
    """Generate configuration using template."""
    template = env.get_template('config.j2')
    return template.render(name=name)
```

### AI Integration Pattern

❌ **WRONG**: Hardcoded prompts
```python
result = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    messages=[{"role": "user", "content": "Generate a README"}]
)
```

✅ **CORRECT**: Use PromptManager
```python
result = prompt_manager.render_and_generate(
    template_name="readme",
    context={"project_name": name, "language": "python"}
)
```
```

---

### Common Pitfalls

**Best Pattern**: Categorized with percentages (ml-odyssey 64+ patterns)

**Why it's effective**: Shows which mistakes are most common, prioritizes learning

**Integration to SGSG**:
```markdown
## Most Common Mistakes (from PR analysis)

### 1. Skipping Local Quality Checks (40%)
❌ Committing without running `./scripts/check-all.sh`
✅ Always run local checks before pushing

### 2. Lowering Quality Thresholds (25%)
❌ Reducing coverage from 90% to pass builds
✅ Write tests to meet the 90% threshold

### 3. Using Direct Tool Invocation (20%)
❌ Running `pytest` or `ruff` directly
✅ Using `./scripts/test.sh` and `./scripts/lint.sh`

### 4. Commenting Out Failing Tests (10%)
❌ `# def test_feature(): ...`
✅ Fix the bug or mark with skip + issue reference

### 5. Adding # noqa Without Justification (5%)
❌ `x = value  # noqa: E501`
✅ Refactor code or document: `# noqa: E501  # Issue #123: API requires 120-char string`
```

---

## Recommendations for SGSG Enhancement

### High Priority (Implement in Phase 4)

1. **Add "Critical Principles" section at top**
   - From: specinit's 5 non-negotiable principles
   - List 5-7 core rules (DRY, Scripts, No Shortcuts, Stay Green, Quality First)
   - Place immediately after Project Overview

2. **Reorganize into 8-10 numbered sections**
   - From: wrist-arcana's clear structure
   - Makes navigation easier
   - Groups related content

3. **Add code examples throughout**
   - From: ml-odyssey and wrist-arcana patterns
   - Generator patterns, AI usage, templating
   - Use ❌ WRONG / ✅ CORRECT format

4. **Add "Security Guidelines" section**
   - From: specinit's security guidance
   - API key handling, path validation, subprocess safety
   - Critical for tool that generates repos

5. **Enhance "Testing Strategy" section**
   - From: wrist-arcana's comprehensive approach
   - Add AAA pattern examples
   - Add mocking guidance
   - Add coverage targets per component type

### Medium Priority

6. **Add "Skills Catalog"**
   - From: ml-odyssey's 82 skills
   - Start with 10-15 common automation tasks
   - Repository setup, code generation, quality checks, git workflows

7. **Add "Most Common Mistakes" section**
   - From: ml-odyssey's 64+ patterns analysis
   - Top 10 mistakes from PR reviews
   - Percentages showing frequency

8. **Add performance targets**
   - From: wrist-arcana's <100ms targets
   - Generation time targets
   - API latency expectations

9. **Document delegation patterns**
   - From: ml-odyssey's 5 delegation patterns
   - When to use which agent
   - Multi-agent workflows

### Low Priority

10. **Add visual diagrams**
    - From: ml-odyssey's tables and wrist-arcana's ASCII art
    - Generator workflow diagram
    - AI orchestration flow

11. **Add troubleshooting section**
    - From: wrist-arcana's troubleshooting
    - Common errors and solutions
    - Debug commands

12. **Add "Zero-Warnings Policy"**
    - From: ml-odyssey's compiler discipline
    - Make warnings explicit failures
    - Document why this matters

---

## Conclusion

### What SGSG Already Does Best

1. **Quality Enforcement**: Most comprehensive quality standards and enforcement
2. **Stay Green Workflow**: Most rigorous development workflow
3. **DRY Architecture**: Single source of truth pattern with references
4. **No Shortcuts Policy**: Most detailed anti-patterns documentation
5. **Tool Invocation Patterns**: Best tables showing correct vs incorrect usage

### What SGSG Should Adopt

1. **Critical Principles Section** (from specinit) - Immediate clarity
2. **Clear 8-10 Section Structure** (from wrist-arcana) - Better navigation
3. **Code Examples Throughout** (from ml-odyssey/wrist-arcana) - Concrete guidance
4. **Security Guidelines** (from specinit) - Essential for repo generator
5. **Skills Catalog** (from ml-odyssey) - Automation clarity
6. **Enhanced Testing Strategy** (from wrist-arcana) - More actionable

### Implementation Strategy

**Phase 3 (Enhancement Plan)**: Prioritize changes by impact
**Phase 4 (Implementation)**: Start with high-priority items
**Phase 5 (Validation)**: Test with AI agents to verify effectiveness

---

**The amalgamated CLAUDE.md will combine:**
- SGSG's quality rigor + enforcement
- specinit's critical principles clarity
- wrist-arcana's structural organization
- ml-odyssey's code examples + skills catalog
- WavelengthWatch's subsystem organization

**Result**: Best-in-class CLAUDE.md for both SGSG and all generated repositories.
