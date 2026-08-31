"""Append-only, hash-chained trial registry.

The registry is deliberately event sourced.  ``register`` appends a pending
trial before evaluation; ``record`` appends its terminal outcome later.  No
existing JSONL line is rewritten.  The materialized view exposed by
``entries`` still contains one logical entry per tested configuration.
"""

from .ledger import (
    AppendOnlyViolation,
    RegistryIntegrityError,
    TrialRegistry,
    render_markdown,
)

__all__ = [
    "AppendOnlyViolation",
    "RegistryIntegrityError",
    "TrialRegistry",
    "render_markdown",
]
