"""Shared IEEE-style matplotlib configuration."""

import matplotlib as mpl
import matplotlib.pyplot as plt

IEEE_COLUMN_WIDTH = 3.5   # inches — single column
IEEE_TEXT_WIDTH   = 7.16  # inches — double column
IEEE_DPI          = 300


def set_ieee_style() -> None:
    mpl.rcParams.update({
        "font.family":        "serif",
        "font.serif":         ["Times New Roman", "DejaVu Serif", "serif"],
        "font.size":          8,
        "axes.titlesize":     9,
        "axes.labelsize":     8,
        "xtick.labelsize":    7,
        "ytick.labelsize":    7,
        "legend.fontsize":    7,
        "figure.dpi":         IEEE_DPI,
        "savefig.dpi":        IEEE_DPI,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.02,
        "axes.linewidth":     0.6,
        "grid.linewidth":     0.4,
        "lines.linewidth":    1.0,
        "text.usetex":        False,
    })


def new_figure(width_col: float = 1.0, height_in: float = 2.0):
    """Create a new figure sized for IEEE column(s)."""
    return plt.figure(figsize=(IEEE_COLUMN_WIDTH * width_col, height_in))
