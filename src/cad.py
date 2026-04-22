"""Cryptographic Agility Debt (CAD) scoring model."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

# Default CAD dimension weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "w_alg":  0.25,  # algorithm support gap
    "w_api":  0.20,  # API surface / change difficulty
    "w_key":  0.15,  # key size constraints
    "w_comp": 0.20,  # compliance overhead
    "w_proc": 0.20,  # procurement delay (normalized)
}

PROC_NORMALIZATION_MONTHS = 36  # max procurement delay for normalization

# CAD tier thresholds
CAD_TIERS = [
    (0.80, "Very High"),
    (0.60, "High"),
    (0.40, "Medium"),
    (0.20, "Low"),
    (0.00, "Very Low"),
]

# Migration phase assignments by CAD tier
MIGRATION_PHASES = {
    "Very Low": 1,
    "Low":      1,
    "Medium":   2,
    "High":     3,
    "Very High": 3,
}

PHASE_WINDOWS = {
    1: (0, 12),
    2: (12, 36),
    3: (36, 60),
}


@dataclass
class CADWeights:
    w_alg:  float = 0.25
    w_api:  float = 0.20
    w_key:  float = 0.15
    w_comp: float = 0.20
    w_proc: float = 0.20

    def __post_init__(self):
        total = self.w_alg + self.w_api + self.w_key + self.w_comp + self.w_proc
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")


@dataclass
class Component:
    id: str
    name: str
    category: str
    vendor: str
    pqc_support: str
    alg_gap: float       # 0 = full support, 1 = no support
    api_surface: float   # 0 = config change, 1 = hardware replacement
    key_constraints: float  # 0 = no constraints, 1 = hardcoded/incompatible
    comp_overhead: float    # 0 = no compliance change, 1 = max overhead
    proc_months: float      # procurement delay in months (0 if software)
    risk_tier: str          # critical / high / medium / low
    notes: str = ""
    source: str = ""


@dataclass
class CADResult:
    component: Component
    score: float              # 0–1
    tier: str
    phase: int                # migration phase 1/2/3
    migration_months: float   # estimated total months to migrate
    dimension_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def phase_window(self):
        return PHASE_WINDOWS[self.phase]


def cad_score(c: Component, weights: CADWeights = CADWeights()) -> float:
    """Compute scalar CAD score in [0, 1] for a component."""
    proc_normalized = min(c.proc_months / PROC_NORMALIZATION_MONTHS, 1.0)
    return (
        weights.w_alg  * c.alg_gap
        + weights.w_api  * c.api_surface
        + weights.w_key  * c.key_constraints
        + weights.w_comp * c.comp_overhead
        + weights.w_proc * proc_normalized
    )


def cad_tier(score: float) -> str:
    for threshold, label in CAD_TIERS:
        if score >= threshold:
            return label
    return "Very Low"


def estimate_migration_months(c: Component, score: float) -> float:
    """Estimate total calendar months to achieve PQC compliance for component."""
    # Base: procurement delay (hardware) or engineering time (software)
    if c.proc_months > 0:
        base = c.proc_months
    else:
        # Estimate from api_surface: 0 = 1 month, 1 = 12 months
        base = 1.0 + 11.0 * c.api_surface

    # Compliance overhead multiplier (CAB cycles, PCI revalidation)
    comp_multiplier = 1.0 + c.comp_overhead * 1.5  # up to 2.5×

    return base * comp_multiplier


def assess_component(c: Component, weights: CADWeights = CADWeights()) -> CADResult:
    """Full CAD assessment for a single component."""
    proc_normalized = min(c.proc_months / PROC_NORMALIZATION_MONTHS, 1.0)
    dim_scores = {
        "alg_gap":       weights.w_alg  * c.alg_gap,
        "api_surface":   weights.w_api  * c.api_surface,
        "key_constraints": weights.w_key * c.key_constraints,
        "comp_overhead": weights.w_comp * c.comp_overhead,
        "proc_delay":    weights.w_proc * proc_normalized,
    }
    score = sum(dim_scores.values())
    tier = cad_tier(score)
    phase = MIGRATION_PHASES[tier]
    mig_months = estimate_migration_months(c, score)

    return CADResult(
        component=c,
        score=score,
        tier=tier,
        phase=phase,
        migration_months=mig_months,
        dimension_scores=dim_scores,
    )


def load_components(data_path: Path) -> List[Component]:
    """Load component definitions from JSON."""
    with open(data_path) as f:
        data = json.load(f)
    return [
        Component(**{k: v for k, v in c.items() if k in Component.__dataclass_fields__})
        for c in data["components"]
    ]


def load_estate(data_path: Path) -> Dict[str, int]:
    """Load SIFI estate endpoint distribution from JSON."""
    with open(data_path) as f:
        data = json.load(f)
    return data["sifi_estate"]["distribution"]


def assess_estate(
    components: List[Component],
    estate: Dict[str, int],
    weights: CADWeights = CADWeights(),
) -> "EstateResult":
    """Assess all components weighted by SIFI estate endpoint count."""
    results = {c.id: assess_component(c, weights) for c in components}

    total_endpoints = sum(estate.get(cid, 0) for cid in [c.id for c in components])
    weighted_sum = 0.0
    total_migration_endpoint_months = 0.0

    for c in components:
        count = estate.get(c.id, 0)
        r = results[c.id]
        weighted_sum += r.score * count
        total_migration_endpoint_months += r.migration_months * count

    estate_cad = weighted_sum / max(total_endpoints, 1)
    median_migration = _weighted_median(
        [results[c.id].migration_months for c in components],
        [estate.get(c.id, 0) for c in components],
    )

    return EstateResult(
        component_results=results,
        estate_distribution=estate,
        estate_cad=estate_cad,
        median_migration_months=median_migration,
        total_endpoints=total_endpoints,
    )


@dataclass
class EstateResult:
    component_results: Dict[str, CADResult]
    estate_distribution: Dict[str, int]
    estate_cad: float
    median_migration_months: float
    total_endpoints: int

    def results_by_phase(self) -> Dict[int, List[CADResult]]:
        phases: Dict[int, List[CADResult]] = {1: [], 2: [], 3: []}
        for r in self.component_results.values():
            phases[r.phase].append(r)
        for lst in phases.values():
            lst.sort(key=lambda x: x.score, reverse=True)
        return phases

    def results_sorted_by_score(self) -> List[CADResult]:
        return sorted(self.component_results.values(), key=lambda r: r.score, reverse=True)


def _weighted_median(values: List[float], weights: List[int]) -> float:
    """Compute weighted median."""
    pairs = sorted(zip(values, weights), key=lambda x: x[0])
    total = sum(w for _, w in pairs)
    cumulative = 0
    for val, w in pairs:
        cumulative += w
        if cumulative >= total / 2:
            return val
    return pairs[-1][0]


def weight_sensitivity_sweep(
    components: List[Component],
    estate: Dict[str, int],
    n_samples: int = 1000,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Monte Carlo sensitivity: sample Dirichlet weight vectors, return std dev of
    estate CAD across samples for each dimension.  Larger std = more sensitive.

    Returns dict: dimension_name -> std_dev_of_estate_cad_when_that_dim_is_varied.
    """
    import numpy as np
    rng = np.random.default_rng(seed)
    dims = ["w_alg", "w_api", "w_key", "w_comp", "w_proc"]
    dim_names = ["alg_gap", "api_surface", "key_constraints", "comp_overhead", "proc_delay"]

    estate_cads = []
    for _ in range(n_samples):
        alpha = rng.dirichlet(np.ones(5))
        w = CADWeights(**dict(zip(dims, alpha)))
        er = assess_estate(components, estate, w)
        estate_cads.append(er.estate_cad)

    estate_cads = np.array(estate_cads)

    # Compute correlation between each dimension's alpha values and resulting CAD
    result = {}
    # Re-sample with tracking to get per-dim correlation
    samples_by_dim = {d: [] for d in dims}
    cads = []
    for _ in range(n_samples):
        alpha = rng.dirichlet(np.ones(5))
        for i, d in enumerate(dims):
            samples_by_dim[d].append(alpha[i])
        w = CADWeights(**dict(zip(dims, alpha)))
        er = assess_estate(components, estate, w)
        cads.append(er.estate_cad)
    cads = np.array(cads)
    for d, dname in zip(dims, dim_names):
        weights_arr = np.array(samples_by_dim[d])
        corr = float(np.corrcoef(weights_arr, cads)[0, 1])
        result[dname] = corr

    return result


def dimension_correlation_matrix(components: List[Component]) -> "np.ndarray":
    """
    Pearson correlation matrix of [alg_gap, api_surface, key_constraints,
    comp_overhead, proc_normalized] across all components.
    """
    import numpy as np
    matrix = np.array([
        [c.alg_gap, c.api_surface, c.key_constraints, c.comp_overhead,
         min(c.proc_months / PROC_NORMALIZATION_MONTHS, 1.0)]
        for c in components
    ])
    return np.corrcoef(matrix.T)


def migration_time_lower_bound(c: Component) -> float:
    """
    Lemma 1 lower bound: migration time >= max(proc_months, 1+11*api_surface).
    """
    software_min = 1.0 + 11.0 * c.api_surface
    return max(float(c.proc_months), software_min)


def f5_estate_cad_lower_bound(estate_cad: float, f5_score: float, f5_fraction: float) -> float:
    """
    Corollary 1: estate CAD >= f5_score * f5_fraction.
    Since F5 BIG-IP hardware dominates the estate.
    """
    return f5_score * f5_fraction
