"""Safe file writer with existence checking and stats tracking.

Provides a centralized utility for writing files that checks for existing
files before writing, tracks created/skipped counts, and logs outcomes.
Used by generators and the CLI to implement additive ``green init`` behavior.

Supports three conflict resolution modes:
- Default: skip existing files
- Force (``force=True``): overwrite all existing files
- Interactive (``interactive=True``): prompt per-file with skip/overwrite/diff
"""

from __future__ import annotations

import difflib
from enum import Enum
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Prompt

if TYPE_CHECKING:
    from pathlib import Path


class WriteResult(Enum):
    """Result of a file write operation.

    Attributes:
        CREATED: File was written successfully (new file).
        SKIPPED: File already exists and was not overwritten.
    """

    CREATED = "created"
    SKIPPED = "skipped"


class FileWriter:
    """Safe file writer that checks for existing files before writing.

    Tracks stats across all write operations and logs per-file outcomes
    using relative paths for readability.

    Three conflict resolution modes:
    - Default: skip existing files silently
    - Force: overwrite all existing files without prompting
    - Interactive: prompt the user per conflicting file

    Attributes:
        created: Number of new files created.
        skipped: Number of files skipped (already existed).
        overwritten: Number of existing files overwritten.

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
        interactive: bool = False,
        console: Console | None = None,
    ) -> None:
        """Initialize FileWriter.

        Args:
            project_root: Root directory for relative path display.
            force: If True, overwrite all existing files without prompting.
            interactive: If True, prompt per-file for conflict resolution.
            console: Rich console for output. If None, creates a new one.

        Raises:
            ValueError: If both force and interactive are True.
        """
        if force and interactive:
            msg = "--force and --interactive are mutually exclusive"
            raise ValueError(msg)

        self._project_root = project_root
        self._force = force
        self._interactive = interactive

        if console is None:
            self._console = Console()
        else:
            self._console = console

        self.created = 0
        self.skipped = 0
        self.overwritten = 0

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

    def _show_diff(self, file_path: Path, new_content: str) -> None:
        """Show unified diff between existing and new content.

        Args:
            file_path: Path to existing file.
            new_content: Content that would replace the file.
        """
        existing = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
        proposed = new_content.splitlines(keepends=True)
        rel = self._relative_path(file_path)

        diff = difflib.unified_diff(
            existing,
            proposed,
            fromfile=f"existing/{rel}",
            tofile=f"generated/{rel}",
        )
        diff_text = "".join(diff)
        if diff_text:
            self._console.print(diff_text)
        else:
            self._console.print("  [dim](files are identical)[/dim]")

    def _resolve_conflict(self, file_path: Path, content: str, rel: str) -> bool:
        """Prompt user to resolve a file conflict interactively.

        Args:
            file_path: Path to the existing file.
            content: New content that would be written.
            rel: Relative path string for display.

        Returns:
            True if the file should be overwritten, False to skip.
        """
        while True:
            choice = Prompt.ask(
                f"  [yellow]CONFLICT[/yellow] {rel}  "
                "[s]kip / [o]verwrite / [d]iff / [a]ll",
                choices=["s", "o", "d", "a"],
                default="s",
            )

            if choice == "s":
                return False
            if choice == "o":
                return True
            if choice == "a":
                self._interactive = False
                self._force = True
                return True
            self._show_diff(file_path, content)

    def _handle_existing(self, file_path: Path, content: str, rel: str) -> WriteResult:
        """Handle an existing file based on the current mode.

        Args:
            file_path: Path to the existing file.
            content: New content to potentially write.
            rel: Relative path string for display.

        Returns:
            WriteResult indicating the outcome.
        """
        if self._force:
            file_path.write_text(content, encoding="utf-8")
            self.overwritten += 1
            self._console.print(f"  [red]OVERWRITE[/red] {rel}")
            return WriteResult.CREATED

        if self._interactive:
            if self._resolve_conflict(file_path, content, rel):
                file_path.write_text(content, encoding="utf-8")
                self.overwritten += 1
                self._console.print(f"  [red]OVERWRITE[/red] {rel}")
                return WriteResult.CREATED
            self.skipped += 1
            self._console.print(f"  [yellow]SKIP[/yellow] {rel} (kept existing)")
            return WriteResult.SKIPPED

        # Default mode: skip
        self.skipped += 1
        self._console.print(f"  [yellow]SKIP[/yellow] {rel} (already exists)")
        return WriteResult.SKIPPED

    def write_file(self, file_path: Path, content: str) -> WriteResult:
        """Write a file, handling conflicts based on current mode.

        Args:
            file_path: Path where file will be written.
            content: Content to write.

        Returns:
            WriteResult indicating whether file was created or skipped.
        """
        rel = self._relative_path(file_path)

        if file_path.exists():
            return self._handle_existing(file_path, content, rel)

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

        if file_path.exists():
            result = self._handle_existing(file_path, content, rel)
            if result == WriteResult.CREATED:
                file_path.chmod(0o755)
            return result

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        file_path.chmod(0o755)
        self.created += 1
        self._console.print(f"  [green]CREATE[/green] {rel}")
        return WriteResult.CREATED

    def copy_tree(self, source: Path, target: Path) -> None:
        """Copy a directory tree, handling conflicts per current mode.

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

            content = source_file.read_text(encoding="utf-8")
            self.write_file(target_file, content)

    def _dir_has_files(self, directory: Path) -> bool:
        """Check if a directory exists and contains entries.

        Args:
            directory: Directory to check.

        Returns:
            True if directory exists and is non-empty.
        """
        return directory.exists() and any(directory.iterdir())

    def skip_existing_dir(self, directory: Path) -> bool:
        """Skip all files in a directory if it already has content.

        Used for generators that write files internally and can't be
        individually controlled. In force mode, always returns False
        to allow regeneration.

        Args:
            directory: Directory to check.

        Returns:
            True if directory had existing files (skipped), False otherwise.
        """
        if self._force or not self._dir_has_files(directory):
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
            Summary string with created, skipped, and overwritten counts.
        """
        parts = [
            f"Created: {self.created}",
            f"Skipped: {self.skipped}",
        ]
        if self.overwritten > 0:
            parts.append(f"Overwritten: {self.overwritten}")
        return ", ".join(parts)
