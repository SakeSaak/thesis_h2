"""
08_heterogeneous_effects.py

HETEROGENEOUS TREATMENT EFFECTS analyse:

Test theory-driven voorspelling: het carbon-conditional effect (β_int) zou
sterker moeten zijn in regimes waar EUA echt bindend is.

Drie stratificaties op de full sample (714 projects, 43 events):

  1. REGIO: EU + Other_Europe (ETS-bound) vs North_America (geen ETS) 
     vs Asia + Other (geen of zwak carbon pricing)
     Voorspelling: β_int sterker negatief in ETS-bound regio

  2. SPONSOR_TYPE: Onderzoek of effect uniform is over sponsor categorieën

  3. PROJECT VINTAGE: 2010-2018 (early hydrogen era) vs 2019-2026 (post-Paris)
     Voorspelling: na 2019 wordt EUA meer relevant beleidsmatig

Dit test mechanism zonder causal identification claim, maar bouwt
een coherent mechanism story.
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
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_heterogeneous"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.98
SEED = 20260518


def hdr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)

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
# Data prep - person-year panel met covariates
# ============================================================================
hdr("Data prep — full sample met stratificatie variabelen")
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

# Strata definieren
def assign_carbon_regime(region):
    if region in ['EU', 'Other_Europe']: return 'ETS_bound'
    if region == 'North_America': return 'No_ETS'
    return 'Weak_carbon_pricing'

df['carbon_regime'] = df['region'].apply(assign_carbon_regime)

def assign_vintage(year):
    return 'Pre_2019' if year < 2019 else 'Post_2019'
df['vintage'] = df['year_announced'].apply(assign_vintage)

print("\nCarbon regime distributie:")
print(df.groupby(['carbon_regime', 'is_blue_ccs'])['event_any'].agg(['size','sum']))
print("\nVintage distributie:")
print(df.groupby(['vintage', 'is_blue_ccs'])['event_any'].agg(['size','sum']))

# Person-year panel
panel_rows = []
for idx, row in df.iterrows():
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
            'carbon_regime': row['carbon_regime'],
            'vintage': row['vintage'],
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()

# Merge EUA
mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['eua'].fillna(panel['eua'].median())
eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['z'] = (panel['mkt_eua'] - eua_mean) / eua_sd

print(f"\nPanel: {len(panel)} rijen, {panel['event_any_yr'].sum()} events")


# ============================================================================
# Estimation helper
# ============================================================================
def fit_carbon_conditional(p_subset, label):
    print(f"\n  Fitting: {label} ({len(p_subset)} obs, {p_subset['event_any_yr'].sum()} events)")
    if p_subset['event_any_yr'].sum() < 3:
        print(f"  ⚠ Skip: te weinig events ({p_subset['event_any_yr'].sum()}) voor inferentie")
        return None
    
    X_blue = p_subset['is_blue_ccs'].values.astype(float)
    X_z = p_subset['z'].values.astype(float)
    X_year = p_subset['year_since_start'].values.astype(float)
    X_cap = p_subset['log_capacity_mw'].values.astype(float)
    events = p_subset['event_any_yr'].values.astype(int)
    
    with pm.Model() as m:
        alpha = pm.Normal("alpha", -4.5, 1.5)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        b_int = pm.Normal("beta_int", 0, 2)
        b_year = pm.Normal("beta_year_since", 0, 1.5)
        b_cap = pm.Normal("beta_cap", 0, 1.5)
        eta = (alpha + b_blue * X_blue + b_eua * X_z 
               + b_int * X_blue * X_z + b_year * X_year + b_cap * X_cap)
        pm.Bernoulli("events", logit_p=eta, observed=events)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)
    
    s = az.summary(trace, var_names=["beta_int"])
    lo_c, hi_c = hdi_cols(s)
    return {
        'label': label,
        'n_obs': len(p_subset),
        'n_events': int(p_subset['event_any_yr'].sum()),
        'beta_int': safe_float(s.loc['beta_int', 'mean']),
        'beta_int_lo': safe_float(s.loc['beta_int', lo_c]),
        'beta_int_hi': safe_float(s.loc['beta_int', hi_c]),
        'n_divergences': int(sum(trace.sample_stats.diverging.values.flatten())),
    }


# ============================================================================
# STRATA 1: Carbon regime (ETS-bound vs No_ETS vs Weak)
# ============================================================================
hdr("STRATA 1: Carbon regime")
print("Theoretische voorspelling: β_int sterker negatief in ETS-bound (EU)")

results_regime = []
for regime in ['ETS_bound', 'No_ETS', 'Weak_carbon_pricing']:
    p_sub = panel[panel['carbon_regime'] == regime]
    res = fit_carbon_conditional(p_sub, f"Carbon regime: {regime}")
    if res: results_regime.append(res)


# ============================================================================
# STRATA 2: Vintage (Pre_2019 vs Post_2019)
# ============================================================================
hdr("STRATA 2: Project vintage")
print("Theoretische voorspelling: β_int sterker negatief Post_2019 (na Paris uitwerking)")

results_vintage = []
for vintage in ['Pre_2019', 'Post_2019']:
    p_sub = panel[panel['vintage'] == vintage]
    res = fit_carbon_conditional(p_sub, f"Vintage: {vintage}")
    if res: results_vintage.append(res)


# ============================================================================
# Hoofdvergelijking
# ============================================================================
hdr("RESULTATEN: heterogeneous carbon-conditional effects")

all_results = results_regime + results_vintage
print(f"\n{'Stratificatie':<40s} | n_events | β_int   | 95% CrI         | Sig?")
print("-" * 95)

# Full sample reference (from earlier work)
print(f"{'FULL SAMPLE (referentie, Spoor B-2)':<40s} | 43       | -1.43   | [-2.59, -0.37]  | ✓")
print("-" * 95)

for r in all_results:
    if r is None: continue
    sig = "✓ <0" if r['beta_int_hi'] < 0 else (" ✓ >0" if r['beta_int_lo'] > 0 else "  -  ")
    print(f"{r['label']:<40s} | {r['n_events']:<8d} | {r['beta_int']:6.3f}  | [{r['beta_int_lo']:5.2f}, {r['beta_int_hi']:5.2f}] | {sig}")


# ============================================================================
# Mechanism interpretatie
# ============================================================================
hdr("MECHANISM INTERPRETATIE")

# Carbon regime ranking
sorted_regime = sorted(results_regime, key=lambda x: x['beta_int'])
print("\nCarbon regime ranking (van meest naar minst negatief):")
for r in sorted_regime:
    print(f"  {r['label']:<40s}: β_int = {r['beta_int']:+.2f}")

ets = next((r for r in results_regime if 'ETS_bound' in r['label']), None)
nots = next((r for r in results_regime if 'No_ETS' in r['label']), None)

if ets and nots:
    if ets['beta_int'] < nots['beta_int']:
        print("\n✓ Voorspelling BEVESTIGD: β_int meer negatief in ETS-bound regio dan in No_ETS")
        print("  Mechanism: EUA-effect identifieert zich daar waar EUA bindend is")
    else:
        print("\n✗ Voorspelling NIET bevestigd: ETS-bound effect is niet sterker dan No_ETS")
        print("  Mogelijke verklaring: carbon-conditional patroon is robuust over regimes")
        print("  → suggereert algemener mechanisme dan alleen EU ETS")

# Save
df_res = pd.DataFrame(all_results)
df_res.to_csv(OUT / "heterogeneous_results.csv", index=False)
print(f"\nResultaten in: {OUT}")

# Plot
fig, ax = plt.subplots(figsize=(10, 5))
y = list(range(len(all_results)))
labels = [r['label'] for r in all_results]
means = [r['beta_int'] for r in all_results]
los = [r['beta_int_lo'] for r in all_results]
his = [r['beta_int_hi'] for r in all_results]
ax.errorbar(means, y, xerr=[np.array(means)-np.array(los), np.array(his)-np.array(means)],
            fmt='o', markersize=8, color='#222288', capsize=5)
ax.axvline(0, ls='--', color='red', alpha=0.6, label='β_int = 0')
ax.axvline(-1.43, ls=':', color='gray', alpha=0.6, label='Full sample reference')
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel(r"$\beta_{int}$ (95% CrI)")
ax.set_title("Heterogeneous carbon-conditional effects across strata")
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/heterogeneous_effects.pdf")
plt.close()
print("Figuur opgeslagen.")
