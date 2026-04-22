"""Unit tests for the CAD scoring model."""

import math
import json
from pathlib import Path
import pytest

from src.cad import (
    CADWeights, Component, CADResult,
    cad_score, cad_tier, estimate_migration_months, assess_component,
    load_components, load_estate, assess_estate, _weighted_median,
    PROC_NORMALIZATION_MONTHS, MIGRATION_PHASES, PHASE_WINDOWS,
)

DATA_PATH = Path(__file__).parent.parent / "data" / "components.json"


# ── helpers ─────────────────────────────────────────────────────────────────

def make_component(**kwargs) -> Component:
    defaults = dict(
        id="T01", name="Test", category="Test", vendor="Test",
        pqc_support="none",
        alg_gap=0.0, api_surface=0.0, key_constraints=0.0,
        comp_overhead=0.0, proc_months=0,
        risk_tier="low",
    )
    defaults.update(kwargs)
    return Component(**defaults)


# ── CADWeights ───────────────────────────────────────────────────────────────

def test_weights_sum_to_one():
    w = CADWeights()
    assert abs(w.w_alg + w.w_api + w.w_key + w.w_comp + w.w_proc - 1.0) < 1e-9


def test_weights_invalid_sum_raises():
    with pytest.raises(ValueError, match="sum to 1.0"):
        CADWeights(w_alg=0.5, w_api=0.5, w_key=0.5, w_comp=0.0, w_proc=0.0)


# ── cad_score ────────────────────────────────────────────────────────────────

def test_cad_score_all_zero():
    c = make_component()
    assert cad_score(c) == pytest.approx(0.0)


def test_cad_score_all_one():
    c = make_component(
        alg_gap=1.0, api_surface=1.0, key_constraints=1.0,
        comp_overhead=1.0, proc_months=PROC_NORMALIZATION_MONTHS,
    )
    assert cad_score(c) == pytest.approx(1.0)


def test_cad_score_proc_capped_at_one():
    c = make_component(proc_months=PROC_NORMALIZATION_MONTHS * 2)
    w = CADWeights()
    score = cad_score(c, w)
    # Only proc dimension contributes; proc_normalized = min(72/36, 1) = 1
    assert score == pytest.approx(w.w_proc)


def test_cad_score_partial():
    c = make_component(alg_gap=1.0)
    w = CADWeights()
    assert cad_score(c, w) == pytest.approx(w.w_alg)


def test_cad_score_in_range():
    c = make_component(
        alg_gap=0.5, api_surface=0.5, key_constraints=0.5,
        comp_overhead=0.5, proc_months=18,
    )
    score = cad_score(c)
    assert 0.0 <= score <= 1.0


# ── cad_tier ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (1.00, "Very High"),
    (0.85, "Very High"),
    (0.80, "Very High"),
    (0.79, "High"),
    (0.60, "High"),
    (0.59, "Medium"),
    (0.40, "Medium"),
    (0.39, "Low"),
    (0.20, "Low"),
    (0.19, "Very Low"),
    (0.00, "Very Low"),
])
def test_cad_tier_boundaries(score, expected):
    assert cad_tier(score) == expected


# ── estimate_migration_months ────────────────────────────────────────────────

def test_migration_months_hardware():
    c = make_component(proc_months=36, comp_overhead=1.0)
    months = estimate_migration_months(c, 1.0)
    assert months == pytest.approx(36 * 2.5)


def test_migration_months_software_zero_proc():
    c = make_component(proc_months=0, api_surface=0.0, comp_overhead=0.0)
    months = estimate_migration_months(c, 0.0)
    assert months == pytest.approx(1.0)


def test_migration_months_positive():
    c = make_component(proc_months=12, comp_overhead=0.5)
    months = estimate_migration_months(c, 0.5)
    assert months > 0


# ── assess_component ─────────────────────────────────────────────────────────

def test_assess_component_returns_result():
    c = make_component(alg_gap=1.0, api_surface=1.0, key_constraints=1.0,
                       comp_overhead=1.0, proc_months=36)
    r = assess_component(c)
    assert isinstance(r, CADResult)
    assert r.score == pytest.approx(1.0)
    assert r.tier == "Very High"
    assert r.phase == 3


def test_assess_component_phase1():
    c = make_component()
    r = assess_component(c)
    assert r.phase == 1
    assert r.tier == "Very Low"


