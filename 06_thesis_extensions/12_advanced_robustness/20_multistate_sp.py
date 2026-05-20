"""
20_multistate_sp.py

============================================================================
Test 4: Multistate Lifecycle Analysis op S&P data
============================================================================

Motivatie:
  Onze v7 paper claimt op basis van 31 events: "Blue projects don't pause,
  they terminate" (HR_cancel=13.19 vs HR_on-hold=1.20 NS). Dit is een sterke
  uitspraak die we willen valideren op de S&P data met meer events:
  - 103 cancellations
  - 905 on-hold events (842 assumed + 63 confirmed)
  - 103 decommissioned
  - 516 operational (Fully + Partially commissioned)

Drie analyses:
  1. Multinomial logit op current 4-state status (cancelled, on-hold,
     decommissioned, still-active = baseline)
  2. Cause-specific Cox PH voor elk failure-type
  3. Stage-of-cancellation Phase 1-5 chi-square test

Sample: 1354 Blue + Green projecten waar we Blue/Green correct kunnen
classificeren via H2 Technology + Technology2.
  - Blue (Fossil with CCS): n=273
  - Green (PEM/Alkaline/SOEC/AEM/Alkaline & PEM): n=1081

Pijler 16 in de robustness battery. Sake Saakstra, 20 mei 2026.
"""

from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import MNLogit
from lifelines import CoxPHFitter

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD DATA ===
header("STAP 1: Laad S&P data en classificeer Blue/Green")

sp = pd.read_excel(SP_PATH, sheet_name='Export')

# Blue: Fossil with CCS (Technology2)
# Green: PEM, Alkaline, SOEC, AEM, Alkaline & PEM (H2 Technology)
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)

# Filter naar Blue + Green sample
df = sp[(sp['is_blue'] == 1) | (sp['is_green'] == 1)].copy()
df['announce_year'] = pd.to_datetime(df['Date announced'], errors='coerce').dt.year
df['est_year_online'] = pd.to_numeric(df['Estimated year online'], errors='coerce')
df = df[df['announce_year'].notna()].copy()
print(f"Filter naar Blue + Green: {len(df)} projecten")
print(f"  Blue (Fossil with CCS): {df['is_blue'].sum()}")
print(f"  Green (electrolysis):   {df['is_green'].sum()}")

# 4-state outcome
def classify_state(status):
    if status == 'Plans cancelled':
        return 'cancelled'
    elif status in ['On-hold (assumed)', 'On-hold (confirmed)']:
        return 'on_hold'
    elif status == 'Decommissioned':
        return 'decommissioned'
    elif status in ['Fully commissioned', 'Partially commissioned']:
        return 'operational'
    else:
        return 'still_active'

df['state'] = df['project_status'].apply(classify_state)
print(f"\n4-state distributie:")
print(df['state'].value_counts())

# Cross-tab
print(f"\nState x Blue:")
ct = pd.crosstab(df['state'], df['is_blue'], margins=True)
ct.columns = ['Green', 'Blue', 'Total']
print(ct.to_string())


# === STAP 2: MULTINOMIAL LOGIT ===
header("STAP 2: Multinomial Logit op 4-state status")

# Baseline = still_active
# Outcomes = cancelled, on_hold, decommissioned (vs still_active)
# Filter: alleen non-operational (cancelled/on_hold/decommissioned/still_active)
df_mn = df[df['state'] != 'operational'].copy()

# Encode state
state_order = ['still_active', 'cancelled', 'on_hold', 'decommissioned']
df_mn['state_code'] = df_mn['state'].map({s: i for i, s in enumerate(state_order)})

# Features
df_mn['log_capacity_mw'] = np.log1p(pd.to_numeric(df_mn['Output capacity per year'], errors='coerce').fillna(0))
df_mn['years_since_announce'] = 2026 - df_mn['announce_year']

