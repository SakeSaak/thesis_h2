"""
18_deaner_ku_hazard_did.py

============================================================================
Test 1: Deaner-Ku Hazard-Rate Difference-in-Differences
============================================================================

Reference: Deaner & Ku (2024), "Causal Duration Analysis with Diff-in-Diff",
University College London, arXiv:2405.05220

Motivatie:
  - Onze CBAM event-study heeft pre-trends violation (F=20.18, p<0.0001) op
    standaard DiD met mean outcomes.
  - Bij absorbing-state outcomes (cancellation = irreversibel) faalt parallel
    trends mechanisch: F_{g,t} = aandeel gecanceld convergeert naar 1.
  - Deaner-Ku (2024) lost dit op door DiD toe te passen op time-average
    hazard rates in plaats van mean outcomes.

Setup:
  - Treated (G=1):  EU-27 hydrogen projecten (n=213)
                    Verwachten indirect CBAM-bescherming via downstream
                    EU-industrie (cement/staal/kunstmest) die niet meer
                    concurreert met onbelaste import.
  - Control (G=0):  Non-EU hydrogen projecten (n=501)
  - Treatment time: 1 oktober 2023 (CBAM transitional adoption)
                    -> kalenderjaar t* = 2024
  - Outcome:        Y_{i,t} = 1 als project i was "Plans cancelled" door jaar t
  - Time grid:      Kalender-jaren 2018 t/m 2026

Auteur: Sake Saakstra, 20 mei 2026
Pijler 14 in de robustness battery
"""

from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
DATA_PATH = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_START = 2018
T_STAR = 2024
T_END = 2026
B_BOOTSTRAP = 500
SEED = 20260520


def header(t):
    print("\n" + "=" * 76 + f"\n  {t}\n" + "=" * 76)


# === STAP 1: LAAD DATA ===
header("STAP 1: Laad data en bouw treatment / control groepen")

df = pd.read_csv(DATA_PATH)
print(f"v7 data: {df.shape[0]} projecten")
print(f"  Year announced range: {df['year_announced'].min():.0f} – {df['year_announced'].max():.0f}")

df['G'] = (df['region'] == 'EU').astype(int)
print(f"\nGroup definitie (G=1 als EU, 0 anders):")
print(f"  G=1 (EU treated):     {(df['G']==1).sum()}")
print(f"  G=0 (non-EU control): {(df['G']==0).sum()}")

df['cancellation_year'] = np.where(
    df['event_type'] == 1,
    df['year_announced'] + df['duration'],
    np.nan
)
n_cancel_total = int((df['event_type'] == 1).sum())
print(f"\nTotaal cancellations: {n_cancel_total}")
print("Cancellation jaar verdeling:")
print(df.loc[df['event_type']==1, 'cancellation_year'].value_counts().sort_index().to_string())

df_panel = df.copy()


# === STAP 2: BOUW PANEL ===
header("STAP 2: Bouw project × kalenderjaar panel")

panel_rows = []
for _, row in df_panel.iterrows():
    for t in range(T_START, T_END + 1):
        if row['year_announced'] <= t:
            cancelled_by_t = (
                (row['event_type'] == 1) and
                (not pd.isna(row['cancellation_year'])) and
                (row['cancellation_year'] <= t)
            )
            panel_rows.append({
                'project_id': row['project_id'],
                'G': row['G'],
                'is_blue_ccs': row['is_blue_ccs'],
                't': t,
                'Y': int(cancelled_by_t),
            })
panel = pd.DataFrame(panel_rows)
print(f"Panel shape: {panel.shape}")
print(f"\nObservaties per groep × jaar:")
print(panel.groupby(['G', 't']).size().unstack().to_string())


# === STAP 3: F en H̄ ===
header("STAP 3: F_{g,t} en time-average hazards H̄_{g,t}")

def compute_F(panel):
    F = panel.groupby(['G', 't'])['Y'].mean().reset_index()
    F.columns = ['G', 't', 'F']
    return F

