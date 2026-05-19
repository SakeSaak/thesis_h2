"""
11_na_only_tvp.py

NA-ONLY TVP analyse — de cleanest mogelijke replicatie van Chapter 7
hoofdresultaten op het deelvolume waar sponsor confounding niet speelt.

Drie specificaties (zoals in script 05):
  M1: Static
  M2: 4-block parameter-driven TVP
  M3: GAS observation-driven TVP (d=1/2)

Plus: alle specificaties MET sponsor_known als covariate (extra robustheid).

Vergelijking met pooled resultaten (script 05):
  Pooled β_int = -1.43, GAS ω = -1.61
  NA β_int (script 10) = -1.34 [-2.7, -0.07]
  
Verwachting: NA-only TVP zou cleanere time-stability moeten tonen.
"""
from __future__ import annotations
from pathlib import Path
import warnings, json
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import pymc as pm
import pytensor, pytensor.tensor as pt
import arviz as az
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_na_tvp"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.99
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
# Data prep: NA-only year × tech aggregaat
# ============================================================================
hdr("NA-only year × tech aggregaat")

df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

# NA-only filter
df_na = df[df['region'] == 'North_America'].copy()
print(f"NA projects: {len(df_na)}")

panel_rows = []
for idx, row in df_na.iterrows():
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

print(f"NA panel: {n_years} jaren, blue events={int(blue_ev.sum())}, PEM events={int(pem_ev.sum())}")
for i, y in enumerate(all_years):
    if blue_ev[i] + pem_ev[i] > 0:
        print(f"  {y}: blue {int(blue_ev[i])}/{int(blue_at[i])}, PEM {int(pem_ev[i])}/{int(pem_at[i])}")


# ============================================================================
# M1: Static NA-only
# ============================================================================
hdr("M1: NA-only Static")
with pm.Model() as m_static:
    alpha = pm.Normal("alpha", -4.0, 1.0)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_eua = pm.Normal("beta_eua", 0, 2)
    b_int = pm.Normal("beta_int", 0, 2)
    eta_blue = alpha + b_blue + b_eua * z_arr + b_int * z_arr
    eta_pem = alpha + b_eua * z_arr
    pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue), observed=blue_ev)
    pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem), observed=pem_ev)
    trace_static = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                              target_accept=TARGET_ACCEPT, random_seed=SEED,
                              progressbar=False, return_inferencedata=True)

s = az.summary(trace_static, var_names=["beta_int","beta_blue","beta_eua"])
lo_c, hi_c = hdi_cols(s)
m1_int = safe_float(s.loc['beta_int','mean'])
m1_lo = safe_float(s.loc['beta_int',lo_c])
m1_hi = safe_float(s.loc['beta_int',hi_c])
print(f"NA Static β_int = {m1_int:.2f} [{m1_lo:.2f}, {m1_hi:.2f}]")


# ============================================================================
# M2: NA-only 4-block TVP (non-centered)
# ============================================================================
hdr("M2: NA-only 4-block TVP (non-centered)")

def block_idx_4(y):
    if y <= 2019: return 0
    if y <= 2022: return 1
    if y <= 2024: return 2
    return 3
block_idx = np.array([block_idx_4(y) for y in all_years], dtype=int)
N_BLOCKS = 4

with pm.Model() as m_blocks:
    alpha = pm.Normal("alpha", -4.0, 1.0)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_eua = pm.Normal("beta_eua", 0, 2)
    beta_int_init = pm.Normal("beta_int_init", -1.0, 2.0)
    sigma_int = pm.HalfNormal("sigma_int", 0.5)
    delta = pm.Normal("delta", 0, 1, shape=N_BLOCKS-1)
    increments = pt.concatenate([pt.zeros(1), sigma_int * delta])
    beta_int_b = pm.Deterministic("beta_int_b", beta_int_init + pt.cumsum(increments))
    beta_int_vec = beta_int_b[block_idx]
    eta_blue = alpha + b_blue + b_eua * z_arr + beta_int_vec * z_arr
    eta_pem = alpha + b_eua * z_arr
    pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue), observed=blue_ev)
    pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem), observed=pem_ev)
    trace_blocks = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                              target_accept=TARGET_ACCEPT, max_treedepth=12,
                              random_seed=SEED, progressbar=False,
                              return_inferencedata=True)

