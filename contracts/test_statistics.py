from __future__ import annotations

import math
import random

from hypothesis import given, strategies as st
import pytest

from fund.contracts import (
    StatisticsContractError,
    assert_gaussian_kurtosis,
    non_excess_kurtosis,
    sharpe_standard_error,
)


@given(
    sharpe=st.floats(
        min_value=-5,
        max_value=5,
        allow_nan=False,
        allow_infinity=False,
    ),
    observations=st.integers(min_value=2, max_value=100_000),
)
def test_gaussian_sharpe_se_reduces_to_known_special_case(
    sharpe: float, observations: int
) -> None:
    actual = sharpe_standard_error(
        sharpe, observations, skewness=0.0, kurtosis=3.0
    )
    expected = math.sqrt(1.0 + sharpe**2 / 2.0) / math.sqrt(observations - 1)
    assert actual == pytest.approx(expected, rel=1e-14, abs=1e-14)


def test_gaussian_sample_reports_pearson_kurtosis_near_three() -> None:
    generator = random.Random(20260811)
    samples = [generator.gauss(0.0, 1.0) for _ in range(50_000)]
    kurtosis = non_excess_kurtosis(samples)
    assert_gaussian_kurtosis(kurtosis, tolerance=0.08)


def test_excess_kurtosis_convention_is_rejected() -> None:
    with pytest.raises(StatisticsContractError, match="non-excess"):
        sharpe_standard_error(0.5, 120, skewness=0.0, kurtosis=0.0)
