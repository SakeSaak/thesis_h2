"""
05_robustness_loowaic.py

Comprehensive robustness analysis voor Chapter 7:
  A. Aggregeer alle data naar year × tech niveau (Binomial likelihood, comparable across modellen)
  B. Fit zes specificaties op dezelfde data:
       1. Static (no time-variation)
       2. 3-block TVP
       3. 4-block TVP (huidige)
       4. 5-block TVP
       5. GAS d=0 (no scaling)
       6. GAS d=1/2 (huidige)
       7. GAS d=1 (full info scaling)
  C. LOO/WAIC comparison via pointwise log-likelihood
  D. Sensitivity tabel
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import json

import numpy as np
import pandas as pd
import pymc as pm
import pytensor
import pytensor.tensor as pt
import arviz as az
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_robustness"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 2, 0.98
SEED = 20260518


def hdr(t):
    print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)


# ============================================================================
# A. AGGREGATE DATA
# ============================================================================
hdr("A. Aggregate data naar year × tech niveau")

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

# Combineer in (n_years * 2)-vorm voor likelihood: row 0..16 = blue, 17..33 = PEM
# Of: gewoon twee Binomial likelihoods toevoegen (cleaner)
print(f"  Years: {n_years}, Total events: blue={int(blue_ev.sum())}, PEM={int(pem_ev.sum())}")


# ============================================================================
# Helper: define block index voor n_blocks blocks
# ============================================================================
def make_block_index(years, n_blocks):
    """Verdeel jaren in n_blocks blocks op basis van economische regimes."""
    if n_blocks == 3:
        # Combineer pre-crisis + pandemic; behoud peak en post-peak
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
    else:
        raise ValueError(n_blocks)
    return np.array([f(y) for y in years], dtype=int)


# ============================================================================
# B. MODEL FITS
# ============================================================================
results = {}

# Common observation-equation likelihood gegeven β_int(t) vector (over jaren)
def build_likelihood(beta_int_t_vec, alpha_int, b_blue, b_eua, model):
    """Add Binomial likelihood terms voor blue en PEM gegeven β_int(t) vector."""
    eta_blue_full = alpha_int + b_blue + b_eua * z_arr + beta_int_t_vec * z_arr
    eta_pem_full = alpha_int + b_eua * z_arr
    p_blue = pt.sigmoid(eta_blue_full)
    p_pem = pt.sigmoid(eta_pem_full)
    pm.Binomial("blue_obs", n=blue_at, p=p_blue, observed=blue_ev)
    pm.Binomial("pem_obs", n=pem_at, p=p_pem, observed=pem_ev)


def fit_static():
    hdr("1. Static model (geen time-variation)")
    with pm.Model() as m:
        alpha_int = pm.Normal("alpha_int", -4.0, 1.0)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        b_int = pm.Normal("beta_int", 0, 2)
        beta_int_vec = pt.fill(pt.zeros(n_years), b_int) + pt.zeros(n_years)
        # Equivalent: gewoon scalar gebruiken
        eta_blue_full = alpha_int + b_blue + b_eua * z_arr + b_int * z_arr
        eta_pem_full = alpha_int + b_eua * z_arr
        pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue_full), observed=blue_ev)
        pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem_full), observed=pem_ev)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS, target_accept=TARGET_ACCEPT,
                          random_seed=SEED, progressbar=False, return_inferencedata=True,
                          idata_kwargs={"log_likelihood": True})
    return trace


def fit_blocks(n_blocks):
    hdr(f"2. Parameter-driven TVP — {n_blocks}-block")
    block_idx = make_block_index(all_years, n_blocks)
    with pm.Model() as m:
        alpha_int = pm.Normal("alpha_int", -4.0, 1.0)
        b_blue = pm.Normal("beta_blue", 0, 2)
        b_eua = pm.Normal("beta_eua", 0, 2)
        sigma_int = pm.HalfNormal("sigma_int", 0.5)
        init_dist = pm.Normal.dist(-1.0, 2.0)
        beta_int_b = pm.GaussianRandomWalk("beta_int_b", sigma=sigma_int, init_dist=init_dist, shape=n_blocks)
        beta_int_vec = beta_int_b[block_idx]
        eta_blue_full = alpha_int + b_blue + b_eua * z_arr + beta_int_vec * z_arr
        eta_pem_full = alpha_int + b_eua * z_arr
        pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue_full), observed=blue_ev)
        pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem_full), observed=pem_ev)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS, target_accept=TARGET_ACCEPT,
                          random_seed=SEED, progressbar=False, return_inferencedata=True,
                          idata_kwargs={"log_likelihood": True})
    return trace


def fit_gas(d_scaling):
    """GAS-(1,1) met scaling d ∈ {0, 0.5, 1}"""
    hdr(f"3. GAS observation-driven TVP — scaling d={d_scaling}")
    z_t = pt.as_tensor_variable(z_arr)
    b_at_t = pt.as_tensor_variable(blue_at)
    b_ev_t = pt.as_tensor_variable(blue_ev)
    p_at_t = pt.as_tensor_variable(pem_at)
    p_ev_t = pt.as_tensor_variable(pem_ev)

    with pm.Model() as m:
        omega = pm.Normal("omega", -1.0, 1.0)
        phi = pm.Beta("phi", 8, 2)
        alpha_gas = pm.HalfNormal("alpha_gas", 0.5)
        beta_int_init = pm.Normal("beta_int_init", -1.0, 1.5)
        alpha_int = pm.Normal("alpha_int", -4.0, 1.0)
        beta_blue = pm.Normal("beta_blue", 0, 2)
        beta_eua = pm.Normal("beta_eua", 0, 2)

        def step(z, b_at_, b_ev_, p_at_, p_ev_, b_prev,
                 om, ph, al, a_i, b_b, b_e, d_):
            eta_blue = a_i + b_b + b_e * z + b_prev * z
            p_blue = pt.sigmoid(eta_blue)
            score = (b_ev_ - b_at_ * p_blue) * z
            info = b_at_ * p_blue * (1.0 - p_blue) * (z * z) + 0.1
            # Scaling: I_t^(-d)
            if d_ == 0:
                scaled = score
            elif d_ == 1:
                scaled = score / info
            else:  # d=1/2
                scaled = score / pt.sqrt(info)
            b_new = om * (1.0 - ph) + ph * b_prev + al * scaled
            return b_new

        beta_int_seq, _ = pytensor.scan(
            fn=step,
            sequences=[z_t, b_at_t, b_ev_t, p_at_t, p_ev_t],
            outputs_info=[beta_int_init],
            non_sequences=[omega, phi, alpha_gas, alpha_int, beta_blue, beta_eua,
                           pt.constant(float(d_scaling))],
        )
        beta_int_traj = pt.concatenate([pt.stack([beta_int_init]), beta_int_seq[:-1]])
        pm.Deterministic("beta_int_traj", beta_int_traj)

        eta_blue_full = alpha_int + beta_blue + beta_eua * z_t + beta_int_traj * z_t
        eta_pem_full = alpha_int + beta_eua * z_t
        pm.Binomial("blue_obs", n=blue_at, p=pt.sigmoid(eta_blue_full), observed=blue_ev)
        pm.Binomial("pem_obs", n=pem_at, p=pt.sigmoid(eta_pem_full), observed=pem_ev)
        trace = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS, target_accept=TARGET_ACCEPT,
                          random_seed=SEED, progressbar=False, return_inferencedata=True,
                          idata_kwargs={"log_likelihood": True})
    return trace


# Run alle modellen
print("\nRunning 7 model variants. Verwachte runtime: 2-5 min totaal\n")
results['M1_static'] = fit_static()
results['M2_3block'] = fit_blocks(3)
results['M3_4block'] = fit_blocks(4)
results['M4_5block'] = fit_blocks(5)
results['M5_GAS_d0'] = fit_gas(0.0)
results['M6_GAS_d05'] = fit_gas(0.5)
results['M7_GAS_d1'] = fit_gas(1.0)


# ============================================================================
# C. LOO / WAIC COMPARISON
# ============================================================================
hdr("C. LOO/WAIC model comparison")

compare_dict = {name: trace for name, trace in results.items()}
try:
    # ArviZ 1.x stijl
    comparison = az.compare(compare_dict, var_name='blue_obs')
except TypeError:
    try:
        # Iets oudere ArviZ
        comparison = az.compare(compare_dict, var_name='blue_obs', method='stacking')
    except Exception:
        # Fall-through, simplest call
        comparison = az.compare(compare_dict)
print("\nLOO comparison (higher elpd_loo = better predictive density):")
print(comparison.round(2).to_string())
comparison.to_csv(OUT / "loo_comparison.csv")

# WAIC variant
waic_results = {}
def _safe_waic(trace, vn):
    for kwargs in [{'var_name': vn}, {}]:
        try:
            return az.waic(trace, **kwargs)
        except Exception:
            pass
    return None

def _safe_loo(trace, vn):
    for kwargs in [{'var_name': vn}, {}]:
        try:
            return az.loo(trace, **kwargs)
        except Exception:
            pass
    return None

for name, trace in results.items():
    rec = {}
    w = _safe_waic(trace, 'blue_obs')
    if w is not None:
        elpd = getattr(w, 'elpd_waic', None) or getattr(w, 'elpd', None)
        rec['waic'] = float(elpd) if elpd is not None else None
        rec['se'] = float(getattr(w, 'se', np.nan))
        p_waic = getattr(w, 'p_waic', None) or getattr(w, 'p', None)
        rec['p_waic'] = float(p_waic) if p_waic is not None else None
    l = _safe_loo(trace, 'blue_obs')
    if l is not None:
        elpd_loo = getattr(l, 'elpd_loo', None) or getattr(l, 'elpd', None)
        rec['loo'] = float(elpd_loo) if elpd_loo is not None else None
        rec['loo_se'] = float(getattr(l, 'se', np.nan))
        p_loo = getattr(l, 'p_loo', None) or getattr(l, 'p', None)
        rec['p_loo'] = float(p_loo) if p_loo is not None else None
    waic_results[name] = rec
print("\nLOO en WAIC per model:")
for name, w in waic_results.items():
    parts = [name]
    if w.get('loo') is not None:
        parts.append(f"elpd_loo={w['loo']:.2f}±{w['loo_se']:.2f} (p_loo={w['p_loo']:.2f})")
    if w.get('waic') is not None:
        parts.append(f"elpd_waic={w['waic']:.2f}±{w['se']:.2f} (p_waic={w['p_waic']:.2f})")
    if 'loo_error' in w or 'waic_error' in w:
        parts.append(f"errors: {w.get('loo_error','')} {w.get('waic_error','')}")
    print("  " + " | ".join(parts))

with open(OUT / "waic_results.json", 'w') as f:
    json.dump({k: {kk: float(vv) if not isinstance(vv, str) else vv for kk, vv in v.items()}
               for k, v in waic_results.items()}, f, indent=2)


# ============================================================================
# D. PARAMETER COMPARISON TABLE
# ============================================================================
hdr("D. Parameter comparison across modellen")

def _f(x):
    """Safe float conversion handling stringified ArviZ outputs."""
    if isinstance(x, (int, float, np.number)):
        return float(x)
    try:
        return float(str(x).split("±")[0].strip())
    except Exception:
        return float("nan")

def _hdi_cols(s):
    """Find HDI columns - kan hdi_3% / hdi_97% zijn of eti3_lb / eti3_ub etc."""
    cols = list(s.columns)
    lo_cands = [c for c in cols if "lb" in c.lower() or c.startswith("hdi_3") or c.startswith("hdi_2")]
    hi_cands = [c for c in cols if "ub" in c.lower() or c.startswith("hdi_97") or c.startswith("hdi_94")]
    return (lo_cands[0] if lo_cands else "mean"), (hi_cands[0] if hi_cands else "mean")

param_table = []
# Static
s = az.summary(results['M1_static'], var_names=['beta_int'])
lo_c, hi_c = _hdi_cols(s)
param_table.append({'model': 'M1 Static',
                    'beta_int_summary': f"{_f(s.loc['beta_int','mean']):.2f} [{_f(s.loc['beta_int',lo_c]):.2f}, {_f(s.loc['beta_int',hi_c]):.2f}]"})

# Blocks
for nb, name in [(3, 'M2_3block'), (4, 'M3_4block'), (5, 'M4_5block')]:
    s = az.summary(results[name], var_names=['beta_int_b'])
    lo_c, hi_c = _hdi_cols(s)
    summary = "; ".join([f"b{i}: {_f(s.iloc[i]['mean']):.2f} [{_f(s.iloc[i][lo_c]):.2f}, {_f(s.iloc[i][hi_c]):.2f}]" 
                          for i in range(nb)])
    param_table.append({'model': f'M{nb-1}+1 {nb}-block', 'beta_int_summary': summary})

# GAS variants
for d_lab, name in [('d=0', 'M5_GAS_d0'), ('d=1/2', 'M6_GAS_d05'), ('d=1', 'M7_GAS_d1')]:
    s = az.summary(results[name], var_names=['omega', 'phi', 'alpha_gas'])
    lo_c, hi_c = _hdi_cols(s)
    summary = (f"ω={_f(s.loc['omega','mean']):.2f} [{_f(s.loc['omega',lo_c]):.2f}, {_f(s.loc['omega',hi_c]):.2f}], "
               f"φ={_f(s.loc['phi','mean']):.2f}, α={_f(s.loc['alpha_gas','mean']):.3f}")
    param_table.append({'model': f'GAS {d_lab}', 'beta_int_summary': summary})

param_df = pd.DataFrame(param_table)
print(param_df.to_string(index=False))
param_df.to_csv(OUT / "param_comparison.csv", index=False)


# ============================================================================
# E. ROBUSTNESS PLOT: GAS trajectories voor d=0, 1/2, 1
# ============================================================================
hdr("E. GAS trajectories vergelijking")
fig, ax = plt.subplots(figsize=(11, 6))
colors = {'M5_GAS_d0': '#117733', 'M6_GAS_d05': '#222288', 'M7_GAS_d1': '#882255'}
labels = {'M5_GAS_d0': 'GAS d=0 (no scaling)', 'M6_GAS_d05': 'GAS d=1/2 (sqrt info)', 'M7_GAS_d1': 'GAS d=1 (full info)'}
for name in ['M5_GAS_d0', 'M6_GAS_d05', 'M7_GAS_d1']:
    traj = results[name].posterior['beta_int_traj'].values.reshape(-1, n_years)
    med = np.median(traj, axis=0)
    lo = np.quantile(traj, 0.025, axis=0)
    hi = np.quantile(traj, 0.975, axis=0)
    ax.fill_between(all_years, lo, hi, color=colors[name], alpha=0.10)
    ax.plot(all_years, med, color=colors[name], lw=2, marker='o', markersize=3, label=labels[name])
ax.axhline(0, ls='--', color='red', alpha=0.6)
ax.axhline(-1.43, ls=':', color='gray', alpha=0.6, label='Static Spoor B-2 ref')
ax.set_xlabel("Calendar year")
ax.set_ylabel(r"$\beta_{int}(t)$")
ax.set_title("GAS robustness: trajectory voor d ∈ {0, 1/2, 1}")
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/gas_scaling_robustness.pdf")
plt.close(fig)

print(f"\nAlle robustness outputs in: {OUT}")