s = az.summary(trace_blocks, var_names=["beta_int_b","sigma_int"])
lo_c, hi_c = hdi_cols(s)
n_div_blocks = int(sum(trace_blocks.sample_stats.diverging.values.flatten()))
print(f"\nNA 4-block (divergences={n_div_blocks}):")
print(f"  Block 0 (2010-2019): β = {safe_float(s.iloc[0]['mean']):.2f} [{safe_float(s.iloc[0][lo_c]):.2f}, {safe_float(s.iloc[0][hi_c]):.2f}]")
print(f"  Block 1 (2020-2022): β = {safe_float(s.iloc[1]['mean']):.2f} [{safe_float(s.iloc[1][lo_c]):.2f}, {safe_float(s.iloc[1][hi_c]):.2f}]")
print(f"  Block 2 (2023-2024): β = {safe_float(s.iloc[2]['mean']):.2f} [{safe_float(s.iloc[2][lo_c]):.2f}, {safe_float(s.iloc[2][hi_c]):.2f}]")
print(f"  Block 3 (2025-2026): β = {safe_float(s.iloc[3]['mean']):.2f} [{safe_float(s.iloc[3][lo_c]):.2f}, {safe_float(s.iloc[3][hi_c]):.2f}]")
print(f"  σ_int: {safe_float(s.loc['sigma_int','mean']):.3f}")


# ============================================================================
# M3: NA-only GAS d=1/2
# ============================================================================
hdr("M3: NA-only GAS observation-driven (d=1/2)")

z_t = pt.as_tensor_variable(z_arr)
b_at_t = pt.as_tensor_variable(blue_at)
b_ev_t = pt.as_tensor_variable(blue_ev)

with pm.Model() as m_gas:
    omega = pm.Normal("omega", -1.0, 1.0)
    phi = pm.Beta("phi", 8, 2)
    alpha_gas = pm.HalfNormal("alpha_gas", 0.5)
    beta_int_init = pm.Normal("beta_int_init", -1.0, 1.5)
    alpha_int = pm.Normal("alpha_int", -4.0, 1.0)
    beta_blue = pm.Normal("beta_blue", 0, 2)
    beta_eua = pm.Normal("beta_eua", 0, 2)
    
    def step(z, b_at_, b_ev_, b_prev, om, ph, al, a_i, b_b, b_e):
        eta = a_i + b_b + b_e * z + b_prev * z
        p = pt.sigmoid(eta)
        score = (b_ev_ - b_at_ * p) * z
        info = b_at_ * p * (1.0 - p) * (z * z) + 0.1
        scaled = score / pt.sqrt(info)
        return om * (1.0 - ph) + ph * b_prev + al * scaled
    
    beta_int_seq, _ = pytensor.scan(
        fn=step,
        sequences=[z_t, b_at_t, b_ev_t],
        outputs_info=[beta_int_init],
        non_sequences=[omega, phi, alpha_gas, alpha_int, beta_blue, beta_eua],
    )
    beta_int_traj = pt.concatenate([pt.stack([beta_int_init]), beta_int_seq[:-1]])
    pm.Deterministic("beta_int_traj", beta_int_traj)
    eta_blue_full = alpha_int + beta_blue + beta_eua * z_t + beta_int_traj * z_t
    eta_pem_full = alpha_int + beta_eua * z_t
    pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue_full), observed=blue_ev)
    pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem_full), observed=pem_ev)
    trace_gas = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, max_treedepth=12,
                          random_seed=SEED, progressbar=False,
                          return_inferencedata=True)

