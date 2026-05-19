"""
10_na_deepdive.py

DEEP DIVE: is het North_America negatieve β_int = -1.39 een schoon resultaat
of óók data composition artefact?

Parallel structuur aan 09_eu_deepdive.py:
  A. Event inventaris voor NA
  B. Sponsor compositie
  C. Temporal split: pre-IRA vs post-IRA (Aug 2022)
  D. Re-fit met sponsor controls
  E. NA-only DiD rond IRA (potentially feasible nu we begrijpen waarom EU faalt)
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

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_na_deepdive"
OUT.mkdir(parents=True, exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.98
SEED = 20260518

def hdr(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)
def safe_float(x):
    if isinstance(x, (int, float, np.number)): return float(x)
    try: return float(str(x).split("±")[0].strip())
    except: return float("nan")
def hdi_cols(s):
    cols = list(s.columns)
    lo = [c for c in cols if 'lb' in c.lower() or 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
    hi = [c for c in cols if 'ub' in c.lower() or 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
    return lo, hi

# Data prep
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)
df['event_year'] = df['year_announced'] + df['duration']

mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
yearly_eua.columns = ['year_calendar', 'eua']

# NA subsample
na = df[df['region']=='North_America'].copy()
na_events = na[na['event_any']==1].copy()
na_events = na_events.merge(yearly_eua, left_on='event_year', right_on='year_calendar', how='left')


# ============================================================================
# A. Event inventaris
# ============================================================================
hdr("A. North_America events — wie, wanneer, EUA-niveau")
print(f"\nTotaal NA events: {len(na_events)}")
print(f"  Blue events: {len(na_events[na_events['is_blue_ccs']==1])}")
print(f"  PEM events: {len(na_events[na_events['is_blue_ccs']==0])}")

cols_show = ['region','tech','is_blue_ccs','sponsor_owner','sponsor_type',
             'year_announced','event_year','eua','log_capacity_mw']
print("\nAlle NA events:")
print(na_events[cols_show].sort_values(['event_year','is_blue_ccs']).to_string())


# ============================================================================
# B. Sponsor compositie — kritiek na EU deep-dive
# ============================================================================
hdr("B. NA sponsor compositie — Unknown vs Named sponsors")
print("\nNA events per sponsor (alle):")
print(na_events.groupby(['sponsor_owner','is_blue_ccs']).size().rename('n_events'))

print("\nNA events per sponsor_type:")
print(na_events.groupby(['sponsor_type','is_blue_ccs']).size().rename('n_events'))

# KRITIEK: hoeveel Blue vs PEM events hebben Unknown sponsor?
print("\nNamed vs Unknown sponsors in NA events:")
na_events['sponsor_known'] = na_events['sponsor_owner'] != 'Unknown'
print(na_events.groupby(['sponsor_known','is_blue_ccs']).size().rename('n_events'))

# Mean EUA per technology per sponsor type
print("\nMean EUA bij events, per (sponsor_known, tech):")
print(na_events.groupby(['sponsor_known','is_blue_ccs'])['eua'].agg(['mean','count']))


# ============================================================================
# C. Temporal: pre/post IRA (Aug 2022)
# ============================================================================
hdr("C. Pre/post IRA temporal split")
na_events['period'] = na_events['event_year'].apply(lambda y: 'pre_IRA' if y < 2022.5 else 'post_IRA')
print("\nEvent counts NA per period × tech:")
print(na_events.groupby(['period','is_blue_ccs']).size().rename('n_events'))

# At-risk panel pre/post IRA
print("\nNA at-risk per period × tech (panel):")
panel_rows = []
for idx, row in na.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': idx, 'year_calendar': t,
            'is_blue_ccs': int(row['is_blue_ccs']),
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'year_since_start': t - t_start,
            'log_capacity_mw': float(row['log_capacity_mw']),
            'sponsor_known': int(row['sponsor_owner'] != 'Unknown'),
        })
panel_na = pd.DataFrame(panel_rows)
panel_na = panel_na[(panel_na['year_calendar'] >= 2010) & (panel_na['year_calendar'] <= 2026)].copy()
panel_na['period'] = panel_na['year_calendar'].apply(lambda y: 'pre_IRA' if y < 2022.5 else 'post_IRA')

print(panel_na.groupby(['period','is_blue_ccs']).agg(
    n_obs=('event_any_yr','size'),
    n_events=('event_any_yr','sum')
))


# ============================================================================
# D. Re-fit met sponsor control
# ============================================================================
hdr("D. NA carbon-conditional MET sponsor_known controle")
panel_na = panel_na.merge(yearly_eua, on='year_calendar', how='left')
panel_na['mkt_eua'] = panel_na['eua'].fillna(panel_na['eua'].median())
eua_mean = panel_na['mkt_eua'].mean()
eua_sd = panel_na['mkt_eua'].std()
panel_na['z'] = (panel_na['mkt_eua'] - eua_mean) / eua_sd

def fit_na(p, with_sponsor=False):
    X_blue = p['is_blue_ccs'].values.astype(float)
    X_z = p['z'].values.astype(float)
    X_year = p['year_since_start'].values.astype(float)
    X_cap = p['log_capacity_mw'].values.astype(float)
    X_sk = p['sponsor_known'].values.astype(float)
    events = p['event_any_yr'].values.astype(int)
    with pm.Model() as m:
        alpha = pm.Normal("alpha", -4.5, 1.5)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        b_int = pm.Normal("beta_int", 0, 2)
        b_year = pm.Normal("beta_year_since", 0, 1.5)
        b_cap = pm.Normal("beta_cap", 0, 1.5)
        eta = alpha + b_blue * X_blue + b_eua * X_z + b_int * X_blue * X_z + b_year * X_year + b_cap * X_cap
        if with_sponsor:
            b_sk = pm.Normal("beta_sponsor_known", 0, 1.5)
            eta = eta + b_sk * X_sk
        pm.Bernoulli("events", logit_p=eta, observed=events)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)
    s = az.summary(trace, var_names=["beta_int","beta_blue","beta_eua"] + (["beta_sponsor_known"] if with_sponsor else []))
    return s

print("\nNA zonder sponsor control:")
s1 = fit_na(panel_na, with_sponsor=False)
print(s1.round(3).to_string())

print("\nNA MET sponsor_known control:")
s2 = fit_na(panel_na, with_sponsor=True)
print(s2.round(3).to_string())


# ============================================================================
# E. NA-only DiD rond IRA (alle NA projecten)
# ============================================================================
hdr("E. NA-only Difference-in-Differences rond IRA (Aug 2022)")
print("Triple-DiD: hazard ~ Blue + Post_IRA + Blue × Post_IRA + controls")
print("Test: heeft IRA differentieel green gered (negatieve Blue × Post_IRA coefficient)?")

panel_na['post_ira'] = (panel_na['year_calendar'] >= 2023).astype(int)

X_blue = panel_na['is_blue_ccs'].values.astype(float)
X_post = panel_na['post_ira'].values.astype(float)
X_year = panel_na['year_since_start'].values.astype(float)
X_cap = panel_na['log_capacity_mw'].values.astype(float)
X_sk = panel_na['sponsor_known'].values.astype(float)
events = panel_na['event_any_yr'].values.astype(int)

with pm.Model() as did_model:
    alpha = pm.Normal("alpha", -5, 1.5)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_post = pm.Normal("beta_post", 0, 2)
    # DE CRUCIALE COEFFICIENT: IRA differential effect op Blue vs PEM
    b_blue_post = pm.Normal("beta_blue_post", 0, 2)
    b_year = pm.Normal("beta_year_since", 0, 1.5)
    b_cap = pm.Normal("beta_cap", 0, 1.5)
    b_sk = pm.Normal("beta_sponsor_known", 0, 1.5)
    eta = (alpha + b_blue * X_blue + b_post * X_post 
           + b_blue_post * X_blue * X_post
           + b_year * X_year + b_cap * X_cap + b_sk * X_sk)
    pm.Bernoulli("events", logit_p=eta, observed=events)
    trace_did = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)

s_did = az.summary(trace_did, var_names=["beta_blue","beta_post","beta_blue_post","beta_sponsor_known"])
print(s_did.round(3).to_string())

print("\n" + "=" * 72)
print("INTERPRETATIE NA-only DiD")
print("=" * 72)
lo_c, hi_c = hdi_cols(s_did)
bp_mean = safe_float(s_did.loc['beta_blue_post','mean'])
bp_lo = safe_float(s_did.loc['beta_blue_post',lo_c])
bp_hi = safe_float(s_did.loc['beta_blue_post',hi_c])
print(f"\nIRA × Blue interaction: β = {bp_mean:.2f} [{bp_lo:.2f}, {bp_hi:.2f}]")
if bp_hi < 0:
    print(f"  → IRA REDUCED Blue cancellation rate differentially (vs PEM)")
    print(f"  → Treatment effect: Blue HR fell by factor {np.exp(bp_mean):.2f} more than PEM post-IRA")
    print(f"  → CAUSAAL bewijs van IRA effect op Blue vs PEM differential")
elif bp_lo > 0:
    print(f"  → IRA INCREASED Blue cancellation rate differentially")
    print(f"  → Treatment effect: Blue HR rose by factor {np.exp(bp_mean):.2f} more than PEM post-IRA")
    print(f"  → IRA hurt Blue projecten (mogelijk via concurrentie van green)")
else:
    print(f"  → CrI bevat 0 — geen causaal effect identificeerbaar")
    print(f"  → Mogelijk power-issue gegeven sample grootte")

print(f"\nResultaten in: {OUT}")
