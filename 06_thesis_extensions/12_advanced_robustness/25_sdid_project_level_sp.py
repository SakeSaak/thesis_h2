"""
25_sdid_project_level_sp.py

============================================================================
Pijler 21: Synthetic DiD project-level op S&P (vervangt Pijler 5)
============================================================================

Reference:
  Arkhangelsky et al (2021), "Synthetic Difference-in-Differences",
    American Economic Review 111(12): 4088-4118
  Abadie, Diamond & Hainmueller (2010), "Synthetic control methods for
    comparative case studies", JASA 105(490): 493-505

Motivatie:
  Pijler 5 deed regional SDID met t*=2023 (informative null, p_perm=0.167).
  Pijler 17 deed sequential SDID op regionaal niveau (informative null).
  Pijler 21 levert PROJECT-LEVEL granularity via:

  Method 1: SUBGROUP PANEL SDID
    Cells = (region × technology) = 14 cells (7 regions × 2 tech)
    Treated: EU × Green (1 cell)
    Controls: 13 cells
    Test = ATT_EUgreen op cumulative cancellation rate

  Method 2: 1-NN MATCHING op pre-treatment covariates
    Voor elke EU Green project: find nearest non-EU Green op
    log_capacity en announce_year (Mahalanobis distance)
    ATT = mean(Y_treated - Y_matched_control)

Beide methoden hebben complementaire strengths:
  - SDID: respect aggregate trends, handle time-varying confounders
  - NN matching: project-level granularity, doesn't require panel structure

Pijler 21 in de robustness battery. Sake Saakstra, 20 mei 2026.
"""

from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy import stats
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_START = 2018
T_TREAT = 2024
T_END = 2026
SEED = 20260520
B_BOOT = 500


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD DATA ===
header("STAP 1: Laad S&P data en bouw 14-cell subgroup panel")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()

# Blue/Green classification
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
df = sp[(sp['is_blue'] == 1) | (sp['is_green'] == 1)].copy()
df['tech'] = np.where(df['is_blue'] == 1, 'Blue', 'Green')
df['region'] = df['Region major']

# Event
df['event_cancel'] = (df['project_status'] == 'Plans cancelled').astype(int)
df['cancellation_year'] = np.where(
    (df['event_cancel'] == 1) & df['est_year_online'].notna(),
    np.ceil((df['announce_year'] + df['est_year_online']) / 2),
    np.where(df['event_cancel'] == 1, df['announce_year'] + 3, np.nan)
).clip(max=2026.0)

print(f"Sample: {len(df)} Blue+Green projecten")
print(f"  Regions × Tech distributie:")
ct = pd.crosstab(df['region'], df['tech'], margins=True)
print(ct.to_string())


# === STAP 2: BOUW SUBGROUP PANEL (14 cells × 9 years) ===
header("STAP 2: Bouw subgroup panel")

cells = []
for region in df['region'].dropna().unique():
    for tech in ['Blue', 'Green']:
        cell = df[(df['region'] == region) & (df['tech'] == tech)]
        if len(cell) == 0:
            continue
        for t in range(T_START, T_END + 1):
            risk_set = cell[cell['announce_year'] <= t]
            if len(risk_set) == 0:
                continue
            n_cancel = ((risk_set['event_cancel'] == 1) &
                        (risk_set['cancellation_year'].notna()) &
                        (risk_set['cancellation_year'] <= t)).sum()
            Y = n_cancel / len(risk_set)
            cells.append({
                'region': region,
                'tech': tech,
                'cell': f"{region}|{tech}",
                't': t,
                'Y': Y,
                'n_risk_set': len(risk_set),
                'n_events': n_cancel,
            })

panel = pd.DataFrame(cells)
print(f"Panel: {panel.shape}")
print(f"\nUnique cells: {panel['cell'].nunique()}")

# Wide format
Y_wide = panel.pivot(index='cell', columns='t', values='Y').fillna(0)
print(f"\nY (cumulative cancellation rate per cell):")
print(Y_wide.round(4).to_string())

