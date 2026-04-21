# Paper 10: Cryptographic Agility Debt — Explainer and Developer Reference

**Title:** Cryptographic Agility Debt: Measuring Post-Quantum Migration Readiness in Systemically Important Financial Infrastructure

**Venue:** IEEE Transactions on Information Forensics and Security (TIFS)

**Repo:** https://github.com/souradeepta/pqc-agility-debt

---

## 1. The Problem

NIST finalized three post-quantum cryptography (PQC) standards in August 2024:
- FIPS 203 (ML-KEM / CRYSTALS-Kyber) — key encapsulation
- FIPS 204 (ML-DSA / CRYSTALS-Dilithium) — digital signatures
- FIPS 205 (SLH-DSA / SPHINCS+) — stateless hash-based signatures

These standards trigger a mandatory migration timeline for financial critical infrastructure. The problem: **migration difficulty is wildly non-uniform**. A software TLS library (OpenSSL 3.x) can be patched in weeks. An F5 BIG-IP hardware appliance requires a 90-month hardware replacement and regulatory approval cycle.

Current practice has no systematic metric for quantifying this difference. SIFI (Systemically Important Financial Institution) security teams cannot prioritize migration or report readiness to regulators without a formal measure.

---

## 2. Core Concept: Cryptographic Agility Debt (CAD)

**CAD is a 5-dimension weighted score [0, 1] measuring how hard it is for a component to migrate to PQC.**

Higher CAD = harder to migrate = more "debt" that must be paid.

### The 5 Dimensions

| Dimension | Weight | What it measures |
|---|---|---|
| Algorithm Hardness (alg) | 0.25 | Is the algorithm quantum-vulnerable? RSA/ECC = high. Already PQC-ready = low. |
| API Surface (api) | 0.20 | How many callers depend on the crypto interface? Wide blast radius = high. |
| Key Infrastructure (key) | 0.15 | Is key material in HSMs, hardware? Hard-to-rotate = high. |
| Procurement Cycle (proc) | 0.20 | How long does replacement take? Hardware = high. Software = low. |
| Compliance Scope (comp) | 0.20 | How many regulations cover this component? More = harder to migrate. |

### The Formula

```
CAD(c) = w_alg * d_alg(c) + w_api * d_api(c) + w_key * d_key(c)
        + w_proc * d_proc(c) + w_comp * d_comp(c)
```

Each dimension score d_i is in [0, 1]. Each weight w_i is in [0, 1] with sum = 1.

Default weights: w_alg=0.25, w_api=0.20, w_key=0.15, w_proc=0.20, w_comp=0.20.

### CAD Tiers

| CAD Score | Tier | Migration Phase |
|---|---|---|
| [0.0, 0.2) | Very Low | Phase 1 (0-12 months) |
| [0.2, 0.4) | Low | Phase 1 (0-12 months) |
| [0.4, 0.6) | Medium | Phase 2 (12-36 months) |
| [0.6, 0.8) | High | Phase 3 (36-60 months) |
| [0.8, 1.0] | Very High | Phase 3 (36-60 months) |

---

## 3. Key Findings (22 Components, 1,847 SIFI Endpoints)

### Headline Numbers

- **39.3%** of SIFI cryptographic endpoints carry High or Very High CAD
- **22.3%** of the estate is F5 BIG-IP hardware (CAD = 1.00) — the worst case
- F5 BIG-IP hardware requires a **90-month** procurement + compliance cycle
- **55.5%** of endpoints (12 components) can migrate in Phase 1 (<=12 months)
- **Estate-weighted CAD = 0.457** — Medium-High tier for the portfolio as a whole

### Component Extremes

| Component | CAD | Tier |
|---|---|---|
| F5 BIG-IP LTM (Hardware) | 1.00 | Very High |
| Cisco ASA (Hardware) | ~0.85 | Very High |
| HSM (Thales/nCipher) | ~0.75 | High |
| OpenSSL 3.x | 0.10 | Very Low |
| Apache httpd | 0.10 | Very Low |
| Nginx | ~0.15 | Very Low |

### Phase Breakdown

| Phase | Timeline | Components | Endpoint % |
|---|---|---|---|
| Phase 1 | 0-12 months | 12 | 55.5% |
| Phase 2 | 12-36 months | 3 | 5.2% |
| Phase 3 | 36-60 months | 7 | 39.3% |

---

## 4. Formal Results

### Definition 1 (Cryptographic Agility Debt)

CAD(c) = sum over i of w_i * d_i(c), where sum(w_i) = 1 and each d_i in [0,1].

### Proposition 1 (Phase 3 Condition)

If estate_cad >= 0.40, then there exists at least one component type c* in the estate such that CAD(c*) >= 0.60 (Phase 3 tier). This ensures that a Medium-High estate-level score is not an artifact of averaging — a true long-cycle component must exist.

