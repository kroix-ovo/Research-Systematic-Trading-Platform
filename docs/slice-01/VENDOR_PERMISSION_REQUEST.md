# Massive / Polygon Written-Permission Request

**Purpose:** obtain a written answer that can be hashed into Slice 01 lineage
before buying or downloading data. This is a draft for the CIO to send through
Massive's sales or support channel; it has not been sent by an agent.

## Subject

Written permission for personal own-account backtesting and immutable research
snapshots

## Message

Hello,

I am an individual researching a daily SPY strategy solely for trading my own
capital. I will not redistribute, display, resell, sublicense, or provide the
raw data or derived signals to another person. Before I subscribe or download
anything, I need written confirmation of the license that applies to this use.

Please answer each item separately and identify the plan or agreement required:

1. **Historical research/backtesting.** May I use Massive U.S. stocks data,
   including unadjusted daily OHLCV, historical NBBO quotes, and SPY corporate
   actions, to backtest a strategy solely for my personal own-account trading?
2. **Non-display and derived use.** May deterministic code calculate and retain
   private volatility forecasts, target positions, backtest results, and other
   derived signals from that data for my own-account trading, without exposing
   them to any third party?
3. **Immutable reproducibility storage.** May I retain the exact raw responses
   or flat-file rows used by a backtest, together with their SHA-256 hashes,
   indefinitely for private audit and reproducibility after a subscription ends?
   If not, what retention or deletion rule applies, and may I retain only hashes,
   manifests, and derived non-reversible results?
4. **Historical entitlement.** Which plan or agreement provides end-of-day
   access to SPY unadjusted daily bars and top-of-book/NBBO quotes from
   2003-09-10 through 2026-08-11? Is a one-time historical download permitted,
   and does access or retention change after cancellation?
5. **Automation.** May my private ingestion code retrieve these records through
   the REST API or flat files and store them in content-addressed local files,
   subject to the answer to item 3?

The project is not a fund offered to investors, an advisory service, a data
product, or a commercial application. Initial capital is $2,000-$2,500. If an
individual plan does not permit this use, please identify the least expensive
license that does and provide the applicable terms.

Please include the date, the legal entity granting permission, and any limits
or deletion obligations in the response. I will preserve the response in the
project's private audit record.

Thank you.

## Acceptance checklist

The Phase 0 license gate passes only if the written response clearly resolves:

- own-account historical backtesting;
- private non-display derived signals;
- raw snapshot retention after subscription termination;
- API or flat-file automation;
- 2003-09-10 through 2026-08-11 daily bars;
- historical NBBO or a named substitute usable by the frozen spread rule; and
- the exact plan, price, attribution, deletion, and cancellation conditions.

Silence, a generic link to terms, or a response that omits retention does not
pass. If immutable raw retention is forbidden, the fund charter's promise of a
permanent byte-identical rerun must be narrowed before the preregistration is
frozen; it cannot be silently assumed.

## ALFRED series admission policy

The primary preregistration names only FRED/ALFRED series DFF. Its current FRED
page identifies the Board of Governors as source and tags the series "Public
Domain: Citation Requested." The P3 connector must preserve the series notes,
source, units, frequency, retrieval timestamp, explicit `realtime_start` and
`realtime_end`, raw response hash, and suggested citation with every snapshot.

No additional FRED or ALFRED series is admitted merely because it is available
through the API. Before first retrieval, deterministic configuration must record
whether its notes contain a copyright notice and the source-specific use and
retention terms. A copyrighted or ambiguous series is refused until permission
is documented. This per-series rule is the reproducibility policy; there is no
blanket assumption that all FRED-hosted observations share one license.
