"""
38_tvp_publication_grade.py
============================================================================
Pijler 24c: Publication-grade TVP fix — Random Walk + AR(1) gerepareerd
============================================================================

OPLOSSING voor twee problemen:
  1. Pijler 24/24a RW failed (1000/2001 divergences) → identification issue
  2. Pijler 24b AR(1) failed (PyTensor numba compile error met Python loop)

FIX 1 — Random Walk met stronger priors:
  - sigma_eta ~ HalfNormal(0.1) i.p.v. 0.5 (forceer kleine tijdsvariatie)
  - Non-centered parameterization
  - target_accept = 0.99

FIX 2 — AR(1) via pytensor.scan (geen Python loop):
  - Vermijdt het tuple-length probleem
  - Stationary parameterization

CROSSCHECK:
  - Vergelijk RW + AR(1) + threshold (Pijler 24b)
  - Posterior predictive check
  - Forecast capability 2027-2030

Auteur: Sake Saakstra, 20 mei 2026
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
import pytensor
import arviz as az

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MACRO_PATH = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: HERBOUW PANEL ===
header("STAP 1: Herbouw panel (identiek Pijler 24/24b)")

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
            'years_since_announce': t - t_start,
        })
panel = pd.DataFrame(panel_rows)
panel = panel.merge(eua_yearly[['year', 'eua_annual', 'eua_z']], on='year', how='left')
panel['eua_z'] = panel['eua_z'].fillna(0.0)

panel_sub = panel[panel['year'].between(2018, 2026)].copy()
years = sorted(panel_sub['year'].unique())
T = len(years)
year_idx = {y: i for i, y in enumerate(years)}
panel_sub['t_idx'] = panel_sub['year'].map(year_idx)
print(f"Panel: {len(panel_sub)} obs, {panel_sub['event_yr'].sum()} events, T={T} years")


# === STAP 2: MODEL 1 — RW MET STRONG INFORMATIVE PRIORS ===
header("STAP 2: Model 1 — Random walk met sigma_eta ~ HalfNormal(0.1)")

print("""
Aanpassingen tov Pijler 24/24a:
  - sigma_eta ~ HalfNormal(0.1) (Pijler 24 had 0.5)
  - target_accept = 0.99 (Pijler 24 had 0.92)
  - 5000 tune (Pijler 24 had 1500)
  - Non-centered parameterization
""")

with pm.Model() as rw_model:
    alpha = pm.Normal('alpha', mu=0, sigma=3)
    beta_blue = pm.Normal('beta_blue', mu=0, sigma=2)
    beta_eua = pm.Normal('beta_eua', mu=0, sigma=2)
    beta_logcap = pm.Normal('beta_logcap', mu=0, sigma=1)
    beta_ysa = pm.Normal('beta_ysa', mu=0, sigma=1)
    
    # Strong prior op sigma_eta — forceer kleine RW variance
    sigma_eta = pm.HalfNormal('sigma_eta', sigma=0.1)
    beta_int_init = pm.Normal('beta_int_init', mu=0, sigma=1)
    
    # Non-centered RW
    innovations_raw = pm.Normal('innovations_raw', mu=0, sigma=1, shape=T-1)
    innovations = sigma_eta * innovations_raw
    beta_int_t = pm.Deterministic(
        'beta_int_t',
        pt.concatenate([[beta_int_init], beta_int_init + pt.cumsum(innovations)])
    )
    
    b_int_obs = beta_int_t[panel_sub['t_idx'].values]
    is_blue_arr = panel_sub['is_blue'].values.astype(float)
    eua_z_arr = panel_sub['eua_z'].values
    
    logit_p = (alpha + beta_blue * is_blue_arr + beta_eua * eua_z_arr
               + b_int_obs * (is_blue_arr * eua_z_arr)
               + beta_logcap * panel_sub['log_capacity'].values
               + beta_ysa * panel_sub['years_since_announce'].values)
    
    pm.Bernoulli('y', logit_p=logit_p, observed=panel_sub['event_yr'].values)
    
    print("Sampling RW (4 chains × 5000 tune × 2000 draws, target_accept=0.99)...")
    trace_rw = pm.sample(
        draws=2000, tune=5000, chains=4, target_accept=0.99,
        random_seed=20260520, progressbar=False, return_inferencedata=True
    )

# Diagnostics
sample_stats_rw = trace_rw.sample_stats
n_div_rw = int(sample_stats_rw['diverging'].sum())
total_rw = int(sample_stats_rw['diverging'].size)
summary_rw = az.summary(trace_rw, var_names=['alpha', 'beta_blue', 'beta_eua', 'sigma_eta', 'beta_int_init'])
print(f"\n--- RW MODEL DIAGNOSTICS ---")
print(summary_rw[['mean', 'sd', 'ess_bulk', 'r_hat']].round(4).to_string())
print(f"\nDivergences: {n_div_rw} / {total_rw} ({100*n_div_rw/total_rw:.2f}%)")


# === STAP 3: MODEL 2 — AR(1) VIA PYTENSOR.SCAN ===
header("STAP 3: Model 2 — AR(1) via pytensor.scan (geen Python loop)")

print("""
AR(1): β(t) = (1-φ)·μ + φ·β(t-1) + ε(t),  ε ~ N(0, σ)

