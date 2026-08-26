# Vertical Slice 01 — Charter

**Purpose.** Convert a verified research *process* into a verified research
*result*. One hypothesis, one universe, one baseline, real point-in-time data,
pre-registered evaluation, and a written postmortem whether it lives or dies.

**This is own-capital research.** Managing outside money triggers RIA
registration (state below ~$100M AUM, SEC above) and typically Series 65; for
futures or pooled vehicles, CTA/CPO registration with NFA/CFTC. Nothing in this
charter is investment advice. Do not accept outside capital without taking
professional advice first.

**Non-goal.** Building a platform. Infrastructure gets built only when this
slice blocks on it, and only as far as this slice consumes it.

---

## 0. The one-paragraph version

We test whether scaling exposure to a single liquid equity index ETF inversely
to a forecast of its conditional volatility beats simply holding it, net of
realistic costs including margin financing, over a fixed post-decimalization
sample beginning 2003-09-10, under purged walk-forward evaluation with every
configuration counted in a trial registry. The hypothesis, the cost model, the
evaluation protocol, and the kill thresholds are frozen in git before any price
data is loaded. The
answer may well be "no". A clean, costed, pre-registered "no" is a successful
outcome of this slice.

---

## 1. The hypothesis

### 1.1 Statement

> **H1.** Scaling exposure to a broad US equity index inversely to a forecast
> of its conditional volatility produces a higher Sharpe ratio, net of all costs
> including financing, than a constant fully-invested position in the same
> index, over the same sample.

Formally, with $w_t = \min\!\left(L,\ \dfrac{\sigma^*}{\hat\sigma_{t}}\right)$
where $\hat\sigma_t$ is a **causal** forecast of next-period volatility formed
strictly from information available at $t$:

$$\text{SR}_{\text{net}}\big(w_t r_{t+1}\big) > \text{SR}_{\text{net}}\big(r_{t+1}\big)$$

### 1.2 Why it might be true (the mechanism)

This is the part that makes it a hypothesis rather than a data-mine. Three
links, two of which are already verified in the existing suite:

1. **Volatility is persistent and forecastable.** Verified: GARCH(1,1)
   persistence $\alpha+\beta=0.98$ implies a variance half-life of ~34 trading
   days (V-02); the RiskMetrics EWMA half-life is 11.2 days (V-04). Tomorrow's
   variance is genuinely predictable in a way tomorrow's return is not.
2. **Expected return is not proportional to conditional variance** at these
   horizons. The time-series risk–return trade-off is weak-to-flat. If true,
   then risk rises in high-volatility regimes without commensurate compensation.
3. **Therefore** $1/\hat\sigma$ scaling raises exposure when reward-per-unit-
   risk is high and cuts it when low, improving the ratio.

There is also a purely mechanical contribution: reducing realised volatility
raises compound growth via reduced variance drain — verified at **3.78 pp/yr**
for a 30% → 12% volatility reduction at unchanged arithmetic mean (V-15).

Primary reference: Moreira & Muir (2017), *Volatility-Managed Portfolios*,
*Journal of Finance* 72(4):1611–1644.

### 1.3 Why it might be false (pre-register the counter-case)

State this **before** looking, so a negative result cannot be rationalised away:

- **The published result is contested, and the counter-case is strong.**
  Cederburg, O'Doherty, Wang & Yan (2020), *Journal of Financial Economics*
  138(1):95–117, examine 103 equity strategies and find vol-managed portfolios
  **do not systematically outperform their unmanaged counterparts in direct
  comparison**. Their objection is methodological: the positive alphas come
  from *spanning regressions* whose implied strategies are **not implementable
  in real time**, and honest out-of-sample versions generally earn *lower*
  certainty-equivalent returns and Sharpe ratios than the unmanaged portfolio.
  **This is the same defect class as G-01** — a full-sample regression sets the
  scaling using information the trader did not have, exactly as a smoothed
  state probability does. Treat this as the falsifying prior: the strongest
  published evidence predicts this hypothesis fails. The scaling rule must be
  strictly causal, and the baseline must be the unmanaged portfolio at matched
  ex-post volatility — the comparison Cederburg et al. show is usually lost.
