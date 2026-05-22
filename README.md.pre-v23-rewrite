# Implementation-Risk Differentials in Hydrogen Technology Pathways

**A Cross-Jurisdictional Causal Evaluation of Carrot-Policy Mechanisms**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Status](https://img.shields.io/badge/status-thesis%20draft-orange.svg)](#status)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Thesis: MSc EOR](https://img.shields.io/badge/thesis-MSc%20EOR%20VU-yellow.svg)](https://vu.nl/en/education/master/econometrics-and-operations-research)

> **Author**: Sake Saakstra · **Supervisor**: prof. dr. Siem Jan Koopman · **Second reader**: dr. Nadine Ketel
> **Programme**: MSc Econometrics & Operations Research (Financial Track), Vrije Universiteit Amsterdam
> **Target submission**: 2026

---

## Abstract

Despite USD $1.3 trillion in announced subsidies and over 422 GW of green hydrogen project announcements globally, only ~7% of 2023 planned capacity reached scheduled Final Investment Decision (Odenweller & Ueckerdt, *Nature Energy* 2025). This thesis provides the first cross-jurisdictional causal evaluation of why low-carbon hydrogen projects survive or fail, and which policy mechanisms move the needle.

Using a project-level dataset of **1,354 Blue and Green hydrogen projects** (S&P Global, 2010-2024) with 367 documented failures, this research:

1. **Identifies a novel mechanism**: pre-FID offtake commitments reduce project failure probability by **11-13 percentage points** across five independent identification strategies (LPM with rich controls, propensity score matching, IPWRA, Oster sensitivity δ\_null = 20.23)
2. **Evaluates four carrot-policy types** via modern difference-in-differences (TWFE, Sun-Abraham 2021, Borusyak-Jaravel-Spiess 2024 imputation), with Rambachan-Roth (2023) honest sensitivity bounds revealing heterogeneous causal-identification strength
3. **Documents a structural break** in policy effectiveness around 2020 via three time-varying-parameter estimators (threshold, AR(1) state-space, random walk)
4. **Grounds findings in a Dixit-Pindyck (1994) real-options framework**, distinguishing V/I-boost mechanisms (output credits, capex grants) from σ-attack mechanisms (offtake mandates, cluster tenders)
5. **Quantifies counterfactual policy scenarios**: an EU sector-optimal carrot mix would deliver an estimated **+113 additional FIDs, +7.83 Mt/y additional CO₂ capture, and +1.76 Mt/y additional H₂ output** over a 3-year horizon (95% bootstrap CI)

These findings are externally corroborated by the 2024-2026 wave of high-profile cancellations: ArcelorMittal's Bremen and Eisenhüttenstadt withdrawals despite €1.3B EU Innovation Fund subsidies, BP's HyGreen Teesside and H2Teesside exits, and seven EU Hydrogen Bank auction winners (1.88 GW) withdrawing in September 2025.

---

## Status

| Component | Status |
|---|---|
| **Empirical analysis (Pijlers 1-40)** | ✅ Complete |
| **Theoretical framework (Pijler 40)** | ✅ Complete |
| **Counterfactual scenarios (Pijler 36)** | ✅ Complete |
| **Stakeholder briefings** | ✅ Complete |
| **Thesis manuscript** | 🟡 In progress (chapters 3, 4, 7, 8 drafted) |
| **Defense** | ⏳ Planned 2026-Q3 |
| **Energy Economics submission** | ⏳ Planned post-defense |

---

## Key findings — robustness scorecard

| # | Finding | Methods converging | Robustness verdict |
|---|---|---|---|
| **1** | **Offtake commitment reduces failure by 11-13 pp** | LPM + PSM + IPWRA + Oster + sector LPM (5 methods) | **WATERTIGHT** (Oster δ\_null = 20.23) |
| **2** | **China 14th FYP causal effect: −4.5 pp annual hazard** | TWFE + Sun-Abraham + BJS-imputation + Honest DiD | **WATERTIGHT** (Honest M\* = 1.50, robust) |
| **3** | **Structural break in policy-effect sign around 2020** | Threshold + AR(1) state-space + random walk | **WATERTIGHT** (3 TVP methods converge) |
| **4** | **EU Innovation Fund: informative null** | All 6 methods non-significant | **WATERTIGHT** (consistent null) |
| **5** | **UK Track-1 selection-funnel artifact** | TWFE + qualitative case-study | **STRONG, QUALIFIED** |
| **6** | **σ-channel vs V/I-channel mechanism taxonomy** | Theoretical + empirical sector-heterogeneity | **STRONG** (falsifiable predictions) |
| **7** | **US 45Q causal effect: −3.8 pp annual hazard** | TWFE + BJS converge, Honest DiD sensitive | **QUALIFIED** (Honest M\* = 0.20) |

See `08_synthesis/` for the full synthesis document, including external industry corroboration.

---

## Repository structure

```
thesis_h2/
├── 00_paper/                        # Journal-version paper (LaTeX)
│   ├── current/                     # Active draft (blueCCS_paper_final.tex)
│   ├── elsarticle_submission/       # Energy Economics target version
│   └── _archive/                    # Historical iterations
├── 01_data/                         # Datasets
│   ├── raw/                         # Original sources (S&P, ENTSO-E, FRED, ICAP, WUI, GPR)
│   ├── intermediate/                # Cleaned + merged panels
│   └── external/                    # API-fetched (yfinance, FRED)
├── 02_scripts/                      # Core analysis pipeline
│   ├── 01_data_prep/                # ETL scripts
│   ├── 02_analysis/                 # Main DiD, TVP, survival models
│   └── 03_figures/                  # Publication figures
├── 03_output/                       # Generated outputs (figures, results, tables)
├── 06_thesis_extensions/            # Pijlers 1-40 (PhD-quality analyses)
│   ├── 01_bayesian_methodology/     # Pijler 24c TVP-DiD
│   ├── 12_advanced_robustness/      # Pijlers 30-34, 39 (causal forest, modern DiD, offtake, Honest DiD)
│   ├── 13_theoretical/              # Pijler 40 real-options × mechanism design
│   └── 14_counterfactual/           # Pijler 36 counterfactual scenarios
├── 07_thesis_drafts/                # Thesis chapter LaTeX files
│   ├── chapter3_real_options.tex
│   ├── chapter4_data.tex
│   ├── chapter7_v2.tex              # Time-varying carbon-conditional hazard
│   └── chapter8_cbam_full.tex       # CBAM causal identification
├── 07_stakeholder_briefings/        # Policy briefings (EU, Gasunie, sponsors)
│   └── POLICY_BRIEFINGS_v2/
├── 08_synthesis/                    # Cross-pijler synthesis documents
├── 08_communicatie/                 # Supervisor communication drafts
├── 09_reproducibility/              # Reproduction instructions + Docker
└── docs/                            # Documentation + archived early-stage notes
    └── archive/                     # Historical working documents
```

---

## Quickstart — reproducing the analysis

### 1. Clone

```bash
git clone https://github.com/SakeSaak/thesis_h2.git
cd thesis_h2
```

### 2. Environment

Tested with Anaconda Python 3.13.9. Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Data

**The S&P Global hydrogen projects database is NOT included** — it requires a commercial license. To reproduce:

- Obtain `Hydrogen_projects_master_data_table_*.xlsx` from S&P Global Market Intelligence
- Place in `01_data/raw/`
- Other datasets (ENTSO-E energy prices, FRED, World Bank, ICAP, WUI, GPR) are publicly available — see `09_reproducibility/README.md` for sources

### 4. Run the main analyses

Each pijler is a standalone Python script. To reproduce the headline findings:

```bash
# Pijler 32: Modern DiD robustness
python 06_thesis_extensions/12_advanced_robustness/42_modern_did_robustness.py

# Pijler 34: Offtake-effect (multi-method ID)
python 06_thesis_extensions/12_advanced_robustness/43_offtake_effect_identification.py

# Pijler 39: Honest DiD sensitivity bounds
python 06_thesis_extensions/12_advanced_robustness/44_honest_did_bounds.py

# Pijler 36: Counterfactual scenarios
python 06_thesis_extensions/14_counterfactual/46_counterfactual_scenarios.py
```

Each script writes outputs (CSV + figures) to its own results directory.

---

## Citation

If you use this research or any of its code, please cite:

```bibtex
@mastersthesis{saakstra2026implementation,
  title  = {Implementation-Risk Differentials in Hydrogen Technology Pathways:
            A Cross-Jurisdictional Causal Evaluation of Carrot-Policy Mechanisms},
  author = {Saakstra, Sake},
  school = {Vrije Universiteit Amsterdam},
  type   = {MSc thesis, Econometrics and Operations Research},
  year   = {2026},
  url    = {https://github.com/SakeSaak/thesis_h2}
}
```

See `CITATION.cff` for machine-readable metadata.

---

## License

This repository is licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). See `LICENSE` for details.

**Important exclusions**: this license does NOT cover S&P Global commercial data, IEA copyrighted publications, or third-party figures from cited papers.

---

## Acknowledgments

This research was conducted under the supervision of **prof. dr. Siem Jan Koopman** (Vrije Universiteit Amsterdam, Tinbergen Institute) and **dr. Nadine Ketel** (Vrije Universiteit Amsterdam) as second reader. The author thanks the Gasunie BL Waterstof Nederland team for context on Dutch hydrogen infrastructure development and the broader Nederland-wide HyNetwork business case.

The research uses commercial data from **S&P Global Market Intelligence Hydrogen Production Assets database** (snapshot 24 March 2024). All views and interpretations are the author's own and do not represent the official positions of S&P Global, the Vrije Universiteit Amsterdam, or Gasunie N.V.

---

## Contact

**Sake Saakstra**
MSc Econometrics & Operations Research (Financial Track)
Vrije Universiteit Amsterdam

- 📧 sake.saakstra@student.vu.nl
- 🔗 GitHub: [@SakeSaak](https://github.com/SakeSaak)

For thesis-related correspondence, please CC supervisor prof. Koopman.

---

*Last updated: 21 May 2026*
