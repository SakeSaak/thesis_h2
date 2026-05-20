"""
22_45v_three_pillars.py

============================================================================
Test 8: US 45V Three-Pillars Treasury Rules — Effect on US Green H2 Projects
============================================================================

Motivatie:
  De US Inflation Reduction Act (IRA, aug 2022) creëerde 45V tax credit:
  $3/kg voor "clean" hydrogen die <0.45 kg CO2e/kg H2 emissies heeft.
  Verwachte impact: massale uitrol US green hydrogen.

  ECHTER: Treasury proposed rules (NPRM) van 22 december 2023 introduceerden
  STRIKTE "three pillars" requirements:

  1. INCREMENTALITY (additionality): clean H2 mag alleen NIEUWE renewable
     electricity gebruiken — niet bestaande hydro/nuclear
  2. TEMPORAL MATCHING: hourly (eventueel jaarlijks tot 2030) matching tussen
     H2 productie en renewable input
  3. DELIVERABILITY: H2 productie en renewable bron moeten in dezelfde grid
     region zijn

  Industry verwachtte deze rules veel losser. De strikte rules verhogen
  drastisch de business-case complexiteit voor US green H2.

  Final rules: 3 januari 2025 (Biden Treasury), grotendeels intact gebleven
  met some flexibility — annual matching toegestaan tot 2030, dan switching
  naar hourly matching.

Hypothese:
  - US green H2 projecten ondervinden negatieve impact op project commitment
    sinds de NPRM (december 2023)
  - Cancellation hazard stijgt, on-hold hazard stijgt
  - Effect specifiek voor Green (electrolysis) projecten — Blue (Fossil+CCS)
    valt niet onder 45V three-pillars

Setup:
  - Treated: US Green H2 projecten (Region major = North America, Technology2 in
    {Electrolysis-related})
  - Control 1: Non-US Green H2 projecten (similar policy environment elders)
  - Control 2: US Blue H2 projecten (US but not affected by 45V rules)
  - Treatment times:
     * NPRM anticipation: 22 december 2023 → kalenderjaar 2024
     * Final rules: 3 januari 2025 → kalenderjaar 2025

Methodes:
  1. Difference-in-differences (3-way: time × geography × technology)
  2. Cause-specific Cox PH met TVC (45V_active dummy from 2024)
  3. Multistate analyse: US Green vs others lifecycle distribution

Auteur: Sake Saakstra, 20 mei 2026
Pijler 18 in de robustness battery
"""

from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from lifelines import CoxPHFitter

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_NPRM = 2024  # NPRM december 2023 -> kalenderjaar 2024
T_FINAL = 2025  # Final rule januari 2025 -> kalenderjaar 2025
B_BOOTSTRAP = 500
SEED = 20260520


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD DATA EN DEFINIEER GROEPEN ===
header("STAP 1: Laad S&P data en definieer 4-way groepen (Geography × Technology)")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()

# Technology classificatie
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)

# Geography
sp['is_us'] = (sp['Geography'] == 'United States').astype(int)
sp['is_na'] = (sp['Region major'] == 'North America').astype(int)
sp['is_eu'] = (sp['Region major'] == 'Europe (EU-27)').astype(int)

# 4-way classification: {US, non-US} × {Green, Blue}
def group_classify(row):
    if row['is_blue'] == 1:
        return 'US_Blue' if row['is_us'] == 1 else 'NonUS_Blue'
    elif row['is_green'] == 1:
        return 'US_Green' if row['is_us'] == 1 else 'NonUS_Green'
    else:
        return 'Other'

sp['group'] = sp.apply(group_classify, axis=1)

# Sample classifiable
df = sp[sp['group'].isin(['US_Green', 'US_Blue', 'NonUS_Green', 'NonUS_Blue'])].copy()
print(f"4-way groep verdeling:")
print(df['group'].value_counts())
print(f"\nTotaal classifiable: {len(df)}")
print(f"Treated (US_Green):    {(df['group']=='US_Green').sum()}")
print(f"Control 1 (NonUS_Green): {(df['group']=='NonUS_Green').sum()}")
print(f"Control 2 (US_Blue):    {(df['group']=='US_Blue').sum()}")
print(f"Control 3 (NonUS_Blue): {(df['group']=='NonUS_Blue').sum()}")


# === STAP 2: EVENT CLASSIFICATIE ===
header("STAP 2: Event classificatie en cancellation timing proxy")

