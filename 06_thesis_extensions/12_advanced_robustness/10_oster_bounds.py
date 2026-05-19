"""
10_oster_bounds.py — Oster (2019) bounds voor omitted variable bias.

Beantwoordt de standaard moderne causal-inference vraag:
  "Hoe groot zou selection-on-unobservables moeten zijn t.o.v. selection-on-observables
   om jouw estimated effect te verklaren?"

Methode (Oster 2019, Journal of Business & Economic Statistics):
  1. Schat een 'restricted' model met alleen treatment: β_naive, R²_naive
  2. Schat 'unrestricted' model met alle controls: β_controlled, R²_controlled
  3. Specifeer R²_max (theoretical upper bound op explained variation)
  4. Bereken δ = bound op (selection on unobservables / selection on observables) onder
     welke β* = 0
  
Interpretatie:
  δ > 1 betekent: unobservables zouden grotere effect moeten hebben dan observables
                  om effect naar nul te brengen — robust to OVB
  δ < 1 betekent: small selection-on-unobservables (kleiner dan observables) genoeg
                  om effect naar nul te brengen — fragile to OVB
  
Standard threshold: δ ≥ 1 (Oster suggests this is "robust")
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")

def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# OSTER 2019 BOUNDS FUNCTION
# ============================================================================
def oster_delta(beta_restricted, beta_full, R_restricted, R_full, R_max, beta_star=0.0):
    """
    Compute Oster (2019) δ bound.
    
    β* = β_full - δ × (β_restricted - β_full) × (R_max - R_full) / (R_full - R_restricted)
    
    Solving for δ given target β*:
    δ = (β_full - β*) × (R_full - R_restricted) / ((β_restricted - β_full) × (R_max - R_full))
    """
    num = (beta_full - beta_star) * (R_full - R_restricted)
    denom = (beta_restricted - beta_full) * (R_max - R_full)
    
    if abs(denom) < 1e-9:
        return np.nan
    return num / denom

def oster_bias_adj_beta(beta_restricted, beta_full, R_restricted, R_full, R_max, delta=1.0):
    """
    Compute Oster bias-adjusted β assuming δ = delta.
    
    β_adjusted = β_full - δ × (β_restricted - β_full) × (R_max - R_full) / (R_full - R_restricted)
    """
    bias = delta * (beta_restricted - beta_full) * (R_max - R_full) / (R_full - R_restricted)
    return beta_full - bias


# ============================================================================
# LOAD DATA
# ============================================================================
hdr("Load S&P sample")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)
sp['is_blue'] = (sp['Technology.1'] == 'Fossil with CCS').astype(int)
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))

def cbam_endex(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if any(k in dl for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']):
        return 1
    if 'chemical feedstock' in sl or 'refinery feedstock' in sl:
        return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)
sp['is_EU'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['post_2022'] = (sp['year_announced'] >= 2022).astype(int)
sp['cbam_x_post'] = sp['cbam_endex'] * sp['post_2022']
sp['EU_x_cbam'] = sp['is_EU'] * sp['cbam_endex']
sp['EU_x_post'] = sp['is_EU'] * sp['post_2022']
sp['triple'] = sp['is_EU'] * sp['cbam_endex'] * sp['post_2022']

finished = sp[(sp['cancel_B']+sp['operating'])==1].copy().reset_index(drop=True)
eu = finished[finished['is_EU']==1].copy().reset_index(drop=True)
print(f"S&P finished sample: N = {len(finished)}")
print(f"EU subsample: N = {len(eu)}")


# ============================================================================
# A. OSTER BOUNDS VOOR EU 2x2 DiD (cbam_x_post)
# ============================================================================
hdr("A. Oster bounds — EU 2x2 DiD (cbam_x_post)")

# Restricted model: alleen treatment dummy + DiD interaction
X_rest = sm.add_constant(eu[['cbam_endex','post_2022','cbam_x_post']])
y_eu = eu['cancel_B'].astype(float)
m_rest = sm.OLS(y_eu, X_rest).fit(cov_type='HC1')
beta_rest_eu = float(m_rest.params['cbam_x_post'])
R_rest_eu = float(m_rest.rsquared)

# Full model met controls (is_blue, log_cap)
X_full = sm.add_constant(eu[['cbam_endex','post_2022','cbam_x_post','is_blue','log_cap']])
m_full = sm.OLS(y_eu, X_full).fit(cov_type='HC1')
beta_full_eu = float(m_full.params['cbam_x_post'])
R_full_eu = float(m_full.rsquared)

print(f"\nRestricted (alleen DiD vars):")
print(f"  β_cbam_x_post = {beta_rest_eu:+.4f}")
print(f"  R² = {R_rest_eu:.4f}")
print(f"\nFull (met is_blue + log_cap controls):")
print(f"  β_cbam_x_post = {beta_full_eu:+.4f}")
print(f"  R² = {R_full_eu:.4f}")
print(f"\nMovement in β when adding controls: Δβ = {beta_full_eu - beta_rest_eu:+.4f}")
print(f"Movement in R²: ΔR² = {R_full_eu - R_rest_eu:+.4f}")

# Oster's recommended R²_max values
print(f"\nOster (2019) recommends R²_max = 1.3 × R²_full or R²_max = 1.0:")
oster_results_eu = []
for R_max_factor, R_max_label in [(R_full_eu * 1.3, "1.3 × R²_full"),
                                     (min(R_full_eu * 2.2, 1.0), "Oster suggested"),
                                     (1.0, "R²_max = 1.0 (maximum possible)")]:
    delta = oster_delta(beta_rest_eu, beta_full_eu, R_rest_eu, R_full_eu, R_max_factor)
    beta_adj = oster_bias_adj_beta(beta_rest_eu, beta_full_eu, R_rest_eu, R_full_eu, R_max_factor, delta=1.0)
    oster_results_eu.append({
        'spec':'EU 2x2 DiD',
        'R_max_label':R_max_label,
        'R_max_value':R_max_factor,
        'delta':delta,
        'beta_adj_delta1':beta_adj,
    })
    print(f"\n  R²_max = {R_max_factor:.4f} ({R_max_label}):")
    print(f"    δ bound (β* = 0): {delta:.4f}")
    print(f"    β_adjusted (δ=1): {beta_adj:+.4f}")
    verdict = '✓ robust to OVB' if delta > 1.0 else ('⚠ fragile to OVB' if delta > 0 else '⚠ very fragile')
    print(f"    Verdict: {verdict}")


# ============================================================================
# B. OSTER BOUNDS VOOR TRIPLE-DIFFERENCE
# ============================================================================
hdr("B. Oster bounds — Triple-difference (triple)")

# Restricted: alle 3 main effects + 3 pairwise + triple (no controls)
X_rest_t = sm.add_constant(finished[['is_EU','cbam_endex','post_2022',
                                       'EU_x_cbam','EU_x_post','cbam_x_post','triple']])
y_full = finished['cancel_B'].astype(float)
m_rest_t = sm.OLS(y_full, X_rest_t).fit(cov_type='HC1')
beta_rest_t = float(m_rest_t.params['triple'])
R_rest_t = float(m_rest_t.rsquared)

# Full: + is_blue, log_cap
X_full_t = sm.add_constant(finished[['is_EU','cbam_endex','post_2022',
                                       'EU_x_cbam','EU_x_post','cbam_x_post','triple',
                                       'is_blue','log_cap']])
m_full_t = sm.OLS(y_full, X_full_t).fit(cov_type='HC1')
beta_full_t = float(m_full_t.params['triple'])
R_full_t = float(m_full_t.rsquared)

print(f"\nRestricted (alleen DiD vars):")
print(f"  β_triple = {beta_rest_t:+.4f}")
print(f"  R² = {R_rest_t:.4f}")
print(f"\nFull (met is_blue + log_cap controls):")
print(f"  β_triple = {beta_full_t:+.4f}")
print(f"  R² = {R_full_t:.4f}")
print(f"\nMovement in β when adding controls: Δβ = {beta_full_t - beta_rest_t:+.4f}")
print(f"Movement in R²: ΔR² = {R_full_t - R_rest_t:+.4f}")

# Note: voor triple-diff is β waarschijnlijk al klein, dus Oster bounds zijn minder informatief
# Maar laten we toch reporten
oster_results_t = []
for R_max_factor, R_max_label in [(R_full_t * 1.3, "1.3 × R²_full"),
                                     (min(R_full_t * 2.2, 1.0), "Oster suggested"),
                                     (1.0, "R²_max = 1.0")]:
    delta = oster_delta(beta_rest_t, beta_full_t, R_rest_t, R_full_t, R_max_factor)
    beta_adj = oster_bias_adj_beta(beta_rest_t, beta_full_t, R_rest_t, R_full_t, R_max_factor, delta=1.0)
    oster_results_t.append({
        'spec':'Triple-difference',
        'R_max_label':R_max_label,
        'R_max_value':R_max_factor,
        'delta':delta,
        'beta_adj_delta1':beta_adj,
    })
    print(f"\n  R²_max = {R_max_factor:.4f} ({R_max_label}):")
    if not np.isnan(delta):
        print(f"    δ bound (β* = 0): {delta:.4f}")
    print(f"    β_adjusted (δ=1): {beta_adj:+.4f}")
    if abs(beta_full_t) < 0.05:
        print(f"    (Triple coefficient al klein, OVB analysis minder informatief)")


# ============================================================================
# C. OSTER BOUNDS VOOR v7 HAZARD MODEL (is_blue_ccs)
# ============================================================================
hdr("C. Oster bounds — v7 hazard model (is_blue_ccs)")

v7 = pd.read_csv('/Users/sakesaakstra/Desktop/thesis_h2/01_data/intermediate/blueccs_project_level_for_R.csv')
v7['region_EU'] = (v7['region']=='EU').astype(int)
v7['region_NorthAm'] = (v7['region']=='North_America').astype(int)
v7['region_Asia'] = (v7['region']=='Asia').astype(int)
v7['year_centered'] = v7['year_announced'] - v7['year_announced'].mean()

# Restricted: alleen is_blue_ccs (focal)
X_rest_v7 = sm.add_constant(v7[['is_blue_ccs']])
y_v7 = v7['event_any'].astype(float)
m_rest_v7 = sm.OLS(y_v7, X_rest_v7).fit(cov_type='HC1')
beta_rest_v7 = float(m_rest_v7.params['is_blue_ccs'])
R_rest_v7 = float(m_rest_v7.rsquared)

# Full: + log_cap + regions + year
X_full_v7 = sm.add_constant(v7[['is_blue_ccs','log_capacity_mw','region_EU','region_NorthAm','region_Asia','year_centered']])
m_full_v7 = sm.OLS(y_v7, X_full_v7).fit(cov_type='HC1')
beta_full_v7 = float(m_full_v7.params['is_blue_ccs'])
R_full_v7 = float(m_full_v7.rsquared)

print(f"\nRestricted (alleen is_blue_ccs):")
print(f"  β_is_blue_ccs = {beta_rest_v7:+.4f}")
print(f"  R² = {R_rest_v7:.4f}")
print(f"\nFull (met all controls):")
print(f"  β_is_blue_ccs = {beta_full_v7:+.4f}")
print(f"  R² = {R_full_v7:.4f}")

oster_results_v7 = []
for R_max_factor, R_max_label in [(R_full_v7 * 1.3, "1.3 × R²_full"),
                                     (min(R_full_v7 * 2.2, 1.0), "Oster suggested"),
                                     (1.0, "R²_max = 1.0")]:
    delta = oster_delta(beta_rest_v7, beta_full_v7, R_rest_v7, R_full_v7, R_max_factor)
    beta_adj = oster_bias_adj_beta(beta_rest_v7, beta_full_v7, R_rest_v7, R_full_v7, R_max_factor, delta=1.0)
    oster_results_v7.append({
        'spec':'v7 hazard model',
        'R_max_label':R_max_label,
        'R_max_value':R_max_factor,
        'delta':delta,
        'beta_adj_delta1':beta_adj,
    })
    print(f"\n  R²_max = {R_max_factor:.4f} ({R_max_label}):")
    print(f"    δ bound (β* = 0): {delta:.4f}")
    print(f"    β_adjusted (δ=1): {beta_adj:+.4f}")
    verdict = '✓ robust to OVB' if delta > 1.0 else ('⚠ fragile' if delta > 0 else '⚠ very fragile')
    print(f"    Verdict: {verdict}")


# ============================================================================
# SUMMARY TABLE
# ============================================================================
hdr("OSTER (2019) OVB BOUNDS — EINDSAMENVATTING")

all_results = oster_results_eu + oster_results_t + oster_results_v7
all_df = pd.DataFrame(all_results)
print(all_df.round(4).to_string(index=False))
all_df.to_csv(OUT / "results/oster_bounds.csv", index=False)

print(f"""

KEY OSTER FINDINGS:

A. EU 2x2 DiD (β_cbam_x_post):
   - Movement on adding controls: Δβ = {beta_full_eu - beta_rest_eu:+.4f}
   - δ bound (R²_max = 1.3 × R²_full): {oster_results_eu[0]['delta']:.4f}
   - Interpretatie: {'Robust' if oster_results_eu[0]['delta'] > 1 else 'Fragile'} t.a.v. unobservables ≥ observables in selection effect

B. Triple-difference (β_triple):
   - Already near-zero estimate β = {beta_full_t:+.4f}
   - δ bound: {oster_results_t[0]['delta']:.4f}
   - Een fragiele δ bound bij een already-null coefficient is logisch
     (the effect doesn't need much OVB to "kill" it because it's already small)

C. v7 hazard model (β_is_blue_ccs):
   - Large empirical effect (β = {beta_full_v7:+.4f}, big movement when adding controls)
   - δ bound: {oster_results_v7[0]['delta']:.4f}
   - {'Robust' if oster_results_v7[0]['delta'] > 1 else 'Fragile'} t.a.v. OVB

→ Resultaten naar:  results/oster_bounds.csv
""")
