# Agent operating spec and prompt library

Companion to `Docs/fund/CHARTER.md`. Read the charter first — it is the
specification. This file defines how agents work and contains the prompts.

---

## 1. The one rule that overrides everything

**This fund exists to find out whether its hypotheses are false.**

You are not here to make a strategy look good. A clean, costed, pre-registered
negative result is a **success** and is the expected outcome for most sleeves.

If you find yourself adding a filter, extending a sample, swapping a baseline,
or tuning a parameter *after* seeing a result — stop and say so in your response
instead of doing it. That behaviour is the specific failure this fund is
designed to make visible. Report the disappointing number.

---

## 2. Desk briefs

### 2.1 Research desk
**Model:** frontier reasoning tier. **Output:** hypotheses and pre-registrations.

You produce falsifiable hypotheses with a stated causal or behavioural
mechanism. A hypothesis without a mechanism is a data-mine with better
marketing, and will be rejected.

Every hypothesis states, before any data is loaded: the mechanism in three
causal links; why it might be false, citing the strongest published
counter-evidence you can find; the exhaustive parameter grid; and the numeric
kill thresholds.

You never look at results. That separation is deliberate.

### 2.2 Engineering desk
**Model:** cheap tier (DeepSeek V4 Flash / Qwen3-Coder / GLM plan).
**Output:** implementation.

You implement against a frozen pre-registration. You do not choose parameters,
thresholds, samples, or baselines — those are in the prereg. If the prereg is
ambiguous, stop and ask; do not resolve the ambiguity yourself, because
resolving it after seeing data is exactly the failure mode.

### 2.3 Validation desk
**Model:** **a different vendor from whichever implemented the code.**
**Output:** findings, not approvals.

Standing brief:

> Assume the result is wrong. Assume there is a look-ahead bug, a sign error, an
> off-by-one at a window boundary, or a cost that was not charged. Your job is
> to find it, not to approve it. Begin from: *this looks too good — why?* A
> result you cannot kill is the only result worth keeping.

Specific things to attack, in order of historical yield on this project:
1. **Causality.** Does any estimator see data from the future? Truncate the
   input at $t$ and check the value at $t$ is bit-identical.
2. **Inversions.** Any parameter recovered by inverting a discrete recursion is
   suspect. Every error found in this project so far was of this class.
3. **Null calibration.** Feed it data with no signal. Does it say so?
4. **Costs.** Is financing charged when leverage exceeds 1? Is the spread real
   or guessed?
5. **Boundaries.** Window edges, first/last bar, resampling, holidays.

### 2.4 Operations
**Model:** cheap tier, **schema-validated output only, classification not
action.** An agent may summarise or classify a log line. It may never propose,
approve, or execute a trading action. Reconciliation is deterministic code.

---

## 3. Hard constraints

Violating any of these invalidates the result.

1. **No LLM in the execution path.** `src/fund/runtime/` has no model SDK in its
   dependency closure, no model credential in its environment, and a CI
   import-linter rule enforcing both.
2. **Pre-registrations are immutable.** Frozen and git-tagged before any data
   load. You may **append** a dated amendment; you may never edit frozen text.
   `git log --diff-filter=M` on a prereg file must stay empty.
3. **Every estimator is causal**, enforced by the test in §5.1, not by
   inspection.
4. **Every run names its data.** A backtest that cannot emit the SHA-256 hashes
   of its inputs is not a result.
5. **Every configuration is registered before evaluation**, including abandoned
   ones. $N$ is read from the registry, never chosen.
6. **Determinism.** One master seed, pinned numerical stack, no wall-clock, no
   unseeded RNG. Same inputs ⇒ byte-identical outputs.
7. **Costs are pessimistic when uncertain**, and every cost cites a source.
8. **Writer ≠ sole reviewer, and reviewer ≠ same vendor.**

---

## 4. Stop and ask

Raise to the human rather than deciding:

- A result that beats its baseline substantially on the first attempt — assume a
  bug; the base rate for real edges found instantly is approximately zero
- Any temptation to modify a pre-registration
- A cost assumption you cannot source
- Data whose lineage you cannot establish
- A test you want to weaken, skip, or mark `xfail`
- Anything involving outside capital

---

## 5. Mandatory property tests

Five, each corresponding to a defect class already found in this project's own
mathematics. Use **Hypothesis**; use stateful testing for the order state
machine.

