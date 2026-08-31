"""Executable contracts for the report's live failure modes.

These functions are small on purpose: future estimators and backtests call them
at their boundaries, while the property suite in the repository's top-level
``contracts/`` directory attacks the invariants independently.
"""

from .accounting import GrowthAccounting, compound_realized_returns
from .causality import CausalContractError, assert_causal_recomputation, causal_estimator
from .risk import (
    QuantileResult,
    RiskMetricError,
    assert_loss_risk_metrics,
    cornish_fisher_or_historical,
)
from .statistics import (
    StatisticsContractError,
    assert_gaussian_kurtosis,
    non_excess_kurtosis,
    sharpe_standard_error,
)
from .telemetry import CapBindingReport, enforce_cap_binding
from .validation import PBOReport, pbo_report
from .volatility import (
    AnnualizedSharpe,
    RangeVarianceReport,
    apply_range_discretization,
    annualized_sharpe,
)

__all__ = [
    "AnnualizedSharpe",
    "CapBindingReport",
    "CausalContractError",
    "GrowthAccounting",
    "PBOReport",
    "QuantileResult",
    "RangeVarianceReport",
    "RiskMetricError",
    "StatisticsContractError",
    "annualized_sharpe",
    "apply_range_discretization",
    "assert_causal_recomputation",
    "assert_gaussian_kurtosis",
    "assert_loss_risk_metrics",
    "causal_estimator",
    "compound_realized_returns",
    "cornish_fisher_or_historical",
    "enforce_cap_binding",
    "non_excess_kurtosis",
    "pbo_report",
    "sharpe_standard_error",
]
