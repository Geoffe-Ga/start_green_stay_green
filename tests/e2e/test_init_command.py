"""E2E tests for init command that verify actual file generation.

These tests run the actual CLI command (not mocked) to verify end-to-end
functionality and ensure all expected files are generated.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile


class TestInitCommand:
    """E2E tests for sgsg init command."""

    def test_init_generates_all_expected_files(self) -> None:
        """Test that init command generates complete project structure.

        This test verifies Issue #186 fix: all 4 new generators from Issue #170
        are integrated into CLI and actually generate files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run actual CLI command
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "test-project",
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

            # Verify command succeeded
            assert result.returncode == 0, f"Command failed: {result.stderr}"

            project_dir = Path(tmpdir) / "test-project"
            assert project_dir.exists(), "Project directory not created"

            # Verify source code structure (StructureGenerator)
            assert (
                project_dir / "test_project" / "__init__.py"
            ).exists(), "Missing test_project/__init__.py from StructureGenerator"
            assert (
                project_dir / "test_project" / "main.py"
            ).exists(), "Missing test_project/main.py from StructureGenerator"

            # Verify tests directory (TestsGenerator)
            assert (
                project_dir / "tests" / "__init__.py"
            ).exists(), "Missing tests/__init__.py from TestsGenerator"
            assert (
                project_dir / "tests" / "test_main.py"
            ).exists(), "Missing tests/test_main.py from TestsGenerator"

            # Verify dependencies (DependenciesGenerator)
            assert (
                project_dir / "requirements.txt"
            ).exists(), "Missing requirements.txt from DependenciesGenerator"
            assert (
                project_dir / "requirements-dev.txt"
            ).exists(), "Missing requirements-dev.txt from DependenciesGenerator"
            assert (
                project_dir / "pyproject.toml"
            ).exists(), "Missing pyproject.toml from DependenciesGenerator"

            # Verify README (ReadmeGenerator)
            assert (
                project_dir / "README.md"
            ).exists(), "Missing README.md from ReadmeGenerator"

            # Verify existing generators still work
            assert (
                project_dir / ".pre-commit-config.yaml"
            ).exists(), "Missing .pre-commit-config.yaml from PreCommitGenerator"
            assert (
                project_dir / ".claude" / "skills"
            ).exists(), "Missing .claude/skills from skills generator"
            assert (
                project_dir / "scripts" / "check-all.sh"
            ).exists(), "Missing scripts/check-all.sh from ScriptsGenerator"

            # Note: AI-powered features (CLAUDE.md, workflows, plans) require
            # an API key and are not generated in tests without one.

    def test_generated_python_code_is_valid(self) -> None:
        """Test that generated Python source code is syntactically valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run actual CLI command
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "syntax-test",
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

            assert result.returncode == 0, f"Command failed: {result.stderr}"

            project_dir = Path(tmpdir) / "syntax-test"

            # Verify main.py can be compiled
            main_py = project_dir / "syntax_test" / "main.py"
            if main_py.exists():
                content = main_py.read_text()
                compile(content, str(main_py), "exec")

            # Verify test file can be compiled
            test_main = project_dir / "tests" / "test_main.py"
            if test_main.exists():
                content = test_main.read_text()
                compile(content, str(test_main), "exec")

    def test_generated_hello_world_runs(self) -> None:
        """Test that generated Hello World application can actually run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run actual CLI command
            result = subprocess.run(
                [
                    "sgsg",
                    "init",
                    "--project-name",
                    "hello-test",
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

            assert result.returncode == 0, f"Command failed: {result.stderr}"

            project_dir = Path(tmpdir) / "hello-test"

            # Try to run the Hello World application
            main_py = project_dir / "hello_test" / "main.py"
            if main_py.exists():
                result = subprocess.run(
                    ["python", str(main_py)],
                    capture_output=True,
                    text=True,
                    check=False,
                    cwd=project_dir,
                )

                assert result.returncode == 0, f"Hello World failed: {result.stderr}"
                assert (
                    "Hello from hello-test" in result.stdout
                ), f"Expected 'Hello from hello-test' in output, got: {result.stdout}"
