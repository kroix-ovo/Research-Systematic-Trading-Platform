"""Minimum Viable Capital (MVC) -- how much capital is needed for an edge to
survive costs, phase by phase.

The question this answers: a strategy can have a genuine, statistically real
edge and still lose money, because fixed costs do not scale with capital. Below
some capital level the data subscription alone consumes the entire expected
return. That level is the Minimum Viable Capital.

Framework
---------
Let C = capital, SR = expected Sharpe of EXCESS returns (over the risk-free
rate), sigma = target annualised volatility.

    gross excess P&L        = SR * sigma * C
    proportional costs      = C * (e + tau * s_half)
    fixed costs             = F                        (independent of C)

where e = fund expense ratio, tau = annual one-way turnover as a fraction of
capital, s_half = half-spread paid per unit of traded notional.

    net expected profit(C)  = C * (SR*sigma - e - tau*s_half) - F

Setting this to zero gives the break-even MVC:

    MVC = F / (SR*sigma - e - tau*s_half)

Because SR appears in the denominator, MVC is hyperbolic in Sharpe: halving the
expected Sharpe doubles the capital required. And because F sits in the
numerator, the choice of data tier -- a decision made before any strategy work
begins -- sets the capital floor for the whole enterprise.

Provider pricing was read from vendor pricing pages in August 2026 and is
recorded in PRICING below. Pricing is dated and must be re-verified.
"""

from __future__ import annotations

import math

import numpy as np

from harness import Registry, rng

SEC = "MVC. Minimum viable capital"

# ---------------------------------------------------------------------------
# Provider pricing, read from vendor pricing pages 2026-08-21.
# Monthly USD for individual / non-professional use.
# ---------------------------------------------------------------------------
PRICING = {
    # Massive (formerly Polygon.io) -- massive.com/pricing, Stocks tab
    "massive_basic":     {"usd_mo": 0,   "history_yr": 2,  "quotes": False,
                          "note": "5 API calls/min, EOD only"},
    "massive_starter":   {"usd_mo": 29,  "history_yr": 5,  "quotes": False,
                          "note": "unlimited calls, 15-min delayed"},
    "massive_developer": {"usd_mo": 79,  "history_yr": 10, "quotes": False,
                          "note": "adds trades"},
    "massive_advanced":  {"usd_mo": 199, "history_yr": 20, "quotes": True,
                          "note": "real-time, quotes, financials; non-pro only"},
    "massive_imbalance": {"usd_mo": 49,  "history_yr": 0,  "quotes": False,
                          "note": "NYSE auction order imbalances"},
    # Tiingo -- tiingo.com/pricing, individual
    "tiingo_starter":    {"usd_mo": 0,   "history_yr": 30, "quotes": False,
                          "note": "500 symbols/mo, 1k req/day, internal use only"},
    "tiingo_power":      {"usd_mo": 30,  "history_yr": 30, "quotes": False,
                          "note": "100k req/day, 40GB/mo, internal use only"},
    # Alpaca -- alpaca.markets/data
    "alpaca_free":       {"usd_mo": 0,   "history_yr": 7,  "quotes": False,
                          "note": "IEX only, 200 calls/min, 15-min delayed API"},
    "alpaca_plus":       {"usd_mo": 99,  "history_yr": 7,  "quotes": True,
                          "note": "full SIP, unlimited calls"},
    # Infrastructure
    "vps_hetzner":       {"usd_mo": 6,   "history_yr": 0,  "quotes": False,
                          "note": "CX22-class always-on VPS"},
    "laptop":            {"usd_mo": 0,   "history_yr": 0,  "quotes": False,
                          "note": "cron on existing hardware"},
}

# Instrument parameters (SPLG, the slice-01 implementation choice)
SPLG_PRICE = 78.0
SPLG_EXPENSE = 0.0002        # 2 bp
SPLG_SPREAD_BP = 1.28        # 1-cent quoted spread at $78
SPLG_HALF = SPLG_SPREAD_BP / 2 / 1e4

