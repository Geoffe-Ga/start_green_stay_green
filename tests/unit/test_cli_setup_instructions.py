"""Tests for language-specific setup instructions in CLI init output."""

from pathlib import Path

from start_green_stay_green.cli import _get_setup_instructions


class TestGetSetupInstructions:
    """Tests for _get_setup_instructions."""

    def test_python_includes_venv_creation(self) -> None:
        """Python setup should create a virtualenv."""
        instructions = _get_setup_instructions(
            ("python",), Path("/home/user/my-project")
        )
        assert "python -m venv .venv" in instructions

    def test_python_includes_venv_activation(self) -> None:
        """Python setup should activate the virtualenv."""
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

    def test_unknown_language_has_sensible_default(self) -> None:
        """Unknown languages should still get pre-commit + check-all."""
        instructions = _get_setup_instructions(("ruby",), Path("/home/user/ruby-proj"))
        assert instructions[0] == "cd /home/user/ruby-proj"
        assert "pre-commit install" in instructions
        assert "./scripts/check-all.sh" in instructions

    def test_all_languages_end_with_check_all(self) -> None:
        """Every language's instructions should end with check-all."""
        for lang in ("python", "typescript", "go", "rust", "java"):
            instructions = _get_setup_instructions((lang,), Path("/home/user/proj"))
            assert (
                instructions[-1] == "./scripts/check-all.sh"
            ), f"{lang} should end with check-all"

    def test_all_languages_include_precommit(self) -> None:
        """Every language's instructions should include pre-commit install."""
        for lang in ("python", "typescript", "go", "rust", "java"):
            instructions = _get_setup_instructions((lang,), Path("/home/user/proj"))
            assert (
                "pre-commit install" in instructions
            ), f"{lang} should include pre-commit install"

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

    def test_empty_languages_tuple_has_sensible_default(self) -> None:
        """Empty languages tuple should still produce valid instructions."""
        instructions = _get_setup_instructions((), Path("/home/user/proj"))
        assert instructions[0].startswith("cd ")
        assert "pre-commit install" in instructions
        assert instructions[-1] == "./scripts/check-all.sh"
