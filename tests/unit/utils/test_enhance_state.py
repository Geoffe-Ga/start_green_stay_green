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


class TestStateFileVersionConstant:
    """Pin the on-the-wire schema version literal."""

    def test_version_constant_is_one(self) -> None:
        """The current schema version is exactly 1 (bumping is breaking)."""
        assert STATE_FILE_VERSION == 1


class TestBatchProgressDefaults:
    """Pin the exact default field values of ``BatchProgress``."""

    def test_default_batch_id_is_empty_string(self) -> None:
        """A default ``BatchProgress`` has an empty-string ``batch_id``."""
        assert BatchProgress().batch_id == ""

    def test_default_submitted_at_is_empty_string(self) -> None:
        """A default ``BatchProgress`` has an empty-string ``submitted_at``."""
        assert BatchProgress().submitted_at == ""

    def test_default_custom_id_map_is_empty_dict(self) -> None:
        """A default ``BatchProgress`` has an empty (not ``None``) map."""
        progress = BatchProgress()
        # isinstance kills a None default; emptiness pins the rest.
        assert isinstance(progress.custom_id_map, dict)
        assert not progress.custom_id_map

    def test_batch_progress_is_frozen(self) -> None:
        """``BatchProgress`` is immutable — assignment raises ``AttributeError``."""
        progress = BatchProgress(batch_id="msgbatch_42")
        with pytest.raises(AttributeError):
            progress.batch_id = "other"  # type: ignore[misc]


class TestParsedSubmittedAtGuard:
    """Pin the ``or`` short-circuit in ``_parsed_submitted_at``."""

    def test_empty_batch_id_with_valid_timestamp_is_never_expired(self) -> None:
        """Missing ``batch_id`` defeats expiry even with a stale timestamp.

        The guard is ``not batch_id or not submitted_at`` — if it were
        ``and`` an empty ``batch_id`` paired with a 25 h-old
        ``submitted_at`` would parse and flag expired. The ``or`` form
        must short-circuit to "no batch" (never expired) instead.
        """
        now = datetime(2026, 5, 10, 1, 0, tzinfo=UTC)
        progress = BatchProgress(
            batch_id="",  # no batch in flight
            submitted_at="2026-05-09T00:00:00+00:00",  # 25 h before ``now``
        )
        assert not progress.is_potentially_expired(now=now)


class TestStartBatchErrorMessage:
    """Pin the exact wording of the in-flight-batch guard message."""

    def test_overwrite_error_message_is_exact(self) -> None:
        """The double-start error message matches verbatim end to end."""
        state = EnhanceState()
        state.start_batch(
            "msgbatch_first",
            {"subagent:foo": "subagents"},
            "2026-05-09T00:00:00Z",
        )
        with pytest.raises(BatchStateError) as exc:
            state.start_batch(
                "msgbatch_second",
                {"subagent:bar": "subagents"},
                "2026-05-09T01:00:00Z",
            )
        assert str(exc.value) == (
            "An in-flight batch is already recorded; clear it via "
            "clear_batch() before starting another."
        )


class TestToDictExactStructure:
    """Pin the exact serialized key set and values of ``to_dict``."""

    def test_to_dict_top_level_keys_are_exact(self) -> None:
        """A batchless state serializes to exactly version/last_run/completed."""
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")
        payload = state.to_dict()
        assert set(payload) == {"version", "last_run", "completed"}
        assert payload["version"] == 1

    def test_completed_record_keys_are_exact(self) -> None:
        """Each completed record serializes to exactly hash/model/timestamp."""
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")
        record = state.to_dict()["completed"]["claude-md"]
        assert set(record) == {"hash", "model", "timestamp"}


class TestFromDictVersionHandling:
    """Pin the ``version`` key read and its ``or`` fallback."""

    def test_explicit_version_is_read_from_payload(self) -> None:
        """A present truthy ``version`` flows through verbatim, not the default.

        Kills the ``"version"`` → ``"XXversionXX"`` key mutant (which
        would fall back to the default) and the ``or`` → ``and`` mutant
        (which would collapse any present version to the default).
        """
        loaded = EnhanceState.from_dict({"version": 7})
        assert loaded.version == 7

    def test_missing_version_falls_back_to_default(self) -> None:
        """An absent ``version`` defaults to the schema constant."""
        loaded = EnhanceState.from_dict({})
        assert loaded.version == STATE_FILE_VERSION


