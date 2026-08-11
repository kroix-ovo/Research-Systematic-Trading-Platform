"""Figures generated directly from the verification suite.

These are the pictures of the findings: each one visualises a specific check,
using the same code the check itself ran.
"""

from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.optimize import minimize
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "verify"))
from style import (setup, save, despine, note, style3d, INK, MUTED, GRID,
                   PANEL, BLUE, RED, GREEN, AMBER, PURPLE, TEAL, PINK,
                   SLATE)                                       # noqa: E402
from harness import rng, gbm_ohlc                               # noqa: E402
from v01_returns_vol import _estimators, _STEP_GRID             # noqa: E402
from v03_portfolio import _psd, _hrp_weights                    # noqa: E402
from v07_meanrev import _simulate_ou                            # noqa: E402
from v08_ml_regime import (_ffd_weights, _simulate_regimes,
                           _forward_filter)                     # noqa: E402

SEQ = LinearSegmentedColormap.from_list(
    "seq", ["#eef2ff", "#c7d6fb", "#8fb0f4", "#4d7fe8", "#2563eb", "#15379c"])
HEAT = LinearSegmentedColormap.from_list(
    "heat", ["#0d3b8f", "#3f7fd6", "#9dc2ec", "#f6d9c4", "#e08b5a", "#c0392b"])


# ==========================================================================
# Figure 14 — the no-trade region (finding P-13)
# ==========================================================================
def fig_no_trade_region():
    g = rng(9600)
    n = 5
    S = _psd(g, n) / n + np.eye(n) * 0.02
    mu = g.normal(0.05, 0.02, n)
    gam = 3.0
    Lam = np.eye(n) * 0.5
    w_target = np.linalg.solve(gam * S, mu)
    direction = np.zeros(n)
    direction[0] = 1.0

    drifts = np.linspace(0, 0.40, 61)
    quad, l1 = [], []
    c = 0.02
    for d in drifts:
        start = w_target + d * direction
        wq = np.linalg.solve(gam * S + 2 * Lam, mu + 2 * Lam @ start)
        quad.append(float(np.sum(np.abs(wq - start))))
        r = minimize(lambda x: -(x @ mu - gam / 2 * x @ S @ x
                                 - c * np.sum(np.abs(x - start))),
                     start.copy(), method="Powell",
                     options={"xtol": 1e-12, "ftol": 1e-14,
                              "maxiter": 200000, "maxfev": 200000})
        l1.append(float(np.sum(np.abs(r.x - start))))
    quad, l1 = np.array(quad), np.array(l1)
    band = drifts[np.argmax(l1 > 1e-3)]

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))

    ax = axes[0]
    ax.plot(drifts, quad, color=RED, lw=2.0,
            label="quadratic cost  $(w-w_0)^\\top\\Lambda(w-w_0)$")
    ax.plot(drifts, l1, color=GREEN, lw=2.0,
            label="proportional (L1) cost  $c\\,\\|w-w_0\\|_1$")
    ax.axvspan(0, band, color=GREEN, alpha=0.10, lw=0)
    ax.annotate(f"genuine no-trade region\n(width {band:.2f})",
                xy=(band / 2, max(quad) * 0.55), ha="center", fontsize=7.0,
                color=GREEN)
    ax.annotate("quadratic costs trade\nat every nonzero drift",
                xy=(0.02, quad[3]), xytext=(0.085, max(quad) * 0.28),
                fontsize=7.0, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9,
                                connectionstyle="arc3,rad=0.25"))
    ax.set_xlabel("drift of the current book away from the target weight")
    ax.set_ylabel("amount traded (gross)")
    ax.set_title("(a) Only a KINKED cost function creates a band")
    ax.legend(loc="upper left")
    ax.set_xlim(0, 0.40)
    despine(ax)

    ax = axes[1]
    x = np.linspace(-0.25, 0.25, 400)
    ax.plot(x, 0.5 * 8 * x**2, color=RED, lw=2.0, label="quadratic: smooth at 0")
    ax.plot(x, 0.10 * np.abs(x), color=GREEN, lw=2.0,
            label="proportional: kink at 0")
    ax.axvline(0, color=GRID, lw=0.8)
    ax.annotate("zero derivative here ⇒\nalways worth trading a little",
                xy=(0.0, 0.0), xytext=(0.045, 0.075), fontsize=7.0, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9,
                                connectionstyle="arc3,rad=-0.3"))
    ax.annotate("subgradient interval $[-c,c]$ ⇒\nsmall deviations absorbed",
                xy=(0.0, 0.0), xytext=(-0.235, 0.105), fontsize=7.0,
                color=GREEN,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9,
                                connectionstyle="arc3,rad=0.3"))
    ax.set_xlabel("trade size $w - w_0$")
    ax.set_ylabel("transaction cost")
    ax.set_title("(b) The mechanism: behaviour at zero")
    ax.legend(loc="upper center")
    ax.set_ylim(0, 0.16)
    despine(ax)

    fig.suptitle("Figure 14 — Finding P-13: quadratic transaction costs do NOT "
                 "produce a no-trade region",
                 fontsize=9.8, color=RED, y=1.03)
    fig.subplots_adjust(wspace=0.28)
    save(fig, "fig14_no_trade_region")


