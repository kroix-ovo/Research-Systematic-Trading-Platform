"""G-01: causal recomputation for every sequential estimator."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from functools import wraps
import pickle
from typing import Any, TypeVar, cast


class CausalContractError(AssertionError):
    """Raised when removing future data changes an estimator's value at time t."""


Estimator = Callable[[Sequence[Any]], Sequence[Any]]
F = TypeVar("F", bound=Estimator)


def _bits(value: Any) -> bytes:
    """Return a representation that preserves exact float bit patterns."""

    return pickle.dumps(value, protocol=5)


def assert_causal_recomputation(
    estimator: Estimator,
    data: Sequence[Any],
    *,
    indices: Iterable[int] | None = None,
) -> None:
    """Assert full-history and truncated-history outputs are bit-identical.

    The estimator must return one output per input.  Indices may be sampled by
    a caller for an expensive estimator; omitting them checks every time point.
    """

    full = estimator(data)
    if len(full) != len(data):
        raise CausalContractError("estimator must return one value per observation")
    selected = range(len(data)) if indices is None else tuple(indices)
    for index in selected:
        if index < 0 or index >= len(data):
            raise IndexError(f"causality index outside input: {index}")
        truncated = estimator(data[: index + 1])
        if len(truncated) != index + 1:
            raise CausalContractError(
                f"truncated estimator returned {len(truncated)} values at t={index}"
            )
        if _bits(truncated[-1]) != _bits(full[index]):
            raise CausalContractError(
                f"future data changed estimator output at t={index}"
            )


def causal_estimator(function: F) -> F:
    """Mark an estimator and attach its mandatory causal-contract runner."""

    @wraps(function)
    def wrapped(data: Sequence[Any]) -> Sequence[Any]:
        result = function(data)
        if len(result) != len(data):
            raise CausalContractError("estimator must return one value per observation")
        return result

    def check(
        data: Sequence[Any], *, indices: Iterable[int] | None = None
    ) -> None:
        assert_causal_recomputation(wrapped, data, indices=indices)

    setattr(wrapped, "assert_causal", check)
    setattr(wrapped, "is_causal_estimator", True)
    return cast(F, wrapped)