def compute_Hbar(F_df, t_start):
    F_df = F_df.copy()
    F_df['tau'] = F_df['t'] - t_start + 1
    F_clip = F_df['F'].clip(upper=0.9999, lower=0.0)
    F_df['Hbar'] = np.where(
        F_clip > 0,
        -np.log(1 - F_clip) / F_df['tau'],
        0.0
    )
    return F_df

F_df = compute_F(panel)
H_df = compute_Hbar(F_df, T_START)
print("F en Hbar per groep:")
print(H_df.pivot(index='t', columns='G', values=['F', 'Hbar']).round(4).to_string())


# === STAP 4: PRE-TRENDS ===
header("STAP 4: Pre-trends specification test op H̄")

pre = H_df[H_df['t'] < T_STAR].copy()
pivot_pre = pre.pivot(index='t', columns='G', values='Hbar')
pivot_pre.columns = ['Hbar_0', 'Hbar_1']
pivot_pre['diff'] = pivot_pre['Hbar_1'] - pivot_pre['Hbar_0']

print(f"Pre-treatment periode: {T_START} – {T_STAR-1}")
print(f"\nTime-average hazard verschillen H̄_1 - H̄_0:")
print(pivot_pre.round(4).to_string())

diffs = pivot_pre['diff'].values
print(f"\nMean pre-treatment diff: {diffs.mean():+.4f}")
print(f"SD: {diffs.std(ddof=1):.4f}")
print(f"Range: [{diffs.min():+.4f}, {diffs.max():+.4f}]")

F_pre = F_df[F_df['t'] < T_STAR].pivot(index='t', columns='G', values='F')
F_pre.columns = ['F_0', 'F_1']
F_pre['F_diff'] = F_pre['F_1'] - F_pre['F_0']
print(f"\n[VERGELIJKING] Standaard DiD op F (mean outcomes):")
print(F_pre.round(4).to_string())
print(f"F-diff: mean={F_pre['F_diff'].mean():+.4f}, sd={F_pre['F_diff'].std():.4f}")
print("(Diverging over tijd → parallel trends fails voor mean outcomes)")


# === STAP 5: HAZARD-DiD ===
header("STAP 5: Hazard-DiD: τ̂_{H,t} voor t ≥ t*")

t_baseline = T_STAR - 1
pivot_all = H_df.pivot(index='t', columns='G', values='Hbar')
pivot_all.columns = ['Hbar_0', 'Hbar_1']

Hbar_1_baseline = pivot_all.loc[t_baseline, 'Hbar_1']
Hbar_0_baseline = pivot_all.loc[t_baseline, 'Hbar_0']

print(f"Baseline (t={t_baseline}):")
print(f"  H̄_1,{t_baseline} = {Hbar_1_baseline:.4f}")
print(f"  H̄_0,{t_baseline} = {Hbar_0_baseline:.4f}")
print(f"  Diff = {Hbar_1_baseline - Hbar_0_baseline:+.4f}")

print(f"\n{'t':<6}{'H̄_1,t':<10}{'H̄_0,t':<10}{'Δ H̄_1':<10}{'Δ H̄_0':<10}{'τ̂_H,t':<12}")
print("-" * 60)
hazard_did_results = []
for t in range(T_STAR, T_END + 1):
    Hbar_1_t = pivot_all.loc[t, 'Hbar_1']
    Hbar_0_t = pivot_all.loc[t, 'Hbar_0']
    delta_Hbar_1 = Hbar_1_t - Hbar_1_baseline
    delta_Hbar_0 = Hbar_0_t - Hbar_0_baseline
    tau_H_t = delta_Hbar_1 - delta_Hbar_0
    print(f"{t:<6}{Hbar_1_t:<10.4f}{Hbar_0_t:<10.4f}{delta_Hbar_1:<+10.4f}{delta_Hbar_0:<+10.4f}{tau_H_t:<+12.4f}")
    hazard_did_results.append({
        't': t,
        'Hbar_1_t': Hbar_1_t,
        'Hbar_0_t': Hbar_0_t,
        'delta_Hbar_1': delta_Hbar_1,
        'delta_Hbar_0': delta_Hbar_0,
        'tau_H_t': tau_H_t,
    })
