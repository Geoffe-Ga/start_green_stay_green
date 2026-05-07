"""Unit tests for ``start_green_stay_green.utils.enhance_state``."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.utils.enhance_state import EnhanceState
from start_green_stay_green.utils.enhance_state import STATE_FILE_VERSION
from start_green_stay_green.utils.enhance_state import TargetCompletion
from start_green_stay_green.utils.enhance_state import hash_inputs
from start_green_stay_green.utils.enhance_state import load_state
from start_green_stay_green.utils.enhance_state import save_state
from start_green_stay_green.utils.enhance_state import state_path_for

if TYPE_CHECKING:
    from pathlib import Path


class TestHashInputs:
    """Hashing must be deterministic and order-sensitive."""

    def test_same_inputs_same_hash(self) -> None:
        """Identical input sequences produce identical hashes."""
        a = hash_inputs(["foo", "bar"])
        b = hash_inputs(["foo", "bar"])
        assert a == b

    def test_order_matters(self) -> None:
        """Different orderings of the same inputs must produce different hashes."""
        a = hash_inputs(["foo", "bar"])
        b = hash_inputs(["bar", "foo"])
        assert a != b

    def test_str_and_bytes_are_equivalent_when_utf8(self) -> None:
        """``str`` and its UTF-8 bytes hash the same — encoding is well-defined."""
        text_hash = hash_inputs(["hello"])
        bytes_hash = hash_inputs([b"hello"])
        assert text_hash == bytes_hash

    def test_returns_sha256_prefix(self) -> None:
        """The returned digest is prefixed with ``sha256:`` for readability."""
        h = hash_inputs(["x"])
        assert h.startswith("sha256:")
        # 64 hex chars after prefix.
        assert len(h) == len("sha256:") + 64

    def test_empty_inputs_still_hashes(self) -> None:
        """Empty iterable returns the digest of the empty string."""
        h = hash_inputs([])
        # The SHA-256 of empty input — locked in so a regression that
        # accidentally seeds the digest is loud.
        assert h == (
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )


class TestEnhanceState:
    """``EnhanceState`` round-trip + skip-decision logic."""

    def test_default_state_is_empty(self) -> None:
        """A default-constructed state has version + empty completed map."""
        state = EnhanceState()
        assert state.version == STATE_FILE_VERSION
        assert state.last_run == ""
        assert state.completed == {}

    def test_is_unchanged_returns_false_for_unknown_target(self) -> None:
        """A target that has never been tuned can never be "unchanged"."""
        state = EnhanceState()
        assert not state.is_unchanged("claude-md", "sha256:anything")

    def test_is_unchanged_matches_stored_hash(self) -> None:
        """Same hash → unchanged; different hash → changed."""
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")
        assert state.is_unchanged("claude-md", "sha256:abc")
        assert not state.is_unchanged("claude-md", "sha256:def")

    def test_mark_completed_sets_timestamp_and_last_run(self) -> None:
        """Recording a completion updates both the per-target and global timestamps."""
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        record = state.completed["claude-md"]
        assert record.hash == "sha256:abc"
        assert record.model == "claude-sonnet"
        assert record.timestamp  # any ISO-8601 string
        assert state.last_run == record.timestamp

    def test_round_trip(self) -> None:
        """``to_dict`` + ``from_dict`` reproduces the original state."""
        original = EnhanceState()
        original.mark_completed("claude-md", "sha256:abc", "claude-sonnet")
        original.mark_completed("subagents", "sha256:def", "claude-opus")

        round_tripped = EnhanceState.from_dict(original.to_dict())

        assert round_tripped.version == original.version
        assert round_tripped.last_run == original.last_run
        assert round_tripped.completed == original.completed

    def test_from_dict_tolerates_unknown_targets(self) -> None:
        """A future target appearing in stored state is loaded, not rejected."""
        loaded = EnhanceState.from_dict(
            {
                "version": 1,
                "last_run": "2026-05-06T07:00:00+00:00",
                "completed": {
                    "future-target": {
                        "hash": "sha256:abc",
                        "model": "claude-x",
                        "timestamp": "2026-05-06T07:00:00+00:00",
                    },
                },
            }
        )
        assert "future-target" in loaded.completed

    def test_from_dict_drops_malformed_records(self) -> None:
        """A record without a ``hash`` is silently dropped (not raised)."""
        loaded = EnhanceState.from_dict(
            {
                "completed": {
                    "good": {"hash": "sha256:abc", "model": "x", "timestamp": "y"},
                    "no-hash": {"model": "x"},
                    "non-dict": "garbage",
                },
            }
        )
        assert set(loaded.completed) == {"good"}

    def test_from_dict_handles_missing_completed(self) -> None:
        """``completed`` absent from payload → empty dict, no crash."""
        loaded = EnhanceState.from_dict({"version": 1})
        assert loaded.completed == {}


class TestStateRoundTripOnDisk:
    """End-to-end ``save_state`` → ``load_state`` cycle."""

    def test_save_then_load_round_trip(self, tmp_path: Path) -> None:
        original = EnhanceState()
        original.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        save_state(tmp_path, original)
        loaded = load_state(tmp_path)

        assert loaded.completed["claude-md"].hash == "sha256:abc"

    def test_load_state_returns_empty_when_file_missing(self, tmp_path: Path) -> None:
        """No state file → empty state (so first runs aren't flagged as changes)."""
        loaded = load_state(tmp_path)
        assert loaded.completed == {}

    def test_load_state_returns_empty_on_invalid_json(self, tmp_path: Path) -> None:
        """Garbage in the state file degrades to empty state, not a crash."""
        path = state_path_for(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json {", encoding="utf-8")

        loaded = load_state(tmp_path)
        assert loaded.completed == {}

    def test_load_state_returns_empty_when_payload_is_not_dict(
        self, tmp_path: Path
    ) -> None:
        """A JSON list at the top level → empty state, not a TypeError."""
        path = state_path_for(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[1, 2, 3]", encoding="utf-8")

        loaded = load_state(tmp_path)
        assert loaded.completed == {}

    def test_save_state_creates_parent_directory(self, tmp_path: Path) -> None:
        """``.claude/`` is created on first save (no init step required)."""
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        save_state(tmp_path, state)

        assert state_path_for(tmp_path).is_file()
        assert (tmp_path / ".claude").is_dir()

    def test_save_state_writes_utf8_with_sorted_keys(self, tmp_path: Path) -> None:
        """The on-disk file is UTF-8 with sorted keys (clean diffs across runs)."""
        state = EnhanceState()
        state.mark_completed("subagents", "sha256:b", "claude-x")
        state.mark_completed("claude-md", "sha256:a", "claude-y")

        save_state(tmp_path, state)
        raw = state_path_for(tmp_path).read_text(encoding="utf-8")
        payload = json.loads(raw)
        # ``sort_keys=True`` ensures completed keys are alphabetical.
        completed_keys = list(payload["completed"].keys())
        assert completed_keys == sorted(completed_keys)


def test_target_completion_is_immutable() -> None:
    """``TargetCompletion`` is a frozen dataclass — locks the contract."""
    rec = TargetCompletion(hash="sha256:abc", model="x", timestamp="y")
    with pytest.raises(AttributeError):
        rec.hash = "sha256:def"  # type: ignore[misc]
