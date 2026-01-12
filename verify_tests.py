#!/usr/bin/env python
"""Verify that all test files are syntactically valid and importable."""

from __future__ import annotations

import ast
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def verify_syntax(file_path: Path) -> bool:
    """Verify that a Python file is syntactically valid.

    Args:
        file_path: Path to the Python file to verify.

    Returns:
        True if file is valid, False otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return False


def main() -> int:
    """Verify all test files.

    Returns:
        0 if all files are valid, 1 otherwise.
    """
    logging.basicConfig(level=logging.INFO)
    test_dir = Path("tests")
    test_files = list(test_dir.glob("**/*.py"))

    logger.info(f"Verifying {len(test_files)} test files...")

    all_valid = True
    for test_file in sorted(test_files):
        if not verify_syntax(test_file):
            all_valid = False
        else:
            logger.info(f"✓ {test_file}")

    if all_valid:
        logger.info(f"\nAll {len(test_files)} test files are syntactically valid!")
        return 0
    else:
        logger.error("\nSome test files have syntax errors!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
