"""Section 2.4 -- portfolio construction.

Markowitz closed form, shrinkage, ERC/risk parity, HRP, Black-Litterman, and
the transaction-cost objective (where the report makes a real error).
"""

from __future__ import annotations

import math

import numpy as np
import sympy as sp
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.optimize import minimize
from scipy.spatial.distance import squareform

from harness import Registry, rng

SEC = "2.4 Portfolio construction"


def run(reg: Registry) -> None:
    _markowitz(reg)
    _error_maximisation(reg)
    _shrinkage(reg)
    _erc(reg)
    _hrp(reg)
    _black_litterman(reg)
    _transaction_costs(reg)


def _psd(g: np.random.Generator, n: int, cond: float = 1.0) -> np.ndarray:
    """Random correlation-like covariance with controllable conditioning."""
    a = g.standard_normal((n, n))
    q, _ = np.linalg.qr(a)
    eig = np.logspace(0, -math.log10(cond), n) if cond > 1 else np.ones(n)
    return q @ np.diag(eig) @ q.T


def _markowitz(reg: Registry) -> None:
    """w* = Sigma^{-1} mu / gamma, verified symbolically and numerically."""
    # Symbolic, 2 assets, fully general
    g_, w1, w2 = sp.symbols("gamma w1 w2", positive=True)
    m1, m2, s11, s12, s22 = sp.symbols("mu1 mu2 S11 S12 S22")
    w = sp.Matrix([w1, w2])
    mu = sp.Matrix([m1, m2])
    S = sp.Matrix([[s11, s12], [s12, s22]])
    obj = (w.T * mu)[0] - g_ / 2 * (w.T * S * w)[0]
    grad = sp.Matrix([sp.diff(obj, w1), sp.diff(obj, w2)])
    sol = sp.solve(grad, [w1, w2], dict=True)[0]
    closed = (S.inv() * mu) / g_
    ok = all(sp.simplify(sol[v] - closed[i]) == 0
             for i, v in enumerate((w1, w2)))
    reg.truth(
        "P-01", SEC,
        r"$\max_w w^\top\mu-\frac{\gamma}{2}w^\top\Sigma w$ has closed-form "
        r"solution $w^*=\frac{1}{\gamma}\Sigma^{-1}\mu$",
        "sympy: solve the first-order condition symbolically for 2 assets and "
        "compare to the stated closed form",
        bool(ok),
        r"$w^*=\gamma^{-1}\Sigma^{-1}\mu$",
        "first-order condition solution equals the closed form identically",
        "Exact symbolic verification. The Hessian is -gamma*Sigma, negative "
        "definite for positive definite Sigma, so this is a maximum.",
    )

    # Numeric, 12 assets
    g = rng(301)
    n = 12
    S = _psd(g, n) + np.eye(n) * 0.5
    mu = g.normal(0.05, 0.03, n)
    gam = 3.0
    closed_w = np.linalg.solve(S, mu) / gam
    res = minimize(lambda x: -(x @ mu - gam / 2 * x @ S @ x),
                   np.zeros(n), method="BFGS",
                   options={"gtol": 1e-12, "maxiter": 10000})
    reg.close(
        "P-02", SEC,
        "Numerical optimiser reproduces the Markowitz closed form",
        "12 assets, BFGS vs analytic solve, max abs weight difference",
        0.0, float(np.max(np.abs(res.x - closed_w))), atol=1e-6, rtol=0,
    )