- **It may be a crisis-alpha artifact.** If the entire effect is 2008 and 2020,
  it is two observations, not an edge. Pre-register a leave-one-crisis-out test.
- **Financing may eat it.** The strategy demands leverage in calm regimes. At
  retail margin rates this is not a rounding error — see §4.3. This is the most
  likely single cause of death and must be modelled, not assumed away.
- **The estimator lags breaks.** Verified: EWMA carries a median **2.4×**
  leverage into a regime break, and a 2σ storm day then costs **21.6% of
  capital in one session** (K-03). The strategy is structurally short gap risk.
- **The leverage cap silently changes the strategy.** Verified: when the cap
  binds, realised volatility falls below target and the strategy becomes
  constant-leverage, not vol-targeted (K-02). If the cap binds most of the time,
  we are not testing H1 at all.

### 1.4 Universe

**SPY**, daily, 2003-09-10 through the fixed pre-registration end date. One
instrument. The 1993-01-29 through 2003-09-09 period is reserved for a
separately licensed, separately frozen, one-time earlier-regime robustness
analysis using the primary-selected configuration; it is never pooled into the
primary result. Robustness replication on **IVV** and **VOO** requires a new
pre-registration after the primary result is frozen.

Rationale for a single instrument: it is the narrowest possible slice; it makes
survivorship bias structurally absent; and volatility management is a
time-series operation that needs no cross-section.

### 1.5 Baselines (the things to beat)

Three, in increasing order of difficulty. H1 must beat **all three**.

| # | Baseline | Why it is here |
|---|---|---|
| B1 | Buy and hold SPY, same costs | The investable alternative |
| B2 | Constant leverage at the strategy's *ex-post average* exposure | Removes "it just levered up" as an explanation |
| B3 | Constant leverage scaled to match the strategy's *ex-post realised volatility* | The scale-free comparison; isolates timing from sizing |

**B3 is the honest test.** A vol-managed strategy has different average exposure
than buy-and-hold, so a raw return comparison is meaningless. Report Sharpe
(scale-free) *and* return at matched ex-post volatility.

---

## 2. Phases and gates

Each phase has a deliverable and an explicit gate. **Do not start phase $n+1$
until phase $n$'s gate is met.** Gates are pass/fail, not judgement calls.

### Phase 0 — Pre-registration `[BLOCKS EVERYTHING]`

Write `PREREGISTRATION.md` (template in §5), fill it completely, commit, and
tag it:

```bash
git add Docs/slice-01/PREREGISTRATION.md
git commit -m "prereg: slice-01 frozen before data load"
git tag -a slice-01-prereg -m "frozen $(date -u +%FT%TZ)"
git rev-parse slice-01-prereg   # record this hash in the final writeup
```

**Gate.** The tag exists, and `git log --diff-filter=M -- Docs/slice-01/PREREGISTRATION.md`
is empty at the end of the project. Any amendment must be a *new, dated,
appended section* explaining what changed and why — never an edit to the frozen
text. Amendments are allowed; silent amendments are not.

### Phase 1 — Caveats become executable contracts

Turn the nine FLAG findings into a `contracts/` package of runtime assertions
and property tests. These run in CI and in the backtest, not just in review.