class TestFromDictLastRunHandling:
    """Pin the ``last_run`` default and ``or`` fallback."""

    def test_missing_last_run_is_empty_string(self) -> None:
        """An absent ``last_run`` defaults to the empty string, not a literal."""
        loaded = EnhanceState.from_dict({})
        assert loaded.last_run == ""

    def test_blank_last_run_stays_empty_string(self) -> None:
        """A present blank ``last_run`` stays empty (``or ""`` fallback)."""
        loaded = EnhanceState.from_dict({"last_run": ""})
        assert loaded.last_run == ""

    def test_present_last_run_is_preserved(self) -> None:
        """A present non-empty ``last_run`` flows through verbatim."""
        loaded = EnhanceState.from_dict({"last_run": "2026-05-06T07:00:00+00:00"})
        assert loaded.last_run == "2026-05-06T07:00:00+00:00"


class TestValidHashPredicate:
    """Pin the ``isinstance and truthy`` predicate guarding hash records."""

    def test_non_string_hash_drops_record(self) -> None:
        """A non-string ``hash`` (truthy) drops the record, not keeps it.

        Pins ``isinstance(raw, str) and raw`` against the ``or`` mutant:
        a truthy non-string would pass an ``or`` form and produce a
        record with a non-string hash.
        """
        loaded = EnhanceState.from_dict(
            {"completed": {"bad": {"hash": 123, "model": "x", "timestamp": "y"}}}
        )
        assert not loaded.completed

    def test_empty_string_hash_drops_record(self) -> None:
        """An empty-string ``hash`` drops the record (falsy → invalid)."""
        loaded = EnhanceState.from_dict(
            {"completed": {"bad": {"hash": "", "model": "x", "timestamp": "y"}}}
        )
        assert not loaded.completed


class TestNonemptyStrPredicate:
    """Pin the ``isinstance and truthy`` predicate guarding ``batch_id``."""

    def test_non_string_batch_id_drops_batch(self) -> None:
        """A non-string ``batch_id`` (truthy) drops the batch, not keeps it."""
        loaded = EnhanceState.from_dict({"batch": {"batch_id": 123}})
        assert loaded.batch is None

    def test_empty_string_batch_id_drops_batch(self) -> None:
        """An empty-string ``batch_id`` drops the batch (falsy → invalid)."""
        loaded = EnhanceState.from_dict({"batch": {"batch_id": ""}})
        assert loaded.batch is None


class TestParseRecordModelAndTimestampDefaults:
    """Pin the model/timestamp default-and-fallback handling in records."""

    def test_missing_model_defaults_to_empty_string(self) -> None:
        """A record without ``model`` parses ``model`` to ``""`` (not a literal)."""
        loaded = EnhanceState.from_dict(
            {"completed": {"t": {"hash": "sha256:abc", "timestamp": "ts"}}}
        )
        assert loaded.completed["t"].model == ""

    def test_blank_model_stays_empty_string(self) -> None:
        """A present blank ``model`` stays empty (``or ""`` fallback)."""
        loaded = EnhanceState.from_dict(
            {"completed": {"t": {"hash": "sha256:abc", "model": "", "timestamp": "ts"}}}
        )
        assert loaded.completed["t"].model == ""

    def test_present_model_is_preserved(self) -> None:
        """A present non-empty ``model`` flows through verbatim."""
        loaded = EnhanceState.from_dict(
            {
                "completed": {
                    "t": {"hash": "sha256:abc", "model": "claude-x", "timestamp": "ts"}
                }
            }
        )
        assert loaded.completed["t"].model == "claude-x"

    def test_missing_timestamp_defaults_to_empty_string(self) -> None:
        """A record without ``timestamp`` parses it to ``""`` (not a literal)."""
        loaded = EnhanceState.from_dict(
            {"completed": {"t": {"hash": "sha256:abc", "model": "m"}}}
        )
        assert loaded.completed["t"].timestamp == ""

    def test_blank_timestamp_stays_empty_string(self) -> None:
        """A present blank ``timestamp`` stays empty (``or ""`` fallback)."""
        loaded = EnhanceState.from_dict(
            {"completed": {"t": {"hash": "sha256:abc", "model": "m", "timestamp": ""}}}
        )
        assert loaded.completed["t"].timestamp == ""

    def test_present_timestamp_is_preserved(self) -> None:
        """A present non-empty ``timestamp`` flows through verbatim."""
        loaded = EnhanceState.from_dict(
            {
                "completed": {
                    "t": {"hash": "sha256:abc", "model": "m", "timestamp": "2026-01-01"}
                }
            }
        )
        assert loaded.completed["t"].timestamp == "2026-01-01"


