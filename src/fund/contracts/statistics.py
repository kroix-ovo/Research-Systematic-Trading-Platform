"""S-04: non-excess kurtosis in Sharpe uncertainty calculations."""

from __future__ import annotations

from collections.abc import Sequence
import math


class StatisticsContractError(AssertionError):
    """Raised when a statistical convention violates a registered contract."""


def non_excess_kurtosis(samples: Sequence[float]) -> float:
    """Return Pearson (non-excess) kurtosis; a Gaussian population is 3."""

    if len(samples) < 4:
        raise ValueError("kurtosis requires at least four observations")
    mean = math.fsum(samples) / len(samples)
    centered = [float(value) - mean for value in samples]
    second = math.fsum(value * value for value in centered) / len(centered)
    if second == 0:
        raise ValueError("kurtosis is undefined for a constant sample")
    fourth = math.fsum(value**4 for value in centered) / len(centered)
    return fourth / second**2


def assert_gaussian_kurtosis(kurtosis: float, *, tolerance: float = 0.15) -> None:
    """Reject a convention that reports Gaussian kurtosis near zero."""

    if not math.isfinite(kurtosis) or abs(kurtosis - 3.0) > tolerance:
        raise StatisticsContractError(
            f"gamma_4 must be non-excess kurtosis near 3; received {kurtosis}"
        )


def sharpe_standard_error(
    sharpe: float,
    observations: int,
    *,
    skewness: float,
    kurtosis: float,
) -> float:
    """Mertens/Lo standard error using *non-excess* ``kurtosis``.

    For Gaussian input (skewness 0, kurtosis 3), the numerator reduces exactly
    to ``sqrt(1 + sharpe**2 / 2)``.
    """

    if observations < 2:
        raise ValueError("at least two observations are required")
    values = (sharpe, skewness, kurtosis)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Sharpe moments must be finite")
    if kurtosis < 1.0:
        raise StatisticsContractError(
            "gamma_4 must be Pearson/non-excess kurtosis (and cannot be below 1)"
        )
    variance_numerator = (
        1.0 - skewness * sharpe + ((kurtosis - 1.0) / 4.0) * sharpe**2
    )
    if variance_numerator <= 0:
        raise StatisticsContractError("Sharpe variance formula is non-positive")
    return math.sqrt(variance_numerator / (observations - 1))