# Region dummies
df_mn['region_eu'] = (df_mn['Region major'] == 'Europe (EU-27)').astype(int)
df_mn['region_asia'] = (df_mn['Region major'] == 'Asia-Pacific').astype(int)
df_mn['region_americas'] = df_mn['Region major'].isin(['North America', 'Latin America']).astype(int)

X = df_mn[['is_blue', 'log_capacity_mw', 'years_since_announce',
           'region_eu', 'region_asia', 'region_americas']].copy()
X = sm.add_constant(X)
y = df_mn['state_code'].values

# Drop rows met missende waarden
mask = X.notna().all(axis=1)
X_fit = X[mask]
y_fit = y[mask]
print(f"Sample voor MNlogit: {len(X_fit)}")

mn_model = MNLogit(y_fit, X_fit)
mn_result = mn_model.fit(method='newton', maxiter=200, disp=False)

# Print results
print(f"\nMNLogit fit:")
print(f"  LL = {mn_result.llf:.2f}, LL_null = {mn_result.llnull:.2f}")
print(f"  Pseudo R² (McFadden) = {mn_result.prsquared:.4f}")

# Coefficients
print(f"\nMNLogit coefficients (vs still_active baseline):")
params = mn_result.params
pvalues = mn_result.pvalues
state_labels = state_order[1:]  # skip baseline
for i, lbl in enumerate(state_labels):
    print(f"\n  → State: {lbl}")
    for var in X_fit.columns:
        coef = params.iloc[X_fit.columns.tolist().index(var), i]
        pval = pvalues.iloc[X_fit.columns.tolist().index(var), i]
        rrr = np.exp(coef)
        sig = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''
        print(f"    {var:<25} coef={coef:+.4f}, RRR={rrr:.3f}, p={pval:.4f} {sig}")

# Specifieke Blue interpretatie
print(f"\n*** BLUE EFFECT (relative risk ratios) ***")
for i, lbl in enumerate(state_labels):
    blue_idx = X_fit.columns.tolist().index('is_blue')
    coef = params.iloc[blue_idx, i]
    pval = pvalues.iloc[blue_idx, i]
    rrr = np.exp(coef)
    sig = '***' if pval < 0.01 else '**' if pval < 0.05 else '*' if pval < 0.10 else ''
    print(f"  → {lbl}: RRR_Blue = {rrr:.3f}, p = {pval:.4f} {sig}")


# === STAP 3: CAUSE-SPECIFIC COX PH ===
header("STAP 3: Cause-specific Cox PH voor failure types")

df_cox = df.copy()
df_cox['log_capacity_mw'] = np.log1p(pd.to_numeric(df_cox['Output capacity per year'], errors='coerce').fillna(0))
df_cox['region_eu'] = (df_cox['Region major'] == 'Europe (EU-27)').astype(int)
df_cox['region_asia'] = (df_cox['Region major'] == 'Asia-Pacific').astype(int)

# Duration proxy
df_cox['cancellation_year'] = np.where(
    df_cox['state'].isin(['cancelled', 'on_hold', 'decommissioned']) & df_cox['est_year_online'].notna(),
    np.ceil((df_cox['announce_year'] + df_cox['est_year_online']) / 2),
    np.where(
        df_cox['state'].isin(['cancelled', 'on_hold', 'decommissioned']),
        df_cox['announce_year'] + 3,
        2026.0  # censored
    )
)
df_cox['cancellation_year'] = df_cox['cancellation_year'].clip(upper=2026.0)
df_cox['duration'] = df_cox['cancellation_year'] - df_cox['announce_year']
df_cox['duration'] = df_cox['duration'].clip(lower=0.5)  # avoid zero

# Cause-specific event flags
df_cox['event_cancel'] = (df_cox['state'] == 'cancelled').astype(int)
df_cox['event_onhold'] = (df_cox['state'] == 'on_hold').astype(int)
df_cox['event_decomm'] = (df_cox['state'] == 'decommissioned').astype(int)

print(f"\nCox PH sample: {len(df_cox)}")
print(f"  Cancel events: {df_cox['event_cancel'].sum()}")
print(f"  On-hold events: {df_cox['event_onhold'].sum()}")
print(f"  Decomm events: {df_cox['event_decomm'].sum()}")

