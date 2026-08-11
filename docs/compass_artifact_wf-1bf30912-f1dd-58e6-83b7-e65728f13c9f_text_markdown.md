# Building a Deterministic Quant Research & Paper-Trading Platform with Agentic Coding Assistants: An Expanded Research Report

*Methodology note: This report concerns software engineering, quantitative methodology, and tooling. Nothing here is investment advice or a recommendation to trade or invest. All pricing/capability figures are dated; the LLM market in 2026 moves weekly and several model names appearing in search results are of uncertain provenance (aggregator/SEO pages) — treat any single-source pricing as provisional and verify against official vendor pages before committing budget.*

## TL;DR
- **Keep the runtime deterministic and keep the plan's architecture; change the *development* economics.** Route bulk agentic coding to cheap Chinese open-weight APIs (DeepSeek V-series ~$0.14–0.44/1M input; GLM/Qwen/Kimi coding plans ~$10–80/mo flat) via Anthropic/OpenAI-compatible proxies, but keep architecture/adversarial-review on a frontier Western model and **self-host** for anything touching alpha or private data.
- **Adopt, don't hand-roll, the risky engine parts.** Nautilus Trader (Rust core, true backtest/live parity) is a stronger foundation than a bespoke Stage 3 engine; keep your hand-rolled point-in-time (PIT) data layer and statistical-validation layer as differentiators. The dominant risk for this project is backtest overfitting, not latency.
- **Latency is nearly irrelevant for daily ETF trading**; your real "latency" budget is data-availability and MOC/MOO cutoffs measured in minutes. Treat the FPGA/HFT material as a career/portfolio artifact — your Aegis-Stream work maps directly onto what Jane Street/Jump/Optiver hire FPGA engineers for.

---

## 1. Alternative and Cheaper Models

### 1.1 The strategic distinction that governs everything
There is a categorical difference between **calling a Chinese-hosted API** and **running Chinese open weights locally**. Open weights (DeepSeek, Qwen, GLM, Kimi are all downloadable under permissive licenses) run fully offline; no prompt or code ever leaves your machine. A hosted endpoint at `api.deepseek.com` or Alibaba's DashScope sends your prompts to servers in China subject to PIPL and local law. **Rule for this project: hosted cheap APIs are fine for generic/public coding; anything containing strategy logic, signals, or private data runs on self-hosted weights or a trusted Western host.**

### 1.2 Chinese frontier/open model families (pricing as of July–Aug 2026)

| Family | Model | $/1M in | $/1M out | Cache-hit in | Context | License |
|---|---|---|---|---|---|---|
| DeepSeek | V4 Flash (`deepseek-v4-flash`) | $0.14 | $0.28 | $0.0028 | 1M | MIT (weights) |
| DeepSeek | V4 Pro (`deepseek-v4-pro`) | $0.435 | $0.87 | $0.003625 | 1M | MIT (weights) |
| Alibaba Qwen | Qwen3-Coder Next | $0.11–0.12 | $0.80 | — | 262K | Apache-2.0 |
| Qwen | Qwen3.5 Flash | $0.10 | $0.40 | — | 1M | Apache-2.0 |
| Qwen | Qwen3 Max | $0.78 | $3.90 | — | 262K | proprietary |
| Moonshot Kimi | K2.6 / K2.7 Code | $0.95 | $4.00 | $0.19 | 262K | open weights |
| Kimi | K2.5 | $0.60 | $3.00 | $0.15 | 262K | open weights |
| Kimi | K3 | $3.00 | $15.00 | $0.30 | 1M | weights published |
| Zhipu/Z.ai GLM | GLM-4.6 | $0.60 | $2.20 | $0.11 | ~200K | MIT |
| GLM | GLM-4.5-Air | $0.20 | $1.10 | $0.03 | — | MIT |
| GLM | GLM-4.5/4.7-Flash | free | free | — | ~128–203K | MIT |

DeepSeek has **announced but not yet dated a 2× peak-hour surcharge** (Beijing-time windows). Thinner-sourced families noted in results: **MiniMax** (M-series, competitive open weights ~80% SWE-bench Verified), **ByteDance Doubao/Seed**, **Baidu ERNIE**, **Tencent Hunyuan**, **iFlytek Spark**, **01.AI Yi**, **StepFun**, **Baichuan** — mostly China-market-focused or less battle-tested for agentic coding than the four leaders.

**Coding-plan subscriptions** (flat-rate, quota-based, Anthropic-compatible — best value for heavy Claude Code use): Z.ai GLM Coding Plan Lite ~$30/quarter (~$10/mo), Pro ~$90/quarter (~$30/mo), Max ~$240/quarter (~$80/mo). The $3/mo promo was removed Feb 11, 2026. Moonshot's Batch API charges ~60% of standard; DeepSeek cache hits are ~98% below cache-miss input.

### 1.3 Western open-weight alternatives
**Meta Llama**, **Mistral** (incl. **Codestral** for code, **Devstral** for agentic coding — Devstral 2 Small is a notable small agentic-coding model), **Mixtral** (MoE), **Google Gemma**, **Microsoft Phi**, **AI2 OLMo** (fully open incl. training data), **IBM Granite**, **NVIDIA Nemotron**, and **OpenAI gpt-oss** (20B/120B open-weight). For a solo operator these matter mostly as **self-hostable, license-clean** options; gpt-oss-20b and small Qwen/Gemma variants are the realistic single-GPU choices.

### 1.4 Local / self-hosted inference — what actually runs
The **MoE-with-small-active-parameters** class is the sweet spot. **Qwen3-30B/35B-A3B** (30–35B total, ~3B active per token) is the standout:
- **~30 tok/s at Q4 on an 8GB RTX 3070 Ti** (community benchmark, r/LocalLLaMA); **~50–65 tok/s on a used RTX 3090** at Q4_K_M with full 32K context.
- Apple Silicon: **Mac Studio M4 Max 48GB runs Q5_K_M at 25–35 tok/s via MLX**; Mac Mini M4 Pro 24GB does Q4_0 at ~15–22 tok/s.
- Unsloth's MTP (multi-token-prediction) speculative decoding pushes Qwen3.6-35B-A3B to ~240 tok/s on an RTX 6000.

Runtimes: **llama.cpp/GGUF** (Q4_K_M is the standard quality/size sweet spot; Q5/Q6 if VRAM allows), **Ollama** (easiest), **vLLM/SGLang** (throughput/production serving), **LM Studio** (GUI), **TensorRT-LLM** (NVIDIA max perf). Quant formats: GGUF (llama.cpp), AWQ/GPTQ (GPU), FP8/NVFP4 (newer NVIDIA). **Tool-calling reliability** is the practical gotcha for agents — llama.cpp needs `--jinja` and correct chat templates; GLM-4.7-Flash is recommended for local Claude Code because it reliably emits tool calls with 128K context.

