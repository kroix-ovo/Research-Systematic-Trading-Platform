# Slice 01 Pre-Registration

Frozen: 2026-08-12T18:01:31Z   Git tag: slice-01-prereg

**Status:** complete draft awaiting the CIO's explicit freeze approval. The tag
above does not yet exist. No market-price data has been loaded or inspected in
preparing this document.

## 1. Hypothesis

H1 (one sentence, falsifiable): Over the fixed 2003-09-10 through 2026-08-11
sample, a strictly causal SPY strategy that scales next-session exposure
inversely to forecast conditional volatility will have higher net,
Lo-corrected Sharpe than each of B1, B2, and B3 after the specified IBKR Pro
Tiered trading, spread, impact, and financing costs; failure of any Section 7
gate falsifies Slice 01.

Mechanism (why it should be true, 3 links):

1. Conditional variance is persistent, so information through session \(t\)
   can forecast risk for session \(t+1\). Existing synthetic verification
   supports this link: V-02 gives a 34-trading-day GARCH variance half-life at
   \(\alpha+\beta=0.98\), and V-04 gives an 11.2-day EWMA half-life.
2. Expected next-session SPY return does not rise proportionally with its
   conditional volatility. This is the unverified economic link and the main
   empirical claim being tested; the verification suite supplies no support
   for it.
3. If links 1 and 2 hold, cutting exposure in forecast high-volatility sessions
   and restoring it in forecast low-volatility sessions reduces uncompensated
   variance and variance drain enough to improve net risk-adjusted return.
   V-15 supports only the variance-drain arithmetic, not the existence of a
   tradable edge.

Prior belief it is true, before looking (a number, 0-1): 0.25. The prior is
below one half because Cederburg, O'Doherty, Wang, and Yan (2020) find that
volatility-managed portfolios do not systematically outperform unmanaged
portfolios in direct comparisons and that reasonable real-time out-of-sample
versions generally have lower certainty-equivalent returns and Sharpe ratios.
Their identified structural instability, plus retail fixed commissions,
integer-share granularity, and financing, is the strongest counter-case.

## 2. Data

Instrument: SPDR S&P 500 ETF Trust, ticker SPY, U.S. regular-session daily data.
No IVV, VOO, futures, options, or constituent data are admissible in Slice 01.

Vendor: Polygon.io / Massive for unadjusted OHLCV, trades or quotes used for
cost calibration, and separately dated corporate actions; ALFRED through the
FRED API for vintage-aware DFF observations. Only a Massive agreement that
explicitly permits own-account backtesting, non-display derived signals, and
immutable local research snapshots is admissible. `yfinance` and adjusted-close
downloads are prohibited inputs.

Sample start/end: 2003-09-10 through 2026-08-11, inclusive. The first 756
eligible sessions are estimator warm-up and are not scored. All remaining
eligible sessions are the primary out-of-sample evaluation sample. The dates
are fixed even if a later vendor release adds earlier or later observations.

Point-in-time method: Store vendor payloads as immutable, content-addressed
tables. Store raw OHLCV with `adjusted=false`; store dividends and splits in
separate event tables with vendor id, retrieval UTC, declared or known-at date
when supplied, ex/execution date, pay and record dates when supplied, amount or
ratio, and SHA-256. Each run must name an immutable manifest. Reconstruct a
total-return series for `as_of` using only rows and corporate actions known by
that `as_of`; reject an unhashed source, an event dated after `as_of`, a missing
required date, and a revision not represented by a new content hash.

What I will do about restatement bias: Vendor-adjusted prices are never source
of truth. Total returns are reconstructed from the frozen raw bars and
corporate-action event vintages. For SPY dividends, `known_at` is the vendor's
declaration date and economic entitlement begins on ex-date. The executable
share ledger books a dividend receivable on ex-date for eligible whole shares,
includes that receivable in NAV, and transfers it to cash on pay date; it never
silently reinvests a fractional dividend. If a split is returned without an
announcement date, its `known_at` is its execution date, which is deliberately
conservative. A zero-event split response is retained and hashed. A rerun from
the same manifest must be byte-identical.

### Prospectively reserved pre-2003 secondary analysis

The 1993-01-29 through 2003-09-09 SPY period is not pooled into the primary
sample and cannot affect promotion. It is reserved for a one-time, side-by-side
regime-robustness analysis using only the single configuration selected by the
primary protocol. It is not a forward holdout; it tests earlier-regime
robustness. Net results are not directly comparable with the primary period and
will never be averaged with them.

No pre-2003 data may be loaded until a separate, frozen secondary registration
names a licensed raw-data source and its immutable-storage rights. That
registration must retain these cost floors: at least $0.125 quoted spread from
1993-01-29 through 1997-06-23, at least $0.0625 from 1997-06-24 through
2001-04-08, and at least $0.01 from 2001-04-09 through 2003-09-09, with
contemporaneous quoted spread used whenever wider. It must use an independently
sourced era-appropriate commission schedule and the same vintage-aware
financing rule. The selected primary configuration is evaluated exactly once.

