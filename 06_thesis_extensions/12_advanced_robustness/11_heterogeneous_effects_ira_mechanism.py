"""
11_heterogeneous_effects_ira_mechanism.py — drie analyses in één script.
A. Heterogene effecten — subgroup-DiD per sector / sponsor / size
B. IRA-DiD heroverweging — schonere sudden shock dan CBAM
C. Mechanism testing — wat MODEREERT de Blue × treatment effect?
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
def hdr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)


# DATA
hdr("Load S&P sample met moderators")
sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled','Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned','Partially commissioned']).astype(int)
sp['is_blue'] = (sp['Technology.1']=='Fossil with CCS').astype(int)
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))

def cbam_endex(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if any(k in dl for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']): return 1
    if 'chemical feedstock' in sl or 'refinery feedstock' in sl: return 1
    return 0

def sector_label(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if 'steel' in dl or 'iron' in dl: return 'Steel'
    if 'ammonia' in dl or 'fertilizer' in dl: return 'Ammonia'
    if 'refinery' in dl or 'refinery feedstock' in sl: return 'Refining'
    if 'chemical' in dl or 'chemical feedstock' in sl: return 'Chemicals'
    if 'cement' in dl: return 'Cement'
    return 'Other'

def sponsor_type(text):
    if pd.isna(text): return 'Unknown'
    t = str(text).lower()
    majors = ['exxon','shell','bp ','chevron','total','equinor','aramco','eni','repsol','marathon',
              'phillips','occidental','suncor','conoco','petrobras','sinopec','cnpc','petronas',
              'enbridge','enagas','engie','rwe','eon','iberdrola','vattenfall','statoil']
    industrial = ['linde','air liquide','airgas','praxair','airproducts','messer','air products']
    if any(m in t for m in majors): return 'Major'
    if any(i in t for i in industrial): return 'IndustrialGas'
    if 'gov' in t or 'ministry' in t or 'state' in t or 'national' in t: return 'Government'
    return 'Independent'

sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)
sp['sector'] = sp.apply(lambda r: sector_label(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)

# Find sponsor column
sponsor_cols = [c for c in sp.columns if 'sponsor' in c.lower() or 'owner' in c.lower() or 'operator' in c.lower()]
print(f"Sponsor columns found: {sponsor_cols}")
if sponsor_cols:
    sp['sponsor_simple'] = sp[sponsor_cols[0]].apply(sponsor_type)
else:
    sp['sponsor_simple'] = 'Unknown'

sp['is_EU'] = (sp['Region major']=='Europe (EU-27)').astype(int)

# Find country column for US identification
country_col = None
for c in ['Country','country','Region','region','Region detail']:
    if c in sp.columns:
        country_col = c
        break
if country_col:
    sp['is_US'] = sp[country_col].astype(str).str.lower().str.contains('united states|^us$| usa').astype(int)
else:
    sp['is_US'] = (sp['Region major']=='North America').astype(int)
print(f"Country col used: {country_col}, US count: {sp['is_US'].sum()}")

sp['post_2022'] = (sp['year_announced'] >= 2022).astype(int)
sp['cbam_x_post'] = sp['cbam_endex'] * sp['post_2022']
sp['is_pem'] = 1 - sp['is_blue']
sp['cap_q'] = pd.qcut(sp['log_cap'], q=4, labels=['Q1_smallest','Q2','Q3','Q4_largest'], duplicates='drop')

finished = sp[(sp['cancel_B']+sp['operating'])==1].copy().reset_index(drop=True)
eu_finished = finished[finished['is_EU']==1].copy().reset_index(drop=True)
print(f"\nFinished sample: N = {len(finished)} ({finished['cancel_B'].sum()} cancellations)")
print(f"EU finished:     N = {len(eu_finished)} ({eu_finished['cancel_B'].sum()} cancellations)")
print(f"\nSector breakdown:")
print(finished['sector'].value_counts())
print(f"\nSponsor breakdown:")
print(finished['sponsor_simple'].value_counts())


# A. HETEROGENE EFFECTEN
hdr("A. Heterogene effecten")

print("A.1 — DiD per CBAM-sector (EU CBAM-exposed subset)")
eu_cbam = eu_finished[eu_finished['cbam_endex']==1].copy()
sector_results = []
for s in eu_cbam['sector'].dropna().unique():
    sub = eu_cbam[eu_cbam['sector']==s].copy()
    if len(sub) < 20 or sub['cancel_B'].sum() < 2: continue
    try:
        X = sm.add_constant(sub[['is_blue','log_cap','post_2022']])
        y = sub['cancel_B'].astype(float)
        m = sm.OLS(y, X).fit(cov_type='HC1')
        b, se, p = m.params['post_2022'], m.bse['post_2022'], m.pvalues['post_2022']
        sector_results.append({'subgroup':s, 'N':len(sub),
                                'cancel_rate':float(sub['cancel_B'].mean()),
                                'beta_post':b, 'se':se, 'p':p,
                                'ci_lo':b-1.96*se, 'ci_hi':b+1.96*se})
    except Exception as e:
        print(f"   {s}: failed ({e})")
sector_df = pd.DataFrame(sector_results)
print(sector_df.round(4).to_string(index=False))
sector_df.to_csv(OUT/"results/het_sector_did.csv", index=False)

print("\nA.2 — DiD per sponsor type (full sample, cbam_x_post focal)")
sponsor_results = []
for sp_lvl in finished['sponsor_simple'].dropna().unique():
    sub = finished[finished['sponsor_simple']==sp_lvl].copy()
    if len(sub) < 30 or sub['cancel_B'].sum() < 3: continue
    try:
        X = sm.add_constant(sub[['cbam_endex','post_2022','cbam_x_post','is_blue','log_cap']])
        y = sub['cancel_B'].astype(float)
        m = sm.OLS(y, X).fit(cov_type='HC1')
        b, se, p = m.params['cbam_x_post'], m.bse['cbam_x_post'], m.pvalues['cbam_x_post']
        sponsor_results.append({'subgroup':sp_lvl, 'N':len(sub),
                                  'cancel_rate':float(sub['cancel_B'].mean()),
                                  'beta_cbam_x_post':b, 'se':se, 'p':p,
                                  'ci_lo':b-1.96*se, 'ci_hi':b+1.96*se})
    except Exception as e:
        print(f"   {sp_lvl}: failed ({e})")
sponsor_df = pd.DataFrame(sponsor_results)
print(sponsor_df.round(4).to_string(index=False))
sponsor_df.to_csv(OUT/"results/het_sponsor_did.csv", index=False)

print("\nA.3 — DiD per project size quartile")
size_results = []
for q in finished['cap_q'].dropna().unique():
    sub = finished[finished['cap_q']==q].copy()
    if len(sub) < 30: continue
    try:
        X = sm.add_constant(sub[['cbam_endex','post_2022','cbam_x_post','is_blue','log_cap','is_EU']])
        y = sub['cancel_B'].astype(float)
        m = sm.OLS(y, X).fit(cov_type='HC1')
        b, se, p = m.params['cbam_x_post'], m.bse['cbam_x_post'], m.pvalues['cbam_x_post']
        size_results.append({'subgroup':str(q), 'N':len(sub),
                              'cancel_rate':float(sub['cancel_B'].mean()),
                              'beta_cbam_x_post':b, 'se':se, 'p':p,
                              'ci_lo':b-1.96*se, 'ci_hi':b+1.96*se})
    except Exception as e:
        print(f"   {q}: failed ({e})")
size_df = pd.DataFrame(size_results)
print(size_df.round(4).to_string(index=False))
size_df.to_csv(OUT/"results/het_size_did.csv", index=False)


# B. IRA HEROVERWEGING
hdr("B. IRA-DiD heroverweging — schonere sudden shock")
print(f"Treatment: PEM-projecten in VS, na 16-aug-2022")
print(f"VS projecten: {finished['is_US'].sum()}, PEM-projecten: {finished['is_pem'].sum()}")
print(f"VS × PEM × Post-2022 = treated cells: {(finished['is_US']*finished['is_pem']*finished['post_2022']).sum()}")

ira = finished.copy()
ira['us_x_pem'] = ira['is_US'] * ira['is_pem']
ira['us_x_post'] = ira['is_US'] * ira['post_2022']
ira['pem_x_post'] = ira['is_pem'] * ira['post_2022']
ira['triple_ira'] = ira['is_US'] * ira['is_pem'] * ira['post_2022']

X_ira = sm.add_constant(ira[['is_US','is_pem','post_2022','us_x_pem','us_x_post','pem_x_post','triple_ira','log_cap']])
y_ira = ira['cancel_B'].astype(float)
m_ira = sm.OLS(y_ira, X_ira).fit(cov_type='HC1')
b_ira = m_ira.params['triple_ira']
se_ira = m_ira.bse['triple_ira']
p_ira = m_ira.pvalues['triple_ira']
print(f"\nIRA Triple-difference β = {b_ira:+.4f} (SE {se_ira:.4f}, p = {p_ira:.4f})")
print(f"  95% CI: [{b_ira-1.96*se_ira:+.4f}, {b_ira+1.96*se_ira:+.4f}]")
print(f"  N = {len(ira)}")

# Verdict
if p_ira < 0.05:
    verdict_ira = ("Significant " + ("negatief — IRA REDUCEERT PEM-cancellation in VS (zoals verwacht)"
                                       if b_ira < 0 else "positief — onverwacht teken"))
else:
    verdict_ira = "Informative null — IRA effect NIET identificeerbaar"
print(f"  Verdict: {verdict_ira}")

# Direct US-PEM pre/post
us_pem = ira[(ira['is_US']==1) & (ira['is_pem']==1)].copy()
print(f"\nDirect US-PEM pre/post comparison:")
print(f"  Pre-IRA  (year<2022): N={(us_pem['post_2022']==0).sum()}, cancel rate = {us_pem[us_pem['post_2022']==0]['cancel_B'].mean()*100:.1f}%")
print(f"  Post-IRA (year>=2022): N={(us_pem['post_2022']==1).sum()}, cancel rate = {us_pem[us_pem['post_2022']==1]['cancel_B'].mean()*100:.1f}%")

pd.DataFrame([{
    'spec':'IRA triple-diff (US × PEM × Post 2022)', 'N':len(ira),
    'beta':b_ira, 'se':se_ira, 'p':p_ira,
    'ci_lo':b_ira-1.96*se_ira, 'ci_hi':b_ira+1.96*se_ira,
    'verdict':verdict_ira,
}]).to_csv(OUT/"results/het_ira.csv", index=False)


# C. MECHANISM TESTING
hdr("C. Mechanism — wat MODEREERT de Blue × treatment effect?")
print("Triple-interactie spec: cancel ~ ... + Blue × log_cap + Blue × is_EU + Blue × post_2022")
finished['blue_x_logcap'] = finished['is_blue'] * finished['log_cap']
finished['blue_x_EU'] = finished['is_blue'] * finished['is_EU']
finished['blue_x_post'] = finished['is_blue'] * finished['post_2022']

X_m = sm.add_constant(finished[['is_blue','log_cap','is_EU','post_2022','cbam_endex',
                                   'blue_x_logcap','blue_x_EU','blue_x_post']])
y_m = finished['cancel_B'].astype(float)
m_m = sm.OLS(y_m, X_m).fit(cov_type='HC1')

mech_rows = []
print(f"\n{'Parameter':<20s} {'β':>10s} {'SE':>8s} {'p':>7s}  Verdict")
print("-" * 70)
for var in ['is_blue','blue_x_logcap','blue_x_EU','blue_x_post']:
    if var in m_m.params.index:
        b, se, p = m_m.params[var], m_m.bse[var], m_m.pvalues[var]
        mark = '⚠ sig' if p<0.05 else ('· marg' if p<0.10 else '(ns)')
        print(f"{var:<20s} {b:+10.4f} {se:>8.4f} {p:>7.4f}  {mark}")
        mech_rows.append({'param':var, 'beta':b, 'se':se, 'p':p})

mech_df = pd.DataFrame(mech_rows)
mech_df.to_csv(OUT/"results/het_mechanism.csv", index=False)

print(f"\nMechanism interpretation:")
b_logcap = m_m.params.get('blue_x_logcap',np.nan)
b_eu = m_m.params.get('blue_x_EU',np.nan)
b_post = m_m.params.get('blue_x_post',np.nan)
print(f"  Blue × log_capacity = {b_logcap:+.4f}: {'grotere Blue projecten fragiler' if b_logcap>0.01 else 'kleinere Blue projecten fragiler' if b_logcap<-0.01 else 'geen size-effect'}")
print(f"  Blue × is_EU = {b_eu:+.4f}: {'EU Blue fragieler dan NA Blue' if b_eu>0.01 else 'NA Blue fragieler dan EU Blue' if b_eu<-0.01 else 'geen regional differentiation'}")
print(f"  Blue × post_2022 = {b_post:+.4f}: {'Blue-fragility INTENSIVEERT post-2022' if b_post>0.01 else 'Blue-fragility DAALT post-2022' if b_post<-0.01 else 'geen tijd-trend'}")


# PLOT
hdr("Generate heterogeneity plot")
plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

ax = axes[0]
if len(sector_df) > 0:
    s_p = sector_df.sort_values('beta_post')
    ax.errorbar(s_p['beta_post'], range(len(s_p)), xerr=1.96*s_p['se'],
                 fmt='o', color='#882288', markersize=10, capsize=4, lw=1.5)
    ax.axvline(0, ls='--', color='black', alpha=0.4)
    ax.set_yticks(range(len(s_p)))
    ax.set_yticklabels([f"{x}\n(N={n})" for x, n in zip(s_p['subgroup'], s_p['N'])])
    ax.set_xlabel('Post-2022 effect on cancellation rate')
    ax.set_title('Panel A: Per-sector heterogeniteit')

ax = axes[1]
if len(sponsor_df) > 0:
    sp_p = sponsor_df.sort_values('beta_cbam_x_post')
    ax.errorbar(sp_p['beta_cbam_x_post'], range(len(sp_p)), xerr=1.96*sp_p['se'],
                 fmt='o', color='#1f77b4', markersize=10, capsize=4, lw=1.5)
    ax.axvline(0, ls='--', color='black', alpha=0.4)
    ax.set_yticks(range(len(sp_p)))
    ax.set_yticklabels([f"{x}\n(N={n})" for x, n in zip(sp_p['subgroup'], sp_p['N'])])
    ax.set_xlabel(r'$\hat\beta_{\mathrm{cbam}\times\mathrm{post}}$')
    ax.set_title('Panel B: Per-sponsor heterogeniteit')

ax = axes[2]
if len(size_df) > 0:
    sz_p = size_df.sort_values('subgroup')
    ax.errorbar(sz_p['beta_cbam_x_post'], range(len(sz_p)), xerr=1.96*sz_p['se'],
                 fmt='o', color='#2ca02c', markersize=10, capsize=4, lw=1.5)
    ax.axvline(0, ls='--', color='black', alpha=0.4)
    ax.set_yticks(range(len(sz_p)))
    ax.set_yticklabels([f"{x}\n(N={n})" for x, n in zip(sz_p['subgroup'], sz_p['N'])])
    ax.set_xlabel(r'$\hat\beta_{\mathrm{cbam}\times\mathrm{post}}$')
    ax.set_title('Panel C: Per-size quartile heterogeniteit')

plt.suptitle('Figure: Heterogeneous treatment effects (Ketel-traditie wie-wordt-geraakt)', y=1.00)
plt.tight_layout()
fig.savefig(OUT/"figures/F_heterogeneous_effects.pdf", bbox_inches='tight', dpi=120)
plt.close()
print("  → F_heterogeneous_effects.pdf")

print("\n" + "="*78)
print("KLAAR. Resultaten in 12_advanced_robustness/results/ en figures/")
print("="*78)
