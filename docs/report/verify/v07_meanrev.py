"""Section 6.5 -- pairs trading: Ornstein-Uhlenbeck, cointegration, Kalman."""

from __future__ import annotations

import math

import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.tsa.vector_ar.vecm import coint_johansen

from harness import Registry, rng

SEC = "6.5 Pairs / statistical arbitrage"


def run(reg: Registry) -> None:
    _ou_stationary(reg)
    _ou_half_life(reg)
    _engle_granger_critical_values(reg)
    _johansen_rank(reg)
    _kalman_hedge_ratio(reg)


def _simulate_ou(g, n, theta, mu, sigma, dt=1.0, x0=None):
    """Exact (not Euler) simulation of dX = theta(mu - X)dt + sigma dW."""
    a = math.exp(-theta * dt)
    sd = sigma * math.sqrt((1 - a**2) / (2 * theta))
    x = np.empty(n)
    x[0] = mu if x0 is None else x0
    e = g.normal(0.0, sd, n)
    for t in range(1, n):
        x[t] = mu + a * (x[t - 1] - mu) + e[t]
    return x


def _ou_stationary(reg: Registry) -> None:
    """Stationary distribution is N(mu, sigma^2/(2 theta))."""
    g = rng(701)
    theta, mu, sigma = 1.5, 0.4, 0.9
    x = _simulate_ou(g, 4_000_000, theta, mu, sigma)
    x = x[1000:]
    var_analytic = sigma**2 / (2 * theta)
    reg.close(
        "M-01", SEC,
        r"Ornstein-Uhlenbeck stationary distribution is "
        r"$\mathcal N(\mu,\ \sigma^2/2\theta)$ -- mean",
        f"exact simulation, 4M steps, theta={theta}, mu={mu}, sigma={sigma}",
        mu, float(np.mean(x)), atol=0.005, rtol=0,
    )
    reg.close(
        "M-02", SEC,
        r"Ornstein-Uhlenbeck stationary variance $=\sigma^2/2\theta$",
        "same simulation, sample variance",
        var_analytic, float(np.var(x, ddof=1)), rtol=0.01,
        note=r"Confirms the report's statement exactly. Practical use: this is "
             r"what makes the z-score in the report's entry rule well defined -- "
             r"the spread has a genuine stationary scale to normalise by, which "
             r"a non-cointegrated pair does not.",
    )


def _ou_half_life(reg: Registry) -> None:
    """Verify the exact inversion and quantify the superseded Euler approximation.

    Exact discretisation of dX = theta(mu - X)dt + sigma dW at spacing dt gives
        X_t - X_{t-1} = (e^{-theta dt} - 1)(X_{t-1} - mu) + noise
    so the OLS slope estimates lambda = e^{-theta dt} - 1, hence
        theta = -ln(1 + lambda)/dt        (exact)
        theta = -lambda/dt                (first-order in theta*dt)
    and half-life = ln(2)/theta.
    """
    g = rng(702)
    rows = []
    for theta in (0.02, 0.05, 0.10, 0.25, 0.50, 1.00):
        n = 400_000
        x = _simulate_ou(g, n, theta, 0.0, 1.0, dt=1.0)
        dx = np.diff(x)
        X = sm.add_constant(x[:-1])
        lam = float(sm.OLS(dx, X).fit().params[1])

        true_hl = math.log(2) / theta
        rep_hl = -math.log(2) / lam                     # report's formula
        exact_hl = -math.log(2) / math.log(1 + lam)     # correct formula
        rows.append((theta, true_hl, rep_hl, exact_hl,
                     rep_hl / true_hl - 1, exact_hl / true_hl - 1))

    # The exact formula must recover the truth at every speed.
    worst_exact = max(abs(r[5]) for r in rows)
    reg.truth(
        "M-03", SEC,
        r"Exact OU half-life from the regression slope is "
        r"$-\ln 2/\ln(1+\lambda)$, not $-\ln 2/\lambda$",
        "simulate OU exactly at six mean-reversion speeds (400k steps each), "
        "run the report's regression, and compare both estimators against the "
        "known true half-life",
        worst_exact < 0.02,
        "exact formula recovers the true half-life at every speed",
        f"max error of the exact formula {worst_exact:.2%}; "
        + "; ".join(f"theta={t:.2f}: true {th:.1f}, exact {ex:.1f}"
                    for t, th, _, ex, _, _ in rows),
        "Establishes the correct reference before assessing the report's "
        "version in M-04.",
        table=[{"theta": t, "true_hl": th, "report_hl": rp, "exact_hl": ex}
               for t, th, rp, ex, _, _ in rows],
    )

    # Use the population slope here so the direction-of-bias assertion is not
    # obscured by OLS sampling noise at the slowest mean-reversion speed.
    bias_rows = []
    for theta in (0.02, 0.05, 0.10, 0.25, 0.50, 1.00):
        lam = math.expm1(-theta)
        true_hl = math.log(2) / theta
        approx_hl = -math.log(2) / lam
        bias_rows.append((theta, true_hl, approx_hl,
                          approx_hl / true_hl - 1))
    errors = [r[3] for r in bias_rows]
    overstates_and_grows = all(e > 0 for e in errors) and all(
        b > a for a, b in zip(errors, errors[1:]))

    reg.truth(
        "M-04", SEC,
        r"The Euler half-life $-\ln 2/\lambda$ overstates the exact OU "
        r"half-life, with error increasing in mean-reversion speed",
        "evaluate the population slope lambda=exp(-theta*dt)-1 at six speeds "
        "and compare the Euler approximation with ln(2)/theta",
        overstates_and_grows,
        "positive, monotonically increasing approximation error",
        "; ".join(f"theta={t:.2f} (true HL {th:.1f}): Euler {ap:.1f} "
                  f"({e:+.0%})" for t, th, ap, e in bias_rows),
        r"The corrected report uses $-\Delta t\ln 2/\ln(1+\lambda)$. This "
        r"check retains the discarded Euler form only as a regression guard that "
        r"quantifies why it must not be restored.",
        table=[{"theta": t, "true_hl": th, "euler_hl": ap,
                "euler_err": e} for t, th, ap, e in bias_rows],
    )


