# Agentic Research Fund — Architecture and Build Plan

**What this is.** A single-operator systematic research fund in which *agents
supply the labour* — hypothesis generation, implementation, adversarial review,
documentation — while every decision that touches money is made by
deterministic, verified, human-gated code.

**What this is not.** An AI that trades. No model runs inside the execution
path, ever. That boundary is the single most important structural decision in
this document, and §7 makes it physical rather than aspirational.

**Capital.** Own capital only. Managing outside money triggers RIA registration
(state regulator below ~$100M AUM, SEC above) and typically Series 65; pooled
vehicles or futures trigger CTA/CPO registration with NFA/CFTC. Nothing here is
investment advice. Do not take a dollar of anyone else's money without taking
professional advice first — that decision is out of scope for this build and
should stay out of scope until at least Milestone 5.

---

## 1. The idea in one page

A hedge fund is an organisation with six functions: research, portfolio
management, risk, execution, operations, and compliance. Most attempts at an
"AI hedge fund" try to replace the *decisions*. That is backwards, and the
existing verification work in `docs/report/` shows why: the errors that survive
review are silent ones — a mis-inverted recursion, a smoothed probability, a
wrong critical value — that produce a system which runs, looks plausible, and is
quietly wrong. Handing decisions to a stochastic system multiplies that class of
failure.

So invert it. Agents replace the **labour** in research and engineering, where
their output is cheap to verify and cheap to reject. Decisions stay in
deterministic code behind pre-registered gates.

| Fund function | Who does it here | Why |
|---|---|---|
| Research | **Agents**, under pre-registration | High volume, verifiable output, cheap to reject |
| Engineering | **Agents**, writer ≠ reviewer, different vendors | Same, plus model diversity catches shared blind spots |
| Validation | **Agents**, adversarial brief, different vendor | SR 11-7 "effective challenge" |
| Portfolio management | **Deterministic code**, no $\hat\mu$ | Verified: plug-in mean-variance destroys 99% of utility (P-03) |
| Risk | **Deterministic code**, pre-trade, outside strategy | Mirrors SEC 15c3-5 |
| Execution | **Deterministic code**, idempotent state machine | Knight Capital |
| Operations | Deterministic + agent triage | Reconciliation must never be judgement |
| Compliance | **The trial registry** (§6) | The fund's real control function |

The fund's actual competitive claim is not a signal. It is that **every result
it produces is pre-registered, costed, deflated against a cumulative trial
count, and reproducible from a seed.** That is rare, and it is what makes a
negative result publishable instead of discarded.

---

## 2. Design axioms

Each is a decision already forced by a verified finding in `docs/report/`. They
are not preferences and should not be relitigated per-sleeve.

| # | Axiom | Forced by |
|---|---|---|
| A1 | No LLM in the execution path | Report §4.2 AI-agent risk |
| A2 | Writer is never sole reviewer; reviewer is a different vendor | SR 11-7; the suite found 3 errors first-line review missed |
| A3 | Never allocate using estimated expected returns | **P-03**: plug-in MV realises Sharpe 0.15 vs 1.85 attainable; Ledoit–Wolf shrinkage does *not* fix it (0.15 → 0.16) because the error is in $\hat\mu$, not $\hat\Sigma$ |
| A4 | Allocation uses inverse-vol / ERC / HRP only | **P-07**: under roughly equal correlation, ERC *is* inverse-vol — no optimiser, no matrix inverse. **P-08**: HRP reshuffles 3.1× less than min-variance on identical distributions |
| A5 | Fund volatility target is derived from Kelly, not chosen | **K-11**: full Kelly targets portfolio vol numerically equal to Sharpe. **K-08**: fraction $c$ of Kelly yields $c(2-c)$ of maximum growth |
| A6 | Every estimator is causal, enforced by test | **G-01**: smoothed vs filtered inflated Sharpe 0.28 → 0.72 with no visual tell |
| A7 | Trial count is cumulative across the fund's entire life | **S-08/S-09**: $N=1{,}000$ ⇒ expected max Sharpe **3.26** from pure noise; $N=10^5$ ⇒ **4.39** |
| A8 | Live P&L is never the arbiter of edge | **S-11**: at true Sharpe 0.5, 95% confidence needs **11 years** of live data |
| A9 | Costs are pessimistic and sourced; financing is never assumed away | Retail margin rates are the most common silent strategy-killer |
| A10 | A pre-registration is immutable; amendments are appended and dated | The one mechanism that makes "we didn't move the goalposts" verifiable |

