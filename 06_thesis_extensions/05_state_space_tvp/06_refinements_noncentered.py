"""
06_refinements_noncentered.py

A1 METHODOLOGICAL REFINEMENTS voor Chapter 7:
  - Non-centered parameterisatie van block random walks (lost divergences op)
  - 4 chains in plaats van 2 (proper convergentie diagnostics)
  - target_accept = 0.99
  - Pareto k diagnostic per model
  - Vergelijk met centered versie uit script 02

Non-centered specificatie:
  β_int_init ~ N(-1, 2)
  delta_b ~ N(0, 1) for b = 1,...,B-1
  sigma_int ~ HalfNormal(0.5)
  β_int(b) = β_int_init + sigma_int * sum_{j<=b}(delta_j)

Dit is wiskundig equivalent maar geometrisch beter geconditioneerd voor HMC.
"""
from __future__ import annotations
from pathlib import Path
import warnings, json
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
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_refinements"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

# 4 CHAINS, 1500 draws, 2000 tune, target_accept 0.99
N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.99
SEED = 20260518


def hdr(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# === Data aggregaat (identiek aan script 05) ===
hdr("Building year × tech aggregaat")
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

panel_rows = []
for idx, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'year_calendar': t,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()

mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['eua'].fillna(panel['eua'].median())
eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['z'] = (panel['mkt_eua'] - eua_mean) / eua_sd

agg = panel.groupby(['year_calendar','is_blue_ccs']).agg(
    n_at_risk=('event_any_yr', 'size'),
    n_events=('event_any_yr', 'sum'),
    z=('z', 'first'),
).reset_index()

all_years = sorted(panel['year_calendar'].unique())
n_years = len(all_years)

def get_yr(year, blue):
    sub = agg[(agg['year_calendar']==year) & (agg['is_blue_ccs']==blue)]
    if len(sub) == 0:
        eua_val = float(yearly_eua[yearly_eua['year_calendar']==year]['eua'].iloc[0])
        return 0, 0, (eua_val - eua_mean) / eua_sd
    r = sub.iloc[0]
    return int(r['n_at_risk']), int(r['n_events']), float(r['z'])

blue_at = np.array([get_yr(y, 1)[0] for y in all_years], dtype=float)
blue_ev = np.array([get_yr(y, 1)[1] for y in all_years], dtype=float)
pem_at  = np.array([get_yr(y, 0)[0] for y in all_years], dtype=float)
pem_ev  = np.array([get_yr(y, 0)[1] for y in all_years], dtype=float)
z_arr   = np.array([get_yr(y, 1)[2] for y in all_years], dtype=float)

print(f"  {n_years} jaren, {int(blue_ev.sum())+int(pem_ev.sum())} totaal events")


def make_block_index(years, n_blocks):
    if n_blocks == 3:
        def f(y):
            if y <= 2022: return 0
            if y <= 2024: return 1
            return 2
    elif n_blocks == 4:
        def f(y):
            if y <= 2019: return 0
            if y <= 2022: return 1
            if y <= 2024: return 2
            return 3
    elif n_blocks == 5:
        def f(y):
            if y <= 2014: return 0
            if y <= 2019: return 1
            if y <= 2022: return 2
            if y <= 2024: return 3
            return 4
    return np.array([f(y) for y in years], dtype=int)


def fit_blocks_noncentered(n_blocks):
    hdr(f"Non-centered {n_blocks}-block TVP ({N_CHAINS} chains × {N_DRAWS} draws)")
    block_idx = make_block_index(all_years, n_blocks)
    
    with pm.Model() as m:
        # Static params
        alpha_int = pm.Normal("alpha_int", -4.0, 1.0)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        
        # NON-CENTERED parameterisatie van random walk over blocks
        beta_int_init = pm.Normal("beta_int_init", -1.0, 2.0)
        sigma_int = pm.HalfNormal("sigma_int", 0.5)
        # delta heeft n_blocks-1 innovations (block 0 = init, blocks 1..n-1 increments)
        delta = pm.Normal("delta", 0, 1, shape=n_blocks - 1)
        # increments[0] = 0 voor block 0, increments[b] = sigma * delta[b-1]
        increments = pt.concatenate([pt.zeros(1), sigma_int * delta])
        beta_int_b = pm.Deterministic("beta_int_b", beta_int_init + pt.cumsum(increments))
        
        beta_int_vec = beta_int_b[block_idx]
        eta_blue_full = alpha_int + b_blue + b_eua * z_arr + beta_int_vec * z_arr
        eta_pem_full = alpha_int + b_eua * z_arr
        pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue_full), observed=blue_ev)
        pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem_full), observed=pem_ev)
        
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, max_treedepth=12,
                          random_seed=SEED, progressbar=False,
                          return_inferencedata=True,
                          idata_kwargs={"log_likelihood": True})
    return trace


