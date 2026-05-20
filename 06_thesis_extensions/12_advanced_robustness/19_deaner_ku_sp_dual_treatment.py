"""
19_deaner_ku_sp_dual_treatment.py

============================================================================
Test 2: Deaner-Ku Hazard-DiD op S&P data met TWEE treatment times
============================================================================

Replicatie van Pijler 14 op S&P Global Commodity Insights data met N=103
cancellations (3.3x meer power dan v7's 31). PLUS: split-treatment tests:

  TEST 2A (Anticipation):  t* = 2024 (CBAM transitional adoption oktober 2023)
                            Vraag: hebben producers ANTICIPATIE-gedrag getoond?
  TEST 2B (Actual effect): t* = 2026 (CBAM full financial effect jan 2026)
                            Vraag: heeft CBAM eenmaal in werking een effect?
                            CAVEAT: maar ~5 maanden post-treatment data
                            (snapshot maart 2026)

Cancellation timing schatting voor S&P:
  midpoint_year = (announce_year + estimated_online_year) / 2 als est_online beschikbaar
                = announce_year + 3 (fallback voor ontbrekende est_online)

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

T_START = 2018
T_END = 2026
B_BOOTSTRAP = 500
SEED = 20260520

def header(t):
    print("\n" + "=" * 76 + f"\n  {t}\n" + "=" * 76)


# === LAAD EN PREPARE S&P DATA ===
header("STAP 1: S&P data laden en cancellation-timing inschatten")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
print(f"Raw shape: {sp.shape}")

sp = sp[sp['Year announced'].notna()].copy()
sp['announce_year'] = pd.to_datetime(sp['Date announced']).dt.year.fillna(sp['Year announced']).astype(int)
sp['est_online_year'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp['is_cancelled'] = (sp['project_status'] == 'Plans cancelled').astype(int)
sp['is_EU27'] = (sp['Region major'] == 'Europe (EU-27)').astype(int)

# Schat cancellation-jaar voor cancelled projecten
sp['cancellation_year'] = np.where(
    sp['is_cancelled'] == 1,
    np.where(
        sp['est_online_year'].notna(),
        sp['announce_year'] + (sp['est_online_year'] - sp['announce_year']) / 2,
        sp['announce_year'] + 3.0  # fallback: 3 jaar typische cancellation lag
    ),
    np.nan
)
sp.loc[sp['cancellation_year'].notna(), 'cancellation_year'] = sp.loc[sp['cancellation_year'].notna(), 'cancellation_year'].round().astype(int)

# Cap cancellation_year op snapshot date (maart 2024)
# Maar onze snapshot loopt tot 2026; we tellen cancellations tot t=2026
sp['cancellation_year'] = sp['cancellation_year'].clip(upper=T_END)

print(f"\nSchattigingen voor S&P data:")
print(f"  Totaal projecten: {len(sp)}")
print(f"  EU-27 (treated):  {(sp['is_EU27']==1).sum()}")
print(f"  Non-EU (control): {(sp['is_EU27']==0).sum()}")
print(f"  Cancellations totaal:  {sp['is_cancelled'].sum()}")
print(f"  Cancellations EU-27:   {((sp['is_EU27']==1) & (sp['is_cancelled']==1)).sum()}")
print(f"  Cancellations non-EU:  {((sp['is_EU27']==0) & (sp['is_cancelled']==1)).sum()}")
print()
print("Geschatte cancellation-jaar verdeling (na cap op T_END=2026):")
print(sp.loc[sp['is_cancelled']==1, 'cancellation_year'].value_counts().sort_index().to_string())

# Voor de Deaner-Ku panel maak we project_id
sp['project_id'] = np.arange(len(sp))


# === BOUW PANEL ===
header("STAP 2: Bouw project x kalenderjaar panel")

panel_rows = []
for _, row in sp.iterrows():
    for t in range(T_START, T_END + 1):
        if row['announce_year'] <= t:
            cancelled_by_t = (
                (row['is_cancelled'] == 1) and
                (not pd.isna(row['cancellation_year'])) and
                (row['cancellation_year'] <= t)
            )
            panel_rows.append({
                'project_id': row['project_id'],
                'G': row['is_EU27'],
                't': t,
                'Y': int(cancelled_by_t),
            })
panel = pd.DataFrame(panel_rows)
print(f"Panel shape: {panel.shape}")
print(f"\nObservaties per groep × jaar:")
print(panel.groupby(['G', 't']).size().unstack().to_string())


# === FUNCTIES voor Deaner-Ku berekening ===
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

# Eenmaal berekenen (point estimate)
F_df = compute_F(panel)
H_df = compute_Hbar(F_df, T_START)
print("\nF en H̄ per groep:")
print(H_df.pivot(index='t', columns='G', values=['F', 'Hbar']).round(4).to_string())


# === FUNCTIE voor één treatment test ===
def run_deaner_ku_test(treatment_year, panel, project_lookup, project_ids,
                       label, B=B_BOOTSTRAP):
    """Voer volledige Deaner-Ku analyse uit voor een specifieke treatment time."""
    print(f"\n{'='*76}")
    print(f"  TEST {label}: t* = {treatment_year}")
    print(f"{'='*76}")

    t_baseline = treatment_year - 1

    # Point estimates
    pivot_all = H_df.pivot(index='t', columns='G', values='Hbar')
    pivot_all.columns = ['Hbar_0', 'Hbar_1']
    Hbar_1_baseline = pivot_all.loc[t_baseline, 'Hbar_1']
    Hbar_0_baseline = pivot_all.loc[t_baseline, 'Hbar_0']

    print(f"\nBaseline (t={t_baseline}):")
    print(f"  H̄_1,{t_baseline} = {Hbar_1_baseline:.4f}")
    print(f"  H̄_0,{t_baseline} = {Hbar_0_baseline:.4f}")

    # Pre-treatment hazard differentials
    pre = H_df[H_df['t'] < treatment_year].copy()
    pivot_pre = pre.pivot(index='t', columns='G', values='Hbar')
    pivot_pre.columns = ['Hbar_0', 'Hbar_1']
    pivot_pre['diff'] = pivot_pre['Hbar_1'] - pivot_pre['Hbar_0']
    pre_t_values = pivot_pre.index.values.astype(float)
    pre_diffs = pivot_pre['diff'].values

    print(f"\nPre-treatment H̄-differentials:")
    print(pivot_pre.round(4).to_string())

    if len(pre_t_values) >= 3:
        slope_pt = float(np.polyfit(pre_t_values, pre_diffs, 1)[0])
        print(f"\nPre-trend slope (lineair): {slope_pt:+.4f} per jaar")
    else:
        slope_pt = float('nan')
        print(f"\nTe weinig pre-treatment perioden voor pre-trend slope test.")

    # ATT per post-treatment jaar
    hazard_did = []
    for t in range(treatment_year, T_END + 1):
        if t not in pivot_all.index:
            continue
        Hbar_1_t = pivot_all.loc[t, 'Hbar_1']
        Hbar_0_t = pivot_all.loc[t, 'Hbar_0']
        delta_Hbar_1 = Hbar_1_t - Hbar_1_baseline
        delta_Hbar_0 = Hbar_0_t - Hbar_0_baseline
        tau_H_t = delta_Hbar_1 - delta_Hbar_0
        # ATT op F via inverse transformatie
        Hbar_1_cf = Hbar_1_t - tau_H_t
        tau_offset = t - T_START + 1
        F_1_t = 1 - np.exp(-tau_offset * Hbar_1_t)
        F_1_cf = 1 - np.exp(-tau_offset * Hbar_1_cf)
        tau_F = F_1_t - F_1_cf
        hazard_did.append({
            't': t, 'Hbar_1_t': Hbar_1_t, 'Hbar_0_t': Hbar_0_t,
            'delta_Hbar_1': delta_Hbar_1, 'delta_Hbar_0': delta_Hbar_0,
            'tau_H_t': tau_H_t, 'F_1_t': F_1_t, 'F_1_cf': F_1_cf,
            'tau_F_t': tau_F,
        })
    results_df = pd.DataFrame(hazard_did)
    print(f"\nATT estimates (point estimates):")
    print(f"{'t':<6}{'H̄_1,t':<10}{'H̄_0,t':<10}{'τ̂_H,t':<12}{'F_1,t':<10}{'F^(0)_1,t':<12}{'τ̂_F,t':<12}")
    print("-" * 76)
    for _, r in results_df.iterrows():
        print(f"{int(r['t']):<6}{r['Hbar_1_t']:<10.4f}{r['Hbar_0_t']:<10.4f}{r['tau_H_t']:<+12.4f}"
              f"{r['F_1_t']:<10.4f}{r['F_1_cf']:<12.4f}{r['tau_F_t']:<+12.4f}")

    # === BOOTSTRAP ===
    print(f"\nBootstrap inference (B={B})...")
    rng = np.random.default_rng(SEED)
    n_projects = len(project_ids)
    bootstrap_tau_H = {t: [] for t in range(treatment_year, T_END + 1)}
    bootstrap_tau_F = {t: [] for t in range(treatment_year, T_END + 1)}
    bootstrap_slopes = []

    for b in range(B):
        if (b + 1) % 100 == 0:
            print(f"  Iteratie {b+1}/{B}")
        boot_ids = rng.choice(project_ids, size=n_projects, replace=True)
        rows = []
        for pid in boot_ids:
            r = project_lookup[pid]
            for t in range(T_START, T_END + 1):
                if r['announce_year'] <= t:
                    cancelled_by_t = (
                        (r['is_cancelled'] == 1) and
                        (not pd.isna(r['cancellation_year'])) and
                        (r['cancellation_year'] <= t)
                    )
                    rows.append({'G': r['is_EU27'], 't': t, 'Y': int(cancelled_by_t)})
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
        # ATT estimates
        for t in range(treatment_year, T_END + 1):
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
        # Pre-trend slope
        pre_b = H_b[H_b['t'] < treatment_year]
        piv_b_pre = pre_b.pivot(index='t', columns='G', values='Hbar')
        if 0 in piv_b_pre.columns and 1 in piv_b_pre.columns:
            diff_b = piv_b_pre[1] - piv_b_pre[0]
            if len(diff_b.dropna()) >= 3:
                x = diff_b.dropna().index.values.astype(float)
                y = diff_b.dropna().values
                slope = np.polyfit(x, y, 1)[0]
                bootstrap_slopes.append(slope)

    # Inference
    print(f"\nBootstrap CI's en p-waarden voor t* = {treatment_year}:")
    print(f"{'t':<6}{'τ̂_H,t':<12}{'95% CI (H)':<26}{'τ̂_F,t':<14}{'95% CI (F)':<28}{'p (H)':<8}")
    print("-" * 96)
    inference_rows = []
    for t in range(treatment_year, T_END + 1):
        boot_H = np.array(bootstrap_tau_H[t])
        boot_F = np.array(bootstrap_tau_F[t])
        if len(boot_H) < 50:
            continue
        tau_H_pt = float(results_df[results_df['t']==t]['tau_H_t'].iloc[0])
        tau_F_pt = float(results_df[results_df['t']==t]['tau_F_t'].iloc[0])
        ci_H = np.percentile(boot_H, [2.5, 97.5])
        ci_F = np.percentile(boot_F, [2.5, 97.5])
        if tau_H_pt > 0:
            p_H = 2 * np.mean(boot_H <= 0)
        else:
            p_H = 2 * np.mean(boot_H >= 0)
        p_H = float(min(p_H, 1.0))
        print(f"{t:<6}{tau_H_pt:<+12.4f}[{ci_H[0]:+.4f}, {ci_H[1]:+.4f}]  {tau_F_pt:<+14.4f}[{ci_F[0]:+.4f}, {ci_F[1]:+.4f}]  {p_H:.4f}")
        inference_rows.append({
            'treatment_year': treatment_year, 't': t,
            'tau_H': tau_H_pt, 'tau_H_ci_lo': ci_H[0], 'tau_H_ci_hi': ci_H[1], 'tau_H_p': p_H,
            'tau_F': tau_F_pt, 'tau_F_ci_lo': ci_F[0], 'tau_F_ci_hi': ci_F[1],
            'n_boot': len(boot_H),
        })

    # Pre-trend slope inference
    boot_slopes = np.array(bootstrap_slopes)
    if len(boot_slopes) > 50:
        slope_se = float(boot_slopes.std())
        slope_ci = np.percentile(boot_slopes, [2.5, 97.5])
        p_slope = float(2 * min(np.mean(boot_slopes <= 0), np.mean(boot_slopes >= 0)))
        print(f"\nPre-trend slope op H̄:")
        print(f"  Point: {slope_pt:+.4f} per jaar")
        print(f"  Bootstrap SE: {slope_se:.4f}")
        print(f"  95% CI: [{slope_ci[0]:+.4f}, {slope_ci[1]:+.4f}]")
        print(f"  Bootstrap p: {p_slope:.4f}")
        if p_slope > 0.05:
            print(f"  → FAILS TO REJECT parallel trends in H̄ at α=0.05 ✓")
        else:
            print(f"  → REJECTS parallel trends in H̄ at α=0.05 ✗")
    else:
        slope_se = float('nan')
        p_slope = float('nan')
        slope_ci = (float('nan'), float('nan'))

    return {
        'treatment_year': treatment_year,
        'inference_df': pd.DataFrame(inference_rows),
        'slope_pt': slope_pt,
        'slope_se': slope_se,
        'slope_p': p_slope,
        'slope_ci': slope_ci,
        'results_df': results_df,
        'pre_pivot': pivot_pre,
        'pivot_all': pivot_all,
    }


# === Build project lookup voor bootstrap ===
project_ids = sp['project_id'].values
project_lookup = {row['project_id']: row.to_dict() for _, row in sp.iterrows()}


# === RUN TEST 2A: ANTICIPATION (t* = 2024) ===
result_2A = run_deaner_ku_test(2024, panel, project_lookup, project_ids,
                                 label="2A — Anticipation effect (CBAM transitional)")


# === RUN TEST 2B: ACTUAL EFFECT (t* = 2026) ===
result_2B = run_deaner_ku_test(2026, panel, project_lookup, project_ids,
                                 label="2B — Actual effect (CBAM full effect 1 jan 2026)")


# === VERGELIJKING + FIGUREN ===
header("VERGELIJKING TEST 2A vs 2B")

print(f"\n{'Treatment time':<25}{'τ̂_H':<14}{'95% CI':<26}{'p':<8}")
print("-" * 76)
print(f"\nTEST 2A (Anticipation, t* = 2024):")
for _, r in result_2A['inference_df'].iterrows():
    print(f"  t={int(r['t'])}: τ̂_H = {r['tau_H']:+.4f} [{r['tau_H_ci_lo']:+.4f}, {r['tau_H_ci_hi']:+.4f}], p = {r['tau_H_p']:.4f}")
print(f"\nTEST 2B (Actual effect, t* = 2026):")
for _, r in result_2B['inference_df'].iterrows():
    print(f"  t={int(r['t'])}: τ̂_H = {r['tau_H']:+.4f} [{r['tau_H_ci_lo']:+.4f}, {r['tau_H_ci_hi']:+.4f}], p = {r['tau_H_p']:.4f}")

# === FIGUREN ===
header("Figuren")

# Figuur 1: H̄ trends
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
years = sorted(H_df['t'].unique())
H_treated = [H_df[(H_df['G']==1) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]
H_control = [H_df[(H_df['G']==0) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]
ax1.plot(years, H_treated, 'o-', color='#d62728', label='Treated (EU-27)', linewidth=2.2, markersize=8)
ax1.plot(years, H_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=8)
ax1.axvline(x=2023.5, color='orange', linestyle='--', alpha=0.7, label='CBAM transitional (t*=2024)')
ax1.axvline(x=2025.5, color='red', linestyle='--', alpha=0.7, label='CBAM full effect (t*=2026)')
ax1.set_xlabel('Calendar year', fontsize=12)
ax1.set_ylabel(r'Time-average hazard $\bar{H}_{g,t}$', fontsize=12)
ax1.set_title('Panel A: Time-average hazards (S&P data, N=3247)', fontsize=12)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(alpha=0.3)

F_treated = [F_df[(F_df['G']==1) & (F_df['t']==t)]['F'].iloc[0] for t in years]
F_control = [F_df[(F_df['G']==0) & (F_df['t']==t)]['F'].iloc[0] for t in years]
ax2.plot(years, F_treated, 'o-', color='#d62728', label='Treated (EU-27)', linewidth=2.2, markersize=8)
ax2.plot(years, F_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=8)
ax2.axvline(x=2023.5, color='orange', linestyle='--', alpha=0.7)
ax2.axvline(x=2025.5, color='red', linestyle='--', alpha=0.7)
ax2.set_xlabel('Calendar year', fontsize=12)
ax2.set_ylabel(r'Mean outcome $F_{g,t}$', fontsize=12)
ax2.set_title('Panel B: Mean outcomes (standard DiD object)', fontsize=12)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(alpha=0.3)

plt.suptitle('Test 2: S&P Data — Deaner-Ku Hazard-DiD with dual treatment times',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_sp_dual_treatment.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {FIG_DIR}/deaner_ku_sp_dual_treatment.png")

# Figuur 2: ATT estimates
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 2A: Anticipation
inf_A = result_2A['inference_df']
ax = axes[0]
ts_A = inf_A['t'].values
tau_H = inf_A['tau_H'].values
ci_lo = inf_A['tau_H_ci_lo'].values
ci_hi = inf_A['tau_H_ci_hi'].values
ax.errorbar(ts_A, tau_H, yerr=[tau_H - ci_lo, ci_hi - tau_H],
            fmt='o', color='#d62728', label=r'$\hat{\tau}_{\bar{H},t}$ (S&P)',
            markersize=10, capsize=5, linewidth=2)
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax.set_xlabel('Calendar year', fontsize=12)
ax.set_ylabel('ATT on time-average hazard', fontsize=12)
ax.set_title(f'Test 2A: Anticipation effect (t*=2024)', fontsize=12)
ax.legend(loc='best')
ax.grid(alpha=0.3)
ax.set_xticks(ts_A)

# 2B: Actual effect
inf_B = result_2B['inference_df']
ax = axes[1]
ts_B = inf_B['t'].values
tau_H = inf_B['tau_H'].values
ci_lo = inf_B['tau_H_ci_lo'].values
ci_hi = inf_B['tau_H_ci_hi'].values
ax.errorbar(ts_B, tau_H, yerr=[tau_H - ci_lo, ci_hi - tau_H],
            fmt='o', color='#d62728', label=r'$\hat{\tau}_{\bar{H},t}$ (S&P)',
            markersize=10, capsize=5, linewidth=2)
ax.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax.set_xlabel('Calendar year', fontsize=12)
ax.set_ylabel('ATT on time-average hazard', fontsize=12)
ax.set_title(f'Test 2B: Actual effect (t*=2026)', fontsize=12)
ax.legend(loc='best')
ax.grid(alpha=0.3)
ax.set_xticks(ts_B if len(ts_B) > 0 else [2026])

plt.suptitle('Deaner-Ku ATT: S&P data with N=103 cancellations',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_sp_att.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: {FIG_DIR}/deaner_ku_sp_att.png")


# === OPSLAAN ===
header("Resultaten opslaan")

# Combineer inference frames
all_inference = pd.concat([
    result_2A['inference_df'].assign(test='2A_anticipation'),
    result_2B['inference_df'].assign(test='2B_actual'),
], ignore_index=True)
all_inference.to_csv(OUTPUT_DIR / 'deaner_ku_sp_inference.csv', index=False)

summary_sp = pd.DataFrame([{
    'test': '2A_anticipation',
    'treatment_year': 2024,
    'n_projects': len(sp),
    'n_treated_EU27': int((sp['is_EU27']==1).sum()),
    'n_control_nonEU': int((sp['is_EU27']==0).sum()),
    'n_cancellations': int(sp['is_cancelled'].sum()),
    'pretrend_slope': result_2A['slope_pt'],
    'pretrend_slope_p': result_2A['slope_p'],
    'tau_H_first_post': float(result_2A['inference_df'].iloc[0]['tau_H']) if len(result_2A['inference_df']) > 0 else float('nan'),
    'tau_H_first_post_p': float(result_2A['inference_df'].iloc[0]['tau_H_p']) if len(result_2A['inference_df']) > 0 else float('nan'),
    'tau_F_last': float(result_2A['inference_df'].iloc[-1]['tau_F']) if len(result_2A['inference_df']) > 0 else float('nan'),
}, {
    'test': '2B_actual',
    'treatment_year': 2026,
    'n_projects': len(sp),
    'n_treated_EU27': int((sp['is_EU27']==1).sum()),
    'n_control_nonEU': int((sp['is_EU27']==0).sum()),
    'n_cancellations': int(sp['is_cancelled'].sum()),
    'pretrend_slope': result_2B['slope_pt'],
    'pretrend_slope_p': result_2B['slope_p'],
    'tau_H_first_post': float(result_2B['inference_df'].iloc[0]['tau_H']) if len(result_2B['inference_df']) > 0 else float('nan'),
    'tau_H_first_post_p': float(result_2B['inference_df'].iloc[0]['tau_H_p']) if len(result_2B['inference_df']) > 0 else float('nan'),
    'tau_F_last': float(result_2B['inference_df'].iloc[-1]['tau_F']) if len(result_2B['inference_df']) > 0 else float('nan'),
}])
summary_sp.to_csv(OUTPUT_DIR / 'deaner_ku_sp_summary.csv', index=False)
H_df.to_csv(OUTPUT_DIR / 'deaner_ku_sp_Hbar_all.csv', index=False)

print("Files:")
for f in ['deaner_ku_sp_inference.csv', 'deaner_ku_sp_summary.csv', 'deaner_ku_sp_Hbar_all.csv']:
    print(f"  - {OUTPUT_DIR}/{f}")


# === EINDCONCLUSIE ===
print("\n" + "=" * 76)
print("  EINDCONCLUSIE TEST 2 (S&P REPLICATIE)")
print("=" * 76)
print(f"\nSample size: N={len(sp)} projecten (vs N=714 in v7, 4.5x meer)")
print(f"Cancellations: N={int(sp['is_cancelled'].sum())} (vs N=31 in v7, 3.3x meer power)")
print()
print(f"TEST 2A (Anticipation, t*=2024):")
print(f"  Pre-trend slope op H̄: {result_2A['slope_pt']:+.4f} per jaar (p = {result_2A['slope_p']:.4f})")
if len(result_2A['inference_df']) > 0:
    print(f"  τ̂_H,2024 = {result_2A['inference_df'].iloc[0]['tau_H']:+.4f}, p = {result_2A['inference_df'].iloc[0]['tau_H_p']:.4f}")
print()
print(f"TEST 2B (Actual effect, t*=2026):")
print(f"  Pre-trend slope op H̄: {result_2B['slope_pt']:+.4f} per jaar (p = {result_2B['slope_p']:.4f})")
if len(result_2B['inference_df']) > 0:
    print(f"  τ̂_H,2026 = {result_2B['inference_df'].iloc[0]['tau_H']:+.4f}, p = {result_2B['inference_df'].iloc[0]['tau_H_p']:.4f}")
print()
print("CAVEAT TEST 2B: snapshot data tot ~maart 2026, slechts ~3 maanden")
print("post-treatment. Resultaten zijn indicatief, niet definitief.")