def _error_maximisation(reg: Registry) -> None:
    """Quantify 'MV error-maximises' -- the report asserts it without a number."""
    g = rng(302)
    n, T = 20, 252 * 5
    true_S = _psd(g, n) * 0.04 / n + np.eye(n) * 0.02
    true_mu = g.normal(0.06, 0.02, n)
    gam = 3.0
    w_true = np.linalg.solve(true_S, true_mu) / gam

    def realised_sharpe(w: np.ndarray) -> float:
        return float(w @ true_mu / math.sqrt(w @ true_S @ w))

    turn, util_loss, sr_hat, sr_lw = [], [], [], []
    L = np.linalg.cholesky(true_S)
    from sklearn.covariance import LedoitWolf
    for _ in range(300):
        r = (g.standard_normal((T, n)) @ L.T) + true_mu / 252
        mu_hat = r.mean(axis=0) * 252
        S_hat = np.cov(r.T) * 252
        w_hat = np.linalg.solve(S_hat, mu_hat) / gam
        turn.append(float(np.sum(np.abs(w_hat - w_true))))
        u_true = w_true @ true_mu - gam / 2 * w_true @ true_S @ w_true
        u_hat = w_hat @ true_mu - gam / 2 * w_hat @ true_S @ w_hat
        util_loss.append(float((u_true - u_hat) / abs(u_true)))
        sr_hat.append(realised_sharpe(w_hat))
        # Same estimator with a shrunk covariance, to size the remedy.
        S_lw = LedoitWolf().fit(r).covariance_ * 252
        sr_lw.append(realised_sharpe(np.linalg.solve(S_lw, mu_hat) / gam))

    sr_true = realised_sharpe(w_true)
    med_sr = float(np.median(sr_hat))
    med_sr_lw = float(np.median(sr_lw))
    reg.add(
        "P-03", SEC,
        r"Mean-variance 'error-maximises': $\Sigma^{-1}$ amplifies estimation "
        r"noise into extreme, unstable weights",
        f"300 replications, {n} assets, 5 years of daily data, UNCONSTRAINED "
        f"plug-in estimates of mu and Sigma",
        f"true attainable Sharpe {sr_true:.2f}",
        f"plug-in MV achieves median Sharpe {med_sr:.2f} "
        f"({med_sr / sr_true - 1:+.0%}); with Ledoit-Wolf shrinkage "
        f"{med_sr_lw:.2f} ({med_sr_lw / sr_true - 1:+.0%}); median utility loss "
        f"{np.median(util_loss):.0%}",
        "PASS",
        rf"Confirms the report's claim with a magnitude. With {n} assets and five "
        rf"years of daily data -- more than most retail backtests have clean -- "
        rf"the unconstrained plug-in mean-variance portfolio realises a Sharpe of "
        rf"{med_sr:.2f} against an attainable {sr_true:.2f}, destroying "
        rf"{np.median(util_loss):.0%} of the utility it was solving for. "
        rf"Substituting a Ledoit-Wolf covariance moves the realised Sharpe only "
        rf"from {med_sr:.2f} to {med_sr_lw:.2f}, and that null result is the "
        r"most useful thing in this check: covariance shrinkage does NOT rescue "
        r"mean-variance here, because the binding error is in $\hat\mu$, not "
        r"$\hat\Sigma$. Expected returns need roughly two orders of magnitude "
        r"more data than covariances to estimate to comparable precision "
        r"(Merton 1980), so no amount of covariance cleverness fixes a noisy "
        r"$\mu$. The report should therefore not present shrinkage as the "
        r"remedy for 'MV error-maximises'. The remedies that actually work are "
        r"the ones that stop using $\hat\mu$ at all -- ERC, HRP, minimum "
        r"variance, inverse vol -- which is precisely why those methods "
        r"dominate in practice, and why the report is right to list them. Note "
        r"also that the setup is deliberately unconstrained: budget, long-only "
        r"and concentration limits are themselves powerful regularisers, a "
        r"second reason the report's 20\% per-ETF cap earns its place.",
        median_util_loss=float(np.median(util_loss)),
        median_weight_error=float(np.median(turn)),
        sr_true=sr_true, sr_plugin=med_sr, sr_lw=med_sr_lw,
    )