# State definition
def classify_state(s):
    if s == 'Plans cancelled':
        return 'cancelled'
    elif s in ['On-hold (assumed)', 'On-hold (confirmed)']:
        return 'on_hold'
    elif s == 'Decommissioned':
        return 'decommissioned'
    elif s in ['Fully commissioned', 'Partially commissioned']:
        return 'operational'
    else:
        return 'still_active'

df['state'] = df['project_status'].apply(classify_state)

# Event year proxy
df['event_year'] = np.where(
    df['state'].isin(['cancelled', 'on_hold', 'decommissioned']) & df['est_year_online'].notna(),
    np.ceil((df['announce_year'] + df['est_year_online']) / 2),
    np.where(
        df['state'].isin(['cancelled', 'on_hold', 'decommissioned']),
        df['announce_year'] + 3,
        2026.0
    )
).clip(max=2026.0)

# Duration
df['duration'] = (df['event_year'] - df['announce_year']).clip(lower=0.5)

# Events
df['event_cancel'] = (df['state'] == 'cancelled').astype(int)
df['event_onhold'] = (df['state'] == 'on_hold').astype(int)
df['event_decomm'] = (df['state'] == 'decommissioned').astype(int)
df['event_any_failure'] = (df['event_cancel'] | df['event_onhold'] | df['event_decomm']).astype(int)

print(f"\nEvent counts per groep:")
event_cols = ['event_cancel', 'event_onhold', 'event_decomm', 'event_any_failure']
print(df.groupby('group')[event_cols].sum())

print(f"\nEvent rate per groep:")
n_per_group = df.groupby('group').size()
rates = df.groupby('group')[event_cols].sum().div(n_per_group, axis=0) * 100
print(rates.round(2).to_string())


# === STAP 3: 3-WAY DiD — TIME × GEOGRAPHY × TECHNOLOGY ===
header("STAP 3: 3-way Difference-in-Differences (time × geography × technology)")

# Bouw panel: project × jaar met cumulative cancellation rate per groep
panel_rows = []
for region_label, geo_filter in [('US', df['is_us']==1), ('NonUS', df['is_us']==0)]:
    for tech_label, tech_filter in [('Green', df['is_green']==1), ('Blue', df['is_blue']==1)]:
        subdf = df[geo_filter & tech_filter].copy()
        for t in range(2018, 2027):
            risk_set = subdf[subdf['announce_year'] <= t]
            if len(risk_set) == 0:
                continue
            n_cancel = ((risk_set['state']=='cancelled') &
                        (risk_set['event_year'] <= t)).sum()
            n_onhold = ((risk_set['state']=='on_hold') &
                        (risk_set['event_year'] <= t)).sum()
            n_failure = ((risk_set['state'].isin(['cancelled','on_hold','decommissioned'])) &
                         (risk_set['event_year'] <= t)).sum()
            panel_rows.append({
                'geography': region_label,
                'technology': tech_label,
                'group': f'{region_label}_{tech_label}',
                't': t,
                'n_risk_set': len(risk_set),
                'cancel_rate': n_cancel / len(risk_set),
                'onhold_rate': n_onhold / len(risk_set),
                'failure_rate': n_failure / len(risk_set),
            })

panel = pd.DataFrame(panel_rows)

