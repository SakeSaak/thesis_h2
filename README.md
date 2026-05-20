# Thesis Hydrogen Implementation Risk — Working Directory

## Structuur

- `00_paper/` — paper bronbestanden en versies
  - `current/` — v7 PDF, paper_final.tex, figures voor de paper
  - `elsarticle_submission/` — Energy Economics submission versie (v1 + v2)
  - `_archive/` — eerdere paper iteraties (v3, v5, v6, Word-versies)
- `01_data/`
  - `raw/` — IEA Hydrogen DB, ENTSO-E downloads, FRED, World Bank, ICAP, EMV, WUI, GPR
  - `intermediate/` — master_panel_daily/weekly/monthly, blueccs_project_level
  - `external/` — yfinance, fred_series
- `02_scripts/` — paper analyse-code + repo metadata (README, LICENSE, requirements, renv.lock)
  - `01_data_prep/` — prepare_h2_data_for_R.py
  - `02_analysis/` — 24, 25d, 26, 27, 28
  - `03_figures/` — 29 headline figure
- `03_output/` — outputs van paper analyses
  - `figures/` — gegenereerde figuren (nog te vullen bij re-run)
  - `results/` — 25d/26/27 CSV outputs
  - `tables/` — voor LaTeX include (nog te vullen)
- `04_notes/` — werkende notities, meeting notes, TODO
- `05_supervisor/` — voor supervisor correspondence en meeting prep
- `_archive_eda/` — vroege exploratie werk (mei 7-8) + tussenfase iteraties

## Run order
1. `02_scripts/01_data_prep/prepare_h2_data_for_R.py`
2. `02_scripts/02_analysis/24_paper_v3_robustness_battery.py` (en 24_patch)
3. `02_scripts/02_analysis/25d_competing_risks_frailty_final.R`
4. `02_scripts/02_analysis/26_marginal_effects_hazard_curves.py`
5. `02_scripts/02_analysis/27_leave_one_region_out.py`
6. `02_scripts/02_analysis/28_overlap_visualisations.py`
7. `02_scripts/03_figures/29_headline_figure_3panel.py`

## Status (mei 2026)
- Paper version: v7 (4 rondes medestudent feedback verwerkt)
- Submission-ready: elsarticle bundle (v2) staat klaar
- Volgende stap: contact Bos voor thesis-supervision via QFRM-cursus
- Thesis: gepland P5 volgend studiejaar
