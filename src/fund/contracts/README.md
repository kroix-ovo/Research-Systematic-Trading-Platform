# Caveat contract traceability

This package contains runtime assertions; the repository-level `contracts/`
directory contains their property tests.

| Finding | Mechanical contract | Failure prevented |
|---|---|---|
| G-01 | `assert_causal_recomputation` and `@causal_estimator` | Future observations changing a signal at time `t` |
| S-04 | Pearson-kurtosis calculation and Sharpe standard-error checks | Excess-kurtosis convention understating Sharpe uncertainty |
| K-02 | Mandatory `cap_binding_fraction`, threshold, acknowledgement | A leverage cap silently turning vol targeting into constant leverage |
| Q-02 | Positive-loss VaR and `VaR <= CVaR` | Risk-limit sign inversion |
| Q-08 | Cornish-Fisher monotonicity with historical fallback | Higher confidence producing a smaller reported loss |
| V-08b | Required prints-per-bar and sourced correction factor | Finite-print range bias causing systematic over-leverage |
| V-12 | Lo-corrected primary Sharpe plus labelled naive diagnostic | Autocorrelation inflating annualized Sharpe |
| V-14 | Realized-return compounding API | Using `mu - sigma^2/2` as a P&L identity |
| S-14 | `PBOReport` requires bootstrap bounds | Treating a noisy PBO draw as a precise gate |

E-03 is intentionally documented rather than enforced. Its measured worst
objective penalty is approximately `9.8e-09`; no M0 or M1 runtime component
computes an Almgren-Chriss schedule, so a runtime assertion would be speculative
infrastructure. If a later execution module implements that approximation, it
must state the fine-grid/temporary-impact assumptions and gain its own
round-trip contract before use.

These contracts cannot force an unrelated future call site to invoke them.
Integration tests at each consuming M1 boundary are therefore part of that
phase's gate; M0 supplies and attacks the invariant implementations themselves.
