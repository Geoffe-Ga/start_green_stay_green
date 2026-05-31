"""Unit tests for ``start_green_stay_green.utils.enhance_state``."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
import json
from typing import TYPE_CHECKING

import pytest

from start_green_stay_green.ai.types import GenerationError
from start_green_stay_green.utils.enhance_state import BatchProgress
from start_green_stay_green.utils.enhance_state import BatchStateError
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
        assert not state.completed

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
        assert not loaded.completed


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
        assert not loaded.completed

    def test_load_state_returns_empty_on_invalid_json(self, tmp_path: Path) -> None:
        """Garbage in the state file degrades to empty state, not a crash."""
        path = state_path_for(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("not valid json {", encoding="utf-8")

        loaded = load_state(tmp_path)
        assert not loaded.completed

    def test_load_state_returns_empty_when_payload_is_not_dict(
        self, tmp_path: Path
    ) -> None:
        """A JSON list at the top level → empty state, not a TypeError."""
        path = state_path_for(tmp_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[1, 2, 3]", encoding="utf-8")

        loaded = load_state(tmp_path)
        assert not loaded.completed

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


class TestBatchProgressExtension:
    """Phase 5a: optional in-flight batch field on ``EnhanceState``."""

    def test_default_state_has_no_batch(self) -> None:
        state = EnhanceState()
        assert state.batch is None
        assert not state.has_batch()

    def test_start_batch_records_id_and_map(self) -> None:
        state = EnhanceState()
        state.start_batch(
            "msgbatch_42",
            {
                "subagent:architecture-review": "subagents",
                "skill:stay-green": "skills",
            },
            "2026-05-09T12:00:00+00:00",
        )

        assert state.has_batch()
        assert isinstance(state.batch, BatchProgress)
        assert state.batch.batch_id == "msgbatch_42"
        # Direction: custom_id (key) → top-level target (value).
        assert state.batch.custom_id_map == {
            "subagent:architecture-review": "subagents",
            "skill:stay-green": "skills",
        }
        assert state.batch.submitted_at == "2026-05-09T12:00:00+00:00"
        # last_run is also bumped so a future read knows when this happened
        assert state.last_run == "2026-05-09T12:00:00+00:00"

    def test_start_batch_refuses_to_overwrite_in_flight(self) -> None:
        state = EnhanceState()
        state.start_batch(
            "msgbatch_first",
            {"subagent:foo": "subagents"},
            "2026-05-09T00:00:00Z",
        )

        with pytest.raises(BatchStateError, match="already recorded") as exc:
            state.start_batch(
                "msgbatch_second",
                {"subagent:bar": "subagents"},
                "2026-05-09T01:00:00Z",
            )
        # Subclasses GenerationError so callers catching the AI-domain
        # parent class handle state-file violations uniformly.
        assert isinstance(exc.value, GenerationError)

    def test_clear_batch_drops_record(self) -> None:
        state = EnhanceState()
        state.start_batch(
            "msgbatch_42",
            {"subagent:foo": "subagents"},
            "2026-05-09T00:00:00Z",
        )
        assert state.has_batch()

        state.clear_batch()
        assert state.batch is None
        assert not state.has_batch()
        # And start_batch is allowed again after a clear
        state.start_batch(
            "msgbatch_43",
            {"subagent:foo": "subagents"},
            "2026-05-09T01:00:00Z",
        )
        assert state.batch is not None
        assert state.batch.batch_id == "msgbatch_43"

    def test_to_dict_omits_batch_when_none(self) -> None:
        """A batchless state round-trips to the same JSON pre-Phase-5a wrote."""
        state = EnhanceState()
        payload = state.to_dict()
        assert "batch" not in payload

    def test_to_dict_includes_batch_when_present(self) -> None:
        state = EnhanceState()
        state.start_batch(
            "msgbatch_42",
            {"subagent:architecture-review": "subagents"},
            "2026-05-09T00:00:00+00:00",
        )

        payload = state.to_dict()
        assert payload["batch"] == {
            "batch_id": "msgbatch_42",
            "submitted_at": "2026-05-09T00:00:00+00:00",
            "custom_id_map": {"subagent:architecture-review": "subagents"},
        }

    def test_round_trip_preserves_batch(self) -> None:
        original = EnhanceState()
        original.start_batch(
            "msgbatch_42",
            {
                "subagent:architecture-review": "subagents",
                "skill:stay-green": "skills",
            },
            "2026-05-09T00:00:00+00:00",
        )

        restored = EnhanceState.from_dict(original.to_dict())
        assert restored.has_batch()
        assert restored.batch is not None
        assert restored.batch.batch_id == "msgbatch_42"
        assert restored.batch.custom_id_map == {
            "subagent:architecture-review": "subagents",
            "skill:stay-green": "skills",
        }

    def test_from_dict_drops_malformed_batch(self) -> None:
        """A malformed ``batch`` payload degrades to ``None`` (no in-flight record)."""
        # Missing batch_id → drop
        state = EnhanceState.from_dict({"batch": {"submitted_at": "x"}})
        assert state.batch is None
        # batch field is not a dict → drop
        state = EnhanceState.from_dict({"batch": "garbage"})
        assert state.batch is None
        # Missing batch field → still None (forward-compat with pre-5a writers)
        state = EnhanceState.from_dict({"completed": {}})
        assert state.batch is None

    def test_pre_phase_5a_state_file_loads_unchanged(self) -> None:
        """A state file produced by the Phase 3c writer must keep working."""
        legacy_payload = {
            "version": 1,
            "last_run": "2026-04-01T00:00:00+00:00",
            "completed": {
                "claude-md": {
                    "hash": "sha256:abc",
                    "model": "claude-sonnet",
                    "timestamp": "2026-04-01T00:00:00+00:00",
                },
            },
        }
        state = EnhanceState.from_dict(legacy_payload)
        assert "claude-md" in state.completed
        assert state.batch is None
        assert not state.has_batch()


class TestBatchProgressExpiry:
    """``is_potentially_expired`` guards against stale 24 h batches."""

    def test_returns_false_when_no_batch_recorded(self) -> None:
        """A default-constructed BatchProgress can never be expired."""
        progress = BatchProgress()
        assert not progress.is_potentially_expired()

    def test_returns_false_within_24h_of_submission(self) -> None:
        """A 23 h-old batch is still live — defer to the API."""

        submitted = datetime(2026, 5, 9, 0, 0, tzinfo=UTC)
        progress = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=submitted.isoformat(),
            custom_id_map={"subagent:foo": "subagents"},
        )
        # 23h59m later — still under the SLA.
        now = submitted + timedelta(hours=23, minutes=59)
        assert not progress.is_potentially_expired(now=now)

    def test_returns_true_at_24h_boundary(self) -> None:
        """Exactly 24h after submission counts as expired (over-report)."""

        submitted = datetime(2026, 5, 9, 0, 0, tzinfo=UTC)
        progress = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=submitted.isoformat(),
            custom_id_map={"subagent:foo": "subagents"},
        )
        now = submitted + timedelta(hours=24)
        assert progress.is_potentially_expired(now=now)

    def test_returns_true_well_past_24h(self) -> None:
        """A 48 h-old batch is unambiguously expired."""

        submitted = datetime(2026, 5, 9, 0, 0, tzinfo=UTC)
        progress = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at=submitted.isoformat(),
            custom_id_map={"subagent:foo": "subagents"},
        )
        assert progress.is_potentially_expired(
            now=submitted + timedelta(hours=48),
        )

    def test_returns_false_for_unparseable_timestamp(self) -> None:
        """A malformed ``submitted_at`` defers to the API rather than failing."""
        progress = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at="not an iso timestamp",
            custom_id_map={"subagent:foo": "subagents"},
        )
        assert not progress.is_potentially_expired()

    def test_handles_tz_naive_submitted_at(self) -> None:
        """A tz-naive ISO string is treated as UTC.

        Pins the ``replace(tzinfo=UTC)`` branch in
        :meth:`BatchProgress._parsed_submitted_at`. Without this
        coverage a refactor that drops the tz-naive promotion would
        produce a ``TypeError: can't subtract offset-naive and
        offset-aware datetimes`` at runtime — exactly the kind of
        regression mutation testing is meant to catch.
        """
        # Submitted 25h ago in tz-naive form; should still flag expired.
        now = datetime(2026, 5, 10, 1, 0, tzinfo=UTC)
        progress = BatchProgress(
            batch_id="msgbatch_42",
            submitted_at="2026-05-09T00:00:00",  # no offset suffix
            custom_id_map={"subagent:foo": "subagents"},
        )
        assert progress.is_potentially_expired(now=now)
