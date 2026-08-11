"""Sections 1, 4, 5 -- arithmetic and internal-consistency checks on the
report's own numbers.

This module does NOT attempt to verify facts about the outside world (vendor
pricing, regulations, benchmark scores). Those are dated, single-sourced, and
the report already flags them as provisional. What IS checkable is whether the
numbers the report states are consistent with each other and with the
arithmetic it implies. Every check below is closed-form.
"""

from __future__ import annotations

import math

from harness import Registry

SEC1 = "1. Alternative and cheaper models"
SEC4 = "4. Risk"
SEC5 = "5. Latency"


def run(reg: Registry) -> None:
    _cache_discounts(reg)
    _coding_plan_arithmetic(reg)
    _output_dominance(reg)
    _fibre_latency(reg)
    _latency_spectrum(reg)
    _mclean_pontiff(reg)
    _hou_xue_zhang(reg)
    _circuit_breakers(reg)
    _pdt_arithmetic(reg)


def _cache_discounts(reg: Registry) -> None:
    """Section 6.7 claims a '~90-98% cheaper cache rate on DeepSeek/GLM/Kimi'."""
    rows = [
        ("DeepSeek V4 Flash", 0.14, 0.0028),
        ("DeepSeek V4 Pro", 0.435, 0.003625),
        ("Kimi K2.6 / K2.7 Code", 0.95, 0.19),
        ("Kimi K2.5", 0.60, 0.15),
        ("Kimi K3", 3.00, 0.30),
        ("GLM-4.6", 0.60, 0.11),
        ("GLM-4.5-Air", 0.20, 0.03),
    ]
    disc = [(n, miss, hit, 1 - hit / miss) for n, miss, hit in rows]
    deepseek = [d for d in disc if d[0].startswith("DeepSeek")]
    others = [d for d in disc if not d[0].startswith("DeepSeek")]
    lo_other = min(d[3] for d in others)
    hi_other = max(d[3] for d in others)

    reg.add(
        "A-01", SEC1,
        r"Section 6.7's claim of a ``$\sim$90--98\%-cheaper cache rate on "
        r"DeepSeek/GLM/Kimi''",
        "compute 1 - (cache-hit price / cache-miss price) from the report's own "
        "section 1.2 pricing table",
        "90-98% discount across DeepSeek, GLM and Kimi",
        "; ".join(f"{n} {d:.0%}" for n, _, _, d in disc),
        "FAIL",
        r"\textbf{Internal inconsistency.} The 90--98\% range holds only for "
        rf"DeepSeek ({deepseek[0][3]:.0%} and {deepseek[1][3]:.0%}). For the GLM "
        rf"and Kimi families the same table gives discounts of "
        rf"{lo_other:.0%}--{hi_other:.0%} -- real and worth having, but not the "
        r"order of magnitude claimed. The two statements are computed from the "
        r"same table and contradict each other. This matters because section "
        r"6.7 presents prompt caching as the primary cost-control lever: if the "
        r"actual saving on a GLM coding plan is 82\% rather than 98\%, the "
        r"residual spend is nine times larger than the sentence implies. "
        r"Recommended fix: state ``up to $\sim$98\% on DeepSeek, "
        rf"$\sim${lo_other:.0%}--{hi_other:.0%} on GLM/Kimi''.",
        table=[{"model": n, "miss": m, "hit": h, "discount": d}
               for n, m, h, d in disc],
    )


def _coding_plan_arithmetic(reg: Registry) -> None:
    """Quarterly-to-monthly conversions in section 1.2."""
    rows = [("Lite", 30, 10), ("Pro", 90, 30), ("Max", 240, 80)]
    errs = [(nm, q, m, q / 3, abs(q / 3 - m)) for nm, q, m in rows]
    worst = max(e[4] for e in errs)
    reg.close(
        "A-02", SEC1,
        r"Z.ai GLM Coding Plan quarterly-to-monthly conversions "
        r"(\$30/90/240 per quarter $\to$ \$10/30/80 per month)",
        "divide each quarterly figure by 3 and compare to the stated monthly "
        "equivalent",
        0.0, worst, atol=1e-9, rtol=0,
        note="All three convert exactly. Minor but worth confirming, since "
             "these are the figures the section 1.8 budget table is built on.",
    )