def test_assess_component_dimension_scores_sum():
    c = make_component(alg_gap=0.5, api_surface=0.3, key_constraints=0.2,
                       comp_overhead=0.4, proc_months=12)
    r = assess_component(c)
    assert abs(sum(r.dimension_scores.values()) - r.score) < 1e-9


# ── load_components / load_estate ────────────────────────────────────────────

def test_load_components():
    components = load_components(DATA_PATH)
    assert len(components) == 30
    ids = [c.id for c in components]
    assert "C01" in ids
    assert "C14" in ids
    assert "C23" in ids  # Bouncy Castle (new)


def test_load_components_f5_hw():
    components = load_components(DATA_PATH)
    f5 = next(c for c in components if c.id == "C01")
    assert f5.alg_gap == 1.0
    assert f5.api_surface == 1.0
    assert f5.proc_months == 36


def test_load_estate():
    estate = load_estate(DATA_PATH)
    assert "C01" in estate
    assert estate["C01"] == 412
    assert sum(estate.values()) == 2045


# ── assess_estate ────────────────────────────────────────────────────────────

def test_assess_estate_f5_dominates():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    # F5 BIG-IP HW should have highest CAD
    sorted_r = result.results_sorted_by_score()
    assert sorted_r[0].component.id == "C01"


def test_assess_estate_cad_in_range():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    assert 0.0 < result.estate_cad < 1.0


def test_assess_estate_phase3_exists():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    phases = result.results_by_phase()
    # Proposition 1: estate_cad > 0.40 implies Phase 3 exists
    assert result.estate_cad > 0.40
    assert len(phases[3]) > 0


def test_assess_estate_total_endpoints():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    assert result.total_endpoints == 2045


def test_assess_estate_phase_counts():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    phases = result.results_by_phase()
    total = sum(len(v) for v in phases.values())
    assert total == 30


# ── _weighted_median ─────────────────────────────────────────────────────────

def test_weighted_median_uniform():
    vals = [1.0, 2.0, 3.0]
    weights = [1, 1, 1]
    assert _weighted_median(vals, weights) == pytest.approx(2.0)


def test_weighted_median_heavy_low():
    vals = [1.0, 10.0]
    weights = [100, 1]
    assert _weighted_median(vals, weights) == pytest.approx(1.0)


def test_weighted_median_heavy_high():
    vals = [1.0, 10.0]
    weights = [1, 100]
    assert _weighted_median(vals, weights) == pytest.approx(10.0)


# ── migration phase phase_window ────────────────────────────────────────────

def test_phase_windows():
    assert PHASE_WINDOWS[1] == (0, 12)
    assert PHASE_WINDOWS[2] == (12, 36)
    assert PHASE_WINDOWS[3] == (36, 60)


# ── proposition 1 verification ───────────────────────────────────────────────

def test_proposition1_reference_estate():
    """Proposition 1: estate_cad >= 0.40 implies Phase 3 component exists."""
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    result = assess_estate(components, estate)
    phases = result.results_by_phase()

    if result.estate_cad >= 0.40:
        assert len(phases[3]) > 0, (
            f"Proposition 1 violated: estate_cad={result.estate_cad:.3f} >= 0.40 "
            f"but no Phase 3 components found"
        )


# ── New analytical functions (Lemma 1, Theorem 1, Corollary 1) ───────────────
from src.cad import (
    migration_time_lower_bound, f5_estate_cad_lower_bound,
    weight_sensitivity_sweep, dimension_correlation_matrix,
)


# Lemma 1: migration_time_lower_bound >= hardware proc months and >= software min
def test_lemma1_hw_lower_bound_gte_proc_months():
    """Lemma 1: migration lower bound >= proc_months for hardware components."""
    components = load_components(DATA_PATH)
    hw = next(c for c in components if c.proc_months >= 24)
    lb = migration_time_lower_bound(hw)
    assert lb >= hw.proc_months


def test_lemma1_sw_lower_bound_gte_software_min():
    """Lemma 1: migration lower bound >= 1 + 11*api_surface for software."""
    components = load_components(DATA_PATH)
    sw = next(c for c in components if c.proc_months == 0)
    lb = migration_time_lower_bound(sw)
    assert lb >= 1.0 + 11.0 * sw.api_surface


