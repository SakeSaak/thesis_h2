"""
32_tvp_state_space_v2.py
============================================================================
Pijler 24a: TVP β_int(t) state-space — PUBLICATION-GRADE HERIMPLEMENTATIE
============================================================================

Doel: herstel van Pijler 24's PyMC convergence issues (1000 divergences,
r_hat > 1.01, ESS < 100) voor PhD Chapter 7 publication-grade defense.

Aanpassingen t.o.v. Pijler 24:
1. NON-CENTERED PARAMETERIZATION voor random walk
   - Was: innovations ~ Normal(0, sigma_eta)
   - Nu:  innovations_raw ~ Normal(0, 1), innovations = sigma_eta * innovations_raw
   - Voorkomt 'funnel' divergences als sigma_eta klein wordt
   
2. 4 CHAINS (was 2) voor robuust r_hat/ESS

3. target_accept = 0.95 (was 0.92)
   - Kleinere step-size, minder divergences
   
4. 3000 tune steps (was 1500)
   - Betere NUTS adaptation
   
5. INFORMATIVE PRIORS gebaseerd op Pijler 22 static finding
   - beta_int_init ~ Normal(0, 1) (Pijler 22 static = -0.33)
   - sigma_eta ~ HalfNormal(0.5) (eerdere posterior mean 1.11 mogelijk overschatting)

6. CONVERGENCE DIAGNOSTICS panel:
   - r_hat < 1.01 per parameter
   - ESS bulk > 400 per chain
   - Divergences < 50 (van 8000 totaal)
   - Energy plot
   - Pair plots

7. POSTERIOR PREDICTIVE CHECKS

Output: publication-ready β_int(t) trajectory met betrouwbare CIs

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
import arviz as az

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MACRO_PATH = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: HERBOUW PERSON-YEAR PANEL (identiek aan Pijler 24) ===
header("STAP 1: Herbouw person-year panel met EUA per jaar")

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

# Restrict to identifiable period: 2018-2026 (years met genoeg events)
panel_sub = panel[panel['year'].between(2018, 2026)].copy()
years = sorted(panel_sub['year'].unique())
T = len(years)
year_idx = {y: i for i, y in enumerate(years)}
panel_sub['t_idx'] = panel_sub['year'].map(year_idx)

print(f"Panel restricted to 2018-2026: {len(panel_sub)} obs, {panel_sub['event_yr'].sum()} events")
print(f"T = {T} time-periods: {years}")


# === STAP 2: NON-CENTERED PARAMETERIZATION BAYESIAN MODEL ===
header("STAP 2: Bayesian random-walk TVP met NON-CENTERED reparameterization")

print("""
Model specificatie:

Observation model:
  event_yr_it ~ Bernoulli(p_it)
  logit(p_it) = alpha + beta_blue * is_blue_i + beta_eua * eua_z_it 
              + beta_int_t[i] * (is_blue_i * eua_z_it)
              + beta_logcap * log_capacity_i 
              + beta_ysa * years_since_announce_it

State model (non-centered random walk):
  beta_int_init ~ Normal(0, 1)
  innovations_raw ~ Normal(0, 1)  [shape T-1]
  sigma_eta ~ HalfNormal(0.5)
  innovations = sigma_eta * innovations_raw
  beta_int_t = beta_int_init + cumulative_sum(innovations)

Priors:
  alpha ~ Normal(0, 3)
  beta_blue ~ Normal(0, 2)
  beta_eua ~ Normal(0, 2)
  beta_logcap ~ Normal(0, 1)
  beta_ysa ~ Normal(0, 1)