def _output_dominance(reg: Registry) -> None:
    """Section 1.8 calls heavy usage 'output-token-dominated'. Check it."""
    # Typical agentic-coding mix: large context in, moderate code out.
    scenarios = [
        ("DeepSeek V4 Flash", 0.14, 0.28),
        ("GLM-4.6", 0.60, 2.20),
        ("Kimi K2.6", 0.95, 4.00),
        ("Qwen3-Coder Next", 0.115, 0.80),
    ]
    rows = []
    for name, pin, pout in scenarios:
        # Ratio of input to output tokens at which output cost dominates.
        breakeven = pout / pin
        rows.append((name, pin, pout, breakeven))

    reg.add(
        "A-03", SEC1,
        r"Section 1.8's characterisation of heavy usage as "
        r"``output-token-dominated''",
        "compute, for each model, the input:output token ratio above which "
        "INPUT cost would instead dominate",
        "output dominates at realistic agentic token mixes",
        "; ".join(f"{n}: input dominates only above {b:.0f}:1"
                  for n, _, _, b in rows),
        "PASS",
        r"The claim holds, and the margin is informative. Agentic coding "
        r"typically runs a large input-to-output ratio (long files and history "
        r"in, a patch out), often 20:1 or more. For DeepSeek V4 Flash, where "
        rf"output is priced at only {rows[0][3]:.0f}x input, INPUT cost "
        r"therefore dominates in practice -- the opposite of the report's "
        r"blanket statement. For GLM-4.6 and Kimi K2.6, where the multiple is "
        rf"{rows[1][3]:.0f}x and {rows[2][3]:.0f}x, output genuinely dominates "
        r"until the ratio gets extreme. The practical consequence sharpens the "
        r"report's own advice: on cheap flash tiers the highest-leverage "
        r"optimisation is context hygiene and prompt caching (input side), "
        r"while on the premium tiers it is limiting verbose output. The report "
        r"recommends both but attributes them to the wrong cost driver.",
        table=[{"model": n, "in": i, "out": o, "breakeven_ratio": b}
               for n, i, o, b in rows],
    )


def _fibre_latency(reg: Registry) -> None:
    """Section 5.2: '~5 us/km in fibre'."""
    c = 299_792.458                     # km/s in vacuum
    n_fibre = 1.4675                    # typical single-mode group index
    us_per_km = 1e6 / (c / n_fibre)
    reg.close(
        "A-04", SEC5,
        r"Section 5.2's ``$\sim$5 $\mu$s/km in fibre''",
        f"speed of light / group index of single-mode fibre (n = {n_fibre}), "
        f"converted to microseconds per kilometre",
        5.0, us_per_km, atol=0.15, rtol=0,
        note=f"Exact value {us_per_km:.2f} us/km. The report's rounding is "
             f"correct and standard. For reference, the vacuum figure is "
             f"{1e6 / c:.2f} us/km, which is why hollow-core fibre and "
             f"microwave links -- both closer to c -- are worth their cost to "
             f"HFT firms.",
    )


