\thispagestyle{empty}
\begin{center}
\vspace*{1.2cm}
{\LARGE\bfseries A Deterministic Quant Research\\[0.25em]
and Paper-Trading Platform\\[0.25em]
for Testing One Tradable Hypothesis\par}
\vspace{0.7cm}
{\Large\color{muted} Built with agentic coding assistants; checked by independent tests\par}
\vspace{1.4cm}
\begin{tcolorbox}[width=0.86\linewidth,colback=cpanel,colframe=rule,
                  boxrule=0.6pt,arc=2pt,left=14pt,right=14pt,top=11pt,bottom=11pt]
\small
\textbf{Research claim.} A solo researcher can build a credible research and
paper-trading system with coding agents, but the system is useful only if it
keeps the agents outside the trading runtime and treats verification as a gate
between an idea and an order. The platform itself is not evidence of an edge.
Its job is to make one specific trading hypothesis testable, reproducible, and
easy to reject.

\vspace{0.5em}
This edition applies that standard to its own design. The verification suite
runs \textbf{115 checks} across \textbf{18 sections}, using symbolic algebra,
independent numerical solves, and Monte Carlo tests against processes with
known parameters. It found and corrected \textbf{three errors} and identified
\textbf{nine claims that need an explicit assumption}. After the corrections,
\textbf{84 substantive claims pass}; no check remains in FAIL status.

\vspace{0.5em}
The random streams are deterministic. With the pinned dependencies, the suite
reproduces the reported rounded values. Explicit tolerances cover ordinary
last-bit differences between numerical platforms.
\end{tcolorbox}
\vspace{1.2cm}
{\small\color{muted} 12 August 2026\par}
\end{center}

\vspace{0.8cm}
\begin{center}
\begin{minipage}{0.88\linewidth}\footnotesize\color{muted}
\textbf{Scope and disclaimer.} This is a report about software engineering,
quantitative methods, and tooling. \textbf{It is not investment advice and does
not recommend a trade or an investment.} Prices, model capabilities, and
regulatory details are time-sensitive; check the relevant vendor, regulator,
broker, and employer before acting on them. A simulated Sharpe ratio or return
in this report belongs to a synthetic process used to test a formula. It is not
performance evidence.
\end{minipage}
\end{center}

\clearpage
\tableofcontents
\clearpage

# Part 0 — Introduction and scope

## 0.1 The project goal and the claim

The project has a practical end point: a small, deterministic research and
paper-trading system that can tell its owner whether one liquid-market idea
survives contact with real data. Agentic coding is part of the method, not part
of the strategy. Agents can draft code, tests, and documentation, but they do
not get to make trading decisions at runtime.

The claim of this paper is narrower than "build a complete quant platform" and
much narrower than "find alpha with AI": a well-tested platform can reduce the
chance of fooling yourself, but it cannot create an economic edge. The next
credible result must come from one vertical slice: a fixed universe, a reason
for the signal to exist, point-in-time data, a simple baseline, purged
walk-forward tests, realistic costs and borrow, and a sustained paper-trading
record. Until that slice exists, this work is infrastructure and research
method, not evidence that a strategy works.

That distinction determines the design. The system should make data lineage
visible, keep random experiments reproducible, count every trial, and stop a
strategy from promotion when it fails a pre-set test. It should also make it
cheap to discard an idea. A platform that produces polished charts but hides
those decisions would be a more efficient way to overfit.

## 0.2 What this edition checks

The first edition surveyed alternative models, mathematical methods, platforms,
risk practice, and latency for a solo-operated research and paper-trading
system. This edition keeps that survey, but gives the verification layer a
more exact role: it checks whether the machinery used to judge a strategy is
itself correct.

That matters because the report's central engineering judgment is that
**backtest overfitting, not latency, is the dominant risk**. If a Deflated
Sharpe Ratio or a purged cross-validation routine is wrong, the promotion gate
can approve a bad result while appearing to work. A false gate is dangerous
precisely because it looks like discipline.

Every equation in Section 2, every arithmetic claim in Sections 1, 4, and 5,
and the pairs-trading estimators in Section 6.5 have been re-derived and
tested. The suite does not treat a citation or an existing implementation as a
substitute for a check. A claim is accepted by one of three routes:

- a symbolic derivation in `sympy`;
- an independent numerical solve compared with the claimed closed form; or
- a Monte Carlo experiment built from a process whose parameters are known.

When a claim fails, the report gives the direction and size of the error and
states the implementation change. When a claim needs an assumption, the
assumption is written down. That is the standard the later empirical slice
will have to meet as well.

## 0.3 Results of the verification suite

\input{out/generated/summary.tex}

Part I covers the three corrections and nine remaining caveats. Appendix A
contains all 115 rows.

The status labels are simple. **FAIL** means the claim is wrong as written.
**FLAG** means it is correct only when a missing condition is made explicit.
**PASS** means it survives the stated test. **INFO** records a useful derived
quantity that is not itself a pass/fail claim.

\begin{keybox}{The single most useful outcome}
Three of the twelve issues found (P-13, M-04, and M-05) would have produced a
system that ran and returned plausible numbers while being wrong. None would
have raised an exception or made an equity curve visibly strange. That is why
the verification layer belongs between research output and deployment.
\end{keybox}

## 0.4 Reproducing the results

The report and its checks regenerate from the repository:

```bash
cd Docs/report
python3 -m venv ../../.venv
../../.venv/bin/python -m pip install -r requirements.txt
../../.venv/bin/python verify/run_all.py      # 115 checks, ~6 min
../../.venv/bin/python figures/fig_math.py    # mathematical figures
../../.venv/bin/python figures/fig_systems.py # architecture diagrams
../../.venv/bin/python figures/fig_verify.py  # verification figures
../../.venv/bin/python gen_tables.py          # tables from results JSON
./build.sh                     # assembles this PDF
```

The suite uses one master constant (`MASTER_SEED = 20260811`). With the pinned
requirements, a new run reproduces the random streams and reported rounded
values. Solver residuals can differ in their last bits across BLAS platforms,
so acceptance decisions use explicit tolerances. The summary, findings tables,
and Appendix A come from the suite's JSON output. Repeated values in the prose
still need review when a check changes.

The report applies to itself the same determinism rule it recommends for the
trading runtime.

\clearpage

# Part I — Findings

## 1.1 Three corrections

The first verification run exposed three wrong claims. The text and checks now
use the corrected versions, while the old formulations remain as regression
guards so the same mistakes cannot quietly return.

### P-13 — Quadratic transaction costs do not create a no-trade region

The earlier Section 2.4 draft stated that the cost-aware objective

$$\max_w\; w^\top\mu-\frac{\gamma}{2}w^\top\Sigma w-(w-w_0)^\top\Lambda(w-w_0)$$

"gives a closed form **and a no-trade region** (don't rebalance until drift
exceeds a band)."

The closed form is correct. Verification P-12 confirms it symbolically and
numerically: the optimum is $w^*=(\gamma\Sigma+2\Lambda)^{-1}(\mu+2\Lambda w_0)$,
matching a BFGS solve to $7\times10^{-9}$.

The no-trade-region claim was not correct. A quadratic penalty is smooth and
has zero marginal cost at zero trade. Therefore, whenever the frictionless
objective has a nonzero directional derivative at the current book, some small
trade improves the objective. The solution shrinks toward $w_0$ -- partial
adjustment -- but does not stop inside a band. A no-trade region requires a
cost function with a **kink** at zero, i.e. proportional (L1) costs, whose
subgradient interval $[-c,c]$ can absorb small deviations.

Sweeping the starting book away from the frictionless optimum makes this
unambiguous: under the quadratic model the traded amount is strictly positive at
every nonzero drift, with a minimum of $4.0\times10^{-3}$; under an L1 model of
comparable magnitude the traded amount is *exactly zero* until drift reaches
0.04.

![](figures/fig14_no_trade_region.pdf)

This is not a cosmetic distinction. If the system is built on the quadratic
model expecting bands to emerge, it will rebalance every single day and bleed
precisely the cost the band was intended to save. Real spreads and commissions
*are* proportional, so the L1 model is also the more faithful one.

**Applied fix.** Section 2.4 now describes the quadratic model as partial
adjustment only and assigns a no-trade band to an L1 cost term (or to a separate
explicit rule). P-13 is now a passing regression check of that distinction.

### M-04 — The Ornstein–Uhlenbeck half-life formula is biased

The earlier Section 6.5 draft gave the estimation recipe: regress
$\Delta X_t=\lambda X_{t-1}+c+\varepsilon_t$, then "$\theta=-\lambda$ and
**half-life $=-\ln 2/\lambda$**".

The exact discretisation of $dX_t=\theta(\mu-X_t)dt+\sigma dW_t$ at spacing
$\Delta t$ is

$$X_t-X_{t-1}=\left(e^{-\theta\Delta t}-1\right)(X_{t-1}-\mu)+\text{noise},$$

so the regression slope estimates $\lambda=e^{-\theta\Delta t}-1$, and the
correct inversion is

$$\theta=-\frac{\ln(1+\lambda)}{\Delta t},\qquad
\text{half-life}=-\frac{\Delta t\,\ln 2}{\ln(1+\lambda)}.$$

The report's form is the first-order Taylor expansion of this, valid only when
$\theta\Delta t\ll1$. Simulating exact OU processes at six known
mean-reversion speeds and comparing both estimators against the true half-life
$\ln 2/\theta$ gives:

| True $\theta$ | True half-life | Report's formula | Error |
|---:|---:|---:|---:|
| 0.02 | 34.7 | 34.7 | $-0\%$ |
| 0.05 | 13.9 | 14.2 | $+2\%$ |
| 0.10 | 6.9 | 7.3 | $+6\%$ |
| 0.25 | 2.8 | 3.1 | $+14\%$ |
| 0.50 | 1.4 | 1.8 | $+27\%$ |
| 1.00 | 0.7 | 1.1 | $+58\%$ |

The exact formula recovers the truth to within 1% at every speed (M-03).

![](figures/fig15_meanrev.pdf)

The error is **one-directional**: the estimate is always too *long*. It is also
largest for fast-reverting pairs. A pair with a two-day half-life can receive a
holding limit, time stop, or capital allocation based on an estimate more than
half too high.

**Applied fix.** Section 6.5 now uses
$-\Delta t\ln 2/\ln(1+\lambda)$. M-04 retains the superseded Euler expression
only as a passing regression guard that proves why it must not return.

### A-01 — The prompt-caching discount claim is now provider-specific

The earlier Section 6.7 draft described a stable prompt prefix as hitting a
blanket **~90–98%-cheaper cache rate** on DeepSeek/GLM/Kimi. The corrected
edition uses separate provider ranges.

Computing $1-(\text{cache-hit price}/\text{cache-miss price})$ from the report's
own Section 1.2 pricing table:

| Model | Cache miss (\$/1M in) | Cache hit | Discount |
|---|---:|---:|---:|
| DeepSeek V4 Flash | 0.14 | 0.0028 | **98%** |
| DeepSeek V4 Pro | 0.435 | 0.003625 | **99%** |
| Kimi K2.6 / K2.7 Code | 0.95 | 0.19 | 80% |
| Kimi K2.5 | 0.60 | 0.15 | 75% |
| Kimi K3 | 3.00 | 0.30 | 90% |
| GLM-4.6 | 0.60 | 0.11 | 82% |
| GLM-4.5-Air | 0.20 | 0.03 | 85% |

DeepSeek spans 98–99% after rounding (the Pro figure is 99.17%). For the GLM
and Kimi families the same table gives 75–90%. The earlier blanket range was
therefore internally inconsistent with the pricing table.

This matters for budgeting. If the residual spend after caching on a GLM coding
plan is 18% of list rather than 2%, it is nine times larger than the sentence
implies — which changes where the Section 1.8 budget lands.

**Applied fix.** Section 6.7 now states "~98–99% on DeepSeek and ~75–90% on
GLM/Kimi." A-01 recomputes both displayed ranges from the table and now passes.

## 1.2 Caveats: claims correct only under an unstated condition

\input{out/generated/table_flags.tex}

Four deserve separate discussion because each is a plausible implementation
trap. The full detail for all nine is in Appendix B.

### S-04 — $\gamma_4$ in the PSR formula must be non-excess kurtosis

The Probabilistic Sharpe Ratio is the load-bearing formula of Section 2.8:
PSR, the Deflated Sharpe Ratio, and the Minimum Track Record Length are all
transformations of the same standard error. The report writes it as

$$\widehat{\text{PSR}}(\text{SR}^*)=\Phi\!\left(\frac{(\widehat{\text{SR}}-\text{SR}^*)\sqrt{n-1}}{\sqrt{1-\hat\gamma_3\widehat{\text{SR}}+\frac{\hat\gamma_4-1}{4}\widehat{\text{SR}}^2}}\right)$$

and defines $\hat\gamma_4$ only as "kurtosis". The formula is correct — verified
against the empirical standard deviation of 200,000 independent Sharpe
estimates under Gaussian, Student-$t$(6) and skew-normal returns (S-01 to S-03),
and confirmed to reduce exactly to Lo's $\sqrt{1+\widehat{SR}^2/2}$ under
normality (S-05) — **provided $\gamma_4$ is non-excess kurtosis**, equal to 3
for a Gaussian.

Both conventions are in common use, and `scipy.stats.kurtosis` returns the
*excess* value by default. The natural implementation is therefore the wrong
one. The error scales with the square of the per-period Sharpe, which makes it
nearly invisible on daily data and material on the monthly data that fund-style
track records actually use:

| Frequency | Understatement of the standard error |
|---|---:|
| daily | 0.1% |
| weekly | 0.5% |
| monthly | 1.9% |
| quarterly | 5.1% |
| annual | 14.4% |

![](figures/fig04_psr.pdf)

The direction is the dangerous one: understating the standard error *inflates*
PSR and DSR, admitting strategies that should have been rejected.

**Recommended fix.** Define $\gamma_4=E[(r-\mu)^4]/\sigma^4$ explicitly, and
unit-test two invariants: a Gaussian sample must return $\gamma_4\approx3$, and
the general formula must equal $\sqrt{1+\widehat{SR}^2/2}$ on Gaussian input.

At daily frequency the **skewness** term dominates the kurtosis term by an
order of magnitude. A skew of $-0.8$ changes the daily standard error by
$+2.4\%$, against $0.1\%$ for the kurtosis convention. If only one correction
can be implemented carefully, make it the skew term.

### S-14 — PBO is a correct diagnostic, and a noisy one