# ==========================================================================
# Figure 15 — OU half-life error and Engle-Granger over-rejection
# ==========================================================================
def fig_meanrev_findings():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))

    # --- (a) half-life: report's formula vs exact
    lam = np.linspace(-0.85, -0.01, 400)
    hl_report = -math.log(2) / lam
    hl_exact = -math.log(2) / np.log(1 + lam)
    ax = axes[0]
    ax.plot(-lam, hl_exact, color=GREEN, lw=2.0,
            label=r"exact:  $-\ln 2/\ln(1+\lambda)$")
    ax.plot(-lam, hl_report, color=RED, lw=2.0, ls=(0, (5, 2)),
            label=r"report §6.5:  $-\ln 2/\lambda$")
    ax.fill_between(-lam, hl_exact, hl_report, color=RED, alpha=0.10, lw=0)
    for th, err in ((0.10, "+6%"), (0.25, "+14%"), (0.50, "+27%"),
                    (1.00, "+58%")):
        l0 = math.exp(-th) - 1
        if -l0 > 0.86:
            continue
        ax.plot([-l0], [-math.log(2) / l0], "o", ms=4.5, color=RED,
                mfc="white", mew=1.3, zorder=5)
        ax.annotate(err, xy=(-l0, -math.log(2) / l0), xytext=(4, 5),
                    textcoords="offset points", fontsize=6.9, color=RED)
    ax.set_xlabel(r"$|\lambda|$ from the regression  $\Delta X_t=\lambda X_{t-1}+c+\varepsilon$")
    ax.set_ylabel("estimated half-life (periods)")
    ax.set_title("(a) Finding M-04: the half-life is overstated")
    ax.set_ylim(0, 20)
    ax.legend(loc="upper right")
    despine(ax)
    note(ax, "error is one-directional: always TOO LONG,\n"
             "and worst on the fast-reverting pairs\nthat are actually worth trading",
         loc="lower left", fontsize=6.6)

    # --- (b) Engle-Granger false positives
    ax = axes[1]
    labels = ["standard ADF\ncritical values", "Engle-Granger\ncritical values"]
    vals = [57.0, 4.7]
    bars = ax.bar(labels, vals, color=[RED, GREEN], width=0.5, edgecolor="none")
    ax.axhline(5.0, color=INK, lw=1.2, ls=(0, (4, 3)))
    ax.text(1.42, 6.4, "nominal 5%", fontsize=7.0, color=INK, ha="right")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.6, f"{v:.1f}%",
                ha="center", fontsize=8.4, color=INK, weight="600")
    ax.set_ylabel("pairs falsely declared cointegrated (%)")
    ax.set_title("(b) Finding M-05: the wrong critical values")
    ax.set_ylim(0, 66)
    despine(ax)
    note(ax, "3,000 pairs of INDEPENDENT random walks,\n"
             "where the true cointegration rate is 0%.\n"
             "An 11× over-rejection feeds a pipeline of\n"
             "pairs that look tradeable and are not.",
         loc="upper right", fontsize=6.6)

    fig.suptitle("Figure 15 — Two correctable defects in the pairs-trading "
                 "section", fontsize=9.8, color=RED, y=1.03)
    fig.subplots_adjust(wspace=0.30)
    save(fig, "fig15_meanrev")


