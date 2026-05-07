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
import hashlib
import json
from typing import Any
from typing import TYPE_CHECKING

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

    Attributes:
        version: Schema version. Always equal to
            :data:`STATE_FILE_VERSION` on round-trip.
        last_run: ISO-8601 UTC timestamp of the most recent
            ``enhance`` invocation that wrote this file.
        completed: Map from target name (e.g. ``"claude-md"``,
            ``"subagents"``) to its :class:`TargetCompletion` record.
    """

    version: int = STATE_FILE_VERSION
    last_run: str = ""
    completed: dict[str, TargetCompletion] = field(default_factory=dict)

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
        return {
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
        )


def _valid_hash(raw: object) -> str | None:
    """Return ``raw`` if it is a non-empty string, else ``None``."""
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