def _engle_granger_critical_values(reg: Registry) -> None:
    """Applying standard ADF critical values to EG residuals over-rejects.

    The report says: 'Engle-Granger two-step -- OLS then ADF unit-root test on
    the residual u_t'. True, but the residual is estimated, not observed, so the
    standard ADF critical values do not apply.
    """
    g = rng(703)
    n, trials = 250, 3000
    rej_naive = 0
    rej_proper = 0
    for _ in range(trials):
        # Two INDEPENDENT random walks: no cointegration exists.
        x = np.cumsum(g.standard_normal(n))
        y = np.cumsum(g.standard_normal(n))
        # Engle-Granger step 1
        res = sm.OLS(y, sm.add_constant(x)).fit()
        u = res.resid
        # Naive: ADF on the residual with standard ADF critical values
        p_naive = adfuller(u, maxlag=1, regression="n", autolag=None)[1]
        rej_naive += int(p_naive < 0.05)
        # Proper: Engle-Granger / Phillips-Ouliaris critical values
        p_proper = coint(y, x, trend="c", maxlag=1, autolag=None)[1]
        rej_proper += int(p_proper < 0.05)

    size_naive = rej_naive / trials
    size_proper = rej_proper / trials
    ok = size_naive > 0.12 and 0.02 < size_proper < 0.09
    reg.truth(
        "M-05", SEC,
        r"Engle-Granger residuals must be tested with cointegration critical "
        r"values, NOT standard ADF critical values",
        f"{trials:,} pairs of INDEPENDENT random walks (n={n}), where the true "
        f"cointegration rate is 0%; measure the false-positive rate of each "
        f"test at a nominal 5% level",
        ok,
        "both tests should reject 5% of the time; only the proper one does",
        f"naive ADF critical values reject {size_naive:.1%} of the time "
        f"(nominal 5%); proper Engle-Granger critical values reject "
        f"{size_proper:.1%}",
        r"\textbf{Material omission.} Section 6.5 describes the Engle-Granger "
        r"procedure correctly but does not warn that the second step needs its "
        r"own critical values. Because $u_t$ is a fitted residual, OLS has "
        r"already minimised its variance, making it look more stationary than "
        r"it is. Using textbook ADF tables therefore finds spurious "
        rf"cointegration roughly {size_naive / 0.05:.0f}x too often -- "
        rf"{size_naive:.0%} of independent random-walk pairs are declared "
        r"cointegrated. For a solo operator screening a few hundred ETF pairs, "
        r"that is a guaranteed pipeline of pairs that look tradeable and are "
        r"not. Use \texttt{statsmodels.tsa.stattools.coint} (which applies "
        r"MacKinnon's Engle-Granger surfaces) or the Johansen test, and never "
        r"\texttt{adfuller} on a regression residual. This interacts badly with "
        r"the multiple-testing problem in section 2.8: screening pairs IS a "
        r"trial count, and it must be registered as one.",
        size_naive=size_naive, size_proper=size_proper,
    )


