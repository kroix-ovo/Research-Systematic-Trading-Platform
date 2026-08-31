"""Q-02 and Q-08: signed loss metrics and safe tail quantiles."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


class RiskMetricError(AssertionError):
    """Raised when a risk metric is incoherent under the house convention."""


def assert_loss_risk_metrics(value_at_risk: float, conditional_var: float) -> None:
    """Enforce the house convention: both are positive losses and VaR <= CVaR."""

    if not math.isfinite(value_at_risk) or not math.isfinite(conditional_var):
        raise RiskMetricError("VaR and CVaR must be finite")
    if value_at_risk <= 0:
        raise RiskMetricError("VaR must be reported as a positive loss")
    if conditional_var < value_at_risk:
        raise RiskMetricError("CVaR must be greater than or equal to VaR")


def _cornish_fisher_z(z_score: float, skewness: float, excess_kurtosis: float) -> float:
    return (
        z_score
        + (z_score**2 - 1.0) * skewness / 6.0
        + (z_score**3 - 3.0 * z_score) * excess_kurtosis / 24.0
        - (2.0 * z_score**3 - 5.0 * z_score) * skewness**2 / 36.0
    )


def _historical_quantile(samples: Sequence[float], confidence: float) -> float:
    if not samples:
        raise ValueError("historical fallback requires observed losses")
    ordered = sorted(float(value) for value in samples)
    if any(not math.isfinite(value) for value in ordered):
        raise ValueError("historical losses must be finite")
    index = max(0, math.ceil(confidence * len(ordered)) - 1)
    return ordered[index]


@dataclass(frozen=True)
class QuantileResult:
    confidences: tuple[float, ...]
    quantiles: tuple[float, ...]
    method: str
    fallback_reason: str | None = None


def cornish_fisher_or_historical(
    *,
    confidences: Sequence[float],
    gaussian_z_scores: Sequence[float],
    mean: float,
    standard_deviation: float,
    skewness: float,
    excess_kurtosis: float,
    historical_losses: Sequence[float],
) -> QuantileResult:
    """Use Cornish-Fisher only when its requested quantiles are non-decreasing."""

    if len(confidences) != len(gaussian_z_scores) or not confidences:
        raise ValueError("confidence and z-score sequences must have equal non-zero length")
    if any(not 0 < value < 1 for value in confidences):
        raise ValueError("confidences must lie strictly inside (0, 1)")
    if any(right <= left for left, right in zip(confidences, confidences[1:])):
        raise ValueError("confidences must be strictly increasing")
    if any(right <= left for left, right in zip(gaussian_z_scores, gaussian_z_scores[1:])):
        raise ValueError("Gaussian z-scores must be strictly increasing")
    if standard_deviation <= 0 or not math.isfinite(standard_deviation):
        raise ValueError("standard deviation must be positive and finite")
    adjusted = tuple(
        mean + standard_deviation * _cornish_fisher_z(z, skewness, excess_kurtosis)
        for z in gaussian_z_scores
    )
    if all(right >= left for left, right in zip(adjusted, adjusted[1:])):
        return QuantileResult(tuple(confidences), adjusted, "cornish-fisher")
    historical = tuple(
        _historical_quantile(historical_losses, confidence)
        for confidence in confidences
    )
    if any(right < left for left, right in zip(historical, historical[1:])):
        raise RiskMetricError("historical quantiles are unexpectedly non-monotone")
    return QuantileResult(
        tuple(confidences),
        historical,
        "historical",
        "Cornish-Fisher quantiles were non-monotone",
    )