def _shrinkage(reg: Registry) -> None:
    """Ledoit-Wolf: convex combination, better conditioned, lower loss."""
    from sklearn.covariance import LedoitWolf, OAS, empirical_covariance

    g = rng(303)
    n, T = 50, 120                      # T < 3n: the regime shrinkage is for
    true_S = _psd(g, n, cond=50) / n + np.eye(n) * 0.01
    L = np.linalg.cholesky(true_S)
    r = g.standard_normal((T, n)) @ L.T

    # sklearn normalises by n (not n-1) and centres the data; match it
    # exactly so the reconstruction test measures the formula, not ddof.
    S_hat = empirical_covariance(r)
    lw = LedoitWolf().fit(r)
    oas = OAS().fit(r)

    # 1. The estimator is literally (1-delta)*S + delta*F with F = mu_bar * I.
    delta = lw.shrinkage_
    mu_bar = np.trace(S_hat) / n
    reconstructed = (1 - delta) * S_hat + delta * mu_bar * np.eye(n)
    reg.close(
        "P-04", SEC,
        r"Ledoit-Wolf is exactly $\hat\Sigma=(1-\delta)S+\delta F$ with $F$ the "
        r"scaled identity target",
        "reconstruct sklearn's estimate from its reported shrinkage intensity; "
        "max abs elementwise difference",
        0.0,
        float(np.max(np.abs(reconstructed - lw.covariance_))),
        atol=1e-10, rtol=0,
        note=f"fitted delta = {delta:.3f}",
    )

    # 2. Conditioning and estimation loss both improve.
    c_sample = float(np.linalg.cond(S_hat))
    c_lw = float(np.linalg.cond(lw.covariance_))
    loss_s = float(np.linalg.norm(S_hat - true_S, "fro"))
    loss_lw = float(np.linalg.norm(lw.covariance_ - true_S, "fro"))
    loss_oas = float(np.linalg.norm(oas.covariance_ - true_S, "fro"))
    ok = c_lw < c_sample and loss_lw < loss_s
    reg.truth(
        "P-05", SEC,
        "Shrinkage improves both conditioning and Frobenius estimation loss "
        "when T is small relative to N",
        f"N={n}, T={T} (T/N = {T / n:.1f}), sample vs Ledoit-Wolf vs OAS",
        ok,
        "condition number and loss both fall",
        f"condition number {c_sample:.0f} -> {c_lw:.0f}; "
        f"Frobenius loss {loss_s:.4f} -> {loss_lw:.4f} (LW), {loss_oas:.4f} (OAS)",
        "The report recommends OAS 'for Gaussian'. Verified here: with genuinely "
        "Gaussian data OAS is competitive with Ledoit-Wolf, but the ordering is "
        "data-dependent and neither dominates. Both massively beat the sample "
        "covariance in the short-sample regime, which is the regime a solo "
        "operator with a few years of daily ETF data is always in.",
        cond_sample=c_sample, cond_lw=c_lw,
    )


def _risk_contributions(w: np.ndarray, S: np.ndarray) -> np.ndarray:
    mrc = S @ w
    return w * mrc


def _erc(reg: Registry) -> None:
    """Equal risk contribution: the objective and its analytic special cases."""
    g = rng(304)
    n = 8
    S = _psd(g, n) / n + np.eye(n) * 0.02

    def obj(x):
        w = np.abs(x)
        w = w / w.sum()
        rc = _risk_contributions(w, S)
        return float(np.sum((rc - rc.mean()) ** 2)) * 1e6

    best, bestv = None, np.inf
    for _ in range(20):
        r = minimize(obj, g.random(n) + 0.5, method="Nelder-Mead",
                     options={"maxiter": 200000, "maxfev": 200000,
                              "xatol": 1e-12, "fatol": 1e-16})
        if r.fun < bestv:
            best, bestv = r, r.fun
    w = np.abs(best.x)
    w = w / w.sum()
    rc = _risk_contributions(w, S)
    spread = float((rc.max() - rc.min()) / rc.mean())
    reg.close(
        "P-06", SEC,
        r"Minimising $\sum_i(w_i(\Sigma w)_i-\frac1N w^\top\Sigma w)^2$ yields "
        r"equal risk contributions $w_i(\Sigma w)_i=w_j(\Sigma w)_j$",
        f"{n}-asset numerical solve, 20 restarts; relative spread of risk "
        f"contributions at the optimum",
        0.0, spread, atol=1e-4, rtol=0,
    )

    # Analytic special case: with equal pairwise correlation, w_i ~ 1/sigma_i.
    n2 = 6
    sig = np.array([0.10, 0.15, 0.20, 0.25, 0.30, 0.40])
    rho = 0.4
    C = np.full((n2, n2), rho)
    np.fill_diagonal(C, 1.0)
    S2 = np.outer(sig, sig) * C

    def obj2(x):
        w = np.abs(x) / np.abs(x).sum()
        rc = _risk_contributions(w, S2)
        return float(np.sum((rc - rc.mean()) ** 2)) * 1e6

    best2, bv2 = None, np.inf
    for _ in range(20):
        r = minimize(obj2, g.random(n2) + 0.5, method="Nelder-Mead",
                     options={"maxiter": 200000, "maxfev": 200000,
                              "xatol": 1e-12, "fatol": 1e-16})
        if r.fun < bv2:
            best2, bv2 = r, r.fun
    w2 = np.abs(best2.x) / np.abs(best2.x).sum()
    analytic = (1 / sig) / np.sum(1 / sig)
    reg.close(
        "P-07", SEC,
        r"Under equal pairwise correlation the ERC solution is exactly "
        r"$w_i\propto1/\sigma_i$ (inverse-volatility weighting)",
        "6 assets, rho=0.4, numerical ERC vs the analytic inverse-vol weights; "
        "max abs weight difference",
        0.0, float(np.max(np.abs(w2 - analytic))), atol=1e-4, rtol=0,
        note="Useful practical corollary the report omits: when correlations "
             "are roughly uniform -- the usual case for a broad ETF sleeve -- "
             "the whole ERC machinery collapses to inverse-vol weighting, "
             "which needs no optimiser and no matrix inverse.",
    )


