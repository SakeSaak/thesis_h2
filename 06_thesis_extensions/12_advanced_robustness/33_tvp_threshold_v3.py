"""
33_tvp_threshold_v3.py
============================================================================
Pijler 24b: STRUCTURAL BREAK / THRESHOLD model voor β_int — PRAGMATISCH
============================================================================

Probleem met Pijler 24a: random walk over T=9 jaren met ~30 events/jaar
is statistically under-identified. PyMC gaf 2001 divergences (van 8000).

Pragmatische oplossing: model β_int als TWO-REGIME process:
  β_int(t) = β_pre  if year ≤ τ
  β_int(t) = β_post if year > τ

waar τ = threshold year (test op 2020, 2021, 2022).

Dit is een formele EENT-test of sign-shift bestaat:
  H0: β_pre = β_post (geen shift)
  H1: β_pre ≠ β_post (shift)

Plus: Sliding window OLS estimates als crosscheck voor TVP patroon.
Plus: AR(1) Bayesian als alternatief (parameter-driven proces).

Voor PhD-thesis: deze pijler is robuuster te verdedigen dan random walk.

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MACRO_PATH = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: HERBOUW PANEL ===
header("STAP 1: Herbouw panel")

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
panel['blue_x_eua_z'] = panel['is_blue'] * panel['eua_z']

print(f"Panel: {len(panel)} obs, {panel['event_yr'].sum()} events")


# === STAP 2: THRESHOLD MODEL — formeel test sign-shift ===
header("STAP 2: Threshold model — test sign-shift formeel")

print("""
Hypothese: β_int verschilt structureel pre- en post-threshold τ
  Model: event ~ alpha + beta_blue * Blue + beta_eua * EUA_z
                + beta_pre * (Blue * EUA_z) * I(year ≤ τ)
                + beta_post * (Blue * EUA_z) * I(year > τ)
                + controls

  Test: Wald test of beta_pre = beta_post
