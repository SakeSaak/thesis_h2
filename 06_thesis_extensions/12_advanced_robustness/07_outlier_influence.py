"""
07_outlier_influence.py — Cook's distance + DFBETA influence diagnostics.

Top-tier econometric work routinely checks whether single observations
disproportionately drive the focal estimates. We apply Cook's distance and
DFBETA on three key specifications:

  A. EU 2x2 DiD (cbam_x_post coefficient on S&P sample)
  B. Triple-difference EU x CBAM x Post (triple coefficient on S&P sample)
  C. Discrete-time logit hazard (is_blue_ccs coefficient on v7 sample)

For each: identify top-5 most influential observations, then refit
WITHOUT them to test sensitivity of focal coefficient.
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from statsmodels.stats.outliers_influence import OLSInfluence
from scipy import stats

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")

def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# DATA LOAD
# ============================================================================
hdr("Data load: S&P sample (Chapter 8 DiD) + v7 sample (Chapter 7 hazard)")

# S&P
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
print(f"  S&P finished sample: N = {len(finished)}")
print(f"  S&P EU subsample:    N = {len(eu)}")


def influence_diagnostics(y, X, name, focal_var):
    """Run OLS influence diagnostics op een spec."""
    print(f"\n--- {name} ---")
    print(f"Focal variable: {focal_var}")
    print(f"Sample size: N = {len(y)}")
    
    # Fit OLS (LPM)
    model = sm.OLS(y, X).fit()
    infl = OLSInfluence(model)
    
    beta_full = model.params[focal_var]
    se_full = model.bse[focal_var]
    p_full = model.pvalues[focal_var]
    print(f"FULL sample: β_{focal_var} = {beta_full:+.4f} (SE {se_full:.4f}, p = {p_full:.4f})")
    
    # Cook's distance
    cooks_d = infl.cooks_distance[0]
    # DFBETAS — een per observation per coefficient
    dfbetas = infl.dfbetas
    
    # Top-5 most influential (by Cook's D)
    top5_idx = np.argsort(cooks_d)[::-1][:5]
    print(f"\nTop-5 most influential observations (by Cook's distance):")
    print(f"  threshold 4/N = {4/len(y):.4f}")
    n_above = (cooks_d > 4/len(y)).sum()
    print(f"  # obs above 4/N threshold: {n_above}")
    
    for i, idx in enumerate(top5_idx, 1):
        # DFBETA for focal var
        dfbeta_focal = dfbetas[idx, X.columns.get_loc(focal_var)]
        print(f"  #{i}: obs idx {idx}, Cook's D = {cooks_d[idx]:.4f}, DFBETA[{focal_var}] = {dfbeta_focal:+.4f}")
    
    # Sensitivity: refit without top-5
    mask = np.ones(len(y), dtype=bool)
    mask[top5_idx] = False
    
    model_red = sm.OLS(y[mask], X[mask]).fit()
    beta_red = model_red.params[focal_var]
    se_red = model_red.bse[focal_var]
    p_red = model_red.pvalues[focal_var]
    
    print(f"\nWithout top-5 most-influential observations (N-5 = {mask.sum()}):")
    print(f"  β_{focal_var} = {beta_red:+.4f} (SE {se_red:.4f}, p = {p_red:.4f})")
    
    pct_change = (beta_red - beta_full) / abs(beta_full) * 100 if abs(beta_full) > 1e-9 else 0
    print(f"  Δβ = {beta_red - beta_full:+.4f} ({pct_change:+.1f}% change)")
    
    # Verdict
    sign_change = (beta_full > 0) != (beta_red > 0)
    sig_change = (p_full < 0.05) != (p_red < 0.05)
    
    if sign_change:
        verdict = "⚠ SIGN CHANGES — coefficient driven by outliers"
    elif sig_change and p_full < 0.05:
        verdict = "⚠ SIGNIFICANCE LOSS — fragile to outliers"
    elif sig_change and p_red < 0.05:
        verdict = "✓ SIGNIFICANCE GAIN — robust without outliers"
    elif abs(pct_change) < 15:
        verdict = "✓ STABLE — coefficient robust to outliers (Δ < 15%)"
    else:
        verdict = "⚠ COEFFICIENT SHIFT >15% — sensitivity concern"
    
    print(f"\nVerdict: {verdict}")
    
    return {
        'name': name,
        'N': len(y),
        'focal_var': focal_var,
        'beta_full': beta_full, 'se_full': se_full, 'p_full': p_full,
        'beta_reduced': beta_red, 'se_reduced': se_red, 'p_reduced': p_red,
        'pct_change': pct_change,
        'verdict': verdict,
        'cooks_d': cooks_d,
        'dfbetas_focal': dfbetas[:, X.columns.get_loc(focal_var)],
        'top5_idx': top5_idx,
    }


# ============================================================================
# SPEC A: EU 2x2 DiD
# ============================================================================
hdr("A. EU 2x2 DiD — Cook's distance + DFBETA (cbam_x_post)")

X_eu = sm.add_constant(eu[['cbam_endex','post_2022','cbam_x_post','is_blue','log_cap']])
y_eu = eu['cancel_B'].astype(float)
result_eu = influence_diagnostics(y_eu.reset_index(drop=True), X_eu.reset_index(drop=True),
                                    "EU 2x2 DiD", "cbam_x_post")


# ============================================================================
# SPEC B: Triple-difference
# ============================================================================
hdr("B. Triple-difference — Cook's distance + DFBETA (triple)")

X_full = sm.add_constant(finished[['is_EU','cbam_endex','post_2022',
                                     'EU_x_cbam','EU_x_post','cbam_x_post','triple',
                                     'is_blue','log_cap']])
y_full = finished['cancel_B'].astype(float)
result_triple = influence_diagnostics(y_full.reset_index(drop=True), X_full.reset_index(drop=True),
                                        "Triple-difference EUxCBAMxPost", "triple")


# ============================================================================
# SPEC C: v7 hazard model (LPM proxy for logit)
# ============================================================================
hdr("C. v7 hazard model — Cook's distance + DFBETA (is_blue_ccs)")

v7 = pd.read_csv('/Users/sakesaakstra/Desktop/thesis_h2/01_data/intermediate/blueccs_project_level_for_R.csv')
v7['region_EU'] = (v7['region']=='EU').astype(int)
v7['region_NorthAm'] = (v7['region']=='North_America').astype(int)
v7['region_Asia'] = (v7['region']=='Asia').astype(int)
v7['region_OtherEur'] = (v7['region']=='Other_Europe').astype(int)
v7['region_ANZ'] = (v7['region']=='ANZ').astype(int)
v7['year_centered'] = v7['year_announced'] - v7['year_announced'].mean()

X_v7 = sm.add_constant(v7[['is_blue_ccs','log_capacity_mw',
                              'region_EU','region_NorthAm','region_Asia','region_OtherEur','region_ANZ',
                              'year_centered']])
y_v7 = v7['event_any'].astype(float)
result_v7 = influence_diagnostics(y_v7.reset_index(drop=True), X_v7.reset_index(drop=True),
                                    "v7 hazard model (LPM)", "is_blue_ccs")


# ============================================================================
# COMBINED SUMMARY TABLE
# ============================================================================
hdr("OUTLIER INFLUENCE — EINDSAMENVATTING")

summary_rows = []
for r in [result_eu, result_triple, result_v7]:
    summary_rows.append({
        'spec': r['name'],
        'focal_var': r['focal_var'],
        'N': r['N'],
        'beta_full': f"{r['beta_full']:+.4f}",
        'p_full': f"{r['p_full']:.4f}",
        'beta_reduced': f"{r['beta_reduced']:+.4f}",
        'p_reduced': f"{r['p_reduced']:.4f}",
        'pct_change': f"{r['pct_change']:+.1f}%",
        'verdict': r['verdict'],
    })

summary_df = pd.DataFrame(summary_rows)
print("\nSamenvatting van outlier-influence diagnostics:")
print(summary_df.to_string(index=False))
summary_df.to_csv(OUT / "results/outlier_influence_summary.csv", index=False)


# ============================================================================
# PLOTS
# ============================================================================
hdr("Generate outlier-influence plots")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})

fig, axes = plt.subplots(2, 3, figsize=(15, 9))

for i, r in enumerate([result_eu, result_triple, result_v7]):
    # Top row: Cook's distance
    ax_top = axes[0, i]
    obs_idx = np.arange(r['N'])
    ax_top.scatter(obs_idx, r['cooks_d'], alpha=0.6, color='#882288', s=15)
    ax_top.axhline(4/r['N'], ls='--', color='red', alpha=0.7,
                   label=f"4/N threshold = {4/r['N']:.3f}")
    # Highlight top-5
    ax_top.scatter(r['top5_idx'], r['cooks_d'][r['top5_idx']],
                    color='red', s=40, alpha=0.9, label='Top-5 influential')
    ax_top.set_xlabel('Observation index')
    ax_top.set_ylabel("Cook's distance")
    ax_top.set_title(f"{r['name']}\nCook's distance distribution")
    ax_top.legend(fontsize=8)
    
    # Bottom row: DFBETA for focal
    ax_bot = axes[1, i]
    ax_bot.scatter(obs_idx, r['dfbetas_focal'], alpha=0.6, color='#1f77b4', s=15)
    ax_bot.axhline(2/np.sqrt(r['N']), ls='--', color='red', alpha=0.7,
                   label=f"±2/√N threshold = ±{2/np.sqrt(r['N']):.3f}")
    ax_bot.axhline(-2/np.sqrt(r['N']), ls='--', color='red', alpha=0.7)
    ax_bot.axhline(0, ls='-', color='black', alpha=0.3)
    ax_bot.scatter(r['top5_idx'], r['dfbetas_focal'][r['top5_idx']],
                    color='red', s=40, alpha=0.9, label='Top-5 (by Cook)')
    ax_bot.set_xlabel('Observation index')
    ax_bot.set_ylabel(f"DFBETA[{r['focal_var']}]")
    ax_bot.set_title(f"DFBETA for {r['focal_var']}")
    ax_bot.legend(fontsize=8)

plt.suptitle('Figure: Outlier influence diagnostics (Cook\'s D + DFBETA on focal coefficients)',
              fontsize=12, y=1.00)
plt.tight_layout()
fig.savefig(OUT / "figures/F_outlier_influence.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_outlier_influence.pdf")


print(f"""

EINDCONCLUSIE OUTLIER-INFLUENCE DIAGNOSTICS:

A. EU 2x2 DiD (cbam_x_post coefficient):
   {result_eu['verdict']}
   β: {result_eu['beta_full']:+.4f} (p={result_eu['p_full']:.3f}) → {result_eu['beta_reduced']:+.4f} (p={result_eu['p_reduced']:.3f})

B. Triple-difference (triple coefficient):
   {result_triple['verdict']}
   β: {result_triple['beta_full']:+.4f} (p={result_triple['p_full']:.3f}) → {result_triple['beta_reduced']:+.4f} (p={result_triple['p_reduced']:.3f})

C. v7 hazard model (is_blue_ccs coefficient, LPM):
   {result_v7['verdict']}
   β: {result_v7['beta_full']:+.4f} (p={result_v7['p_full']:.3f}) → {result_v7['beta_reduced']:+.4f} (p={result_v7['p_reduced']:.3f})

→ De analyse toont of single-observation outliers de focal coefficient driven.
""")