# ==========================================================================
# Figure 16 — volatility estimators: bias, extrapolation, drift
# ==========================================================================
def fig_vol_estimators():
    sigma = 0.02
    truth = sigma**2
    grid = _STEP_GRID
    zero, drift = {}, {}
    for tag, mu, store in (("zero", 0.0, zero), ("drift", 0.02, drift)):
        for k in ("parkinson", "garman_klass", "rogers_satchell"):
            store[k] = []
        for m in grid:
            d = gbm_ohlc(rng(104_000 + m), 60_000, m, sigma_daily=sigma,
                         mu_daily=mu)
            est = _estimators(d)
            for k in store:
                store[k].append(float(np.mean(est[k])))

    fig, axes = plt.subplots(1, 3, figsize=(9.8, 3.2))
    xs = np.array([m**-0.5 for m in grid])

    ax = axes[0]
    cols = {"parkinson": BLUE, "garman_klass": PURPLE,
            "rogers_satchell": TEAL}
    names = {"parkinson": "Parkinson", "garman_klass": "Garman-Klass",
             "rogers_satchell": "Rogers-Satchell"}
    for k, col in cols.items():
        y = np.array(zero[k]) / truth
        b, a = np.polyfit(xs, y, 1)
        ax.plot(xs, y, "o", ms=4, color=col, mfc="white", mew=1.2)
        xf = np.linspace(0, xs.max() * 1.05, 50)
        ax.plot(xf, a + b * xf, color=col, lw=1.4, label=names[k])
        ax.plot([0], [a], "*", ms=11, color=col, zorder=6)
    ax.axhline(1.0, color=INK, lw=1.1, ls=(0, (4, 3)))
    ax.text(0.004, 1.006, "true $\\sigma^2$", fontsize=7.0, color=INK)
    ax.set_xlabel("$m^{-1/2}$  (m = intraday observations per bar)")
    ax.set_ylabel("estimate / true variance")
    ax.set_title("(a) Unbiased only in the continuum limit")
    ax.set_xlim(-0.004, xs.max() * 1.06)
    ax.legend(loc="lower left")
    despine(ax)
    note(ax, "★ = extrapolated intercept\n(recovers $\\sigma^2$ to 0.1%)",
         loc="upper right", fontsize=6.6)

    ax = axes[1]
    bias = (np.array(zero["parkinson"]) / truth - 1) * 100
    ax.semilogx(grid, bias, "o-", color=BLUE, ms=4.5, mfc="white", mew=1.3)
    ax.axhline(0, color=INK, lw=1.0, ls=(0, (4, 3)))
    ax.fill_between([grid[0], 300], -30, 0, color=RED, alpha=0.07, lw=0)
    ax.text(140, -22, "thinly traded ETFs\nlive here", fontsize=7.0,
            color=RED, ha="center")
    ax.set_xlabel("prints per bar")
    ax.set_ylabel("Parkinson bias (%)")
    ax.set_title("(b) Finding V-08b: real bars are biased LOW")
    despine(ax)
    note(ax, "A variance that is too low is divided into\n"
             "in §2.3 vol targeting ⇒ systematic over-leverage.",
         loc="lower right", fontsize=6.5)

    ax = axes[2]
    keys = list(cols)
    delta = []
    for k in keys:
        a0 = np.polyfit(xs, np.array(zero[k]), 1)[1]
        a1 = np.polyfit(xs, np.array(drift[k]), 1)[1]
        delta.append((a1 - a0) / truth * 100)
    bars = ax.bar([names[k] for k in keys], delta,
                  color=[cols[k] for k in keys], width=0.55, edgecolor="none")
    for b, v in zip(bars, delta):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.0, f"{v:+.1f}%",
                ha="center", fontsize=7.6, color=INK)
    ax.axhline(0, color=INK, lw=0.9)
    ax.set_ylabel("drift-induced bias (%)")
    ax.set_title("(c) Only Rogers-Satchell is drift-free")
    ax.tick_params(axis="x", rotation=16)
    despine(ax)

    fig.suptitle("Figure 16 — Range-based volatility estimators: correct in "
                 "theory, biased on real bars",
                 fontsize=9.8, color=INK, y=1.04)
    fig.subplots_adjust(wspace=0.36)
    save(fig, "fig16_vol_estimators")


