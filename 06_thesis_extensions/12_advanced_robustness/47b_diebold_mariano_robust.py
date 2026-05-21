"""
47b_diebold_mariano_robust.py

Robustness extension to 47_diebold_mariano.py.

ISSUE met v1 (time-based split <= 2021): training set bevat slechts 5 events
omdat 88% van events in de 2023-2024 cancellation wave zit. Dit reduceert de
power van de DM test substantieel.

UITBREIDING:
  V1. Time-based split (47_diebold_mariano.py) — al gerund
  V2. K-fold CV per project (k=5) — random 80/20 splits, alle events in
      train AND test verdeling
  V3. Rolling-window 1-step-ahead — voor T in [2021..2024], fit op years <= T-1,
      predict year T

Identical loss function (Bernoulli log-loss) en DM testing methodology als v1.
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt

# Reuse panel construction from 47
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"

EPS = 1e-10
M2_BREAKPOINTS = (2017, 2022)
RNG_SEED = 20260521

def hdr(t):
    print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)

# Build panel (identical to 47)
df_proj = pd.read_csv(PROJECT_CSV)
panel_rows = []
for _, row in df_proj.iterrows():
    t_start = int(row['year_announced']); duration = int(row['duration'])
    t_end = t_start + duration
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
            'region': row['region'],
            'year_announced': t_start,
        })
panel = pd.DataFrame(panel_rows)

mp = pd.read_csv(MASTER_PANEL)
mp['date'] = pd.to_datetime(mp['date'], errors='coerce')
mp['year_calendar'] = mp['date'].dt.year
eua_yr = mp.groupby('year_calendar')['eua_phase3'].mean().reset_index()
eua_yr.columns = ['year_calendar', 'eua_raw']
eua_yr['eua_z'] = (eua_yr['eua_raw'] - eua_yr['eua_raw'].mean()) / eua_yr['eua_raw'].std()
panel = panel.merge(eua_yr[['year_calendar', 'eua_z']], on='year_calendar', how='left')
panel['eua_z'] = panel['eua_z'].fillna(panel['eua_z'].mean())
panel['blue_x_eua'] = panel['is_blue_ccs'] * panel['eua_z']

print(f"Panel: {len(panel)} rows, {panel['event_any_yr'].sum()} events, "
      f"{panel['project_id'].nunique()} projects")


def build_X(df, model='M1'):
    base_cols = ['is_blue_ccs', 'log_capacity_mw', 'year_since_start']
    X = df[base_cols].copy()
    X['year_since_start_sq'] = X['year_since_start'] ** 2
    region_dum = pd.get_dummies(df['region'], prefix='region', drop_first=True, dtype=float)
    X = pd.concat([X, region_dum], axis=1)
    X['eua_z'] = df['eua_z'].values

    if model == 'M1':
        X['blue_x_eua'] = df['blue_x_eua'].values
    elif model == 'M2':
        blk0 = (df['year_calendar'] <= M2_BREAKPOINTS[0]).astype(float).values
        blk1 = ((df['year_calendar'] > M2_BREAKPOINTS[0]) & (df['year_calendar'] <= M2_BREAKPOINTS[1])).astype(float).values
        blk2 = (df['year_calendar'] > M2_BREAKPOINTS[1]).astype(float).values
        X['blue_x_eua_blk0'] = (df['blue_x_eua'] * blk0).values
        X['blue_x_eua_blk1'] = (df['blue_x_eua'] * blk1).values
        X['blue_x_eua_blk2'] = (df['blue_x_eua'] * blk2).values
    elif model == 'M3':
        yr_centered = (df['year_calendar'] - 2018).values
        X['blue_x_eua'] = df['blue_x_eua'].values
        X['blue_x_eua_yrtrend'] = (df['blue_x_eua'] * yr_centered).values
        X['blue_x_eua_yrtrend_sq'] = (df['blue_x_eua'] * (yr_centered ** 2)).values
    X = X.astype(float)
    X = sm.add_constant(X, has_constant='add')
    return X

def fit_predict(train_df, test_df, model):
    X_tr = build_X(train_df, model); y_tr = train_df['event_any_yr'].astype(int).values
    try:
        fit = sm.Logit(y_tr, X_tr).fit(disp=0, maxiter=300, method='lbfgs')
    except Exception:
        # Fallback: ridge-regularized via L-BFGS-B
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(C=1.0, max_iter=2000, fit_intercept=False)
        lr.fit(X_tr.values, y_tr)
        X_te = build_X(test_df, model)
        for c in X_tr.columns:
            if c not in X_te.columns: X_te[c] = 0.0
        X_te = X_te[X_tr.columns]
        return np.clip(lr.predict_proba(X_te.values)[:, 1], EPS, 1-EPS), None
    X_te = build_X(test_df, model)
    for c in fit.model.exog_names:
        if c not in X_te.columns: X_te[c] = 0.0
    X_te = X_te[fit.model.exog_names]
    return np.clip(fit.predict(X_te), EPS, 1-EPS), fit


def hac_var(d, lag=None):
    d = np.asarray(d, dtype=float); T = len(d)
    if lag is None: lag = max(1, int(np.floor(T ** (1/3))))
    e = d - d.mean()
    v = (e @ e) / T
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        v += 2 * w * (e[k:] @ e[:-k]) / T
    return max(v, EPS)

def dm_test(loss_A, loss_B):
    d = np.asarray(loss_A) - np.asarray(loss_B); T = len(d)
    d_bar = d.mean(); v = hac_var(d); se = np.sqrt(v / T)
    dm = d_bar / se
    lag = max(1, int(np.floor(T ** (1/3))))
    corr = np.sqrt((T + 1 - 2*lag + lag*(lag-1)/T) / T)
    dm_hln = dm * corr
    return {'mean_diff': d_bar, 'se_hac': se, 'DM_stat': dm,
            'DM_pvalue': 2*(1 - stats.norm.cdf(abs(dm))),
            'DM_HLN_stat': dm_hln,
            'DM_HLN_pvalue': 2*(1 - stats.t.cdf(abs(dm_hln), df=T-1)),
            'T': T}


# ============================================================================
# V2 — 5-FOLD CV PER PROJECT
# ============================================================================
hdr("V2 — 5-fold CV per project (events spread across train and test)")

rng = np.random.RandomState(RNG_SEED)
project_ids = panel['project_id'].unique()
rng.shuffle(project_ids)

kf = KFold(n_splits=5, shuffle=True, random_state=RNG_SEED)
all_loss = []

for fold_idx, (train_pids_idx, test_pids_idx) in enumerate(kf.split(project_ids)):
    train_pids = project_ids[train_pids_idx]
    test_pids = project_ids[test_pids_idx]
    train_df = panel[panel['project_id'].isin(train_pids)].copy()
    test_df = panel[panel['project_id'].isin(test_pids)].copy()
    fold_results = {'fold': fold_idx + 1, 'n_train': len(train_df),
                    'n_test': len(test_df), 'events_train': int(train_df['event_any_yr'].sum()),
                    'events_test': int(test_df['event_any_yr'].sum())}
    y_te = test_df['event_any_yr'].astype(int).values
    losses_this_fold = {'fold': fold_idx + 1,
                        'project_id': test_df['project_id'].values,
                        'year_calendar': test_df['year_calendar'].values,
                        'event': y_te}
    for spec in ['M1', 'M2', 'M3']:
        p, _ = fit_predict(train_df, test_df, spec)
        loss = -(y_te * np.log(p) + (1-y_te) * np.log(1-p))
        losses_this_fold[f'loss_{spec}'] = loss
        fold_results[f'mean_loss_{spec}'] = loss.mean()
    all_loss.append(pd.DataFrame(losses_this_fold))
    print(f"  Fold {fold_idx+1}: train events={fold_results['events_train']}, "
          f"test events={fold_results['events_test']}, "
          f"M1={fold_results['mean_loss_M1']:.5f}, M2={fold_results['mean_loss_M2']:.5f}, "
          f"M3={fold_results['mean_loss_M3']:.5f}")

pooled = pd.concat(all_loss, ignore_index=True)
print(f"\nPooled: {len(pooled)} obs, {pooled['event'].sum()} events across folds")

print("\nMean OOS log-loss across all folds:")
for m in ['M1', 'M2', 'M3']:
    print(f"  {m}: {pooled[f'loss_{m}'].mean():.5f}")

print("\nPairwise DM tests on pooled losses:")
dm_results_v2 = []
for A, B in [('M1', 'M2'), ('M1', 'M3'), ('M2', 'M3')]:
    out = dm_test(pooled[f'loss_{A}'].values, pooled[f'loss_{B}'].values)
    out.update({'model_A': A, 'model_B': B, 'method': '5-fold CV pooled'})
    dm_results_v2.append(out)
    print(f"  {A} vs {B}: mean diff = {out['mean_diff']:+.5f}, "
          f"DM-HLN = {out['DM_HLN_stat']:+.2f}, p_HLN = {out['DM_HLN_pvalue']:.3f}")


# ============================================================================
# V3 — ROLLING-WINDOW 1-STEP-AHEAD FORECAST
# ============================================================================
hdr("V3 — Rolling-window 1-step-ahead forecast")

rolling_losses = []
for T in [2021, 2022, 2023, 2024]:
    train_df = panel[panel['year_calendar'] < T].copy()
    test_df = panel[panel['year_calendar'] == T].copy()
    if len(test_df) == 0: continue
    y_te = test_df['event_any_yr'].astype(int).values
    print(f"\n  Year T={T}: train events={int(train_df['event_any_yr'].sum())}, "
          f"test obs={len(test_df)}, test events={int(y_te.sum())}")
    row = {'year': T, 'n_test': len(test_df), 'events_test': int(y_te.sum())}
    losses_yr = {'year': T, 'project_id': test_df['project_id'].values, 'event': y_te}
    for spec in ['M1', 'M2', 'M3']:
        p, _ = fit_predict(train_df, test_df, spec)
        loss = -(y_te * np.log(p) + (1-y_te) * np.log(1-p))
        losses_yr[f'loss_{spec}'] = loss
        row[f'mean_loss_{spec}'] = loss.mean()
        row[f'sum_loss_{spec}'] = loss.sum()
        print(f"    {spec}: mean loss = {loss.mean():.5f}, sum = {loss.sum():.2f}")
    rolling_losses.append(pd.DataFrame(losses_yr))

rolling = pd.concat(rolling_losses, ignore_index=True)
print(f"\nRolling pooled: {len(rolling)} obs, {rolling['event'].sum()} events")
print("\nPairwise DM tests on rolling-window pooled losses:")
dm_results_v3 = []
for A, B in [('M1', 'M2'), ('M1', 'M3'), ('M2', 'M3')]:
    out = dm_test(rolling[f'loss_{A}'].values, rolling[f'loss_{B}'].values)
    out.update({'model_A': A, 'model_B': B, 'method': 'Rolling 1-step'})
    dm_results_v3.append(out)
    print(f"  {A} vs {B}: mean diff = {out['mean_diff']:+.5f}, "
          f"DM-HLN = {out['DM_HLN_stat']:+.2f}, p_HLN = {out['DM_HLN_pvalue']:.3f}")


# ============================================================================
# COMBINE + SAVE
# ============================================================================
hdr("Combine all DM-test results across V1 (time-split), V2 (5-fold CV), V3 (rolling)")

# Read V1 results
dm_v1 = pd.read_csv(OUTPUT_DIR / "dm_pairwise.csv")
dm_v1['method'] = 'Time-split (train <=2021)'
dm_v2 = pd.DataFrame(dm_results_v2)
dm_v3 = pd.DataFrame(dm_results_v3)

# Pad columns
for df in (dm_v1, dm_v2, dm_v3):
    for c in ['mean_diff', 'se_hac', 'DM_stat', 'DM_pvalue', 'DM_HLN_stat', 'DM_HLN_pvalue', 'T', 'method']:
        if c not in df.columns: df[c] = np.nan

cols_keep = ['method', 'model_A', 'model_B', 'mean_diff', 'DM_HLN_stat', 'DM_HLN_pvalue', 'T']
combined = pd.concat([dm_v1[cols_keep], dm_v2[cols_keep], dm_v3[cols_keep]], ignore_index=True)
combined.to_csv(OUTPUT_DIR / "dm_pairwise_combined.csv", index=False)
print("\nCombined DM pairwise table:")
print(combined.to_string(index=False))

# Mean OOS log-loss per model per method
summary_combined = pd.DataFrame([
    {'method': 'Time-split (train <=2021)', 'model': 'M1', 'mean_loss': 0.29761, 'best?': False},
    {'method': 'Time-split (train <=2021)', 'model': 'M2', 'mean_loss': 0.29749, 'best?': False},
    {'method': 'Time-split (train <=2021)', 'model': 'M3', 'mean_loss': 0.29657, 'best?': True},
    {'method': '5-fold CV pooled', 'model': 'M1', 'mean_loss': pooled['loss_M1'].mean(), 'best?': False},
    {'method': '5-fold CV pooled', 'model': 'M2', 'mean_loss': pooled['loss_M2'].mean(), 'best?': False},
    {'method': '5-fold CV pooled', 'model': 'M3', 'mean_loss': pooled['loss_M3'].mean(), 'best?': False},
    {'method': 'Rolling 1-step',   'model': 'M1', 'mean_loss': rolling['loss_M1'].mean(), 'best?': False},
    {'method': 'Rolling 1-step',   'model': 'M2', 'mean_loss': rolling['loss_M2'].mean(), 'best?': False},
    {'method': 'Rolling 1-step',   'model': 'M3', 'mean_loss': rolling['loss_M3'].mean(), 'best?': False},
])
# Mark best per method
for method in summary_combined['method'].unique():
    mask = summary_combined['method'] == method
    best_idx = summary_combined.loc[mask, 'mean_loss'].idxmin()
    summary_combined['best?'] = False
    summary_combined.loc[best_idx, 'best?'] = True
# We have to do this per method actually
summary_combined['best?'] = False
for method in summary_combined['method'].unique():
    sub = summary_combined[summary_combined['method'] == method]
    best_model = sub.loc[sub['mean_loss'].idxmin(), 'model']
    summary_combined.loc[(summary_combined['method'] == method) & (summary_combined['model'] == best_model), 'best?'] = True

summary_combined.to_csv(OUTPUT_DIR / "dm_model_summary_combined.csv", index=False)
print("\nMean OOS log-loss across all three methodologies:")
print(summary_combined.to_string(index=False))

print(f"\nOutputs:\n  {OUTPUT_DIR / 'dm_pairwise_combined.csv'}")
print(f"  {OUTPUT_DIR / 'dm_model_summary_combined.csv'}")