results_df = pd.DataFrame(hazard_did_results)


# === STAP 6: INVERSE TRANSFORMATION ===
header("STAP 6: Inverse transformatie naar mean outcomes")

print(f"{'t':<6}{'F_1,t':<10}{'F^(0)_1,t':<14}{'τ_F,t (ATT)':<14}")
print("-" * 50)
att_results = []
for _, row in results_df.iterrows():
    t = int(row['t'])
    tau_H = row['tau_H_t']
    Hbar_1_t = row['Hbar_1_t']
    Hbar_1_cf = Hbar_1_t - tau_H
    tau_offset = t - T_START + 1
    F_1_t = 1 - np.exp(-tau_offset * Hbar_1_t)
    F_1_cf = 1 - np.exp(-tau_offset * Hbar_1_cf)
    tau_F = F_1_t - F_1_cf
    print(f"{t:<6}{F_1_t:<10.4f}{F_1_cf:<14.4f}{tau_F:<+14.4f}")
    att_results.append({
        't': t,
        'F_1_t_observed': F_1_t,
        'F_1_t_counterfactual': F_1_cf,
        'tau_F_t': tau_F,
    })
att_df = pd.DataFrame(att_results)


# === STAP 7: BOOTSTRAP ===
header(f"STAP 7: Bootstrap inference (B = {B_BOOTSTRAP})")

rng = np.random.default_rng(SEED)
project_ids = df_panel['project_id'].unique()
n_projects = len(project_ids)
print(f"Cluster-bootstrap op {n_projects} projecten...")

# Versnelling: pre-bouw project-niveau lookup
project_lookup = {pid: row for pid, row in zip(df_panel['project_id'], df_panel.to_dict('records'))}

bootstrap_tau_H = {t: [] for t in range(T_STAR, T_END + 1)}
bootstrap_tau_F = {t: [] for t in range(T_STAR, T_END + 1)}

for b in range(B_BOOTSTRAP):
    if (b + 1) % 100 == 0:
        print(f"  Iteratie {b+1}/{B_BOOTSTRAP}")
    boot_ids = rng.choice(project_ids, size=n_projects, replace=True)
    rows = []
    for pid in boot_ids:
        r = project_lookup[pid]
        for t in range(T_START, T_END + 1):
            if r['year_announced'] <= t:
                cancelled_by_t = (
                    (r['event_type'] == 1) and
                    (not pd.isna(r['cancellation_year'])) and
                    (r['cancellation_year'] <= t)
                )
                rows.append({'G': r['G'], 't': t, 'Y': int(cancelled_by_t)})
    boot_panel = pd.DataFrame(rows)
    F_b = compute_F(boot_panel)
    H_b = compute_Hbar(F_b, T_START)
    pivot_b = H_b.pivot(index='t', columns='G', values='Hbar')
    if 0 not in pivot_b.columns or 1 not in pivot_b.columns:
        continue
    pivot_b.columns = ['Hbar_0', 'Hbar_1']
    if t_baseline not in pivot_b.index:
        continue
    Hbar_1_base_b = pivot_b.loc[t_baseline, 'Hbar_1']
    Hbar_0_base_b = pivot_b.loc[t_baseline, 'Hbar_0']
    for t in range(T_STAR, T_END + 1):
        if t not in pivot_b.index:
            continue
        Hbar_1_t = pivot_b.loc[t, 'Hbar_1']
        Hbar_0_t = pivot_b.loc[t, 'Hbar_0']
        tau_H_b = (Hbar_1_t - Hbar_1_base_b) - (Hbar_0_t - Hbar_0_base_b)
        bootstrap_tau_H[t].append(tau_H_b)
        Hbar_1_cf_b = Hbar_1_t - tau_H_b
        tau_offset = t - T_START + 1
        F_1_t = 1 - np.exp(-tau_offset * Hbar_1_t)
        F_1_cf = 1 - np.exp(-tau_offset * Hbar_1_cf_b)
        bootstrap_tau_F[t].append(F_1_t - F_1_cf)