**Proof sketch:** By contradiction. Assume all components have CAD < 0.60. Then estate_cad < 0.40 (since estate_cad is an endpoint-weighted average). Contradiction.

The reference estate has estate_cad = 0.457 >= 0.40, and F5 BIG-IP hardware with CAD = 1.00 confirms the Phase 3 component exists.

---

## 5. Code Architecture

```
src/
  cad.py            -- CadDimension, CadComponent, CadMetric (formula)
  experiments.py    -- Orchestrates: load data -> compute CAD -> figures -> results.tex
  figures/
    common.py       -- set_ieee_style() for all matplotlib figures
    fig2_cad_distribution.py  -- bar chart: CAD score by component
    fig3_dimension_radar.py   -- radar chart: 5-dimension breakdown for top components
    fig4_phase_migration.py   -- stacked bar: components by phase
    fig5_estate_pareto.py     -- trade-off frontier: migration months vs CAD
data/
  pqc_cad_data.json           -- 22 components with 5-dimension scores, source citations
results/
  results.tex                 -- auto-generated macros (never edit manually)
tests/
  test_cad.py                 -- 37 unit tests
```

### Key Classes

**CadDimension** (src/cad.py): Represents one dimension score with a name and value [0, 1].

**CadComponent** (src/cad.py): A named infrastructure component with 5 dimensions and an endpoint count.

**CadMetric** (src/cad.py): Computes CAD scores, tiers, phases, and estate-weighted CAD.

### Running the Experiments

```bash
python3 -m src.experiments --data-dir data --results-dir results
# Generates: results/results.tex, results/fig2_*.pdf through fig5_*.pdf
```

### Running the Tests

```bash
python3 -m pytest tests/ -v
# Expected: 37 passed
```

### Building the Paper

```bash
cd paper/
pdflatex paper10.tex
bibtex paper10
pdflatex paper10.tex
pdflatex paper10.tex
# Expected: paper10.pdf, no ! errors
```

---

## 6. Data Notes

The dataset (`data/pqc_cad_data.json`) is a calibrated synthetic dataset derived from publicly available sources:
- NIST IR 8547 (migration guidance)
- F5 Networks product lifecycle documentation
- Thales HSM product datasheets
- CVSSv3 scoring for algorithm vulnerability
- PCI DSS, SOX, GLBA compliance scope mappings

**No Amex proprietary data is included.** The dataset represents a generic SIFI network topology calibrated to match public sector disclosures.

---

## 7. Macro Reference (results.tex)

Key macros generated by experiments.py:

| Macro | Value | Description |
|---|---|---|
| \NumComponents | 22 | Total components surveyed |
| \TotalEndpoints | 1,847 | Total SIFI cryptographic endpoints |
| \EstateCad | 0.457 | Endpoint-weighted estate CAD |
| \HighBurdenEndpointPct | 39.3 | % endpoints with High/Very High CAD |
| \NumHighBurden | 7 | Component types with High/Very High CAD |
| \FfiveHwCadScore | 1.00 | F5 BIG-IP hardware CAD score |
| \FfiveHwEndpointPct | 22.3 | % estate that is F5 BIG-IP hardware |
| \FfiveHwMigrationMonths | 90 | F5 BIG-IP hardware migration cycle (months) |
| \OpenSslCadScore | 0.10 | OpenSSL 3.x CAD score (best case) |
| \PhaseOneComponents | 12 | Components in Phase 1 |
| \PhaseThreeComponents | 7 | Components in Phase 3 |

**Rule:** Never hardcode these numbers in the .tex file. Always use macros.

---

## 8. Known Issues and Fixes

**Macro name digit rule:** Macro `\F5HwCadScore` caused `! LaTeX Error: Missing \begin{document}` because LaTeX stops parsing control sequences at the first digit. Fixed by renaming to `\FfiveHwCadScore` (and all F5-related macros).

**No Unicode in .tex:** All symbols use LaTeX math mode. No Greek letters or arrows as Unicode.

**No `\qed` in proofs:** The `amsthm` proof environment auto-appends the QED square. Explicit `\qed` produces a double symbol.

---

## 9. NIW Relevance

This paper directly supports the NIW petition by demonstrating:
1. **Original research** — First formal CAD metric in the literature
2. **SIFI expertise** — Deep knowledge of financial infrastructure crypto requirements
3. **National importance** — PQC migration at SIFIs is a federal mandate per NIST IR 8547 and Executive Order 14028
4. **Quantitative rigor** — Formal proposition, 37 unit tests, public dataset

**Venue:** IEEE TIFS (Transactions on Information Forensics and Security) — top-tier peer-reviewed journal in the security domain.
