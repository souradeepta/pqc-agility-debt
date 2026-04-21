"""Fig 4 — Risk-CAD matrix: data sensitivity (risk tier) vs. CAD score.

Bubble size proportional to log(endpoint_count).
Quadrants define migration priority.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI

RISK_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
RISK_LABELS = {4: "Critical", 3: "High", 2: "Medium", 1: "Low"}

TIER_COLORS = {
    "Very High": "#c0392b",
    "High":      "#e67e22",
    "Medium":    "#f1c40f",
    "Low":       "#27ae60",
    "Very Low":  "#2980b9",
}

SHORT_NAMES = {
    "C01": "F5 BIG-IP HW", "C02": "F5 BIG-IP VE", "C03": "Luna HSM",
    "C04": "nShield HSM", "C05": "PAN-OS", "C06": "Cisco ASA",
    "C07": "FortiGate", "C08": "AD CS", "C09": "EJBCA",
    "C10": "AWS ACM", "C11": "AWS KMS", "C12": "Vault",
    "C13": "Azure KV", "C14": "OpenSSL", "C15": "Java JDK",
    "C16": "Win CNG", "C17": "Nginx", "C18": "Apache",
    "C19": "ACME Client", "C20": "Juniper SRX", "C21": "DataPower",
    "C22": "Spring",
}


def plot_risk_cad_matrix(results_sorted, estate: dict, out_path: Path) -> None:
    set_ieee_style()

    fig, ax = plt.subplots(figsize=(IEEE_COLUMN_WIDTH, 2.6))

    # Jitter to avoid exact overlaps
    rng = np.random.default_rng(42)

    for r in results_sorted:
        cid = r.component.id
        count = estate.get(cid, 1)
        risk_y = RISK_ORDER.get(r.component.risk_tier, 1)
        x = r.score
        y = risk_y + rng.uniform(-0.12, 0.12)
        size = 20 + 60 * np.log1p(count) / np.log1p(max(estate.values()))
        color = TIER_COLORS[r.tier]

        ax.scatter(x, y, s=size, c=color, alpha=0.8, edgecolors="white",
                   linewidths=0.3, zorder=3)

        # Label only large/important bubbles
        if count >= 40 or r.score >= 0.8 or r.component.risk_tier == "critical":
            offset_x = 0.02
            name = SHORT_NAMES.get(cid, cid)
            ax.annotate(name, (x, y), fontsize=4.5, va="center",
                        xytext=(x + offset_x, y),
                        ha="left", color="#333")

    # Priority quadrant lines
    ax.axvline(0.60, color="#888", linestyle="--", linewidth=0.7, alpha=0.7, zorder=2)
    ax.axhline(2.5, color="#888", linestyle="--", linewidth=0.7, alpha=0.7, zorder=2)

    # Quadrant labels
    ax.text(0.75, 3.8, "PRIORITY\nMIGRATE", fontsize=4.5, ha="center",
            color="#c0392b", fontweight="bold", alpha=0.7)
    ax.text(0.25, 3.8, "Monitor", fontsize=4.5, ha="center",
            color="#555", alpha=0.7)
    ax.text(0.75, 1.2, "Planned\nMigration", fontsize=4.5, ha="center",
            color="#e67e22", alpha=0.7)
    ax.text(0.25, 1.2, "Low\nPriority", fontsize=4.5, ha="center",
            color="#27ae60", alpha=0.7)

    ax.set_xlabel("CAD Score", fontsize=7)
    ax.set_ylabel("Risk Tier", fontsize=7)
    ax.set_xlim(0, 1.25)
    ax.set_ylim(0.3, 4.7)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["Low", "Medium", "High", "Critical"], fontsize=6.5)
    ax.grid(alpha=0.2, linewidth=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Bubble size legend
    for cnt, lbl in [(10, "10"), (100, "100"), (400, "400+")]:
        sz = 20 + 60 * np.log1p(cnt) / np.log1p(max(estate.values()))
        ax.scatter([], [], s=sz, c="#888", alpha=0.6, label=f"{lbl} endpoints")
    ax.legend(loc="upper left", fontsize=4.5, framealpha=0.85,
              handletextpad=0.3, borderpad=0.4)

    plt.tight_layout(pad=0.3)
    plt.savefig(out_path, dpi=IEEE_DPI, bbox_inches="tight")
    plt.close()
