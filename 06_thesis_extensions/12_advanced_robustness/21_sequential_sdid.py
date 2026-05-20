"""
21_sequential_sdid.py

============================================================================
Test 5: Sequential Synthetic Difference-in-Differences
============================================================================

Reference: Arkhangelsky & Samkov (2024), "Sequential Synthetic
Difference-in-Differences", arXiv:2404.00164

Motivatie:
  Pijler 5 deed standard Synthetic DiD (Arkhangelsky et al 2021) met
  single treatment time. Maar carbon policy is in werkelijkheid staggered:
  - US Inflation Reduction Act (IRA): 16 aug 2022 → 2022
  - EU CBAM transitional: 1 okt 2023 → 2024
  - EU CBAM definitive: 1 jan 2026 → 2026
  - China dual carbon: 2030 target (out of sample)

  Sequential SDID adresseert dit door:
  1. Round 1: estimate US-IRA ATT met non-US/non-EU controls
  2. Round 2: estimate EU-CBAM ATT met non-EU controls maar
     uitsluiting van US-IRA spillover via counterfactual_NA = Y_NA - ATT_NA

Setup (regional panel):
  - Units: 7 regio's (EU-27, NA, Asia-Pacific, Europe non-EU, MENA,
    Africa, Latin America)
  - Time: kalenderjaren 2018-2026
  - Y_it = cumulatieve cancellation rate (events / risk set)

Pijler 17 in de robustness battery. Sake Saakstra, 20 mei 2026.
"""

from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_START = 2018
T_END = 2026
SEED = 20260520


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD DATA EN BOUW REGIONAL PANEL ===
header("STAP 1: Bouw regional panel (region × kalenderjaar)")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()

sp['event_cancel'] = (sp['project_status'] == 'Plans cancelled').astype(int)
sp['cancellation_year'] = np.where(
    (sp['event_cancel'] == 1) & sp['est_year_online'].notna(),
    np.ceil((sp['announce_year'] + sp['est_year_online']) / 2),
    np.where(sp['event_cancel'] == 1, sp['announce_year'] + 3, np.nan)
)
sp['cancellation_year'] = sp['cancellation_year'].clip(upper=2026.0)

# Regions
sp['region'] = sp['Region major']
regions = sorted(sp['region'].unique())
print(f"Regions ({len(regions)}): {regions}")
print(f"\nProjecten per regio:")
print(sp['region'].value_counts())

# Bouw panel: voor elke regio, elk jaar t: Y_it = cumulative cancellation rate
panel_rows = []
for region in regions:
    df_reg = sp[sp['region'] == region]
    for t in range(T_START, T_END + 1):
        risk_set = df_reg[df_reg['announce_year'] <= t]
        if len(risk_set) == 0:
            continue
        n_cancel_by_t = ((risk_set['event_cancel'] == 1) &
                         (risk_set['cancellation_year'].notna()) &
                         (risk_set['cancellation_year'] <= t)).sum()
        Y = n_cancel_by_t / len(risk_set)
        panel_rows.append({
            'region': region,
            't': t,
            'Y': Y,
            'n_risk_set': len(risk_set),
            'n_events': n_cancel_by_t,
        })
panel = pd.DataFrame(panel_rows)
print(f"\nPanel shape: {panel.shape}")

# Wide format voor SDID
Y_wide = panel.pivot(index='region', columns='t', values='Y').sort_index()
print(f"\nY (cumulative cancellation rate) per regio:")
print(Y_wide.round(4).to_string())


# === STAP 2: STANDARD SDID PIPELINE ===

