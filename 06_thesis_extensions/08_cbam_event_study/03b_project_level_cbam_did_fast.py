"""
03b_project_level_cbam_did_fast.py — Project-level CBAM DiD (frequentist).

Statsmodels logit (1-2 seconden per spec ipv 5-10 minuten Bayesiaan).
Runs alle 9 (treatment × exposure) specs.

Bonus: voegt cluster-robust standard errors toe (project-level clustering),
en doet event-time dynamic specification voor pre-trend check.
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
OUT = PROJECT_ROOT / "06_thesis_extensions/08_cbam_event_study/results_project_level"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "figures").mkdir(exist_ok=True)


def hdr(t): print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# ============================================================================
# 1. Build month-level panel met alle covariaten
# ============================================================================
hdr("Build month-level panel")

v7 = pd.read_csv(PROJECT_CSV)
v7['is_blue_ccs'] = v7['is_blue_ccs'].astype(int)
v7['year_announced'] = v7['year_announced'].astype(int)
v7['duration'] = v7['duration'].astype(int).clip(lower=1)
v7['event_any'] = (v7['event_type'] > 0).astype(int)
v7['event_year'] = v7['year_announced'] + v7['duration']

# CBAM exposure proxy
def cbam_T1(s): 
    return int(str(s).strip() in ['Oil_major', 'Industrial_gas', 'Steel'])
def cbam_T2(r): 
    return int(str(r).strip() in ['EU', 'Other_Europe'])
v7['cbam_T1'] = v7['sponsor_type'].apply(cbam_T1)
v7['cbam_T2'] = v7['region'].apply(cbam_T2)
v7['cbam_T3'] = v7['is_blue_ccs']  # Blue = gas-dependent = CBAM-exposed

# Build panel
panel_rows = []
for idx, row in v7.iterrows():
    t_start = pd.Timestamp(f"{int(row['year_announced'])}-06-15")
    t_end_yr = int(row['event_year'])
    t_end = pd.Timestamp(f"{t_end_yr}-06-15")
    if t_end > pd.Timestamp('2026-05-19'):
        t_end = pd.Timestamp('2026-05-19')
    months = pd.date_range(t_start, t_end, freq='MS')
    for m in months:
        is_event = (row['event_any'] == 1) and (m.year == t_end_yr) and (m.month >= 5)
        panel_rows.append({
            'project_id': idx,
            'month': m,
            'is_blue_ccs': int(row['is_blue_ccs']),
            'cbam_T1': int(row['cbam_T1']),
            'cbam_T2': int(row['cbam_T2']),
            'cbam_T3': int(row['cbam_T3']),
            'log_capacity_mw': float(row['log_capacity_mw']),
            'event': int(is_event),
            'years_since_start': (m - t_start).days / 365.25,
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['month'] >= '2018-01-01') & (panel['month'] <= '2026-05-01')].copy()
panel['year'] = panel['month'].dt.year

print(f"Panel: {len(panel):,} obs, {panel['event'].sum()} events")
print(f"Period: {panel['month'].min().strftime('%Y-%m')} → {panel['month'].max().strftime('%Y-%m')}")

# Treatment dates
TREATMENT_DATES = {
    'regulation_force_apr2023': '2023-04-01',
    'transitional_oct2023':     '2023-10-01',
    'definitive_jan2026':       '2026-01-01',
}
for name, date in TREATMENT_DATES.items():
    panel[f'post_{name}'] = (panel['month'] >= pd.Timestamp(date)).astype(int)


# ============================================================================
# 2. DiD specs across all (treatment, exposure) combinations
# ============================================================================
hdr("DiD specifications — frequentist logit met cluster-robust SE")

def fit_did_logit(panel, treatment_col, exposure_col):
    """Logit hazard model with DiD interaction."""
    df = panel.copy()
    df['exposed'] = df[exposure_col]
    df['post'] = df[treatment_col]
    df['did'] = df['exposed'] * df['post']
    
    y = df['event']
    X = sm.add_constant(df[['is_blue_ccs', 'exposed', 'post', 'did',
                             'log_capacity_mw', 'years_since_start']])
    
    try:
        # Logit met cluster-robust SE (project-level)
        model = sm.Logit(y, X).fit(disp=0, cov_type='cluster',
                                    cov_kwds={'groups': df['project_id']})
        return model
    except Exception as e:
        print(f"  fit failed: {e}")
        return None

print(f"\n{'Treatment':<28s} | {'Exposure':<10s} | β_DID    | 95% CI            | p-val  | n_obs")
print("-" * 95)

results_rows = []
for treat_name in ['regulation_force_apr2023', 'transitional_oct2023', 'definitive_jan2026']:
    for exp_name in ['cbam_T1', 'cbam_T2', 'cbam_T3']:
        treat_col = f'post_{treat_name}'
        mdl = fit_did_logit(panel, treat_col, exp_name)
        if mdl is None:
            continue
        
        b_did = mdl.params.get('did', np.nan)
        se_did = mdl.bse.get('did', np.nan)
        p_did = mdl.pvalues.get('did', np.nan)
        ci_lo = b_did - 1.96 * se_did
        ci_hi = b_did + 1.96 * se_did
        sig = "*" if p_did < 0.05 else " "
        
        print(f"{treat_name:<28s} | {exp_name:<10s} | {b_did:+.3f}{sig}  | [{ci_lo:+.2f}, {ci_hi:+.2f}]  | {p_did:.3f}  | {int(mdl.nobs):,}")
        
        results_rows.append({
            'treatment': treat_name,
            'exposure': exp_name,
            'beta_DID': b_did,
            'se_DID': se_did,
            'p_value': p_did,
            'ci_lo': ci_lo,
            'ci_hi': ci_hi,
            'significant_05': p_did < 0.05,
            'sign_negative': b_did < 0,
            'n_obs': int(mdl.nobs),
        })

results_df = pd.DataFrame(results_rows)
results_df.to_csv(OUT / "did_results_frequentist.csv", index=False)


# ============================================================================
# 3. EVENT-TIME DYNAMIC SPECIFICATION (Hanemaaijer-Ketel-Marie style)
# ============================================================================
hdr("Event-time dynamic specification — focus op CBAM-transitional shock (okt 2023)")
print("\nDoel: pre-trend check + dynamiek post-treatment\n")

# Create event-time relative to October 2023
TREATMENT_DATE = pd.Timestamp('2023-10-01')
panel['event_time'] = ((panel['month'].dt.year - TREATMENT_DATE.year) * 12 +
                       (panel['month'].dt.month - TREATMENT_DATE.month))

# Cap event time at [-30, +30] months
panel['et'] = panel['event_time'].clip(lower=-30, upper=30)

# Use T1 (sponsor-based exposure) as primary spec
df = panel[(panel['event_time'] >= -24) & (panel['event_time'] <= 24)].copy()
df['exposed'] = df['cbam_T1']

# Build event-time dummies (drop t=-1 as reference)
for k in range(-24, 25, 3):  # 3-month buckets for power
    if k == -3:
        continue  # reference period
    df[f'et_bucket_{k}'] = ((df['event_time'] >= k) & (df['event_time'] < k + 3)).astype(int)

# Interaction: exposed × event-time bucket
et_buckets = [c for c in df.columns if c.startswith('et_bucket_')]
for b in et_buckets:
    df[f'did_{b}'] = df['exposed'] * df[b]

# Fit dynamic spec
y = df['event']
did_vars = [f'did_{b}' for b in et_buckets]
controls = ['is_blue_ccs', 'exposed', 'log_capacity_mw', 'years_since_start'] + et_buckets
X = sm.add_constant(df[controls + did_vars])

try:
    mdl_dyn = sm.Logit(y, X).fit(disp=0, maxiter=200, method='bfgs',
                                  cov_type='cluster', cov_kwds={'groups': df['project_id']})
    
    print("Dynamic DiD coefficients (β_DID at each event-time bucket, relative to t=-3):")
    print(f"\n{'Event time (months)':<22s} | β_DID    | SE      | 95% CI         | n_treated_obs")
    print("-" * 90)
    
    dyn_rows = []
    for b in et_buckets:
        k = int(b.replace('et_bucket_', ''))
        coef_name = f'did_{b}'
        if coef_name in mdl_dyn.params.index:
            b_val = mdl_dyn.params[coef_name]
            se_val = mdl_dyn.bse[coef_name]
            ci_lo = b_val - 1.96 * se_val
            ci_hi = b_val + 1.96 * se_val
            n_treat = int(((df['exposed']==1) & (df[b]==1)).sum())
            label = f"[{k:+3d}, {k+3:+3d})"
            print(f"{label:<22s} | {b_val:+.3f}  | {se_val:.3f}  | [{ci_lo:+.2f}, {ci_hi:+.2f}]  | {n_treat}")
            dyn_rows.append({'event_time': k, 'beta_did': b_val, 'se': se_val,
                            'ci_lo': ci_lo, 'ci_hi': ci_hi})
    
    dyn_df = pd.DataFrame(dyn_rows)
    dyn_df.to_csv(OUT / "event_time_dynamic_did.csv", index=False)
    
    # Plot
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.errorbar(dyn_df['event_time'], dyn_df['beta_did'],
                yerr=1.96 * dyn_df['se'], fmt='o-', capsize=4, lw=2, color='#882288')
    ax.axhline(0, ls='--', color='black', alpha=0.5)
    ax.axvline(0, ls=':', color='red', lw=2, alpha=0.7, label='CBAM transitional start')
    ax.fill_betweenx([dyn_df['beta_did'].min()-0.5, dyn_df['beta_did'].max()+0.5],
                     -3, 0, alpha=0.15, color='gray', label='Reference period')
    ax.set_xlabel("Event-time (months relative to October 2023)")
    ax.set_ylabel(r"$\beta_{\mathrm{DID}}$ (treated×post interaction)")
    ax.set_title("Event-time DiD: CBAM transitional shock, T1 exposure (sponsor-based)\nPre-trends test in left half, dynamic effects in right half")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUT / "figures/event_time_dynamic_did.pdf")
    plt.close()
    print(f"\nFiguur: {OUT}/figures/event_time_dynamic_did.pdf")
    
    # Pre-trend test
    pre_buckets = dyn_df[dyn_df['event_time'] < 0]
    post_buckets = dyn_df[dyn_df['event_time'] >= 0]
    
    print(f"\nPre-trend assessment:")
    print(f"  Pre-treatment β_DID coefficients: {len(pre_buckets)}")
    print(f"  Number with CI crossing 0: {((pre_buckets['ci_lo'] < 0) & (pre_buckets['ci_hi'] > 0)).sum()}/{len(pre_buckets)}")
    print(f"  Mean pre β_DID: {pre_buckets['beta_did'].mean():+.3f}")
    print(f"\nPost-treatment summary:")
    print(f"  Mean post β_DID: {post_buckets['beta_did'].mean():+.3f}")
    print(f"  Number with CI excluding 0: {((post_buckets['ci_lo'] > 0) | (post_buckets['ci_hi'] < 0)).sum()}/{len(post_buckets)}")
    
except Exception as e:
    print(f"Dynamic spec failed: {e}")

print(f"\nResultaten directory: {OUT}")