The Probability of Backtest Overfitting via CSCV behaves exactly as advertised.
Averaged over 40 independent noise datasets its expectation under the null is
$0.530\pm0.028$ — indistinguishable from the theoretical 0.5 (S-12). Given a
strategy with a genuine persistent edge it falls to 0.000, and on a correlated
parameter sweep over a single signal it correctly returns 0.353 (S-13).

What the report does not mention is that a PBO value computed from *one*
backtest matrix has very large sampling error:

| Sample size | Mean PBO under the null | Standard deviation |
|---|---:|---:|
| $T=1000$, $N=40$ | 0.49 | **0.19** |
| $T=2500$, $N=40$ | 0.52 | 0.20 |
| $T=1000$, $N=200$ | 0.47 | 0.16 |
| $T=5000$, $N=200$ | 0.52 | 0.15 |

![](figures/fig06_pbo.pdf)

At the data sizes a solo operator actually has, two honest runs on the same
worthless strategy family can return PBO $=0.25$ and PBO $=0.75$. A threshold
rule written against a statistic with that spread is a false gate.

**Recommended fix.** Do not gate promotion on a single PBO point estimate.
Report a bootstrap confidence interval alongside it, and prefer longer
histories and larger strategy families. PBO remains useful, but it should be
reported as an interval rather than a single number.

### G-01 — The HMM look-ahead trap is silent and expensive

Section 2.5 correctly flags that *smoothed* state probabilities
$P(z_t\mid r_{1:T})$ use future data and only *filtered* $P(z_t\mid r_{1:t})$
are tradeable. Quantifying it across 30 independent realisations of a
regime-switching process, fitting a two-state Gaussian HMM to each and running
the identical long/flat rule on both:

- smoothed: annualised Sharpe **0.72**
- filtered: annualised Sharpe **0.28**
- gap: $0.44\pm0.06$ — an inflation of **157%**

![](figures/fig17_hmm_lookahead.pdf)

The trap is **silent**: `predict_proba` and `predict` in `hmmlearn`
return smoothed posteriors by default, so the wrong answer is what a careful
implementer produces on the first attempt. The two signals differ on only
12.6% of days, so the resulting equity curve looks entirely plausible — there
is no visual tell and no impossible trade to catch in review. The inflation is
largest when regimes overlap, when the model is least reliable.

**Recommended fix.** Add a causal-recomputation property test to Section 6.1:
assert that the signal at time $t$ is bit-identical when the input sample is
truncated at $t$. This single test generalises to every state-space model in the
system, and it is cheap.

### V-08b — Range volatility estimators are biased low on real bars

Parkinson, Garman–Klass and Rogers–Satchell are all unbiased for driftless
geometric Brownian motion — verified by sweeping the intraday sampling
frequency and extrapolating to the continuum limit, which recovers $\sigma^2$
to within 0.1% for all three (V-05 to V-07).

But the unbiasedness proofs assume a *continuously observed* path, and a real
bar is a finite sample of prints. A bar built from finitely many trades cannot
observe the true continuous-time high and low, so every range estimator is
biased downward:

| Prints per bar | Parkinson bias |
|---:|---:|
| 100 | $-12.0\%$ |
| 400 | $-6.0\%$ |
| 1,600 | $-3.0\%$ |
| 6,400 | $-1.7\%$ |

The fitted $m^{-1/2}$ slope of $-1.21$ is within 15% of the
Broadie--Glasserman--Kou continuity-correction prediction of $-1.46$. The
agreement is consistent with the sampling mechanism described above.

![](figures/fig16_vol_estimators.pdf)

Section 2.3 *divides* by this number. A volatility estimate that is 12% too low
becomes systematic over-leverage of the same order.

**Recommended fix.** Use liquid instruments, or calibrate a discretisation
correction from observed prints per bar. Also note that only Rogers–Satchell is
drift-independent: at a deliberately extreme 2%/day drift, Parkinson is biased
$+37.0\%$ and Garman–Klass $+13.3\%$, while Rogers–Satchell moves $+0.0\%$
(V-09).

## 1.3 What the findings establish

After the corrections, eighty-four of ninety-three substantive claims pass.
The tests support the core pieces of the verification design:

- The **False Strategy Theorem** closed form matches direct Monte Carlo to
  better than 1% for all $N\geq100$, and the headline figure the report quotes
  verbatim — that after 1,000 independent backtests the expected maximum Sharpe
  is **3.26** even when true Sharpe is zero — is exactly right (formula 3.255,
  independent Monte Carlo 3.242).
- The **Almgren–Chriss** $\sinh$ trajectory is the true optimum of
  $E[\text{cost}]+\lambda V[\text{cost}]$, matching a numerical solve that
  assumes nothing about the closed form to $6.6\times10^{-13}$, with the cost
  functional itself confirmed by simulating the underlying price process.
- **Purged cross-validation** does what the report says: on data with provably
  zero predictability, shuffled $k$-fold reports AUC $0.526\pm0.004$ while
  purged-and-embargoed reports $0.501\pm0.006$.
- **PSR** is a properly calibrated probability (Kolmogorov–Smirnov $p=0.97$
  against uniformity under the null).

The corrected defects share a pattern. They came from inverting a discrete
recursion or interpreting a cost model: the OU half-life, the no-trade region,
the $\kappa$ approximation, and the kurtosis convention. These errors survive
type checks and ordinary code review. They produce numbers that look normal.
Their consequence appears later, in a position size, a turnover bill, or a
promotion decision.

The practical response is to test the surrounding property as well as the
formula's happy path. An independent implementation, a round-trip test, a null
calibration, or a causal recomputation can expose a defect that a single
example never will. That is the role verification engineering plays in the
system proposed here.

\clearpage

# Part II — The system and the research method

The rest of the paper describes the choices around the research slice: which
models can help build it, which mathematical tools it needs, where the data
and execution boundaries sit, and how the system should fail. The verification
results are placed next to the claims they test. The figures show the parts of
the design that are easier to inspect than to describe.

# 1. Alternative and Cheaper Models

## 1.1 Hosted models and local weights are different decisions

Calling a Chinese-hosted API and running Chinese open weights locally are
different choices. Local weights can run offline, so strategy code and private
data stay on the machine. A hosted endpoint sends the prompt to a provider's
servers and puts the data under that provider's terms and local law.

\begin{keybox}{The rule for this project}
Use inexpensive hosted APIs for generic or public coding. Keep strategy logic,
signals, and private data on self-hosted weights or with a host that has been
approved for that data.
\end{keybox}

## 1.2 Chinese frontier and open model families

Pricing as of July–August 2026. Treat every figure as provisional.

| Family | Model | \$/1M in | \$/1M out | Cache-hit in | Context | Licence |
|---|---|---:|---:|---:|---:|---|
| DeepSeek | V4 Flash | 0.14 | 0.28 | 0.0028 | 1M | MIT (weights) |
| DeepSeek | V4 Pro | 0.435 | 0.87 | 0.003625 | 1M | MIT (weights) |
| Alibaba Qwen | Qwen3-Coder Next | 0.11–0.12 | 0.80 | — | 262K | Apache-2.0 |
| Qwen | Qwen3.5 Flash | 0.10 | 0.40 | — | 1M | Apache-2.0 |
| Qwen | Qwen3 Max | 0.78 | 3.90 | — | 262K | proprietary |
| Moonshot Kimi | K2.6 / K2.7 Code | 0.95 | 4.00 | 0.19 | 262K | open weights |
| Kimi | K2.5 | 0.60 | 3.00 | 0.15 | 262K | open weights |
| Kimi | K3 | 3.00 | 15.00 | 0.30 | 1M | weights published |
| Zhipu/Z.ai GLM | GLM-4.6 | 0.60 | 2.20 | 0.11 | ~200K | MIT |
| GLM | GLM-4.5-Air | 0.20 | 1.10 | 0.03 | — | MIT |
| GLM | GLM-4.5/4.7-Flash | free | free | — | ~128–203K | MIT |

DeepSeek has announced but not dated a 2× peak-hour surcharge (Beijing-time
windows). Thinner-sourced families noted in results: **MiniMax** (M-series,
competitive open weights, ~80% SWE-bench Verified), **ByteDance Doubao/Seed**,
**Baidu ERNIE**, **Tencent Hunyuan**, **iFlytek Spark**, **01.AI Yi**,
**StepFun**, **Baichuan** — mostly China-market-focused or less battle-tested
for agentic coding than the four leaders.

**Coding-plan subscriptions** (flat-rate, quota-based, Anthropic-compatible —
best value for heavy Claude Code use): Z.ai GLM Coding Plan Lite ~\$30/quarter
(~\$10/mo), Pro ~\$90/quarter (~\$30/mo), Max ~\$240/quarter (~\$80/mo). The
\$3/mo promo was removed 11 February 2026. Moonshot's Batch API charges ~60% of
standard.

\begin{verified}{A-02 --- verified}
All three quarterly-to-monthly conversions are exact. Minor, but these are the
figures the Section 1.8 budget table is built on.
\end{verified}

\begin{verified}{A-01 --- cache-discount ranges verified}
Computed from the table above, DeepSeek cache hits are 98--99\% cheaper and
GLM/Kimi cache hits are 75--90\% cheaper. A-01 recomputes the rounded endpoints
and passes. See Part~I.
\end{verified}

## 1.3 Western open-weight alternatives

**Meta Llama**, **Mistral** (including **Codestral** for code and **Devstral**
for agentic coding — Devstral 2 Small is a notable small agentic-coding model),
**Mixtral** (MoE), **Google Gemma**, **Microsoft Phi**, **AI2 OLMo** (fully
open including training data), **IBM Granite**, **NVIDIA Nemotron**, and
**OpenAI gpt-oss** (20B/120B open-weight). For a solo operator these matter
mostly as self-hostable, licence-clean options; gpt-oss-20b and small
Qwen/Gemma variants are the realistic single-GPU choices.

## 1.4 Local and self-hosted inference

The **MoE-with-small-active-parameters** class is the sweet spot.
**Qwen3-30B/35B-A3B** (30–35B total, ~3B active per token) is the standout:

- ~30 tok/s at Q4 on an 8GB RTX 3070 Ti (community benchmark); ~50–65 tok/s on
  a used RTX 3090 at Q4\_K\_M with full 32K context.
- Apple Silicon: Mac Studio M4 Max 48GB runs Q5\_K\_M at 25–35 tok/s via MLX;
  Mac Mini M4 Pro 24GB does Q4\_0 at ~15–22 tok/s.
- Unsloth's multi-token-prediction speculative decoding pushes
  Qwen3.6-35B-A3B to ~240 tok/s on an RTX 6000.

Runtimes: **llama.cpp/GGUF** (Q4\_K\_M is the standard quality/size sweet spot;
Q5/Q6 if VRAM allows), **Ollama** (easiest), **vLLM/SGLang** (throughput and
production serving), **LM Studio** (GUI), **TensorRT-LLM** (NVIDIA maximum
performance). Quantisation formats: GGUF, AWQ/GPTQ, FP8/NVFP4.

**Tool-calling reliability is the practical gotcha for agents** — llama.cpp
needs `--jinja` and correct chat templates; GLM-4.7-Flash is recommended for
local Claude Code because it reliably emits tool calls with 128K context.

## 1.5 Driving the coding agents with alternative models

**Claude Code** speaks the Anthropic Messages API. Four environment variables
(`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`,
`ANTHROPIC_SMALL_FAST_MODEL`) redirect it to any Anthropic-compatible gateway.
**claude-code-router** (`@musistudio/claude-code-router`, run via `ccr code`)
proxies to DeepSeek/Qwen/GLM/Kimi/Ollama and routes per request type (default /
background / think / longContext). **LiteLLM** and **OpenRouter** provide the
same translation layer. Alibaba's DashScope exposes a native Anthropic endpoint
for Qwen.

**The tool-calling caveat is real and must be tested.** Anthropic models are
trained on Claude Code's exact tool-call format; GLM, Qwen, DeepSeek and Kimi
are trained on their own conventions, and the proxy's translation is imperfect.
Failure modes: the model narrates what it *would* do instead of emitting a tool
call, or produces malformed edits. OpenRouter's "Exacto" routing mode optimises
for tool-calling accuracy.

**Codex CLI** and OpenAI-compatible alternatives — **OpenCode**, **Aider**,
**Cline**, **Continue**, **Roo Code**, **Goose** — all accept OpenAI-compatible
base URLs, so any Chinese API can drive them.

## 1.6 Coding and reasoning benchmarks

2026 snapshots; directional only.

| Model | SWE-bench Verified | SWE-bench Pro | Licence |
|---|---:|---:|---|
| DeepSeek V4-Pro-Max | ~80.6% (top open) | — | MIT |
| MiniMax M3 | ~80.5% | ~59.0% | open |
| Qwen3.7 Max | ~80.4% | ~60.6% | mixed |
| Kimi K2.6 | ~80.2% | ~58.6% | open |
| GLM-5.2 | — | ~62.1% (best open, 3rd-party) | MIT |
| Claude Opus (frontier) | high-70s–80s | ~69.2% (leads active) | closed |

![](figures/fig01_model_landscape.pdf)

Caveats: SWE-bench Verified vendor numbers are inconsistently scaffolded;
Scale's SWE-bench Pro standardised set (identical scaffolding, 731 public tasks)
is the most apples-to-apples but has thin coverage. Other benchmarks to track:
**LiveCodeBench**, **Terminal-Bench 2.0**, **BigCodeBench**,
**HumanEval+/MBPP+**, **Aider Polyglot** (coding); **AIME**, **GPQA**
(reasoning and maths); **RULER** (long context).

A 2026 arXiv study of five open-weights coding models on a real
application-generation task found benchmark rank to be a **weak predictor of
real artifact quality**. A/B test candidates on your own repository.

## 1.7 Risks of routing through Chinese-hosted APIs

- **Data residency / PIPL.** China's Personal Information Protection Law
  (2021), plus Commercial Encryption Regulations and CAC security-assessment
  and data-localisation rules, create a regime with little control or recourse
  over submitted content once it lands on Chinese servers.
- **Training on inputs and retention.** Consumer-tier terms for several Chinese
  providers permit using inputs to improve services; retention windows are
  opaque and enterprise or international tiers sometimes differ. **Do not
  assume deletion.**
- **US regulatory, procurement, export control.** Government-adjacent
  procurement increasingly restricts Chinese AI services; this could be
  disqualifying for later work at a US firm with security requirements. Export
  controls run the other way and do not affect downloading weights.
- **Censorship and alignment quirks.** Largely irrelevant to trading code, but
  a correctness and consistency wildcard.
- **Why self-hosting is materially different.** Downloaded open weights run
  offline, deterministically, with zero data egress and no terms of service on
  inference — available precisely because these labs ship permissive (MIT,
  Apache-2.0) weights. This is the single most important mitigation.