VOL_TARGET = 0.125           # quarter-Kelly at an assumed Sharpe of 0.5
TURNOVER = 2.0               # annual one-way turnover, vol-managed monthly


def run(reg: Registry) -> None:
    _pricing_table(reg)
    _mvc_formula(reg)
    _mvc_ladder(reg)
    _three_thousand_verdict(reg)
    _granularity_floor(reg)
    _phase_costs(reg)
    _statistical_independence(reg)


# ---------------------------------------------------------------------------
def annual_fixed(*keys: str) -> float:
    return 12.0 * sum(PRICING[k]["usd_mo"] for k in keys)


def net_rate(sr: float, sigma: float = VOL_TARGET,
             e: float = SPLG_EXPENSE, tau: float = TURNOVER,
             s_half: float = SPLG_HALF) -> float:
    """Net proportional return rate after all capital-proportional costs."""
    return sr * sigma - e - tau * s_half


def mvc(F: float, sr: float, **kw) -> float:
    r = net_rate(sr, **kw)
    return float("inf") if r <= 0 else F / r


def _pricing_table(reg: Registry) -> None:
    """Record the pricing that every downstream number depends on."""
    cheapest_30yr = min(
        (k for k, v in PRICING.items() if v["history_yr"] >= 20),
        key=lambda k: PRICING[k]["usd_mo"])
    cheapest_quotes = min(
        (k for k, v in PRICING.items() if v["quotes"]),
        key=lambda k: PRICING[k]["usd_mo"])
    reg.add(
        "MVC-01", SEC,
        "Provider pricing as read from vendor pages, August 2026",
        "browser read of massive.com/pricing, tiingo.com/pricing, "
        "alpaca.markets/data",
        "-",
        f"cheapest 20+yr history: {cheapest_30yr} at "
        f"\\${PRICING[cheapest_30yr]['usd_mo']}/mo; cheapest quote-level "
        f"data: {cheapest_quotes} at "
        f"\\${PRICING[cheapest_quotes]['usd_mo']}/mo",
        "INFO",
        r"The single most consequential pricing fact for a small account: "
        r"\textbf{Tiingo's free tier carries 30+ years of end-of-day history}, "
        r"and its \$30/mo Power tier lifts the rate limits without changing the "
        r"history. Massive's 20+ year archive costs \$199/mo because it is "
        r"bundled with real-time and quote data. A daily-frequency strategy "
        r"needs neither. Quote data is required only to calibrate the spread "
        r"term of the cost model, which is a one-off measurement rather than a "
        r"subscription. Buying the wrong tier is the most expensive mistake "
        r"available at this account size, and it is made before any research "
        r"begins.",
        pricing=PRICING,
    )


def _mvc_formula(reg: Registry) -> None:
    """Verify the closed form against a direct numerical root-find."""
    F, sr = 360.0, 0.5
    analytic = mvc(F, sr)

    # Independent check: bisection on the profit function.
    def profit(C):
        return C * net_rate(sr) - F

    lo, hi = 1.0, 1e9
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if profit(mid) < 0:
            lo = mid
        else:
            hi = mid
    numeric = math.sqrt(lo * hi)
    reg.close(
        "MVC-02", SEC,
        r"Break-even MVC $=F/(SR\sigma-e-\tau s_{1/2})$",
        "closed form vs bisection on the profit function, F=\\$360/yr, SR=0.5",
        analytic, numeric, rtol=1e-6,
        note="Confirms the algebra. The formula's shape is the finding: MVC is "
             "hyperbolic in Sharpe and linear in fixed cost, so a halved Sharpe "
             "expectation doubles the capital floor, and every dollar of "
             "monthly subscription raises it by 12/(net rate) dollars.",
    )

    # The leverage of a single subscription dollar.
    r = net_rate(0.5)
    per_dollar_month = 12.0 / r
    reg.add(
        "MVC-03", SEC,
        "Each \\$1/month of fixed cost raises the capital floor by "
        "12/(net rate)",
        "differentiate MVC with respect to monthly fixed cost at SR=0.5",
        "-", f"\\${per_dollar_month:,.0f} of required capital per \\$1/mo",
        "INFO",
        rf"At a Sharpe of 0.5 and a {VOL_TARGET:.1%} volatility target, every "
        rf"\$1/month of recurring cost adds \${per_dollar_month:,.0f} to the "
        r"capital needed to break even. A \$99/mo market-data plan therefore "
        rf"carries a \${99 * per_dollar_month:,.0f} capital prerequisite. This "
        r"is the number to put in front of any subscription decision.",
        per_dollar_month=per_dollar_month,
    )


