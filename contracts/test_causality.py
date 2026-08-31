from __future__ import annotations

import math

from hypothesis import given, strategies as st
import pytest

from fund.contracts import (
    CausalContractError,
    assert_causal_recomputation,
    causal_estimator,
)


FINITE = st.floats(
    min_value=-1e6,
    max_value=1e6,
    allow_nan=False,
    allow_infinity=False,
    width=64,
)


@causal_estimator
def expanding_mean(values: list[float]) -> list[float]:
    return [math.fsum(values[: index + 1]) / (index + 1) for index in range(len(values))]


@given(st.lists(FINITE, min_size=1, max_size=30))
def test_causal_recomputation_accepts_prefix_only_estimator(values: list[float]) -> None:
    assert_causal_recomputation(expanding_mean, values)
    expanding_mean.assert_causal(values)


def test_causal_recomputation_kills_future_leak() -> None:
    def smoothed(values: list[float]) -> list[float]:
        mean = math.fsum(values) / len(values)
        return [mean] * len(values)

    with pytest.raises(CausalContractError, match="future data changed"):
        assert_causal_recomputation(smoothed, [1.0, 2.0, 100.0])
