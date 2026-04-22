"""Fig 7: Cumulative endpoint fraction vs CAD score (CDF view)."""
from __future__ import annotations

from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI


def plot_endpoint_cdf(results_sorted, estate: Dict[str, int], out_path) -> None:
    """
    CDF: fraction of total endpoints with CAD score <= x.
    Shows what fraction of the estate must migrate at each debt level.
    """
    set_ieee_style()

    total = sum(estate.values())
    scores = []
    ep_weights = []
    for r in results_sorted:
        count = estate.get(r.component.id, 0)
        scores.append(r.score)
        ep_weights.append(count)

    # Sort by CAD ascending for CDF
    pairs = sorted(zip(scores, ep_weights), key=lambda x: x[0])
    xs = [p[0] for p in pairs]
    ws = [p[1] for p in pairs]
    cumulative = np.cumsum(ws) / max(total, 1)

    fig, ax = plt.subplots(figsize=(IEEE_COLUMN_WIDTH, 2.6))
    ax.plot(xs, cumulative, color="#1f77b4", linewidth=1.5, label="Endpoints")
    ax.fill_between(xs, cumulative, alpha=0.15, color="#1f77b4")

    # Tier lines
    tier_lines = [(0.20, "Low"), (0.40, "Med"), (0.60, "High"), (0.80, "V.High")]
    for thresh, label in tier_lines:
        ax.axvline(thresh, color="#666666", linewidth=0.7, linestyle="--")
        ax.text(thresh + 0.01, 0.05, label, fontsize=5, color="#444444")

    ax.set_xlabel("CAD Score")
    ax.set_ylabel("Cumulative Endpoint Fraction")
    ax.set_title("Endpoint CDF by CAD Score", fontsize=9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(str(out_path), dpi=IEEE_DPI)
    plt.close(fig)
    print(f"[fig7] saved {out_path}")
