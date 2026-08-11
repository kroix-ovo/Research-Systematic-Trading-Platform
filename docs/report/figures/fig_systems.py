"""Systems and process diagrams: architecture, state machine, governance,
latency spectrum, model routing, and the model cost/capability landscape."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verify"))
from style import (setup, save, despine, note, INK, MUTED, GRID, PANEL,
                   BLUE, RED, GREEN, AMBER, PURPLE, TEAL, PINK, SLATE)  # noqa

from harness import rng                                    # noqa: E402


def _box(ax, x, y, w, h, label, sub="", fc="white", ec=SLATE, tc=INK,
         fs=7.6, lw=1.0, radius=0.02, bold=True):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2 + (0.016 if sub else 0), label,
            ha="center", va="center", fontsize=fs, color=tc,
            weight="600" if bold else "normal", zorder=3)
    if sub:
        ax.text(x + w / 2, y + h * 0.21, sub, ha="center", va="center",
                fontsize=6.0, color=MUTED, zorder=3)
    return (x + w / 2, y + h / 2, x, y, w, h)


def _arrow(ax, p0, p1, color=SLATE, lw=1.1, style="-|>", rad=0.0, ls="-"):
    a = FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=9,
                        color=color, lw=lw, zorder=1, linestyle=ls,
                        connectionstyle=f"arc3,rad={rad}",
                        shrinkA=1.5, shrinkB=1.5)
    ax.add_patch(a)


# ==========================================================================
# Figure 1 — model cost vs capability
# ==========================================================================
def fig_model_landscape():
    # Values transcribed from the report's own sections 1.2 and 1.6.
    # Provenance is uneven; the report flags this and so does the caption.
    models = [
        # name, SWE-bench Pro %, $/1M out, context K, family
        ("DeepSeek V4-Pro",   59.5, 0.87,  1000, "DeepSeek"),
        ("DeepSeek V4 Flash", 52.0, 0.28,  1000, "DeepSeek"),
        ("MiniMax M3",        59.0, 1.20,   200, "MiniMax"),
        ("Qwen3.7 Max",       60.6, 3.90,   262, "Qwen"),
        ("Qwen3-Coder Next",  53.0, 0.80,   262, "Qwen"),
        ("Kimi K2.6",         58.6, 4.00,   262, "Kimi"),
        ("GLM-5.2",           62.1, 2.20,   200, "GLM"),
        ("GLM-4.5-Air",       47.0, 1.10,   128, "GLM"),
        ("Claude Opus",       69.2, 75.0,   200, "Frontier"),
    ]
    cols = {"DeepSeek": BLUE, "Qwen": PURPLE, "Kimi": TEAL, "GLM": GREEN,
            "MiniMax": PINK, "Frontier": RED}

    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    for name, score, cost, ctx, fam in models:
        ax.scatter(score, cost, s=22 + ctx * 0.26, color=cols[fam], alpha=0.30,
                   edgecolors=cols[fam], linewidths=1.3, zorder=3)
        dy = 1.28 if name not in ("Kimi K2.6", "GLM-4.5-Air") else 0.76
        ax.annotate(name, (score, cost * dy), fontsize=6.9, color=INK,
                    ha="center", zorder=4)
    ax.set_yscale("log")
    ax.set_xlabel("SWE-bench Pro (%) — higher is better")
    ax.set_ylabel("output price,  $ per 1M tokens  (log scale)")
    ax.set_title("Figure 1 — Cost versus coding capability: the open-weight "
                 "families cluster at a fraction of frontier pricing",
                 fontsize=9.6, loc="left")
    ax.set_xlim(43, 74)
    ax.set_ylim(0.15, 160)

    # The band the report recommends for bulk implementation work.
    ax.axhspan(0.15, 1.5, color=GREEN, alpha=0.06, lw=0)
    ax.text(43.6, 0.19, "bulk-implementation band recommended in §1.8",
            fontsize=6.8, color=GREEN)

    handles = [Line2D([], [], marker="o", ls="", color=c, alpha=0.55, ms=6,
                      label=f) for f, c in cols.items()]
    handles.append(Line2D([], [], marker="o", ls="", color=SLATE, alpha=0.30,
                          ms=10, label="bubble ∝ context window"))
    ax.legend(handles=handles, loc="upper left", ncol=2, fontsize=6.9)
    despine(ax)
    note(ax, "Figures transcribed from the report's §1.2/§1.6 tables. Benchmark\n"
             "provenance is uneven and pricing is dated — verify before relying\n"
             "on any single point. Ordering, not precision, is the message.",
         loc="lower right", fontsize=6.3)
    save(fig, "fig01_model_landscape")


# ==========================================================================
# Figure 8 — latency spectrum
# ==========================================================================
def fig_latency():
    fig, ax = plt.subplots(figsize=(9.4, 2.9))
    tiers = [
        (3e-9,   "AMD Alveo UL3524\ntransceiver", RED),
        (13.9e-9, "Exegy STAC-T0\nactionable", RED),
        (3e-7,   "FPGA tick-to-trade\n(typical)", AMBER),
        (2e-6,   "kernel bypass\n(Solarflare + Onload)", AMBER),
        (5e-3,   "retail\nWebSocket", TEAL),
        (1e-1,   "retail REST\nround trip", TEAL),
        (6e2,    "THIS SYSTEM\n(MOC decision budget)", GREEN),
    ]
    ax.set_xscale("log")
    ax.set_xlim(1e-9, 1e4)
    ax.set_ylim(-1.0, 1.5)
    ax.plot([1e-9, 1e4], [0, 0], color=GRID, lw=3, solid_capstyle="round",
            zorder=1)

    for i, (t, lbl, col) in enumerate(tiers):
        up = i % 2 == 0
        y = 0.30 if up else -0.30
        ax.plot([t, t], [0, y * 0.72], color=col, lw=1.0, zorder=2)
        ax.scatter([t], [0], s=52, color=col, zorder=4, edgecolors="white",
                   linewidths=1.4)
        ax.text(t, y * 1.02, lbl, ha="center",
                va="bottom" if up else "top", fontsize=7.0, color=col,
                weight="600" if "THIS SYSTEM" in lbl else "normal")

    ax.annotate("", xy=(6e2, 0.62), xytext=(3e-9, 0.62),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.9))
    ax.text(1.4e-3, 0.72, "11.3 orders of magnitude", ha="center",
            fontsize=7.4, color=MUTED)

    ax.set_yticks([])
    ax.set_xlabel("end-to-end latency (seconds, log scale)")
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    ax.grid(False)
    ax.set_title("Figure 8 — The latency spectrum, with this system's operating "
                 "point marked",
                 fontsize=9.6, loc="left", pad=12)
    note(ax, "A daily-ETF system whose binding deadline is the 15:50 ET MOC cutoff sits\n"
             "~2×10¹¹× above the fastest tier. Microsecond optimisation here buys nothing.",
         loc="lower left", fontsize=6.6)
    save(fig, "fig08_latency_spectrum")


# ==========================================================================
# Figure 9 — system architecture with the no-LLM boundary
# ==========================================================================
def fig_architecture():
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # --- deterministic runtime region
    ax.add_patch(FancyBboxPatch((0.035, 0.055), 0.62, 0.70,
                                boxstyle="round,pad=0,rounding_size=0.02",
                                facecolor="#f4f9f6", edgecolor=GREEN,
                                lw=1.5, zorder=0))
    ax.text(0.048, 0.722, "DETERMINISTIC RUNTIME  —  no LLM in this region",
            fontsize=8.2, color=GREEN, weight="700")

    # --- agentic / development region
    ax.add_patch(FancyBboxPatch((0.685, 0.055), 0.28, 0.70,
                                boxstyle="round,pad=0,rounding_size=0.02",
                                facecolor="#fbf6f6", edgecolor=RED,
                                lw=1.5, ls=(0, (5, 3)), zorder=0))
    ax.text(0.697, 0.722, "AGENTIC  —  development time only",
            fontsize=8.2, color=RED, weight="700")

    w, h = 0.165, 0.098
    col1, col2, col3 = 0.062, 0.255, 0.448
    r1, r2, r3, r4 = 0.590, 0.445, 0.300, 0.125

    pit = _box(ax, col1, r1, w, h, "Point-in-time\ndata layer",
               "ALFRED · EDGAR · Norgate", fc="white", ec=BLUE)
    cost = _box(ax, col1, r2, w, h, "Cost model",
                "spread + ADV calibrated", fc="white", ec=BLUE)
    sig = _box(ax, col2, r1, w, h, "Signal / feature\nengine",
               "causal by construction", fc="white", ec=BLUE)
    eng = _box(ax, col2, r2, w, h, "Nautilus Trader",
               "backtest = live parity", fc="white", ec=BLUE)
    val = _box(ax, col3, r1, w, h, "Validation layer",
               "DSR · PBO · purged CV", fc="#eef4ff", ec=BLUE, lw=1.6)
    risk = _box(ax, col3, r2, w, h, "Pre-trade risk",
                "mirrors SEC 15c3-5", fc="#eef4ff", ec=BLUE, lw=1.6)

    gate = _box(ax, col2, r3, w, h, "Promotion gate",
                "state machine", fc="white", ec=AMBER, lw=1.4)
    broker = _box(ax, col3, r3, w, h, "Paper broker",
                  "Alpaca / IBKR", fc="white", ec=BLUE)
    kill = _box(ax, col1, r3, w, h, "Kill switch",
                "state persisted OUT of process", fc="#fff8ec", ec=RED, lw=1.5)

    obs = _box(ax, col1, r4, 0.35, 0.078, "Observability & reconciliation",
               "live-vs-backtest tracking error · CUSUM · position diff",
               fc="white", ec=SLATE)
    reg = _box(ax, col3, r4, w, 0.078, "Trial registry",
               "counts EVERY config", fc="#eef4ff", ec=BLUE, lw=1.6)

    for a, b in ((pit, sig), (sig, val), (cost, eng), (eng, risk),
                 (sig, eng), (val, risk)):
        _arrow(ax, (a[2] + a[4], a[1]), (b[2], b[1])) if abs(a[1] - b[1]) < 1e-9 \
            else _arrow(ax, (a[0], a[3]), (b[0], b[3] + b[5]), rad=0.0)
    _arrow(ax, (val[0], val[3]), (risk[0], risk[3] + risk[5]))
    _arrow(ax, (risk[0], risk[3]), (broker[0], broker[3] + broker[5]))
    _arrow(ax, (gate[2] + gate[4], gate[1]), (broker[2], broker[1]))
    _arrow(ax, (eng[0], eng[3]), (gate[0], gate[3] + gate[5]))
    _arrow(ax, (kill[2] + kill[4], kill[1] - 0.02),
           (gate[2], gate[1] - 0.02), color=RED, lw=1.4)
    _arrow(ax, (broker[0], broker[3]), (reg[0], reg[3] + reg[5]),
           color=SLATE, ls=(0, (3, 2)))
    _arrow(ax, (obs[2] + obs[4], obs[1]), (reg[2], reg[1]), color=SLATE)

    # agentic column
    aw = 0.235
    ax1 = _box(ax, 0.705, r1, aw, h, "Codex — implement",
               "bulk coding, cheap tier", fc="white", ec=RED)
    ax2 = _box(ax, 0.705, r2, aw, h, "Claude Code — challenge",
               "adversarial review, different vendor", fc="white", ec=RED)
    ax3 = _box(ax, 0.705, r3, aw, h, "CI + human",
               "no direct merge", fc="white", ec=RED)
    ax4 = _box(ax, 0.705, r4, aw, 0.078, "Self-hosted Qwen3-30B-A3B",
               "any runtime research · zero data egress", fc="#fbf1f1", ec=RED)
    _arrow(ax, (ax1[0], ax1[3]), (ax2[0], ax2[3] + ax2[5]), color=RED)
    _arrow(ax, (ax2[0], ax2[3]), (ax3[0], ax3[3] + ax3[5]), color=RED)

    # the boundary itself
    ax.plot([0.672, 0.672], [0.055, 0.755], color=INK, lw=2.2, zorder=5)
    ax.text(0.672, 0.775, "the boundary that must never be crossed at runtime",
            ha="center", fontsize=7.6, color=INK, weight="600")

    ax.text(0.5, 0.94,
            "Figure 9 — System architecture: the agentic tooling writes the "
            "system, but never runs inside it",
            ha="center", fontsize=9.8, color=INK, weight="600")
    ax.text(0.5, 0.885,
            "Every element inside the green region is deterministic and "
            "reproducible from a seed. Agents operate only at development time, "
            "behind a review gate.",
            ha="center", fontsize=7.4, color=MUTED)
    save(fig, "fig09_architecture")


# ==========================================================================
# Figure 10 — order lifecycle state machine
# ==========================================================================
def fig_state_machine():
    """Order lifecycle, drawn in a coordinate system whose aspect matches the
    page so the boxes are not stretched."""
    FW, FH = 9.4, 4.6
    fig, ax = plt.subplots(figsize=(FW, FH))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, FH / FW)
    ax.axis("off")
    Y = FH / FW

    bw, bh = 0.125, 0.060
    top, bot = 0.345, 0.160
    states = {
        "INTENT":    (0.085, top),
        "PENDING":   (0.265, top),
        "SENT":      (0.445, top),
        "ACKED":     (0.625, top),
        "PARTIAL":   (0.805, top),
        "UNKNOWN":   (0.265, bot),
        "CANCELLED": (0.445, bot),
        "REJECTED":  (0.625, bot),
        "FILLED":    (0.805, bot),
    }
    term = {"FILLED", "REJECTED", "CANCELLED"}
    cols = {"FILLED": GREEN, "REJECTED": RED, "UNKNOWN": RED,
            "CANCELLED": AMBER}

    for name, (x, y) in states.items():
        col = cols.get(name, BLUE)
        ax.add_patch(FancyBboxPatch((x - bw / 2, y - bh / 2), bw, bh,
                                    boxstyle="round,pad=0,rounding_size=0.018",
                                    facecolor="white", edgecolor=col,
                                    lw=1.9 if name in term else 1.3, zorder=3))
        if name in term:
            ax.add_patch(FancyBboxPatch((x - bw / 2 + 0.006, y - bh / 2 + 0.006),
                                        bw - 0.012, bh - 0.012,
                                        boxstyle="round,pad=0,rounding_size=0.015",
                                        facecolor="none", edgecolor=col,
                                        lw=0.7, zorder=4))
        ax.text(x, y, name, ha="center", va="center", fontsize=7.0,
                color=col, weight="700", zorder=5)

    def h_link(a_, b_, label, col=SLATE):
        (x0, y0), (x1, _) = states[a_], states[b_]
        _arrow(ax, (x0 + bw / 2 + 0.004, y0), (x1 - bw / 2 - 0.004, y0), color=col)
        ax.text((x0 + x1) / 2, y0 + 0.036, label, ha="center", va="bottom",
                fontsize=6.3, color=col, linespacing=1.3)

    def v_link(a_, b_, label, col=SLATE, side=1):
        (x0, y0), (x1, y1) = states[a_], states[b_]
        _arrow(ax, (x0, y0 - bh / 2 - 0.004), (x1, y1 + bh / 2 + 0.004), color=col)
        ax.text(x0 + side * 0.012, (y0 + y1) / 2,
                label, ha="left" if side > 0 else "right", va="center",
                fontsize=6.3, color=col)

    h_link("INTENT", "PENDING", "persist intent\n(outbox pattern)")
    h_link("PENDING", "SENT", "submit with\nidempotency key")
    h_link("SENT", "ACKED", "broker ack")
    h_link("ACKED", "PARTIAL", "partial fill")
    v_link("SENT", "CANCELLED", "cancel", AMBER)
    v_link("ACKED", "REJECTED", "reject", RED)
    v_link("PARTIAL", "FILLED", "complete", GREEN)

    # timeout / crash: SENT drops to UNKNOWN
    _arrow(ax, (0.445 - bw / 2 - 0.004, top - 0.014),
           (0.265 + bw / 2 + 0.004, bot + 0.020), color=RED, rad=0.24)
    ax.text(0.300, (top + bot) / 2 + 0.030, "timeout /\nprocess crash",
            ha="center", fontsize=6.3, color=RED, linespacing=1.3)

    # Recovery is a PROCEDURE, not a single edge: it may resolve to any state,
    # so it is drawn as a self-loop rather than an arrow to one destination.
    _arrow(ax, (0.265 - 0.028, bot - bh / 2 - 0.004),
           (0.265 + 0.028, bot - bh / 2 - 0.004), color=RED, rad=1.5,
           ls=(0, (3, 2)))
    ax.text(0.265, bot - 0.098,
            "query broker → reconcile → resume\n"
            "(may resolve to ANY state)",
            ha="center", va="center", fontsize=6.2, color=RED,
            linespacing=1.35)

    # duplicate-suppression self-loop on ACKED
    _arrow(ax, (0.625 - 0.028, top + bh / 2 + 0.004),
           (0.625 + 0.028, top + bh / 2 + 0.004), color=GREEN, rad=-1.5)
    ax.text(0.625, top + 0.093, "duplicate submit rejected\nby idempotency key",
            ha="center", fontsize=6.3, color=GREEN, linespacing=1.3)

    ax.text(0.5, Y - 0.004,
            "Figure 10 — Order lifecycle: every transition persisted, every "
            "submission idempotent",
            ha="center", va="top", fontsize=9.8, color=INK, weight="600")
    ax.text(0.5, 0.004,
            "Double-ruled states are terminal. UNKNOWN is the state most systems "
            "omit and the one that causes duplicate orders: never assume an "
            "unacknowledged order\nwas not filled. This machine is the natural "
            "target for the TLA+ model-checking and Hypothesis stateful testing "
            "recommended in §6.1.",
            ha="center", va="bottom", fontsize=6.8, color=MUTED,
            linespacing=1.45)
    save(fig, "fig10_state_machine")


# ==========================================================================
# Figure 11 — three lines of defence mapped onto SR 11-7
# ==========================================================================
def fig_three_lines():
    fig, ax = plt.subplots(figsize=(9.0, 3.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    lines = [
        ("FIRST LINE\nOwnership", "Codex (implementer)\n+ you as author",
         "builds the model, owns its\nassumptions and limitations", BLUE),
        ("SECOND LINE\nEffective challenge", "Claude Code\n(adversarial validator)",
         "independent, competent, and\nincentivised to find faults", AMBER),
        ("THIRD LINE\nAssurance", "CI + promotion gate\n+ periodic self-audit",
         "verifies the first two actually\nhappened, on every change", GREEN),
    ]
    w = 0.29
    for i, (title, who, what, col) in enumerate(lines):
        x = 0.025 + i * (w + 0.033)
        ax.add_patch(FancyBboxPatch((x, 0.16), w, 0.60,
                                    boxstyle="round,pad=0,rounding_size=0.03",
                                    facecolor="white", edgecolor=col, lw=1.6))
        ax.add_patch(FancyBboxPatch((x, 0.60), w, 0.16,
                                    boxstyle="round,pad=0,rounding_size=0.03",
                                    facecolor=col, edgecolor=col, lw=1.6))
        ax.text(x + w / 2, 0.68, title, ha="center", va="center",
                fontsize=7.8, color="white", weight="700")
        ax.text(x + w / 2, 0.475, who, ha="center", va="center",
                fontsize=8.0, color=INK, weight="600")
        ax.text(x + w / 2, 0.295, what, ha="center", va="center",
                fontsize=6.8, color=MUTED)
        if i < 2:
            _arrow(ax, (x + w + 0.004, 0.46), (x + w + 0.028, 0.46),
                   color=SLATE, lw=1.3)

    ax.text(0.5, 0.90,
            "Figure 11 — SR 11-7 model risk governance, mapped onto a "
            "one-person operation",
            ha="center", fontsize=9.8, color=INK, weight="600")
    ax.text(0.5, 0.055,
            "The report's existing rule that the writer is never the sole "
            "reviewer IS the SR 11-7 independence principle. Using a different "
            "vendor for review adds model diversity on top of role separation, "
            "so a shared blind spot in one model family cannot pass unchallenged.",
            ha="center", fontsize=6.9, color=MUTED)
    save(fig, "fig11_three_lines")


# ==========================================================================
# Figure 12 — model routing dataflow
# ==========================================================================
def fig_model_routing():
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    tasks = [
        ("Architecture / design", "frontier Western or GLM-5.x",
         "low volume, highest reasoning", PURPLE, False),
        ("Bulk implementation", "DeepSeek V4 Flash / Qwen3-Coder / GLM plan",
         "highest volume, cheapest tier", BLUE, False),
        ("Adversarial review", "a DIFFERENT vendor from the implementer",
         "enforces writer ≠ reviewer + model diversity", AMBER, False),
        ("Test generation", "Qwen3-Coder / Kimi K2.7 Code",
         "enumerates cases well, cheap", TEAL, False),
        ("Runtime research agents", "self-hosted Qwen3-30B-A3B",
         "schema-validated, timeout-bounded", GREEN, True),
        ("Embeddings", "self-hosted bge / e5 / Qwen-embed",
         "cheap, private, deterministic", GREEN, True),
    ]
    y0, dy, h = 0.735, 0.118, 0.088
    for i, (task, model, why, col, private) in enumerate(tasks):
        y = y0 - i * dy
        ax.text(0.018, y + h / 2, task, fontsize=7.8, color=INK, va="center",
                weight="600")
        ax.add_patch(FancyBboxPatch((0.30, y), 0.40, h,
                                    boxstyle="round,pad=0,rounding_size=0.02",
                                    facecolor="white", edgecolor=col, lw=1.3))
        ax.text(0.50, y + h / 2 + 0.014, model, fontsize=7.2, color=col,
                ha="center", va="center", weight="600")
        ax.text(0.50, y + h / 2 - 0.022, why, fontsize=6.2, color=MUTED,
                ha="center", va="center")
        _arrow(ax, (0.285, y + h / 2), (0.297, y + h / 2), color=col)
        if private:
            ax.text(0.715, y + h / 2, "◆ never leaves the machine",
                    fontsize=6.6, color=GREEN, va="center", weight="600")

    ax.add_patch(FancyBboxPatch((0.705, 0.055), 0.28, 0.30,
                                boxstyle="round,pad=0,rounding_size=0.02",
                                facecolor="#f4f9f6", edgecolor=GREEN, lw=1.4))
    ax.text(0.845, 0.305, "THE GOVERNING RULE", ha="center", fontsize=7.4,
            color=GREEN, weight="700")
    ax.text(0.845, 0.185,
            "Hosted cheap APIs are fine\nfor generic, public code.\n\n"
            "Anything carrying strategy\nlogic, signals, or private data\n"
            "runs on self-hosted weights.",
            ha="center", va="center", fontsize=6.8, color=INK)

    ax.text(0.5, 0.925,
            "Figure 12 — Model routing: cheap where volume lives, independent "
            "where review lives, local where alpha lives",
            ha="center", fontsize=9.6, color=INK, weight="600")
    save(fig, "fig12_model_routing")


# ==========================================================================
# Figure 13 — live vs backtest divergence with a CUSUM alarm
# ==========================================================================
def fig_cusum():
    g = rng(9500)
    n = 750
    bt_mu, bt_sd = 0.00045, 0.0075
    live = g.normal(bt_mu, bt_sd, n)
    decay_at = 420
    live[decay_at:] = g.normal(-0.00015, bt_sd * 1.25, n - decay_at)

    eq_live = np.cumprod(1 + live)
    eq_bt = np.cumprod(1 + np.full(n, bt_mu))

    # One-sided CUSUM on standardised deviation from the backtest mean.
    k, hlim = 0.5, 5.0
    z = (live - bt_mu) / bt_sd
    S = np.zeros(n)
    for t in range(1, n):
        S[t] = max(0.0, S[t - 1] - z[t] - k)
    alarm = int(np.argmax(S > hlim)) if np.any(S > hlim) else None

    fig, axes = plt.subplots(2, 1, figsize=(9.0, 4.2), sharex=True,
                             gridspec_kw={"height_ratios": [1.5, 1],
                                          "hspace": 0.14})
    ax = axes[0]
    ax.plot(eq_bt, color=SLATE, lw=1.3, ls=(0, (4, 3)),
            label="backtest expectation")
    ax.plot(eq_live, color=BLUE, lw=1.6, label="live / paper equity")
    ax.axvline(decay_at, color=MUTED, lw=0.9, ls=(0, (2, 3)))
    ax.text(decay_at + 6, eq_live.min() * 1.005, "true edge decays here",
            fontsize=6.9, color=MUTED)
    if alarm:
        ax.axvline(alarm, color=RED, lw=1.4)
        ax.text(alarm + 6, eq_live.max() * 0.995,
                f"CUSUM alarm\n(day {alarm}, {alarm - decay_at} days later)",
                fontsize=6.9, color=RED, va="top")
    ax.set_ylabel("cumulative equity")
    ax.legend(loc="upper left")
    despine(ax)
    ax.set_title("Figure 13 — Detecting strategy decay before it becomes a "
                 "drawdown", fontsize=9.6, loc="left")

    ax = axes[1]
    ax.plot(S, color=AMBER, lw=1.4)
    ax.axhline(hlim, color=RED, lw=1.1, ls=(0, (4, 3)))
    ax.text(4, hlim * 1.10, f"decision threshold h = {hlim:g}", fontsize=6.8,
            color=RED)
    ax.fill_between(np.arange(n), 0, S, color=AMBER, alpha=0.14, lw=0)
    if alarm:
        ax.axvline(alarm, color=RED, lw=1.4)
    ax.set_ylabel("CUSUM statistic")
    ax.set_xlabel("trading day")
    despine(ax)
    note(ax, "The equity curve alone is not yet visibly broken at the alarm "
             "point — that is the whole value of\nsequential monitoring. Pair "
             "this with the §5.5 decommissioning process so the alarm has a "
             "defined consequence.",
         loc="upper left", fontsize=6.5)
    save(fig, "fig13_cusum")


if __name__ == "__main__":
    setup()
    print("  systems figures:")
    fig_model_landscape()
    fig_latency()
    fig_architecture()
    fig_state_machine()
    fig_three_lines()
    fig_model_routing()
    fig_cusum()
