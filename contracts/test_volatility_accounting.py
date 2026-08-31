from __future__ import annotations

import math
import random

from hypothesis import given, strategies as st
import pytest

from fund.contracts import (
    annualized_sharpe,
    apply_range_discretization,
    compound_realized_returns,
)
from fund.contracts.volatility import VolatilityContractError


@given(
    raw_variance=st.floats(
        min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False
    ),
    prints=st.integers(min_value=1, max_value=10_000_000),
    correction=st.floats(
        min_value=1.0, max_value=5.0, allow_nan=False, allow_infinity=False
    ),
)
def test_range_estimator_applies_correction_and_emits_print_count(
    raw_variance: float, prints: int, correction: float
) -> None:
    report = apply_range_discretization(
        raw_variance,
        prints_per_bar=prints,
        correction_factor=correction,
    )
    assert report.corrected_variance >= report.raw_variance
    assert report.as_telemetry()["prints_per_bar"] == prints


def test_range_estimator_refuses_unsourced_correction() -> None:
    with pytest.raises(VolatilityContractError, match="refused"):
        apply_range_discretization(0.01, prints_per_bar=100, correction_factor=None)


@given(
    st.lists(
        st.floats(
            min_value=-0.99,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        max_size=40,
    )
)
def test_growth_is_product_of_realized_wealth_relatives(returns: list[float]) -> None:
    report = compound_realized_returns(returns)
    expected = math.prod(1.0 + value for value in returns) - 1.0
    assert report.total_return == pytest.approx(expected, rel=1e-14, abs=1e-14)
    assert report.method == "compounded-realized-simple-returns"


def test_lo_correction_is_primary_when_returns_are_autocorrelated() -> None:
    generator = random.Random(20260811)
    state = 0.0
    returns = []
    for _ in range(5_000):
        state = 0.3 * state + generator.gauss(0.0, 0.01)
        returns.append(0.0004 + state)
    report = annualized_sharpe(returns, periods_per_year=252, max_lag=20)
    assert report.variance_ratio > 1.0
    assert report.lo_corrected < report.naive_sqrt_diagnostic


@given(
    returns=st.lists(
        st.floats(
            min_value=-1.0,
            max_value=1.0,
            allow_nan=False,
            allow_infinity=False,
        ),
        min_size=3,
        max_size=30,
        unique=True,
    ),
    periods=st.integers(min_value=1, max_value=365),
)
def test_zero_lag_lo_case_matches_labelled_naive_diagnostic(
    returns: list[float], periods: int
) -> None:
    report = annualized_sharpe(returns, periods_per_year=periods, max_lag=0)
    assert report.lo_corrected == pytest.approx(report.naive_sqrt_diagnostic)
