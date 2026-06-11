"""Tests for language-specific setup instructions in CLI init output.

The shell-sensitive helpers (``_venv_activation_command``,
``_quote_path_for_shell``, ``_check_all_command``) and
``_get_setup_instructions`` all take ``os_name``/``env`` explicitly, so
every test here is hermetic: the real ``os.name`` is never patched —
``pathlib.Path`` dispatches on it at construction time, so patching it
crashes ``Path()`` on Windows runners (#380).

Cross-platform literal goldens: POSIX-flavored test paths use a single
path component (e.g. ``Path("my-project")``) because multi-component
POSIX paths stringify with backslashes on Windows runners. Windows
test paths like ``Path("C:\\Users\\dev\\proj")`` stringify identically
on every platform (on POSIX the backslashes are literal name
characters), so their goldens are safe everywhere.
"""

from pathlib import Path
import shlex
from typing import TypedDict

import pytest

from start_green_stay_green.cli import _check_all_command
from start_green_stay_green.cli import _finalize_init
from start_green_stay_green.cli import _get_setup_instructions
from start_green_stay_green.cli import _quote_path_for_shell
from start_green_stay_green.cli import _venv_activation_command

# A PSModulePath value marks the environment as PowerShell (#284/#409).
POWERSHELL_ENV = {"PSModulePath": "C:\\Program Files\\PowerShell\\Modules"}


class _PlatformArgs(TypedDict):
    """Keyword arguments selecting a platform for the instruction helpers."""

    os_name: str
    env: dict[str, str]


# Default hermetic platform args for tests that don't care about shell.
POSIX_BASH: _PlatformArgs = {"os_name": "posix", "env": {"SHELL": "/bin/bash"}}


def _assert_cd_command(command: str, path: Path) -> None:
    """Assert that ``command`` is a POSIX cd to exactly ``path``.

    The shlex round-trip keeps the assertion platform-agnostic: on
    Windows ``str(Path(...))`` uses backslashes, which ``shlex.quote``
    wraps in quotes, so a literal string comparison would be
    platform-dependent (#380). Parsing the command back proves a shell
    would cd to exactly the intended directory.

    Args:
        command: The generated shell command under test.
        path: The project path the command must cd into.
    """
    assert shlex.split(command) == ["cd", str(path)]