| Finding | Contract to implement |
|---|---|
| **S-04** | `sharpe_standard_error()` asserts $\gamma_4\approx3$ on Gaussian input and reduces to $\sqrt{1+SR^2/2}$; kurtosis is non-excess by construction |
| **K-02** | Backtest emits `cap_binding_fraction`; run **fails** if > 25% without an explicit acknowledgement flag |
| **Q-02** | One VaR sign convention, asserted: `VaR > 0` and `VaR <= CVaR` |
| **Q-08** | Cornish–Fisher quantile asserted non-decreasing in confidence; falls back to historical simulation when it trips |
| **G-01** | **Causal recomputation test**: signal at $t$ is bit-identical when input is truncated at $t$. Applies to every estimator in the pipeline |
| **V-08b** | Volatility estimators log prints-per-bar and apply (or refuse) a discretisation correction |
| **V-12** | Annualisation uses the Lo (2002) autocorrelation correction; naive $\sqrt{252}$ is a separate, labelled diagnostic |
| **V-14** | Growth is computed by compounding realised returns; $\mu-\tfrac12\sigma^2$ is never used for accounting |
| **S-14** | PBO is reported as a bootstrap interval, never a point estimate |
| **E-03** | (No action; documented as immaterial — objective penalty $\sim10^{-8}$) |

**Gate.** `pytest contracts/` green. **G-01's causal recomputation test is the
non-negotiable one** — it is the single test that would have caught the largest
error class found so far.

### Phase 2 — Point-in-time data with documented lineage

For a single surviving ETF, survivorship bias is absent — but **restatement
bias is not**, and it is the trap here:

> Every vendor's *adjusted close* series is retroactively rewritten on each new
> dividend. A backtest run today sees a different price history than the same
> backtest run last year. That is a look-ahead you cannot see.

Therefore:

- Store **raw OHLCV** plus **dividend and split events with their ex-dates and
  announcement dates** as separate immutable tables.
- Reconstruct total-return series **as of** a given date, from events known at
  that date. Never store a pre-adjusted series as the source of truth.
- Every table carries: vendor, retrieval timestamp, vendor's own
  as-of/vintage field if any, and a SHA-256 content hash.
- A `manifest.json` records the hash set for each backtest run. **A run that
  cannot name its data hashes is not a result.**

Selected vendor: **Polygon.io / Massive** for raw OHLCV and corporate actions.
Its dividend records separately expose declaration, ex-dividend, record, and
pay dates. Source bars must be requested with `adjusted=false`. The current
Starter plan is $29/mo for five years; Advanced is $199/mo, but Massive's full
daily archive begins in September 2003 and therefore does not cover SPY's
1993-2003 history. The CIO fixed the primary sample to begin on 2003-09-10
rather than splice a second vendor or apply a modern cost model to the
pre-decimalization tick regimes. **ALFRED** is also selected for genuinely vintage-aware macro
and financing inputs, always with explicit real-time/vintage parameters.
**yfinance is prototyping only** — personal-use terms, unofficial,
rate-limited, and not point-in-time. See `DATA_SOURCE_DECISION.md` for the
license and historical-quote-access gates that must be resolved before this
pre-registration can freeze.

**Gate.**
1. `test_no_future_data`: for a random sample of 200 as-of dates, the
   reconstructed series contains no event with ex-date > as-of date.
2. `test_reproducible`: same manifest hash ⇒ byte-identical series.
3. A written `LINEAGE.md`: where each field came from, what was adjusted, what
   was discarded, and known vendor quirks.

### Phase 3 — Cost model, calibrated not assumed

Costs are where this hypothesis most plausibly dies, so they are built **before**
the signal and they are deliberately pessimistic.

| Component | Treatment |
|---|---|
| Spread | Half-spread × turnover, calibrated from actual SPY quoted spreads; do **not** use a flat guess |
| Commission | **IBKR Pro Tiered**, including the $0.35 whole-share order minimum, pass-through fees, and the separate fractional-share rule at $2,000-$2,500 NAV |
| Impact | Square-root law, $Y\sigma_{\text{daily}}\sqrt{Q/V}$. Verified negligible at retail size (**0.18 bp** on $10k in SPY, E-09) — include it anyway so it scales |
| **Financing** | **The one that matters.** Margin borrowing at the actual broker rate when $w_t>1$; interest earned on cash when $w_t<1$. Use the historical broker-call/Fed-funds+spread series, not a constant |
| Slippage | Modelled as execution at MOC/next-open with a pre-registered adverse assumption |
| Taxes | Out of scope; state this explicitly in the writeup |

