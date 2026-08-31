from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from fund.prereg import (
    FrozenPreregistrationError,
    PreregistrationValidationError,
    freeze,
    validate,
    verify_frozen,
)
from fund.registry import TrialRegistry, render_markdown


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


def test_validate_rejects_placeholders(
    tmp_path: Path, complete_preregistration: str
) -> None:
    path = write_prereg(initialize_repo(tmp_path), complete_preregistration)
    validate(path)
    path.write_text(
        complete_preregistration.replace("Prior belief it is true, before looking (a number, 0-1): 0.30", "Prior belief it is true, before looking (a number, 0-1): TBD"),
        encoding="utf-8",
    )
    with pytest.raises(PreregistrationValidationError, match="placeholder"):
        validate(path)


def test_freeze_tags_and_verify_frozen(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo = initialize_repo(tmp_path)
    path = write_prereg(repo, complete_preregistration)

    tag_hash = freeze(path)

    assert tag_hash == git(repo, "rev-parse", "slice-01-prereg")
    assert verify_frozen(path) == tag_hash
    assert not git(repo, "log", "--diff-filter=M", "--format=%H", "--", str(path.relative_to(repo)))


def test_verify_frozen_rejects_worktree_change(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo = initialize_repo(tmp_path)
    path = write_prereg(repo, complete_preregistration)
    freeze(path)
    path.write_text(f"{complete_preregistration}\nAmendment after results.\n", encoding="utf-8")

    with pytest.raises(FrozenPreregistrationError, match="differs"):
        verify_frozen(path)


def test_dummy_prereg_round_trips_tag_registry_report(
    tmp_path: Path, complete_preregistration: str
) -> None:
    repo = initialize_repo(tmp_path)
    path = write_prereg(repo, complete_preregistration)
    tag_hash = freeze(path)
    registry = TrialRegistry(
        repo / "out" / "registry.jsonl",
        clock=lambda: "2026-08-11T16:01:00Z",
    )
    trial_id = registry.register(
        {
            "sleeve_id": "slice-01",
            "prereg_hash": tag_hash,
            "config": {"estimator": "dummy"},
            "data_manifest_hash": "sha256:dummy-manifest",
            "seed": 20260811,
        }
    )
    registry.record(trial_id, {"contract": "round-trip"})

    report = render_markdown(registry)
    assert tag_hash in report
    assert trial_id in report
    assert "round-trip" in report
