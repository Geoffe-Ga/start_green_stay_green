"""Test YAML fence stripping for Issue #160."""

from __future__ import annotations

from start_green_stay_green.utils.yaml_utils import strip_markdown_fences


def test_strip_markdown_fences_yaml() -> None:
    """Test stripping markdown fences from YAML content."""
    # YAML wrapped in markdown fences (with trailing newline preserved)
    input_yaml = """```yaml
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
```"""

    # Expected: fences removed, content preserved including any internal formatting
    expected = """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest"""

    result = strip_markdown_fences(input_yaml)
    assert result == expected


def test_strip_markdown_fences_no_language() -> None:
    """Test stripping markdown fences without language specifier."""
    input_yaml = """```
name: CI
on: [push]
```"""

    expected = """name: CI
on: [push]"""

    result = strip_markdown_fences(input_yaml)
    assert result == expected


def test_strip_markdown_fences_already_clean() -> None:
    """Test that clean YAML is returned unchanged."""
    input_yaml = """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest"""

    result = strip_markdown_fences(input_yaml)
    assert result == input_yaml


def test_strip_markdown_fences_multiple_code_blocks() -> None:
    """Test stripping when there are multiple code blocks (take first)."""
    input_yaml = """```yaml
name: CI
```

```python
print("hello")
```"""

    expected = """name: CI"""

    result = strip_markdown_fences(input_yaml)
    assert result == expected


def test_strip_markdown_fences_with_backticks_in_yaml() -> None:
    """Test that backticks inside YAML content are preserved."""
    input_yaml = """```yaml
name: CI
description: "This is a `special` character"
```"""

    expected = """name: CI
description: "This is a `special` character\""""

    result = strip_markdown_fences(input_yaml)
    assert result == expected
