"""YAML utility functions for handling AI-generated content.

Provides utilities for cleaning and validating YAML content that may come
from AI models, which sometimes wrap output in markdown code fences despite
instructions not to.
"""

from __future__ import annotations

import re


def strip_markdown_fences(content: str) -> str:
    r"""Strip markdown code fences from YAML content.

    AI models sometimes wrap YAML output in markdown code fences like:
    ```yaml
    ...content...
    ```

    This function removes those fences, handling various formats:
    - ```yaml ... ```
    - ``` ... ```
    - Content with no fences (returned unchanged)
    - Multiple code blocks (extracts first YAML block)

    Preserves whitespace in the content itself (only strips fences).

    Args:
        content: Raw content that may contain markdown fences.

    Returns:
        Clean content with fences removed.

    Examples:
        >>> strip_markdown_fences("```yaml\nname: CI\n```")
        'name: CI'
        >>> strip_markdown_fences("name: CI")
        'name: CI'
    """
    # Pattern matches: ``` or ```yaml at start, content, ``` at end
    # Uses DOTALL flag so . matches newlines (including trailing newlines)
    # Captures everything between opening fence newline and closing fence
    fence_pattern = r"^```(?:yaml|yml)?\s*\n(.*)```\s*$"

    match = re.match(fence_pattern, content.strip(), re.DOTALL)
    if match:
        # Return the content without fences, preserving all internal whitespace
        return match.group(1)

    # No fences found, return as-is (strip only leading/trailing whitespace)
    return content.strip()
