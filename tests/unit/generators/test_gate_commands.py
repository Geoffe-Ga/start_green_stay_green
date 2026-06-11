"""Tests for the shared cross-platform gate documentation table (#386).

One canonical table maps each scaffolded language's gate scripts to the
toolchain-native cross-platform command they wrap. The renderer turns
that table into the ``scripts/README.md`` emitted into generated
projects, so generated repos document a working Windows invocation for
every gate without any per-language Windows shims (DRY).
"""

from __future__ import annotations

import pytest

from start_green_stay_green.generators.gate_commands import GATE_DOCS
from start_green_stay_green.generators.gate_commands import canonical_language
from start_green_stay_green.generators.gate_commands import render_scripts_readme

#: Languages the scripts generator has dedicated builders for.
CANONICAL_LANGUAGES = {
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
}


class TestCanonicalLanguage:
    """Alias resolution matches the scripts generator's dispatch table."""

    @pytest.mark.parametrize(
        ("alias", "expected"),
        [
            ("typescript", "typescript"),
            ("ts", "typescript"),
            ("javascript", "typescript"),
            ("js", "typescript"),
            ("python", "python"),
            ("go", "go"),
            ("rust", "rust"),
            ("swift", "swift"),
            ("kotlin", "kotlin"),
            ("cpp", "cpp"),
            ("java", "java"),
            ("csharp", "csharp"),
            ("ruby", "ruby"),
        ],
    )
    def test_known_languages_resolve(self, alias: str, expected: str) -> None:
        """Every dispatch-table alias maps to its canonical language."""
        assert canonical_language(alias) == expected

    def test_unknown_language_falls_back_to_python(self) -> None:
        """Unknown languages mirror generate()'s python-builder fallback."""
        assert canonical_language("cobol") == "python"


class TestGateDocsTable:
    """The single source of truth covers every language and key gate."""

    def test_covers_all_canonical_languages(self) -> None:
        """Exactly the scripts generator's languages are documented."""
        assert set(GATE_DOCS) == CANONICAL_LANGUAGES

    @pytest.mark.parametrize("language", sorted(CANONICAL_LANGUAGES))
    def test_every_language_documents_core_gates(self, language: str) -> None:
        """check-all, test, lint, and format rows exist for each language."""
        documented = set(GATE_DOCS[language])
        assert {"check-all.sh", "test.sh", "lint.sh", "format.sh"} <= documented

    @pytest.mark.parametrize(
        ("language", "gate", "native"),
        [
            ("python", "test.sh", "pytest tests/"),
            ("python", "lint.sh", "ruff check ."),
            ("typescript", "test.sh", "npx jest"),
            ("typescript", "lint.sh", "npx eslint ."),
            ("go", "test.sh", "go test -cover ./..."),
            ("go", "lint.sh", "golangci-lint run ./..."),
            ("rust", "test.sh", "cargo test"),
            ("rust", "lint.sh", "cargo clippy --all -- -D warnings"),
            ("swift", "test.sh", "swift test --enable-code-coverage"),
            ("swift", "lint.sh", "swiftlint lint --strict"),
            ("kotlin", "test.sh", "./gradlew test"),
            (
                "kotlin",
                "lint.sh",
                "detekt --config detekt.yml --build-upon-default-config",
            ),
            ("java", "test.sh", "mvn test"),
            ("java", "lint.sh", "mvn -q checkstyle:check && mvn -q pmd:check"),
            ("csharp", "test.sh", "dotnet test"),
            ("csharp", "lint.sh", "dotnet build --nologo"),
            ("ruby", "test.sh", "bundle exec rspec"),
            ("ruby", "lint.sh", "bundle exec rubocop --force-exclusion"),
            (
                "cpp",
                "test.sh",
                "cmake --build build && ctest --test-dir build --output-on-failure",
            ),
        ],
    )
    def test_native_commands_are_the_toolchain_runners(
        self, language: str, gate: str, native: str
    ) -> None:
        """test/lint gates document the exact toolchain-native command."""
        assert GATE_DOCS[language][gate].native == native

    @pytest.mark.parametrize("language", sorted(CANONICAL_LANGUAGES))
    def test_no_bespoke_windows_shims_in_native_commands(self, language: str) -> None:
        """Native commands never branch per platform (DRY constraint).

        The toolchain runners (npm/npx, go, cargo, mvn, dotnet, bundle,
        swift, cmake/ctest) are cross-platform by design, so no command
        may embed PowerShell, cmd.exe, or ``.ps1`` constructs.
        """
        for doc in GATE_DOCS[language].values():
            assert "powershell" not in doc.native.lower()
            assert ".ps1" not in doc.native
            assert "cmd /c" not in doc.native.lower()


