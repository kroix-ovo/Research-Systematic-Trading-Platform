# Charter amendments

Amendments to `Docs/fund/CHARTER.md`. Append-only. Each records what changed,
why, and what it costs to comply. The charter is a living document, but its
changes must be as legible as a pre-registration's.

---

## A-001 — The trial registry must count researcher degrees of freedom, not just configurations

**Date:** 2026-08-23
**Status:** ACCEPTED, not yet implemented
**Amends:** §6 (trial registry), §4 (sleeve lifecycle), M0 build scope
**Severity:** High — it undermines the deflation apparatus the fund is built on

### The defect

§6 defines the registry as one entry per *configuration* evaluated. In practice
that means grid points: parameter values swept inside a pre-registered search.

That is not the quantity the deflation mathematics needs. The False Strategy
Theorem (verification S-08/S-09) and the Deflated Sharpe Ratio both take $N$ =
**the number of independent trials from which the reported result was
selected**. A trial is any choice that could have gone another way and that was
resolved, even partly, by looking at outcomes. Grid points are a subset of
those.

Everything below is a trial in the Harvey–Liu–Zhu sense, and none of it enters
$N$ under the current definition:

| Degree of freedom | Example from this project's own history |
|---|---|
| Universe | S&P 500 exposure vs a broader ETF set |
| Instrument | **SPY → SPLG** (expense ratio and share granularity) |
| Sample period | **1993–present → 2003-09-10–present** (decimalization) |
| Broker / cost model | **IBKR Pro → Alpaca** (per-order minimum at \$3k) |
| Execution rule | **MOC → late-session marketable order** |
| Volatility estimator | EWMA vs GARCH vs range-based; half-life choice |
| Rebalancing rule | band width; monthly vs weekly |
| Baseline definition | buy-and-hold vs matched-volatility unmanaged |

Five of those eight were decided in a single afternoon of design conversation,
before any pre-registration existed. Each was defensible on its own merits. That
is precisely what makes them dangerous: a garden of forking paths is walked one
reasonable step at a time.

### Why it matters quantitatively

$N$ enters the hurdle through the expected maximum Sharpe under the null. From
S-08/S-09:

| $N$ | Expected max Sharpe from pure noise |
|---:|---:|
| 10 | 1.57 |
| 100 | 2.53 |
| 1,000 | 3.26 |
| 10,000 | 3.86 |
| 100,000 | 4.39 |

An undercounted $N$ therefore produces a hurdle that is **too low**, which
admits strategies that should have been rejected. The direction of the error is
the dangerous one — the same asymmetry flagged in S-04 for the kurtosis
convention. A registry that counts only grid points while the operator has
silently resolved a dozen design forks gives a false sense that deflation was
applied.

### The amendment

**§6 is amended to read that the registry counts *decisions*, not
configurations.** Concretely:

1. **A registry entry is required for every resolved design fork**, not only for
   evaluated parameter values. Schema gains a `kind` field:
   `config` | `design_choice` | `abandoned`.

2. **Design choices made before a pre-registration is frozen are still trials**
   and must be back-registered at freeze time. The pre-registration template
   gains a mandatory section: *"Design choices already made, and the
   alternatives considered."* If the honest answer is "I don't remember what
   else I considered", that is itself information and must be recorded as
   `unknown_count: true`.

3. **$N$ used for DSR is read from the registry as the total count of
   `config` + `design_choice` entries** attributable to the sleeve, including
   those inherited from the platform (instrument, universe, sample period are
   shared across sleeves and count for each).

4. **Where the count is genuinely unknowable**, report DSR at a *range* of $N$
   spanning the plausible interval rather than a point, and gate on the
   pessimistic end. This mirrors the treatment MVC-11 now applies to the capital
   floor and S-14 applies to PBO: a statistic whose input is uncertain is
   reported as an interval.