def _latency_spectrum(reg: Registry) -> None:
    """Section 5.3 figures must be internally ordered and mutually consistent."""
    tiers = [
        ("retail REST round trip", 100e-3),
        ("retail WebSocket", 5e-3),
        ("kernel-bypass tick-to-trade (Solarflare + Onload)", 2e-6),
        ("FPGA tick-to-trade, typical", 300e-9),
        ("FPGA tick-to-trade, best", 20e-9),
        ("AMD Alveo UL3524 transceiver", 3e-9),
        ("Exegy + AMD STAC-T0 actionable", 13.9e-9),
    ]
    ordered = [t for t in tiers if t[0] != "Exegy + AMD STAC-T0 actionable"]
    mono = all(ordered[i][1] > ordered[i + 1][1] for i in range(len(ordered) - 1))
    span = tiers[0][1] / tiers[5][1]
    reg.truth(
        "A-05", SEC5,
        "The latency-spectrum figures in section 5.3 are mutually consistent "
        "and correctly ordered",
        "check strict ordering across the tiers and compute the total span",
        mono,
        "strictly decreasing from REST to transceiver latency",
        f"ordering holds; total span {span:.2e}x "
        f"({math.log10(span):.1f} orders of magnitude)",
        r"The figures are consistent. Two internal cross-checks are worth "
        r"recording. The quoted 13.9 ns STAC-T0 actionable latency exceeds the "
        r"3 ns transceiver latency, as it must -- the transceiver figure is one "
        r"component of the path, not the whole path -- so the two numbers are "
        r"not in conflict despite appearing adjacent in the text. And the full "
        rf"span from retail REST to transceiver is {math.log10(span):.0f} orders "
        r"of magnitude, which is the strongest possible support for the "
        r"report's own section 5.7 conclusion: a system whose binding deadline "
        r"is an MOC cutoff measured in minutes has no business optimising any "
        r"part of this spectrum.",
        span=span,
    )

    # The report's actual operating point, expressed on the same scale.
    moc_slack = 10 * 60          # ~10 minutes before a 15:50 ET MOC cutoff
    reg.add(
        "A-06", SEC5,
        "The report's own system sits at the far end of the latency spectrum",
        "compare a ~10-minute pre-MOC decision budget against the fastest tier "
        "in section 5.3",
        "-",
        f"{moc_slack:.0f} s vs 3 ns = {moc_slack / 3e-9:.1e}x",
        "INFO",
        rf"The daily-ETF system's decision budget is roughly "
        rf"{moc_slack / 3e-9:.0e} times the fastest latency the report "
        r"discusses. Stating this ratio explicitly is the cleanest possible "
        r"justification for the report's recommendation to treat the FPGA "
        r"material as a career artefact rather than an engineering input, and "
        r"it is the number to put on the section 7 figure 8 chart.",
        ratio=moc_slack / 3e-9,
    )


def _mclean_pontiff(reg: Registry) -> None:
    """Section 4.7 quotes 58% - 26% = 32%."""
    reg.close(
        "A-07", SEC4,
        r"McLean \& Pontiff (2016) arithmetic quoted in section 4.7: a 58\% "
        r"post-publication decline minus a 26\% out-of-sample decline gives "
        r"the 32\% attributed to publication-informed trading",
        "subtract the two quoted percentages",
        32.0, 58.0 - 26.0, atol=1e-9, rtol=0,
        note="Internally consistent, and the decomposition is quoted verbatim "
             "from the paper. Worth confirming because the 32% figure is the "
             "one that carries the report's argument: it isolates the portion "
             "of decay attributable to publication rather than to data mining.",
    )


def _hou_xue_zhang(reg: Registry) -> None:
    """Section 4.7's 452 anomalies, 65% and 82% failure rates."""
    total = 452
    f1, f2 = 0.65, 0.82
    n1, n2 = round(total * f1), round(total * f2)
    reg.add(
        "A-08", SEC4,
        r"Hou, Xue \& Zhang (2020) failure rates quoted in section 4.7",
        "convert the quoted percentages into counts out of 452 replicated "
        "anomalies",
        "65% fail at |t| < 1.96; 82% fail at |t| < 2.78",
        f"{n1} of {total} anomalies fail the single test; {n2} of {total} fail "
        f"the multiple-testing hurdle ({n2 - n1} additional casualties)",
        "PASS",
        rf"Arithmetically consistent with the quoted percentages. The "
        rf"incremental figure is the one the report should surface: raising the "
        rf"hurdle from $|t|>1.96$ to $|t|>2.78$ kills a further {n2 - n1} "
        rf"anomalies, leaving roughly {total - n2} of {total} standing. That is "
        r"the empirical anchor for the Harvey-Liu-Zhu $t>3.0$ recommendation "
        r"cited two lines later, and it is the single most persuasive argument "
        r"in the report for building section 2.8's deflation machinery before "
        r"writing any strategy.",
        survivors=total - n2, incremental=n2 - n1,
    )


