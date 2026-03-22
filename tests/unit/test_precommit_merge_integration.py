"""Tests for pre-commit config merge integration in CLI.

Tests _write_precommit_config and _merge_and_write_precommit
behavior with existing, new, force, and malformed configs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from pathlib import Path

from start_green_stay_green.cli import _write_precommit_config
from start_green_stay_green.utils.file_writer import FileWriter

EXISTING_CONFIG = (
    "repos:\n"
    "- repo: https://github.com/pre-commit/hooks\n"
    "  rev: v4.5.0\n"
    "  hooks:\n"
    "  - id: trailing-whitespace\n"
)

GENERATED_CONFIG = (
    "repos:\n"
    "- repo: https://github.com/psf/black\n"
    "  rev: '24.1.0'\n"
    "  hooks:\n"
    "  - id: black\n"
)


class TestWritePrecommitConfig:
    """Test _write_precommit_config branching logic."""

    def test_new_file_creates_via_file_writer(self, tmp_path: Path) -> None:
        """Test new file is created through FileWriter."""
        writer = FileWriter(project_root=tmp_path, console=Console(quiet=True))
        precommit_file = tmp_path / ".pre-commit-config.yaml"

        _write_precommit_config(precommit_file, GENERATED_CONFIG, writer)

        assert precommit_file.exists()
        assert "psf/black" in precommit_file.read_text()
        assert writer.created == 1

    def test_existing_file_merges(self, tmp_path: Path) -> None:
        """Test existing file triggers merge instead of skip."""
        writer = FileWriter(project_root=tmp_path, console=Console(quiet=True))
        precommit_file = tmp_path / ".pre-commit-config.yaml"
        precommit_file.write_text(EXISTING_CONFIG)

        _write_precommit_config(precommit_file, GENERATED_CONFIG, writer)

        content = precommit_file.read_text()
        assert "pre-commit/hooks" in content
        assert "psf/black" in content

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """Test force mode overwrites instead of merging."""
        writer = FileWriter(
            project_root=tmp_path,
            force=True,
            console=Console(quiet=True),
        )
        precommit_file = tmp_path / ".pre-commit-config.yaml"
        precommit_file.write_text(EXISTING_CONFIG)

        _write_precommit_config(precommit_file, GENERATED_CONFIG, writer)

        content = precommit_file.read_text()
        assert "psf/black" in content
        assert "pre-commit/hooks" not in content

    def test_no_file_writer_writes_directly(self, tmp_path: Path) -> None:
        """Test without FileWriter, writes directly."""
        precommit_file = tmp_path / ".pre-commit-config.yaml"

        _write_precommit_config(precommit_file, GENERATED_CONFIG, None)

        assert precommit_file.exists()
        assert "psf/black" in precommit_file.read_text()

    def test_malformed_existing_skips_merge(self, tmp_path: Path) -> None:
        """Test malformed existing YAML skips merge gracefully."""
        writer = FileWriter(project_root=tmp_path, console=Console(quiet=True))
        precommit_file = tmp_path / ".pre-commit-config.yaml"
        precommit_file.write_text("repos: [{bad yaml")

        _write_precommit_config(precommit_file, GENERATED_CONFIG, writer)

        # Should keep existing (malformed) content, not crash
        assert precommit_file.read_text() == "repos: [{bad yaml"
