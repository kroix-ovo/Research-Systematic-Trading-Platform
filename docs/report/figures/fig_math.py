"""Mathematical-model figures, including the 3D surfaces.

Every figure here is generated from the same code paths the verification suite
uses, so the pictures and the numbers cannot drift apart.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verify"))
from style import (setup, save, despine, note, style3d, INK, MUTED, GRID,
                   PANEL, BLUE, RED, GREEN, AMBER, PURPLE, TEAL, PINK, SLATE,
                   C_TRUE, C_GOOD, C_BAD, C_CAVEAT)   # noqa: E402

from harness import rng                                # noqa: E402
from v05_validation import _fst_expected_max, _sr_se, _pbo   # noqa: E402
from v06_execution import AC                           # noqa: E402

# A perceptually smooth sequential map in the report's blue.
SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#eef2ff", "#c7d6fb", "#8fb0f4", "#4d7fe8", "#2563eb", "#15379c"])
DIV = LinearSegmentedColormap.from_list(
    "div", ["#1b6fd4", "#8fb6e8", "#f2f4f8", "#eba98d", "#d63b3b"])


# ==========================================================================
# 1. False Strategy Theorem -- 2D curve and 3D surface
# ==========================================================================
def fig_false_strategy():
    g = rng(9001)
    Ns = np.unique(np.round(np.logspace(0.5, 5.2, 60)).astype(int))
    approx = np.array([_fst_expected_max(int(n)) for n in Ns])

    mc_N = [10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
    mc = []
    for n in mc_N:
        reps = max(2000, min(30000, 3_000_000 // n))
        mc.append(float(np.mean(g.standard_normal((reps, n)).max(axis=1))))

    fig = plt.figure(figsize=(9.4, 3.5))
    ax = fig.add_subplot(1, 2, 1)
    ax.semilogx(Ns, approx, color=BLUE, lw=1.9,
                label="False Strategy Theorem (closed form)")
    ax.semilogx(mc_N, mc, "o", ms=4.5, color=INK, mfc="white", mew=1.3,
                label="direct Monte Carlo")
    ax.axhline(3.26, color=RED, lw=0.9, ls=(0, (4, 3)))
    ax.axvline(1000, color=RED, lw=0.9, ls=(0, (4, 3)))
    ax.plot([1000], [3.26], "o", ms=7, color=RED, zorder=5)
    ax.annotate("N = 1,000  →  E[max SR] = 3.26\n(verified: formula 3.255,\nMonte Carlo 3.242)",
                xy=(1000, 3.26), xytext=(23, 4.05),
                fontsize=7.4, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8,
                                connectionstyle="arc3,rad=0.18"))
    ax.set_xlabel("Number of independent backtest trials, $N$")
    ax.set_ylabel(r"Expected maximum Sharpe under the null")
    ax.set_title("Selecting the best of $N$ worthless strategies")
    ax.set_ylim(0.5, 5.0)
    ax.legend(loc="lower right")
    despine(ax)
    note(ax, "true Sharpe of every strategy = 0", loc="upper left")

    # --- 3D: hurdle as a function of N and the dispersion of trial Sharpes
    ax = fig.add_subplot(1, 2, 2, projection="3d")
    logN = np.linspace(1, 5, 70)
    vsr = np.linspace(0.25, 2.0, 70)
    LN, VS = np.meshgrid(logN, vsr)
    Z = np.vectorize(lambda ln, v: _fst_expected_max(int(10**ln), var_sr=v**2))(LN, VS)
    surf = ax.plot_surface(LN, VS, Z, cmap=SEQ, linewidth=0,
                           antialiased=True, alpha=0.97,
                           rcount=70, ccount=70)
    ax.contour(LN, VS, Z, zdir="z", offset=0, levels=10, colors=[GRID],
               linewidths=0.5)
    ax.set_xlabel("$\\log_{10} N$ trials")
    ax.set_ylabel(r"$\sqrt{V[\widehat{SR}]}$")
    ax.set_zlabel("hurdle Sharpe")
    ax.set_zlim(0, None)
    ax.view_init(elev=22, azim=-128)
    ax.set_title("Deflation hurdle surface", pad=0)
    style3d(ax)
    cb = fig.colorbar(surf, ax=ax, shrink=0.52, aspect=15, pad=0.10)
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=6.5, colors=MUTED)

    fig.suptitle("Figure 2 — The False Strategy Theorem: a raw Sharpe ratio is "
                 "meaningless without the trial count",
                 fontsize=10, color=INK, y=1.04, x=0.5)
    save(fig, "fig02_false_strategy")


# ==========================================================================
# 2. Almgren-Chriss: trajectories, 3D surface, efficient frontier
# ==========================================================================
def fig_almgren_chriss():
    fig = plt.figure(figsize=(9.6, 6.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], hspace=0.42, wspace=0.28)

    ac = AC(N=100)
    t = np.linspace(0, ac.T, ac.N + 1)

    # --- (a) trajectories at several risk aversions
    ax = fig.add_subplot(gs[0, 0])
    lams = [1e-9, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3]
    cols = SEQ(np.linspace(0.42, 1.0, len(lams)))
    for l, c in zip(lams, cols):
        x = ac.optimal_numeric(l)
        ax.plot(t, x / ac.X, color=c, lw=1.6)
    ax.plot(t, 1 - t / ac.T, color=INK, lw=1.1, ls=(0, (4, 3)),
            label="TWAP ($\\lambda\\to0$ limit)")
    ax.text(0.60, 0.60, "increasing\nrisk aversion $\\lambda$", fontsize=7.2,
            color=MUTED, transform=ax.transAxes, ha="left")
    ax.annotate("", xy=(0.30, 0.22), xytext=(0.62, 0.58),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0,
                                connectionstyle="arc3,rad=-0.25"))
    ax.set_xlabel("fraction of execution horizon")
    ax.set_ylabel("fraction of position remaining")
    ax.set_title("(a) Optimal liquidation trajectories")
    ax.legend(loc="lower left")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    despine(ax)
    note(ax, "$x_j = X\\,\\sinh(\\kappa(T-t_j))/\\sinh(\\kappa T)$\n"
             "matches the numerical optimum to $6.6\\times10^{-13}$",
         loc="upper right", fontsize=6.4)

    # --- (b) 3D surface: trajectory as a function of time and risk aversion
    ax = fig.add_subplot(gs[0, 1], projection="3d")
    lam_grid = np.logspace(-9, -3, 60)
    T_grid = np.linspace(0, 1, ac.N + 1)
    LG, TG = np.meshgrid(np.log10(lam_grid), T_grid)
    Z = np.zeros_like(LG)
    for j, l in enumerate(lam_grid):
        Z[:, j] = ac.optimal_numeric(l) / ac.X
    surf = ax.plot_surface(LG, TG, Z, cmap=SEQ, linewidth=0, antialiased=True,
                           rcount=60, ccount=60, alpha=0.98)
    ax.set_xlabel("$\\log_{10}\\lambda$")
    ax.set_ylabel("time / $T$")
    ax.set_zlabel("position held")
    ax.view_init(elev=24, azim=-124)
    ax.set_title("(b) Trajectory surface", pad=0)
    style3d(ax)

    # --- (c) efficient frontier of execution
    ax = fig.add_subplot(gs[1, 0])
    lams = np.logspace(-9, -2.2, 200)
    V, E = [], []
    for l in lams:
        x = ac.optimal_numeric(l)
        V.append(ac.cost_variance(x))
        E.append(ac.expected_cost(x))
    V, E = np.array(V), np.array(E)
    ax.plot(np.sqrt(V) / 1e3, E / 1e3, color=BLUE, lw=2.0)
    for l, lbl in ((1e-8, "patient\n(low $\\lambda$)"), (1e-6, ""),
                   (1e-4, ""), (1e-3, "urgent\n(high $\\lambda$)")):
        x = ac.optimal_numeric(l)
        ax.plot(math.sqrt(ac.cost_variance(x)) / 1e3,
                ac.expected_cost(x) / 1e3, "o", ms=5.5, color=INK,
                mfc="white", mew=1.3, zorder=5)
        if lbl:
            off = (10, 10) if "urgent" in lbl else (-6, 22)
            ha = "left" if "urgent" in lbl else "right"
            ax.annotate(lbl, xy=(math.sqrt(ac.cost_variance(x)) / 1e3,
                                 ac.expected_cost(x) / 1e3),
                        xytext=off, textcoords="offset points", ha=ha,
                        fontsize=7.2, color=MUTED)
    ax.set_xlabel("cost standard deviation  (thousands)")
    ax.set_ylabel("expected cost  (thousands)")
    ax.set_title("(c) Efficient frontier of execution")
    despine(ax)
    note(ax, "monotone and convex (verified E-07)", loc="upper right")

    # --- (d) the kappa approximation error
    ax = fig.add_subplot(gs[1, 1])
    Ns = np.array([3, 5, 8, 12, 20, 35, 60, 120, 250, 600, 1500])
    err, pen = [], []
    for N in Ns:
        a = AC(N=int(N))
        l = 2e-6
        ke, kr = a.kappa_exact(l), a.kappa_approx(l)
        err.append(abs(kr / ke - 1) * 100)
        pen.append(abs(a.objective(a.trajectory_sinh(l, kr), l)
                       / a.objective(a.trajectory_sinh(l, ke), l) - 1))
    ax.loglog(Ns, err, "o-", color=AMBER, ms=4, mfc="white", mew=1.2,
              label="error in $\\kappa$ (%)")
    ax2 = ax.twinx()
    ax2.loglog(Ns, pen, "s-", color=GREEN, ms=3.6, mfc="white", mew=1.2,
               label="objective penalty (relative)")
    ax2.set_ylabel("objective penalty", color=GREEN, fontsize=8)
    ax2.tick_params(axis="y", colors=GREEN, labelsize=7)
    ax2.grid(False)
    ax2.spines["top"].set_visible(False)
    ax.set_xlabel("number of execution slices $N$")
    ax.set_ylabel("error in $\\kappa$  (%)", color=AMBER)
    ax.tick_params(axis="y", colors=AMBER)
    ax.set_title("(d) Cost of the $\\kappa\\approx\\sqrt{\\lambda\\sigma^2/\\eta}$ "
                 "approximation")
    despine(ax, left=True)
    note(ax, "the schedule is wrong by up to 0.5%,\n"
             "but costs essentially nothing:\nthe optimum is very flat",
         loc="lower left")

    fig.suptitle("Figure 3 — Almgren-Chriss optimal execution: verified closed "
                 "form, trajectory surface, and the cost of approximation",
                 fontsize=10, color=INK, y=0.985)
    save(fig, "fig03_almgren_chriss")


# ==========================================================================
# 3. PSR standard-error surface (3D) + kurtosis convention
# ==========================================================================
def fig_psr_surface():
    fig = plt.figure(figsize=(10.2, 3.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.3, 1.0, 1.0], wspace=0.60)

    # --- 3D: SE multiplier as a function of skew and kurtosis.
    # Evaluated at a per-period Sharpe of 0.4 (e.g. quarterly observations of
    # an annualised 0.8), where both correction terms are clearly visible.
    ax = fig.add_subplot(gs[0, 0], projection="3d")
    sk = np.linspace(-2.0, 2.0, 80)
    ku = np.linspace(1.5, 12.0, 80)
    SK, KU = np.meshgrid(sk, ku)
    sr = 0.4
    inner = 1 - SK * sr + (KU - 1) / 4 * sr**2
    Zv = np.sqrt(np.clip(inner, 0.0, None))
    surf = ax.plot_surface(SK, KU, Zv, cmap=DIV, linewidth=0, rcount=80,
                           ccount=80, antialiased=True, alpha=0.98)
    ax.contour(SK, KU, Zv, zdir="z", offset=0.0, levels=9, colors=[GRID],
               linewidths=0.5)
    ax.set_xlabel("skewness $\\gamma_3$", labelpad=-2)
    ax.set_ylabel("kurtosis $\\gamma_4$", labelpad=-2)
    ax.set_zlabel("SE multiplier", labelpad=-6)
    ax.set_box_aspect((1, 1, 0.72), zoom=0.88)
    ax.set_zlim(0, None)
    ax.view_init(elev=20, azim=-58)
    ax.set_title("(a) PSR denominator surface\n"
                 "(per-period $SR=0.4$)", pad=-2, fontsize=8.8)
    style3d(ax)

    # --- kurtosis convention error vs frequency
    ax = fig.add_subplot(gs[0, 1])
    freqs = [("daily", 252), ("weekly", 52), ("monthly", 12),
             ("quarterly", 4), ("annual", 1)]
    ku_t = 6.0
    errs = []
    for nm, per in freqs:
        s = 0.8 / math.sqrt(per)
        correct = _sr_se(s, 1000, 0.0, ku_t)
        wrong = _sr_se(s, 1000, 0.0, ku_t - 3.0)
        errs.append(abs(wrong / correct - 1) * 100)
    bars = ax.bar([f[0] for f in freqs], errs, color=[GRID] * 2 + [AMBER, RED, RED],
                  edgecolor="none", width=0.62)
    for b, e in zip(bars, errs):
        ax.text(b.get_x() + b.get_width() / 2, e + 0.4, f"{e:.1f}%",
                ha="center", fontsize=7, color=INK)
    ax.set_ylabel("understatement of the\nSharpe standard error (%)")
    ax.set_title("(b) Using EXCESS kurtosis by mistake")
    ax.set_ylim(0, max(errs) * 1.28)
    ax.tick_params(axis="x", rotation=28)
    despine(ax)
    note(ax, "understates SE ⇒ inflates PSR/DSR", loc="upper left",
         fontsize=6.6)

    # --- MinTRL: years needed for 95% confidence
    ax = fig.add_subplot(gs[0, 2])
    srs = np.linspace(0.2, 2.0, 200)
    z = stats.norm.ppf(0.95)
    yrs = []
    for s_ann in srs:
        s = s_ann / math.sqrt(252)
        yrs.append((1 + (1 + (3 - 1) / 4 * s**2) * (z / s) ** 2) / 252)
    ax.plot(srs, yrs, color=BLUE, lw=2.0)
    ax.fill_between([0.3, 0.8], 0, 60, color=AMBER, alpha=0.11, lw=0)
    ax.text(0.55, 46, "the report's realistic\nsolo range (§4.8)",
            ha="center", fontsize=7.2, color=AMBER)
    for s_ann in (0.3, 0.5, 1.0):
        s = s_ann / math.sqrt(252)
        y = (1 + (1 + 0.5 * s**2) * (z / s) ** 2) / 252
        ax.plot([s_ann], [y], "o", ms=5, color=INK, mfc="white", mew=1.3)
        ax.annotate(f"{y:.0f} yr", xy=(s_ann, y), xytext=(7, 6),
                    textcoords="offset points", fontsize=7.2, color=INK)
    ax.set_xlabel("true annualised Sharpe ratio")
    ax.set_ylabel("years of data for 95% confidence")
    ax.set_title("(c) Minimum track record length")
    ax.set_ylim(0, 60)
    ax.set_xlim(0.2, 2.0)
    despine(ax)

    fig.suptitle("Figure 4 — Probabilistic Sharpe Ratio: the standard error "
                 "that everything downstream depends on",
                 fontsize=10, color=INK, y=1.02)
    save(fig, "fig04_psr")


# ==========================================================================
# 4. Purged k-fold CV with embargo -- timeline diagram
# ==========================================================================
def fig_purged_cv():
    fig, axes = plt.subplots(2, 1, figsize=(9.4, 4.0),
                            gridspec_kw={"hspace": 0.55})
    T = 100
    h = 8          # label horizon
    fold = (40, 60)
    emb = 4

    for ax, purged in zip(axes, (False, True)):
        ax.set_xlim(0, T)
        ax.set_ylim(0.05, 3.35)
        ax.axis("off")

        # observation bar
        ax.add_patch(plt.Rectangle((0, 2.3), T, 0.52, facecolor=PANEL,
                                   edgecolor=GRID, lw=0.8))
        # test fold
        ax.add_patch(plt.Rectangle((fold[0], 2.3), fold[1] - fold[0], 0.52,
                                   facecolor=BLUE, edgecolor="none"))
        ax.text((fold[0] + fold[1]) / 2, 2.56, "TEST", ha="center",
                va="center", color="white", fontsize=8, weight="bold")

        if purged:
            for lo, hi, col in ((fold[0] - h, fold[0], RED),
                                (fold[1], fold[1] + h, RED)):
                ax.add_patch(plt.Rectangle((lo, 2.3), hi - lo, 0.52,
                                           facecolor=RED, alpha=0.30,
                                           edgecolor="none", hatch="///"))
            ax.add_patch(plt.Rectangle((fold[1] + h, 2.3), emb, 0.52,
                                       facecolor=AMBER, alpha=0.42,
                                       edgecolor="none"))
            ax.text(fold[0] - h / 2, 3.02, "purged", ha="center",
                    fontsize=7.2, color=RED)
            ax.text(fold[1] + h / 2, 3.02, "purged", ha="center",
                    fontsize=7.2, color=RED)
            ax.text(fold[1] + h + emb / 2, 3.02, "embargo", ha="center",
                    fontsize=7.2, color=AMBER)

        ax.text(6, 2.56, "TRAIN", ha="center", va="center", color=MUTED,
                fontsize=8, weight="bold")

        # label windows for a few representative samples
        picks = [(30, GREEN), (36, RED if not purged else RED), (52, BLUE),
                 (64, RED if not purged else RED), (76, GREEN)]
        for i, (t0, col) in enumerate(picks):
            y = 1.62 - i * 0.30
            leaks = (t0 + h > fold[0]) and (t0 < fold[1] + h)
            in_test = fold[0] <= t0 < fold[1]
            if in_test:
                c = BLUE
            elif leaks:
                c = RED if not purged else SLATE
            else:
                c = GREEN
            ax.plot([t0, t0 + h], [y, y], color=c, lw=3.2,
                    solid_capstyle="butt",
                    alpha=0.35 if (purged and leaks and not in_test) else 1.0)
            ax.plot([t0], [y], "|", color=c, ms=7, mew=1.4)
            lbl = ("test sample" if in_test else
                   ("LEAKS into test" if leaks and not purged else
                    ("removed by purge" if leaks else "safe training sample")))
            txt_c = c if not (purged and leaks and not in_test) else SLATE
            if t0 + h > 70:      # keep right-hand labels inside the axes
                ax.text(t0 - 1.5, y,
                        f"$t={t0}$ — {lbl}", va="center", ha="right",
                        fontsize=6.9, color=txt_c)
            else:
                ax.text(t0 + h + 1.5, y,
                        f"label window of sample at $t={t0}$ — {lbl}",
                        va="center", fontsize=6.9, color=txt_c)

        ax.set_title("Standard $k$-fold: training labels overlap the test window"
                     if not purged else
                     "Purged $k$-fold with embargo: overlapping samples removed",
                     fontsize=9, color=RED if not purged else GREEN,
                     loc="left", pad=6)

    axes[1].text(0, -0.30,
                 "Verified (S-15): on data with ZERO true predictability, "
                 "shuffled $k$-fold reports AUC 0.526 ± 0.004; contiguous "
                 "blocks 0.499 ± 0.006; purged + embargoed 0.501 ± 0.006.",
                 transform=axes[1].transAxes, fontsize=7.2, color=MUTED)

    fig.suptitle("Figure 5 — Why standard cross-validation leaks on financial "
                 "labels, and what purging removes",
                 fontsize=10, color=INK, y=1.02)
    save(fig, "fig05_purged_cv")


# ==========================================================================
# 5. PBO distribution and its sampling variability
# ==========================================================================
def fig_pbo():
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.1))

    T, N, S = 1000, 40, 12
    # (a) null vs edge distribution of the OOS rank logit
    ax = axes[0]
    null_vals, edge_vals = [], []
    for k in range(30):
        g = rng(9100 + k)
        null_vals.append(_pbo(g.standard_normal((T, N)) * 0.01, S))
        e = g.standard_normal((T, N)) * 0.01
        e[:, 7] += 0.01 * 0.9
        edge_vals.append(_pbo(e, S))
    bins = np.linspace(0, 1, 21)
    ax.hist(null_vals, bins=bins, color=RED, alpha=0.62, edgecolor="none",
            label="no edge (pure noise)")
    ax.hist(edge_vals, bins=bins, color=GREEN, alpha=0.72, edgecolor="none",
            label="one genuine edge")
    ax.axvline(0.5, color=INK, lw=1.0, ls=(0, (4, 3)))
    ax.set_xlabel("PBO")
    ax.set_ylabel("count (30 datasets)")
    ax.set_title("(a) PBO separates skill from selection")
    ax.legend(loc="upper center")
    despine(ax)

    # (b) sampling variability
    ax = axes[1]
    configs = [(1000, 40), (2500, 40), (1000, 200), (5000, 200)]
    means, sds, labels = [], [], []
    for (t_, n_) in configs:
        vals = [_pbo(rng(9200 + t_ + n_ + k).standard_normal((t_, n_)) * 0.01, S)
                for k in range(24)]
        means.append(np.mean(vals))
        sds.append(np.std(vals, ddof=1))
        labels.append(f"T={t_}\nN={n_}")
    x = np.arange(len(configs))
    ax.errorbar(x, means, yerr=sds, fmt="o", ms=6, color=INK, mfc="white",
                mew=1.4, capsize=5, ecolor=AMBER, elinewidth=1.6)
    ax.axhline(0.5, color=GREEN, lw=1.0, ls=(0, (4, 3)))
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("PBO under the null")
    ax.set_ylim(0, 1)
    ax.set_title("(b) …but a single PBO is very noisy")
    despine(ax)
    note(ax, "bars = ±1 sd across datasets\n"
             "sd ≈ 0.19 at realistic sizes", loc="upper left")

    # (c) hurdle table as a bar
    ax = axes[2]
    Ns = [10, 100, 1000, 10000, 100000]
    hur = [_fst_expected_max(n) for n in Ns]
    ax.barh([f"{n:,}" for n in Ns], hur, color=SEQ(np.linspace(0.35, 0.9, 5)),
            edgecolor="none", height=0.6)
    for i, h in enumerate(hur):
        ax.text(h + 0.06, i, f"{h:.2f}", va="center", fontsize=7.4, color=INK)
    ax.set_xlabel("Sharpe ratio expected from noise alone")
    ax.set_ylabel("number of trials")
    ax.set_title("(c) The hurdle a real strategy must clear")
    ax.set_xlim(0, 5.2)
    despine(ax)

    fig.suptitle("Figure 6 — Probability of Backtest Overfitting: a correct "
                 "diagnostic that is itself a noisy statistic",
                 fontsize=10, color=INK, y=1.04)
    fig.subplots_adjust(wspace=0.38)
    save(fig, "fig06_pbo")


# ==========================================================================
# 6. Kelly: growth, drawdown, and estimation error
# ==========================================================================
def fig_kelly():
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.0))

    # (a) growth curve
    ax = axes[0]
    c = np.linspace(0, 2.0, 300)
    ax.plot(c, c * (2 - c), color=BLUE, lw=2.0)
    ax.fill_between(c, 0, c * (2 - c), where=(c <= 1), color=BLUE, alpha=0.08)
    for cf, lbl in ((0.25, "¼ Kelly"), (0.5, "½ Kelly"), (1.0, "full Kelly")):
        ax.plot([cf], [cf * (2 - cf)], "o", ms=5.5, color=INK, mfc="white",
                mew=1.3, zorder=5)
        ax.annotate(f"{lbl}\n{cf * (2 - cf):.0%} of max growth",
                    xy=(cf, cf * (2 - cf)), xytext=(0, -30),
                    textcoords="offset points", ha="center", fontsize=6.9,
                    color=INK)
    ax.axvline(1.0, color=MUTED, lw=0.8, ls=(0, (3, 3)))
    ax.set_xlabel("fraction $c$ of the Kelly bet")
    ax.set_ylabel("growth rate / maximum")
    ax.set_title("(a) Growth is flat near the optimum")
    ax.set_ylim(0, 1.15)
    ax.set_xlim(0, 2)
    despine(ax)

    # (b) drawdown
    ax = axes[1]
    g = rng(9300)
    mu_v, sig_v = 0.08, 0.20
    fk = mu_v / sig_v**2
    steps = 252 * 10
    dt = 1 / 252
    z = g.standard_normal((4000, steps))
    data = []
    for cf in (1.0, 0.5, 0.25):
        fv = cf * fk
        inc = (fv * mu_v - 0.5 * fv**2 * sig_v**2) * dt + \
            fv * sig_v * math.sqrt(dt) * z
        eq = np.exp(np.cumsum(inc, axis=1))
        peak = np.maximum.accumulate(eq, axis=1)
        data.append(np.min(eq / peak - 1, axis=1))
    parts = ax.violinplot(data, positions=[0, 1, 2], widths=0.72,
                          showextrema=False, showmedians=True)
    for pc, col in zip(parts["bodies"], (RED, AMBER, GREEN)):
        pc.set_facecolor(col)
        pc.set_alpha(0.55)
        pc.set_edgecolor("none")
    parts["cmedians"].set_color(INK)
    parts["cmedians"].set_linewidth(1.3)
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["full", "½", "¼"])
    ax.set_xlabel("Kelly fraction")
    ax.set_ylabel("worst drawdown over 10 years")
    ax.set_title("(b) …but drawdown is not")
    ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0%}")
    despine(ax)

    # (c) estimation error
    ax = axes[2]
    g2 = rng(9301)
    n = 10 * 252
    est = np.empty(4000)
    for i in range(len(est)):
        r = g2.normal(mu_v / 252, sig_v / math.sqrt(252), n)
        est[i] = (np.mean(r) * 252) / (np.std(r, ddof=1) * math.sqrt(252)) ** 2
    ax.hist(est, bins=70, color=SLATE, alpha=0.75, edgecolor="none")
    ax.axvline(fk, color=GREEN, lw=1.8, label=f"true $f^*$ = {fk:.1f}")
    ax.axvline(np.percentile(est, 5), color=RED, lw=1.0, ls=(0, (4, 3)))
    ax.axvline(np.percentile(est, 95), color=RED, lw=1.0, ls=(0, (4, 3)),
               label="5th–95th percentile")
    ax.set_xlabel("Kelly fraction estimated from 10 years of data")
    ax.set_xlim(-3, 8)
    ax.set_ylabel("frequency")
    ax.set_title("(c) 10 years cannot identify $f^*$")
    ax.legend(loc="upper right", fontsize=6.9)
    despine(ax)
    note(ax, f"5–95%: [{np.percentile(est, 5):.2f}, "
             f"{np.percentile(est, 95):.2f}]\naround a true $f^*$ of {fk:.1f}",
         loc="lower left", fontsize=6.6)

    fig.suptitle("Figure 7 — Why fractional Kelly is not conservatism but "
                 "correct sizing under parameter uncertainty",
                 fontsize=10, color=INK, y=1.04)
    fig.subplots_adjust(wspace=0.34)
    save(fig, "fig07_kelly")


if __name__ == "__main__":
    setup()
    print("  math figures:")
    fig_false_strategy()
    fig_almgren_chriss()
    fig_psr_surface()
    fig_purged_cv()
    fig_pbo()
    fig_kelly()
