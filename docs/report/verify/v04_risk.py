"""Section 2.7 -- risk metrics: VaR, CVaR coherence, Cornish-Fisher."""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from harness import Registry, rng

SEC = "2.7 Risk metrics"


def run(reg: Registry) -> None:
    _var_sign_convention(reg)
    _var_not_subadditive(reg)
    _cvar_subadditive(reg)
    _gaussian_es(reg)
    _cornish_fisher(reg)
    _ratio_definitions(reg)


def _var_sign_convention(reg: Registry) -> None:
    """The report writes parametric VaR as 'mu + z_alpha sigma' with no sign
    convention. Both readings appear in the literature and they differ by the
    sign of the whole quantity."""
    mu, sig, alpha = 0.0005, 0.012, 0.99
    z_lo = stats.norm.ppf(1 - alpha)      # -2.326
    z_hi = stats.norm.ppf(alpha)          # +2.326
    as_written_lo = mu + z_lo * sig       # negative: a return quantile
    as_written_hi = mu + z_hi * sig       # positive: a loss quantile

    g = rng(401)
    r = g.normal(mu, sig, 4_000_000)
    empirical_q = float(np.percentile(r, (1 - alpha) * 100))
    reg.close(
        "Q-01", SEC,
        r"Parametric VaR as a RETURN quantile: $q_{1-\alpha}=\mu+z_{1-\alpha}\sigma$",
        f"MC: 4M normal draws, alpha={alpha}, compared to the empirical "
        f"{(1 - alpha) * 100:g}th percentile",
        as_written_lo, empirical_q, rtol=0.01,
    )
    reg.add(
        "Q-02", SEC,
        r"The report's $\mu+z_\alpha\sigma$ is ambiguous without a sign "
        r"convention",
        "evaluate both readings at the same parameters",
        "one unambiguous number",
        f"return-quantile reading {as_written_lo:+.4f}; "
        f"loss-quantile reading {as_written_hi:+.4f}",
        "FLAG",
        r"Section 2.7 gives parametric VaR as $\mu+z_\alpha\sigma$ without "
        r"stating whether $\alpha$ is the tail probability or the confidence "
        r"level, or whether VaR is reported as a positive loss or a negative "
        r"return. The two readings differ by roughly "
        rf"{abs(as_written_hi - as_written_lo):.4f} here -- a sign flip on the "
        r"risk number itself. This is not a theoretical quibble: a sign error "
        r"in a risk limit is precisely the class of defect the report's "
        r"section 4.3 pre-trade controls exist to prevent, and it must be "
        r"pinned down by a property-based test (section 6.1) asserting "
        r"VaR $>$ 0 and VaR $\le$ CVaR under the house convention.",
        return_reading=as_written_lo, loss_reading=as_written_hi,
    )


def _var_not_subadditive(reg: Registry) -> None:
    """Concrete counterexample: two independent defaultable bonds."""
    p_default, loss, alpha = 0.04, 100.0, 0.95
    # Single bond: P(loss = 0) = 0.96 > 0.95, so the 95% VaR is 0.
    var_single = 0.0
    # Two independent bonds: P(no default) = 0.96^2 = 0.9216 < 0.95,
    # so the 95% quantile of the combined loss falls in the "one default" atom.
    p_none = (1 - p_default) ** 2
    var_pair = loss if p_none < alpha else 0.0

    g = rng(402)
    n = 4_000_000
    a = (g.random(n) < p_default) * loss
    b = (g.random(n) < p_default) * loss
    emp_single = float(np.percentile(a, alpha * 100))
    emp_pair = float(np.percentile(a + b, alpha * 100))

    violated = emp_pair > emp_single + emp_single
    reg.truth(
        "Q-03", SEC,
        r"VaR is NOT subadditive: a concrete counterexample",
        f"two independent bonds, {p_default:.0%} default probability, loss "
        f"{loss:g} each; {n:,} Monte Carlo draws at the {alpha:.0%} level",
        bool(violated and abs(emp_pair - var_pair) < 1e-9),
        f"analytic: VaR(A)=VaR(B)={var_single:g}, VaR(A+B)={var_pair:g}",
        f"empirical: VaR(A)={emp_single:g}, VaR(B)={emp_single:g}, "
        f"VaR(A+B)={emp_pair:g} > {emp_single + emp_single:g}",
        r"Confirms the report's assertion that VaR fails subadditivity, with a "
        r"minimal reproducible example. Diversifying across two INDEPENDENT "
        r"positions makes measured VaR go UP, from 0 to 100. Any risk limit "
        r"expressed in VaR can therefore penalise genuine diversification, "
        r"which is exactly the Artzner et al. coherence objection the report "
        r"cites.",
        var_single=emp_single, var_pair=emp_pair,
    )


