#!/usr/bin/env python
"""Verify that all test files are syntactically valid and importable."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


def verify_syntax(file_path: Path) -> bool:
    """Verify that a Python file is syntactically valid.

    Args:
        file_path: Path to the Python file to verify.

    Returns:
        True if file is valid, False otherwise.
    """
    try:
        with open(file_path) as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return False


def main() -> int:
    """Verify all test files.

    Returns:
        0 if all files are valid, 1 otherwise.
    """
    test_dir = Path("tests")
    test_files = list(test_dir.glob("**/*.py"))

    print(f"Verifying {len(test_files)} test files...")

    all_valid = True
    for test_file in sorted(test_files):
        if not verify_syntax(test_file):
            all_valid = False
        else:
            print(f"✓ {test_file}")

    if all_valid:
        print(f"\nAll {len(test_files)} test files are syntactically valid!")
        return 0
    else:
        print("\nSome test files have syntax errors!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
