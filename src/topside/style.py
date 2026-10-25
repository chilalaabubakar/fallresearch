"""Shared figure style for publication figures.

Adapted from the figures4papers house style (Chen Liu,
https://github.com/ChenLiu-1996/figures4papers, scientific-figure-making/):
  * semantic colours: blue = proposed method (flexible scheduling),
    red/pink = alternative (fixed demand), grey = baseline (gas turbines only)
  * top/right spines off, frameless legends, no grid
  * fonts large relative to the canvas, so text stays readable when a
    ~10 inch figure is scaled to a ~6.5 inch page width
  * black bar edges + hatching so bars stay distinct in grayscale print
  * PNG at 300 dpi plus vector PDF with editable (TrueType) text
Deliberate difference: bar charts always start at zero (bar length encodes
magnitude); only line plots get tightened axis limits.
"""

from pathlib import Path

import matplotlib.pyplot as plt

PALETTE = {
    "blue_main": "#0F4D92", "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE", "green_2": "#AADCA9", "green_3": "#8BCF8B",
    "red_1": "#F6CFCB", "red_2": "#E9A6A1", "red_strong": "#B64342",
    "neutral": "#CFCECE", "grey": "#767676", "dark": "#4D4D4D", "ink": "#272727",
    "highlight": "#FFD700", "teal": "#42949E", "violet": "#9A4D8E",
}

# Cases: baseline grey, alternative red, proposed method blue (battery variant lighter blue)
CASE_COLOR = {"gt_only": PALETTE["grey"], "wind_fixed": PALETTE["red_2"],
              "wind_flex": PALETTE["blue_main"], "wind_flex_battery": PALETTE["blue_secondary"]}
CASE_HATCH = {"gt_only": "", "wind_fixed": "//", "wind_flex": "", "wind_flex_battery": ".."}

# Consumer flexibility classes
CLASS_COLOR = {"must_run": PALETTE["grey"], "flexible": PALETTE["blue_main"],
               "sheddable": PALETTE["red_strong"], "mixed": PALETTE["teal"]}

# Power sources in schedule plots
SOURCE_COLOR = {"gt": PALETTE["red_2"], "wind": PALETTE["blue_secondary"], "battery": PALETTE["teal"]}

FONT_SIZE = 14
LINE_WIDTH = 2.5


FONT_PREFERENCE = ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans")


def _first_available_font():
    """First installed font from FONT_PREFERENCE (Liberation Sans has Arial's metrics)."""
    from matplotlib import font_manager
    installed = {f.name for f in font_manager.fontManager.ttflist}
    return next((f for f in FONT_PREFERENCE if f in installed), "sans-serif")


def apply_publication_style(font_size=FONT_SIZE):
    plt.rcParams.update({
        "font.family": [_first_available_font()],
        "font.size": font_size,
        "axes.titlesize": font_size,
        "axes.labelsize": font_size,
        "xtick.labelsize": font_size - 2,
        "ytick.labelsize": font_size - 2,
        "legend.fontsize": font_size - 2,
        "axes.linewidth": 1.5,
        "xtick.major.width": 1.5,
        "ytick.major.width": 1.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "legend.frameon": False,
        "lines.linewidth": LINE_WIDTH,
        "svg.fonttype": "none",       # editable text in SVG
        "pdf.fonttype": 42,           # TrueType text in PDF (editable, journal-friendly)
        "savefig.dpi": 300,
        "figure.dpi": 100,
    })


def finalize_figure(fig, out_dir, name, formats=("png", "pdf")):
    """Save in each format (PNG 300 dpi, vector PDF) and close. Returns the first path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / f"{name}.{ext}" for ext in formats]
    for p in paths:
        fig.savefig(p, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    return paths[0]


def bar_kwargs(case):
    """Fill, edge and hatch for one case's bar."""
    return {"facecolor": CASE_COLOR[case], "edgecolor": "black", "linewidth": 1.2, "hatch": CASE_HATCH[case]}