# Languages exercised by the per-language common-tail tests. The
# unknown-language default path is covered separately with "php"
# (java gained its own Maven step with #366, csharp its dotnet step
# with #371, ruby its bundler steps with #373).
ALL_LANGUAGES = (
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


def _always_posix() -> bool:
    """Pin the POSIX branch of the is_windows seam."""
    return False


def _always_windows() -> bool:
    """Pin the Windows branch of the is_windows seam."""
    return True


class TestVenvActivationCommand:
    """Tests for _venv_activation_command shell detection."""

    @pytest.mark.parametrize(
        ("shell", "expected"),
        [
            ("/usr/bin/fish", "source .venv/bin/activate.fish"),
            ("/opt/homebrew/bin/fish", "source .venv/bin/activate.fish"),
            ("/bin/csh", "source .venv/bin/activate.csh"),
            ("/bin/tcsh", "source .venv/bin/activate.csh"),
            ("/bin/bash", "source .venv/bin/activate"),
            ("/bin/zsh", "source .venv/bin/activate"),
            ("/bin/sh", "source .venv/bin/activate"),
        ],
    )
    def test_posix_shell_detection(self, shell: str, expected: str) -> None:
        """POSIX shells should map to their matching activation script."""
        assert _venv_activation_command("posix", {"SHELL": shell}) == expected

    def test_posix_missing_shell_defaults_to_bash_form(self) -> None:
        """Missing SHELL env var should fall back to the bash/zsh form."""
        command = _venv_activation_command("posix", {})
        assert command == "source .venv/bin/activate"

    def test_posix_unknown_shell_defaults_to_bash_form(self) -> None:
        """Unrecognized shells should fall back to the bash/zsh form."""
        command = _venv_activation_command("posix", {"SHELL": "/usr/bin/nushell"})
        assert command == "source .venv/bin/activate"

    def test_posix_empty_shell_defaults_to_bash_form(self) -> None:
        """An empty SHELL value should fall back to the bash/zsh form."""
        command = _venv_activation_command("posix", {"SHELL": ""})
        assert command == "source .venv/bin/activate"

    def test_windows_cmd_uses_scripts_activate(self) -> None:
        """Windows without PSModulePath should emit the cmd activate script."""
        command = _venv_activation_command("nt", {})
        assert command == ".venv\\Scripts\\activate"

    def test_windows_powershell_uses_activate_ps1(self) -> None:
        """Windows with PSModulePath set should emit the PowerShell script."""
        command = _venv_activation_command("nt", POWERSHELL_ENV)
        assert command == ".venv\\Scripts\\Activate.ps1"

    def test_windows_ignores_posix_shell_var(self) -> None:
        """On Windows, a stray SHELL env var should not trigger POSIX forms."""
        command = _venv_activation_command("nt", {"SHELL": "/usr/bin/fish"})
        assert command == ".venv\\Scripts\\activate"


class TestQuotePathForShell:
    """Tests for _quote_path_for_shell platform-aware quoting."""

    def test_posix_simple_path_is_unquoted(self) -> None:
        """A safe POSIX path should pass through without quoting."""
        assert _quote_path_for_shell("posix", Path("my-project")) == "my-project"

    def test_posix_path_with_spaces_uses_posix_quoting(self) -> None:
        """POSIX quoting must match shlex semantics exactly."""
        quoted = _quote_path_for_shell("posix", Path("my project"))
        assert quoted == "'my project'"

    def test_posix_quoting_matches_shlex_for_absolute_paths(self) -> None:
        """The POSIX branch must be exactly shlex.quote of the path."""
        path = Path("/home/user/my project")
        assert _quote_path_for_shell("posix", path) == shlex.quote(str(path))

    def test_windows_path_is_double_quoted(self) -> None:
        """Windows paths get double quotes — valid in both cmd and PowerShell.

        ``shlex.quote`` would emit ``'C:\\Users\\dev\\proj'``, which
        cmd.exe does not understand at all; double quotes work in both
        Windows shells (#409 deferred UX issue).
        """
        path = Path("C:\\Users\\dev\\proj")
        assert _quote_path_for_shell("nt", path) == '"C:\\Users\\dev\\proj"'

    def test_windows_path_with_spaces_is_double_quoted(self) -> None:
        """Windows paths with spaces survive copy-paste via double quotes."""
        path = Path("C:\\Users\\dev\\my project")
        quoted = _quote_path_for_shell("nt", path)
        assert quoted == '"C:\\Users\\dev\\my project"'

    def test_windows_never_uses_posix_single_quotes(self) -> None:
        """The nt branch must not fall back to POSIX single-quoting."""
        quoted = _quote_path_for_shell("nt", Path("my project"))
        assert quoted == '"my project"'
        assert "'" not in quoted


class TestCheckAllCommand:
    """Tests for _check_all_command platform-aware gate invocation."""

    def test_posix_invokes_script_directly(self) -> None:
        """POSIX runs the generated script directly via its exec bit."""
        assert _check_all_command("posix") == "./scripts/check-all.sh"

    def test_windows_invokes_via_git_bash(self) -> None:
        """Windows runs the POSIX script through bash (Git Bash).

        Generated projects have no native Windows gate runner yet, and
        NTFS has no executable bit — passing the script as an argument
        to bash needs neither ``./`` invocation nor the exec bit.
        """
        assert _check_all_command("nt") == "bash scripts/check-all.sh"

    def test_windows_does_not_reference_dot_slash(self) -> None:
        """The Windows form must not rely on ./ exec-bit invocation."""
        assert not _check_all_command("nt").startswith("./")


class TestPerShellGoldenInstructions:
    """Golden full-instruction-list assertions per supported shell.

    Each case pins the complete, copy-pasteable instruction list for a
    Python project so any drift in ordering, quoting, activation, or
    gate invocation fails loudly. Paths are chosen to stringify
    identically on POSIX and Windows runners (see module docstring).
    """

    PIP_INSTALL = "pip install -r requirements.txt -r requirements-dev.txt"

    def test_posix_bash_golden(self) -> None:
        """bash/zsh: source activate + direct ./scripts invocation."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("my-project"),
            os_name="posix",
            env={"SHELL": "/bin/bash"},
        )
        assert instructions == [
            "cd my-project",
            "python -m venv .venv",
            "source .venv/bin/activate",
            self.PIP_INSTALL,
            "pre-commit install",
            "./scripts/check-all.sh",
        ]

    def test_fish_golden(self) -> None:
        """fish: activate.fish + direct ./scripts invocation."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("my-project"),
            os_name="posix",
            env={"SHELL": "/usr/bin/fish"},
        )
        assert instructions == [
            "cd my-project",
            "python -m venv .venv",
            "source .venv/bin/activate.fish",
            self.PIP_INSTALL,
            "pre-commit install",
            "./scripts/check-all.sh",
        ]

    def test_csh_golden(self) -> None:
        """csh/tcsh: activate.csh + direct ./scripts invocation."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("my-project"),
            os_name="posix",
            env={"SHELL": "/bin/csh"},
        )
        assert instructions == [
            "cd my-project",
            "python -m venv .venv",
            "source .venv/bin/activate.csh",
            self.PIP_INSTALL,
            "pre-commit install",
            "./scripts/check-all.sh",
        ]

    def test_windows_cmd_golden(self) -> None:
        """cmd.exe: double-quoted cd, Scripts activate, Git Bash gate."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("C:\\Users\\dev\\my project"),
            os_name="nt",
            env={},
        )
        assert instructions == [
            'cd "C:\\Users\\dev\\my project"',
            "python -m venv .venv",
            ".venv\\Scripts\\activate",
            self.PIP_INSTALL,
            "pre-commit install",
            "bash scripts/check-all.sh",
        ]

    def test_windows_powershell_golden(self) -> None:
        """PowerShell: double-quoted cd, Activate.ps1, Git Bash gate."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("C:\\Users\\dev\\my project"),
            os_name="nt",
            env=POWERSHELL_ENV,
        )
        assert instructions == [
            'cd "C:\\Users\\dev\\my project"',
            "python -m venv .venv",
            ".venv\\Scripts\\Activate.ps1",
            self.PIP_INSTALL,
            "pre-commit install",
            "bash scripts/check-all.sh",
        ]

    def test_windows_non_python_golden(self) -> None:
        """Non-Python languages on Windows still get the Git Bash gate."""
        instructions = _get_setup_instructions(
            ("typescript",),
            Path("C:\\Users\\dev\\ts-proj"),
            os_name="nt",
            env={},
        )
        assert instructions == [
            'cd "C:\\Users\\dev\\ts-proj"',
            "npm install",
            "pre-commit install",
            "bash scripts/check-all.sh",
        ]


class TestGetSetupInstructions:
    """Tests for _get_setup_instructions."""

    def test_python_includes_venv_creation(self) -> None:
        """Python setup should create a virtualenv."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project"), **POSIX_BASH
        )
        assert "python -m venv .venv" in instructions

    def test_python_activation_respects_shell_env(self) -> None:
        """The fish activation form appears when SHELL points at fish."""
        instructions = _get_setup_instructions(
            ("python",),
            Path("/home/user/my-project"),
            os_name="posix",
            env={"SHELL": "/usr/bin/fish"},
        )
        assert "source .venv/bin/activate.fish" in instructions

    def test_python_activation_defaults_without_shell_var(self) -> None:
        """Unset SHELL yields the bash/zsh activation default."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project"), os_name="posix", env={}
        )
        assert "source .venv/bin/activate" in instructions

    def test_python_includes_pip_install(self) -> None:
        """Python setup should install requirements."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project"), **POSIX_BASH
        )
        pip_cmds = [c for c in instructions if "pip install" in c]
        assert len(pip_cmds) == 1
        assert "requirements.txt" in pip_cmds[0]
        assert "requirements-dev.txt" in pip_cmds[0]

    def test_python_includes_precommit_and_check_all(self) -> None:
        """Python setup should end with pre-commit install and check-all."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project"), **POSIX_BASH
        )
        assert "pre-commit install" in instructions
        assert "./scripts/check-all.sh" in instructions

    def test_python_starts_with_cd(self) -> None:
        """Python setup should start with cd into project."""
        path = Path("/home/user/my-project")
        instructions = _get_setup_instructions(("python",), path, **POSIX_BASH)
        _assert_cd_command(instructions[0], path)

    def test_typescript_includes_npm_install(self) -> None:
        """TypeScript setup should run npm install."""
        instructions = _get_setup_instructions(
            ("typescript",), Path("/home/user/ts-proj"), **POSIX_BASH
        )
        assert "npm install" in instructions

    def test_typescript_no_venv(self) -> None:
        """TypeScript should not include Python venv steps."""
        instructions = _get_setup_instructions(
            ("typescript",), Path("/home/user/ts-proj"), **POSIX_BASH
        )
        assert "python -m venv .venv" not in instructions

    def test_go_includes_mod_download(self) -> None:
        """Go setup should download modules."""
        instructions = _get_setup_instructions(
            ("go",), Path("/home/user/go-proj"), **POSIX_BASH
        )
        assert "go mod download" in instructions

    def test_rust_includes_cargo_build(self) -> None:
        """Rust setup should run cargo build."""
        instructions = _get_setup_instructions(
            ("rust",), Path("/home/user/rust-proj"), **POSIX_BASH
        )
        assert "cargo build" in instructions

    def test_swift_includes_swift_build(self) -> None:
        """Swift setup should resolve dependencies and build the SPM package."""
        instructions = _get_setup_instructions(
            ("swift",), Path("/home/user/swift-proj"), **POSIX_BASH
        )
        assert "swift package resolve" in instructions
        assert "swift build" in instructions

    def test_kotlin_creates_wrapper_then_builds(self) -> None:
        """Kotlin setup should create the Gradle wrapper, then build (#356).

        The wrapper jar is a binary artifact the generator never writes, so
        the first step materialises it from a local Gradle install.
        """
        instructions = _get_setup_instructions(
            ("kotlin",), Path("/home/user/wear-proj"), **POSIX_BASH
        )
        gradle_wrapper_cmds = [
            c for c in instructions if c.startswith("gradle wrapper")
        ]
        assert len(gradle_wrapper_cmds) == 1
        assert "./gradlew build" in instructions
        wrapper_idx = instructions.index(gradle_wrapper_cmds[0])
        build_idx = instructions.index("./gradlew build")
        assert wrapper_idx < build_idx

    def test_cpp_installs_conan_then_builds_and_tests(self) -> None:
        """cpp setup runs Conan, configures CMake, builds, then tests (#361).

        The .tpk packaging path needs Tizen Studio (not installable by
        init), so the steps cover only the plain CMake + Conan build of
        the pure-logic library and its Catch2 tests.
        """
        instructions = _get_setup_instructions(
            ("cpp",), Path("/home/user/watch-proj"), **POSIX_BASH
        )

        conan_idx = instructions.index(
            "conan install . --output-folder=build --build=missing"
        )
        configure_cmds = [
            c for c in instructions if c.startswith("cmake -B build -S .")
        ]
        assert len(configure_cmds) == 1
        assert "conan_toolchain.cmake" in configure_cmds[0]
        build_idx = instructions.index("cmake --build build")
        test_idx = instructions.index("ctest --test-dir build")
        assert conan_idx < instructions.index(configure_cmds[0]) < build_idx < test_idx
        assert not any("tizen" in c for c in instructions)

    def test_java_runs_the_pure_logic_maven_tests(self) -> None:
        """java setup runs mvn test — what the generated pom can do (#366).

        The watch APK build needs Android tooling (Android Studio /
        Gradle) that init cannot install, so no Gradle/APK step appears.
        """
        instructions = _get_setup_instructions(
            ("java",), Path("/home/user/wear-proj"), **POSIX_BASH
        )
        assert "mvn test" in instructions
        assert not any("gradle" in c for c in instructions)

    def test_csharp_runs_the_dotnet_test_suite(self) -> None:
        """csharp setup verifies the scaffold with one dotnet test run (#370).

        ``dotnet test`` implicitly restores and builds with the csproj's
        Roslyn analyzers as errors, so no separate restore/build steps
        appear — the csproj is the single home of the quality policy.
        """
        instructions = _get_setup_instructions(
            ("csharp",), Path("/home/user/dotnet-proj"), **POSIX_BASH
        )
        assert "dotnet test" in instructions
        assert not any("dotnet restore" in c for c in instructions)
        assert not any("dotnet build" in c for c in instructions)

    def test_ruby_includes_bundler_steps(self) -> None:
        """Ruby instructions provision gems and verify the scaffold (#373).

        `bundle install` provisions the pinned quality gems and
        `bundle exec rspec` verifies the scaffold — the csharp #371
        lesson: a supported language must not sit on the
        unknown-language default path.
        """
        instructions = _get_setup_instructions(
            ("ruby",), Path("/home/user/ruby-proj"), **POSIX_BASH
        )
        assert "bundle install" in instructions
        assert "bundle exec rspec" in instructions

    def test_unknown_language_has_sensible_default(self) -> None:
        """Unknown languages should still get pre-commit + check-all.

        ruby gained its own bundler steps with #373, so the probe uses
        php — a language with no setup-step entry.
        """
        path = Path("/home/user/php-proj")
        instructions = _get_setup_instructions(("php",), path, **POSIX_BASH)
        _assert_cd_command(instructions[0], path)
        assert "pre-commit install" in instructions
        assert "./scripts/check-all.sh" in instructions

    @pytest.mark.parametrize("lang", ALL_LANGUAGES)
    def test_language_ends_with_check_all(self, lang: str) -> None:
        """Every language's instructions should end with check-all."""
        instructions = _get_setup_instructions(
            (lang,), Path("/home/user/proj"), **POSIX_BASH
        )
        assert instructions[-1] == "./scripts/check-all.sh"

    @pytest.mark.parametrize("lang", ALL_LANGUAGES)
    def test_language_ends_with_git_bash_check_all_on_windows(self, lang: str) -> None:
        """Every language's Windows instructions end with the bash gate."""
        instructions = _get_setup_instructions(
            (lang,), Path("C:\\Users\\dev\\proj"), os_name="nt", env={}
        )
        assert instructions[-1] == "bash scripts/check-all.sh"

    @pytest.mark.parametrize("lang", ALL_LANGUAGES)
    def test_language_includes_precommit(self, lang: str) -> None:
        """Every language's instructions should include pre-commit install."""
        instructions = _get_setup_instructions(
            (lang,), Path("/home/user/proj"), **POSIX_BASH
        )
        assert "pre-commit install" in instructions

    def test_returns_list_of_strings(self) -> None:
        """Instructions should be a list of strings."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/proj"), **POSIX_BASH
        )
        assert isinstance(instructions, list)
        assert all(isinstance(cmd, str) for cmd in instructions)

    def test_project_path_in_cd_command(self) -> None:
        """The cd command should use the exact project path."""
        path = Path("/home/user/my-awesome-project")
        instructions = _get_setup_instructions(("python",), path, **POSIX_BASH)
        _assert_cd_command(instructions[0], path)

    def test_multi_language_python_and_typescript(self) -> None:
        """Multi-language python+typescript should include steps for both."""
        instructions = _get_setup_instructions(
            ("python", "typescript"), Path("/home/user/fullstack"), **POSIX_BASH
        )
        assert "python -m venv .venv" in instructions
        assert "npm install" in instructions
        assert "pre-commit install" in instructions
        assert instructions[-1] == "./scripts/check-all.sh"

    def test_multi_language_preserves_order(self) -> None:
        """Language-specific steps should appear in the order of the languages tuple."""
        instructions = _get_setup_instructions(
            ("python", "typescript"), Path("/home/user/proj"), **POSIX_BASH
        )
        # Python venv must come before npm install
        venv_idx = instructions.index("python -m venv .venv")
        npm_idx = instructions.index("npm install")
        assert venv_idx < npm_idx

    def test_multi_language_rust_then_go(self) -> None:
        """Rust then Go should keep ordering."""
        instructions = _get_setup_instructions(
            ("rust", "go"), Path("/home/user/proj"), **POSIX_BASH
        )
        cargo_idx = instructions.index("cargo build")
        go_idx = instructions.index("go mod download")
        assert cargo_idx < go_idx

    def test_multi_language_common_tail_not_duplicated(self) -> None:
        """pre-commit install and check-all should appear only once."""
        instructions = _get_setup_instructions(
            ("python", "typescript", "go"), Path("/home/user/proj"), **POSIX_BASH
        )
        assert instructions.count("pre-commit install") == 1
        assert instructions.count("./scripts/check-all.sh") == 1

    def test_multi_language_cd_not_duplicated(self) -> None:
        """cd command should appear only once."""
        instructions = _get_setup_instructions(
            ("python", "rust"), Path("/home/user/proj"), **POSIX_BASH
        )
        cd_cmds = [c for c in instructions if c.startswith("cd ")]
        assert len(cd_cmds) == 1

    def test_path_with_spaces_is_quoted(self) -> None:
        """Paths containing spaces should be shell-quoted for safe copy-paste."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my project"), **POSIX_BASH
        )
        # The cd command should quote the path so `cd /home/user/my project`
        # doesn't silently break when copy-pasted
        cd_cmd = instructions[0]
        assert cd_cmd != "cd /home/user/my project"
        assert "my project" in cd_cmd  # path is still present
        # Either quoted or escaped
        assert "'" in cd_cmd or "\\" in cd_cmd or '"' in cd_cmd

    def test_duplicate_languages_not_doubled(self) -> None:
        """Duplicate languages in input should produce a single set of steps."""
        instructions = _get_setup_instructions(
            ("python", "python"), Path("/home/user/proj"), **POSIX_BASH
        )
        assert instructions.count("python -m venv .venv") == 1

    def test_duplicate_languages_preserves_order(self) -> None:
        """Deduplication should preserve the order of first occurrence."""
        instructions = _get_setup_instructions(
            ("typescript", "python", "typescript"),
            Path("/home/user/proj"),
            **POSIX_BASH,
        )
        npm_idx = instructions.index("npm install")
        venv_idx = instructions.index("python -m venv .venv")
        assert npm_idx < venv_idx
        assert instructions.count("npm install") == 1

    def test_empty_languages_tuple_has_sensible_default(self) -> None:
        """Empty languages tuple should still produce valid instructions."""
        instructions = _get_setup_instructions(
            (), Path("/home/user/proj"), **POSIX_BASH
        )
        assert instructions[0].startswith("cd ")
        assert "pre-commit install" in instructions
        assert instructions[-1] == "./scripts/check-all.sh"


class TestFinalizeInitWindowsNote:
    """The Git Bash note appears on Windows and only on Windows.

    Platform selection goes through the patchable ``is_windows`` seam
    from ``utils.fs`` (#380) — never by patching the real ``os.name``.
    Rich wraps long lines at column width, so assertions normalize
    whitespace before searching.
    """

    @staticmethod
    def _printed_output(capsys: pytest.CaptureFixture[str]) -> str:
        """Return captured stdout with all whitespace collapsed.

        Args:
            capsys: The pytest capture fixture for the test.

        Returns:
            The captured stdout joined on single spaces.
        """
        return " ".join(capsys.readouterr().out.split())

    def test_windows_prints_git_bash_note(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """On Windows the success message explains the Git Bash gate."""
        monkeypatch.setattr("start_green_stay_green.cli.is_windows", _always_windows)

        _finalize_init(tmp_path, "proj", ("python",))

        output = self._printed_output(capsys)
        assert "Git Bash" in output
        assert "bash scripts/check-all.sh" in output

    def test_posix_omits_git_bash_note(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """On POSIX no Windows-specific note clutters the output."""
        # bool() returns False — refurb's FURB111-preferred lambda: False.
        monkeypatch.setattr("start_green_stay_green.cli.is_windows", _always_posix)

        _finalize_init(tmp_path, "proj", ("python",))

        output = self._printed_output(capsys)
        assert "Git Bash" not in output
