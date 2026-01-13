# Mutation Testing Configuration

## Overview

Mutation testing has been configured with MAXIMUM QUALITY standards while maintaining practical, achievable thresholds.

## Configuration Summary

### Threshold: 80% Minimum Mutation Score

This strikes the ideal balance:
- ✅ **High quality**: Ensures test suite catches 80%+ of bugs
- ✅ **Achievable**: Not impossible like 100%, but still rigorous
- ✅ **Industry standard**: Aligns with MAXIMUM QUALITY engineering practices
- ✅ **Meaningful**: Below 80% indicates significant test coverage gaps

### What Changed

1. **pyproject.toml** - Added `[tool.mutmut]` configuration:
   ```toml
   [tool.mutmut]
   paths_to_mutate = "start_green_stay_green/"
   backup = false
   runner = "pytest -x --assert=plain --tb=short -q"
   tests_dir = "tests/"
   dict_synonyms = "Struct, NamedStruct"
   ```

2. **scripts/mutation.sh** - New dedicated mutation testing script:
   - Enforces 80% minimum threshold (configurable via `--min-score`)
   - Provides clear, actionable feedback
   - Shows surviving mutants for debugging
   - Handles edge cases (zero mutants, timeout, etc.)

3. **scripts/test.sh** - Updated to use mutation.sh:
   - `./scripts/test.sh --mutation` now calls `./scripts/mutation.sh`
   - Consistent interface maintained

4. **CI Configuration** (.github/workflows/ci.yml):
   - Updated to use `./scripts/mutation.sh` directly
   - Runs only on main branch (expensive operation)
   - Clear failure messages when threshold not met

5. **Documentation Updates**:
   - CLAUDE.md: Added mutation testing workflows
   - scripts/README.md: Added mutation.sh documentation
   - Clear quality standards documented

## Usage

### Run Mutation Tests Locally

```bash
# Standard run with 80% minimum (MAXIMUM QUALITY)
./scripts/mutation.sh

# Run with custom threshold
./scripts/mutation.sh --min-score 70

# Show detailed output
./scripts/mutation.sh --verbose
```

### View Results

```bash
# Show all results
mutmut results

# View specific surviving mutant
mutmut show <id>

# Generate HTML report
mutmut html
# Open .mutmut-cache/index.html in browser
```

### Run via test.sh

```bash
# Also works
./scripts/test.sh --mutation
```

## Quality Standards

| Mutation Score | Quality Level | Status |
|----------------|---------------|--------|
| 80-100% | MAXIMUM QUALITY | ✅ Pass |
| 70-79% | Good | ⚠️ Consider improvement |
| 60-69% | Acceptable | ⚠️ Needs work |
| <60% | Poor | ❌ Unacceptable |

## How Mutation Testing Works

1. **Mutmut modifies your code** with small changes (mutations):
   - `==` becomes `!=`
   - `+` becomes `-`
   - `True` becomes `False`
   - Function return values changed
   - Etc.

2. **Runs your test suite** against each mutation

3. **Classifies results**:
   - **Killed**: Test suite caught the mutation ✅
   - **Survived**: Mutation went undetected ❌
   - **Suspicious**: Mutation caused timeout
   - **Timeout**: Tests took too long

4. **Calculates score**:
   ```
   Mutation Score = (Killed / Total) × 100%
   ```

## Improving Mutation Score

If your score is below 80%:

1. **Identify surviving mutants**:
   ```bash
   mutmut results
   mutmut show 1  # View first surviving mutant
   ```

2. **Add tests** to catch these mutations:
   - Add edge case tests
   - Test error conditions
   - Verify return values
   - Check boolean conditions

3. **Run again**:
   ```bash
   ./scripts/mutation.sh
   ```

## CI Integration

Mutation testing runs automatically:
- **On main branch**: After merging PRs
- **Not on PRs**: Too slow for every commit
- **Scheduled**: Daily security scan includes mutation testing

To skip mutation testing locally (not recommended):
```bash
# Just run regular tests
./scripts/check-all.sh
```

## Performance Notes

- **Runtime**: Several minutes (depends on codebase size)
- **CPU intensive**: Runs many test iterations
- **Cacheable**: Results cached in `.mutmut-cache/`
- **Incremental**: Only re-tests changed code

Clear cache if needed:
```bash
rm -rf .mutmut-cache
```

## Troubleshooting

### "Warning: No mutants were generated"

This means mutmut found no code to mutate. Check:
- Ensure `start_green_stay_green/` has Python code
- Verify paths in `pyproject.toml` are correct

### "Mutation score below minimum threshold"

Your tests aren't catching all mutations:
1. Run `mutmut show <id>` to see surviving mutants
2. Add tests to catch these mutations
3. Re-run mutation tests

### "Timeout" or "Suspicious" mutants

Tests are taking too long or hanging:
- Add `pytest-timeout` decorator to slow tests
- Optimize test performance
- Consider excluding slow integration tests from mutation testing

## References

- **CLAUDE.md**: Lines 888-909 (Mutation Testing section)
- **pyproject.toml**: Lines 383-389 (Mutmut config)
- **scripts/mutation.sh**: Complete implementation
- **MAXIMUM_QUALITY_ENGINEERING.md**: Quality standards reference

## Why 80% and Not 100%?

**100% mutation score is unrealistic** for several reasons:

1. **Equivalent mutants**: Some mutations are functionally identical
2. **Defensive code**: Error handling that's hard to trigger
3. **Edge cases**: Some mutations are impossible to trigger in normal flow
4. **Diminishing returns**: 80→100% requires exponential effort

**80% hits the sweet spot**:
- High enough to ensure quality
- Low enough to be achievable
- Industry-standard for MAXIMUM QUALITY projects
- Catches vast majority of real bugs

## Summary

✅ **Configured**: Mutation testing with 80% minimum threshold
✅ **Enforced**: Automatic validation in `./scripts/mutation.sh`
✅ **Documented**: Clear standards and workflows
✅ **Integrated**: Works with CI/CD pipeline
✅ **Practical**: Achievable while maintaining MAXIMUM QUALITY

**Result**: You now have enterprise-grade mutation testing that ensures your test suite is effective at catching bugs, without the impossible 100% requirement.
