"""Naming utilities for deriving language-specific identifiers.

Provides helpers for converting package names into the casing conventions
required by generated source code (e.g. Swift's UpperCamelCase type names).
"""

from __future__ import annotations


def pascal_case(name: str) -> str:
    """Convert a separator-delimited name to PascalCase (UpperCamelCase).

    Both underscores and hyphens are treated as word separators, so
    ``test_project`` and ``test-project`` both become ``TestProject``.
    Empty segments produced by repeated or leading/trailing separators are
    dropped. This matches the casing required for Swift type and package
    names.

    Args:
        name: The separator-delimited name to convert.

    Returns:
        The PascalCase form of ``name`` (an empty string if ``name`` has no
        word characters).
    """
    words = name.replace("-", "_").split("_")
    return "".join(word.capitalize() for word in words if word)