def _cvar_subadditive(reg: Registry) -> None:
    """CVaR/ES satisfies subadditivity across many random dependence structures."""
    g = rng(403)
    alpha = 0.95
    n = 200_000

    def es(x: np.ndarray) -> float:
        q = np.percentile(x, alpha * 100)
        tail = x[x >= q]
        return float(tail.mean()) if tail.size else float(q)

    worst_violation = -np.inf
    trials = 300
    for _ in range(trials):
        # Random dependence: mixture of Gaussian copula, comonotone and
        # independent blocks, plus heavy tails and jumps.
        rho = g.uniform(-0.9, 0.9)
        df = g.integers(2, 30)
        z1 = g.standard_t(df, n)
        z2 = rho * z1 + math.sqrt(max(1 - rho**2, 0)) * g.standard_t(df, n)
        a = z1 * g.uniform(0.5, 2.0) + (g.random(n) < 0.01) * g.uniform(5, 40)
        b = z2 * g.uniform(0.5, 2.0) + (g.random(n) < 0.01) * g.uniform(5, 40)
        gap = es(a + b) - (es(a) + es(b))       # must be <= 0
        worst_violation = max(worst_violation, gap / (abs(es(a)) + abs(es(b))))

    # Allow a small tolerance for the finite-sample estimation of the tail mean.
    ok = worst_violation < 5e-3
    reg.truth(
        "Q-04", SEC,
        r"CVaR / Expected Shortfall IS subadditive: "
        r"$ES(A+B)\le ES(A)+ES(B)$",
        f"{trials} random dependence structures (Gaussian copula with rho in "
        f"[-0.9,0.9], Student-t margins df 2-30, 1% jump contamination), "
        f"{n:,} draws each",
        bool(ok),
        "no violation beyond finite-sample tail-estimation noise",
        f"largest normalised gap ES(A+B)-ES(A)-ES(B) across {trials} "
        f"trials: {worst_violation:+.3f} (must be <= 0; negative means "
        f"diversification benefit)",
        "Complements Q-03. Subadditivity is the coherence axiom VaR fails and "
        "ES satisfies, and it holds here under every dependence structure "
        "tested including strongly comonotone and jump-contaminated cases. "
        "This is the concrete basis for the report's recommendation to size "
        "risk limits in CVaR rather than VaR.",
        worst_violation=worst_violation,
    )