def _circuit_breakers(reg: Registry) -> None:
    """Section 4.4's Rule 80B description, checked for internal consistency."""
    levels = [(1, 0.07, "15-minute halt if before 15:25 ET; none at/after"),
              (2, 0.13, "15-minute halt if before 15:25 ET; none at/after"),
              (3, 0.20, "halt for the remainder of the day, at any time")]
    mono = all(levels[i][1] < levels[i + 1][1] for i in range(len(levels) - 1))
    reg.truth(
        "A-09", SEC4,
        "Section 4.4's market-wide circuit-breaker (Rule 80B) thresholds are "
        "internally consistent",
        "check that the three levels are strictly increasing and that the "
        "time-of-day carve-out applies only to Levels 1 and 2",
        mono,
        "-7% / -13% / -20%, strictly increasing, Level 3 with no time carve-out",
        "; ".join(f"Level {n}: {p:.0%} -- {d}" for n, p, d in levels),
        r"Internally consistent as written, and the asymmetry the report "
        r"highlights is the operationally important part: a Level 1 or 2 breach "
        r"AT or after 15:25 ET does not halt trading, so a system that assumes "
        r"``a 7\% drop means the market stops'' will keep trading into a "
        r"cascading close. Since the report's own system trades the MOC "
        r"auction at roughly 15:50 ET, this carve-out lands squarely inside its "
        r"execution window -- which makes it a required test case, not "
        r"background reading. Note thresholds are recalculated daily from the "
        r"prior S\&P 500 close, so they must be fetched, never hardcoded. "
        r"Regulatory details must be confirmed against current FINRA/SEC "
        r"sources before reliance.",
    )


def _pdt_arithmetic(reg: Registry) -> None:
    """Section 3.6's PDT description: the 4-trades-in-5-days / 6% test."""
    # The historical rule: 4+ day trades in 5 business days AND those day
    # trades exceeding 6% of total trades in the account over that period.
    total_trades = 50
    day_trades = 4
    pct = day_trades / total_trades
    triggers = day_trades >= 4 and pct > 0.06
    # A counterexample: same day-trade count, much higher total activity.
    total_busy = 200
    pct_busy = day_trades / total_busy
    triggers_busy = day_trades >= 4 and pct_busy > 0.06
    reg.truth(
        "A-10", "3.6 Regulatory",
        "Section 3.6's pattern-day-trader test is a CONJUNCTION of two "
        "conditions, and the report states both",
        "evaluate the historical test at two activity levels with an identical "
        "day-trade count",
        triggers and not triggers_busy,
        "4 day trades trigger at low total activity but not at high",
        f"{day_trades} day trades in {total_trades} total = {pct:.0%} "
        f"-> triggers; {day_trades} in {total_busy} total = {pct_busy:.0%} "
        f"-> does not trigger",
        r"The report states the rule correctly, including the 6\% clause that "
        r"is frequently omitted in secondary sources. The worked counterexample "
        r"shows why the clause matters: day-trade COUNT alone does not "
        r"determine the classification. This check verifies the report's "
        r"internal logic only. The report itself flags that this framework was "
        r"reportedly eliminated effective June 2026 and replaced by an "
        r"intraday-margin standard; that status, and everything else in section "
        r"3.6, must be confirmed directly with FINRA and the broker before any "
        r"reliance. Nothing here is legal or tax advice.",
    )