# Run alle 3 block specifications
results = {}
for nb in [3, 4, 5]:
    results[f"{nb}block"] = fit_blocks_noncentered(nb)


# === Diagnostics ===
hdr("DIAGNOSTICS COMPARISON (non-centered)")
for name, trace in results.items():
    n_div = int(sum(trace.sample_stats.diverging.values.flatten()))
    s = az.summary(trace, var_names=["beta_int_b", "sigma_int", "alpha_int", "beta_blue", "beta_eua"])
    
    # Extract r_hat and ess_bulk safely (kunnen strings zijn in nieuwere arviz)
    def safe_float(x):
        if isinstance(x, (int, float, np.number)): return float(x)
        try: return float(str(x).split("±")[0].strip())
        except: return float("nan")
    
    rhats = s['r_hat'].apply(safe_float) if 'r_hat' in s.columns else None
    esss = s['ess_bulk'].apply(safe_float) if 'ess_bulk' in s.columns else None
    
    max_rhat = rhats.max() if rhats is not None else np.nan
    min_ess = esss.min() if esss is not None else np.nan
    
    print(f"\n{name}:")
    print(f"  Divergences: {n_div}")
    print(f"  Max R-hat: {max_rhat:.4f}")
    print(f"  Min ESS_bulk: {min_ess:.0f}")
    
    # Pareto k diagnostic
    try:
        loo_result = az.loo(trace, var_name='blue_obs', pointwise=True)
        pareto_k = loo_result.pareto_k.values if hasattr(loo_result, 'pareto_k') else None
        if pareto_k is not None:
            n_ok = int((pareto_k < 0.5).sum())
            n_warning = int(((pareto_k >= 0.5) & (pareto_k < 0.7)).sum())
            n_bad = int(((pareto_k >= 0.7) & (pareto_k < 1.0)).sum())
            n_very_bad = int((pareto_k >= 1.0).sum())
            print(f"  Pareto k: ok(<0.5)={n_ok}, warning(0.5-0.7)={n_warning}, bad(0.7-1)={n_bad}, very_bad(>=1)={n_very_bad}")
    except Exception as e:
        print(f"  Pareto k niet beschikbaar: {e}")

# === Print β_int posteriors voor 4-block (de hoofdspecificatie) ===
hdr("β_int(b) per regime — non-centered 4-block (vergelijk met centered)")
s4 = az.summary(results['4block'], var_names=["beta_int_b"])
def safe_float(x):
    if isinstance(x, (int, float, np.number)): return float(x)
    try: return float(str(x).split("±")[0].strip())
    except: return float("nan")

block_names_4 = ["2010-2019", "2020-2022", "2023-2024", "2025-2026"]
print("\nVergelijk met centered versie (script 02):")
print("  Block               | Non-centered      | Centered (script 02)")
print("  --------------------|-------------------|--------------------")
centered_results = [
    ("2010-2019", -1.587, -2.969, -0.444),
    ("2020-2022", -1.808, -3.273, -0.547),
    ("2023-2024", -0.817, -2.443, +0.669),
    ("2025-2026", -1.876, -4.184, -0.182),
]
for i, (name_block, c_med, c_lo, c_hi) in enumerate(centered_results):
    nc_med = safe_float(s4.iloc[i]['mean'])
    # Find HDI columns flexible
    lo_col = [c for c in s4.columns if 'lb' in c.lower() or 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
    hi_col = [c for c in s4.columns if 'ub' in c.lower() or 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
    nc_lo = safe_float(s4.iloc[i][lo_col])
    nc_hi = safe_float(s4.iloc[i][hi_col])
    print(f"  {name_block:19s} | {nc_med:5.2f} [{nc_lo:5.2f},{nc_hi:5.2f}] | {c_med:5.2f} [{c_lo:5.2f},{c_hi:5.2f}]")


# Save resultaten
output_summary = {}
for name, trace in results.items():
    n_div = int(sum(trace.sample_stats.diverging.values.flatten()))
    output_summary[name] = {'n_divergences': n_div}
    s = az.summary(trace, var_names=["beta_int_b"])
    rows = []
    for i in range(int(name[0])):
        rows.append({
            'block': i,
            'mean': safe_float(s.iloc[i]['mean']),
        })
    output_summary[name]['blocks'] = rows

with open(OUT / "noncentered_summary.json", 'w') as f:
    json.dump(output_summary, f, indent=2)
print(f"\nAlle resultaten in: {OUT}")
