"""V-08b and V-12: discretized ranges and autocorrelation-aware Sharpe."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


class VolatilityContractError(AssertionError):
    """Raised when a volatility or annualisation invariant is violated."""


@dataclass(frozen=True)
class RangeVarianceReport:
    raw_variance: float
    corrected_variance: float
    prints_per_bar: int
    discretization_correction: float

    def as_telemetry(self) -> dict[str, float | int]:
        return {
            "raw_range_variance": self.raw_variance,
            "corrected_range_variance": self.corrected_variance,
            "prints_per_bar": self.prints_per_bar,
            "discretization_correction": self.discretization_correction,
        }


def apply_range_discretization(
    raw_variance: float,
    *,
    prints_per_bar: int,
    correction_factor: float | None,
) -> RangeVarianceReport:
    """Apply a sourced correction and emit prints-per-bar, or refuse the value."""

    if not math.isfinite(raw_variance) or raw_variance < 0:
        raise ValueError("raw variance must be finite and non-negative")
    if isinstance(prints_per_bar, bool) or not isinstance(prints_per_bar, int):
        raise ValueError("prints_per_bar must be an integer")
    if prints_per_bar <= 0:
        raise VolatilityContractError("range variance requires observed prints_per_bar")
    if correction_factor is None:
        raise VolatilityContractError(
            "range estimator refused: no discretization correction was supplied"
        )
    if not math.isfinite(correction_factor) or correction_factor < 1.0:
        raise VolatilityContractError(
            "finite-print range variance correction must be finite and >= 1"
        )
    return RangeVarianceReport(
        raw_variance=raw_variance,
        corrected_variance=raw_variance * correction_factor,
        prints_per_bar=prints_per_bar,
        discretization_correction=correction_factor,
    )


@dataclass(frozen=True)
class AnnualizedSharpe:
    lo_corrected: float
    naive_sqrt_diagnostic: float
    variance_ratio: float
    autocorrelations: tuple[float, ...]


def _sample_autocorrelation(samples: Sequence[float], lag: int, mean: float) -> float:
    centered = tuple(value - mean for value in samples)
    scale = max(abs(value) for value in centered)
    if scale == 0:
        raise ValueError("Sharpe is undefined for constant returns")
    normalized = tuple(value / scale for value in centered)
    denominator = math.fsum(value**2 for value in normalized)
    numerator = math.fsum(
        normalized[index] * normalized[index - lag]
        for index in range(lag, len(normalized))
    )
    return numerator / denominator


def annualized_sharpe(
    returns: Sequence[float],
    *,
    periods_per_year: int,
    max_lag: int | None = None,
) -> AnnualizedSharpe:
    """Return Lo-corrected Sharpe with naive sqrt scaling labelled diagnostic.

    ``max_lag`` truncates Lo's variance-ratio sum when the sample cannot support
    all ``periods_per_year - 1`` lags.  The chosen lag is part of the returned
    telemetry through the autocorrelation tuple and must be pre-registered.
    """

    values = tuple(float(value) for value in returns)
    if len(values) < 3 or any(not math.isfinite(value) for value in values):
        raise ValueError("annualized Sharpe needs at least three finite returns")
    if periods_per_year < 1:
        raise ValueError("periods_per_year must be positive")
    supported = min(periods_per_year - 1, len(values) - 2)
    lag_count = supported if max_lag is None else max_lag
    if lag_count < 0 or lag_count > supported:
        raise ValueError(f"max_lag must be in [0, {supported}]")
    mean = math.fsum(values) / len(values)
    deviations = tuple(value - mean for value in values)
    scale = max(abs(value) for value in deviations)
    if scale == 0:
        raise ValueError("Sharpe is undefined for constant returns")
    normalized_stdev = math.sqrt(
        math.fsum((value / scale) ** 2 for value in deviations)
        / (len(values) - 1)
    )
    periodic_sharpe = (mean / scale) / normalized_stdev
    autocorrelations = tuple(
        _sample_autocorrelation(values, lag, mean)
        for lag in range(1, lag_count + 1)
    )
    variance_ratio = 1.0 + 2.0 * math.fsum(
        (1.0 - lag / periods_per_year) * correlation
        for lag, correlation in enumerate(autocorrelations, start=1)
    )
    if variance_ratio <= 0 or not math.isfinite(variance_ratio):
        raise VolatilityContractError("Lo variance ratio is non-positive")
    return AnnualizedSharpe(
        lo_corrected=periodic_sharpe
        * math.sqrt(periods_per_year / variance_ratio),
        naive_sqrt_diagnostic=periodic_sharpe * math.sqrt(periods_per_year),
        variance_ratio=variance_ratio,
        autocorrelations=autocorrelations,
    )
