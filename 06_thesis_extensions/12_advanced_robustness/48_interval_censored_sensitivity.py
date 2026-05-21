"""
48_interval_censored_sensitivity.py

============================================================================
Pijler 48: Interval-censored event-timing sensitivity analysis
============================================================================

Reference:
  Sun, Jianguo (2006), "The Statistical Analysis of Interval-Censored Failure
  Time Data", Springer.

  Cox, David R. (1972), "Regression Models and Life-Tables", JRSS-B 34: 187-202.

  Klein, John P. and Melvin L. Moeschberger (2003), "Survival Analysis:
  Techniques for Censored and Truncated Data", 2nd ed., Springer.

Motivation:
  De S&P database registreert project_status maar geen exacte event-datum
  voor cancellation, on-hold, of decommissioning transities. Pijler 20
  (Master Cox PH) gebruikt de approximatie

    event_year = ceil((announce_year + est_year_online) / 2)  if event=1,
                 of  announce_year + 3                          als default,
                 of  2026 (snapshot)                            als geen event.

  Deze midpoint-imputation is methodologisch reasonable maar arbitrair. De
  reviewer (mei 2026) wees expliciet op event-timing als methodologisch
  zorgpunt voor survival modelling met sparse-event data.

  Pijler 48 voert een rigoureuze interval-censored sensitivity uit:
    1. Earliest assumption: event_year = announce_year + 0.5 (vroegst mogelijk)
    2. Midpoint assumption: huidige benadering (replica van Pijler 20)
    3. Latest assumption: event_year = min(est_year_online, 2026) (uiterlijk)

  Voor elke timing-assumptie wordt de master Cox PH herschat en vergeleken
  op HR_Blue,cancel, 95% CI, Schoenfeld PH test, en concordance index.

  Indien de hazard-ratio en sign-direction stabiel zijn over de drie scenarios,
  is de substantieve interpretatie robust onder event-timing uncertainty.
  Indien niet, moet de interpretation expliciet gequalificeerd worden.

  Optioneel (V2): Turnbull NPMLE of interval-censored Cox PH via lifelines.

Auteur: Sake Saakstra, 21 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_RAW = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_YEAR = 2026

FAILURE_STATES = ['Plans cancelled', 'On-hold (assumed)', 'On-hold (confirmed)', 'Decommissioned']
BLUE_TECH = ['Fossil with CCS']
GREEN_TECH = ['Electrolysis']

def hdr(t):
    print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD S&P data
# ============================================================================
hdr("Step 1: Load S&P 24-03-2026 data + filter Blue/Green")

df_raw = pd.read_excel(SP_RAW)
print(f"S&P raw: {len(df_raw)} projects")

# Identify columns
status_col = 'project_status' if 'project_status' in df_raw.columns else 'Project status major'
ann_col = 'Year announced'
online_col = 'Estimated year online'
tech_col = 'Technology2' if 'Technology2' in df_raw.columns else 'H2 Technology'
cap_col = 'Output capacity per year'
region_col = 'Region major'

# Sample: Blue (Fossil+CCS) + Green (Electrolysis)
df = df_raw[df_raw[tech_col].isin(BLUE_TECH + GREEN_TECH)].copy()
df['is_blue'] = df[tech_col].isin(BLUE_TECH).astype(int)
df['announce_year'] = pd.to_numeric(df[ann_col], errors='coerce')
df['est_year_online'] = pd.to_numeric(df[online_col], errors='coerce')
df['failed'] = df[status_col].isin(FAILURE_STATES).astype(int)

# Drop rows without announce year
df = df.dropna(subset=['announce_year'])
df['announce_year'] = df['announce_year'].astype(int)
df = df[df['announce_year'] >= 2010]
print(f"Filtered Blue+Green with valid announce_year >= 2010: {len(df)} projects "
      f"({df['is_blue'].sum()} Blue + {(df['is_blue']==0).sum()} Green)")
print(f"  Total failure events: {df['failed'].sum()}")
print(f"  With est_year_online: {df['est_year_online'].notna().sum()} of {len(df)}")

# Covariates
df['log_capacity'] = np.log1p(pd.to_numeric(df[cap_col], errors='coerce').fillna(0))
df['region_eu'] = (df[region_col] == 'Europe (EU-27)').astype(int)
df['region_na'] = (df[region_col] == 'North America').astype(int)
df['region_asia'] = (df[region_col] == 'Asia-Pacific').astype(int)


# ============================================================================
# 2. CONSTRUCT THREE EVENT-TIMING ASSUMPTIONS
# ============================================================================
hdr("Step 2: Three event-timing scenarios — earliest / midpoint / latest")

def event_year_earliest(row):
    """Earliest possible event year: just after announcement (lower bound)."""
    if row['failed'] == 0:
        return float(SNAPSHOT_YEAR)
    return float(row['announce_year']) + 0.5  # vroegst mogelijk

def event_year_midpoint(row):
    """Current Pijler 20 approach: midpoint between announce and est_online."""
    if row['failed'] == 0:
        return float(SNAPSHOT_YEAR)
    if pd.notna(row['est_year_online']):
        return float(np.ceil((row['announce_year'] + row['est_year_online']) / 2))
    return float(row['announce_year']) + 3.0

def event_year_latest(row):
    """Latest possible event year: at expected online, or snapshot."""
    if row['failed'] == 0:
        return float(SNAPSHOT_YEAR)
    if pd.notna(row['est_year_online']):
        # Event must precede or coincide with planned online (could be cancelled at online date)
        return float(min(row['est_year_online'], SNAPSHOT_YEAR))
    return float(SNAPSHOT_YEAR)  # max upper bound: snapshot year

for scenario, fn in [('earliest', event_year_earliest),
                     ('midpoint', event_year_midpoint),
                     ('latest', event_year_latest)]:
    df[f'event_year_{scenario}'] = df.apply(fn, axis=1)
    df[f'duration_{scenario}'] = (df[f'event_year_{scenario}'] - df['announce_year']).clip(lower=0.5)

print("Duration distribution per scenario (years):")
for s in ['earliest', 'midpoint', 'latest']:
    d = df[df['failed']==1][f'duration_{s}']
    print(f"  {s}: mean={d.mean():.2f}, median={d.median():.2f}, "
          f"min={d.min():.2f}, max={d.max():.2f}")


# ============================================================================
# 3. COX PH FIT UNDER EACH SCENARIO
# ============================================================================
hdr("Step 3: Cox PH regression under each timing scenario")

covariates = ['is_blue', 'log_capacity', 'region_eu', 'region_na', 'region_asia']

results = []
for s in ['earliest', 'midpoint', 'latest']:
    fit_df = df[['failed', f'duration_{s}'] + covariates].copy()
    fit_df = fit_df.rename(columns={f'duration_{s}': 'duration'}).dropna()
    cph = CoxPHFitter()
    try:
        cph.fit(fit_df, duration_col='duration', event_col='failed', show_progress=False)
        summary = cph.summary
        # Extract Blue coefficient
        row = summary.loc['is_blue']
        hr = row['exp(coef)']
        ci_lo = row['exp(coef) lower 95%']
        ci_hi = row['exp(coef) upper 95%']
        pval = row['p']
        # Schoenfeld PH test
        try:
            ph_test = cph.check_assumptions(fit_df, p_value_threshold=0.05, show_plots=False)
            ph_blue_p = ph_test[0].summary.loc[('is_blue', 'km'), 'p'] if len(ph_test) > 0 else np.nan
        except Exception:
            ph_blue_p = np.nan
        # Concordance index
        cindex = cph.concordance_index_
        n_events = int(fit_df['failed'].sum())
        n_obs = int(len(fit_df))
        results.append({
            'scenario': s,
            'n_obs': n_obs,
            'n_events': n_events,
            'HR_Blue': hr,
            'CI_lo': ci_lo,
            'CI_hi': ci_hi,
            'p_Blue': pval,
            'PH_p_Blue': ph_blue_p,
            'concordance': cindex,
        })
        print(f"\n  {s.upper()}: n={n_obs}, events={n_events}")
        print(f"    HR_Blue = {hr:.3f} [{ci_lo:.3f}, {ci_hi:.3f}], p = {pval:.4f}")
        ph_str = f'{ph_blue_p:.4f}' if not np.isnan(ph_blue_p) else 'NA'
        print(f'    PH test p (Blue) = {ph_str}')
        print(f"    Concordance = {cindex:.3f}")
    except Exception as e:
        print(f"  {s.upper()}: FAILED — {e}")
        results.append({'scenario': s, 'error': str(e)})

results_df = pd.DataFrame(results)
results_df.to_csv(OUTPUT_DIR / "pijler48_timing_sensitivity.csv", index=False)


# ============================================================================
# 4. PER-OUTCOME DECOMPOSITION (Cancel only vs On-hold only vs Pooled)
# ============================================================================
hdr("Step 4: Decomposition — cancel-only vs on-hold-only vs pooled")

outcome_groups = {
    'cancel_only':  ['Plans cancelled'],
    'onhold_only':  ['On-hold (assumed)', 'On-hold (confirmed)'],
    'decomm_only':  ['Decommissioned'],
    'all_failure':  FAILURE_STATES,
}

decomp_results = []
for outcome_name, states in outcome_groups.items():
    df['failed_outcome'] = df[status_col].isin(states).astype(int)
    n_events = df['failed_outcome'].sum()
    if n_events < 20:
        print(f"  {outcome_name}: only {n_events} events — skipping")
        continue
    for s in ['earliest', 'midpoint', 'latest']:
        fit_df = df[['failed_outcome', f'duration_{s}'] + covariates].copy()
        fit_df = fit_df.rename(columns={f'duration_{s}': 'duration'}).dropna()
        cph = CoxPHFitter()
        try:
            cph.fit(fit_df, duration_col='duration', event_col='failed_outcome', show_progress=False)
            row = cph.summary.loc['is_blue']
            decomp_results.append({
                'outcome': outcome_name,
                'scenario': s,
                'n_events': int(n_events),
                'HR_Blue': row['exp(coef)'],
                'CI_lo': row['exp(coef) lower 95%'],
                'CI_hi': row['exp(coef) upper 95%'],
                'p_Blue': row['p'],
            })
        except Exception as e:
            print(f"  {outcome_name} × {s}: failed — {e}")

decomp_df = pd.DataFrame(decomp_results)
decomp_df.to_csv(OUTPUT_DIR / "pijler48_outcome_decomposition.csv", index=False)
print("\nPer-outcome × per-scenario HR_Blue summary:")
print(decomp_df.to_string(index=False))


# ============================================================================
# 5. FIGURE: HR_Blue under three scenarios + outcome decomposition
# ============================================================================
hdr("Step 5: Figure — sensitivity visualization")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Panel A: pooled hazard ratio over scenarios
ax = axes[0]
scenarios = ['earliest', 'midpoint', 'latest']
x_pos = np.arange(len(scenarios))
hrs = [results_df[results_df['scenario'] == s]['HR_Blue'].iloc[0] for s in scenarios]
lo = [results_df[results_df['scenario'] == s]['CI_lo'].iloc[0] for s in scenarios]
hi = [results_df[results_df['scenario'] == s]['CI_hi'].iloc[0] for s in scenarios]
ax.errorbar(x_pos, hrs, yerr=[np.array(hrs)-np.array(lo), np.array(hi)-np.array(hrs)],
            fmt='o', markersize=10, capsize=8, color='#1f77b4', linewidth=2)
ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5, label='HR = 1 (no effect)')
ax.set_xticks(x_pos); ax.set_xticklabels([s.capitalize() for s in scenarios])
ax.set_ylabel('HR$_{\\mathrm{Blue}}$ (any failure)')
ax.set_title('A. Pooled HR$_{\\mathrm{Blue}}$ under event-timing scenarios')
ax.grid(True, alpha=0.3)
ax.legend()

# Panel B: per-outcome decomposition
ax = axes[1]
outcomes = ['cancel_only', 'onhold_only', 'decomm_only', 'all_failure']
outcomes_present = [o for o in outcomes if o in decomp_df['outcome'].values]
colors = {'earliest': '#1f77b4', 'midpoint': '#ff7f0e', 'latest': '#2ca02c'}
width = 0.25
for i, s in enumerate(scenarios):
    sub = decomp_df[decomp_df['scenario'] == s].set_index('outcome').reindex(outcomes_present)
    x = np.arange(len(outcomes_present)) + (i - 1) * width
    ax.bar(x, sub['HR_Blue'], width=width,
           yerr=[sub['HR_Blue'] - sub['CI_lo'], sub['CI_hi'] - sub['HR_Blue']],
           label=s.capitalize(), color=colors[s], alpha=0.85, capsize=4)
ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
ax.set_xticks(np.arange(len(outcomes_present)))
ax.set_xticklabels([o.replace('_', '\n') for o in outcomes_present], fontsize=9)
ax.set_ylabel('HR$_{\\mathrm{Blue}}$')
ax.set_title('B. Per-outcome decomposition')
ax.legend(title='Scenario')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / "pijler48_timing_sensitivity.pdf", bbox_inches='tight')
plt.savefig(FIG_DIR / "pijler48_timing_sensitivity.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Figure saved: {FIG_DIR / 'pijler48_timing_sensitivity.pdf'}")


# ============================================================================
# 6. SUMMARY
# ============================================================================
hdr("Step 6: Summary — robustness of HR_Blue across timing assumptions")

print("\nPooled HR_Blue across three scenarios:")
for r in results:
    if 'HR_Blue' in r:
        print(f"  {r['scenario'].upper():10s}: HR = {r['HR_Blue']:.3f} "
              f"[{r['CI_lo']:.3f}, {r['CI_hi']:.3f}], p = {r['p_Blue']:.4f}")

print("\nRange of HR_Blue across scenarios:")
hrs = [r['HR_Blue'] for r in results if 'HR_Blue' in r]
print(f"  min: {min(hrs):.3f}")
print(f"  max: {max(hrs):.3f}")
print(f"  range/midpoint: {(max(hrs)-min(hrs))/np.mean(hrs)*100:.1f}%")
print(f"  All scenarios statistically significant (p < 0.05): {all(r['p_Blue']<0.05 for r in results if 'p_Blue' in r)}")
print(f"  All point estimates exceed 1.0 (Blue > Green hazard): {all(r['HR_Blue']>1.0 for r in results if 'HR_Blue' in r)}")

print(f"\nOutputs:")
print(f"  {OUTPUT_DIR / 'pijler48_timing_sensitivity.csv'}")
print(f"  {OUTPUT_DIR / 'pijler48_outcome_decomposition.csv'}")
print(f"  {FIG_DIR / 'pijler48_timing_sensitivity.pdf'}")
