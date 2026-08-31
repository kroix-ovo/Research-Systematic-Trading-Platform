"""Section 2.8 -- statistical validation. The report's highest-stakes maths.

PSR, the False Strategy Theorem / Deflated Sharpe Ratio, MinTRL, PBO via CSCV,
and purged k-fold cross-validation with embargo. These are the checks that
decide whether a strategy is allowed to trade, so an error here is not academic.
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np
from scipy import stats
from scipy.optimize import brentq

from harness import Registry, rng

SEC = "2.8 Statistical validation"


def run(reg: Registry) -> None:
    _sharpe_standard_error(reg)
    _psr(reg)
    _false_strategy_theorem(reg)
    _dsr_headline(reg)
    _mintrl(reg)
    _pbo_cscv(reg)
    _purged_cv(reg)


# ---------------------------------------------------------------- PSR
def _sr_se(sr: float, n: int, skew: float, kurt_noncentral: float) -> float:
    """Standard error of the Sharpe estimator, Mertens (2002) / Lo (2002).

    Var[SR_hat] = (1/(n-1)) * (1 - gamma3*SR + (gamma4-1)/4 * SR^2)
    with gamma4 the NON-EXCESS kurtosis (3 for a Gaussian).
    """
    return math.sqrt((1 - skew * sr + (kurt_noncentral - 1) / 4 * sr**2)
                     / (n - 1))


def _sharpe_standard_error(reg: Registry) -> None:
    """The PSR denominator IS the standard error of the Sharpe estimate.

    This is the single most load-bearing formula in section 2.8: everything
    downstream (PSR, DSR, MinTRL) is a transformation of it.
    """
    g = rng(501)
    n = 1250                                   # 5 years of daily data
    reps = 200_000
    rows = []

    # Case 1: Gaussian. Denominator should reduce to sqrt(1 + SR^2/2).
    for label, sampler, skew_t, kurt_t in (
        ("Gaussian", lambda size: g.standard_normal(size), 0.0, 3.0),
        ("Student-t(6)",
         lambda size: g.standard_t(6, size) / math.sqrt(6 / 4), 0.0, 6.0),
        ("skew-normal(a=6)", None, None, None),
    ):
        # Drawn in row chunks. A single (reps, n) array is 2 GB here, and the
        # standardise-and-shift steps each allocate another copy -- enough to
        # exhaust a 8 GB machine. Chunking is value-identical because every
        # sampler fills C-order, and the generator state is saved and restored
        # so the second pass replays exactly the same draws.
        CH = 5_000
        skewnorm_case = label == "skew-normal(a=6)"

        def _draw(rows, src):
            if skewnorm_case:
                return stats.skewnorm.rvs(6, size=(rows, n), random_state=src)
            return sampler((rows, n))

        def _fresh():
            return np.random.RandomState(11) if skewnorm_case else None

        state = None if skewnorm_case else g.bit_generator.state
        src = _fresh()

        # Pass 1: global mean and standard deviation by streaming sums.
        s1 = s2 = 0.0
        cnt = 0
        left = reps
        while left > 0:
            m_ = min(CH, left)
            b = _draw(m_, src)
            s1 += float(b.sum())
            s2 += float(np.square(b).sum())
            cnt += b.size
            left -= m_
            del b
        gmean = s1 / cnt
        gstd = math.sqrt(max(s2 / cnt - gmean * gmean, 0.0))

        # Pass 2: replay the identical draws, standardise, accumulate Sharpes.
        if skewnorm_case:
            src = _fresh()
        else:
            g.bit_generator.state = state
        mu_target = 0.06                       # per-period mean -> SR = 0.06
        sr_parts, head = [], []
        head_left = 2_000_000
        left = reps
        while left > 0:
            m_ = min(CH, left)
            b = (_draw(m_, src) - gmean) / gstd
            if head_left > 0:
                take = min(head_left, b.size)
                head.append(b.ravel()[:take].copy())
                head_left -= take
            xb = b + mu_target
            sr_parts.append(xb.mean(axis=1) / xb.std(axis=1, ddof=1))
            left -= m_
            del b, xb
        sr_hat = np.concatenate(sr_parts)
        del sr_parts

        if skewnorm_case:
            headv = np.concatenate(head)
            skew_t = float(stats.skew(headv))
            kurt_t = float(stats.kurtosis(headv)) + 3.0
            del headv
        del head
        emp_sd = float(np.std(sr_hat, ddof=1))
        sr_true = mu_target
        predicted = _sr_se(sr_true, n, skew_t, kurt_t)
        rows.append((label, skew_t, kurt_t, emp_sd, predicted))

    for i, (label, sk, ku, emp, pred) in enumerate(rows):
        reg.close(
            f"S-0{i + 1}", SEC,
            r"PSR denominator $\sqrt{1-\hat\gamma_3\widehat{SR}"
            r"+\frac{\hat\gamma_4-1}{4}\widehat{SR}^2}$ (over $\sqrt{n-1}$) is "
            rf"the true standard error of $\widehat{{SR}}$ -- {label}",
            f"{reps:,} independent samples of n={n}; empirical sd of the "
            f"Sharpe estimate vs the formula (skew {sk:.2f}, kurtosis {ku:.2f})",
            emp, pred, rtol=0.02,
            note="Confirms the formula as written in the report, PROVIDED "
                 "gamma_4 is non-excess kurtosis.",
        )

    # The kurtosis-convention trap. Its size scales with the PER-PERIOD Sharpe,
    # so it is invisible at daily frequency and material at monthly/annual.
    ku_t = 6.0
    conv_rows = []
    for freq, per_year in (("daily", 252), ("weekly", 52),
                           ("monthly", 12), ("quarterly", 4)):
        sr_p = 0.8 / math.sqrt(per_year)          # annualised Sharpe 0.8
        correct = _sr_se(sr_p, 1000, 0.0, ku_t)
        wrong = _sr_se(sr_p, 1000, 0.0, ku_t - 3.0)
        conv_rows.append((freq, sr_p, wrong / correct - 1))
    # The skewness term, by contrast, bites even at daily frequency.
    sr_d = 0.8 / math.sqrt(252)
    skew_effect = _sr_se(sr_d, 1000, -0.8, ku_t) / _sr_se(sr_d, 1000, 0.0, ku_t) - 1
    reg.add(
        "S-04", SEC,
        r"$\gamma_4$ in the PSR formula must be NON-EXCESS kurtosis, and the "
        r"size of the error depends on the return frequency",
        "recompute the Sharpe standard error under both kurtosis conventions "
        "across sampling frequencies, at a fixed annualised Sharpe of 0.8",
        "identical results under either convention",
        "; ".join(f"{f}: {d:+.1%}" for f, _, d in conv_rows),
        "FLAG",
        r"Section 2.8 defines $\hat\gamma_4$ only as 'kurtosis'. Both conventions "
        r"are in common use and \texttt{scipy.stats.kurtosis} returns the EXCESS "
        r"value by default, so the natural implementation is the wrong one. The "
        r"error scales with the SQUARE of the per-period Sharpe, which makes it "
        rf"nearly invisible on daily data ({conv_rows[0][2]:+.1%}) but material "
        rf"on monthly data ({conv_rows[2][2]:+.1%}) and worse on quarterly "
        rf"({conv_rows[3][2]:+.1%}). Since fund-style track records are almost "
        r"always evaluated monthly, the bug would surface precisely when the "
        r"stakes are highest -- and it understates the standard error, which "
        r"inflates PSR and DSR and lets strategies through the promotion gate "
        r"that should have been rejected. The direction of the error is the "
        r"dangerous one. Separately, note that the SKEWNESS term dominates at "
        rf"daily frequency: a realistic skew of $-0.8$ changes the standard "
        rf"error by {skew_effect:+.1%} on daily data, an order of magnitude more "
        r"than the kurtosis term. Fix: define $\gamma_4=E[(r-\mu)^4]/\sigma^4$ "
        r"explicitly in the report, and unit-test that a Gaussian sample gives "
        r"$\gamma_4\approx3$ and that the denominator reduces to "
        r"$\sqrt{1+\widehat{SR}^2/2}$.",
        table=[{"freq": f, "sr_per_period": sp, "rel_err": d}
               for f, sp, d in conv_rows],
        skew_effect_daily=skew_effect,
    )

    # Gaussian reduction: denominator -> sqrt(1 + SR^2/2) (Lo 2002).
    sr = 0.06
    full = math.sqrt(1 - 0.0 * sr + (3.0 - 1) / 4 * sr**2)
    lo = math.sqrt(1 + sr**2 / 2)
    reg.close(
        "S-05", SEC,
        r"Under normality the PSR denominator reduces exactly to Lo (2002)'s "
        r"$\sqrt{1+\widehat{SR}^2/2}$",
        "algebraic reduction with skew=0, kurtosis=3",
        lo, full, rtol=1e-12,
        note=r"(gamma_4 - 1)/4 = (3-1)/4 = 1/2. A useful invariant to assert in "
             r"code: with Gaussian inputs the general formula must equal the "
             r"simple one.",
    )


def _psr(reg: Registry) -> None:
    """PSR is a calibrated probability: P(true SR > benchmark)."""
    g = rng(502)
    n = 1250
    sr_benchmark = 0.0

    def psr(x: np.ndarray, sr_star: float) -> float:
        sr = float(np.mean(x) / np.std(x, ddof=1))
        sk = float(stats.skew(x))
        ku = float(stats.kurtosis(x)) + 3.0
        return float(stats.norm.cdf((sr - sr_star) / _sr_se(sr, len(x), sk, ku)))

    # Calibration: under the null (true SR = benchmark) PSR must be Uniform(0,1).
    reps = 40_000
    vals = np.empty(reps)
    for i in range(reps):
        vals[i] = psr(g.standard_normal(n), sr_benchmark)
    ks = stats.kstest(vals, "uniform")
    reg.truth(
        "S-06", SEC,
        r"PSR is a calibrated probability: under the null $SR=SR^*$ it is "
        r"uniformly distributed",
        f"{reps:,} null samples of n={n}; Kolmogorov-Smirnov test against "
        f"Uniform(0,1)",
        ks.pvalue > 0.01,
        "KS p-value > 0.01 (cannot reject uniformity)",
        f"KS statistic {ks.statistic:.4f}, p = {ks.pvalue:.3f}; "
        f"empirical P(PSR > 0.95) = {np.mean(vals > 0.95):.4f} "
        f"(nominal 0.05)",
        "This is the property that makes PSR usable as a promotion gate: a "
        "0.95 threshold really does admit 5% of worthless strategies, not "
        "some unknown fraction. Verified rather than assumed.",
        ks_stat=float(ks.statistic), ks_p=float(ks.pvalue),
        false_positive=float(np.mean(vals > 0.95)),
    )


def _fst_expected_max(n_trials: int, var_sr: float = 1.0) -> float:
    """Bailey-Lopez de Prado False Strategy Theorem approximation."""
    gamma = 0.5772156649015329            # Euler-Mascheroni
    a = stats.norm.ppf(1 - 1 / n_trials)
    b = stats.norm.ppf(1 - 1 / (n_trials * math.e))
    return math.sqrt(var_sr) * ((1 - gamma) * a + gamma * b)


def _false_strategy_theorem(reg: Registry) -> None:
    """E[max SR] over N independent trials, vs direct Monte Carlo."""
    g = rng(503)
    rows = []
    for N in (10, 50, 100, 500, 1000, 5000, 10000):
        approx = _fst_expected_max(N)
        # Direct MC: expected maximum of N i.i.d. standard normals.
        reps = max(4000, min(40000, 4_000_000 // N))
        # Chunked so the peak allocation stays near 16 MB regardless of N.
        # Row-major fill keeps the stream identical to one big draw.
        _chunk = max(1, 2_000_000 // N)
        _acc, _left = 0.0, reps
        while _left > 0:
            _m = min(_chunk, _left)
            _acc += float(g.standard_normal((_m, N)).max(axis=1).sum())
            _left -= _m
        mc = _acc / reps
        rows.append((N, approx, mc, approx / mc - 1))

    worst = max(abs(r[3]) for r in rows)
    worst_big = max(abs(r[3]) for r in rows if r[0] >= 50)
    reg.truth(
        "S-07", SEC,
        r"False Strategy Theorem: $E[\max_N\widehat{SR}]\approx\sqrt{V[\widehat{SR}]}"
        r"[(1-\gamma)\Phi^{-1}(1-\frac1N)+\gamma\Phi^{-1}(1-\frac1{N e})]$",
        "compare the closed form against direct Monte Carlo of the maximum of "
        "N i.i.d. standard normals, N from 10 to 10,000",
        worst_big < 0.02,
        "closed form within 2% of Monte Carlo for N >= 50",
        "; ".join(f"N={N}: formula {a:.3f} vs MC {m:.3f} ({d:+.1%})"
                  for N, a, m, d in rows),
        rf"The approximation is excellent across three orders of magnitude in "
        rf"N, and improves as N grows: the error is {rows[0][3]:+.1%} at N=10 "
        rf"but under 1\% for every N >= 100 and {rows[-1][3]:+.1%} at N=10,000. "
        r"Since the whole point of the theorem is large trial counts, it is "
        r"accurate exactly where it is used; the report need not caveat it, but "
        r"should not apply it to a handful of trials. Note $\gamma$ here is the "
        r"Euler-Mascheroni constant 0.5772, which the report states correctly "
        r"-- worth flagging only because $\gamma_3$ and $\gamma_4$ elsewhere in "
        r"the same section denote skewness and kurtosis, an unfortunate but "
        r"standard collision.",
        table=[{"N": N, "formula": a, "mc": m, "rel_err": d}
               for N, a, m, d in rows],
    )


def _dsr_headline(reg: Registry) -> None:
    """The report quotes: 1000 trials -> expected max Sharpe 3.26."""
    approx = _fst_expected_max(1000, var_sr=1.0)
    g = rng(504)
    # Chunked: a single (200_000, 1000) draw is a 1.6 GB allocation.
    # standard_normal fills C-order, so chunking by rows consumes the
    # same stream and yields the same values.
    _acc, _n = 0.0, 0
    for _ in range(40):
        _acc += float(g.standard_normal((5_000, 1000)).max(axis=1).sum())
        _n += 5_000
    mc = _acc / _n
    reg.close(
        "S-08", SEC,
        r"Report's headline claim: with $E[SR]=0$, $V[SR]=1$, after 1{,}000 "
        r"independent backtests the expected maximum Sharpe is \textbf{3.26}",
        "evaluate the False Strategy Theorem at N=1000, and confirm by direct "
        "Monte Carlo (200k replications of the max of 1000 normals)",
        3.26, approx, atol=0.01, rtol=0,
        note=f"Formula gives {approx:.4f}; independent Monte Carlo gives "
             f"{mc:.4f}. The quoted figure is correct as stated. Its practical "
             f"meaning is worth spelling out in the report: an operator who "
             f"tries 1,000 parameter combinations and reports the best one has "
             f"an expected Sharpe of 3.26 from PURE NOISE, so a raw Sharpe of "
             f"3 is evidence of a large search, not of skill.",
        mc=mc,
    )

    # How many trials does a solo operator actually run? Grid sweeps hit
    # thousands fast. Show the implied hurdle.
    rows = [(N, _fst_expected_max(N)) for N in (10, 100, 1000, 10000, 100000)]
    reg.add(
        "S-09", SEC,
        "The deflation hurdle rises with the number of trials, and a routine "
        "parameter sweep already implies thousands of trials",
        "expected maximum Sharpe under the null at realistic trial counts",
        "-",
        "; ".join(f"N={N:,}: hurdle SR {h:.2f}" for N, h in rows),
        "INFO",
        r"A three-parameter grid at 10 values each is 1,000 trials before any "
        r"variant selection; adding a universe choice and two signal variants "
        r"reaches $10^5$. At that point the null expects a maximum Sharpe of "
        rf"{rows[-1][1]:.2f}. This is why the report is right that section 2.8 "
        r"is the highest-ROI engineering in the plan -- and why the trial "
        r"registry must count EVERY configuration ever evaluated, including "
        r"abandoned ones, or N is understated and the deflation is worthless.",
        table=[{"N": N, "hurdle": h} for N, h in rows],
    )


def _mintrl(reg: Registry) -> None:
    """Minimum Track Record Length: solve PSR(n) = target for n."""
    sr, sk, ku = 0.5 / math.sqrt(252), 0.0, 3.0     # SR 0.5 annual, daily data
    target, sr_star = 0.95, 0.0

    def psr_of_n(n: float) -> float:
        return stats.norm.cdf((sr - sr_star) / _sr_se(sr, n, sk, ku)) - target

    n_star = brentq(psr_of_n, 10, 10_000_000)
    # Closed form: n = 1 + (1 - g3*SR + (g4-1)/4*SR^2) * (z_target/(SR-SR*))^2
    z = stats.norm.ppf(target)
    closed = 1 + (1 - sk * sr + (ku - 1) / 4 * sr**2) * (z / (sr - sr_star)) ** 2
    reg.close(
        "S-10", SEC,
        r"Minimum Track Record Length: solving PSR $=$ target for $n$ gives "
        r"$n^*=1+\left[1-\gamma_3 SR+\frac{\gamma_4-1}{4}SR^2\right]"
        r"\left(\frac{z_{target}}{SR-SR^*}\right)^2$",
        "root-find PSR(n) = 0.95 numerically and compare to the closed form",
        closed, n_star, rtol=1e-6,
        note=f"For an annualised Sharpe of 0.5 against a zero benchmark, "
             f"95% confidence requires {n_star:.0f} daily observations = "
             f"{n_star / 252:.1f} years. The report mentions MinTRL without "
             f"this number, which is the one that matters: a solo operator "
             f"with three years of paper trading cannot statistically "
             f"distinguish a Sharpe-0.5 strategy from noise.",
        years=n_star / 252,
    )

    rows = []
    for sr_ann in (0.3, 0.5, 0.8, 1.0, 1.5, 2.0):
        s = sr_ann / math.sqrt(252)
        n_req = 1 + (1 + (3 - 1) / 4 * s**2) * (z / s) ** 2
        rows.append((sr_ann, n_req / 252))
    reg.add(
        "S-11", SEC,
        "Track record length required for 95% confidence scales as $1/SR^2$",
        "closed-form MinTRL across annualised Sharpe ratios, daily data, "
        "Gaussian returns",
        "-",
        "; ".join(f"SR {s:.1f}: {y:.1f} yr" for s, y in rows),
        "INFO",
        r"This table belongs in the report next to section 4.8's 'realistic "
        r"solo expectation is net Sharpe 0.3-0.8'. At a true Sharpe of 0.5 it "
        rf"takes {rows[1][1]:.0f} years of live data to be 95\% sure the "
        rf"strategy is not noise; at 0.3 it takes {rows[0][1]:.0f} years. The "
        r"honest conclusion is that live P\&L will never be the arbiter on a "
        r"solo timescale, which is exactly why the ex-ante controls (PBO, DSR, "
        r"purged CV) have to carry the weight.",
        table=[{"sharpe": s, "years": y} for s, y in rows],
    )


# ---------------------------------------------------------------- PBO / CSCV
def _pbo(M: np.ndarray, S: int = 12) -> float:
    """Probability of Backtest Overfitting via Combinatorially Symmetric CV.

    M is (T observations x N strategies). Split the rows into S disjoint blocks,
    take every way of choosing S/2 blocks as the training set, pick the
    in-sample best strategy, and record its out-of-sample rank. PBO is the
    fraction of splits where that strategy lands below the OOS median.
    """
    T, N = M.shape
    T = (T // S) * S
    blocks = np.array_split(M[:T], S)
    below = 0
    total = 0
    for tr in combinations(range(S), S // 2):
        te = tuple(i for i in range(S) if i not in tr)
        A = np.concatenate([blocks[i] for i in tr])
        B = np.concatenate([blocks[i] for i in te])
        sr_is = A.mean(axis=0) / (A.std(axis=0, ddof=1) + 1e-300)
        sr_oos = B.mean(axis=0) / (B.std(axis=0, ddof=1) + 1e-300)
        best = int(np.argmax(sr_is))
        # Relative rank of the IS-best strategy in the OOS ordering.
        rank = float(stats.rankdata(sr_oos)[best]) / (N + 1)
        below += int(rank < 0.5)
        total += 1
    return below / total


def _pbo_cscv(reg: Registry) -> None:
    """PBO calibration, power, and -- the part the report omits -- its own
    sampling variability."""
    g = rng(505)
    T, N, S = 1000, 40, 12
    n_splits = math.comb(S, S // 2)

    # --- calibration under the null, averaged over many datasets ---------
    # PBO computed on ONE performance matrix is a single draw; the null claim
    # is about its expectation, so it must be averaged over datasets.
    datasets = 40
    null_vals = np.array([_pbo(g.standard_normal((T, N)) * 0.01, S)
                          for _ in range(datasets)])
    mean_null = float(null_vals.mean())
    sd_null = float(null_vals.std(ddof=1))
    se_null = sd_null / math.sqrt(datasets)

    reg.truth(
        "S-12", SEC,
        r"PBO via CSCV is calibrated: under the null that no strategy has an "
        r"edge, $E[\text{PBO}]=0.5$",
        f"T={T}, N={N} strategies, S={S} blocks = {n_splits:,} symmetric "
        f"splits; averaged over {datasets} independent noise datasets",
        abs(mean_null - 0.5) < 3 * se_null,
        "mean PBO = 0.50",
        f"mean PBO = {mean_null:.3f} +/- {se_null:.3f} (standard error)",
        "Confirms the estimator is unbiased under the null. Note this required "
        "averaging over datasets -- see S-14 for why that distinction matters "
        "operationally.",
        mean_null=mean_null, se_null=se_null,
    )

    # --- power: a genuine edge must drive PBO to zero --------------------
    edged = g.standard_normal((T, N)) * 0.01
    edged[:, 7] += 0.01 * 0.9            # ~0.9 daily SR units -> unmistakable
    pbo_edge = _pbo(edged, S)

    # The realistic case: a grid sweep over one signal, so the variants share a
    # common component and differ only by noise.
    common = g.standard_normal((T, 1)) * 0.004
    sweep = common + g.standard_normal((T, N)) * 0.010
    pbo_sweep = _pbo(sweep, S)

    reg.truth(
        "S-13", SEC,
        r"PBO has power: a strategy with a genuine persistent edge drives PBO "
        r"to zero, while a pure parameter sweep does not",
        f"same geometry; one case with a real edge planted in column 7, one "
        f"case a correlated {N}-variant sweep over a single signal",
        pbo_edge < 0.05 and pbo_sweep > 0.2,
        "PBO ~ 0 with a real edge; PBO ~ 0.5 for a noise sweep",
        f"genuine edge PBO = {pbo_edge:.3f}; correlated parameter sweep "
        f"PBO = {pbo_sweep:.3f}",
        r"The second case is the one a solo operator actually faces: a grid "
        r"sweep over one signal, where every variant shares a common component "
        r"and differs only by noise. PBO correctly reports that selecting the "
        r"best variant generalises no better than a coin flip. Note PBO and DSR "
        r"answer different questions -- DSR asks 'is this Sharpe real given N "
        r"trials?', PBO asks 'does my SELECTION PROCEDURE generalise?' -- so "
        r"the report is right to gate promotion on both.",
        pbo_edge=pbo_edge, pbo_sweep=pbo_sweep,
    )

    # --- the omitted caveat: PBO is itself a very noisy statistic --------
    rows = []
    for (t_, n_) in ((1000, 40), (2500, 40), (1000, 200), (5000, 200)):
        vals = np.array([_pbo(rng(50500 + t_ + n_ + k)
                              .standard_normal((t_, n_)) * 0.01, S)
                         for k in range(24)])
        rows.append((t_, n_, float(vals.mean()), float(vals.std(ddof=1))))

    reg.add(
        "S-14", SEC,
        "A PBO value computed from a single backtest matrix has very large "
        "sampling error and cannot be read as a precise number",
        "24 independent null datasets at each (T, N); report the spread of the "
        "resulting PBO estimates",
        "PBO should concentrate near 0.5 under the null",
        "; ".join(f"T={t_}, N={n_}: mean {m:.2f}, sd {s:.2f}"
                  for t_, n_, m, s in rows),
        "FLAG",
        r"The report presents PBO as a scalar to be compared against a "
        r"threshold. In practice, at the data sizes a solo operator has, the "
        rf"estimator's own standard deviation under the null is around "
        rf"{rows[0][3]:.2f} at T={rows[0][0]}, N={rows[0][1]}. Two "
        r"honest runs of the same worthless strategy family can therefore "
        r"return PBO $=0.25$ and PBO $=0.75$. Consequences for the build: "
        r"(i) do not gate promotion on a single PBO point estimate; "
        r"(ii) report a bootstrap confidence interval alongside it; "
        r"(iii) prefer longer histories and larger strategy families, since the "
        rf"spread falls to {rows[-1][3]:.2f} at T={rows[-1][0]}, N={rows[-1][1]}. "
        r"This does not weaken the case for PBO -- it is still the right "
        r"diagnostic -- but a threshold rule written against a noisy statistic "
        r"is a false gate, and false gates are worse than no gate because they "
        r"are trusted.",
        table=[{"T": t_, "N": n_, "mean": m, "sd": s} for t_, n_, m, s in rows],
    )


# ---------------------------------------------------------------- purged CV
def _purged_cv(reg: Registry) -> None:
    """Demonstrate that standard k-fold CV leaks with overlapping labels, and
    that purging plus embargo removes the leak.

    Construction, with ZERO true predictability by design:
      returns r_t are i.i.d.
      feature  X_t = sum of the h returns ENDING at t      (backward window)
      label    y_t = sign of the h returns STARTING at t+1 (forward window)
    The two windows are disjoint, so X_t carries no information about y_t.
    But X_{t'} for a nearby t' OVERLAPS the label window of t, so a training
    sample adjacent to a test sample leaks. That is precisely the failure mode
    purging exists to prevent.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import KFold

    g = rng(506)
    n, h = 3000, 20
    reps = 10
    shuf_auc, block_auc, purged_auc = [], [], []

    for rep in range(reps):
        r = g.standard_normal(n + 2 * h)
        back = np.array([r[t: t + h].sum() for t in range(n)])
        fwd = np.array([r[t + h: t + 2 * h].sum() for t in range(n)])
        # Lagged copies so the forest has near-duplicate rows to memorise.
        X = np.column_stack([back, np.roll(back, 1), np.roll(back, 2),
                             np.roll(back, 3), np.roll(back, 5)])[h:]
        y = (fwd > 0).astype(int)[h:]
        m = len(y)
        idx = np.arange(m)

        def score(tr, te, sink):
            if len(tr) < 50 or len(np.unique(y[tr])) < 2 \
                    or len(np.unique(y[te])) < 2:
                return
            clf = RandomForestClassifier(n_estimators=80, min_samples_leaf=3,
                                         n_jobs=1, random_state=0)
            clf.fit(X[tr], y[tr])
            sink.append(roc_auc_score(y[te], clf.predict_proba(X[te])[:, 1]))

        # (a) SHUFFLED k-fold -- sklearn's KFold(shuffle=True), the naive
        #     default. Train and test rows are interleaved throughout, so
        #     almost every test row has a temporal neighbour in training.
        for tr, te in KFold(5, shuffle=True, random_state=rep).split(idx):
            score(tr, te, shuf_auc)

        # (b) contiguous blocked folds, no purging: leakage survives only at
        #     the two fold boundaries.
        folds = np.array_split(idx, 5)
        for fold in folds:
            score(np.setdiff1d(idx, fold), fold, block_auc)

        # (c) contiguous folds WITH purge + embargo.
        embargo = int(0.01 * m)
        for fold in folds:
            lo, hi = fold[0] - h - embargo, fold[-1] + h + embargo
            drop = np.arange(max(lo, 0), min(hi + 1, m))
            score(np.setdiff1d(idx, drop), fold, purged_auc)

    def ms(a):
        return float(np.mean(a)), float(np.std(a, ddof=1) / math.sqrt(len(a)))

    m_shuf, se_shuf = ms(shuf_auc)
    m_block, se_block = ms(block_auc)
    m_purge, se_purge = ms(purged_auc)

    ok = ((m_shuf - 0.5) > 3 * se_shuf
          and abs(m_purge - 0.5) < 3 * se_purge)
    reg.truth(
        "S-15", SEC,
        r"Shuffled k-fold CV manufactures skill out of nothing when labels "
        r"overlap in time; contiguous folds with purging and embargo do not",
        f"{reps} replications x 5 folds on data with ZERO true predictability "
        f"BY CONSTRUCTION (feature window and label window are disjoint, "
        f"h={h}); random forest, AUC",
        ok,
        "shuffled CV AUC significantly above 0.5; purged CV AUC "
        "indistinguishable from 0.5",
        f"shuffled k-fold {m_shuf:.4f} +/- {se_shuf:.4f}; "
        f"contiguous blocks (no purge) {m_block:.4f} +/- {se_block:.4f}; "
        f"purged + embargoed {m_purge:.4f} +/- {se_purge:.4f}",
        r"This reproduces the report's section 2.12 claim end to end on data "
        r"with provably zero signal. Three points the report should absorb. "
        rf"First, the naive pipeline reports AUC {m_shuf:.3f} against a truth "
        r"of 0.5, with a small standard error -- it looks significant. Second, "
        r"the leak requires no look-ahead in the feature: the feature and label "
        r"windows are disjoint by construction, and the leak comes entirely "
        r"from neighbouring TRAINING rows sharing the test row's label window. "
        r"An audit for 'no future data in features' is therefore necessary but "
        r"not sufficient, which is the single most important practical "
        r"consequence. Third, simply using contiguous folds instead of shuffled "
        rf"ones already removes most of the damage ({m_block:.3f}), because "
        r"only the fold boundaries leak; purging and embargo clean up the "
        r"remainder. Blocking is the cheap 90\% fix, purging is the rest.",
        shuffled_auc=m_shuf, blocked_auc=m_block, purged_auc=m_purge,
        shuffled_se=se_shuf, purged_se=se_purge,
    )
