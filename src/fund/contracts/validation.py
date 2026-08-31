"""S-14: PBO must be carried as a bootstrap interval, never a scalar."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


class PBOContractError(AssertionError):
    """Raised when PBO evidence lacks its sampling-uncertainty interval."""


def _interpolated_quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


@dataclass(frozen=True)
class PBOReport:
    estimate: float
    confidence: float
    interval_lower: float
    interval_upper: float
    bootstrap_replicates: int
    method: str = "bootstrap-interval"

    def as_result(self) -> dict[str, float | int | str]:
        """Serialize without offering a point-estimate-only representation."""

        return {
            "estimate": self.estimate,
            "confidence": self.confidence,
            "interval_lower": self.interval_lower,
            "interval_upper": self.interval_upper,
            "bootstrap_replicates": self.bootstrap_replicates,
            "method": self.method,
        }


def pbo_report(
    estimate: float,
    bootstrap_estimates: Sequence[float],
    *,
    confidence: float = 0.95,
) -> PBOReport:
    """Construct the only supported PBO reporting type: estimate plus interval."""

    values = tuple(float(value) for value in bootstrap_estimates)
    if not 0 <= estimate <= 1 or not math.isfinite(estimate):
        raise ValueError("PBO estimate must be finite and in [0, 1]")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be inside (0, 1)")
    if len(values) < 20:
        raise PBOContractError("PBO requires at least 20 bootstrap replicates")
    if any(not 0 <= value <= 1 or not math.isfinite(value) for value in values):
        raise ValueError("bootstrap PBO estimates must be finite and in [0, 1]")
    tail = (1.0 - confidence) / 2.0
    lower = _interpolated_quantile(values, tail)
    upper = _interpolated_quantile(values, 1.0 - tail)
    if lower > upper:
        raise PBOContractError("bootstrap interval is inverted")
    return PBOReport(
        estimate=estimate,
        confidence=confidence,
        interval_lower=lower,
        interval_upper=upper,
        bootstrap_replicates=len(values),
    )
