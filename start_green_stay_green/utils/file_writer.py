"""Safe file writer with existence checking and stats tracking.

Provides a centralized utility for writing files that checks for existing
files before writing, tracks created/skipped counts, and logs outcomes.
Used by generators and the CLI to implement additive ``green init`` behavior.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from pathlib import Path


class WriteResult(Enum):
    """Result of a file write operation.

    Attributes:
        CREATED: File was written successfully (new or overwritten).
        SKIPPED: File already exists and was not overwritten.
    """

    CREATED = "created"
    SKIPPED = "skipped"


class FileWriter:
    """Safe file writer that checks for existing files before writing.

    Tracks stats across all write operations and logs per-file outcomes
    using relative paths for readability.

    Attributes:
        created: Number of files created.
        skipped: Number of files skipped (already existed).

    Example:
        >>> writer = FileWriter(project_root=Path("/tmp/my-project"))
        >>> writer.write_file(Path("/tmp/my-project/README.md"), "# Hello")
        <WriteResult.CREATED: 'created'>
        >>> writer.summary()
        'Created: 1, Skipped: 0'
    """

    def __init__(
        self,
        project_root: Path,
        *,
        force: bool = False,
        console: Console | None = None,
    ) -> None:
        """Initialize FileWriter.

        Args:
            project_root: Root directory for relative path display.
            force: If True, overwrite existing files without checking.
            console: Rich console for output. If None, creates a new one.
        """
        self._project_root = project_root
        self._force = force

        if console is None:
            self._console = Console()
        else:
            self._console = console

        self.created = 0
        self.skipped = 0

    def _relative_path(self, file_path: Path) -> str:
        """Get path relative to project root for display.

        Args:
            file_path: Absolute path to display.

        Returns:
            Relative path string, or absolute if not under project root.
        """
        try:
            return str(file_path.relative_to(self._project_root))
        except ValueError:
            return str(file_path)

    def write_file(self, file_path: Path, content: str) -> WriteResult:
        """Write a file, skipping if it already exists.

        Args:
            file_path: Path where file will be written.
            content: Content to write.

        Returns:
            WriteResult indicating whether file was created or skipped.
        """
        rel = self._relative_path(file_path)

        if file_path.exists() and not self._force:
            self.skipped += 1
            self._console.print(f"  [yellow]SKIP[/yellow] {rel} (already exists)")
            return WriteResult.SKIPPED

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        self.created += 1
        self._console.print(f"  [green]CREATE[/green] {rel}")
        return WriteResult.CREATED

    def write_script(self, file_path: Path, content: str) -> WriteResult:
        """Write a script file with executable permissions.

        Args:
            file_path: Path where script will be written.
            content: Script content.

        Returns:
            WriteResult indicating whether script was created or skipped.
        """
        rel = self._relative_path(file_path)

        if file_path.exists() and not self._force:
            self.skipped += 1
            self._console.print(f"  [yellow]SKIP[/yellow] {rel} (already exists)")
            return WriteResult.SKIPPED

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        file_path.chmod(0o755)
        self.created += 1
        self._console.print(f"  [green]CREATE[/green] {rel}")
        return WriteResult.CREATED

    def copy_tree(self, source: Path, target: Path) -> None:
        """Copy a directory tree, skipping existing files in target.

        Walks the source directory and copies each file individually,
        checking for existence before each write.

        Args:
            source: Source directory to copy from.
            target: Target directory to copy to.
        """
        target.mkdir(parents=True, exist_ok=True)

        for source_file in sorted(source.rglob("*")):
            if not source_file.is_file():
                continue

            relative = source_file.relative_to(source)
            target_file = target / relative

            content = source_file.read_text()
            self.write_file(target_file, content)

    def skip_existing_dir(self, directory: Path) -> bool:
        """Skip all files in a directory if it already has content.

        Used for generators that write files internally and can't be
        individually controlled. If the directory exists and contains files,
        marks them all as skipped and returns True.

        Args:
            directory: Directory to check.

        Returns:
            True if directory had existing files (skipped), False otherwise.
        """
        if not directory.exists() or not any(directory.iterdir()):
            return False

        for f in sorted(directory.rglob("*")):
            if f.is_file():
                self.skipped += 1
                rel = self._relative_path(f)
                self._console.print(f"  [yellow]SKIP[/yellow] {rel} (already exists)")
        return True

    def summary(self) -> str:
        """Return a summary of write operations.

        Returns:
            Summary string with created and skipped counts.
        """
        return f"Created: {self.created}, Skipped: {self.skipped}"
