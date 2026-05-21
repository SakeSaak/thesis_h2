# Changelog

Major thesis milestones, categorized per analytical contribution (pijler).
For full commit history, see `git log`.

---

## [Unreleased] — May 2026

### Repository housekeeping
- Professional `README.md` with abstract, key findings, repository structure, reproduction instructions
- `LICENSE` (CC BY-NC-SA 4.0) and `CITATION.cff` for academic citation
- `requirements.txt` with full Python dependency list
- `.gitignore` expanded to exclude bulk ENTSO-E energy price data and other regeneratable intermediate files
- Top-level cleanup: legacy planning documents moved to `docs/archive/2026-05_pre_track_ABC/`

---

## Track C — Stakeholder Deliverables (commit `7f6e9da`)

### Added
- `07_stakeholder_briefings/POLICY_BRIEFINGS_v2/`:
  - `01_EU_DG_CLIMA_briefing.md` — 4 concrete policy recommendations for EU Commission
  - `02_Gasunie_BL_Waterstof_briefing.md` — strategic lessons for HyNetwork business case (Nederlands)
  - `03_Sponsors_thesis_briefing.md` — supervisor + sponsor status briefing
  - `README.md` — navigation + methodological context

---

## Track B — Counterfactual Scenarios (commit `1f2b91a`)

### Added — Pijler 36
- `06_thesis_extensions/14_counterfactual/46_counterfactual_scenarios.py`
- Five scenarios with bootstrap 95% CIs:
  - **S1**: EU 45Q-equivalent → +4 FIDs, +3.40 Mt/y CO₂
  - **S2**: EU offtake-mandate → +83 FIDs, +858 kt/y H₂
  - **S3**: UK switch to 45Q → +7 FIDs, +12.25 Mt/y CO₂
  - **S4**: OECD China-FYP-equivalent → +98 FIDs, +976 kt/y H₂
  - **S5**: EU sector-optimal mix → **+113 FIDs, +7.83 Mt/y CO₂ + 1.76 Mt/y H₂**
- 500-iteration bootstrap project-level resampling + ATE Gaussian uncertainty

---

## Track A — Top-tier Foundation (commits `addb536`, `1a2504d`, `a7849ab`)

### Added — Pijler 40: Real-options × mechanism design (`a7849ab`)
- `06_thesis_extensions/13_theoretical/PIJLER40_REAL_OPTIONS_MECHANISM_DESIGN.md` (1,732 words)
- `45_real_options_numerical.py` — Dixit-Pindyck V*/I implementation
- Sector calibration: chemical/refinery σ=0.12 (V*/I=3.04), power & heat σ=0.40 (V*/I=7.15)
- Four mechanism types characterized: output-credit, capex-grant, cluster-tender, offtake-mandate
- Empirical match: σ-channel mechanisms stronger in high-σ sectors

### Added — Pijler 39: Honest DiD bounds (`1a2504d`)
- `44_honest_did_bounds.py` — Rambachan-Roth (2023) relative-magnitudes bounds
- v2 methodology: average ATT(e=0,1,2) + median pre-trend (robust to single-period noise)
- China FYP M\* = 1.50 (ROBUST under M ≤ 1.5)
- US 45Q M\* = 0.20, EU IF M\* = 0.00, UK Track M\* = 0.00 (sensitivity-bounded)

### Added — Pijler 34: Offtake-effect (`addb536`)
- `43_offtake_effect_identification.py` — multi-method causal identification
- ATE convergence: LPM −0.131, PSM −0.111, IPWRA −0.133, Oster-adj −0.125
- **Oster δ\_null = 20.23** — exceptional sensitivity robustness
- Sector heterogeneity: power & heat −22.8 pp, refinery −25.7 pp, chemical NS
- Policy interactions: UK Track complement, China FYP offset, EU IF marginal

---

## Pre-Track foundation (Pijlers 1-33)

Earlier work in repository established:

- **Pijlers 16-23**: Cox proportional hazards survival analysis with competing risks
- **Pijler 24c**: Time-varying parameter DiD with threshold + AR(1) + random walk (commit `cabff13`)
- **Pijler 25-28**: Cross-jurisdictional DiD for US 45Q, EU IF, UK Track-1, China FYP
- **Pijler 29**: Real options framework first draft (markdown)
- **Pijler 30**: Causal forest HTE with BLP omnibus test (commit `eb2d1c0`)
- **Pijler 31**: Sectoral triple-DiD (16 sector × policy interactions tested)
- **Pijler 32**: Modern DiD robustness: TWFE + Sun-Abraham + BJS-imputation convergence (commit `cabff13`)
- **Pijler 33**: Subgroup DiD validation

---

## Original journal paper (`00_paper/current/`)

Initial paper version `blueCCS_paper_final.tex` (~10,000 words) established:
- Cross-sectional cancellation rate differentials
- Survival analysis baseline
- Early policy-effect estimates

This paper is the foundation; the thesis extends it with the methodological and theoretical contributions in `06_thesis_extensions/`.

---

*Full per-commit history: `git log --oneline`*