## 3. Signal specification

Estimators to be tried (EXHAUSTIVE LIST — anything added later is an amendment):

1. EWMA of close-to-close squared log returns.
2. Gaussian quasi-maximum-likelihood GARCH(1,1) of close-to-close log returns.
3. Rolling close-to-close realised variance.
4. Rolling Rogers-Satchell variance from unadjusted regular-session OHLC.

Every forecast is the annualized square root of conditional variance and uses
only observations complete before the order session. Each estimator must pass
the G-01 bit-identical truncated-input contract. Forecasts that are non-finite
or non-positive cause the target to be cash and emit an error record; they are
not forward-filled.

Parameter grids (EXHAUSTIVE):

- EWMA decay \(\lambda\in\{0.90,0.94,0.97\}\); initialize from the first 63
  eligible squared returns and update once per completed session.
- GARCH(1,1): one specification, \(r_t=\mu+\epsilon_t\),
  \(h_t=\omega+\alpha\epsilon_{t-1}^2+\beta h_{t-1}\), Gaussian QMLE,
  \(\omega>0\), \(\alpha\ge0\), \(\beta\ge0\),
  \(\alpha+\beta\le0.999\). Refit on the expanding sample at each calendar
  quarter boundary and hold fitted parameters within the quarter. No alternate
  innovation distribution, optimizer, or rolling fit window is admissible.
- Close-to-close realised-variance lookback
  \(k\in\{10,21,63\}\) completed sessions.
- Rogers-Satchell lookback \(k\in\{10,21,63\}\) completed sessions.
- Annual volatility target
  \(\sigma^*\in\{0.10,0.125,0.15\}\).
- Gross leverage cap \(L\in\{1.0,1.5,2.0\}\). Caps above 1 are research and
  paper simulations only; live leverage remains prohibited until the M6 human
  gate.
- Target weight is \(w_t=\min(L,\sigma^*/\hat\sigma_t)\), bounded below by
  zero. No smoothing, overlay, stop-loss, return forecast, or circuit-breaker
  filter may be added to the research signal.

Implied trial count N: 10 estimator variants x 3 volatility targets x 3 caps =
90 primary candidate configurations. Cost sensitivities, the $2,000 capital
robustness run, baselines, crisis exclusions, errors, and abandonments are also
registered. DSR uses the actual cumulative fund registry count at report time,
never a hand-entered 90 and never a smaller number.

Rebalancing frequency: Evaluate once per eligible session. Round the target
position to the nearest whole SPY share, with exact half shares rounded toward
the lower absolute exposure. Trade only when the difference from the current
position has notional of at least $350 at the decision reference price. This is
the fixed L1 no-trade band: a $0.35 whole-share commission is then no more than
10 bp of order notional. No fractional-share order is allowed in the primary
test. Initial simulated NAV is $2,500; the entire protocol is repeated at
$2,000 as a non-selection robustness test.

Execution assumption: After session \(t\) closes, compute the target from data
available through \(t\), submit an IBKR-style market-on-close order for session
\(t+1\) before its cutoff, and apply the new position only to the
close-\(t+1\)-to-close-\(t+2\) return. The fill reference is the official
session-\(t+1\) close plus an adverse half-spread and impact in trade direction.
No session's close is used to size an order executed at that same close.

Volatility target sigma*: exhaustive grid \(\{10\%,12.5\%,15\%\}\) annualized;
no target is privileged after results are observed.

Leverage cap L: exhaustive grid \(\{1.0,1.5,2.0\}\). If simulated equity is
below $2,000, target leverage above 1 is disallowed and the position is reduced
to at most 1 at the next eligible execution; the event is logged. Any broker
maintenance requirement that is stricter when P4 is sourced replaces this rule
only through a pre-evaluation amendment.

## 4. Costs

Spread: For each order, charge one half of the contemporaneous Massive NBBO
spread in the adverse direction using the last valid regular-session quote at
or before 15:50 ET on the execution date. If no valid quote exists within the
preceding five minutes, use the 95th percentile of valid 15:45-15:50 ET quoted
spreads over the preceding 21 eligible sessions; if that history is unavailable,
refuse the trade and register an error. Never infer spread from adjusted OHLC.
The same rule applies to strategy and rebalancing baselines.

Commission: IBKR Pro Tiered U.S. stock schedule, modeled as
\(\max(\$0.0035\times\text{whole shares},\$0.35)\) per order plus documented
exchange, clearing, regulatory, and pass-through fees. The fee schedule and its
retrieval date are manifest inputs. Because the primary test prohibits
fractional orders, the fractional-share 1%-of-trade-value rule is not blended
into the primary result.

