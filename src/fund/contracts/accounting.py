"""V-14: growth accounting compounds realized simple returns."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class GrowthAccounting:
    initial_wealth: float
    ending_wealth: float
    total_return: float
    wealth_path: tuple[float, ...]
    method: str = "compounded-realized-simple-returns"


def compound_realized_returns(
    returns: Sequence[float], *, initial_wealth: float = 1.0
) -> GrowthAccounting:
    """Compute P&L by multiplying realized wealth relatives, never mu-sigma²/2."""

    if not math.isfinite(initial_wealth) or initial_wealth <= 0:
        raise ValueError("initial wealth must be positive and finite")
    wealth = initial_wealth
    path: list[float] = []
    for value in returns:
        simple_return = float(value)
        if not math.isfinite(simple_return) or simple_return < -1.0:
            raise ValueError("simple returns must be finite and cannot be below -100%")
        wealth *= 1.0 + simple_return
        path.append(wealth)
    return GrowthAccounting(
        initial_wealth=initial_wealth,
        ending_wealth=wealth,
        total_return=wealth / initial_wealth - 1.0,
        wealth_path=tuple(path),
    )