# 3-way DiD estimation
# Treated: US Green
# Triple-difference: (US_Green - NonUS_Green) - (US_Blue - NonUS_Blue) before vs after
def did_3way(panel, outcome_col, t_pre_end, t_post_start, t_post_end):
    """Triple-difference: DiDD."""
    pre = panel[(panel['t'] >= 2018) & (panel['t'] <= t_pre_end)]
    post = panel[(panel['t'] >= t_post_start) & (panel['t'] <= t_post_end)]
    if len(pre) == 0 or len(post) == 0:
        return None

    def mean_per_group(d):
        return d.groupby('group')[outcome_col].mean()

    pre_m = mean_per_group(pre)
    post_m = mean_per_group(post)

    # DiD_Green = (US_Green_post - US_Green_pre) - (NonUS_Green_post - NonUS_Green_pre)
    if 'US_Green' not in pre_m.index or 'NonUS_Green' not in pre_m.index:
        return None
    did_green = (post_m.get('US_Green', np.nan) - pre_m.get('US_Green', np.nan)) - \
                (post_m.get('NonUS_Green', np.nan) - pre_m.get('NonUS_Green', np.nan))

    if 'US_Blue' in pre_m.index and 'NonUS_Blue' in pre_m.index:
        did_blue = (post_m.get('US_Blue', np.nan) - pre_m.get('US_Blue', np.nan)) - \
                   (post_m.get('NonUS_Blue', np.nan) - pre_m.get('NonUS_Blue', np.nan))
    else:
        did_blue = np.nan

    didd = did_green - did_blue if not np.isnan(did_blue) else np.nan
    return {
        'outcome': outcome_col,
        'pre_period': f'2018–{t_pre_end}',
        'post_period': f'{t_post_start}–{t_post_end}',
        'did_green': did_green,
        'did_blue': did_blue,
        'triple_diff': didd,
        'US_Green_pre': pre_m.get('US_Green', np.nan),
        'US_Green_post': post_m.get('US_Green', np.nan),
        'NonUS_Green_pre': pre_m.get('NonUS_Green', np.nan),
        'NonUS_Green_post': post_m.get('NonUS_Green', np.nan),
        'US_Blue_pre': pre_m.get('US_Blue', np.nan),
        'US_Blue_post': post_m.get('US_Blue', np.nan),
        'NonUS_Blue_pre': pre_m.get('NonUS_Blue', np.nan),
        'NonUS_Blue_post': post_m.get('NonUS_Blue', np.nan),
    }


# Test 8A: NPRM effect (t_pre_end=2023, t_post=2024-2026)
print("\n--- TEST 8A: NPRM effect (December 2023 → t* = 2024) ---")
results_8A = {}
for outcome in ['cancel_rate', 'onhold_rate', 'failure_rate']:
    r = did_3way(panel, outcome, t_pre_end=2023, t_post_start=2024, t_post_end=2026)
    if r:
        results_8A[outcome] = r
        print(f"\nOutcome: {outcome}")
        print(f"  DiD Green (US vs NonUS):     {r['did_green']:+.4f}")
        print(f"  DiD Blue  (US vs NonUS):     {r['did_blue']:+.4f}")
        print(f"  Triple difference (Green−Blue): {r['triple_diff']:+.4f}")
        print(f"  US_Green: pre={r['US_Green_pre']:.4f}, post={r['US_Green_post']:.4f}, Δ={r['US_Green_post']-r['US_Green_pre']:+.4f}")
        print(f"  NonUS_Green: pre={r['NonUS_Green_pre']:.4f}, post={r['NonUS_Green_post']:.4f}, Δ={r['NonUS_Green_post']-r['NonUS_Green_pre']:+.4f}")
        print(f"  US_Blue: pre={r['US_Blue_pre']:.4f}, post={r['US_Blue_post']:.4f}, Δ={r['US_Blue_post']-r['US_Blue_pre']:+.4f}")

# Test 8B: Final rule effect (t_pre_end=2024, t_post=2025-2026)
print("\n--- TEST 8B: Final rule effect (January 2025 → t* = 2025) ---")
results_8B = {}
for outcome in ['cancel_rate', 'onhold_rate', 'failure_rate']:
    r = did_3way(panel, outcome, t_pre_end=2024, t_post_start=2025, t_post_end=2026)
    if r:
        results_8B[outcome] = r
        print(f"\nOutcome: {outcome}")
        print(f"  DiD Green (US vs NonUS):     {r['did_green']:+.4f}")
        print(f"  DiD Blue  (US vs NonUS):     {r['did_blue']:+.4f}")
        print(f"  Triple difference (Green−Blue): {r['triple_diff']:+.4f}")


# === STAP 4: COX PH MET 45V_ACTIVE INDICATOR ===
header("STAP 4: Cause-specific Cox PH met 45V-active treatment indicator")

# Voor Cox PH: gebruik static indicator (project crosses into 2024+ era)
# Simple approach: project announced before 2024 has different exposure than after
df_cox = df.copy()
df_cox['announce_post_NPRM'] = (df_cox['announce_year'] >= T_NPRM).astype(int)
df_cox['us_green'] = ((df_cox['is_us']==1) & (df_cox['is_green']==1)).astype(int)
df_cox['us_blue'] = ((df_cox['is_us']==1) & (df_cox['is_blue']==1)).astype(int)
df_cox['log_capacity'] = np.log1p(pd.to_numeric(df_cox['Output capacity per year'], errors='coerce').fillna(0))
df_cox['years_since_announce'] = 2026 - df_cox['announce_year']