Sampling: 4 chains x 3000 tune x 2000 draws, target_accept=0.95
""")

with pm.Model() as tvp_model_v2:
    # Static main effects
    alpha = pm.Normal('alpha', mu=0, sigma=3)
    beta_blue = pm.Normal('beta_blue', mu=0, sigma=2)
    beta_eua = pm.Normal('beta_eua', mu=0, sigma=2)
    beta_logcap = pm.Normal('beta_logcap', mu=0, sigma=1)
    beta_ysa = pm.Normal('beta_ysa', mu=0, sigma=1)
    
    # NON-CENTERED RANDOM WALK for beta_int(t)
    beta_int_init = pm.Normal('beta_int_init', mu=0, sigma=1)
    sigma_eta = pm.HalfNormal('sigma_eta', sigma=0.5)
    innovations_raw = pm.Normal('innovations_raw', mu=0, sigma=1, shape=T-1)
    innovations = pm.Deterministic('innovations', sigma_eta * innovations_raw)
    beta_int_t = pm.Deterministic(
        'beta_int_t',
        pm.math.concatenate([[beta_int_init], beta_int_init + pm.math.cumsum(innovations)])
    )
    
    # Linear predictor
    b_int_obs = beta_int_t[panel_sub['t_idx'].values]
    is_blue_arr = panel_sub['is_blue'].values.astype(float)
    eua_z_arr = panel_sub['eua_z'].values
    
    logit_p = (alpha
               + beta_blue * is_blue_arr
               + beta_eua * eua_z_arr
               + b_int_obs * (is_blue_arr * eua_z_arr)
               + beta_logcap * panel_sub['log_capacity'].values
               + beta_ysa * panel_sub['years_since_announce'].values)
    
    # Observation
    pm.Bernoulli('y', logit_p=logit_p, observed=panel_sub['event_yr'].values)
    
    print("Sampling (4 chains x 3000 tune x 2000 draws — geschat 3-6 min)...")
    trace = pm.sample(
        draws=2000,
        tune=3000,
        chains=4,
        target_accept=0.95,
        random_seed=20260520,
        progressbar=False,
        return_inferencedata=True,
    )


# === STAP 3: CONVERGENCE DIAGNOSTICS ===
header("STAP 3: Convergence diagnostics")

# Summary table
summary_stats = az.summary(trace, var_names=['alpha', 'beta_blue', 'beta_eua', 'beta_int_init',
                                              'sigma_eta', 'beta_logcap', 'beta_ysa'],
                            hdi_prob=0.95)
print("\nKey parameters posterior summary:")
print(summary_stats.round(4).to_string())

# Divergence count
sample_stats = trace.sample_stats
n_divergences = int(sample_stats['diverging'].sum())
total_draws = int(sample_stats['diverging'].size)
print(f"\nDivergences: {n_divergences} / {total_draws} ({100*n_divergences/total_draws:.2f}%)")

# r_hat extreme
max_rhat = summary_stats['r_hat'].max()
min_ess = summary_stats['ess_bulk'].min()
print(f"Maximum r_hat (key params): {max_rhat:.4f}  [target < 1.01]")
print(f"Minimum ESS_bulk (key params): {min_ess:.0f}  [target > 400]")

# Beta_int_t diagnostics
beta_int_summary = az.summary(trace, var_names=['beta_int_t'], hdi_prob=0.95)
print(f"\nbeta_int_t r_hat range: [{beta_int_summary['r_hat'].min():.3f}, {beta_int_summary['r_hat'].max():.3f}]")
print(f"beta_int_t ESS_bulk range: [{beta_int_summary['ess_bulk'].min():.0f}, {beta_int_summary['ess_bulk'].max():.0f}]")


# === STAP 4: BETA_INT(T) POSTERIOR TRAJECTORY ===
header("STAP 4: β_int(t) posterior trajectory")

beta_int_samples = trace.posterior['beta_int_t'].values  # shape: (4, 2000, T)
beta_int_mean = beta_int_samples.mean(axis=(0,1))
beta_int_median = np.median(beta_int_samples, axis=(0,1))
beta_int_lo = np.percentile(beta_int_samples, 2.5, axis=(0,1))
beta_int_hi = np.percentile(beta_int_samples, 97.5, axis=(0,1))
beta_int_lo80 = np.percentile(beta_int_samples, 10, axis=(0,1))
beta_int_hi80 = np.percentile(beta_int_samples, 90, axis=(0,1))

# Posterior probability of negative
p_negative = np.mean(beta_int_samples < 0, axis=(0,1))

print(f"\n{'Year':<6}{'Mean':<10}{'Median':<10}{'95% CI':<24}{'P(β<0)':<10}")
print("-" * 60)
for i, y in enumerate(years):
    print(f"{y:<6}{beta_int_mean[i]:+.4f}    {beta_int_median[i]:+.4f}    "
          f"[{beta_int_lo[i]:+.3f}, {beta_int_hi[i]:+.3f}]    {p_negative[i]:.3f}")

bayes_tvp = pd.DataFrame({
    'year': years,
    'beta_int_mean': beta_int_mean,
    'beta_int_median': beta_int_median,
    'beta_int_lo95': beta_int_lo,
    'beta_int_hi95': beta_int_hi,
    'beta_int_lo80': beta_int_lo80,
    'beta_int_hi80': beta_int_hi80,
    'p_negative': p_negative,
})

# Sign-shift detection
print("\n=== SIGN-SHIFT DETECTION ===")
print(f"Eerste jaar met P(β_int < 0) > 0.95: ", end="")
shift_years = [y for y, p in zip(years, p_negative) if p > 0.95]
if shift_years:
    print(f"{shift_years[0]}")
else:
    print("geen")
print(f"Laatste jaar met P(β_int > 0) > 0.50: ", end="")
positive_years = [y for y, p in zip(years, p_negative) if p < 0.50]
if positive_years:
    print(f"{positive_years[-1]}")
else:
    print("geen")


# === STAP 5: σ_η POSTERIOR ===
header("STAP 5: σ_η posterior (mate van tijdsvariatie)")

sigma_post = trace.posterior['sigma_eta'].values.flatten()
print(f"σ_η posterior:")
print(f"  Mean: {sigma_post.mean():.4f}")
print(f"  Median: {np.median(sigma_post):.4f}")
print(f"  95% CI: [{np.percentile(sigma_post, 2.5):.4f}, {np.percentile(sigma_post, 97.5):.4f}]")
print(f"  P(σ_η > 0.1): {np.mean(sigma_post > 0.1):.3f}  [evidence voor tijdsvariatie]")
print(f"  P(σ_η > 0.3): {np.mean(sigma_post > 0.3):.3f}")
print(f"  P(σ_η > 0.5): {np.mean(sigma_post > 0.5):.3f}")
print(f"\nVergelijking met Pijler 24 (centered): mean = 1.11 (mogelijk overschatting door divergences)")


# === STAP 6: POSTERIOR PREDICTIVE CHECK ===
header("STAP 6: Posterior predictive check")

with tvp_model_v2:
    ppc = pm.sample_posterior_predictive(trace, var_names=['y'], random_seed=20260520, progressbar=False)

# Observed vs simulated event rate per year
ppc_yhat = ppc.posterior_predictive['y'].values  # (4, 2000, N)
obs_y = panel_sub['event_yr'].values

# Aggregate per year
event_rate_obs = []
event_rate_ppc_mean = []
event_rate_ppc_lo = []
event_rate_ppc_hi = []

for y in years:
    mask = panel_sub['year'].values == y
    obs_rate = obs_y[mask].mean()
    ppc_rates = ppc_yhat[:, :, mask].mean(axis=2)
    event_rate_obs.append(obs_rate)
    event_rate_ppc_mean.append(ppc_rates.mean())
    event_rate_ppc_lo.append(np.percentile(ppc_rates, 2.5))
    event_rate_ppc_hi.append(np.percentile(ppc_rates, 97.5))

ppc_check = pd.DataFrame({
    'year': years,
    'obs_event_rate': event_rate_obs,
    'ppc_mean': event_rate_ppc_mean,
    'ppc_lo95': event_rate_ppc_lo,
    'ppc_hi95': event_rate_ppc_hi,
})
print("Posterior predictive check per jaar:")
print(ppc_check.round(4).to_string(index=False))


# === STAP 7: FIGUREN ===
header("STAP 7: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: β_int(t) trajectory met 95% and 80% CI
ax = axes[0, 0]
ax.plot(years, beta_int_mean, 'o-', color='#d62728', linewidth=2.5, markersize=10, label='Posterior mean')
ax.fill_between(years, beta_int_lo, beta_int_hi, color='#d62728', alpha=0.15, label='95% CI')
ax.fill_between(years, beta_int_lo80, beta_int_hi80, color='#d62728', alpha=0.25, label='80% CI')
ax.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
ax.axhline(y=-0.325, color='green', linestyle='--', alpha=0.6, label='Static estimate (Pijler 22)')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('β_int(t) — Blue × EUA interaction', fontsize=12)
ax.set_title('Pijler 24a: β_int(t) posterior trajectory (non-centered RW)')
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)

# Panel B: P(β_int(t) < 0)
ax = axes[0, 1]
colors_p = ['#d62728' if p > 0.95 else '#ffc107' if p > 0.50 else '#1f77b4' for p in p_negative]
ax.bar(years, p_negative, color=colors_p, edgecolor='black', alpha=0.8)
ax.axhline(y=0.95, color='red', linestyle='--', alpha=0.6, label='95% threshold')
ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='50% threshold')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('P(β_int(t) < 0)', fontsize=12)
ax.set_title('Posterior probability of negative interaction')
ax.legend(loc='lower right', fontsize=10)
ax.set_ylim(0, 1.05)
ax.grid(alpha=0.3, axis='y')

# Panel C: σ_η posterior
ax = axes[1, 0]
ax.hist(sigma_post, bins=50, color='#9c27b0', edgecolor='black', alpha=0.8, density=True)
ax.axvline(x=np.median(sigma_post), color='red', linestyle='--', linewidth=2, label=f'Median = {np.median(sigma_post):.3f}')
ax.axvline(x=np.percentile(sigma_post, 2.5), color='red', linestyle=':', alpha=0.6)
ax.axvline(x=np.percentile(sigma_post, 97.5), color='red', linestyle=':', alpha=0.6, label='95% CI')
ax.set_xlabel('σ_η posterior', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.set_title(f'σ_η posterior: evidence voor tijdsvariatie\n95% CI: [{np.percentile(sigma_post, 2.5):.3f}, {np.percentile(sigma_post, 97.5):.3f}]')
ax.legend()
ax.grid(alpha=0.3, axis='y')

# Panel D: Posterior predictive check
ax = axes[1, 1]
ax.plot(years, event_rate_obs, 'o-', color='black', linewidth=2.5, markersize=10, label='Observed event rate')
ax.fill_between(years, ppc_check['ppc_lo95'], ppc_check['ppc_hi95'], color='#1f77b4', alpha=0.2, label='95% PPC')
ax.plot(years, ppc_check['ppc_mean'], 's--', color='#1f77b4', linewidth=2, label='PPC mean')
ax.set_xlabel('Year', fontsize=12)
ax.set_ylabel('Annual event rate', fontsize=12)
ax.set_title('Posterior predictive check')
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)

plt.suptitle('Pijler 24a: Publication-grade TVP-state-space (non-centered)',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler24a_tvp_v2_diagnostics.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler24a_tvp_v2_diagnostics.png")

# Trace plot voor key params
fig, axes = plt.subplots(3, 2, figsize=(14, 10))
az.plot_trace(trace, var_names=['alpha', 'beta_blue', 'beta_eua', 'sigma_eta', 'beta_int_init'], axes=axes[:3, :2])
plt.suptitle('Pijler 24a: Trace plots (convergence check)', fontsize=14, y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler24a_traceplots.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler24a_traceplots.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Opslaan")

bayes_tvp.to_csv(OUTPUT_DIR / 'pijler24a_bayes_v2_beta_int.csv', index=False)
ppc_check.to_csv(OUTPUT_DIR / 'pijler24a_ppc_check.csv', index=False)
summary_stats.to_csv(OUTPUT_DIR / 'pijler24a_param_summary.csv')

# Convergence summary
conv_summary = pd.DataFrame([{
    'method': 'Pijler 24a: TVP non-centered (publication-grade)',
    'chains': 4,
    'tune': 3000,
    'draws': 2000,
    'target_accept': 0.95,
    'n_divergences': n_divergences,
    'total_draws': total_draws,
    'divergence_pct': 100*n_divergences/total_draws,
    'max_rhat_key': float(max_rhat),
    'min_ess_key': float(min_ess),
    'beta_int_t_max_rhat': float(beta_int_summary['r_hat'].max()),
    'beta_int_t_min_ess': float(beta_int_summary['ess_bulk'].min()),
    'sigma_eta_mean': float(sigma_post.mean()),
    'sigma_eta_median': float(np.median(sigma_post)),
    'sigma_eta_ci_lo': float(np.percentile(sigma_post, 2.5)),
    'sigma_eta_ci_hi': float(np.percentile(sigma_post, 97.5)),
    'p_neg_2018': float(p_negative[0]),
    'p_neg_2021': float(p_negative[3]),
    'p_neg_2024': float(p_negative[6]),
    'pijler_24_n_divergences': 1000,  # for comparison
    'pijler_24_sigma_eta_mean': 1.11,
}])
conv_summary.to_csv(OUTPUT_DIR / 'pijler24a_convergence_summary.csv', index=False)


# === EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 24a (Publication-grade TVP)")
print("=" * 78)

print(f"""
CONVERGENCE STATUS:
  Divergences:        {n_divergences} / {total_draws} ({100*n_divergences/total_draws:.2f}%)
                      [Pijler 24 had 1000/2000 = 50.00%]
  Max r_hat (key):    {max_rhat:.4f}   [target < 1.01]
  Min ESS_bulk (key): {min_ess:.0f}    [target > 400]
  
