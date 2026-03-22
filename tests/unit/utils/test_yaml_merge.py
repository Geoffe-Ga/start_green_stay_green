"""Tests for YAML merge utility for .pre-commit-config.yaml.

Tests the merge logic that combines existing and generated pre-commit
configs, preserving existing repos and appending new ones.
"""

from __future__ import annotations

import pytest
import yaml

from start_green_stay_green.utils.yaml_merge import merge_precommit_configs


class TestMergeBasicBehavior:
    """Test core merge semantics."""

    def test_empty_existing_returns_generated(self) -> None:
        """Test empty existing string returns generated config."""
        generated = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        merged, added, kept = merge_precommit_configs("", generated)
        assert "trailing-whitespace" in merged
        assert added == 1
        assert kept == 0

    def test_same_repo_keeps_existing(self) -> None:
        """Test same repo URL keeps existing config entirely."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.4.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
            "  - id: custom-hook\n"
        )
        generated = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
            "  - id: end-of-file-fixer\n"
        )
        merged, added, kept = merge_precommit_configs(existing, generated)
        # Should keep existing rev and hooks
        assert "v4.4.0" in merged
        assert "custom-hook" in merged
        assert added == 0
        assert kept == 1

    def test_new_repo_appended(self) -> None:
        """Test new repo from generated is appended to existing."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        generated = (
            "repos:\n"
            "- repo: https://github.com/astral-sh/ruff-pre-commit\n"
            "  rev: v0.2.0\n"
            "  hooks:\n"
            "  - id: ruff\n"
        )
        merged, added, kept = merge_precommit_configs(existing, generated)
        assert "ruff-pre-commit" in merged
        assert "pre-commit/hooks" in merged
        assert added == 1
        assert kept == 1

    def test_mixed_overlap_and_new(self) -> None:
        """Test mix of overlapping and new repos."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        generated = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.6.0\n"
            "  hooks:\n"
            "  - id: end-of-file-fixer\n"
            "- repo: https://github.com/psf/black\n"
            "  rev: '24.1.0'\n"
            "  hooks:\n"
            "  - id: black\n"
        )
        merged, added, kept = merge_precommit_configs(existing, generated)
        # Existing repo kept with original rev
        assert "v4.5.0" in merged
        # New repo appended
        assert "psf/black" in merged
        assert added == 1
        assert kept == 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_malformed_yaml_raises_value_error(self) -> None:
        """Test malformed YAML raises ValueError."""
        with pytest.raises(ValueError, match=r"[Ii]nvalid"):
            merge_precommit_configs("repos: [{bad yaml", "repos:\n- repo: x\n")

    def test_missing_repos_key_in_existing(self) -> None:
        """Test existing config without repos key gets generated repos."""
        existing = "default_language_version:\n  python: python3.11\n"
        generated = (
            "repos:\n"
            "- repo: https://github.com/psf/black\n"
            "  rev: '24.1.0'\n"
            "  hooks:\n"
            "  - id: black\n"
        )
        merged, added, kept = merge_precommit_configs(existing, generated)
        assert "psf/black" in merged
        assert "python3.11" in merged
        assert added == 1
        assert kept == 0

    def test_missing_repos_key_in_generated(self) -> None:
        """Test generated config without repos key returns existing."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        merged, added, kept = merge_precommit_configs(existing, "ci:\n  skip: []\n")
        assert "pre-commit/hooks" in merged
        assert added == 0
        assert kept == 1

    def test_none_repos_in_existing(self) -> None:
        """Test existing config with repos: null."""
        existing = "repos:\n"
        generated = (
            "repos:\n"
            "- repo: https://github.com/psf/black\n"
            "  rev: '24.1.0'\n"
            "  hooks:\n"
            "  - id: black\n"
        )
        merged, added, _kept = merge_precommit_configs(existing, generated)
        assert "psf/black" in merged
        assert added == 1

    def test_both_empty_repos(self) -> None:
        """Test both configs have empty repos."""
        _merged, added, kept = merge_precommit_configs("repos:\n", "repos:\n")
        assert added == 0
        assert kept == 0


class TestTopLevelKeys:
    """Test preservation of top-level keys."""

    def test_existing_top_level_keys_preserved(self) -> None:
        """Test top-level keys from existing config are preserved."""
        existing = (
            "default_language_version:\n"
            "  python: python3.11\n"
            "ci:\n"
            "  skip:\n"
            "  - mypy\n"
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        generated = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        merged, _, _ = merge_precommit_configs(existing, generated)
        assert "python3.11" in merged
        assert "mypy" in merged

    def test_new_top_level_keys_from_generated(self) -> None:
        """Test new top-level keys from generated are added."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        generated = (
            "default_language_version:\n"
            "  python: python3.12\n"
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        merged, _, _ = merge_precommit_configs(existing, generated)
        assert "python3.12" in merged


class TestOutputFormat:
    """Test that output is valid YAML."""

    def test_output_is_valid_yaml(self) -> None:
        """Test merged output can be parsed back as YAML."""
        existing = (
            "repos:\n"
            "- repo: https://github.com/pre-commit/hooks\n"
            "  rev: v4.5.0\n"
            "  hooks:\n"
            "  - id: trailing-whitespace\n"
        )
        generated = (
            "repos:\n"
            "- repo: https://github.com/psf/black\n"
            "  rev: '24.1.0'\n"
            "  hooks:\n"
            "  - id: black\n"
        )
        merged, _, _ = merge_precommit_configs(existing, generated)
        parsed = yaml.safe_load(merged)
        assert "repos" in parsed
        assert len(parsed["repos"]) == 2
