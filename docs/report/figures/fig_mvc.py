"""Minimum Viable Capital figures, generated from v10_mvc's own code paths."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verify"))
from style import (setup, save, despine, note, style3d, INK, MUTED, GRID,
                   PANEL, BLUE, RED, GREEN, AMBER, PURPLE, TEAL, PINK,
                   SLATE)                                      # noqa: E402
from v10_mvc import (PRICING, annual_fixed, net_rate, mvc, VOL_TARGET,
                     SPLG_PRICE, SPLG_EXPENSE, TURNOVER, SPLG_HALF,
                     TAX_RATE, sr_standard_error)              # noqa: E402

SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#eef2ff", "#c7d6fb", "#8fb0f4", "#4d7fe8", "#2563eb", "#15379c"])

STACKS = [
    ("free: Tiingo Starter + laptop", ("tiingo_starter", "laptop"), GREEN),
    ("Tiingo Power + laptop", ("tiingo_power", "laptop"), TEAL),
    ("Tiingo Power + VPS", ("tiingo_power", "vps_hetzner"), BLUE),
    ("Massive Advanced + VPS", ("massive_advanced", "vps_hetzner"), AMBER),
    ("Massive Adv + Alpaca Plus + VPS",
     ("massive_advanced", "alpaca_plus", "vps_hetzner"), RED),
]
CAPITAL = 3000.0


def fig_mvc():
    fig = plt.figure(figsize=(10.0, 6.4))
    gs = fig.add_gridspec(2, 2, hspace=0.42, wspace=0.28,
                          height_ratios=[1, 1])

    # ---------------------------------------------------- (a) MVC vs Sharpe
    ax = fig.add_subplot(gs[0, 0])
    srs = np.linspace(0.15, 1.0, 300)
    for name, keys, col in STACKS:
        F = annual_fixed(*keys)
        if F == 0:
            continue
        ax.semilogy(srs, [mvc(F, s) for s in srs], color=col, lw=1.8,
                    label=f"{name}  (\\${F:,.0f}/yr)")
        ax.semilogy(srs, [mvc(F, s, tax=TAX_RATE) for s in srs], color=col,
                    lw=1.0, ls=(0, (2, 2)), alpha=0.75)
    ax.axhline(CAPITAL, color=INK, lw=1.3, ls=(0, (4, 3)))
    ax.text(0.175, CAPITAL * 1.30, "\\$3,000 starting capital", fontsize=7.0,
            color=INK, ha="left")
    ax.axvspan(0.3, 0.8, color=SLATE, alpha=0.08, lw=0)
    ax.text(0.55, 6.0e5, "realistic solo Sharpe range (section 4.8)",
            fontsize=6.5, color=MUTED, ha="center", va="center")
    ax.set_xlabel("expected Sharpe ratio (excess returns)")
    ax.set_ylabel("minimum viable capital  (log scale)")
    ax.set_title("(a) MVC is hyperbolic in Sharpe, linear in fixed cost")
    ax.set_xlim(0.15, 1.0)
    ax.set_ylim(1e3, 1e6)
    ax.legend(loc="upper right", fontsize=6.4)
    despine(ax)
    note(ax, "solid = untaxed;  dotted = after 30% short-term tax\n"
             "(tax raises every floor by 1/(1-t) = +43%)",
         loc="lower center", fontsize=6.3)

    # ------------------------------- (b) MVC is an interval, not a number
    ax = fig.add_subplot(gs[0, 1])
    F = annual_fixed("tiingo_power", "laptop")
    sr_hat = 0.5
    yrs = np.arange(2, 31)
    lo_mvc, hi_mvc, inf_from = [], [], None
    for y in yrs:
        se = sr_standard_error(sr_hat, float(y))
        sr_lo, sr_hi = sr_hat - 1.96 * se, sr_hat + 1.96 * se
        lo_mvc.append(mvc(F, sr_hi, tax=TAX_RATE))
        hv = mvc(F, sr_lo, tax=TAX_RATE)
        hi_mvc.append(hv if math.isfinite(hv) else np.nan)
        if not math.isfinite(hv):
            inf_from = y
    lo_mvc = np.array(lo_mvc)
    hi_mvc = np.array(hi_mvc)
    top = 1e6

    ax.fill_between(yrs, lo_mvc, np.nan_to_num(hi_mvc, nan=top),
                    color=AMBER, alpha=0.18, lw=0)
    ax.semilogy(yrs, lo_mvc, color=GREEN, lw=1.8,
                label="optimistic end of 95% Sharpe CI")
    ax.semilogy(yrs, hi_mvc, color=RED, lw=1.8,
                label="pessimistic end of 95% Sharpe CI")
    if inf_from is not None:
        ax.axvspan(yrs[0], inf_from + 0.5, color=RED, alpha=0.07, lw=0)
        ax.text((yrs[0] + inf_from) / 2, 3.4e5,
                "Sharpe CI contains zero\n→ MVC unbounded above",
                ha="center", fontsize=6.9, color=RED)
    ax.axhline(CAPITAL, color=INK, lw=1.3, ls=(0, (4, 3)))
    ax.text(29.4, CAPITAL * 1.28, "\\$3,000", fontsize=7.0, color=INK,
            ha="right")
    ax.set_xlabel("years of data used to estimate the Sharpe ratio")
    ax.set_ylabel("minimum viable capital  (log scale)")
    ax.set_title("(b) MVC is an interval, not a number")
    ax.set_ylim(1e3, top)
    ax.set_xlim(2, 30)
    ax.legend(loc="lower left", fontsize=6.6)
    despine(ax)
    note(ax, "point estimate \\$5,790 at $\\widehat{SR}=0.5$;\n"
             "even the optimistic bound exceeds \\$3,000",
         loc="upper right", fontsize=6.4)

    # ------------------------------------------ (c) the $3,000 verdict
    ax = fig.add_subplot(gs[1, 0])
    gross = 0.5 * VOL_TARGET * CAPITAL
    prop = CAPITAL * (SPLG_EXPENSE + TURNOVER * SPLG_HALF)
    names, nets, cols = [], [], []
    for name, keys, col in STACKS:
        F = annual_fixed(*keys)
        names.append(name.split(":")[0].replace(" + ", "+"))
        nets.append((1 - TAX_RATE) * (gross - prop) - F)
        cols.append(GREEN if (1 - TAX_RATE) * (gross - prop) - F > 0 else RED)
    y = np.arange(len(names))
    ax.barh(y, nets, color=cols, height=0.6, edgecolor="none")
    ax.axvline(0, color=INK, lw=1.0)
    for i, v in enumerate(nets):
        ax.text(v + (60 if v > 0 else -60), i, f"\\${v:+,.0f}", va="center",
                ha="left" if v > 0 else "right", fontsize=7.0,
                color=GREEN if v > 0 else RED)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.0)
    ax.invert_yaxis()
    ax.set_xlabel("expected AFTER-TAX net annual P&L at \\$3,000  (USD)")
    ax.set_title("(c) After tax, even the free stack barely clears zero")
    ax.set_xlim(-4000, 1100)
    despine(ax)
    note(ax, f"gross \\${gross:.0f}/yr at Sharpe 0.5, "
             f"\\${(1 - TAX_RATE) * (gross - prop):.0f} after 30% tax;\n"
             f"a \\$30/mo data plan costs \\$360/yr",
         loc="upper left", fontsize=6.4)

    # ------------------------------------------ (d) capital by phase
    ax = fig.add_subplot(gs[1, 1])
    phases = ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"]
    cap_req = [0, 0, 0, 0, 0, 0, 3000, 12000]
    fixed = [annual_fixed("laptop"),
             annual_fixed("tiingo_power", "laptop") + 199,
             annual_fixed("tiingo_power", "laptop"),
             annual_fixed("tiingo_power", "laptop"),
             annual_fixed("tiingo_power", "laptop"),
             annual_fixed("tiingo_power", "vps_hetzner"),
             annual_fixed("tiingo_power", "vps_hetzner"),
             annual_fixed("tiingo_power", "vps_hetzner")]
    x = np.arange(len(phases))
    ax.bar(x, cap_req, color=BLUE, width=0.6, edgecolor="none",
           label="trading capital required")
    ax2 = ax.twinx()
    ax2.plot(x, fixed, "o-", color=AMBER, ms=4.5, mfc="white", mew=1.3,
             label="recurring cost (USD/yr)")
    ax2.set_ylabel("recurring cost  (USD/yr)", color=AMBER, fontsize=8)
    ax2.tick_params(axis="y", colors=AMBER, labelsize=7)
    ax2.grid(False)
    ax2.spines["top"].set_visible(False)
    ax2.set_ylim(0, 700)
    ax.axvspan(-0.5, 5.5, color=GREEN, alpha=0.07, lw=0)
    ax.text(2.5, 1500, "no trading capital required", ha="center",
            fontsize=7.2, color=GREEN)
    ax.annotate("capital constraint\nfirst binds here", xy=(6, 3000),
                xytext=(4.4, 6800), fontsize=6.9, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.9,
                                connectionstyle="arc3,rad=-0.25"))
    ax.set_xticks(x)
    ax.set_xticklabels(phases)
    ax.set_xlabel("build milestone")
    ax.set_ylabel("trading capital  (USD)", color=BLUE)
    ax.tick_params(axis="y", colors=BLUE)
    ax.set_ylim(0, 13000)
    ax.set_title("(d) Capital does not bind until M6")
    despine(ax, left=True)
    note(ax, "M1's cost spike is one month of quote data to\ncalibrate the "
             "spread term — a measurement,\nnot a subscription.",
         loc="upper center", fontsize=6.4)

    fig.suptitle("Figure 21 — Minimum Viable Capital: at small size the binding "
                 "constraint is the vendor invoice, not the market",
                 fontsize=10, color=INK, y=0.985)
    save(fig, "fig21_mvc")


if __name__ == "__main__":
    setup()
    print("  MVC figures:")
    fig_mvc()