---

## 3. Organisation: agents as staff

Five desks. Three are agent-staffed; two are code and must never be.

```
                    ┌─────────────────────┐
                    │   YOU (CIO)         │  promotion gates, capital
                    │   human, accountable│  decisions, kill decisions
                    └──────────┬──────────┘
                               │
   ┌───────────────┬───────────┴───────────┬────────────────┐
   │               │                       │                │
┌──▼─────────┐ ┌───▼──────────┐   ┌────────▼──────┐ ┌───────▼────────┐
│ RESEARCH   │ │ ENGINEERING  │   │  VALIDATION   │ │  OPERATIONS    │
│ agents     │ │ agents       │   │  agents       │ │ code + triage  │
│            │ │              │   │  DIFFERENT    │ │                │
│ hypotheses │ │ implements   │   │  VENDOR       │ │ reconciliation │
│ preregs    │ │ slices       │   │  tries to KILL│ │ monitoring     │
│ lit review │ │ contracts    │   │  results      │ │ alerting       │
└────────────┘ └──────────────┘   └───────────────┘ └────────────────┘
                               │
        ═══════════════════════╪═══════════════════════  A1 BOUNDARY
                               │        no model crosses this line
   ┌───────────────┬───────────┴───────────┬────────────────┐
┌──▼─────────┐ ┌───▼──────────┐   ┌────────▼──────┐ ┌───────▼────────┐
│ ALLOCATION │ │  RISK        │   │  EXECUTION    │ │  REGISTRY      │
│ code only  │ │  code only   │   │  code only    │ │  append-only   │
│            │ │              │   │               │ │                │
│ inverse-vol│ │ pre-trade    │   │ order state   │ │ every trial    │
│ ERC / HRP  │ │ limits,      │   │ machine,      │ │ ever run,      │
│ no mu-hat  │ │ kill switch  │   │ idempotency   │ │ cumulative N   │
└────────────┘ └──────────────┘   └───────────────┘ └────────────────┘
```

### 3.1 Model routing per desk

| Desk | Model | Rationale |
|---|---|---|
| Research (hypotheses, preregs) | Frontier reasoning tier | Low volume, highest judgement content |
| Engineering (bulk implementation) | Cheap tier — DeepSeek V4 Flash / Qwen3-Coder / GLM plan | Highest volume; verified negligible cost |
| Validation (adversarial) | **Different vendor from Engineering** | A2 — model diversity on top of role separation |
| Test generation | Qwen3-Coder / Kimi K2.7 Code | Enumerates cases well, cheap |
| Anything touching a live signal, parameter, or P&L | **Self-hosted Qwen3-30B-A3B** | Zero data egress |
| Ops triage (log summarisation only) | Cheap tier, schema-validated output | Never proposes an action, only classifies |

**Rule:** hosted APIs are fine for generic and public code. Anything carrying
strategy logic, live parameters, or P&L runs on self-hosted weights.

### 3.2 The Validation desk's standing brief

This desk is the fund's edge and must be adversarial by construction. Its brief
is permanent and does not vary by task:

> Assume the result is wrong. Assume there is a look-ahead bug, a sign error, an
> off-by-one at a window boundary, or a cost that was not charged. Your job is
> to find it, not to approve it. Begin from: *this looks too good — why?*
> A result you cannot kill is the only result worth keeping.

---

## 4. The sleeve lifecycle