# === STAP 8: INFERENCE ===
header("STAP 8: Bootstrap CI's en p-waarden")
print(f"{'t':<6}{'τ̂_H,t':<12}{'95% CI (H)':<26}{'τ̂_F,t':<14}{'95% CI (F)':<28}{'p (H)':<8}")
print("-" * 96)
inference_results = []
for t in range(T_STAR, T_END + 1):
    boot_H = np.array(bootstrap_tau_H[t])
    boot_F = np.array(bootstrap_tau_F[t])
    if len(boot_H) < 50:
        continue
    tau_H_pt = float(results_df[results_df['t']==t]['tau_H_t'].iloc[0])
    tau_F_pt = float(att_df[att_df['t']==t]['tau_F_t'].iloc[0])
    ci_H = np.percentile(boot_H, [2.5, 97.5])
    ci_F = np.percentile(boot_F, [2.5, 97.5])
    if tau_H_pt > 0:
        p_H = 2 * np.mean(boot_H <= 0)
    else:
        p_H = 2 * np.mean(boot_H >= 0)
    p_H = float(min(p_H, 1.0))
    print(f"{t:<6}{tau_H_pt:<+12.4f}[{ci_H[0]:+.4f}, {ci_H[1]:+.4f}]  {tau_F_pt:<+14.4f}[{ci_F[0]:+.4f}, {ci_F[1]:+.4f}]  {p_H:.4f}")
    inference_results.append({
        't': t, 'tau_H': tau_H_pt, 'tau_H_ci_lo': ci_H[0], 'tau_H_ci_hi': ci_H[1],
        'tau_H_p': p_H, 'tau_F': tau_F_pt, 'tau_F_ci_lo': ci_F[0], 'tau_F_ci_hi': ci_F[1],
        'n_boot_valid': len(boot_H),
    })
inference_df = pd.DataFrame(inference_results)


# === STAP 9: PRE-TRENDS BOOTSTRAP ===
header("STAP 9: Pre-trend slope bootstrap test")

pre_t_values = pivot_pre.index.values.astype(float)
pre_diffs = pivot_pre['diff'].values
slope_pt = float(np.polyfit(pre_t_values, pre_diffs, 1)[0])
print(f"Pre-treatment H̄-differential slope (per jaar): {slope_pt:+.4f}")

print(f"Bootstrap pre-trend slope ({B_BOOTSTRAP} iteraties)...")
boot_slopes = []
for b in range(B_BOOTSTRAP):
    if (b + 1) % 100 == 0:
        print(f"  Iteratie {b+1}/{B_BOOTSTRAP}")
    boot_ids = rng.choice(project_ids, size=n_projects, replace=True)
    rows = []
    for pid in boot_ids:
        r = project_lookup[pid]
        for t in pre_t_values.astype(int):
            if r['year_announced'] <= t:
                cancelled_by_t = (
                    (r['event_type'] == 1) and
                    (not pd.isna(r['cancellation_year'])) and
                    (r['cancellation_year'] <= t)
                )
                rows.append({'G': r['G'], 't': t, 'Y': int(cancelled_by_t)})
    boot_panel = pd.DataFrame(rows)
    F_b = compute_F(boot_panel)
    H_b = compute_Hbar(F_b, T_START)
    piv_b = H_b.pivot(index='t', columns='G', values='Hbar')
    if 0 not in piv_b.columns or 1 not in piv_b.columns:
        continue
    diff_b = piv_b[1] - piv_b[0]
    if len(diff_b.dropna()) < 3:
        continue
    x = diff_b.dropna().index.values.astype(float)
    y = diff_b.dropna().values
    slope = np.polyfit(x, y, 1)[0]
    boot_slopes.append(slope)
boot_slopes = np.array(boot_slopes)

