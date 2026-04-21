# PQC Agility Debt: Post-Quantum Migration Readiness in SIFI Infrastructure

**Paper 10 of IEEE cybersecurity portfolio for EB2-NIW petition.**

> Cryptographic Agility Debt: Measuring Post-Quantum Migration Readiness
> in Systemically Important Financial Infrastructure
>
> Target venue: IEEE Transactions on Information Forensics and Security (TIFS)

## Key Results

| Finding | Value |
|---|---|
| Components surveyed | 22 |
| Estate cryptographic endpoints | 1,847 |
| Estate-weighted CAD | 0.457 (Medium-High) |
| High/Very High CAD endpoints | 39.3% |
| F5 BIG-IP HW CAD | 1.00 (Very High) — 22.3% of estate |
| F5 BIG-IP HW migration time | 90 months |
| Phase 3 (hardware) endpoints | 39.3% — cannot complete before 36 months |

## Quick Start

```bash
pip install -r requirements.txt
make all          # experiments + figures + PDF
make test         # 37 unit tests
```

## Repo Structure

```
src/
  cad.py             # CAD metric: 5-dimension scoring, estate assessment
  experiments.py     # Orchestrator -> results/results.tex + figures
  figures/
    fig2_cad_distribution.py   # CAD score bar chart (22 components)
    fig3_dimension_radar.py    # Dimension profiles for 4 representative components
    fig4_risk_cad_matrix.py    # Risk tier vs CAD scatter (bubble = endpoint count)
    fig5_migration_timeline.py # 3-phase Gantt migration roadmap
data/
  components.json    # 22-component CAD assessment data (public vendor sources)
paper/
  paper10.tex        # IEEEtran two-column LaTeX (no hardcoded numbers)
  paper10.bib        # 16 verified references
  IEEEtran.cls       # IEEE LaTeX class (local copy)
  IEEEtran.bst       # IEEE bibliography style (local copy)
results/
  results.tex        # Auto-generated LaTeX macros (make experiments)
tests/
  test_cad.py        # 37 unit tests (pytest)
```
