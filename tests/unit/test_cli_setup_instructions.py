"""Tests for language-specific setup instructions in CLI init output."""

from pathlib import Path

import pytest

from start_green_stay_green.cli import _get_setup_instructions
from start_green_stay_green.cli import _venv_activation_command

# Languages exercised by the per-language common-tail tests; "java" covers
# the unknown-language default path.
ALL_LANGUAGES = ("python", "typescript", "go", "rust", "swift", "java")


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
        env = {"PSModulePath": "C:\\Users\\dev\\Documents\\PowerShell\\Modules"}
        command = _venv_activation_command("nt", env)
        assert command == ".venv\\Scripts\\Activate.ps1"

    def test_windows_ignores_posix_shell_var(self) -> None:
        """On Windows, a stray SHELL env var should not trigger POSIX forms."""
        command = _venv_activation_command("nt", {"SHELL": "/usr/bin/fish"})
        assert command == ".venv\\Scripts\\activate"


class TestGetSetupInstructions:
    """Tests for _get_setup_instructions."""

    def test_python_includes_venv_creation(self) -> None:
        """Python setup should create a virtualenv."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "python -m venv .venv" in instructions

    def test_python_includes_venv_activation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Python setup should activate the virtualenv."""
        monkeypatch.delenv("SHELL", raising=False)
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "source .venv/bin/activate" in instructions

    def test_python_activation_respects_fish_shell(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Python setup should emit the fish activation script under fish."""
        monkeypatch.setenv("SHELL", "/usr/bin/fish")
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "source .venv/bin/activate.fish" in instructions
        assert "source .venv/bin/activate" not in instructions

    def test_python_activation_defaults_without_shell_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Python setup should keep the bash/zsh form when SHELL is unset."""
        monkeypatch.delenv("SHELL", raising=False)
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "source .venv/bin/activate" in instructions

    def test_python_includes_pip_install(self) -> None:
        """Python setup should install requirements."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        pip_cmds = [c for c in instructions if "pip install" in c]
        assert len(pip_cmds) == 1
        assert "requirements.txt" in pip_cmds[0]
        assert "requirements-dev.txt" in pip_cmds[0]

    def test_python_includes_precommit_and_check_all(self) -> None:
        """Python setup should end with pre-commit install and check-all."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "pre-commit install" in instructions
        assert "./scripts/check-all.sh" in instructions

    def test_python_starts_with_cd(self) -> None:
        """Python setup should start with cd into project."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert instructions[0] == "cd /home/user/my-project"

    def test_typescript_includes_npm_install(self) -> None:
        """TypeScript setup should run npm install."""
        instructions = _get_setup_instructions(
            ("typescript",), Path("/home/user/ts-proj")
        )
        assert "npm install" in instructions

    def test_typescript_no_venv(self) -> None:
        """TypeScript should not include Python venv steps."""
        instructions = _get_setup_instructions(
            ("typescript",), Path("/home/user/ts-proj")
        )
        assert "python -m venv .venv" not in instructions

    def test_go_includes_mod_download(self) -> None:
        """Go setup should download modules."""
        instructions = _get_setup_instructions(("go",), Path("/home/user/go-proj"))
        assert "go mod download" in instructions

    def test_rust_includes_cargo_build(self) -> None:
        """Rust setup should run cargo build."""
        instructions = _get_setup_instructions(("rust",), Path("/home/user/rust-proj"))
        assert "cargo build" in instructions

    def test_swift_includes_swift_build(self) -> None:
        """Swift setup should resolve dependencies and build the SPM package."""
        instructions = _get_setup_instructions(
            ("swift",), Path("/home/user/swift-proj")
        )
        assert "swift package resolve" in instructions
        assert "swift build" in instructions

    def test_unknown_language_has_sensible_default(self) -> None:
        """Unknown languages should still get pre-commit + check-all."""
        instructions = _get_setup_instructions(("ruby",), Path("/home/user/ruby-proj"))
        assert instructions[0] == "cd /home/user/ruby-proj"
        assert "pre-commit install" in instructions
        assert "./scripts/check-all.sh" in instructions

    @pytest.mark.parametrize("lang", ALL_LANGUAGES)
    def test_language_ends_with_check_all(self, lang: str) -> None:
        """Every language's instructions should end with check-all."""
        instructions = _get_setup_instructions((lang,), Path("/home/user/proj"))
        assert instructions[-1] == "./scripts/check-all.sh"

    @pytest.mark.parametrize("lang", ALL_LANGUAGES)
    def test_language_includes_precommit(self, lang: str) -> None:
        """Every language's instructions should include pre-commit install."""
        instructions = _get_setup_instructions((lang,), Path("/home/user/proj"))
        assert "pre-commit install" in instructions

    def test_returns_list_of_strings(self) -> None:
        """Instructions should be a list of strings."""
        instructions = _get_setup_instructions(("python",), Path("/home/user/proj"))
        assert isinstance(instructions, list)
        assert all(isinstance(cmd, str) for cmd in instructions)

    def test_project_path_in_cd_command(self) -> None:
        """The cd command should use the exact project path."""
        path = Path("/home/user/my-awesome-project")
        instructions = _get_setup_instructions(("python",), path)
        assert instructions[0] == "cd /home/user/my-awesome-project"

    def test_multi_language_python_and_typescript(self) -> None:
        """Multi-language python+typescript should include steps for both."""
        instructions = _get_setup_instructions(
            ("python", "typescript"), Path("/home/user/fullstack")
        )
        assert "python -m venv .venv" in instructions
        assert "npm install" in instructions
        assert "pre-commit install" in instructions
        assert instructions[-1] == "./scripts/check-all.sh"

    def test_multi_language_preserves_order(self) -> None:
        """Language-specific steps should appear in the order of the languages tuple."""
        instructions = _get_setup_instructions(
            ("python", "typescript"), Path("/home/user/proj")
        )
        # Python venv must come before npm install
        venv_idx = instructions.index("python -m venv .venv")
        npm_idx = instructions.index("npm install")
        assert venv_idx < npm_idx

    def test_multi_language_rust_then_go(self) -> None:
        """Rust then Go should keep ordering."""
        instructions = _get_setup_instructions(("rust", "go"), Path("/home/user/proj"))
        cargo_idx = instructions.index("cargo build")
        go_idx = instructions.index("go mod download")
        assert cargo_idx < go_idx

    def test_multi_language_common_tail_not_duplicated(self) -> None:
        """pre-commit install and check-all should appear only once."""
        instructions = _get_setup_instructions(
            ("python", "typescript", "go"), Path("/home/user/proj")
        )
        assert instructions.count("pre-commit install") == 1
        assert instructions.count("./scripts/check-all.sh") == 1

    def test_multi_language_cd_not_duplicated(self) -> None:
        """cd command should appear only once."""
        instructions = _get_setup_instructions(
            ("python", "rust"), Path("/home/user/proj")
        )
        cd_cmds = [c for c in instructions if c.startswith("cd ")]
        assert len(cd_cmds) == 1

    def test_path_with_spaces_is_quoted(self) -> None:
        """Paths containing spaces should be shell-quoted for safe copy-paste."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my project")
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
            ("python", "python"), Path("/home/user/proj")
        )
        assert instructions.count("python -m venv .venv") == 1

    def test_duplicate_languages_preserves_order(self) -> None:
        """Deduplication should preserve the order of first occurrence."""
        instructions = _get_setup_instructions(
            ("typescript", "python", "typescript"), Path("/home/user/proj")
        )
        npm_idx = instructions.index("npm install")
        venv_idx = instructions.index("python -m venv .venv")
        assert npm_idx < venv_idx
        assert instructions.count("npm install") == 1

    def test_empty_languages_tuple_has_sensible_default(self) -> None:
        """Empty languages tuple should still produce valid instructions."""
        instructions = _get_setup_instructions((), Path("/home/user/proj"))
        assert instructions[0].startswith("cd ")
        assert "pre-commit install" in instructions
        assert instructions[-1] == "./scripts/check-all.sh"