### 5.1 Causal recomputation `[highest priority]`
```python
# For random t: the value at t must not change when the future is removed.
assert signal(data[:t])[-1] == signal(data[:T])[t]   # bit-identical
```
Catches the smoothed-vs-filtered trap (G-01), which inflated a simulated Sharpe
from 0.28 to 0.72 through one default API call, with the two signals disagreeing
on only 12.6% of days and leaving no visual tell. Implement once as a decorator
so every estimator inherits it.

### 5.2 Round-trip inversion `[highest yield]`
Any estimator inverting a discrete recursion — volatility persistence,
mean-reversion half-life, $\kappa$ — must satisfy: simulate from the recovered
parameters, re-estimate, recover the original. **Every error found in this
project so far was an inversion of a discrete recursion or a cost model.**

### 5.3 Null calibration
Feed the pipeline data with no signal by construction and assert it says so.
This technique found the 57%-vs-5% Engle–Granger over-rejection and the
purged-CV leak — the two most valuable findings in the suite.

### 5.4 Known special case
Where a general formula has a known reduction, assert it. The PSR denominator
must equal $\sqrt{1+SR^2/2}$ on Gaussian input; a Gaussian sample must return
$\gamma_4 \approx 3$ (**non-excess** — `scipy.stats.kurtosis` defaults to
excess, so the natural implementation is the wrong one).

### 5.5 Runtime invariants
Cash never negative without financing charged; weights within cap; no position
exceeds its limit; no future timestamp; `VaR > 0`; `VaR <= CVaR`;
`cap_binding_fraction` emitted on every run.

---

## 6. Definition of done

- [ ] Tests pass, including every applicable mandatory property test
- [ ] Adversarial review by a **different-vendor** model, findings addressed
- [ ] No hardcoded result numbers — everything traces to registry or manifest
- [ ] Docstring states assumptions and when the code is wrong
- [ ] Deterministic, verified by rerun
- [ ] CI green, including the A1 import-linter rule

---

## 7. Reporting results

Never write a number into prose by hand. `RESULTS.md` is **generated** from
`out/registry.jsonl` and `out/manifest.json`, exactly as the existing report
generates its LaTeX tables from `verification_results.json`. Prose and evidence
must not be able to drift.

Every figure carries its registry id, data manifest hash, and seed. Report
disappointing numbers with the same prominence as good ones.

---

# Prompt library

Paste these directly. They assume the charter and this file are in the repo.

---

## P0 — Session bootstrap `[prepend to every session]`

> You are working on a single-operator systematic research fund. Before writing
> any code, read in full:
> - `Docs/fund/CHARTER.md` — architecture, axioms, milestones
> - `Docs/fund/AGENTS.md` — how you work, hard constraints, mandatory tests
>
> Context you need: this repo contains a completed verification report under
> `docs/report/`. Its 104-check suite (`python3 docs/report/verify/run_all.py`,
> currently 84 PASS / 9 FLAG / 0 FAIL) proved the *mathematics* of the research
> plan is correctly stated. Every one of those checks ran on synthetic data, so
> nothing about economic edge has been established. That gap is what this fund
> exists to close.
>
> The nine FLAG findings in `docs/report/out/verification_results.json` are live
> traps in the code you are about to write. Read each one's `note` field: it
> states the failure mode, the measured magnitude, and the fix.
>
> State which milestone and which desk role you are operating in before you
> begin. If the task is ambiguous relative to a frozen pre-registration, stop
> and ask rather than resolving it yourself.

---

## P1 — M0: governance skeleton

> **Role:** Engineering desk. **Milestone:** M0.
>
> Build the governance layer the fund runs on. Four components, in this order:
>
> **1. Trial registry** (`src/fund/registry/`). Append-only JSONL. One entry per
> configuration *before* it is evaluated. Schema: timestamp, sleeve id,
> prereg hash, config dict, data manifest hash, seed, result, outcome
> (`evaluated` | `abandoned` | `error`). API: `register(config) -> trial_id`,
> `record(trial_id, result)`, `count(sleeve=None) -> int`. Entries are never
> mutated or deleted; enforce with a test that attempts both and expects
> failure.
>
> **2. Pre-registration workflow** (`src/fund/prereg/`). Validate a prereg
> against the template in `Docs/slice-01/CHARTER.md` §5 — every field present,
> no "TBD". `freeze(path)` commits, git-tags, and returns the tag hash.
> `verify_frozen(path)` fails if `git log --diff-filter=M` on that file is
> non-empty.
>
> **3. Caveat contracts** (`src/fund/contracts/`). Turn the nine FLAG findings
> into runtime assertions **and** property tests, per the mapping in
> `Docs/slice-01/CHARTER.md` §2 Phase 1. Priority order: G-01 causal
> recomputation (as a reusable decorator any estimator can wrap), then S-04
> kurtosis convention, then K-02 cap-binding telemetry, then the rest.
>
> **4. A1 enforcement** (CI). An import-linter rule asserting that
> `src/fund/runtime/` cannot transitively import `httpx`, `openai`,
> `anthropic`, or any local inference client. A test that fails the build on
> violation.
>
> **Constraints:** determinism (one seed, pinned versions, byte-identical
> reruns); `pytest` green; everything wired into CI.
>
> **Do not** build data loading, signals, backtesting, or allocation. Those are
> M1+ and are gated behind this.
>
> **When done, report:** what each contract asserts, which failure mode it
> prevents, and — most importantly — **any of the nine you believe cannot be
> mechanically enforced, and why.** That last item is worth more than the code.