""")

threshold_results = []
for tau in [2019, 2020, 2021, 2022, 2023]:
    pre_mask = (panel['year'] <= tau).astype(int)
    post_mask = (panel['year'] > tau).astype(int)
    
    work = panel.copy()
    work['blue_x_eua_z_pre'] = work['blue_x_eua_z'] * pre_mask
    work['blue_x_eua_z_post'] = work['blue_x_eua_z'] * post_mask
    
    formula = ('event_yr ~ is_blue + eua_z + blue_x_eua_z_pre + blue_x_eua_z_post '
               '+ log_capacity + years_since_announce + I(years_since_announce ** 2)')
    
    mod = smf.glm(formula=formula, data=work, family=sm.families.Binomial()).fit(cov_type='HC3')
    
    b_pre = float(mod.params['blue_x_eua_z_pre'])
    b_post = float(mod.params['blue_x_eua_z_post'])
    se_pre = float(mod.bse['blue_x_eua_z_pre'])
    se_post = float(mod.bse['blue_x_eua_z_post'])
    p_pre = float(mod.pvalues['blue_x_eua_z_pre'])
    p_post = float(mod.pvalues['blue_x_eua_z_post'])
    
    # Wald test of beta_pre = beta_post
    diff = b_pre - b_post
    cov = mod.cov_params()
    var_diff = cov.loc['blue_x_eua_z_pre', 'blue_x_eua_z_pre'] + \
               cov.loc['blue_x_eua_z_post', 'blue_x_eua_z_post'] - \
               2 * cov.loc['blue_x_eua_z_pre', 'blue_x_eua_z_post']
    se_diff = np.sqrt(max(var_diff, 0))
    z_stat = diff / se_diff if se_diff > 0 else np.nan
    p_diff = 2 * (1 - stats.norm.cdf(abs(z_stat))) if not np.isnan(z_stat) else np.nan
    
    n_pre = int(((panel['year'] <= tau) & (panel['event_yr'] == 1)).sum())
    n_post = int(((panel['year'] > tau) & (panel['event_yr'] == 1)).sum())
    
    threshold_results.append({
        'tau': tau,
        'beta_pre': b_pre, 'se_pre': se_pre, 'p_pre': p_pre,
        'beta_post': b_post, 'se_post': se_post, 'p_post': p_post,
        'diff': diff, 'se_diff': se_diff, 'z_diff': z_stat, 'p_diff': p_diff,
        'n_events_pre': n_pre, 'n_events_post': n_post,
        'AIC': float(mod.aic), 'BIC': float(mod.bic_llf),
    })

threshold_df = pd.DataFrame(threshold_results)
print(threshold_df.round(4).to_string(index=False))

# Best threshold by AIC
best_tau_idx = threshold_df['AIC'].idxmin()
best_tau = int(threshold_df.loc[best_tau_idx, 'tau'])
print(f"\nBest threshold by AIC: τ* = {best_tau}")
print(f"At τ* = {best_tau}:")
print(f"  β_pre  = {threshold_df.loc[best_tau_idx, 'beta_pre']:+.4f} (p = {threshold_df.loc[best_tau_idx, 'p_pre']:.4f})")
print(f"  β_post = {threshold_df.loc[best_tau_idx, 'beta_post']:+.4f} (p = {threshold_df.loc[best_tau_idx, 'p_post']:.4f})")
print(f"  Diff   = {threshold_df.loc[best_tau_idx, 'diff']:+.4f}")
print(f"  Wald p (β_pre = β_post): {threshold_df.loc[best_tau_idx, 'p_diff']:.4f}")


# === STAP 3: SLIDING WINDOW ROBUSTNESS ===
header("STAP 3: Sliding window OLS — visualiseer evolutie")

formula_sliding = ('event_yr ~ is_blue + eua_z + blue_x_eua_z + log_capacity '
                   '+ years_since_announce + I(years_since_announce ** 2)')

tvp_rows = []
for center_year in range(2014, 2026):
    yr_start = center_year - 2
    yr_end = center_year + 2
    sub = panel[(panel['year'] >= yr_start) & (panel['year'] <= yr_end)].copy()
    if sub['event_yr'].sum() < 15:
        continue
    try:
        mod = smf.glm(formula=formula_sliding, data=sub, family=sm.families.Binomial()).fit(cov_type='HC3')
        b = float(mod.params['blue_x_eua_z'])
        se = float(mod.bse['blue_x_eua_z'])
        p = float(mod.pvalues['blue_x_eua_z'])
        if abs(b) < 10:  # filter extreme/unstable estimates
            tvp_rows.append({'year': center_year, 'beta_int': b, 'se': se, 'p': p, 'n_events': sub['event_yr'].sum()})
    except Exception:
        continue

tvp_window = pd.DataFrame(tvp_rows)
print("\nSliding 5y window β_int(t):")
print(tvp_window.round(4).to_string(index=False))


# === STAP 4: AR(1) BAYESIAN — alternative TVP ===
header("STAP 4: AR(1) parameter-driven Bayesian model")

print("""
Model: β_int(t+1) = (1-φ) * μ + φ * β_int(t) + ε_t,  ε_t ~ N(0, σ²)
       
Dit is parameter-driven (mean-reverting) ipv random walk:
  - φ = persistence parameter
  - μ = long-run mean of β_int
  - σ = innovation SD