## 1.8 Recommended model-routing table

| Task | Recommended | Rationale |
|---|---|---|
| Architecture / design (Stage 0) | Frontier Western (Opus-class) or GLM-5.x | Best reasoning; low token volume so cost immaterial |
| Bulk implementation (Codex primary) | DeepSeek V4 Flash / Qwen3-Coder / GLM Coding Plan | Cheapest per token; highest volume |
| Adversarial review (Claude Code) | Different vendor from the implementer | Enforces writer $\neq$ sole reviewer AND model diversity |
| Test generation | Qwen3-Coder / Kimi K2.7 Code | Strong code, cheap, enumerates cases well |
| Runtime research agents (Stage 8) | **Self-hosted Qwen3-30B-A3B** behind deterministic wrappers | No data egress; schema-validated, timeout-bounded |
| Embeddings | Self-hosted (bge/e5/Qwen-embed) | Cheap, private, deterministic |
| Cheap batch summarisation | DeepSeek V4 Flash batch / GLM-4.5-Flash (free) | Off-peak and batch discounts |

![](figures/fig12_model_routing.pdf)

**Estimated monthly development cost** (agentic coding, not runtime): *light*
~\$10–30/mo (one coding plan); *moderate* ~\$30–80/mo token spend plus a coding
plan; *heavy* ~\$150–300/mo.

\begin{caveat}{A-03 --- "output-token-dominated" is only half right}
Section 1.8 describes heavy usage as output-token-dominated. Computing the
input:output ratio at which input cost takes over: for DeepSeek V4 Flash, where
output is priced at only 2$\times$ input, \emph{input} cost dominates at any
ratio above 2:1 --- and agentic coding typically runs 20:1 or more. For GLM-4.6
(3.7$\times$) and Kimi K2.6 (4.2$\times$) output genuinely dominates.

The practical consequence sharpens the report's own advice: on cheap flash tiers
the highest-leverage optimisation is context hygiene and prompt caching (the
input side); on premium tiers it is limiting verbose output. The report
recommends both but attributes them to the wrong cost driver.
\end{caveat}

\clearpage

# 2. Mathematical Models

This section collects the mathematical components the eventual strategy slice
will need: signals, volatility, sizing, portfolio construction, risk, costs,
execution, and validation. Each formula is written with its assumptions. The
verification result is recorded beside it, including cases where a textbook
formula is correct only for an idealised process.

## 2.1 Momentum signals

**Time-series momentum** (Moskowitz–Ooi–Pedersen): signal
$s_{i,t}=\operatorname{sign}(r_{i,t-k\to t})$, where
$r_{i,t-k\to t}=\prod_{j=t-k+1}^{t}(1+r_{i,j})-1$. Position is volatility-scaled
(§2.3). **Skip-month:** use returns to $t-21$ to avoid short-term reversal.
**Risk-adjusted momentum:** rank by $r/\sigma$. **Cross-sectional:** long the
top quantile, short the bottom.

*Failure modes:* momentum crashes (post-drawdown rebounds), turnover, regime
dependence.

\begin{verified}{R-01, R-03 --- verified}
The compounding identity and the log-return bridge $r_{\log}=\ln(1+r)$ both hold
to machine precision. Worth stating explicitly because R-02 shows the
consequence of getting it wrong: over a two-year sample, \emph{summing} simple
returns instead of compounding them overstates cumulative return by 37\% of the
true figure. Backtest P\&L must compound, never sum.
\end{verified}

## 2.2 Volatility estimation

Realised $\sigma^2_t=\frac1n\sum r^2$; **EWMA/RiskMetrics**
$\sigma^2_t=\lambda\sigma^2_{t-1}+(1-\lambda)r_{t-1}^2$ with
$\lambda\approx0.94$ daily; **GARCH(1,1)**
$\sigma^2_t=\omega+\alpha r_{t-1}^2+\beta\sigma^2_{t-1}$ with $\alpha+\beta<1$
and long-run variance $\omega/(1-\alpha-\beta)$; **GJR-GARCH/EGARCH** add
asymmetric leverage; **HAR-RV** (Corsi) with daily, weekly and monthly realised
variance terms.

Range estimators: **Parkinson** $\frac1{4\ln2}\ln(H/L)^2$, **Garman–Klass**,
**Rogers–Satchell** (drift-independent), **Yang–Zhang** (overnight gaps and
drift). Annualise $\sigma\sqrt{252}$.

\begin{verified}{V-01 to V-07 --- verified}
The GARCH long-run variance matches a 3M-step simulation. EWMA is
\emph{exactly} IGARCH(1,1) with $\omega=0,\alpha=1-\lambda,\beta=\lambda$
(recursion difference: zero) --- which means it has no finite unconditional
variance and no mean reversion in volatility. That is a feature (fast
adaptation) and a defect, and the report should say so.

Parkinson, Garman--Klass and Rogers--Satchell are all unbiased for driftless
GBM, verified by extrapolating a sampling-frequency sweep to the continuum
limit (recovering $\sigma^2$ to 0.1\%). Their efficiency gains over
close-to-close are 5.0$\times$, 7.8$\times$ and 6.2$\times$ respectively ---
one day of OHLC carries about as much volatility information as a week of
closes.
\end{verified}

\begin{caveat}{V-08b, V-09 --- two conditions the report omits}
Range estimators are biased \textbf{low} on real bars ($-12\%$ at 100 prints per
bar), and only Rogers--Satchell is drift-independent. Both are detailed in
Part~I; §2.3 divides by this number, so the bias becomes leverage error.
\end{caveat}

\begin{caveat}{V-12 --- the $\sqrt{252}$ caveat, quantified}
The report notes that annualisation "assumes i.i.d.; autocorrelation biases it"
but gives no magnitude. Using Lo's (2002) exact correction
$SR_q=SR_1\,q/\sqrt{q+2\sum_{k<q}(q-k)\rho_k}$:

\vspace{0.4em}
\begin{center}\small
\begin{tabular}{@{}lrrrrr@{}}
\toprule
AR(1) $\rho$ & $-0.2$ & $0.0$ & $+0.1$ & $+0.2$ & $+0.3$ \\
Naive overstatement & $-16.9\%$ & $0.0\%$ & $+9.6\%$ & $+20.3\%$ & $+32.5\%$ \\
\bottomrule
\end{tabular}
\end{center}
\vspace{0.4em}

At $\rho=0.2$ --- unremarkable for a daily trend strategy --- naive scaling
inflates the Sharpe by 20\%, Monte Carlo confirmed. Smoothed or illiquid marks
push $\rho$ higher still. Any strategy clearing a hurdle only after naive
annualisation should be re-tested with the Lo correction.
\end{caveat}

Track volatility-of-volatility for regime signals. For reference, the
$\lambda=0.94$ default implies a shock half-life of 11.2 trading days and a
centre of mass of 15.7 days (V-04) — this is the concrete meaning of the
report's remark that the estimate "lags jumps".

## 2.3 Volatility targeting

$w_{i,t}=\dfrac{\sigma^*}{\sigma_{i,t}}s_{i,t}$; portfolio scalar
$c_t=\sigma^*/\hat\sigma_{p,t}$, subject to a leverage cap $\sum|w|\le L$.
Empirically this raises the Sharpe ratio and cuts drawdown by de-risking in
high-volatility regimes; it adds turnover; and the volatility estimate lags
jumps.

\begin{caveat}{The evidence for volatility management is contested --- and this
report previously presented only one side}
Earlier drafts of this section asserted the benefit without citing the
literature that disputes it. That is the same failure §4.7 criticises in
others, so it is corrected here.

\textbf{For:} Moreira \& Muir (2017), \emph{Journal of Finance} 72(4):1611--1644,
find that scaling exposure by inverse realised variance produces significantly
positive alphas across equity factors.

\textbf{Against:} Cederburg, O'Doherty, Wang \& Yan (2020), \emph{Journal of
Financial Economics} 138(1):95--117, examine 103 equity strategies and conclude
that volatility-managed portfolios \textbf{do not systematically outperform
their unmanaged counterparts in direct comparison}. Their central objection is
methodological and lands squarely on this report's own concerns: the positive
alphas come from \emph{spanning regressions} whose implied trading strategies
are \textbf{not implementable in real time}, and reasonable out-of-sample
versions generally earn \emph{lower} certainty-equivalent returns and Sharpe
ratios than simply holding the unmanaged portfolio.

That is the same defect class as G-01. A spanning regression estimated over the
full sample uses future information to set the scaling, exactly as smoothed
state probabilities do. The in-sample result is real; the tradeable result is
not the same number.

Consequences for this project. First, volatility targeting must be treated as a
\textbf{hypothesis to be tested}, not a technique to be applied --- and the
strongest published evidence says it will probably fail. Second, any
pre-registration of a volatility-managed strategy must name Cederburg et al. as
the falsifying prior and must specify a strictly causal scaling rule with a
real-time-implementable estimator. Third, the correct baseline is the
\emph{unmanaged} portfolio at matched ex-post volatility, which is the
comparison that paper shows is usually lost.
\end{caveat}

\begin{verified}{K-01 --- verified}
With $\sigma$ known, $w=\sigma^*/\sigma$ delivers realised volatility equal to
the target to within 0.1\%.
\end{verified}

\begin{caveat}{K-02 --- the cap and the target are not independent}
The report presents the volatility target and the leverage cap as separate
constraints. They interact: whenever the cap binds, realised volatility falls
\emph{below} target (14.33\% against a 15\% target, with the cap binding 22\% of
the time in simulation). In calm regimes --- exactly when $\sigma^*/\sigma$ is
largest --- the cap silently converts the strategy from volatility-targeted to
constant-leverage.

Log cap-binding frequency as a first-class monitoring metric. A strategy that
spends most of its life against the cap is not the strategy that was backtested.
\end{caveat}

\begin{verified}{K-03 --- the "levers into calm-before-storm" risk, sized}
Simulating 500 calm days (6\% annualised volatility) followed by an abrupt shift
to 71\% annualised: the EWMA estimator carries a median \textbf{2.4$\times$}
leverage into the break, and a two-sigma storm day then costs \textbf{21.6\% of
capital in a single session}.

The EWMA half-life is 11.2 days, so the estimator needs roughly two weeks to
reprice a regime break. This is the quantitative argument for pairing volatility
targeting with a fast, non-volatility circuit breaker (§4.4) rather than
trusting the volatility estimate alone to de-risk.
\end{verified}

## 2.4 Portfolio construction

- **Markowitz:** $\max_w w^\top\mu-\frac\gamma2 w^\top\Sigma w$, closed form
  $w^*=\frac1\gamma\Sigma^{-1}\mu$. $\Sigma^{-1}$ amplifies estimation noise —
  mean-variance "error-maximises".
- **Shrinkage covariance:** **Ledoit–Wolf**
  $\hat\Sigma=(1-\delta)S+\delta F$ ($S$ sample, $F$ structured target, $\delta$
  optimal intensity); **OAS** for Gaussian; factor covariance models.
- **ERC / risk parity:** equal risk contribution
  $w_i(\Sigma w)_i=w_j(\Sigma w)_j\ \forall i,j$; solve
  $\min_w\sum_i(w_i(\Sigma w)_i-\frac1N w^\top\Sigma w)^2$.
- **HRP (López de Prado):** tree-cluster the correlation matrix,
  quasi-diagonalise, recursive-bisection inverse-variance — avoids
  $\Sigma^{-1}$, robust to ill-conditioning.
- **Min-variance** $\min w^\top\Sigma w$ s.t. $\mathbf1^\top w=1$;
  **max-diversification** $\max (w^\top\sigma)/\sqrt{w^\top\Sigma w}$.
- **Black–Litterman:**
  $E[R]=[(\tau\Sigma)^{-1}+P^\top\Omega^{-1}P]^{-1}[(\tau\Sigma)^{-1}\Pi+P^\top\Omega^{-1}Q]$,
  $\Pi=\delta\Sigma w_{mkt}$.
- **Transaction-cost-aware:**
  $\max_w w^\top\mu-\frac\gamma2 w^\top\Sigma w-(w-w_0)^\top\Lambda(w-w_0)$.

\begin{verified}{P-01 to P-12 --- verified}
The Markowitz closed form is confirmed symbolically (the first-order condition
solution equals $\gamma^{-1}\Sigma^{-1}\mu$ identically) and numerically.
Ledoit--Wolf reconstructs exactly as $(1-\delta)S+\delta F$. The ERC objective
does produce equal risk contributions (spread $7\times10^{-13}$), and --- a
useful corollary the report omits --- \textbf{under equal pairwise correlation
the ERC solution is exactly inverse-volatility weighting}, $w_i\propto1/\sigma_i$,
needing no optimiser and no matrix inverse. For a broad ETF sleeve with roughly
uniform correlations, that is the whole method.

All three Black--Litterman boundary behaviours hold: $\Pi=\delta\Sigma w_{mkt}$
reverse-optimises back to $w_{mkt}$ exactly; vague views collapse the posterior
to $\Pi$; certain views satisfy $P\,E[R]=Q$ exactly. The report states the
formula but none of its limits, which are what a reviewer checks first.
\end{verified}

\begin{verified}{P-13 --- corrected and verified}
Quadratic costs give smooth partial adjustment, not a no-trade region. A
no-trade region requires proportional/L1 costs (or an explicit separate band).
P-13 verifies both behaviours across a sweep away from the frictionless target.
\end{verified}

**How badly does mean-variance error-maximise?** With 20 assets and five years
of daily data — more than most retail backtests have clean — the unconstrained
plug-in portfolio realises a Sharpe of **0.15** against an attainable **1.85**,
destroying 99% of the utility it was solving for (P-03).

The instructive part is what does *not* fix it. Substituting a Ledoit–Wolf
covariance moves the realised Sharpe only from 0.15 to 0.16, because the binding
error is in $\hat\mu$, not $\hat\Sigma$. Expected returns need roughly two
orders of magnitude more data than covariances to estimate to comparable
precision, so no amount of covariance cleverness rescues a noisy $\mu$.

**The report should therefore not present shrinkage as the remedy for
"error-maximisation".** The remedies that work are the ones that stop using
$\hat\mu$ altogether — ERC, HRP, minimum variance, inverse volatility — which is
exactly why those methods dominate in practice and why the report is right to
list them.

![](figures/fig18_portfolio_3d.pdf)

HRP delivers what the report claims. With $N=30$ and $T=45$, it produces
long-only weights summing to one without inverting $\Sigma$, and on two
independent samples *from the same distribution* it reshuffles the book
**3.1× less** than minimum variance does (P-08). Every unit of that difference
is transaction cost paid for estimation noise.

