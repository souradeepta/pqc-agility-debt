"""Run all CAD experiments, generate LaTeX macros, and dispatch figure generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cad import (
    CADWeights, assess_estate, load_components, load_estate, cad_tier,
    PHASE_WINDOWS,
)
from .figures.fig2_cad_distribution import plot_cad_distribution
from .figures.fig3_dimension_radar import plot_dimension_radar
from .figures.fig4_risk_cad_matrix import plot_risk_cad_matrix
from .figures.fig5_migration_timeline import plot_migration_timeline


def _tier_count(results_sorted, tier: str) -> int:
    return sum(1 for r in results_sorted if r.tier == tier)


def _phase_endpoint_pct(estate_result, phase: int) -> float:
    phases = estate_result.results_by_phase()
    ph_eps = sum(
        estate_result.estate_distribution.get(r.component.id, 0)
        for r in phases[phase]
    )
    return 100.0 * ph_eps / max(estate_result.total_endpoints, 1)


def _highest_risk_high_cad(results_sorted, estate_result) -> str:
    """Return the top-priority component (critical risk + highest CAD)."""
    critical = [r for r in results_sorted
                if r.component.risk_tier == "critical"]
    if critical:
        return critical[0].component.name
    return results_sorted[0].component.name


def run_experiments(data_dir: Path, results_dir: Path) -> None:
    data_path = data_dir / "components.json"
    components = load_components(data_path)
    estate = load_estate(data_path)
    weights = CADWeights()

    estate_result = assess_estate(components, estate, weights)
    results_sorted = estate_result.results_sorted_by_score()

    # ── figures ─────────────────────────────────────────────────────────────
    results_dir.mkdir(parents=True, exist_ok=True)
    plot_cad_distribution(results_sorted, results_dir / "fig2_cad_distribution.pdf")
    plot_dimension_radar(results_sorted, results_dir / "fig3_dimension_radar.pdf")
    plot_risk_cad_matrix(results_sorted, estate, results_dir / "fig4_risk_cad_matrix.pdf")
    plot_migration_timeline(estate_result, results_dir / "fig5_migration_timeline.pdf")
    print("Figures generated.")

    # ── summary stats ────────────────────────────────────────────────────────
    top_cad = results_sorted[0]
    bottom_cad = results_sorted[-1]
    ph_counts = {ph: len(lst) for ph, lst in estate_result.results_by_phase().items()}

    print(f"\nEstate CAD (weighted): {estate_result.estate_cad:.3f}")
    print(f"Median migration: {estate_result.median_migration_months:.1f} months")
    print(f"Highest CAD: {top_cad.component.name} = {top_cad.score:.3f} ({top_cad.tier})")
    print(f"Lowest  CAD: {bottom_cad.component.name} = {bottom_cad.score:.3f} ({bottom_cad.tier})")
    print(f"Phase 1 components: {ph_counts[1]} | Phase 2: {ph_counts[2]} | Phase 3: {ph_counts[3]}")

    # ── LaTeX macros ─────────────────────────────────────────────────────────
    macros = {}

    macros["NumComponents"] = str(len(components))
    macros["TotalEndpoints"] = f"{estate_result.total_endpoints:,}"
    macros["EstateCad"] = f"{estate_result.estate_cad:.3f}"
    macros["MedianMigrationYears"] = f"{estate_result.median_migration_months / 12:.1f}"
    macros["MedianMigrationMonths"] = f"{estate_result.median_migration_months:.0f}"

    macros["HighestCadComponent"] = top_cad.component.name
    macros["HighestCadScore"] = f"{top_cad.score:.2f}"
    macros["HighestCadTier"] = top_cad.tier
    macros["LowestCadComponent"] = bottom_cad.component.name
    macros["LowestCadScore"] = f"{bottom_cad.score:.2f}"

    macros["NumVeryHigh"] = str(_tier_count(results_sorted, "Very High"))
    macros["NumHigh"] = str(_tier_count(results_sorted, "High"))
    macros["NumMedium"] = str(_tier_count(results_sorted, "Medium"))
    macros["NumLow"] = str(_tier_count(results_sorted, "Low"))
    macros["NumVeryLow"] = str(_tier_count(results_sorted, "Very Low"))

    macros["PhaseOneComponents"] = str(ph_counts[1])
    macros["PhaseTwoComponents"] = str(ph_counts[2])
    macros["PhaseThreeComponents"] = str(ph_counts[3])

    macros["PhaseOneEndpointPct"] = f"{_phase_endpoint_pct(estate_result, 1):.1f}"
    macros["PhaseTwoEndpointPct"] = f"{_phase_endpoint_pct(estate_result, 2):.1f}"
    macros["PhaseThreeEndpointPct"] = f"{_phase_endpoint_pct(estate_result, 3):.1f}"

    macros["TopPriorityComponent"] = _highest_risk_high_cad(results_sorted, estate_result)

    # Weight macros
    macros["WeightAlg"] = f"{weights.w_alg:.2f}"
    macros["WeightApi"] = f"{weights.w_api:.2f}"
    macros["WeightKey"] = f"{weights.w_key:.2f}"
    macros["WeightComp"] = f"{weights.w_comp:.2f}"
    macros["WeightProc"] = f"{weights.w_proc:.2f}"

    # F5 BIG-IP specific (primary SIFI component)
    f5_hw = next(r for r in results_sorted if r.component.id == "C01")
    macros["FfiveHwCadScore"] = f"{f5_hw.score:.2f}"
    macros["FfiveHwMigrationMonths"] = f"{f5_hw.migration_months:.0f}"
    macros["FfiveHwEndpointCount"] = str(estate.get("C01", 0))
    macros["FfiveHwEndpointPct"] = f"{100 * estate.get('C01', 0) / estate_result.total_endpoints:.1f}"

    openssl = next(r for r in results_sorted if r.component.id == "C14")
    macros["OpenSslCadScore"] = f"{openssl.score:.2f}"

    # Critical tier endpoints
    critical_eps = sum(
        estate.get(r.component.id, 0)
        for r in results_sorted
        if r.component.risk_tier == "critical"
    )
    macros["CriticalTierEndpointPct"] = f"{100 * critical_eps / estate_result.total_endpoints:.1f}"
    macros["CriticalTierEndpoints"] = str(critical_eps)

    # Phase 3 timing
    macros["PhaseThreeStartYear"] = "3"
    macros["PhaseThreeEndYear"] = "5"

    # CAD range
    macros["CadRangeMin"] = f"{results_sorted[-1].score:.2f}"
    macros["CadRangeMax"] = f"{results_sorted[0].score:.2f}"

    # Very High + High = "high-burden" components
    high_burden = sum(1 for r in results_sorted if r.tier in ("Very High", "High"))
    high_burden_eps = sum(
        estate.get(r.component.id, 0)
        for r in results_sorted if r.tier in ("Very High", "High")
    )
    macros["NumHighBurden"] = str(high_burden)
    macros["HighBurdenEndpointPct"] = f"{100 * high_burden_eps / estate_result.total_endpoints:.1f}"

    tex = "\n".join(
        f"\\newcommand{{\\{k}}}{{{v}}}"
        for k, v in sorted(macros.items())
    ) + "\n"

    macro_path = results_dir / "results.tex"
    macro_path.write_text(tex)
    print(f"\nLaTeX macros written to {macro_path}")
    print(f"Total macros: {len(macros)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir",    type=Path, default=Path("data"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    args = parser.parse_args()
    run_experiments(args.data_dir, args.results_dir)


if __name__ == "__main__":
    main()
