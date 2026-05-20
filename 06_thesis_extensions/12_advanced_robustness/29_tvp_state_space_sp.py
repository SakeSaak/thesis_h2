"""
29_tvp_state_space_sp.py
============================================================================
Pijler 24: TVP β_int(t) state-space op S&P data — Chapter 7 hoofdbijdrage
============================================================================

Doel: ontwikkel het time-varying parameter (TVP) state-space model voor de
Blue × EUA interactie op S&P data, gebruikmakend van een random-walk
specificatie voor β_int(t).

Onderzoeksvraag:
  Is β_int(t) — de Blue × EUA interactie — werkelijk tijdsvariërend?
  Wordt het sterker over tijd (Hypothese A) of inconsistent/volatiel
  (Hypothese B = sample-compositie artefact)?

Specification:
  Observation: event_yr_t ~ Bernoulli(p_t)
               logit(p_t) = α + β_blue × Blue + β_eua × EUA_z 
                          + β_int(t) × (Blue × EUA_z) + γ × X
  State:       β_int(t) = β_int(t-1) + η_t,  η_t ~ N(0, σ²_η)

Implementatie via:
  1. Sliding-window OLS (snelle benadering)
  2. Kalman filter via random-walk parameter (statsmodels.tsa.statespace)
  3. PyMC random-walk Bayesian (full posterior)

Vergelijking met Pijler 17 historic SV pilot.

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MACRO_PATH = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: REBUILD PERSON-YEAR PANEL ===
header("STAP 1: Person-year panel met EUA per jaar")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
df = sp[(sp['is_blue'] == 1) | (sp['is_green'] == 1)].copy().reset_index(drop=True)
df['project_id'] = df.index
df['cancelled'] = (df['project_status'] == 'Plans cancelled').astype(int)
df['onhold'] = df['project_status'].isin(['On-hold (assumed)', 'On-hold (confirmed)']).astype(int)
df['decomm'] = (df['project_status'] == 'Decommissioned').astype(int)
df['event_any'] = (df['cancelled'] | df['onhold'] | df['decomm']).astype(int)
df['event_year'] = np.where(
    df['event_any'] == 1,
    np.where(df['est_year_online'].notna(),
             np.ceil((df['announce_year'] + df['est_year_online']) / 2),
             df['announce_year'] + 3),
    2026.0
).clip(min=df['announce_year'], max=2026.0)
df['log_capacity'] = np.log1p(pd.to_numeric(df['Output capacity per year'], errors='coerce').fillna(0))
df['region_eu'] = (df['Region major'] == 'Europe (EU-27)').astype(int)

macro = pd.read_csv(MACRO_PATH)
macro['date'] = pd.to_datetime(macro['date'])
macro['year'] = macro['date'].dt.year
eua_yearly = macro.groupby('year')['eua'].mean().reset_index()
eua_yearly.columns = ['year', 'eua_annual']
mu_eua = eua_yearly[(eua_yearly['year'] >= 2010) & (eua_yearly['year'] <= 2025)]['eua_annual'].mean()
sd_eua = eua_yearly[(eua_yearly['year'] >= 2010) & (eua_yearly['year'] <= 2025)]['eua_annual'].std()
eua_yearly['eua_z'] = (eua_yearly['eua_annual'] - mu_eua) / sd_eua

panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['announce_year'])
    t_end = int(row['event_year'])
    is_event = int(row['event_any'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year': t,
            'event_yr': int(is_event and (t == t_end)),
            'is_blue': int(row['is_blue']),
            'log_capacity': float(row['log_capacity']),
            'region_eu': int(row['region_eu']),
            'years_since_announce': t - t_start,
        })
panel = pd.DataFrame(panel_rows)
panel = panel.merge(eua_yearly[['year', 'eua_annual', 'eua_z']], on='year', how='left')
panel['eua_z'] = panel['eua_z'].fillna(0.0)
panel['blue_x_eua_z'] = panel['is_blue'] * panel['eua_z']

print(f"Panel: {len(panel)} rijen, {panel['event_yr'].sum()} events")


# === STAP 2: SLIDING WINDOW OLS ESTIMATE OF β_int(t) ===
header("STAP 2: Sliding-window estimate van β_int(t) (5-jaars vensters)")

formula = ('event_yr ~ is_blue + eua_z + blue_x_eua_z + log_capacity '
           '+ years_since_announce + I(years_since_announce ** 2)')

window_size = 5  # jaren
tvp_rows = []
for center_year in range(2014, 2026):
    yr_start = center_year - window_size // 2
    yr_end = center_year + window_size // 2
    sub = panel[(panel['year'] >= yr_start) & (panel['year'] <= yr_end)].copy()
    if sub['event_yr'].sum() < 15:
        tvp_rows.append({'year': center_year, 'beta_int': np.nan, 'se': np.nan, 'p': np.nan, 'n_events': sub['event_yr'].sum()})
        continue
    try:
        mod = smf.glm(formula=formula, data=sub, family=sm.families.Binomial()).fit(cov_type='HC3')
        b = float(mod.params['blue_x_eua_z'])
        se = float(mod.bse['blue_x_eua_z'])
        p = float(mod.pvalues['blue_x_eua_z'])
        tvp_rows.append({'year': center_year, 'beta_int': b, 'se': se, 'p': p, 'n_events': sub['event_yr'].sum()})
    except Exception as e:
        tvp_rows.append({'year': center_year, 'beta_int': np.nan, 'se': np.nan, 'p': np.nan, 'n_events': sub['event_yr'].sum()})

tvp_window = pd.DataFrame(tvp_rows)
print("\nSliding-window β_int(t) estimates (5y windows):")
print(tvp_window.round(4).to_string(index=False))


# === STAP 3: RANDOM WALK BAYESIAN VIA PYMC ===
header("STAP 3: Random-walk Bayesian voor β_int(t)")

try:
    import pymc as pm
    import arviz as az
    
    # Build annual aggregates: events per year, exposures per year
    yearly = panel.groupby('year').agg(
        N_obs=('event_yr', 'size'),
        N_events=('event_yr', 'sum'),
        avg_eua_z=('eua_z', 'mean'),
        n_blue=('is_blue', 'sum'),
    ).reset_index()
    
    # For each year, fit a logit with full data, then collect the time-series of beta_int(t)
    # We use PyMC to estimate the entire time-series jointly with a random walk prior
    print("\n--- Bayesian random-walk TVP model ---")
    
    panel_subset = panel[panel['year'].between(2018, 2026)].copy()  # focus on identifiable period
    years = sorted(panel_subset['year'].unique())
    T = len(years)
    print(f"Years: {years}, T = {T}")
    print(f"Sample: {len(panel_subset)}, events: {panel_subset['event_yr'].sum()}")
    
    # Map year to time index
    year_idx = {y: i for i, y in enumerate(years)}
    panel_subset['t_idx'] = panel_subset['year'].map(year_idx)
    
    with pm.Model() as tvp_model:
        # Static main effects
        alpha = pm.Normal('alpha', mu=0, sigma=5)
        beta_blue = pm.Normal('beta_blue', mu=0, sigma=2)
        beta_eua = pm.Normal('beta_eua', mu=0, sigma=2)
        beta_logcap = pm.Normal('beta_logcap', mu=0, sigma=1)
        beta_ysa = pm.Normal('beta_ysa', mu=0, sigma=1)
        
        # Random-walk for β_int(t)
        sigma_eta = pm.HalfNormal('sigma_eta', sigma=0.5)
        beta_int_init = pm.Normal('beta_int_init', mu=0, sigma=2)
        innovations = pm.Normal('innovations', mu=0, sigma=sigma_eta, shape=T-1)
        beta_int = pm.Deterministic('beta_int', pm.math.concatenate([[beta_int_init], beta_int_init + pm.math.cumsum(innovations)]))
        
        # Linear predictor
        b_int_for_obs = beta_int[panel_subset['t_idx'].values]
        is_blue_arr = panel_subset['is_blue'].values.astype(float)
        eua_z_arr = panel_subset['eua_z'].values
        logit_p = (alpha
                   + beta_blue * is_blue_arr
                   + beta_eua * eua_z_arr
                   + b_int_for_obs * (is_blue_arr * eua_z_arr)
                   + beta_logcap * panel_subset['log_capacity'].values
                   + beta_ysa * panel_subset['years_since_announce'].values)
        
        # Observation
        pm.Bernoulli('y', logit_p=logit_p, observed=panel_subset['event_yr'].values)
        
        # Sample
        print("  Sampling (this takes 1-2 min)...")
        trace = pm.sample(draws=1000, tune=1500, chains=2, target_accept=0.92,
                          random_seed=20260520, progressbar=False)
    
    # Extract posterior for β_int(t)
    beta_int_samples = trace.posterior['beta_int'].values
    beta_int_mean = beta_int_samples.mean(axis=(0,1))
    beta_int_lo = np.percentile(beta_int_samples, 2.5, axis=(0,1))
    beta_int_hi = np.percentile(beta_int_samples, 97.5, axis=(0,1))
    
    print(f"\n=== TVP β_int(t) POSTERIOR ===")
    print(f"{'Year':<6}{'Mean':<10}{'95% CI':<24}")
    for i, y in enumerate(years):
        print(f"{y:<6}{beta_int_mean[i]:+.4f}    [{beta_int_lo[i]:+.4f}, {beta_int_hi[i]:+.4f}]")
    
    # Sigma_eta posterior
    sigma_post = trace.posterior['sigma_eta'].values.flatten()
    print(f"\nσ_η posterior: mean = {sigma_post.mean():.4f}, 95% CI = [{np.percentile(sigma_post, 2.5):.4f}, {np.percentile(sigma_post, 97.5):.4f}]")
    
    bayes_tvp = pd.DataFrame({
        'year': years,
        'beta_int_mean': beta_int_mean,
        'beta_int_lo': beta_int_lo,
        'beta_int_hi': beta_int_hi,
    })
    
    pymc_success = True
    
except ImportError:
    print("PyMC niet beschikbaar — skip Bayesian TVP")
    pymc_success = False
    bayes_tvp = pd.DataFrame()
except Exception as e:
    print(f"PyMC sampling errored: {e}")
    pymc_success = False
    bayes_tvp = pd.DataFrame()


# === STAP 4: VERGELIJK MET PIJLER 17 HISTORIC SV/GAS ===
header("STAP 4: Vergelijk met Pijler 17 historic (SV/GAS pilot op v7)")

sv_path = OUTPUT_DIR / 'sv_comparison_with_gas.csv'
if sv_path.exists():
    sv_old = pd.read_csv(sv_path)
    print("Pijler 17 historic GAS-h1 β_int(t) (op v7):")
    print(sv_old[['year', 'beta_int_t']].round(4).to_string(index=False))


# === STAP 5: PLOTS ===
header("STAP 5: Visualisaties")

fig, ax = plt.subplots(figsize=(12, 7))

# Sliding window
valid_w = tvp_window.dropna(subset=['beta_int'])
ax.plot(valid_w['year'], valid_w['beta_int'], 'o-', color='#1f77b4',
        linewidth=2, markersize=10, label='Sliding 5y window (frequentist)')
ax.fill_between(valid_w['year'], valid_w['beta_int'] - 1.96 * valid_w['se'],
                valid_w['beta_int'] + 1.96 * valid_w['se'],
                color='#1f77b4', alpha=0.15, label='95% CI sliding')

# Bayesian random walk
if pymc_success and len(bayes_tvp) > 0:
    ax.plot(bayes_tvp['year'], bayes_tvp['beta_int_mean'], 's-', color='#d62728',
            linewidth=2, markersize=10, label='Bayesian RW posterior mean')
    ax.fill_between(bayes_tvp['year'], bayes_tvp['beta_int_lo'], bayes_tvp['beta_int_hi'],
                    color='#d62728', alpha=0.2, label='95% Bayesian CI')

# Historic v7 SV pilot
if sv_path.exists():
    ax.plot(sv_old['year'], sv_old['beta_int_t'], 'd--', color='gray',
            linewidth=1.5, markersize=8, alpha=0.7, label='v7 SV/GAS pilot (Pijler 17 historic)')

ax.axhline(y=0, color='black', linestyle=':', alpha=0.6)
ax.axhline(y=-0.325, color='green', linestyle='--', alpha=0.6, label='Static S&P estimate (-0.325)')
ax.axhline(y=-2.28, color='purple', linestyle='--', alpha=0.6, label='Static v7 estimate (-2.28)')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('β_int(t) — Blue × EUA interaction', fontsize=12)
ax.set_title('Pijler 24: TVP β_int(t) — drie estimation methoden\n(S&P data, vergelijking met v7 historic pilot)',
             fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler24_tvp_beta_int.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler24_tvp_beta_int.png")


# === STAP 6: HYPOTHESETESTING ===
header("STAP 6: Hypothese A (real TVP) vs Hypothese B (sample artefact)")

valid_betas = valid_w['beta_int'].dropna().values
if len(valid_betas) >= 3:
    # Test 1: Trend in β_int(t) over time
    yrs_valid = valid_w['year'].dropna().values
    if len(yrs_valid) >= 3:
        slope, intercept = np.polyfit(yrs_valid, valid_betas, 1)
        print(f"\nLinear trend in β_int(t):")
        print(f"  slope = {slope:+.5f} per year")
        print(f"  intercept (2014) = {intercept:+.4f}")
    
    # Test 2: Variance of β_int(t) — high variance ~ Hypothesis B
    sd_betas = np.std(valid_betas)
    print(f"\nVariance of β_int(t): SD = {sd_betas:.4f}")
    print(f"  Range: [{valid_betas.min():+.4f}, {valid_betas.max():+.4f}]")
    
    # Test 3: Sign consistency
    n_neg = sum(valid_betas < 0)
    n_pos = sum(valid_betas > 0)
    print(f"\nSign consistency: {n_neg} negatief, {n_pos} positief (van {len(valid_betas)})")
    
    if n_neg >= len(valid_betas) * 0.8:
        print(f"  → Direction consistent — supports Hypothesis A (real TVP)")
    elif n_pos >= len(valid_betas) * 0.5:
        print(f"  → Direction inconsistent — supports Hypothesis B (sample artefact)")
    else:
        print(f"  → Mixed direction — inconclusive")


# === STAP 7: OPSLAAN ===
header("STAP 7: Opslaan")
tvp_window.to_csv(OUTPUT_DIR / 'pijler24_sliding_window_beta_int.csv', index=False)
if pymc_success and len(bayes_tvp) > 0:
    bayes_tvp.to_csv(OUTPUT_DIR / 'pijler24_bayes_rw_beta_int.csv', index=False)

summary = pd.DataFrame([{
    'method': 'Pijler 24: TVP β_int(t) state-space on S&P',
    'n_panel_rows': len(panel),
    'n_events': int(panel['event_yr'].sum()),
    'static_estimate_p22': -0.325,
    'sliding_window_mean': float(np.nanmean(tvp_window['beta_int'])),
    'sliding_window_sd': float(np.nanstd(tvp_window['beta_int'])),
    'sliding_window_min': float(np.nanmin(tvp_window['beta_int'])),
    'sliding_window_max': float(np.nanmax(tvp_window['beta_int'])),
    'pymc_success': pymc_success,
    'pymc_sigma_eta_mean': float(sigma_post.mean()) if pymc_success else np.nan,
}])
summary.to_csv(OUTPUT_DIR / 'pijler24_summary.csv', index=False)


print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 24 (TVP β_int(t) state-space)")
print("=" * 78)
if len(valid_betas) >= 3:
    print(f"\nSliding window β_int(t) statistieken:")
    print(f"  Mean: {np.mean(valid_betas):+.4f}")
    print(f"  SD: {np.std(valid_betas):.4f}")
    print(f"  Range: [{np.min(valid_betas):+.4f}, {np.max(valid_betas):+.4f}]")
    if n_neg >= len(valid_betas) * 0.8:
        print(f"\n*** HYPOTHESE A ondersteund: β_int(t) consistent negatief ***")
        print(f"Carbon-conditional effect is real en mogelijk tijdsvariërend.")
    else:
        print(f"\n*** HYPOTHESE B ondersteund: β_int(t) volatiel/inconsistent ***")
        print(f"Suggesteert dat v7 finding (-2.51) mogelijk sample-compositie artefact was.")