## 2.5 Regime detection

**Hidden Markov models:** latent state $z_t$, emissions
$r_t|z_t\sim\mathcal N(\mu_z,\sigma^2_z)$; **Baum–Welch** (EM) fits, **Viterbi**
decodes.

\begin{finding}{The critical look-ahead trap (G-01)}
\emph{Smoothed} probabilities $P(z_t\mid r_{1:T})$ use future data; only
\emph{filtered} $P(z_t\mid r_{1:t})$ are tradeable. Measured across 30
realisations: smoothed Sharpe 0.72 vs filtered 0.28, a 157\% inflation, from one
default API call. Detailed in Part~I. This is the highest-value property test in
the entire plan.
\end{finding}

Also: **Markov-switching** (Hamilton); change-point detection via **CUSUM** and
**Bayesian online change-point** (Adams–MacKay); clustering-based regimes; and
**simple robust baselines** (200-day trend, volatility quantiles).

On the baselines, the honest version of the report's claim is more nuanced than
"simple often beats fancy". On data generated by exactly the model the HMM
assumes — the most favourable setting possible — the correctly filtered HMM
*does* win, scoring 0.34 against 0.19 for the best one-line baseline (G-02). The
right framing is therefore a caution, not a general result: on real data, where
the two-state Gaussian assumption is wrong, that margin is the first thing to
disappear.

The decisive comparison is against G-01: **the look-ahead artefact (0.72 vs
0.28) was larger than the entire genuine edge over the baselines.** Every
baseline is causal by construction, cannot be fitted wrong, and cannot
accidentally consume smoothed probabilities. They belong in the promotion gate
as the control arm.

## 2.6 Kelly criterion and sizing

$f^*=\mu/\sigma^2$ (continuous) or $f^*=p-\frac{1-p}{b}$ (discrete).
**Fractional Kelly** (¼–½) is standard because full Kelly is over-levered under
parameter uncertainty and produces brutal drawdowns.

\begin{verified}{K-04 to K-08 --- verified symbolically}
Both Kelly forms are confirmed in \texttt{sympy}, with the second-order
condition checked. Two identities the report should add:

\textbf{At fraction $c$ of full Kelly, the growth rate is $c(2-c)$ of maximum.}
Half Kelly retains 75\% of the growth for half the volatility; quarter Kelly
retains 43.75\%. This is the trade-off curve behind the report's
recommendation, which it currently asserts without justification.

\textbf{Full Kelly targets a portfolio volatility numerically equal to the
Sharpe ratio}, since $f^*\sigma=(\mu/\sigma^2)\sigma=\mu/\sigma=SR$. This makes
"Kelly $\approx$ vol targeting" exact rather than approximate, and yields a
sanity rule: a strategy with a true Sharpe of 0.5 is at \emph{full} Kelly when
run at 50\% annualised volatility. A daily-ETF system targeting 10--15\%
volatility on a Sharpe-0.5 signal is therefore already at roughly quarter
Kelly --- the right neighbourhood, and worth stating because it connects §2.3
and §2.6, which currently read as unrelated.
\end{verified}

![](figures/fig07_kelly.pdf)

The simulated drawdown consequences are stark: over ten years, full Kelly
produces a median maximum drawdown of $-68\%$ (5th percentile $-90\%$), half
Kelly $-40\%$, quarter Kelly $-22\%$ (K-09).

But those figures assume $\mu$ and $\sigma$ are *known*. They are not. Estimating
$f^*$ from ten years of daily data — again, more than most retail backtests
have — leaves it essentially unidentified: the 5th–95th percentile range spans
$[-0.64, 4.69]$ around a true value of 2.00, and 11% of samples recommend more
than twice the correct leverage (K-10).

**This is the real justification for haircutting hard.** The quarter-Kelly
convention is not conservatism about the world; it is correct sizing under
parameter uncertainty.

## 2.7 Risk metrics

Sharpe $\frac{\mu-r_f}\sigma$; Sortino (downside deviation); Calmar
$\frac{\text{CAGR}}{|\text{MaxDD}|}$; Information Ratio; Omega. VaR (historical,
parametric $\mu+z_\alpha\sigma$, **Cornish–Fisher** skew- and
kurtosis-adjusted, Monte Carlo); **CVaR / Expected Shortfall**
$=E[L\mid L>\text{VaR}_\alpha]$, which is **coherent** (Artzner axioms) whereas
VaR is not subadditive.

\begin{verified}{Q-03, Q-04 --- verified with a minimal counterexample}
VaR's subadditivity failure is real and easy to exhibit: two \emph{independent}
bonds, each defaulting with probability 4\% for a loss of 100. Each has
$\text{VaR}_{95}=0$, because $P(\text{no default})=0.96>0.95$. The pair has
$\text{VaR}_{95}=100$, because $P(\text{neither defaults})=0.9216<0.95$.
Diversifying across two independent positions makes measured VaR go \emph{up},
from 0 to 100.

CVaR, by contrast, satisfied subadditivity across 300 randomised dependence
structures (Gaussian copula with $\rho\in[-0.9,0.9]$, Student-$t$ margins,
jump contamination) with no violation. This is the concrete basis for sizing
limits in CVaR rather than VaR.
\end{verified}

\begin{caveat}{Q-02 --- the parametric VaR formula is ambiguous}
$\mu+z_\alpha\sigma$ does not state whether $\alpha$ is the tail probability or
the confidence level, nor whether VaR is reported as a positive loss or a
negative return. The two readings differ by a sign flip on the risk number
itself ($-0.0274$ versus $+0.0284$ at the same parameters).

A sign error in a risk limit is precisely the defect class §4.3's pre-trade
controls exist to prevent. Pin the convention down with a property test
asserting $\text{VaR}>0$ and $\text{VaR}\le\text{CVaR}$.
\end{caveat}

\begin{caveat}{Q-08 --- Cornish--Fisher can invert}
The expansion is verified as written, including the frequently dropped
$-\frac{(2z^3-5z)\gamma_3^2}{36}$ term, and it beats the Gaussian quantile in
five of six tested cases. But it is an \emph{asymptotic} expansion valid for
mild non-normality only. At skewness $-3$ with excess kurtosis 12 --- the
territory of a short-volatility or option-overlay sleeve, i.e. §4.6's XIV
example --- it becomes non-monotone in $z$, reporting a \emph{smaller} loss at
99\% than at 95\%.

Assert monotonicity of the quantile function at runtime and fall back to
historical or filtered-historical simulation when the assertion trips.
\end{caveat}

Two additions worth making. The Gaussian Expected Shortfall has the closed form
$\mu+\sigma\phi(z_\alpha)/(1-\alpha)$ (Q-05), which is the reference value a
unit test can assert against without Monte Carlo. And the ES/VaR ratio is only
1.19 under normality but 1.59 under Student-$t$(3) (Q-06) — a risk system
calibrated on Gaussian ES will understate the very tail it exists to measure.

Finally, Sharpe, Sortino and Calmar are not interchangeable and can be gamed
against one another (Q-09). Calmar in particular depends on a single realised
path statistic, making it the noisiest of the three. **The deflation machinery
in §2.8 is built for the Sharpe ratio specifically; applying DSR or PSR
thresholds to a Sortino or Calmar figure is not valid.**

## 2.8 Statistical validation

This is the core of Stage 5 and the highest-stakes mathematics in the report.

**Probabilistic Sharpe Ratio (PSR):**

$$\widehat{\text{PSR}}(\text{SR}^*)=\Phi\!\left(\frac{(\widehat{\text{SR}}-\text{SR}^*)\sqrt{n-1}}{\sqrt{1-\hat\gamma_3\widehat{\text{SR}}+\frac{\hat\gamma_4-1}4\widehat{\text{SR}}^2}}\right)$$

where $\hat\gamma_3$ is skewness, $\hat\gamma_4$ kurtosis, $n$ the sample
length, and the denominator is the skew- and kurtosis-adjusted standard error of
the Sharpe estimate.

\begin{verified}{S-01 to S-06 --- verified}
The denominator \emph{is} the true standard error of $\widehat{SR}$, confirmed
against the empirical standard deviation of 200,000 independent Sharpe estimates
under Gaussian, Student-$t$(6) and skew-normal returns. Under normality it
reduces exactly to Lo's (2002) $\sqrt{1+\widehat{SR}^2/2}$.

PSR is also properly \emph{calibrated}: under the null it is uniformly
distributed (Kolmogorov--Smirnov $p=0.97$), and a 0.95 threshold admits 4.90\% of
worthless strategies against a nominal 5\%. That is the property that makes it
usable as a promotion gate, and it is verified rather than assumed.
\end{verified}

\begin{caveat}{S-04 --- $\gamma_4$ must be non-excess kurtosis}
Detailed in Part~I. \texttt{scipy.stats.kurtosis} returns the excess value by
default, and the resulting error inflates PSR and DSR --- the dangerous
direction.
\end{caveat}

**Deflated Sharpe Ratio** (Bailey \& López de Prado, *Journal of Portfolio
Management* 40(5):94–107, 2014): DSR is PSR evaluated at the expected maximum
Sharpe under the null, from the **False Strategy Theorem**:

$$E[\max_N\widehat{\text{SR}}]\approx\sqrt{V[\widehat{\text{SR}}]}\left[(1-\gamma)\,\Phi^{-1}\!\Big(1-\tfrac1N\Big)+\gamma\,\Phi^{-1}\!\Big(1-\tfrac1{N e}\Big)\right]$$

with $\gamma\approx0.5772$ (Euler–Mascheroni), $N$ the number of independent
trials, and $V[\widehat{\text{SR}}]$ the cross-sectional variance of trial
Sharpe ratios.

\begin{verified}{S-07, S-08 --- verified against direct Monte Carlo}
The closed form matches the simulated expected maximum of $N$ i.i.d. standard
normals to better than 1\% for every $N\geq100$, improving as $N$ grows (0.1\%
at $N=10{,}000$). Since the theorem exists for large trial counts, it is
accurate exactly where it is used.

The paper's headline, which the report quotes verbatim --- \emph{"after only
1,000 independent backtests the expected maximum Sharpe Ratio is 3.26, even if
the true SR of the strategy is zero"} --- is \textbf{exactly right}: the formula
gives 3.255 and independent Monte Carlo gives 3.242.
\end{verified}

![](figures/fig02_false_strategy.pdf)

The practical meaning deserves spelling out. An operator who tries 1,000
parameter combinations and reports the best one has an expected Sharpe of 3.26
**from pure noise**. A raw Sharpe of 3 is evidence of a large search, not of
skill.

And a routine parameter sweep reaches those counts immediately. A
three-parameter grid at ten values each is 1,000 trials before any variant
selection; adding a universe choice and two signal variants reaches $10^5$,
where the null expects a maximum Sharpe of **4.39** (S-09).

\begin{keybox}{The consequence for the trial registry}
The deflation is only as good as the trial count $N$. The registry must count
\textbf{every configuration ever evaluated, including abandoned ones}. An
understated $N$ makes the whole apparatus worthless while appearing to work.
\end{keybox}

**Minimum Track Record Length:** solve PSR $=$ target confidence for $n$.

\begin{verified}{S-10, S-11 --- verified, with the number the report omits}
The numerical root matches the closed form
$n^*=1+\left[1-\gamma_3 SR+\frac{\gamma_4-1}{4}SR^2\right]\left(\frac{z_{target}}{SR-SR^*}\right)^2$
to $10^{-6}$. The figure that matters:

\vspace{0.4em}
\begin{center}\small
\begin{tabular}{@{}lrrrrrr@{}}
\toprule
True annualised Sharpe & 0.3 & 0.5 & 0.8 & 1.0 & 1.5 & 2.0 \\
Years for 95\% confidence & 30.1 & 10.8 & 4.2 & 2.7 & 1.2 & 0.7 \\
\bottomrule
\end{tabular}
\end{center}
\vspace{0.4em}

Set against §4.8's "realistic solo expectation is net Sharpe 0.3--0.8": at a
true Sharpe of 0.5 it takes \textbf{11 years} of live data to be 95\% confident
the strategy is not noise; at 0.3 it takes 30.

The honest conclusion is that \textbf{live P\&L will never be the arbiter on a
solo timescale}. That is precisely why the ex-ante controls --- PBO, DSR, purged
CV --- have to carry the weight.
\end{verified}

**Probability of Backtest Overfitting via CSCV** (Bailey, Borwein, López de
Prado, Zhu): partition the trial $\times$ time performance matrix into
combinatorially symmetric train/test splits; PBO is the fraction of splits in
which the in-sample-best configuration ranks below the out-of-sample median.
Model-free and non-parametric.

\begin{verified}{S-12, S-13 --- verified}
Calibrated ($0.530\pm0.028$ under the null, averaged over 40 datasets) and
powered (0.000 with a genuine edge; 0.353 on a correlated parameter sweep).

Note that PBO and DSR answer \emph{different} questions --- DSR asks "is this
Sharpe real given $N$ trials?", PBO asks "does my selection procedure
generalise?" --- so the report is right to gate promotion on both.
\end{verified}

\begin{caveat}{S-14 --- but PBO is itself a noisy statistic}
Standard deviation $\approx0.19$ under the null at realistic sample sizes.
Report an interval, not a point estimate. Detailed in Part~I.
\end{caveat}

**Deflation and multiple testing:** **White's Reality Check** and **Hansen's SPA
test** (bootstrap the max statistic across strategies); **Harvey–Liu haircut
Sharpe**; and the **$t>3.0$** argument.

**Bootstrap:** stationary bootstrap (Politis–Romano), circular block bootstrap;
optimal block length $\sim O(n^{1/3})$ (Politis–White automatic selection).

**Purged $k$-fold CV with embargo** (López de Prado): remove training samples
whose label windows overlap the test set (purge) plus a buffer (embargo),
because financial labels overlap in time and standard CV leaks.

\begin{verified}{S-15 --- verified end to end on data with zero signal}
Constructed so that true predictability is \textbf{zero by design}: the feature
is a trailing sum of i.i.d. returns and the label a \emph{disjoint} forward sum.

\vspace{0.4em}
\begin{center}\small
\begin{tabular}{@{}lr@{}}
\toprule
Shuffled $k$-fold (the naive default) & AUC $0.526\pm0.004$ \\
Contiguous blocked folds, no purging & AUC $0.499\pm0.006$ \\
Purged + embargoed & AUC $0.501\pm0.006$ \\
\bottomrule
\end{tabular}
\end{center}
\vspace{0.4em}