**Gate.** A one-page `COSTS.md` deriving every number from a source, plus a
sensitivity table showing the strategy's net Sharpe at 0.5×, 1×, and 2× the
assumed cost level. **If the result flips between 1× and 2×, it is not a result.**

### Phase 4 — Baselines first

Implement and fully evaluate B1, B2, B3 **before** the signal exists in code.
This ordering matters: it prevents the baseline from being quietly weakened to
make the strategy look better.

**Gate.** Baseline equity curves reproduce published SPY total return to within
a stated tolerance over matched windows. If you cannot reproduce buy-and-hold,
nothing downstream is trustworthy.

### Phase 5 — The signal, under purged walk-forward

- **Estimators:** EWMA($\lambda$), GARCH(1,1), realised variance over a lookback,
  and a range-based estimator (Rogers–Satchell — the only drift-independent one,
  V-09). All strictly causal, all subject to the G-01 contract.
- **Walk-forward:** expanding window, purged, with embargo. No parameter is ever
  fitted on data used for evaluation.
- **Trial registry:** every configuration ever evaluated is written to an
  append-only log with a timestamp and a hash — **including abandoned ones**.
  $N$ is read from the registry, not chosen. An understated $N$ makes the
  deflation worthless while appearing to work.
- **Deflation:** DSR using the registry's $N$; PBO via CSCV reported as a
  bootstrap interval (S-14).
- **Significance vs baseline:** Ledoit–Wolf (2008) robust Sharpe-difference
  test, which is valid under autocorrelation and non-normality — not a naive
  $t$-test on overlapping returns.

**Gate.** Every number in the results table traces to a registry entry and a
data manifest hash.

### Phase 6 — The decision gate

Thresholds are **read from `PREREGISTRATION.md`**, not chosen now. Suggested
defaults to fill in at Phase 0:

- Net Sharpe exceeds **all three** baselines, and
- Deflated Sharpe Ratio > 0.95 at the registry's $N$, and
- PBO 95% interval upper bound < 0.5, and
- Ledoit–Wolf Sharpe-difference $p$ < 0.05 vs B3, and
- Result survives leave-one-crisis-out (drop 2008, drop 2020, drop both), and
- Result survives the 2× cost sensitivity, and
- `cap_binding_fraction` < 25%.

**Any single failure ⇒ the slice is a documented negative result.** Go to
Phase 8. Do not tune. Do not add a filter. Do not extend the universe. That is
the goalpost-moving the review warned about, and the pre-registration exists
precisely to make it visible.

### Phase 7 — Paper trading (only if Phase 6 passes)

Minimum **three months**, deterministic, with:

- Daily reconciliation: internal positions vs broker positions, diffed and
  logged. Any mismatch halts.
- Live-vs-backtest tracking error monitored with a CUSUM chart against a
  pre-registered band.
- Full order state machine with idempotency keys and persisted transitions;
  halt state stored **outside** process memory.
- Every fill compared against the modelled cost. **Realised slippage vs modelled
  slippage is the headline number** — it is the first honest measurement of
  whether the Phase 3 cost model was fiction.

**Gate.** Tracking error inside band, zero unexplained reconciliation breaks.

### Phase 8 — Postmortem `[MANDATORY, EITHER OUTCOME]`

`POSTMORTEM.md` containing: the frozen pre-registration hash; what was
predicted; what happened; every configuration in the registry with $N$; where
the cost model was wrong; what would have to be true for the opposite
conclusion; and what the next slice should be.

**A negative result written up this way is a stronger portfolio artifact than a
positive result without one.** It is the thing almost no retail quant has.

---

## 3. What "done" looks like

A reviewer should be able to run one command, get the same numbers, and read one
document that says what was predicted and what happened:

