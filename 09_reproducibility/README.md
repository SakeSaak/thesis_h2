# Implementation-Risk Differentials in Hydrogen Technology Pathways

**Master's Thesis — MSc Econometrics & Operations Research, Financial Track**
**Vrije Universiteit Amsterdam, 2025-2026**

**Author:** Sake Saakstra
**Supervisor:** prof. Siem Jan Koopman
**Second reader (proposed):** dr. Nadine Ketel

## Abstract

This thesis examines whether the EU Carbon Border Adjustment Mechanism (CBAM) acts as a quasi-experimental shock that differentially affects the implementation hazard of hydrogen production projects. Using project-level data from three independent sources (v7 curated S&P sample, S&P Global Market Intelligence master table, IEA Hydrogen Projects Database), we apply discrete-time hazard models, Bayesian time-varying parameter state-space models, and difference-in-differences identification strategies. The cross-sectional EU-specific association is robust associationally but FRAGILE under modern small-sample inference (Wild Cluster Bootstrap, cluster-permutation, Honest DiD bounds), and the triple-difference null is robust across all four inference methods. We conclude that CBAM-driven cancellation hazard differentials cannot be causally identified given current power and parallel-trends evidence, framed as a *honest informative null* in the Ketel (2023) tradition.

## Repository structure

```
thesis_h2/
├── 01_data/
│   ├── raw/                 # Raw data exports (S&P, IEA, EUA prices)
│   └── intermediate/        # Cleaned curated samples (v7 with 714 projects)
├── 02_documents/            # Thesis documents, supervisor correspondence
├── 03_scripts_python/       # Core analysis scripts
├── 04_analysis_pijler*/     # Pijler 0 main analyses (hazard model, TVP, real options)
├── 06_thesis_extensions/    # Robustness extensions
│   ├── 01_bayesian_methodology/   # Pijler 0 Bayesian re-analysis
│   ├── 05_state_space_tvp/        # TVP state-space (Chapter 6)
│   ├── 06_real_options_calibration/  # Real options theoretical framework
│   ├── 07_event_study/             # EUA event study
│   ├── 08_cbam_event_study/        # CBAM political agreement event study (equity)
│   ├── 09_sp_global_cbam/          # Pijler 1: S&P Global cross-sectional + DiD
│   ├── 10_iea_cross_validation/    # Pijler 2: IEA cross-validation
│   ├── 11_v7_sp_matching/          # Pijler 3: v7→S&P matching, augmented hazard
│   └── 12_advanced_robustness/     # Pijler 4: Honest DiD, WCB, permutation, Bayesian, hazard diagnostics
├── 07_thesis_drafts/        # LaTeX thesis chapters
├── 08_communicatie/         # Email correspondence supervisors
└── 09_reproducibility/      # This folder — README, data dictionary, makefile
```

## Quick reproduction

Requires Python 3.13 (Anaconda) and R 4.x. To replicate all results:

```bash
make all          # Reproduces all analyses end-to-end
make pijler1      # Just S&P Global analysis
make pijler4      # Just advanced robustness suite (Pijler 4)
make thesis       # Recompile LaTeX thesis chapters
```

Or manually:

```bash
# Pijler 1-4 (estimated total runtime: 15-25 minutes)
cd 06_thesis_extensions/09_sp_global_cbam && python *.py
cd 06_thesis_extensions/10_iea_cross_validation && python *.py
cd 06_thesis_extensions/11_v7_sp_matching && python *.py
cd 06_thesis_extensions/12_advanced_robustness && python *.py
```

## Data sources

| Source | Version | Records | Used in |
|---|---|---|---|
| v7 curated S&P sample | March 2025 | 714 projects, 43 events | Pijler 0 (Chapters 5-7) |
| S&P Global master table | 19 May 2026 | 3,343 projects, 206 events | Pijler 1 (Chapter 8) |
| IEA Hydrogen Projects Database | Sept 2025 + Feb 2026 correction | 2,625 projects | Pijler 2 (Chapter 8) |
| EUA spot prices (Refinitiv) | Daily 2010-2026 | ~4,200 obs | Real options + event study |

See `data_dictionary.md` for variable definitions and coding conventions.

## Pre-registration

This thesis follows an explicit pre-registration. The pre-registration document is in `02_documents/preregistration.pdf` (committed before any cross-sectional CBAM analysis was performed).

## Method overview

- **Identification strategy:** triangulation across 4 pijlers (curated sample, S&P primary, IEA cross-validation, v7→S&P matching) and 4 inference methods (asymptotic cluster-robust SE, Wild Cluster Bootstrap, permutation, Bayesian)
- **Key methods:** discrete-time logit hazard, Cox PH cross-check, Bayesian TVP state-space (PyMC), Honest DiD bounds (Rambachan-Roth 2023), DiD/event-study identification
- **Inference:** all DiD specs reported with both asymptotic and small-sample-robust p-values (WCB, permutation)

## Robustness suite (Pijler 4)

1. **Honest DiD bounds** (Rambachan-Roth 2023) — breakdown M̄ on focal ATT
2. **Wild Cluster Bootstrap** (Cameron-Gelbach-Miller 2008, Roodman et al 2019) — year + sponsor clustering
3. **Permutation inference** — unit-level + cluster-level
4. **Bayesian DiD** with modern Vehtari et al 2021 diagnostics
5. **Hazard model diagnostics** — Hosmer-Lemeshow, AUC, calibration, Cox PH cross-check, Schoenfeld residuals, GLMM frailty
6. **Out-of-sample CV** — 5-fold + rolling-window time-based
7. **Roth-Sant'Anna functional form sensitivity** — LPM/logit/probit comparison

## Software dependencies

See `requirements.txt`. Critical packages:
- Python 3.13, pandas 2.2, numpy 2.1, scipy 1.15
- statsmodels 0.14, scikit-learn 1.6
- pymc 6.0, arviz 1.1 (for Bayesian analysis)
- lifelines 0.30 (for Cox PH)
- cvxpy 1.8 (for Honest DiD LP solver)
- matplotlib 3.10

## Reproducibility notes

- All random seeds set to `42` for stochastic procedures
- All bootstrap replications: B=999 (WCB) or B=2999 (permutation)
- All Bayesian samplings: 2 chains × 2000 draws + 1000 warmup
- Results files saved per-analysis under `*/results/` with CSV format
- All figures saved as PDF at 120 dpi

## License

Code: MIT License (see LICENSE)
Data: Academic use only. v7 sample provided under restricted use agreement.

## Citation

Saakstra, S. (2026). *Implementation-Risk Differentials in Hydrogen Technology Pathways*. MSc Thesis, VU Amsterdam.

## Contact

For questions about the analysis or to request access to v7 curated sample, contact the author.