# ==========================================================================
# Figure 17 — the HMM look-ahead trap
# ==========================================================================
def fig_hmm_lookahead():
    from hmmlearn import hmm
    import logging
    logging.getLogger("hmmlearn").setLevel(logging.ERROR)

    n = 4000
    p_stay = np.array([0.96, 0.94])
    mu_s = np.array([0.0006, -0.0008])
    sd_s = np.array([0.009, 0.017])
    g = rng(8020)
    state, r = _simulate_regimes(g, n, p_stay, mu_s, sd_s)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = hmm.GaussianHMM(n_components=2, covariance_type="diag",
                                n_iter=150, random_state=0, tol=1e-4)
        model.fit(r.reshape(-1, 1))
        smoothed = model.predict_proba(r.reshape(-1, 1))
    filtered = _forward_filter(model, r)
    bull = int(np.argmax(model.means_.ravel()))

    def eq(prob):
        pos = (prob[:, bull] > 0.5).astype(float)
        return np.cumprod(1 + pos[:-1] * r[1:])

    fig, axes = plt.subplots(2, 1, figsize=(9.2, 4.4), sharex=True,
                             gridspec_kw={"height_ratios": [1.6, 1],
                                          "hspace": 0.16})
    ax = axes[0]
    ax.plot(eq(smoothed), color=RED, lw=1.7,
            label="using SMOOTHED $P(z_t\\mid r_{1:T})$  — look-ahead")
    ax.plot(eq(filtered), color=GREEN, lw=1.7,
            label="using FILTERED $P(z_t\\mid r_{1:t})$  — tradeable")
    ax.plot(np.cumprod(1 + r[1:]), color=SLATE, lw=1.2, ls=(0, (4, 3)),
            label="buy and hold")
    ax.set_ylabel("cumulative equity")
    ax.legend(loc="upper left")
    despine(ax)
    ax.set_title("Figure 17 — Finding G-01: the same model, the same rule, one "
                 "default API call apart", fontsize=9.8, loc="left",
                 color=RED)
    note(ax, "Averaged over 30 independent runs: smoothed Sharpe 0.72 vs "
             "filtered 0.28 (gap 0.44 ± 0.06).\nThe curves are both plausible. "
             "There is no visual tell.", loc="lower right", fontsize=6.7)

    ax = axes[1]
    diff = (smoothed[:, bull] > 0.5) != (filtered[:, bull] > 0.5)
    ax.fill_between(np.arange(n), 0, 1, where=(state == 1), color=SLATE,
                    alpha=0.14, lw=0, step="mid", label="true bear regime")
    ax.plot(smoothed[:, bull], color=RED, lw=0.8, alpha=0.85,
            label="smoothed $P(\\mathrm{bull})$")
    ax.plot(filtered[:, bull], color=GREEN, lw=0.8, alpha=0.85,
            label="filtered $P(\\mathrm{bull})$")
    ax.scatter(np.where(diff)[0], np.full(diff.sum(), -0.10), s=1.6,
               color=AMBER, marker="|")
    ax.text(12, -0.20, f"signal disagreement: {diff.mean():.1%} of days",
            fontsize=6.9, color=AMBER)
    ax.set_ylim(-0.28, 1.05)
    ax.set_ylabel("P(bull)")
    ax.set_xlabel("trading day")
    ax.legend(loc="lower right", ncol=3, fontsize=6.8)
    despine(ax)
    save(fig, "fig17_hmm_lookahead")