5. **§4 sleeve lifecycle is amended**: the existing rule that a failed gate sends
   a sleeve to `KILLED` rather than back to `IN RESEARCH` already prevents the
   worst case. It is extended — *any* change to a frozen design choice
   constitutes a new sleeve with a new pre-registration and inherits the
   accumulated $N$.

### What this costs

It makes the fund's hurdle materially harder to clear, which is the point. A
realistic slice-01 might carry $N \approx 200$–2,000 once design forks are
counted honestly, against perhaps 50–200 counted as grid points alone. Reading
the table above, that moves the noise hurdle from roughly 2.5–3.0 to 3.3–3.5.

It also imposes a discipline that is genuinely annoying in practice: you must
log a decision *at the moment you make it*, including the ones that feel like
housekeeping. The instrument switch from SPY to SPLG felt like an
implementation detail. It is not — it was chosen partly because SPY's
granularity was unworkable, which is an outcome-informed choice.

### Honest limitations of this amendment

- **It cannot be fully enforced.** There is no mechanical way to detect a design
  fork the operator did not record. Unlike the causal-recomputation contract
  (G-01), which a test can enforce absolutely, this one depends on self-report.
  Its value is that it makes the undercount *visible and estimable* rather than
  invisible.
- **The correct $N$ is not well defined.** Trials are not independent — the
  choice of instrument and the choice of universe overlap. The FST assumes
  independence, so a literal count over-corrects. Reporting a range (point 4)
  is a pragmatic response, not a rigorous solution.
- **A stricter reading would count reading a paper as a trial.** Selecting the
  vol-managed hypothesis *because* Moreira & Muir published a positive result is
  itself selection on an outcome, and the relevant $N$ then includes the
  published literature's own multiple testing. The amendment does not attempt to
  price that. It is one reason to treat any surviving result with suspicion even
  after deflation.

### Implementation

Belongs in **M0**, alongside the registry itself — retrofitting a decision log
after the fact is exactly the failure it exists to prevent. Prompt `P1` in
`Docs/fund/AGENTS.md` should be extended to build the `kind` field and the
back-registration workflow.

---

## A-002 — Volatility management must be pre-registered against its falsifying literature

**Date:** 2026-08-23
**Status:** ACCEPTED, applied
**Amends:** research-report §2.3; `Docs/slice-01/CHARTER.md` §1.3

Earlier drafts recommended volatility targeting throughout without citing
Cederburg, O'Doherty, Wang & Yan (2020), *JFE* 138(1):95–117, who find
vol-managed portfolios do not systematically beat unmanaged ones in direct
comparison, because the published alphas come from spanning regressions that
are not implementable in real time.

This is the same defect class as G-01 (smoothed vs filtered): a full-sample
regression sets the scaling using information the trader did not have.

Applied: report §2.3 now carries both sides; slice-01 §1.3 names Cederburg et
al. as the falsifying prior and requires a strictly causal scaling rule with the
unmanaged portfolio at matched ex-post volatility as the baseline.

---

## A-003 — Minimum viable capital is an interval, and taxes belong in it

**Date:** 2026-08-23
**Status:** ACCEPTED, applied
**Amends:** research-report §3.7

Two corrections to the first draft of the MVC section:

- **Tax.** At ~200% turnover gains are short-term, and the data subscription is
  not deductible without trader status (TCJA). The floor scales as
  $\text{MVC}/(1-t)$ — +43% at a 30% blended rate (MVC-09, MVC-10). Corollary:
  a Roth IRA sets $t=0$ and is close to ideal for a high-turnover, long-only,
  unlevered strategy.
- **Uncertainty.** The draft reported MVC at point values of $SR$, the error
  S-14 identifies for PBO. Since $\text{MVC}\propto 1/SR$, the Sharpe's sampling
  error is amplified: at ten years of daily data the 95% Sharpe interval still
  contains zero, so **MVC has no finite upper bound** (MVC-11). The point values
  survive only as a ranking of cost stacks, never as a capital requirement.
