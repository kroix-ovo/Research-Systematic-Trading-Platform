"""Immutable companion ledger for frozen pre-registration amendments.

The frozen Markdown document is never edited.  Each approved change is instead
bound to that document's annotated Git tag and appended to a hash-chained JSONL
ledger.  The effective timestamp is supplied by the caller so a replay does not
depend on the process clock.

As with the trial registry, the adjacent head checkpoint makes accidental
mutation and tail truncation evident.  It is not a substitute for signed remote
or WORM storage against an operator who can replace both files.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
from typing import Any, BinaryIO, Iterator, Mapping

import fcntl

from .workflow import validate, verify_frozen


_GENESIS_HASH = "0" * 64


class AmendmentIntegrityError(RuntimeError):
    """Raised when an amendment ledger fails its hash-chain checks."""


class ImmutableAmendmentError(RuntimeError):
    """Raised when a caller attempts to update or delete an amendment."""


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
        raise ValueError("amendments must contain finite JSON-serializable data") from exc
    return encoded.encode("utf-8")


def _utc_timestamp(value: str | datetime) -> str:
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("effective_at must be an ISO-8601 UTC timestamp") from exc
    elif isinstance(value, datetime):
        parsed = value
    else:
        raise TypeError("effective_at must be a datetime or ISO-8601 string")
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("effective_at must be an ISO-8601 UTC timestamp")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _repo_relative(path: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=path.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"pre-registration must be inside a Git repository: {detail}")
    repo = Path(completed.stdout.strip()).resolve()
    try:
        return str(path.resolve().relative_to(repo))
    except ValueError as exc:
        raise ValueError("pre-registration must be inside its Git repository") from exc


class AmendmentLedger:
    """Append dated changes without modifying the frozen pre-registration."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self.head_path = self.path.with_name(f"{self.path.name}.head")

    @contextmanager
    def _locked_file(self) -> Iterator[BinaryIO]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield handle
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def append(
        self,
        preregistration: str | os.PathLike[str],
        *,
        sleeve_id: str,
        effective_at: str | datetime,
        changes: Mapping[str, Any],
        reason: str,
    ) -> str:
        """Append an amendment and return its content-and-chain hash.

        The referenced pre-registration must already pass the frozen Git-tag
        check.  ``changes`` should name the frozen fields affected and their
        replacement or addition; it is deliberately separate from ``reason``.
        """

        if not isinstance(sleeve_id, str) or not sleeve_id.strip():
            raise ValueError("sleeve_id must be a non-empty string")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("reason must be a non-empty string")
        if not isinstance(changes, Mapping) or not changes:
            raise ValueError("changes must be a non-empty mapping")

        prereg = Path(preregistration)
        registration = validate(prereg)
        prereg_hash = verify_frozen(prereg)
        timestamp = _utc_timestamp(effective_at)
        prereg_path = _repo_relative(prereg)

        with self._locked_file() as handle:
            events = self._read_and_verify(handle)
            event: dict[str, Any] = {
                "schema_version": 1,
                "event": "amended",
                "sequence": len(events) + 1,
                "effective_at": timestamp,
                "sleeve_id": sleeve_id.strip(),
                "prereg_path": prereg_path,
                "prereg_tag": registration.tag,
                "prereg_hash": prereg_hash,
                "changes": dict(changes),
                "reason": reason.strip(),
                "previous_event_hash": (
                    events[-1]["event_hash"] if events else _GENESIS_HASH
                ),
            }
            event["event_hash"] = sha256(_canonical_json(event)).hexdigest()
            handle.seek(0, os.SEEK_END)
            handle.write(_canonical_json(event) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
            self._write_head(event["event_hash"])
        return event["event_hash"]

    def entries(self) -> list[dict[str, Any]]:
        """Return amendments in append order after verifying the full chain."""

        with self._locked_file() as handle:
            return self._read_and_verify(handle)

    def head_hash(self) -> str:
        """Return the verified current ledger head, or the genesis hash."""

        entries = self.entries()
        return entries[-1]["event_hash"] if entries else _GENESIS_HASH

    def verify_integrity(self) -> None:
        """Raise if content changed, a row disappeared, or the tail was cut."""

        self.entries()

    def update(self, event_hash: str, values: Mapping[str, Any]) -> None:
        del event_hash, values
        raise ImmutableAmendmentError("amendments cannot be updated; append a correction")

    def delete(self, event_hash: str) -> None:
        del event_hash
        raise ImmutableAmendmentError("amendments cannot be deleted")

    def _read_and_verify(self, handle: BinaryIO) -> list[dict[str, Any]]:
        handle.seek(0)
        rows = handle.read().splitlines()
        events: list[dict[str, Any]] = []
        previous_hash = _GENESIS_HASH
        required = {
            "schema_version",
            "event",
            "sequence",
            "effective_at",
            "sleeve_id",
            "prereg_path",
            "prereg_tag",
            "prereg_hash",
            "changes",
            "reason",
            "previous_event_hash",
            "event_hash",
        }
        for line_number, row in enumerate(rows, start=1):
            try:
                event = json.loads(row)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise AmendmentIntegrityError(
                    f"invalid amendment JSON on line {line_number}"
                ) from exc
            if not isinstance(event, dict):
                raise AmendmentIntegrityError(
                    f"amendment must be an object on line {line_number}"
                )
            if set(event) != required:
                raise AmendmentIntegrityError(
                    f"amendment fields mismatch on line {line_number}"
                )
            claimed_hash = event.pop("event_hash")
            if event.get("previous_event_hash") != previous_hash:
                raise AmendmentIntegrityError(
                    f"broken amendment chain on line {line_number}"
                )
            if sha256(_canonical_json(event)).hexdigest() != claimed_hash:
                raise AmendmentIntegrityError(
                    f"amendment content changed on line {line_number}"
                )
            if (
                event.get("schema_version") != 1
                or event.get("event") != "amended"
                or event.get("sequence") != line_number
                or not isinstance(event.get("changes"), dict)
                or not event["changes"]
                or not isinstance(event.get("reason"), str)
                or not event["reason"]
            ):
                raise AmendmentIntegrityError(
                    f"invalid amendment event on line {line_number}"
                )
            try:
                _utc_timestamp(event["effective_at"])
            except (TypeError, ValueError) as exc:
                raise AmendmentIntegrityError(
                    f"invalid amendment timestamp on line {line_number}"
                ) from exc
            event["event_hash"] = claimed_hash
            events.append(event)
            previous_hash = claimed_hash

        if self.head_path.exists():
            checkpoint = self.head_path.read_text(encoding="ascii").strip()
            if checkpoint != previous_hash:
                raise AmendmentIntegrityError(
                    "amendment tail does not match head checkpoint"
                )
        elif events:
            raise AmendmentIntegrityError("amendment head checkpoint is missing")
        return events

    def _write_head(self, event_hash: str) -> None:
        temporary = self.head_path.with_name(f".{self.head_path.name}.{os.getpid()}.tmp")
        temporary.write_text(f"{event_hash}\n", encoding="ascii")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, self.head_path)
