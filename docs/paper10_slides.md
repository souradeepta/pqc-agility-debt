# Cryptographic Agility Debt: Measuring PQC Migration Readiness in SIFI Environments

**Souradeepta Biswas** | sdb.svnit@gmail.com
IEEE TIFS Submission | April 2026

---

## Slide 1: The PQC Deadline Is Real

**August 2024:** NIST finalized three post-quantum cryptography standards:
- FIPS 203 (ML-KEM) — key encapsulation
- FIPS 204 (ML-DSA) — digital signatures
- FIPS 205 (SLH-DSA) — hash-based signatures

**NIST IR 8547:** Federal agencies and critical infrastructure must migrate by 2030-2035.

**The question nobody has answered:** *How hard is migration, and for which components?*

---

## Slide 2: The Gap — No Formal Migration Difficulty Metric

Practitioners know migration difficulty varies enormously:
- OpenSSL 3.x patch: **weeks**
- F5 BIG-IP hardware replacement: **7.5 years**

But there is **no formal metric** to quantify this gap.

Without a metric:
- CISOs cannot prioritize migration spend
- Regulators cannot assess readiness
- Engineers cannot allocate remediation timelines

**This paper introduces Cryptographic Agility Debt (CAD).**

---

## Slide 3: What is Cryptographic Agility Debt?

**CAD(c) = weighted sum of 5 migration difficulty dimensions**

| Dimension | Weight | Captures |
|---|---|---|
| Algorithm hardness | 0.25 | Quantum vulnerability of current algorithm |
| API surface | 0.20 | Blast radius of crypto interface changes |
| Key infrastructure | 0.15 | HSM/hardware key rotation difficulty |
| Procurement cycle | 0.20 | Time to replace/upgrade component |
| Compliance scope | 0.20 | Regulatory burden of migration |

**Range:** CAD in [0, 1]. Higher = harder to migrate.

---

## Slide 4: CAD Tiers and Migration Phases

| CAD Score | Tier | NIST-Aligned Phase | Timeline |
|---|---|---|---|
| [0.0, 0.2) | Very Low | Phase 1 | 0-12 months |
| [0.2, 0.4) | Low | Phase 1 | 0-12 months |
| [0.4, 0.6) | Medium | Phase 2 | 12-36 months |
| [0.6, 0.8) | High | Phase 3 | 36-60 months |
| [0.8, 1.0] | Very High | Phase 3 | 36-60 months |

Phase 3 components require hardware replacement, HSM procurement, and multi-year regulatory approval cycles.

---

## Slide 5: Study Scope — 22 Components, 1,847 SIFI Endpoints

**Dataset:** Calibrated synthetic SIFI network topology derived from public sources (NIST IR 8547, vendor product documentation, PCI DSS/SOX/GLBA scope mappings).

**Components surveyed:** Software TLS stacks, hardware load balancers, HSMs, PKI infrastructure, VPN appliances, API gateways, database encryption modules.

**Endpoints:** 1,847 cryptographic endpoints across 22 component types in a representative SIFI environment.

---

## Slide 6: Headline Results

- **39.3%** of SIFI cryptographic endpoints carry High or Very High CAD
- **55.5%** of endpoints can migrate in Phase 1 (<=12 months)
- **5.2%** of endpoints require Phase 2 (12-36 months)
- **Estate-weighted CAD = 0.457** (Medium-High tier)

The 39.3% Phase 3 burden represents the "hard tail" of PQC migration — components that cannot be migrated within standard software update cycles.

---

## Slide 7: The Extremes — F5 vs OpenSSL

### Worst Case: F5 BIG-IP LTM (Hardware Appliance)
- CAD = 1.00 (maximum possible)
- All 5 dimensions at maximum score
- 22.3% of SIFI endpoints (412 of 1,847)
- Migration requires hardware procurement + field replacement
- Estimated cycle: 90 months (7.5 years)

### Best Case: OpenSSL 3.x / Apache httpd
- CAD = 0.10 (minimum in dataset)
- Algorithm hardness is only elevated dimension
- Package manager update + config change
- Migration cycle: <30 days

---

## Slide 8: Component CAD Distribution (Figure 2)

[Figure 2: Bar chart showing CAD scores for all 22 components, colored by tier (Very Low=green, Low=yellow-green, Medium=yellow, High=orange, Very High=red)]

Key observations:
- Bimodal distribution: 12 components cluster below 0.20, 7 cluster above 0.60
- Middle tier (Medium) has only 3 components
- Hardware appliances (F5, Cisco ASA) and HSMs occupy the High/Very High tier

---

## Slide 9: Dimension Analysis — Why F5 Scores 1.00 (Figure 3)

[Figure 3: Radar chart comparing F5 BIG-IP hardware vs OpenSSL across all 5 dimensions]

