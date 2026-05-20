"""
19_deaner_ku_sp_dual_treatment.py

============================================================================
Test 2: Deaner-Ku Hazard-DiD op S&P data met DUAL TREATMENT TIME
============================================================================

Reference: Deaner & Ku (2024), arXiv:2405.05220

Methodologische motivatie (rectificatie t.o.v. Pijler 14):
  CBAM kent TWEE distincte treatment-tijdstippen die verschillende causale
  effecten testen:

  1. ANTICIPATION TEST (t* = 1 okt 2023 → kalenderjaar 2024):
     - CBAM transitional adoption datum
     - Alleen reporting requirements, GEEN financial obligations
     - Test: reageert de markt op formele adoption?

  2. ACTUAL EFFECT TEST (t* = 1 jan 2026):
     - CBAM definitive phase begin
     - Importers moeten daadwerkelijk certificates kopen tegen EU-ETS prijs
     - Test: causaal effect van actual financial costs

  Pijler 14 testte alleen (1) op v7 data. We doen nu BEIDE op S&P data
  (3249 projecten, 103 cancellations vs v7's 714 projecten, 31 cancellations).

Data:
  S&P Global Hydrogen Projects Master Database (24 maart 2026 snapshot)
  N = 3249, met 103 "Plans cancelled" events
  Treated: 1003 EU-27 projecten
  Control: 2246 non-EU projecten

Cancellation timing proxy (S&P heeft geen exact event date):
  cancellation_year = ceil((announce_year + est_year_online) / 2)
  fallback voor 35 projecten zonder est_year_online: announce_year + 3 jaar

Auteur: Sake Saakstra, 20 mei 2026
Pijler 15 in de robustness battery
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
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD S&P DATA ===
header("STAP 1: Laad S&P data en bouw treatment / control groepen")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
print(f"S&P data: {sp.shape[0]} projecten, {sp.shape[1]} kolommen")

# Treatment definitie: G = 1 als EU-27, anders 0
sp['G'] = (sp['Region major'] == 'Europe (EU-27)').astype(int)
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year.astype('Int64')
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')

# Filter projecten met geldige announce_year
sp = sp[sp['announce_year'].notna()].copy()
sp['announce_year'] = sp['announce_year'].astype(float)
print(f"Na filter geldige announce_year: {len(sp)} projecten")
print(f"  G=1 (EU treated):     {(sp['G']==1).sum()}")
print(f"  G=0 (non-EU control): {(sp['G']==0).sum()}")

# Cancellation timing proxy
sp['event_type'] = (sp['project_status'] == 'Plans cancelled').astype(int)

# Proxy: midpoint(announce, est_online) of fallback announce+3
sp['cancellation_year'] = np.where(
    (sp['event_type'] == 1) & sp['est_year_online'].notna(),
    np.ceil((sp['announce_year'] + sp['est_year_online']) / 2),
    np.where(
        sp['event_type'] == 1,
        sp['announce_year'] + 3,
        np.nan
    )
)
# Clip naar [announce_year, 2026]
sp['cancellation_year'] = sp[['cancellation_year', 'announce_year']].apply(
    lambda x: max(x['cancellation_year'], x['announce_year']) if not pd.isna(x['cancellation_year']) else np.nan,
    axis=1
)
sp['cancellation_year'] = sp['cancellation_year'].clip(upper=2026.0)

n_cancel_total = int(sp['event_type'].sum())
print(f"\nTotaal cancellations: {n_cancel_total}")
print(f"  EU cancelled: {((sp['event_type']==1) & (sp['G']==1)).sum()}")
print(f"  Non-EU cancelled: {((sp['event_type']==1) & (sp['G']==0)).sum()}")
print(f"\nCancellation jaar verdeling (proxy):")
print(sp.loc[sp['event_type']==1, 'cancellation_year'].value_counts().sort_index().to_string())

# Voeg project_id toe
sp['project_id'] = range(len(sp))


# === STAP 2: BOUW PANEL ===
header("STAP 2: Bouw project × kalenderjaar panel")

panel_rows = []
for _, row in sp.iterrows():
    for t in range(T_START, T_END + 1):
        if row['announce_year'] <= t:
            cancelled_by_t = (
                (row['event_type'] == 1) and
                (not pd.isna(row['cancellation_year'])) and
                (row['cancellation_year'] <= t)
            )
            panel_rows.append({
                'project_id': row['project_id'],
                'G': row['G'],
                't': t,
                'Y': int(cancelled_by_t),
            })
panel = pd.DataFrame(panel_rows)
print(f"Panel shape: {panel.shape}")
print(f"\nObservaties per groep × jaar:")
print(panel.groupby(['G', 't']).size().unstack().to_string())


# === STAP 3: F en H̄ ===
header("STAP 3: F_{g,t} en H̄_{g,t}")

def compute_F(panel):
    F = panel.groupby(['G', 't'])['Y'].mean().reset_index()
    F.columns = ['G', 't', 'F']
    return F

def compute_Hbar(F_df, t_start):
    F_df = F_df.copy()
    F_df['tau'] = F_df['t'] - t_start + 1
    F_clip = F_df['F'].clip(upper=0.9999, lower=0.0)
    F_df['Hbar'] = np.where(F_clip > 0, -np.log(1 - F_clip) / F_df['tau'], 0.0)
    return F_df

F_df = compute_F(panel)
H_df = compute_Hbar(F_df, T_START)
print(H_df.pivot(index='t', columns='G', values=['F', 'Hbar']).round(4).to_string())


# === STAP 4: PIPELINE FUNCTIE PER t* ===

def run_deaner_ku(t_star, panel_df, project_lookup, project_ids,
                  H_df_full, t_start=T_START, t_end=T_END, b_boot=B_BOOTSTRAP, rng_seed=SEED, label=''):
    """Volledige Deaner-Ku pipeline voor gegeven treatment time t*."""
    print(f"\n--- Deaner-Ku pipeline voor t* = {t_star} ({label}) ---")

    t_baseline = t_star - 1
    pivot_all = H_df_full.pivot(index='t', columns='G', values='Hbar')
    pivot_all.columns = ['Hbar_0', 'Hbar_1']
    if t_baseline not in pivot_all.index:
        print(f"Baseline t={t_baseline} niet in data — skip")
        return None

    # Pre-trends slope
    pre = H_df_full[H_df_full['t'] < t_star]
    pivot_pre = pre.pivot(index='t', columns='G', values='Hbar')
    pivot_pre.columns = ['Hbar_0', 'Hbar_1']
    pivot_pre['diff'] = pivot_pre['Hbar_1'] - pivot_pre['Hbar_0']
    pre_t = pivot_pre.index.values.astype(float)
    pre_diffs = pivot_pre['diff'].values
    if len(pre_diffs) >= 2:
        slope_pt = float(np.polyfit(pre_t, pre_diffs, 1)[0])
    else:
        slope_pt = float('nan')

    # ATT point estimates
    Hbar_1_base = pivot_all.loc[t_baseline, 'Hbar_1']
    Hbar_0_base = pivot_all.loc[t_baseline, 'Hbar_0']
    point_results = []
    for t in range(t_star, t_end + 1):
        if t not in pivot_all.index:
            continue
        H1 = pivot_all.loc[t, 'Hbar_1']
        H0 = pivot_all.loc[t, 'Hbar_0']
        tau_H = (H1 - Hbar_1_base) - (H0 - Hbar_0_base)
        Hbar_1_cf = H1 - tau_H
        tau_offset = t - t_start + 1
        F_1_t = 1 - np.exp(-tau_offset * H1)
        F_1_cf = 1 - np.exp(-tau_offset * Hbar_1_cf)
        tau_F = F_1_t - F_1_cf
        point_results.append({'t': t, 'tau_H': tau_H, 'tau_F': tau_F,
                              'F_1_t': F_1_t, 'F_1_cf': F_1_cf})
    point_df = pd.DataFrame(point_results)

    # Bootstrap inference
    rng = np.random.default_rng(rng_seed)
    boot_tau_H = {t: [] for t in range(t_star, t_end + 1)}
    boot_tau_F = {t: [] for t in range(t_star, t_end + 1)}
    boot_slopes = []
    n_proj = len(project_ids)
    print(f"  Bootstrap {b_boot} iteraties...")
    for b in range(b_boot):
        if (b + 1) % 100 == 0:
            print(f"    iter {b+1}/{b_boot}")
        boot_ids = rng.choice(project_ids, size=n_proj, replace=True)
        rows = []
        for pid in boot_ids:
            r = project_lookup[pid]
            for t in range(t_start, t_end + 1):
                if r['announce_year'] <= t:
                    cancelled_by_t = (
                        (r['event_type'] == 1) and
                        (not pd.isna(r['cancellation_year'])) and
                        (r['cancellation_year'] <= t)
                    )
                    rows.append({'G': r['G'], 't': t, 'Y': int(cancelled_by_t)})
        b_panel = pd.DataFrame(rows)
        F_b = compute_F(b_panel)
        H_b = compute_Hbar(F_b, t_start)
        piv_b = H_b.pivot(index='t', columns='G', values='Hbar')
        if 0 not in piv_b.columns or 1 not in piv_b.columns:
            continue
        if t_baseline not in piv_b.index:
            continue
        H1b_base = piv_b.loc[t_baseline, 1]
        H0b_base = piv_b.loc[t_baseline, 0]
        for t in range(t_star, t_end + 1):
            if t not in piv_b.index:
                continue
            H1 = piv_b.loc[t, 1]
            H0 = piv_b.loc[t, 0]
            tau_H_b = (H1 - H1b_base) - (H0 - H0b_base)
            boot_tau_H[t].append(tau_H_b)
            Hbar_1_cf = H1 - tau_H_b
            tau_offset = t - t_start + 1
            F_1_t = 1 - np.exp(-tau_offset * H1)
            F_1_cf = 1 - np.exp(-tau_offset * Hbar_1_cf)
            boot_tau_F[t].append(F_1_t - F_1_cf)
        # Pre-trend slope
        diff_b = piv_b[1] - piv_b[0]
        diff_pre = diff_b[diff_b.index < t_star]
        if len(diff_pre.dropna()) >= 3:
            x = diff_pre.dropna().index.values.astype(float)
            y = diff_pre.dropna().values
            slope_b = np.polyfit(x, y, 1)[0]
            boot_slopes.append(slope_b)
    boot_slopes = np.array(boot_slopes)

    # Inference summary
    inf_results = []
    for t in range(t_star, t_end + 1):
        bH = np.array(boot_tau_H[t])
        bF = np.array(boot_tau_F[t])
        if len(bH) < 50:
            continue
        pt_row = point_df[point_df['t'] == t].iloc[0]
        tau_H = float(pt_row['tau_H'])
        tau_F = float(pt_row['tau_F'])
        ci_H = np.percentile(bH, [2.5, 97.5])
        ci_F = np.percentile(bF, [2.5, 97.5])
        if tau_H > 0:
            p_H = 2 * np.mean(bH <= 0)
        else:
            p_H = 2 * np.mean(bH >= 0)
        p_H = float(min(p_H, 1.0))
        inf_results.append({
            't': t, 'tau_H': tau_H, 'tau_H_ci_lo': ci_H[0], 'tau_H_ci_hi': ci_H[1],
            'tau_H_p': p_H, 'tau_F': tau_F, 'tau_F_ci_lo': ci_F[0],
            'tau_F_ci_hi': ci_F[1], 'n_boot_valid': len(bH),
        })
    inf_df = pd.DataFrame(inf_results)

    # Slope inference
    if len(boot_slopes) >= 50:
        slope_se = float(boot_slopes.std())
        slope_ci = np.percentile(boot_slopes, [2.5, 97.5])
        p_slope = float(2 * min(np.mean(boot_slopes <= 0), np.mean(boot_slopes >= 0)))
    else:
        slope_se = slope_ci = p_slope = float('nan')

    return {
        't_star': t_star,
        'label': label,
        'point_df': point_df,
        'inf_df': inf_df,
        'pretrend_pivot': pivot_pre,
        'slope_pt': slope_pt,
        'slope_se': slope_se,
        'slope_ci': slope_ci,
        'slope_p': p_slope,
        'boot_slopes': boot_slopes,
    }


# Pre-bouw lookup
project_ids = sp['project_id'].values
project_lookup = {pid: row for pid, row in zip(sp['project_id'], sp.to_dict('records'))}


# === STAP 5: RUN TEST 2A — ANTICIPATION (t* = 2024) ===
header("STAP 5: TEST 2A — ANTICIPATION (CBAM transitional adoption okt 2023 → t* = 2024)")

result_2024 = run_deaner_ku(
    t_star=2024,
    panel_df=panel,
    project_lookup=project_lookup,
    project_ids=project_ids,
    H_df_full=H_df,
    label='ANTICIPATION (CBAM transitional adoption)',
)

print(f"\nPre-trend slope op H̄ (pre-2024): {result_2024['slope_pt']:+.4f}")
print(f"Bootstrap SE: {result_2024['slope_se']:.4f}, 95% CI: [{result_2024['slope_ci'][0]:+.4f}, {result_2024['slope_ci'][1]:+.4f}]")
print(f"Bootstrap p = {result_2024['slope_p']:.4f}")
if not pd.isna(result_2024['slope_p']):
    if result_2024['slope_p'] > 0.05:
        print("→ FAILS to reject parallel trends in H̄ at α=0.05 ✓")
    else:
        print("→ REJECTS parallel trends in H̄ at α=0.05 ✗")

print(f"\nATT estimates (t* = 2024):")
print(f"{'t':<6}{'τ̂_H,t':<14}{'95% CI (H)':<26}{'τ̂_F,t':<14}{'95% CI (F)':<26}{'p (H)':<8}")
print("-" * 96)
for _, r in result_2024['inf_df'].iterrows():
    print(f"{int(r['t']):<6}{r['tau_H']:<+14.4f}[{r['tau_H_ci_lo']:+.4f}, {r['tau_H_ci_hi']:+.4f}]  {r['tau_F']:<+14.4f}[{r['tau_F_ci_lo']:+.4f}, {r['tau_F_ci_hi']:+.4f}]  {r['tau_H_p']:.4f}")


# === STAP 6: RUN TEST 2B — ACTUAL EFFECT (t* = 2026) ===
header("STAP 6: TEST 2B — ACTUAL EFFECT (CBAM definitive phase 1 jan 2026 → t* = 2026)")

result_2026 = run_deaner_ku(
    t_star=2026,
    panel_df=panel,
    project_lookup=project_lookup,
    project_ids=project_ids,
    H_df_full=H_df,
    label='ACTUAL EFFECT (CBAM definitive phase)',
)

print(f"\nPre-trend slope op H̄ (pre-2026): {result_2026['slope_pt']:+.4f}")
print(f"Bootstrap SE: {result_2026['slope_se']:.4f}, 95% CI: [{result_2026['slope_ci'][0]:+.4f}, {result_2026['slope_ci'][1]:+.4f}]")
print(f"Bootstrap p = {result_2026['slope_p']:.4f}")
if not pd.isna(result_2026['slope_p']):
    if result_2026['slope_p'] > 0.05:
        print("→ FAILS to reject parallel trends in H̄ at α=0.05 ✓")
    else:
        print("→ REJECTS parallel trends in H̄ at α=0.05 ✗")

print(f"\nATT estimates (t* = 2026):")
print(f"{'t':<6}{'τ̂_H,t':<14}{'95% CI (H)':<26}{'τ̂_F,t':<14}{'95% CI (F)':<26}{'p (H)':<8}")
print("-" * 96)
for _, r in result_2026['inf_df'].iterrows():
    print(f"{int(r['t']):<6}{r['tau_H']:<+14.4f}[{r['tau_H_ci_lo']:+.4f}, {r['tau_H_ci_hi']:+.4f}]  {r['tau_F']:<+14.4f}[{r['tau_F_ci_lo']:+.4f}, {r['tau_F_ci_hi']:+.4f}]  {r['tau_H_p']:.4f}")


# === STAP 7: FIGUREN ===
header("STAP 7: Figuren")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5.5))
years = sorted(H_df['t'].unique())
H_treated = [H_df[(H_df['G']==1) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]
H_control = [H_df[(H_df['G']==0) & (H_df['t']==t)]['Hbar'].iloc[0] for t in years]

# Panel A: H̄ over tijd met BEIDE t* markers
ax1.plot(years, H_treated, 'o-', color='#d62728', label='Treated (EU)', linewidth=2.2, markersize=7)
ax1.plot(years, H_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=7)
ax1.axvline(x=2023.75, color='gray', linestyle='--', alpha=0.7, label='CBAM transitional (okt 2023)')
ax1.axvline(x=2025.95, color='red', linestyle='--', alpha=0.7, label='CBAM definitive (jan 2026)')
ax1.set_xlabel('Calendar year', fontsize=12)
ax1.set_ylabel(r'Time-average hazard $\bar{H}_{g,t}$', fontsize=12)
ax1.set_title('S&P data: Time-average hazards\n(N=3249, 103 cancellations)', fontsize=12)
ax1.legend(loc='upper left', fontsize=9)
ax1.grid(alpha=0.3)

# Panel B: F over tijd
F_treated = [F_df[(F_df['G']==1) & (F_df['t']==t)]['F'].iloc[0] for t in years]
F_control = [F_df[(F_df['G']==0) & (F_df['t']==t)]['F'].iloc[0] for t in years]
ax2.plot(years, F_treated, 'o-', color='#d62728', label='Treated (EU)', linewidth=2.2, markersize=7)
ax2.plot(years, F_control, 's-', color='#1f77b4', label='Control (non-EU)', linewidth=2.2, markersize=7)
ax2.axvline(x=2023.75, color='gray', linestyle='--', alpha=0.7, label='CBAM transitional')
ax2.axvline(x=2025.95, color='red', linestyle='--', alpha=0.7, label='CBAM definitive')
ax2.set_xlabel('Calendar year', fontsize=12)
ax2.set_ylabel(r'Mean outcome $F_{g,t}$ (cumulative cancel rate)', fontsize=12)
ax2.set_title('S&P data: Mean outcomes\n(Standard DiD object)', fontsize=12)
ax2.legend(loc='upper left', fontsize=9)
ax2.grid(alpha=0.3)

plt.suptitle('Deaner-Ku op S&P data — dual treatment time (Pijler 15)',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_sp_dual_treatment.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: deaner_ku_sp_dual_treatment.png")

# Figuur 2: ATT estimates voor beide t*
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

# Panel 1: t* = 2024
inf24 = result_2024['inf_df']
ts = inf24['t'].values
ax1.errorbar(ts - 0.1, inf24['tau_H'].values,
             yerr=[inf24['tau_H'].values - inf24['tau_H_ci_lo'].values,
                   inf24['tau_H_ci_hi'].values - inf24['tau_H'].values],
             fmt='o', color='#d62728', markersize=9, capsize=5, linewidth=2,
             label=r'$\hat{\tau}_{\bar{H},t}$')
ax1.errorbar(ts + 0.1, inf24['tau_F'].values,
             yerr=[inf24['tau_F'].values - inf24['tau_F_ci_lo'].values,
                   inf24['tau_F_ci_hi'].values - inf24['tau_F'].values],
             fmt='s', color='#2ca02c', markersize=9, capsize=5, linewidth=2,
             label=r'$\hat{\tau}_{F,t}$')
ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax1.set_xlabel('Calendar year', fontsize=11)
ax1.set_ylabel('ATT estimate', fontsize=11)
ax1.set_title(f'TEST 2A: ANTICIPATION test (t* = 2024)\nCBAM transitional adoption okt 2023',
              fontsize=11)
ax1.legend(loc='best', fontsize=10)
ax1.grid(alpha=0.3)
ax1.set_xticks(ts)

# Panel 2: t* = 2026
inf26 = result_2026['inf_df']
ts2 = inf26['t'].values
ax2.errorbar(ts2 - 0.05, inf26['tau_H'].values,
             yerr=[inf26['tau_H'].values - inf26['tau_H_ci_lo'].values,
                   inf26['tau_H_ci_hi'].values - inf26['tau_H'].values],
             fmt='o', color='#d62728', markersize=9, capsize=5, linewidth=2,
             label=r'$\hat{\tau}_{\bar{H},t}$')
ax2.errorbar(ts2 + 0.05, inf26['tau_F'].values,
             yerr=[inf26['tau_F'].values - inf26['tau_F_ci_lo'].values,
                   inf26['tau_F_ci_hi'].values - inf26['tau_F'].values],
             fmt='s', color='#2ca02c', markersize=9, capsize=5, linewidth=2,
             label=r'$\hat{\tau}_{F,t}$')
ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
ax2.set_xlabel('Calendar year', fontsize=11)
ax2.set_ylabel('ATT estimate', fontsize=11)
ax2.set_title(f'TEST 2B: ACTUAL EFFECT test (t* = 2026)\nCBAM definitive phase jan 2026',
              fontsize=11)
ax2.legend(loc='best', fontsize=10)
ax2.grid(alpha=0.3)
ax2.set_xticks(ts2)

plt.suptitle('S&P Deaner-Ku ATT estimates: Anticipation vs Actual Effect',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'deaner_ku_sp_att.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: deaner_ku_sp_att.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Resultaten opslaan")

result_2024['inf_df'].to_csv(OUTPUT_DIR / 'deaner_ku_sp_inference_t2024.csv', index=False)
result_2026['inf_df'].to_csv(OUTPUT_DIR / 'deaner_ku_sp_inference_t2026.csv', index=False)
H_df.to_csv(OUTPUT_DIR / 'deaner_ku_sp_Hbar.csv', index=False)

summary = {
    'method': 'Deaner-Ku Hazard-DiD (S&P data, dual treatment)',
    'reference': 'arXiv:2405.05220 (2024)',
    'n_projects': int(len(sp)),
    'n_treated_EU': int((sp['G']==1).sum()),
    'n_control_nonEU': int((sp['G']==0).sum()),
    'n_cancellations_total': n_cancel_total,
    'time_range': f'{T_START}–{T_END}',
    # Test 2A: anticipation
    't_star_2A': 2024,
    'label_2A': 'ANTICIPATION',
    'pretrend_slope_2A': result_2024['slope_pt'],
    'pretrend_slope_p_2A': result_2024['slope_p'],
    'tau_H_2024_anticipation': float(result_2024['inf_df'][result_2024['inf_df']['t']==2024]['tau_H'].iloc[0]) if len(result_2024['inf_df'][result_2024['inf_df']['t']==2024]) > 0 else np.nan,
    'tau_H_2025_anticipation': float(result_2024['inf_df'][result_2024['inf_df']['t']==2025]['tau_H'].iloc[0]) if len(result_2024['inf_df'][result_2024['inf_df']['t']==2025]) > 0 else np.nan,
    'tau_H_2026_anticipation': float(result_2024['inf_df'][result_2024['inf_df']['t']==2026]['tau_H'].iloc[0]) if len(result_2024['inf_df'][result_2024['inf_df']['t']==2026]) > 0 else np.nan,
    'tau_H_p_2024_anticipation': float(result_2024['inf_df'][result_2024['inf_df']['t']==2024]['tau_H_p'].iloc[0]) if len(result_2024['inf_df'][result_2024['inf_df']['t']==2024]) > 0 else np.nan,
    # Test 2B: actual effect
    't_star_2B': 2026,
    'label_2B': 'ACTUAL_EFFECT',
    'pretrend_slope_2B': result_2026['slope_pt'],
    'pretrend_slope_p_2B': result_2026['slope_p'],
    'tau_H_2026_actual': float(result_2026['inf_df'][result_2026['inf_df']['t']==2026]['tau_H'].iloc[0]) if len(result_2026['inf_df'][result_2026['inf_df']['t']==2026]) > 0 else np.nan,
    'tau_H_p_2026_actual': float(result_2026['inf_df'][result_2026['inf_df']['t']==2026]['tau_H_p'].iloc[0]) if len(result_2026['inf_df'][result_2026['inf_df']['t']==2026]) > 0 else np.nan,
    'tau_F_2026_actual': float(result_2026['inf_df'][result_2026['inf_df']['t']==2026]['tau_F'].iloc[0]) if len(result_2026['inf_df'][result_2026['inf_df']['t']==2026]) > 0 else np.nan,
    'b_bootstrap': B_BOOTSTRAP,
}
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / 'deaner_ku_sp_summary.csv', index=False)

print(f"Files: deaner_ku_sp_inference_t2024.csv, deaner_ku_sp_inference_t2026.csv, deaner_ku_sp_Hbar.csv, deaner_ku_sp_summary.csv")


# === STAP 9: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE TEST 2 (S&P data, dual treatment)")
print("=" * 78)
print(f"\nN = {len(sp)} projecten, {n_cancel_total} cancellations")
print(f"Treated EU = {(sp['G']==1).sum()}, Control non-EU = {(sp['G']==0).sum()}")

print(f"\n--- TEST 2A: ANTICIPATION (t* = 2024) ---")
print(f"Pre-trend slope op H̄: {result_2024['slope_pt']:+.4f}, p = {result_2024['slope_p']:.4f}")
if not pd.isna(result_2024['slope_p']):
    if result_2024['slope_p'] > 0.05:
        print("→ Parallel trends in H̄ NIET verworpen ✓")
    else:
        print("→ Parallel trends in H̄ verworpen ✗ — Deaner-Ku ID onder spanning")
if len(result_2024['inf_df']) > 0:
    print("ATT:")
    for _, r in result_2024['inf_df'].iterrows():
        sig = " (sig)" if r['tau_H_p'] < 0.05 else ""
        print(f"  τ̂_H,{int(r['t'])} = {r['tau_H']:+.4f}, p = {r['tau_H_p']:.4f}{sig}")

print(f"\n--- TEST 2B: ACTUAL EFFECT (t* = 2026) ---")
print(f"Pre-trend slope op H̄: {result_2026['slope_pt']:+.4f}, p = {result_2026['slope_p']:.4f}")
if not pd.isna(result_2026['slope_p']):
    if result_2026['slope_p'] > 0.05:
        print("→ Parallel trends in H̄ NIET verworpen ✓")
    else:
        print("→ Parallel trends in H̄ verworpen ✗")
if len(result_2026['inf_df']) > 0:
    print("ATT:")
    for _, r in result_2026['inf_df'].iterrows():
        sig = " (sig)" if r['tau_H_p'] < 0.05 else ""
        print(f"  τ̂_H,{int(r['t'])} = {r['tau_H']:+.4f}, p = {r['tau_H_p']:.4f}{sig}")

print(f"\n--- VERGELIJKING MET PIJLER 14 (v7 data) ---")
print(f"v7 (N=714, 31 events):  τ̂_H,2024 = -0.0002, p = 0.844 (insignificant)")
print(f"S&P (N=3249, 103 events): {'... zie boven'}")
print(f"\n3.3x meer events → more statistical power om effecten te detecteren als ze bestaan.")
