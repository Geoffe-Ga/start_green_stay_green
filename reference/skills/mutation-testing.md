# Mutation Testing: Mutant-Conscious Coding

**Purpose**: Guide developers to write high-value tests that kill mutants through logic validation, not cosmetic shortcuts.

**Philosophy**: Mutation testing reveals whether your tests actually verify behavior or just achieve coverage. A test that doesn't kill mutants is a test that doesn't test.

---

## Core Principles

### 1. Test Logic, Not Cosmetics

**HIGH VALUE** ✅ Logic Tests:
- Boundary conditions with exact values
- Error handling with specific exceptions
- State transitions and side effects
- Algorithm correctness with edge cases
- Return value validation with assertions

**LOW VALUE** ❌ Cosmetic Tests:
- String matching with `"error" in output`
- Existence checks with `assert function_exists`
- Type checks with `isinstance()` alone
- Coverage shortcuts with no assertions
- Help text validation (unless user-facing critical)

### 2. The Mutant-Killing Checklist

For every test, ask:

1. **Would this test fail if I changed a constant by 1?**
   ```python
   # BAD: Doesn't kill MAX_LENGTH = 100 → 101
   assert len(name) <= MAX_PROJECT_NAME_LENGTH

   # GOOD: Kills the mutant
   assert MAX_PROJECT_NAME_LENGTH == 100
   name_100 = "a" * 100
   assert is_valid(name_100) == True
   name_101 = "a" * 101
   assert is_valid(name_101) == False
   ```

2. **Would this test fail if I changed an operator?**
   ```python
   # BAD: Doesn't kill > → >=
   assert len(items) > 0

   # GOOD: Tests exact boundary
   assert len([]) == 0  # Empty case
   assert len([1]) == 1  # Single item
   ```

3. **Would this test fail if I removed a check?**
   ```python
   # BAD: Doesn't kill missing validation
   result = process_input(value)
   assert result is not None

   # GOOD: Tests that validation happens
   with pytest.raises(ValueError, match="Invalid input"):
       process_input(invalid_value)
   ```

4. **Would this test fail if I changed an error message?**
   ```python
   # BAD: Doesn't kill message mutations
   with pytest.raises(FileNotFoundError):
       load_config(missing_file)

   # GOOD: Validates exact message
   with pytest.raises(FileNotFoundError) as exc:
       load_config(missing_file)
   assert "Configuration file not found" in str(exc.value)
   assert str(missing_file) in str(exc.value)
   ```

### 3. High-Value Test Patterns

#### Pattern 1: Exact Constant Values

```python
def test_constant_exact_value():
    """Test constant is exactly N, not N±1.

    Kills mutations: N → N+1, N → N-1, N → 0
    """
    assert MAX_RETRIES == 3
    assert MAX_RETRIES != 2
    assert MAX_RETRIES != 4
    assert isinstance(MAX_RETRIES, int)
```

#### Pattern 2: Boundary Testing

```python
def test_boundary_exact():
    """Test exact boundary, not approximate.

    Kills mutations: >= → >, <= → <, off-by-one errors
    """
    # Test exactly at boundary
    assert is_valid_length(100) == True   # At max
    assert is_valid_length(101) == False  # Over max
    assert is_valid_length(99) == True    # Under max

    # Test exactly at zero
    assert is_valid_length(0) == True     # At min
    assert is_valid_length(-1) == False   # Under min
```

#### Pattern 3: Complete Error Messages

```python
def test_error_message_complete():
    """Test complete error message, not just type.

    Kills mutations: message string changes, message → None
    """
    with pytest.raises(ValueError) as exc:
        validate_input("invalid")

    error_msg = str(exc.value)
    # Test all components of message
    assert "Invalid input" in error_msg
    assert "invalid" in error_msg
    assert error_msg  # Not None
    assert len(error_msg) > 10  # Has content
```

#### Pattern 4: State Verification

```python
def test_state_changes_exact():
    """Test exact state changes, not just final state.

    Kills mutations: missing updates, wrong order, partial updates
    """
    obj = StatefulObject()

    # Initial state
    assert obj.state == State.INIT
    assert obj.counter == 0
    assert obj.data is None

    # After first action
    obj.action1()
    assert obj.state == State.PROCESSING
    assert obj.counter == 1
    assert obj.data is not None

    # After second action
    obj.action2()
    assert obj.state == State.COMPLETE
    assert obj.counter == 2
    assert obj.data == expected_data
```

#### Pattern 5: Collection Contents

```python
def test_collection_exact_contents():
    """Test exact collection contents, not just size.

    Kills mutations: wrong items, wrong order, duplicates
    """
    result = get_items()

    # Test exact contents and order
    assert result == ["item1", "item2", "item3"]
    assert result[0] == "item1"
    assert result[-1] == "item3"
    assert len(result) == 3

    # Test no duplicates
    assert len(set(result)) == len(result)
```

### 4. Mutation-Killing Code Style

#### Write Testable Code

```python
# BAD: Hard to test exact behavior
def process(data):
    if not data:
        print("Error: No data")
        return
    # ... more code

# GOOD: Testable with exact assertions
def process(data):
    if not data:
        raise ValueError("No data provided")
    # ... more code
```

#### Use Named Constants

```python
# BAD: Magic numbers that mutants can change
if len(name) > 100:
    raise ValueError("Too long")

# GOOD: Testable constant
MAX_NAME_LENGTH = 100

if len(name) > MAX_NAME_LENGTH:
    raise ValueError(f"Name exceeds {MAX_NAME_LENGTH} characters")

# Now tests can verify MAX_NAME_LENGTH == 100
```

#### Write Specific Error Messages

```python
# BAD: Generic message, mutations hard to catch
raise ValueError("Invalid")

# GOOD: Specific message that tests can verify
raise ValueError(f"Invalid project name: {name}. Expected alphanumeric only.")
```