def _johansen_rank(reg: Registry) -> None:
    """Johansen trace test recovers the number of cointegrating vectors."""
    g = rng(704)
    n = 1500
    trials = 200
    correct = 0
    for _ in range(trials):
        # Three series with exactly one cointegrating relationship:
        # a common stochastic trend drives all three, plus stationary noise.
        f = np.cumsum(g.standard_normal(n))
        z = _simulate_ou(g, n, 0.3, 0.0, 1.0)
        w = np.cumsum(g.standard_normal(n)) * 0.6
        y1 = f + 0.5 * g.standard_normal(n)
        y2 = 2.0 * f + z + 0.5 * g.standard_normal(n)
        y3 = w + 0.5 * g.standard_normal(n)
        Y = np.column_stack([y1, y2, y3])
        r = coint_johansen(Y, det_order=0, k_ar_diff=1)
        # Trace statistic vs the 95% critical value, sequential from r=0.
        rank = 0
        for i in range(3):
            if r.lr1[i] > r.cvt[i, 1]:
                rank = i + 1
            else:
                break
        correct += int(rank == 1)
    rate = correct / trials
    reg.truth(
        "M-06", SEC,
        r"Johansen trace test recovers the rank of $\Pi$, i.e. the number of "
        r"cointegrating vectors",
        f"{trials} simulated 3-variable systems (n={n}) built with exactly one "
        f"cointegrating relationship; sequential trace test at the 95% level",
        rate > 0.80,
        "rank 1 identified in the large majority of replications",
        f"correct rank identified in {rate:.0%} of replications",
        r"Confirms the report's description that the rank of $\Pi$ counts the "
        r"cointegrating vectors and that the trace statistic tests it "
        r"sequentially. Note the test is applied here with the correct "
        r"asymptotic critical values built in, which is exactly the advantage "
        r"over the hand-rolled Engle-Granger route in M-05. For a solo "
        r"operator the practical recommendation follows: prefer Johansen, both "
        r"because it needs no choice of dependent variable (as the report "
        r"notes) and because it is much harder to get the inference wrong.",
        detection_rate=rate,
    )


def _kalman_hedge_ratio(reg: Registry) -> None:
    """Kalman-filtered beta tracks a drifting hedge ratio better than rolling OLS."""
    g = rng(705)
    n = 2000
    # True hedge ratio follows a random walk, with a structural break midway.
    beta_true = 1.0 + np.cumsum(g.normal(0, 0.004, n))
    beta_true[n // 2:] += 0.35
    x = np.cumsum(g.normal(0, 1.0, n)) + 50.0
    obs_sd = 0.5
    y = beta_true * x + g.normal(0, obs_sd, n)

    # --- rolling OLS -------------------------------------------------
    def rolling_beta(win):
        b = np.full(n, np.nan)
        for t in range(win, n):
            xx = x[t - win:t]
            yy = y[t - win:t]
            b[t] = float(np.dot(xx, yy) / np.dot(xx, xx))
        return b

    # --- Kalman filter: state = beta, random walk, observation y = beta*x + e
    def kalman_beta(q, r):
        b = np.empty(n)
        P = 1.0
        bh = 1.0
        for t in range(n):
            P = P + q                                # predict
            k = P * x[t] / (x[t] ** 2 * P + r)       # gain
            bh = bh + k * (y[t] - bh * x[t])         # update
            P = (1 - k * x[t]) * P
            b[t] = bh
        return b

    rows = []
    for win in (30, 60, 120):
        b = rolling_beta(win)
        m = ~np.isnan(b)
        rows.append((f"rolling OLS {win}d",
                     float(np.sqrt(np.mean((b[m] - beta_true[m]) ** 2)))))
    bk = kalman_beta(q=0.004**2, r=obs_sd**2)
    rmse_k = float(np.sqrt(np.mean((bk[120:] - beta_true[120:]) ** 2)))
    rows.append(("Kalman", rmse_k))

    best_roll = min(r[1] for r in rows[:-1])
    reg.truth(
        "M-07", SEC,
        r"A Kalman filter tracks a time-varying hedge ratio $\beta_t$ "
        r"substantially better than rolling OLS, including through a "
        r"structural break",
        f"simulated random-walk beta with a +0.35 level break at the midpoint, "
        f"n={n}; RMSE of the estimated beta against the truth",
        rmse_k < best_roll,
        "Kalman RMSE below the best rolling-OLS window",
        "; ".join(f"{nm}: RMSE {v:.4f}" for nm, v in rows)
        + f" (Kalman is {best_roll / rmse_k:.1f}x better than the best window)",
        r"Confirms the report's claim that a Kalman filter 'tracks structural "
        r"breaks far better than rolling OLS'. The mechanism is worth stating: "
        r"rolling OLS faces an unavoidable bias-variance choice through its "
        r"window length -- short windows are noisy, long windows lag the break "
        r"-- whereas the Kalman gain adapts automatically, widening after a "
        r"surprise and narrowing in quiet periods. The cost is two variance "
        r"parameters (process $q$ and observation $r$) that must themselves be "
        r"estimated, and which are exactly the kind of free parameter the "
        r"report's section 2.8 trial registry needs to count.",
        table=[{"method": nm, "rmse": v} for nm, v in rows],
    )
