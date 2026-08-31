"""Hash-chained JSONL storage for the fund-level trial count.

Assumptions
-----------
The ledger and its adjacent head checkpoint live on storage controlled by the
operator.  Hash chaining detects accidental mutation, line deletion, and tail
truncation, but it is not a substitute for signed remote/WORM storage against a
malicious operator who can replace both files.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, BinaryIO, Iterator

import fcntl


_GENESIS_HASH = "0" * 64
_OUTCOMES = frozenset({"evaluated", "abandoned", "error"})
_REGISTRATION_FIELDS = frozenset(
    {"sleeve_id", "prereg_hash", "config", "data_manifest_hash", "seed"}
)


class RegistryIntegrityError(RuntimeError):
    """Raised when the ledger does not match its hash chain or checkpoint."""


class AppendOnlyViolation(RuntimeError):
    """Raised when a caller requests mutation or deletion of a trial."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("registry values must be finite, JSON-serializable data") from exc
    return encoded.encode("utf-8")


def _timestamp(clock: Callable[[], datetime | str]) -> str:
    value = clock()
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise TypeError("registry clock must return a datetime or ISO-8601 string")
    if parsed.tzinfo is None:
        raise ValueError("registry timestamps must be timezone-aware")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class TrialRegistry:
    """An append-only event ledger with one materialized trial per registration.

    ``clock`` is injectable so research reruns and tests can produce
    byte-identical ledgers.  The default wall clock is appropriate for the live
    audit trail; it must not be used as an input to a calculation.
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        clock: Callable[[], datetime | str] = _utc_now,
    ) -> None:
        self.path = Path(path)
        self.head_path = self.path.with_name(f"{self.path.name}.head")
        self._clock = clock

    @contextmanager
    def _locked_file(self) -> Iterator[BinaryIO]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield handle
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def register(self, registration: Mapping[str, Any]) -> str:
        """Append a configuration before evaluation and return its trial id."""

        missing = _REGISTRATION_FIELDS.difference(registration)
        extra = set(registration).difference(_REGISTRATION_FIELDS)
        if missing or extra:
            raise ValueError(
                f"registration fields mismatch; missing={sorted(missing)}, "
                f"extra={sorted(extra)}"
            )
        if not isinstance(registration["sleeve_id"], str) or not registration["sleeve_id"]:
            raise ValueError("sleeve_id must be a non-empty string")
        if not isinstance(registration["prereg_hash"], str) or not registration["prereg_hash"]:
            raise ValueError("prereg_hash must be a non-empty string")
        if not isinstance(registration["data_manifest_hash"], str) or not registration["data_manifest_hash"]:
            raise ValueError("data_manifest_hash must be a non-empty string")
        if not isinstance(registration["config"], Mapping):
            raise ValueError("config must be a mapping")
        if isinstance(registration["seed"], bool) or not isinstance(registration["seed"], int):
            raise ValueError("seed must be an integer")

        with self._locked_file() as handle:
            events = self._read_and_verify(handle)
            sequence = 1 + sum(event["event"] == "registered" for event in events)
            registered_at = _timestamp(self._clock)
            identity = {
                "sequence": sequence,
                "timestamp": registered_at,
                **dict(registration),
            }
            trial_id = sha256(_canonical_json(identity)).hexdigest()
            event = {
                "schema_version": 1,
                "event": "registered",
                "timestamp": registered_at,
                "trial_id": trial_id,
                "sleeve_id": registration["sleeve_id"],
                "prereg_hash": registration["prereg_hash"],
                "config": dict(registration["config"]),
                "data_manifest_hash": registration["data_manifest_hash"],
                "seed": registration["seed"],
                "result": None,
                "outcome": None,
            }
            self._append(handle, event, self._last_hash(events))
        return trial_id

    def record(
        self,
        trial_id: str,
        result: Mapping[str, Any],
        *,
        outcome: str = "evaluated",
    ) -> None:
        """Append a terminal result for a previously registered trial."""

        if outcome not in _OUTCOMES:
            raise ValueError(f"outcome must be one of {sorted(_OUTCOMES)}")
        if not isinstance(result, Mapping):
            raise ValueError("result must be a mapping")
        with self._locked_file() as handle:
            events = self._read_and_verify(handle)
            registrations = {
                event["trial_id"]: event
                for event in events
                if event["event"] == "registered"
            }
            if trial_id not in registrations:
                raise KeyError(f"unknown trial_id: {trial_id}")
            if any(
                event["event"] == "recorded" and event["trial_id"] == trial_id
                for event in events
            ):
                raise AppendOnlyViolation(f"trial already has an outcome: {trial_id}")
            original = registrations[trial_id]
            event = {
                "schema_version": 1,
                "event": "recorded",
                "timestamp": _timestamp(self._clock),
                "trial_id": trial_id,
                "sleeve_id": original["sleeve_id"],
                "prereg_hash": original["prereg_hash"],
                "config": original["config"],
                "data_manifest_hash": original["data_manifest_hash"],
                "seed": original["seed"],
                "result": dict(result),
                "outcome": outcome,
            }
            self._append(handle, event, self._last_hash(events))

    def count(self, sleeve: str | None = None) -> int:
        """Return the cumulative number of registered configurations."""

        return sum(
            entry["sleeve_id"] == sleeve if sleeve is not None else True
            for entry in self.entries()
        )

    def entries(self) -> list[dict[str, Any]]:
        """Return one logical entry per configuration, preserving registration order."""

        with self._locked_file() as handle:
            events = self._read_and_verify(handle)
        ordered: list[dict[str, Any]] = []
        positions: dict[str, int] = {}
        for event in events:
            if event["event"] == "registered":
                positions[event["trial_id"]] = len(ordered)
                ordered.append(
                    {
                        key: event[key]
                        for key in (
                            "timestamp",
                            "trial_id",
                            "sleeve_id",
                            "prereg_hash",
                            "config",
                            "data_manifest_hash",
                            "seed",
                            "result",
                            "outcome",
                        )
                    }
                )
            else:
                position = positions.get(event["trial_id"])
                if position is None:
                    raise RegistryIntegrityError("result event precedes registration")
                ordered[position]["result"] = event["result"]
                ordered[position]["outcome"] = event["outcome"]
                ordered[position]["recorded_at"] = event["timestamp"]
        return ordered

    def verify_integrity(self) -> None:
        """Raise if a line was changed/deleted or the ledger tail was truncated."""

        with self._locked_file() as handle:
            self._read_and_verify(handle)

    def update(self, trial_id: str, values: Mapping[str, Any]) -> None:
        """Reject mutation explicitly; corrections are new trials or appended events."""

        del trial_id, values
        raise AppendOnlyViolation("registry entries cannot be updated")

    def delete(self, trial_id: str) -> None:
        """Reject deletion explicitly; the cumulative trial count never shrinks."""

        del trial_id
        raise AppendOnlyViolation("registry entries cannot be deleted")

    @staticmethod
    def _last_hash(events: list[dict[str, Any]]) -> str:
        return events[-1]["event_hash"] if events else _GENESIS_HASH

    def _append(
        self,
        handle: BinaryIO,
        event: dict[str, Any],
        previous_hash: str,
    ) -> None:
        event["previous_event_hash"] = previous_hash
        event["event_hash"] = sha256(_canonical_json(event)).hexdigest()
        payload = _canonical_json(event) + b"\n"
        handle.seek(0, os.SEEK_END)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        self._write_head(event["event_hash"])

    def _read_and_verify(self, handle: BinaryIO) -> list[dict[str, Any]]:
        handle.seek(0)
        rows = handle.read().splitlines()
        events: list[dict[str, Any]] = []
        previous_hash = _GENESIS_HASH
        for line_number, row in enumerate(rows, start=1):
            try:
                event = json.loads(row)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise RegistryIntegrityError(
                    f"invalid registry JSON on line {line_number}"
                ) from exc
            claimed_hash = event.pop("event_hash", None)
            if event.get("previous_event_hash") != previous_hash:
                raise RegistryIntegrityError(
                    f"broken registry chain on line {line_number}"
                )
            calculated_hash = sha256(_canonical_json(event)).hexdigest()
            if claimed_hash != calculated_hash:
                raise RegistryIntegrityError(
                    f"registry content changed on line {line_number}"
                )
            event["event_hash"] = claimed_hash
            self._validate_event(event, line_number)
            events.append(event)
            previous_hash = claimed_hash

        if self.head_path.exists():
            checkpoint = self.head_path.read_text(encoding="ascii").strip()
            if checkpoint != previous_hash:
                raise RegistryIntegrityError("registry tail does not match head checkpoint")
        elif events:
            raise RegistryIntegrityError("registry head checkpoint is missing")
        return events

    @staticmethod
    def _validate_event(event: Mapping[str, Any], line_number: int) -> None:
        kind = event.get("event")
        outcome = event.get("outcome")
        result = event.get("result")
        if kind not in {"registered", "recorded"}:
            raise RegistryIntegrityError(f"invalid event type on line {line_number}")
        if kind == "registered" and (outcome is not None or result is not None):
            raise RegistryIntegrityError(
                f"registration must be pending on line {line_number}"
            )
        if kind == "recorded" and (outcome not in _OUTCOMES or not isinstance(result, dict)):
            raise RegistryIntegrityError(f"invalid outcome on line {line_number}")

    def _write_head(self, event_hash: str) -> None:
        temporary = self.head_path.with_name(f".{self.head_path.name}.{os.getpid()}.tmp")
        temporary.write_text(f"{event_hash}\n", encoding="ascii")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, self.head_path)


def render_markdown(registry: TrialRegistry) -> str:
    """Generate a deterministic audit report directly from the registry."""

    entries = registry.entries()
    lines = ["# Trial Registry Report", "", f"Cumulative trials: {len(entries)}", ""]
    for entry in entries:
        lines.extend(
            [
                f"## Trial {entry['trial_id']}",
                "",
                f"- Sleeve: `{entry['sleeve_id']}`",
                f"- Pre-registration: `{entry['prereg_hash']}`",
                f"- Data manifest: `{entry['data_manifest_hash']}`",
                f"- Seed: `{entry['seed']}`",
                f"- Outcome: `{entry['outcome'] or 'pending'}`",
                f"- Config: `{json.dumps(entry['config'], sort_keys=True, separators=(',', ':'))}`",
                f"- Result: `{json.dumps(entry['result'], sort_keys=True, separators=(',', ':'))}`",
                "",
            ]
        )
    return "\n".join(lines)