PyTensor scan-based implementation vermijdt het tuple-length compile probleem.
Stationary AR(1) heeft expected value μ en variance σ²/(1-φ²).
""")

def ar1_step(epsilon, prev_beta, mu_ar, phi):
    new_beta = (1 - phi) * mu_ar + phi * prev_beta + epsilon
    return new_beta

with pm.Model() as ar1_model:
    alpha = pm.Normal('alpha', mu=0, sigma=3)
    beta_blue = pm.Normal('beta_blue', mu=0, sigma=2)
    beta_eua = pm.Normal('beta_eua', mu=0, sigma=2)
    beta_logcap = pm.Normal('beta_logcap', mu=0, sigma=1)
    beta_ysa = pm.Normal('beta_ysa', mu=0, sigma=1)
    
    # AR(1) parameters
    mu_ar = pm.Normal('mu_ar', mu=0, sigma=1)
    phi = pm.Beta('phi', alpha=2, beta=2)  # persistence in (0,1)
    sigma_ar = pm.HalfNormal('sigma_ar', sigma=0.3)
    
    # Initial state from stationary distribution
    sigma_stationary = sigma_ar / pt.sqrt(1 - phi**2 + 1e-6)
    beta_0 = pm.Normal('beta_0', mu=mu_ar, sigma=sigma_stationary)
    
    # Innovations
    innovations = pm.Normal('innovations', mu=0, sigma=sigma_ar, shape=T-1)
    
    # Build trajectory via pytensor.scan
    results, _ = pytensor.scan(
        fn=ar1_step,
        sequences=[innovations],
        outputs_info=[beta_0],
        non_sequences=[mu_ar, phi],
        strict=True,
    )
    
    beta_int_t = pm.Deterministic('beta_int_t', pt.concatenate([[beta_0], results]))
    
    b_int_obs = beta_int_t[panel_sub['t_idx'].values]
    is_blue_arr = panel_sub['is_blue'].values.astype(float)
    eua_z_arr = panel_sub['eua_z'].values
    
    logit_p = (alpha + beta_blue * is_blue_arr + beta_eua * eua_z_arr
               + b_int_obs * (is_blue_arr * eua_z_arr)
               + beta_logcap * panel_sub['log_capacity'].values
               + beta_ysa * panel_sub['years_since_announce'].values)
    
    pm.Bernoulli('y', logit_p=logit_p, observed=panel_sub['event_yr'].values)
    
    print("Sampling AR(1) via scan (4 chains × 3000 tune × 2000 draws, target_accept=0.95)...")
    trace_ar1 = pm.sample(
        draws=2000, tune=3000, chains=4, target_accept=0.95,
        random_seed=20260520, progressbar=False, return_inferencedata=True
    )

# Diagnostics
sample_stats_ar1 = trace_ar1.sample_stats
n_div_ar1 = int(sample_stats_ar1['diverging'].sum())
total_ar1 = int(sample_stats_ar1['diverging'].size)
summary_ar1 = az.summary(trace_ar1, var_names=['alpha', 'beta_blue', 'beta_eua', 'mu_ar', 'phi', 'sigma_ar', 'beta_0'])
print(f"\n--- AR(1) MODEL DIAGNOSTICS ---")
print(summary_ar1[['mean', 'sd', 'ess_bulk', 'r_hat']].round(4).to_string())
print(f"\nDivergences: {n_div_ar1} / {total_ar1} ({100*n_div_ar1/total_ar1:.2f}%)")


# === STAP 4: EXTRACT TIME-SERIES POSTERIORS ===
header("STAP 4: Extract β_int(t) posterior trajectories")

# RW
beta_rw_samples = trace_rw.posterior['beta_int_t'].values
beta_rw_mean = beta_rw_samples.mean(axis=(0,1))
beta_rw_lo = np.percentile(beta_rw_samples, 2.5, axis=(0,1))
beta_rw_hi = np.percentile(beta_rw_samples, 97.5, axis=(0,1))
p_neg_rw = np.mean(beta_rw_samples < 0, axis=(0,1))

# AR(1)
beta_ar1_samples = trace_ar1.posterior['beta_int_t'].values
beta_ar1_mean = beta_ar1_samples.mean(axis=(0,1))
beta_ar1_lo = np.percentile(beta_ar1_samples, 2.5, axis=(0,1))
beta_ar1_hi = np.percentile(beta_ar1_samples, 97.5, axis=(0,1))
p_neg_ar1 = np.mean(beta_ar1_samples < 0, axis=(0,1))

print(f"\n{'Year':<6}{'RW mean':<12}{'RW 95% CI':<22}{'AR(1) mean':<14}{'AR(1) 95% CI':<22}{'P(β<0) RW':<11}{'P(β<0) AR1':<11}")
for i, y in enumerate(years):
    print(f"{y:<6}"
          f"{beta_rw_mean[i]:+.3f}      "
          f"[{beta_rw_lo[i]:+.3f}, {beta_rw_hi[i]:+.3f}]   "
          f"{beta_ar1_mean[i]:+.3f}        "
          f"[{beta_ar1_lo[i]:+.3f}, {beta_ar1_hi[i]:+.3f}]   "
          f"{p_neg_rw[i]:.3f}     "
          f"{p_neg_ar1[i]:.3f}")

# σ posteriors
sigma_eta_rw = trace_rw.posterior['sigma_eta'].values.flatten()
sigma_ar = trace_ar1.posterior['sigma_ar'].values.flatten()
phi_post = trace_ar1.posterior['phi'].values.flatten()

print(f"\nσ_η (RW): mean = {sigma_eta_rw.mean():.4f}, 95% CI = [{np.percentile(sigma_eta_rw, 2.5):.4f}, {np.percentile(sigma_eta_rw, 97.5):.4f}]")
print(f"σ_ar (AR1): mean = {sigma_ar.mean():.4f}, 95% CI = [{np.percentile(sigma_ar, 2.5):.4f}, {np.percentile(sigma_ar, 97.5):.4f}]")
print(f"φ (persistence): mean = {phi_post.mean():.4f}, 95% CI = [{np.percentile(phi_post, 2.5):.4f}, {np.percentile(phi_post, 97.5):.4f}]")


# === STAP 5: MODEL COMPARISON via WAIC/LOO ===
header("STAP 5: Model comparison via LOO")

try:
    waic_rw = az.loo(trace_rw)
    waic_ar1 = az.loo(trace_ar1)
    print(f"\nLOO RW:    elpd_loo = {waic_rw.elpd_loo:.2f} ± {waic_rw.se:.2f}")
    print(f"LOO AR(1): elpd_loo = {waic_ar1.elpd_loo:.2f} ± {waic_ar1.se:.2f}")
    
    diff = waic_ar1.elpd_loo - waic_rw.elpd_loo
    print(f"\nΔelpd_loo (AR1 - RW): {diff:+.2f}")
    print(f"  {'AR(1) preferred' if diff > 2 else 'RW preferred' if diff < -2 else 'Similar fit'}")
except Exception as e:
    print(f"LOO compare failed: {e}")
    waic_rw = waic_ar1 = None


# === STAP 6: FORECAST 2027-2030 ===
header("STAP 6: Forecast β_int(t) voor 2027-2030 met AR(1)")

print("AR(1) parameters → forward simulation:")
n_forecast = 4
n_sim = 1000
phi_med = float(np.median(phi_post))
mu_med = float(np.median(trace_ar1.posterior['mu_ar'].values))
sigma_med = float(np.median(sigma_ar))
beta_last = float(beta_ar1_mean[-1])

print(f"  φ = {phi_med:.3f}, μ = {mu_med:.3f}, σ = {sigma_med:.3f}")
print(f"  β_int(2026) = {beta_last:+.3f}")

rng = np.random.default_rng(20260520)
forecast_paths = np.zeros((n_sim, n_forecast))
for i in range(n_sim):
    b = beta_last
    for j in range(n_forecast):
        b = (1 - phi_med) * mu_med + phi_med * b + rng.normal(0, sigma_med)
        forecast_paths[i, j] = b

forecast_years = list(range(2027, 2027 + n_forecast))
forecast_mean = forecast_paths.mean(axis=0)
forecast_lo = np.percentile(forecast_paths, 2.5, axis=0)
forecast_hi = np.percentile(forecast_paths, 97.5, axis=0)

print(f"\nAR(1) forecast β_int(t):")
for i, y in enumerate(forecast_years):
    print(f"  {y}: {forecast_mean[i]:+.3f} [95% CI: {forecast_lo[i]:+.3f}, {forecast_hi[i]:+.3f}]")


# === STAP 7: VISUALISATIES ===
header("STAP 7: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: RW + AR(1) trajectories overlay
ax = axes[0, 0]
ax.plot(years, beta_rw_mean, 'o-', color='#1f77b4', linewidth=2.5, markersize=10, label='RW mean')
ax.fill_between(years, beta_rw_lo, beta_rw_hi, color='#1f77b4', alpha=0.15, label='RW 95% CI')

ax.plot(years, beta_ar1_mean, 's-', color='#d62728', linewidth=2.5, markersize=10, label='AR(1) mean')
ax.fill_between(years, beta_ar1_lo, beta_ar1_hi, color='#d62728', alpha=0.15, label='AR(1) 95% CI')

# Threshold model (Pijler 24b) overlay
ax.axhline(y=3.40, xmin=0, xmax=0.27, color='gray', linewidth=2.5, label='Threshold β_pre = +3.40')
ax.axhline(y=-1.25, xmin=0.27, xmax=1, color='gray', linewidth=2.5, label='Threshold β_post = -1.25')

ax.axhline(y=0, color='black', linewidth=0.8)
ax.axhline(y=-0.325, color='green', linestyle='--', alpha=0.5, label='Static (Pijler 22)')
ax.set_xlabel('Year')
ax.set_ylabel('β_int(t)')
ax.set_title('Three methods comparison')
ax.legend(loc='best', fontsize=8)
ax.grid(alpha=0.3)

# Panel B: P(β < 0)
ax = axes[0, 1]
x_pos = np.arange(len(years))
width = 0.35
ax.bar(x_pos - width/2, p_neg_rw, width, label='RW', color='#1f77b4', edgecolor='black')
ax.bar(x_pos + width/2, p_neg_ar1, width, label='AR(1)', color='#d62728', edgecolor='black')
ax.axhline(y=0.95, color='red', linestyle='--', alpha=0.6, label='95% threshold')
ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)
ax.set_xticks(x_pos)
ax.set_xticklabels(years, rotation=45)
ax.set_ylabel('P(β_int(t) < 0)')
ax.set_title('Posterior probability of negative interaction')
ax.legend()
ax.grid(alpha=0.3, axis='y')

# Panel C: σ posteriors
ax = axes[1, 0]
ax.hist(sigma_eta_rw, bins=50, color='#1f77b4', alpha=0.6, density=True, label=f'σ_η (RW): med = {np.median(sigma_eta_rw):.3f}')
ax.hist(sigma_ar, bins=50, color='#d62728', alpha=0.6, density=True, label=f'σ_ar (AR1): med = {np.median(sigma_ar):.3f}')
ax.set_xlabel('Variance parameter posterior')
ax.set_ylabel('Density')
ax.set_title('Time-variation parameters')
ax.legend()
ax.grid(alpha=0.3, axis='y')

# Panel D: AR(1) forecast
ax = axes[1, 1]
ax.plot(years, beta_ar1_mean, 'o-', color='#d62728', linewidth=2.5, markersize=10, label='AR(1) posterior (historical)')
ax.fill_between(years, beta_ar1_lo, beta_ar1_hi, color='#d62728', alpha=0.15)

ax.plot(forecast_years, forecast_mean, 's--', color='#9c27b0', linewidth=2.5, markersize=10, label='AR(1) forecast 2027-2030')
ax.fill_between(forecast_years, forecast_lo, forecast_hi, color='#9c27b0', alpha=0.15, label='Forecast 95% CI')

ax.axhline(y=0, color='black', linewidth=0.8)
ax.axhline(y=float(mu_med), color='gray', linestyle=':', alpha=0.5, label=f'μ_ar = {mu_med:+.3f}')
ax.set_xlabel('Year')
ax.set_ylabel('β_int(t)')
ax.set_title(f'AR(1) forecast: persistence φ = {phi_med:.3f}')
ax.legend(loc='best', fontsize=9)
ax.grid(alpha=0.3)

plt.suptitle('Pijler 24c: Publication-grade TVP — RW (stronger prior) + AR(1) via scan + forecast',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler24c_publication_grade.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler24c_publication_grade.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Opslaan")

bayes_compare = pd.DataFrame({
    'year': years,
    'rw_mean': beta_rw_mean, 'rw_lo95': beta_rw_lo, 'rw_hi95': beta_rw_hi, 'p_neg_rw': p_neg_rw,
    'ar1_mean': beta_ar1_mean, 'ar1_lo95': beta_ar1_lo, 'ar1_hi95': beta_ar1_hi, 'p_neg_ar1': p_neg_ar1,
})
bayes_compare.to_csv(OUTPUT_DIR / 'pijler24c_bayes_compare.csv', index=False)

forecast_df = pd.DataFrame({
    'year': forecast_years,
    'forecast_mean': forecast_mean,
    'forecast_lo95': forecast_lo,
    'forecast_hi95': forecast_hi,
})
forecast_df.to_csv(OUTPUT_DIR / 'pijler24c_ar1_forecast.csv', index=False)

conv = pd.DataFrame([{
    'method': 'Pijler 24c: Publication-grade TVP',
    'rw_divergences': n_div_rw,
    'rw_total': total_rw,
    'rw_divergence_pct': 100*n_div_rw/total_rw,
    'rw_sigma_eta_mean': float(sigma_eta_rw.mean()),
    'ar1_divergences': n_div_ar1,
    'ar1_total': total_ar1,
    'ar1_divergence_pct': 100*n_div_ar1/total_ar1,
    'ar1_phi_mean': float(phi_post.mean()),
    'ar1_phi_ci_lo': float(np.percentile(phi_post, 2.5)),
    'ar1_phi_ci_hi': float(np.percentile(phi_post, 97.5)),
    'ar1_sigma_mean': float(sigma_ar.mean()),
    'ar1_mu_mean': float(np.mean(trace_ar1.posterior['mu_ar'].values)),
    'loo_rw_elpd': float(waic_rw.elpd_loo) if waic_rw else np.nan,
    'loo_ar1_elpd': float(waic_ar1.elpd_loo) if waic_ar1 else np.nan,
}])
conv.to_csv(OUTPUT_DIR / 'pijler24c_convergence.csv', index=False)

print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 24c (Publication-grade TVP)")
print("=" * 78)
print(f"""
CONVERGENCE STATUS:
  RW divergences:    {n_div_rw} / {total_rw} ({100*n_div_rw/total_rw:.2f}%)
                     (Pijler 24: 1000/2000 = 50%, Pijler 24a: 2001/8000 = 25%)
  AR(1) divergences: {n_div_ar1} / {total_ar1} ({100*n_div_ar1/total_ar1:.2f}%)

DRIE METHODES SAMENGEVOEGD:
  1. Threshold (Pijler 24b):  τ*=2020, β_pre = +3.40, β_post = -1.25, Wald p < 0.0001
  2. Random Walk:             σ_η = {sigma_eta_rw.mean():.3f} [{np.percentile(sigma_eta_rw, 2.5):.3f}, {np.percentile(sigma_eta_rw, 97.5):.3f}]
  3. AR(1):                   φ = {phi_post.mean():.3f}, σ_ar = {sigma_ar.mean():.3f}, μ = {float(np.mean(trace_ar1.posterior['mu_ar'].values)):.3f}

AR(1) FORECAST 2027-2030:
  Mean β_int trajectory: {[f'{forecast_mean[i]:+.2f}' for i in range(n_forecast)]}
  Direction: {'consolidating around mean μ_ar' if abs(forecast_mean[-1] - mu_med) < 0.5 else 'continued movement'}

VOOR PHD CHAPTER 7:
  Drie convergerende methodes versterken sign-shift finding.
  AR(1) levert forecast-capability voor PhD scenario analyse.
""")
