"""
09_eu_deepdive.py

DEEP DIVE: waarom is β_int positief in ETS-bound regio (EU + Other_Europe)?

Vijf onderzoeken om de finding te ontleden:
  A. Event inventaris: wie, wanneer, EUA-niveau, sponsor type
  B. Sub-regional split: EU vs Other_Europe (UK valt onder Other_Europe na Brexit)
  C. Temporele split: pre-2023 vs 2023+ (peak cancellation periode)
  D. Sponsor type analyse: state-backed vs industrial vs unknown
  E. Influence analysis: leave-one-event-out om robuustheid te testen
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
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_eu_deepdive"
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


# ============================================================================
# Data prep
# ============================================================================
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

# EU + Other_Europe subsample
eu = df[df['region'].isin(['EU','Other_Europe'])].copy()
eu_events = eu[eu['event_any']==1].copy()

# Merge EUA at cancellation time
eu_events = eu_events.merge(yearly_eua, left_on='event_year', right_on='year_calendar', how='left')


# ============================================================================
# A. EVENT INVENTARIS
# ============================================================================
hdr("A. EU events — wie, wanneer, EUA-niveau bij cancellation")
print(f"\nTotaal EU+Other_Europe events: {len(eu_events)}")
print(f"  Blue events: {len(eu_events[eu_events['is_blue_ccs']==1])}")
print(f"  PEM events: {len(eu_events[eu_events['is_blue_ccs']==0])}")

print("\nAlle EU events in detail:")
cols_show = ['region','tech','is_blue_ccs','sponsor_owner','sponsor_type',
             'year_announced','event_year','eua','log_capacity_mw']
for col in cols_show:
    if col not in eu_events.columns:
        continue
print(eu_events[cols_show].sort_values(['event_year','is_blue_ccs']).to_string())

# Cruciale observatie: EUA niveau bij cancellation
print(f"\nEUA distributie bij Blue cancellation events in EU:")
blue_evs = eu_events[eu_events['is_blue_ccs']==1]
print(blue_evs['eua'].describe().round(1))
print(f"\nEUA distributie bij PEM cancellation events in EU:")
pem_evs = eu_events[eu_events['is_blue_ccs']==0]
print(pem_evs['eua'].describe().round(1))

# Belangrijke vraag: zijn blue cancellations geclusterd bij HIGH of LOW EUA?
print(f"\nMean EUA at Blue EU cancellation: €{blue_evs['eua'].mean():.1f}")
print(f"Mean EUA at PEM EU cancellation: €{pem_evs['eua'].mean():.1f}")
if blue_evs['eua'].mean() > pem_evs['eua'].mean():
    print("→ Blue cancellations gebeuren bij HOGERE EUA dan PEM cancellations")
    print("  Dit is consistent met het waargenomen POSITIEVE β_int (omgekeerd patroon)")
else:
    print("→ Blue cancellations gebeuren bij LAGERE EUA dan PEM cancellations")
    print("  Dit is consistent met de oorspronkelijke (negatieve) carbon-conditional theorie")


# ============================================================================
# B. SUB-REGIONAL: EU vs Other_Europe
# ============================================================================
hdr("B. Sub-regional split: EU vs Other_Europe (UK valt onder Other_Europe na Brexit)")
print("\nEvent counts per sub-region:")
sub = eu.groupby(['region','is_blue_ccs']).agg(
    n_proj=('event_any','size'),
    n_ev=('event_any','sum')
)
print(sub)

# Geen aparte gegevens voor Brexit-jaar, maar Other_Europe omvat UK
print("\nMean EUA at events per sub-region:")
print(eu_events.groupby(['region','is_blue_ccs'])['eua'].mean().round(1))


# ============================================================================
# C. TEMPORAL SPLIT: pre-2023 vs 2023+
# ============================================================================
hdr("C. Temporele split — pre-2023 vs 2023+")
print("\nEU+Other_Europe events per periode:")
eu_events['period'] = eu_events['event_year'].apply(lambda y: 'pre_2023' if y < 2023 else '2023+')
print(eu_events.groupby(['period','is_blue_ccs']).size().rename('n_events'))


# ============================================================================
# D. SPONSOR TYPE ANALYSE
# ============================================================================
hdr("D. Sponsor analyse — wie cancelt in EU?")
print("\nEU+Other_Europe events per sponsor_type:")
if 'sponsor_type' in eu_events.columns:
    print(eu_events.groupby(['sponsor_type','is_blue_ccs']).size().rename('n_events'))
print("\nUnieke sponsors die in EU hebben gecanceld:")
print(eu_events.groupby('sponsor_owner')['is_blue_ccs'].agg(['count','sum']))


# ============================================================================
# E. INFLUENCE ANALYSIS: leave-one-event-out (LOEO)
# ============================================================================
hdr("E. Leave-one-event-out: hoe robust is de positieve β_int in EU?")

# Bouw EU+Other_Europe person-year panel
panel_rows = []
for idx, row in eu.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': idx,
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
        })
panel_eu = pd.DataFrame(panel_rows)
panel_eu = panel_eu[(panel_eu['year_calendar'] >= 2010) & (panel_eu['year_calendar'] <= 2026)].copy()
panel_eu = panel_eu.merge(yearly_eua, on='year_calendar', how='left')
panel_eu['mkt_eua'] = panel_eu['eua'].fillna(panel_eu['eua'].median())
eua_mean = panel_eu['mkt_eua'].mean()
eua_sd = panel_eu['mkt_eua'].std()
panel_eu['z'] = (panel_eu['mkt_eua'] - eua_mean) / eua_sd

# Find rows die events markeren
event_indices = panel_eu[panel_eu['event_any_yr']==1].index.tolist()
print(f"\nAantal events om uit te sluiten: {len(event_indices)}")

def fit_eu(p):
    X_blue = p['is_blue_ccs'].values.astype(float)
    X_z = p['z'].values.astype(float)
    X_year = p['year_since_start'].values.astype(float)
    X_cap = p['log_capacity_mw'].values.astype(float)
    events = p['event_any_yr'].values.astype(int)
    with pm.Model() as m:
        alpha = pm.Normal("alpha", -4.5, 1.5)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        b_int = pm.Normal("beta_int", 0, 2)
        b_year = pm.Normal("beta_year_since", 0, 1.5)
        b_cap = pm.Normal("beta_cap", 0, 1.5)
        eta = alpha + b_blue * X_blue + b_eua * X_z + b_int * X_blue * X_z + b_year * X_year + b_cap * X_cap
        pm.Bernoulli("events", logit_p=eta, observed=events)
        trace = pm.sample(800, tune=1000, chains=2, target_accept=0.98,
                          random_seed=SEED, progressbar=False, return_inferencedata=True)
    s = az.summary(trace, var_names=["beta_int"])
    lo_c, hi_c = hdi_cols(s)
    return safe_float(s.loc['beta_int','mean']), safe_float(s.loc['beta_int',lo_c]), safe_float(s.loc['beta_int',hi_c])

# Baseline (alle events)
print("\nBaseline (alle EU events):")
m_base, lo_base, hi_base = fit_eu(panel_eu)
print(f"  β_int = {m_base:.2f} [{lo_base:.2f}, {hi_base:.2f}]")

# Leave-one-event-out
print("\nLeave-one-event-out (LOEO) per event:")
loeo_results = []
for i, ev_idx in enumerate(event_indices):
    panel_drop = panel_eu.drop(ev_idx).copy()
    # Reset het project's events naar 0 voor consistentie
    pid = panel_eu.loc[ev_idx, 'project_id']
    # Subselect this project's other rows; gewoon event_any_yr=0
    panel_drop = panel_drop[panel_drop['project_id']!=pid]  # Drop ALL rows of this project
    try:
        m, lo, hi = fit_eu(panel_drop)
        loeo_results.append({'event_idx': ev_idx, 'project_id': pid, 'beta_int': m, 'lo': lo, 'hi': hi})
        print(f"  Drop event #{i+1} (project {pid}): β_int = {m:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    except Exception as e:
        print(f"  Drop event #{i+1}: ERROR ({e})")

# Summary
if loeo_results:
    print(f"\nLOEO summary:")
    betas = [r['beta_int'] for r in loeo_results]
    print(f"  Min β_int: {min(betas):.2f}")
    print(f"  Max β_int: {max(betas):.2f}")
    print(f"  Range: {max(betas)-min(betas):.2f}")
    # Welke event verschuift β_int het meest?
    sorted_results = sorted(loeo_results, key=lambda r: r['beta_int'])
    print(f"\nMeest extreme LOEO resultaten:")
    print(f"  Laagste β_int (event drop met grootste impact downward): event {sorted_results[0]['project_id']}, β_int = {sorted_results[0]['beta_int']:+.2f}")
    print(f"  Hoogste β_int (event drop met grootste impact upward): event {sorted_results[-1]['project_id']}, β_int = {sorted_results[-1]['beta_int']:+.2f}")
    
    pd.DataFrame(loeo_results).to_csv(OUT / "loeo_results.csv", index=False)


print(f"\nResultaten in: {OUT}")
