"""
TEST 3: Event-study identification via exogenous shocks

Approach: Use four well-identified events in 2019-2022 to separate pi-shocks
from sigma-shocks. Test whether Blue-Green cancellation hazard differential
responds differently to pi-events vs sigma-events.

EVENTS (with rationale for classification):
- EU Green Deal announcement: 11 Dec 2019 (pi+, large regime credibility shift)
- COVID-19 pandemic onset: 11 Mar 2020 (sigma+, market volatility shock)
- Russian invasion of Ukraine: 24 Feb 2022 (sigma+, energy volatility shock)
- Inflation Reduction Act passage: 16 Aug 2022 (pi+, US regime credibility shift)

Identification logic: If Blue-Green differential responds significantly to
pi-events but NOT sigma-events (or vice versa), pi and sigma have empirically
distinguishable effects via the exogenous shocks. If responses are similar,
they remain non-separable even with exogenous variation.

CAVEAT: IRA (Aug 2022) and Ukraine invasion (Feb 2022) are close in time,
which may confound event-specific effects. We address this with placebo tests
and event-specific stratification.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
warnings.filterwarnings('ignore')

import statsmodels.formula.api as smf
from scipy.stats import chi2

SP_PATH = "../../../01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"

# ----------------------------------------
# EVENT DEFINITIONS
# ----------------------------------------
EVENTS = {
    'EU_Green_Deal':  {'date': '2019-12-11', 'type': 'pi',    'pi_loading': +1.0, 'sigma_loading': 0.0},
    'COVID':          {'date': '2020-03-11', 'type': 'sigma', 'pi_loading': 0.0,  'sigma_loading': +1.0},
    'Ukraine':        {'date': '2022-02-24', 'type': 'sigma', 'pi_loading': +0.2, 'sigma_loading': +1.0},  # mild pi too
    'IRA':            {'date': '2022-08-16', 'type': 'pi',    'pi_loading': +1.0, 'sigma_loading': 0.0},
}
print("Events:")
for k, v in EVENTS.items():
    print(f"  {k:20s}: {v['date']} ({v['type']})")

# Window: 6 months before to 6 months after event
WINDOW_MONTHS = 6

# ----------------------------------------
# DATA LOAD
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

bg['date_announced'] = pd.to_datetime(bg['date_announced'], errors='coerce')
print(f"\nRaw Blue+Green: {len(bg)}, with announcement date: {bg['date_announced'].notna().sum()}")

# Event definitions (cancel + on-hold + decom)
status = bg['project_status'].astype(str).str.lower()
bg['event_any'] = ((status.str.contains('cancel', na=False)) |
                    (status.str.contains('on-hold|on hold|paused', na=False)) |
                    (status.str.contains('decommiss', na=False))).astype(int)
bg['is_blue'] = (bg['tech_class'] == 'Blue').astype(int)
bg['log_cap'] = np.log(pd.to_numeric(bg['capacity_per_year'], errors='coerce').fillna(1) + 1)
bg['has_capex_support'] = bg['capex_support'].notna().astype(int)
bg['year_num'] = pd.to_numeric(bg['year_announced'], errors='coerce')

# ----------------------------------------
# EVENT-WINDOW ASSIGNMENT
# Each project gets dummies for being announced in each event's window
# ----------------------------------------
for evt_name, evt_info in EVENTS.items():
    evt_date = pd.Timestamp(evt_info['date'])
    window_start = evt_date - pd.DateOffset(months=WINDOW_MONTHS)
    window_end = evt_date + pd.DateOffset(months=WINDOW_MONTHS)
    bg[f'in_window_{evt_name}'] = ((bg['date_announced'] >= window_start) & 
                                    (bg['date_announced'] <= window_end)).astype(int)

# Aggregate pi-shock and sigma-shock windows
bg['in_pi_window'] = (bg['in_window_EU_Green_Deal'] | bg['in_window_IRA']).astype(int)
bg['in_sigma_window'] = (bg['in_window_COVID'] | bg['in_window_Ukraine']).astype(int)
bg['in_any_event_window'] = (bg['in_pi_window'] | bg['in_sigma_window']).astype(int)

print(f"\nEvent-window coverage:")
print(f"  In pi-event window (Green Deal | IRA):     {bg['in_pi_window'].sum()} projects")
print(f"  In sigma-event window (COVID | Ukraine):   {bg['in_sigma_window'].sum()} projects")
print(f"  In any event window:                       {bg['in_any_event_window'].sum()} projects")
print(f"  Outside all event windows (control):       {(1 - bg['in_any_event_window']).sum()} projects")

# Filter to projects with announcement date
sample = bg.dropna(subset=['date_announced', 'year_num', 'Region_major']).copy()
print(f"\nFinal analysis sample: n={len(sample)}, events={sample['event_any'].sum()}, blue={sample['is_blue'].sum()}")

# ----------------------------------------
# ANALYSIS A: Differential response to pi-events vs sigma-events
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS A: Pooled — Blue x pi-event vs Blue x sigma-event")
print("="*72)

f_main = ("event_any ~ is_blue + in_pi_window + in_sigma_window "
          "+ is_blue:in_pi_window + is_blue:in_sigma_window "
          "+ log_cap + has_capex_support + C(Region_major) + year_num")
m_main = smf.logit(f_main, data=sample).fit(disp=False)
print(m_main.summary2().tables[1].round(3).to_string())

# Joint test of (Blue x pi, Blue x sigma) = 0
W1 = m_main.wald_test('is_blue:in_pi_window = 0, is_blue:in_sigma_window = 0', scalar=False)
print(f"\nJoint Wald test of (Blue x pi-event, Blue x sigma-event) = 0:")
print(f"  Wald chi2 = {float(W1.statistic):.3f}, df = {W1.df_denom}, p = {float(W1.pvalue):.4f}")
print(f"  → {'REJECT' if float(W1.pvalue) < 0.10 else 'CANNOT reject'} joint null")

# Equal loadings test
W2 = m_main.wald_test('is_blue:in_pi_window = is_blue:in_sigma_window', scalar=False)
print(f"\nWald test of EQUAL loadings (Blue x pi == Blue x sigma):")
print(f"  Wald chi2 = {float(W2.statistic):.3f}, df = {W2.df_denom}, p = {float(W2.pvalue):.4f}")
print(f"  → {'Loadings DISTINCT' if float(W2.pvalue) < 0.10 else 'Loadings INDISTINGUISHABLE'} at p<0.10")

# ----------------------------------------
# ANALYSIS B: Event-by-event decomposition
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS B: Event-by-event response")
print("(Most granular — check each event individually)")
print("="*72)

f_each = ("event_any ~ is_blue "
          "+ in_window_EU_Green_Deal + is_blue:in_window_EU_Green_Deal "
          "+ in_window_COVID + is_blue:in_window_COVID "
          "+ in_window_Ukraine + is_blue:in_window_Ukraine "
          "+ in_window_IRA + is_blue:in_window_IRA "
          "+ log_cap + has_capex_support + C(Region_major) + year_num")
m_each = smf.logit(f_each, data=sample).fit(disp=False)

# Extract Blue × event interactions
print("\nBlue × event-window interaction coefficients:")
interactions = ['is_blue:in_window_EU_Green_Deal', 'is_blue:in_window_COVID',
                'is_blue:in_window_Ukraine', 'is_blue:in_window_IRA']
labels = {'is_blue:in_window_EU_Green_Deal': 'EU Green Deal (pi)',
          'is_blue:in_window_COVID': 'COVID (sigma)',
          'is_blue:in_window_Ukraine': 'Ukraine (sigma)',
          'is_blue:in_window_IRA': 'IRA (pi)'}
for term in interactions:
    if term in m_each.params:
        c = m_each.params[term]; s = m_each.bse[term]; p = m_each.pvalues[term]
        sig = ' *' if p < 0.10 else '   '
        print(f"  {labels[term]:25s}: β = {c:+.3f}  SE = {s:.3f}  p = {p:.4f}{sig}")

# Test: pi-events have SAME effect as sigma-events?
W3 = m_each.wald_test(
    'is_blue:in_window_EU_Green_Deal + is_blue:in_window_IRA '
    '= is_blue:in_window_COVID + is_blue:in_window_Ukraine',
    scalar=False)
print(f"\nWald test: (Blue x Green Deal + Blue x IRA) = (Blue x COVID + Blue x Ukraine)")
print(f"  Wald chi2 = {float(W3.statistic):.3f}, df = {W3.df_denom}, p = {float(W3.pvalue):.4f}")
print(f"  → {'pi-events DIFFER from sigma-events' if float(W3.pvalue) < 0.10 else 'pi-events INDISTINGUISHABLE from sigma-events'}")

# ----------------------------------------
# ANALYSIS C: Placebo test
# Test pre-event 6 months as "fake" event to check for selection bias
# ----------------------------------------
print("\n" + "="*72)
print("ANALYSIS C: Placebo test — same window logic, but 12 months BEFORE each event")
print("(If 'placebo events' also generate effects, the main result is suspect)")
print("="*72)

for evt_name, evt_info in EVENTS.items():
    placebo_date = pd.Timestamp(evt_info['date']) - pd.DateOffset(months=12)
    p_start = placebo_date - pd.DateOffset(months=WINDOW_MONTHS)
    p_end = placebo_date + pd.DateOffset(months=WINDOW_MONTHS)
    sample[f'placebo_{evt_name}'] = ((sample['date_announced'] >= p_start) & 
                                      (sample['date_announced'] <= p_end)).astype(int)

sample['placebo_pi'] = (sample['placebo_EU_Green_Deal'] | sample['placebo_IRA']).astype(int)
sample['placebo_sigma'] = (sample['placebo_COVID'] | sample['placebo_Ukraine']).astype(int)

f_placebo = ("event_any ~ is_blue + placebo_pi + placebo_sigma "
             "+ is_blue:placebo_pi + is_blue:placebo_sigma "
             "+ log_cap + has_capex_support + C(Region_major) + year_num")
try:
    m_pl = smf.logit(f_placebo, data=sample).fit(disp=False)
    for term in ['is_blue:placebo_pi', 'is_blue:placebo_sigma']:
        if term in m_pl.params:
            c = m_pl.params[term]; p = m_pl.pvalues[term]
            print(f"  {term:35s}: β = {c:+.3f}, p = {p:.4f}")
    Wp = m_pl.wald_test('is_blue:placebo_pi = 0, is_blue:placebo_sigma = 0', scalar=False)
    print(f"\nPlacebo joint Wald: chi2 = {float(Wp.statistic):.3f}, p = {float(Wp.pvalue):.4f}")
    print(f"  → {'Concerning: placebo events also significant' if float(Wp.pvalue) < 0.10 else 'GOOD: placebo events not significant (clean ID)'}")
except Exception as e:
    print(f"Placebo failed: {e}")

# ----------------------------------------
# Save results
# ----------------------------------------
out = {
    'analysis_A_joint_pi_sigma_wald_p': float(W1.pvalue),
    'analysis_A_equal_loadings_p': float(W2.pvalue),
    'analysis_A_pi_loading': float(m_main.params.get('is_blue:in_pi_window', np.nan)),
    'analysis_A_sigma_loading': float(m_main.params.get('is_blue:in_sigma_window', np.nan)),
    'analysis_B_pi_vs_sigma_p': float(W3.pvalue),
    'n_sample': len(sample),
    'n_events': int(sample['event_any'].sum()),
    'n_in_pi_window': int(sample['in_pi_window'].sum()),
    'n_in_sigma_window': int(sample['in_sigma_window'].sum()),
}
pd.DataFrame([out]).to_csv("test3_results_summary.csv", index=False)
print(f"\nSummary saved.")
print(f"\n=== VERDICT ===")
if float(W2.pvalue) < 0.10 and float(W3.pvalue) < 0.10:
    print("→ Pi-events and sigma-events generate DISTINGUISHABLE Blue-Green hazard responses")
    print("→ Identification via exogenous variation: SUCCESSFUL")
    print("→ Proposition 1 / 7 verdedigbaar via event-study evidence")
else:
    print("→ Pi-events and sigma-events generate INDISTINGUISHABLE Blue-Green responses")
    print("→ Identification via exogenous variation: NOT SUCCESSFUL")
    print("→ Consistent with Tests 1+2 — multi-channel reality confirmed")