F5 BIG-IP LTM (Hardware) dimension scores:
- Algorithm hardness: 1.00 — RSA/ECC-only, no PQC-capable ASICs
- API surface: 1.00 — handles all TLS termination for the estate
- Key infrastructure: 1.00 — hardware key storage, no soft-rotation path
- Procurement cycle: 1.00 — 90-month replacement cycle with capital approval
- Compliance scope: 1.00 — covered by PCI DSS, SOX, GLBA, OCC guidance simultaneously

---

## Slide 10: Migration Roadmap — 3-Phase Alignment (Figure 4)

[Figure 4: Stacked bar showing component distribution across Phase 1/2/3, with endpoint counts]

**Phase 1 (0-12 months):** 12 components, 55.5% of endpoints
- OpenSSL, Nginx, Apache, software VPN clients, API gateway software
- Action: Package update + algorithm config flag

**Phase 2 (12-36 months):** 3 components, 5.2% of endpoints
- Intermediate appliances with firmware upgrade paths
- Action: Vendor firmware + key rotation

**Phase 3 (36-60 months):** 7 components, 39.3% of endpoints
- F5 hardware, Cisco ASA, HSMs, hardware PKI CAs
- Action: Capital budget + procurement + regulatory pre-approval

---

## Slide 11: Proposition 1 — Estate-Level Guarantee

**Proposition 1:** If estate_cad >= 0.40, then there exists at least one component type c* in the estate with CAD(c*) >= 0.60 (Phase 3 tier).

**Why this matters:** An estate-weighted score of 0.457 is not an artifact of averaging many medium-CAD components. By Proposition 1, at least one component with a 7.5-year migration cycle must exist.

For the reference estate: estate_cad = 0.457 >= 0.40, confirmed by F5 BIG-IP hardware (CAD = 1.00).

**Regulatory implication:** A SIFI reporting estate_cad >= 0.40 cannot claim readiness for Phase 3 components without explicit hardware procurement plans.

---

## Slide 12: Regulatory Threshold Recommendations

Based on CAD tiers and NIST IR 8547 phase alignment:

| Estate CAD | Regulatory Classification | Required Action |
|---|---|---|
| < 0.30 | Ready (Phase 1/2 only) | Standard migration plan |
| 0.30-0.40 | Elevated (Phase 2 components present) | Enhanced monitoring |
| 0.40-0.60 | High Burden (Phase 3 exists, Prop. 1) | Board-level reporting required |
| > 0.60 | Critical (majority Phase 3) | Regulatory pre-filing required |

Reference estate: 0.457 -> High Burden tier -> Board-level reporting.

---

## Slide 13: Comparison with Prior Work

| Approach | Scope | Quantitative? | SIFI-calibrated? |
|---|---|---|---|
| NIST IR 8547 | Migration phases (qualitative) | No | No |
| NSA CNSA 2.0 | Algorithm lists only | No | No |
| Quantum Economic Development Consortium (QEDC) | Survey-based | Ordinal only | No |
| **CAD (this paper)** | **Component-level, 5-dimension weighted** | **Yes [0,1]** | **Yes (1,847 endpoints)** |

CAD is the first metric that supports quantitative regulatory reporting and prioritization.

---

## Slide 14: Open-Source Artifacts

All code and data released at: https://github.com/souradeepta/pqc-agility-debt

- `src/cad.py` — CAD metric implementation (CadDimension, CadComponent, CadMetric)
- `src/experiments.py` — Full experiment pipeline
- `data/pqc_cad_data.json` — 22-component calibrated SIFI dataset with source citations
- `tests/test_cad.py` — 37 unit tests (100% pass rate)
- `results/results.tex` — Auto-generated LaTeX macros

**Usage:** Other researchers can plug in their own component dimension scores and compute CAD, tiers, and phase assignments using the same framework.

---

## Slide 15: Conclusions and Future Work

**Contributions:**
1. First formal 5-dimension CAD metric for PQC migration difficulty
2. First systematic CAD measurement across 22 SIFI infrastructure components
3. Proposition 1: Estate-level guarantee linking aggregate score to Phase 3 components
4. Three-phase migration roadmap aligned with NIST IR 8547
5. Regulatory threshold recommendations for SIFI reporting

**Key finding:** 39.3% of SIFI cryptographic endpoints are locked in Phase 3 (36-60 month migration), driven by hardware appliances with CAD = 1.00. The 90-month F5 procurement cycle means SIFIs that have not initiated hardware replacement planning today will not meet a 2030 migration target.

**Future work:** Longitudinal tracking of CAD as vendors release PQC-capable hardware, extension to quantum key distribution (QKD) integration scenarios.

---

*Souradeepta Biswas | sdb.svnit@gmail.com | IEEE TIFS 2026*
