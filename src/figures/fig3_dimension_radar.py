"""Fig 3 — Radar chart comparing CAD dimension profiles for representative components.

Shows 4 representative components: one Very High CAD, one High, one Medium, one Low.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI

DIMENSIONS = ["Alg Gap", "API Surface", "Key Constraints", "Comp Overhead", "Proc Delay"]
N = len(DIMENSIONS)
ANGLES = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
ANGLES += ANGLES[:1]  # close the polygon


def _get_values(r, proc_norm: float = 36.0):
    c = r.component
    proc_normalized = min(c.proc_months / proc_norm, 1.0)
    vals = [c.alg_gap, c.api_surface, c.key_constraints, c.comp_overhead, proc_normalized]
    return vals + vals[:1]


def plot_dimension_radar(results_sorted, out_path: Path) -> None:
    set_ieee_style()

    # Pick 4 representative components: one per tier region
    # Very High: C01 (F5 BIG-IP HW), High: C05 (Palo Alto), Medium: C19 (ACME), Low: C14 (OpenSSL)
    rep_ids = ["C01", "C05", "C19", "C14"]
    rep_labels = ["F5 BIG-IP HW\n(Very High)", "Palo Alto PAN-OS\n(High)",
                  "Custom ACME\n(Medium)", "OpenSSL 3.x\n(Very Low)"]
    rep_colors = ["#c0392b", "#e67e22", "#f1c40f", "#2980b9"]

    result_map = {r.component.id: r for r in results_sorted}

    fig, axes = plt.subplots(1, 4, figsize=(IEEE_COLUMN_WIDTH * 2, 2.2),
                             subplot_kw={"polar": True})

    for ax, cid, label, color in zip(axes, rep_ids, rep_labels, rep_colors):
        if cid not in result_map:
            continue
        r = result_map[cid]
        vals = _get_values(r)

        ax.plot(ANGLES, vals, color=color, linewidth=1.2)
        ax.fill(ANGLES, vals, color=color, alpha=0.25)

        ax.set_xticks(ANGLES[:-1])
        ax.set_xticklabels(["AG", "AS", "KC", "CO", "PD"], fontsize=5.5)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(["", "", "", ""], fontsize=4)
        ax.set_ylim(0, 1.0)
        ax.set_title(label, fontsize=5.5, pad=5)
        ax.tick_params(axis="both", which="both", pad=1)

        # Score annotation in center
        ax.text(0, -0.35, f"CAD={r.score:.2f}", ha="center", va="center",
                fontsize=5.5, color=color, fontweight="bold",
                transform=ax.transData)

    # Dimension key below figure
    fig.text(0.5, 0.01, "AG=Alg Gap  AS=API Surface  KC=Key Constraints  "
             "CO=Compliance Overhead  PD=Proc Delay",
             ha="center", fontsize=5, color="#555")

    plt.tight_layout(pad=0.5)
    plt.savefig(out_path, dpi=IEEE_DPI, bbox_inches="tight")
    plt.close()
