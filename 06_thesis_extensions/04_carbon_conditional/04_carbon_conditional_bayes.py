"""
04_carbon_conditional_bayes.py

Spoor B-2: Bayesian carbon-conditional hazard model met PyMC.
Sensitivity grid op de Blue×EUA interaction coefficient.

Replicatie van Spoor B-1 maar met:
  - Bernoulli likelihood (logit) - identiek aan v7's GLM
  - 4 prior specificaties op de interaction term (blue_x_eua)
  - Marginal HR met credible intervals bij z=-1, 0, +1

Outputs:
  - 04_bayes_posterior_summary.csv : alle priors x coefficienten
  - 04_bayes_marginal_HR.csv       : marginal HR per prior x z
  - figures/posterior_interaction.pdf : posterior densities blue_x_eua
  - figures/marginal_HR_curves.pdf    : 4 marginal HR curves overlapped

Auteur: Sake Saakstra
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
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/04_carbon_conditional/results_bayes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "figures").mkdir(exist_ok=True)

RUN_MODE = "quick"   # "quick" of "full"
if RUN_MODE == "quick":
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1000, 1000, 2, 0.90
else:
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 2000, 2000, 4, 0.95
RANDOM_SEED = 20260518

# ============================================================================
# PRIOR SPECIFICATIES (focus op interaction term)
# ============================================================================
# v7 frequentist gaf interactie = -2.28. Onze priors variëren in informativiteit:
PRIOR_SPECS = {
    "vague": {
        "blue": dict(mu=0.0, sigma=5.0),
        "eua":  dict(mu=0.0, sigma=5.0),
        "int":  dict(mu=0.0, sigma=5.0),  # echt niet-informatief
        "default": dict(mu=0.0, sigma=2.0),
    },
    "weakly_informative": {
        "blue": dict(mu=0.0, sigma=2.0),
        "eua":  dict(mu=0.0, sigma=2.0),
        "int":  dict(mu=0.0, sigma=2.0),  # zwak informatief
        "default": dict(mu=0.0, sigma=1.5),
    },
    "skeptical": {
        "blue": dict(mu=0.0, sigma=1.5),
        "eua":  dict(mu=0.0, sigma=1.5),
        "int":  dict(mu=0.0, sigma=1.0),  # skeptisch over interactie
        "default": dict(mu=0.0, sigma=1.5),
    },
    "informative_v7": {
        "blue": dict(mu=0.0, sigma=2.0),
        "eua":  dict(mu=0.0, sigma=2.0),
        "int":  dict(mu=-2.5, sigma=0.5),  # gecentreerd op v7 finding
        "default": dict(mu=0.0, sigma=1.5),
    },
}


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# DATA LADEN + PANEL OPBOUW (identiek aan Spoor B-1)
# ============================================================================
header("Data + person-year panel")

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
            'region': row['region'],
            'sponsor_type': row['sponsor_type'],
        })
panel = pd.DataFrame(panel_rows)
print(f"  Panel: {len(panel)} rijen, events = {panel['event_any_yr'].sum()}")

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
print(f"  EUA: mean=€{eua_mean:.1f}, sd=€{eua_sd:.1f}")


# ============================================================================
# DESIGN MATRIX
# ============================================================================
X_blue = panel['is_blue_ccs'].values.astype(float)
X_eua = panel['mkt_eua_z'].values.astype(float)
X_year = panel['year_since_start'].values.astype(float)
X_year2 = (X_year ** 2)
X_capacity = panel['log_capacity_mw'].values.astype(float)

region_dum = pd.get_dummies(panel['region'], prefix='region', drop_first=True).astype(float)
sponsor_dum = pd.get_dummies(panel['sponsor_type'], prefix='sponsor', drop_first=True).astype(float)
X_region = region_dum.values
X_sponsor = sponsor_dum.values
n_region = X_region.shape[1]
n_sponsor = X_sponsor.shape[1]
events_obs = panel['event_any_yr'].values.astype(int)
print(f"  Design: {n_region} region dum, {n_sponsor} sponsor dum")


# ============================================================================
# FIT FUNCTIE
# ============================================================================
def fit_bayes_logit(spec_name, spec):
    """
    Minimal carbon-conditional model. Sponsor + region weggelaten:
    sponsor_type heeft perfect separation (sommige categorieen 0 events),
    en met 43 events kunnen we niet beide modelleren plus de interactie.
    """
    print(f"\n--- Prior: {spec_name} ---")
    with pm.Model():
        alpha = pm.Normal("alpha", mu=-4.5, sigma=1.5)
        beta_blue = pm.Normal("beta_blue", mu=spec['blue']['mu'], sigma=spec['blue']['sigma'])
        beta_eua = pm.Normal("beta_eua", mu=spec['eua']['mu'], sigma=spec['eua']['sigma'])
        beta_int = pm.Normal("beta_int", mu=spec['int']['mu'], sigma=spec['int']['sigma'])
        beta_year = pm.Normal("beta_year", mu=0.0, sigma=spec['default']['sigma'])
        beta_cap = pm.Normal("beta_cap", mu=0.0, sigma=spec['default']['sigma'])
        
        eta = (alpha
               + beta_blue * X_blue
               + beta_eua * X_eua
               + beta_int * X_blue * X_eua
               + beta_year * X_year
               + beta_cap * X_capacity)
        
        pm.Bernoulli("events", logit_p=eta, observed=events_obs)
        
        trace = pm.sample(
            draws=N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
            target_accept=TARGET_ACCEPT, random_seed=RANDOM_SEED,
            progressbar=False, return_inferencedata=True,
        )
    
    s = az.summary(trace, var_names=["beta_blue", "beta_eua", "beta_int"])
    print(s.round(3).to_string())
    return trace


# ============================================================================
# RUN ALLE PRIORS
# ============================================================================
header("Fitting 4 Bayesian models")
traces = {}
for spec_name, spec in PRIOR_SPECS.items():
    traces[spec_name] = fit_bayes_logit(spec_name, spec)


# ============================================================================
# SAMENVATTINGSTABEL
# ============================================================================
header("Posterior summary across priors")
rows = []
for spec_name, trace in traces.items():
    for var in ["beta_blue", "beta_eua", "beta_int"]:
        draws = trace.posterior[var].values.flatten()
        rh = float(az.summary(trace, var_names=[var])["r_hat"].iloc[0])
        ess = float(az.summary(trace, var_names=[var])["ess_bulk"].iloc[0])
        rows.append({
            'prior': spec_name,
            'coef': var,
            'mean': float(draws.mean()),
            'median': float(np.median(draws)),
            'sd': float(draws.std()),
            'ci_lo': float(np.quantile(draws, 0.025)),
            'ci_hi': float(np.quantile(draws, 0.975)),
            'rhat': rh,
            'ess': ess,
        })
summary_df = pd.DataFrame(rows)
print(summary_df.round(3).to_string(index=False))
summary_df.to_csv(OUTPUT_DIR / "04_bayes_posterior_summary.csv", index=False)
print(f"\nOpgeslagen: 04_bayes_posterior_summary.csv")


# ============================================================================
# MARGINAL HR PER PRIOR PER Z
# ============================================================================
header("Marginal HR(Blue|z) per prior")
z_grid = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5])

marg_rows = []
for spec_name, trace in traces.items():
    bb = trace.posterior["beta_blue"].values.flatten()
    bi = trace.posterior["beta_int"].values.flatten()
    for z in z_grid:
        log_hr_draws = bb + bi * z
        hr_draws = np.exp(log_hr_draws)
        marg_rows.append({
            'prior': spec_name,
            'z': z,
            'eua_eur_tco2': eua_mean + z * eua_sd,
            'HR_median': float(np.median(hr_draws)),
            'HR_lo': float(np.quantile(hr_draws, 0.025)),
            'HR_hi': float(np.quantile(hr_draws, 0.975)),
        })
marg_df = pd.DataFrame(marg_rows)
print("\nMarginal HR (median) by prior x z:")
pivot = marg_df.pivot(index='prior', columns='z', values='HR_median').round(2)
print(pivot.to_string())
marg_df.to_csv(OUTPUT_DIR / "04_bayes_marginal_HR.csv", index=False)


# ============================================================================
# FIGUUR 1: posterior densities van beta_int per prior
# ============================================================================
header("Figures")
colors = {'vague':'#4477AA', 'weakly_informative':'#EE6677',
          'skeptical':'#228833', 'informative_v7':'#CCBB44'}

fig, ax = plt.subplots(figsize=(10, 5.5))
for spec_name, trace in traces.items():
    draws = trace.posterior["beta_int"].values.flatten()
    ax.hist(draws, bins=60, density=True, alpha=0.45,
            color=colors[spec_name], label=spec_name)
ax.axvline(-2.28, linestyle='--', color='black', lw=1.5,
           label='Frequentist MLE (β_int = -2.28)')
ax.axvline(0, linestyle=':', color='red', alpha=0.5, label='No interaction')
ax.set_xlabel("β (Blue × EUA_z): interaction coefficient")
ax.set_ylabel("Posterior density")
ax.set_title("Posterior of carbon-conditional interaction coefficient across priors")
ax.legend(loc='upper left')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/posterior_interaction.pdf")
plt.close(fig)
print("  posterior_interaction.pdf")


# ============================================================================
# FIGUUR 2: marginal HR curves overlay
# ============================================================================
z_fine = np.linspace(-1.5, 1.5, 50)
fig, ax = plt.subplots(figsize=(10, 6))
for spec_name, trace in traces.items():
    bb = trace.posterior["beta_blue"].values.flatten()
    bi = trace.posterior["beta_int"].values.flatten()
    hr_medians = []
    hr_los = []
    hr_his = []
    for z in z_fine:
        hr_draws = np.exp(bb + bi * z)
        hr_medians.append(np.median(hr_draws))
        hr_los.append(np.quantile(hr_draws, 0.025))
        hr_his.append(np.quantile(hr_draws, 0.975))
    ax.plot(z_fine, hr_medians, color=colors[spec_name], lw=2, label=spec_name)
    ax.fill_between(z_fine, hr_los, hr_his, color=colors[spec_name], alpha=0.12)

ax.axhline(1, linestyle='--', color='red', alpha=0.7, label='HR = 1')
ax.set_yscale('log')
ax.set_xlabel("EUA carbon price (z-score)")
ax.set_ylabel("Marginal Blue_CCS HR (log scale)")
ax.set_title("Bayesian marginal HR: Blue_CCS vs PEM conditional on EUA, across priors")
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
xticks = np.linspace(-1.5, 1.5, 7)
ax2.set_xticks(xticks)
ax2.set_xticklabels([f"€{eua_mean + z*eua_sd:.0f}" for z in xticks])
ax2.set_xlabel("EUA price (€/tCO₂)")
ax.legend(loc='upper right')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/marginal_HR_curves.pdf")
plt.close(fig)
print("  marginal_HR_curves.pdf")


# ============================================================================
# AFRONDEN
# ============================================================================
header("KLAAR (Spoor B-2: Bayesian)")
print(f"Mode: {RUN_MODE}")
print(f"Resultaten in: {OUTPUT_DIR}")
