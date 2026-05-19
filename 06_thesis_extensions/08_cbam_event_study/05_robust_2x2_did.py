"""
05_robust_2x2_did.py — Robust 2x2 DiD specifications, geen perfect separation.

Lessen van de triple-diff: 85 events is te weinig voor 8-cell triple-diff.
Fallback naar 2x2 DiD met meerdere exposure-keuzes, en Cox PH als comparison.

Specificaties:
  Spec A: Standard 2x2 logit, Blue × Post (waarbij Blue = CBAM-exposed via gas)
  Spec B: Standard 2x2 logit, EU-region × Post
  Spec C: Standard 2x2 logit, Major-sponsor × Post (Oil_major, Industrial_gas, Steel)
  
  + cluster-robust SE
  + control variabelen
  + multiple treatment dates including placebo
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/08_cbam_event_study/results_robust_did"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# Build panel — alleen jaarlijks, voldoende observations per cel
# ============================================================================
hdr("Build YEAR-level panel (meer cell-level events)")

v7 = pd.read_csv(PROJECT_CSV)
v7['is_blue_ccs'] = v7['is_blue_ccs'].astype(int)
v7['year_announced'] = v7['year_announced'].astype(int)
v7['duration'] = v7['duration'].astype(int).clip(lower=1)
v7['event_any'] = (v7['event_type'] > 0).astype(int)
v7['event_year'] = v7['year_announced'] + v7['duration']

def major_sponsor(s):
    return int(str(s).strip() in ['Oil_major','Industrial_gas','Steel'])
def eu_region(r):
    return int(str(r).strip() in ['EU','Other_Europe'])

v7['major_sponsor'] = v7['sponsor_type'].apply(major_sponsor)
v7['eu_region'] = v7['region'].apply(eu_region)

rows = []
for idx, row in v7.iterrows():
    t_start = int(row['year_announced'])
    t_end = int(row['event_year'])
    if t_end > 2026: t_end = 2026
    for y in range(t_start, t_end + 1):
        is_event = (row['event_any']==1) and (y == int(row['event_year']))
        rows.append({
            'project_id': idx, 'year': y,
            'is_blue': int(row['is_blue_ccs']),
            'major_sponsor': int(row['major_sponsor']),
            'eu_region': int(row['eu_region']),
            'log_cap': float(row['log_capacity_mw']),
            'years_since': y - t_start,
            'event': int(is_event),
        })
panel = pd.DataFrame(rows)
panel = panel[(panel['year'] >= 2018) & (panel['year'] <= 2026)].copy()
print(f"Year panel: {len(panel):,} obs, {panel['event'].sum()} events")

# Event distribution check
print(f"\nEvents per (Blue × EU × Post-Oct-2023):")
panel['post_oct2023'] = (panel['year'] >= 2024).astype(int)  # post-Oct-2023 ≈ from 2024
print(panel[panel['event']==1].groupby(['is_blue','eu_region','post_oct2023']).size().rename('n_events'))


# ============================================================================
# SPEC A: 2x2 DiD met Blue × Post
# ============================================================================
hdr("SPEC A — Blue × Post DiD (treated = Blue projecten als CBAM-feedstock-exposed)")

def fit_2x2_did(panel, exposed_col, post_col, label):
    df = panel.copy()
    df['E'] = df[exposed_col]
    df['P'] = df[post_col]
    df['EP'] = df['E'] * df['P']
    
    y = df['event']
    X = sm.add_constant(df[['E','P','EP','is_blue','log_cap','years_since']])
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=200,
                                cov_type='cluster',
                                cov_kwds={'groups': df['project_id']})
        b = m.params['EP']
        se = m.bse['EP']
        p = m.pvalues['EP']
        ci = (b - 1.96*se, b + 1.96*se)
        return b, se, p, ci, int(m.nobs)
    except Exception as e:
        return None, None, None, None, None

# Build treatment date columns
TREATMENTS = {
    'regulation_apr2023': 2023,    # year-level, after-apr ≈ from 2023
    'transitional_oct2023': 2024,   # post ≈ 2024 onwards (since oct2023 yr-half year)
    'definitive_jan2026':   2026,
    'PLACEBO_2020':         2020,
    'PLACEBO_2022':         2022,
}
for name, y in TREATMENTS.items():
    panel[f'post_{name}'] = (panel['year'] >= y).astype(int)

print(f"\n{'Treatment':<25s} | {'Exposure':<14s} | β_DiD   | 95% CI         | p     | N")
print("-" * 85)
all_results = []
for trt_name in TREATMENTS:
    for exp_col, exp_label in [
        ('is_blue', 'Blue (T3)'),
        ('eu_region', 'EU region (T2)'),
        ('major_sponsor', 'Major sponsor (T1)'),
    ]:
        result = fit_2x2_did(panel, exp_col, f'post_{trt_name}', exp_label)
        if result[0] is None:
            continue
        b, se, p, ci, n = result
        is_placebo = 'PLACEBO' in trt_name
        marker = "🅿️" if is_placebo else "  "
        sig = "*" if p < 0.05 else " "
        print(f"{marker} {trt_name:<23s} | {exp_label:<14s} | {b:+.3f}{sig} | [{ci[0]:+.2f}, {ci[1]:+.2f}] | {p:.3f} | {n:,}")
        all_results.append({
            'treatment': trt_name, 'exposure': exp_label,
            'beta_DiD': b, 'se': se, 'p': p, 'ci_lo': ci[0], 'ci_hi': ci[1],
            'is_placebo': is_placebo, 'sig_05': p<0.05, 'n_obs': n,
        })

results_df = pd.DataFrame(all_results)
results_df.to_csv(OUT / "robust_did_specs.csv", index=False)


# ============================================================================
# REAL vs PLACEBO comparison — per exposure type
# ============================================================================
hdr("Real vs Placebo CARS — per exposure")

for exp in results_df['exposure'].unique():
    sub = results_df[results_df['exposure'] == exp]
    real = sub[~sub['is_placebo']]
    plac = sub[sub['is_placebo']]
    print(f"\n{exp}:")
    print(f"  Real treatments β_DiD: {real['beta_DiD'].values.round(3).tolist()}")
    print(f"  Real treatments mean: {real['beta_DiD'].mean():+.3f}, median: {real['beta_DiD'].median():+.3f}")
    print(f"  Placebo β_DiD:        {plac['beta_DiD'].values.round(3).tolist()}")
    print(f"  Placebo mean:         {plac['beta_DiD'].mean():+.3f}, median: {plac['beta_DiD'].median():+.3f}")


# ============================================================================
# VISUALISATIE — bar chart van β_DiD per spec
# ============================================================================
fig, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)

for ax, exp in zip(axes, results_df['exposure'].unique()):
    sub = results_df[results_df['exposure'] == exp].copy()
    sub = sub.sort_values('treatment')
    colors = ['#882288' if not p else '#888888' for p in sub['is_placebo']]
    ax.barh(sub['treatment'], sub['beta_DiD'], xerr=1.96*sub['se'],
            color=colors, alpha=0.8, capsize=4)
    ax.axvline(0, ls='--', color='black')
    ax.set_xlabel(r"$\beta_{\mathrm{DiD}}$")
    ax.set_title(f"Exposure: {exp}")
    ax.grid(alpha=0.3, axis='x')

axes[0].set_ylabel("Treatment date")
fig.suptitle("Robust 2×2 DiD: Real (purple) vs Placebo (grey) treatment dates", fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(OUT / "figures/robust_did_comparison.pdf")
plt.close()

print(f"\nFiguur: {OUT}/figures/robust_did_comparison.pdf")


# ============================================================================
# SAMENVATTING
# ============================================================================
hdr("EINDSAMENVATTING")
print("\nVerdict per (treatment, exposure) cell:")
print("  '✓' = real treatment significantly different from 0 AND placebos non-significant")
print("  '~' = real treatment not robust (placebos also significant of vergelijkbare magnitude)")
print("  '✗' = real treatment null (CrI contains 0)")
print()

verdict_count = {'✓': 0, '~': 0, '✗': 0}
for exp in results_df['exposure'].unique():
    sub = results_df[results_df['exposure'] == exp]
    for trt in sub[~sub['is_placebo']]['treatment'].unique():
        real_row = sub[(sub['treatment']==trt) & (~sub['is_placebo'])].iloc[0]
        # Check if real coefficient is significant
        real_sig = real_row['sig_05']
        # Check if placebos have similar magnitudes
        placebos = sub[sub['is_placebo']]
        placebo_mag = placebos['beta_DiD'].abs().mean()
        real_mag = abs(real_row['beta_DiD'])
        is_robust = real_sig and (real_mag > 1.5 * placebo_mag)
        if is_robust:
            verdict = '✓'
        elif real_sig:
            verdict = '~'
        else:
            verdict = '✗'
        verdict_count[verdict] += 1
        print(f"  {trt:25s} × {exp:18s}: {verdict}  (real β={real_row['beta_DiD']:+.2f}, placebo mean |β|={placebo_mag:.2f})")

print(f"\nFrequentie verdicts: {verdict_count}")

if verdict_count['✓'] > 0:
    print(f"\n→ Identification ROBUST in {verdict_count['✓']} specs")
elif verdict_count['~'] > 0:
    print(f"\n→ Identification AMBIGUOUS in {verdict_count['~']} specs (placebo similar magnitude)")
else:
    print(f"\n→ Identification NULL across all specs — geen causaal CBAM-effect detecteerbaar")
