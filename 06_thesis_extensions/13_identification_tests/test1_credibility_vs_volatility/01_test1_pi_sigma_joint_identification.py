"""
TEST 1: Policy credibility (pi) jointly identified from general volatility (sigma)?

Approach: Pooled logit event model with Blue x carbon-price interaction split
into pi-conditional and sigma-conditional components.

If both pi-coefficient and sigma-coefficient are jointly significant with
distinct loadings (after controlling for their correlation), pi and sigma
are empirically separable — Proposition 1 verdedigbaar.

If only one is significant, or if correlation between pi and sigma proxies
is too high (VIF explosion), they are NOT separable — Proposition 1 falls.

PROXIES
- pi_t: BBD US EPU index (USEPUINDXD) — text-based policy-specific uncertainty
- sigma_t: VIXCLS (general market volatility) AND EWMA of EUA returns (carbon-specific)

PROJECT-LEVEL MAPPING
Each project gets the pi_t and sigma_t value of its announcement month.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
warnings.filterwarnings('ignore')

import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy.stats import chi2

# ----------------------------------------
# DATA LOAD
# ----------------------------------------
SP_PATH = "../../../01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MP_PATH = "../../../01_data/intermediate/master_panel_monthly.csv"

# Master panel (monthly): contains EPU, VIX, EUA, etc.
mp = pd.read_csv(MP_PATH)
mp['date'] = pd.to_datetime(mp['date'])
mp['year'] = mp['date'].dt.year
mp['month'] = mp['date'].dt.month
# Some columns are duplicated per month (multiple rows per date); average to one observation per month
mp_monthly = mp.groupby(['year', 'month']).agg({
    'USEPUINDXD': 'mean',     # US Economic Policy Uncertainty (BBD)
    'GEPUCURRENT': 'mean',    # Global EPU (BBD)
    'VIXCLS': 'mean',         # VIX
    'eua_phase3': 'mean',
    'eua_phase4': 'mean',
    'eua': 'mean',
}).reset_index()

# Construct combined EUA price (phase 3 + phase 4 + eua)
mp_monthly['eua_combined'] = mp_monthly[['eua_phase3', 'eua_phase4', 'eua']].mean(axis=1)
mp_monthly['eua_return'] = np.log(mp_monthly['eua_combined']).diff()

# EWMA volatility of EUA returns (sigma-proxy, carbon-specific)
mp_monthly['eua_ewma_var'] = mp_monthly['eua_return'].ewm(alpha=0.06, adjust=False).var()
mp_monthly['eua_sigma'] = np.sqrt(mp_monthly['eua_ewma_var'])

# Normalize all proxies to z-scores for interpretability
for col in ['USEPUINDXD', 'GEPUCURRENT', 'VIXCLS', 'eua_sigma']:
    mp_monthly[f'{col}_z'] = (mp_monthly[col] - mp_monthly[col].mean()) / mp_monthly[col].std()

# Pi and Sigma proxies
mp_monthly['pi_proxy'] = mp_monthly['USEPUINDXD_z']
mp_monthly['sigma_proxy_general'] = mp_monthly['VIXCLS_z']
mp_monthly['sigma_proxy_carbon'] = mp_monthly['eua_sigma_z']

print("=== Proxy correlation (THE KEY DIAGNOSTIC) ===")
proxies = mp_monthly[['pi_proxy', 'sigma_proxy_general', 'sigma_proxy_carbon']].dropna()
print(proxies.corr().round(3))
print()
print(f"Sample correlation pi vs sigma_general:  {proxies['pi_proxy'].corr(proxies['sigma_proxy_general']):.3f}")
print(f"Sample correlation pi vs sigma_carbon:   {proxies['pi_proxy'].corr(proxies['sigma_proxy_carbon']):.3f}")
print(f"Sample correlation sigma_general vs sigma_carbon: {proxies['sigma_proxy_general'].corr(proxies['sigma_proxy_carbon']):.3f}")
print()

# ----------------------------------------
# PROJECT LOAD + MERGE
# ----------------------------------------
df = pd.read_excel(SP_PATH, sheet_name='Export')
df['tech_class'] = 'Other'
df.loc[df['Technology2'] == 'Electrolysis', 'tech_class'] = 'Green'
df.loc[df['Technology2'] == 'Fossil with CCS', 'tech_class'] = 'Blue'
bg = df[df['tech_class'].isin(['Blue', 'Green'])].copy()

bg = bg.rename(columns={
    'Year announced': 'year_announced',
    'Date announced': 'date_announced',
    'Region major': 'Region_major',
    'Primary end use sector': 'end_use_sector',
    'Output capacity per year': 'capacity_per_year',
    'Capex support': 'capex_support',
    'Record ID': 'Record_ID',
})

# Extract month from date_announced
bg['date_announced'] = pd.to_datetime(bg['date_announced'], errors='coerce')
bg['announce_year'] = bg['date_announced'].dt.year
bg['announce_month'] = bg['date_announced'].dt.month
# Fallback: use year_announced if date_announced is missing
bg['announce_year'] = bg['announce_year'].fillna(pd.to_numeric(bg['year_announced'], errors='coerce'))
bg['announce_month'] = bg['announce_month'].fillna(6)  # mid-year default

# Merge proxies to projects on (announce_year, announce_month)
bg = bg.merge(
    mp_monthly[['year', 'month', 'pi_proxy', 'sigma_proxy_general', 'sigma_proxy_carbon', 'eua_combined']],
    left_on=['announce_year', 'announce_month'],
    right_on=['year', 'month'],
    how='left'
)
print(f"Merged sample: n={len(bg)}, pi_proxy non-null: {bg['pi_proxy'].notna().sum()}")

# Event definition (same as Test 2 — broad: cancel + on-hold + decom)
status = bg['project_status'].astype(str).str.lower()
bg['event_any'] = ((status.str.contains('cancel', na=False)) |
                    (status.str.contains('on-hold|on hold|paused', na=False)) |
                    (status.str.contains('decommiss', na=False))).astype(int)
bg['is_blue'] = (bg['tech_class'] == 'Blue').astype(int)
bg['log_cap'] = np.log(pd.to_numeric(bg['capacity_per_year'], errors='coerce').fillna(1) + 1)
bg['has_capex_support'] = bg['capex_support'].notna().astype(int)
bg['year_num'] = pd.to_numeric(bg['announce_year'], errors='coerce')

# Sample restriction: drop missing pi/sigma observations
sample = bg.dropna(subset=['pi_proxy', 'sigma_proxy_general', 'sigma_proxy_carbon']).copy()
print(f"Final analysis sample: n={len(sample)}, events={sample['event_any'].sum()}, blue={sample['is_blue'].sum()}")
print()

# ----------------------------------------
# ANALYSIS 1: Joint identification with both proxies
# ----------------------------------------
print("="*72)
print("ANALYSIS 1: Joint pi + sigma_general (VIX) in Blue interaction")
print("="*72)

# Model: P(event) = f(blue + blue*pi + blue*sigma + controls)
f1 = ("event_any ~ is_blue + is_blue:pi_proxy + is_blue:sigma_proxy_general "
      "+ pi_proxy + sigma_proxy_general "
      "+ log_cap + has_capex_support + C(Region_major) + year_num")
m1 = smf.logit(f1, data=sample).fit(disp=False)
print(m1.summary2().tables[1].round(3).to_string())

# Joint Wald test for pi vs sigma interactions
print(f"\nJoint Wald test of (is_blue:pi_proxy, is_blue:sigma_proxy_general) = 0:")
W = m1.wald_test('is_blue:pi_proxy = 0, is_blue:sigma_proxy_general = 0', scalar=False)
print(f"  Wald chi2 = {float(W.statistic):.3f}, df = {W.df_denom}, p = {float(W.pvalue):.4f}")

# Test if loadings are equal (would mean indistinguishable)
W2 = m1.wald_test('is_blue:pi_proxy = is_blue:sigma_proxy_general', scalar=False)
print(f"\nWald test of EQUAL loadings (is_blue:pi == is_blue:sigma_general):")
print(f"  Wald chi2 = {float(W2.statistic):.3f}, df = {W2.df_denom}, p = {float(W2.pvalue):.4f}")
print(f"  → {'Can REJECT equality (loadings distinct)' if float(W2.pvalue) < 0.10 else 'CANNOT reject equality (loadings indistinguishable)'} at p<0.10")

# ----------------------------------------
# ANALYSIS 2: Carbon-specific sigma (EUA EWMA)
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS 2: pi (BBD EPU) + sigma_carbon (EUA EWMA volatility)")
print("(More theoretically targeted: sigma here is carbon-payoff volatility,")
print(" which is what the Dixit-Pindyck framework directly considers)")
print("="*72)

f2 = ("event_any ~ is_blue + is_blue:pi_proxy + is_blue:sigma_proxy_carbon "
      "+ pi_proxy + sigma_proxy_carbon "
      "+ log_cap + has_capex_support + C(Region_major) + year_num")
m2 = smf.logit(f2, data=sample).fit(disp=False)
print(m2.summary2().tables[1].round(3).to_string())

W3 = m2.wald_test('is_blue:pi_proxy = 0, is_blue:sigma_proxy_carbon = 0', scalar=False)
print(f"\nJoint Wald test of (is_blue:pi_proxy, is_blue:sigma_proxy_carbon) = 0:")
print(f"  Wald chi2 = {float(W3.statistic):.3f}, df = {W3.df_denom}, p = {float(W3.pvalue):.4f}")

W4 = m2.wald_test('is_blue:pi_proxy = is_blue:sigma_proxy_carbon', scalar=False)
print(f"\nWald test of EQUAL loadings (is_blue:pi == is_blue:sigma_carbon):")
print(f"  Wald chi2 = {float(W4.statistic):.3f}, df = {W4.df_denom}, p = {float(W4.pvalue):.4f}")

# ----------------------------------------
# ANALYSIS 3: Variance Inflation Factor (multicollinearity diagnostic)
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS 3: Multicollinearity diagnostic — Variance Inflation Factors")
print("(VIF > 5 = problematic; VIF > 10 = severe collinearity)")
print("="*72)
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif

# Construct interaction terms
X = pd.DataFrame({
    'is_blue': sample['is_blue'],
    'pi_proxy': sample['pi_proxy'],
    'sigma_proxy_general': sample['sigma_proxy_general'],
    'sigma_proxy_carbon': sample['sigma_proxy_carbon'],
    'blue_x_pi': sample['is_blue'] * sample['pi_proxy'],
    'blue_x_sigma_general': sample['is_blue'] * sample['sigma_proxy_general'],
    'blue_x_sigma_carbon': sample['is_blue'] * sample['sigma_proxy_carbon'],
}).dropna()
X = sm.add_constant(X)
print(f"\nVIF table (n={len(X)}):")
for i, col in enumerate(X.columns):
    if col == 'const':
        continue
    try:
        v = vif(X.values, i)
        print(f"  {col:28s}: {v:6.2f}{' ← PROBLEM' if v > 5 else ''}{' ← SEVERE' if v > 10 else ''}")
    except Exception:
        pass

# ----------------------------------------
# ANALYSIS 4: Separate single-channel models for benchmark
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS 4: Benchmark — single-channel models")
print("(Compare AIC/BIC: which proxy alone fits best?)")
print("="*72)

base = "event_any ~ is_blue + log_cap + has_capex_support + C(Region_major) + year_num"
m_base = smf.logit(base, data=sample).fit(disp=False)

for proxy_name in ['pi_proxy', 'sigma_proxy_general', 'sigma_proxy_carbon']:
    f = base + f" + {proxy_name} + is_blue:{proxy_name}"
    m_p = smf.logit(f, data=sample).fit(disp=False)
    lr = 2 * (m_p.llf - m_base.llf)
    print(f"  Add only {proxy_name:25s}: ΔLL={m_p.llf - m_base.llf:+.2f}, ΔAIC={m_p.aic - m_base.aic:+.2f}, "
          f"LR={lr:.2f}, p={1-chi2.cdf(lr, 2):.4f}")

# Save key results
res_summary = {
    'correlation_pi_vs_sigma_general': proxies['pi_proxy'].corr(proxies['sigma_proxy_general']),
    'correlation_pi_vs_sigma_carbon': proxies['pi_proxy'].corr(proxies['sigma_proxy_carbon']),
    'joint_pi_sigma_general_wald_p': float(W.pvalue),
    'joint_pi_sigma_carbon_wald_p': float(W3.pvalue),
    'loadings_distinct_general_p': float(W2.pvalue),
    'loadings_distinct_carbon_p': float(W4.pvalue),
    'pi_loading_general_model': float(m1.params.get('is_blue:pi_proxy', np.nan)),
    'sigma_general_loading': float(m1.params.get('is_blue:sigma_proxy_general', np.nan)),
    'pi_loading_carbon_model': float(m2.params.get('is_blue:pi_proxy', np.nan)),
    'sigma_carbon_loading': float(m2.params.get('is_blue:sigma_proxy_carbon', np.nan)),
    'n_sample': len(sample),
    'n_events': int(sample['event_any'].sum()),
}
pd.DataFrame([res_summary]).to_csv("test1_results_summary.csv", index=False)
print(f"\n\n=== KEY DIAGNOSTIC INTERPRETATION ===")
print(f"Correlation pi vs sigma_general: {res_summary['correlation_pi_vs_sigma_general']:.3f}")
print(f"Correlation pi vs sigma_carbon:  {res_summary['correlation_pi_vs_sigma_carbon']:.3f}")
print(f"Pi-loading distinct from sigma (general): p = {res_summary['loadings_distinct_general_p']:.4f}")
print(f"Pi-loading distinct from sigma (carbon): p = {res_summary['loadings_distinct_carbon_p']:.4f}")
print()
print("VERDICT:")
if res_summary['loadings_distinct_carbon_p'] < 0.10 and abs(res_summary['correlation_pi_vs_sigma_carbon']) < 0.5:
    print("  → pi AND sigma JOINTLY IDENTIFIABLE (distinct loadings, moderate correlation)")
    print("  → Proposition 1 (credibility-conditional threshold) verdedigbaar")
else:
    print("  → pi and sigma NOT jointly identifiable")
    print("  → Proposition 1 must be softened to interpretive layer")
print("\nResults saved: test1_results_summary.csv")