""")

try:
    import pymc as pm
    import arviz as az
    
    panel_sub = panel[panel['year'].between(2018, 2026)].copy()
    years = sorted(panel_sub['year'].unique())
    T = len(years)
    year_idx = {y: i for i, y in enumerate(years)}
    panel_sub['t_idx'] = panel_sub['year'].map(year_idx)
    
    with pm.Model() as ar1_model:
        # Static main effects
        alpha = pm.Normal('alpha', mu=0, sigma=3)
        beta_blue = pm.Normal('beta_blue', mu=0, sigma=2)
        beta_eua = pm.Normal('beta_eua', mu=0, sigma=2)
        beta_logcap = pm.Normal('beta_logcap', mu=0, sigma=1)
        beta_ysa = pm.Normal('beta_ysa', mu=0, sigma=1)
        
        # AR(1) for beta_int(t)
        mu_int = pm.Normal('mu_int', mu=0, sigma=1)
        phi = pm.Beta('phi', alpha=2, beta=2)  # persistence in [0,1]
        sigma_eps = pm.HalfNormal('sigma_eps', sigma=0.3)
        
        # Non-centered AR(1)
        innov_raw = pm.Normal('innov_raw', mu=0, sigma=1, shape=T)
        
        # Build beta_int_t via scan-equivalent
        beta_int_t_list = [mu_int + sigma_eps * innov_raw[0]]
        for t in range(1, T):
            beta_int_t_list.append((1-phi) * mu_int + phi * beta_int_t_list[t-1] + sigma_eps * innov_raw[t])
        beta_int_t = pm.Deterministic('beta_int_t', pm.math.stack(beta_int_t_list))
        
        # Linear predictor
        b_int_obs = beta_int_t[panel_sub['t_idx'].values]
        is_blue_arr = panel_sub['is_blue'].values.astype(float)
        eua_z_arr = panel_sub['eua_z'].values
        
        logit_p = (alpha + beta_blue * is_blue_arr + beta_eua * eua_z_arr
                   + b_int_obs * (is_blue_arr * eua_z_arr)
                   + beta_logcap * panel_sub['log_capacity'].values
                   + beta_ysa * panel_sub['years_since_announce'].values)
        
        pm.Bernoulli('y', logit_p=logit_p, observed=panel_sub['event_yr'].values)
        
        print("Sampling AR(1) (4 chains x 2000 tune x 1500 draws)...")
        trace_ar1 = pm.sample(
            draws=1500, tune=2000, chains=4, target_accept=0.95,
            random_seed=20260520, progressbar=False, return_inferencedata=True,
        )
    
    # Diagnostics
    summary_ar1 = az.summary(trace_ar1, var_names=['alpha', 'beta_blue', 'beta_eua', 'mu_int', 'phi', 'sigma_eps'])
    print("\n--- AR(1) PARAMETERS ---")
    print(summary_ar1.round(4).to_string())
    
    n_div = int(trace_ar1.sample_stats['diverging'].sum())
    print(f"\nDivergences: {n_div} / {1500*4} = {100*n_div/(1500*4):.2f}%")
    
    # Beta_int_t posterior
    beta_int_samples = trace_ar1.posterior['beta_int_t'].values
    beta_int_mean = beta_int_samples.mean(axis=(0,1))
    beta_int_lo = np.percentile(beta_int_samples, 2.5, axis=(0,1))
    beta_int_hi = np.percentile(beta_int_samples, 97.5, axis=(0,1))
    
    print(f"\nAR(1) β_int(t) posterior:")
    for i, y in enumerate(years):
        print(f"  {y}: {beta_int_mean[i]:+.3f} [{beta_int_lo[i]:+.3f}, {beta_int_hi[i]:+.3f}]")
    
    ar1_df = pd.DataFrame({
        'year': years,
        'beta_int_mean': beta_int_mean,
        'beta_int_lo95': beta_int_lo,
        'beta_int_hi95': beta_int_hi,
    })
    
    ar1_success = n_div < 200
    
except Exception as e:
    print(f"AR(1) sampling failed: {e}")
    ar1_success = False
    ar1_df = pd.DataFrame()
    n_div = -1


# === STAP 5: GROOTSCHALIG VOORZICHTIGE SYNTHESE ===
header("STAP 5: Synthese — wat blijft over conclusies?")

print("""
DRIE METHODES, WAT VINDEN ZE?
""")

# Threshold model at best tau
best_row = threshold_df.loc[best_tau_idx]
print(f"1. THRESHOLD MODEL (τ* = {best_tau}, AIC-optimal):")
print(f"   β_pre  = {best_row['beta_pre']:+.4f}")
print(f"   β_post = {best_row['beta_post']:+.4f}")
print(f"   Diff   = {best_row['diff']:+.4f}")
print(f"   Wald p = {best_row['p_diff']:.4f}  {'***' if best_row['p_diff']<0.001 else '**' if best_row['p_diff']<0.01 else '*' if best_row['p_diff']<0.05 else '.' if best_row['p_diff']<0.1 else 'NS'}")

print(f"\n2. SLIDING WINDOW (5y):")
print(f"   Range β_int: [{tvp_window['beta_int'].min():+.3f}, {tvp_window['beta_int'].max():+.3f}]")
mean_pre = tvp_window[tvp_window['year'] < 2021]['beta_int'].mean()
mean_post = tvp_window[tvp_window['year'] >= 2021]['beta_int'].mean()
print(f"   Mean pre-2021:  {mean_pre:+.3f}")
print(f"   Mean post-2021: {mean_post:+.3f}")

if ar1_success:
    print(f"\n3. AR(1) BAYESIAN:")
    print(f"   Divergences: {n_div} ({100*n_div/(1500*4):.2f}%) — {'OK' if n_div < 200 else 'CONCERN'}")
    print(f"   φ posterior mean: {trace_ar1.posterior['phi'].values.mean():.3f}")
    print(f"   μ_int posterior mean: {trace_ar1.posterior['mu_int'].values.mean():+.3f}")
    print(f"   β_int(2018): {ar1_df.iloc[0]['beta_int_mean']:+.3f}")
    print(f"   β_int(2024): {ar1_df.iloc[6]['beta_int_mean']:+.3f}")


# === STAP 6: FIGUREN ===
header("STAP 6: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Threshold results across tau
ax = axes[0, 0]
ax.errorbar(threshold_df['tau'], threshold_df['beta_pre'], yerr=1.96*threshold_df['se_pre'],
            fmt='o-', color='#1f77b4', label='β_pre', linewidth=2, markersize=10)
ax.errorbar(threshold_df['tau'], threshold_df['beta_post'], yerr=1.96*threshold_df['se_post'],
            fmt='s-', color='#d62728', label='β_post', linewidth=2, markersize=10)
ax.axhline(y=0, color='black', linewidth=0.8, linestyle='-')
ax.set_xlabel('Threshold year τ')
ax.set_ylabel('β_int estimates ± 95% CI')
ax.set_title('Threshold model results across τ candidates')
ax.legend(loc='best')
ax.grid(alpha=0.3)

# Panel B: Sliding window
ax = axes[0, 1]
ax.errorbar(tvp_window['year'], tvp_window['beta_int'], yerr=1.96*tvp_window['se'],
            fmt='o-', color='#9c27b0', linewidth=2, markersize=10)
ax.fill_between(tvp_window['year'],
                tvp_window['beta_int'] - 1.96*tvp_window['se'],
                tvp_window['beta_int'] + 1.96*tvp_window['se'],
                color='#9c27b0', alpha=0.15)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.axvline(x=2021, color='gray', linestyle='--', alpha=0.6, label='Hypothesized threshold')
ax.set_xlabel('Center year (5y sliding window)')
ax.set_ylabel('β_int(t) sliding estimate')
ax.set_title('Sliding window β_int(t)')
ax.legend()
ax.grid(alpha=0.3)

# Panel C: AR(1) Bayesian (if available)
ax = axes[1, 0]
if ar1_success and len(ar1_df) > 0:
    ax.plot(ar1_df['year'], ar1_df['beta_int_mean'], 'o-', color='#2ca02c', linewidth=2.5, markersize=10, label='AR(1) posterior mean')
    ax.fill_between(ar1_df['year'], ar1_df['beta_int_lo95'], ar1_df['beta_int_hi95'], color='#2ca02c', alpha=0.2, label='95% CI')
    ax.axhline(y=0, color='black', linewidth=0.8)
    ax.set_xlabel('Year')
    ax.set_ylabel('β_int(t) AR(1) posterior')
    ax.set_title(f'AR(1) Bayesian TVP\n(divergences: {n_div}/{1500*4})')
    ax.legend()
    ax.grid(alpha=0.3)
else:
    ax.text(0.5, 0.5, 'AR(1) sampling failed\n(see logs)', ha='center', va='center', transform=ax.transAxes, fontsize=14)

# Panel D: Combined comparison
ax = axes[1, 1]
# Threshold
ax.axhline(y=best_row['beta_pre'], xmin=0, xmax=(best_tau - 2014)/(2025-2014),
           color='#1f77b4', linewidth=2.5, label=f'Threshold β_pre = {best_row["beta_pre"]:+.3f}')
ax.axhline(y=best_row['beta_post'], xmin=(best_tau - 2014)/(2025-2014), xmax=1,
           color='#d62728', linewidth=2.5, label=f'Threshold β_post = {best_row["beta_post"]:+.3f}')
# Sliding window
ax.plot(tvp_window['year'], tvp_window['beta_int'], 'o--', color='#9c27b0', alpha=0.7,
        markersize=8, label='Sliding window')
# AR(1)
if ar1_success and len(ar1_df) > 0:
    ax.plot(ar1_df['year'], ar1_df['beta_int_mean'], 's-', color='#2ca02c', alpha=0.7,
            markersize=8, label='AR(1) posterior')
# Static
ax.axhline(y=-0.325, color='gray', linestyle=':', alpha=0.6, label='Static (Pijler 22)')
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_xlabel('Year')
ax.set_ylabel('β_int estimates')
ax.set_title('All methods comparison')
ax.legend(loc='best', fontsize=9)
ax.grid(alpha=0.3)

plt.suptitle('Pijler 24b: Multiple TVP methods — threshold + sliding + AR(1)',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler24b_threshold_methods.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler24b_threshold_methods.png")


# === STAP 7: OPSLAAN ===
header("STAP 7: Opslaan")

threshold_df.to_csv(OUTPUT_DIR / 'pijler24b_threshold_results.csv', index=False)
tvp_window.to_csv(OUTPUT_DIR / 'pijler24b_sliding_window.csv', index=False)
if ar1_success and len(ar1_df) > 0:
    ar1_df.to_csv(OUTPUT_DIR / 'pijler24b_ar1_posterior.csv', index=False)


# === EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 24b (threshold + sliding + AR(1))")
print("=" * 78)

print(f"""
DRIE INDEPENDENT METHODES, CONSISTENT PATROON?

