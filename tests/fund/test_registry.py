from __future__ import annotations

from pathlib import Path

import pytest

from fund.registry import (
    AppendOnlyViolation,
    RegistryIntegrityError,
    TrialRegistry,
    render_markdown,
)


FIXED_TIME = "2026-08-11T16:00:00Z"


def registration(sleeve: str = "slice-01") -> dict[str, object]:
    return {
        "sleeve_id": sleeve,
        "prereg_hash": "sha256:prereg",
        "config": {"estimator": "ewma", "lambda": 0.94},
        "data_manifest_hash": "sha256:manifest",
        "seed": 20260811,
    }


def registry(path: Path) -> TrialRegistry:
    return TrialRegistry(path, clock=lambda: FIXED_TIME)


def test_register_precedes_result_and_count_is_cumulative(tmp_path: Path) -> None:
    trials = registry(tmp_path / "registry.jsonl")
    first = trials.register(registration())
    second = trials.register(registration("slice-02"))

    pending = trials.entries()
    assert [entry["outcome"] for entry in pending] == [None, None]
    assert trials.count() == 2
    assert trials.count("slice-01") == 1

    trials.record(first, {"net_sharpe": -0.1})
    trials.record(second, {"reason": "operator stop"}, outcome="abandoned")
    assert [entry["outcome"] for entry in trials.entries()] == [
        "evaluated",
        "abandoned",
    ]


def test_registry_rejects_update_delete_and_second_outcome(tmp_path: Path) -> None:
    trials = registry(tmp_path / "registry.jsonl")
    trial_id = trials.register(registration())
    trials.record(trial_id, {"value": 1})

    with pytest.raises(AppendOnlyViolation):
        trials.update(trial_id, {"value": 2})
    with pytest.raises(AppendOnlyViolation):
        trials.delete(trial_id)
    with pytest.raises(AppendOnlyViolation):
        trials.record(trial_id, {"value": 2})


def test_hash_chain_detects_mutation(tmp_path: Path) -> None:
    trials = registry(tmp_path / "registry.jsonl")
    trials.register(registration())
    original = trials.path.read_text(encoding="utf-8")
    trials.path.write_text(original.replace("slice-01", "slice-99"), encoding="utf-8")

    with pytest.raises(RegistryIntegrityError, match="content changed"):
        trials.verify_integrity()


def test_head_checkpoint_detects_tail_deletion(tmp_path: Path) -> None:
    trials = registry(tmp_path / "registry.jsonl")
    trial_id = trials.register(registration())
    trials.record(trial_id, {"value": 1})
    rows = trials.path.read_text(encoding="utf-8").splitlines()
    trials.path.write_text(f"{rows[0]}\n", encoding="utf-8")

    with pytest.raises(RegistryIntegrityError, match="head checkpoint"):
        trials.verify_integrity()


def test_fixed_clock_produces_byte_identical_ledgers(tmp_path: Path) -> None:
    paths = [tmp_path / "a.jsonl", tmp_path / "b.jsonl"]
    for path in paths:
        trials = registry(path)
        trial_id = trials.register(registration())
        trials.record(trial_id, {"net_sharpe": 0.25})

    assert paths[0].read_bytes() == paths[1].read_bytes()
    assert paths[0].with_name("a.jsonl.head").read_bytes() == paths[1].with_name(
        "b.jsonl.head"
    ).read_bytes()


def test_report_is_generated_from_registry(tmp_path: Path) -> None:
    trials = registry(tmp_path / "registry.jsonl")
    trial_id = trials.register(registration())
    trials.record(trial_id, {"net_sharpe": 0.25})

    report = render_markdown(trials)
    assert trial_id in report
    assert "sha256:prereg" in report
    assert "Cumulative trials: 1" in report