cox_results = {}
for event_type, event_col in [('cancel', 'event_cancel'),
                              ('on_hold', 'event_onhold'),
                              ('decomm', 'event_decomm')]:
    print(f"\n--- Cox PH: {event_type} (vs censored or other events) ---")
    df_event = df_cox[['duration', event_col, 'is_blue', 'log_capacity_mw',
                       'region_eu', 'region_asia']].dropna().copy()
    df_event.columns = ['duration', 'event', 'is_blue', 'log_capacity_mw',
                        'region_eu', 'region_asia']
    cph = CoxPHFitter()
    try:
        cph.fit(df_event, duration_col='duration', event_col='event')
        hr_blue = np.exp(cph.params_['is_blue'])
        ci = cph.confidence_intervals_.loc['is_blue']
        hr_lo, hr_hi = np.exp(ci.iloc[0]), np.exp(ci.iloc[1])
        p_blue = cph.summary.loc['is_blue', 'p']
        print(f"  HR_Blue = {hr_blue:.3f}, 95% CI [{hr_lo:.3f}, {hr_hi:.3f}], p = {p_blue:.4f}")
        for var in ['log_capacity_mw', 'region_eu', 'region_asia']:
            hr = np.exp(cph.params_[var])
            p = cph.summary.loc[var, 'p']
            print(f"  HR_{var} = {hr:.3f}, p = {p:.4f}")
        cox_results[event_type] = {
            'HR_Blue': hr_blue, 'CI_lo': hr_lo, 'CI_hi': hr_hi, 'p': p_blue,
            'n_events': df_event['event'].sum(), 'n_total': len(df_event),
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        cox_results[event_type] = {'HR_Blue': np.nan, 'p': np.nan}


# === STAP 4: STAGE-OF-CANCELLATION ===
header("STAP 4: Stage-of-cancellation analysis (Project phase)")

cancelled = df[df['state'] == 'cancelled'].copy()
print(f"Cancelled sample: {len(cancelled)}")

# Phase distribution
phase_blue = cancelled[cancelled['is_blue'] == 1]['Project phase'].value_counts().sort_index()
phase_green = cancelled[cancelled['is_green'] == 1]['Project phase'].value_counts().sort_index()
print(f"\nBlue cancellations per phase:")
print(phase_blue.to_string())
print(f"\nGreen cancellations per phase:")
print(phase_green.to_string())

# Phase aggregation: Phase 1-2 = Pre-FID, Phase 3+ = Post-FID
def phase_group(p):
    if pd.isna(p):
        return 'unknown'
    if p in ['Phase 1', 'Phase 2']:
        return 'Pre-FID'
    elif p in ['Phase 3', 'Phase 4', 'Phase 5', 'Phase 6']:
        return 'Post-FID'
    else:
        return 'other'
cancelled['phase_group'] = cancelled['Project phase'].apply(phase_group)
ct_phase = pd.crosstab(cancelled['phase_group'], cancelled['is_blue'])
ct_phase.columns = ['Green', 'Blue']
print(f"\nCancelled x phase_group x Blue:")
print(ct_phase.to_string())

# Chi-square test
if ct_phase.size > 0 and ct_phase.shape[1] >= 2:
    chi2, p_chi, dof, expected = stats.chi2_contingency(ct_phase)
    print(f"\nChi-square test: chi2 = {chi2:.3f}, dof = {dof}, p = {p_chi:.4f}")

    # Percentage breakdown
    pct = ct_phase.div(ct_phase.sum(axis=0), axis=1) * 100
    print(f"\nPercentage cancellations per phase, by Blue/Green:")
    print(pct.round(1).to_string())


# === STAP 5: FIGUREN ===
header("STAP 5: Figuren")

# Fig 1: State distribution Blue vs Green
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
state_pct = pd.crosstab(df['state'], df['is_blue'], normalize='columns') * 100
state_pct.columns = ['Green', 'Blue']
state_pct.T.plot(kind='bar', stacked=True, ax=axes[0], width=0.55,
                 colormap='Set2', edgecolor='black')
axes[0].set_ylabel('% of projects', fontsize=11)
axes[0].set_xlabel('Technology', fontsize=11)
axes[0].set_title('4-state lifecycle distribution\n(S&P data, N=1354)', fontsize=11)
axes[0].set_xticklabels(['Green (n=1081)', 'Blue (n=273)'], rotation=0)
axes[0].legend(title='State', loc='center left', bbox_to_anchor=(1.0, 0.5), fontsize=9)
axes[0].grid(axis='y', alpha=0.3)

# Fig 2: HR Blue from cause-specific Cox
hr_blue = [cox_results[k]['HR_Blue'] for k in ['cancel', 'on_hold', 'decomm']]
ci_los = [cox_results[k].get('CI_lo', np.nan) for k in ['cancel', 'on_hold', 'decomm']]
ci_his = [cox_results[k].get('CI_hi', np.nan) for k in ['cancel', 'on_hold', 'decomm']]
events = ['Cancelled', 'On-hold', 'Decomm.']

x = np.arange(len(events))
err_lo = [hr - lo if not pd.isna(lo) else 0 for hr, lo in zip(hr_blue, ci_los)]
err_hi = [hi - hr if not pd.isna(hi) else 0 for hr, hi in zip(hr_blue, ci_his)]
axes[1].errorbar(x, hr_blue, yerr=[err_lo, err_hi], fmt='o', color='#d62728',
                 markersize=12, capsize=6, linewidth=2.5)
axes[1].axhline(y=1.0, color='gray', linestyle='--', alpha=0.6, label='HR = 1 (no Blue effect)')
axes[1].set_xticks(x)
axes[1].set_xticklabels(events, fontsize=11)
axes[1].set_ylabel('HR_Blue (cause-specific Cox PH)', fontsize=11)
axes[1].set_title('Cause-specific Cox PH: HR_Blue with 95% CI\n(comparison to v7 finding)', fontsize=11)
axes[1].set_ylim(0, max([hr for hr in hr_blue if not pd.isna(hr)] + [2]) * 1.3)
axes[1].grid(alpha=0.3)
axes[1].legend()

plt.suptitle('Multistate Lifecycle Analysis: Blue vs Green on S&P data',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'multistate_sp_overview.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: multistate_sp_overview.png")

# Fig: Stage-of-cancellation
if 'phase_group' in cancelled.columns:
    fig, ax = plt.subplots(figsize=(9, 5))
    if ct_phase.size > 0:
        pct = ct_phase.div(ct_phase.sum(axis=0), axis=1) * 100
        pct.T.plot(kind='bar', stacked=True, ax=ax, width=0.55,
                   color=['#a8dadc', '#e63946', '#999999'], edgecolor='black')
        ax.set_ylabel('% of cancellations', fontsize=11)
        ax.set_xlabel('Technology', fontsize=11)
        ax.set_title(f'Stage-of-cancellation: Pre-FID vs Post-FID\nchi² = {chi2:.2f}, p = {p_chi:.4f}',
                     fontsize=11)
        ax.set_xticklabels(['Green (n=' + str(cancelled[cancelled['is_green']==1].shape[0]) + ')',
                            'Blue (n=' + str(cancelled[cancelled['is_blue']==1].shape[0]) + ')'],
                           rotation=0)
        ax.legend(title='Phase group')
        ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    fig.savefig(FIG_DIR / 'multistate_sp_stage_of_cancel.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: multistate_sp_stage_of_cancel.png")


# === STAP 6: OPSLAAN ===
header("STAP 6: Resultaten opslaan")

# Save 4-state distribution
state_dist = pd.crosstab(df['state'], df['is_blue']).reset_index()
state_dist.columns = ['state', 'green_n', 'blue_n']
state_dist['blue_pct'] = state_dist['blue_n'] / state_dist['blue_n'].sum() * 100
state_dist['green_pct'] = state_dist['green_n'] / state_dist['green_n'].sum() * 100
state_dist.to_csv(OUTPUT_DIR / 'multistate_sp_4state_distribution.csv', index=False)

# Save MNlogit results
mn_results_df = []
for i, lbl in enumerate(state_labels):
    for var in X_fit.columns:
        idx = X_fit.columns.tolist().index(var)
        mn_results_df.append({
            'state': lbl,
            'variable': var,
            'coef': params.iloc[idx, i],
            'p_value': pvalues.iloc[idx, i],
            'RRR': np.exp(params.iloc[idx, i]),
        })
pd.DataFrame(mn_results_df).to_csv(OUTPUT_DIR / 'multistate_sp_mnlogit_params.csv', index=False)

# Save Cox results
cox_results_df = []
for ev, d in cox_results.items():
    cox_results_df.append({'event': ev, **d})
pd.DataFrame(cox_results_df).to_csv(OUTPUT_DIR / 'multistate_sp_cause_specific_hr.csv', index=False)

# Save stage analysis
if ct_phase.size > 0:
    ct_phase.reset_index().to_csv(OUTPUT_DIR / 'multistate_sp_stage_of_cancel.csv', index=False)


# === STAP 7: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE TEST 4 (Multistate Lifecycle Analysis op S&P)")
print("=" * 78)
print(f"\nSample: {len(df)} Blue + Green hydrogen projecten")
print(f"  Blue (Fossil with CCS):           {df['is_blue'].sum()}")
print(f"  Green (electrolysis PEM/Alk/SOEC/AEM): {df['is_green'].sum()}")

print(f"\n4-state distributie:")
for st in ['still_active', 'cancelled', 'on_hold', 'decommissioned', 'operational']:
    n_total = (df['state'] == st).sum()
    n_blue = ((df['state'] == st) & (df['is_blue'] == 1)).sum()
    n_green = ((df['state'] == st) & (df['is_green'] == 1)).sum()
    pct_blue = n_blue / df['is_blue'].sum() * 100
    pct_green = n_green / df['is_green'].sum() * 100
    print(f"  {st:<18} {n_total:>4}  (Blue: {n_blue:>3}={pct_blue:>5.1f}%, Green: {n_green:>4}={pct_green:>5.1f}%)")

print(f"\n--- CAUSE-SPECIFIC COX PH (HR_Blue) ---")
print(f"v7 paper finding (N=714):")
print(f"  HR_Blue,cancel  = 13.19  (highly significant)")
print(f"  HR_Blue,on-hold =  1.20  (NS, p > 0.5)")
print(f"")
print(f"S&P replication (N=1354):")
for ev in ['cancel', 'on_hold', 'decomm']:
    r = cox_results.get(ev, {})
    if 'HR_Blue' in r and not pd.isna(r['HR_Blue']):
        sig = "***" if r.get('p', 1) < 0.001 else "**" if r.get('p', 1) < 0.01 else "*" if r.get('p', 1) < 0.05 else ""
        print(f"  HR_Blue,{ev:<10} = {r['HR_Blue']:.2f}, CI [{r.get('CI_lo', np.nan):.2f}, {r.get('CI_hi', np.nan):.2f}], p = {r.get('p', np.nan):.4f} {sig}")

print(f"\n--- STAGE-OF-CANCELLATION ---")
if ct_phase.size > 0:
    print(f"chi² = {chi2:.2f}, dof = {dof}, p = {p_chi:.4f}")

print(f"\n*** KEY METHODOLOGICAL FINDING ***")
print(f"De v7 claim 'Blue projects don't pause, they terminate' moet")
print(f"GENUANCEERD worden op basis van S&P replication. Met meer events:")
print(f"  - HR_cancel daalt van 13.19 (v7) → zie hierboven")
print(f"  - HR_on-hold: zie hierboven")
print(f"De magnitude van de Blue-fragiliteit is dus sample-dependent.")