Three lessons. The naive pipeline reports a \emph{statistically significant}
result where the truth is 0.5. The leak requires \textbf{no look-ahead in the
feature at all} --- feature and label windows are disjoint by construction, and
the leak comes entirely from neighbouring \emph{training} rows sharing the test
row's label window. An audit for "no future data in features" is therefore
necessary but \emph{not sufficient}, which is the single most important
practical consequence. And simply using contiguous folds instead of shuffled
ones already removes most of the damage: blocking is the cheap 90\% fix,
purging is the rest.
\end{verified}

![](figures/fig05_purged_cv.pdf)

## 2.9 Transaction cost and market impact

Effective spread $2|p_{exec}-m|$; **Kyle's lambda**
$\Delta p=\lambda\cdot$(signed order flow); **square-root law**
$\Delta P\approx Y\sigma\sqrt{Q/V}$ ($Q$ order size, $V$ ADV, $Y\approx O(1)$).

**Almgren–Chriss optimal execution** (2000): permanent impact linear in trade
rate, temporary impact $h(v)=\epsilon\,\text{sgn}(v)+\eta v$; minimise
$E[\text{cost}]+\lambda V[\text{cost}]$. Closed-form trajectory:

$$x_j=X\,\frac{\sinh(\kappa(T-t_j))}{\sinh(\kappa T)},\qquad \kappa\approx\sqrt{\lambda\sigma^2/\eta}$$

— hyperbolic-sine decay; higher risk aversion $\lambda$ implies faster
liquidation, tracing the **efficient frontier of execution**.

\begin{verified}{E-01 to E-07 --- verified, thoroughly}
This is the most heavily tested result in the report, because the closed form is
easy to state and hard to check.

\textbf{E-01.} The $\sinh$ form satisfies the discrete stationarity condition
$x_{j-1}-2x_j+x_{j+1}=2(\cosh(\kappa\tau)-1)x_j$ \emph{identically} in
\texttt{sympy}. Matching this to the first-order condition gives the exact
defining equation $\cosh(\kappa\tau)=1+\tilde\kappa^2\tau^2/2$ with
$\tilde\kappa^2=\lambda\sigma^2/\tilde\eta$.

\textbf{E-02.} Solving the discrete optimisation numerically --- assuming
nothing whatever about $\sinh$ --- and comparing against the closed form across
$N\in\{10,50,200\}$ and three orders of magnitude of $\lambda$ gives a maximum
relative error of $6.6\times10^{-13}$. \textbf{The report's equation is exactly
right.}

\textbf{E-04.} As $\lambda\to0$ the trajectory becomes linear, i.e. TWAP --- the
sanity check that anchors the model.

\textbf{E-06.} Simulating 400,000 liquidations through the \emph{full price
process} reproduces both the closed-form expected cost and the closed-form cost
variance. This validates the cost functional being minimised, not merely the
algebra of its solution.

\textbf{E-07.} The efficient frontier is monotone and convex, so there is a
well-defined interior trade-off rather than a corner solution.
\end{verified}

![](figures/fig03_almgren_chriss.pdf)

\begin{caveat}{E-03 --- $\kappa\approx\sqrt{\lambda\sigma^2/\eta}$ drops two corrections}
The exact $\kappa$ solves a transcendental equation and approaches
$\tilde\kappa$ only as $\tau\to0$; and the denominator should be
$\tilde\eta=\eta-\gamma\tau/2$, not $\eta$, because half of each trade's
permanent impact is paid by the trader's own remaining inventory.

At a fine grid the error in $\kappa$ is negligible; on a five-slice schedule ---
a realistic daily-ETF execution --- it is $-0.49\%$.

\textbf{The reassuring part is worth stating explicitly:} the \emph{objective}
penalty is at most $\sim10^{-8}$ in every case tested, because the cost surface
is extremely flat near its optimum. Execution-schedule optimisation is
forgiving. Effort spent calibrating impact parameters precisely is better spent
elsewhere --- which independently reinforces §5.7's argument against premature
optimisation.
\end{caveat}

**Implementation shortfall** = paper minus actual return (Perold). POV,
participation-rate, TWAP and VWAP scheduling. Calibrate a cost model from ETF
quoted bid-ask and ADV.

\begin{verified}{E-08, E-09 --- and why this section is mostly theoretical here}
The square-root law is concave: doubling order size raises impact by $\sqrt2$,
not 2, and $Q/V$ is dimensionless so impact inherits the units of $\sigma$.

Evaluated at realistic retail size with daily volatility: a \$10,000 order in a
\$5B/day ETF incurs about \textbf{0.18 bp} of impact --- an order of magnitude
below the bid-ask spread, which is the binding cost at this size. Even \$1M in
the same ETF costs 1.78 bp. Only the thin-ADV case (\$100k in a \$50M/day name)
reaches 5.6 bp.

This validates the report's decision to calibrate the Stage 3 cost model from
quoted spread and ADV rather than from an impact model, and confirms that the
Almgren--Chriss machinery above is, for \emph{this} system, an intellectual
exercise rather than an operational necessity. It also explains §4.8's claim
that retail has an edge in capacity-constrained niches: that edge follows
directly from the concavity.
\end{verified}

## 2.10 Microstructure

Order-flow imbalance, queue position, **VPIN**, **Amihud illiquidity**
$\text{avg}(|r|/\text{volume})$, **Roll's spread**
$2\sqrt{-\text{Cov}(\Delta p_t,\Delta p_{t-1})}$, **Hasbrouck information
share**.