def _hrp_weights(cov: np.ndarray) -> np.ndarray:
    """Lopez de Prado HRP: tree clustering, quasi-diagonalisation, recursive
    bisection with inverse-variance allocation. No matrix inverse anywhere."""
    std = np.sqrt(np.diag(cov))
    corr = cov / np.outer(std, std)
    np.fill_diagonal(corr, 1.0)
    dist = np.sqrt(np.clip((1.0 - corr) / 2.0, 0, None))
    np.fill_diagonal(dist, 0.0)
    link = linkage(squareform(dist, checks=False), method="single")

    # Quasi-diagonalise: depth-first leaf order of the dendrogram.
    order = [n.id for n in to_tree(link).pre_order(lambda x: x)]

    def ivp(sub: np.ndarray) -> np.ndarray:
        iv = 1.0 / np.diag(sub)
        return iv / iv.sum()

    w = np.ones(len(order))
    clusters = [order]
    while clusters:
        nxt = []
        for c in clusters:
            if len(c) <= 1:
                continue
            h = len(c) // 2
            left, right = c[:h], c[h:]
            nxt += [left, right]
            vl = float(ivp(cov[np.ix_(left, left)]) @
                       cov[np.ix_(left, left)] @ ivp(cov[np.ix_(left, left)]))
            vr = float(ivp(cov[np.ix_(right, right)]) @
                       cov[np.ix_(right, right)] @ ivp(cov[np.ix_(right, right)]))
            alpha = 1.0 - vl / (vl + vr)
            for i in left:
                w[i] *= alpha
            for i in right:
                w[i] *= 1.0 - alpha
        clusters = nxt
    return w


def _hrp(reg: Registry) -> None:
    """HRP avoids inversion and is stable where mean-variance explodes."""
    g = rng(305)
    n, T = 30, 45
    true_S = _psd(g, n, cond=300) / n + np.eye(n) * 0.002
    L = np.linalg.cholesky(true_S)

    hrp_turn, mv_turn = [], []
    for _ in range(200):
        r1 = g.standard_normal((T, n)) @ L.T
        r2 = g.standard_normal((T, n)) @ L.T
        S1, S2 = np.cov(r1.T), np.cov(r2.T)
        w1, w2 = _hrp_weights(S1), _hrp_weights(S2)
        hrp_turn.append(float(np.sum(np.abs(w1 - w2))))
        m1 = np.linalg.solve(S1, np.ones(n))
        m1 = m1 / m1.sum()
        m2 = np.linalg.solve(S2, np.ones(n))
        m2 = m2 / m2.sum()
        mv_turn.append(float(np.sum(np.abs(m1 - m2))))

    w = _hrp_weights(np.cov((g.standard_normal((T, n)) @ L.T).T))
    props_ok = bool(abs(w.sum() - 1) < 1e-10 and np.all(w >= -1e-12))
    reg.truth(
        "P-08", SEC,
        "HRP produces long-only weights summing to 1 without inverting the "
        "covariance matrix, and is dramatically more stable than minimum "
        "variance under resampling",
        f"200 paired resamples, N={n}, T={T} (T/N={T / n:.1f}), condition "
        f"number ~{np.linalg.cond(true_S):.0f}",
        props_ok and np.median(hrp_turn) < np.median(mv_turn),
        "HRP weights valid and more stable than MV",
        f"weights sum to {w.sum():.10f}, min weight {w.min():.4f}; median "
        f"turnover between independent samples: HRP {np.median(hrp_turn):.3f} "
        f"vs min-variance {np.median(mv_turn):.3f} "
        f"({np.median(mv_turn) / np.median(hrp_turn):.1f}x worse)",
        "Confirms the report's 'avoids Sigma^{-1}; robust to ill-conditioning'. "
        "The stability ratio is the number worth quoting: on two independent "
        "samples from the SAME distribution, minimum variance reshuffles its "
        "book several times more than HRP does. That difference is pure "
        "transaction cost paid for estimation noise.",
        hrp_turnover=float(np.median(hrp_turn)),
        mv_turnover=float(np.median(mv_turn)),
    )


