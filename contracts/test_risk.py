from __future__ import annotations

from hypothesis import given, strategies as st
import pytest

from fund.contracts import (
    RiskMetricError,
    assert_loss_risk_metrics,
    cornish_fisher_or_historical,
)


@given(
    value_at_risk=st.floats(
        min_value=1e-12, max_value=1e9, allow_nan=False, allow_infinity=False
    ),
    tail_increment=st.floats(
        min_value=0.0, max_value=1e9, allow_nan=False, allow_infinity=False
    ),
)
def test_positive_loss_var_is_bounded_by_cvar(
    value_at_risk: float, tail_increment: float
) -> None:
    assert_loss_risk_metrics(value_at_risk, value_at_risk + tail_increment)


@pytest.mark.parametrize("value_at_risk,conditional_var", [(-1.0, 2.0), (2.0, 1.0)])
def test_var_sign_or_order_inversion_is_rejected(
    value_at_risk: float, conditional_var: float
) -> None:
    with pytest.raises(RiskMetricError):
        assert_loss_risk_metrics(value_at_risk, conditional_var)


def test_cornish_fisher_inversion_falls_back_to_historical() -> None:
    z_scores = [0.5 + index * 3.0 / 79 for index in range(80)]
    confidences = [0.50 + index * 0.499 / 79 for index in range(80)]
    result = cornish_fisher_or_historical(
        confidences=confidences,
        gaussian_z_scores=z_scores,
        mean=0.0,
        standard_deviation=1.0,
        skewness=-3.0,
        excess_kurtosis=12.0,
        historical_losses=[index / 100 for index in range(1, 101)],
    )
    assert result.method == "historical"
    assert all(right >= left for left, right in zip(result.quantiles, result.quantiles[1:]))


def test_mild_cornish_fisher_case_remains_primary() -> None:
    result = cornish_fisher_or_historical(
        confidences=[0.90, 0.95, 0.99],
        gaussian_z_scores=[1.2816, 1.6449, 2.3263],
        mean=0.0,
        standard_deviation=1.0,
        skewness=0.2,
        excess_kurtosis=0.5,
        historical_losses=[0.5, 1.0, 1.5, 2.0],
    )
    assert result.method == "cornish-fisher"