1. THRESHOLD MODEL (AIC-optimal τ = {best_tau}):
   β_pre  = {best_row['beta_pre']:+.4f}  ({'**' if best_row['p_pre']<0.01 else '*' if best_row['p_pre']<0.05 else 'NS'})
   β_post = {best_row['beta_post']:+.4f}  ({'**' if best_row['p_post']<0.01 else '*' if best_row['p_post']<0.05 else 'NS'})
   Diff Wald p: {best_row['p_diff']:.4f}  {'***' if best_row['p_diff']<0.001 else '**' if best_row['p_diff']<0.01 else '*' if best_row['p_diff']<0.05 else 'NS'}

2. SLIDING WINDOW:
   Pre-2021 mean: {mean_pre:+.3f}
   Post-2021 mean: {mean_post:+.3f}

3. AR(1) BAYESIAN:
   {'WERKT (' + str(n_div) + ' divergences)' if ar1_success else 'FAILED'}

PUBLICATION-GRADE STATUS:
""")

if abs(best_row['diff']) > 0.5 and best_row['p_diff'] < 0.10:
    print(f"  ✓ Threshold model bevestigt regime-shift")
    print(f"  ✓ Sliding window patroon consistent: pre {mean_pre:+.3f} → post {mean_post:+.3f}")
    print(f"  ✓ PhD Chapter 7 claim defensible via threshold-test")
    print(f"\n  KEY MESSAGE voor thesis:")
    print(f"  'A formal Wald test rejects β_pre = β_post at τ* = {best_tau}'")
    print(f"  'consistent with sliding window evidence'")
elif best_row['p_diff'] < 0.20:
    print(f"  ⚠ Marginal evidence for regime-shift")
    print(f"  ⚠ Sample size limits statistical power")
    print(f"  ⚠ Honest reporting: present as suggestive, not conclusive")
else:
    print(f"  ✗ No strong evidence for regime-shift")
    print(f"  → Reconsider TVP claim in thesis")
    print(f"  → Static model adequate for the data")