class TestParseBatchSubmittedAtHandling:
    """Pin the ``submitted_at`` key read and ``or ""`` fallback in batches."""

    def test_present_submitted_at_is_preserved(self) -> None:
        """A present ``submitted_at`` is read from the right key, verbatim.

        Kills the ``"submitted_at"`` → ``"XXsubmitted_atXX"`` key mutant
        (wrong key → ``""``) and the ``or`` → ``and`` mutant (a present
        value ``and ""`` collapses to ``""``).
        """
        loaded = EnhanceState.from_dict(
            {
                "batch": {
                    "batch_id": "msgbatch_42",
                    "submitted_at": "2026-05-09T00:00:00",
                }
            }
        )
        assert loaded.batch is not None
        assert loaded.batch.submitted_at == "2026-05-09T00:00:00"

    def test_missing_submitted_at_defaults_to_empty_string(self) -> None:
        """An absent ``submitted_at`` defaults to ``""`` (not a literal)."""
        loaded = EnhanceState.from_dict({"batch": {"batch_id": "msgbatch_42"}})
        assert loaded.batch is not None
        assert loaded.batch.submitted_at == ""

    def test_blank_submitted_at_stays_empty_string(self) -> None:
        """A present blank ``submitted_at`` stays empty (``or ""`` fallback)."""
        loaded = EnhanceState.from_dict(
            {"batch": {"batch_id": "msgbatch_42", "submitted_at": ""}}
        )
        assert loaded.batch is not None
        assert loaded.batch.submitted_at == ""


class TestSaveStateDirectoryAndFormatting:
    """Pin ``save_state``'s directory creation and JSON formatting."""

    def test_save_state_creates_nested_missing_parents(self, tmp_path: Path) -> None:
        """Saving into a deep, not-yet-existing project path creates all parents.

        Pins ``mkdir(parents=True)``: with ``parents=False`` the missing
        ``project/.claude`` grandparents would raise ``FileNotFoundError``.
        """
        project = tmp_path / "deep" / "nested" / "project"
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        save_state(project, state)

        assert state_path_for(project).is_file()

    def test_save_state_is_idempotent_when_dir_exists(self, tmp_path: Path) -> None:
        """A second save into an existing ``.claude`` succeeds (``exist_ok=True``).

        Pins ``exist_ok=True``: with ``exist_ok=False`` the second
        ``mkdir`` would raise ``FileExistsError``.
        """
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        save_state(tmp_path, state)
        save_state(tmp_path, state)  # must not raise

        assert state_path_for(tmp_path).is_file()

    def test_save_state_uses_indent_two(self, tmp_path: Path) -> None:
        """The on-disk JSON is indented with exactly two spaces.

        Pins ``indent=2`` against the ``indent=3`` mutant by comparing
        the file byte-for-byte to the canonical two-space dump.
        """
        state = EnhanceState()
        state.mark_completed("claude-md", "sha256:abc", "claude-sonnet")

        save_state(tmp_path, state)

        raw = state_path_for(tmp_path).read_text(encoding="utf-8")
        expected = json.dumps(state.to_dict(), indent=2, sort_keys=True)
        assert raw == expected
        # A nested completed key sits at exactly four spaces (indent=2, depth 2).
        assert '    "claude-md"' in raw
        assert '     "claude-md"' not in raw
