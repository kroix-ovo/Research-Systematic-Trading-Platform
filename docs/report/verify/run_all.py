"""Run the complete verification suite and emit results for the report.

    python3 run_all.py

Writes ../out/verification_results.json and prints a summary table.
Fully deterministic: same seeds in, same numbers out.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import Registry, OUT_DIR, MASTER_SEED   # noqa: E402

MODULES = [
    ("v01_returns_vol", "Returns, volatility estimation, annualisation"),
    ("v02_sizing", "Volatility targeting and the Kelly criterion"),
    ("v03_portfolio", "Portfolio construction"),
    ("v04_risk", "Risk metrics: VaR, CVaR, Cornish-Fisher"),
    ("v05_validation", "Statistical validation: PSR, DSR, PBO, purged CV"),
    ("v06_execution", "Transaction costs, market impact, microstructure"),
    ("v07_meanrev", "Pairs trading: OU, cointegration, Kalman"),
    ("v08_ml_regime", "Regime detection and the ML toolkit"),
    ("v09_report_arithmetic", "Report-internal arithmetic and consistency"),
]

STATUS_ORDER = ["FAIL", "FLAG", "PASS", "INFO"]


def main() -> int:
    reg = Registry()
    t0 = time.time()
    for mod_name, label in MODULES:
        t = time.time()
        print(f"  running {mod_name:24s} {label} ...", flush=True)
        mod = __import__(mod_name)
        before = len(reg.checks)
        mod.run(reg)
        print(f"    {len(reg.checks) - before:3d} checks "
              f"in {time.time() - t:6.1f}s", flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    reg.dump(OUT_DIR / "verification_results.json")

    summary = reg.summary()
    total = len(reg.checks)
    print("\n" + "=" * 78)
    print(f"VERIFICATION SUITE COMPLETE  --  {total} checks in "
          f"{time.time() - t0:.1f}s  (master seed {MASTER_SEED})")
    print("=" * 78)
    for s in STATUS_ORDER:
        if s in summary:
            print(f"  {s:5s} {summary[s]:3d}")

    for s in ("FAIL", "FLAG"):
        items = [c for c in reg.checks if c.status == s]
        if not items:
            continue
        head = ("ERRORS FOUND IN THE REPORT" if s == "FAIL"
                else "CLAIMS REQUIRING A STATED CAVEAT")
        print(f"\n{head}:")
        for c in items:
            print(f"  [{c.cid:8s}] {c.section}")
            print(f"             {c.claim[:100]}")

    print(f"\nWrote {OUT_DIR / 'verification_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