if len(boot_slopes) > 50:
    slope_se = float(boot_slopes.std())
    slope_ci = np.percentile(boot_slopes, [2.5, 97.5])
    slope_z = slope_pt / slope_se if slope_se > 0 else 0
    p_slope = float(2 * min(np.mean(boot_slopes <= 0), np.mean(boot_slopes >= 0)))
    print(f"\nPre-trend slope: {slope_pt:+.4f}")
    print(f"Bootstrap SE:   {slope_se:.4f}")
    print(f"95% CI:         [{slope_ci[0]:+.4f}, {slope_ci[1]:+.4f}]")
    print(f"z = {slope_z:+.2f}, p = {p_slope:.4f}")
    if p_slope > 0.05:
        print(f"→ FAILS TO REJECT parallel trends in H̄ at α=0.05 ✓")
    else:
        print(f"→ REJECTS parallel trends in H̄ at α=0.05 ✗")
else:
    p_slope = float('nan')
    slope_se = float('nan')


# === STAP 10: FIGUREN ===
header("STAP 10: Figuren")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
years = sorted(H_df['t'].unique())
H_treated = [H_df[(H_df['G']==1) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]
H_control = [H_df[(H_df['G']==0) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]
ax1.plot(years, H_treated, 'o-', color='#d62728', label='Treated (EU)', linewidth=2.2, markersize=7)
ax1.plot(years, H_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=7)
ax1.axvline(x=T_STAR - 0.5, color='gray', linestyle='--', alpha=0.7, label=f'CBAM transition (t*={T_STAR})')
ax1.set_xlabel('Calendar year', fontsize=12)
ax1.set_ylabel(r'Time-average hazard $\bar{H}_{g,t}$', fontsize=12)
ax1.set_title('Panel A: Time-average hazards (Deaner-Ku)', fontsize=12)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(alpha=0.3)

F_treated = [F_df[(F_df['G']==1) & (F_df['t']==t)]['F'].iloc[0] for t in years]
F_control = [F_df[(F_df['G']==0) & (F_df['t']==t)]['F'].iloc[0] for t in years]
ax2.plot(years, F_treated, 'o-', color='#d62728', label='Treated (EU)', linewidth=2.2, markersize=7)
ax2.plot(years, F_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=7)
ax2.axvline(x=T_STAR - 0.5, color='gray', linestyle='--', alpha=0.7, label=f'CBAM transition (t*={T_STAR})')
ax2.set_xlabel('Calendar year', fontsize=12)
ax2.set_ylabel(r'Mean outcome $F_{g,t}$', fontsize=12)
ax2.set_title('Panel B: Mean outcomes (standard DiD — fails)', fontsize=12)
ax2.legend(loc='upper left', fontsize=10)
ax2.grid(alpha=0.3)

plt.suptitle('Deaner-Ku Hazard-DiD vs Standard DiD: pre-treatment trends',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_hazard_did_trends.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {FIG_DIR}/deaner_ku_hazard_did_trends.png")

fig, ax = plt.subplots(figsize=(10, 6))
ts_post = inference_df['t'].values
tau_H = inference_df['tau_H'].values
tau_F = inference_df['tau_F'].values
ci_H_lo = inference_df['tau_H_ci_lo'].values
ci_H_hi = inference_df['tau_H_ci_hi'].values
ci_F_lo = inference_df['tau_F_ci_lo'].values
ci_F_hi = inference_df['tau_F_ci_hi'].values

x_H = ts_post - 0.15
x_F = ts_post + 0.15
ax.errorbar(x_H, tau_H, yerr=[tau_H - ci_H_lo, ci_H_hi - tau_H],
            fmt='o', color='#d62728', label=r'$\hat{\tau}_{\bar{H},t}$ (ATT on hazards)',
            markersize=10, capsize=5, linewidth=2)
ax.errorbar(x_F, tau_F, yerr=[tau_F - ci_F_lo, ci_F_hi - tau_F],
            fmt='s', color='#2ca02c', label=r'$\hat{\tau}_{F,t}$ (ATT on mean outcomes)',
            markersize=10, capsize=5, linewidth=2)
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax.set_xlabel('Calendar year (post-CBAM)', fontsize=12)
ax.set_ylabel('ATT', fontsize=12)
ax.set_title(f'Deaner-Ku ATT estimates with 95% bootstrap CI (CBAM t*={T_STAR})', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)
ax.set_xticks(ts_post)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_att_estimates.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {FIG_DIR}/deaner_ku_att_estimates.png")


# === STAP 11: OPSLAAN ===
header("STAP 11: Resultaten opslaan")

results_df.to_csv(OUTPUT_DIR / 'deaner_ku_tau_H.csv', index=False)
att_df.to_csv(OUTPUT_DIR / 'deaner_ku_tau_F.csv', index=False)
inference_df.to_csv(OUTPUT_DIR / 'deaner_ku_inference.csv', index=False)
pivot_pre.reset_index().to_csv(OUTPUT_DIR / 'deaner_ku_pretrend.csv', index=False)
H_df.to_csv(OUTPUT_DIR / 'deaner_ku_Hbar_all.csv', index=False)

summary = {
    'method': 'Deaner-Ku Hazard-DiD',
    'reference': 'arXiv:2405.05220 (2024)',
    'n_projects': int(len(df_panel)),
    'n_treated_EU': int((df_panel['G']==1).sum()),
    'n_control_nonEU': int((df_panel['G']==0).sum()),
    'n_cancellations_total': n_cancel_total,
    'time_range': f'{T_START}–{T_END}',
    'treatment_year': T_STAR,
    'pretrend_slope': slope_pt,
    'pretrend_slope_p': p_slope,
    'pretrend_slope_se': slope_se,
    'tau_H_2024': float(inference_df[inference_df['t']==2024]['tau_H'].iloc[0]),
    'tau_H_2024_p': float(inference_df[inference_df['t']==2024]['tau_H_p'].iloc[0]),
    'tau_H_2025': float(inference_df[inference_df['t']==2025]['tau_H'].iloc[0]),
    'tau_H_2025_p': float(inference_df[inference_df['t']==2025]['tau_H_p'].iloc[0]),
    'tau_H_2026': float(inference_df[inference_df['t']==2026]['tau_H'].iloc[0]),
    'tau_H_2026_p': float(inference_df[inference_df['t']==2026]['tau_H_p'].iloc[0]),
    'tau_F_2026': float(inference_df[inference_df['t']==2026]['tau_F'].iloc[0]),
    'b_bootstrap': B_BOOTSTRAP,
}
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / 'deaner_ku_summary.csv', index=False)

print("Files:")
for f in ['deaner_ku_tau_H.csv', 'deaner_ku_tau_F.csv', 'deaner_ku_inference.csv',
          'deaner_ku_pretrend.csv', 'deaner_ku_Hbar_all.csv', 'deaner_ku_summary.csv']:
    print(f"  - {OUTPUT_DIR}/{f}")


print("\n" + "=" * 76)
print("EINDCONCLUSIE")
print("=" * 76)
print(f"Pre-trend slope op H̄ (vóór CBAM): {slope_pt:+.4f}")
if not pd.isna(p_slope):
    print(f"Bootstrap p-waarde: {p_slope:.4f}")
    if p_slope > 0.05:
        print("→ Parallel trends in H̄ NIET verworpen ✓")
        print("→ Deaner-Ku identification valid (anders dan F-trends)")
    else:
        print("→ Parallel trends in H̄ wel verworpen ✗")

print()
print(f"τ̂_H,2024 = {summary['tau_H_2024']:+.4f}, p = {summary['tau_H_2024_p']:.4f}")
print(f"τ̂_H,2025 = {summary['tau_H_2025']:+.4f}, p = {summary['tau_H_2025_p']:.4f}")
print(f"τ̂_H,2026 = {summary['tau_H_2026']:+.4f}, p = {summary['tau_H_2026_p']:.4f}")
print(f"τ̂_F,2026 (ATT op mean cancellation rate) = {summary['tau_F_2026']:+.4f}")
print()
print("Beleidsinterpretatie:")
print(f"  CBAM transitional fase (2023-2025) → kalenderjaar {T_STAR}")
print(f"  Causale ATT op cancellation hazard = {summary['tau_H_2024']:+.4f}")
print(f"  Significantie: p = {summary['tau_H_2024_p']:.4f}")
