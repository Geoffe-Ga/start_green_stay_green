# Issue 7: AI Orchestrator Core - Implementation Notes

## Overview

Implemented the core AI orchestration system for coordinating generation tasks using the Anthropic Claude API. The implementation follows TDD principles with comprehensive test coverage and strict quality standards.

## Implementation Summary

### Files Created/Modified

1. **start_green_stay_green/ai/orchestrator.py** (NEW)
   - AIOrchestrator class with generate() and tune() methods
   - GenerationResult and TokenUsage data classes
   - ModelConfig constants for Claude models
   - Custom exceptions: GenerationError, PromptTemplateError
   - Retry logic with exponential backoff
   - Response parsing and validation

2. **start_green_stay_green/ai/__init__.py** (MODIFIED)
   - Exports public API components
   - Comprehensive module docstring

3. **tests/unit/ai/test_orchestrator.py** (NEW)
   - 40+ unit tests covering all functionality
   - Tests for error handling, retry logic, validation
   - Parametrized tests for output formats
   - Mock-based testing of API interactions

4. **tests/integration/test_orchestrator_integration.py** (NEW)
   - Integration tests for end-to-end workflows
   - Multi-format generation tests
   - Retry recovery tests
   - Model switching tests

5. **tests/conftest.py** (NEW)
   - Shared fixtures for test suite

## Key Features Implemented

### 1. AI Orchestrator Core
- **Initialization**: API key validation, configurable retry parameters
- **Generate Method**:
  - Template-based prompt construction
  - Context variable injection
  - Format-specific instructions (YAML, TOML, Markdown, Bash)
  - Response validation
  - Token usage tracking
- **Tune Method**:
  - Lightweight content adaptation
  - Uses Sonnet by default for cost efficiency
  - Context-aware tuning prompts

### 2. Error Handling
- Custom exception hierarchy
- Retry logic with exponential backoff
- Rate limit handling with delays
- Timeout recovery
- Detailed error messages with cause tracking

### 3. Response Processing
- Content extraction from API responses
- Empty response validation
- Token usage calculation
- Metadata capture (model, message_id, stop_reason)

### 4. Configuration
- Model constants (Opus for generation, Sonnet for tuning)
- Configurable retry parameters
- Temperature and max_tokens control
- Format validation

## Test Coverage

### Unit Tests (40+ tests)
- Initialization validation
- Input validation (empty prompts, missing context)
- Format validation
- Error handling (timeouts, rate limits, API errors)
- Retry logic verification
- Token usage tracking
- Context injection
- Response validation
- Model configuration

### Integration Tests (7 tests)
- Full generation workflow
- Tuning workflow
- Retry recovery
- Multiple format generation
- Complex context injection
- Model switching

## Quality Standards Met

### Code Quality
- ✅ Type hints on all functions (MyPy strict mode compatible)
- ✅ Google-style docstrings with examples
- ✅ Error handling with specific exceptions
- ✅ Comprehensive logging
- ✅ No TODO/FIXME without issue references
- ✅ No bare except clauses
- ✅ Input validation on all public methods

### Testing
- ✅ TDD approach (tests written first)
- ✅ Unit and integration test coverage
- ✅ Mock-based testing for external APIs
- ✅ Parametrized tests for variations
- ✅ Async test support
- ✅ Edge case coverage

### Documentation
- ✅ Module-level docstrings
- ✅ Class docstrings with examples
- ✅ Function docstrings with Args/Returns/Raises
- ✅ Type annotations in docstrings
- ✅ Code examples in docstrings

## API Interface

### AIOrchestrator

```python
class AIOrchestrator:
    def __init__(
        self,
        api_key: str,
        model: str = ModelConfig.OPUS,
        *,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ) -> None: ...

    async def generate(
        self,
        prompt_template: str,
        context: dict[str, str],
        output_format: Literal["yaml", "toml", "markdown", "bash"],
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> GenerationResult: ...

    async def tune(
        self,
        content: str,
        target_context: str,
        model: str = ModelConfig.SONNET,
        *,
        max_tokens: int = 4096,
    ) -> str: ...
```

### Data Models

```python
@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int: ...

@dataclass(frozen=True)
class GenerationResult:
    content: str
    format: OutputFormat
    token_usage: TokenUsage
    model: str
    message_id: str
```

### Model Configuration

```python
class ModelConfig:
    OPUS: str = "claude-opus-4-20250514"
    SONNET: str = "claude-sonnet-4-20250514"
```

## Usage Examples

### Basic Generation

```python
from start_green_stay_green.ai import AIOrchestrator

orchestrator = AIOrchestrator(api_key="sk-...")

result = await orchestrator.generate(
    prompt_template="Create README for {language} project",
    context={"language": "Python"},
    output_format="markdown",
)

print(f"Generated {result.token_usage.total_tokens} tokens")
print(result.content)
```

### Content Tuning

```python
tuned = await orchestrator.tune(
    content="# Generic Project\n...",
    target_context="Python project with pytest and black",
)
```

### Custom Model

```python
from start_green_stay_green.ai import ModelConfig

result = await orchestrator.generate(
    prompt_template="Complex analysis task",
    context={},
    output_format="yaml",
    model=ModelConfig.OPUS,  # Override default
)
```

## Design Decisions

### 1. Async API
- All I/O operations are async for performance
- Uses asyncio.to_thread for Anthropic client (which is sync)
- Enables concurrent generation tasks

### 2. Immutable Data Classes
- GenerationResult and TokenUsage are frozen dataclasses
- Prevents accidental mutation
- Thread-safe by design

### 3. Exponential Backoff
- Initial delay: 1 second
- Doubles on each retry
- Max delay: 60 seconds
- Prevents overwhelming API during outages

### 4. Model Selection
- Opus for generation (higher quality)
- Sonnet for tuning (cost-efficient)
- Overridable per-call

### 5. Format-Specific Instructions
- Each output format has tailored instructions
- Ensures valid output (shebang for bash, proper YAML indent, etc.)
- Reduces post-processing needs

## Next Steps

This implementation completes Issue 2.1. The orchestrator is now ready for use in:
- Issue 2.2: Prompt Templates
- Issue 2.3: Response Validators
- Generator implementations (Epic 3)

## Acceptance Criteria Status

- ✅ `ai/orchestrator.py` implemented
- ✅ Anthropic API client configured
- ✅ Prompt template loading system
- ✅ Context injection from reference files (via context dict)
- ✅ Response parsing and validation
- ✅ Error handling and retry logic
- ✅ Token usage tracking
- ✅ Both generate() and tune() methods implemented
- ✅ Uses claude-opus-4-20250514 for generate
- ✅ Uses claude-sonnet-4-20250514 for tune
- ✅ TDD approach followed
- ✅ Comprehensive test coverage
- ✅ Type annotations (MyPy strict compatible)
- ✅ Comprehensive docstrings

## Testing Instructions

```bash
# Run all tests
./scripts/test.sh

# Run only orchestrator tests
pytest tests/unit/ai/test_orchestrator.py -v

# Run integration tests
pytest tests/integration/test_orchestrator_integration.py -v

# Check coverage
./scripts/coverage.sh

# Run all quality checks
./scripts/check-all.sh
```

## Notes

- Anthropic client is synchronous, wrapped with asyncio.to_thread
- Retry logic only retries on RateLimitError and APITimeoutError
- General APIError exceptions are not retried (fail fast)
- Empty responses are rejected with GenerationError
- All context variables must be present in template
