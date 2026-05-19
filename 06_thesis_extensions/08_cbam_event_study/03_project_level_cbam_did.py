"""
03_project_level_cbam_did.py — Project-level CBAM Difference-in-Differences

Drie verbeteringen tov het equity event study:
  1. PROJECT-LEVEL outcome (cancellation hazard, niet stock returns)
  2. MULTIPLE candidate treatment dates getest:
     - April 2023: CBAM regulation in force
     - October 2023: CBAM transitional phase start (REPORTING obligation)
     - January 2026: CBAM definitive period (FINANCIAL obligation)
  3. PROXY-BASED CBAM exposure via sponsor type:
     - Oil_major, Industrial_gas, Steel, Pure_play met fertilizer downstream → treated
     - Other, Utility, Unknown → control (less direct CBAM exposure)

Hypothese: als CBAM een causaal effect heeft, dan zou de Blue × CBAM-exposed
cancellation hazard moeten differentieel reageren op de transitional-start (okt 2023).
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
SUPPLEMENT_CSV = PROJECT_ROOT / "06_thesis_extensions/08_cbam_event_study/data/cbam_supplement_events.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/08_cbam_event_study/results_project_level"
OUT.mkdir(parents=True, exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.98
SEED = 20260519


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# 1. LOAD v7 + SUPPLEMENT
# ============================================================================
hdr("Combine v7 sample + post-2025 supplement")

v7 = pd.read_csv(PROJECT_CSV)
v7['is_blue_ccs'] = v7['is_blue_ccs'].astype(int)
v7['year_announced'] = v7['year_announced'].astype(int)
v7['duration'] = v7['duration'].astype(int).clip(lower=1)
v7['event_any'] = (v7['event_type'] > 0).astype(int)
v7['event_year'] = v7['year_announced'] + v7['duration']
# Assume mid-year event timing for events without specific date
v7['event_month'] = 6
v7['event_date'] = pd.to_datetime(v7['event_year'].astype(str) + '-' + 
                                    v7['event_month'].astype(str) + '-15',
                                    errors='coerce')

print(f"v7 sample: {len(v7)} projecten, {v7['event_any'].sum()} events")

# Load supplement
sup = pd.read_csv(SUPPLEMENT_CSV)
sup['event_date'] = pd.to_datetime(sup['event_date'])
print(f"Supplement: {len(sup)} events tussen {sup['event_date'].min()} en {sup['event_date'].max()}")


# ============================================================================
# 2. CBAM EXPOSURE PROXY VARIABLES
# ============================================================================
hdr("CBAM exposure classification (proxy-based)")

# T1: end-use proxy via sponsor_type
def cbam_endex_t1(sponsor_type):
    if pd.isna(sponsor_type):
        return 0
    s = str(sponsor_type).strip()
    if s in ['Oil_major', 'Industrial_gas', 'Steel']:
        return 1  # Likely CBAM-covered downstream
    return 0

# T2: geographic exposure
def cbam_endex_t2(region):
    if pd.isna(region):
        return 0
    s = str(region).strip()
    if s in ['EU', 'Other_Europe']:
        return 1  # Inside or adjacent to EU CBAM jurisdiction
    return 0

# T3: feedstock-based — Blue projects are gas-dependent (CBAM-relevant input)
def cbam_endex_t3(is_blue):
    return int(is_blue == 1)

v7['cbam_T1'] = v7['sponsor_type'].apply(cbam_endex_t1)
v7['cbam_T2'] = v7['region'].apply(cbam_endex_t2)
v7['cbam_T3'] = v7['is_blue_ccs'].apply(cbam_endex_t3)

print(f"\nT1 (end-use via sponsor): {v7['cbam_T1'].sum()} treated / {len(v7)} projecten")
print(f"T2 (geographic EU+OE):    {v7['cbam_T2'].sum()} treated / {len(v7)} projecten")
print(f"T3 (Blue feedstock):       {v7['cbam_T3'].sum()} treated / {len(v7)} projecten")

# Crosstab T1 x is_blue
print(f"\nT1 × Blue crosstab (events alleen):")
print(v7[v7['event_any']==1].groupby(['cbam_T1','is_blue_ccs']).size().unstack(fill_value=0))


# ============================================================================
# 3. BUILD MONTH-LEVEL PERSON-MONTH PANEL
# ============================================================================
hdr("Build month-level person-month panel for event study")

# Each project contributes person-months from announce to event/censoring
panel_rows = []
for idx, row in v7.iterrows():
    t_start = pd.Timestamp(f"{int(row['year_announced'])}-06-15")  # mid-year assumption
    t_end = t_start + pd.DateOffset(years=int(row['duration']))
    if t_end > pd.Timestamp('2026-05-19'):  # current date
        t_end = pd.Timestamp('2026-05-19')
    
    months = pd.date_range(t_start, t_end, freq='MS')
    for m in months:
        is_event = (row['event_any'] == 1) and (m.year == row['event_year']) and (m.month >= 6)
        # Also include events from supplement if mapping is closer
        panel_rows.append({
            'project_id': idx,
            'month': m,
            'is_blue_ccs': int(row['is_blue_ccs']),
            'cbam_T1': int(row['cbam_T1']),
            'cbam_T2': int(row['cbam_T2']),
            'cbam_T3': int(row['cbam_T3']),
            'log_capacity_mw': float(row['log_capacity_mw']),
            'region': str(row['region']),
            'event': int(is_event),
            'years_since_start': (m - t_start).days / 365.25,
        })

panel = pd.DataFrame(panel_rows)
panel = panel[(panel['month'] >= '2018-01-01') & (panel['month'] <= '2026-05-01')].copy()

print(f"Person-month panel: {len(panel):,} obs, {panel['event'].sum()} events")
print(f"Date range: {panel['month'].min()} → {panel['month'].max()}")
print(f"\nEvent counts per kalenderjaar:")
print(panel.groupby(panel['month'].dt.year)['event'].sum())


# ============================================================================
# 4. CANDIDATE TREATMENT DATES
# ============================================================================
TREATMENT_DATES = {
    'CBAM_regulation_force': '2023-04-01',     # Regulation enters into force
    'CBAM_transitional':      '2023-10-01',     # Transitional reporting phase
    'CBAM_definitive':        '2026-01-01',     # Definitive (financial) phase
}

# Add post-treatment indicators
for name, date in TREATMENT_DATES.items():
    panel[f'post_{name}'] = (panel['month'] >= pd.Timestamp(date)).astype(int)

print(f"\nPost-treatment fractions:")
for name in TREATMENT_DATES:
    print(f"  post_{name}: {panel[f'post_{name}'].mean()*100:.1f}% van observations")


# ============================================================================
# 5. RUN PROJECT-LEVEL DiD FOR EACH (TREATMENT, EXPOSURE) COMBINATION
# ============================================================================
hdr("Run project-level DiD specifications")

def fit_did(panel, treatment_col, exposure_col, with_blue_interaction=True):
    """
    Logit hazard model met DiD interaction.
    
    eta = α + β_blue*Blue + β_exposed*Exposed + β_post*Post 
        + β_did*(Exposed × Post) + γ controls + ε
    """
    y = panel['event'].values.astype(int)
    X_blue = panel['is_blue_ccs'].values.astype(float)
    X_exp = panel[exposure_col].values.astype(float)
    X_post = panel[treatment_col].values.astype(float)
    X_cap = panel['log_capacity_mw'].values.astype(float)
    X_yrs = panel['years_since_start'].values.astype(float)
    
    # Did interaction
    X_did = X_exp * X_post
    
    with pm.Model() as m:
        alpha = pm.Normal("alpha", -6, 1.5)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_exp = pm.Normal("beta_exposed", 0, 2)
        b_post = pm.Normal("beta_post", 0, 2)
        b_did = pm.Normal("beta_DID", 0, 2)
        b_cap = pm.Normal("beta_cap", 0, 1.5)
        b_yrs = pm.Normal("beta_years_since", 0, 1.5)
        
        eta = (alpha + b_blue*X_blue + b_exp*X_exp + b_post*X_post + b_did*X_did
               + b_cap*X_cap + b_yrs*X_yrs)
        
        pm.Bernoulli("event", logit_p=eta, observed=y)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)
    
    s = az.summary(trace, var_names=['beta_DID', 'beta_blue', 'beta_exposed', 'beta_post'])
    return s, trace

# Run alle combinaties (3 treatment dates × 3 exposure definitions = 9 specs)
results = {}
treatments = ['post_CBAM_regulation_force', 'post_CBAM_transitional', 'post_CBAM_definitive']
exposures = ['cbam_T1', 'cbam_T2', 'cbam_T3']

# Wegens tijdsefficiëntie: run alleen meest relevante (transitional + definitive op T1 en T2)
key_specs = [
    ('post_CBAM_transitional', 'cbam_T1'),
    ('post_CBAM_transitional', 'cbam_T2'),
    ('post_CBAM_transitional', 'cbam_T3'),
    ('post_CBAM_definitive',   'cbam_T1'),
    ('post_CBAM_definitive',   'cbam_T2'),
    ('post_CBAM_definitive',   'cbam_T3'),
    ('post_CBAM_regulation_force', 'cbam_T1'),
]

print(f"\nRunning {len(key_specs)} DiD specifications...\n")
for treat, exp in key_specs:
    print(f"  Fitting: treatment={treat:35s}, exposure={exp}")
    try:
        s, tr = fit_did(panel, treat, exp)
        results[(treat, exp)] = {'summary': s, 'trace': tr}
        b_did = s.loc['beta_DID']
        lo_c = [c for c in s.columns if 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
        hi_c = [c for c in s.columns if 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
        print(f"    → β_DID = {b_did['mean']:+.3f} [{b_did[lo_c]:+.3f}, {b_did[hi_c]:+.3f}]")
    except Exception as e:
        print(f"    FAILED: {e}")

# ============================================================================
# 6. SUMMARY TABLE
# ============================================================================
hdr("SUMMARY: β_DID across specifications")

summary_rows = []
for (treat, exp), data in results.items():
    s = data['summary']
    b_did = s.loc['beta_DID']
    lo_c = [c for c in s.columns if 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
    hi_c = [c for c in s.columns if 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
    cri_lo = b_did[lo_c]
    cri_hi = b_did[hi_c]
    excludes_zero = (cri_lo > 0) or (cri_hi < 0)
    summary_rows.append({
        'treatment': treat.replace('post_', ''),
        'exposure': exp,
        'beta_DID': b_did['mean'],
        'cri_lo': cri_lo,
        'cri_hi': cri_hi,
        'cri_excludes_0': excludes_zero,
    })

results_df = pd.DataFrame(summary_rows)
print(results_df.to_string(index=False))

# Interpretatie
print("\nInterpretatie:")
for _, row in results_df.iterrows():
    sig = "✓ SIGNIFICANT" if row['cri_excludes_0'] else "~ null"
    sign = "negative" if row['beta_DID'] < 0 else "positive"
    print(f"  {row['treatment']:30s} × {row['exposure']}: {sig} ({sign} effect = {row['beta_DID']:+.3f})")

results_df.to_csv(OUT / "did_results_all_specs.csv", index=False)
print(f"\nResultaten in {OUT}")