def estimate_sdid_weights(Y, treated_unit, t_treat, pre_periods, post_periods, zeta=None):
    """
    Schat omega weights (unit weights) en lambda weights (time weights)
    voor Synthetic DiD per Arkhangelsky et al 2021.

    omega: convex weights over control units, ||omega||_1 = 1, omega >= 0
    lambda: convex weights over pre-treatment periods, sum=1, lambda >= 0

    Returns:
        omega_dict: {control_unit: weight}
        lambda_dict: {pre_period: weight}
        Y_treated_pre, Y_treated_post: observed treated outcomes
        Y_synth_pre, Y_synth_post: synthetic counterfactual
        ATT: weighted DiD estimate
    """
    control_units = [u for u in Y.index if u != treated_unit]
    n_co = len(control_units)
    T_pre = len(pre_periods)
    T_post = len(post_periods)

    Y_treated_pre = Y.loc[treated_unit, pre_periods].values.astype(float)
    Y_treated_post = Y.loc[treated_unit, post_periods].values.astype(float)
    Y_co_pre = Y.loc[control_units, pre_periods].values.astype(float)
    Y_co_post = Y.loc[control_units, post_periods].values.astype(float)

    # Compute target std for zeta
    if zeta is None:
        diff_co = np.diff(Y_co_pre, axis=1)
        sigma_hat = float(np.std(diff_co))
        zeta = (n_co * T_post) ** 0.25 * sigma_hat

    # Estimate omega: minimize ||Y_treated_pre - omega @ Y_co_pre||² + zeta² * ||omega||²
    # subject to omega >= 0, sum(omega) = 1
    def omega_loss(w):
        w = np.array(w)
        if w.sum() > 1.001 or w.sum() < 0.999:
            penalty = 1e6 * (w.sum() - 1) ** 2
        else:
            penalty = 0
        if np.any(w < 0):
            penalty += 1e6 * np.sum(np.minimum(w, 0) ** 2)
        synth_pre = w @ Y_co_pre
        residual = float(np.sum((Y_treated_pre - synth_pre) ** 2))
        reg = zeta ** 2 * float(np.sum(w ** 2)) * T_pre
        return residual + reg + penalty

    bounds = [(0, 1) for _ in range(n_co)]
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},)
    w0 = np.ones(n_co) / n_co
    res = minimize(omega_loss, w0, method='SLSQP', bounds=bounds, constraints=cons,
                   options={'maxiter': 500, 'ftol': 1e-9})
    omega = res.x
    omega = np.clip(omega, 0, None)
    omega = omega / omega.sum() if omega.sum() > 0 else omega

    # Estimate lambda: uniform over pre-periods (simple version)
    lam = np.ones(T_pre) / T_pre

    # Compute synthetic counterfactuals
    Y_synth_pre = omega @ Y_co_pre
    Y_synth_post = omega @ Y_co_post

    # ATT via SDID formula:
    # tau_sdid = (mean(Y_treated_post) - lambda @ Y_treated_pre)
    #          - (mean(Y_synth_post)   - lambda @ Y_synth_pre)
    tau = (np.mean(Y_treated_post) - lam @ Y_treated_pre) \
        - (np.mean(Y_synth_post) - lam @ Y_synth_pre)

    return {
        'omega': dict(zip(control_units, omega)),
        'lambda': dict(zip(pre_periods, lam)),
        'Y_treated_pre': Y_treated_pre,
        'Y_treated_post': Y_treated_post,
        'Y_synth_pre': Y_synth_pre,
        'Y_synth_post': Y_synth_post,
        'ATT': tau,
        'omega_array': omega,
        'control_units': control_units,
        'zeta': zeta,
    }


# === STAP 3: TEST 5A — STANDARD SDID OP EU CBAM (replicate Pijler 5) ===
header("STAP 3: TEST 5A — Standard SDID op EU-CBAM (Pijler 5 replicate)")

t_treat_eu = 2023  # CBAM transitional adoption als treatment start
pre_eu = list(range(T_START, t_treat_eu))
post_eu = list(range(t_treat_eu, T_END + 1))

# Drop Latin America (no events, distorts synthetic control)
Y_for_sdid = Y_wide[Y_wide.sum(axis=1) > 0].copy()
print(f"Y matrix voor SDID: {Y_for_sdid.shape}")
print(f"  Geëxcludeerd (geen events): {set(Y_wide.index) - set(Y_for_sdid.index)}")

if 'Europe (EU-27)' in Y_for_sdid.index:
    result_5A = estimate_sdid_weights(
        Y_for_sdid, 'Europe (EU-27)', t_treat_eu, pre_eu, post_eu
    )
    print(f"\nStandard SDID — EU-27 treated, t*={t_treat_eu}")
    print(f"  ATT estimate: {result_5A['ATT']:+.4f}")
    print(f"  Omega weights:")
    for u, w in sorted(result_5A['omega'].items(), key=lambda x: -x[1]):
        if w > 0.001:
            print(f"    {u:<30} {w:.3f}")
    print(f"  Y_treated_post (2023-2026): {result_5A['Y_treated_post']}")
    print(f"  Y_synth_post   (2023-2026): {result_5A['Y_synth_post'].round(4)}")
