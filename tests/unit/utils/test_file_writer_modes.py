"""Tests for FileWriter force and interactive modes.

Tests the --force and --interactive conflict resolution behavior
added in T2 (#252).
"""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from rich.console import Console

from start_green_stay_green.utils.file_writer import FileWriter
from start_green_stay_green.utils.file_writer import WriteResult


class TestForceMode:
    """Test FileWriter with force=True."""

    def test_force_overwrites_existing_file(self, tmp_path: Path) -> None:
        """Test write_file overwrites existing file when force=True."""
        writer = FileWriter(project_root=tmp_path, force=True)
        file_path = tmp_path / "existing.py"
        file_path.write_text("original content")

        result = writer.write_file(file_path, "new content")

        assert result == WriteResult.CREATED
        assert file_path.read_text() == "new content"
        assert writer.overwritten == 1
        assert writer.skipped == 0

    def test_force_overwrites_existing_script(self, tmp_path: Path) -> None:
        """Test write_script overwrites existing script when force=True."""
        writer = FileWriter(project_root=tmp_path, force=True)
        script_path = tmp_path / "test.sh"
        script_path.write_text("#!/bin/bash\noriginal")

        result = writer.write_script(script_path, "#!/bin/bash\nnew")

        assert result == WriteResult.CREATED
        assert script_path.read_text() == "#!/bin/bash\nnew"
        assert writer.overwritten == 1

    def test_force_overwrites_in_copy_tree(self, tmp_path: Path) -> None:
        """Test copy_tree with force=True overwrites existing files."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "file.txt").write_text("new")

        target = tmp_path / "target"
        target.mkdir()
        (target / "file.txt").write_text("old")

        writer = FileWriter(project_root=tmp_path, force=True)
        writer.copy_tree(source, target)

        assert (target / "file.txt").read_text() == "new"
        assert writer.overwritten == 1
        assert writer.skipped == 0

    def test_force_logs_overwrite(self, tmp_path: Path) -> None:
        """Test force mode logs OVERWRITE instead of CREATE for existing files."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, force=True, console=mock_console)
        existing = tmp_path / "file.py"
        existing.write_text("old")

        writer.write_file(existing, "new")

        call_args = mock_console.print.call_args[0][0]
        assert "OVERWRITE" in call_args

    def test_force_creates_new_file_normally(self, tmp_path: Path) -> None:
        """Test force mode still says CREATE for new files."""
        mock_console = MagicMock(spec=Console)
        writer = FileWriter(project_root=tmp_path, force=True, console=mock_console)

        writer.write_file(tmp_path / "new.py", "content")

        call_args = mock_console.print.call_args[0][0]
        assert "CREATE" in call_args

    def test_force_skip_existing_dir_returns_false(self, tmp_path: Path) -> None:
        """Test skip_existing_dir always returns False in force mode."""
        writer = FileWriter(project_root=tmp_path, force=True)
        arch_dir = tmp_path / "plans" / "architecture"
        arch_dir.mkdir(parents=True)
        (arch_dir / "rules.md").write_text("existing rules")

        result = writer.skip_existing_dir(arch_dir)

        assert not result

    def test_force_tracks_overwritten_count(self, tmp_path: Path) -> None:
        """Test force mode tracks overwritten files separately."""
        writer = FileWriter(project_root=tmp_path, force=True)
        existing = tmp_path / "existing.py"
        existing.write_text("old")

        writer.write_file(existing, "new")
        writer.write_file(tmp_path / "new.py", "content")

        assert writer.created == 1
        assert writer.overwritten == 1
        assert writer.skipped == 0

    def test_summary_includes_overwritten(self, tmp_path: Path) -> None:
        """Test summary includes overwritten count when non-zero."""
        writer = FileWriter(project_root=tmp_path, force=True)
        existing = tmp_path / "existing.py"
        existing.write_text("old")

        writer.write_file(existing, "new")
        writer.write_file(tmp_path / "new.py", "content")

        summary = writer.summary()
        assert "Created: 1" in summary
        assert "Overwritten: 1" in summary
        assert "Skipped: 0" in summary


class TestInteractiveMode:
    """Test FileWriter with interactive=True."""

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_skip(self, mock_ask: MagicMock, tmp_path: Path) -> None:
        """Test interactive mode skips when user chooses 's'."""
        mock_ask.return_value = "s"
        writer = FileWriter(
            project_root=tmp_path,
            interactive=True,
            console=Console(quiet=True),
        )
        existing = tmp_path / "file.py"
        existing.write_text("original")

        result = writer.write_file(existing, "new")

        assert result == WriteResult.SKIPPED
        assert existing.read_text() == "original"
        assert writer.skipped == 1

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_overwrite(self, mock_ask: MagicMock, tmp_path: Path) -> None:
        """Test interactive mode overwrites when user chooses 'o'."""
        mock_ask.return_value = "o"
        writer = FileWriter(
            project_root=tmp_path,
            interactive=True,
            console=Console(quiet=True),
        )
        existing = tmp_path / "file.py"
        existing.write_text("original")

        result = writer.write_file(existing, "new content")

        assert result == WriteResult.CREATED
        assert existing.read_text() == "new content"

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_all_overwrites_remaining(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Test interactive 'a' switches to force mode for remaining files."""
        mock_ask.return_value = "a"
        writer = FileWriter(
            project_root=tmp_path,
            interactive=True,
            console=Console(quiet=True),
        )
        file1 = tmp_path / "file1.py"
        file1.write_text("old1")
        file2 = tmp_path / "file2.py"
        file2.write_text("old2")

        writer.write_file(file1, "new1")
        # After 'a', should not prompt again
        writer.write_file(file2, "new2")

        assert file1.read_text() == "new1"
        assert file2.read_text() == "new2"
        # Should only have been called once (for file1)
        mock_ask.assert_called_once()

    @patch("start_green_stay_green.utils.file_writer.Prompt.ask")
    def test_interactive_diff_then_skip(
        self, mock_ask: MagicMock, tmp_path: Path
    ) -> None:
        """Test interactive 'd' shows diff then re-prompts."""
        # First call returns 'd' (show diff), second returns 's' (skip)
        mock_ask.side_effect = ["d", "s"]
        writer = FileWriter(
            project_root=tmp_path,
            interactive=True,
            console=Console(quiet=True),
        )
        existing = tmp_path / "file.py"
        existing.write_text("line1\nline2\n")

        result = writer.write_file(existing, "line1\nline3\n")

        assert result == WriteResult.SKIPPED
        assert existing.read_text() == "line1\nline2\n"
        assert mock_ask.call_count == 2

    def test_interactive_no_prompt_for_new_files(self, tmp_path: Path) -> None:
        """Test interactive mode does not prompt for new files."""
        writer = FileWriter(
            project_root=tmp_path,
            interactive=True,
            console=Console(quiet=True),
        )

        result = writer.write_file(tmp_path / "new.py", "content")

        assert result == WriteResult.CREATED


class TestMutualExclusion:
    """Test that force and interactive are mutually exclusive."""

    def test_force_and_interactive_raises(self, tmp_path: Path) -> None:
        """Test that force=True and interactive=True raises ValueError."""
        with __import__("pytest").raises(ValueError, match="mutually exclusive"):
            FileWriter(project_root=tmp_path, force=True, interactive=True)