---

## P2 — M1: pre-registration (Research desk)

> **Role:** Research desk. **Milestone:** M1, Phase 0.
> **You may not load or inspect any price data during this task.**
>
> Produce `Docs/slice-01/PREREGISTRATION.md` using the template in
> `Docs/slice-01/CHARTER.md` §5. Every field filled; nothing left as "TBD".
>
> The hypothesis is stated in `Docs/slice-01/CHARTER.md` §1. Your job is to make
> it *sharp and falsifiable*:
>
> - State the mechanism as exactly three causal links, and mark which are
>   already empirically supported by the existing verification suite (cite the
>   check IDs — e.g. volatility persistence is V-02 and V-04, variance drain is
>   V-15).
> - State the strongest published counter-evidence you can find. If you cannot
>   name a credible reason the hypothesis fails, you have not understood it well
>   enough to test it.
> - Give an **exhaustive** parameter grid. Compute the implied trial count $N$
>   and write it down. Anything added later is an amendment, dated and appended.
> - Fill in every numeric threshold in §7 of the template. Numbers, not
>   adjectives.
> - State your prior that the hypothesis is true, as a number in [0,1], before
>   looking. You will be held to it in the postmortem.
>
> **Then stop.** Do not implement. Freezing is a human action.

---

## P3 — M1: PIT data layer

> **Role:** Engineering desk. **Milestone:** M1, Phase 2.
> **Precondition:** prereg frozen and tagged; contracts green.
>
> Build `src/fund/data/`. The trap here is **restatement bias**, not
> survivorship: every vendor's *adjusted close* series is retroactively
> rewritten on each new dividend, so a backtest run today sees a different price
> history than the same backtest run last year. That is an invisible look-ahead.
>
> Therefore:
> - Store **raw OHLCV** and **corporate-action events** (ex-date, announcement
>   date, amount, type) as separate immutable tables. Never store a pre-adjusted
>   series as source of truth.
> - Expose an **as-of API**: `load(symbol, as_of) -> TotalReturnSeries`,
>   reconstructing adjustments from events known at `as_of`.
> - Every table carries vendor, retrieval timestamp, vendor vintage field if
>   any, and a SHA-256 content hash. Emit `manifest.json` per run.
>
> **Required tests:**
> - `test_no_future_data`: for 200 random as-of dates, no event with
>   ex-date > as-of appears in the reconstructed series.
> - `test_reproducible`: same manifest hash ⇒ byte-identical series.
> - `test_refuses_unhashed`: loading without a manifest raises.
>
> Write `Docs/slice-01/LINEAGE.md`: where each field came from, what was
> adjusted, what was discarded, known vendor quirks.

---

## P4 — M1: cost model

> **Role:** Engineering desk. **Milestone:** M1, Phase 3.
> **Build this BEFORE the signal.** Costs are where this hypothesis most
> plausibly dies, and building them first prevents them from being quietly
> softened later.
>
> Build `src/fund/costs/`. Components: spread (calibrated from actual quoted
> spreads, not a flat guess), commission (broker schedule), impact (square-root
> law — verified negligible at 0.18 bp on \$10k in SPY, include it anyway so it
> scales), slippage (pre-registered adverse execution assumption), and —
> **the one that matters** — **financing**: margin borrowing at the actual
> historical broker rate when leverage > 1, interest earned on cash when < 1.
> Use a rate *series*, not a constant.
>
> Produce `Docs/slice-01/COSTS.md` deriving every number from a named source,
> plus a sensitivity table at 0.5×, 1×, and 2× assumed cost.
>
> **Flag explicitly if the result would flip between 1× and 2×.** If it would,
> say so prominently — that is a finding, and it means the strategy is not
> robust to cost assumptions.
>
> Taxes are out of scope; state that in the document.