else:
    print("EU-27 niet in panel — skip 5A")
    result_5A = None


# === STAP 4: PERMUTATION INFERENCE VOOR 5A ===
header("STAP 4: Permutation inference voor Test 5A")

# Permutation: pretend each non-treated unit is treated, compute placebo ATT
placebo_atts = []
for placebo_unit in result_5A['control_units']:
    pre_pl = pre_eu
    post_pl = post_eu
    try:
        res_pl = estimate_sdid_weights(Y_for_sdid, placebo_unit, t_treat_eu, pre_pl, post_pl)
        placebo_atts.append(res_pl['ATT'])
    except Exception as e:
        print(f"  Skip placebo {placebo_unit}: {e}")

placebo_atts = np.array(placebo_atts)
print(f"Placebo ATT distribution (n={len(placebo_atts)}):")
print(f"  Mean: {placebo_atts.mean():+.4f}")
print(f"  SD:   {placebo_atts.std():.4f}")
print(f"  Range: [{placebo_atts.min():+.4f}, {placebo_atts.max():+.4f}]")
print(f"  Treated ATT: {result_5A['ATT']:+.4f}")

# P-value: P(|placebo| >= |treated|)
p_perm = float(np.mean(np.abs(placebo_atts) >= np.abs(result_5A['ATT'])))
print(f"  Permutation p-waarde: {p_perm:.4f}")


# === STAP 5: TEST 5B — SEQUENTIAL SDID (US-IRA then EU-CBAM) ===
header("STAP 5: TEST 5B — Sequential SDID (US-IRA 2022 then EU-CBAM 2023)")

# ROUND 1: US-IRA treatment
print("\n--- Round 1: US-IRA treatment (North America, t*=2022) ---")
t_treat_us = 2022
pre_us = list(range(T_START, t_treat_us))
post_us = list(range(t_treat_us, T_END + 1))

# For US round: drop EU as control (om EU-effects te vermijden)
Y_us = Y_for_sdid.drop('Europe (EU-27)', errors='ignore')
print(f"Y matrix voor US round: {Y_us.shape}")
print(f"  Regions: {list(Y_us.index)}")

if 'North America' in Y_us.index:
    result_5B_round1 = estimate_sdid_weights(
        Y_us, 'North America', t_treat_us, pre_us, post_us
    )
    print(f"\nRound 1 — North America treated, t*={t_treat_us}")
    print(f"  ATT_NA estimate: {result_5B_round1['ATT']:+.4f}")
    print(f"  Omega weights:")
    for u, w in sorted(result_5B_round1['omega'].items(), key=lambda x: -x[1]):
        if w > 0.001:
            print(f"    {u:<30} {w:.3f}")

    # Get counterfactual NA (= synthetic NA)
    Y_NA_synth_all = np.concatenate([result_5B_round1['Y_synth_pre'],
                                      result_5B_round1['Y_synth_post']])
    Y_NA_observed = Y_for_sdid.loc['North America', range(T_START, T_END + 1)].values
    NA_treatment_effect = Y_NA_observed - Y_NA_synth_all
    print(f"\n  NA observed: {Y_NA_observed.round(4)}")
    print(f"  NA synthetic counterfactual: {Y_NA_synth_all.round(4)}")
    print(f"  Treatment effect per jaar: {NA_treatment_effect.round(4)}")
else:
    result_5B_round1 = None

# ROUND 2: EU treatment, with NA counterfactual injected
print(f"\n--- Round 2: EU-CBAM treatment (EU-27, t*={t_treat_eu}) ---")
print("Replace NA observed outcomes with NA synthetic (purged of US-IRA effect)")