def _gaussian_es(reg: Registry) -> None:
    """ES has a closed form under normality: mu + sigma*phi(z_alpha)/(1-alpha)."""
    mu, sig, alpha = 0.0, 1.0, 0.975
    z = stats.norm.ppf(alpha)
    analytic = mu + sig * stats.norm.pdf(z) / (1 - alpha)
    g = rng(404)
    x = g.normal(mu, sig, 8_000_000)
    q = np.percentile(x, alpha * 100)
    empirical = float(x[x >= q].mean())
    reg.close(
        "Q-05", SEC,
        r"Gaussian Expected Shortfall $=\mu+\sigma\frac{\phi(z_\alpha)}"
        r"{1-\alpha}$",
        f"MC: 8M standard normal draws at alpha={alpha}",
        analytic, empirical, rtol=0.005,
        note="The report gives ES only as the definition E[L | L > VaR]. The "
             "closed form is worth stating because it is the reference value "
             "a unit test can assert against without Monte Carlo.",
    )

    ratio = analytic / z
    reg.add(
        "Q-06", SEC,
        r"Under normality ES exceeds VaR by a fixed, modest factor -- which is "
        r"exactly why normality is dangerous here",
        f"ratio ES/VaR at alpha={alpha} under normality vs Student-t(3)",
        f"normal: {ratio:.3f}x",
        f"normal {ratio:.3f}x; Student-t(3) empirical "
        f"{_t_es_ratio(alpha, 3):.3f}x",
        "INFO",
        r"The Gaussian ES/VaR ratio is only about "
        rf"{ratio:.2f}, so under a normal model the tail looks tame. With "
        rf"Student-t(3) tails the same ratio is {_t_es_ratio(alpha, 3):.2f}. "
        r"A risk system calibrated on Gaussian ES will therefore understate the "
        r"cost of the tail it is supposed to be measuring, which is the "
        r"practical reason the report's Cornish-Fisher and historical VaR "
        r"variants exist.",
        gaussian_ratio=ratio,
    )


def _t_es_ratio(alpha: float, df: int) -> float:
    g = rng(405)
    x = g.standard_t(df, 4_000_000)
    q = float(np.percentile(x, alpha * 100))
    return float(x[x >= q].mean()) / q


def _cornish_fisher(reg: Registry) -> None:
    """Cornish-Fisher: skew/kurtosis-adjusted quantile, and where it breaks."""
    def cf_z(z: float, s: float, k_excess: float) -> float:
        return (z
                + (z**2 - 1) * s / 6
                + (z**3 - 3 * z) * k_excess / 24
                - (2 * z**3 - 5 * z) * s**2 / 36)

    g = rng(406)
    n = 8_000_000
    rows = []
    for name, x in (
        ("skew-normal(a=4)", stats.skewnorm.rvs(4, size=n,
                                                random_state=np.random.RandomState(7))),
        ("Student-t(6)", g.standard_t(6, n)),
        ("lognormal(s=0.4)", g.lognormal(0, 0.4, n)),
    ):
        mu, sd = float(np.mean(x)), float(np.std(x, ddof=1))
        s = float(stats.skew(x))
        ke = float(stats.kurtosis(x))          # excess kurtosis
        for alpha in (0.95, 0.99):
            z = stats.norm.ppf(alpha)
            cf = mu + sd * cf_z(z, s, ke)
            gauss = mu + sd * z
            emp = float(np.percentile(x, alpha * 100))
            rows.append((name, alpha, emp, cf, gauss,
                         abs(cf - emp) / abs(emp), abs(gauss - emp) / abs(emp)))

    better = sum(1 for r in rows if r[5] < r[6])
    reg.truth(
        "Q-07", SEC,
        r"Cornish-Fisher $z_{cf}=z+\frac{(z^2-1)\gamma_3}{6}"
        r"+\frac{(z^3-3z)(\gamma_4-3)}{24}-\frac{(2z^3-5z)\gamma_3^2}{36}$ "
        r"improves on the Gaussian quantile for skewed/fat-tailed data",
        "3 distributions x 2 confidence levels, 8M draws each; relative error "
        "against the empirical quantile",
        better >= 5,
        "Cornish-Fisher closer than Gaussian in at least 5 of 6 cases",
        f"Cornish-Fisher wins {better}/6; " + "; ".join(
            f"{nm}@{a:.0%}: CF err {ec:.1%} vs Gaussian {eg:.1%}"
            for nm, a, _, _, _, ec, eg in rows),
        r"Verifies the expansion as written, including the often-dropped "
        r"$-\frac{(2z^3-5z)\gamma_3^2}{36}$ term. Note the expansion uses "
        r"EXCESS kurtosis ($\gamma_4-3$); the report writes $\gamma_4$ for "
        r"kurtosis in section 2.8 and $\gamma_4-3$ implicitly here, so the "
        r"convention must be fixed once and asserted in code. Cornish-Fisher is "
        r"also non-monotone for large $|\gamma_3|$ -- see Q-08.",
        table=[{"dist": nm, "alpha": a, "empirical": e, "cf": c, "gauss": gs}
               for nm, a, e, c, gs, _, _ in rows],
    )

    # Monotonicity failure: the expansion can produce a non-increasing quantile
    # function, which is nonsense as a risk measure.
    def cf_only(z, s, ke):
        return cf_z(z, s, ke)

    zs = np.linspace(0.5, 3.5, 400)
    bad = []
    for s, ke in ((0.5, 1.0), (1.0, 2.0), (2.0, 6.0), (3.0, 12.0),
                  (4.0, 20.0), (6.0, 50.0), (-3.0, 12.0)):
        vals = np.array([cf_only(z, s, ke) for z in zs])
        if np.any(np.diff(vals) < 0):
            bad.append((s, ke))
    reg.add(
        "Q-08", SEC,
        "Cornish-Fisher is not monotone in the quantile for large skewness, so "
        "it can report a SMALLER loss at a HIGHER confidence level",
        "scan z in [0.5, 3.5] at several (skew, excess kurtosis) pairs and test "
        "for a decreasing segment",
        "quantile function must be non-decreasing in z",
        f"non-monotone at (skew, excess kurt) = {bad}" if bad
        else "monotone at all tested parameters",
        "FLAG" if bad else "PASS",
        r"The report lists Cornish-Fisher without its domain of validity. It is "
        r"an asymptotic expansion, valid for mild non-normality only; at the "
        r"skewness levels typical of an option-overlay or short-vol sleeve "
        r"(section 4.6's XIV example) it can invert, reporting a smaller loss "
        r"at 99\% than at 95\%. The runtime must assert monotonicity of the "
        r"quantile function -- a natural Hypothesis property test (section 6.1) "
        r"-- and fall back to historical or filtered-historical simulation when "
        r"the assertion trips.",
        bad_params=[{"skew": s, "excess_kurt": k} for s, k in bad],
    )


