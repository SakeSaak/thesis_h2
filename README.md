# Implementation Risk under Transition Uncertainty in Clean-Hydrogen Investment

**A Real-Options Framework with Time-Varying Empirical Identification**

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![Status](https://img.shields.io/badge/status-v2.3%20candidate-orange.svg)](#status)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Thesis: MSc EOR](https://img.shields.io/badge/thesis-MSc%20EOR%20VU-yellow.svg)](https://vu.nl/en/education/master/econometrics-and-operations-research)

> **Author**: Sake Saakstra · **Supervisor**: prof. dr. Siem Jan Koopman · **Second reader**: dr. Nadine Ketel
> **Programme**: MSc Econometrics & Operations Research (Financial Track), Vrije Universiteit Amsterdam
> **Target submission**: 2026

---

## Abstract

Clean-hydrogen projects announce in large volumes — globally over 420 GW of green production and substantial Blue (CCS-equipped) capacity since 2020 — yet only a small fraction of announced capacity reaches Final Investment Decision. This dissertation asks why, and how policy mechanisms shape the answer.

The framework is real-options under irreversibility and transition uncertainty. The investment decision is staged (front-end design → FID → construction → operations), each stage with its own sunk-capital forfeit and cancellation threshold. The sponsor's expected payoff evolves under two sources of stochastic variation: a payoff-relevant state variable (carbon price, technology cost) and a policy-regime-credibility belief that determines whether the contemporary policy environment will persist over the investment horizon. Optimal cancellation thresholds respond to five comparative-statics channels (μ, σ, ρ, η, κ) and to the credibility belief π. The framework is intentionally reduced-form on credibility: π is treated as an organising interpretive layer rather than a structurally identified state.

The empirical analysis uses a project-level dataset of **2,989 Blue and Green hydrogen projects** from the S&P Global Hydrogen Project Database (snapshot 24 March 2026), with **1,000 broad failure events** (cancelled, on-hold, or decommissioned). Three substantive findings emerge.

First, pre-FID offtake commitments are associated with substantially lower cancellation hazard in a stratified analysis that is robust to multiple matching estimators and to the Oster (2019) bound on selection-on-unobservables. Three formal identification tests reported in Appendix A.14 show that this effect operates through multiple co-operating channels (μ, σ, η) that are statistically indistinguishable in observational data; the empirical signature is robust, the unique-channel identification claim is not.

Second, the time-varying intensity of the carbon-conditional cancellation hazard, estimated through a score-driven GAS specification with sparse-event-suitable shrinkage, recovers a discontinuous step around the 2020 European Green Deal regime boundary that constant-parameter and parameter-driven block-step specifications cannot accommodate. The structural-break finding is robust across out-of-sample tests; the interpretation of the break as a credibility-shift response is one of several observationally equivalent interpretations.

Third, the cross-jurisdictional carrot-policy ranking (China 14th Five-Year Plan > US 45Q > UK Track-1 ≫ EU Innovation Fund) systematically tracks the number of economic frictions each instrument addresses, not the per-unit monetary value of the subsidy. The EU Innovation Fund informative null and the EU CBAM weak-transmission finding are reported as substantive contributions about which economic frictions are binding in the contemporary capital-abundant clean-technology environment.

---

## Status

| Component | Status | Notes |
|---|---|---|
| **Thesis main** (`00_paper/thesis_v1/`) | v2.3 candidate, 141 pages | Awaiting supervisor feedback on Proposition formal status |
| **Paper 1**: TVP methodology (`09_papers/paper1_*/`) | 8,193 w, 24 p, submission-ready | Target: *Journal of Applied Econometrics* |
| **Paper 2**: Carrot-policy DiD (`09_papers/paper2_*/`) | 6,284 w, first draft | Target: *Energy Economics* |
| **Paper 3**: Offtake mechanism (`09_papers/paper3_*/`) | 4,138 w, first draft | Target: *JEEM* |
| **Paper 4**: Real-options theory (`09_papers/paper4_*/`) | 5,228 w, first draft | Target: *REEP* |
| **Defence** | Planned 2026-Q3 | |

---

## Empirical findings — identification status

Findings are graded on the identification hierarchy of Appendix A.12, not on a single robustness label.

| # | Finding | Identification status | Robustness evidence |
|---|---|---|---|
| 1 | Pre-FID offtake commitment is associated with lower cancellation hazard | L3.a + L3.b (multiple matching estimators converging) | Oster δ_null = 20.23; cross-sectoral pattern survives in 4-of-4 strata |
| 2 | Channel-attribution of (1) to σ versus μ versus η | **Not separately identified** | Three identification tests (Appendix A.14) cannot statistically discriminate the three channels (LR p = 0.19; joint Wald p = 0.96) |
| 3 | TVP β_int(t) structural break around 2020 in the carbon-conditional hazard | L4 + L2 (GAS structural-break detection; OOS-dominant over constant-parameter and block-step) | DM-HLN = +5.59 vs M1 baseline; placebo-stable |
| 4 | Channel-attribution of (3) to π versus σ versus expectations | **Not separately identified** | Pooled regression cannot distinguish loadings; event-study with four exogenous shocks cannot reject equality |
| 5 | China 14th FYP cancellation-hazard effect | L3.a + L3.b (Sun-Abraham + BJS + IPWRA + SDID + Honest DiD converging) | M* = 1.5 (substantively robust) |
| 6 | US 45Q cancellation-hazard effect | L3.a (DiD converging) | M* = 0.2 (point-identified, partial-id-fragile); event-study corroboration p = 0.05 |
| 7 | EU Innovation Fund informative null | L3.a + L3.b (precise null across 6 estimators) | Substantive contribution: F4-non-binding in capital-abundant environment |
| 8 | EU CBAM weak transmission in transitional phase | L3.a + L3.b (precise null across 8 estimators) | Predicted to strengthen in post-2026 definitive phase |

The use of "**Not separately identified**" rather than "falsified" is deliberate: the underlying empirical signatures (1) and (3) are robust, but their attribution to a specific theoretical channel is empirically underdetermined among observationally equivalent alternatives. This identification limit is documented as a methodological contribution in Chapter 10 and is the natural target for follow-up research using exogenous-variation designs (RDD around constitutional carbon-budget amendments, election-driven climate-policy reversals, natural-experiment volatility shocks isolated from policy-credibility content).

---

## Repository structure

```
thesis_h2/
├── 00_paper/                          # Main thesis manuscript
│   ├── thesis_v1/                     # Active v2.3 candidate (LaTeX + PDF)
│   └── archive_v7_precursor_paper/    # Historical v7 single-paper manuscript
├── 01_data/                           # Datasets
│   ├── raw/                           # Original sources (S&P, FRED, ICAP, EMV, ...)
│   └── intermediate/                  # Cleaned + merged monthly/weekly panels
├── 02_scripts/                        # Core analysis pipeline (data-prep, analysis, figures)
├── 03_output/                         # Generated outputs (figures, tables, results)
├── 06_thesis_extensions/              # Extended methodological analyses
│   ├── 01_bayesian_methodology/       # Bayesian TVP variants
│   ├── 04_carbon_conditional/         # Carbon-conditional hazard specification
│   ├── 05_state_space_tvp/            # GAS state-space (Paper 1 implementation)
│   ├── 11_v7_sp_matching/             # Sample-window dependence analysis
│   ├── 12_advanced_robustness/        # Modern DiD, IPWRA, Honest DiD, Causal Forest
│   ├── 13_identification_tests/       # Appendix A.14 tests (pi-sigma, offtake, event-study)
│   ├── 13_theoretical/                # Real-options analytical extensions
│   └── 14_counterfactual/             # Counterfactual policy scenarios
├── 07_chapter_drafts_archive/         # Historical chapter draft snapshots
├── 07_stakeholder_briefings/          # Policy briefings (archived)
├── 08_synthesis/                      # Cross-component synthesis documents
├── 09_papers/                         # Four working papers (Papers 1-4)
├── 09_reproducibility/                # Reproduction instructions
└── docs/                              # Documentation
```

---

## Reproducing the analysis

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

**The S&P Global Hydrogen Production Assets database is not included** — it requires a commercial licence. To reproduce, obtain `Hydrogen_projects_master_data_table_*.xlsx` from S&P Global Market Intelligence and place it in `01_data/raw/`. Other datasets (FRED, ICAP carbon prices, Baker-Bloom-Davis Equity Market Volatility, BBD Economic Policy Uncertainty) are publicly available; see `09_reproducibility/README.md` for source URLs.

### 4. Headline analyses

```bash
# Paper 1 (TVP methodology): score-driven GAS hazard model
python 06_thesis_extensions/05_state_space_tvp/04_gas_hazard.py

# Paper 2 (Carrot-policy): modern DiD estimators
python 06_thesis_extensions/12_advanced_robustness/42_modern_did_robustness.py

# Paper 3 (Offtake mechanism): identification + Oster bound
python 06_thesis_extensions/12_advanced_robustness/43_offtake_effect_identification.py

# Appendix A.14 identification battery
python 06_thesis_extensions/13_identification_tests/test1_credibility_vs_volatility/01_test1_pi_sigma_joint_identification.py
python 06_thesis_extensions/13_identification_tests/test2_offtake_decomposition/02_test2_offtake_decomposition.py
python 06_thesis_extensions/13_identification_tests/test3_instrumental_variables/01_test3_event_study_identification.py
```

Each script writes outputs (CSV + figures) to its own results directory.

---

## Citation

```bibtex
@mastersthesis{saakstra2026implementation,
  title  = {Implementation Risk under Transition Uncertainty in Clean-Hydrogen Investment:
            A Real-Options Framework with Time-Varying Empirical Identification},
  author = {Saakstra, Sake},
  school = {Vrije Universiteit Amsterdam},
  type   = {MSc thesis, Econometrics and Operations Research (Financial Track)},
  year   = {2026},
  url    = {https://github.com/SakeSaak/thesis_h2}
}
```

See `CITATION.cff` for machine-readable metadata.

---

## License

Code and original text in this repository are licensed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). See `LICENSE` for details.

**Important exclusions**: this licence does not cover S&P Global commercial data, IEA copyrighted publications, or third-party figures from cited papers. Such material is used here under fair-use academic-research provisions and is not redistributed in derivative form.

---

## Acknowledgments

This research is conducted under the supervision of **prof. dr. Siem Jan Koopman** (Vrije Universiteit Amsterdam, Tinbergen Institute) and **dr. Nadine Ketel** (Vrije Universiteit Amsterdam) as second reader.

The research uses commercial data from **S&P Global Market Intelligence Hydrogen Production Assets database** (snapshot 24 March 2026). All views and interpretations are the author's own and do not represent the official positions of S&P Global, the Vrije Universiteit Amsterdam, or the author's employer.

---

## Contact

**Sake Saakstra** — MSc Econometrics & Operations Research (Financial Track), Vrije Universiteit Amsterdam

- 📧 sake.saakstra@student.vu.nl
- 🔗 GitHub: [@SakeSaak](https://github.com/SakeSaak)

For thesis-related correspondence, please CC supervisor prof. Koopman.

---

*Last updated: 22 May 2026*