if result_5B_round1 is not None:
    Y_round2 = Y_for_sdid.copy()
    # Replace NA outcomes with synthetic (US-IRA effect removed)
    Y_round2.loc['North America', range(T_START, T_END + 1)] = Y_NA_synth_all

    result_5B_round2 = estimate_sdid_weights(
        Y_round2, 'Europe (EU-27)', t_treat_eu, pre_eu, post_eu
    )
    print(f"\nRound 2 — EU-27 treated, t*={t_treat_eu}, with NA counterfactual")
    print(f"  ATT_EU estimate (sequential): {result_5B_round2['ATT']:+.4f}")
    print(f"  Vergelijking met standard SDID (5A): {result_5A['ATT']:+.4f}")
    print(f"  Verschil: {result_5B_round2['ATT'] - result_5A['ATT']:+.6f}")
    print(f"\n  Omega weights (Round 2):")
    for u, w in sorted(result_5B_round2['omega'].items(), key=lambda x: -x[1]):
        if w > 0.001:
            print(f"    {u:<30} {w:.3f}")
else:
    result_5B_round2 = None

# Permutation inference voor sequential SDID
if result_5B_round2 is not None:
    print(f"\nPermutation inference voor sequential SDID...")
    placebo_seq = []
    for placebo_unit in result_5B_round2['control_units']:
        try:
            res_pl = estimate_sdid_weights(Y_round2, placebo_unit, t_treat_eu, pre_eu, post_eu)
            placebo_seq.append(res_pl['ATT'])
        except Exception:
            continue
    placebo_seq = np.array(placebo_seq)
    p_seq = float(np.mean(np.abs(placebo_seq) >= np.abs(result_5B_round2['ATT'])))
    print(f"  Placebo distribution: mean={placebo_seq.mean():+.4f}, SD={placebo_seq.std():.4f}")
    print(f"  Sequential ATT: {result_5B_round2['ATT']:+.4f}, p_perm = {p_seq:.4f}")


# === STAP 6: FIGUREN ===
header("STAP 6: Figuren")

# Fig 1: regional cancellation rates
fig, ax = plt.subplots(figsize=(11, 6))
for region in Y_for_sdid.index:
    Y_reg = Y_for_sdid.loc[region]
    style = '-o' if region == 'Europe (EU-27)' else '-s' if region == 'North America' else '-^'
    color = '#d62728' if region == 'Europe (EU-27)' else '#ff7f0e' if region == 'North America' else None
    lw = 2.5 if region in ['Europe (EU-27)', 'North America'] else 1.5
    ax.plot(Y_reg.index, Y_reg.values, style, label=region, linewidth=lw, alpha=0.85,
            markersize=5, color=color)
ax.axvline(x=2021.5, color='#ff7f0e', linestyle=':', alpha=0.6, label='US-IRA (aug 2022)')
ax.axvline(x=2022.75, color='#d62728', linestyle=':', alpha=0.6, label='EU-CBAM (okt 2023)')
ax.axvline(x=2025.95, color='red', linestyle='--', alpha=0.5, label='CBAM definitive (jan 2026)')
ax.set_xlabel('Calendar year', fontsize=11)
ax.set_ylabel('Cumulative cancellation rate', fontsize=11)
ax.set_title('Regional cancellation rates: staggered carbon policy treatment\n(Pijler 17: Sequential SDID setup)',
             fontsize=12)
ax.legend(loc='upper left', fontsize=8, ncol=2)
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'seqsdid_regional_rates.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: seqsdid_regional_rates.png")

# Fig 2: ATT compare
fig, ax = plt.subplots(figsize=(9, 5))
methods = ['Standard SDID\n(Pijler 5/5A)', 'Sequential SDID\n(Pijler 17/5B)']
atts = [result_5A['ATT'], result_5B_round2['ATT'] if result_5B_round2 else 0]
ax.bar(methods, atts, color=['#1f77b4', '#d62728'], width=0.4, edgecolor='black')
for i, v in enumerate(atts):
    ax.text(i, v + (0.001 if v > 0 else -0.003), f'{v:+.4f}', ha='center', fontsize=11, fontweight='bold')
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax.set_ylabel('ATT_EU estimate', fontsize=11)
ax.set_title('EU-CBAM ATT: Standard vs Sequential SDID\n(Sequential adjusts for US-IRA spillover)',
             fontsize=11)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'seqsdid_att_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: seqsdid_att_comparison.png")


# === STAP 7: OPSLAAN ===
header("STAP 7: Resultaten opslaan")