### 1.5 Driving the coding agents with alternative models
- **Claude Code** speaks the Anthropic Messages API. Four env vars (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL`) redirect it to any Anthropic-compatible gateway. **claude-code-router** (`@musistudio/claude-code-router`, run via `ccr code`) proxies to DeepSeek/Qwen/GLM/Kimi/Ollama and **routes per request type** (default / background / think / longContext). **LiteLLM** and **OpenRouter** provide the same translation layer; OpenRouter publishes an official Claude Code cookbook. Alibaba's DashScope exposes a native Anthropic endpoint for Qwen (`.../apps/anthropic`).
- **The tool-calling caveat is real and must be tested:** Anthropic models are trained on Claude Code's exact tool-call format; GLM/Qwen/DeepSeek/Kimi are trained on their own conventions and the proxy's translation is imperfect. Failure modes: model narrates what it *would* do instead of emitting a tool call; malformed edits. OpenRouter's "Exacto" routing mode optimizes for tool-calling accuracy.
- **Codex CLI** and OpenAI-compatible alternatives — **OpenCode**, **Aider** (Aider Polyglot is its own benchmark), **Cline**, **Continue**, **Roo Code**, **Goose** — all accept OpenAI-compatible base URLs, so any Chinese API (all expose OpenAI-compatible endpoints) can drive them.

### 1.6 Coding/reasoning benchmarks (2026 snapshots — treat as directional)

| Model | SWE-bench Verified | SWE-bench Pro | License |
|---|---|---|---|
| DeepSeek V4-Pro-Max | ~80.6% (top open) | — | MIT |
| MiniMax M3 | ~80.5% | ~59.0% | open |
| Qwen3.7 Max | ~80.4% | ~60.6% | mixed |
| Kimi K2.6 | ~80.2% | ~58.6% (ties GPT-5.5) | open |
| GLM-5.2 | — | ~62.1% (best open, 3rd-party) | MIT |
| Claude Opus (frontier) | high-70s–80s | ~69.2% (leads active) | closed |

Caveats: SWE-bench Verified vendor numbers are inconsistently scaffolded; Scale's SWE-bench Pro *standardized* set (identical scaffolding, 731 public tasks) is the most apples-to-apples but has thin coverage. Other benchmarks to track: **LiveCodeBench**, **Terminal-Bench 2.0**, **BigCodeBench**, **HumanEval+/MBPP+**, **Aider Polyglot** (coding); **AIME**, **GPQA** (reasoning/math); **RULER** (long-context). A 2026 arXiv study of five open-weights coding models on a real application-generation task found benchmark rank to be a **weak predictor of real artifact quality** — you must A/B test candidates on your own repo.

### 1.7 Risks of routing through Chinese-hosted APIs (balanced, factual)
- **Data residency / PIPL:** China's Personal Information Protection Law (2021) plus Commercial Encryption Regulations and CAC security-assessment/data-localization rules (Ch. 3, Arts. 38–42) create a regime where you have little control or recourse over submitted content once it lands on Chinese servers.
- **Training-on-inputs / retention:** consumer-tier terms for several Chinese providers permit using inputs to improve services; retention windows are opaque and enterprise/international tiers sometimes differ. **Do not assume deletion.**
- **US regulatory / procurement / export-control:** government-adjacent procurement increasingly restricts Chinese AI services; this could be disqualifying if you later work for a US firm with security requirements. (Export controls run the other way and don't affect you downloading weights.)
- **Censorship / alignment quirks:** content-policy RLHF is largely irrelevant to trading code but a correctness/consistency wildcard.
- **Why self-hosting is materially different:** downloaded open weights run offline, deterministically, with zero data egress and no ToS on inference — available precisely because these labs ship permissive (MIT/Apache-2.0) weights. This is the single most important mitigation.

### 1.8 Recommended model-routing table for THIS project

| Task | Recommended | Rationale |
|---|---|---|
| Architecture / design (Stage 0) | Frontier Western (Opus-class) or GLM-5.x | Best reasoning; low token volume so cost immaterial |
| Bulk implementation (Codex primary) | DeepSeek V4 Flash / Qwen3-Coder / GLM Coding Plan | Cheapest per token; high volume |
| Adversarial review / red-team (Claude Code) | Different vendor from implementer | Enforces writer≠sole-reviewer AND model diversity |
| Test generation | Qwen3-Coder / Kimi K2.7 Code | Strong code, cheap, enumerates cases well |
| Runtime research agents (bounded, Stage 8) | **Self-hosted Qwen3-30B-A3B** behind deterministic wrappers | No data egress; schema-validated, timeout-bounded |
| Embeddings | Self-hosted (bge/e5/Qwen-embed) | Cheap, private, deterministic |
| Cheap batch summarization | DeepSeek V4 Flash batch / GLM-4.5-Flash (free) | Off-peak/batch discounts |

**Estimated monthly *development* cost** (agentic coding, not runtime): *Light* ~$10–30/mo (one coding plan); *Moderate* ~$30–80/mo token spend + a coding plan; *Heavy* ~$150–300/mo (output-token-dominated) — mitigate with prompt caching (up to ~98% off on DeepSeek cache hits), batch APIs (40–60% off), context hygiene, and flash-tier routing for mechanical work.

---

## 2. Mathematical Models
*All equations stated for typesetting; symbols defined inline; assumptions/failure modes flagged.*

### 2.1 Momentum signals
**Time-series momentum (Moskowitz-Ooi-Pedersen, TSMOM):** signal $s_{i,t}=\operatorname{sign}(r_{i,t-k\to t})$, where $r_{i,t-k\to t}=\prod_{j=t-k+1}^{t}(1+r_{i,j})-1$. Position is vol-scaled (§2.3). **Skip-month:** use returns to $t-21$ to avoid short-term reversal. **Risk-adjusted momentum:** rank by $r/\sigma$. **Cross-sectional:** long top / short bottom quantile. *Failure modes:* momentum crashes (post-drawdown rebounds), turnover, regime dependence.

### 2.2 Volatility estimation
Realized $\sigma^2_t=\frac1n\sum r^2$; **EWMA/RiskMetrics** $\sigma^2_t=\lambda\sigma^2_{t-1}+(1-\lambda)r_{t-1}^2$, $\lambda\approx0.94$ (daily); **GARCH(1,1)** $\sigma^2_t=\omega+\alpha r_{t-1}^2+\beta\sigma^2_{t-1}$, $\alpha+\beta<1$, long-run variance $\omega/(1-\alpha-\beta)$; **GJR-GARCH/EGARCH** add asymmetric leverage ($+\gamma r_{t-1}^2\mathbb1[r_{t-1}<0]$); **HAR-RV** (Corsi) with daily/weekly/monthly RV terms; range estimators **Parkinson** $\frac1{4\ln2}\ln(H/L)^2$, **Garman-Klass**, **Rogers-Satchell** (drift-independent), **Yang-Zhang** (overnight gaps + drift). Annualize $\sigma\sqrt{252}$ (assumes i.i.d.; autocorrelation biases it). Track vol-of-vol for regime signals.

### 2.3 Volatility targeting
$w_{i,t}=\frac{\sigma^\*}{\sigma_{i,t}}s_{i,t}$; portfolio scalar $c_t=\sigma^\*/\hat\sigma_{p,t}$, subject to leverage cap $\sum|w|\le L$. Empirically raises Sharpe and cuts drawdown by de-risking in high-vol regimes; adds turnover; the vol estimate lags jumps and can lever *into* calm-before-storm periods.

### 2.4 Portfolio construction
- **Markowitz:** $\max_w w^\top\mu-\frac\gamma2 w^\top\Sigma w$, closed form $w^\*=\frac1\gamma\Sigma^{-1}\mu$; $\Sigma^{-1}$ amplifies estimation noise (the estimation-error problem — MV "error-maximizes").
- **Shrinkage covariance:** **Ledoit-Wolf** $\hat\Sigma=(1-\delta)S+\delta F$ (S sample, F structured target, $\delta$ optimal intensity); **OAS** for Gaussian; factor covariance models.
- **ERC / risk parity:** equal risk contribution $w_i(\Sigma w)_i=w_j(\Sigma w)_j\ \forall i,j$; solve $\min_w\sum_i(w_i(\Sigma w)_i-\frac1N w^\top\Sigma w)^2$.
- **HRP (Lopez de Prado):** tree-cluster the correlation matrix, quasi-diagonalize, recursive-bisection inverse-variance — avoids $\Sigma^{-1}$; robust to ill-conditioning.
- **Min-variance** $\min w^\top\Sigma w$ s.t. $\mathbf1^\top w=1$; **max-diversification** $\max (w^\top\sigma)/\sqrt{w^\top\Sigma w}$.
- **Black-Litterman:** $E[R]=[(\tau\Sigma)^{-1}+P^\top\Omega^{-1}P]^{-1}[(\tau\Sigma)^{-1}\Pi+P^\top\Omega^{-1}Q]$, $\Pi=\delta\Sigma w_{mkt}$ (implied equilibrium), P/Q = views, $\Omega$ = view uncertainty.
- **Transaction-cost-aware:** $\max_w w^\top\mu-\frac\gamma2 w^\top\Sigma w-(w-w_0)^\top\Lambda(w-w_0)$; quadratic costs give a closed form and a **no-trade region** (don't rebalance until drift exceeds a band).

### 2.5 Regime detection
**HMM:** latent state $z_t$, emissions $r_t|z_t\sim\mathcal N(\mu_z,\sigma^2_z)$; **Baum-Welch** (EM) fits, **Viterbi** decodes. **Critical look-ahead trap:** *smoothed* probabilities $P(z_t|r_{1:T})$ use future data; only *filtered* $P(z_t|r_{1:t})$ are tradeable. **Markov-switching** (Hamilton); change-point via **CUSUM** and **Bayesian online change-point** (Adams-MacKay); clustering-based regimes; and **simple robust baselines** (200-day trend, vol quantiles) that often beat the fancy models out-of-sample.

### 2.6 Kelly criterion & sizing
$f^\*=\mu/\sigma^2$ (continuous) or $f^\*=p-\frac{1-p}{b}$ (discrete). **Fractional Kelly** (¼–½) is standard because full Kelly is over-levered under parameter uncertainty and produces brutal drawdowns. Kelly ≈ vol targeting when $\mu,\sigma$ are the strategy's; estimation error in $\mu$ dominates, so haircut hard.

### 2.7 Risk metrics
Sharpe $\frac{\mu-r_f}\sigma$; Sortino (downside dev); Calmar $\frac{\text{CAGR}}{|\text{MaxDD}|}$; Information Ratio (active/tracking error); Omega. VaR (historical / parametric $\mu+z_\alpha\sigma$ / **Cornish-Fisher** skew-kurtosis-adjusted / Monte Carlo); **CVaR/Expected Shortfall** $=E[L|L>\text{VaR}_\alpha]$ is **coherent** (Artzner axioms: monotonicity, subadditivity, positive homogeneity, translation invariance) whereas VaR is not subadditive. Max-drawdown distribution theory, drawdown-at-risk, time-under-water.

### 2.8 Statistical validation math (Stage 5 core)
- **Probabilistic Sharpe Ratio (PSR):**
$$\widehat{\text{PSR}}(\text{SR}^\*)=\Phi\!\left(\frac{(\widehat{\text{SR}}-\text{SR}^\*)\sqrt{n-1}}{\sqrt{1-\hat\gamma_3\widehat{\text{SR}}+\frac{\hat\gamma_4-1}4\widehat{\text{SR}}^2}}\right)$$
$\hat\gamma_3$ = skewness, $\hat\gamma_4$ = kurtosis, $n$ = sample length; the denominator is the skew/kurtosis-adjusted standard error of the SR estimate.
- **Deflated Sharpe Ratio (Bailey & López de Prado, *Journal of Portfolio Management* 40(5):94–107, 2014):** DSR = PSR evaluated at the expected maximum Sharpe under the null, $\text{SR}^\*$, from the **False Strategy Theorem:**
$$E[\max_N\widehat{\text{SR}}]\approx\sqrt{V[\widehat{\text{SR}}]}\left[(1-\gamma)\,\Phi^{-1}\!\Big(1-\tfrac1N\Big)+\gamma\,\Phi^{-1}\!\Big(1-\tfrac1N e^{-1}\Big)\right]$$
$\gamma\approx0.5772$ (Euler-Mascheroni constant), $N$ = number of independent trials, $V[\widehat{\text{SR}}]$ = cross-sectional variance of the trial Sharpe ratios. The paper's headline, stated verbatim: assuming E[SR]=0 and V[SR]=1, "**after only 1,000 independent backtests the expected maximum Sharpe Ratio is 3.26, even if the true SR of the strategy is zero.**"
- **Minimum Track Record Length (MinTRL):** solve PSR = target confidence for $n$.
- **Probability of Backtest Overfitting (PBO) via CSCV** (Bailey-Borwein-López de Prado-Zhu): partition the trial×time performance matrix into combinatorially symmetric train/test splits; PBO = fraction of splits where the in-sample-best config ranks **below the OOS median**. Model-free, non-parametric.
- **Deflation / multiple testing:** **White's Reality Check** and **Hansen's SPA test** (bootstrap the max statistic across strategies); **Harvey-Liu haircut Sharpe** and the **t > 3.0** argument (with hundreds of factors tested, raise the usual t > 2 hurdle).
- **Bootstrap:** stationary bootstrap (Politis-Romano), circular block bootstrap; optimal block length ~ $O(n^{1/3})$ (Politis-White automatic selection).
- **Purged k-fold CV with embargo** (López de Prado): remove training samples whose label windows overlap the test set (purge) plus a buffer (embargo), because financial labels overlap in time and standard CV leaks; plus walk-forward analysis.

### 2.9 Transaction cost & market impact
Effective spread $2|p_{exec}-m|$ (m = midquote); **Kyle's lambda** $\Delta p=\lambda\cdot$(signed order flow); **square-root law** impact $\approx Y\sigma\sqrt{Q/V}$ (Q order size, V ADV, Y ≈ O(1)). **Almgren-Chriss optimal execution** (2000): permanent impact linear in trade rate, temporary impact $h(v)=\epsilon\,\text{sgn}(v)+\eta v$; minimize $E[\text{cost}]+\lambda V[\text{cost}]$. Closed-form trajectory of remaining holdings:
$$x_j=X\,\frac{\sinh(\kappa(T-t_j))}{\sinh(\kappa T)},\qquad \kappa\approx\sqrt{\lambda\sigma^2/\eta}$$
— hyperbolic-sine decay; higher risk aversion $\lambda$ ⇒ faster liquidation — tracing the **efficient frontier of execution** (cost vs. variance). **Implementation shortfall** = paper − actual return (Perold). POV/participation-rate, TWAP, VWAP scheduling. Calibrate a cost model from ETF quoted bid-ask and ADV so a typical order at your size costs a few bp — this is Stage 3's cost model.

### 2.10 Microstructure (only if you go intraday later)
Order-flow imbalance, queue position, **VPIN**, **Amihud illiquidity** $\text{avg}(|r|/\text{volume})$, **Roll's spread** $2\sqrt{-\text{Cov}(\Delta p_t,\Delta p_{t-1})}$, **Hasbrouck information share**.

### 2.11 Backtest math correctness
Log vs simple returns ($r_{\log}=\ln(1+r)$); **variance drain / vol drag** $g\approx\mu-\frac12\sigma^2$ (geometric ≈ arithmetic − half variance — why vol targeting aids compounding); correct annualization; **Brinson attribution** (allocation vs selection); precise cash/dividend/split accounting.

### 2.12 Where ML fits mathematically
**Fractional differentiation** (López de Prado — stationary while preserving memory); **triple-barrier labeling** (profit-take / stop / time barriers); **meta-labeling** (a second model sizes/filters a primary signal); **sample uniqueness & weights** from label overlap; **sequential bootstrap**; and the core reason **standard CV fails**: temporal label overlap ⇒ train/test leakage (hence purging/embargo, §2.8).

---

## 3. Platforms

### 3.1 Brokers & paper-trading APIs

| Broker | Paper | Assets | Rate limits | Gotchas |
|---|---|---|---|---|
| **Alpaca** | native paper env | US equities, options (paper), crypto | free 200 req/min; Algo Trader Plus up to 10,000 req/min | free data is **IEX-only (~2–5% of consolidated volume)** — fine for daily research, not execution-sensitive; SIP needs Algo Trader Plus (~$99/mo); PFOF |
| **Interactive Brokers** | paper account | global multi-asset | ~50 msg/s pacing | TWS API / Client Portal Web API; use **ib_async** (successor to ib_insync); institutional-grade |
| Tradier | yes | equities/options | REST | good options; smaller ecosystem |
| TradeStation | yes | multi-asset | REST | approval friction |
| Schwab (thinkorswim) | yes | equities/options | OAuth | post-TDA migration; slow app approval |
| Coinbase/Kraken/Binance | crypto | crypto | varies | 24/7, no PDT |
| Tradovate/Rithmic/CQG | some sims | futures | varies | pro-grade; pair with Databento data |

**Recommendation:** **Alpaca paper** for Stage 6 (as the plan assumes) — best DX, true paper env, Python/Go SDKs. Add an **IBKR paper** adapter behind your provider-neutral interface for fidelity and breadth.

### 3.2 Market-data vendors (emphasis on point-in-time & survivorship-bias-free)

| Vendor | Strength | ~Cost 2026 | PIT / SBF |
|---|---|---|---|
| Polygon.io ("Massive") | flat-rate SIP real-time+historical | Stocks Advanced ~$199/mo | 7+ yr; SIP-sourced |
| Databento | institutional tick/L2, direct feeds, ns ts | metered ~$100–500/mo | best microstructure; US = 15 exchanges + 30 ATS |
| Alpaca data | free IEX / paid SIP | free / $99 | partial free volume |
| Tiingo | EOD + fundamentals + news | ~$10–50/mo | good value |
| EODHD / FMP / Twelve Data / Alpha Vantage | broad, cheap | $10–50/mo | mixed quality |
| Norgate Data | **survivorship-bias-free** US eq/futures | tiered | **SBF** — key for backtests |
| CRSP | academic gold standard | institutional | SBF, delisting returns |
| FRED / **ALFRED** | macro; **ALFRED = vintage/PIT** | free | critical PIT macro |
| SEC EDGAR (full-text + XBRL) | filings/fundamentals | free | filing timestamps = natural PIT |
| ORATS / OptionMetrics / CBOE DataShop | options/IV surfaces | institutional | OptionMetrics = academic std |

**Point-in-time is make-or-break for your Stage 2.** Use **ALFRED** for macro vintages, **EDGAR filing timestamps** for fundamentals availability, and **Norgate/CRSP** for survivorship-bias-free price universes. **yfinance** is prototyping-only — non-commercial ToS, unofficial, rate-limited, not point-in-time.

### 3.3 Backtest/research frameworks — build vs adopt

| Framework | Type | Live parity | Verdict |
|---|---|---|---|
| **Nautilus Trader** | event-driven, **Rust core** + Python | **true backtest = live, no rewrite** | **strongest adopt candidate**; 16 venues incl. IBKR/Databento; steep learning curve; order-lifecycle state machines built in; optional Redis-backed state persistence |
| QuantConnect LEAN | C# engine, Python API, cloud | live via QC | most complete end-to-end; ecosystem lock-in |
| VectorBT / vectorbtpro | vectorized | none | fast **signal triage** ("does this have alpha?"), not execution |
| Zipline-reloaded | event-driven | limited | Pipeline API for factor research |
| Backtrader | event-driven | brokers | mature but **effectively EOL** — migrate off |
| Backtesting.py / bt / PyBroker | light | varies | bt good for allocation/rebalance |
| Qlib / FinRL / Lumibot / Hummingbot | ML/RL/crypto | varies | niche |

**Recommendation (this directly answers your Stage 3 question):** **Adopt Nautilus Trader as the execution/backtest engine.** Its Rust core, event-driven order state machines, and **genuine backtest/live parity** solve exactly the "backtest-to-live divergence" risk your plan worries about, and its correctness-and-safety-first design philosophy matches your verification instincts. Keep VectorBT upstream for fast signal triage. **Keep hand-rolling your point-in-time data layer (Stage 2) and statistical-validation layer (Stage 5)** — those are your differentiators and no framework does them well. This is a "borrow the engine, own the science" split.

### 3.4 Data/compute infrastructure
Time-series store: **DuckDB + Parquet** (the plan's choice) is right for daily-ETF scale; ArcticDB if you outgrow it; ClickHouse/QuestDB/TimescaleDB/kdb+ for bigger/faster needs. Table format: Parquet + manifests (fine), Delta/Iceberg optional. DataFrames: **Polars** (Arrow-native, lazy, fast) over pandas. Parallel backtests: **Ray** for parameter sweeps (Dask alternative). Orchestration: **Prefect** fine; **Dagster** if you want asset-based lineage; **Temporal** if you want durable execution for the order pipeline. Experiment tracking: **MLflow** can *back* your Stage 5 trial registry rather than hand-rolling storage (W&B/Neptune/Aim/DVC alternatives).

### 3.5 Deployment & secrets
Small always-on: **Hetzner** (best price/perf ~€5–20/mo), DigitalOcean, AWS Lightsail, GCP e2-small; a daily-EOD system can even run on GitHub Actions cron or a $5 VPS. **Colocation is irrelevant** at this frequency. Docker for reproducibility (the plan). Secrets: **SOPS + age** or 1Password CLI for a solo dev; Vault/AWS Secrets Manager are overkill until multi-node.

### 3.6 Regulatory/compliance for a US individual (⚠️ not legal advice; verify with a professional and your employer)
- **Pattern Day Trader — MAJOR 2026 CHANGE:** the historical FINRA Rule 4210 PDT framework (a "pattern day trader" = **4+ day trades in 5 business days** in a **margin** account exceeding 6% of trades, requiring **$25,000** minimum equity) was, per SEC approval order 34-105226 (approved April 14, 2026) and FINRA Regulatory Notice 26-10, **eliminated effective June 4, 2026**, replaced by a real-time **intraday-margin** standard (broker phase-in permitted to Oct 20, 2027). *This is a fast-moving change — confirm current status directly with FINRA/your broker.* The general 25% maintenance margin and $2,000 margin-account minimum under Rule 4210 remain.
- **Regulation T** (Federal Reserve, 12 CFR 220): **50% initial margin** on margin equity securities (unchanged since 1974).
- **Wash sale rule** (IRC §1091 / IRS Pub 550): loss disallowed if a substantially identical security is bought within **30 days before or after** (a **61-day window**); the disallowed loss adds to the replacement-share basis (§1091(d)) and is permanently lost if the replacement is in an IRA (Rev. Rul. 2008-5). Reported on **Form 8949** (code "W").
- **Section 1256 contracts** (regulated futures, broad-based index options like SPX/VIX): **60% long-term / 40% short-term** regardless of holding period + year-end mark-to-market; reported on **Form 6781**.
- **Registration:** trading **only your own capital** does **not** require investment-adviser registration (the Advisers Act "ABC test" requires Advice + Business + Compensation for advising *others*). **Managing others' money** triggers RIA registration (state regulator below ~$100M AUM, SEC above) and typically **Series 65**; for futures/commodity pools, **CTA/CPO** registration with **NFA/CFTC** and typically **Series 3**.
- **SEC Market Access Rule 15c3-5** (2010) governs broker-dealers, not you — but it's the **conceptual template** for the pre-trade controls your system should mimic: pre-set credit/capital limits, erroneous-order ("fat-finger") price/size rejects, authorized-access restriction, and immediate post-trade surveillance. (Knight Capital paid a $12M settlement for violating this rule.)
- **Form 8949 / 1099-B reconciliation:** reconcile broker-reported basis (covered vs noncovered securities, Boxes A–F) against your tax-lot accounting (FIFO/specific-ID) — a reason to build the tax-lot module (§6.4).
- **Market manipulation:** spoofing/layering is prohibited under **CEA §4c(a)(5)** (added by Dodd-Frank §747; 7 U.S.C. §6c(a)(5)); scienter required. Not a risk for long-only ETF strategies.
- **Broker ToS & market-data redistribution:** most retail data licenses forbid redistribution; automated trading is generally allowed but rate-limited.
- **⚠️ Employment considerations:** personal-trading policies, **preclearance**, **blackout windows**, and conflicts may apply if you work in industry — **check your employer's compliance function before trading**; do not rely on this report.

---

## 4. Risk (deeper than the baseline plan)

### 4.1 Model risk management adapted from SR 11-7
The Fed/OCC **SR 11-7** guidance adapts cleanly. Pillars: **model definition** (any quantitative method turning inputs into estimates — your signals, cost model, and any ML all qualify), **three lines of defense**, **effective challenge** (critical review by a competent, independent party), a **model inventory**, **validation** (conceptual soundness + outcomes analysis + ongoing monitoring), and **documentation**. **Solo-operator mapping:** first line = Codex (implementer) + you as author; **second line = Claude Code as independent adversarial validator** — literally "effective challenge," and your existing "writer ≠ sole reviewer" rule is SR 11-7's independence principle; third line = CI + a periodic Stage 9 self-audit + the promotion state-machine gate. Maintain a model inventory (each strategy, its assumptions, limitations, validation date) and a revalidation cadence.

### 4.2 Risk taxonomy (adds AI-agent risk explicitly)
Market, liquidity, execution, model, **data** (vendor error, revisions, PIT violations), operational, technology, counterparty/broker, **key-person** (you lose interest/capacity), regulatory, cyber, and **AI-agent risk**: prompt injection into research agents, hallucinated logic silently merged, **silent scope creep** (agent "helpfully" changes a risk limit), agentic tool misuse. Mitigation for the last: the deterministic runtime (no LLM in execution path), schema-validated agent outputs, and the review gate.

### 4.3 Pre-trade risk controls (mirror 15c3-5)
Fat-finger notional limits, max order notional/size, max position, max daily loss, max drawdown, gross/net exposure limits, per-name concentration (your 20%/ETF cap), restricted lists, **price collars** (reject orders far from last), order-rate limiting — **all enforced deterministically, pre-submission, outside the strategy code.**

### 4.4 Kill switches & circuit breakers
- **State persisted outside process memory** (DB/Redis) so a restart can't "forget" it's halted — the single most important reliability pattern.
- **Dead-man's switch / heartbeat:** if the strategy stops heartbeating, flatten/halt.
- **Market-wide halts:** respond correctly to **LULD** (limit-up/limit-down) bands and **Rule 80B** market-wide circuit breakers. Per SEC/Investor.gov: a Level 1 (−7%) or Level 2 (−13%) breach before 3:25 p.m. ET halts market-wide trading for **15 minutes**; the same breach *at or after* 3:25 p.m. does **not** halt; a Level 3 (−20%) breach at **any** time halts trading for the **remainder of the day**. Thresholds are set daily off the prior day's S&P 500 close. Handle reopen gap risk.

### 4.5 Reconciliation & idempotency engineering
Exactly-once order semantics via **idempotency keys** (client order IDs), **duplicate-order rejection**, the **outbox pattern** (persist intent before sending), **two-phase state machines** (PENDING→SENT→ACKED→FILLED, with persisted transitions), periodic position reconciliation (diff internal vs broker positions), and **recovery from unknown broker state** (on restart: query the broker, reconcile, only then resume). Chaos-test by killing the process mid-order.

### 4.6 Case studies → engineering lessons

| Event | What happened | Lesson |
|---|---|---|
| **Knight Capital (2012)** | Manual deploy left **dead "Power Peg" code** on 1 of 8 SMARS servers; a reused feature flag reactivated it. Per SEC Admin. Proc. 34-70694 (Oct 16 2013): while processing just **212 parent orders**, SMARS "sent millions of child orders, resulting in **4 million executions in 154 stocks for more than 397 million shares in approximately 45 minutes**," leaving a ~$3.5B net-long / ~$3.15B net-short position; Knight "lost over $460 million" (press reported ~$440M) and paid a **$12M** Market-Access-Rule settlement; no kill switch; warning emails ignored | automated, verified, all-or-nothing deploys; fully remove dead code; never reuse flags; a kill switch; alerts that page, not email. Your no-direct-merge + CI is the direct antidote |
| **LTCM (1998)** | extreme leverage + correlated convergence trades + stable-correlation models | leverage kills; correlations →1 in crises; your no-leverage/long-only constraints institutionalize this |
| **Flash Crash (2010)** | liquidity evaporation + feedback loops | model liquidity as fragile; don't assume fills at last price |
| **XIV / Volmageddon (2018)** | a vol spike wiped out inverse-VIX ETNs | understand product mechanics & tail convexity before trading vol |
| **Archegos (2021)** | concentration + hidden swap leverage | concentration limits (your 20% cap) matter |
| **Amaranth (2006)** | concentrated nat-gas spread bets | position/concentration limits |
| **Quant Quake (Aug 2007)** | crowded factor unwinds hit everyone at once | crowding/capacity risk; monitor correlation to known factors |
| **Negative oil (2020)** | systems couldn't represent negative prices | test edge cases (negative/zero prices, splits) |

### 4.7 Backtest overfitting = the dominant risk
The **seven sins of quantitative investing**, survivorship/look-ahead/restatement bias, data snooping, selection bias under the null. Empirical anchors:
- **McLean & Pontiff (2016, *Journal of Finance* 71(1):5–31):** studied 97 published predictors — "**Portfolio returns are 26% lower out-of-sample and 58% lower post-publication. The out-of-sample decline is an upper bound estimate of data mining effects. We estimate a 32% (58%–26%) lower return from publication-informed trading.**"
- **Hou, Xue & Zhang (2020, *Review of Financial Studies* 33(5):2019):** replicated 452 anomalies — "**65% of the 452 anomalies... cannot clear the single test hurdle of the absolute t-value of 1.96. Imposing the higher multiple test hurdle of 2.78 at the 5% significance level raises the failure rate to 82%.**"
- **Harvey-Liu-Zhu:** with hundreds of factors tested, raise the significance bar to **t > 3.0**.
This is why Stage 5 (DSR/PBO/deflation) is the highest-ROI engineering in the whole plan.

### 4.8 Capacity, crowding, realistic expectations
Retail has an **edge in capacity-constrained niches** (small size = negligible impact) and a **disadvantage in crowded factor trades** (no scale, cost, or financing edge). **Realistic solo expectation after costs:** most retail systematic strategies that survive honest validation land at **low single-digit net Sharpe (~0.3–0.8)**; a persistent net Sharpe > 1 after DSR/PBO deflation is exceptional and should be treated with suspicion until proven live.

### 4.9 Behavioral / process controls
Predefined shutdown criteria (max drawdown, N consecutive losing months, live-vs-backtest tracking-error breach); a written "when do I stop" rule *before* deploying; no discretionary override of the deterministic limits.

### 4.10 Production risk monitoring
Rolling Sharpe; realized drawdown vs the expected-drawdown distribution (Monte Carlo); **live-vs-backtest tracking error**; **signal-decay** monitoring; **feature drift / PSI** (population stability index); execution slippage vs modeled slippage; and **CUSUM/EWMA statistical-process-control charts** to detect strategy degradation before it becomes a drawdown.

---

## 5. Latency (as a spectrum — and why it barely matters here)

### 5.1 Taxonomy

| Tier | Frequency | Acceptable latency | Tech | You? |
|---|---|---|---|---|
| Daily / EOD | 1/day | **seconds–minutes** | Python, REST, cron | **YES — this is you** |
| Intraday / swing | min–hr | sub-second–seconds | WebSocket, async | maybe later |
| High-frequency | ms–μs | microseconds | C++/Rust, kernel bypass, colo | no |
| Ultra-low-latency / HFT | μs–ns | **nanoseconds** | **FPGA/ASIC**, colo, microwave | career only |

### 5.2 Where latency comes from
Feed handler + decoding, network propagation (**~5 μs/km in fiber**; microwave/mmWave faster line-of-sight), NIC + kernel network stack, OS scheduling jitter, GC/interpreter overhead, serialization, DB writes, broker-side latency.

### 5.3 Concrete numbers
- Retail **REST round-trip: tens–hundreds of ms**; WebSocket streaming lower but still ms.
- Kernel-bypass software (Solarflare X2522 + OpenOnload): **~just under 2 μs tick-to-trade**.
- **FPGA tick-to-trade: 100–500 ns end-to-end**; the best firms hit single-to-double-digit ns; AMD Alveo **UL3524 delivers <3 ns transceiver latency** (UL3422 ~2.34 ns); Exegy + AMD recorded a **13.9 ns** STAC-T0 actionable latency.
- Kernel bypass: Solarflare/Onload, DPDK, io_uring, AF_XDP; plus busy-polling, CPU pinning/isolcpus, NUMA awareness, hugepages.

### 5.4 Measurement methodology
Hardware timestamping (**PTP/IEEE 1588**, PPS), Corvil/Beeks-style monitoring, **percentile discipline (p50/p99/p99.9/max)** — tail latency kills, not the mean — **coordinated omission** awareness, **HdrHistogram**, and eBPF probes for zero-blocking telemetry.

### 5.5 Protocols & feeds
FIX (text) vs binary; **ITCH/OUCH** (Nasdaq), **PITCH** (Cboe), **CME MDP 3.0 / iLink 3**, **SBE** (Simple Binary Encoding). A retail trader gets REST/WebSocket; ITCH/OUCH and colo require exchange membership/sponsored access.

### 5.6 Appendix — hardware-accelerated trading (for your Aegis-Stream / RTL background)
Your **SystemVerilog trading engine with fixed-function FPU** and **FPGA market-data replay / limit-order-book prototype (Aegis-Stream)** map almost exactly onto real HFT FPGA stacks: a 5-stage tick-to-trade pipeline (network ingress → market-data parse → order-book maintenance → signal eval → order transmit), each stage pipelined/parallelized; the lowest-latency critical paths are still **hand-written RTL** (HLS narrows but doesn't close the gap). Hardware: AMD/Xilinx **Alveo UL3524/UL3422**, Solarflare X2/X3 NICs, Exablaze/Cisco Nexus SmartNICs, **Arista 7130 / Metamako layer-1** switches; IP cores from **Enyx, Exegy, NovaSparks, Xelera**. **FPGA vs ASIC:** FPGAs reload in seconds (fast iteration, "production deploys that make a verification engineer nervous"); ASICs give deterministic ns latency but no reconfig — only top firms tape out. **Career angle (directly relevant to your goals):** FPGA/RTL trading roles at **Jane Street, Jump Trading, Citadel Securities, Optiver, IMC, Hudson River Trading, Tower Research, DRW, XTX, Maven, Quantlab**; they want RTL fluency, comfort with order-book/trade-feed structures and FIX/OUCH/ITCH, HW/SW co-design, and quant communication. **Aegis-Stream is a strong interview artifact** — a portfolio-grade (not production) low-latency LOB + market-data replay is exactly what these firms respect.

### 5.7 What latency budget your actual system needs
**For the Stage 1–9 daily ETF system, a latency budget of seconds-to-minutes is entirely appropriate.** The real bottlenecks — and where to spend engineering effort:
1. **Data availability** — when the vendor publishes the EOD bar / when your PIT snapshot is ready.
2. **Workflow scheduling** — Prefect flow timing relative to market close.
3. **Broker fill timing** — **MOC/MOO cutoffs** (e.g., NYSE MOC ~15:50 ET) are the true hard deadlines; miss the cutoff and you don't trade.
4. **Order acknowledgment** — seconds is fine.

**Optimizing microsecond latency here would be premature optimization of the highest order** — it would add complexity and risk (recall Knight) for zero economic benefit. Spend that engineering on data correctness and overfitting control instead.

---

## 6. New Suggestions & Ideas

### 6.1 Agentic development workflow upgrades
- **Spec-driven development** (GitHub **Spec Kit** / spec-kit style): write the spec first, let agents implement against it — pairs perfectly with your AGENTS.md/CLAUDE.md split.
- **Test-first agent workflow:** Claude writes the failing (adversarial) test, Codex implements to green — enforces writer≠reviewer at the test level.
- **Property-based testing (Hypothesis)** for financial invariants: "weights sum ≤ gross limit," "no position exceeds 20%," "cash never negative," "no future timestamp used in a signal." Your **SVA-analogue**.
- **Hypothesis stateful testing** for the **order state machine** — model-based testing that random-walks the state machine hunting invariant violations.
- **Mutation testing (mutmut / cosmic-ray)** to validate that your *tests* actually catch bugs.
- **Formal methods for the order state machine:** **TLA+/PlusCal** or **Alloy** to model-check exactly-once/idempotency under crash+retry.
- **Differential testing** against a reference backtester (run the same strategy through Nautilus and your engine; diff the equity curves) — the "backtest-to-live divergence harness."
- **Metamorphic testing** (scaling all prices ⇒ predictable P&L scaling), **deterministic simulation testing** (FoundationDB/Antithesis style: seed all randomness, replay the whole day), **fuzzing broker responses** (malformed fills, out-of-order acks, dupes), **golden/approval testing** of reports.

### 6.2 Verification-engineering transplant (your differentiator)
The UVM mindset: **coverage-driven verification** (track which market/strategy states your tests exercise), **constrained-random stimulus** (Hypothesis is your generator), **assertions** (runtime invariant checks = SVA), **scoreboards** (an independent model predicts expected P&L/positions and checks against actual), and **formal property verification** (TLA+/Alloy). **Framing this explicitly — "I applied silicon-verification rigor to a trading system" — is exactly what a verification-hiring manager at Nvidia/Apple/Jane Street wants to see.**

### 6.3 CI/CD & supply chain
**SLSA provenance**, **sigstore/cosign** signing, **pip-audit / safety** for CVEs, **SBOM (CycloneDX / Syft)**, **Dependabot/Renovate**, **hash-pinned** dependencies, **reproducible builds**, and pre-commit **secret scanning (detect-secrets, gitleaks, trufflehog)** — the last directly enforces your "no secrets in repo" non-negotiable.

### 6.4 Missing stages / sub-stages to add
- **Stage 2.5 — Tax-lot accounting module** (FIFO/specific-ID, wash-sale tracking, Form 8949/1099-B reconciliation).
- **Stage 3.5 — Corporate-action edge-case module** (splits, spinoffs, special dividends, symbol changes, ETF reconstitutions) with a golden test set.
- **Stage 4.5 — Options-overlay design stage (explicitly deferred)** — document the interface now.
- **Stage 5.5 — Strategy-decommissioning process** — a written, gated way to retire a degraded strategy (mirror of the promotion state machine).
- **Stage 7.5 — Data-vendor migration abstraction** — a provider-neutral data interface so swapping Polygon↔Databento↔Norgate is config, not rewrite.
- **Stage 9.5 — Backtest-to-live divergence harness** (see 6.1 differential testing).

### 6.5 Alternative strategy sleeves (methodology, not recommendations)
Carry; cross-asset trend; seasonality/turn-of-month; **low-vol anomaly**; term-structure/roll-yield via ETFs; tail-hedge overlays; **cross-sectional ETF momentum**; defensive/risk-off rotation; and **pairs / statistical arbitrage on cointegrated ETF pairs**:
- **Cointegration:** **Engle-Granger** two-step — OLS $Y_t=\alpha+\beta X_t+u_t$ then **ADF unit-root test on the residual $u_t$** (H0 = no cointegration / non-stationary residual). **Johansen** (VECM $\Delta x_t=\Pi x_{t-1}+\sum\Gamma_i\Delta x_{t-i}+u_t$; **rank of $\Pi$** = number of cointegrating vectors; **trace** and **max-eigenvalue** statistics) — detects multiple relationships, no dependent-variable choice.
- **Ornstein-Uhlenbeck spread:** $dX_t=\theta(\mu-X_t)\,dt+\sigma\,dW_t$; stationary distribution $\mathcal N(\mu,\sigma^2/2\theta)$. **Half-life of mean reversion $=\ln 2/\theta$.** Estimate via OLS of $\Delta X_t=\lambda X_{t-1}+c+\varepsilon_t$; then $\theta=-\lambda$ and **half-life $=-\ln 2/\lambda$** (sign matters: $\lambda<0$ ⇒ positive half-life).
- **Signal:** $z_t=(Z_t-\text{mean}(Z))/\text{std}(Z)$ on spread $Z_t=Y_t-\beta X_t$; illustrative entry at $|z|\approx2$, exit toward 0, stop near $|z|\approx3$ (thresholds are parameters, not rules). **Kalman filter** for a **dynamic hedge ratio** $\beta_t$ (state = evolving $\beta,\alpha$; recursive updates; tracks structural breaks far better than rolling OLS).

### 6.6 Career/portfolio artifact strategy (ML or verification eng; Jane Street / D. E. Shaw / Nvidia / Apple)
- **Open-source** (build reputation, no alpha leak): the deterministic backtester harness, the PIT data-layer design, the property-based/formal testing of the order state machine, the DSR/PBO validation library, and **Aegis-Stream**.
- **Keep private:** any actual profitable signal, parameters, and live results.
- **Interview framing:** lead with the **verification story** (SVA→Hypothesis, scoreboards, TLA+ model-checking of exactly-once) and the **overfitting-control story** (DSR/PBO, purged CV) — both signal maturity. **Impresses:** "I assumed my backtest was lying and built the machinery to prove it"; "I model-checked the order state machine in TLA+." **Reads as naive:** a shiny Sharpe-4 equity curve with no deflation, no cost model, no PIT discipline.

### 6.7 Cost-control for agentic development
**Prompt caching** (a stable system-prompt prefix hits the ~90–98%-cheaper cache rate on DeepSeek/GLM/Kimi), **batch APIs** (40–60% off for async test-gen/refactors), **context/session hygiene** (compact context, drop stale files), **model routing** (mechanical work → free/flash tiers; hard reasoning → frontier), and **off-peak scheduling** before DeepSeek's announced peak surcharge lands.

---

## 7. Figures/Diagrams that would strengthen the report (for later rendering)
1. **Model cost-vs-capability scatter** — x = SWE-bench Pro, y = $/1M output (log), bubble = context window; highlights DeepSeek/Qwen/GLM/Kimi vs frontier Western.
2. **False Strategy Theorem curve** — expected max Sharpe vs number of independent trials N, with the N=1000 → 3.26 point annotated.
3. **Almgren-Chriss efficient frontier of execution** — expected cost vs cost variance, with sample optimal trajectories.
4. **Purged k-fold CV with embargo diagram** — timeline showing train/test blocks, purged overlap, and embargo buffer.
5. **Order-lifecycle state machine** — PENDING→SENT→ACKED→PARTIAL→FILLED/REJECTED with idempotency keys and persisted transitions.
6. **Three-lines-of-defense mapping** — Codex (implement) / Claude Code (validate) / CI+human (assure), overlaid on SR 11-7.
7. **Live-vs-backtest equity curve** with a CUSUM/EWMA degradation alarm firing.
8. **Latency spectrum (log scale)** — REST 100 ms → WebSocket → kernel-bypass 2 μs → FPGA 100 ns → transceiver 3 ns, with your system's operating point circled at the "minutes" end.
9. **System architecture** — PIT data layer → Nautilus engine → validation (DSR/PBO) → paper broker → observability, with the "no LLM in execution path" boundary drawn explicitly.
10. **Model-routing dataflow** — which model drives which agent for which task type.

---

## 8. Bottom line & staged recommendations
Your architecture is sound; the highest-value changes, in order:

**Stage now (design-time decisions):**
1. **Adopt Nautilus Trader** for the execution/backtest core (its Rust-core order state machines and true backtest/live parity retire your biggest engine risk) while **keeping your PIT-data (Stage 2) and statistical-validation (Stage 5) layers hand-rolled** as differentiators.
2. **Set up the model-routing rig** (claude-code-router / LiteLLM): bulk implementation → DeepSeek V4 Flash / Qwen3-Coder / a GLM coding plan; adversarial review → a *different* vendor from the implementer; **self-host Qwen3-30B-A3B** for any runtime research agents so no strategy data ever egresses.

**Stage next (build-time):**
3. **Over-invest in overfitting control** — implement DSR, PBO/CSCV, purged-CV-with-embargo, and a trial registry before writing a single "promising" strategy. Treat any net Sharpe > 1 after deflation as suspect until proven in paper/live.
4. **Build the pre-trade control + kill-switch + reconciliation layer deterministically** (mirroring 15c3-5), with halt state persisted outside process memory.

**Benchmarks/thresholds that would change these recommendations:**
- If you ever move to **intraday/sub-second frequency**, revisit latency (WebSocket + async, colocation still irrelevant until true HFT) and the microstructure math in §2.10.
- If your **development token spend exceeds ~$300/mo**, shift more work to self-hosted Qwen3-30B-A3B and batch APIs.
- If a strategy's **live-vs-backtest tracking error breaches your pre-set band** or its CUSUM chart alarms, trigger the Stage 5.5 decommissioning process.
- If you ever intend to **manage outside capital**, stop and get RIA/Series 65 (or CTA/Series 3) advice first — that crosses a bright regulatory line this report does not.

**And frame the whole thing — especially Aegis-Stream and the formal/property-based verification — as a verification-engineering portfolio artifact**, which is where your comparative advantage over other quant-curious candidates actually lies.

*Reminder: general methodology only; nothing here recommends trading or investing, and all regulatory/tax points must be confirmed with a qualified professional and your employer's compliance function.*