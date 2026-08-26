# CIO Decision Record

This file records human decisions that constrain future work. It is not a
substitute for a frozen sleeve pre-registration, and no entry here authorizes a
strategy to pass a promotion gate.

## D-001 — Separate amendment ledger

- **Date:** 2026-08-11
- **Decision:** Approved.
- **Rule:** A frozen `PREREGISTRATION.md` is never edited. Every amendment is a
  new dated event in a separate append-only, hash-chained companion ledger.
- **Implementation:** `fund.prereg.AmendmentLedger` binds every event to the
  frozen document's repository path, annotated Git tag, and tag hash. The
  adjacent head checkpoint detects tail truncation.
- **Consequence:** An amendment changes the prospective specification from its
  effective time forward. It does not rewrite or rescue an already evaluated
  trial. Any affected configuration must be registered as a new trial.

## D-002 — Milestone M1 hypothesis

- **Date:** 2026-08-11
- **Decision:** Keep the vol-managed SPY sleeve.
- **Scope:** This chooses the hypothesis family and instrument only. The exact
  estimator list, grid, data vintage, costs, thresholds, and stopping rules
  remain unset until the M1 pre-registration is completed and frozen.

## D-003 — Broker and execution integration target

- **Date:** 2026-08-11
- **Decision:** Interactive Brokers (IBKR).
- **Scope:** IBKR is the paper/live broker integration target. This does not
  select the historical point-in-time market-data vendor.
- **Boundary:** IBKR connectivity, orders, reconciliation, risk, and allocation
  are deterministic code. Model credentials and LLM calls are forbidden from
  that dependency path.

## D-004 — M1 data sources

- **Date:** 2026-08-12
- **Decision:** Start with Polygon.io, now branded Massive, rather than Tiingo.
- **Reason:** The current dividends endpoint exposes `declaration_date`,
  `ex_dividend_date`, `record_date`, and `pay_date` separately. Raw OHLCV will
  be requested with `adjusted=false`; corporate actions remain separate source
  tables.
- **Macro vintages:** Add ALFRED through the FRED API. Every query must set an
  explicit real-time period or vintage date; the API default is current-vintage
  FRED behavior, not an historical ALFRED view.
- **Exclusion:** `yfinance` remains prototyping-only. It is not an admissible M1
  source, manifest input, baseline source, or gap-fill mechanism.
- **Current price/coverage check:** Stocks Starter is $29/month with five years
  of history; Developer is $79/month with ten years; Advanced is $199/month
  with all Massive stock history, whose daily aggregate archive begins in
  September 2003. These are individual-use prices checked on 2026-08-12.
- **Consequence:** Starter is suitable for building the ingestion contract and
  fixtures, but cannot support the complete primary evaluation. The CIO later
  selected a primary start of 2003-09-10 in D-006; Massive licensing remains a
  written pre-freeze gate.

## D-005 — Initial capital band

- **Date:** 2026-08-12
- **Decision:** $2,000-$2,500 of own capital.
- **Cost consequence:** IBKR per-order minimums, fractional-share treatment,
  margin financing, and cash interest must be modelled at this account size,
  not borrowed from the report's $10,000 illustration.
- **Risk consequence:** $2,000 is the regulatory minimum equity ordinarily
  required before using margin. The lower end therefore has no operating
  cushion for a leveraged daily-rebalanced strategy. Paper trading can proceed
  at a simulated $2,000-$2,500 NAV, but live leverage requires a separate human
  approval after the broker confirms account eligibility and requirements.

## D-006 — Slice 01 primary and secondary sample

- **Date:** 2026-08-12
- **Decision:** Shorten the primary SPY sample to 2003-09-10 through the fixed
  pre-registration end date. Do not splice a second vendor into the primary
  result.
- **Reason:** Massive's single-vendor archive begins on 2003-09-10, and the
  pre-2001 fractional tick regimes require materially different spread and
  execution-cost models. Applying a modern cost model to 1993-2001 would violate
  A9 more seriously than using a shorter primary sample.
- **Secondary analysis:** Reserve 1993-01-29 through 2003-09-09 for a separately
  licensed, separately frozen, one-time regime-robustness analysis. It must use
  the primary-selected configuration, its own era-appropriate costs, and be
  reported beside rather than pooled with the primary sample. It is not a
  forward holdout.

## D-007 — IBKR account plan assumption

- **Date:** 2026-08-12
- **Decision:** Use IBKR Pro Tiered as the historical-cost and paper/live
  integration assumption. Research uses the ordinary posted U.S. account
  schedule; the legal account type remains a separate pre-live CIO decision.
- **Cost consequence:** Model the current $0.0035-per-share first tier, $0.35
  whole-share order minimum, pass-through fees, and the separate fractional
  order rule explicitly. Do not silently substitute IBKR Lite's zero headline
  commission.
- **Routing consequence:** Pro provides SmartRouting and avoids making an
  auction-order research design depend on Lite's routing and special fee
  conditions.

## Inputs still required before the real M1 freeze

- Written confirmation that the chosen Massive plan permits this non-display,
  own-capital backtest and immutable research storage.
- Confirmation that the selected Massive access includes the historical NBBO
  data required by the frozen spread rule, or a written license for a named
  alternative quote source before freezing.
- A per-series ALFRED snapshot/reproducibility policy. DFF is tagged public
  domain with citation requested, but each additional series must pass the same
  copyright-note check before admission.
- Independent different-vendor validation of M0 (A2).