A **sleeve** is one strategy with one pre-registration. Sleeves move through a
state machine. Transitions are gated; there are no shortcuts.

```
  IDEA ──► PREREGISTERED ──► IN RESEARCH ──► GATED ──┬──► PAPER ──► LIVE
                                                     │              │
                                                     └──► KILLED ◄──┘
                                                          │
                                                          ▼
                                                     POSTMORTEM
                                                     (mandatory,
                                                      either path)
```

| State | Entry condition | Who decides |
|---|---|---|
| `IDEA` | A hypothesis with a stated causal mechanism | Research desk |
| `PREREGISTERED` | Prereg complete, committed, git-tagged, **before any data load** | You |
| `IN RESEARCH` | Contracts green; data lineage documented; costs sourced | Engineering |
| `GATED` | All pre-registered thresholds evaluated — pass *or* fail | Code, not judgement |
| `PAPER` | Passed gate; ≥3 months deterministic paper with reconciliation | You |
| `LIVE` | Paper tracking error inside band; zero unexplained breaks | You |
| `KILLED` | Any gate failure, or decommission trigger fires | Code, then you |
| `POSTMORTEM` | **Always**, from either terminal state | Research desk |

**The critical rule: a sleeve that fails its gate goes to `KILLED`, not back to
`IN RESEARCH`.** Re-entering research with a modified hypothesis is a *new*
sleeve with a *new* pre-registration and a *new* registry entry. This is what
stops goalpost-moving from being invisible, and it is why $N$ accumulates.

### 4.1 Sleeve admission test (for sleeves 2+)

A new sleeve must clear its own gate **and**:

- $|\rho|$ with the existing live portfolio $< 0.5$ over the evaluation window.
  A correlated sleeve adds trial count without adding diversification — it makes
  the fund worse on both axes.
- Its marginal contribution to portfolio risk is positive after costs.
- Capacity at your size, at its turnover, with its spread.

### 4.2 Decommissioning triggers (pre-registered per sleeve)

Written *before* going live, deterministic, not discretionary:

- Realised drawdown exceeds the pre-registered band
- Live-vs-backtest tracking error breaches its CUSUM threshold
- $N$ consecutive losing months, $N$ fixed in advance
- Signal-decay monitor fires
- The mechanism's premise is publicly falsified

---

## 5. Capital allocation — derived, not chosen

This section is short because the verified findings make most of it forced.

### 5.1 Across sleeves

Use **inverse-volatility** for $\le 6$ sleeves, **HRP** above that. Never
mean-variance with estimated returns (A3).

Justification, in order: P-03 shows plug-in MV realises Sharpe 0.15 against an
attainable 1.85 and that covariance shrinkage does not rescue it, because
expected returns need roughly two orders of magnitude more data than covariances
to estimate comparably (Merton 1980). P-07 shows that under roughly equal
pairwise correlation — the normal case for a handful of sleeves — ERC collapses
*exactly* to inverse-volatility, so the optimiser buys nothing. P-08 shows HRP
reshuffles 3.1× less than minimum variance across samples from an identical
distribution, and every unit of that difference is transaction cost paid for
estimation noise.

$$w_i = \frac{1/\hat\sigma_i}{\sum_j 1/\hat\sigma_j}$$