class TestRenderScriptsReadme:
    """The rendered scripts/README.md documents all three invocations."""

    def test_row_per_shell_script(self) -> None:
        """Every passed .sh script gets a table row; non-.sh are skipped."""
        content = render_scripts_readme(
            "python",
            ["check-all.sh", "test.sh", "analyze_mutations.py"],
            package_name="pkg",
        )
        assert "| `check-all.sh` |" in content
        assert "| `test.sh` |" in content
        assert "analyze_mutations.py" not in content

    def test_posix_and_git_bash_invocations(self) -> None:
        """Each row pairs the POSIX path with the Git Bash invocation."""
        content = render_scripts_readme(
            "go", ["check-all.sh", "test.sh", "lint.sh"], package_name="pkg"
        )
        assert "`./scripts/test.sh`" in content
        assert "`bash scripts/test.sh`" in content
        assert "`./scripts/lint.sh`" in content
        assert "`bash scripts/lint.sh`" in content

    def test_package_name_is_interpolated(self) -> None:
        """Python rows substitute the real package name everywhere."""
        content = render_scripts_readme(
            "python",
            ["typecheck.sh", "security.sh", "complexity.sh", "coverage.sh"],
            package_name="my_pkg",
        )
        assert "mypy my_pkg/" in content
        assert "__PACKAGE__" not in content

    def test_unknown_script_renders_em_dash(self) -> None:
        """Scripts without a table entry still get an honest row."""
        content = render_scripts_readme("go", ["mystery.sh"], package_name="pkg")
        assert "| `mystery.sh` |" in content
        assert "—" in content

    def test_check_all_is_the_first_row(self) -> None:
        """check-all.sh leads the table as the headline gate."""
        content = render_scripts_readme(
            "rust", ["test.sh", "check-all.sh", "lint.sh"], package_name="pkg"
        )
        rows = [line for line in content.splitlines() if line.startswith("| `")]
        assert rows[0].startswith("| `check-all.sh` |")

    def test_unknown_language_uses_python_docs(self) -> None:
        """Fallback mirrors generate(): unknown languages get python gates."""
        content = render_scripts_readme("cobol", ["lint.sh"], package_name="pkg")
        assert "ruff check ." in content

    def test_windows_section_documents_git_bash_and_line_endings(self) -> None:
        """The Windows section explains Git Bash, LF pinning, and limits."""
        content = render_scripts_readme("python", ["check-all.sh"], package_name="pkg")
        assert "bash scripts/check-all.sh" in content
        assert "Git Bash" in content
        assert ".gitattributes" in content
        # Honest enforcement-gap statement: native commands do not
        # reproduce the scripts' option sets and threshold checks.
        assert "source of truth" in content

    def test_kotlin_documents_gradlew_bat(self) -> None:
        """The Gradle wrapper's Windows entry point is called out."""
        content = render_scripts_readme("kotlin", ["test.sh"], package_name="pkg")
        assert "gradlew.bat" in content

    def test_python_documents_venv_activation(self) -> None:
        """Python native commands require the activated project venv."""
        content = render_scripts_readme("python", ["test.sh"], package_name="pkg")
        assert ".venv\\Scripts\\activate" in content

    def test_rendering_is_deterministic(self) -> None:
        """Identical inputs produce byte-identical output (reproducible)."""
        args = ("swift", ["check-all.sh", "lint.sh", "test.sh"])
        first = render_scripts_readme(*args, package_name="pkg")
        second = render_scripts_readme(*args, package_name="pkg")
        assert first == second

    def test_uses_lf_line_endings_only(self) -> None:
        """Rendered content never carries CR characters."""
        content = render_scripts_readme(
            "csharp", ["check-all.sh", "test.sh"], package_name="pkg"
        )
        assert "\r" not in content