def _mvc_ladder(reg: Registry) -> None:
    """MVC across realistic Sharpe expectations and cost stacks."""
    stacks = [
        ("free everything (Tiingo Starter + laptop)",
         annual_fixed("tiingo_starter", "laptop")),
        ("Tiingo Power + laptop", annual_fixed("tiingo_power", "laptop")),
        ("Tiingo Power + VPS", annual_fixed("tiingo_power", "vps_hetzner")),
        ("Massive Advanced + VPS",
         annual_fixed("massive_advanced", "vps_hetzner")),
        ("Massive Advanced + Alpaca Plus + VPS",
         annual_fixed("massive_advanced", "alpaca_plus", "vps_hetzner")),
    ]
    sharpes = (0.8, 0.5, 0.3, 0.2)
    rows = []
    for name, F in stacks:
        rows.append((name, F, [mvc(F, s) for s in sharpes]))

    tiingo_row = rows[1]
    heavy_row = rows[-1]
    reg.add(
        "MVC-04", SEC,
        "Minimum viable capital across cost stacks and Sharpe expectations",
        f"MVC = F / (SR*sigma - e - tau*s_half), sigma={VOL_TARGET:.3f}, "
        f"e={SPLG_EXPENSE * 1e4:.0f}bp, tau={TURNOVER:.1f}/yr, "
        f"half-spread={SPLG_HALF * 1e4:.2f}bp",
        "MVC rises hyperbolically as Sharpe falls",
        "; ".join(
            f"{n} (\\${F:,.0f}/yr): "
            + "/".join(f"{v:,.0f}" for v in vals)
            for n, F, vals in rows[1:4]) + "  [at SR 0.8/0.5/0.3/0.2]",
        "PASS",
        r"The table is the answer to ``how much capital do I need''. At the "
        rf"realistic Sharpe range the report's section 4.8 gives for a solo "
        rf"operator (0.3--0.8), a lean stack "
        rf"(\${tiingo_row[1]:,.0f}/yr) implies a floor of roughly "
        rf"\${tiingo_row[2][0]:,.0f}--\${tiingo_row[2][2]:,.0f}. The same "
        rf"strategy on a full real-time stack "
        rf"(\${heavy_row[1]:,.0f}/yr) needs "
        rf"\${heavy_row[2][0]:,.0f}--\${heavy_row[2][2]:,.0f}. "
        r"Nothing about the strategy changed between those two rows -- only the "
        r"subscription decision. For a daily-frequency system the lean stack is "
        r"not a compromise: end-of-day bars are the entire data requirement, "
        r"and Tiingo's free tier already carries more history than the "
        r"post-decimalisation sample can use.",
        table=[{"stack": n, "fixed_usd_yr": F,
                "mvc": dict(zip(map(str, sharpes), vals))}
               for n, F, vals in rows],
        sharpes=list(sharpes),
    )


