# Reproducibility Guide

This document provides detailed step-by-step instructions to reproduce all results in the thesis.

## System requirements

- macOS 12+ or Linux (tested on macOS 14 + Ubuntu 22.04)
- Python 3.13 via Anaconda
- R 4.3+ (optional, for some Pijler 0 cross-checks)
- LaTeX (TeX Live 2024 or newer) for thesis compilation
- ~5 GB disk space (data + intermediate files + figures)
- ~8 GB RAM (PyMC sampling)
- Runtime: 20-30 minutes for full pipeline

## Setup steps

```bash
# 1. Clone the repository
git clone <repo-url> thesis_h2
cd thesis_h2

# 2. Create conda environment
conda create -n thesis_h2 python=3.13 -y
conda activate thesis_h2

# 3. Install Python packages
pip install -r 09_reproducibility/requirements.txt

# 4. Place restricted data files (NOT included in repo)
# Copy the following to 01_data/raw/:
#   - Hydrogen projects master data table.xlsx  (S&P Global, 19 May 2026)
#   - Hydrogen Production Projects Database - September 2025_correction_Feb26.xlsx  (IEA)

# 5. Verify data integrity
python -c "import pandas as pd; df=pd.read_csv('01_data/intermediate/blueccs_project_level_for_R.csv'); print(f'v7 sample: {df.shape}, events: {df[\"event_any\"].sum()}')"
# Expected output: v7 sample: (714, 11), events: 43
```

## Run pipeline

```bash
cd 09_reproducibility
make all
```

Or step-by-step:

```bash
# Pijler 0 — already in 04_analysis_pijler0/ (legacy structure)
# These are the v7 hazard model, TVP state-space, real options

# Pijler 1 — S&P primary analysis
cd 06_thesis_extensions/09_sp_global_cbam
python 01_sp_logit_cross_sectional.py     # Cross-sectional logit M1-M4
python 02_sp_did_vintage_cohort.py        # Project vintage DiD
python 03_sp_eu_subset_analysis.py        # EU-only paradox
python 04_sp_placebo_grid.py              # 5-placebo grid (2015, 2017, 2019, 2020, 2021)
python 05_sp_triple_difference.py         # EU×CBAM×Post

# Pijler 2 — IEA cross-validation
cd ../10_iea_cross_validation
python 01_iea_logit_operational.py
python 02_iea_eu_subset.py

# Pijler 3 — v7→S&P matching
cd ../11_v7_sp_matching
python 01_match_v7_to_sp.py
python 02_augmented_hazard.py

# Pijler 4 — Advanced robustness
cd ../12_advanced_robustness
python 01_honest_did_v2.py                # Rambachan-Roth bounds
python 02_wild_cluster_bootstrap.py       # Roodman-MacKinnon WCB
python 03_permutation_inference.py        # Fisher permutation
python 04_bayesian_diagnostics_v2.py      # Bayesian DiD + Vehtari diagnostics
python 05_hazard_diagnostics_suite.py     # Hosmer-Lemeshow, AUC, Cox PH, Schoenfeld, GLMM
python 06_oos_cv_and_functional_form.py   # Cross-validation + Roth-Sant'Anna

# Compile thesis chapters
cd ../../07_thesis_drafts/chapter8_cbam
pdflatex -interaction=nonstopmode chapter8_cbam_full.tex
pdflatex -interaction=nonstopmode chapter8_cbam_full.tex
pdflatex -interaction=nonstopmode chapter8_cbam_full.tex
```

## Expected outputs

Each Pijler-X folder will produce:
- `results/*.csv` — All numerical results in CSV
- `figures/*.pdf` — All figures in PDF at 120 dpi

Pijler 4 produces specifically:
| File | What it contains |
|---|---|
| `12_advanced_robustness/results/honest_did_bounds.csv` | Rambachan-Roth bounds across M̄ grid |
| `12_advanced_robustness/results/wcb_summary.csv` | Wild Cluster Bootstrap p-values |
| `12_advanced_robustness/results/permutation_summary.csv` | Permutation inference results |
| `12_advanced_robustness/results/bayesian_diagnostics_full.csv` | Bayesian convergence diagnostics |
| `12_advanced_robustness/results/hazard_diagnostics_summary.csv` | Hazard model diagnostics summary |
| `12_advanced_robustness/results/oos_cv_kfold.csv` | 5-fold CV results |
| `12_advanced_robustness/results/oos_cv_rolling.csv` | Rolling-window CV results |
| `12_advanced_robustness/results/functional_form_sensitivity.csv` | LPM/logit/probit comparison |

## Random seeds

All stochastic procedures use seed=42 (np.random.seed, sampling random_state). To verify exact reproducibility:

```bash
python -c "import numpy as np; np.random.seed(42); print(np.random.rand(3))"
# Expected: [0.37454012 0.95071431 0.73199394]
```

If your output differs from the reported numbers by more than ±0.001 (numerical noise) or rejection/acceptance changes for any test, please report an issue.

## Known issues and version-specific caveats

- `arviz 1.1.0` deprecated `hdi_prob` → `ci_prob`. Our scripts use the new name.
- `arviz.plot_posterior` removed; we use `plot_forest` as substitute in some places.
- `lifelines 0.30.x` requires `event_col` and `duration_col` as strings (not column references).
- PyMC sampler initialization may differ slightly across hardware; convergence diagnostics (R̂, ESS) should be consistent.
- Wild cluster bootstrap with sponsor-clustering takes ~2 minutes (large G).

## Audit checklist

Top-tier reproducibility audit items (per Christensen-Miguel guidelines):

- [x] Code public and version-controlled
- [x] All data sources documented in `data_dictionary.md`
- [x] Random seeds set
- [x] Pre-registration available (`02_documents/preregistration.pdf`)
- [x] Methods + parameter choices documented in inline comments
- [x] Results CSV files committed for cross-check
- [x] Figures generated programmatically (not edited externally)
- [x] LaTeX source committed
- [x] Sensitivity analyses included (4 prior sensitivities, 4 inference methods, 3 functional forms)
- [x] Replication time estimated: 20-30 min full pipeline