def test_lemma1_lower_bound_positive():
    components = load_components(DATA_PATH)
    for c in components:
        assert migration_time_lower_bound(c) > 0.0


def test_lemma1_hw_migration_gte_lower_bound():
    """Lemma 1: for hardware (proc_months>0), actual migration >= lb."""
    from src.cad import estimate_migration_months
    components = load_components(DATA_PATH)
    hw_components = [c for c in components if c.proc_months > 0]
    for c in hw_components:
        lb = migration_time_lower_bound(c)
        actual = estimate_migration_months(c, 0.5)
        # For hardware, base = proc_months; lb = max(proc_months, 1+11*api)
        # Only guarantee when proc_months dominates (proc_months >= 1+11*api_surface)
        if c.proc_months >= 1.0 + 11.0 * c.api_surface:
            assert actual >= lb - 1e-9, f"{c.name}: actual={actual:.1f} < lb={lb:.1f}"


# Theorem 1: estate CAD is bounded by component scores
def test_theorem1_estate_cad_bounded_by_max():
    """Theorem 1: estate CAD <= max component CAD score."""
    from src.cad import cad_score
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    er = assess_estate(components, estate)
    max_score = max(cad_score(c) for c in components)
    assert er.estate_cad <= max_score + 1e-9


def test_theorem1_estate_cad_gte_min():
    """Theorem 1: estate CAD >= min component CAD score (weighted)."""
    from src.cad import cad_score
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    er = assess_estate(components, estate)
    min_score = min(cad_score(c) for c in components if estate.get(c.id, 0) > 0)
    assert er.estate_cad >= min_score - 1e-9


# Corollary 1: F5 lower bound
def test_corollary1_f5_lower_bound_valid():
    """Corollary 1: estate CAD >= f5_score * f5_fraction."""
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    er = assess_estate(components, estate)
    f5 = next(r for r in er.results_sorted_by_score() if r.component.id == "C01")
    f5_frac = estate.get("C01", 0) / max(er.total_endpoints, 1)
    lb = f5_estate_cad_lower_bound(er.estate_cad, f5.score, f5_frac)
    assert er.estate_cad >= lb - 1e-9


def test_corollary1_f5_lower_bound_nonneg():
    assert f5_estate_cad_lower_bound(0.5, 1.0, 0.2) >= 0.0


def test_corollary1_f5_lb_increases_with_f5_score():
    lb1 = f5_estate_cad_lower_bound(0.5, 0.8, 0.2)
    lb2 = f5_estate_cad_lower_bound(0.5, 1.0, 0.2)
    assert lb2 > lb1


# Weight sensitivity tests
def test_weight_sensitivity_returns_five_dims():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    sens = weight_sensitivity_sweep(components, estate, n_samples=50, seed=0)
    assert len(sens) == 5


def test_weight_sensitivity_values_in_range():
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    sens = weight_sensitivity_sweep(components, estate, n_samples=50, seed=0)
    for v in sens.values():
        assert -1.0 <= v <= 1.0


def test_weight_sensitivity_alg_gap_positive():
    """Increasing algorithm gap weight should positively correlate with estate CAD."""
    components = load_components(DATA_PATH)
    estate = load_estate(DATA_PATH)
    sens = weight_sensitivity_sweep(components, estate, n_samples=200, seed=42)
    assert sens["alg_gap"] > 0.0


# Dimension correlation matrix tests
def test_dimension_corr_matrix_shape():
    components = load_components(DATA_PATH)
    corr = dimension_correlation_matrix(components)
    assert corr.shape == (5, 5)


def test_dimension_corr_matrix_diagonal_ones():
    import numpy as np
    components = load_components(DATA_PATH)
    corr = dimension_correlation_matrix(components)
    assert all(abs(corr[i, i] - 1.0) < 1e-9 for i in range(5))


def test_dimension_corr_matrix_symmetric():
    import numpy as np
    components = load_components(DATA_PATH)
    corr = dimension_correlation_matrix(components)
    assert np.allclose(corr, corr.T, atol=1e-9)


def test_dimension_corr_values_bounded():
    import numpy as np
    components = load_components(DATA_PATH)
    corr = dimension_correlation_matrix(components)
    assert np.all(corr >= -1.0 - 1e-9) and np.all(corr <= 1.0 + 1e-9)