Impact: Adverse square-root impact
\(Y\sigma_{d,t}\sqrt{Q_t/V_t}\) with \(Y=1\), order size \(Q_t\), same-day SPY
consolidated volume proxy \(V_t\), and the causal 21-session daily-volatility
estimate available before execution. \(V_t\) is always the trailing 21-session
median consolidated volume known before the order session; same-day completed
volume is not used. Impact is never set to zero merely because it is small.

Financing (long AND short of 1x): For exposure above 1, accrue a daily debit on
the borrowed cash using the point-in-time ALFRED DFF rate plus the current IBKR
Pro first-tier markup of 1.50 percentage points, using ACT/360 and the rate
known on that date. For exposure below 1, credit 0% because this $2,000-$2,500
account remains below IBKR's first-$10,000 interest threshold. There is no
securities short position. Borrowing and cash interest are accrued on calendar
days, including weekends and holidays, and posted to the next session.

Sensitivity levels to be reported: 0.5x, 1x, and 2x applied jointly to spread,
commission, pass-through fees, and impact; financing is always charged at 1x
because scaling an interest rate is not a plausible execution-cost scenario.
Taxes are outside scope and must be stated as such in `COSTS.md` and results.

## 5. Baselines

B1: Whole-share buy-and-hold SPY from the first scored execution through the
fixed end date, with the same initial NAV, initial execution cost, corporate
actions, and cash-interest rule. Cash dividends accumulate and are not given
free fractional reinvestment. This is the investable small-account alternative,
not the separate fractional curve used to validate data reconstruction.

B2: Constant non-negative exposure equal to the candidate strategy's ex-post
average daily gross exposure. It uses the same whole-share rounding, $350
no-trade rule, execution delay, costs, and financing. It is a diagnostic
ex-post comparator, not represented as a tradable real-time forecast.

B3: Constant non-negative exposure chosen from the exhaustive grid
\(\{0,0.001,0.002,\ldots,L\}\) to minimize absolute difference from the
candidate strategy's ex-post realized volatility; ties select lower exposure.
It must match within 1 annualized basis point or report the closest feasible
match and fail the B3 comparison gate. It uses the same whole-share rounding,
$350 no-trade rule, execution delay, costs, and financing. It is a diagnostic
ex-post comparator.

Comparison metric (scale-free AND matched-volatility): Primary metric is net
annualized Sharpe using Lo (2002) autocorrelation correction and a zero return
threshold. Also report CAGR and cumulative return for strategy and B1/B2/B3
after rescaling comparator returns to the strategy's ex-post realized
volatility. Naive square-root-of-252 Sharpe is diagnostic and explicitly
labelled only. All wealth paths compound realized net returns; the
\(\mu-\sigma^2/2\) approximation is prohibited for accounting. Separately, a
zero-cost fractional validation curve reinvests each distribution according to
the corporate-action ledger and is compared with State Street's published SPY
market-value total returns over exactly matched month-end 1-, 3-, 5-, and
10-year windows. That validation curve cannot enter a baseline or strategy
comparison.

## 6. Evaluation protocol

Walk-forward scheme: Use 2003-09-10 through the 756th eligible session only as
warm-up. Score all later sessions. Non-GARCH estimators update causally every
session without fitted hyperparameters. GARCH parameters refit at each calendar
quarter boundary on the expanding history ending before that quarter. The 90
fixed configurations are never selected or altered within a fold. At the end,
the single candidate with highest primary-sample net Lo-corrected Sharpe is the
reported candidate; ties within \(10^{-12}\) resolve by lower cap, lower target,
then the estimator order and parameter order printed in Section 3.

Purge length: 1 eligible trading session between the final observation used to
fit a GARCH parameter set and the first scored label of its evaluation block.

Embargo length: 1 eligible trading session after each evaluation block before
its observations may enter a later GARCH refit. The embargoed session can be
traded using the previously fitted model but cannot enter that refit.

Deflation method and where N comes from: Bailey and Lopez de Prado Deflated
Sharpe Ratio using non-excess kurtosis and Lo-corrected Sharpe inputs. The trial
count is queried from the append-only fund registry and includes every
evaluated, abandoned, and errored configuration across the fund. It must be at
least the 90 primary candidates. PBO is CSCV with 16 contiguous blocks and
10,000 master-seed bootstrap resamples and is reported only as a percentile
95% interval.

Significance test vs baseline: Ledoit-Wolf (2008) studentized time-series
bootstrap test of the strategy-minus-B3 Sharpe difference, one-sided alternative
greater than zero, 10,000 stationary-bootstrap resamples, expected block length
20 sessions, master seed 20260811. Report the unrounded p-value.

