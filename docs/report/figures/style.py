"""Shared plotting style for the report figures.

Everything renders to vector PDF for LaTeX inclusion. One palette, one font
stack, one set of axis conventions, so the figure set reads as a single system.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib import rcParams          # noqa: E402

FIG_DIR = Path(__file__).resolve().parent
OUT = FIG_DIR

# --- palette -------------------------------------------------------------
INK = "#12172b"
MUTED = "#5b6478"
GRID = "#dfe3ec"
PANEL = "#f7f8fb"

BLUE = "#2563eb"
RED = "#d63b3b"
GREEN = "#0f9d6b"
AMBER = "#dd8b12"
PURPLE = "#7c4ddb"
TEAL = "#0d9aa8"
PINK = "#d6337f"
SLATE = "#8792a8"

CYCLE = [BLUE, RED, GREEN, AMBER, PURPLE, TEAL, PINK, SLATE]

# Semantic colours used consistently across the whole figure set.
C_TRUE = INK          # ground truth
C_GOOD = GREEN        # correct / honest / verified
C_BAD = RED           # wrong / inflated / naive
C_CAVEAT = AMBER      # correct-with-caveat


def setup() -> None:
    rcParams.update({
        "figure.dpi": 140,
        "savefig.dpi": 140,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial",
                            "DejaVu Sans"],
        "font.size": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "600",
        "axes.labelsize": 8.5,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "axes.linewidth": 0.7,
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.prop_cycle": plt.cycler(color=CYCLE),
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "legend.frameon": False,
        "legend.fontsize": 7.5,
        "lines.linewidth": 1.5,
        "lines.solid_capstyle": "round",
        "mathtext.fontset": "dejavusans",
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "pdf.fonttype": 42,
    })


def despine(ax, left=True, bottom=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)


def save(fig, name: str) -> Path:
    p = OUT / f"{name}.pdf"
    fig.savefig(p)
    plt.close(fig)
    print(f"    wrote {p.name}")
    return p


def note(ax, text: str, loc="lower right", fontsize=6.8, color=MUTED):
    """Small caption inside the axes, for the 'what this shows' line."""
    xy = {"lower right": (0.985, 0.03, "right", "bottom"),
          "lower left": (0.015, 0.03, "left", "bottom"),
          "upper right": (0.985, 0.97, "right", "top"),
          "upper left": (0.015, 0.97, "left", "top")}[loc]
    ax.text(xy[0], xy[1], text, transform=ax.transAxes, ha=xy[2], va=xy[3],
            fontsize=fontsize, color=color, linespacing=1.35)


def style3d(ax):
    """Consistent, restrained styling for 3D axes."""
    ax.xaxis.pane.set_facecolor("white")
    ax.yaxis.pane.set_facecolor("white")
    ax.zaxis.pane.set_facecolor("white")
    for pane in (ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane):
        pane.set_edgecolor(GRID)
        pane.set_alpha(1.0)
    ax.grid(True, color=GRID, linewidth=0.5)
    ax.tick_params(labelsize=7, colors=MUTED, pad=1)
    for a in (ax.xaxis, ax.yaxis, ax.zaxis):
        a.label.set_size(8)
        a.label.set_color(INK)
    ax.xaxis._axinfo["grid"].update(color=GRID, linewidth=0.5)
    ax.yaxis._axinfo["grid"].update(color=GRID, linewidth=0.5)
    ax.zaxis._axinfo["grid"].update(color=GRID, linewidth=0.5)
