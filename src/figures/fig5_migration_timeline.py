"""Fig 5 — Migration timeline: phase Gantt chart showing PQC migration phases.

Horizontal bar chart grouped by migration phase with endpoint coverage annotations.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

from .common import set_ieee_style, IEEE_COLUMN_WIDTH, IEEE_DPI

PHASE_COLORS = {1: "#27ae60", 2: "#e67e22", 3: "#c0392b"}
PHASE_LABELS = {1: "Phase 1: 0-12 months\n(Software stacks, cloud services)",
                2: "Phase 2: 12-36 months\n(Firmware, API gateways, managed CAs)",
                3: "Phase 3: 36-60 months\n(Hardware: HSMs, F5 appliances, firewalls)"}

SHORT_NAMES = {
    "C01": "F5 BIG-IP HW", "C02": "F5 BIG-IP VE", "C03": "Thales Luna HSM",
    "C04": "Entrust nShield", "C05": "Palo Alto PAN-OS", "C06": "Cisco ASA",
    "C07": "Fortinet FortiGate", "C08": "MS AD CS", "C09": "EJBCA",
    "C10": "AWS ACM", "C11": "AWS KMS", "C12": "HashiCorp Vault",
    "C13": "Azure KV", "C14": "OpenSSL 3.x", "C15": "Java JDK 21+",
    "C16": "Windows CNG", "C17": "Nginx", "C18": "Apache httpd",
    "C19": "Custom ACME", "C20": "Juniper SRX", "C21": "IBM DataPower",
    "C22": "Spring Framework",
}


def plot_migration_timeline(estate_result, out_path: Path) -> None:
    set_ieee_style()

    phases = estate_result.results_by_phase()
    total_endpoints = estate_result.total_endpoints

    # Build ordered list: Phase 1 bottom, Phase 3 top (reversed for Gantt readability)
    all_results = []
    phase_separators = []
    for ph in [3, 2, 1]:
        if phases[ph]:
            phase_separators.append((len(all_results), ph))
            all_results.extend(sorted(phases[ph], key=lambda r: r.score, reverse=True))

    fig, ax = plt.subplots(figsize=(IEEE_COLUMN_WIDTH, len(all_results) * 0.24 + 1.0))

    y_pos = np.arange(len(all_results))
    phase_window_ends = {1: 12, 2: 36, 3: 60}
    phase_window_starts = {1: 0, 2: 12, 3: 36}

    for i, r in enumerate(all_results):
        ph = r.phase
        start = phase_window_starts[ph]
        duration = min(r.migration_months, phase_window_ends[ph]) - start
        duration = max(duration, 1.0)
        color = PHASE_COLORS[ph]
        count = estate_result.estate_distribution.get(r.component.id, 0)

        ax.barh(i, duration, left=start, color=color, alpha=0.75,
                edgecolor="white", linewidth=0.3, height=0.72)

        name = SHORT_NAMES.get(r.component.id, r.component.id)
        label = f"{name} ({count} ep)"
        ax.text(-0.5, i, label, va="center", ha="right", fontsize=5, color="#333")

    # Phase boundary lines
    for month, label_text in [(12, "12mo"), (36, "36mo")]:
        ax.axvline(month, color="#555", linestyle="--", linewidth=0.7, alpha=0.6)
        ax.text(month, len(all_results) - 0.3, label_text, ha="center",
                va="bottom", fontsize=5, color="#555")

    ax.set_xlabel("Calendar Months from Migration Start", fontsize=7)
    ax.set_xlim(-0.5, 63)
    ax.set_ylim(-0.5, len(all_results) - 0.3)
    ax.set_yticks([])
    ax.set_xticks([0, 12, 24, 36, 48, 60])
    ax.grid(axis="x", alpha=0.25, linewidth=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Phase legend
    patches = [mpatches.Patch(color=PHASE_COLORS[ph], alpha=0.75,
                               label=f"Phase {ph}") for ph in [1, 2, 3]]
    ax.legend(handles=patches, loc="lower right", fontsize=5.5,
              framealpha=0.85, edgecolor="#ccc")

    # Coverage annotation
    ph1_eps = sum(
        estate_result.estate_distribution.get(r.component.id, 0)
        for r in phases[1]
    )
    ph2_eps = sum(
        estate_result.estate_distribution.get(r.component.id, 0)
        for r in phases[2]
    )
    ph3_eps = sum(
        estate_result.estate_distribution.get(r.component.id, 0)
        for r in phases[3]
    )
    ax.text(6, -0.45, f"Ph1: {ph1_eps/total_endpoints*100:.0f}% endpoints",
            fontsize=4.5, color=PHASE_COLORS[1], ha="center")
    ax.text(24, -0.45, f"Ph2: {ph2_eps/total_endpoints*100:.0f}%",
            fontsize=4.5, color=PHASE_COLORS[2], ha="center")
    ax.text(48, -0.45, f"Ph3: {ph3_eps/total_endpoints*100:.0f}%",
            fontsize=4.5, color=PHASE_COLORS[3], ha="center")

    plt.tight_layout(pad=0.3)
    plt.savefig(out_path, dpi=IEEE_DPI, bbox_inches="tight")
    plt.close()
