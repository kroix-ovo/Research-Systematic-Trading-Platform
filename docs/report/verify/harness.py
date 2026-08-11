"""Deterministic verification harness for the quant research report.

Every mathematical claim in the report is re-derived here either symbolically
(sympy), numerically (closed form vs. optimiser), or by Monte Carlo against a
known generating process. Nothing is asserted on authority.

Status semantics
----------------
PASS  the claim is correct exactly as written in the report.
FLAG  the claim is correct only under an unstated assumption, is imprecise,
      or is an approximation whose error is material at plausible parameters.
      The report text must be amended to state the caveat.
FAIL  the claim is wrong as written and must be corrected.
INFO  a derived quantity recorded for the report; not a pass/fail claim.

All randomness is seeded. Re-running reproduces byte-identical results.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import numpy as np

# Master seed. Every module derives its streams from this so the whole suite is
# reproducible from one number.
MASTER_SEED = 20260811

OUT_DIR = Path(__file__).resolve().parent.parent / "out"


def rng(stream: int) -> np.random.Generator:
    """Independent, reproducible generator for a given stream id."""
    return np.random.default_rng([MASTER_SEED, stream])


@dataclass
class Check:
    cid: str
    section: str
    claim: str
    method: str
    expected: str
    observed: str
    status: str
    note: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


class Registry:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def add(
        self,
        cid: str,
        section: str,
        claim: str,
        method: str,
        expected: Any,
        observed: Any,
        status: str,
        note: str = "",
        **payload: Any,
    ) -> Check:
        c = Check(
            cid=cid,
            section=section,
            claim=claim,
            method=method,
            expected=_fmt(expected),
            observed=_fmt(observed),
            status=status,
            note=note,
            payload=payload,
        )
        self.checks.append(c)
        return c

    def close(
        self,
        cid: str,
        section: str,
        claim: str,
        method: str,
        expected: float,
        observed: float,
        rtol: float = 1e-8,
        atol: float = 0.0,
        note: str = "",
        **payload: Any,
    ) -> Check:
        """Register a numeric-agreement check."""
        ok = bool(np.isclose(expected, observed, rtol=rtol, atol=atol))
        return self.add(
            cid,
            section,
            claim,
            method,
            expected,
            observed,
            "PASS" if ok else "FAIL",
            note or f"agreement to rtol={rtol:g}, atol={atol:g}",
            **payload,
        )

    def truth(
        self,
        cid: str,
        section: str,
        claim: str,
        method: str,
        ok: bool,
        expected: Any,
        observed: Any,
        note: str = "",
        **payload: Any,
    ) -> Check:
        return self.add(
            cid, section, claim, method, expected, observed,
            "PASS" if ok else "FAIL", note, **payload,
        )

    # -- reporting -------------------------------------------------------
    def summary(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.checks:
            out[c.status] = out.get(c.status, 0) + 1
        return out

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "master_seed": MASTER_SEED,
                    "summary": self.summary(),
                    "checks": [asdict(c) for c in self.checks],
                },
                indent=2,
                default=_json_default,
            )
        )


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def _fmt(v: Any) -> str:
    if isinstance(v, str):
        return v
    if isinstance(v, (bool, np.bool_)):
        return "true" if v else "false"
    if isinstance(v, (int, np.integer)):
        return f"{int(v):,}"
    if isinstance(v, (float, np.floating)):
        f = float(v)
        if f != 0 and (abs(f) < 1e-4 or abs(f) >= 1e6):
            return f"{f:.4e}"
        return f"{f:.6g}"
    if isinstance(v, (list, tuple, np.ndarray)):
        a = np.asarray(v, dtype=float).ravel()
        return "[" + ", ".join(f"{x:.4g}" for x in a[:6]) + ("...]" if a.size > 6 else "]")
    return str(v)


# --------------------------------------------------------------------------
# Shared simulation utilities
# --------------------------------------------------------------------------

def gbm_ohlc(g: np.random.Generator, n_days: int, steps_per_day: int,
             sigma_daily: float, mu_daily: float = 0.0,
             chunk: int = 2000) -> dict[str, np.ndarray]:
    """Simulate intraday GBM and return daily OHLC log-ratios.

    Generated in chunks: the full (n_days, steps) path matrix would be tens of
    gigabytes at the sample sizes needed to resolve a 1% bias. Returns the four
    log-ratios the range estimators consume, all relative to the day's open.
    """
    dt = 1.0 / steps_per_day
    drift = (mu_daily - 0.5 * sigma_daily**2) * dt
    diff = sigma_daily * math.sqrt(dt)
    hi, lo, cl = [], [], []
    done = 0
    while done < n_days:
        m = min(chunk, n_days - done)
        z = g.standard_normal((m, steps_per_day))
        logs = np.cumsum(drift + diff * z, axis=1)
        # The open is log 0 by construction; include it in the range so H >= O
        # and L <= O, matching how a real bar is formed.
        hi.append(np.maximum(logs.max(axis=1), 0.0))
        lo.append(np.minimum(logs.min(axis=1), 0.0))
        cl.append(logs[:, -1])
        done += m
    h, l, c = np.concatenate(hi), np.concatenate(lo), np.concatenate(cl)
    # Log ratios: o is the origin, so ln(H/O)=h, ln(C/O)=c, etc.
    return {
        "hl": h - l,      # ln(H/L)
        "co": c,          # ln(C/O)
        "ho": h,          # ln(H/O)
        "lo": l,          # ln(L/O)
        "hc": h - c,      # ln(H/C)
        "lc": l - c,      # ln(L/C)
    }


def ar1(g: np.random.Generator, n: int, rho: float, sd: float = 1.0,
        mean: float = 0.0) -> np.ndarray:
    """Stationary AR(1) via an IIR filter (exact, and far faster than a loop)."""
    from scipy.signal import lfilter

    eps = g.normal(0.0, sd, n)
    # Seed the filter at the stationary variance so there is no burn-in.
    zi = np.array([rho * g.normal(0.0, sd / math.sqrt(1 - rho**2))])
    x, _ = lfilter([1.0], [1.0, -rho], eps, zi=zi)
    return x + mean


def sharpe(x: np.ndarray, ddof: int = 1) -> float:
    return float(np.mean(x) / np.std(x, ddof=ddof))


def max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    return float(np.min(equity / peak - 1.0))
