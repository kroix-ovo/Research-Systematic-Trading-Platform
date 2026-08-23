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
                     SPLG_PRICE, SPLG_EXPENSE, TURNOVER,
                     SPLG_HALF)                                # noqa: E402

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
        y = [mvc(F, s) for s in srs]
        ax.semilogy(srs, y, color=col, lw=1.8,
                    label=f"{name}  (\\${F:,.0f}/yr)")
    ax.axhline(CAPITAL, color=INK, lw=1.3, ls=(0, (4, 3)))
    ax.text(0.175, CAPITAL * 1.30, "\\$3,000 starting capital", fontsize=7.0,
            color=INK, ha="left")
    ax.axvspan(0.3, 0.8, color=SLATE, alpha=0.08, lw=0)
    ax.text(0.315, 2.2e4, "realistic solo Sharpe range (section 4.8)",
            fontsize=6.6, color=MUTED, ha="center", va="center",
            rotation=90)
    ax.set_xlabel("expected Sharpe ratio (excess returns)")
    ax.set_ylabel("minimum viable capital  (log scale)")
    ax.set_title("(a) MVC is hyperbolic in Sharpe, linear in fixed cost")
    ax.set_xlim(0.15, 1.0)
    ax.set_ylim(1e3, 1e6)
    ax.legend(loc="upper right", fontsize=6.6)
    despine(ax)
    note(ax, "curves below the dashed line are affordable at \\$3,000",
         loc="lower center", fontsize=6.5)

    # -------------------------------------------- (b) net P&L vs capital
    ax = fig.add_subplot(gs[0, 1])
    caps = np.logspace(3, 5.3, 400)
    sr = 0.5
    for name, keys, col in STACKS:
        F = annual_fixed(*keys)
        pnl = caps * net_rate(sr) - F
        ax.plot(caps, pnl, color=col, lw=1.8)
        be = mvc(F, sr)
        if 1e3 < be < 2e5:
            ax.plot([be], [0], "o", ms=5, color=col, mfc="white", mew=1.4,
                    zorder=5)
    ax.set_xscale("log")
    ax.axhline(0, color=INK, lw=1.0)
    ax.axvline(CAPITAL, color=INK, lw=1.3, ls=(0, (4, 3)))
    ax.text(CAPITAL * 1.15, -7400, "\\$3,000", fontsize=7.0, color=INK)
    ax.fill_between(caps, -8000, 0, color=RED, alpha=0.05, lw=0)
    ax.text(1.05e3, -5400, "loses money in expectation\neven with a real edge",
            fontsize=6.9, color=RED)
    ax.set_xlabel("capital  (log scale)")
    ax.set_ylabel("expected net annual P&L  (USD)")
    ax.set_title(f"(b) Break-even points at Sharpe {sr}")
    ax.set_ylim(-8000, 9000)
    ax.set_xlim(1e3, 2e5)
    despine(ax)
    note(ax, "circles mark break-even capital\nfor each cost stack",
         loc="upper left", fontsize=6.5)

    # ------------------------------------------ (c) the $3,000 verdict
    ax = fig.add_subplot(gs[1, 0])
    gross = 0.5 * VOL_TARGET * CAPITAL
    prop = CAPITAL * (SPLG_EXPENSE + TURNOVER * SPLG_HALF)
    names, nets, cols = [], [], []
    for name, keys, col in STACKS:
        F = annual_fixed(*keys)
        names.append(name.split(":")[0].replace(" + ", "+"))
        nets.append(gross - prop - F)
        cols.append(GREEN if gross - prop - F > 0 else RED)
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
    ax.set_xlabel("expected net annual P&L at \\$3,000  (USD)")
    ax.set_title("(c) At \\$3,000, only a zero-subscription stack survives")
    ax.set_xlim(-4000, 1100)
    despine(ax)
    note(ax, f"gross expected return \\${gross:.0f}/yr at Sharpe 0.5;\n"
             f"a \\$30/mo data plan costs \\$360/yr",
         loc="upper left", fontsize=6.5)

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
