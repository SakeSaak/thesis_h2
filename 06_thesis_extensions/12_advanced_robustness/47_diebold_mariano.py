"""
47_diebold_mariano.py

============================================================================
Pijler 41: Diebold-Mariano forecast comparison voor M1/M2/M3 carbon-conditional
============================================================================

Reference:
  Diebold, Francis X. and Roberto S. Mariano (1995), "Comparing predictive
  accuracy", Journal of Business & Economic Statistics 13(3): 253-263.

  Hansen, Peter R., Asger Lunde, and James M. Nason (2011), "The model
  confidence set", Econometrica 79(2): 453-497.

Motivation:
  De thesis Chapter 7 vergelijkt drie specifications voor de carbon-conditional
  Blue/Green hazard interactie:
    M1 — Static β_int (constant over time)
    M2 — Time-block β_int (3-block random walk equivalent: pre-2018, 2018-2022, 2023+)
    M3 — Time-varying β_int(t) (smooth piecewise-linear approximation of GAS)

  De bestaande LOO-CV (results_robustness/loo_comparison.csv) wijst op M2/M4 als
  best-fitting, maar LOO is een leave-one-out fit-score, geen formele out-of-
  sample forecast comparison. Voor publication-grade forecast claims is de
  Diebold-Mariano test de standaard methodologie.

Methode:
  1. Build person-year panel (v7 sample) met time-varying EUA z_t
  2. Time-based split: train op years <= 2021, test op years >= 2022
     (test set heeft 75-80% van events door de 2023-2024 cancellation wave)
  3. Estimate M1, M2, M3 via discrete-time logit op training set
  4. OOS log-loss per project-year in test set per model:
        L_m,t = -y_t·log(p_m,t) - (1-y_t)·log(1-p_m,t)
  5. Pairwise DM tests:
        d_AB,t = L_A,t - L_B,t
        DM_AB = mean(d_AB) / sqrt(HAC_var(d_AB) / T)
        DM_AB ~ N(0,1) under H0 (equal predictive accuracy)
  6. Model Confidence Set (MCS) via Hansen-Lunde-Nason (2011) heuristic

Outputs:
  - results/dm_pairwise.csv (DM statistics + p-values)
  - results/dm_per_obs_losses.csv (per-observation losses, voor inspectie)
  - results/dm_model_summary.csv (summary statistics per model)
  - figures/dm_loss_comparison.pdf

Auteur: Sake Saakstra, 21 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import matplotlib.pyplot as plt

# ============================================================================
# CONFIG
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

SPLIT_YEAR = 2021  # train: <= this, test: > this
M2_BREAKPOINTS = (2017, 2022)  # 3 blocks: <=2017, 2018-2022, 2023+
RNG_SEED = 20260521
EPS = 1e-10


def hdr(t):
    print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD + BUILD PERSON-YEAR PANEL
# ============================================================================
hdr("Step 1: Load + build person-year panel")

df_proj = pd.read_csv(PROJECT_CSV)
print(f"v7 project-level data: {len(df_proj)} projects "
      f"({df_proj['is_blue_ccs'].sum()} Blue + {(df_proj['is_blue_ccs']==0).sum()} PEM)")

# Build person-year panel
panel_rows = []
for _, row in df_proj.iterrows():
    t_start = int(row['year_announced'])
    duration = int(row['duration'])
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
print(f"  Person-year panel: {len(panel)} rows | "
      f"events_any_yr: {panel['event_any_yr'].sum()}")

# Merge EUA (z-score) per calendar year
mp = pd.read_csv(MASTER_PANEL)
mp['date'] = pd.to_datetime(mp['date'], errors='coerce')
mp['year_calendar'] = mp['date'].dt.year

# EUA column detection
eua_col = next((c for c in mp.columns if 'eua' in c.lower() and 'z' in c.lower()), None)
if eua_col is None:
    eua_col = next((c for c in mp.columns if 'eua' in c.lower() and 'price' in c.lower()), None)
if eua_col is None:
    eua_col = next((c for c in mp.columns if 'eua' in c.lower()), None)
print(f"  Using EUA column: {eua_col}")

eua_yr = mp.groupby('year_calendar')[eua_col].mean().reset_index()
eua_yr.columns = ['year_calendar', 'eua_raw']
# Z-score over full sample period
eua_yr['eua_z'] = (eua_yr['eua_raw'] - eua_yr['eua_raw'].mean()) / eua_yr['eua_raw'].std()

panel = panel.merge(eua_yr[['year_calendar', 'eua_z']], on='year_calendar', how='left')
panel['eua_z'] = panel['eua_z'].fillna(panel['eua_z'].mean())  # post-2026 if extends
panel['blue_x_eua'] = panel['is_blue_ccs'] * panel['eua_z']

print(f"  Final panel: {len(panel)} rows, years {panel['year_calendar'].min()}-{panel['year_calendar'].max()}")
print(f"  Event rate: {panel['event_any_yr'].mean():.4f}")


# ============================================================================
# 2. TRAIN/TEST SPLIT
# ============================================================================
hdr("Step 2: Time-based train/test split")

train = panel[panel['year_calendar'] <= SPLIT_YEAR].copy()
test = panel[panel['year_calendar'] > SPLIT_YEAR].copy()
print(f"  Train: {len(train)} obs ({train['event_any_yr'].sum()} events), years <= {SPLIT_YEAR}")
print(f"  Test:  {len(test)} obs ({test['event_any_yr'].sum()} events), years > {SPLIT_YEAR}")


# ============================================================================
# 3. FIT THREE SPECIFICATIONS
# ============================================================================
hdr("Step 3: Estimate M1 (static), M2 (3-block), M3 (smooth time-varying)")

# Common base controls
def build_X(df, model='M1'):
    """Build design matrix for the three model specs."""
    base_cols = ['is_blue_ccs', 'log_capacity_mw', 'year_since_start']
    X = df[base_cols].copy()
    X['year_since_start_sq'] = X['year_since_start'] ** 2
    # Region dummies (drop 1)
    region_dum = pd.get_dummies(df['region'], prefix='region', drop_first=True, dtype=float)
    X = pd.concat([X, region_dum], axis=1)
    # Year linear effect (so models don't conflate time with β_int)
    X['eua_z'] = df['eua_z'].values

    if model == 'M1':
        # Static β_int (single blue × EUA interaction)
        X['blue_x_eua'] = df['blue_x_eua'].values

    elif model == 'M2':
        # 3-block β_int: separate interaction per block
        blk0 = (df['year_calendar'] <= M2_BREAKPOINTS[0]).astype(float).values
        blk1 = ((df['year_calendar'] > M2_BREAKPOINTS[0]) &
                (df['year_calendar'] <= M2_BREAKPOINTS[1])).astype(float).values
        blk2 = (df['year_calendar'] > M2_BREAKPOINTS[1]).astype(float).values
        X['blue_x_eua_blk0'] = (df['blue_x_eua'] * blk0).values
        X['blue_x_eua_blk1'] = (df['blue_x_eua'] * blk1).values
        X['blue_x_eua_blk2'] = (df['blue_x_eua'] * blk2).values

    elif model == 'M3':
        # Smooth time-varying β_int: interaction × linear time + interaction × quadratic time
        # Approximates GAS-driven smooth evolution
        yr_centered = (df['year_calendar'] - 2018).values
        X['blue_x_eua'] = df['blue_x_eua'].values
        X['blue_x_eua_yrtrend'] = (df['blue_x_eua'] * yr_centered).values
        X['blue_x_eua_yrtrend_sq'] = (df['blue_x_eua'] * (yr_centered ** 2)).values

    X = X.astype(float)
    X = sm.add_constant(X, has_constant='add')
    return X

def fit_model(train_df, model):
    """Fit discrete-time logit on training set."""
    X = build_X(train_df, model=model)
    y = train_df['event_any_yr'].astype(int).values
    # statsmodels Logit
    res = sm.Logit(y, X, missing='drop').fit(disp=0, maxiter=200, method='lbfgs')
    return res, list(X.columns)

def predict_proba(fit, df, model):
    """Predict probability of event_any_yr=1 for each row."""
    X = build_X(df, model=model)
    # Align columns to fit
    for c in fit.model.exog_names:
        if c not in X.columns:
            X[c] = 0.0
    X = X[fit.model.exog_names]
    return fit.predict(X)

models = {}
for spec in ['M1', 'M2', 'M3']:
    fit, cols = fit_model(train, spec)
    models[spec] = fit
    print(f"\n  {spec} fitted ({fit.df_model:.0f} params, "
          f"LLF train = {fit.llf:.2f}, pseudo-R² = {fit.prsquared:.4f})")
    # Report key blue×EUA coefficients
    for c in cols:
        if 'blue_x_eua' in c:
            i = fit.model.exog_names.index(c)
            est = fit.params.iloc[i] if hasattr(fit.params, 'iloc') else fit.params[i]
            se = fit.bse.iloc[i] if hasattr(fit.bse, 'iloc') else fit.bse[i]
            print(f"    {c}: β = {est:+.3f} (SE = {se:.3f})")


# ============================================================================
# 4. OOS PREDICTIONS + PER-OBS LOG-LOSS
# ============================================================================
hdr("Step 4: OOS predictions + per-observation log-loss on test set")

y_test = test['event_any_yr'].astype(int).values
loss_table = test[['project_id', 'year_calendar', 'is_blue_ccs', 'event_any_yr']].copy()

for spec, fit in models.items():
    p = np.clip(predict_proba(fit, test, spec), EPS, 1 - EPS)
    # Bernoulli log-loss
    loss = -(y_test * np.log(p) + (1 - y_test) * np.log(1 - p))
    loss_table[f'p_{spec}'] = p
    loss_table[f'loss_{spec}'] = loss
    print(f"  {spec}: mean log-loss = {loss.mean():.5f}, "
          f"sum = {loss.sum():.2f}")

loss_table.to_csv(OUTPUT_DIR / "dm_per_obs_losses.csv", index=False)


# ============================================================================
# 5. PAIRWISE DIEBOLD-MARIANO TESTS
# ============================================================================
hdr("Step 5: Pairwise Diebold-Mariano tests")

def hac_variance(d, lag=None):
    """Newey-West HAC variance estimate for series d."""
    d = np.asarray(d, dtype=float)
    T = len(d)
    if lag is None:
        lag = max(1, int(np.floor(T ** (1/3))))
    d_bar = d.mean()
    e = d - d_bar
    gamma0 = (e @ e) / T
    var_hac = gamma0
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1)  # Bartlett kernel
        gamma_k = (e[k:] @ e[:-k]) / T
        var_hac += 2.0 * w * gamma_k
    return max(var_hac, EPS)

def dm_test(loss_A, loss_B):
    """Diebold-Mariano test: H0 E[loss_A - loss_B] = 0."""
    d = np.asarray(loss_A) - np.asarray(loss_B)
    T = len(d)
    d_bar = d.mean()
    v_hac = hac_variance(d)
    se = np.sqrt(v_hac / T)
    dm = d_bar / se
    pval = 2.0 * (1.0 - stats.norm.cdf(abs(dm)))
    # Harvey-Leybourne-Newbold (1997) small-sample correction
    lag = max(1, int(np.floor(T ** (1/3))))
    correction = np.sqrt((T + 1 - 2*lag + lag*(lag-1)/T) / T)
    dm_hln = dm * correction
    pval_hln = 2.0 * (1.0 - stats.t.cdf(abs(dm_hln), df=T-1))
    return {
        'mean_diff': d_bar,
        'se_hac': se,
        'DM_stat': dm,
        'DM_pvalue': pval,
        'DM_HLN_stat': dm_hln,
        'DM_HLN_pvalue': pval_hln,
        'T': T,
        'lag_NW': lag,
    }

pairs = [('M1', 'M2'), ('M1', 'M3'), ('M2', 'M3')]
dm_results = []
for A, B in pairs:
    out = dm_test(loss_table[f'loss_{A}'].values, loss_table[f'loss_{B}'].values)
    out.update({'model_A': A, 'model_B': B})
    dm_results.append(out)
    sign = 'A better' if out['mean_diff'] < 0 else 'B better' if out['mean_diff'] > 0 else 'equal'
    print(f"  {A} vs {B}: mean diff = {out['mean_diff']:+.5f}, "
          f"DM = {out['DM_stat']:+.2f}, p = {out['DM_pvalue']:.3f}, "
          f"DM-HLN = {out['DM_HLN_stat']:+.2f}, p_HLN = {out['DM_HLN_pvalue']:.3f}  "
          f"[{sign}]")

dm_df = pd.DataFrame(dm_results)
dm_df = dm_df[['model_A', 'model_B', 'mean_diff', 'se_hac',
               'DM_stat', 'DM_pvalue', 'DM_HLN_stat', 'DM_HLN_pvalue', 'T', 'lag_NW']]
dm_df.to_csv(OUTPUT_DIR / "dm_pairwise.csv", index=False)


# ============================================================================
# 6. MODEL CONFIDENCE SET (heuristic)
# ============================================================================
hdr("Step 6: Model Confidence Set (Hansen-Lunde-Nason 2011, simplified)")

mean_loss = {m: loss_table[f'loss_{m}'].mean() for m in ['M1', 'M2', 'M3']}
print("  Mean OOS log-loss per model:")
for m, lv in sorted(mean_loss.items(), key=lambda x: x[1]):
    print(f"    {m}: {lv:.5f}")

# Simple MCS heuristic: keep models where pairwise DM-HLN p > 0.10 vs the best
best = min(mean_loss, key=mean_loss.get)
mcs = {best}
for m in ['M1', 'M2', 'M3']:
    if m == best:
        continue
    pair = [(r['model_A'], r['model_B'], r['DM_HLN_pvalue']) for r in dm_results
            if {r['model_A'], r['model_B']} == {best, m}][0]
    if pair[2] > 0.10:
        mcs.add(m)
print(f"\n  Best model by mean loss: {best}")
print(f"  Model Confidence Set (p_HLN > 0.10): {sorted(mcs)}")


# ============================================================================
# 7. SUMMARY + FIGURE
# ============================================================================
hdr("Step 7: Summary tables + figure")

summary = pd.DataFrame([
    {'model': m,
     'n_params': int(models[m].df_model + 1),
     'LLF_train': float(models[m].llf),
     'pseudo_R2_train': float(models[m].prsquared),
     'mean_OOS_log_loss': float(mean_loss[m]),
     'sum_OOS_log_loss': float(loss_table[f'loss_{m}'].sum()),
     'in_MCS_p10': m in mcs}
    for m in ['M1', 'M2', 'M3']
])
summary.to_csv(OUTPUT_DIR / "dm_model_summary.csv", index=False)
print(summary.to_string(index=False))

# Figure: per-year cumulative loss
fig, ax = plt.subplots(figsize=(8, 5))
years_test = sorted(loss_table['year_calendar'].unique())
for m, color in zip(['M1', 'M2', 'M3'], ['#1f77b4', '#ff7f0e', '#2ca02c']):
    yr_loss = loss_table.groupby('year_calendar')[f'loss_{m}'].sum().reindex(years_test).fillna(0)
    ax.plot(yr_loss.index, yr_loss.cumsum().values, marker='o', label=m, color=color, lw=2)
ax.set_xlabel('Calendar year (test set)')
ax.set_ylabel('Cumulative OOS log-loss')
ax.set_title(f'Cumulative OOS log-loss by year, train ≤ {SPLIT_YEAR}')
ax.legend(title='Specification', loc='upper left')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(FIG_DIR / "dm_loss_comparison.pdf", bbox_inches='tight')
plt.savefig(FIG_DIR / "dm_loss_comparison.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"\nFigure saved: {FIG_DIR / 'dm_loss_comparison.pdf'}")

hdr("DONE")
print(f"Outputs:\n  {OUTPUT_DIR / 'dm_pairwise.csv'}")
print(f"  {OUTPUT_DIR / 'dm_per_obs_losses.csv'}")
print(f"  {OUTPUT_DIR / 'dm_model_summary.csv'}")
print(f"  {FIG_DIR / 'dm_loss_comparison.pdf'}")
