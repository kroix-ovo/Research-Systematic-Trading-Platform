# Research: Systematic Trading Platform

A deterministic quant research and paper-trading platform for testing one
tradable hypothesis at a time, built with agentic coding assistants, and
designed so that **it can falsify its own hypotheses**.

## The claim

The platform is **not** evidence of an edge. Its job is to make one specific
trading hypothesis testable, reproducible, and easy to reject. The competitive
claim is not a signal, it is that every result is pre-registered, costed,
deflated against a cumulative trial count, and reproducible from a seed.

## What is here

| Path | Contents |
|---|---|
| `docs/report/` | The verified research report, its verification suite, and figures |
| `docs/fund/` | Fund architecture, agent operating spec, charter amendments |
| `docs/slice-01/` | Milestone M1 — the first pre-registered hypothesis |
| `src/fund/` | M0 governance skeleton: A1 boundary enforcement, contracts |
| `contracts/` | Property tests turning report caveats into executable checks |
| `tests/fund/` | Registry, pre-registration freeze, and amendment tests |

## The verification suite

```bash
python3 docs/report/verify/run_all.py     # 115 checks, ~6 min
```

Symbolic algebra, independent numerical solves, and Monte Carlo against
processes with known parameters. Every check is seeded and reproducible.

**Current status: 115 checks across 18 sections — 90 PASS, 10 FLAG, 0 FAIL.**

The suite found and corrected **three errors** in the original research, each of
the kind that survives ordinary review because the code still runs:

- **P-13** — quadratic transaction costs do not produce a no-trade region; that
  requires a kinked (L1) cost function.
- **M-04** — the Ornstein–Uhlenbeck half-life inversion was the Euler
  approximation, overstating the half-life by up to 58% at fast mean reversion.
- **A-01** — an internal inconsistency in the prompt-caching discount claim.

It also found that applying standard ADF critical values to Engle–Granger
residuals declares **57% of independent random-walk pairs cointegrated** against
a nominal 5%.

## Design axioms

1. **No LLM in the execution path.** Enforced structurally: the runtime has no
   model SDK in its dependency closure, no model credential in its environment,
   and a CI import-linter rule that fails the build on violation.
2. **Writer is never sole reviewer**, and the reviewer is a different vendor.
3. **Never allocate using estimated expected returns.** Plug-in mean-variance
   realises Sharpe 0.15 against 1.85 attainable, and covariance shrinkage does
   not fix it, because the binding error is in the mean.
4. **Every estimator is causal**, enforced by a bit-identical recomputation
   test rather than by inspection.
5. **The trial count is cumulative across the project's entire life.**

## Scope and disclaimers

Own capital only. Nothing here is investment, legal, or tax advice. Managing
outside money triggers registration requirements that are explicitly out of
scope. All regulatory and tax points must be confirmed with a qualified
professional. Vendor pricing is dated and must be re-verified before reliance.