```
Docs/slice-01/
  PREREGISTRATION.md      frozen, tagged, hash recorded
  LINEAGE.md              where every datum came from
  COSTS.md                every cost derived from a source
  RESULTS.md              generated, never hand-edited
  POSTMORTEM.md           what was predicted vs what happened
src/slice01/
  contracts/              the nine caveats, executable
  data/                   PIT loader, as-of API, manifest hashing
  costs/                  calibrated cost model
  signals/                causal volatility estimators
  eval/                   purged walk-forward, registry, DSR, PBO, LW test
  backtest/               thin; baselines first
out/
  registry.jsonl          append-only, every trial
  manifest.json           data hashes per run
```

---

## 4. Sequencing rules

1. **Pre-registration before data.** Non-negotiable.
2. **Contracts before signals.** Phase 1 before Phase 5.
3. **Costs before strategy.** Phase 3 before Phase 5.
4. **Baselines before the thing being tested.** Phase 4 before Phase 5.
5. **Writer is never sole reviewer.** Implementation and adversarial review use
   different models from different vendors.
6. **No LLM in the execution path, ever.** Agents write and review the system;
   they never run inside it at trade time.
7. **Infrastructure is pulled, not pushed.** Build it when the slice blocks on
   it. If you cannot name the phase that consumes it, do not build it.

---

## 5. `PREREGISTRATION.md` template

Copy this, fill every field, commit, tag. Leave nothing as "TBD".

```markdown
# Slice 01 Pre-Registration
Frozen: <UTC timestamp>   Git tag: slice-01-prereg

## 1. Hypothesis
H1 (one sentence, falsifiable):
Mechanism (why it should be true, 3 links):
Prior belief it is true, before looking (a number, 0-1):

## 2. Data
Instrument:            Vendor:            Sample start/end:
Point-in-time method:
What I will do about restatement bias:

## 3. Signal specification
Estimators to be tried (EXHAUSTIVE LIST — anything added later is an amendment):
Parameter grids (EXHAUSTIVE):
Implied trial count N:
Rebalancing frequency:      Execution assumption:
Volatility target sigma*:   Leverage cap L:

## 4. Costs
Spread:      Commission:      Impact:
Financing (long AND short of 1x):
Sensitivity levels to be reported:

## 5. Baselines
B1:   B2:   B3:
Comparison metric (scale-free AND matched-volatility):

## 6. Evaluation protocol
Walk-forward scheme:    Purge length:    Embargo length:
Deflation method and where N comes from:
Significance test vs baseline:
Robustness: leave-one-crisis-out periods:

## 7. Decision thresholds (FILL IN NUMBERS NOW)
Proceed to paper trading only if ALL of:
  - [ ] Net Sharpe > B1, B2, B3
  - [ ] DSR > ____
  - [ ] PBO 95% upper bound < ____
  - [ ] LW Sharpe-difference p < ____ vs B3
  - [ ] Survives leave-one-crisis-out
  - [ ] Survives ____x cost sensitivity
  - [ ] cap_binding_fraction < ____

## 8. Stopping rules
I will abandon this slice if:
I will NOT do the following to rescue a negative result:
  - add instruments        - add filters/overlays
  - change the sample      - change the baseline
  - change sigma* or L after seeing results

## 9. What would change my mind
If the result is positive, the most likely non-edge explanation is:
If negative, what I would want to test next:
```

---

## 6. Honest expectations

Set these now, in writing, so the outcome cannot be reinterpreted later.

- The report's own §4.8 estimate — most retail systematic strategies that
  survive honest validation land at **net Sharpe 0.3–0.8** — applies here.
- Verified S-11: at a true Sharpe of 0.5 it takes **11 years** of live data to
  be 95% confident the strategy is not noise. **Live P&L will never be the
  arbiter on a solo timescale.** The ex-ante controls carry the weight; paper
  trading validates *execution*, not *edge*.
- Verified S-08/S-09: with 1,000 trials the null expects a maximum Sharpe of
  **3.26** from pure noise, rising to **4.39** at $10^5$. This is why the
  registry counts everything, and why a small pre-registered grid is a feature.
- The most likely outcome is that vol-management improves the *ratio* modestly
  and that financing costs consume much of it. That is a real finding. Write it
  up.
