"""
01_sp_cross_sectional.py — S&P Global cross-sectional & vintage-cohort analyse

S&P data: 3,343 projecten, 1,155 cancelled, 122 kolommen incl. echte end-use sector

Drie analyses:
  A. Cross-sectional logit: P(cancelled) ~ tech + end_use + region + year + export
  B. Vintage cohort: cancellation rates by announce-year cohort
  C. CBAM exposure stratificatie met echte end-use data

Voordelen tov v7-only:
  - 5x meer projecten
  - Echte end-use classificatie (geen sponsor-proxy meer)
  - Export destination data (CBAM-direct relevant)
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/09_sp_global_cbam")
(OUT / "figures").mkdir(parents=True, exist_ok=True)
(OUT / "results").mkdir(parents=True, exist_ok=True)


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# LOAD + CLEAN S&P data
# ============================================================================
hdr("Load S&P Global Hydrogen Master Data")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx',
                   sheet_name='Export')
print(f"Initial: {sp.shape[0]:,} projecten × {sp.shape[1]} kolommen")

# Clean voor analyse
sp = sp[sp['Project status major'].notna()].copy()
sp = sp[sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[(sp['year_announced'] >= 2010) & (sp['year_announced'] <= 2026)].copy()

# Event: cancelled OR offline (excludes "on-hold")
sp['cancelled'] = sp['Project status major'].isin(['Cancelled', 'Offline']).astype(int)
sp['operating'] = sp['Project status major'].isin(['Operating']).astype(int)
sp['planning'] = sp['Project status major'].isin(['Planning - early', 'Planning - advanced']).astype(int)

print(f"\nNa cleaning: {len(sp):,} projecten")
print(f"  Cancelled/Offline: {sp['cancelled'].sum():,} ({100*sp['cancelled'].mean():.1f}%)")
print(f"  Operating:         {sp['operating'].sum():,} ({100*sp['operating'].mean():.1f}%)")
print(f"  Planning:          {sp['planning'].sum():,} ({100*sp['planning'].mean():.1f}%)")

# ============================================================================
# BUILD COVARIATES
# ============================================================================
hdr("Build covariates")

# Blue vs Green tech indicator
def tech_class(tech1):
    if pd.isna(tech1):
        return 'Unknown'
    t = str(tech1).strip()
    if t == 'Fossil with CCS':
        return 'Blue_CCS'
    elif t == 'Electrolysis':
        return 'Green_electrolysis'
    elif t == 'Waste':
        return 'Waste'
    else:
        return 'Other'
sp['tech_class'] = sp['Technology.1'].apply(tech_class)
sp['is_blue'] = (sp['tech_class'] == 'Blue_CCS').astype(int)
sp['is_green'] = (sp['tech_class'] == 'Green_electrolysis').astype(int)

# CBAM-end-use exposure (DIRECT from S&P data!)
def cbam_endex(detail, sector):
    if pd.isna(detail):
        detail = ''
    detail_low = str(detail).lower()
    sector_low = str(sector).lower() if pd.notna(sector) else ''
    # Direct CBAM coverage from Jan 2026
    if any(k in detail_low for k in ['fertilizer','ammonia','steel','chemicals','oil refinery','refinery','cement']):
        return 1
    if 'chemical feedstock' in sector_low or 'refinery feedstock' in sector_low:
        return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'],
                                                   r['Primary end use sector']), axis=1)

# EU region indicator (covers CBAM jurisdiction)
sp['region_EU27'] = (sp['Region major'] == 'Europe (EU-27)').astype(int)
sp['region_EU_or_adjacent'] = sp['Region major'].isin(['Europe (EU-27)', 'Europe (non EU-27)']).astype(int)

# Export-to-EU indicator
def export_to_eu(will_export, dest):
    if str(will_export).strip() != 'Yes':
        return 0
    if pd.isna(dest):
        return 0
    d = str(dest).lower()
    return int(any(k in d for k in ['europ','germany','netherlands','france','spain','italy',
                                      'belgium','poland','sweden','denmark','austria','czech',
                                      'finland','greece','portugal','hungary','ireland']))
sp['export_to_eu'] = sp.apply(lambda r: export_to_eu(r['Will export'], r['Export destination geography']), axis=1)

# CBAM-effective exposure: end-use OR EU-region OR export-to-EU
sp['cbam_exposed'] = (sp['cbam_endex'] | sp['region_EU27'] | sp['export_to_eu']).astype(int)
sp['cbam_exposed_strict'] = (sp['cbam_endex'] & (sp['region_EU27'] | sp['export_to_eu'])).astype(int)

# Capacity (log)
sp['capacity_t_y'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_capacity'] = np.log1p(sp['capacity_t_y'].fillna(sp['capacity_t_y'].median()))

print(f"\nTech distributie:")
print(sp['tech_class'].value_counts())
print(f"\nCBAM end-use exposed: {sp['cbam_endex'].sum():,} ({100*sp['cbam_endex'].mean():.1f}%)")
print(f"EU-27 region:          {sp['region_EU27'].sum():,} ({100*sp['region_EU27'].mean():.1f}%)")
print(f"Export to EU:          {sp['export_to_eu'].sum():,} ({100*sp['export_to_eu'].mean():.1f}%)")
print(f"CBAM-exposed (union):  {sp['cbam_exposed'].sum():,} ({100*sp['cbam_exposed'].mean():.1f}%)")
print(f"CBAM-exposed (strict): {sp['cbam_exposed_strict'].sum():,} ({100*sp['cbam_exposed_strict'].mean():.1f}%)")


# ============================================================================
# ANALYSIS A — CROSS-SECTIONAL LOGIT
# ============================================================================
hdr("ANALYSIS A — Cross-sectional logit: P(cancelled)")

# Filter naar finished status (cancelled OR operating, exclude planning)
df_a = sp[sp['cancelled'] + sp['operating'] == 1].copy()
print(f"Sample: {len(df_a):,} projecten (cancelled + operating)")
print(f"  Cancelled: {df_a['cancelled'].sum():,} ({100*df_a['cancelled'].mean():.1f}%)")

y = df_a['cancelled']
X_vars = ['is_blue', 'cbam_endex', 'region_EU27', 'export_to_eu', 'log_capacity', 'year_announced']
X = sm.add_constant(df_a[X_vars])
m_a = sm.Logit(y, X).fit(disp=0)

print("\nCross-sectional model (Cancelled ~ Blue + CBAM-endex + EU + Export_EU + log_cap + year):")
print(m_a.summary().tables[1])

# Marginal effects
me = m_a.get_margeff(method='dydx').summary_frame()
print("\nMarginal effects (Δprob of cancellation):")
print(me.round(4))


# ============================================================================
# ANALYSIS B — VINTAGE COHORT ANALYSE
# ============================================================================
hdr("ANALYSIS B — Vintage cohort: cancellation rate by announcement year")

# Vintage cohort = jaar van project announce
vintage = sp.groupby('year_announced').agg(
    n_projects=('Record ID', 'count'),
    n_cancelled=('cancelled', 'sum'),
    n_operating=('operating', 'sum'),
    pct_cancelled=('cancelled', 'mean'),
).round(3)
vintage['pct_cancelled'] = (vintage['pct_cancelled'] * 100).round(1)
print(vintage.tail(15))

# Cohort × tech_class
vintage_tech = sp.groupby(['year_announced','tech_class']).agg(
    n=('Record ID', 'count'),
    cancelled=('cancelled', 'sum'),
).reset_index()
vintage_tech['pct_cancelled'] = (vintage_tech['cancelled'] / vintage_tech['n'] * 100).round(1)
vintage_tech_wide = vintage_tech.pivot_table(index='year_announced', columns='tech_class',
                                              values='pct_cancelled')
print(f"\nCancellation rates per (announce-year × tech_class), %:")
print(vintage_tech_wide.fillna(0).round(1).tail(15))

# Pre-CBAM vs post-CBAM-agreement vintages
CBAM_AGREEMENT = 2022  # December 2022 CBAM political agreement
sp['vintage_pre_cbam'] = (sp['year_announced'] < CBAM_AGREEMENT).astype(int)
sp['vintage_post_cbam'] = (sp['year_announced'] >= CBAM_AGREEMENT).astype(int)

print(f"\nCBAM-aware vintage analyse (announced >= {CBAM_AGREEMENT}):")
for v_label, v_col in [('Pre-CBAM (announced < 2022)', 'vintage_pre_cbam'),
                         ('Post-CBAM (announced >= 2022)', 'vintage_post_cbam')]:
    sub = sp[sp[v_col]==1]
    n_t = len(sub)
    n_c = sub['cancelled'].sum()
    print(f"  {v_label}: n={n_t:,}, cancelled={n_c:,} ({100*n_c/n_t:.1f}%)")
    # Per tech
    for tech in ['Blue_CCS', 'Green_electrolysis']:
        s2 = sub[sub['tech_class']==tech]
        if len(s2) > 0:
            print(f"    {tech}: n={len(s2):,}, cancelled={s2['cancelled'].sum():,} ({100*s2['cancelled'].mean():.1f}%)")


# ============================================================================
# ANALYSIS C — CBAM exposure DiD via vintage cohort
# ============================================================================
hdr("ANALYSIS C — Vintage × CBAM-exposure DiD")

# Treatment: announced in/after 2022 (CBAM aware vintage)
# Exposed: CBAM end-use + EU/export-EU
# Outcome: cancellation rate
df_c = sp[sp['cancelled'] + sp['operating'] == 1].copy()
df_c['post_cbam_vintage'] = (df_c['year_announced'] >= 2022).astype(int)
df_c['exposed'] = df_c['cbam_exposed']

# 2x2 DiD
cells = df_c.groupby(['exposed','post_cbam_vintage']).agg(
    n=('Record ID', 'count'),
    n_cancelled=('cancelled','sum'),
    pct_cancelled=('cancelled','mean'),
)
cells['pct_cancelled'] = (cells['pct_cancelled'] * 100).round(2)
print(f"\n2×2 cells (Exposed × Post-CBAM-vintage):")
print(cells)

# DiD calculation (in pct points)
e1p1 = cells.loc[(1,1), 'pct_cancelled']
e1p0 = cells.loc[(1,0), 'pct_cancelled']
e0p1 = cells.loc[(0,1), 'pct_cancelled']
e0p0 = cells.loc[(0,0), 'pct_cancelled']
did = (e1p1 - e1p0) - (e0p1 - e0p0)
print(f"\nDiD (cancel rate, pct points):")
print(f"  Exposed × Post-CBAM-vintage:  {e1p1:.2f}% (vs pre {e1p0:.2f}%) → Δ = {e1p1-e1p0:+.2f}pp")
print(f"  Non-exposed × Post-CBAM-vintage: {e0p1:.2f}% (vs pre {e0p0:.2f}%) → Δ = {e0p1-e0p0:+.2f}pp")
print(f"  DiD: {did:+.2f}pp")

# Statistical test via logit
df_c['EP'] = df_c['exposed'] * df_c['post_cbam_vintage']
y = df_c['cancelled']
X = sm.add_constant(df_c[['exposed','post_cbam_vintage','EP','is_blue','log_capacity']])
m_c = sm.Logit(y, X).fit(disp=0)
print(f"\nLogit DiD coefficient (interaction):")
print(f"  β_EP = {m_c.params['EP']:+.3f} (SE={m_c.bse['EP']:.3f}, p={m_c.pvalues['EP']:.3f})")
print(f"  95% CI: [{m_c.params['EP']-1.96*m_c.bse['EP']:+.2f}, {m_c.params['EP']+1.96*m_c.bse['EP']:+.2f}]")
print(f"\n=> Interpretatie: een β_EP {'>' if m_c.params['EP']>0 else '<'} 0 betekent dat CBAM-exposed projecten")
print(f"   announced in 2022+ {'meer' if m_c.params['EP']>0 else 'minder'} cancellations hadden dan we zouden")
print(f"   verwachten obv algemene exposure-trend + algemene vintage-trend.")

# Save resultaten
m_a.summary2().tables[1].to_csv(OUT / "results/A_cross_sectional_logit.csv")
vintage.to_csv(OUT / "results/B_vintage_cohort_rates.csv")
vintage_tech_wide.to_csv(OUT / "results/B_vintage_tech_rates.csv")
m_c.summary2().tables[1].to_csv(OUT / "results/C_vintage_did.csv")


# ============================================================================
# VISUALIZATIONS
# ============================================================================
hdr("Visualizations")

# Plot 1: Vintage cohort cancellation rates per tech
fig, ax = plt.subplots(figsize=(11, 6))
for tech, col in [('Blue_CCS', '#882288'), ('Green_electrolysis', '#117733')]:
    sub = vintage_tech[vintage_tech['tech_class']==tech]
    sub = sub[sub['n'] >= 5]  # min 5 projecten per cohort
    ax.plot(sub['year_announced'], sub['pct_cancelled'], 'o-',
            color=col, lw=2, label=f"{tech} (n≥5 per cohort)", markersize=7)

ax.axvline(2022, ls='--', color='red', alpha=0.6, label='CBAM political agreement (Dec 2022)')
ax.axvline(2023.75, ls=':', color='darkred', alpha=0.6, label='CBAM transitional (Oct 2023)')
ax.set_xlabel('Vintage cohort (year announced)')
ax.set_ylabel('Cancellation rate (%)')
ax.set_title('Hydrogen project cancellation rates by vintage cohort, S&P Global (n=3,343)')
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/vintage_cohort_cancellation.pdf")
plt.close()
print(f"Plot saved: {OUT}/figures/vintage_cohort_cancellation.pdf")

# Plot 2: CBAM-exposed vs not, by vintage
df_plot = df_c.copy()
df_plot['cohort'] = df_plot['year_announced'].clip(upper=2024)
plot_data = df_plot.groupby(['cohort','exposed']).agg(
    n=('Record ID','count'),
    cancel_rate=('cancelled','mean'),
).reset_index()
plot_data['cancel_rate'] *= 100
plot_data = plot_data[plot_data['n'] >= 10]

fig, ax = plt.subplots(figsize=(11, 6))
for exp, lbl, col in [(0, 'Not CBAM-exposed', '#888888'), (1, 'CBAM-exposed', '#882288')]:
    sub = plot_data[plot_data['exposed']==exp]
    ax.plot(sub['cohort'], sub['cancel_rate'], 'o-', color=col, lw=2,
            label=lbl, markersize=8)

ax.axvline(2022, ls='--', color='red', alpha=0.6, label='CBAM agreement (2022)')
ax.set_xlabel('Vintage (year announced)')
ax.set_ylabel('Cancellation rate (%)')
ax.set_title('Cancellation rate by CBAM-exposure × vintage cohort')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/cbam_exposed_vs_not_vintage.pdf")
plt.close()
print(f"Plot saved: {OUT}/figures/cbam_exposed_vs_not_vintage.pdf")

print(f"\nAll outputs: {OUT}")