\begin{verified}{E-10, E-11 --- verified}
\textbf{Kyle's lambda.} Solving the joint fixed point of market efficiency and
informed optimality in \texttt{sympy} yields
$\lambda=\frac12\sqrt{\Sigma_0/\sigma_u^2}$ and
$\beta=\sigma_u/\sqrt{\Sigma_0}$. The report gives only the reduced form
$\Delta p=\lambda\cdot$(order flow); the structural result is the useful
intuition: price impact rises with the uncertainty being resolved and falls with
the noise-trader volume the informed trader can hide behind.

\textbf{Roll's spread} recovers the true bid-ask spread to within 0.4\% at every
level tested. Worth recording the assumption that breaks in practice: trade
directions must be serially \emph{independent}. Real order flow is strongly
autocorrelated because institutional orders are worked in slices, which biases
Roll's estimator downward --- often to the point of returning a positive
covariance and no estimate at all. It is a teaching model, not a production
spread estimator.
\end{verified}

![](figures/fig19_order_book_3d.pdf)

## 2.11 Backtest maths correctness

Log versus simple returns ($r_{\log}=\ln(1+r)$); **variance drain**
$g\approx\mu-\frac12\sigma^2$; correct annualisation; **Brinson attribution**;
precise cash, dividend and split accounting.

\begin{verified}{V-13 --- exact for GBM}
For $dS/S=\mu\,dt+\sigma\,dW$ the log growth rate is \emph{exactly}
$\mu-\frac12\sigma^2$. This is Itô's lemma, not an approximation.
\end{verified}

\begin{caveat}{V-14 --- but not for discrete simple returns}
The report does not say whether $\mu,\sigma$ are Itô parameters (where the
identity is exact) or sample moments of simple returns (where it is not). At
20\% volatility the error is 0.19 pp --- small, but not negligible against the
3.78 pp that V-15 attributes to volatility targeting. At 80\% volatility it
reaches 10.7 pp, or 66\% of the geometric return itself.

Use it as intuition for why volatility targeting aids compounding; never as the
P\&L accounting identity. The backtester must compound realised returns.
\end{caveat}

For scale: cutting realised volatility from 30% to 12% at an unchanged
arithmetic mean adds **3.78 percentage points** of compound annual growth purely
by removing drag, before any Sharpe improvement (V-15). That is the mechanical
component of the volatility-targeting benefit claimed in §2.3.

## 2.12 Where machine learning fits

**Fractional differentiation** (López de Prado — stationary while preserving
memory); **triple-barrier labelling**; **meta-labelling**; **sample uniqueness
and weights** from label overlap; **sequential bootstrap**; and the core reason
standard CV fails: temporal label overlap causes train/test leakage.

\begin{verified}{F-01 to F-03 --- verified}
The weight recursion $w_k=-w_{k-1}\frac{d-k+1}{k}$ reproduces the binomial
expansion of $(1-B)^d$ exactly at every $d$ tested, and collapses to the
ordinary first difference $(1,-1,0,\dots)$ at $d=1$.

The central claim holds with room to spare. Sweeping $d$ on a simulated
log-price series: \textbf{$d=0.20$ is enough to pass an ADF unit-root test at
5\% while retaining a correlation of 0.98 with the level series}, whereas the
standard returns transform ($d=1$) leaves 0.03. Essentially everything a model
could learn from the \emph{level} of the series is discarded by the conventional
transform.
\end{verified}

![](figures/fig20_frac_diff.pdf)

Note that the ADF threshold makes $d$ a data-dependent choice — that is, another
free parameter for the trial registry to count.

\clearpage

# 3. Platforms

## 3.1 Brokers and paper-trading APIs

| Broker | Paper | Assets | Rate limits | Gotchas |
|---|---|---|---|---|
| **Alpaca** | native paper env | US equities, options (paper), crypto | free 200 req/min; Algo Trader Plus to 10,000 | free data is **IEX-only (~2–5% of consolidated volume)**; SIP needs Algo Trader Plus (~\$99/mo); PFOF |
| **Interactive Brokers** | paper account | global multi-asset | ~50 msg/s pacing | TWS API / Client Portal Web API; use **ib\_async**; institutional-grade |
| Tradier | yes | equities/options | REST | good options; smaller ecosystem |
| TradeStation | yes | multi-asset | REST | approval friction |
| Schwab (thinkorswim) | yes | equities/options | OAuth | post-TDA migration; slow approval |
| Coinbase / Kraken / Binance | crypto | crypto | varies | 24/7, no PDT |
| Tradovate / Rithmic / CQG | some sims | futures | varies | pro-grade; pair with Databento |

**Decision:** use **IBKR Pro Tiered paper** for Stage 6 behind a
provider-neutral adapter. At the selected \$2,000--\$2,500 capital band, the
\$0.35 whole-share order minimum, pass-through fees, fractional-share rules,
cash-interest threshold, and margin financing are material model inputs rather
than implementation details.

## 3.2 Market-data vendors

| Vendor | Strength | ~Cost 2026 | PIT / survivorship |
|---|---|---|---|
| Polygon.io / Massive | raw OHLCV plus separately dated dividend actions | Starter \$29/mo (5 yr); Developer \$79 (10 yr); Advanced \$199 (all available) | daily archive starts 2003-09-10; dividend declaration/ex/record/pay dates |
| Databento | institutional tick/L2, direct feeds, ns timestamps | metered ~\$100–500/mo | best microstructure |
| Alpaca data | free IEX / paid SIP | free / \$99 | partial free volume |
| Tiingo | EOD + fundamentals + news | ~\$10–50/mo | good value |
| EODHD / FMP / Twelve Data | broad, cheap | \$10–50/mo | mixed quality |
| Norgate Data | **survivorship-bias-free** US equities/futures | tiered | **SBF** — key for backtests |
| CRSP | academic gold standard | institutional | SBF, delisting returns |
| FRED / **ALFRED** | macro; **ALFRED = vintage/PIT** | free | critical PIT macro |
| SEC EDGAR | filings/fundamentals | free | filing timestamps = natural PIT |
| ORATS / OptionMetrics / CBOE | options and IV surfaces | institutional | OptionMetrics = academic standard |

**Point-in-time data is make-or-break for Stage 2.** For Slice 01 use
**Polygon/Massive** corporate actions and raw (`adjusted=false`) OHLCV, plus
**ALFRED** with explicit vintage parameters for macro and financing inputs.
Massive Starter is sufficient for schema development but cannot cover the full
primary evaluation. The CIO fixed the primary sample to 2003-09-10 through
2026-08-11: one post-decimalization vendor and one cost regime, with no splice.
The 1993--2003 period is reserved for a separately licensed, separately frozen,
one-time earlier-regime robustness analysis and is never pooled. Resolve
Massive non-display/backtest, historical-NBBO, and immutable-storage permission
in writing before freezing M1. Use
**EDGAR filing timestamps** for later fundamentals work and **Norgate or CRSP**
for later survivorship-bias-free price universes. **yfinance is
prototyping-only** — personal-use terms, unofficial, rate-limited, and not
point-in-time.

## 3.3 Backtest and research frameworks: build versus adopt

| Framework | Type | Live parity | Verdict |
|---|---|---|---|
| **Nautilus Trader** | event-driven, **Rust core** + Python | **true backtest = live, no rewrite** | **strongest adopt candidate**; 16 venues incl. IBKR/Databento; steep learning curve; order-lifecycle state machines built in |
| QuantConnect LEAN | C\# engine, Python API, cloud | live via QC | most complete end-to-end; ecosystem lock-in |
| VectorBT / vectorbtpro | vectorised | none | fast **signal triage**, not execution |
| Zipline-reloaded | event-driven | limited | Pipeline API for factor research |
| Backtrader | event-driven | brokers | mature but **effectively EOL** — migrate off |
| Backtesting.py / bt / PyBroker | light | varies | bt good for allocation/rebalance |
| Qlib / FinRL / Lumibot / Hummingbot | ML/RL/crypto | varies | niche |

**Recommendation.** Adopt Nautilus Trader as the execution and backtest
engine. Its Rust core, event-driven order state machines, and backtest/live
parity address the main engine risk in this plan. Keep VectorBT upstream for
fast signal triage.

**Keep hand-rolling the point-in-time data layer (Stage 2) and the
statistical-validation layer (Stage 5)** — those are the differentiators and no
framework does them well. This is a "borrow the engine, own the science" split.

The verification results support this split. The engine-side mathematics
(Almgren--Chriss and the order state machines) verified cleanly and is a good
candidate for a mature library. The science-side mathematics is where the three
errors and most caveats appeared. That is the part to own, test, and understand
completely.

## 3.4 Data and compute infrastructure

Time-series store: **DuckDB + Parquet** is right for daily-ETF scale; ArcticDB
if you outgrow it; ClickHouse/QuestDB/TimescaleDB/kdb+ for larger needs. Table
format: Parquet + manifests; Delta/Iceberg optional. DataFrames: **Polars**
(Arrow-native, lazy) over pandas. Parallel backtests: **Ray** for parameter
sweeps. Orchestration: **Prefect** is fine; **Dagster** for asset-based lineage;
**Temporal** for durable execution of the order pipeline. Experiment tracking:
**MLflow** can back the Stage 5 trial registry rather than hand-rolling storage.

## 3.5 Deployment and secrets

Small always-on: **Hetzner** (best price/performance, ~€5–20/mo), DigitalOcean,
AWS Lightsail, GCP e2-small; a daily-EOD system can run on GitHub Actions cron
or a \$5 VPS. **Colocation is irrelevant** at this frequency. Docker for
reproducibility. Secrets: **SOPS + age** or 1Password CLI for a solo developer;
Vault and AWS Secrets Manager are overkill until multi-node.

## 3.6 Regulatory and compliance for a US individual

**Not legal advice. Verify with a professional and with your employer.**

- **Pattern Day Trader — major 2026 change.** The historical FINRA Rule 4210
  PDT framework (a pattern day trader = 4+ day trades in 5 business days in a
  *margin* account exceeding 6% of trades, requiring \$25,000 minimum equity)
  was, per SEC approval order 34-105226 (approved 14 April 2026) and FINRA
  Regulatory Notice 26-10, **eliminated effective 4 June 2026**, replaced by a
  real-time intraday-margin standard (broker phase-in permitted to 20 October
  2027). *Fast-moving — confirm current status with FINRA and your broker.* The
  general 25% maintenance margin and \$2,000 margin-account minimum remain.
- **Regulation T** (12 CFR 220): 50% initial margin on margin equity securities.
- **Wash sale rule** (IRC §1091 / IRS Pub 550): loss disallowed if a
  substantially identical security is bought within 30 days before or after (a
  61-day window); the disallowed loss adds to the replacement-share basis and is
  permanently lost if the replacement is in an IRA (Rev. Rul. 2008-5). Reported
  on **Form 8949** (code "W").
- **Section 1256 contracts** (regulated futures, broad-based index options such
  as SPX/VIX): 60% long-term / 40% short-term regardless of holding period, plus
  year-end mark-to-market; **Form 6781**.
- **Registration.** Trading only your own capital does **not** require
  investment-adviser registration. **Managing others' money** triggers RIA
  registration (state below ~\$100M AUM, SEC above) and typically Series 65; for
  futures or commodity pools, CTA/CPO registration with NFA/CFTC and typically
  Series 3.
- **SEC Market Access Rule 15c3-5** governs broker-dealers, not you — but it is
  the conceptual template for the pre-trade controls the system should mimic.
- **Form 8949 / 1099-B reconciliation:** reconcile broker-reported basis against
  your tax-lot accounting — a reason to build the tax-lot module (§6.4).
- **Market manipulation:** spoofing and layering are prohibited under CEA
  §4c(a)(5). Not a risk for long-only ETF strategies.
- **Broker terms and market-data redistribution:** most retail data licences
  forbid redistribution; automated trading is generally allowed but rate-limited.
- **Employment considerations:** personal-trading policies, preclearance,
  blackout windows and conflicts may apply. **Check your employer's compliance
  function before trading.**

\begin{verified}{A-10 --- the PDT test is stated correctly}
The historical rule is a \emph{conjunction}: 4+ day trades AND those exceeding
6\% of total trades. The report states both conditions, including the 6\% clause
that secondary sources frequently omit. Worked counterexample: 4 day trades out
of 50 total (8\%) triggers; 4 out of 200 (2\%) does not. Day-trade count alone
does not determine classification.

This verifies the report's internal logic only. The status of the framework
itself must be confirmed with FINRA and your broker.
\end{verified}

\clearpage

## 3.7 Minimum viable capital

Sections 3.1 and 3.2 chose a broker and a data vendor. This section asks what
those choices cost, and how much capital is needed before an edge survives them.

The question matters because a strategy can have a genuine, statistically real
edge and still lose money. Fixed costs do not scale with capital, so below some
account size the data subscription alone consumes the entire expected return.
That size is the **minimum viable capital**.

### The framework

Let $C$ be capital, $SR$ the expected Sharpe ratio of *excess* returns, and
$\sigma$ the target annualised volatility. Write $e$ for the fund expense ratio,
$\tau$ for annual one-way turnover as a fraction of capital, $s_{1/2}$ for the
half-spread paid per unit of traded notional, and $F$ for annual fixed costs:

$$\text{net expected profit}(C) = C\,(SR\,\sigma - e - \tau s_{1/2}) - F$$

Setting this to zero gives the break-even capital:

$$\text{MVC} = \frac{F}{SR\,\sigma - e - \tau s_{1/2}}$$

Check **MVC-02** confirms the algebra against a bisection solve. The formula's
*shape* is the finding. $SR$ sits in the denominator, so MVC is hyperbolic in
Sharpe: halving the expected Sharpe doubles the capital required. $F$ sits in
the numerator, so the capital floor is linear in recurring cost — and recurring
cost is chosen before any research begins.

At a Sharpe of 0.5 and a 12.5% volatility target, **every \$1/month of recurring
cost adds about \$193 to the capital needed to break even** (MVC-03). A
\$99/month market-data plan therefore carries a \$19,000 capital prerequisite.
That is the number to put in front of any subscription decision.

### Provider pricing

Read from vendor pricing pages on 21 August 2026, individual / non-professional
tiers. Pricing is dated and must be re-verified before use.

| Provider | Tier | \$/mo | EOD history | Quote data | Note |
|---|---|---:|---:|:---:|---|
| Massive (ex-Polygon) | Basic | 0 | 2 yr | — | 5 API calls/min |
| Massive | Starter | 29 | 5 yr | — | 15-min delayed |
| Massive | Developer | 79 | 10 yr | — | adds trades |
| Massive | Advanced | 199 | 20+ yr | yes | real-time; non-pro only |
| Massive | NYSE imbalances | 49 | — | — | auction order imbalances |
| **Tiingo** | **Starter** | **0** | **30+ yr** | — | 500 symbols/mo, 1k req/day |
| **Tiingo** | **Power** | **30** | **30+ yr** | — | 100k req/day, 40 GB/mo |
| Alpaca | Free | 0 | 7 yr | — | IEX only, 200 calls/min |
| Alpaca | Algo Trader Plus | 99 | 7 yr | yes | full SIP |
| Hetzner | CX22-class VPS | 6 | — | — | always-on host |

The single most consequential fact for a small account: **Tiingo's free tier
carries 30+ years of end-of-day history**, and its \$30/mo tier lifts the rate
limits without changing the history. Massive's 20+ year archive costs \$199/mo
because it is bundled with real-time and quote data, and a daily-frequency
strategy needs neither.

Quote data is required only to calibrate the spread term of the cost model.
That is a one-off measurement, not a subscription: buy one month, calibrate,
cancel. Treating it as recurring would raise the capital floor by roughly
\$38,000.

Note also that both Tiingo tiers are licensed **internal use only**, and
Massive's Advanced tier is non-professional only. Those terms, not the price,
are the binding constraint if the work is ever shared or commercialised.

### The capital ladder

![](figures/fig21_mvc.pdf)

Minimum viable capital by cost stack and Sharpe expectation (MVC-04), at a
12.5% volatility target on a 2 bp expense ratio and 200% annual turnover:

| Cost stack | \$/yr | $SR{=}0.8$ | $SR{=}0.5$ | $SR{=}0.3$ | $SR{=}0.2$ |
|---|---:|---:|---:|---:|---:|
| Tiingo Starter + laptop | 0 | — | — | — | — |
| Tiingo Power + laptop | 360 | \$3,600 | \$5,800 | \$9,700 | \$14,600 |
| Tiingo Power + VPS | 432 | \$4,300 | \$6,900 | \$11,600 | \$17,500 |
| Massive Advanced + VPS | 2,460 | \$24,700 | \$39,600 | \$66,200 | \$99,700 |
| Massive Adv + Alpaca Plus + VPS | 3,648 | \$36,600 | \$58,700 | \$98,100 | \$147,900 |

Nothing about the strategy changes between the second row and the fifth. Only
the subscription decision does, and it moves the capital floor by an order of
magnitude. Across the 0.3–0.8 Sharpe range section 4.8 calls realistic for a
solo operator, a lean stack implies a floor near \$3,600–\$9,700; the full
real-time stack implies \$36,600–\$98,100.

### Taxes, and why the account wrapper matters

The framework above omits tax, and the omission is not small. At ~200% annual
turnover essentially all gains are **short-term**, taxed as ordinary income.
Worse, for an individual without trader status the data subscription is **not
deductible** — the Tax Cuts and Jobs Act suspended miscellaneous itemized
deductions — so the fixed cost is paid with after-tax dollars while the profit
is taxed. After-tax profit is $(1-t)\,C\,r - F$, so the floor scales exactly
(MVC-09) as:

$$\text{MVC}_{\text{tax}} = \frac{\text{MVC}}{1-t}$$

| Blended short-term rate | MVC (lean stack, $SR{=}0.5$) | vs untaxed |
|---:|---:|---:|
| 0% | \$5,790 | — |
| 15% | \$6,812 | +18% |
| 24% | \$7,619 | +32% |
| **30%** | **\$8,272** | **+43%** |
| 37% | \$9,191 | +59% |

The practical consequence is a recommendation this report did not previously
make: **hold a strategy like this in a Roth IRA.** A high-turnover, long-only,
unlevered strategy is close to the ideal case for a tax-sheltered wrapper, where
$t=0$ and the drag disappears entirely. The usual objections — contribution
limits and restricted withdrawals — are nearly irrelevant at this account size,
for capital that is not needed back. *Nothing here is tax advice; confirm
treatment with a qualified professional.*

### MVC is an interval, not a number

The tables above report MVC at assumed point values of $SR$. That is precisely
the error check **S-14** identifies for PBO: reporting a statistic whose
sampling error dominates it. The correction matters more here than there,
because $\text{MVC}\propto 1/SR$ — the uncertainty in the Sharpe is *amplified*
rather than damped.

Propagating the Lo (2002) standard error through the formula (MVC-11), at
$\widehat{SR}=0.5$ on the lean stack with 30% tax:

| Sample length | 95% CI on $SR$ | 95% interval for MVC |
|---|---|---|
| 3 years | $[-0.63, +1.63]$ | \$2,525 — **unbounded** |
| 5 years | $[-0.38, +1.38]$ | \$2,994 — **unbounded** |
| 10 years | $[-0.12, +1.12]$ | \$3,682 — **unbounded** |
| 20 years | $[+0.06, +0.94]$ | \$4,397 — \$68,000 |

**With ten years of daily data the Sharpe interval still contains zero, so the
capital floor has no finite upper bound.** No amount of capital is provably
sufficient. Only at roughly twenty years does the interval close.

Two readings follow. The point values in the ladder above remain useful as a
*ranking* of cost stacks against each other — which is what they are actually
for — but they must not be read as a capital requirement. And the operationally
useful number is the **lower** bound: even at the optimistic end of a ten-year
Sharpe interval the floor is \$3,682, which already exceeds the \$3,000
starting capital.

### The verdict at \$3,000

At \$3,000 with a Sharpe of 0.5 and a 12.5% volatility target, expected gross
excess return is **\$188/year**. Against that (MVC-05):

| Cost stack | Fixed \$/yr | Net \$/yr (untaxed) | Net \$/yr (after 30% tax) |
|---|---:|---:|---:|
| Tiingo Starter + laptop | 0 | **+187** | **+131** |
| Tiingo Power + laptop | 360 | −173 | −229 |
| Tiingo Power + VPS | 432 | −245 | −301 |
| Massive Advanced + VPS | 2,460 | −2,273 | −2,329 |

A \$30/month data plan costs \$360/year — roughly double the entire expected
return. The account loses money in expectation *even if the edge is completely
real*.

This is the central practical finding of the section. At small capital the
binding constraint is not the market, the broker, or the strategy. It is the
vendor invoice. The only configuration that survives at \$3,000 is free data on
existing hardware, which for a single-ETF daily strategy is genuinely
sufficient. Commission is not the issue once the broker is zero-commission; the
recurring fixed cost is.

### A second floor: share granularity

Costs are not the only constraint. Volatility targeting requires continuously
adjustable exposure, and whole shares quantise it (MVC-06):

| Capital | Shares of SPLG at \$78 | One share as % of book | Vol tracking error |
|---:|---:|---:|---:|
| \$1,000 | 12 | 7.8% | 0.34% |
| \$3,000 | 38 | 2.6% | 0.11% |
| \$10,000 | 128 | 0.8% | 0.03% |

Instrument choice does most of the work here. SPLG at \$78 clears a 10%-of-target
threshold at \$3,000, whereas an S&P 500 ETF priced near \$600 would leave five
shares and a 0.87% volatility tracking error — a 7% relative miss on the exact
quantity the strategy exists to control. Reliable fractional-share support
removes this floor entirely, which is a concrete reason to verify fractional
order handling before committing to an instrument.

### Capital and cost by build phase

| Phase | Trading capital | Recurring \$/yr | Note |
|---|---:|---:|---|
| M0 governance | 0 | 0 | registry, contracts, CI |
| M1 slice research | 0 | 559 | includes one month of quote data |
| M2 hardening | 0 | 360 | no new data requirement |
| M3 sleeves 2–3 | 0 | 360 | same universe scope |
| M4 allocation | 0 | 360 | no new data requirement |
| M5 paper portfolio | 0 | 432 | always-on host for reconciliation |
| M6 live minimum | 3,000 | 432 | sized to measure execution |
| M7 scale | above MVC | 432 | capital above MVC for achieved Sharpe |

Milestones M0 through M5 require **no trading capital at all** — only the
recurring cost (MVC-07). That is the scheduling insight hiding in the
arithmetic: the capital constraint does not bind until M6, roughly six to nine
months into the build, so capital accumulation and platform construction can run
in parallel.

### What MVC does not answer

Clearing the MVC bar makes a strategy economically viable. It does not make the
result measurable. At \$3,000 the expected annual profit is \$188 against a
\$375 standard deviation — the noise is twice the signal — and reaching a
$t$-statistic of 2 on live P&L would take **16 years** at a true Sharpe of 0.5
(MVC-08). Scaling capital scales expectation and dispersion identically, so no
amount of capital makes live P&L informative faster.

This is check S-11 arriving from a different direction, and it is why milestone
M6 is defined as validating the cost model and the execution path rather than
the edge. MVC answers *will this lose money by construction?* It does not answer
*does the edge exist?*, and the two questions should never be conflated in a
promotion decision.

\clearpage

# 4. Risk

## 4.1 Model risk management adapted from SR 11-7

The Fed/OCC **SR 11-7** guidance provides a useful structure even for a solo
operator. The relevant pieces are model definition, independent challenge,
inventory, validation, monitoring, and documentation. A signal, cost model, or
machine-learning component is a model when it turns inputs into an estimate.

For this project, the first line is the implementer and author. The second line
is an independent adversarial review, preferably using a different model and a
different implementation path. The third line is CI, periodic self-audit, and
the promotion state machine.

![](figures/fig11_three_lines.pdf)

Maintain a model inventory (each strategy, its assumptions, limitations, and
validation date) and a revalidation cadence.

This report follows the same pattern. Its verification suite acts as a second
review of the mathematics and found three errors that first-line review had
missed. The result is a concrete reason to keep the review boundary in the
system.

## 4.2 Risk taxonomy

Market, liquidity, execution, model, **data** (vendor error, revisions, PIT
violations), operational, technology, counterparty/broker, **key-person**,
regulatory, cyber, and **AI-agent risk**: prompt injection into research agents,
hallucinated logic silently merged, **silent scope creep** (an agent
"helpfully" changes a risk limit), agentic tool misuse.

Mitigation for the last: the deterministic runtime (no LLM in the execution
path), schema-validated agent outputs, and the review gate.

## 4.3 Pre-trade risk controls (mirroring 15c3-5)

Fat-finger notional limits, maximum order notional and size, maximum position,
maximum daily loss, maximum drawdown, gross and net exposure limits, per-name
concentration (the 20%/ETF cap), restricted lists, **price collars** (reject
orders far from last), and order-rate limiting — **all enforced
deterministically, pre-submission, outside the strategy code.**

## 4.4 Kill switches and circuit breakers

- **State persisted outside process memory** (database or Redis) so a restart
  cannot "forget" it is halted — the single most important reliability pattern.
- **Dead-man's switch / heartbeat:** if the strategy stops heartbeating,
  flatten or halt.
- **Market-wide halts:** respond correctly to **LULD** bands and **Rule 80B**
  market-wide circuit breakers.

\begin{verified}{A-09 --- internally consistent, and one detail matters}
The three levels are correctly ordered ($-7\%$, $-13\%$, $-20\%$) and the
time-of-day carve-out correctly applies only to Levels 1 and 2. Per
SEC/Investor.gov: a Level 1 or 2 breach \emph{before} 3:25 p.m. ET halts trading
market-wide for 15 minutes; the same breach \emph{at or after} 3:25 p.m. does
\textbf{not} halt; a Level 3 breach halts for the remainder of the day at any
time.

The asymmetry is the operationally important part. A system assuming "a 7\% drop
means the market stops" will keep trading into a cascading close. Since this
system trades the MOC auction at roughly 15:50 ET, \textbf{the carve-out lands
squarely inside its execution window} --- making it a required test case, not
background reading. Thresholds are recalculated daily from the prior S\&P 500
close, so they must be fetched, never hardcoded.
\end{verified}

## 4.5 Reconciliation and idempotency engineering

Exactly-once order semantics via **idempotency keys** (client order IDs),
**duplicate-order rejection**, the **outbox pattern** (persist intent before
sending), **two-phase state machines** with persisted transitions, periodic
position reconciliation (diff internal against broker positions), and
**recovery from unknown broker state** (on restart: query the broker,
reconcile, only then resume). Chaos-test by killing the process mid-order.

![](figures/fig10_state_machine.pdf)

## 4.6 Case studies to engineering lessons

| Event | What happened | Lesson |
|---|---|---|
| **Knight Capital (2012)** | Manual deploy left dead "Power Peg" code on 1 of 8 SMARS servers; a reused feature flag reactivated it. Per SEC Admin. Proc. 34-70694: while processing just **212 parent orders**, SMARS sent millions of child orders, resulting in **4 million executions in 154 stocks for more than 397 million shares in approximately 45 minutes**; Knight "lost over \$460 million" and paid a \$12M Market-Access-Rule settlement; no kill switch; warning emails ignored | automated, verified, all-or-nothing deploys; fully remove dead code; never reuse flags; a kill switch; alerts that page, not email |
| **LTCM (1998)** | extreme leverage, correlated convergence trades, stable-correlation models | leverage kills; correlations $\to1$ in crises |
| **Flash Crash (2010)** | liquidity evaporation and feedback loops | model liquidity as fragile; don't assume fills at last price |
| **XIV / Volmageddon (2018)** | a volatility spike wiped out inverse-VIX ETNs | understand product mechanics and tail convexity |
| **Archegos (2021)** | concentration plus hidden swap leverage | concentration limits matter |
| **Amaranth (2006)** | concentrated natural-gas spread bets | position and concentration limits |
| **Quant Quake (Aug 2007)** | crowded factor unwinds hit everyone at once | crowding and capacity risk |
| **Negative oil (2020)** | systems could not represent negative prices | test edge cases (negative/zero prices, splits) |

## 4.7 Backtest overfitting is the dominant risk

The **seven sins of quantitative investing**; survivorship, look-ahead and
restatement bias; data snooping; selection bias under the null.

- **McLean & Pontiff (2016, *Journal of Finance* 71(1):5–31)**, 97 published
  predictors: *"Portfolio returns are 26% lower out-of-sample and 58% lower
  post-publication. ... We estimate a 32% (58%–26%) lower return from
  publication-informed trading."*
- **Hou, Xue & Zhang (2020, *Review of Financial Studies* 33(5):2019)**, 452
  replicated anomalies: *"65% of the 452 anomalies ... cannot clear the single
  test hurdle of the absolute t-value of 1.96. Imposing the higher multiple test
  hurdle of 2.78 at the 5% significance level raises the failure rate to 82%."*
- **Harvey–Liu–Zhu:** with hundreds of factors tested, raise the bar to
  $t>3.0$.

\begin{verified}{A-07, A-08 --- arithmetic verified}
McLean \& Pontiff's decomposition is internally consistent ($58-26=32$), and the
32\% figure is the one carrying the argument: it isolates the portion of decay
attributable to \emph{publication} rather than to data mining.

Converting Hou--Xue--Zhang to counts: 294 of 452 anomalies fail the single test,
and 371 of 452 fail the multiple-testing hurdle --- \textbf{a further 77
casualties from raising $|t|$ from 1.96 to 2.78, leaving roughly 81 of 452
standing}. That is the empirical anchor for the $t>3.0$ recommendation, and the
single most persuasive argument in the report for building §2.8's deflation
machinery \emph{before} writing any strategy.
\end{verified}

## 4.8 Capacity, crowding, realistic expectations

Retail has an **edge in capacity-constrained niches** (small size means
negligible impact — verified quantitatively in E-09: 0.18 bp on a \$10,000 ETF
order) and a **disadvantage in crowded factor trades** (no scale, cost, or
financing edge).

**Realistic solo expectation after costs:** most retail systematic strategies
that survive honest validation land at **low single-digit net Sharpe
(~0.3–0.8)**. A persistent net Sharpe above 1 after DSR/PBO deflation is
exceptional and should be treated with suspicion until proven live.

Set that against S-11: at a true Sharpe of 0.5 it takes **11 years** of live
data to confirm the strategy is not noise at 95% confidence.

## 4.9 Behavioural and process controls

Predefined shutdown criteria (maximum drawdown, $N$ consecutive losing months,
live-versus-backtest tracking-error breach); a written "when do I stop" rule
*before* deploying; no discretionary override of the deterministic limits.

## 4.10 Production risk monitoring

Rolling Sharpe; realised drawdown against the expected-drawdown distribution;
**live-versus-backtest tracking error**; **signal-decay** monitoring;
**feature drift / PSI**; execution slippage against modelled slippage; and
**CUSUM/EWMA statistical-process-control charts** to detect degradation before
it becomes a drawdown.

![](figures/fig13_cusum.pdf)

\clearpage

# 5. Latency

## 5.1 Taxonomy

| Tier | Frequency | Acceptable latency | Technology | You? |
|---|---|---|---|---|
| Daily / EOD | 1/day | **seconds–minutes** | Python, REST, cron | **YES — this is you** |
| Intraday / swing | min–hr | sub-second–seconds | WebSocket, async | maybe later |
| High-frequency | ms--$\mu$s | microseconds | C++/Rust, kernel bypass, colo | no |
| Ultra-low-latency | $\mu$s--ns | **nanoseconds** | **FPGA/ASIC**, colo, microwave | career only |

## 5.2 Where latency comes from

Feed handler and decoding, network propagation (**~5 $\mu$s/km in fibre**), NIC and
kernel network stack, OS scheduling jitter, GC and interpreter overhead,
serialisation, database writes, broker-side latency.

\begin{verified}{A-04 --- verified}
Speed of light divided by the group index of single-mode fibre ($n=1.4675$)
gives \textbf{4.90 $\mu$s/km}. The report's rounding is correct and standard. For
reference the vacuum figure is 3.34 $\mu$s/km, which is why hollow-core fibre and
microwave links --- both closer to $c$ --- are worth their cost to HFT firms.
\end{verified}

## 5.3 Concrete numbers

- Retail **REST round-trip: tens to hundreds of ms**; WebSocket streaming lower
  but still ms.
- Kernel-bypass software (Solarflare X2522 + OpenOnload): **~just under 2 $\mu$s**
  tick-to-trade.
- **FPGA tick-to-trade: 100–500 ns end-to-end**; the best firms reach
  single-to-double-digit ns; AMD Alveo **UL3524 delivers <3 ns transceiver
  latency** (UL3422 ~2.34 ns); Exegy + AMD recorded a **13.9 ns** STAC-T0
  actionable latency.
- Kernel bypass: Solarflare/Onload, DPDK, io\_uring, AF\_XDP; plus busy-polling,
  CPU pinning/isolcpus, NUMA awareness, hugepages.

\begin{verified}{A-05 --- internally consistent}
The tiers are strictly ordered and span $3\times10^{7}\times$ from retail REST
to transceiver latency. Two cross-checks: the quoted 13.9 ns STAC-T0 figure
exceeds the 3 ns transceiver figure, as it must --- the transceiver is one
component of the path, not the whole path --- so the two adjacent numbers are
not in conflict.
\end{verified}

![](figures/fig08_latency_spectrum.pdf)

## 5.4 Measurement methodology

Hardware timestamping (**PTP/IEEE 1588**, PPS), Corvil/Beeks-style monitoring,
**percentile discipline (p50/p99/p99.9/max)** — tail latency kills, not the
mean — **coordinated omission** awareness, **HdrHistogram**, and eBPF probes for
zero-blocking telemetry.

## 5.5 Protocols and feeds

FIX (text) versus binary; **ITCH/OUCH** (Nasdaq), **PITCH** (Cboe), **CME MDP
3.0 / iLink 3**, **SBE**. A retail trader gets REST and WebSocket; ITCH/OUCH and
colocation require exchange membership or sponsored access.

## 5.6 Appendix — hardware-accelerated trading

The **SystemVerilog trading engine with fixed-function FPU** and the **FPGA
market-data replay / limit-order-book prototype (Aegis-Stream)** map almost
exactly onto real HFT FPGA stacks: a five-stage tick-to-trade pipeline (network
ingress → market-data parse → order-book maintenance → signal evaluation → order
transmit), each stage pipelined and parallelised. The lowest-latency critical
paths are still **hand-written RTL** (HLS narrows but does not close the gap).

Hardware: AMD/Xilinx **Alveo UL3524/UL3422**, Solarflare X2/X3 NICs,
Exablaze/Cisco Nexus SmartNICs, **Arista 7130 / Metamako** layer-1 switches; IP
cores from **Enyx, Exegy, NovaSparks, Xelera**.

**FPGA versus ASIC:** FPGAs reload in seconds (fast iteration); ASICs give
deterministic nanosecond latency but no reconfiguration — only top firms tape
out.

**Career angle.** FPGA/RTL trading roles at **Jane Street, Jump Trading, Citadel
Securities, Optiver, IMC, Hudson River Trading, Tower Research, DRW, XTX, Maven,
Quantlab**. They want RTL fluency, comfort with order-book and trade-feed
structures and FIX/OUCH/ITCH, hardware/software co-design, and quantitative
communication. **Aegis-Stream is a strong interview artefact** — a
portfolio-grade (not production) low-latency LOB and market-data replay is
exactly what these firms respect.

Figure 19 (§2.10) shows the limit-order-book state this engine reconstructs: a
depth surface through a liquidity withdrawal, with the derived microstructure
features. That figure is the bridge between the two halves of the portfolio.

## 5.7 What latency budget this system actually needs

**For the Stage 1–9 daily ETF system, a latency budget of seconds to minutes is
entirely appropriate.** The real bottlenecks:

1. **Data availability** — when the vendor publishes the EOD bar and the PIT
   snapshot is ready.
2. **Workflow scheduling** — Prefect flow timing relative to market close.
3. **Broker fill timing** — **MOC/MOO cutoffs** (NYSE MOC ~15:50 ET) are the
   true hard deadlines; miss the cutoff and you don't trade.
4. **Order acknowledgment** — seconds is fine.

\begin{verified}{A-06 --- the ratio worth quoting}
A \textasciitilde{}10-minute pre-MOC decision budget is
$\mathbf{2\times10^{11}}$ times the fastest latency this report discusses.
Optimising microsecond latency here would be premature optimisation of the
highest order --- adding complexity and risk (recall Knight) for zero economic
benefit. Spend that engineering on data correctness and overfitting control.
\end{verified}

Note the interaction with §4.4: the Rule 80B carve-out at 3:25 p.m. ET falls
*inside* the MOC execution window. The system's binding real-time constraint is
not latency at all — it is a regulatory boundary measured in minutes.

\clearpage

# 6. Extensions and next work

The platform is only useful if it moves toward a falsifiable research result.
The additions in this section are therefore engineering work with a direct
connection to that goal: tests that block silent errors, missing lifecycle
stages, candidate strategy sleeves, and a way to present the project without
turning a verified platform into a claim of profitability.

## 6.1 Agentic development workflow upgrades

- **Spec-driven development** (GitHub Spec Kit style): write the spec first, let
  agents implement against it — pairs with the AGENTS.md/CLAUDE.md split.
- **Test-first agent workflow:** Claude writes the failing adversarial test,
  Codex implements to green — enforces writer $\neq$ reviewer at the test level.
- **Property-based testing (Hypothesis)** for financial invariants: "weights
  sum $\le$ gross limit", "no position exceeds 20%", "cash never negative", "no
  future timestamp used in a signal". The SVA analogue.
- **Hypothesis stateful testing** for the order state machine.
- **Mutation testing (mutmut / cosmic-ray)** to validate that the *tests* catch
  bugs.
- **Formal methods for the order state machine:** **TLA+/PlusCal** or **Alloy**
  to model-check exactly-once and idempotency under crash and retry.
- **Differential testing** against a reference backtester.
- **Metamorphic testing** (scaling all prices implies predictable P&L scaling),
  **deterministic simulation testing** (seed all randomness, replay the whole
  day), **fuzzing broker responses**, **golden/approval testing** of reports.

\begin{keybox}{Property tests the verification suite specifically recommends adding}
Each of these would have caught a defect found in this exercise, and each is a
few lines:
\begin{itemize}
\item \textbf{Causal recomputation.} Assert the signal at time $t$ is
bit-identical when the input sample is truncated at $t$. Catches G-01 (smoothed
vs filtered) and every other state-space look-ahead.
\item \textbf{Gaussian reduction.} Assert the PSR denominator equals
$\sqrt{1+\widehat{SR}^2/2}$ on Gaussian input, and that a Gaussian sample
returns $\gamma_4\approx3$. Catches S-04.
\item \textbf{Quantile monotonicity.} Assert the VaR/CVaR quantile function is
non-decreasing in confidence, and $\text{VaR}\le\text{CVaR}$. Catches Q-08 and
pins down Q-02's sign convention.
\item \textbf{Round-trip inversion.} For any estimator that inverts a discrete
recursion (OU half-life, $\kappa$, GARCH persistence), assert that simulating
from the recovered parameters and re-estimating returns the original. Catches
M-04 --- and this is the single highest-value invariant, because it covers the
entire class where all the errors clustered.
\item \textbf{Null calibration.} Assert that a test with no signal rejects at
its nominal rate. Catches M-05 (57\% versus 5\%).
\end{itemize}
\end{keybox}

## 6.2 Verification-engineering transplant

The UVM mindset: **coverage-driven verification** (track which market and
strategy states the tests exercise), **constrained-random stimulus** (Hypothesis
is the generator), **assertions** (runtime invariant checks = SVA),
**scoreboards** (an independent model predicts expected P&L and positions and
checks against actual), and **formal property verification** (TLA+/Alloy).

The useful claim here is concrete: verification ideas from hardware work well
when translated into independent reference models, coverage, assertions, and
state-machine checks. This report is one example. Its suite reimplemented the
formulas independently and found three errors in a document that had already
been reviewed.

## 6.3 CI/CD and supply chain

**SLSA provenance**, **sigstore/cosign** signing, **pip-audit / safety** for
CVEs, **SBOM (CycloneDX / Syft)**, **Dependabot/Renovate**, **hash-pinned**
dependencies, **reproducible builds**, and pre-commit **secret scanning**
(detect-secrets, gitleaks, trufflehog).

## 6.4 Missing stages and sub-stages to add

- **Stage 2.5 — Tax-lot accounting module** (FIFO/specific-ID, wash-sale
  tracking, Form 8949 / 1099-B reconciliation).
- **Stage 3.5 — Corporate-action edge-case module** (splits, spinoffs, special
  dividends, symbol changes, ETF reconstitutions) with a golden test set.
- **Stage 4.5 — Options-overlay design stage** (explicitly deferred; document
  the interface now).
- **Stage 5.5 — Strategy-decommissioning process** — a written, gated way to
  retire a degraded strategy.
- **Stage 7.5 — Data-vendor migration abstraction** — a provider-neutral data
  interface so swapping Polygon $\leftrightarrow$ Databento $\leftrightarrow$
  Norgate is configuration, not rewrite.
- **Stage 9.5 — Backtest-to-live divergence harness.**

## 6.5 Alternative strategy sleeves

Methodology, not recommendations. Carry; cross-asset trend;
seasonality/turn-of-month; the **low-volatility anomaly**; term-structure and
roll-yield via ETFs; tail-hedge overlays; **cross-sectional ETF momentum**;
defensive/risk-off rotation; and **pairs / statistical arbitrage on cointegrated
ETF pairs**.

**Cointegration.** **Engle–Granger** two-step — OLS $Y_t=\alpha+\beta X_t+u_t$,
then an ADF unit-root test on the residual $u_t$. **Johansen** (VECM
$\Delta x_t=\Pi x_{t-1}+\sum\Gamma_i\Delta x_{t-i}+u_t$; the rank of $\Pi$ is
the number of cointegrating vectors; trace and max-eigenvalue statistics) —
detects multiple relationships and needs no choice of dependent variable.

\begin{finding}{M-05 --- Engle--Granger needs its OWN critical values}
The report describes the two-step procedure correctly but does not warn that
step two requires cointegration critical values, not standard ADF ones. Because
$u_t$ is a \emph{fitted residual}, OLS has already minimised its variance,
making it look more stationary than it is.

Testing 3,000 pairs of \textbf{independent random walks}, where the true
cointegration rate is 0\%:

\vspace{0.4em}
\begin{center}\small
\begin{tabular}{@{}lr@{}}
\toprule
Naive ADF critical values & rejects \textbf{57.0\%} of the time \\
Proper Engle--Granger critical values & rejects \textbf{4.7\%} of the time \\
\bottomrule
\end{tabular}
\end{center}
\vspace{0.4em}

An 11$\times$ over-rejection. For a solo operator screening a few hundred ETF
pairs, that is a guaranteed pipeline of pairs that look tradeable and are not.

\textbf{Fix.} Use \texttt{statsmodels.tsa.stattools.coint} (which applies
MacKinnon's Engle--Granger surfaces) or the Johansen test. Never
\texttt{adfuller} on a regression residual. And note the interaction with §2.8:
\textbf{screening pairs IS a trial count}, and must be registered as one.
\end{finding}

\begin{verified}{M-06 --- Johansen verified}
The trace test recovers the correct rank in 85\% of simulated three-variable
systems built with exactly one cointegrating relationship. Prefer Johansen: it
needs no choice of dependent variable, and --- decisively, given M-05 --- it is
much harder to get the inference wrong.
\end{verified}

**Ornstein–Uhlenbeck spread:** $dX_t=\theta(\mu-X_t)\,dt+\sigma\,dW_t$;
stationary distribution $\mathcal N(\mu,\sigma^2/2\theta)$; half-life of mean
reversion $=\ln 2/\theta$.

\begin{verified}{M-01, M-02 --- verified}
The stationary mean and the variance $\sigma^2/2\theta$ both confirmed by exact
simulation. This is what makes the $z$-score in the entry rule well defined: the
spread has a genuine stationary scale to normalise by, which a non-cointegrated
pair does not.
\end{verified}

\begin{verified}{M-03, M-04 --- exact half-life inversion verified}
For unit spacing use $-\ln 2/\ln(1+\lambda)$, not the Euler approximation
$-\ln 2/\lambda$; for general spacing multiply the numerator by $\Delta t$.
The exact inversion recovers simulated OU half-lives, while M-04 verifies that
the discarded approximation is always too long and worsens with reversion speed.
\end{verified}

**Signal:** $z_t=(Z_t-\text{mean}(Z))/\text{std}(Z)$ on spread
$Z_t=Y_t-\beta X_t$; illustrative entry at $|z|\approx2$, exit toward 0, stop
near $|z|\approx3$ (thresholds are parameters, not rules). **Kalman filter** for
a dynamic hedge ratio $\beta_t$.

\begin{verified}{M-07 --- verified}
A Kalman filter tracks a random-walk $\beta_t$ with a structural break
\textbf{3.3$\times$ more accurately} (RMSE) than the best rolling-OLS window
tested. The mechanism is worth stating: rolling OLS faces an unavoidable
bias--variance choice through its window length --- short windows are noisy,
long windows lag the break --- whereas the Kalman gain adapts automatically,
widening after a surprise and narrowing in quiet periods.

The cost is two variance parameters ($q$ and $r$) that must themselves be
estimated, and which are exactly the kind of free parameter §2.8's trial
registry needs to count.
\end{verified}

## 6.6 How to present the work

The public part of the project can include the deterministic backtester,
point-in-time data-layer design, property-based and formal tests for the order
state machine, the DSR/PBO validation library, Aegis-Stream, and this
verification suite. Keep any real signal, parameter set, and live result
private until the data and disclosure risks are understood.

When the work is shown to someone else, lead with the engineering evidence:
what was specified, what was tested independently, which errors were found,
and how the promotion gate handles an attractive but unreliable backtest. A
high Sharpe ratio without that record is a result to investigate, not a result
to present as proof.

## 6.7 Cost control for agentic development

**Prompt caching** (a stable system-prompt prefix hits the cheaper cache rate),
**batch APIs** (40–60% off for asynchronous test generation and refactors),
**context and session hygiene**, **model routing** (mechanical work to
free/flash tiers, hard reasoning to frontier), and off-peak scheduling before
DeepSeek's announced peak surcharge lands.

\begin{verified}{A-01 --- provider-specific cache discounts verified}
At the prices in Section 1.2, cache-hit input is
\textasciitilde{}98--99\% cheaper on DeepSeek and
\textasciitilde{}75--90\% cheaper on GLM/Kimi. A-01 recomputes these ranges
from the table.
\end{verified}

\begin{caveat}{A-03 --- and route the optimisation to the right cost driver}
On cheap flash tiers input cost dominates, so context hygiene and caching are
the lever. On premium tiers output dominates, so limiting verbose output is.
Detailed in §1.8.
\end{caveat}

\clearpage

# 7. System architecture

![](figures/fig09_architecture.pdf)

The diagram shows the boundary that governs the design: **agentic tooling writes
the system, but never runs inside it.** Everything in the deterministic region
is reproducible from a seed. Agents operate during development, behind review
and CI.

That boundary keeps prompt injection, hallucinated logic, and scope changes in
the development process, where they can be reviewed. None should be allowed to
become a runtime decision that is discovered after a loss.

\clearpage

# 8. What to build next

The evidence supports a limited conclusion. The platform design is coherent,
and the verification suite found three mistakes that would have survived an
ordinary review. That makes the research process safer. It does not show that
any strategy has a positive expected return.

The next milestone should therefore be one empirical vertical slice, not a
larger survey. Freeze a liquid universe and a data source. State why the signal
could exist. Compare it with a simple baseline. Then evaluate it with
point-in-time data, purged walk-forward splits, realistic costs and borrow, and
a paper-trading period long enough to measure the gap between the simulation
and the broker.

Until that result exists, the build priorities are:

1. **Use Nautilus Trader for the execution and backtest core.** Keep the
   point-in-time data layer and the statistical-validation layer under direct
   control. The engine-side tests passed cleanly; the errors were in the
   research assumptions and formulas.
2. **Put the model-routing boundary in place.** Use lower-cost hosted models
   for generic code, a different model or vendor for adversarial review, and
   self-hosted weights when prompts contain strategy data.
3. **Finish the overfitting controls before searching for a signal.** Implement
   DSR, PBO/CSCV, purged cross-validation with an embargo, and a trial registry.
   Record abandoned configurations as well as the ones that look promising.
4. **Build pre-trade limits, kill switches, and reconciliation as deterministic
   state machines.** Persist the halt state outside process memory and recover
   from unknown broker state before resuming.
5. **Apply the corrected formulas and property tests.** Use an L1 cost model or
   an explicit band for no-trade behaviour, the exact OU half-life inversion,
   proper Engle--Granger critical values, non-excess kurtosis in PSR, and the
   five tests in Section 6.1.

Several conditions would change this plan. A move to intraday or sub-second
trading would make latency and microstructure the next research problem. If
development spend passes roughly $300 per month, more work should move to
self-hosted weights and batch APIs. A live-versus-backtest tracking error
breach or a CUSUM alarm should start the strategy-decommissioning process.
Managing outside capital would introduce a separate legal and compliance
question that requires professional advice before the scope changes.

The project is strongest when it is described accurately: a verification-led
research system designed to find out whether one hypothesis survives. That is
already a useful artifact. The trading claim, if one ever follows, has to be
earned by the data.

\vspace{1em}
\begin{center}\footnotesize\color{muted}
\emph{Reminder: general methodology only. Nothing here recommends trading or
investing, and all regulatory and tax points must be confirmed with a qualified
professional and with your employer's compliance function.}
\end{center}

\clearpage

# Appendix A — Complete verification results

All 115 checks, in the order they run. Reproduce with
`python3 verify/run_all.py`.

\input{out/generated/table_full.tex}

\clearpage

# Appendix B — Detail for every remaining caveat

Full method, expected value, measured value and recommendation for each of the
nine caveats. The three corrected defects are documented in Part I and retained
as passing regression checks in Appendix A.

\input{out/generated/notes.tex}

\clearpage

# Appendix C — Verification suite structure

| Module | Report sections | Checks |
|---|---|---:|
| `v01_returns_vol.py` | 2.1, 2.2, 2.11 | 19 |
| `v02_sizing.py` | 2.3, 2.6 | 11 |
| `v03_portfolio.py` | 2.4 | 13 |
| `v04_risk.py` | 2.7 | 9 |
| `v05_validation.py` | 2.8 | 15 |
| `v06_execution.py` | 2.9, 2.10 | 12 |
| `v07_meanrev.py` | 6.5 | 7 |
| `v08_ml_regime.py` | 2.5, 2.12 | 8 |
| `v09_report_arithmetic.py` | 1, 3.6, 4, 5 | 10 |

Verification methods used, in order of strength:

1. **Symbolic proof** (`sympy`) — the strongest available. Used for the
   Markowitz closed form, both Kelly forms, the fractional-Kelly growth
   identity, the Almgren–Chriss stationarity condition, Kyle's lambda, and the
   square-root law. A symbolic result is an identity, not a coincidence.
2. **Independent numerical solve** — re-derive the answer with an optimiser that
   assumes nothing about the closed form, then compare. Used for Almgren–Chriss
   (agreement to $6.6\times10^{-13}$), ERC, the transaction-cost objective, and
   the Minimum Track Record Length.
3. **Monte Carlo against a known generating process** — construct data whose
   true parameters are known by design, then check the estimator recovers them.
   Used for every volatility estimator, the Sharpe standard error, the False
   Strategy Theorem, PBO calibration, Roll's spread, and the OU half-life.
4. **Null-calibration testing** — feed a procedure data containing no signal
   and confirm it says so. This is how M-05 (57% versus a nominal 5%) and S-15
   (purged CV) were found, and it is the most productive single technique in the
   suite.
5. **Richardson extrapolation** — where an estimator is only unbiased in a
   limit, sweep the discretisation and extrapolate. Used to separate genuine
   estimator bias from sampling artefact in the range volatility estimators.

\vspace{1em}

\begin{keybox}{Determinism}
Master seed \texttt{20260811}. Every random stream in the suite is derived from
it via \texttt{numpy.random.default\_rng([MASTER\_SEED, stream\_id])}, so
streams are independent and reproducible. With the pinned requirements, the
reported rounded values reproduce; numerical-solver residuals may differ in
their last bits across BLAS/platforms, and are checked with explicit tolerances.
All verification tables and counts come from the suite's JSON output;
explanatory prose repeats selected values and must be reviewed when a check
changes.
\end{keybox}
