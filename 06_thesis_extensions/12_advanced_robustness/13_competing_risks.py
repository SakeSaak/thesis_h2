"""
13_competing_risks.py — Cause-Specific Cox PH voor competing risks.

Onze huidige analyse collapseert alle "events" in cancel_B (binary). Maar:
  v7:  event_type 1 (N=31, mogelijk pre-commissioning cancellation) 
       event_type 2 (N=12, mogelijk post-commissioning decommissioning)
  S&P: 13 status categorieën die op ten minste 3 outcome paden wijzen:
       1. Plans cancelled (103)
       2. Decommissioned (103) — na commissioning
       3. On-hold assumed/confirmed (949) — niet definitief gecanceld

Methode (Beyersmann-Allignol-Schumacher 2012 / Fine-Gray 1999):
  Cause-specific Cox PH: voor elk event type apart, alle andere events tellen
  als censored. Toont of de Blue-vs-PEM gap verschilt per uitkomstpad.

Belangrijke vraag: is onze "Blue is fragiler" finding gedreven door:
  (a) Meer Blue-projecten worden gecanceld vóór commissioning?
  (b) Meer Blue-projecten worden gedecommissioneerd ná commissioning?
  (c) Beide?
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lifelines import CoxPHFitter, KaplanMeierFitter

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
def hdr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)


# ============================================================================
# A. v7 COMPETING RISKS — cause-specific Cox PH
# ============================================================================
hdr("A. v7 competing risks — cause-specific Cox PH")

v7 = pd.read_csv('/Users/sakesaakstra/Desktop/thesis_h2/01_data/intermediate/blueccs_project_level_for_R.csv')
print(f"v7 sample: N = {len(v7)}, total events = {v7['event_any'].sum()}")
print(f"\nEvent type breakdown:")
print(v7.groupby(['tech','event_type']).size().unstack(fill_value=0))

# Inspect: wat zijn event_type 1 en 2 precies?
# Logisch hypothese: 1 = pre-commissioning cancellation, 2 = post-commissioning decommissioning
print(f"\nEvent counts by tech and event_type:")
print(v7.groupby(['tech','event_type'])['duration'].agg(['count','mean','median']).round(2))

# Build covariate matrix
v7['blue'] = (v7['tech']=='Blue_CCS').astype(int)
v7['log_cap'] = v7['log_capacity_mw']
v7['eu'] = (v7['region']=='EU').astype(int)
v7['na'] = (v7['region']=='North_America').astype(int)
v7['year_c'] = v7['year_announced'] - 2015  # center
v7 = v7.dropna(subset=['log_cap','year_c'])

print(f"\nFinal sample for Cox PH: N = {len(v7)}")

# Cause-specific Cox PH: voor elke event-type, censor andere events
print("\n" + "-"*78)
print("CAUSE-SPECIFIC COX PH MODELS")
print("-"*78)

results_v7 = []
for event_type_focal in [1, 2]:
    print(f"\n>>> Event type {event_type_focal} as focal event")
    # event = 1 als event_type == focal, 0 anders (censored OR andere event types)
    df_cr = v7.copy()
    df_cr['event_focal'] = (df_cr['event_type'] == event_type_focal).astype(int)
    
    n_focal = df_cr['event_focal'].sum()
    print(f"  N events: {n_focal} / {len(df_cr)} ({100*n_focal/len(df_cr):.1f}%)")
    
    try:
        cph = CoxPHFitter(penalizer=0.01)
        cph.fit(df_cr[['duration','event_focal','blue','log_cap','eu','na','year_c']],
                 duration_col='duration', event_col='event_focal')
        
        summary = cph.summary[['coef','se(coef)','p','exp(coef)']]
        print(f"  Cox PH coefficients:")
        for var in ['blue','log_cap','eu','na','year_c']:
            if var in summary.index:
                row = summary.loc[var]
                marker = '⚠ sig' if row['p']<0.05 else ('· marg' if row['p']<0.10 else '')
                print(f"    {var:<10s}: HR = {row['exp(coef)']:.3f}, β = {row['coef']:+.4f}, "
                       f"SE = {row['se(coef)']:.4f}, p = {row['p']:.4f} {marker}")
        
        results_v7.append({
            'event_type': event_type_focal,
            'n_events': int(n_focal),
            'beta_blue': float(cph.summary.loc['blue','coef']),
            'HR_blue': float(cph.summary.loc['blue','exp(coef)']),
            'se_blue': float(cph.summary.loc['blue','se(coef)']),
            'p_blue': float(cph.summary.loc['blue','p']),
            'beta_logcap': float(cph.summary.loc['log_cap','coef']),
            'p_logcap': float(cph.summary.loc['log_cap','p']),
            'beta_eu': float(cph.summary.loc['eu','coef']),
            'p_eu': float(cph.summary.loc['eu','p']),
            'concordance': float(cph.concordance_index_),
        })
    except Exception as e:
        print(f"  Cox PH failed: {e}")

# Pooled (alle events) — voor vergelijking
print(f"\n>>> Pooled (all events) — baseline comparison")
df_pool = v7.copy()
df_pool['event_pool'] = (df_pool['event_type'] != 0).astype(int)
cph_pool = CoxPHFitter(penalizer=0.01)
cph_pool.fit(df_pool[['duration','event_pool','blue','log_cap','eu','na','year_c']],
              duration_col='duration', event_col='event_pool')
beta_blue_pool = cph_pool.summary.loc['blue','coef']
HR_blue_pool = cph_pool.summary.loc['blue','exp(coef)']
p_blue_pool = cph_pool.summary.loc['blue','p']
print(f"  HR_blue (pooled): {HR_blue_pool:.3f}, β = {beta_blue_pool:+.4f}, p = {p_blue_pool:.4f}")

results_v7.append({
    'event_type': 0,  # 0 codeert "pooled"
    'n_events': int(df_pool['event_pool'].sum()),
    'beta_blue': beta_blue_pool,
    'HR_blue': HR_blue_pool,
    'se_blue': float(cph_pool.summary.loc['blue','se(coef)']),
    'p_blue': p_blue_pool,
    'beta_logcap': float(cph_pool.summary.loc['log_cap','coef']),
    'p_logcap': float(cph_pool.summary.loc['log_cap','p']),
    'beta_eu': float(cph_pool.summary.loc['eu','coef']),
    'p_eu': float(cph_pool.summary.loc['eu','p']),
    'concordance': float(cph_pool.concordance_index_),
})

results_v7_df = pd.DataFrame(results_v7)
results_v7_df['label'] = results_v7_df['event_type'].map({0:'Pooled (all events)',
                                                              1:'Type 1 (pre-commissioning?)',
                                                              2:'Type 2 (post-commissioning?)'})
print(f"\nSummary table:")
print(results_v7_df[['label','n_events','HR_blue','p_blue','concordance']].round(4).to_string(index=False))
results_v7_df.to_csv(OUT/"results/cr_v7_cox_results.csv", index=False)


# ============================================================================
# B. S&P COMPETING RISKS — 3-way outcome split
# ============================================================================
hdr("B. S&P competing risks — 3-way outcome split (cancelled / decommissioned / on-hold)")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['is_blue'] = (sp['Technology.1']=='Fossil with CCS').astype(int)
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))
sp['is_EU'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['is_NA'] = (sp['Region major']=='North America').astype(int)
sp['year_c'] = sp['year_announced'] - 2015

# Define 3 outcome paths
sp['outcome'] = 0  # default = censored / still in pipeline
sp.loc[sp['project_status']=='Plans cancelled', 'outcome'] = 1
sp.loc[sp['project_status']=='Decommissioned', 'outcome'] = 2
sp.loc[sp['project_status'].isin(['On-hold (assumed)','On-hold (confirmed)']), 'outcome'] = 3

print(f"S&P outcome distribution:")
print(sp.groupby(['Technology.1','outcome']).size().unstack(fill_value=0))

# Compute duration = years since announcement (synthetic, since we don't have exit dates)
sp['duration'] = 2026 - sp['year_announced'] + 1  # synthetic age

sp_cr = sp.dropna(subset=['log_cap','year_c']).copy()
print(f"\nSample for S&P Cox: N = {len(sp_cr)}")

results_sp = []
outcome_labels = {1:'Cancelled (Plans cancelled)',
                   2:'Decommissioned (post-commissioning)',
                   3:'On-hold (assumed/confirmed)'}

for focal in [1, 2, 3]:
    print(f"\n>>> Outcome {focal}: {outcome_labels[focal]} as focal event")
    df = sp_cr.copy()
    df['event_focal'] = (df['outcome'] == focal).astype(int)
    n_focal = df['event_focal'].sum()
    print(f"  N events: {n_focal}")
    
    if n_focal < 10:
        print(f"  Too few events, skipping")
        continue
    
    try:
        cph = CoxPHFitter(penalizer=0.05)
        cph.fit(df[['duration','event_focal','is_blue','log_cap','is_EU','is_NA','year_c']],
                 duration_col='duration', event_col='event_focal')
        
        print(f"  Cox PH coefficients:")
        for var in ['is_blue','log_cap','is_EU','is_NA','year_c']:
            if var in cph.summary.index:
                row = cph.summary.loc[var]
                marker = '⚠ sig' if row['p']<0.05 else ('· marg' if row['p']<0.10 else '')
                print(f"    {var:<10s}: HR = {row['exp(coef)']:.3f}, β = {row['coef']:+.4f}, "
                       f"SE = {row['se(coef)']:.4f}, p = {row['p']:.4f} {marker}")
        
        results_sp.append({
            'outcome': focal,
            'label': outcome_labels[focal],
            'n_events': int(n_focal),
            'HR_blue': float(cph.summary.loc['is_blue','exp(coef)']),
            'beta_blue': float(cph.summary.loc['is_blue','coef']),
            'se_blue': float(cph.summary.loc['is_blue','se(coef)']),
            'p_blue': float(cph.summary.loc['is_blue','p']),
            'HR_logcap': float(cph.summary.loc['log_cap','exp(coef)']),
            'p_logcap': float(cph.summary.loc['log_cap','p']),
            'HR_EU': float(cph.summary.loc['is_EU','exp(coef)']),
            'p_EU': float(cph.summary.loc['is_EU','p']),
            'concordance': float(cph.concordance_index_),
        })
    except Exception as e:
        print(f"  Cox PH failed: {e}")

results_sp_df = pd.DataFrame(results_sp)
if len(results_sp_df) > 0:
    print(f"\nSummary table:")
    print(results_sp_df[['label','n_events','HR_blue','p_blue','HR_EU','p_EU','concordance']].round(4).to_string(index=False))
    results_sp_df.to_csv(OUT/"results/cr_sp_cox_results.csv", index=False)


# ============================================================================
# C. KAPLAN-MEIER VISUALIZATION per event type
# ============================================================================
hdr("C. Kaplan-Meier curves per event type")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Panel A: v7 cancelation (event_type 1) — Blue vs PEM
ax = axes[0]
v7_t = v7.copy()
v7_t['event_1'] = (v7_t['event_type']==1).astype(int)
for tech_lbl, color in [('Blue_CCS','#882288'), ('PEM','#1f77b4')]:
    sub = v7_t[v7_t['tech']==tech_lbl]
    kmf = KaplanMeierFitter()
    kmf.fit(sub['duration'], sub['event_1'], label=tech_lbl)
    kmf.plot_survival_function(ax=ax, ci_show=True)
ax.set_title('Panel A: v7 — Pre-commissioning cancellation\n(event_type 1, N=31)')
ax.set_xlabel('Years since announcement')
ax.set_ylabel('Survival probability')
ax.set_ylim(0.5, 1.05)

# Panel B: v7 post-commissioning (event_type 2)
ax = axes[1]
v7_t['event_2'] = (v7_t['event_type']==2).astype(int)
for tech_lbl, color in [('Blue_CCS','#882288'), ('PEM','#1f77b4')]:
    sub = v7_t[v7_t['tech']==tech_lbl]
    kmf = KaplanMeierFitter()
    kmf.fit(sub['duration'], sub['event_2'], label=tech_lbl)
    kmf.plot_survival_function(ax=ax, ci_show=True)
ax.set_title('Panel B: v7 — Post-commissioning decommissioning?\n(event_type 2, N=12)')
ax.set_xlabel('Years since announcement')
ax.set_ylim(0.5, 1.05)

# Panel C: S&P Cox PH summary — HR per outcome
ax = axes[2]
if len(results_sp_df) > 0:
    rsp = results_sp_df.sort_values('outcome')
    y_pos = range(len(rsp))
    ax.errorbar(rsp['beta_blue'], y_pos, xerr=1.96*rsp['se_blue'],
                 fmt='o', color='#882288', markersize=10, capsize=5, lw=1.8)
    ax.axvline(0, ls='--', color='black', alpha=0.4)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([f"{r['label'].split('(')[0].strip()}\n(N={r['n_events']})"
                          for _, r in rsp.iterrows()], fontsize=8)
    ax.set_xlabel(r'$\hat\beta_{\mathrm{Blue}}$ from Cox PH (cause-specific)')
    ax.set_title('Panel C: S&P — Blue HR per outcome\n(cause-specific Cox PH)')

plt.suptitle('Competing Risks Cox PH — Cause-specific hazard analysis', y=1.00, fontsize=12)
plt.tight_layout()
fig.savefig(OUT / "figures/F_competing_risks.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_competing_risks.pdf")


# ============================================================================
# EINDSAMENVATTING
# ============================================================================
hdr("EINDSAMENVATTING — Competing Risks")

print("v7 sample:")
for _, r in results_v7_df.iterrows():
    sig_mark = '★' if r['p_blue'] < 0.05 else ('·' if r['p_blue'] < 0.10 else ' ')
    print(f"  {r['label']:<32s}: HR_Blue = {r['HR_blue']:.2f} (p = {r['p_blue']:.3f}) {sig_mark}")

print(f"\nS&P sample:")
if len(results_sp_df) > 0:
    for _, r in results_sp_df.iterrows():
        sig_mark = '★' if r['p_blue'] < 0.05 else ('·' if r['p_blue'] < 0.10 else ' ')
        print(f"  {r['label']:<32s}: HR_Blue = {r['HR_blue']:.2f} (p = {r['p_blue']:.3f}) {sig_mark}")

print(f"""
KEY VRAGEN:
1. Is de Blue-fragiliteit gedreven door cancellation VOOR commissioning?
2. Of door decommissioning NA commissioning?
3. Of door on-hold zonder definitief cancellation?

INTERPRETATIE:
  - Als HR_Blue verschilt per event type → Blue heeft een SPECIFIEK
    failure mode-patroon, niet uniform across the lifecycle.
  - Als HR_Blue consistent is → Blue is uniform fragieler ongeacht
    waar in het lifecycle.

VOLGENDE STAPPEN:
  - Output → results/cr_v7_cox_results.csv, cr_sp_cox_results.csv
  - Plot  → figures/F_competing_risks.pdf
  - Te integreren in Chapter 8 als 10e robustness pijler
""")