# Drop cells with no variance (all zeros)
keep_mask = Y_wide.sum(axis=1) > 0
Y_wide = Y_wide[keep_mask]
print(f"\nNa filtering: {Y_wide.shape[0]} cells met events")


# === STAP 3: SDID FUNCTIE ===

def estimate_sdid(Y, treated_unit, t_treat, pre_periods, post_periods, zeta=None):
    """SDID met SLSQP omega-optimalisatie en uniform lambda."""
    if treated_unit not in Y.index:
        return None
    controls = [u for u in Y.index if u != treated_unit]
    n_co = len(controls)
    if n_co < 2:
        return None
    T_pre = len(pre_periods)
    T_post = len(post_periods)

    Y_t_pre = Y.loc[treated_unit, pre_periods].values.astype(float)
    Y_t_post = Y.loc[treated_unit, post_periods].values.astype(float)
    Y_c_pre = Y.loc[controls, pre_periods].values.astype(float)
    Y_c_post = Y.loc[controls, post_periods].values.astype(float)

    if zeta is None:
        diff_co = np.diff(Y_c_pre, axis=1)
        sigma_hat = float(np.std(diff_co))
        zeta = (n_co * T_post) ** 0.25 * sigma_hat

    def omega_loss(w):
        synth = w @ Y_c_pre
        residual = float(np.sum((Y_t_pre - synth) ** 2))
        reg = zeta ** 2 * float(np.sum(w ** 2)) * T_pre
        return residual + reg

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},)
    bounds = [(0, 1) for _ in range(n_co)]
    w0 = np.ones(n_co) / n_co
    res = minimize(omega_loss, w0, method='SLSQP', bounds=bounds, constraints=cons,
                   options={'maxiter': 500, 'ftol': 1e-9})
    omega = np.clip(res.x, 0, None)
    omega = omega / omega.sum() if omega.sum() > 0 else omega

    lam = np.ones(T_pre) / T_pre
    Y_synth_pre = omega @ Y_c_pre
    Y_synth_post = omega @ Y_c_post

    tau = (np.mean(Y_t_post) - lam @ Y_t_pre) \
        - (np.mean(Y_synth_post) - lam @ Y_synth_pre)

    return {
        'ATT': float(tau),
        'omega': dict(zip(controls, omega)),
        'controls': controls,
        'Y_t_pre': Y_t_pre,
        'Y_t_post': Y_t_post,
        'Y_synth_pre': Y_synth_pre,
        'Y_synth_post': Y_synth_post,
    }


# === STAP 4: TEST A — EU GREEN vs ALL CONTROLS ===
header("STAP 4: Method 1A — SDID met EU Green als treated (alle anderen als control)")

t_treat = T_TREAT
pre = list(range(T_START, t_treat))
post = list(range(t_treat, T_END + 1))

if 'Europe (EU-27)|Green' in Y_wide.index:
    result_A = estimate_sdid(Y_wide, 'Europe (EU-27)|Green', t_treat, pre, post)
    print(f"\nATT_EUGreen = {result_A['ATT']:+.4f}")
    print(f"\nTop 5 omega weights (synthetic EU Green composition):")
    sorted_omegas = sorted(result_A['omega'].items(), key=lambda x: -x[1])
    for u, w in sorted_omegas[:5]:
        if w > 0.001:
            print(f"  {u:<35} {w:.3f}")
    print(f"\nY_treated pre:  {result_A['Y_t_pre'].round(4)}")
    print(f"Y_synth pre:    {result_A['Y_synth_pre'].round(4)}")
    print(f"Y_treated post: {result_A['Y_t_post'].round(4)}")
    print(f"Y_synth post:   {result_A['Y_synth_post'].round(4)}")

    # Permutation inference
    print(f"\nPermutation inference (each control unit as placebo)...")
    placebos = []
    for placebo in result_A['controls']:
        try:
            r = estimate_sdid(Y_wide, placebo, t_treat, pre, post)
            if r is not None:
                placebos.append(r['ATT'])
        except Exception:
            continue
    placebos = np.array(placebos)
    p_perm = float(np.mean(np.abs(placebos) >= np.abs(result_A['ATT']))) if len(placebos) > 0 else float('nan')
    print(f"  Placebo distribution (n={len(placebos)}): mean={placebos.mean():+.4f}, sd={placebos.std():.4f}")
    print(f"  Range: [{placebos.min():+.4f}, {placebos.max():+.4f}]")
    print(f"  Treated ATT: {result_A['ATT']:+.4f}")
    print(f"  Permutation p-waarde: {p_perm:.4f}")