### 5. Common Mutation Categories

| Mutation Type | How to Kill It |
|---------------|----------------|
| **Constant Mutations** | Test exact value with equality assertions |
| **Operator Mutations** | Test boundary cases and edge values |
| **Boolean Mutations** | Test both True and False branches explicitly |
| **String Mutations** | Test exact string contents with equality |
| **Collection Mutations** | Test exact size, order, and contents |
| **None Mutations** | Test both None and not-None cases |
| **Return Mutations** | Test exact return values, not just type |

### 6. Red Flags (Avoid These)

🚩 **"test_function_exists"** - Existence tests don't verify behavior

🚩 **"assert result"** - Truthy tests miss specific values

🚩 **"assert 'error' in output"** - Weak string matching misses mutations

🚩 **"assert function() is not None"** - Doesn't test what the value is

🚩 **"assert len(result) > 0"** - Doesn't test exact size or contents

🚩 **Tests with no assertions** - Coverage without verification

### 7. Mutation Testing Workflow

1. **Write Feature Code**
   - Use constants for magic numbers
   - Write specific error messages
   - Make behavior testable

2. **Write High-Value Tests**
   - Test exact values and boundaries
   - Verify complete error messages
   - Test state changes explicitly

3. **Run Mutation Tests**
   ```bash
   # On specific file
   ./scripts/mutation.sh --paths-to-mutate start_green_stay_green/module.py

   # Analyze results
   ./scripts/analyze_mutations.py
   ```

4. **Kill Surviving Mutants**
   ```bash
   # View specific mutant
   mutmut show <id>

   # Write test to kill it
   # Focus on logic, not cosmetics
   ```

5. **Verify Score**
   ```bash
   # Must be ≥80%
   ./scripts/mutation.sh
   ```

### 8. Practical Examples

#### Example 1: Password Validation

```python
# Code
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

def validate_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password too short. Minimum {MIN_PASSWORD_LENGTH} characters."
        )
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(
            f"Password too long. Maximum {MAX_PASSWORD_LENGTH} characters."
        )

# HIGH-VALUE Tests
def test_password_min_length_exact():
    """Kills: MIN_PASSWORD_LENGTH = 8 → 7, 9"""
    assert MIN_PASSWORD_LENGTH == 8

    # Exactly at boundary
    validate_password("a" * 8)  # Should pass

    with pytest.raises(ValueError, match="Password too short"):
        validate_password("a" * 7)  # Should fail

def test_password_max_length_exact():
    """Kills: MAX_PASSWORD_LENGTH = 128 → 127, 129"""
    assert MAX_PASSWORD_LENGTH == 128

    validate_password("a" * 128)  # Should pass

    with pytest.raises(ValueError, match="Password too long"):
        validate_password("a" * 129)  # Should fail

def test_password_error_messages_exact():
    """Kills: error message string mutations"""
    with pytest.raises(ValueError) as exc:
        validate_password("short")

    error = str(exc.value)
    assert "Password too short" in error
    assert "8 characters" in error
```

#### Example 2: State Machine

```python
# Code
class OrderStateMachine:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    def __init__(self):
        self.state = self.PENDING

    def start_processing(self):
        if self.state != self.PENDING:
            raise ValueError(f"Cannot process order in state: {self.state}")
        self.state = self.PROCESSING

    def complete(self):
        if self.state != self.PROCESSING:
            raise ValueError(f"Cannot complete order in state: {self.state}")
        self.state = self.COMPLETED

# HIGH-VALUE Tests
def test_state_constants_exact():
    """Kills: state string mutations"""
    assert OrderStateMachine.PENDING == "pending"
    assert OrderStateMachine.PROCESSING == "processing"
    assert OrderStateMachine.COMPLETED == "completed"
    assert OrderStateMachine.CANCELLED == "cancelled"

def test_initial_state_exact():
    """Kills: wrong initial state"""
    order = OrderStateMachine()
    assert order.state == OrderStateMachine.PENDING
    assert order.state != OrderStateMachine.PROCESSING

def test_state_transition_exact():
    """Kills: missing state updates, wrong transitions"""
    order = OrderStateMachine()

    # Valid transition
    order.start_processing()
    assert order.state == OrderStateMachine.PROCESSING
    assert order.state != OrderStateMachine.PENDING

    # Next valid transition
    order.complete()
    assert order.state == OrderStateMachine.COMPLETED
    assert order.state != OrderStateMachine.PROCESSING

def test_invalid_transitions_blocked():
    """Kills: missing validation checks"""
    order = OrderStateMachine()

    # Can't complete from pending
    with pytest.raises(ValueError, match="Cannot complete order in state: pending"):
        order.complete()

    # State unchanged after error
    assert order.state == OrderStateMachine.PENDING
```

### 9. Integration with CI/CD

**Pre-commit**: Quick check on changed files
```yaml
- id: mutation-test
  entry: scripts/mutation.sh --paths-to-mutate
  pass_filenames: true
```

**Pull Request**: Full mutation test
```yaml
- name: Mutation Testing
  run: ./scripts/mutation.sh
```

**Merge Gate**: Block if score < 80%
```yaml
- name: Check Mutation Score
  run: ./scripts/mutation.sh || exit 1
```

---

## Summary

**Remember**:
- 🎯 **Test logic, not cosmetics**
- 🔬 **Verify exact values and boundaries**
- 🚨 **Validate complete error messages**
- 🎲 **Test all state transitions**
- 📊 **Aim for 85-90% mutation score (buffer above 80%)**

**The Goal**: Every test should fail when code behavior changes. If a test doesn't fail, it's not testing.

**The Standard**: 80% minimum mutation score. No shortcuts. No exceptions.