# ==========================================================================
# Figure 18 — 3D: portfolio weight stability (HRP vs minimum variance)
# ==========================================================================
def fig_portfolio_3d():
    g = rng(9700)
    n, T = 30, 45
    true_S = _psd(g, n, cond=300) / n + np.eye(n) * 0.002
    L = np.linalg.cholesky(true_S)

    reps = 24
    Wh = np.zeros((reps, n))
    Wm = np.zeros((reps, n))
    for i in range(reps):
        r = g.standard_normal((T, n)) @ L.T
        S = np.cov(r.T)
        Wh[i] = _hrp_weights(S)
        m = np.linalg.solve(S, np.ones(n))
        Wm[i] = m / m.sum()

    # A SHARED z-range is essential: the comparison is meaningless if each
    # surface is autoscaled to its own spread.
    zlo = min(Wh.min(), Wm.min()) * 1.05
    zhi = max(Wh.max(), Wm.max()) * 1.05

    fig = plt.figure(figsize=(10.2, 3.9))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.92], wspace=0.50)
    for j, (W, name, col, cmap) in enumerate(
            ((Wh, "Hierarchical Risk Parity", GREEN, "Greens"),
             (Wm, "Minimum variance  ($\\Sigma^{-1}$)", RED, "Reds"))):
        ax = fig.add_subplot(gs[0, j], projection="3d")
        X, Yg = np.meshgrid(np.arange(n), np.arange(reps))
        ax.plot_surface(X, Yg, W, cmap=cmap, linewidth=0, antialiased=True,
                        rcount=reps, ccount=n, alpha=0.96,
                        vmin=zlo, vmax=zhi)
        ax.set_zlim(zlo, zhi)
        ax.set_xlabel("asset", labelpad=-5)
        ax.set_ylabel("resample", labelpad=-5)
        ax.set_zlabel("weight", labelpad=-7)
        ax.set_title(name, pad=-2, fontsize=8.6, color=col)
        ax.view_init(elev=32, azim=-58)
        ax.set_box_aspect((1, 1, 0.55), zoom=0.90)
        style3d(ax)
        if j == 1:
            ax.text2D(0.5, -0.06, "same vertical scale as the panel at left",
                      transform=ax.transAxes, ha="center", fontsize=6.4,
                      color=MUTED)

    ax = fig.add_subplot(gs[0, 2])
    turn_h = [np.abs(Wh[i] - Wh[i + 1]).sum() for i in range(reps - 1)]
    turn_m = [np.abs(Wm[i] - Wm[i + 1]).sum() for i in range(reps - 1)]
    parts = ax.violinplot([turn_h, turn_m], positions=[0, 1], widths=0.7,
                          showextrema=False, showmedians=True)
    for pc, c in zip(parts["bodies"], (GREEN, RED)):
        pc.set_facecolor(c)
        pc.set_alpha(0.55)
        pc.set_edgecolor("none")
    parts["cmedians"].set_color(INK)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["HRP", "min-variance"])
    ax.set_ylabel("gross turnover between resamples")
    ax.set_title("Rebalancing forced by noise alone", fontsize=8.8)
    despine(ax)
    note(ax, f"median {np.median(turn_m) / np.median(turn_h):.1f}× worse. Both "
             f"samples are drawn\nfrom the SAME distribution, so every trade\n"
             f"here is pure estimation error.", loc="upper left", fontsize=6.5)

    fig.suptitle("Figure 18 — Why the report is right to prefer methods that "
                 "never invert $\\Sigma$  (N=30, T=45)",
                 fontsize=9.8, color=INK, y=1.03)
    save(fig, "fig18_portfolio_3d")


