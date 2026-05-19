"""
04_eu_specific_cbam.py — EU-27 specifieke CBAM analyse.

Het globale patroon was: CBAM-exposed → lower cancellation (sector fundamentals)
Maar binnen EU-27: CBAM-exposed → +19.7pp HIGHER cancellation
Plus T3 strict (EU AND CBAM-covered): β = +0.789 (p=0.038)

Dit suggereert een EU-specifiek CBAM-effect. Deze analyse test:
  1. Is het EU-pattern placebo-robust?
  2. Is het ook in andere CBAM-exposure proxies zichtbaar?
  3. Hoe varieert het per EU-country?
  4. Wat is de cancellation timing distributie binnen EU?
  5. Triple-diff Blue × CBAM × Post BINNEN EU
  
Als placebo's ook significant zijn → patroon is artifact
Als placebo's null zijn → echte CBAM signal!
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
(OUT / "results/eu_specific").mkdir(parents=True, exist_ok=True)
(OUT / "figures/eu_specific").mkdir(parents=True, exist_ok=True)


def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD + EU-27 FILTER
# ============================================================================
hdr("Load S&P + filter naar EU-27 only")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx',
                   sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[(sp['year_announced'] >= 2010) & (sp['year_announced'] <= 2026)].copy()

# Filter naar EU-27
eu = sp[sp['Region major'] == 'Europe (EU-27)'].copy()
print(f"Volledige S&P sample: {len(sp):,}")
print(f"EU-27 subset:          {len(eu):,} ({100*len(eu)/len(sp):.1f}%)")

# Counts per EU country
print(f"\nProjecten per EU-land (top 15):")
print(eu['Region minor'].value_counts().head(15))


# ============================================================================
# 2. Build covariates (same as before maar binnen EU)
# ============================================================================
def t1_endex(detail, sector):
    detail_low = str(detail).lower() if pd.notna(detail) else ''
    sector_low = str(sector).lower() if pd.notna(sector) else ''
    if any(k in detail_low for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']):
        return 1
    if 'chemical feedstock' in sector_low or 'refinery feedstock' in sector_low:
        return 1
    return 0
eu['T1_narrow'] = eu.apply(lambda r: t1_endex(r['Primary end use sector detail'],
                                                r['Primary end use sector']), axis=1)
def tech_class(t):
    if pd.isna(t): return 'Unknown'
    return {'Fossil with CCS':'Blue_CCS','Electrolysis':'Green'}.get(str(t).strip(),'Other')
eu['tech_class'] = eu['Technology.1'].apply(tech_class)
eu['is_blue'] = (eu['tech_class']=='Blue_CCS').astype(int)
eu['capacity_ty'] = pd.to_numeric(eu['Calculated hydrogen production per year'], errors='coerce')
eu['log_capacity'] = np.log1p(eu['capacity_ty'].fillna(eu['capacity_ty'].median()))

# Cancellation definitions
eu['cancel_A'] = eu['project_status'].isin(['Plans cancelled']).astype(int)
eu['cancel_B'] = eu['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
eu['cancel_C'] = eu['project_status'].isin(['Plans cancelled', 'Decommissioned',
                                              'On-hold (confirmed)']).astype(int)
eu['operating'] = eu['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)

print(f"\nWithin EU-27:")
print(f"  Cancel def A (Plans cancelled):   {eu['cancel_A'].sum():>3} ({100*eu['cancel_A'].mean():.1f}%)")
print(f"  Cancel def B (PRIMARY):           {eu['cancel_B'].sum():>3} ({100*eu['cancel_B'].mean():.1f}%)")
print(f"  Cancel def C (+ on-hold conf):    {eu['cancel_C'].sum():>3} ({100*eu['cancel_C'].mean():.1f}%)")
print(f"  Operating:                          {eu['operating'].sum():>3} ({100*eu['operating'].mean():.1f}%)")
print(f"  T1-CBAM-exposed:                   {eu['T1_narrow'].sum():>3} ({100*eu['T1_narrow'].mean():.1f}%)")
print(f"  Blue CCS:                          {eu['is_blue'].sum():>3} ({100*eu['is_blue'].mean():.1f}%)")


# ============================================================================
# 3. EU CROSS-SECTIONAL LOGIT
# ============================================================================
hdr("EU cross-sectional logit (cancel_B ~ CBAM-endex + controls)")

df = eu[(eu['cancel_B']+eu['operating']) == 1].copy()
print(f"Analyse sample (EU finished): {len(df):,} projecten")
print(f"  Cancelled: {df['cancel_B'].sum():,} ({100*df['cancel_B'].mean():.1f}%)")
print(f"  Operating: {df['operating'].sum():,}\n")

eu_models = {}
for spec_name, X_cols in [
    ('EU-M1: Basic',        ['T1_narrow']),
    ('EU-M2: + tech',       ['T1_narrow','is_blue']),
    ('EU-M3: + capacity',   ['T1_narrow','is_blue','log_capacity']),
    ('EU-M4: + year',       ['T1_narrow','is_blue','log_capacity','year_announced']),
]:
    y = df['cancel_B']
    X = sm.add_constant(df[X_cols])
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=100)
        b = m.params['T1_narrow']
        se = m.bse['T1_narrow']
        p = m.pvalues['T1_narrow']
        marg = m.get_margeff(method='dydx').summary_frame().loc['T1_narrow']
        eu_models[spec_name] = {'beta':b,'se':se,'p':p,'marg':marg['dy/dx']}
        sig = "★" if p < 0.05 else " "
        print(f"{spec_name:<22s} | β={b:+.3f}{sig} | p={p:.3f} | 95%CI [{b-1.96*se:+.2f},{b+1.96*se:+.2f}] | Δp={marg['dy/dx']*100:+.1f}pp")
    except Exception as e:
        print(f"{spec_name}: FAIL ({e})")

pd.DataFrame(eu_models).T.to_csv(OUT / "results/eu_specific/eu_cross_sectional.csv")


# ============================================================================
# 4. PLACEBO-ROBUST DiD BINNEN EU
# ============================================================================
hdr("EU-only DiD met meerdere placebo dates — KRITIEK voor causale claim")

df_did = eu[(eu['cancel_B']+eu['operating'])==1].copy()

# Test treatment dates met dichte placebo grid
TREATMENTS = {
    'CBAM_agreement_2022':   2022,   # PRIMARY
    'CBAM_regulation_2023':  2023,
    'PLACEBO_2015':          2015,   # 7 jaar vóór CBAM
    'PLACEBO_2017':          2017,   # 5 jaar vóór CBAM
    'PLACEBO_2019':          2019,   # 3 jaar vóór CBAM
    'PLACEBO_2020':          2020,   # 2 jaar vóór CBAM
    'PLACEBO_2021':          2021,   # 1 jaar vóór CBAM
}

eu_did_results = []
for trt_name, trt_year in TREATMENTS.items():
    df_t = df_did.copy()
    df_t['post'] = (df_t['year_announced'] >= trt_year).astype(int)
    df_t['EP'] = df_t['T1_narrow'] * df_t['post']
    
    # Check minimum cell sizes
    cells = df_t.groupby(['T1_narrow','post']).size()
    if cells.min() < 3:
        eu_did_results.append({
            'treatment': trt_name, 'beta_EP': np.nan, 'se': np.nan, 'p': np.nan,
            'ci_lo': np.nan, 'ci_hi': np.nan, 'is_placebo': 'PLACEBO' in trt_name,
            'min_cell': int(cells.min()), 'fit_ok': False,
        })
        continue
    
    y = df_t['cancel_B']
    X = sm.add_constant(df_t[['T1_narrow','post','EP','is_blue','log_capacity']])
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=200)
        b = m.params['EP']
        se = m.bse['EP']
        p = m.pvalues['EP']
        eu_did_results.append({
            'treatment': trt_name,
            'beta_EP': b, 'se': se, 'p': p,
            'ci_lo': b-1.96*se, 'ci_hi': b+1.96*se,
            'is_placebo': 'PLACEBO' in trt_name,
            'min_cell': int(cells.min()),
            'fit_ok': True,
        })
    except Exception as e:
        eu_did_results.append({
            'treatment': trt_name, 'beta_EP': np.nan, 'fit_ok': False,
            'is_placebo': 'PLACEBO' in trt_name, 'error': str(e),
        })

eu_did_df = pd.DataFrame(eu_did_results)
print(f"{'Treatment':<25s} | β_EP    | 95% CI         | p     | min_cell | Note")
print("-" * 90)
for _, r in eu_did_df.iterrows():
    pl = "🅿️" if r['is_placebo'] else "  "
    if not r.get('fit_ok', False):
        print(f"{pl} {r['treatment']:<23s} | (fit fail, min_cell={r.get('min_cell','?')})")
        continue
    sig = "★" if r['p'] < 0.05 else " "
    print(f"{pl} {r['treatment']:<23s} | {r['beta_EP']:+.3f}{sig} | [{r['ci_lo']:+.2f},{r['ci_hi']:+.2f}] | {r['p']:.3f} | {r['min_cell']}")

eu_did_df.to_csv(OUT / "results/eu_specific/eu_did_specs.csv", index=False)


# ============================================================================
# 5. EU vs NON-EU TRIPLE-DIFFERENCE (Region × CBAM × Post)
# ============================================================================
hdr("Triple-difference: Region × CBAM-exposure × Post-2022 (full sample)")
print("Vraag: Is het CBAM-effect significant DIFFERENT in EU vs niet-EU?\n")

sp['region_EU27'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['T1_narrow'] = sp.apply(lambda r: t1_endex(r['Primary end use sector detail'],
                                                r['Primary end use sector']), axis=1)
sp['tech_class'] = sp['Technology.1'].apply(tech_class)
sp['is_blue'] = (sp['tech_class']=='Blue_CCS').astype(int)
sp['capacity_ty'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_capacity'] = np.log1p(sp['capacity_ty'].fillna(sp['capacity_ty'].median()))
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)

df_tri = sp[(sp['cancel_B']+sp['operating'])==1].copy()
df_tri['post'] = (df_tri['year_announced'] >= 2022).astype(int)

# Triple difference: EU × CBAM-exp × Post
df_tri['EU_CBAM'] = df_tri['region_EU27'] * df_tri['T1_narrow']
df_tri['EU_post'] = df_tri['region_EU27'] * df_tri['post']
df_tri['CBAM_post'] = df_tri['T1_narrow'] * df_tri['post']
df_tri['EU_CBAM_post'] = df_tri['region_EU27'] * df_tri['T1_narrow'] * df_tri['post']

y = df_tri['cancel_B']
X = sm.add_constant(df_tri[['region_EU27','T1_narrow','post','EU_CBAM','EU_post','CBAM_post','EU_CBAM_post',
                              'is_blue','log_capacity']])

try:
    m_tri = sm.Logit(y, X).fit(disp=0, maxiter=300)
    print(m_tri.summary().tables[1])
    b_3way = m_tri.params['EU_CBAM_post']
    se_3way = m_tri.bse['EU_CBAM_post']
    p_3way = m_tri.pvalues['EU_CBAM_post']
    print(f"\n★ KRITIEKE COEFFICIENT: β_EU×CBAM×Post = {b_3way:+.3f} (SE={se_3way:.3f}, p={p_3way:.3f})")
    print(f"  95% CI: [{b_3way-1.96*se_3way:+.2f}, {b_3way+1.96*se_3way:+.2f}]")
    print(f"\nInterpretatie:")
    if p_3way < 0.05:
        if b_3way > 0:
            print(f"  ★ SIGNIFICANT positief: EU-CBAM-projecten in 2022+ cohorten cancellen")
            print(f"    significant MEER dan we zouden verwachten obv EU-, CBAM-, of post-effects alleen.")
            print(f"    Dit is consistent met CBAM als causale drijfveer.")
        else:
            print(f"  ★ SIGNIFICANT negatief: onverwacht patroon.")
    else:
        print(f"  ~ NULL: We kunnen geen causaal EU-specifiek CBAM-effect identificeren.")
        print(f"    Het 19.7pp EU-pattern is dus mogelijk een cross-sectional artefact,")
        print(f"    niet een treatment effect van CBAM.")
    m_tri.summary2().tables[1].to_csv(OUT / "results/eu_specific/triple_diff_eu.csv")
except Exception as e:
    print(f"Triple-diff failed: {e}")


# ============================================================================
# 6. PER-COUNTRY ANALYSIS BINNEN EU
# ============================================================================
hdr("Cancellation patterns per EU-country (waar zit het signaal?)")

eu_country = eu[(eu['cancel_B']+eu['operating'])==1].copy()
country_stats = eu_country.groupby('Region minor').agg(
    n_total=('Record ID','count'),
    n_cancelled=('cancel_B','sum'),
    n_cbam_exp=('T1_narrow','sum'),
    n_cbam_cancelled=('cancel_B', lambda x: ((x==1) & (eu_country.loc[x.index, 'T1_narrow']==1)).sum()),
).reset_index()
country_stats['cancel_rate'] = (country_stats['n_cancelled']/country_stats['n_total']*100).round(1)
country_stats['cancel_rate_cbam'] = np.where(country_stats['n_cbam_exp'] > 0,
    (country_stats['n_cbam_cancelled']/country_stats['n_cbam_exp']*100).round(1), np.nan)
country_stats = country_stats[country_stats['n_total'] >= 10].sort_values('n_total', ascending=False)
print(country_stats.to_string(index=False))

country_stats.to_csv(OUT / "results/eu_specific/per_country.csv", index=False)


# ============================================================================
# 7. TIMING ANALYSIS — wanneer (Year announced) zien we het patroon?
# ============================================================================
hdr("Vintage timing patroon in EU sample")

eu_vintage = eu[(eu['cancel_B']+eu['operating'])==1].groupby(['year_announced','T1_narrow']).agg(
    n=('Record ID','count'), cancelled=('cancel_B','sum'),
).reset_index()
eu_vintage['rate'] = (eu_vintage['cancelled']/eu_vintage['n']*100).round(1)
print("Cancel rate per (vintage × CBAM-exposure) in EU-27:")
eu_v_wide = eu_vintage.pivot_table(index='year_announced', columns='T1_narrow', values='rate')
eu_v_wide.columns = ['Non-CBAM (%)','CBAM-endex (%)']
eu_v_count = eu_vintage.pivot_table(index='year_announced', columns='T1_narrow', values='n')
eu_v_count.columns = ['N non-CBAM','N CBAM']
combined = pd.concat([eu_v_count, eu_v_wide], axis=1)
print(combined.tail(15))


# ============================================================================
# 8. VISUALIZATIONS — EU-specific
# ============================================================================
hdr("Visualisaties")

# Plot 1: EU vintage cohort cancel rates per CBAM-exposure
fig, ax = plt.subplots(figsize=(11, 6))
for cbam, lbl, col in [(0,'Non-CBAM (EU)','#888888'),(1,'CBAM-exposed (EU)','#882288')]:
    sub = eu_vintage[(eu_vintage['T1_narrow']==cbam) & (eu_vintage['n']>=3)]
    ax.plot(sub['year_announced'], sub['rate'], 'o-', color=col, lw=2.5, label=lbl, markersize=8)

ax.axvline(2022, ls='--', color='red', alpha=0.6, lw=2, label='CBAM agreement (Dec 2022)')
ax.axvline(2023.75, ls=':', color='darkred', alpha=0.6, lw=2, label='CBAM transitional (Oct 2023)')
ax.set_xlabel('Vintage cohort (announce year)')
ax.set_ylabel('Cancellation rate (%) — EU-27 sample, def B')
ax.set_title('EU-27 sample: Cancellation rates by CBAM exposure and vintage\n(n=1,027 EU projects, 151 cancelled total)')
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/eu_specific/eu_vintage_cancellation.pdf", bbox_inches='tight')
plt.close()

# Plot 2: Placebo coefficient stability
fit_ok = eu_did_df[eu_did_df['fit_ok']==True].copy().sort_values('treatment')
fig, ax = plt.subplots(figsize=(11, 6))
colors = ['#882288' if not p else '#888888' for p in fit_ok['is_placebo']]
ax.errorbar(range(len(fit_ok)), fit_ok['beta_EP'],
            yerr=1.96*fit_ok['se'], fmt='o', capsize=5, markersize=10,
            color='black', ecolor='gray', lw=2)
for i, (_, row) in enumerate(fit_ok.iterrows()):
    ax.scatter([i], [row['beta_EP']], color=colors[i], s=120, zorder=5,
                edgecolor='black', lw=1)
ax.axhline(0, ls='--', color='black', alpha=0.5)
ax.set_xticks(range(len(fit_ok)))
ax.set_xticklabels(fit_ok['treatment'], rotation=45, ha='right')
ax.set_ylabel(r"$\beta_{\mathrm{CBAM \times Post}}$ (EU-only DiD)")
ax.set_title('EU-only DiD: real treatment dates (purple) vs placebos (grey)\nCausal identification valid only if real >> placebos')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "figures/eu_specific/eu_placebo_chart.pdf", bbox_inches='tight')
plt.close()

print(f"\nPlots: {OUT}/figures/eu_specific/")


# ============================================================================
# EINDSAMENVATTING — KAN HET EU-SIGNAAL CAUSAAL ZIJN?
# ============================================================================
hdr("KRITIEKE EINDVERDICT: Is het EU-pattern placebo-robust?")

real_betas = eu_did_df[(eu_did_df['is_placebo']==False) & (eu_did_df['fit_ok']==True)]['beta_EP']
placebo_betas = eu_did_df[(eu_did_df['is_placebo']==True) & (eu_did_df['fit_ok']==True)]['beta_EP']

print(f"\nReal treatment β_EP (CBAM_2022, CBAM_2023):")
for _, r in eu_did_df[(~eu_did_df['is_placebo']) & (eu_did_df['fit_ok'])].iterrows():
    print(f"  {r['treatment']:25s}: β = {r['beta_EP']:+.3f} (p={r['p']:.3f})")

print(f"\nPlacebo β_EP:")
for _, r in eu_did_df[(eu_did_df['is_placebo']) & (eu_did_df['fit_ok'])].iterrows():
    print(f"  {r['treatment']:25s}: β = {r['beta_EP']:+.3f} (p={r['p']:.3f})")

if len(real_betas) > 0 and len(placebo_betas) > 0:
    print(f"\nGemiddelden:")
    print(f"  Real mean |β|:    {real_betas.abs().mean():.3f}")
    print(f"  Placebo mean |β|: {placebo_betas.abs().mean():.3f}")
    print(f"  Ratio real/placebo: {real_betas.abs().mean()/max(placebo_betas.abs().mean(),0.01):.2f}")
    
    if real_betas.abs().mean() > 2.0 * placebo_betas.abs().mean():
        print(f"\n✓ VERDICT: Real >> Placebo → EU-pattern is consistent met causale CBAM-impact")
    elif real_betas.abs().mean() > 1.3 * placebo_betas.abs().mean():
        print(f"\n~ VERDICT: Real moderately > Placebo → suggestief maar niet conclusief")
    else:
        print(f"\n✗ VERDICT: Real ≈ Placebo → EU-pattern is GEEN CBAM-causaal effect, mogelijk algemene vintage-trend")