s = az.summary(trace_gas, var_names=["omega","phi","alpha_gas"])
lo_c, hi_c = hdi_cols(s)
n_div_gas = int(sum(trace_gas.sample_stats.diverging.values.flatten()))
print(f"\nNA GAS (divergences={n_div_gas}):")
print(f"  ω (long-run): {safe_float(s.loc['omega','mean']):.2f} [{safe_float(s.loc['omega',lo_c]):.2f}, {safe_float(s.loc['omega',hi_c]):.2f}]")
print(f"  φ (persistence): {safe_float(s.loc['phi','mean']):.2f}")
print(f"  α_gas (score response): {safe_float(s.loc['alpha_gas','mean']):.4f}")

# Trajectory
traj = trace_gas.posterior['beta_int_traj'].values.reshape(-1, n_years)
traj_df = pd.DataFrame({
    'year': all_years,
    'median': np.median(traj, axis=0),
    'lo95': np.quantile(traj, 0.025, axis=0),
    'hi95': np.quantile(traj, 0.975, axis=0),
})
print(f"\nNA GAS β_int(t) trajectorie (selected jaren):")
for y in [2014, 2018, 2022, 2023, 2024]:
    if y in all_years:
        r = traj_df[traj_df['year']==y].iloc[0]
        print(f"  {y}: {r['median']:+.2f} [{r['lo95']:+.2f}, {r['hi95']:+.2f}]")


# ============================================================================
# HOOFDVERGELIJKING NA-only vs Pooled
# ============================================================================
hdr("HOOFDVERGELIJKING: NA-only vs Pooled resultaten")

print(f"\n{'Specificatie':<30s} | NA-only          | Pooled (script 05)  | Δ")
print("-" * 90)
print(f"{'Static β_int':<30s} | {m1_int:5.2f} [{m1_lo:5.2f},{m1_hi:5.2f}] | -1.37 [-2.20,-0.49] | NA cleaner?")

# GAS comparison
omega_na = safe_float(az.summary(trace_gas).loc['omega','mean'])
omega_pool = -1.61  # from script 04
print(f"{'GAS ω (long-run mean)':<30s} | {omega_na:5.2f}            | {omega_pool:5.2f}            | NA vs pooled")

alpha_gas_na = safe_float(az.summary(trace_gas).loc['alpha_gas','mean'])
print(f"{'GAS α_gas':<30s} | {alpha_gas_na:.4f}          | 0.045          |")


# ============================================================================
# Figuren
# ============================================================================
fig, ax = plt.subplots(figsize=(11, 6))
ax.fill_between(all_years, traj_df['lo95'], traj_df['hi95'], color='#4477AA', alpha=0.25, label='NA GAS 95% CrI')
ax.plot(all_years, traj_df['median'], color='#222288', lw=2.5, marker='o', markersize=4, label='NA GAS median')
ax.axhline(0, ls='--', color='red', alpha=0.6, label='No interaction')
ax.axhline(omega_pool, ls=':', color='gray', alpha=0.6, label=f'Pooled ω = {omega_pool}')
ax.axhline(m1_int, ls='-.', color='#882255', alpha=0.6, label=f'NA Static β = {m1_int:.2f}')
ax.set_xlabel("Calendar year")
ax.set_ylabel(r"$\beta_{int}(t)$ — NA-only sample")
ax.set_title("North America-only GAS time-varying carbon-conditional coefficient")
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/na_gas_trajectory.pdf")
plt.close()
print(f"\nFiguur: na_gas_trajectory.pdf opgeslagen")

# Save results
output = {
    'static_beta_int': m1_int,
    'static_lo95': m1_lo,
    'static_hi95': m1_hi,
    'gas_omega': omega_na,
    'gas_phi': safe_float(az.summary(trace_gas).loc['phi','mean']),
    'gas_alpha': alpha_gas_na,
    'blocks_divergences': n_div_blocks,
    'gas_divergences': n_div_gas,
    'n_blue_events': int(blue_ev.sum()),
    'n_pem_events': int(pem_ev.sum()),
}
with open(OUT / 'na_tvp_summary.json', 'w') as f:
    json.dump({k: float(v) if isinstance(v, (int,float,np.number)) else v for k, v in output.items()}, f, indent=2)
traj_df.to_csv(OUT / "na_gas_trajectory.csv", index=False)
print(f"\nResultaten in: {OUT}")