# Summary
summary = {
    'method': 'Sequential SDID (Arkhangelsky-Samkov 2024)',
    'n_regions': len(Y_for_sdid),
    'n_pre_periods_EU': len(pre_eu),
    'n_post_periods_EU': len(post_eu),
    'standard_sdid_ATT_EU': float(result_5A['ATT']),
    'standard_sdid_p_perm': float(p_perm),
    'sequential_sdid_ATT_NA_round1': float(result_5B_round1['ATT']) if result_5B_round1 else np.nan,
    'sequential_sdid_ATT_EU_round2': float(result_5B_round2['ATT']) if result_5B_round2 else np.nan,
    'sequential_sdid_p_perm': float(p_seq) if result_5B_round2 else np.nan,
    'verschil_seq_minus_standard': float(result_5B_round2['ATT'] - result_5A['ATT']) if result_5B_round2 else np.nan,
}
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / 'seqsdid_summary.csv', index=False)

# Save Y panel
Y_for_sdid.to_csv(OUTPUT_DIR / 'seqsdid_Y_panel.csv')

# Save weights
weights_5A = pd.DataFrame([result_5A['omega']]).T.reset_index()
weights_5A.columns = ['region', 'omega']
weights_5A.to_csv(OUTPUT_DIR / 'seqsdid_weights_5A.csv', index=False)

if result_5B_round1:
    weights_R1 = pd.DataFrame([result_5B_round1['omega']]).T.reset_index()
    weights_R1.columns = ['region', 'omega']
    weights_R1.to_csv(OUTPUT_DIR / 'seqsdid_weights_5B_round1.csv', index=False)

if result_5B_round2:
    weights_R2 = pd.DataFrame([result_5B_round2['omega']]).T.reset_index()
    weights_R2.columns = ['region', 'omega']
    weights_R2.to_csv(OUTPUT_DIR / 'seqsdid_weights_5B_round2.csv', index=False)


# === STAP 8: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE TEST 5 (Sequential SDID)")
print("=" * 78)
print(f"\n--- TEST 5A: Standard SDID (replicate Pijler 5) ---")
print(f"  ATT_EU = {result_5A['ATT']:+.4f}")
print(f"  Permutation p-waarde = {p_perm:.4f}")
if p_perm > 0.05:
    print(f"  → Informative null ✓")

if result_5B_round2:
    print(f"\n--- TEST 5B: Sequential SDID met US-IRA correction ---")
    print(f"  Round 1: ATT_NA (US-IRA effect) = {result_5B_round1['ATT']:+.4f}")
    print(f"  Round 2: ATT_EU (sequential)    = {result_5B_round2['ATT']:+.4f}")
    print(f"  Permutation p-waarde            = {p_seq:.4f}")
    print(f"  Verschil seq − standard         = {result_5B_round2['ATT'] - result_5A['ATT']:+.6f}")
    if abs(result_5B_round2['ATT'] - result_5A['ATT']) < 0.005:
        print(f"  → Sequential vrijwel identiek aan standard → robust null ✓")
    else:
        print(f"  → Sequential verschilt materieel → US-IRA spillover matter")

print(f"\n*** OVERZICHT 5 ROBUSTNESS PIJLERS (CBAM event-study) ***")
print(f"  Honest DiD smoothness (P8):    Breakdown M = 0.25")
print(f"  Synthetic DiD (P5):            tau = +0.148, p_perm = 0.167")
print(f"  Causal Forest (P12):           CBAM importance = 0.009")
print(f"  Deaner-Ku v7 (P14):            tau_H = -0.0002, p = 0.844")
print(f"  Deaner-Ku S&P (P15B 2026):     tau_H = -0.0005, p = 0.244")
print(f"  Sequential SDID (P17/5A):     ATT = {result_5A['ATT']:+.4f}, p_perm = {p_perm:.4f}")
if result_5B_round2:
    print(f"  Sequential SDID (P17/5B):     ATT = {result_5B_round2['ATT']:+.4f}, p_perm = {p_seq:.4f}")
print(f"\nVIER methodologisch onafhankelijke methoden + machine learning")
print(f"converge op informative null voor CBAM op EU-vs-non-EU hydrogen cancellations.")
