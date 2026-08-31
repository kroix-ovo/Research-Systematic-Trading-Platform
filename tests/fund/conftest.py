from __future__ import annotations

import pytest


@pytest.fixture
def complete_preregistration() -> str:
    return """# Slice 01 Pre-Registration
Frozen: 2026-08-11T16:00:00Z   Git tag: slice-01-prereg

## 1. Hypothesis
H1 (one sentence, falsifiable): Causal volatility scaling beats all baselines net of costs.
Mechanism (why it should be true, 3 links): persistence; weak risk-return relation; inverse-risk exposure.
Prior belief it is true, before looking (a number, 0-1): 0.30

## 2. Data
Instrument: SPY
Vendor: Polygon.io / Massive plus ALFRED
Sample start/end: 2003-09-10 through the frozen retrieval vintage
Point-in-time method: raw OHLCV plus as-of corporate actions
What I will do about restatement bias: reconstruct each vintage from immutable events

## 3. Signal specification
Estimators to be tried (EXHAUSTIVE LIST — anything added later is an amendment): EWMA only
Parameter grids (EXHAUSTIVE): lambda in {0.94}
Implied trial count N: 1
Rebalancing frequency: daily
Execution assumption: next close
Volatility target sigma*: 0.10
Leverage cap L: 1.0

## 4. Costs
Spread: sourced half-spread
Commission: broker schedule
Impact: square-root model
Financing (long AND short of 1x): historical debit and credit rate series
Sensitivity levels to be reported: 0.5x, 1x, 2x

## 5. Baselines
B1: buy and hold
B2: matched average exposure
B3: matched realized volatility
Comparison metric (scale-free AND matched-volatility): Sharpe and return at matched volatility

## 6. Evaluation protocol
Walk-forward scheme: expanding annual folds
Purge length: 1 day
Embargo length: 1 day
Deflation method and where N comes from: DSR using the fund registry
Significance test vs baseline: Ledoit-Wolf robust Sharpe difference
Robustness: leave-one-crisis-out periods: 2008, 2020, and both

## 7. Decision thresholds (FILL IN NUMBERS NOW)
Proceed to paper trading only if ALL of:
  - [ ] Net Sharpe > B1, B2, B3
  - [ ] DSR > 0.95
  - [ ] PBO 95% upper bound < 0.50
  - [ ] LW Sharpe-difference p < 0.05 vs B3
  - [ ] Survives leave-one-crisis-out
  - [ ] Survives 2x cost sensitivity
  - [ ] cap_binding_fraction < 0.25

## 8. Stopping rules
I will abandon this slice if: any registered gate fails
I will NOT do the following to rescue a negative result: alter the frozen hypothesis or grid
  - add instruments        - add filters/overlays
  - change the sample      - change the baseline
  - change sigma* or L after seeing results

## 9. What would change my mind
If the result is positive, the most likely non-edge explanation is: restatement bias or understated costs
If negative, what I would want to test next: a separately preregistered low-correlation sleeve
"""
