"""Fig 2 — CAD score distribution across SIFI infrastructure components.

Horizontal bar chart sorted by CAD score, colored by tier.
"""

from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI

TIER_COLORS = {
    "Very High": "#c0392b",
    "High":      "#e67e22",
    "Medium":    "#f1c40f",
    "Low":       "#27ae60",
    "Very Low":  "#2980b9",
}

# Short display names for components (truncated for figure)
SHORT_NAMES = {
    "C01": "F5 BIG-IP HW",
    "C02": "F5 BIG-IP VE",
    "C03": "Thales Luna HSM",
    "C04": "Entrust nShield",
    "C05": "Palo Alto PAN-OS",
    "C06": "Cisco ASA",
    "C07": "Fortinet FortiGate",
    "C08": "MS AD CS",
    "C09": "EJBCA",
    "C10": "AWS ACM",
    "C11": "AWS KMS",
    "C12": "HashiCorp Vault",
    "C13": "Azure Key Vault",
    "C14": "OpenSSL 3.x",
    "C15": "Java JDK 21+",
    "C16": "Windows CNG",
    "C17": "Nginx",
    "C18": "Apache httpd",
    "C19": "Custom ACME Client",
    "C20": "Juniper SRX",
    "C21": "IBM DataPower",
    "C22": "Spring Framework",
}


def plot_cad_distribution(results_sorted, out_path: Path) -> None:
    set_ieee_style()

    names = [SHORT_NAMES.get(r.component.id, r.component.id) for r in results_sorted]
    scores = [r.score for r in results_sorted]
    tiers = [r.tier for r in results_sorted]
    colors = [TIER_COLORS[t] for t in tiers]

    fig, ax = plt.subplots(figsize=(IEEE_COLUMN_WIDTH, len(names) * 0.22 + 0.6))

    y = np.arange(len(names))
    bars = ax.barh(y, scores, color=colors, edgecolor="white", linewidth=0.3, height=0.72)

    # Score labels
    for bar, score in zip(bars, scores):
        ax.text(score + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}", va="center", ha="left", fontsize=5.5)

    # Phase boundary lines
    ax.axvline(0.40, color="#555", linestyle=":", linewidth=0.7, alpha=0.7)
    ax.axvline(0.60, color="#555", linestyle="--", linewidth=0.7, alpha=0.7)
    ax.axvline(0.80, color="#555", linestyle="-", linewidth=0.7, alpha=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6)
    ax.set_xlabel("CAD Score", fontsize=7)
    ax.set_xlim(0, 1.15)
    ax.set_ylim(-0.5, len(names) - 0.5)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3, linewidth=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend
    patches = [mpatches.Patch(color=c, label=t) for t, c in TIER_COLORS.items()]
    ax.legend(handles=patches, loc="lower right", fontsize=5.5,
              framealpha=0.85, edgecolor="#ccc")

    plt.tight_layout(pad=0.3)
    plt.savefig(out_path, dpi=IEEE_DPI, bbox_inches="tight")
    plt.close()
