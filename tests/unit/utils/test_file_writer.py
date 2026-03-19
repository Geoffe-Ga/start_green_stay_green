"""Unit tests for FileWriter utility.

Tests the safe file writing behavior that checks for existing files
before writing, tracks stats, and logs per-file outcomes.
"""

from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console

from start_green_stay_green.utils.file_writer import FileWriter
from start_green_stay_green.utils.file_writer import WriteResult


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
        assert script_path.stat().st_mode & 0o755 == 0o755

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
        assert "src/main.py" in call_args
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