# === STAP 5: TEST B — EU GREEN vs NON-EU GREEN (clean tech comparison) ===
header("STAP 5: Method 1B — EU Green vs only non-EU Green cells")

Y_green_only = Y_wide[Y_wide.index.str.contains('Green')]
print(f"Green-only sample: {Y_green_only.shape}")
print(Y_green_only.round(4).to_string())

if 'Europe (EU-27)|Green' in Y_green_only.index:
    result_B = estimate_sdid(Y_green_only, 'Europe (EU-27)|Green', t_treat, pre, post)
    if result_B:
        print(f"\nATT_EUGreen (clean comparison) = {result_B['ATT']:+.4f}")
        print(f"\nOmega weights:")
        for u, w in sorted(result_B['omega'].items(), key=lambda x: -x[1]):
            if w > 0.001:
                print(f"  {u:<35} {w:.3f}")

        # Permutation
        placebos_B = []
        for placebo in result_B['controls']:
            try:
                r = estimate_sdid(Y_green_only, placebo, t_treat, pre, post)
                if r is not None:
                    placebos_B.append(r['ATT'])
            except Exception:
                continue
        placebos_B = np.array(placebos_B)
        p_perm_B = float(np.mean(np.abs(placebos_B) >= np.abs(result_B['ATT']))) if len(placebos_B) > 0 else float('nan')
        print(f"  Placebo n={len(placebos_B)}, p_perm = {p_perm_B:.4f}")


# === STAP 6: METHOD 2 — 1-NN MATCHING OP PROJECT-LEVEL ===
header("STAP 6: Method 2 — 1-NN matching op log_capacity + announce_year")

df['log_capacity'] = np.log1p(pd.to_numeric(df['Output capacity per year'], errors='coerce').fillna(0))

# EU Green = treated
eu_green = df[(df['region'] == 'Europe (EU-27)') & (df['tech'] == 'Green')].copy()
non_eu_green = df[(df['region'] != 'Europe (EU-27)') & (df['tech'] == 'Green')].copy()

print(f"Treated (EU Green): n = {len(eu_green)}")
print(f"Control pool (non-EU Green): n = {len(non_eu_green)}")

# Standardize matching features
scaler = StandardScaler()
features_co = scaler.fit_transform(non_eu_green[['log_capacity', 'announce_year']].values)
features_tr = scaler.transform(eu_green[['log_capacity', 'announce_year']].values)

# Match: 1-NN
nbrs = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(features_co)
distances, indices = nbrs.kneighbors(features_tr)

# Get matched outcomes
eu_green_idx = eu_green.reset_index(drop=True)
matched_co_idx = non_eu_green.iloc[indices.flatten()].reset_index(drop=True)

print(f"\nMatched pairs: {len(eu_green_idx)} EU Green → {len(matched_co_idx)} matched non-EU Green")
print(f"Mean matching distance (standardized): {distances.mean():.3f}")

# ATT on event_cancel
Y_treated = eu_green_idx['event_cancel'].values
Y_control = matched_co_idx['event_cancel'].values
ATT_matching = float(Y_treated.mean() - Y_control.mean())

