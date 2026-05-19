"""
07_within_sponsor.py

CAUSAL IDENTIFICATION via WITHIN-SPONSOR comparison:

Strategie: filter op sponsors die ZOWEL Blue als PEM projecten hebben (8 sponsors).
Voeg sponsor random effects toe aan hazard model. β_int_within wordt geïdentificeerd
puur uit binnen-sponsor variatie, controlerend voor alle sponsor-level confounders.

Vergelijking:
  - Full sample (alle 714 projecten, 256 sponsors waaronder veel "Unknown")
  - Multi-tech sponsors only (404 projecten in 8 sponsors)
  - Multi-tech sponsors met sponsor random effects (causal-style identification)

Als β_int overleeft within-sponsor → effect is niet door sponsor-keuze verklaard.
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
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_within_sponsor"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.99
SEED = 20260518


def hdr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# Data prep
# ============================================================================
hdr("Data prep: identify multi-tech sponsors")
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

# Identify sponsors met zowel Blue als PEM
sponsor_tech = df.groupby('sponsor_owner')['is_blue_ccs'].nunique()
multi_tech_sponsors = sponsor_tech[sponsor_tech == 2].index.tolist()
# Exclude "Unknown" — niet bruikbaar voor identification
multi_tech_sponsors = [s for s in multi_tech_sponsors if s != "Unknown"]
print(f"Multi-tech sponsors ({len(multi_tech_sponsors)}):")
for sp in multi_tech_sponsors:
    sub = df[df['sponsor_owner']==sp]
    b = (sub['is_blue_ccs']==1).sum()
    p = (sub['is_blue_ccs']==0).sum()
    ev = sub['event_any'].sum()
    print(f"  {sp}: Blue={b}, PEM={p}, events={ev}")

df_ms = df[df['sponsor_owner'].isin(multi_tech_sponsors)].copy()
print(f"\nMulti-tech subsample: {len(df_ms)} projecten, {df_ms['event_any'].sum()} events")
print(f"  Blue: {(df_ms['is_blue_ccs']==1).sum()} projects, {df_ms[df_ms['is_blue_ccs']==1]['event_any'].sum()} events")
print(f"  PEM:  {(df_ms['is_blue_ccs']==0).sum()} projects, {df_ms[df_ms['is_blue_ccs']==0]['event_any'].sum()} events")

# Build person-year panel
panel_rows = []
for idx, row in df_ms.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': idx,
            'sponsor_owner': row['sponsor_owner'],
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
        })
panel_ms = pd.DataFrame(panel_rows)
panel_ms = panel_ms[(panel_ms['year_calendar'] >= 2010) & (panel_ms['year_calendar'] <= 2026)].copy()

# Merge EUA
mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
panel_ms = panel_ms.merge(yearly_eua, on='year_calendar', how='left')
panel_ms['mkt_eua'] = panel_ms['eua'].fillna(panel_ms['eua'].median())
eua_mean = panel_ms['mkt_eua'].mean()
eua_sd = panel_ms['mkt_eua'].std()
panel_ms['z'] = (panel_ms['mkt_eua'] - eua_mean) / eua_sd

# Sponsor indices
sponsor_to_idx = {s: i for i, s in enumerate(multi_tech_sponsors)}
panel_ms['sponsor_idx'] = panel_ms['sponsor_owner'].map(sponsor_to_idx).astype(int)
n_sponsors = len(multi_tech_sponsors)

print(f"\nPerson-year panel: {len(panel_ms)} rijen, {panel_ms['event_any_yr'].sum()} events, {n_sponsors} sponsors")


# ============================================================================
# Model arrays
# ============================================================================
X_blue = panel_ms['is_blue_ccs'].values.astype(float)
X_z = panel_ms['z'].values.astype(float)
X_year_since = panel_ms['year_since_start'].values.astype(float)
X_cap = panel_ms['log_capacity_mw'].values.astype(float)
sponsor_idx = panel_ms['sponsor_idx'].values.astype(int)
events_obs = panel_ms['event_any_yr'].values.astype(int)


# ============================================================================
# MODEL 1: Pooled (geen sponsor FE) — baseline op multi-tech subsample
# ============================================================================
hdr(f"Model 1: Pooled multi-tech subsample (geen sponsor FE)")
with pm.Model() as pooled_model:
    alpha = pm.Normal("alpha", -4.5, 1.5)
    beta_blue = pm.Normal("beta_blue", 0, 2)
    beta_eua = pm.Normal("beta_eua", 0, 2)
    beta_int = pm.Normal("beta_int", 0, 2)
    beta_year = pm.Normal("beta_year_since", 0, 1.5)
    beta_cap = pm.Normal("beta_cap", 0, 1.5)
    
    eta = (alpha + beta_blue * X_blue + beta_eua * X_z 
           + beta_int * X_blue * X_z 
           + beta_year * X_year_since + beta_cap * X_cap)
    pm.Bernoulli("events", logit_p=eta, observed=events_obs)
    
    trace_pooled = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                              target_accept=TARGET_ACCEPT, random_seed=SEED,
                              progressbar=False, return_inferencedata=True)


# ============================================================================
# MODEL 2: Sponsor Random Effects (within-sponsor identification)
# ============================================================================
hdr(f"Model 2: Sponsor random effects (causal within-sponsor identification)")
with pm.Model() as sponsor_re_model:
    # Hyper-prior op sponsor heterogeneity
    sigma_sponsor = pm.HalfNormal("sigma_sponsor", 1.0)
    # Sponsor-specifieke intercepts (non-centered)
    sponsor_z = pm.Normal("sponsor_z", 0, 1, shape=n_sponsors)
    sponsor_re = pm.Deterministic("sponsor_re", sigma_sponsor * sponsor_z)
    
    # Globaal niveau
    alpha_global = pm.Normal("alpha_global", -4.5, 1.5)
    
    # Hoofdcoëfficiënten
    beta_blue = pm.Normal("beta_blue", 0, 2)
    beta_eua = pm.Normal("beta_eua", 0, 2)
    beta_int = pm.Normal("beta_int", 0, 2)
    beta_year = pm.Normal("beta_year_since", 0, 1.5)
    beta_cap = pm.Normal("beta_cap", 0, 1.5)
    
    # Linear predictor met sponsor effect
    eta = (alpha_global 
           + sponsor_re[sponsor_idx]
           + beta_blue * X_blue + beta_eua * X_z 
           + beta_int * X_blue * X_z 
           + beta_year * X_year_since + beta_cap * X_cap)
    pm.Bernoulli("events", logit_p=eta, observed=events_obs)
    
    trace_re = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)


# ============================================================================
# Diagnostics + Vergelijking
# ============================================================================
hdr("Diagnostics + within-sponsor vs pooled vergelijking")

def safe_float(x):
    if isinstance(x, (int, float, np.number)): return float(x)
    try: return float(str(x).split("±")[0].strip())
    except: return float("nan")

def hdi_cols(s):
    cols = list(s.columns)
    lo = [c for c in cols if 'lb' in c.lower() or 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
    hi = [c for c in cols if 'ub' in c.lower() or 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
    return lo, hi

def print_diag(name, trace):
    n_div = int(sum(trace.sample_stats.diverging.values.flatten()))
    s = az.summary(trace, var_names=["beta_int", "beta_blue", "beta_eua", "beta_year_since", "beta_cap"])
    print(f"\n{name}: divergences = {n_div}")
    lo_c, hi_c = hdi_cols(s)
    for v in s.index:
        med = safe_float(s.loc[v, 'mean'])
        lo = safe_float(s.loc[v, lo_c])
        hi = safe_float(s.loc[v, hi_c])
        sig = "✓" if (hi < 0 or lo > 0) else " "
        print(f"  {v:20s}: {med:6.3f} [{lo:6.3f}, {hi:6.3f}] {sig}")

print_diag("Model 1 (pooled multi-tech)", trace_pooled)
print_diag("Model 2 (sponsor RE - causal)", trace_re)

# Sponsor RE-specifiek
hdr("Sponsor-level heterogeneity")
s_re = az.summary(trace_re, var_names=["sigma_sponsor", "sponsor_re"])
print(s_re.to_string())

# Volledige vergelijking
hdr("HOOFDVERGELIJKING: β_int across modellen")
print(f"\n{'Model':<35s} | β_int   | 95% CrI               | Interpretatie")
print("-" * 100)

# Full sample (van eerdere script)
print(f"{'Static, full sample (aggregaat)':<35s} | -1.37   | [-2.20, -0.49]        | Static aggregaat (script 05)")

# Multi-tech subsample pooled
s_pooled = az.summary(trace_pooled, var_names=["beta_int"])
lo_c, hi_c = hdi_cols(s_pooled)
m_pooled = safe_float(s_pooled.loc['beta_int', 'mean'])
lo_pooled = safe_float(s_pooled.loc['beta_int', lo_c])
hi_pooled = safe_float(s_pooled.loc['beta_int', hi_c])
print(f"{'Multi-tech pooled (geen FE)':<35s} | {m_pooled:6.3f}  | [{lo_pooled:5.2f}, {hi_pooled:5.2f}]        | Subsample restrictie")

# Sponsor RE
s_re = az.summary(trace_re, var_names=["beta_int"])
lo_c, hi_c = hdi_cols(s_re)
m_re = safe_float(s_re.loc['beta_int', 'mean'])
lo_re = safe_float(s_re.loc['beta_int', lo_c])
hi_re = safe_float(s_re.loc['beta_int', hi_c])
print(f"{'Multi-tech + sponsor RE (CAUSAL)':<35s} | {m_re:6.3f}  | [{lo_re:5.2f}, {hi_re:5.2f}]        | Within-sponsor identification ★")


# Interpretatie
hdr("INTERPRETATIE")
diff = m_re - m_pooled
print(f"Δβ_int (RE - pooled) = {diff:+.3f}")
if abs(diff) < 0.3:
    print("=> β_int verandert WEINIG door sponsor-controle.")
    print("   => Sponsor-keuze is geen substantiële confounder")
    print("   => STERKE evidence voor causaal mechanisme")
elif diff > 0:
    print("=> β_int wordt MINDER negatief (kleiner in magnitude) na sponsor-FE.")
    print("   => Sponsor-keuze verklaart deel van het effect")
    print("   => MATIGE evidence: gemixte causale + selectie verklaring")
else:
    print("=> β_int wordt MEER negatief na sponsor-FE.")
    print("   => Unobserved sponsor characteristics maskeerden effect")
    print("   => STERKE evidence voor causaal mechanisme")

# CrI exclusie van 0?
if hi_re < 0:
    print(f"\n✓ Within-sponsor CrI [{lo_re:.2f}, {hi_re:.2f}] sluit 0 uit — significant causaal effect")
elif lo_re > 0:
    print(f"\n✗ Within-sponsor CrI [{lo_re:.2f}, {hi_re:.2f}] is positief — onverwacht!")
else:
    print(f"\n! Within-sponsor CrI [{lo_re:.2f}, {hi_re:.2f}] bevat 0 — geen causale conclusie mogelijk")
    print("  (mogelijk power-issue met slechts {0} events in {1} sponsors)".format(
        int(panel_ms['event_any_yr'].sum()), n_sponsors))

# Save
output_df = pd.DataFrame({
    'model': ['Pooled (multi-tech)', 'Sponsor RE (causal)'],
    'beta_int_median': [m_pooled, m_re],
    'beta_int_lo95': [lo_pooled, lo_re],
    'beta_int_hi95': [hi_pooled, hi_re],
})
output_df.to_csv(OUT / "within_sponsor_results.csv", index=False)
print(f"\nResultaten opgeslagen in: {OUT}")
