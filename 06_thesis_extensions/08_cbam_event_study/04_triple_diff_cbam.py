"""
04_triple_diff_cbam.py — Triple-difference CBAM-DiD met multiple treatment dates.

Spec: η_it = α + β1 Blue + β2 Exposed + β3 Post + β4 (Blue×Exp) + β5 (Blue×Post)
            + β6 (Exp×Post) + β7 (Blue×Exp×Post) + γ X_it + ε

β7 = TRIPLE-DIFFERENCE: het CBAM-specifieke effect op Blue × Exposed projecten,
controlerend voor algemene exposed-effects en algemene Blue-effects.

Run alle 4 treatment dates (incl placebo) × 2 exposure proxies (T1, T2) = 8 specs.
Plus event-time dynamic spec voor pre-trends.
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
OUT = PROJECT_ROOT / "06_thesis_extensions/08_cbam_event_study/results_triple_diff"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# 1. Load + build month-level panel
# ============================================================================
hdr("Build panel")

v7 = pd.read_csv(PROJECT_CSV)
v7['is_blue_ccs'] = v7['is_blue_ccs'].astype(int)
v7['year_announced'] = v7['year_announced'].astype(int)
v7['duration'] = v7['duration'].astype(int).clip(lower=1)
v7['event_any'] = (v7['event_type'] > 0).astype(int)
v7['event_year'] = v7['year_announced'] + v7['duration']

def t1(s): return int(str(s).strip() in ['Oil_major','Industrial_gas','Steel'])
def t2(r): return int(str(r).strip() in ['EU','Other_Europe'])
v7['cbam_T1'] = v7['sponsor_type'].apply(t1)
v7['cbam_T2'] = v7['region'].apply(t2)

# Build month panel
rows = []
for idx, row in v7.iterrows():
    t_start = pd.Timestamp(f"{int(row['year_announced'])}-06-15")
    t_end = pd.Timestamp(f"{int(row['event_year'])}-06-15")
    if t_end > pd.Timestamp('2026-05-19'):
        t_end = pd.Timestamp('2026-05-19')
    months = pd.date_range(t_start, t_end, freq='MS')
    for m in months:
        is_event = (row['event_any']==1) and (m.year==int(row['event_year'])) and (m.month>=5)
        rows.append({
            'project_id': idx, 'month': m, 'is_blue': int(row['is_blue_ccs']),
            'cbam_T1': int(row['cbam_T1']), 'cbam_T2': int(row['cbam_T2']),
            'log_cap': float(row['log_capacity_mw']),
            'years_since': (m - t_start).days / 365.25,
            'event': int(is_event),
        })
panel = pd.DataFrame(rows)
panel = panel[(panel['month'] >= '2018-01-01') & (panel['month'] <= '2026-05-01')].copy()
print(f"Panel: {len(panel):,} obs, {panel['event'].sum()} events")

# Treatment dates (incl placebo)
TREATMENTS = {
    'regulation_apr2023': '2023-04-01',
    'transitional_oct2023': '2023-10-01',
    'definitive_jan2026':   '2026-01-01',
    'PLACEBO_jan2021':      '2021-01-01',
    'PLACEBO_jan2022':      '2022-01-01',
}
for name, date in TREATMENTS.items():
    panel[f'post_{name}'] = (panel['month'] >= pd.Timestamp(date)).astype(int)


# ============================================================================
# 2. TRIPLE-DIFFERENCE LOGIT — alle specs
# ============================================================================
def fit_triple_diff(panel, treatment, exposure):
    df = panel.copy()
    df['B'] = df['is_blue']
    df['E'] = df[exposure]
    df['P'] = df[treatment]
    df['BE'] = df['B']*df['E']
    df['BP'] = df['B']*df['P']
    df['EP'] = df['E']*df['P']
    df['BEP'] = df['B']*df['E']*df['P']
    
    y = df['event']
    X = sm.add_constant(df[['B','E','P','BE','BP','EP','BEP','log_cap','years_since']])
    try:
        m = sm.Logit(y, X).fit(disp=0, maxiter=200,
                                cov_type='cluster',
                                cov_kwds={'groups': df['project_id']})
        return m
    except Exception as e:
        print(f"  fit fail: {e}")
        return None

hdr("Triple-difference specifications")
print(f"\n{'Treatment':<25s} | {'Exp':<3s} | β_BEP (triple-DiD) | 95% CI            | p     | N")
print("-" * 95)

specs = []
for trt_name in ['regulation_apr2023','transitional_oct2023','definitive_jan2026',
                  'PLACEBO_jan2021','PLACEBO_jan2022']:
    for exp in ['cbam_T1','cbam_T2']:
        m = fit_triple_diff(panel, f'post_{trt_name}', exp)
        if m is None: continue
        b = m.params['BEP']
        se = m.bse['BEP']
        p = m.pvalues['BEP']
        cl = b - 1.96*se
        ch = b + 1.96*se
        is_placebo = 'PLACEBO' in trt_name
        sig = "*" if p < 0.05 else " "
        marker = "🅿️" if is_placebo else "  "
        print(f"{marker} {trt_name:<23s} | {exp:<3s} | {b:+.3f}{sig}             | [{cl:+.2f}, {ch:+.2f}]  | {p:.3f} | {int(m.nobs):,}")
        specs.append({
            'treatment': trt_name, 'exposure': exp,
            'beta_BEP': b, 'se': se, 'p': p, 'ci_lo': cl, 'ci_hi': ch,
            'is_placebo': is_placebo, 'sig_05': p<0.05, 'n_obs': int(m.nobs),
        })

results_df = pd.DataFrame(specs)
results_df.to_csv(OUT / "triple_diff_all_specs.csv", index=False)


# ============================================================================
# 3. PLACEBO COMPARISON
# ============================================================================
hdr("PLACEBO vs ECHTE TREATMENT vergelijking")

real_specs = results_df[~results_df['is_placebo']]
placebo_specs = results_df[results_df['is_placebo']]

print("\nReal treatment dates (mean β_BEP across exposures):")
for trt in real_specs['treatment'].unique():
    sub = real_specs[real_specs['treatment']==trt]
    print(f"  {trt:30s}: mean β = {sub['beta_BEP'].mean():+.3f}, max |β| = {sub['beta_BEP'].abs().max():.3f}")

print("\nPlacebo dates (mean β_BEP across exposures):")
for trt in placebo_specs['treatment'].unique():
    sub = placebo_specs[placebo_specs['treatment']==trt]
    print(f"  {trt:30s}: mean β = {sub['beta_BEP'].mean():+.3f}, max |β| = {sub['beta_BEP'].abs().max():.3f}")

print("\nFalsification verdict:")
real_avg = real_specs['beta_BEP'].abs().mean()
placebo_avg = placebo_specs['beta_BEP'].abs().mean()
if real_avg > 1.5 * placebo_avg:
    print(f"  ✓ Real |β_BEP| ({real_avg:.2f}) >> placebo |β_BEP| ({placebo_avg:.2f})")
    print(f"    Patroon onderscheidt zich van placebo — identification staat overeind")
else:
    print(f"  ~ Real |β_BEP| ({real_avg:.2f}) ≈ placebo |β_BEP| ({placebo_avg:.2f})")
    print(f"    Patroon NIET onderscheiden van placebo — identification ondermijnd")


# ============================================================================
# 4. EVENT-TIME DYNAMIC SPECIFICATION
# ============================================================================
hdr("Event-time dynamic spec around CBAM transitional shock (oct 2023)")

TR_DATE = pd.Timestamp('2023-10-01')
panel['et'] = ((panel['month'].dt.year - TR_DATE.year)*12 +
                (panel['month'].dt.month - TR_DATE.month))

# Bucket into quarters voor power
panel['et_q'] = (panel['et'] // 3) * 3

# Sample: limit to [-18 months, +30 months] window
df_dyn = panel[(panel['et'] >= -18) & (panel['et'] <= 30)].copy()
df_dyn['exposed'] = df_dyn['cbam_T1']

# Create dummies for each quarter bucket
qs = sorted(df_dyn['et_q'].unique())
qs.remove(-3)  # reference: most recent pre-treatment quarter [-3,-1)
print(f"Event-time quarters in panel: {qs}")
print(f"Reference quarter: [-3, 0) (most recent pre-treatment)")

# Build dummy variables
for q in qs:
    df_dyn[f'q_{q}'] = (df_dyn['et_q'] == q).astype(int)
    df_dyn[f'did_q_{q}'] = df_dyn['is_blue'] * df_dyn['exposed'] * df_dyn[f'q_{q}']

# Fit dynamic triple-diff
q_dummies = [f'q_{q}' for q in qs]
did_dummies = [f'did_q_{q}' for q in qs]

y = df_dyn['event']
X_cols = ['is_blue', 'exposed', 'log_cap', 'years_since'] + q_dummies + did_dummies
X = sm.add_constant(df_dyn[X_cols])

try:
    mdyn = sm.Logit(y, X).fit(disp=0, maxiter=300, method='bfgs',
                                cov_type='cluster',
                                cov_kwds={'groups': df_dyn['project_id']})
    
    print(f"\n{'Event-time bucket':<22s} | β_dyn   | SE     | 95% CI         | n_events_in_bucket")
    print("-" * 90)
    dyn_rows = []
    for q in qs:
        name = f'did_q_{q}'
        if name not in mdyn.params: continue
        b = mdyn.params[name]
        se = mdyn.bse[name]
        ci_lo = b - 1.96*se
        ci_hi = b + 1.96*se
        # Count events in this bucket where treated
        n_treat_evt = ((df_dyn['is_blue']==1) & (df_dyn['exposed']==1) & 
                       (df_dyn['et_q']==q) & (df_dyn['event']==1)).sum()
        label = f"[{q:+d}, {q+3:+d})"
        print(f"{label:<22s} | {b:+.3f}  | {se:.3f} | [{ci_lo:+.2f}, {ci_hi:+.2f}] | {n_treat_evt}")
        dyn_rows.append({'q': q, 'beta': b, 'se': se, 'ci_lo': ci_lo, 'ci_hi': ci_hi})
    
    dyn_df = pd.DataFrame(dyn_rows)
    dyn_df.to_csv(OUT / "dynamic_did_event_time.csv", index=False)
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.errorbar(dyn_df['q'], dyn_df['beta'], yerr=1.96*dyn_df['se'],
                fmt='o-', capsize=4, lw=2, color='#882288', markersize=7)
    # Reference quarter at [-3, 0) = beta=0
    ax.scatter([-3], [0], marker='s', color='black', s=80, zorder=5, label='Reference q=[-3,0)')
    ax.axhline(0, ls='--', color='black', alpha=0.5)
    ax.axvline(0, ls=':', color='red', lw=2.5, alpha=0.7, label='CBAM transitional start (Oct 2023)')
    ax.fill_betweenx([dyn_df['beta'].min()-0.5, dyn_df['beta'].max()+0.5],
                     -3, 0, alpha=0.15, color='gray')
    ax.set_xlabel("Event time (months from CBAM transitional start)")
    ax.set_ylabel(r"$\beta_{\mathrm{Blue} \times \mathrm{Exposed} \times \mathrm{Post}}$ (Triple-DiD)")
    ax.set_title("Dynamic Triple-Difference: CBAM Transitional Phase Shock\n(Blue × CBAM-exposed × Post-treatment interaction)")
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT / "figures/dynamic_triple_diff.pdf")
    plt.close()
    
    # Pre-trend test
    pre = dyn_df[dyn_df['q'] < 0]
    post = dyn_df[dyn_df['q'] >= 0]
    pre_cross = ((pre['ci_lo'] < 0) & (pre['ci_hi'] > 0)).sum()
    post_excl = ((post['ci_lo'] > 0) | (post['ci_hi'] < 0)).sum()
    print(f"\nPre-trend test:")
    print(f"  Pre-treatment quarters: {len(pre)} (CI crosses 0 in {pre_cross} of them)")
    print(f"  Mean pre β: {pre['beta'].mean():+.3f}")
    print(f"  Post-treatment quarters: {len(post)} (CI excludes 0 in {post_excl} of them)")
    print(f"  Mean post β: {post['beta'].mean():+.3f}")
    print(f"\nFiguur: {OUT}/figures/dynamic_triple_diff.pdf")
except Exception as e:
    print(f"Dynamic fit failed: {e}")

print(f"\n\nResultaten directory: {OUT}")