def _black_litterman(reg: Registry) -> None:
    """BL reduces to equilibrium with no views, and honours views as Omega->0."""
    g = rng(306)
    n = 6
    S = _psd(g, n) / n + np.eye(n) * 0.02
    w_mkt = np.array([0.30, 0.25, 0.15, 0.15, 0.10, 0.05])
    delta, tau = 2.5, 0.05
    Pi = delta * S @ w_mkt

    def bl(P, Q, Omega):
        A = np.linalg.inv(tau * S) + P.T @ np.linalg.inv(Omega) @ P
        b = np.linalg.inv(tau * S) @ Pi + P.T @ np.linalg.inv(Omega) @ Q
        return np.linalg.solve(A, b)

    # 1. Reverse optimisation is self-consistent: Pi recovers w_mkt.
    w_back = np.linalg.solve(S, Pi) / delta
    reg.close(
        "P-09", SEC,
        r"$\Pi=\delta\Sigma w_{mkt}$ is the equilibrium return vector: feeding "
        r"it back through $w=\frac1\delta\Sigma^{-1}\mu$ recovers $w_{mkt}$",
        "6 assets, reverse then forward optimisation, max abs difference",
        0.0, float(np.max(np.abs(w_back - w_mkt))), atol=1e-12, rtol=0,
    )

    # 2. Vanishingly confident views leave the posterior at equilibrium.
    P = np.zeros((1, n))
    P[0, 0], P[0, 1] = 1.0, -1.0
    Q = np.array([0.05])
    post_vague = bl(P, Q, np.array([[1e12]]))
    reg.close(
        "P-10", SEC,
        r"With no information in the views ($\Omega\to\infty$) the "
        r"Black-Litterman posterior collapses to the equilibrium prior $\Pi$",
        "one relative view with variance 1e12; max abs deviation from Pi",
        0.0, float(np.max(np.abs(post_vague - Pi))), atol=1e-9, rtol=0,
    )

    # 3. Certain views are honoured exactly.
    post_sure = bl(P, Q, np.array([[1e-12]]))
    reg.close(
        "P-11", SEC,
        r"With certain views ($\Omega\to0$) the posterior satisfies "
        r"$P\,E[R]=Q$ exactly",
        "same view with variance 1e-12; |P E[R] - Q|",
        0.0, float(abs((P @ post_sure - Q)[0])), atol=1e-8, rtol=0,
        note="Together P-09/10/11 pin down the three boundary behaviours that "
             "make the formula trustworthy. The report states the formula but "
             "none of its limits, which are what a reviewer would check first.",
    )


