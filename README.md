# Implementation Risk under Transition Uncertainty in Clean-Hydrogen Investment

**A Real-Options Framework with Time-Varying Empirical Identification**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20359771.svg)](https://doi.org/10.5281/zenodo.20359771)
[![Code License: MIT](https://img.shields.io/badge/Code%20License-MIT-yellow.svg)](LICENSE-CODE)
[![Writing License: CC BY 4.0](https://img.shields.io/badge/Writing%20License-CC%20BY%204.0-lightgrey.svg)](LICENSE-WRITING)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/)
[![Status: v1.1 release](https://img.shields.io/badge/status-v1.1%20release-green.svg)](#status)

> **Author**: Sake Saakstra (independent researcher; MSc EOR Financial Track student, Vrije Universiteit Amsterdam)
> **Status**: pre-thesis research infrastructure, released for academic citeability and intellectual-property timestamping. Formal MSc thesis procedure is scheduled for 2026-2027.

---

## Citation

If you use this research, code, data, or findings, please cite:

```
Saakstra, S. (2026). Implementation Risk under Transition Uncertainty in Clean-Hydrogen
Investment: A Real-Options Framework with Time-Varying Empirical Identification.
Zenodo. https://doi.org/10.5281/zenodo.20359771
```

For BibTeX:
```bibtex
@misc{saakstra2026implementation,
  author       = {Saakstra, Sake},
  title        = {Implementation Risk under Transition Uncertainty in Clean-Hydrogen
                  Investment: A Real-Options Framework with Time-Varying Empirical
                  Identification},
  year         = {2026},
  publisher    = {Zenodo},
  version      = {v1.1},
  doi          = {10.5281/zenodo.20359771},
  url          = {https://github.com/SakeSaak/thesis_h2}
}
```

The DOI `10.5281/zenodo.20359771` is the **concept DOI** (always resolves to
the most recent version). The version-specific DOI for v1.0.1 is
`10.5281/zenodo.20359772` and can be used when citing a specific version.
For most academic citation contexts, the concept DOI is preferred.

---

## Abstract

Clean-hydrogen projects announce in large volumes — globally over 420 GW of green production and substantial Blue (CCS-equipped) capacity since 2020 — yet only a small fraction of announced capacity reaches Final Investment Decision. This research asks why, and how policy mechanisms shape the answer.

The framework is real-options under irreversibility and transition uncertainty. The investment decision is staged (front-end design → FID → construction → operations), each stage with its own sunk-capital forfeit and cancellation threshold. The sponsor's expected payoff evolves under two sources of stochastic variation: a payoff-relevant state variable (carbon price, technology cost) and a policy-regime-credibility belief that determines whether the contemporary policy environment will persist over the investment horizon. Optimal cancellation thresholds respond to five comparative-statics channels (μ, σ, ρ, η, κ) and to the credibility belief π. The framework is intentionally reduced-form on credibility: π is treated as an organising interpretive layer rather than a structurally identified state.

The empirical analysis uses a project-level dataset from the S&P Global Hydrogen Project Database (snapshot 24 March 2026). Three substantive findings emerge.

**First**, pre-FID offtake commitments are associated with substantially lower cancellation hazard (−11 to −13pp across five matching estimators) in a stratified analysis that is robust to the Oster (2019) bound on selection-on-unobservables (δ_null = 20.23). Three formal identification tests show that this effect operates through multiple co-operating channels (μ, σ, η) that are statistically indistinguishable in observational data; the empirical signature is robust, the unique-channel identification claim is not.

**Second**, the time-varying intensity of the carbon-conditional cancellation hazard, estimated through a score-driven GAS specification with sparse-event-suitable shrinkage, recovers a discontinuous step around the 2020 European Green Deal regime boundary that constant-parameter and parameter-driven block-step specifications cannot accommodate. The structural-break finding is robust across out-of-sample tests.

**Third**, the cross-jurisdictional carrot-policy ranking (China 14th Five-Year Plan > US 45Q > UK Track-1 ≫ EU Innovation Fund) tracks the number of economic frictions each instrument addresses, not the per-unit monetary value of the subsidy. The EU Innovation Fund informative null is reported as a substantive contribution about which economic frictions are binding in the contemporary capital-abundant clean-technology environment.

The central economic proposition: *implementation-risk dynamics under transition uncertainty are themselves a substantive economic phenomenon, not a measurement nuisance to be controlled away in pursuit of stable underlying parameters.*

---

## Status (v1.0 release)

| Component | Version | Size | Status |
|---|---|---|---|
| **Bridging thesis** (`00_paper/thesis_v1/`) | v2.7 | 159 pages | Compiles clean, 0 LaTeX errors, 0 undefined references |
| **Paper 1**: TVP / score-driven methodology (`09_papers/paper1_tvp_methodology/`) | v2.7 | 25 pages | Single-author, draft-complete |
| **Paper 2**: Carrot-policy DiD (`09_papers/paper2_carrot_policy_did/`) | v2.7 | 21 pages | Single-author, draft-complete |
| **Paper 3**: Offtake mechanism (`09_papers/paper3_offtake_mechanism/`) | v2.7 | 15 pages | Single-author, draft-complete |
| **Paper 4**: Real-options theory (`09_papers/paper4_real_options_theory/`) | v2.7 | 18 pages | Single-author, draft-complete |
| **Executive Summary** (`00_paper/executive_summary/`) | v1.0 | 4 pages | Compact entry-point document for non-specialist audiences |
| **ETS2 Policy Brief** (`07_stakeholder_briefings/ETS2_policy_brief/`) | v1.0 | 6 pages | Evidence-positioned policy memo for EU/national audiences |
| **Identification tests** (`06_thesis_extensions/13_identification_tests/`) | v1.0 | 3 formal tests | Battery of pi-vs-sigma joint identification, offtake decomposition, event-study |
| **Robustness pijlers** (`06_thesis_extensions/12_advanced_robustness/`) | v1.0 | 48 Python scripts | Honest DiD, modern DiD estimators, GAS-TVP, Sun-Abraham, BJS, IPWRA, etc. |

Total writing: 159-page bridging thesis + 79-page companion-paper portfolio (4 standalone papers) + 10-page distribution-ready briefs (executive summary + ETS2 policy brief).

---

## Findings by identification status

Findings are graded on the L1–L4 identification hierarchy developed in Chapter 5 of the thesis and visually summarised in the Scope of Claims table (Chapter 1 §1.4).

| # | Finding | Level | Robustness evidence |
|---|---|---|---|
| 1 | Pre-FID offtake commitments reduce cancellation hazard by 11–13 pp | L3.a + L3.b | Convergent across 5 matching estimators; Oster δ_null = 20.23 |
| 2 | Channel-attribution of (1) to σ vs. μ vs. η | **Not separately identified** | Three identification tests (Appendix A.14) cannot statistically discriminate; reported as substantive identification limit |
| 3 | TVP β_int(t) structural break around 2020 | L4 + L2 | GAS-TVP detection; DM-HLN out-of-sample dominance over M1/M2 |
| 4 | Channel-attribution of (3) to π vs. σ vs. expectations | **Not separately identified** | Event-study with four exogenous shocks cannot reject equality |
| 5 | China 14th FYP cancellation-hazard effect | L3.a + L3.b | Sun-Abraham + BJS + IPWRA + SDID + Rambachan-Roth M* = 1.5 |
| 6 | US 45Q cancellation-hazard effect | L3.a | Modern DiD converging; Rambachan-Roth sensitivity-bounded |
| 7 | EU Innovation Fund informative null | L3.a + L3.b | Precise null across 6 estimators; reported as substantive contribution |
| 8 | EU CBAM weak transmission in transitional phase | L3.a + L3.b | Precise null across 8 estimators |

The phrase "**Not separately identified**" is deliberate: empirical signatures (1) and (3) are robust, but their attribution to a single theoretical channel is empirically underdetermined among observationally equivalent alternatives. This identification limit is documented as a methodological contribution in Chapter 10.

---

## Policy relevance

The empirical findings have direct relevance for ongoing European and national clean-energy policy discussions, particularly around the EU Emissions Trading System Phase 2 (ETS2), the EU Hydrogen Bank, member-state subsidy design, and industrial competitiveness in the energy transition.

The central evidence-positioned insight is that **carbon-price signals alone are likely insufficient when demand certainty, infrastructure coordination, policy credibility, and implementation frictions are not simultaneously addressed**. The EU Innovation Fund informative null (€10B+ disbursed, no detectable cancellation-hazard reduction) and the EU CBAM weak-transmission finding in the transitional phase document this empirically. The offtake-commitment effect (−11 to −13pp cancellation-hazard reduction, robust across five matching estimators) identifies demand certainty as a substantively under-appreciated mechanism through which subsidies operate. The friction-count ranking of carrot-policy effectiveness (China FYP > 45Q > Track-1 ≫ EU IF) suggests that policy effectiveness tracks the number of binding economic frictions each instrument addresses, not the per-unit monetary value of the subsidy.

These findings are positioned as **evidence on implementation risk under transition uncertainty** rather than as normative policy advocacy. The disposition is consistent with the dissertation's central economic proposition: implementation-risk dynamics under transition uncertainty are themselves a substantive economic phenomenon, not a measurement nuisance to be controlled away in pursuit of stable underlying parameters.

A focused ETS2 policy brief, building on these findings with audience-appropriate framing, is in preparation as a separate deliverable.

---

## Repository structure

```
thesis_h2/
├── 00_paper/                          # Bridging thesis manuscript
│   ├── thesis_v1/                     # Active v2.7 (LaTeX + PDF)
│   └── archive_v7_precursor_paper/    # Historical v7 single-paper manuscript
├── 01_data/                           # Datasets
│   ├── raw/                           # Original sources (S&P, FRED, ICAP, EMV, …)
│   └── intermediate/                  # Cleaned + merged monthly/weekly panels
├── 02_scripts/                        # Core analysis pipeline (data-prep, analysis, figures)
├── 03_output/                         # Generated outputs (figures, tables, results)
├── 06_thesis_extensions/              # Extended methodological analyses
│   ├── 01_bayesian_methodology/       # Bayesian TVP variants
│   ├── 12_advanced_robustness/        # 48 robustness pijlers
│   ├── 13_identification_tests/       # Three formal identification tests
│   └── 14_tinbergen_reference_works/  # Reference library
├── 09_papers/                         # Four companion papers
│   ├── paper1_tvp_methodology/
│   ├── paper2_carrot_policy_did/
│   ├── paper3_offtake_mechanism/
│   └── paper4_real_options_theory/
├── CITATION.cff                       # Citation metadata
├── LICENSE-CODE                       # MIT license for Python scripts
├── LICENSE-WRITING                    # CC-BY 4.0 license for written work (LaTeX, PDF)
├── README.md                          # This file
└── requirements.txt                   # Python dependencies
```

---

## Licensing

- **Python code** (`*.py` in `02_scripts/`, `06_thesis_extensions/`): MIT license, see [LICENSE-CODE](LICENSE-CODE).
- **Written work** (`*.tex` and `*.pdf` in `00_paper/`, `09_papers/`, and policy briefs): Creative Commons Attribution 4.0 International (CC BY 4.0), see [LICENSE-WRITING](LICENSE-WRITING).
- **Data**: The S&P Global Hydrogen Project Database snapshot is third-party licensed material. The processed analysis-ready intermediate datasets (`01_data/intermediate/`) are derived works under fair-use; redistribution rights are subject to the underlying source license.

---

## Reproducibility

Python 3.13+. Install dependencies:

```bash
pip install -r requirements.txt
```

The full analysis pipeline can be reproduced by executing scripts in `02_scripts/` and `06_thesis_extensions/12_advanced_robustness/` in numerical order. Each script writes outputs to `03_output/` and `06_thesis_extensions/12_advanced_robustness/results/`.

The thesis and companion papers compile with TeX Live 2024 (`pdflatex` + `bibtex`).

---

## Disclaimer

This is independent academic research. The work does not reflect the official position of any institution or employer. All findings, errors, and opinions are the author's own.
