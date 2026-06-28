"""Unit tests for FileWriter utility.

Tests the safe file writing behavior that checks for existing files
before writing, tracks stats, and logs per-file outcomes.
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from rich.console import Console

from start_green_stay_green.utils.file_writer import FileWriter
from start_green_stay_green.utils.file_writer import WriteResult
from tests.conftest import assert_executable


def _printed_strings(mock_console: MagicMock) -> list[str]:
    """Collect every first positional arg passed to console.print.

    Returns:
        List of printed string payloads, one per print() call.
    """
    return [call.args[0] for call in mock_console.print.call_args_list]


def _last_printed(mock_console: MagicMock) -> str:
    """Return the most recent string passed to console.print.

    Returns:
        The last printed string payload.
    """
    return str(mock_console.print.call_args[0][0])


class TestWriteResult:
    """Test WriteResult enum values."""

    def test_has_created_value(self) -> None:
        """Test CREATED enum value exists."""
        assert WriteResult.CREATED.value == "created"

    def test_has_skipped_value(self) -> None:
        """Test SKIPPED enum value exists."""
        assert WriteResult.SKIPPED.value == "skipped"


class TestFileWriterInit:
    """Test FileWriter initialization."""

    def test_default_init(self, tmp_path: Path) -> None:
        """Test default FileWriter has zero stats."""
        writer = FileWriter(project_root=tmp_path)
        assert writer.created == 0
        assert writer.skipped == 0

    def test_custom_console(self, tmp_path: Path) -> None:
        """Test FileWriter accepts custom console."""
        console = Console()
        writer = FileWriter(project_root=tmp_path, console=console)
        assert writer.created == 0


class TestWriteFile:
    """Test FileWriter.write_file() behavior."""

    def test_creates_new_file(self, tmp_path: Path) -> None:
        """Test write_file creates a new file when it doesn't exist."""
        writer = FileWriter(project_root=tmp_path)
        file_path = tmp_path / "new_file.py"

        result = writer.write_file(file_path, "content")

        assert result == WriteResult.CREATED
        assert file_path.read_text() == "content"
        assert writer.created == 1
        assert writer.skipped == 0

    def test_skips_existing_file(self, tmp_path: Path) -> None:
        """Test write_file skips an existing file by default."""
        writer = FileWriter(project_root=tmp_path)
        file_path = tmp_path / "existing.py"
        file_path.write_text("original content")

        result = writer.write_file(file_path, "new content")

        assert result == WriteResult.SKIPPED
        assert file_path.read_text() == "original content"
        assert writer.created == 0
        assert writer.skipped == 1

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test write_file creates parent directories if needed."""
        writer = FileWriter(project_root=tmp_path)
        file_path = tmp_path / "subdir" / "deep" / "new_file.py"

        result = writer.write_file(file_path, "content")

        assert result == WriteResult.CREATED
        assert file_path.exists()
        assert file_path.read_text() == "content"

    def test_tracks_multiple_writes(self, tmp_path: Path) -> None:
        """Test write_file tracks stats across multiple calls."""
        writer = FileWriter(project_root=tmp_path)
        existing = tmp_path / "existing.py"
        existing.write_text("old")

        writer.write_file(tmp_path / "new1.py", "content1")
        writer.write_file(existing, "content2")
        writer.write_file(tmp_path / "new2.py", "content3")

        assert writer.created == 2
        assert writer.skipped == 1


class TestWriteScript:
    """Test FileWriter.write_script() behavior."""

    def test_creates_executable_script(self, tmp_path: Path) -> None:
        """Test write_script creates file with executable permissions."""
        writer = FileWriter(project_root=tmp_path)
        script_path = tmp_path / "test.sh"

        result = writer.write_script(script_path, "#!/bin/bash\necho hello")

        assert result == WriteResult.CREATED
        assert script_path.read_text() == "#!/bin/bash\necho hello"
        # Platform-aware: exact 0o755 on POSIX, existence on Windows (#380)
        assert_executable(script_path)

    def test_creates_missing_parent_directories(self, tmp_path: Path) -> None:
        """write_script creates absent parent dirs (parents=True)."""
        writer = FileWriter(project_root=tmp_path)
        # Two levels deep, neither parent exists yet.
        script_path = tmp_path / "scripts" / "nested" / "deploy.sh"

        result = writer.write_script(script_path, "#!/bin/bash\n")

        # With parents=False this raises FileNotFoundError instead.
        assert result == WriteResult.CREATED
        assert script_path.is_file()

    def test_created_counter_increments_by_one_per_script(self, tmp_path: Path) -> None:
        """Each new script bumps the created counter by exactly one."""
        writer = FileWriter(project_root=tmp_path)

        assert writer.created == 0
        writer.write_script(tmp_path / "a.sh", "#!/bin/bash\n")
        assert writer.created == 1
        writer.write_script(tmp_path / "b.sh", "#!/bin/bash\n")
        # Exactly 2: kills `= 1`, `-= 1`, and `+= 2` mutations.
        assert writer.created == 2

    def test_skips_existing_script(self, tmp_path: Path) -> None:
        """Test write_script skips existing script file."""
        writer = FileWriter(project_root=tmp_path)
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\noriginal")

        result = writer.write_script(script_path, "#!/bin/bash\nnew")

        assert result == WriteResult.SKIPPED
        assert script_path.read_text() == "#!/bin/bash\noriginal"


class TestCopyTree:
    """Test FileWriter.copy_tree() behavior."""

    def test_copies_new_directory(self, tmp_path: Path) -> None:
        """Test copy_tree copies source directory to new target."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("content1")
        (source / "file2.txt").write_text("content2")

        target = tmp_path / "target"
        writer = FileWriter(project_root=tmp_path)

        writer.copy_tree(source, target)

        assert (target / "file1.txt").read_text() == "content1"
        assert (target / "file2.txt").read_text() == "content2"
        assert writer.created == 2

    def test_skips_existing_files_in_target(self, tmp_path: Path) -> None:
        """Test copy_tree skips files that already exist in target."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file1.txt").write_text("new content")
        (source / "file2.txt").write_text("content2")

        target = tmp_path / "target"
        target.mkdir()
        (target / "file1.txt").write_text("existing content")

        writer = FileWriter(project_root=tmp_path)
        writer.copy_tree(source, target)

        assert (target / "file1.txt").read_text() == "existing content"
        assert (target / "file2.txt").read_text() == "content2"
        assert writer.created == 1
        assert writer.skipped == 1

    def test_copies_nested_directories(self, tmp_path: Path) -> None:
        """Test copy_tree handles nested subdirectories."""
        source = tmp_path / "source"
        (source / "sub").mkdir(parents=True)
        (source / "top.txt").write_text("top")
        (source / "sub" / "nested.txt").write_text("nested")

        target = tmp_path / "target"
        writer = FileWriter(project_root=tmp_path)
        writer.copy_tree(source, target)

        assert (target / "top.txt").read_text() == "top"
        assert (target / "sub" / "nested.txt").read_text() == "nested"
        assert writer.created == 2


class TestSummary:
    """Test FileWriter summary output."""

    def test_summary_text_with_mixed_stats(self, tmp_path: Path) -> None:
        """Test summary returns correct text for mixed results."""
        writer = FileWriter(project_root=tmp_path)
        existing = tmp_path / "existing.py"
        existing.write_text("old")

        writer.write_file(tmp_path / "new.py", "content")
        writer.write_file(existing, "content")

        summary = writer.summary()
        assert "Created: 1" in summary
        assert "Skipped: 1" in summary

    def test_summary_text_all_created(self, tmp_path: Path) -> None:
        """Test summary text when all files are created."""
        writer = FileWriter(project_root=tmp_path)
        writer.write_file(tmp_path / "a.py", "a")
        writer.write_file(tmp_path / "b.py", "b")

        summary = writer.summary()
        assert "Created: 2" in summary
        assert "Skipped: 0" in summary

    def test_summary_text_all_skipped(self, tmp_path: Path) -> None:
        """Test summary text when all files are skipped."""
        writer = FileWriter(project_root=tmp_path)
        existing = tmp_path / "existing.py"
        existing.write_text("old")

        writer.write_file(existing, "new")

        summary = writer.summary()
        assert "Created: 0" in summary
        assert "Skipped: 1" in summary


class TestRelativePaths:
    """Test that log output uses relative paths."""

    def test_logs_relative_path_on_create(self, tmp_path: Path) -> None:
        """Test CREATE log uses path relative to project_root."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)

        writer.write_file(tmp_path / "src" / "main.py", "content")

        call_args = mock_console.print.call_args[0][0]
        assert str(Path("src") / "main.py") in call_args
        assert "CREATE" in call_args

    def test_logs_relative_path_on_skip(self, tmp_path: Path) -> None:
        """Test SKIP log uses path relative to project_root."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)
        existing = tmp_path / "README.md"
        existing.write_text("old")

        writer.write_file(existing, "new")

        call_args = mock_console.print.call_args[0][0]
        assert "README.md" in call_args
        assert "SKIP" in call_args


class TestLineEndings:
    """Generated files keep LF endings on every platform (#386).

    On Windows, text-mode writes translate \\n to \\r\\n by default —
    fatal for the bash quality gates (bash cannot execute CRLF
    scripts). The Windows CI leg (#380) runs these tests on a platform
    where the assertion is load-bearing.
    """

    CONTENT = "#!/usr/bin/env bash\nset -euo pipefail\necho ok\n"

    def test_write_file_uses_lf_only(self, tmp_path: Path) -> None:
        """write_file never emits CR bytes."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        target = tmp_path / "config.yaml"

        writer.write_file(target, self.CONTENT)

        assert b"\r" not in target.read_bytes()

    def test_write_script_uses_lf_only(self, tmp_path: Path) -> None:
        """write_script never emits CR bytes."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        target = tmp_path / "gate.sh"

        writer.write_script(target, self.CONTENT)

        assert b"\r" not in target.read_bytes()

    def test_force_overwrite_uses_lf_only(self, tmp_path: Path) -> None:
        """The force-overwrite path also writes LF-only bytes."""
        writer = FileWriter(
            project_root=tmp_path,
            force=True,
            console=MagicMock(spec=Console),
        )
        target = tmp_path / "gate.sh"
        target.write_text("old")

        writer.write_script(target, self.CONTENT)

        assert b"\r" not in target.read_bytes()


class TestMutualExclusionMessage:
    """Exact wording of the mutual-exclusion error (#249)."""

    def test_error_message_is_exact(self, tmp_path: Path) -> None:
        """force+interactive raises ValueError with the exact message."""
        with pytest.raises(ValueError, match="mutually exclusive") as exc:
            FileWriter(project_root=tmp_path, force=True, interactive=True)

        assert str(exc.value) == "--force and --interactive are mutually exclusive"


class TestIsForceProperty:
    """Behavior of the is_force property (#263)."""

    def test_is_force_is_attribute_not_method(self, tmp_path: Path) -> None:
        """is_force is a property: equals the bool, not a bound method."""
        writer = FileWriter(project_root=tmp_path, force=True)

        # If @property were removed, writer.is_force would be a bound method
        # (truthy) and `is True` would fail.
        assert writer.is_force is True

    def test_is_force_false_by_default(self, tmp_path: Path) -> None:
        """is_force returns exactly False in default mode."""
        writer = FileWriter(project_root=tmp_path)

        assert writer.is_force is False


class TestShowDiffOutput:
    """Exact diff rendering in interactive 'd' flow (#265,#267,#269-275)."""

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_diff_preserves_line_endings(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Diff keeps newlines so changed lines render on separate lines."""
        mock_ask.side_effect = ["d", "s"]
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        existing = tmp_path / "file.py"
        existing.write_text("line1\nline2\n")

        writer.write_file(existing, "line1\nline3\n")

        diff_text = _printed_strings(mock_console)[0]
        # keepends=True keeps the trailing newline on each diff body line.
        # If keepends=False, difflib joins tokens with no separators, so
        # "-line2" and "+line3" would not each end in "\n".
        assert "-line2\n" in diff_text
        assert "+line3\n" in diff_text

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_diff_uses_existing_and_generated_labels(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Diff header uses 'existing/<rel>' and 'generated/<rel>' labels."""
        mock_ask.side_effect = ["d", "s"]
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        existing = tmp_path / "pkg" / "mod.py"
        existing.parent.mkdir()
        existing.write_text("a\n")

        writer.write_file(existing, "b\n")

        diff_text = _printed_strings(mock_console)[0]
        rel = str(Path("pkg") / "mod.py")
        # rel must appear (kills rel=None -> "existing/None"); exact prefixes
        # kill the XX-wrap mutants on the fromfile/tofile labels.
        assert f"--- existing/{rel}" in diff_text
        assert f"+++ generated/{rel}" in diff_text

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_diff_joined_without_separator(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """diff_text is the diff lines joined with '' (no inserted chars)."""
        mock_ask.side_effect = ["d", "s"]
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        existing = tmp_path / "f.py"
        existing.write_text("same\n")

        writer.write_file(existing, "diff\n")

        diff_text = _printed_strings(mock_console)[0]
        # join("") keeps lines contiguous; join("XXXX") would inject "XXXX"
        # between every line. diff_text=None would not be a str.
        assert isinstance(diff_text, str)
        assert "XXXX" not in diff_text
        # The two header lines are adjacent with only their own newlines.
        assert "+++ generated/f.py\n@@" in diff_text

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_diff_identical_files_message(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Identical content prints the exact 'files are identical' notice."""
        mock_ask.side_effect = ["d", "s"]
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        existing = tmp_path / "f.py"
        existing.write_text("identical\n")

        writer.write_file(existing, "identical\n")

        assert _printed_strings(mock_console)[0] == "  [dim](files are identical)[/dim]"


class TestConflictPrompt:
    """Exact prompt text and choices in _resolve_conflict (#277-283)."""

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_prompt_text_and_choices_exact(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Prompt passes exact message, choices list, and default."""
        mock_ask.return_value = "s"
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=Console(quiet=True)
        )
        existing = tmp_path / "conf.py"
        existing.write_text("old")

        writer.write_file(existing, "new")

        args, kwargs = mock_ask.call_args
        rel = "conf.py"
        expected_msg = (
            f"  [yellow]CONFLICT[/yellow] {rel}  "
            "[s]kip / [o]verwrite / [d]iff / [a]ll"
        )
        assert args[0] == expected_msg
        assert kwargs["choices"] == ["s", "o", "d", "a"]
        assert kwargs["default"] == "s"


class TestInteractiveAllSwitchesToForce:
    """Interactive 'a' flips state to force mode (#293,#294)."""

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_all_sets_force_clears_interactive(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """After 'a', is_force is True and a later conflict does not prompt."""
        mock_ask.return_value = "a"
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=Console(quiet=True)
        )
        f1 = tmp_path / "a1.py"
        f1.write_text("old1")
        f2 = tmp_path / "a2.py"
        f2.write_text("old2")

        writer.write_file(f1, "new1")
        # is_force True confirms _force=True; interactive must be cleared so
        # the second existing file takes the force branch (no second prompt).
        assert writer.is_force is True

        writer.write_file(f2, "new2")
        mock_ask.assert_called_once()
        assert f2.read_text() == "new2"
        assert writer.overwritten == 2


class TestOverwriteAndSkipLogs:
    """Exact log strings and counters for existing-file handling."""

    def test_force_overwrite_log_exact(self, tmp_path: Path) -> None:
        """Force overwrite prints the exact OVERWRITE line (#301)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, force=True, console=mock_console)
        existing = tmp_path / "x.py"
        existing.write_text("old")

        writer.write_file(existing, "new")

        assert _last_printed(mock_console) == "  [red]OVERWRITE[/red] x.py"

    def test_force_overwrite_increments_count(self, tmp_path: Path) -> None:
        """Force overwrite increments overwritten by one per file (#298)."""
        writer = FileWriter(
            project_root=tmp_path, force=True, console=MagicMock(spec=Console)
        )
        a = tmp_path / "a.py"
        a.write_text("old")
        b = tmp_path / "b.py"
        b.write_text("old")

        writer.write_file(a, "new")
        writer.write_file(b, "new")

        # `= 1` would leave this at 1; `+= 1` reaches 2.
        assert writer.overwritten == 2

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_overwrite_log_exact(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Interactive overwrite prints the exact OVERWRITE line (#305)."""
        mock_ask.return_value = "o"
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        existing = tmp_path / "y.py"
        existing.write_text("old")

        writer.write_file(existing, "new")

        assert _last_printed(mock_console) == "  [red]OVERWRITE[/red] y.py"

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_overwrite_increments_count(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Interactive overwrite increments overwritten correctly (#302-304)."""
        mock_ask.return_value = "o"
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=MagicMock(spec=Console)
        )
        a = tmp_path / "a.py"
        a.write_text("old")
        b = tmp_path / "b.py"
        b.write_text("old")

        writer.write_file(a, "new")
        writer.write_file(b, "new")

        # `= 1` stays 1; `-= 1` -> -1; `+= 2` -> 4. Only `+= 1` gives 2.
        assert writer.overwritten == 2

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_skip_log_exact_and_count(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Interactive skip prints exact SKIP line and bumps skipped (#306,#309)."""
        mock_ask.return_value = "s"
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(
            project_root=tmp_path, interactive=True, console=mock_console
        )
        a = tmp_path / "a.py"
        a.write_text("old")
        b = tmp_path / "b.py"
        b.write_text("old")

        writer.write_file(a, "new")
        writer.write_file(b, "new")

        assert (
            _last_printed(mock_console)
            == "  [yellow]SKIP[/yellow] b.py (kept existing)"
        )
        assert writer.skipped == 2

    def test_default_skip_log_exact_and_count(self, tmp_path: Path) -> None:
        """Default-mode skip prints exact SKIP line and bumps skipped (#310,#313)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)
        a = tmp_path / "a.py"
        a.write_text("old")
        b = tmp_path / "b.py"
        b.write_text("old")

        writer.write_file(a, "new")
        writer.write_file(b, "new")

        assert (
            _last_printed(mock_console)
            == "  [yellow]SKIP[/yellow] b.py (already exists)"
        )
        assert writer.skipped == 2


class TestCreateLogAndCount:
    """Exact CREATE log strings and created counter (#320,#328-331)."""

    def test_write_file_create_log_exact(self, tmp_path: Path) -> None:
        """write_file prints the exact CREATE line for a new file (#320)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)

        writer.write_file(tmp_path / "n.py", "content")

        assert _last_printed(mock_console) == "  [green]CREATE[/green] n.py"

    def test_write_script_create_log_exact(self, tmp_path: Path) -> None:
        """write_script prints the exact CREATE line for a new script (#331)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)

        writer.write_script(tmp_path / "s.sh", "#!/bin/bash\n")

        assert _last_printed(mock_console) == "  [green]CREATE[/green] s.sh"

    def test_write_script_increments_created(self, tmp_path: Path) -> None:
        """write_script increments created by one per new script (#328-330)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))

        writer.write_script(tmp_path / "a.sh", "x")
        writer.write_script(tmp_path / "b.sh", "y")

        # `= 1` stays 1; `-= 1` -> -1; `+= 2` -> 4. Only `+= 1` gives 2.
        assert writer.created == 2


class TestWriteScriptRelPathAndExecutable:
    """write_script rel label and chmod-on-overwrite branch (#321,#323,#325)."""

    def test_write_script_create_uses_rel_path(self, tmp_path: Path) -> None:
        """New-script CREATE log uses the relative path, not None (#321)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)
        nested = tmp_path / "scripts" / "go.sh"

        writer.write_script(nested, "x")

        rel = str(Path("scripts") / "go.sh")
        assert _last_printed(mock_console) == f"  [green]CREATE[/green] {rel}"

    def test_write_script_force_overwrite_is_executable(self, tmp_path: Path) -> None:
        """Force-overwritten script becomes executable (#323 result==CREATED)."""
        writer = FileWriter(
            project_root=tmp_path, force=True, console=MagicMock(spec=Console)
        )
        script = tmp_path / "run.sh"
        script.write_text("old")

        result = writer.write_script(script, "#!/bin/bash\nnew")

        assert result == WriteResult.CREATED
        assert script.read_text() == "#!/bin/bash\nnew"
        # The `if result == WriteResult.CREATED` branch must run make_executable;
        # `!=` would skip chmod.
        assert_executable(script)

    def test_write_script_skip_does_not_chmod(self, tmp_path: Path) -> None:
        """Skipped existing script is NOT re-chmodded (#323 SKIPPED branch)."""
        with patch(
            "start_green_stay_green.utils.file_writer.make_executable"
        ) as mock_chmod:
            writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
            script = tmp_path / "run.sh"
            script.write_text("old")

            result = writer.write_script(script, "new")

        assert result == WriteResult.SKIPPED
        # With `!=`, a SKIPPED result would wrongly trigger make_executable.
        mock_chmod.assert_not_called()


class TestSkipExistingDir:
    """Behavior of _dir_has_files / skip_existing_dir (#342-352)."""

    def test_empty_dir_returns_false(self, tmp_path: Path) -> None:
        """An existing but empty directory is not skipped (#342 and->or)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        empty = tmp_path / "empty"
        empty.mkdir()

        # exists() is True, any(iterdir()) is False. `and` -> False (not
        # skipped); `or` -> True (wrongly skipped).
        assert not writer.skip_existing_dir(empty)

    def test_nonexistent_dir_returns_false(self, tmp_path: Path) -> None:
        """A missing directory is not skipped without touching iterdir (#342)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))

        assert not writer.skip_existing_dir(tmp_path / "missing")

    def test_populated_dir_skips_and_returns_true(self, tmp_path: Path) -> None:
        """A non-empty directory is skipped and returns True (#343,#352)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)
        d = tmp_path / "plans"
        d.mkdir()
        (d / "one.md").write_text("a")
        (d / "two.md").write_text("b")

        result = writer.skip_existing_dir(d)

        # `not self._dir_has_files` is essential: `or self._dir_has_files`
        # would return False here. `return False` mutant flips the True.
        assert result
        assert writer.skipped == 2

    def test_populated_dir_logs_exact_and_uses_rel(self, tmp_path: Path) -> None:
        """Each skipped file logs the exact SKIP line with its rel path (#350,#351)."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, console=mock_console)
        d = tmp_path / "plans"
        d.mkdir()
        (d / "only.md").write_text("a")

        writer.skip_existing_dir(d)

        rel = str(Path("plans") / "only.md")
        assert _last_printed(mock_console) == (
            f"  [yellow]SKIP[/yellow] {rel} (already exists)"
        )

    def test_skip_count_increments_per_file(self, tmp_path: Path) -> None:
        """skip_existing_dir bumps skipped by exactly one per file (#347-349)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        d = tmp_path / "plans"
        d.mkdir()
        (d / "a.md").write_text("a")
        (d / "b.md").write_text("b")
        (d / "c.md").write_text("c")

        writer.skip_existing_dir(d)

        # `= 1` stays 1; `-= 1` -> -3; `+= 2` -> 6. Only `+= 1` gives 3.
        assert writer.skipped == 3

    def test_rglob_pattern_matches_nested_files(self, tmp_path: Path) -> None:
        """rglob('*') walks nested files so they get counted (#346)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        d = tmp_path / "plans"
        (d / "sub").mkdir(parents=True)
        (d / "top.md").write_text("a")
        (d / "sub" / "deep.md").write_text("b")

        writer.skip_existing_dir(d)

        # rglob("*") finds both the top and nested file. A bogus pattern
        # like "XX*XX" would match nothing -> skipped stays 0.
        assert writer.skipped == 2


class TestSummaryExactStrings:
    """Exact summary formatting and the overwritten boundary (#353-359)."""

    def test_summary_exact_without_overwritten(self, tmp_path: Path) -> None:
        """Summary joins exactly 'Created: N, Skipped: M' when none overwritten."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        writer.write_file(tmp_path / "n.py", "x")
        existing = tmp_path / "e.py"
        existing.write_text("old")
        writer.write_file(existing, "new")

        # Kills XX-wraps on the part strings (#353,#354), the ", " join
        # separator (#359), and the >0 boundary (#356: >=0 would append
        # "Overwritten: 0").
        assert writer.summary() == "Created: 1, Skipped: 1"

    def test_summary_exact_with_overwritten(self, tmp_path: Path) -> None:
        """Summary appends exact 'Overwritten: N' part when count > 0 (#358)."""
        writer = FileWriter(
            project_root=tmp_path, force=True, console=MagicMock(spec=Console)
        )
        existing = tmp_path / "e.py"
        existing.write_text("old")
        writer.write_file(existing, "new")
        writer.write_file(tmp_path / "n.py", "x")

        assert writer.summary() == "Created: 1, Skipped: 0, Overwritten: 1"

    def test_summary_omits_overwritten_at_zero(self, tmp_path: Path) -> None:
        """Summary omits the Overwritten part when count is exactly 0 (#356)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        writer.write_file(tmp_path / "n.py", "x")

        # overwritten == 0: `> 0` is False (omit); `>= 0` is True (would add
        # "Overwritten: 0").
        assert writer.summary() == "Created: 1, Skipped: 0"


class TestMkdirParents:
    """Parent-directory creation flags (#325,#332)."""

    def test_write_script_creates_nested_parents(self, tmp_path: Path) -> None:
        """write_script creates missing intermediate parent dirs (#325)."""
        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        nested = tmp_path / "a" / "b" / "c" / "go.sh"

        result = writer.write_script(nested, "x")

        # parents=True is required: with parents=False, the missing
        # intermediate dirs would raise FileNotFoundError.
        assert result == WriteResult.CREATED
        assert nested.read_text() == "x"

    def test_copy_tree_creates_nested_target(self, tmp_path: Path) -> None:
        """copy_tree creates a deeply nested target directory (#332)."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "f.txt").write_text("c")
        target = tmp_path / "deep" / "nested" / "target"

        writer = FileWriter(project_root=tmp_path, console=MagicMock(spec=Console))
        writer.copy_tree(source, target)

        # target.mkdir(parents=True) is required for the nested path;
        # parents=False would raise FileNotFoundError before any copy.
        assert (target / "f.txt").read_text() == "c"
