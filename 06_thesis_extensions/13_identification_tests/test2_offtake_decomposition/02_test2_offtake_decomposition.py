"""
TEST 2 v2: Offtake mechanism decomposition.

Two analyses:
A) Blue-Green hazard differential heterogeneity across channels (channel × tech)
B) Offtake-commitment effect heterogeneity across channels (offtake × channel)
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
warnings.filterwarnings('ignore')

import statsmodels.formula.api as smf
from scipy.stats import chi2

# ----------------------------------------
# DATA LOADING + DEFINITIONS (same as v1)
# ----------------------------------------
SP_PATH = "../../../01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
df = pd.read_excel(SP_PATH, sheet_name='Export')

df['tech_class'] = 'Other'
df.loc[df['Technology2'] == 'Electrolysis', 'tech_class'] = 'Green'
df.loc[df['Technology2'] == 'Fossil with CCS', 'tech_class'] = 'Blue'
bg = df[df['tech_class'].isin(['Blue', 'Green'])].copy()

# Rename columns with spaces for patsy compatibility
bg = bg.rename(columns={
    'Region major': 'Region_major',
    'Primary end use sector': 'end_use_sector',
    'Year announced': 'Year_announced',
    'Output capacity per year': 'capacity_per_year',
    'Capex support': 'capex_support',
    'Record ID': 'Record_ID',
})

status = bg['project_status'].astype(str).str.lower()
bg['event_any'] = ((status.str.contains('cancel', na=False)) | 
                    (status.str.contains('on-hold|on hold|paused', na=False)) | 
                    (status.str.contains('decommiss', na=False))).astype(int)

def channel_proxy(sec):
    if pd.isna(sec) or sec == 'Unknown':
        return 'Unknown'
    s = str(sec).lower()
    if 'chemical feedstock' in s or 'refinery' in s:
        return 'mu_proxy'
    if 'power' in s or 'industry (other)' in s:
        return 'sigma_proxy'
    if 'transport' in s or 'gas grid' in s:
        return 'eta_proxy'
    return 'Other'

bg['channel_proxy'] = bg['end_use_sector'].apply(channel_proxy)
bg['has_offtake'] = bg['Offtaker'].notna().astype(int)
bg['is_blue'] = (bg['tech_class'] == 'Blue').astype(int)
bg['year_num'] = pd.to_numeric(bg['Year_announced'], errors='coerce')
bg['log_cap'] = np.log(pd.to_numeric(bg['capacity_per_year'], errors='coerce').fillna(1) + 1)
bg['has_capex_support'] = bg['capex_support'].notna().astype(int)

main = bg[bg['channel_proxy'].isin(['mu_proxy', 'sigma_proxy', 'eta_proxy'])].copy()
print(f"Analysis sample: n={len(main)}, events={main['event_any'].sum()}, offtake-committed={main['has_offtake'].sum()}")

# ============================================================
# ANALYSIS A: Blue × channel heterogeneity
# ============================================================
print("\n" + "="*72)
print("ANALYSIS A: Blue-Green event differential heterogeneity across channels")
print("="*72)

f_main = ("event_any ~ is_blue * C(channel_proxy, Treatment(reference='sigma_proxy')) "
          "+ log_cap + has_capex_support + C(Region_major, Treatment(reference='North America')) "
          "+ year_num")
m_main = smf.logit(f_main, data=main).fit(disp=False)
print(m_main.summary2().tables[1].round(3).to_string())

# Channel-specific Blue coefficients
print("\nBlue effect by channel (separate regressions, marginal):")
for ch in ['mu_proxy', 'sigma_proxy', 'eta_proxy']:
    sub = main[main['channel_proxy'] == ch]
    if (sub['is_blue'].sum() >= 5) and (sub['event_any'].sum() >= 10):
        try:
            m = smf.logit("event_any ~ is_blue + log_cap + has_capex_support + C(Region_major) + year_num",
                         data=sub).fit(disp=False)
            print(f"  {ch:14s}: Blue β = {m.params['is_blue']:+.3f}  SE = {m.bse['is_blue']:.3f}  "
                  f"p = {m.pvalues['is_blue']:.4f}  n_blue = {sub['is_blue'].sum()}  events = {sub['event_any'].sum()}")
        except Exception as e:
            print(f"  {ch}: failed — {e}")

# LR test
m_null = smf.logit("event_any ~ is_blue + C(channel_proxy, Treatment(reference='sigma_proxy')) "
                   "+ log_cap + has_capex_support + C(Region_major) + year_num",
                   data=main).fit(disp=False)
lr_stat = 2 * (m_main.llf - m_null.llf)
df_diff = int(m_main.df_model - m_null.df_model)
lr_p = 1 - chi2.cdf(lr_stat, df_diff)
print(f"\nLR test of Blue × channel heterogeneity:")
print(f"  LR = {lr_stat:.3f}, df = {df_diff}, p = {lr_p:.4f}  "
      f"→ {'REJECT' if lr_p < 0.10 else 'CANNOT reject'} homogeneity at p<0.10")

# ============================================================
# ANALYSIS B: Offtake × channel heterogeneity (the Paper 3 claim)
# ============================================================
print("\n" + "="*72)
print("ANALYSIS B: Offtake-commitment effect heterogeneity across channels")
print("(This is the central Paper 3 sigma-channel mechanism test)")
print("="*72)

# Full pooled with offtake × channel interaction
f_offtake = ("event_any ~ has_offtake * C(channel_proxy, Treatment(reference='sigma_proxy')) "
             "+ is_blue + log_cap + has_capex_support + C(Region_major) + year_num")
m_off = smf.logit(f_offtake, data=main).fit(disp=False)
print(m_off.summary2().tables[1].round(3).to_string())

# Channel-specific offtake effects
print("\nOfftake-commitment effect by channel (separate regressions):")
for ch in ['mu_proxy', 'sigma_proxy', 'eta_proxy']:
    sub = main[main['channel_proxy'] == ch]
    n_off = sub['has_offtake'].sum()
    n_no_off = (1 - sub['has_offtake']).sum()
    if n_off >= 20 and n_no_off >= 50 and sub['event_any'].sum() >= 20:
        try:
            m = smf.logit("event_any ~ has_offtake + is_blue + log_cap + has_capex_support "
                         "+ C(Region_major) + year_num", data=sub).fit(disp=False)
            print(f"  {ch:14s}: Offtake β = {m.params['has_offtake']:+.3f}  SE = {m.bse['has_offtake']:.3f}  "
                  f"p = {m.pvalues['has_offtake']:.4f}  n_offtake = {int(n_off)}  events = {int(sub['event_any'].sum())}")
        except Exception as e:
            print(f"  {ch}: failed — {e}")
    else:
        print(f"  {ch:14s}: SKIPPED (n_offtake={int(n_off)}, n_no_offtake={int(n_no_off)}, events={int(sub['event_any'].sum())}) — insufficient")

# LR test for offtake heterogeneity
m_off_null = smf.logit("event_any ~ has_offtake + C(channel_proxy, Treatment(reference='sigma_proxy')) "
                       "+ is_blue + log_cap + has_capex_support + C(Region_major) + year_num",
                       data=main).fit(disp=False)
lr_stat = 2 * (m_off.llf - m_off_null.llf)
df_diff = int(m_off.df_model - m_off_null.df_model)
lr_p = 1 - chi2.cdf(lr_stat, df_diff)
print(f"\nLR test of Offtake × channel heterogeneity:")
print(f"  LR = {lr_stat:.3f}, df = {df_diff}, p = {lr_p:.4f}  "
      f"→ {'REJECT' if lr_p < 0.10 else 'CANNOT reject'} homogeneity at p<0.10")
print(f"\nINTERPRETATION:")
print(f"  - If offtake is uniformly negative across channels: multi-channel co-operation (reviewer's concern confirmed)")
print(f"  - If offtake is most negative in sigma_proxy: sigma-channel dominant (Paper 3 claim supported)")
print(f"  - If offtake is most negative in mu_proxy: mu-channel dominant (Paper 3 claim REJECTED)")

# Save model results
out = []
for ch in ['mu_proxy', 'sigma_proxy', 'eta_proxy']:
    sub = main[main['channel_proxy'] == ch]
    if sub['has_offtake'].sum() >= 20 and sub['event_any'].sum() >= 20:
        try:
            m = smf.logit("event_any ~ has_offtake + is_blue + log_cap + has_capex_support "
                         "+ C(Region_major) + year_num", data=sub).fit(disp=False)
            out.append({
                'channel': ch,
                'n': len(sub),
                'n_offtake': int(sub['has_offtake'].sum()),
                'events': int(sub['event_any'].sum()),
                'offtake_coef': m.params['has_offtake'],
                'offtake_se': m.bse['has_offtake'],
                'offtake_p': m.pvalues['has_offtake'],
                'odds_ratio': np.exp(m.params['has_offtake']),
            })
        except Exception:
            pass
res = pd.DataFrame(out)
print(f"\n\nFinal channel-stratified offtake effect table:")
print(res.round(3).to_string(index=False))
res.to_csv("offtake_by_channel_logit_results.csv", index=False)
print("\nSaved: offtake_by_channel_logit_results.csv")
