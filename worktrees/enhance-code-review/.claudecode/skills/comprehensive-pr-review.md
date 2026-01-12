# Comprehensive PR Review Skill

## Purpose
Provide structured, thorough code reviews that evaluate PRs across multiple dimensions of quality, security, and project compliance.

## Review Structure

When reviewing a pull request, provide analysis in these sections:

### 1. Summary
Brief overview of what the PR does and its scope (2-3 sentences).

### 2. Strengths
What is done well in this PR? Highlight positive aspects:
- Good design decisions
- Well-written code
- Comprehensive tests
- Clear documentation
- Proper error handling
- Security best practices

### 3. Security Concerns
Critical security issues that must be addressed:
- Potential vulnerabilities
- Unsafe operations
- Exposed secrets or credentials
- Input validation issues
- Authentication/authorization flaws
- Dependency vulnerabilities

**Severity Levels:**
- 🔴 **BLOCKING**: Must fix before merge
- 🟡 **HIGH**: Should fix soon
- 🟢 **LOW**: Nice to have

### 4. Problems
Critical issues that block merging:
- Bugs or incorrect logic
- Breaking changes
- Performance issues
- Missing tests
- Failing CI checks
- Incomplete implementations

### 5. Code Quality
Non-blocking quality improvements:
- Readability issues
- Naming conventions
- Code organization
- Duplication
- Complexity
- Missing documentation

### 6. CLAUDE.md Adherence
Check against project-specific requirements from CLAUDE.md:
- ✅ 90% test coverage met?
- ✅ 95% docstring coverage met?
- ✅ Ruff ALL rules passing?
- ✅ MyPy strict mode passing?
- ✅ No forbidden patterns used?
- ✅ Conventional commits followed?
- ✅ All acceptance criteria met?

### 7. Testing
Evaluate test quality:
- Are there tests for new functionality?
- Do tests cover edge cases?
- Are integration tests included?
- Is mutation testing passing?
- Are test names descriptive?

### 8. Documentation
Check documentation completeness:
- Docstrings on all public APIs?
- README updated if needed?
- CHANGELOG updated?
- Comments explain complex logic?
- Examples provided where helpful?

### 9. Requests
Medium-priority improvements or suggestions:
- Refactoring opportunities
- Performance optimizations
- Additional tests
- Documentation enhancements
- Future considerations

### 10. Verdict
Clear final decision with reasoning:

**Options:**
- ✅ **LGTM** - Looks Good To Me, ready to merge
- 🔄 **CHANGES_REQUESTED** - Must address blocking issues before merge
- 💬 **COMMENTS** - Suggestions only, approve with minor improvements

**Reasoning:**
Explain why you're giving this verdict. Reference specific issues if CHANGES_REQUESTED.

## Example Review Format

```markdown
## Code Review

### Summary
This PR implements the XYZ feature, adding 3 new modules and 200 lines of code with comprehensive tests.

### Strengths
- Excellent test coverage (95%) with property-based tests
- Clear, descriptive function names
- Proper error handling with custom exceptions
- Well-documented with Google-style docstrings

### Security Concerns
None identified. Input validation is proper and no unsafe operations detected.

### Problems
🔴 **BLOCKING**:
1. `process_data()` in `core.py:42` can raise unhandled `ValueError` - needs try/catch
2. Missing integration tests for the API endpoint

### Code Quality
- `utils.py:15-30` has cyclomatic complexity of 12, exceeds limit of 10
- Consider extracting `_validate_input()` helper function
- Variable name `tmp` should be more descriptive

### CLAUDE.md Adherence
- ✅ 95% test coverage (exceeds 90% requirement)
- ✅ 98% docstring coverage (exceeds 95% requirement)
- ✅ Ruff ALL rules passing
- ✅ MyPy strict mode passing
- ❌ One forbidden pattern: print statement in `debug.py:22` (use logging)
- ✅ Conventional commits followed

### Testing
- Strong unit test coverage
- Good use of fixtures and parameterization
- Missing: Integration test for end-to-end flow
- Mutation score: 85% (exceeds 80% requirement)

### Documentation
- All public APIs have docstrings
- README updated with new feature
- Examples are clear and helpful
- Consider adding architecture diagram

### Requests
- Refactor `process_data()` to reduce complexity
- Add type hints to internal helper functions
- Consider adding performance benchmarks

### Verdict
🔄 **CHANGES_REQUESTED**

**Reasoning:**
Two blocking issues must be fixed:
1. Unhandled exception in `process_data()`
2. Missing integration tests

Also needs to fix the forbidden print statement. Once these are addressed, this will be ready to merge. The code quality is otherwise excellent.
```

## Guidelines

- Be specific: Reference file names and line numbers
- Be constructive: Suggest solutions, not just problems
- Be thorough: Check all aspects of quality
- Be fair: Acknowledge what's done well
- Be clear: Use severity levels for security/problems
- Be consistent: Follow this structure every time

## When to Use

Use this skill for all PR reviews to ensure:
- Nothing is missed
- Quality standards are maintained
- Reviews are consistent across the team
- Security is prioritized
- Project-specific requirements are checked
