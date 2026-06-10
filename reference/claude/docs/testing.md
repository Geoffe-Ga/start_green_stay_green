# Testing Strategy

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Workflow](workflow.md) | [Tools →](tools.md)

---

## 1. Test Organization

```
tests/
├── unit/                           # Fast, isolated tests
│   ├── {{MODULE_1}}/
│   ├── {{MODULE_2}}/
│   └── {{MODULE_N}}/
├── integration/                    # Component interaction tests
│   └── test_integration.py
├── e2e/                           # End-to-end workflow tests
│   └── test_e2e.py
└── fixtures/                       # Shared test data
    ├── conftest.py               # Pytest configuration
    └── data/
```

## 2. Test Structure (AAA Pattern)

All tests follow **Arrange-Act-Assert** structure for clarity:

```python
def test_function_with_valid_input_returns_expected_result():
    """Test function returns expected result with valid input."""
    # Arrange: Set up test data and mocks
    input_data = {"key": "value"}
    expected_output = {"result": "processed"}

    # Act: Execute the functionality being tested
    result = process_data(input_data)

    # Assert: Verify expected outcomes
    assert result == expected_output
    assert result["result"] == "processed"
```

**Benefits**:
- **Arrange**: Clear setup makes test reproducible
- **Act**: Single action makes test focused
- **Assert**: Explicit checks make failures obvious

## 3. Mocking Patterns

### Mock External API Calls

```python
@pytest.fixture
def mock_api_client(mocker):
    """Mock external API client."""
    mock = mocker.Mock()
    mock.fetch.return_value = {"status": "success", "data": [1, 2, 3]}
    return mock

def test_service_uses_api_client(mock_api_client):
    """Test service calls API client correctly."""
    service = DataService(client=mock_api_client)

    result = service.get_data()

    # Verify API was called
    mock_api_client.fetch.assert_called_once_with("/data")
    assert result["status"] == "success"
```

### Mock File System Operations

```python
def test_function_creates_file(tmp_path, mocker):
    """Test function creates expected file."""
    # tmp_path is a pytest fixture for temporary directory
    target_file = tmp_path / "output.txt"

    # Execute function
    create_file(target_file, "content")

    # Verify file created with correct content
    assert target_file.exists()
    assert target_file.read_text() == "content"
```

### Mock Database Queries

```python
@pytest.fixture
def mock_database(mocker):
    """Mock database connection."""
    mock_db = mocker.Mock()
    mock_db.query.return_value = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
    ]
    return mock_db

def test_repository_fetches_items(mock_database):
    """Test repository fetches items from database."""
    repo = ItemRepository(db=mock_database)

    items = repo.get_all()

    mock_database.query.assert_called_once_with("SELECT * FROM items")
    assert len(items) == 2
    assert items[0]["name"] == "Item 1"
```

## 4. Coverage Targets

| Component Type | Minimum | Target | Rationale |
|----------------|---------|--------|-----------|
| **Core Logic** | 95% | 98%+ | Critical functionality, must be bulletproof |
| **API/Endpoints** | 90% | 95%+ | User-facing, many edge cases |
| **Utilities** | 90% | 95%+ | Widely reused, bugs multiply |
| **CLI** | 80% | 85%+ | User-facing, some UI code hard to test |
| **Configuration** | 85% | 90%+ | Critical for application setup |

**Overall Project**: 90% minimum, 95%+ target

**Enforcement**: `pytest --cov-fail-under=90` in `scripts/test.sh`

## 5. Test Naming Convention

```python
# Format: test_<unit>_<scenario>_<expected_outcome>

# Examples:
def test_validator_with_valid_input_returns_true():
    """Test validator returns True for valid input."""
    pass

def test_parser_with_empty_string_raises_value_error():
    """Test parser raises ValueError for empty string."""
    pass

def test_service_with_missing_config_uses_defaults():
    """Test service uses defaults when config missing."""
    pass
```

## 6. Property-Based Testing

Use Hypothesis to test invariants and edge cases:

```python
from hypothesis import given, strategies as st

@given(
    value=st.integers(min_value=0, max_value=100),
    multiplier=st.integers(min_value=1, max_value=10),
)
def test_multiply_is_commutative(value, multiplier):
    """Test multiplication is commutative."""
    assert multiply(value, multiplier) == multiply(multiplier, value)

@given(
    text=st.text(min_size=1, max_size=100),
)
def test_encode_decode_is_identity(text):
    """Test encoding then decoding returns original."""
    encoded = encode(text)
    decoded = decode(encoded)
    assert decoded == text
```

**When to Use**:
- Testing invariants (idempotency, commutativity)
- Validating input handling across wide range
- Finding edge cases you didn't think of

## 7. Mutation Testing

Every test suite must pass mutation testing. This ensures tests are effective at catching bugs:

```bash
# Run mutation tests with 80% minimum score
./scripts/mutation.sh

# View results
mutmut results
mutmut html

# View specific surviving mutants
mutmut show <id>

# Score must be 80%+ for MAXIMUM QUALITY
```

**Important**: Use `./scripts/mutation.sh` instead of running `mutmut` directly. The script enforces the 80% minimum threshold and provides clear feedback.

---

**Navigation**: [← Back to CLAUDE.md](../CLAUDE.md) | [← Workflow](workflow.md) | [Tools →](tools.md)