# Cox PH for each outcome with 45V interaction
print("\n--- Cause-specific Cox PH with US_Green × 45V_era interaction ---")
cox_results = {}
for event_type, event_col in [('cancel', 'event_cancel'),
                              ('on_hold', 'event_onhold'),
                              ('any_failure', 'event_any_failure')]:
    print(f"\n--- {event_type} ---")
    cox_data = df_cox[['duration', event_col, 'us_green', 'us_blue',
                       'announce_post_NPRM', 'log_capacity',
                       'years_since_announce']].dropna().copy()
    # Interactie: US_Green × post_NPRM
    cox_data['US_Green_x_postNPRM'] = cox_data['us_green'] * cox_data['announce_post_NPRM']
    cox_data.columns = [c if c != event_col else 'event' for c in cox_data.columns]

    if cox_data['event'].sum() < 20:
        print(f"  Too few events ({cox_data['event'].sum()}) — skip")
        continue

    cph = CoxPHFitter()
    try:
        cph.fit(cox_data, duration_col='duration', event_col='event')
        for var in ['us_green', 'us_blue', 'announce_post_NPRM', 'US_Green_x_postNPRM',
                    'log_capacity', 'years_since_announce']:
            if var in cph.params_.index:
                hr = np.exp(cph.params_[var])
                p = cph.summary.loc[var, 'p']
                ci_lo = np.exp(cph.confidence_intervals_.loc[var].iloc[0])
                ci_hi = np.exp(cph.confidence_intervals_.loc[var].iloc[1])
                sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else '.' if p < 0.10 else ''
                print(f"  HR_{var:<25} = {hr:.3f}, CI [{ci_lo:.3f}, {ci_hi:.3f}], p = {p:.4f} {sig}")
        cox_results[event_type] = {
            'HR_us_green': float(np.exp(cph.params_.get('us_green', np.nan))) if 'us_green' in cph.params_.index else np.nan,
            'HR_interaction': float(np.exp(cph.params_.get('US_Green_x_postNPRM', np.nan))) if 'US_Green_x_postNPRM' in cph.params_.index else np.nan,
            'p_interaction': float(cph.summary.loc['US_Green_x_postNPRM', 'p']) if 'US_Green_x_postNPRM' in cph.summary.index else np.nan,
            'n_events': int(cox_data['event'].sum()),
        }
    except Exception as e:
        print(f"  ERROR: {e}")


# === STAP 5: FIGUREN ===
header("STAP 5: Figuren")