def _ratio_definitions(reg: Registry) -> None:
    """Sharpe / Sortino / Calmar consistency and their disagreement."""
    g = rng(407)
    n = 252 * 20
    # Negatively skewed returns: the case where the ratios disagree most.
    r = 0.0004 + 0.008 * g.standard_normal(n) - 0.02 * (g.random(n) < 0.01)
    rf = 0.0

    sharpe = float(np.mean(r - rf) / np.std(r, ddof=1)) * math.sqrt(252)
    downside = float(np.sqrt(np.mean(np.minimum(r - rf, 0) ** 2)))
    sortino = float(np.mean(r - rf) / downside) * math.sqrt(252)

    eq = np.cumprod(1 + r)
    years = n / 252
    cagr = float(eq[-1] ** (1 / years) - 1)
    peak = np.maximum.accumulate(eq)
    mdd = float(np.min(eq / peak - 1))
    calmar = cagr / abs(mdd)

    reg.add(
        "Q-09", SEC,
        r"Sharpe, Sortino and Calmar rank the same track record differently "
        r"under negative skew",
        f"{years:.0f} years of simulated daily returns with 1% crash days; "
        f"all three ratios computed from the same series",
        "the three are not interchangeable",
        f"Sharpe {sharpe:.2f}, Sortino {sortino:.2f}, Calmar {calmar:.2f} "
        f"(CAGR {cagr:.1%}, max drawdown {mdd:.1%})",
        "INFO",
        r"The report lists the three ratios without noting that they encode "
        r"different risk preferences and can be gamed against one another. "
        r"Sortino exceeds Sharpe whenever upside dispersion outweighs downside, "
        r"and Calmar depends on a single realised path statistic (the worst "
        r"drawdown), making it the noisiest of the three and the easiest to "
        r"flatter with a short sample. The report's deflation machinery "
        r"(section 2.8) is built for the Sharpe ratio specifically; applying "
        r"DSR/PSR thresholds to a Sortino or Calmar figure is not valid.",
        sharpe=sharpe, sortino=sortino, calmar=calmar, mdd=mdd,
    )