Robustness: leave-one-crisis-out periods: Re-evaluate the selected candidate
and its baselines after separately excluding 2007-10-01 through 2009-06-30
(global financial crisis), 2020-02-19 through 2020-06-30 (COVID shock), and
2022-01-03 through 2022-10-12 (inflation/tightening bear), then excluding all
three intervals together. Exclusion means remove those returns from scoring,
not from the causal estimator history. Survival requires the candidate's net
Sharpe to remain strictly above B1, B2, and B3 in every exclusion; significance
is not re-gated on the shorter samples.

## 7. Decision thresholds (FILL IN NUMBERS NOW)

Proceed to paper trading only if ALL of:

- [ ] Net Sharpe > B1, B2, B3
- [ ] DSR > 0.95
- [ ] PBO 95% upper bound < 0.50
- [ ] LW Sharpe-difference p < 0.05 vs B3
- [ ] Survives leave-one-crisis-out
- [ ] Survives 2x cost sensitivity
- [ ] cap_binding_fraction < 0.25

For the 2x gate, the selected candidate must retain net Sharpe strictly above
B1, B2, and B3 when the Section 4 scalable trading costs are doubled. For the
cap gate, `cap_binding_fraction` is the fraction of scored, signal-valid
sessions on which the unconstrained target exceeds \(L\). Failure of any one
box is a negative Slice 01 result and sends the sleeve to postmortem, not back
to research.

## 8. Stopping rules

I will abandon this slice if: Any Section 7 gate fails; data lineage or license
cannot support immutable reproduction; the separate fractional data-validation
curve differs from State Street's published SPY market-value annualized total
return by more than 10 basis points on any exactly matched month-end 1-, 3-,
5-, or 10-year window; any causality contract fails; any manifest mismatch
occurs; or implementation and different-vendor validation cannot resolve a
severity-1 finding. Abandonment is registered and followed by a postmortem.

I will NOT do the following to rescue a negative result: inspect a failed result
and then alter an estimator, parameter, cost, crisis window, data endpoint,
whole-share rule, no-trade threshold, promotion threshold, or tie-breaker. I
will not pool the pre-2003 secondary period into the primary series.

- add instruments
- add filters/overlays
- change the sample
- change the baseline
- change sigma* or L after seeing results

Any future scientific change creates a new sleeve and new trial count. A
factual correction required before evaluation uses the separate dated,
hash-chained amendment ledger and needs explicit CIO approval.

## 9. What would change my mind

If the result is positive, the most likely non-edge explanation is: understated
MOC execution cost or a corporate-action/as-of error, followed by winner's
curse across the 90 correlated candidates. A positive result is presumed buggy
until different-vendor validation reproduces truncation invariance, every cost
leg, registry count, and manifest hash.

If negative, what I would want to test next: First, no rescue of Slice 01. Write
its postmortem. Then consider a separately pre-registered sleeve selected for
low correlation to equity volatility timing, not a new SPY volatility filter.
The one-time pre-2003 analysis may still be run under its separate frozen
registration, but cannot reverse or average away the primary decision.

## Sources fixed at pre-registration

- Moreira and Muir, [Volatility-Managed Portfolios](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12513),
  *Journal of Finance* 72 (2017), 1611-1644.
- Cederburg, O'Doherty, Wang, and Yan,
  [On the Performance of Volatility-Managed Portfolios](https://www.lehigh.edu/~xuy219/research/COWY.pdf),
  *Journal of Financial Economics* 138 (2020), 95-117.
- Massive, [Stocks day aggregates](https://massive.com/docs/flat-files/stocks/day-aggregates)
  and [stocks quotes](https://massive.com/docs/flat-files/stocks/quotes), both
  documenting archive coverage beginning 2003-09-10.
- SEC, [Effects of decimal trading](https://www.sec.gov/rules-regulations/2001/07/request-comment-effects-decimal-trading-subpennies),
  documenting full U.S. equity decimalization on 2001-04-09 and the change from
  a 1/16-dollar to one-cent minimum quote increment.
- SEC, [Decimalization implementation order](https://www.sec.gov/rules-regulations/2000/01/order-directing-exchanges-national-association-securities-dealers-inc-submit-decimalization),
  documenting the 1997 move from eighths to sixteenths.
- Interactive Brokers, [U.S. stock commissions](https://www.interactivebrokers.com/en/pricing/commissions-stocks.php),
  [margin rates](https://www.interactivebrokers.com/en/trading/margin-rates.php),
  and [cash interest](https://www.interactivebrokers.com/en/accounts/fees/pricing-interest-rates.php).
- St. Louis Fed, [ALFRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html),
  [FRED API terms](https://fred.stlouisfed.org/docs/api/terms_of_use.html), and
  [DFF series notes](https://fred.stlouisfed.org/series/DFF).
- State Street, [SPY fund page and published performance](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy).
