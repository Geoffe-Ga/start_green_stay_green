"""State tracking for the ``green enhance`` resume / skip-unchanged path.

Phase 3c of the optimization roadmap: persists per-target source
hashes after a successful tune so a follow-up ``green enhance`` on a
project whose inputs have not changed becomes a fast no-op. Eliminates
the cost of re-tuning artifacts that would land identical content.

The state lives at ``<project>/.claude/.enhance-state.json``. The
schema is intentionally minimal — every field is necessary for either
skip-decision making or for diagnosing why a stored hash mismatched.

Schema (JSON):

    {
      "version": 1,
      "last_run": "2026-05-06T07:00:00+00:00",
      "completed": {
        "claude-md": {
          "hash": "sha256:abc…",
          "model": "claude-sonnet-…",
          "timestamp": "2026-05-06T07:00:00+00:00"
        },
        "subagents": { ... }
      }
    }

Forward-compat: callers must tolerate unknown ``completed`` keys (a
future Phase 4 might add ``skills``) and unknown top-level keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from datetime import timedelta
import hashlib
import json
from typing import Any
from typing import TYPE_CHECKING

from start_green_stay_green.ai.types import GenerationError

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

# Stored on every state file. Bump only when an existing reader would
# misinterpret the new schema; additive fields are not breaking.
STATE_FILE_VERSION = 1

# Path within a green-init project where the state file lives. Keeping
# it under ``.claude/`` matches the existing convention for tool
# scratch state and keeps a future ``.gitignore`` rule narrow.
STATE_FILE_RELATIVE = ".claude/.enhance-state.json"


class BatchStateError(GenerationError):
    """Raised on a state-machine violation in :class:`EnhanceState`.

    Subclasses :class:`GenerationError` so callers handling AI-domain
    failures with a single ``except GenerationError`` clause catch
    state-file misuse without separate plumbing. Currently raised
    by :meth:`EnhanceState.start_batch` when a caller tries to
    overwrite an in-flight batch without first calling
    :meth:`EnhanceState.clear_batch`.
    """


@dataclass(frozen=True)
class BatchProgress:
    """In-flight batch metadata persisted across ``green enhance`` calls.

    Phase 5a — present iff a batch was submitted but not yet
    fetched. The CLI's resume path checks for this on every
    invocation so an interrupted run can be picked up without
    re-submitting (which would burn cost on duplicate work).

    **Lifecycle**: a ``green enhance --batch`` run flows
    submit → :meth:`EnhanceState.start_batch` (persist record) →
    poll → reconcile → :meth:`EnhanceState.clear_batch` (drop
    record). Phase 5b's CLI must call :meth:`is_potentially_expired`
    before the poll step so a state file that crossed Anthropic's
    24 h SLA boundary can be cleared and re-submitted instead of
    hitting an opaque ``404`` on the stale ``batch_id``.

    Attributes:
        batch_id: Anthropic identifier returned by
            :meth:`AIOrchestrator.submit_tool_use_batch`. Empty in a
            default-constructed state — :meth:`EnhanceState.has_batch`
            treats that as "no batch in flight".
        submitted_at: ISO-8601 UTC timestamp of submission. Used as
            the basis for the 24 h SLA expiry check.
        custom_id_map: Map from each submitted ``custom_id`` to the
            top-level :class:`EnhanceState` ``completed`` target it
            belongs under (e.g. ``"subagent:architecture-review"
            → "subagents"``). The direction is **custom_id → target**
            because the Phase 5b reconciliation path iterates
            :attr:`BatchResultsBundle.successes` (already keyed by
            ``custom_id``) and looks each target up directly without
            inverting the map.
    """

    batch_id: str = ""
    submitted_at: str = ""
    custom_id_map: dict[str, str] = field(default_factory=dict)

    def is_potentially_expired(self, *, now: datetime | None = None) -> bool:
        """Return ``True`` when this batch may have crossed the 24 h SLA.

        Anthropic batches have a hard ≤24 h server-side TTL; after
        that the ``batch_id`` is no longer valid and any
        ``poll_batch`` / ``fetch_batch_results`` call returns a
        ``404``-class error. Phase 5b's CLI must call this before
        polling so a stale record can be cleared (and the user
        prompted to re-submit) instead of bubbling an opaque error.

        Best-effort — uses :attr:`submitted_at` plus the local
        clock, both of which can drift relative to the Anthropic
        server. Tuned to over-report (24 h, not 23) so a borderline
        batch is treated as live and the API gets the final say.

        Args:
            now: Override the current-time source (testing hook).
                Defaults to :func:`datetime.now(UTC)`.

        Returns:
            ``False`` if no batch is recorded, the timestamp is
            unparseable, or less than 24 h has elapsed; ``True``
            otherwise.
        """
        submitted = self._parsed_submitted_at()
        if submitted is None:
            return False
        current = now if now is not None else datetime.now(UTC)
        return (current - submitted) >= _BATCH_TTL

    def _parsed_submitted_at(self) -> datetime | None:
        """Return :attr:`submitted_at` as a tz-aware datetime, or ``None``."""
        if not self.batch_id or not self.submitted_at:
            return None
        try:
            parsed = datetime.fromisoformat(self.submitted_at)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed


# Anthropic Message Batches API server-side TTL. Documented at
# https://docs.claude.com/en/api/creating-message-batches —
# batches that have not completed within 24 h are expired.
_BATCH_TTL: timedelta = timedelta(hours=24)


@dataclass(frozen=True)
class TargetCompletion:
    """Completion record for a single ``green enhance`` target.

    Attributes:
        hash: Hex-encoded ``sha256:`` of the source inputs that drove
            the tune (reference template content + project metadata).
            A subsequent ``enhance`` run hashes the same inputs and
            compares — equal hash → skip, different → re-tune.
        model: Identifier of the Claude model that produced the
            tune. Stored for diagnostics; not used in skip decisions.
        timestamp: ISO-8601 UTC timestamp of when this target was
            last successfully tuned.
    """

    hash: str
    model: str
    timestamp: str


@dataclass
class EnhanceState:
    """Persistent state for ``green enhance``.

    Mutable by design — the CLI layer drives the lifecycle through
    :meth:`mark_completed`, :meth:`start_batch`, and :meth:`clear_batch`,
    which would all need replace-and-reassign workarounds under
    ``frozen=True``. The on-disk file is the durable contract;
    in-memory mutation is bounded to the duration of one
    ``green enhance`` invocation.

    Attributes:
        version: Schema version. Always equal to
            :data:`STATE_FILE_VERSION` on round-trip.
        last_run: ISO-8601 UTC timestamp of the most recent
            ``enhance`` invocation that wrote this file.
        completed: Map from target name (e.g. ``"claude-md"``,
            ``"subagents"``) to its :class:`TargetCompletion` record.
        batch: In-flight :class:`BatchProgress` recorded after a
            ``--batch`` submission and cleared once results are
            reconciled. ``None`` when no batch is in flight.
    """

    version: int = STATE_FILE_VERSION
    last_run: str = ""
    completed: dict[str, TargetCompletion] = field(default_factory=dict)
    batch: BatchProgress | None = None

    def has_batch(self) -> bool:
        """``True`` if a submitted-but-not-yet-fetched batch is recorded."""
        return self.batch is not None and bool(self.batch.batch_id)

    def start_batch(
        self,
        batch_id: str,
        custom_id_map: dict[str, str],
        submitted_at: str,
    ) -> None:
        """Record a freshly-submitted batch.

        Refuses to overwrite an existing in-flight batch — the caller
        must :meth:`clear_batch` first, signalling that the prior run
        was reconciled. Without this guard a re-run of
        ``green enhance --batch`` would silently abandon the previous
        batch's results and the user would pay twice.

        Raises:
            BatchStateError: When an in-flight batch is already
                recorded. Subclasses :class:`GenerationError` so
                callers can ``except GenerationError`` to catch all
                AI-domain failures uniformly.
        """
        if self.has_batch():
            msg = (
                "An in-flight batch is already recorded; clear it via "
                "clear_batch() before starting another."
            )
            raise BatchStateError(msg)
        self.batch = BatchProgress(
            batch_id=batch_id,
            submitted_at=submitted_at,
            custom_id_map=custom_id_map.copy(),
        )
        self.last_run = submitted_at

    def clear_batch(self) -> None:
        """Drop the in-flight batch record after results are reconciled."""
        self.batch = None

    def is_unchanged(self, target: str, current_hash: str) -> bool:
        """Return ``True`` if ``target`` was last tuned at ``current_hash``.

        A missing target (never tuned) returns ``False`` — the caller
        should run the tune.

        Args:
            target: Target name (matches the keys of
                ``completed``).
            current_hash: Hash of the inputs that *would* drive a
                fresh tune, for comparison against the stored hash.

        Returns:
            ``True`` only if a stored completion exists *and* its
            hash equals ``current_hash``.
        """
        record = self.completed.get(target)
        return record is not None and record.hash == current_hash

    def mark_completed(self, target: str, source_hash: str, model: str) -> None:
        """Record a successful tune of ``target``.

        Args:
            target: Target name.
            source_hash: Hash of the inputs that produced this run's
                output (what we'll compare against next time).
            model: Model identifier (e.g. ``ModelConfig.SONNET``).
        """
        timestamp = datetime.now(UTC).isoformat()
        self.completed[target] = TargetCompletion(
            hash=source_hash,
            model=model,
            timestamp=timestamp,
        )
        self.last_run = timestamp

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly mapping."""
        payload: dict[str, Any] = {
            "version": self.version,
            "last_run": self.last_run,
            "completed": {
                target: {
                    "hash": rec.hash,
                    "model": rec.model,
                    "timestamp": rec.timestamp,
                }
                for target, rec in self.completed.items()
            },
        }
        if self.batch is not None and self.batch.batch_id:
            payload["batch"] = {
                "batch_id": self.batch.batch_id,
                "submitted_at": self.batch.submitted_at,
                "custom_id_map": dict(self.batch.custom_id_map),
            }
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> EnhanceState:
        """Build a state instance from a previously-serialised mapping.

        Tolerant of unknown ``completed`` keys (forward-compat with
        future targets) and missing optional keys; skips records that
        are malformed rather than aborting the whole load — a stale
        record is no worse than a missing one (worst case the caller
        re-tunes the target).
        """
        return cls(
            version=int(
                payload.get("version", STATE_FILE_VERSION) or STATE_FILE_VERSION
            ),
            last_run=str(payload.get("last_run", "") or ""),
            completed=_parse_completed_records(payload.get("completed")),
            batch=_parse_batch_progress(payload.get("batch")),
        )


def _valid_hash(raw: object) -> str | None:
    """Return ``raw`` if it is a non-empty string, else ``None``."""
    if isinstance(raw, str) and raw:
        return raw
    return None


def _nonempty_str(raw: object) -> str | None:
    """Return ``raw`` when it's a non-empty string; else ``None``.

    Same predicate as :func:`_valid_hash` today, but separate by intent:
    ``_valid_hash`` validates a SHA-256 digest string and a future
    tightening (e.g. enforcing the ``sha256:`` prefix) would be
    correct. ``_nonempty_str`` validates an Anthropic-side opaque
    identifier (``batch_id``) and must NOT add format requirements
    — the only contract is "must be present and non-empty."
    """
    if isinstance(raw, str) and raw:
        return raw
    return None


def _parse_record(raw: object) -> TargetCompletion | None:
    """Validate and build a single ``TargetCompletion`` from a stored payload.

    Returns ``None`` for malformed input so the caller can drop the
    record instead of aborting the whole load.
    """
    if not isinstance(raw, dict):
        return None
    hash_value = _valid_hash(raw.get("hash"))
    if hash_value is None:
        return None
    return TargetCompletion(
        hash=hash_value,
        model=str(raw.get("model", "") or ""),
        timestamp=str(raw.get("timestamp", "") or ""),
    )


def _parse_completed_records(raw: object) -> dict[str, TargetCompletion]:
    """Parse the ``completed`` map, dropping any malformed entries."""
    if not isinstance(raw, dict):
        return {}
    completed: dict[str, TargetCompletion] = {}
    for name, payload in raw.items():
        record = _parse_record(payload)
        if record is not None:
            completed[str(name)] = record
    return completed


def _parse_batch_progress(raw: object) -> BatchProgress | None:
    """Parse an optional ``batch`` payload, returning ``None`` when absent.

    A malformed batch record degrades to "no batch in flight",
    matching the rest of the state-file philosophy: worst case, the
    caller re-submits — a duplicate batch is recoverable, an
    aborted run from a parse failure is not.
    """
    if not isinstance(raw, dict):
        return None
    batch_id = _nonempty_str(raw.get("batch_id"))
    if batch_id is None:
        return None
    return BatchProgress(
        batch_id=batch_id,
        submitted_at=str(raw.get("submitted_at", "") or ""),
        custom_id_map=_parse_custom_id_map(raw.get("custom_id_map")),
    )


def _parse_custom_id_map(raw: object) -> dict[str, str]:
    """Coerce a stored ``custom_id_map`` into the typed shape, dropping garbage."""
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


def state_path_for(project_path: Path) -> Path:
    """Return the canonical state-file path for a project."""
    return project_path / STATE_FILE_RELATIVE


def load_state(project_path: Path) -> EnhanceState:
    """Read the project's ``.enhance-state.json``, or return an empty state.

    A missing file, an unreadable file, or a JSON-shaped file that
    happens to be malformed all degrade to "empty state" rather than
    aborting the run. The worst-case outcome is a redundant re-tune,
    which is exactly the pre-Phase-3c behaviour and therefore safe.

    Args:
        project_path: Project root.

    Returns:
        Either the parsed state or a default-constructed empty one.
    """
    path = state_path_for(project_path)
    if not path.is_file():
        return EnhanceState()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return EnhanceState()
    if not isinstance(payload, dict):
        return EnhanceState()
    return EnhanceState.from_dict(payload)


def save_state(project_path: Path, state: EnhanceState) -> None:
    """Persist ``state`` to ``<project>/.claude/.enhance-state.json``.

    Creates the parent directory if absent. Writes UTF-8 with
    ``sort_keys=True`` so the file diffs cleanly across runs (useful
    if a user commits the state file even though we recommend
    ignoring it).

    Args:
        project_path: Project root.
        state: The state to write.
    """
    path = state_path_for(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def hash_inputs(parts: Iterable[bytes | str]) -> str:
    """Hash a sequence of inputs into a stable ``sha256:<hex>`` string.

    Each part is encoded to UTF-8 (if a ``str``) and fed in order
    into a single SHA-256 digest. Order matters — callers must pass
    the parts in a deterministic order so re-runs with identical
    inputs produce the same hash.

    Args:
        parts: Iterable of bytes or str chunks.

    Returns:
        The lowercase hex digest prefixed with ``"sha256:"``.
    """
    digest = hashlib.sha256()
    for part in parts:
        if isinstance(part, str):
            digest.update(part.encode("utf-8"))
        else:
            digest.update(part)
    return f"sha256:{digest.hexdigest()}"