def _three_thousand_verdict(reg: Registry) -> None:
    """The specific question: is $3,000 viable?"""
    C = 3000.0
    sr = 0.5
    gross = sr * VOL_TARGET * C
    prop = C * (SPLG_EXPENSE + TURNOVER * SPLG_HALF)
    rows = []
    for name, keys in (
            ("free (Tiingo Starter + laptop)", ("tiingo_starter", "laptop")),
            ("Tiingo Power + laptop", ("tiingo_power", "laptop")),
            ("Tiingo Power + VPS", ("tiingo_power", "vps_hetzner")),
            ("Massive Advanced + VPS", ("massive_advanced", "vps_hetzner")),
    ):
        F = annual_fixed(*keys)
        rows.append((name, F, gross - prop - F))

    viable = [r for r in rows if r[2] > 0]
    reg.truth(
        "MVC-05", SEC,
        r"At \$3,000 the strategy is viable ONLY on a zero-subscription stack",
        f"expected annual P\\&L at C=\\${C:,.0f}, SR={sr}, "
        f"sigma={VOL_TARGET:.1%}: gross \\${gross:.2f}, proportional costs "
        f"\\${prop:.2f}, minus fixed costs",
        len(viable) == 1,
        "only the free stack clears zero",
        "; ".join(f"{n}: {p:+.0f}/yr" for n, F, p in rows),
        rf"At \$3,000 with a Sharpe of 0.5, the expected gross excess return is "
        rf"\${gross:.0f}/yr. A \$30/mo data plan costs \$360/yr. The "
        r"subscription alone is roughly double the entire expected return, so "
        r"the account loses money in expectation \emph{even if the edge is "
        r"completely real}. This is the central practical finding of the "
        r"section: at small capital the binding constraint is not the market, "
        r"the broker, or the strategy -- it is the vendor invoice. The only "
        r"configuration that survives at \$3,000 is free data on existing "
        r"hardware, which for a single-ETF daily strategy is genuinely "
        r"sufficient. Commission is not the issue once the broker is "
        r"zero-commission; the recurring fixed cost is.",
        gross=gross, proportional=prop,
        table=[{"stack": n, "fixed": F, "net": p} for n, F, p in rows],
    )


def _granularity_floor(reg: Registry) -> None:
    """A second, independent capital floor: share quantisation."""
    rows = []
    for C in (1000, 3000, 5000, 10000, 25000, 50000):
        step = SPLG_PRICE / C                     # one share as fraction of book
        rms = step / math.sqrt(12)                # uniform quantisation error
        vol_err = rms * 0.15                      # on a 15%-vol underlying
        rows.append((C, math.floor(C / SPLG_PRICE), step, rms, vol_err))

    # Threshold: quantisation-induced vol error under 10% of the target.
    tol = 0.10 * VOL_TARGET
    ok = [r for r in rows if r[4] < tol]
    floor = ok[0][0] if ok else float("nan")
    reg.truth(
        "MVC-06", SEC,
        "Share quantisation imposes a capital floor independent of costs",
        f"whole-share granularity on SPLG at ${SPLG_PRICE:.0f}; RMS "
        f"quantisation error converted to volatility tracking error against a "
        f"{VOL_TARGET:.1%} target",
        floor <= 3000,
        f"error below 10% of target vol ({tol:.2%})",
        "; ".join(f"\\${C:,}: {n} sh, vol err {v:.2%}"
                  for C, n, s, r, v in rows[:4]),
        r"A second floor, independent of the cost floor and often overlooked. "
        r"Volatility targeting requires continuously adjustable exposure; whole "
        r"shares quantise it. The instrument choice does most of the work here: "
        rf"SPLG at \${SPLG_PRICE:.0f} clears the threshold at \$3,000, whereas "
        r"an S\&P 500 ETF priced near \$600 would leave only five shares and a "
        r"0.87\% volatility tracking error -- a 7\% relative miss on the exact "
        r"quantity the strategy exists to control. Fractional-share support "
        r"removes this floor entirely where the broker offers it reliably, "
        r"which is a concrete reason to verify fractional order handling before "
        r"committing to an instrument.",
        table=[{"capital": C, "shares": n, "step": s, "rms": r, "vol_err": v}
               for C, n, s, r, v in rows],
    )