# Fig 1: Cumulative cancellation rates per group, with vertical markers for 45V events
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
for outcome, ax, title in [('cancel_rate', ax1, 'Cumulative cancellation rate'),
                            ('onhold_rate', ax2, 'Cumulative on-hold rate')]:
    for grp, color, marker in [('US_Green', '#d62728', 'o'),
                                ('NonUS_Green', '#ff7f0e', 's'),
                                ('US_Blue', '#1f77b4', '^'),
                                ('NonUS_Blue', '#9467bd', 'D')]:
        sub = panel[panel['group'] == grp].sort_values('t')
        if len(sub) > 0:
            ax.plot(sub['t'], sub[outcome], marker + '-', color=color,
                    label=grp.replace('_', ' '), linewidth=2, markersize=6)
    ax.axvline(x=2021.6, color='gray', linestyle=':', alpha=0.6, label='IRA (aug 2022)')
    ax.axvline(x=2023.5, color='red', linestyle='--', alpha=0.6, label='45V NPRM (dec 2023)')
    ax.axvline(x=2025.0, color='darkred', linestyle='--', alpha=0.6, label='45V Final (jan 2025)')
    ax.set_xlabel('Calendar year', fontsize=11)
    ax.set_ylabel(title.replace(' rate', ' rate (fraction)'), fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.legend(loc='upper left', fontsize=8, ncol=2)
    ax.grid(alpha=0.3)
plt.suptitle('US 45V Three-Pillars Treasury Rules: effect on US Green H2 projects',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'p45v_rates_over_time.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: p45v_rates_over_time.png")

# Fig 2: 3-way DiD bar chart
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, results, title in [(axes[0], results_8A, 'TEST 8A: NPRM effect (t*=2024)'),
                            (axes[1], results_8B, 'TEST 8B: Final rule effect (t*=2025)')]:
    if not results:
        continue
    outcomes_lst = list(results.keys())
    did_green = [results[o]['did_green'] for o in outcomes_lst]
    did_blue = [results[o]['did_blue'] for o in outcomes_lst]
    triple = [results[o]['triple_diff'] for o in outcomes_lst]
    x = np.arange(len(outcomes_lst))
    w = 0.25
    ax.bar(x - w, did_green, w, label='DiD Green (US vs NonUS)', color='#d62728', edgecolor='black')
    ax.bar(x, did_blue, w, label='DiD Blue (US vs NonUS, placebo)', color='#1f77b4', edgecolor='black')
    ax.bar(x + w, triple, w, label='Triple diff (DDD)', color='#2ca02c', edgecolor='black')
    ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(outcomes_lst, fontsize=10)
    ax.set_ylabel('DiD effect on cumulative rate', fontsize=11)
    ax.set_title(title, fontsize=11)
    ax.legend(loc='best', fontsize=8)
    ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'p45v_did_estimates.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: p45v_did_estimates.png")


# === STAP 6: OPSLAAN ===
header("STAP 6: Resultaten opslaan")

# 4-way state distribution
state_dist = pd.crosstab(df['state'], df['group']).reset_index()
state_dist.to_csv(OUTPUT_DIR / 'p45v_state_distribution.csv', index=False)

# DiD results
did_rows = []
for label, results in [('NPRM_2024', results_8A), ('FinalRule_2025', results_8B)]:
    for outcome, r in results.items():
        row = {'test': label, **r}
        did_rows.append(row)
pd.DataFrame(did_rows).to_csv(OUTPUT_DIR / 'p45v_did_results.csv', index=False)

# Cox results
cox_rows = []
for ev, r in cox_results.items():
    cox_rows.append({'event': ev, **r})
pd.DataFrame(cox_rows).to_csv(OUTPUT_DIR / 'p45v_cox_results.csv', index=False)

# Panel data
panel.to_csv(OUTPUT_DIR / 'p45v_panel.csv', index=False)


# === STAP 7: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE TEST 8 (45V Three-Pillars on US Green H2)")
print("=" * 78)
print(f"\nSample: {len(df)} classifiable projecten in 4 groepen")
print(f"  US_Green:     {(df['group']=='US_Green').sum()}")
print(f"  NonUS_Green:  {(df['group']=='NonUS_Green').sum()}")
print(f"  US_Blue:      {(df['group']=='US_Blue').sum()}")
print(f"  NonUS_Blue:   {(df['group']=='NonUS_Blue').sum()}")

print(f"\n--- TEST 8A: NPRM EFFECT (t* = 2024, three-pillars proposed) ---")
for outcome, r in results_8A.items():
    sign_label = "↑ HIGHER" if r['triple_diff'] > 0 else "↓ LOWER"
    print(f"  {outcome}: triple-diff = {r['triple_diff']:+.4f}  ({sign_label})")

print(f"\n--- TEST 8B: FINAL RULE EFFECT (t* = 2025) ---")
for outcome, r in results_8B.items():
    sign_label = "↑ HIGHER" if r['triple_diff'] > 0 else "↓ LOWER"
    print(f"  {outcome}: triple-diff = {r['triple_diff']:+.4f}  ({sign_label})")

print(f"\n--- COX PH WITH US_GREEN × POST-NPRM INTERACTION ---")
for ev, r in cox_results.items():
    sig = '***' if r.get('p_interaction', 1) < 0.001 else '**' if r.get('p_interaction', 1) < 0.01 else '*' if r.get('p_interaction', 1) < 0.05 else ''
    print(f"  {ev}: HR_(US_Green × post-NPRM) = {r['HR_interaction']:.3f}, p = {r['p_interaction']:.4f} {sig}")

print("\n*** BELEIDSINTERPRETATIE ***")
print("Wanneer 45V three-pillars rules NPRM negatief effect heeft op US green H2:")
print("  - cancel_rate triple diff > 0 (US Green relatief meer cancellations)")
print("  - onhold_rate triple diff > 0 (meer on-hold)")
print("  - Cox HR > 1 voor interactie (hogere failure hazard voor late-arriving US Green)")
print("Indien triple diff ≈ 0: geen detecteerbaar 45V-effect")