# ==========================================================================
# Figure 19 — 3D limit order book (ties to the Aegis-Stream artefact)
# ==========================================================================
def fig_order_book_3d():
    """A limit order book as a depth surface over (event time, price offset).

    Depth is persistent in time (AR(1)), which is what makes a liquidity
    withdrawal visible as a canyon rather than lost in noise.
    """
    g = rng(9800)
    n_t, n_lvl = 120, 10
    offsets = np.concatenate([np.arange(-n_lvl, 0), np.arange(1, n_lvl + 1)])
    mid = 100 + np.cumsum(g.normal(0, 0.010, n_t))

    # Persistent depth: AR(1) in time, growing away from the touch.
    shape = np.abs(offsets) ** 0.72
    depth = np.zeros((n_t, len(offsets)))
    depth[0] = shape * 1000
    for t in range(1, n_t):
        depth[t] = (0.86 * depth[t - 1]
                    + 0.14 * shape * 1000 * g.uniform(0.75, 1.25, len(offsets)))

    # Liquidity withdrawal: the touch thins abruptly, then refills. The bid
    # side pulls harder than the ask, which is the asymmetry that shows up in
    # order-flow imbalance and is what a signal would actually key on.
    ev, dur = 55, 12
    near = np.abs(offsets) <= 4
    near_bid = near & (offsets < 0)
    near_ask = near & (offsets > 0)
    ramp_b = np.concatenate([np.linspace(1, 0.08, 3),
                             np.full(dur - 6, 0.08),
                             np.linspace(0.08, 1, 3)])
    ramp_a = np.concatenate([np.linspace(1, 0.45, 3),
                             np.full(dur - 6, 0.45),
                             np.linspace(0.45, 1, 3)])
    for i, t in enumerate(range(ev, ev + dur)):
        depth[t, near_bid] *= ramp_b[i]
        depth[t, near_ask] *= ramp_a[i]

    fig = plt.figure(figsize=(9.8, 4.0))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    T, O = np.meshgrid(np.arange(n_t), offsets, indexing="ij")
    ax.plot_surface(T, O, depth, cmap=SEQ, linewidth=0, antialiased=True,
                    rcount=n_t, ccount=len(offsets), alpha=0.97)
    ax.contour(T, O, depth, zdir="z", offset=0, levels=8, colors=[GRID],
               linewidths=0.4)
    ax.set_xlabel("event time", labelpad=-3)
    ax.set_ylabel("price offset (ticks from mid)", labelpad=-3)
    ax.set_zlabel("resting size", labelpad=-6)
    ax.view_init(elev=34, azim=-56)
    ax.set_box_aspect((1.4, 1, 0.62), zoom=0.94)
    ax.set_title("(a) Depth surface through a liquidity withdrawal",
                 pad=-2, fontsize=8.8)
    style3d(ax)

    ax = fig.add_subplot(1, 2, 2)
    top = depth[:, near].sum(axis=1)
    bid_top = depth[:, (offsets < 0) & near].sum(axis=1)
    ask_top = depth[:, (offsets > 0) & near].sum(axis=1)
    imb = (bid_top - ask_top) / (bid_top + ask_top)
    ax.plot(top / top[:ev].mean(), color=BLUE, lw=1.7,
            label="top-4 depth (normalised)")
    ax.plot(imb, color=AMBER, lw=1.3, label="order-flow imbalance")
    ax.plot(0.30 + (mid - mid[:ev].mean()) * 1.2, color=SLATE, lw=1.1,
            ls=(0, (4, 3)), label="mid price (offset, ×1.2)")
    ax.axvspan(ev, ev + dur, color=RED, alpha=0.10, lw=0)
    ax.annotate("withdrawal", xy=(ev + dur / 2, 0.10), xytext=(ev + 22, -0.30),
                fontsize=7.2, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9,
                                connectionstyle="arc3,rad=-0.25"))
    ax.axhline(0, color=GRID, lw=0.8)
    ax.set_xlabel("event time")
    ax.set_ylabel("normalised value")
    ax.set_title("(b) The microstructure features it produces", fontsize=8.8)
    ax.legend(loc="upper left", fontsize=6.9)
    ax.set_ylim(-0.72, 1.75)
    despine(ax)
    note(ax, "Bid depth collapses to ~8% of normal while the mid barely moves.\n"
             "That is the fragility behind the report's §4.6 Flash Crash lesson,\n"
             "and the state the Aegis-Stream book engine reconstructs in hardware.",
         loc="lower right", fontsize=6.4)

    fig.suptitle("Figure 19 — Limit-order-book state: the §2.10 microstructure "
                 "material, and the bridge to Aegis-Stream",
                 fontsize=9.8, color=INK, y=1.02)
    fig.subplots_adjust(wspace=0.26)
    save(fig, "fig19_order_book_3d")


