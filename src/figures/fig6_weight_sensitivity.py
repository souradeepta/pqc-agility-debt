"""Fig 6: Weight sensitivity — correlation of each CAD dimension with estate CAD."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI

DIM_LABELS = {
    "alg_gap":         "Algorithm Gap",
    "api_surface":     "API Surface",
    "key_constraints": "Key Constraints",
    "comp_overhead":   "Compliance Overhead",
    "proc_delay":      "Procurement Delay",
}


def plot_weight_sensitivity(sensitivity: dict, out_path) -> None:
    """Bar chart of Pearson correlation of each weight dimension with estate CAD."""
    set_ieee_style()

    dims = list(DIM_LABELS.keys())
    labels = [DIM_LABELS[d] for d in dims]
    values = [sensitivity.get(d, 0.0) for d in dims]
    colors = ["#d62728" if v > 0 else "#1f77b4" for v in values]

    fig, ax = plt.subplots(figsize=(IEEE_COLUMN_WIDTH, 2.8))
    bars = ax.barh(labels, values, color=colors, edgecolor="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Pearson Correlation with Estate CAD")
    ax.set_title("Weight Dimension Sensitivity", fontsize=9)
    ax.set_xlim(-1.0, 1.0)

    for bar, v in zip(bars, values):
        x_off = 0.02 if v >= 0 else -0.02
        ha = "left" if v >= 0 else "right"
        ax.text(v + x_off, bar.get_y() + bar.get_height() / 2,
                f"{v:.3f}", va="center", ha=ha, fontsize=6)

    fig.tight_layout()
    fig.savefig(str(out_path), dpi=IEEE_DPI)
    plt.close(fig)
    print(f"[fig6] saved {out_path}")
