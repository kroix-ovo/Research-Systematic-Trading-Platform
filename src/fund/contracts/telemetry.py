"""K-02: leverage-cap binding is first-class, gateable telemetry."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


class CapBindingError(AssertionError):
    """Raised when the leverage cap changes the tested strategy too often."""


@dataclass(frozen=True)
class CapBindingReport:
    cap_binding_fraction: float
    observations: int
    cap: float
    threshold: float
    acknowledged: bool

    def as_telemetry(self) -> dict[str, float | int | bool]:
        """Return the mandatory JSON-compatible runtime telemetry."""

        return {
            "cap_binding_fraction": self.cap_binding_fraction,
            "cap_binding_observations": self.observations,
            "leverage_cap": self.cap,
            "cap_binding_threshold": self.threshold,
            "cap_binding_acknowledged": self.acknowledged,
        }


def enforce_cap_binding(
    gross_exposures: Sequence[float],
    *,
    cap: float,
    threshold: float = 0.25,
    acknowledged: bool = False,
    absolute_tolerance: float = 1e-12,
) -> CapBindingReport:
    """Measure cap binding and fail above the threshold unless acknowledged."""

    if not gross_exposures:
        raise ValueError("cap telemetry requires at least one exposure")
    if not math.isfinite(cap) or cap <= 0:
        raise ValueError("cap must be positive and finite")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1]")
    if any(not math.isfinite(value) or value < 0 for value in gross_exposures):
        raise ValueError("gross exposures must be finite and non-negative")
    bound = sum(
        value >= cap - absolute_tolerance for value in gross_exposures
    )
    fraction = bound / len(gross_exposures)
    report = CapBindingReport(
        cap_binding_fraction=fraction,
        observations=len(gross_exposures),
        cap=cap,
        threshold=threshold,
        acknowledged=acknowledged,
    )
    if fraction > threshold and not acknowledged:
        raise CapBindingError(
            f"cap_binding_fraction={fraction:.6f} exceeds {threshold:.6f}"
        )
    return report