# ==========================================================================
# Figure 20 — fractional differentiation trade-off
# ==========================================================================
def fig_frac_diff():
    from statsmodels.tsa.stattools import adfuller
    g = rng(801)
    n, width = 5000, 200
    price = 100 * np.exp(np.cumsum(g.normal(0.0002, 0.011, n)))
    logp = np.log(price)

    ds, adfs, corrs = [], [], []
    series = {}
    for d in np.round(np.arange(0.0, 1.01, 0.05), 2):
        w = _ffd_weights(d, width)
        out = np.array([np.dot(w[::-1], logp[i - width + 1:i + 1])
                        for i in range(width - 1, n)])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            adfs.append(adfuller(out, maxlag=1, autolag=None)[0])
        corrs.append(float(np.corrcoef(out, logp[width - 1:])[0, 1]))
        ds.append(float(d))
        if d in (0.0, 0.20, 1.0):
            series[float(d)] = out
    ds, adfs, corrs = np.array(ds), np.array(adfs), np.array(corrs)
    crit = -2.86
    d_min = ds[np.argmax(adfs < crit)]

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
    ax = axes[0]
    ax.plot(ds, adfs, color=BLUE, lw=2.0, label="ADF statistic")
    ax.axhline(crit, color=RED, lw=1.1, ls=(0, (4, 3)))
    ax.text(0.62, crit + 0.45, "5% unit-root critical value", fontsize=6.9,
            color=RED)
    ax.set_xlabel("differencing order $d$")
    ax.set_ylabel("ADF statistic", color=BLUE)
    ax.tick_params(axis="y", colors=BLUE)
    ax2 = ax.twinx()
    ax2.plot(ds, corrs, color=GREEN, lw=2.0)
    ax2.set_ylabel("correlation with the level series", color=GREEN)
    ax2.tick_params(axis="y", colors=GREEN)
    ax2.grid(False)
    ax2.spines["top"].set_visible(False)
    ax.axvline(d_min, color=INK, lw=1.2, ls=(0, (2, 2)))
    ax.axvspan(d_min, 1.0, color=SLATE, alpha=0.07, lw=0)
    ax.annotate(f"$d={d_min:.2f}$: stationary,\ncorrelation still "
                f"{corrs[np.argmax(adfs < crit)]:.2f}",
                xy=(d_min, crit), xytext=(d_min + 0.09, -1.1), fontsize=7.0,
                color=INK,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.8))
    ax.text(0.63, -0.6, "everything to the right\nis discarded memory",
            fontsize=6.9, color=MUTED, ha="center")
    ax.set_title("(a) Stationarity arrives long before $d=1$")
    despine(ax, left=True)

    ax = axes[1]
    for d, col, lbl in ((0.0, SLATE, "$d=0$  (raw log price, non-stationary)"),
                        (0.20, GREEN, f"$d={d_min:.2f}$  (stationary, memory kept)"),
                        (1.0, RED, "$d=1$  (returns, memory destroyed)")):
        s = series[d]
        ax.plot((s - s.mean()) / s.std(), color=col, lw=0.85, alpha=0.9,
                label=lbl)
    ax.set_xlabel("observation")
    ax.set_ylabel("standardised value")
    ax.set_title("(b) What each transform leaves behind")
    ax.legend(loc="upper left", fontsize=6.8)
    despine(ax)

    fig.suptitle("Figure 20 — Fractional differentiation: stationary while "
                 "preserving memory (verified F-03)",
                 fontsize=9.8, color=INK, y=1.03)
    fig.subplots_adjust(wspace=0.34)
    save(fig, "fig20_frac_diff")


if __name__ == "__main__":
    setup()
    print("  verification figures:")
    fig_no_trade_region()
    fig_meanrev_findings()
    fig_vol_estimators()
    fig_hmm_lookahead()
    fig_portfolio_3d()
    fig_order_book_3d()
    fig_frac_diff()
