# Integration Tests

This directory contains comprehensive integration tests for the Start Green Stay Green project. Integration tests verify the interactions between multiple components and end-to-end workflows.

## Test Organization

Integration tests are organized by functional area:

### test_ai_orchestration_flow.py

Tests the complete AI generation workflow including:

- **AIOrchestrator Initialization**: API key validation, context setup, credentials verification
- **Template Loading**: Loading templates, variable processing, syntax validation
- **Content Generation**: AI-powered content creation with prompts
- **Tuning and Validation**: Response tuning, structure validation, output formatting
- **End-to-End Flow**: Complete orchestration workflow with error recovery

**Key Test Classes:**
- `TestAIOrchestratorInitialization`: Orchestrator setup and validation
- `TestTemplateLoadingAndProcessing`: Template operations
- `TestContentGeneration`: AI content generation
- `TestTuningAndValidation`: Response processing
- `TestEndToEndOrchestrationFlow`: Complete workflows

### test_generator_integration.py

Tests generator orchestration and multi-generator workflows:

- **Generator Initialization**: Configuration validation, output directory setup
- **Specific Generators**: Tests for CI, pre-commit, scripts, CLAUDE.md, GitHub Actions
- **File Creation**: Writing files and directories to disk
- **Multi-Generator Orchestration**: Running multiple generators, execution order, configuration sharing
- **Error Handling**: Generator failures and recovery

**Key Test Classes:**
- `TestGeneratorInitialization`: Generator setup
- `TestSpecificGenerators`: Individual generator implementations
- `TestFileCreationFromGenerators`: File system operations
- `TestMultiGeneratorOrchestration`: Generator coordination
- `TestCLIToGeneratorIntegration`: CLI communication

### test_github_workflow_integration.py

Tests GitHub API integration and repository setup:

- **GitHub Client**: Authentication, user info retrieval, rate limit handling
- **Repository Creation**: Repository creation, configuration, topic management
- **GitHub Actions**: Workflow creation, action enablement, branch protection
- **Integration Setup**: Webhooks, deploy keys, repository secrets
- **Error Handling**: Authentication, rate limits, and network errors

**Key Test Classes:**
- `TestGitHubClientInitialization`: Client setup and authentication
- `TestRepositoryCreation`: Repository management
- `TestGitHubActionsWorkflow`: Workflow setup
- `TestGitHubIntegrationConfiguration`: Integration configuration
- `TestGitHubAPIErrorHandling`: Error scenarios
- `TestEndToEndGitHubWorkflow`: Complete workflows

### test_end_to_end_project_creation.py

Tests the complete `green init` project creation workflow:

- **Complete Project Initialization**: All components, directories, files
- **Language-Specific Setup**: Python, TypeScript, Go, Rust
- **Quality Infrastructure**: CI/CD, pre-commit, scripts, testing
- **Project Validation**: Structure, configuration, syntax, readiness
- **Error Handling**: Generator failures, cleanup, error messages

**Key Test Classes:**
- `TestCompleteProjectInitialization`: End-to-end project setup
- `TestLanguageSpecificSetup`: Language configurations
- `TestQualityInfrastructureSetup`: Infrastructure setup
- `TestProjectValidation`: Validation checks
- `TestProjectReadiness`: Readiness verification
- `TestErrorHandlingAndRecovery`: Error scenarios

### test_init_command.py

Tests the complete init command orchestration (pre-existing):

- Command execution
- Project directory creation
- Required directories and files
- Language support
- Generator orchestration
- Error handling
- Configuration management
- Git integration

## Testing Approach

### Use of Mocks

All integration tests use mocks to avoid external dependencies:

```python
# Example: Mocking external API
with patch("start_green_stay_green.github.client.GitHubClient") as mock:
    mock_instance = AsyncMock()
    mock.return_value = mock_instance
    mock_instance.verify_authentication = AsyncMock(return_value=True)

    result = await mock_instance.verify_authentication()
    assert result is True
```

### Temporary Directories

Tests use `temp_directory` fixture for file operations:

```python
@pytest.mark.asyncio
async def test_generator_creates_file(self, temp_directory: Path) -> None:
    """Test generator creates file on disk."""
    output_file = temp_directory / "test.txt"
    # ... test code ...
```

### Fixtures

Shared fixtures are defined in `tests/conftest.py`:

- `sample_api_key`: Sample API key for testing
- `sample_context`: Sample context variables
- `sample_prompt_template`: Sample prompt template
- `temp_directory`: Temporary directory for file operations
- `sample_project_config`: Sample project configuration
- `sample_generator_output`: Sample generator output

## Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test class
pytest tests/integration/test_ai_orchestration_flow.py::TestAIOrchestratorInitialization -v

# Run specific test
pytest tests/integration/test_ai_orchestration_flow.py::TestAIOrchestratorInitialization::test_orchestrator_initializes_with_api_key -v

# Run with coverage
pytest tests/integration/ --cov=start_green_stay_green --cov-report=term-missing

# Run integration tests only (without unit/e2e)
pytest tests/integration/ -m integration -v
```

## Coverage Goals

- **Target**: 80%+ coverage of integration paths
- **Execution Time**: Tests should complete in < 2 minutes
- **Cleanup**: No leftover files after test execution
- **Isolation**: Tests should not affect each other

## Test Patterns

### Pattern 1: Initialization Testing

```python
@pytest.mark.asyncio
async def test_component_initializes(self) -> None:
    """Test component initialization."""
    with patch("module.Component") as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        mock_instance.config = {"key": "value"}

        assert mock_instance.config == {"key": "value"}
```

### Pattern 2: Operation Testing

```python
@pytest.mark.asyncio
async def test_component_performs_operation(self) -> None:
    """Test component operation."""
    with patch("module.Component") as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        mock_instance.do_something = AsyncMock(return_value="result")

        result = await mock_instance.do_something()

        assert result == "result"
        mock_instance.do_something.assert_called_once()
```

### Pattern 3: Error Handling

```python
@pytest.mark.asyncio
async def test_component_handles_error(self) -> None:
    """Test component error handling."""
    with patch("module.Component") as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        mock_instance.do_something = AsyncMock(
            side_effect=ValueError("Error message")
        )

        with pytest.raises(ValueError):
            await mock_instance.do_something()
```

### Pattern 4: End-to-End Workflow

```python
@pytest.mark.asyncio
async def test_complete_workflow(self) -> None:
    """Test complete workflow."""
    with patch("module.Orchestrator") as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance

        # Setup complete workflow
        mock_instance.step1 = AsyncMock(return_value={})
        mock_instance.step2 = AsyncMock(return_value={})
        mock_instance.step3 = AsyncMock(return_value={"success": True})

        result = await mock_instance.step3()

        assert result["success"] is True
```

## Dependencies

Integration tests depend on:

- `pytest`: Test framework
- `pytest-asyncio`: Async test support
- `pytest-mock`: Mocking utilities
- `pytest-cov`: Coverage reporting

These are included in the development dependencies in `pyproject.toml`.

## Maintenance

When adding new components or workflows:

1. Identify the integration points
2. Create appropriate test class
3. Mock external dependencies
4. Test both happy path and error cases
5. Ensure proper cleanup (temporary files)
6. Update this README with new test descriptions

## Notes

- All tests use async/await for consistency with async codebase
- Mocks are used extensively to avoid external dependencies
- Tests focus on component interactions, not implementation details
- Temporary directories are used for file operations
- Error handling is tested for all critical operations
