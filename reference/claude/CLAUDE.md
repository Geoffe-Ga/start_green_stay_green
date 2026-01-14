# Claude Code Project Context

## Project Overview
Start Green Stay Green - A meta-tool for generating quality-controlled, AI-ready repositories with enterprise-grade quality controls pre-configured.

## Architecture

### Core Philosophy
- **Maximum Quality**: No shortcuts, comprehensive tooling, strict enforcement
- **AI-First**: Designed for AI-assisted development workflows
- **Composable**: Modular generators for each quality component
- **Multi-Language**: Support for Python, TypeScript, Go, Rust, and more

### Component Structure
```
start_green_stay_green/
├── ai/              # AI orchestration and generation
├── config/          # Configuration management
├── generators/      # Component generators (CI, scripts, etc.)
├── github/          # GitHub integration
└── utils/           # Common utilities
```

## Quality Standards

### Code Quality Tools
- **Ruff**: ALL rules enabled (no exceptions except formatter conflicts)
- **MyPy**: Strict mode, no untyped definitions
- **Pytest**: 90% coverage minimum, mutation testing
- **Bandit**: Security scanning with no skips

### Coverage Requirements
- **Code Coverage**: 90% minimum (branch coverage)
- **Docstring Coverage**: 95% minimum (interrogate)
- **Mutation Score**: Track and improve continuously

### Complexity Limits
- **Cyclomatic Complexity**: Max 10 per function
- **Maintainability Index**: Minimum 20 (radon)
- **Max Arguments**: 5 per function
- **Max Branches**: 12 per function

## Development Workflow

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `bugfix/*`: Bug fixes
- `hotfix/*`: Emergency fixes

### Commit Convention
Follow Conventional Commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### Stay Green Workflow

**Policy**: Never request review with failing checks. Never merge without LGTM.

Follow these **4 sequential gates** for every code change:

**Gate 1: Local Pre-Commit** (Iterate Until Green)
- Run `./scripts/check-all.sh`
- Fix all formatting, linting, types, complexity, security issues
- Fix tests and coverage (90%+ required)
- Only push when all local checks pass (exit code 0)

**Gate 2: CI Pipeline** (Iterate Until Green)
- Push to branch: `git push origin feature-branch`
- Monitor CI: `gh pr checks --watch`
- If CI fails: fix locally, re-run Gate 1, push again
- Only proceed when all CI jobs show ✅

**Gate 3: Mutation Testing** (Iterate Until 80%+)
- Run `./scripts/mutation.sh` (or wait for CI job)
- If score < 80%: add tests to kill surviving mutants
- Re-run Gate 1, push, wait for CI
- Only proceed when mutation score ≥ 80%

**Gate 4: Code Review** (Iterate Until LGTM)
- Wait for code review (AI or human)
- If feedback provided: address ALL concerns
- Re-run Gate 1, push, wait for CI and mutation
- Only merge when review shows LGTM with no reservations

**Quick Checklist** before merging:
- [ ] Gate 1: `./scripts/check-all.sh` passes locally (exit 0)
- [ ] Gate 2: All CI jobs show ✅ (green)
- [ ] Gate 3: Mutation score ≥ 80% (if applicable)
- [ ] Gate 4: Code review shows LGTM
- [ ] Ready to merge!

**Anti-Patterns** (DO NOT DO):
- ❌ Don't request review with failing CI
- ❌ Don't skip local checks (`git commit --no-verify`)
- ❌ Don't lower quality thresholds to pass
- ❌ Don't ignore review feedback
- ❌ Don't merge without LGTM

## Testing Strategy

### Test Types
1. **Unit Tests**: Test individual functions/classes in isolation
2. **Integration Tests**: Test component interactions
3. **E2E Tests**: Test complete workflows
4. **Property-Based Tests**: Use Hypothesis for edge cases
5. **Mutation Tests**: Verify test effectiveness

### Test Organization
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests
├── fixtures/       # Shared test data
└── e2e/           # End-to-end scenarios
```

## AI Subagent Guidelines

### Available Subagents
- **chief-architect**: Strategic decisions and system design
- **foundation-orchestrator**: Repository foundation setup
- **implementation-engineer**: Standard implementation work
- **test-engineer**: Test suite development
- **security-specialist**: Security reviews and fixes

### When to Use Subagents
1. **Complex multi-step tasks** - Use appropriate orchestrator
2. **Specialized reviews** - Use review specialists
3. **Parallel work** - Coordinate multiple agents
4. **Phase-based development** - Use hierarchical delegation

### Subagent Communication
- Clear, specific task descriptions
- Include acceptance criteria
- Reference relevant files/issues
- Specify dependencies between tasks

## Skills to Apply

### Vibe Skill
- Consistent code style across the project
- Clear, descriptive naming
- Proper docstrings for all public APIs
- Type hints on all functions
- No abbreviations in names

### Concurrency Skill
- Use asyncio for I/O-bound AI operations
- ThreadPoolExecutor for parallel file operations
- Proper error handling in concurrent code
- Resource cleanup with context managers

## Common Patterns

### Generator Pattern
All generators inherit from base generator:
```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseGenerator(ABC):
    """Base class for all component generators."""

    @abstractmethod
    def generate(self, target_path: Path, config: dict) -> None:
        """Generate component at target path with configuration."""
        pass
```

### AI Integration Pattern
```python
from anthropic import Anthropic

async def generate_with_ai(
    prompt: str,
    context: dict[str, str]
) -> str:
    """Generate content using Claude API."""
    client = Anthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

## Key Files

### Configuration
- `pyproject.toml`: All tool configurations
- `requirements.txt`: Runtime dependencies
- `requirements-dev.txt`: Development dependencies

### Documentation
- `plan/SPEC.md`: Complete project specification
- `plan/MAXIMUM_QUALITY_ENGINEERING.md`: Quality framework
- `reference/`: Reference implementations and examples

### Entry Points
- `start_green_stay_green/cli.py`: CLI implementation
- `start_green_stay_green/ai/orchestrator.py`: AI coordination

## Important Notes

### Never Skip
- Type checking
- Security scanning
- Test coverage
- Docstring coverage
- Conventional commits

### Always Include
- Type hints on all functions
- Docstrings on all public APIs
- Error handling for external operations
- Tests for all new functionality
- Updates to relevant documentation

### Prefer
- Composition over inheritance
- Explicit over implicit
- Standard library over third-party (when reasonable)
- Async/await over callbacks
- Pathlib over os.path
- Dataclasses/Pydantic over dicts

## External Resources
- [MAXIMUM_QUALITY_ENGINEERING.md](../plan/MAXIMUM_QUALITY_ENGINEERING.md)
- [SPEC.md](../plan/SPEC.md)
- [Agent Documentation](../agents/)
