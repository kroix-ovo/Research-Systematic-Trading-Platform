# Slice 01 Data-Source Decision

**Decision date:** 2026-08-12  
**Status:** primary sample and sources selected; pre-registration draft written
but unfrozen; no price data has been loaded or inspected.

## Selected sources

1. **Polygon.io / Massive** is the primary SPY market-data and
   corporate-action provider.
2. **ALFRED**, accessed through the FRED API with explicit real-time/vintage
   parameters, is the macro and financing-vintage source.
3. **yfinance is prohibited beyond prototyping.** It may not feed a registered
   run, fill a vendor gap, validate a baseline, or appear in a manifest.

## Why Massive fits the P3 schema

The current [Dividends endpoint](https://massive.com/docs/rest/stocks/corporate-actions/dividends)
returns the announcement (`declaration_date`), `ex_dividend_date`,
`record_date`, `pay_date`, original cash amount, currency, distribution type,
and a vendor event id as separate fields. That is materially stronger for an
as-of reconstruction than a daily row containing only a cash-dividend factor.

The canonical source tables will preserve the raw payload and normalize at
least these fields:

| Table | Required normalized fields |
|---|---|
| `raw_ohlcv` | symbol, session date, unadjusted O/H/L/C, volume, VWAP if present, vendor, retrieval UTC, raw-payload SHA-256 |
| `dividend_events` | vendor event id, symbol, declaration date, ex-date, record date, pay date, cash amount, currency, distribution type, retrieval UTC, raw-payload SHA-256 |
| `split_events` | vendor event id, symbol, execution date, split-from, split-to, adjustment type, retrieval UTC, raw-payload SHA-256 |
| `alfred_observations` | series id, observation date, real-time start/end, value, units, retrieval UTC, raw-payload SHA-256 |

Massive aggregates are split-adjusted by default. Every source request must set
`adjusted=false`; the adjusted series returned by the vendor is never source of
truth. See the [Custom Bars documentation](https://massive.com/docs/rest/stocks/aggregates/custom-bars).

One schema gap remains explicit: the current [Splits endpoint](https://massive.com/docs/rest/stocks/corporate-actions/splits)
documents an execution date and ratio but not a split announcement date. SPY
must still be queried, and a zero-event response must be preserved and hashed;
the schema cannot pretend an announcement timestamp exists. If an event is
returned, Slice 01 needs a second source or a conservative written policy for
split `known_at` before reconstruction can proceed.

## Current pricing and history gate

The current [individual stock plans](https://www.massive.com/stocks), checked
2026-08-12, are:

| Plan | Monthly | History |
|---|---:|---:|
| Basic | $0 | 2 years |
| Starter | **$29** | 5 years |
| Developer | $79 | 10 years |
| Advanced | **$199** | all available / 20+ years |

The [daily flat-file archive](https://massive.com/docs/flat-files/stocks/day-aggregates)
begins on 2003-09-10. Therefore even Advanced cannot supply SPY history
beginning in 1993. The CIO fixed the primary sample to 2003-09-10 through
2026-08-11 so it can remain a single-vendor, post-decimalization test. Starter
is approved for contract development and schema validation only; its five-year
entitlement still cannot supply the complete primary evaluation dataset.

At $2,000-$2,500 of capital, Starter costs $348 per year, or roughly 13.9%-17.4%
of starting capital. Advanced costs $2,388 per year, or roughly 95.5%-119.4%.
Data subscriptions are research overhead rather than backtest trading costs,
but that economic mismatch rules out Advanced as a standing subscription at
the initial capital level.

## License gate

The current [Massive market-data terms](https://massive.com/legal/market-data-terms-of-service)
describe individual market data as personal/non-business and, absent written
consent or another agreement, restrict non-display and derived-strategy use.
This document does not interpret those terms. Before purchasing or ingesting,
obtain written confirmation from Massive that the intended own-capital,
non-redistributed backtest and immutable local snapshots are permitted under
the selected plan.

ALFRED is available through the free FRED API and is genuinely vintage-aware:
the [real-time-period documentation](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)
defines when information was known, and `vintage_dates` can request data as it
existed on specified historical dates. The current [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html)
also contain caching/archiving and third-party-series restrictions. P3 needs
immutable inputs, so the exact snapshot policy must be confirmed before the
connector writes source data.

## Why the primary sample now starts in 2003

The history gap is not merely a vendor seam. U.S. equity quoting used a minimum
increment of one eighth of a dollar before the NYSE's 1997 reduction to one
sixteenth, and full decimalization reduced the standard increment from one
sixteenth to one cent on 2001-04-09. Those regimes require different spread
floors and an independently sourced historical commission model. Applying a
modern penny-spread assumption to them would violate A9.

The primary M1 result therefore starts on Massive's 2003-09-10 archive boundary.
The 1993-01-29 through 2003-09-09 period is prospectively reserved for a
separately licensed and separately frozen analysis using the one configuration
selected by the primary test. It will be evaluated once, described as an
earlier-regime robustness test rather than a forward holdout, and reported
side-by-side rather than pooled.

## Capital-sensitive IBKR facts for P4

Current source checks establish the assumptions to investigate, not yet to
freeze:

- [IBKR Pro tiered commissions](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php)
  begin at $0.0035 per whole share with a $0.35 order minimum; fractional orders
  have a $0.01 minimum. Fixed pricing has a $1.00 order minimum.
- IBKR Lite lists $0 commissions for eligible U.S. retail accounts, but its
  schedule has a specific fee condition when OnClose, OnOpen, outside-hours, or
  sub-$1 order volume exceeds 10% of monthly U.S. stock volume. A daily MOC
  strategy cannot ignore that clause.
- [Current USD margin rates](https://www.interactivebrokers.com/en/trading/margin-rates.php)
  for balances below $100,000 are benchmark plus 1.5% for Pro and benchmark
  plus 2.5% for Lite. The displayed rates are time-varying and are not a valid
  historical constant.
- [FINRA's margin rule](https://www.finra.org/rules-guidance/rulebooks/finra-rules/4210?page=1)
  ordinarily requires $2,000 minimum equity before margin use. A $2,000 start
  has no cushion for a strategy that may require new daily commitments.

The CIO selected IBKR Pro Tiered. P4 must model its exact whole-share order
minimum, pass-through fees, historical financing proxy, and cash-interest
threshold at the $2,000-$2,500 NAV. The earlier $10,000 impact illustration is
not transferable. The primary preregistration uses whole-share orders and a
$350 minimum rebalance notional, making the $0.35 commission at most 10 bp of
each executed order; it repeats the primary protocol at $2,000 as robustness.

## Gates before Phase 0 can freeze

1. Obtain written Massive permission for own-account backtesting, non-display
   derived signals, and immutable local raw snapshots.
2. Confirm licensed access to the 2003-2026 historical NBBO observations used
   by the preregistered spread rule, or amend the draft before results with a
   named, licensed quote source.
3. Admit only ALFRED series whose notes and source rights permit the intended
   immutable snapshot. DFF is the named initial series and is tagged public
   domain with citation requested; other series are not implicitly approved.
4. Complete independent different-vendor M0 validation under A2.

No P3 connector or market-data download starts until these gates and the human
freeze of `PREREGISTRATION.md` are complete.
