# Testing Strategy

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Workflow](workflow.md) | [Tools →](tools.md)

---


### 1 Test Organization

```
tests/
├── unit/                           # Fast, isolated tests
│   ├── ai/
│   ├── config/
│   ├── generators/
│   └── utils/
├── integration/                    # Component interaction tests
│   ├── test_generator_integration.py
│   └── test_ai_config_flow.py
├── e2e/                           # End-to-end workflow tests
│   └── test_full_generation_flow.py
└── fixtures/                       # Shared test data
    ├── conftest.py               # Pytest configuration
    └── data/
```

### 2 Test Structure (AAA Pattern)

All tests follow **Arrange-Act-Assert** structure for clarity:

```python
def test_generator_creates_valid_ci_workflow():
    """Test CI generator creates valid GitHub Actions workflow."""
    # Arrange: Set up test data and mocks
    generator = CIGenerator(language="python")
    target_path = tmp_path / "output"
    target_path.mkdir()

    # Act: Execute the functionality being tested
    result = generator.generate(target_path)

    # Assert: Verify expected outcomes
    assert result.success
    workflow_file = target_path / ".github" / "workflows" / "ci.yml"
    assert workflow_file.exists()

    workflow = yaml.safe_load(workflow_file.read_text())
    assert workflow["jobs"]["test"]["runs-on"] == "ubuntu-latest"
    assert "pytest" in workflow["jobs"]["test"]["steps"][-1]["run"]
```

**Benefits**:
- **Arrange**: Clear setup makes test reproducible
- **Act**: Single action makes test focused
- **Assert**: Explicit checks make failures obvious

### 3 Mocking Patterns

#### Mock AI Orchestrator

```python
@pytest.fixture
def mock_orchestrator(mocker):
    """Mock AI orchestrator for generator tests."""
    mock = mocker.Mock(spec=AIOrchestrator)
    mock.generate.return_value = GenerationResult(
        content="# Generated Content\\n\\nThis is a test.",
        format="markdown",
        token_usage=TokenUsage(input_tokens=100, output_tokens=50),
        model="claude-sonnet-4-5-20250929",
        message_id="msg_test123",
    )
    return mock

def test_generator_uses_ai_orchestrator(mock_orchestrator):
    """Test generator calls AI orchestrator with correct prompt."""
    generator = READMEGenerator(orchestrator=mock_orchestrator)

    result = generator.generate(project_name="test-project", language="python")

    # Verify orchestrator was called
    mock_orchestrator.generate.assert_called_once()
    call_args = mock_orchestrator.generate.call_args

    # Verify prompt includes project details
    assert "test-project" in call_args[0][0]  # prompt argument
    assert call_args[1]["output_format"] == "markdown"
```

#### Mock Template Environment

```python
@pytest.fixture
def mock_template_env(tmp_path):
    """Mock Jinja2 environment with test templates."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create test template
    (templates_dir / "config.yml.j2").write_text("""
name: {{ project_name }}
language: {{ language }}
""")

    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    return env

def test_generator_renders_template(mock_template_env):
    """Test generator renders template with correct context."""
    template = mock_template_env.get_template("config.yml.j2")
    result = template.render(project_name="test", language="python")

    assert "name: test" in result
    assert "language: python" in result
```

#### Mock File System Operations

```python
def test_generator_creates_directory_structure(tmp_path, mocker):
    """Test generator creates expected directory structure."""
    # Mock Path.mkdir to track calls
    mkdir_spy = mocker.spy(Path, "mkdir")

    generator = ScaffoldGenerator()
    generator.create_structure(tmp_path)

    # Verify mkdir called for each expected directory
    expected_dirs = ["src", "tests", "docs", "scripts"]
    for dir_name in expected_dirs:
        assert any(
            str(call[0][0]).endswith(dir_name)
            for call in mkdir_spy.call_args_list
        )
```

### 4 Coverage Targets

| Component Type | Minimum | Target | Rationale |
|----------------|---------|--------|-----------|
| **Generators** | 95% | 98%+ | Core functionality, must be bulletproof |
| **AI Integration** | 90% | 95%+ | Complex logic, many edge cases |
| **Utils** | 90% | 95%+ | Widely reused, bugs multiply |
| **CLI** | 80% | 85%+ | User-facing, some UI code hard to test |
| **Configuration** | 85% | 90%+ | Critical for project setup |
| **Templates** | N/A | N/A | Tested via integration tests |

**Overall Project**: 90% minimum, 97%+ target (current: 97.22%)

**Enforcement**: `pytest --cov-fail-under=90` in `scripts/test.sh`

### 5 Test Naming Convention

```python
# Format: test_<unit>_<scenario>_<expected_outcome>

# Examples:
def test_orchestrator_generate_with_valid_prompt_returns_result():
    """Test orchestrator generates content with valid input."""
    pass

def test_config_loader_missing_file_raises_file_not_found():
    """Test loader raises FileNotFoundError for missing config."""
    pass

def test_generator_empty_config_raises_validation_error():
    """Test generator rejects empty configuration."""
    pass
```

### 6 Property-Based Testing

Use Hypothesis for generators to test invariants:

```python
from hypothesis import given, strategies as st

@given(
    language=st.sampled_from(["python", "typescript", "go", "rust"]),
    project_name=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            blacklist_characters="/\\:*?\"<>|",
        ),
    ),
)
def test_generator_handles_all_valid_inputs(language, project_name):
    """Test generator handles all combinations of valid inputs."""
    generator = ProjectGenerator(language=language)

    # Should either succeed or fail with clear error
    try:
        result = generator.validate_name(project_name)
        assert result.is_valid
    except ValueError as e:
        # If validation fails, error message must be clear
        assert project_name in str(e) or language in str(e)

@given(
    config=st.fixed_dictionaries({
        "name": st.text(min_size=1, max_size=100),
        "language": st.sampled_from(["python", "typescript", "go"]),
        "include_ci": st.booleans(),
        "include_tests": st.booleans(),
    })
)
def test_config_generator_is_idempotent(config, tmp_path):
    """Test generator produces same output for same input."""
    generator = ConfigGenerator()

    # Generate twice with same input
    result1 = generator.generate(tmp_path / "out1", **config)
    result2 = generator.generate(tmp_path / "out2", **config)

    # Outputs should be identical
    assert result1.files_created == result2.files_created
    for file_name in result1.files_created:
        content1 = (tmp_path / "out1" / file_name).read_text()
        content2 = (tmp_path / "out2" / file_name).read_text()
        assert content1 == content2
```

**When to Use**:
- Testing invariants (idempotency, commutativity)
- Validating input handling across wide range
- Finding edge cases you didn't think of

### 7 Mutation Testing

Every test suite must pass mutation testing. This ensures tests are effective at catching bugs:

```bash
# Run mutation tests with 80% minimum score (MAXIMUM QUALITY)
./scripts/mutation.sh

# Run with custom threshold
./scripts/mutation.sh --min-score 70

# View results
mutmut results
mutmut html

# View specific surviving mutants
mutmut show <id>

# Score must be 80%+ for MAXIMUM QUALITY
```

**Important**: Use `./scripts/mutation.sh` instead of running `mutmut` directly. The script enforces the 80% minimum threshold and provides clear feedback.

---



---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Workflow](workflow.md) | [Tools →](tools.md)
