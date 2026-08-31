from __future__ import annotations

from hypothesis import given, strategies as st
import pytest

from fund.contracts import enforce_cap_binding, pbo_report
from fund.contracts.telemetry import CapBindingError
from fund.contracts.validation import PBOContractError


@given(
    exposures=st.lists(
        st.floats(
            min_value=0.0,
            max_value=2.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=1,
        max_size=100,
    )
)
def test_cap_binding_fraction_is_always_emitted(exposures: list[float]) -> None:
    report = enforce_cap_binding(
        exposures,
        cap=1.0,
        threshold=1.0,
    )
    expected = sum(value >= 1.0 - 1e-12 for value in exposures) / len(exposures)
    assert report.cap_binding_fraction == expected
    assert "cap_binding_fraction" in report.as_telemetry()


def test_cap_binding_gate_requires_explicit_acknowledgement() -> None:
    exposures = [1.0, 1.0, 1.0, 0.5]
    with pytest.raises(CapBindingError):
        enforce_cap_binding(exposures, cap=1.0, threshold=0.25)
    report = enforce_cap_binding(
        exposures, cap=1.0, threshold=0.25, acknowledged=True
    )
    assert report.acknowledged


@given(
    estimates=st.lists(
        st.floats(
            min_value=0.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=20,
        max_size=100,
    ),
    point=st.floats(
        min_value=0.0,
        max_value=1.0,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_pbo_result_always_contains_bootstrap_interval(
    estimates: list[float], point: float
) -> None:
    report = pbo_report(point, estimates)
    result = report.as_result()
    assert result["interval_lower"] <= result["interval_upper"]
    assert result["bootstrap_replicates"] == len(estimates)
    assert result["method"] == "bootstrap-interval"


def test_pbo_point_estimate_without_interval_is_refused() -> None:
    with pytest.raises(PBOContractError, match="bootstrap"):
        pbo_report(0.5, [0.4, 0.6])
