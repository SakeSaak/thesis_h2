"""
01_tvp_hazard_pilot.py

METHODOLOGISCHE PILOT: Non-Gaussian state-space hazard model met
time-varying parameters (TVP). Hoofdbijdrage van de thesis.

Model (Koopman 2000 JRSSB, Koopman 2016 REStat framework):

  Observation equation (Bernoulli):
    logit(h_it) = α + β_blue(t)·blue_i + β_eua(t)·eua_t 
                + β_int(t)·blue_i·eua_t + β_year·year_since_start_i
                + β_cap·log_capacity_i

  State equation (Gaussian random walks):
    β_blue(t+1) = β_blue(t) + η_blue,t,   η_blue ~ N(0, σ²_blue)
    β_eua(t+1)  = β_eua(t)  + η_eua,t,    η_eua  ~ N(0, σ²_eua)
    β_int(t+1)  = β_int(t)  + η_int,t,    η_int  ~ N(0, σ²_int)

  σ-hyperpriors: Half-Normal(0.5) — empirical Bayes regularization

De hoofdfinding: posterior trajectory van β_int(t) — heeft de carbon-conditional
sensitiviteit zich versterkt of verzwakt over 2010-2026?

Vergelijking:
  - Static logit (baseline, β's constant)
  - Time-varying Bayesian (deze pilot)
  - Information criteria via LOO

Outputs:
  - results/posterior_states.csv  : β_blue(t), β_eua(t), β_int(t) trajectories
  - results/tvp_diagnostics.txt   : Rhat, ESS, divergences
  - figures/beta_int_trajectory.pdf : main figure — Hoofdbijdrage
  - figures/all_states.pdf : alle drie de TVP trajectoriën
  - figures/marginal_HR_by_year.pdf : implied HR over tijd

Auteur: Sake Saakstra
Methodologische pilot — Koopman-supervised thesis chapter 6
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymc as pm
import pytensor.tensor as pt
import arviz as az

# ============================================================================
# CONFIG
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "figures").mkdir(exist_ok=True)

RUN_MODE = "quick"  # "quick" of "full"
if RUN_MODE == "quick":
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1000, 1500, 2, 0.98
else:
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 3000, 3000, 4, 0.98
RANDOM_SEED = 20260518


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# DATA LADEN EN PERSON-YEAR PANEL
# ============================================================================
header("Data + person-year panel met year-index voor TVP")

df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)
df['project_id'] = df.index

panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
        })
panel = pd.DataFrame(panel_rows)

# Merge EUA
mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
yearly_eua.columns = ['year_calendar', 'mkt_eua']
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['mkt_eua'].fillna(panel['mkt_eua'].median())

eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['mkt_eua_z'] = (panel['mkt_eua'] - eua_mean) / eua_sd

# CRUCIAAL: year index voor TVP indexing in PyMC
# Beperk tot 2010-2026: pre-2010 heeft te weinig observaties voor TVP
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()
years_sorted = sorted(panel['year_calendar'].unique())
year_to_idx = {y: i for i, y in enumerate(years_sorted)}
panel['year_idx'] = panel['year_calendar'].map(year_to_idx).astype(int)
n_years = len(years_sorted)
print(f"  Restricted to 2010-2026: {len(panel)} rows, {n_years} years")

print(f"  Panel: {len(panel)} rijen, events = {panel['event_any_yr'].sum()}")
print(f"  Jaren: {n_years} (van {years_sorted[0]} tot {years_sorted[-1]})")
print(f"  EUA z-range: [{panel['mkt_eua_z'].min():.2f}, {panel['mkt_eua_z'].max():.2f}]")

# Events per year
ev_per_year = panel.groupby('year_calendar')['event_any_yr'].sum()
print(f"  Events per year:")
for y, n in ev_per_year.items():
    if n > 0:
        print(f"    {y}: {n} events")


# ============================================================================
# DESIGN ARRAYS
# ============================================================================
X_blue = panel['is_blue_ccs'].values.astype(float)
X_eua = panel['mkt_eua_z'].values.astype(float)
X_year_since = panel['year_since_start'].values.astype(float)
X_capacity = panel['log_capacity_mw'].values.astype(float)
year_idx = panel['year_idx'].values.astype(int)
events_obs = panel['event_any_yr'].values.astype(int)


# ============================================================================
# STATE-SPACE TVP HAZARD MODEL
# ============================================================================
header(f"Fitting non-Gaussian state-space TVP hazard model")
print(f"  Mode: {RUN_MODE}  ({N_CHAINS} chains x {N_DRAWS} draws)")
print(f"  States: β_blue(t), β_eua(t), β_int(t)  over {n_years} years")

with pm.Model() as ssm:
    # === Hyperpriors voor state innovation variances ===
    # Half-Normal: regularisering naar smooth trajectories
    sigma_blue = pm.HalfNormal("sigma_blue", sigma=0.3)
    sigma_eua = pm.HalfNormal("sigma_eua", sigma=0.3)
    sigma_int = pm.HalfNormal("sigma_int", sigma=0.3)
    
    # === Initial state priors (weakly informative) ===
    init_dist = pm.Normal.dist(mu=0, sigma=2)
    
    # === STATE EQUATIONS: Gaussian random walks ===
    beta_blue_t = pm.GaussianRandomWalk(
        "beta_blue_t", sigma=sigma_blue, init_dist=init_dist, shape=n_years
    )
    beta_eua_t = pm.GaussianRandomWalk(
        "beta_eua_t", sigma=sigma_eua, init_dist=init_dist, shape=n_years
    )
    beta_int_t = pm.GaussianRandomWalk(
        "beta_int_t", sigma=sigma_int, init_dist=init_dist, shape=n_years
    )
    
    # === Static control coefficients ===
    alpha = pm.Normal("alpha", mu=-4.5, sigma=1.5)
    beta_year_since = pm.Normal("beta_year_since", mu=0, sigma=1.5)
    beta_cap = pm.Normal("beta_cap", mu=0, sigma=1.5)
    
    # === OBSERVATION EQUATION: Bernoulli with logit link ===
    # Per person-year, look up β at that calendar year via year_idx
    eta = (alpha
           + beta_blue_t[year_idx] * X_blue
           + beta_eua_t[year_idx] * X_eua
           + beta_int_t[year_idx] * X_blue * X_eua
           + beta_year_since * X_year_since
           + beta_cap * X_capacity)
    
    pm.Bernoulli("events", logit_p=eta, observed=events_obs)
    
    # Sample
    trace = pm.sample(
        draws=N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
        target_accept=TARGET_ACCEPT, max_treedepth=12,
        random_seed=RANDOM_SEED,
        progressbar=False, return_inferencedata=True,
    )


# ============================================================================
# DIAGNOSTIEK
# ============================================================================
header("MCMC Diagnostics")
diag_vars = ["sigma_blue", "sigma_eua", "sigma_int", "alpha", 
             "beta_year_since", "beta_cap"]
diag = az.summary(trace, var_names=diag_vars)
print(diag.round(3).to_string())

print("\nState-space coefficient summaries (selected years):")
state_summary = az.summary(trace, var_names=["beta_blue_t", "beta_eua_t", "beta_int_t"])
key_years = [years_sorted[0], 2015, 2020, 2024, years_sorted[-1]]
print(f"  Year_calendar -> state index mapping:")
for y in key_years:
    if y in year_to_idx:
        i = year_to_idx[y]
        print(f"    {y} -> idx={i}")
        for var in ["beta_blue_t", "beta_eua_t", "beta_int_t"]:
            key = f"{var}[{i}]"
            if key in state_summary.index:
                row = state_summary.loc[key]
                try:
                    m = float(row['mean']); lo = float(row['hdi_3%']); hi = float(row['hdi_97%'])
                    rh = float(row['r_hat']); ess = int(float(row['ess_bulk']))
                    print(f"      {var}({y}) = {m:.3f} [{lo:.3f}, {hi:.3f}]  Rhat={rh:.3f}  ESS={ess}")
                except (ValueError, TypeError):
                    print(f"      {var}({y}) = {row['mean']} [...]")

max_rhat = state_summary['r_hat'].max()
min_ess = state_summary['ess_bulk'].min()
n_div = sum(trace.sample_stats.diverging.values.flatten())
print(f"\n  Overall: max Rhat={max_rhat:.3f}, min ESS={int(min_ess)}, divergences={n_div}")

# Save diagnostics
with open(OUTPUT_DIR / "tvp_diagnostics.txt", 'w') as f:
    f.write(f"State-space TVP hazard model diagnostics\n")
    f.write(f"Mode: {RUN_MODE}\n")
    f.write(f"Max Rhat: {max_rhat:.4f}\n")
    f.write(f"Min ESS: {int(min_ess)}\n")
    f.write(f"Divergences: {n_div}\n\n")
    f.write("Hyperparameters:\n")
    f.write(diag.to_string())
    f.write("\n\nState trajectories (per year):\n")
    f.write(state_summary.to_string())


# ============================================================================
# EXTRACT POSTERIOR TRAJECTORIES
# ============================================================================
header("Extracting posterior state trajectories")
state_rows = []
for var in ["beta_blue_t", "beta_eua_t", "beta_int_t"]:
    draws = trace.posterior[var].values  # (chains, draws, n_years)
    flat = draws.reshape(-1, n_years)
    for i, y in enumerate(years_sorted):
        d = flat[:, i]
        state_rows.append({
            'state': var,
            'year': y,
            'median': float(np.median(d)),
            'mean': float(d.mean()),
            'sd': float(d.std()),
            'lo_95': float(np.quantile(d, 0.025)),
            'hi_95': float(np.quantile(d, 0.975)),
            'lo_80': float(np.quantile(d, 0.10)),
            'hi_80': float(np.quantile(d, 0.90)),
        })

states_df = pd.DataFrame(state_rows)
states_df.to_csv(OUTPUT_DIR / "posterior_states.csv", index=False)
print(f"  Opgeslagen: posterior_states.csv ({len(states_df)} rows)")


# ============================================================================
# HOOFDFIGUUR: β_int(t) over tijd — DE ZWAARTEPUNT VAN HET HOOFDSTUK
# ============================================================================
header("Hoofdfiguur: β_int(t) trajectory")

int_df = states_df[states_df['state']=='beta_int_t'].sort_values('year')

fig, ax = plt.subplots(figsize=(11, 6))
ax.fill_between(int_df['year'], int_df['lo_95'], int_df['hi_95'],
                color='#4477AA', alpha=0.20, label='95% credible band')
ax.fill_between(int_df['year'], int_df['lo_80'], int_df['hi_80'],
                color='#4477AA', alpha=0.35, label='80% credible band')
ax.plot(int_df['year'], int_df['median'], color='#222288', lw=2.5,
        marker='o', markersize=4, label='Posterior median')
ax.axhline(0, linestyle='--', color='red', alpha=0.7, label='No interaction (β_int = 0)')

# Reference: static estimate from Spoor B-2
ax.axhline(-1.43, linestyle=':', color='gray', alpha=0.7,
           label='Static estimate (Bayesian WI, Spoor B-2)')

ax.set_xlabel("Calendar year")
ax.set_ylabel(r"$\beta_{int}(t)$: time-varying carbon-conditional coefficient")
ax.set_title("Time-varying Blue × EUA interaction: posterior trajectory 2010–2026")
ax.legend(loc='upper right')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/beta_int_trajectory.pdf")
plt.close(fig)
print(f"  Opgeslagen: figures/beta_int_trajectory.pdf")


# ============================================================================
# OVERZICHTSFIGUUR: alle 3 trajectoriën
# ============================================================================
fig, axes = plt.subplots(3, 1, figsize=(11, 11), sharex=True)
for ax, var, title, color in [
    (axes[0], 'beta_blue_t', r"$\beta_{blue}(t)$: time-varying Blue main effect", '#228833'),
    (axes[1], 'beta_eua_t',  r"$\beta_{EUA}(t)$: time-varying EUA main effect",   '#EE6677'),
    (axes[2], 'beta_int_t',  r"$\beta_{int}(t)$: time-varying Blue×EUA interaction", '#4477AA'),
]:
    d = states_df[states_df['state']==var].sort_values('year')
    ax.fill_between(d['year'], d['lo_95'], d['hi_95'], color=color, alpha=0.20)
    ax.fill_between(d['year'], d['lo_80'], d['hi_80'], color=color, alpha=0.35)
    ax.plot(d['year'], d['median'], color=color, lw=2.5, marker='o', markersize=3)
    ax.axhline(0, linestyle='--', color='black', alpha=0.4)
    ax.set_title(title)
    ax.set_ylabel("Coefficient value")
    ax.grid(alpha=0.3)
axes[2].set_xlabel("Calendar year")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/all_states.pdf")
plt.close(fig)
print(f"  Opgeslagen: figures/all_states.pdf")


# ============================================================================
# IMPLIED MARGINAL HR(blue | z=0) PER YEAR
# ============================================================================
header("Implied marginal Blue HR by year (at mean EUA, z=0)")
blue_df = states_df[states_df['state']=='beta_blue_t'].sort_values('year').reset_index()
fig, ax = plt.subplots(figsize=(11, 6))
hr_med = np.exp(blue_df['median'])
hr_lo = np.exp(blue_df['lo_95'])
hr_hi = np.exp(blue_df['hi_95'])
ax.fill_between(blue_df['year'], hr_lo, hr_hi, color='#882255', alpha=0.20, label='95% CrI')
ax.plot(blue_df['year'], hr_med, color='#882255', lw=2.5, marker='o', markersize=4, label='Posterior median')
ax.axhline(1, linestyle='--', color='red', alpha=0.7, label='HR = 1')
ax.set_yscale('log')
ax.set_xlabel("Calendar year")
ax.set_ylabel("Implied Blue_CCS HR at mean EUA (log scale)")
ax.set_title("Time-varying marginal hazard ratio: Blue_CCS vs PEM at mean EUA price")
ax.legend(loc='upper right')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/marginal_HR_by_year.pdf")
plt.close(fig)
print(f"  Opgeslagen: figures/marginal_HR_by_year.pdf")


# ============================================================================
# SAMENVATTING - intetessantste observaties
# ============================================================================
header("KEY FINDINGS")
print("Posterior median of β_int(t) by key year:")
for y in [years_sorted[0], 2014, 2018, 2021, 2024, years_sorted[-1]]:
    if y in year_to_idx:
        row = states_df[(states_df['state']=='beta_int_t') & (states_df['year']==y)].iloc[0]
        sig = "✓" if (row['hi_95'] < 0 or row['lo_95'] > 0) else " "
        print(f"  {y}: {row['median']:7.3f}  [{row['lo_95']:7.3f}, {row['hi_95']:7.3f}]  {sig}")

print(f"\nHyperparameter sigma_int (innovation SD): {trace.posterior['sigma_int'].mean().values:.3f}")
print(f"  Low value → smooth trajectory")
print(f"  High value → quickly-changing β_int(t)")

print(f"\nResultaten in: {OUTPUT_DIR}")
