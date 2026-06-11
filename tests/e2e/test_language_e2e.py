"""E2E tests for multi-language CLI support.

Tests the complete sgsg init flow for supported languages, verifying
that the CLI produces valid project structures end-to-end.

Note: every base.SUPPORTED_LANGUAGES entry now runs the full pipeline.
Kotlin completed it with #357/#358, C/C++ followed with #362 (quality
tooling) and #363 (CI workflow), Java with #366 (Wear OS foundation +
CI) and #367 (quality tooling), C# with #370 (quality tooling on top
of the foundation scaffold + CI), and Ruby with #373, so all of them
join CLI_SUPPORTED_LANGUAGES below.

All tests use an environment with API keys stripped and a null keyring
backend to prevent real Anthropic API calls. See Issue #196.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile

import pytest

from tests.conftest import get_env_without_api_keys

# Languages fully supported in the CLI pipeline (all generators)
CLI_SUPPORTED_LANGUAGES = (
    "python",
    "typescript",
    "go",
    "rust",
    "swift",
    "kotlin",
    "cpp",
    "java",
    "csharp",
    "ruby",
)

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
    "swift": [
        "Sources/test_project/TestProjectApp.swift",
        "Sources/test_project/ContentView.swift",
        "Package.swift",
        "Tests/test_projectTests/test_projectTests.swift",
        ".swiftlint.yml",
        "README.md",
    ],
    "kotlin": [
        "settings.gradle.kts",
        "build.gradle.kts",
        "gradle.properties",
        "app/build.gradle.kts",
        "app/src/main/AndroidManifest.xml",
        "app/src/main/kotlin/com/example/test_project/MainActivity.kt",
        "app/src/test/kotlin/com/example/test_project/GreetingTest.kt",
        "detekt.yml",
        ".github/workflows/ci.yml",
        "README.md",
    ],
    "cpp": [
        "CMakeLists.txt",
        "conanfile.txt",
        "tizen-manifest.xml",
        "src/main.cpp",
        "src/greeting.cpp",
        "inc/greeting.h",
        "tests/test_greeting.cpp",
        ".clang-format",
        ".clang-tidy",
        ".github/workflows/ci.yml",
        "README.md",
    ],
    "java": [
        "pom.xml",
        "pmd-ruleset.xml",
        "src/main/java/com/example/test_project/Greeting.java",
        "src/test/java/com/example/test_project/GreetingTest.java",
        "app/src/main/AndroidManifest.xml",
        "app/src/main/java/com/example/test_project/MainActivity.java",
        ".pre-commit-config.yaml",
        "scripts/check-all.sh",
        ".github/workflows/ci.yml",
        "README.md",
    ],
    "csharp": [
        "test-project.csproj",
        "src/Program.cs",
        "tests/MainTests.cs",
        ".editorconfig",
        "CodeMetricsConfig.txt",
        ".pre-commit-config.yaml",
        "scripts/check-all.sh",
        "plans/architecture/ArchitectureTest.cs",
        ".github/workflows/ci.yml",
        "README.md",
    ],
    "ruby": [
        "Gemfile",
        "lib/test_project.rb",
        "spec/test_project_spec.rb",
        "spec/spec_helper.rb",
        ".rubocop.yml",
        ".pre-commit-config.yaml",
        "scripts/check-all.sh",
        "plans/architecture/packwerk.yml",
        "plans/architecture/package.yml",
        ".github/workflows/ci.yml",
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
                env=get_env_without_api_keys(),
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
                env=get_env_without_api_keys(),
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
                env=get_env_without_api_keys(),
            )

            assert result.returncode == 0, f"sgsg init failed: {result.stdout}"

            project_dir = Path(tmpdir) / "test-default-lang"
            assert project_dir.exists()

            # Python-specific files should exist
            assert (project_dir / "test_default_lang" / "__init__.py").exists()
            assert (project_dir / "test_default_lang" / "main.py").exists()
            assert (project_dir / "pyproject.toml").exists()
