"""E2E tests for multi-language CLI support.

Tests the complete sgsg init flow for supported languages, verifying
that the CLI produces valid project structures end-to-end.

Note: java, csharp, and ruby are supported at the generator level but
the full CLI pipeline (PreCommitGenerator) only supports python, typescript,
go, and rust currently. Those 3 languages are tested at the unit/integration
level via test_language_generators.py.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import pytest

# Languages fully supported in the CLI pipeline (all generators)
CLI_SUPPORTED_LANGUAGES = ("python", "typescript", "go", "rust")

# Expected key files per language that sgsg init should create
EXPECTED_KEY_FILES: dict[str, list[str]] = {
    "python": [
        "test_project/__init__.py",
        "test_project/main.py",
        "tests/__init__.py",
        "tests/test_main.py",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "README.md",
    ],
    "typescript": [
        "src/index.ts",
        "tsconfig.json",
        "package.json",
        "tests/index.test.ts",
        "README.md",
    ],
    "go": [
        "cmd/test_project/main.go",
        "go.mod",
        "cmd/test_project/main_test.go",
        "README.md",
    ],
    "rust": [
        "src/main.rs",
        "Cargo.toml",
        "tests/integration_test.rs",
        "README.md",
    ],
}


class TestLanguageE2E:
    """E2E tests for sgsg init with each supported language."""

    @pytest.mark.parametrize("lang", CLI_SUPPORTED_LANGUAGES)
    def test_sgsg_init_with_language(self, lang: str) -> None:
        """Test sgsg init creates a valid project for each language."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "test-project",
                    "--language",
                    lang,
                    "--output-dir",
                    tmpdir,
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert (
                result.returncode == 0
            ), f"sgsg init failed for {lang}: {result.stdout}"

            project_dir = Path(tmpdir) / "test-project"
            assert project_dir.exists(), f"Project directory not created for {lang}"

            # Verify key files for this language
            expected = EXPECTED_KEY_FILES[lang]
            for expected_file in expected:
                file_path = project_dir / expected_file
                assert file_path.exists(), f"Missing {expected_file} for {lang}"

    def test_sgsg_init_unsupported_language(self) -> None:
        """Test sgsg init rejects unsupported language with clear error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "test-project",
                    "--language",
                    "brainfuck",
                    "--output-dir",
                    tmpdir,
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert (
                result.returncode != 0
            ), "Expected non-zero exit code for unsupported language"

    def test_sgsg_init_default_is_python(self) -> None:
        """Test sgsg init with explicit python produces python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "test-default-lang",
                    "--language",
                    "python",
                    "--output-dir",
                    tmpdir,
                    "--no-interactive",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            project_dir = Path(tmpdir) / "test-default-lang"
            assert project_dir.exists()

            # Python-specific files should exist
            assert (project_dir / "test_default_lang" / "__init__.py").exists()
            assert (project_dir / "test_default_lang" / "main.py").exists()
            assert (project_dir / "pyproject.toml").exists()