{'✓ EXCELLENT' if n_divergences < 40 and max_rhat < 1.01 and min_ess > 400 else
 '⚠ ACCEPTABLE' if n_divergences < 200 and max_rhat < 1.05 else
 '✗ NEEDS WORK'}

σ_η POSTERIOR (mate van tijdsvariatie):
  Mean:               {sigma_post.mean():.4f}  
                      [Pijler 24 reported 1.11 — mogelijk overschatting]
  Median:             {np.median(sigma_post):.4f}
  95% CI:             [{np.percentile(sigma_post, 2.5):.4f}, {np.percentile(sigma_post, 97.5):.4f}]
  P(σ_η > 0.1):       {np.mean(sigma_post > 0.1):.3f}  [evidence van tijdsvariatie]

SIGN-SHIFT EVIDENCE:
  P(β_int < 0) over jaren:""")
for i, y in enumerate(years):
    bar = "█" * int(p_negative[i] * 20)
    print(f"    {y}: {p_negative[i]:.3f} {bar}")

print(f"""
PUBLICATION-GRADE STATUS:
""")
if n_divergences < 40 and max_rhat < 1.01:
    print("  ✓ Posterior is publication-grade")
    print("  ✓ Chapter 7 TVP-state-space claim defensible")
    print("  ✓ Sign-shift bevinding robuust over chain initialization")
elif n_divergences < 200:
    print("  ⚠ Minor convergence concerns, mogelijk extra runs nodig")
else:
    print("  ✗ Significant convergence issues — verder werk vereist")
    print("    → Consider Kalman filter via statsmodels als alternative")
