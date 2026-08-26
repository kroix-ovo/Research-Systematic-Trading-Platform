# M0 Governance Skeleton — Implementation Report

**Role:** Engineering desk  
**Milestone:** M0  
**Status:** implementation and first-party tests complete; independent
different-vendor validation remains a separate A2 gate.

## Delivered controls

1. `src/fund/registry/` is an event-sourced, append-only JSONL trial ledger.
   Registration is a physical event written before a result can be recorded.
   Each line is hash-chained and a separate head checkpoint detects tail
   truncation. `count()` counts registrations, including pending, abandoned,
   and errored trials; it never infers `N` from winning results.
2. `src/fund/prereg/` validates all nine template sections, rejects placeholder
   text, requires numeric decision thresholds, and freezes a new document with
   a Git commit and annotated tag. Git dates come from the UTC timestamp written
   in the preregistration rather than the process clock. Approved amendments
   go to a separate hash-chained companion ledger that binds each event to the
   frozen tag without modifying the frozen Markdown.
3. `src/fund/contracts/` implements the caveat contracts. Property tests live
   in the repository-level `contracts/` directory, making the charter's
   `pytest contracts/` gate executable.
4. `src/fund/runtime/` is protected by both an Import Linter forbidden-import
   contract and an independent AST dependency scan. A startup guard refuses
   model credentials in the runtime environment.
5. CI installs an exactly pinned development toolchain, runs the full pytest
   suite, checks the A1 import boundary, and compiles source plus contracts.

## Contract-by-contract report

| ID | Assertion | Failure prevented |
|---|---|---|
| G-01 | Full-history output at `t` is bit-identical to output from input truncated at `t` | Smoothed/future-aware estimates masquerading as filtered estimates |
| S-04 | Sharpe uncertainty accepts Pearson non-excess kurtosis and reduces to the Gaussian special case | Understated Sharpe error and inflated PSR/DSR |
| K-02 | Every checked run emits `cap_binding_fraction`; values above 25% fail unless explicitly acknowledged | Silent conversion from volatility targeting to constant leverage |
| Q-02 | VaR is a positive loss and cannot exceed CVaR | Risk-limit sign inversion |
| Q-08 | Cornish-Fisher quantiles must be non-decreasing; otherwise historical quantiles are returned | Smaller loss estimates at higher confidence |
| V-08b | Range variance requires prints-per-bar plus a sourced correction factor, otherwise it refuses to return a value | Finite-print downward bias and resulting over-leverage |
| V-12 | Lo autocorrelation correction is the primary annualized Sharpe; square-root scaling is labelled diagnostic output | Autocorrelation-driven Sharpe inflation |
| V-14 | Accounting compounds each realized simple return | Treating the continuous-time approximation as a discrete P&L identity |
| S-14 | PBO serialization requires a bootstrap interval and at least 20 replicates | Promotion on a noisy scalar PBO draw |

E-03 is deliberately not a runtime contract. The report measured a worst
objective penalty of roughly `9.8e-09`, and neither M0 nor M1 consumes an
Almgren-Chriss scheduler. Adding execution-schedule machinery now would violate
the charter's pull-only infrastructure rule. If a later milestone consumes the
approximation, its fine-grid and impact assumptions must become executable at
that boundary.

## What is not fully mechanically enforceable

- A library contract cannot prove that every future estimator or backtest calls
  it. Each M1 consuming boundary needs an integration test that deliberately
  violates the invariant and proves the complete run fails.
- `prints_per_bar` and a discretization factor can be required, but software
  cannot prove the factor is empirically calibrated or its source is credible.
- A bootstrap interval can be required, but the generic report type cannot prove
  that the resampling design is statistically appropriate for the later PBO
  implementation.
- The A1 dependency rule can ban known clients and all current transitive paths,
  but no finite denylist can name an inference client that does not exist yet.
  Network egress allowlisting and container credential separation remain M5/M6
  deployment controls.
- Local hash chaining is tamper-evident, not malicious-operator-proof. An
  operator with filesystem control could replace both the ledger and its head
  checkpoint. Remote signed or WORM anchoring is the later hardening path.
- A2 cannot be self-certified by the implementation author. This report and its
  tests still require adversarial review by a different-vendor model.

## Specification conflict resolved by CIO ruling

A10 permits dated amendments appended to a frozen preregistration, while P1
requires `verify_frozen(path)` to fail if that path ever has a Git modification
commit. Appending to the same Markdown file necessarily produces such a commit.
On 2026-08-11 the CIO approved the separate-ledger resolution. M0 therefore
implements the stricter P1 rule: frozen text cannot change at all. Amendments
are new dated events in `AmendmentLedger`, which is append-only, hash-chained,
bound to the annotated preregistration tag, and protected against tail
truncation by a separate head checkpoint. An amendment cannot retroactively
rescue an evaluated trial; an affected configuration must be registered anew.