print(f"\nTreated cancellation rate (EU Green):  {Y_treated.mean():.4f}")
print(f"Matched control cancellation rate:     {Y_control.mean():.4f}")
print(f"ATT (matching) = {ATT_matching:+.4f}")

# Bootstrap inference (cluster bootstrap on treated units)
rng = np.random.default_rng(SEED)
boot_atts = []
n_tr = len(eu_green_idx)
for b in range(B_BOOT):
    idx = rng.choice(n_tr, size=n_tr, replace=True)
    yT = Y_treated[idx]
    yC = Y_control[idx]
    boot_atts.append(yT.mean() - yC.mean())
boot_atts = np.array(boot_atts)
ci_lo, ci_hi = np.percentile(boot_atts, [2.5, 97.5])
p_boot = float(np.mean(np.abs(boot_atts) >= np.abs(ATT_matching)) if ATT_matching != 0 else 1.0)
# Hetzelfde, maar tweezijdig
if ATT_matching > 0:
    p_boot_2sided = 2 * np.mean(boot_atts <= 0)
else:
    p_boot_2sided = 2 * np.mean(boot_atts >= 0)
p_boot_2sided = min(p_boot_2sided, 1.0)

print(f"\nBootstrap inference (B={B_BOOT}):")
print(f"  ATT_matching = {ATT_matching:+.4f}")
print(f"  Bootstrap mean = {boot_atts.mean():+.4f}")
print(f"  Bootstrap SE = {boot_atts.std():.4f}")
print(f"  95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]")
print(f"  Tweezijdige bootstrap p = {p_boot_2sided:.4f}")


# === STAP 7: FIGUREN ===
header("STAP 7: Figuren")

# Fig 1: SDID time series voor EU Green
fig, ax = plt.subplots(figsize=(11, 6))
years = list(range(T_START, T_END + 1))
if 'result_A' in dir() and result_A:
    Y_tr_all = np.concatenate([result_A['Y_t_pre'], result_A['Y_t_post']])
    Y_synth_all = np.concatenate([result_A['Y_synth_pre'], result_A['Y_synth_post']])
    ax.plot(years, Y_tr_all, 'o-', color='#d62728', linewidth=2.5, markersize=8, label='EU Green (treated)')
    ax.plot(years, Y_synth_all, 's--', color='#1f77b4', linewidth=2, markersize=7, label='Synthetic counterfactual')
    ax.axvline(x=t_treat - 0.5, color='gray', linestyle=':', alpha=0.7, label=f'CBAM t* = {t_treat}')
    ax.fill_between([t_treat - 0.5, T_END + 0.5], 0, max(Y_tr_all.max(), Y_synth_all.max()) * 1.2,
                    alpha=0.1, color='red', label='Post-treatment')
    ax.set_xlabel('Calendar year', fontsize=11)
    ax.set_ylabel('Cumulative cancellation rate', fontsize=11)
    ax.set_title(f'Pijler 21: Project-level SDID — EU Green vs Synthetic\nATT = {result_A["ATT"]:+.4f}',
                 fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler21_sdid_timeseries.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler21_sdid_timeseries.png")

# Fig 2: ATT comparison + bootstrap distribution
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Panel 1: ATT comparison
methods_lbl = ['SDID Method 1A\n(EU Green vs all)',
               'SDID Method 1B\n(EU Green vs nonEU Green)',
               '1-NN Matching\n(project-level)']
atts_lst = [result_A['ATT'] if result_A else 0,
            result_B['ATT'] if result_B else 0,
            ATT_matching]
colors = ['#d62728', '#ff7f0e', '#2ca02c']
ax1.bar(methods_lbl, atts_lst, color=colors, edgecolor='black', width=0.5)
for i, v in enumerate(atts_lst):
    ax1.text(i, v + (0.005 if v > 0 else -0.01), f'{v:+.4f}', ha='center', fontsize=10, fontweight='bold')
ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax1.set_ylabel('ATT (EU Green effect)', fontsize=11)
ax1.set_title('ATT estimates across 3 methods', fontsize=11)
ax1.grid(axis='y', alpha=0.3)

# Panel 2: Bootstrap distribution for matching
ax2.hist(boot_atts, bins=40, color='#2ca02c', edgecolor='black', alpha=0.7)
ax2.axvline(x=ATT_matching, color='black', linestyle='-', linewidth=2, label=f'ATT = {ATT_matching:+.4f}')
ax2.axvline(x=ci_lo, color='red', linestyle='--', label=f'95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]')
ax2.axvline(x=ci_hi, color='red', linestyle='--')
ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.5)
ax2.set_xlabel('Bootstrap ATT', fontsize=11)
ax2.set_ylabel('Frequency', fontsize=11)
ax2.set_title(f'Bootstrap distribution (1-NN matching)\np = {p_boot_2sided:.4f}', fontsize=11)
ax2.legend(loc='best', fontsize=9)
ax2.grid(alpha=0.3)

plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler21_att_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler21_att_comparison.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Resultaten opslaan")

summary = {
    'method': 'Pijler 21: Project-level SDID + 1-NN matching',
    'reference_p5': 'Replaces Pijler 5 (regional SDID)',
    'reference_p17': 'Complements Pijler 17 (sequential SDID)',
    'n_treated_EUgreen': int(len(eu_green)),
    'n_control_pool': int(len(non_eu_green)),
    'method_1A_ATT': float(result_A['ATT']) if result_A else np.nan,
    'method_1A_p_perm': float(p_perm) if 'p_perm' in dir() else np.nan,
    'method_1B_ATT': float(result_B['ATT']) if result_B else np.nan,
    'method_1B_p_perm': float(p_perm_B) if 'p_perm_B' in dir() else np.nan,
    'method_2_matching_ATT': float(ATT_matching),
    'method_2_matching_ci_lo': float(ci_lo),
    'method_2_matching_ci_hi': float(ci_hi),
    'method_2_matching_p_boot': float(p_boot_2sided),
    'matching_mean_distance': float(distances.mean()),
}
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / 'pijler21_summary.csv', index=False)


# === STAP 9: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 21 (Project-level SDID op S&P)")
print("=" * 78)

print(f"\nDrie methoden voor EU Green CBAM-effect (t* = {T_TREAT}):")
print(f"  1A. SDID (EU Green vs all): ATT = {result_A['ATT']:+.4f}, p_perm = {p_perm:.4f}")
if result_B:
    print(f"  1B. SDID (EU Green vs nonEU Green): ATT = {result_B['ATT']:+.4f}, p_perm = {p_perm_B:.4f}")
print(f"  2.  1-NN Matching: ATT = {ATT_matching:+.4f}, CI [{ci_lo:+.4f}, {ci_hi:+.4f}], p = {p_boot_2sided:.4f}")

print(f"\nVERGELIJKING MET EERDERE PIJLERS:")
print(f"  P5 (regional SDID t*=2023): tau = +0.148, p_perm = 0.167")
print(f"  P17 (sequential SDID t*=2023): tau = +0.001, p_perm = 1.000")
print(f"  P21 Method 2 (project matching): ATT = {ATT_matching:+.4f}, p = {p_boot_2sided:.4f}")

print(f"\n*** ROBUST CONCLUSIE OVER PROJECT-LEVEL SDID + REGIONAL SDID + MATCHING ***")
if abs(ATT_matching) < 0.02 and p_boot_2sided > 0.05:
    print("Geen significant CBAM effect op EU Green cancellations bij project-level.")
    print("Consistent met de informative-null over P5, P17.")
elif p_boot_2sided < 0.05:
    print(f"Project-level matching DETECTEERT effect: ATT = {ATT_matching:+.4f}, p = {p_boot_2sided:.4f}")
    print("Mogelijk heterogeen effect dat regionale aggregatie miste.")