Constraints: long-only at fund level initially; 20% cap per instrument; gross
leverage $\le 1.0$ until Milestone 6 (avoids financing costs entirely and keeps
K-02's cap-binding pathology out of the system).

### 5.2 Fund-level volatility target

Derived from K-11 and K-08 rather than picked:

- K-11: full Kelly targets portfolio volatility **numerically equal to the
  Sharpe ratio**. $f^*\sigma = (\mu/\sigma^2)\sigma = \mu/\sigma = SR$.
- K-08: running at fraction $c$ of Kelly yields $c(2-c)$ of maximum growth.
- K-10: ten years of daily data leaves the Kelly fraction essentially
  unidentified — 5th–95th range $[-0.64, 4.69]$ around a true 2.00.

Therefore, with an honest fund Sharpe expectation of 0.3–0.8 (report §4.8):

| Expected fund Sharpe | Full-Kelly vol | **Quarter-Kelly target** | Growth retained |
|---:|---:|---:|---:|
| 0.3 | 30% | **7.5%** | 43.75% |
| 0.5 | 50% | **12.5%** | 43.75% |
| 0.8 | 80% | **20%** | 43.75% |

**Start at quarter Kelly.** This is not conservatism about markets; it is
correct sizing under the parameter uncertainty K-10 measures.

### 5.3 Rebalancing

Quadratic transaction-cost penalties do **not** produce a no-trade region — a
band requires a kinked (L1) cost, which is also the more faithful model since
real spreads and commissions are proportional. Either use an L1 objective or
impose an explicit band as a separate rule. Do not expect the band to fall out
of the algebra.

---

## 6. The trial registry — the fund's real compliance function

This is the piece that makes the whole thing defensible, and the piece almost
no retail operation has.

**One append-only log, fund-level, for the entire life of the fund.** Every
configuration ever evaluated, in any sleeve, including abandoned ones:

```jsonl
{"ts":"...","sleeve":"slice-01","prereg_hash":"...","config":{...},
 "data_manifest":"sha256:...","seed":20260811,"result":{...},"outcome":"evaluated"}
```

### 6.1 Two different multiple-testing problems (do not conflate them)

**Within a sleeve** — you selected the best of $N$ configurations, so use the
**Deflated Sharpe Ratio** with that sleeve's $N$ read from the registry.
Verified S-08: at $N=1{,}000$ the null expects a maximum Sharpe of 3.26.

**Across sleeves** — each admitted sleeve is a separate *discovery*, and you are
keeping the winners across many independent tests. That is a false-discovery-
rate problem, not a max-Sharpe problem. Use **Benjamini–Hochberg** across sleeve
$p$-values, not a second DSR.

Getting this backwards in either direction is a real error: applying DSR across
sleeves over-penalises genuine diversification, and ignoring FDR across sleeves
means the tenth sleeve is admitted on evidence that would not have admitted the
first.

### 6.2 Why $N$ must be cumulative

Because you will be tempted to reset it. A three-parameter grid at ten values is
1,000 trials before any variant selection; a fund that has run ten sleeves is
plausibly at $10^4$–$10^5$, where the null expects a maximum Sharpe of
**3.86–4.39** (S-09). Resetting $N$ per sleeve makes the deflation apparatus
appear to work while doing nothing.

**PBO is reported as a bootstrap interval, never a point estimate** — S-14
measured its null standard deviation at $\approx0.19$, so two honest runs on the
same worthless family can return 0.25 and 0.75.

---

## 7. Making axiom A1 physical

"No LLM in the execution path" is worthless as a policy. Make it structural:

1. **Package separation.** `src/fund/runtime/` has no network client and no
   model SDK in its dependency closure. Enforce with an import-linter rule in
   CI: `runtime` may not import anything that transitively reaches `httpx`,
   `openai`, `anthropic`, or a local inference server.
2. **Process separation.** The runtime executes in a container with egress
   allowed only to the broker and data vendor, by allowlist.
3. **Credential separation.** No model API key exists in the runtime's
   environment. It cannot call a model even if code were added.
4. **CI gate.** A test asserts the dependency rule and fails the build on
   violation.

Agent output reaches the runtime only as **reviewed, merged, tested source
code** — never as data at trade time.

---

## 8. Risk architecture

Deterministic, pre-submission, outside strategy code. Modelled on SEC 15c3-5,
which governs broker-dealers rather than you but is the correct template.

**Pre-trade** — fat-finger notional cap; max order size; max position; max daily
loss; max drawdown; gross/net exposure; 20% per-instrument concentration; price
collars rejecting orders far from last; order-rate limiting.

**Kill switches** — halt state persisted **outside process memory** so a restart
cannot forget it is halted. This is the single most important reliability
pattern in the document. Dead-man's heartbeat: no heartbeat ⇒ flatten or halt.

**Market-wide halts** — Rule 80B levels are asymmetric in a way that matters
here: a Level 1 or 2 breach *before* 3:25 p.m. ET halts trading for 15 minutes;
the same breach *at or after* 3:25 p.m. does **not**. Since MOC execution sits
at ~15:50 ET, **that carve-out lands inside the fund's execution window** and is
a required test case, not background reading. Thresholds reset daily from the
prior S&P 500 close — fetch them, never hardcode.

**Order lifecycle** — idempotency keys, duplicate rejection, outbox pattern,
persisted transitions, and an explicit `UNKNOWN` state. On restart: query the
broker, reconcile, *then* resume. Never assume an unacknowledged order was not
filled.

---

## 9. Operations and monitoring

| Monitor | Fires on | Action |
|---|---|---|
| Position reconciliation | Any internal-vs-broker mismatch | **Halt**, page |
| Live-vs-backtest tracking error | CUSUM breach of pre-registered band | Review; possible decommission |
| Realised vs modelled slippage | Sustained divergence | Recalibrate cost model |
| Signal decay | Rolling IC / Sharpe degradation | Decommission review |
| Feature drift (PSI) | Distribution shift | Investigate |
| Volatility cap binding | `cap_binding_fraction` > 25% | Flag: strategy is no longer what was backtested (K-02) |
| Data freshness / lineage | Missing or unhashed input | **Refuse to trade** |

Alerts page. They do not email. Knight Capital's warning emails were read after
the fact.

---

## 10. Staged build-out

Each milestone has a deliverable and a gate. Do not start $n+1$ before $n$'s
gate is green.

### M0 — Governance skeleton `[2–3 weeks]`
Trial registry (append-only, hashed); pre-registration workflow with git
tagging; the nine caveat contracts as executable tests (see
`Docs/slice-01/CHARTER.md` §2 Phase 1); CI wiring including the A1 import-linter
rule.
**Gate:** `pytest` green; A1 rule enforced; a dummy prereg round-trips through
tag → registry → report.

### M1 — Sleeve 01, end to end `[6–10 weeks]`
The full vertical slice: one hypothesis, PIT data with lineage, sourced costs,
baselines first, purged walk-forward, gate, postmortem. **Detailed plan already
written: `Docs/slice-01/CHARTER.md`.**
**Gate:** a `POSTMORTEM.md` exists — *whatever the outcome*. A clean negative
result passes this gate.

> **M1 is the milestone that matters.** Everything before it is scaffolding;
> everything after it is repetition. The reviewer's critique is answered here
> and nowhere else.

### M2 — Harden what M1 actually used `[2–4 weeks]`
Refactor only the infrastructure M1 exercised. Delete anything speculative.
**Gate:** M1 reruns byte-identically on the refactored stack.

### M3 — Sleeves 02–03 `[8–12 weeks]`
Two more hypotheses, chosen for *low correlation* with sleeve 01 rather than for
expected return. Same pipeline, now amortised. Introduce BH false-discovery
control across sleeves (§6.1).
**Gate:** each sleeve independently gated; admission test §4.1 passed.

### M4 — Allocation layer `[3–4 weeks]`
Inverse-vol across surviving sleeves; quarter-Kelly fund vol target; L1
rebalancing band; concentration and gross limits.
**Gate:** portfolio backtest reproduces the sum of its sleeves plus documented
allocation effects — no unexplained residual.

### M5 — Paper portfolio `[3+ months, wall-clock]`
Full stack, deterministic, daily reconciliation, all monitors live. This
milestone cannot be compressed; it is measuring wall-clock behaviour.
**Gate:** zero unexplained reconciliation breaks; tracking error inside band;
realised vs modelled slippage documented.

### M6 — Live, own capital, minimum size `[ongoing]`
Smallest size at which fills are realistic. The objective is measuring
execution, not making money. Scale only after the cost model is confirmed
against real fills.
**Gate:** three months live with slippage inside the modelled band.

### M7 — Scale and repeat `[ongoing]`
Increase size; add sleeves; revalidate on cadence; run the Stage 9 self-audit.

**Total to M5: roughly 6–9 months of part-time work.** Anyone promising faster
is skipping M1's gate.

---

## 11. Economics of running it

**Development** (agentic coding, not runtime): light ~\$10–30/mo on one coding
plan; moderate ~\$30–80/mo plus a plan; heavy ~\$150–300/mo. Mitigate with
prompt caching — up to ~98% on DeepSeek, ~75–90% on GLM/Kimi — batch APIs
(40–60% off), context hygiene, and flash-tier routing for mechanical work.

Note the cost-driver subtlety: on cheap flash tiers where output is priced at
only ~2× input, agentic coding's high input:output ratio means **input** cost
dominates, so caching and context hygiene are the lever. On premium tiers output
dominates and terseness is the lever.

**Data:** Massive/Polygon Stocks Starter is currently \$29/mo for five years;
Developer is \$79/mo for ten years; Advanced is \$199/mo for its full archive,
which begins in 2003. ALFRED/FRED API access has no subscription fee but still
requires an API key and compliance with source-series and storage terms. Prices
and terms last checked 2026-08-12; verify again before purchase.
**Infra:** ~€5–20/mo (Hetzner). A daily-frequency system needs nothing more.
**Colocation is irrelevant** at this frequency: the fund's decision budget is
~10 minutes against a 15:50 ET MOC cutoff, roughly $2\times10^{11}$ times the
fastest latency the report discusses.

**If development spend exceeds ~\$300/mo**, shift bulk work to self-hosted
Qwen3-30B-A3B and batch APIs.

---

## 12. How this fails

Written now, so it is recognisable later.

| Failure mode | Early warning | Countermeasure |
|---|---|---|
| **Platform searching for a purpose** | Building infra no sleeve consumes | M1 gate; infra is pulled, never pushed |
| **Goalpost creep** | Sleeve re-enters research after failing | Failed gate ⇒ `KILLED`; changes are a new sleeve with new $N$ |
| **Registry decay** | $N$ resets, or "exploratory" runs unlogged | Registry is append-only; DSR reads $N$ from it, never from a human |
| **Agent-produced plausible nonsense** | Result beats baseline on first attempt | Validation desk's standing brief; treat as a bug until proven |
| **Silent look-ahead** | Suspiciously smooth equity curve | Causal-recomputation contract on every estimator (A6) |
| **Cost fiction** | Realised slippage ≫ modelled | M6 exists precisely to measure this |
| **Financing eats the edge** | Leverage > 1 in calm regimes | Gross ≤ 1.0 until M6; financing modelled explicitly thereafter |
| **Correlated sleeve sprawl** | Fund Sharpe flat as sleeves are added | Admission test §4.1: $\|\rho\| < 0.5$ |
| **Boredom** | Milestones slip with no decision | Key-person risk is real for a solo operator; M1's postmortem is the natural exit point if interest fades |

---

## 13. What success looks like at each horizon

- **3 months.** M0 + M1 in research. The nine caveats are executable contracts.
  A pre-registration is frozen and tagged.
- **6 months.** M1 complete with a written postmortem. **Either outcome
  counts.** You can hand a reviewer one command and one document.
- **9 months.** Two or three gated sleeves, an allocation layer, a paper
  portfolio running with reconciliation.
- **12 months.** Live at minimum size with a cost model confirmed against real
  fills, or a documented decision not to trade — which, if the evidence says so,
  is the correct outcome and a better artifact than a forced position.

The deliverable that makes this credible is not a Sharpe ratio. It is a fund
whose entire research history — every trial, every hash, every abandoned
configuration — is on the record and reproducible.
