# Data Dictionary

This document lists all key variables used in the analysis, their definitions, sources, and coding conventions.

## v7 curated sample (`01_data/intermediate/blueccs_project_level_for_R.csv`)

| Variable | Type | Range | Description |
|---|---|---|---|
| `project_id` | int | 0-713 | Anonymized project identifier (no S&P Record IDs to protect data agreement) |
| `is_blue_ccs` | binary | {0, 1} | 1 if project uses Fossil-with-CCS hydrogen technology, 0 if PEM electrolysis |
| `log_capacity_mw` | float | -7 to 10 | Natural log of stated production capacity (MW H₂ equivalent) |
| `region` | str | {EU, North_America, Asia, Other_Europe, Other, ANZ, MENA} | Geographic region |
| `sponsor_type` | str | various | Project sponsor type (Energy major, Industrial, Government, Unknown) |
| `sponsor_owner` | str | various | Primary owner organization (anonymized for some entries) |
| `tech` | str | {PEM, Blue_CCS} | Technology classification |
| `year_announced` | float | 2002-2026 | Year of public project announcement |
| `duration` | int | 0-25 | Years between announcement and either event or end of observation (May 2026) |
| `event_any` | binary | {0, 1} | 1 if project was cancelled/decommissioned, 0 if still active or completed |
| `event_type` | int | various | Detailed event coding (cancel vs operational vs unknown) |

## S&P Global master table (`/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx`)

| Variable | Type | Description |
|---|---|---|
| `project_status` | str | Status: Announced, Under construction, Operating, Plans cancelled, Decommissioned, etc. |
| `cancel_B` | binary | DERIVED: 1 if project_status in {Plans cancelled, Decommissioned}, 0 otherwise. *Definition B* used throughout. |
| `operating` | binary | DERIVED: 1 if project_status in {Fully commissioned, Partially commissioned}, 0 otherwise |
| `Year announced` | int | Year of project announcement |
| `Technology.1` | str | Technology level: Fossil with CCS, Electrolysis, Biomass, etc. |
| `Calculated hydrogen production per year` | float | Annual production capacity (MW H₂ equivalent) |
| `Primary end use sector` | str | High-level end use category |
| `Primary end use sector detail` | str | Detailed end use (e.g., 'Steel', 'Refinery feedstock') |
| `cbam_endex` | binary | DERIVED: 1 if end use is in CBAM-direct sectors (fertilizer, ammonia, steel, chemicals, refinery, cement), 0 otherwise |
| `Region major` | str | Major region (Europe (EU-27), North America, Asia-Pacific, etc.) |
| `is_EU` | binary | DERIVED: 1 if Region major == 'Europe (EU-27)', 0 otherwise |
| `post_2022` | binary | DERIVED: 1 if Year announced >= 2022 (CBAM political agreement), 0 otherwise |
| `cbam_x_post` | binary | DERIVED: cbam_endex × post_2022 (focal DiD interaction) |
| `triple` | binary | DERIVED: is_EU × cbam_endex × post_2022 (focal triple-difference interaction) |

## IEA Hydrogen Projects Database

| Variable | Description |
|---|---|
| `Status` | Project lifecycle status |
| `Year announced` | Year of announcement |
| `End-use sector` | Multi-checkbox encoding of all end uses (parsed into separate dummies) |
| `Technology` | Process technology |

## CBAM-end-use coding rule (CRITICAL)

CBAM-direct sectors (`cbam_endex = 1`):
- Fertilizer / Ammonia production
- Iron & Steel
- Chemicals & Chemical feedstock
- Refinery / Refinery feedstock
- Cement

CBAM-indirect / not-direct:
- Power generation
- Transport (mobility)
- Buildings (heating)
- Heat (district)
- Other / multiple

## Treatment timing

| Date | Event | Used as |
|---|---|---|
| 13 Dec 2022 | CBAM political agreement (Council + Parliament) | Vintage cutoff for cohort DiD |
| 17 May 2023 | CBAM regulation published in EU Official Journal | Equity event study window center |
| 1 Oct 2023 | CBAM transitional phase begins (reporting only) | — |
| 1 Jan 2026 | CBAM definitive phase begins (financial obligations) | Implicit "treatment in force" date |

## Coding conventions

- All probabilities and rates reported in [0, 1]
- Hazard ratios reported as exp(β) for logit/Cox specifications
- AME (average marginal effect) reported on probability scale in percentage points (×100)
- p-values reported to 3 decimals; "<0.001" if smaller
- Confidence intervals: 95% throughout
- Bayesian intervals: 95% highest density interval (HDI) unless noted otherwise

## Missing data handling

- v7 sample: complete cases (listwise deletion for `sponsor_owner == "Unknown"` only in GLMM frailty model)
- S&P: complete cases for project_status, Year announced; capacity imputed with median for missing values (5% of sample)
- IEA: complete cases for status and announcement year

## Pre-processing notes

- Capacity outliers winsorized at 99.5th percentile to prevent leverage issues
- Log-transformation of capacity (log(1+MW)) to handle skewness
- Year centered on sample mean (~2018) to improve numerical stability