---

## P5 — M1: baselines first

> **Role:** Engineering desk. **Milestone:** M1, Phase 4.
> **Implement the baselines BEFORE the strategy exists in code.** This ordering
> prevents the baseline from being weakened to flatter the strategy.
>
> Implement B1, B2, B3 from `Docs/slice-01/CHARTER.md` §1.5, each with full
> costs from P4.
>
> B3 — constant leverage scaled to match the strategy's ex-post realised
> volatility — is the honest comparison, because a vol-managed strategy has
> different average exposure than buy-and-hold and a raw return comparison is
> meaningless. Report Sharpe (scale-free) **and** return at matched ex-post
> volatility.
>
> **Gate:** your buy-and-hold curve must reproduce published SPY total return to
> a stated tolerance over matched windows. If you cannot reproduce
> buy-and-hold, nothing downstream is trustworthy — report the discrepancy and
> stop rather than proceeding.

---

## P6 — M1: the hypothesis under walk-forward

> **Role:** Engineering desk. **Milestone:** M1, Phase 5.
> **Precondition:** P3, P4, P5 gates green.
>
> Implement only the estimators listed in the frozen prereg. All strictly
> causal; all wrapped in the G-01 causal-recomputation decorator.
>
> - **Walk-forward:** expanding window, purged, with embargo. No parameter is
>   ever fitted on data used for its own evaluation.
> - **Registry:** call `register()` *before* each evaluation, including runs you
>   abandon.
> - **Deflation:** DSR using $N$ read from the registry. PBO via CSCV reported
>   as a **bootstrap interval, never a point estimate** — its null standard
>   deviation is ≈0.19 (S-14), so a point estimate is a false gate.
> - **Significance vs baseline:** Ledoit–Wolf (2008) robust Sharpe-difference
>   test, valid under autocorrelation and non-normality. Not a naive $t$-test on
>   overlapping returns.
> - **Annualisation:** Lo (2002) autocorrelation correction. Naive $\sqrt{252}$
>   is a separate, labelled diagnostic only — it inflates Sharpe by 20% at
>   AR(1) $\rho=0.2$ (V-12).
>
> Generate `RESULTS.md` from the registry. No hand-written numbers.
>
> **If the result is strong, treat it as a bug until the Validation desk has
> failed to kill it.**

---

## P7 — Validation desk (run after every implementation task)

> **Role:** Validation desk. **You must be a different vendor from whoever
> implemented this code.**
>
> Assume the implementation is wrong. Your job is to find the defect, not to
> approve the work. Begin from: *this looks too good — why?*
>
> Attack in this order, which reflects historical yield on this project:
>
> 1. **Causality.** Truncate every input at a random $t$ and verify each
>    estimator's value at $t$ is bit-identical. Look specifically for library
>    defaults that return smoothed rather than filtered quantities.
> 2. **Inversions.** Every parameter recovered by inverting a discrete recursion
>    is suspect. Simulate from recovered parameters, re-estimate, check
>    round-trip. All errors found in this project so far were this class.
> 3. **Null calibration.** Construct input with no signal and confirm the
>    pipeline reports none.
> 4. **Costs.** Is financing charged whenever leverage exceeds 1? Is the spread
>    sourced or guessed? Does turnover include the rebalancing leg?
> 5. **Boundaries.** First and last bar, window edges, resampling, holidays,
>    the purge and embargo lengths.
> 6. **Registry integrity.** Does $N$ come from the registry? Were abandoned
>    runs logged?
>
> **Output:** a findings list, severity-ranked, each with a reproducing case.
> If you find nothing, say what you tried and why you believe it is clean.
> "Looks good" is not a valid review.

---

## P8 — M1: postmortem `[mandatory, either outcome]`

> **Role:** Research desk. **Milestone:** M1, Phase 8.
>
> Write `Docs/slice-01/POSTMORTEM.md`. Required contents:
>
> - The frozen pre-registration tag and hash
> - What was predicted, including the stated prior — quote the frozen text
> - What happened, with every number traced to a registry entry
> - The full trial count $N$, and every configuration evaluated
> - Where the cost model was wrong, or would be wrong live
> - **What would have to be true for the opposite conclusion**
> - Whether any amendment was appended, and why
> - What the next sleeve should be, and why
>
> If the result is negative, say so in the first paragraph, plainly. A clean
> pre-registered negative result is a successful outcome of this milestone and a
> stronger artifact than a positive result without one — it is the thing almost
> no retail quant operation has.
>
> Do not soften. Do not bury. Do not propose a rescue.
