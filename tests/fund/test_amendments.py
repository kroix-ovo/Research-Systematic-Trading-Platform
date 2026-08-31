from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from fund.prereg import (
    AmendmentIntegrityError,
    AmendmentLedger,
    FrozenPreregistrationError,
    ImmutableAmendmentError,
    freeze,
)


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return completed.stdout.strip()


def initialize_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "M0 Contract Test")
    git(repo, "config", "user.email", "m0@example.invalid")
    return repo


def write_prereg(repo: Path, text: str) -> Path:
    path = repo / "Docs" / "slice-01" / "PREREGISTRATION.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


def frozen_prereg(
    tmp_path: Path, complete_preregistration: str
) -> tuple[Path, Path, str]:
    repo = initialize_repo(tmp_path)
    prereg = write_prereg(repo, complete_preregistration)
    return repo, prereg, freeze(prereg)


def test_amendment_is_separate_dated_and_bound_to_frozen_tag(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo, prereg, prereg_hash = frozen_prereg(tmp_path, complete_preregistration)
    original = prereg.read_bytes()
    ledger = AmendmentLedger(repo / "Docs" / "slice-01" / "AMENDMENTS.jsonl")

    amendment_hash = ledger.append(
        prereg,
        sleeve_id="slice-01",
        effective_at="2026-08-12T12:30:00Z",
        changes={"cost_sensitivity": "add 3x diagnostic; frozen 2x gate unchanged"},
        reason="diagnostic requested before any result was evaluated",
    )

    assert prereg.read_bytes() == original
    assert ledger.head_hash() == amendment_hash
    assert ledger.entries() == [
        {
            "schema_version": 1,
            "event": "amended",
            "sequence": 1,
            "effective_at": "2026-08-12T12:30:00Z",
            "sleeve_id": "slice-01",
            "prereg_path": "Docs/slice-01/PREREGISTRATION.md",
            "prereg_tag": "slice-01-prereg",
            "prereg_hash": prereg_hash,
            "changes": {
                "cost_sensitivity": "add 3x diagnostic; frozen 2x gate unchanged"
            },
            "reason": "diagnostic requested before any result was evaluated",
            "previous_event_hash": "0" * 64,
            "event_hash": amendment_hash,
        }
    ]


def test_amendment_refuses_unfrozen_preregistration(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo = initialize_repo(tmp_path)
    prereg = write_prereg(repo, complete_preregistration)
    ledger = AmendmentLedger(repo / "Docs" / "slice-01" / "AMENDMENTS.jsonl")

    with pytest.raises(FrozenPreregistrationError):
        ledger.append(
            prereg,
            sleeve_id="slice-01",
            effective_at="2026-08-12T12:30:00Z",
            changes={"estimator": "add a diagnostic"},
            reason="pre-results request",
        )


def test_amendment_requires_explicit_utc_date_and_nonempty_change(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo, prereg, _ = frozen_prereg(tmp_path, complete_preregistration)
    ledger = AmendmentLedger(repo / "Docs" / "slice-01" / "AMENDMENTS.jsonl")

    with pytest.raises(ValueError, match="UTC"):
        ledger.append(
            prereg,
            sleeve_id="slice-01",
            effective_at="2026-08-12T12:30:00-04:00",
            changes={"estimator": "diagnostic"},
            reason="pre-results request",
        )
    with pytest.raises(ValueError, match="non-empty mapping"):
        ledger.append(
            prereg,
            sleeve_id="slice-01",
            effective_at="2026-08-12T16:30:00Z",
            changes={},
            reason="pre-results request",
        )


def test_amendment_ledger_detects_mutation_and_tail_truncation(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo, prereg, _ = frozen_prereg(tmp_path, complete_preregistration)
    path = repo / "Docs" / "slice-01" / "AMENDMENTS.jsonl"
    ledger = AmendmentLedger(path)
    for hour in (12, 13):
        ledger.append(
            prereg,
            sleeve_id="slice-01",
            effective_at=f"2026-08-12T{hour}:30:00Z",
            changes={"diagnostic": f"diagnostic-{hour}"},
            reason="approved before evaluation",
        )

    rows = path.read_text(encoding="utf-8").splitlines()
    path.write_text(f"{rows[0]}\n", encoding="utf-8")
    with pytest.raises(AmendmentIntegrityError, match="head checkpoint"):
        ledger.verify_integrity()

    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    event = json.loads(rows[0])
    event["reason"] = "silently changed"
    rows[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(AmendmentIntegrityError, match="content changed"):
        ledger.verify_integrity()


def test_amendments_are_never_updated_or_deleted(tmp_path: Path) -> None:
    ledger = AmendmentLedger(tmp_path / "AMENDMENTS.jsonl")
    with pytest.raises(ImmutableAmendmentError, match="cannot be updated"):
        ledger.update("event", {"reason": "rewrite"})
    with pytest.raises(ImmutableAmendmentError, match="cannot be deleted"):
        ledger.delete("event")
