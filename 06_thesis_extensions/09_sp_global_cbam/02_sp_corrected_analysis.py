"""
02_sp_corrected_analysis.py — Cross-sectional met JUISTE cancel definitie (B).

Definitie B: Plans cancelled + Decommissioned = 206 events (6.2%)
Match perfect met v7 sample (43/714 = 6%).

Plus: Match S&P sample met v7 sample voor end-use augmentatie van v7.
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
(OUT / "results").mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(parents=True, exist_ok=True)


def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD S&P en pas JUISTE cancel definitie B toe
# ============================================================================
hdr("Load S&P met definitie B (Plans cancelled + Decommissioned)")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx',
                   sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[(sp['year_announced'] >= 2010) & (sp['year_announced'] <= 2026)].copy()

# DEFINITIE B
sp['cancelled_strict'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)
sp['planning'] = sp['project_status'].isin([
    'Announced (early stage)', 'Announced (advanced)', 'Feasibility', 'Design',
    'Permitted', 'Financed', 'Under construction'
]).astype(int)
sp['on_hold'] = sp['project_status'].isin(['On-hold (assumed)', 'On-hold (confirmed)']).astype(int)

print(f"Cancellation rates per status group:")
print(f"  Plans cancelled + Decommissioned: {sp['cancelled_strict'].sum():,} ({100*sp['cancelled_strict'].mean():.1f}%)")
print(f"  Operating:                         {sp['operating'].sum():,} ({100*sp['operating'].mean():.1f}%)")
print(f"  Planning:                          {sp['planning'].sum():,} ({100*sp['planning'].mean():.1f}%)")
print(f"  On-hold:                           {sp['on_hold'].sum():,} ({100*sp['on_hold'].mean():.1f}%)")

# Tech / region / end-use
def tech_class(t):
    if pd.isna(t): return 'Unknown'
    t = str(t).strip()
    return {'Fossil with CCS':'Blue_CCS','Electrolysis':'Green','Waste':'Waste'}.get(t,'Other')
sp['tech_class'] = sp['Technology.1'].apply(tech_class)
sp['is_blue'] = (sp['tech_class']=='Blue_CCS').astype(int)

def cbam_endex(detail, sector):
    detail_low = str(detail).lower() if pd.notna(detail) else ''
    sector_low = str(sector).lower() if pd.notna(sector) else ''
    if any(k in detail_low for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']):
        return 1
    if 'chemical feedstock' in sector_low or 'refinery feedstock' in sector_low:
        return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'],
                                                   r['Primary end use sector']), axis=1)
sp['region_EU27'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['region_EU_or_adjacent'] = sp['Region major'].isin(['Europe (EU-27)','Europe (non EU-27)']).astype(int)

def export_to_eu(will_export, dest):
    if str(will_export).strip()!='Yes': return 0
    if pd.isna(dest): return 0
    d = str(dest).lower()
    return int(any(k in d for k in ['europ','germany','netherlands','france','spain','italy',
                                      'belgium','poland','sweden','denmark','austria','czech',
                                      'finland','greece','portugal','hungary','ireland']))
sp['export_to_eu'] = sp.apply(lambda r: export_to_eu(r['Will export'], r['Export destination geography']), axis=1)
sp['cbam_exposed'] = (sp['cbam_endex'] | sp['region_EU27'] | sp['export_to_eu']).astype(int)
sp['capacity_t_y'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_capacity'] = np.log1p(sp['capacity_t_y'].fillna(sp['capacity_t_y'].median()))


# ============================================================================
# 2. CROSS-SECTIONAL met DEF B — alleen finished projects
# ============================================================================
hdr("Cross-sectional met definitie B (cancelled vs operating only)")

df = sp[(sp['cancelled_strict'] + sp['operating']) == 1].copy()
print(f"Sample: {len(df):,} finished projects")
print(f"  Cancelled (def B): {df['cancelled_strict'].sum():,} ({100*df['cancelled_strict'].mean():.1f}%)")
print(f"  Operating:         {df['operating'].sum():,}")

if len(df) > 50 and df['cancelled_strict'].sum() > 10:
    y = df['cancelled_strict']
    X = sm.add_constant(df[['is_blue','cbam_endex','region_EU27','export_to_eu',
                              'log_capacity','year_announced']])
    m = sm.Logit(y, X).fit(disp=0)
    print("\nLogit model (cancelled ~ Blue + CBAM-endex + EU + Export_EU + log_cap + year):")
    print(m.summary().tables[1])
    
    me = m.get_margeff(method='dydx').summary_frame()
    print("\nMarginal effects (Δ probability of cancellation):")
    print(me.round(4))
    
    # Save
    m.summary2().tables[1].to_csv(OUT / "results/B_corrected_cross_sectional.csv")


# ============================================================================
# 3. CROSS-SECTIONAL met DEF B incl ON-HOLD als "soft cancel" — uitbreiding
# ============================================================================
hdr("Robuustheid: definitie C (incl. On-hold confirmed)")

sp['cancelled_medium'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned', 
                                                       'On-hold (confirmed)']).astype(int)
df_c = sp[(sp['cancelled_medium'] + sp['operating']) == 1].copy()
print(f"Sample: {len(df_c):,}, cancelled (def C): {df_c['cancelled_medium'].sum()}")

y = df_c['cancelled_medium']
X = sm.add_constant(df_c[['is_blue','cbam_endex','region_EU27','export_to_eu',
                            'log_capacity','year_announced']])
m_c = sm.Logit(y, X).fit(disp=0)
print(m_c.summary().tables[1])


# ============================================================================
# 4. VINTAGE COHORT ANALYSE met DEF B
# ============================================================================
hdr("Vintage cohort cancellation rates (definitie B)")

# Per cohort, alle projecten (incl planning) want we willen rate over alle vintages
vintage = sp.groupby('year_announced').agg(
    n_total=('Record ID','count'),
    n_cancelled_B=('cancelled_strict','sum'),
    n_operating=('operating','sum'),
    n_planning=('planning','sum'),
    n_on_hold=('on_hold','sum'),
).reset_index()
vintage['cancel_rate_B'] = (vintage['n_cancelled_B']/vintage['n_total']*100).round(1)
vintage['onhold_rate'] = (vintage['n_on_hold']/vintage['n_total']*100).round(1)
print(vintage.tail(15).to_string(index=False))

# Cohort × tech_class met definitie B
print(f"\nCancel rate (def B) per cohort × tech_class:")
ct = sp.groupby(['year_announced','tech_class']).agg(
    n=('Record ID','count'),
    cancelled=('cancelled_strict','sum'),
).reset_index()
ct['rate'] = (ct['cancelled']/ct['n']*100).round(1)
ct_wide = ct.pivot_table(index='year_announced', columns='tech_class', values='rate')
print(ct_wide.tail(15).round(1))

# Cohort × CBAM exposure
print(f"\nCancel rate (def B) per cohort × CBAM exposure:")
ct2 = sp.groupby(['year_announced','cbam_endex']).agg(
    n=('Record ID','count'),
    cancelled=('cancelled_strict','sum'),
).reset_index()
ct2['rate'] = (ct2['cancelled']/ct2['n']*100).round(1)
ct2_wide = ct2.pivot_table(index='year_announced', columns='cbam_endex', values='rate')
ct2_wide.columns = ['Non-exposed (rate %)','CBAM-exposed (rate %)']
print(ct2_wide.tail(15))


# ============================================================================
# 5. VINTAGE × CBAM-EXPOSURE DiD met DEF B
# ============================================================================
hdr("Vintage × CBAM-exposure DiD (definitie B)")

df_did = sp[(sp['cancelled_strict']+sp['operating'])==1].copy()
df_did['post_cbam_vintage'] = (df_did['year_announced']>=2022).astype(int)

cells = df_did.groupby(['cbam_endex','post_cbam_vintage']).agg(
    n=('Record ID','count'),
    cancelled=('cancelled_strict','sum'),
)
cells['rate'] = (cells['cancelled']/cells['n']*100).round(2)
print("2x2 cells:")
print(cells)

# DiD computation
try:
    e1p1 = cells.loc[(1,1),'rate']
    e1p0 = cells.loc[(1,0),'rate']
    e0p1 = cells.loc[(0,1),'rate']
    e0p0 = cells.loc[(0,0),'rate']
    did = (e1p1-e1p0)-(e0p1-e0p0)
    print(f"\nRaw DiD (cancel rate pct points):")
    print(f"  CBAM-exposed:    pre={e1p0:.1f}%, post={e1p1:.1f}%, Δ={e1p1-e1p0:+.1f}pp")
    print(f"  Non-CBAM exposed: pre={e0p0:.1f}%, post={e0p1:.1f}%, Δ={e0p1-e0p0:+.1f}pp")
    print(f"  DiD: {did:+.2f}pp")
except KeyError:
    print("Niet alle 4 cells beschikbaar")

# Logit DiD
df_did['EP'] = df_did['cbam_endex']*df_did['post_cbam_vintage']
y = df_did['cancelled_strict']
X = sm.add_constant(df_did[['cbam_endex','post_cbam_vintage','EP','is_blue','log_capacity']])
m_did = sm.Logit(y, X).fit(disp=0)
print(f"\nLogit DiD interaction (β_EP):")
print(f"  Coef:  {m_did.params['EP']:+.3f}")
print(f"  SE:    {m_did.bse['EP']:.3f}")
print(f"  p:     {m_did.pvalues['EP']:.3f}")
print(f"  95% CI: [{m_did.params['EP']-1.96*m_did.bse['EP']:+.2f}, {m_did.params['EP']+1.96*m_did.bse['EP']:+.2f}]")


# ============================================================================
# 6. VISUALISATIE — vintage cancel rates
# ============================================================================
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: cancel rate per tech per vintage
ax = axes[0]
for tech, col in [('Blue_CCS','#882288'),('Green','#117733')]:
    sub = ct[ct['tech_class']==tech]
    sub = sub[sub['n']>=5]
    ax.plot(sub['year_announced'], sub['rate'], 'o-', color=col, lw=2,
            label=f"{tech} (n≥5)", markersize=7)
ax.axvline(2022, ls='--', color='red', alpha=0.6, label='CBAM agreement')
ax.axvline(2023.75, ls=':', color='darkred', alpha=0.6, label='CBAM transitional')
ax.set_xlabel('Vintage cohort (announce year)')
ax.set_ylabel('Cancellation rate (%) — definitie B')
ax.set_title('Cancel rate per tech & vintage (S&P, def B = 206 events)')
ax.legend(loc='best')
ax.grid(alpha=0.3)

# Plot 2: cancel rate per CBAM-exposure per vintage
ax = axes[1]
for cbex, lbl, col in [(0,'Niet CBAM-exposed','#888888'),(1,'CBAM-exposed','#882288')]:
    sub = ct2[ct2['cbam_endex']==cbex]
    sub = sub[sub['n']>=5]
    ax.plot(sub['year_announced'], sub['rate'], 'o-', color=col, lw=2,
            label=lbl, markersize=7)
ax.axvline(2022, ls='--', color='red', alpha=0.6, label='CBAM agreement')
ax.set_xlabel('Vintage cohort (announce year)')
ax.set_ylabel('Cancellation rate (%) — definitie B')
ax.set_title('Cancel rate per CBAM-endex & vintage')
ax.legend(loc='best')
ax.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(OUT / "figures/sp_corrected_vintage.pdf")
plt.close()
print(f"\nFiguur: {OUT}/figures/sp_corrected_vintage.pdf")

# Save samenvattende stats
summary = {
    'cancel_def': 'B (Plans cancelled + Decommissioned)',
    'n_total': int(len(sp)),
    'n_cancelled': int(sp['cancelled_strict'].sum()),
    'n_operating': int(sp['operating'].sum()),
    'n_cbam_exposed': int(sp['cbam_endex'].sum()),
    'beta_cbam_endex': float(m.params['cbam_endex']) if 'm' in dir() else np.nan,
    'p_cbam_endex': float(m.pvalues['cbam_endex']) if 'm' in dir() else np.nan,
    'did_interaction_beta': float(m_did.params['EP']),
    'did_interaction_p': float(m_did.pvalues['EP']),
    'did_raw_pp': float(did) if 'did' in dir() else np.nan,
}
pd.Series(summary).to_csv(OUT / "results/sp_corrected_summary.csv")
print(f"\nSummary: {OUT}/results/sp_corrected_summary.csv")