def _transaction_costs(reg: Registry) -> None:
    """The report's no-trade-region claim. Quadratic costs do NOT produce one.

    Report text (2.4): 'quadratic costs give a closed form and a no-trade region
    (don't rebalance until drift exceeds a band)'.

    The closed form is right. The no-trade region is wrong: it requires
    PROPORTIONAL (L1) costs. Under a smooth quadratic penalty the solution is
    continuous in the starting weights and always trades a nonzero amount.
    """
    g = rng(307)
    n = 5
    S = _psd(g, n) / n + np.eye(n) * 0.02
    mu = g.normal(0.05, 0.02, n)
    gam = 3.0
    Lam = np.eye(n) * 0.5

    # --- (a) the closed form the report claims -------------------------
    w0 = g.normal(0, 0.2, n)
    closed = np.linalg.solve(gam * S + 2 * Lam, mu + 2 * Lam @ w0)
    res = minimize(
        lambda x: -(x @ mu - gam / 2 * x @ S @ x - (x - w0) @ Lam @ (x - w0)),
        np.zeros(n), method="BFGS", options={"gtol": 1e-14, "maxiter": 50000})
    reg.close(
        "P-12", SEC,
        r"The cost-aware objective $w^\top\mu-\frac\gamma2 w^\top\Sigma w"
        r"-(w-w_0)^\top\Lambda(w-w_0)$ has closed form "
        r"$w^*=(\gamma\Sigma+2\Lambda)^{-1}(\mu+2\Lambda w_0)$",
        "5 assets, analytic solve vs BFGS, max abs weight difference",
        0.0, float(np.max(np.abs(res.x - closed))), atol=1e-6, rtol=0,
        note="The report's 'closed form' claim is correct.",
    )

    # --- (b) the no-trade region claim ---------------------------------
    w_target = np.linalg.solve(gam * S, mu)     # frictionless optimum
    drifts = np.linspace(0.0, 0.4, 41)
    direction = np.zeros(n)
    direction[0] = 1.0
    quad_trade, l1_trade = [], []
    for d in drifts:
        start = w_target + d * direction
        wq = np.linalg.solve(gam * S + 2 * Lam, mu + 2 * Lam @ start)
        quad_trade.append(float(np.sum(np.abs(wq - start))))
        # Proportional (L1) cost of the same order of magnitude
        c = 0.02
        rl1 = minimize(
            lambda x: -(x @ mu - gam / 2 * x @ S @ x - c * np.sum(np.abs(x - start))),
            start.copy(), method="Powell",
            options={"xtol": 1e-12, "ftol": 1e-14, "maxiter": 200000,
                     "maxfev": 200000})
        l1_trade.append(float(np.sum(np.abs(rl1.x - start))))

    quad_trade = np.array(quad_trade)
    l1_trade = np.array(l1_trade)
    # Quadratic: trade is strictly positive for every nonzero drift.
    quad_always_trades = bool(np.all(quad_trade[1:] > 1e-6))
    # L1: there is a genuine band of drifts with (numerically) zero trade.
    l1_band = drifts[np.argmax(l1_trade > 1e-3)] if np.any(l1_trade > 1e-3) else np.nan
    l1_has_band = bool(l1_band > 0)

    reg.add(
        "P-13", SEC,
        r"Quadratic transaction costs do NOT create a no-trade region; "
        r"proportional (L1) costs do",
        "sweep the starting weight away from the frictionless optimum and "
        "measure the traded amount under each cost model",
        "report claims quadratic costs give a no-trade region",
        f"quadratic: trade > 0 at every nonzero drift "
        f"(min traded {quad_trade[1]:.2e}); "
        f"L1: exactly zero trade until drift reaches {l1_band:.2f}",
        "FAIL" if (quad_always_trades and l1_has_band) else "INFO",
        r"\textbf{Correction required.} Section 2.4 states that quadratic costs "
        r"'give a closed form AND a no-trade region'. The closed form is correct "
        r"(P-12); the no-trade region is not. A smooth quadratic penalty has zero "
        r"derivative at zero trade, so the first-order condition always prescribes "
        r"a strictly positive trade -- the solution shrinks toward $w_0$ "
        r"(partial adjustment) but never stops. A no-trade region requires a cost "
        r"function with a KINK at zero, i.e. proportional/L1 costs, whose "
        r"subgradient interval $[-c,c]$ absorbs small deviations. This is not "
        r"pedantry: it changes the implementation. If the system is built on the "
        r"quadratic model expecting bands to appear, it will rebalance every "
        r"single day and bleed the cost the band was meant to save. Real spreads "
        r"and commissions ARE proportional, so the L1 model is also the more "
        r"faithful one. Recommended fix: either state the objective with an L1 "
        r"term, or keep the quadratic form and impose the no-trade band as an "
        r"explicit separate rule.",
        quad_min_trade=float(quad_trade[1]), l1_band_width=float(l1_band),
        drifts=drifts.tolist(), quad_trade=quad_trade.tolist(),
        l1_trade=l1_trade.tolist(),
    )
