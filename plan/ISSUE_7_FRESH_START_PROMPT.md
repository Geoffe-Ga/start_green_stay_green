# Issue #7: AI Orchestrator - Fresh Start Implementation Guide

**Issue**: #7 - Implement AI generation orchestrator
**Branch**: `feature/7-ai-orchestrator-v2`
**Status**: Ready for implementation
**RCA Reference**: `/plan/RCA_PR37_AI_ORCHESTRATOR_FAILURE.md`

---

## Prerequisites

Before starting, verify:

```bash
# 1. Switch to main branch
git checkout main
git pull origin main

# 2. Verify baseline passes
./scripts/check-all.sh

# 3. Create fresh branch
git checkout -b feature/7-ai-orchestrator-v2

# 4. Verify branch baseline
./scripts/check-all.sh
```

All checks MUST pass before proceeding.

---

## Implementation Phases

### Phase 1: Data Classes (No External Dependencies)

**Goal**: Implement the data structures used by the orchestrator.

**Step 1.1: Create Test File**
```bash
# Create test file first (TDD)
touch tests/unit/ai/test_orchestrator.py
```

**Step 1.2: Write First Test**
```python
"""Unit tests for AI Orchestrator data classes."""

import pytest

from start_green_stay_green.ai.orchestrator import TokenUsage


class TestTokenUsage:
    """Test TokenUsage data class."""

    def test_token_usage_calculates_total_correctly(self) -> None:
        """Test TokenUsage calculates total tokens correctly."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150
```

**Step 1.3: Run Checks (Should Fail)**
```bash
./scripts/check-all.sh
# Expected: ImportError - TokenUsage doesn't exist
```

**Step 1.4: Implement TokenUsage**
```python
# In start_green_stay_green/ai/orchestrator.py
from dataclasses import dataclass

@dataclass(frozen=True)
class TokenUsage:
    """Token usage information from API response.

    Attributes:
        input_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens in the response.
    """

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used.

        Returns:
            Sum of input and output tokens.
        """
        return self.input_tokens + self.output_tokens
```

**Step 1.5: Run Checks (Should Pass)**
```bash
./scripts/check-all.sh
# All checks must pass before continuing
```

**Step 1.6: Commit**
```bash
git add -A
git commit -m "feat(ai): add TokenUsage data class (#7)"
```

**Repeat for**:
- `GenerationConfig` data class
- `GenerationResult` data class
- `ModelConfig` constants class

---

### Phase 2: Exception Classes

**Goal**: Implement custom exception types.

**Step 2.1: Write Tests First**
```python
class TestGenerationError:
    """Test GenerationError exception."""

    def test_generation_error_with_message_stores_message(self) -> None:
        """Test GenerationError stores message."""
        error = GenerationError("Test error")
        assert str(error) == "Test error"

    def test_generation_error_with_cause_stores_cause(self) -> None:
        """Test GenerationError stores underlying cause."""
        cause = ValueError("Original error")
        error = GenerationError("Wrapped", cause=cause)
        assert error.cause is cause
```

**Step 2.2: Implement, Check, Commit**

```bash
# After implementation
./scripts/check-all.sh  # Must pass
git commit -m "feat(ai): add GenerationError exception class (#7)"
```

---

### Phase 3: AIOrchestrator Core

**Goal**: Implement the orchestrator class with mocked API.

**Step 3.1: Write Initialization Tests**
```python
class TestAIOrchestrator:
    """Test AIOrchestrator class."""

    def test_orchestrator_init_with_api_key_stores_key(self) -> None:
        """Test orchestrator stores API key."""
        orchestrator = AIOrchestrator(api_key="test-key")
        assert orchestrator.api_key == "test-key"

    def test_orchestrator_init_with_empty_key_raises_error(self) -> None:
        """Test orchestrator rejects empty API key."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            AIOrchestrator(api_key="")
```

**Step 3.2: Implement Minimal __init__**
```python
class AIOrchestrator:
    """Coordinates AI-powered generation tasks."""

    def __init__(self, api_key: str) -> None:
        """Initialize AIOrchestrator.

        Args:
            api_key: Anthropic API key.

        Raises:
            ValueError: If api_key is empty.
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        self.api_key = api_key
```

**Step 3.3: Check and Commit**
```bash
./scripts/check-all.sh  # Must pass
git commit -m "feat(ai): add AIOrchestrator initialization (#7)"
```

---

### Phase 4: Context Injection

**Goal**: Implement prompt template processing.

**Test First**:
```python
def test_inject_context_replaces_variables(self) -> None:
    """Test context injection replaces template variables."""
    orchestrator = AIOrchestrator(api_key="test")
    result = orchestrator._inject_context(
        template="Hello {name}",
        context={"name": "World"},
    )
    assert result == "Hello World"
```

---

### Phase 5: API Integration

**Goal**: Implement API calls with proper mocking.

**Important**: When testing invalid types, use proper typing:

```python
from typing import Any

@pytest.mark.asyncio
async def test_generate_with_invalid_format_raises_error(
    self,
    orchestrator: AIOrchestrator,
) -> None:
    """Test generate() raises ValueError for invalid format."""
    invalid_format: Any = "invalid"  # Explicit Any for test
    with pytest.raises(ValueError, match="Invalid output format"):
        await orchestrator.generate(
            prompt_template="Test",
            context={},
            output_format=invalid_format,
        )
```

This avoids the need for `# type: ignore`.

---

### Phase 6: Retry Logic

**Goal**: Implement exponential backoff retry.

---

### Phase 7: Integration Tests

**Goal**: Add integration tests with mocked external services.

---

## Quality Checkpoints

After EVERY phase:

1. `./scripts/check-all.sh` must pass
2. No `# type: ignore` without issue reference
3. No `# noqa` without issue reference
4. No bare `except` clauses
5. 90%+ coverage on new code

---

## Commit Message Format

```
feat(ai): <description> (#7)
```

Examples:
- `feat(ai): add TokenUsage data class (#7)`
- `feat(ai): add AIOrchestrator initialization (#7)`
- `feat(ai): implement context injection (#7)`
- `feat(ai): add retry logic with exponential backoff (#7)`
- `test(ai): add integration tests for orchestrator (#7)`

---

## Pull Request Checklist

Before creating PR:

- [ ] `./scripts/check-all.sh` passes
- [ ] All tests pass with 90%+ coverage
- [ ] No forbidden patterns (type: ignore, noqa, TODO without issue)
- [ ] All public APIs have docstrings
- [ ] Commit history is clean and incremental

---

## References

- [CLAUDE.md](/CLAUDE.md) - Development standards
- [SPEC.md](/plan/SPEC.md) - Project specification
- [Maximum Quality Engineering](/reference/MAXIMUM_QUALITY_ENGINEERING.md) - Quality framework
