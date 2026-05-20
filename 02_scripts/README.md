# Implementation-Risk Differentials in Hydrogen Technology Pathways

**Replication package for Saakstra (2026)**, *"Implementation-Risk Differentials in Hydrogen Technology Pathways: Evidence from a Segmented Investment Ecosystem and Carbon-Price-Conditional Risk"*, Working Paper, Vrije Universiteit Amsterdam.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![R 4.3+](https://img.shields.io/badge/R-4.3+-276DC3.svg)](https://www.r-project.org/)

---

## Headline findings

This paper documents four substantive findings about hydrogen project realisation:

1. **Segmented investment ecosystems** — Blue_CCS and PEM projects operate in partially distinct populations. McFadden R² = 0.70 in the propensity model; both PSM and entropy balancing fail to find an exchangeable subsample.
2. **Robust hazard differential across 11 estimators** — Blue_CCS HR ∈ [5, 14] across all specifications. Cox PH = 11.93 [4.67, 30.49], preferred doubly robust = 6.87.
3. **Terminal cancellation, not real-option delay** — Fine-Gray decomposition: HR = 13.19 [5.28, 32.91] for terminal cancellation vs HR = 1.20 [0.34, 4.26] for on-hold. Blue_CCS projects do not pause; they terminate.
4. **Carbon-price-conditional risk premium** — Blue_CCS × EUA interaction = −2.51 (p < 0.0001). Predicted HR collapses from 673 [215, 2104] at low carbon prices to 4.67 [2.14, 10.16] at high carbon prices.

---

## Citation

If you use this code or data, please cite:

```bibtex
@unpublished{Saakstra2026,
  author = {Saakstra, Sake},
  title  = {Implementation-Risk Differentials in Hydrogen Technology Pathways:
            Evidence from a Segmented Investment Ecosystem and
            Carbon-Price-Conditional Risk},
  note   = {Working Paper, Vrije Universiteit Amsterdam},
  year   = {2026},
  url    = {https://github.com/sakesaakstra/blueCCS-hydrogen}
}
```

A `CITATION.cff` file is also provided for automatic citation export.

---

## Repository structure

```
blueCCS-hydrogen/
├── README.md                      # this file
├── LICENSE                        # MIT
├── CITATION.cff                   # machine-readable citation
├── requirements.txt               # Python dependencies (locked)
├── renv.lock                      # R dependencies (locked)
├── .gitignore                     # standard ignore patterns
│
├── data/
│   ├── README.md                  # data acquisition instructions
│   ├── raw/                       # raw downloads (gitignored)
│   └── processed/                 # cleaned panel CSVs
│
├── scripts/
│   ├── 01_yahoo_finance_download.py
│   ├── 02_entsoe_power_download.py
│   ├── ...                        # (data prep scripts 01-22)
│   ├── 23_psm_overlap_diagnostics.py
│   ├── 24_paper_v3_robustness_battery.py    # 11-estimator battery
│   ├── 25d_competing_risks_frailty_final.R  # Fine-Gray + frailty
│   ├── 26_marginal_effects_hazard_curves.py # delta method
│   ├── 27_leave_one_region_out.py           # LOR robustness
│   └── prepare_h2_data_for_R.py             # Python→R handoff
│
├── output_data/                   # CSV exports of all numerical results
│   ├── master_panel_daily.csv
│   ├── 26_marginal_effects.csv
│   ├── 27_lor_results.csv
│   └── 25d_competing_risks_frailty_summary.csv
│
├── figures/                       # output figures (PNG)
│   ├── fig_marginal_effects_eua.png         # Figure 1 in paper
│   ├── fig_lor_forest.png                   # Figure 2 in paper
│   ├── fig_marginal_effects_4panel.png      # Appendix A1
│   ├── fig_ps_density.png                   # Section 3.2
│   ├── fig_common_support.png               # Appendix A2
│   ├── fig_love_plot.png                    # Section 3.3
│   └── fig_weight_distributions.png         # Diagnostics
│
└── paper/
    ├── blueCCS_paper.tex          # LaTeX source
    ├── blueCCS_paper.pdf          # compiled paper
    └── figures/                   # symbolic link or copies of PNGs
```

---

## Reproduction

### 1. Clone the repository

```bash
git clone https://github.com/sakesaakstra/blueCCS-hydrogen.git
cd blueCCS-hydrogen
```

### 2. Set up the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate            # Windows
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Set up the R environment

```r
install.packages("renv")
renv::restore()
```

### 4. Acquire the raw data

See `data/README.md` for detailed instructions. Briefly:

- **IEA Hydrogen Projects Database**: download the March 2024 release from <https://www.iea.org/data-and-statistics/data-product/hydrogen-projects-database> and place in `data/raw/`.
- **ENTSO-E power prices**: register at <https://transparency.entsoe.eu>, obtain an API key, set `ENTSOE_API_KEY` in your shell environment.
- **EUA prices**: scripts download ICAP price CSVs automatically.
- **FRED, Yahoo Finance, Baker-Bloom-Davis EPU**: scripts download via public APIs.

### 5. Run the analysis pipeline

```bash
# Build master panel from raw downloads
python scripts/01_yahoo_finance_download.py
python scripts/02_entsoe_power_download.py
# ... (run 01-22 in order, or use the orchestrator below)
python scripts/20_master_panel_assembly.py

# Run the eleven-estimator robustness battery
python scripts/24_paper_v3_robustness_battery.py

# Marginal effects + delta method (Figure 1, Table 5)
python scripts/26_marginal_effects_hazard_curves.py

# Leave-one-region-out (Table 6, Figure 2)
python scripts/27_leave_one_region_out.py

# Prepare data for R, then run Fine-Gray + frailty
python scripts/prepare_h2_data_for_R.py
Rscript scripts/25d_competing_risks_frailty_final.R
```

### 6. Compile the paper

```bash
cd paper
pdflatex blueCCS_paper.tex
pdflatex blueCCS_paper.tex          # second pass for cross-references
```

Total replication runtime: approximately 15--25 minutes on a standard laptop (M1/M2 Mac or equivalent), excluding data downloads.

---

## Output reproduction map

Each table and figure in the paper is produced by a specific script:

| Paper element | Script | Output file |
|---|---|---|
| Table 3 (11 estimators) | `24_paper_v3_robustness_battery.py` | `output_data/24_robustness_summary.csv` |
| Table 4 (4 macro interactions) | `26_marginal_effects_hazard_curves.py` | `output_data/26_interactions.csv` |
| Table 5 (3 EUA z-levels) | `26_marginal_effects_hazard_curves.py` | `output_data/26_marginal_effects.csv` |
| Table 6 (LOR robustness) | `27_leave_one_region_out.py` | `output_data/27_lor_results.csv` |
| Figure 1 (EUA marginal effects) | `26_marginal_effects_hazard_curves.py` | `figures/fig_marginal_effects_eua.png` |
| Figure 2 (LOR forest plot) | `27_leave_one_region_out.py` | `figures/fig_lor_forest.png` |
| Fine-Gray + frailty (Table 3, last rows) | `25d_competing_risks_frailty_final.R` | `output_data/25d_competing_risks_frailty_summary.csv` |
| Appendix A1 (4-panel marginal effects) | `26_marginal_effects_hazard_curves.py` | `figures/fig_marginal_effects_4panel.png` |
| Appendix A2 (common support) | `23_psm_overlap_diagnostics.py` | `figures/fig_common_support.png` |

---

## Methodology

The full methodology is detailed in the paper. Brief overview of the eleven estimators:

1. **GLM iid SE** (baseline discrete-time hazard)
2. **GLM cluster sponsor SE** (Wooldridge 2010)
3. **GLM cluster sponsor × region SE**
4. **Cox proportional hazards** (Cox 1972, with Schoenfeld test 1982)
5. **PSM caliper 0.05** (Rosenbaum & Rubin 1983, Caliendo & Kopeinig 2008)
6. **IPW stabilised** (Robins, Rotnitzky & Zhao 1994)
7. **Doubly robust AIPW** (Bang & Robins 2005) — *preferred*
8. **Entropy balancing** (Hainmueller 2012) — *informative failure*
9. **Firth penalised** (Firth 1993, Heinze & Schemper 2002)
10. **Fine-Gray subdistribution** (Fine & Gray 1999) — terminal vs delay
11. **Shared frailty Cox** (Therneau, Grambsch & Pankratz 2003)

Marginal effects with delta-method 95% CIs follow Wooldridge (2010). Leave-one-region-out analyses (Section 6.7) systematically exclude each of seven regions to test regional robustness.

---

## Data sources

| Variable group | Provider | Sample span | License |
|---|---|---|---|
| Project records | IEA Hydrogen Projects Database (March 2024) | to 2024-03 | CC BY-NC-SA |
| EUA carbon price | ICAP | 2010-2025 | Public |
| TTF gas futures | ICE Endex (via yfinance) | 2017-2026 | Yahoo ToS |
| Day-ahead power | ENTSO-E Transparency Platform | 2021-2026 | Free with registration |
| Equity prices | Yahoo Finance (`yfinance`) | 2010-2026 | Yahoo ToS |
| US macro (DGS10, etc.) | FRED, Federal Reserve Bank of St. Louis | 2010-2026 | Public |
| VIX | CBOE via FRED | 2010-2026 | Public |
| EPU index | Baker, Bloom & Davis (2016) | 2010-2026 | Public |

The processed master panel (`output_data/master_panel_daily.csv`, 4,919 daily observations × 47 columns) is included for reviewer convenience.

---

## License

Code: MIT License (see `LICENSE` file).
IEA project data: redistributed under CC BY-NC-SA in accordance with IEA terms. Downstream users must comply with original licenses for all data sources.

---

## Contact

**Sake Saakstra**
Vrije Universiteit Amsterdam — Department of Econometrics
Gasunie — Business Line Waterstof Nederland
Email: <s.saakstra@vu.nl>

---

## Acknowledgements

The author thanks colleagues at the VU Amsterdam Department of Econometrics and at Gasunie's Business Line Waterstof Nederland for valuable discussions. All errors are the author's own.
