"""Generate LaTeX tables from verification_results.json.

The report never hardcodes a verification number: every table and every count
in the summary is produced here from the suite's own output, so the prose and
the evidence cannot drift apart.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "out" / "verification_results.json"
GEN = ROOT / "out" / "generated"

STATUS_CMD = {"PASS": r"\PASS", "FAIL": r"\FAIL", "FLAG": r"\FLAG",
              "INFO": r"\INFO"}


def esc(s: str) -> str:
    """Escape bare LaTeX specials only.

    The verification notes are authored as LaTeX already (they contain math,
    \\textbf, \\texttt and pre-escaped percent signs), so a blanket escape would
    mangle them. This walks the string, passing through math spans and
    backslash sequences untouched and escaping only genuinely bare specials.
    """
    out: list[str] = []
    i, n, in_math = 0, len(s), False
    while i < n:
        ch = s[i]
        if ch == "$":                       # toggle math mode
            in_math = not in_math
            out.append(ch)
            i += 1
        elif in_math:                       # verbatim inside math
            out.append(ch)
            i += 1
        elif ch == "\\":                    # a LaTeX command: copy verbatim
            out.append(ch)
            i += 1
            if i < n and s[i].isalpha():
                while i < n and s[i].isalpha():
                    out.append(s[i])
                    i += 1
            elif i < n:                     # escaped char such as \% or \&
                out.append(s[i])
                i += 1
        elif ch in "%&#_":
            out.append("\\" + ch)
            i += 1
        elif ch == "~":
            out.append(r"\textasciitilde{}")
            i += 1
        elif ch == "^":
            out.append(r"\textasciicircum{}")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def load():
    d = json.loads(RESULTS.read_text())
    return d["checks"], d["summary"], d["master_seed"]


def table_full(checks) -> str:
    """The complete 100+ row appendix table."""
    rows = []
    cur = None
    for c in checks:
        if c["section"] != cur:
            cur = c["section"]
            rows.append(r"\multicolumn{4}{l}{}\\[-0.6em]")
            rows.append(
                r"\multicolumn{4}{l}{\textbf{\small " + esc(cur) + r"}}\\[0.2em]")
        rows.append(
            f"{STATUS_CMD[c['status']]} & \\texttt{{\\small {esc(c['cid'])}}} & "
            f"\\small {esc(c['claim'])} & "
            f"\\footnotesize\\color{{muted}}{esc(c['observed'])} \\\\")
    body = "\n".join(rows)
    return (
        r"\begingroup\footnotesize" "\n"
        r"\begin{longtable}{@{}p{0.055\linewidth}p{0.065\linewidth}"
        r"p{0.47\linewidth}p{0.34\linewidth}@{}}" "\n"
        r"\toprule" "\n"
        r"\textbf{Status} & \textbf{ID} & \textbf{Claim} & "
        r"\textbf{Measured} \\" "\n"
        r"\midrule" "\n"
        r"\endfirsthead" "\n"
        r"\toprule" "\n"
        r"\textbf{Status} & \textbf{ID} & \textbf{Claim} & "
        r"\textbf{Measured} \\" "\n"
        r"\midrule" "\n"
        r"\endhead" "\n"
        + body + "\n"
        r"\bottomrule" "\n"
        r"\end{longtable}\endgroup" "\n")


def table_findings(checks, status: str) -> str:
    """Compact table of just the FAIL or FLAG rows."""
    sel = [c for c in checks if c["status"] == status]
    rows = []
    for c in sel:
        rows.append(
            f"\\texttt{{\\small {esc(c['cid'])}}} & \\small {esc(c['section'])} & "
            f"\\small {esc(c['claim'])} \\\\")
    return (
        r"\begingroup\small" "\n"
        r"\begin{longtable}{@{}p{0.075\linewidth}p{0.26\linewidth}"
        r"p{0.60\linewidth}@{}}" "\n"
        r"\toprule" "\n"
        r"\textbf{ID} & \textbf{Report section} & \textbf{Issue} \\" "\n"
        r"\midrule\endhead" "\n"
        + "\n".join(rows) + "\n"
        r"\bottomrule" "\n"
        r"\end{longtable}\endgroup" "\n")


def summary_block(summary, checks, seed) -> str:
    total = len(checks)
    n_sec = len({c["section"] for c in checks})
    return (
        r"\begin{center}\small" "\n"
        r"\begin{tabular}{@{}lr@{\hspace{2.2em}}lr@{}}" "\n"
        r"\toprule" "\n"
        rf"Total checks & \textbf{{{total}}} & \PASS\ verified as stated & "
        rf"\textbf{{{summary.get('PASS', 0)}}} \\" "\n"
        rf"Report sections covered & {n_sec} & \FLAG\ correct with an unstated "
        rf"caveat & \textbf{{{summary.get('FLAG', 0)}}} \\" "\n"
        rf"Master seed & \texttt{{{seed}}} & \FAIL\ wrong as written & "
        rf"\textbf{{{summary.get('FAIL', 0)}}} \\" "\n"
        rf"Runtime & $\approx$6 min & \INFO\ derived quantity & "
        rf"\textbf{{{summary.get('INFO', 0)}}} \\" "\n"
        r"\bottomrule" "\n"
        r"\end{tabular}\end{center}" "\n")


def note_blocks(checks) -> str:
    """Full detail for every FAIL and FLAG, as callout boxes."""
    out = []
    for c in checks:
        if c["status"] not in ("FAIL", "FLAG"):
            continue
        env = "finding" if c["status"] == "FAIL" else "caveat"
        title = (f"{c['cid']} \\; --- \\; {esc(c['section'])}")
        out.append(
            f"\\begin{{{env}}}{{{title}}}\n"
            f"\\textbf{{Claim under test.}} {esc(c['claim'])}\n\n"
            f"\\textbf{{Method.}} {esc(c['method'])}\n\n"
            f"\\textbf{{Expected.}} {esc(c['expected'])} \\quad "
            f"\\textbf{{Measured.}} {esc(c['observed'])}\n\n"
            f"{esc(c['note'])}\n"
            f"\\end{{{env}}}\n")
    return "\n".join(out)


def main() -> None:
    checks, summary, seed = load()
    GEN.mkdir(parents=True, exist_ok=True)
    (GEN / "table_full.tex").write_text(table_full(checks))
    (GEN / "table_fails.tex").write_text(table_findings(checks, "FAIL"))
    (GEN / "table_flags.tex").write_text(table_findings(checks, "FLAG"))
    (GEN / "summary.tex").write_text(summary_block(summary, checks, seed))
    (GEN / "notes.tex").write_text(note_blocks(checks))
    print(f"  generated 5 LaTeX fragments from {len(checks)} checks "
          f"({summary})")


if __name__ == "__main__":
    main()