def _phase_costs(reg: Registry) -> None:
    """Capital and cost requirement by build phase."""
    phases = [
        ("M0 governance", 0.0, annual_fixed("laptop"),
         "no data, no capital: registry, contracts, CI"),
        ("M1 slice research", 0.0,
         annual_fixed("tiingo_power", "laptop") + 199.0,
         "EOD history all year, plus ONE month of quote data to calibrate "
         "the spread term"),
        ("M2 hardening", 0.0, annual_fixed("tiingo_power", "laptop"),
         "no new data requirement"),
        ("M3 sleeves 2-3", 0.0, annual_fixed("tiingo_power", "laptop"),
         "same universe scope"),
        ("M4 allocation", 0.0, annual_fixed("tiingo_power", "laptop"),
         "no new data requirement"),
        ("M5 paper portfolio", 0.0,
         annual_fixed("tiingo_power", "vps_hetzner"),
         "always-on host required for daily reconciliation"),
        ("M6 live minimum", 3000.0,
         annual_fixed("tiingo_power", "vps_hetzner"),
         "capital sized to measure execution, not to earn"),
        ("M7 scale", float("nan"),
         annual_fixed("tiingo_power", "vps_hetzner"),
         "capital above MVC for the achieved Sharpe"),
    ]
    total_to_m5 = sum(p[2] for p in phases[:6]) / 12 * 1  # rough monthly sum
    reg.add(
        "MVC-07", SEC,
        "Capital and recurring cost by build phase",
        "phase-by-phase requirement derived from the milestone structure",
        "-",
        "; ".join(f"{n}: \\${F:,.0f}/yr" for n, C, F, _ in phases[:7]),
        "INFO",
        r"Milestones M0 through M5 require \emph{no trading capital at all} -- "
        r"only the recurring data and infrastructure cost. That is the "
        r"scheduling insight hiding in the MVC arithmetic: the capital "
        r"constraint does not bind until M6, roughly six to nine months into "
        r"the build, so capital accumulation and platform construction can run "
        r"in parallel. The one irregular line is M1, which needs a single "
        r"month of quote-level data (about \$199, or \$99 on the broker's own "
        r"feed) to calibrate the spread term of the cost model. Buy it, "
        r"calibrate, cancel: it is a measurement, not a subscription. Treating "
        r"it as recurring would raise the M6 capital floor by roughly "
        rf"\${199 * 12 / net_rate(0.5):,.0f}.",
        table=[{"phase": n, "capital": C, "fixed_usd_yr": F, "note": d}
               for n, C, F, d in phases],
    )


def _statistical_independence(reg: Registry) -> None:
    """MVC is about economics; it says nothing about whether you can TELL."""
    C, sr = 3000.0, 0.5
    exp_pnl = sr * VOL_TARGET * C
    sd_pnl = VOL_TARGET * C
    # Years for the t-stat on live P&L to reach 2.
    years = (2.0 / sr) ** 2
    reg.add(
        "MVC-08", SEC,
        "Clearing the MVC bar does not make the result measurable",
        f"expected vs realised dispersion of annual P\\&L at C=\\${C:,.0f}, "
        f"SR={sr}",
        "-",
        f"expected \\${exp_pnl:.0f}/yr against a standard deviation of "
        f"\\${sd_pnl:.0f}/yr; {years:.0f} years for a t-statistic of 2",
        "INFO",
        rf"At \$3,000 the expected annual profit is \${exp_pnl:.0f} against a "
        rf"\${sd_pnl:.0f} standard deviation -- the noise is "
        rf"{sd_pnl / exp_pnl:.0f} times the signal. Scaling capital scales both "
        r"identically, so \emph{no amount of capital makes live P\&L "
        r"informative faster}. This is the same result as S-11 from a different "
        r"direction, and it is the reason the charter's milestone M6 is defined "
        r"as validating the cost model and the plumbing rather than the edge. "
        r"MVC answers ``will this lose money by construction''. It does not "
        r"answer ``does the edge exist'', and the two questions should never be "
        r"conflated in a promotion decision.",
        exp_pnl_usd=exp_pnl, sd_usd=sd_pnl, years_for_t2=years,
    )
