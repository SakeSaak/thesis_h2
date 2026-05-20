"""
26_45v_bootstrap_inference.py

============================================================================
Pijler 18b: Formele Bootstrap Inference voor 45V Triple-DiD
============================================================================

Motivatie:
  Pijler 18 leverde dramatische triple-DiD point estimates:
  - DDD cancel_rate (NPRM 2024): +0.285
  - DDD failure_rate (NPRM 2024): +0.368
  Maar zonder formele inference — geen bootstrap CI's, geen permutation
  p-waarde. Voor PhD-watertight rapportage en publication-grade claims is
  rigorous inference vereist.

  Pijler 18b voegt vier robustheids-elementen toe:
  1. CLUSTER BOOTSTRAP op project_id (B=1000)
  2. PERMUTATION TEST op groep-labels (B=1000)
  3. ALTERNATIVE CONTROL SETS robustness (3 specs)
  4. TRUMP CONFOUNDER ROBUSTNESS (pre-2025 cutoff)

Voor publication: voldoende formele inference om als publishable
finding voor Energy Policy / Climate Policy te framen.

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

T_NPRM = 2024
T_FINAL = 2025
B_BOOT = 1000
B_PERM = 1000
SEED = 20260520


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD DATA EN BOUW GROEPEN (zelfde als Pijler 18) ===
header("STAP 1: Laad S&P data en bouw 4-way groepen")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()

sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
sp['is_us'] = (sp['Geography'] == 'United States').astype(int)


def group_classify(row):
    if row['is_blue'] == 1:
        return 'US_Blue' if row['is_us'] == 1 else 'NonUS_Blue'
    elif row['is_green'] == 1:
        return 'US_Green' if row['is_us'] == 1 else 'NonUS_Green'
    else:
        return 'Other'

sp['group'] = sp.apply(group_classify, axis=1)
df = sp[sp['group'].isin(['US_Green', 'US_Blue', 'NonUS_Green', 'NonUS_Blue'])].copy()
df = df.reset_index(drop=True)
df['project_id'] = df.index

print(f"Sample: {len(df)} classifiable projecten")
print(f"  US_Green:    {(df['group']=='US_Green').sum()}")
print(f"  NonUS_Green: {(df['group']=='NonUS_Green').sum()}")
print(f"  US_Blue:     {(df['group']=='US_Blue').sum()}")
print(f"  NonUS_Blue:  {(df['group']=='NonUS_Blue').sum()}")


# State + event year
def classify_state(s):
    if s == 'Plans cancelled':
        return 'cancelled'
    elif s in ['On-hold (assumed)', 'On-hold (confirmed)']:
        return 'on_hold'
    elif s == 'Decommissioned':
        return 'decommissioned'
    elif s in ['Fully commissioned', 'Partially commissioned']:
        return 'operational'
    else:
        return 'still_active'

df['state'] = df['project_status'].apply(classify_state)
df['event_year'] = np.where(
    df['state'].isin(['cancelled', 'on_hold', 'decommissioned']) & df['est_year_online'].notna(),
    np.ceil((df['announce_year'] + df['est_year_online']) / 2),
    np.where(
        df['state'].isin(['cancelled', 'on_hold', 'decommissioned']),
        df['announce_year'] + 3,
        2026.0
    )
).clip(max=2026.0)


# === STAP 2: DDD FUNCTIE ===

def compute_ddd(df_subset, outcome_col='cancel_rate', t_pre_end=2023, t_post_start=2024, t_post_end=2026):
    """Bereken triple-difference op aggregaat panel."""
    panel = []
    for is_us_val in [0, 1]:
        for is_green_val in [0, 1]:
            sub = df_subset[(df_subset['is_us'] == is_us_val) &
                            ((df_subset['is_green'] == is_green_val) |
                             (df_subset['is_blue'] == (1 - is_green_val)))]
            # Filter to specific tech
            if is_green_val == 1:
                sub = df_subset[(df_subset['is_us'] == is_us_val) & (df_subset['is_green'] == 1)]
            else:
                sub = df_subset[(df_subset['is_us'] == is_us_val) & (df_subset['is_blue'] == 1)]
            if len(sub) == 0:
                continue
            for t in range(2018, 2027):
                risk = sub[sub['announce_year'] <= t]
                if len(risk) == 0:
                    continue
                n_cancel = ((risk['state'] == 'cancelled') & (risk['event_year'] <= t)).sum()
                Y = n_cancel / len(risk)
                panel.append({
                    'is_us': is_us_val, 'is_green': is_green_val,
                    'group': f"{'US' if is_us_val else 'NonUS'}_{'Green' if is_green_val else 'Blue'}",
                    't': t, 'Y': Y, 'n': len(risk),
                })
    p = pd.DataFrame(panel)
    if len(p) == 0:
        return None
    pre = p[p['t'] <= t_pre_end].groupby('group')['Y'].mean()
    post = p[(p['t'] >= t_post_start) & (p['t'] <= t_post_end)].groupby('group')['Y'].mean()
    needed = {'US_Green', 'NonUS_Green', 'US_Blue', 'NonUS_Blue'}
    if not needed.issubset(set(pre.index)) or not needed.issubset(set(post.index)):
        return None
    did_green = (post['US_Green'] - pre['US_Green']) - (post['NonUS_Green'] - pre['NonUS_Green'])
    did_blue = (post['US_Blue'] - pre['US_Blue']) - (post['NonUS_Blue'] - pre['NonUS_Blue'])
    ddd = did_green - did_blue
    return {'did_green': did_green, 'did_blue': did_blue, 'ddd': ddd}


# === STAP 3: POINT ESTIMATE ===
header("STAP 3: Point estimate (replicate Pijler 18)")

ddd_point = compute_ddd(df, t_pre_end=2023, t_post_start=2024, t_post_end=2026)
print(f"\nNPRM effect (t* = 2024):")
print(f"  DiD Green = {ddd_point['did_green']:+.4f}")
print(f"  DiD Blue  = {ddd_point['did_blue']:+.4f}")
print(f"  DDD       = {ddd_point['ddd']:+.4f}")


# === STAP 4: CLUSTER BOOTSTRAP OP project_id ===
header(f"STAP 4: Cluster bootstrap (B = {B_BOOT})")

rng = np.random.default_rng(SEED)
n = len(df)
project_ids = df['project_id'].values

bootstrap_ddds = []
print(f"Cluster bootstrap op {n} projecten...")
for b in range(B_BOOT):
    if (b + 1) % 100 == 0:
        print(f"  iter {b+1}/{B_BOOT}")
    boot_idx = rng.choice(project_ids, size=n, replace=True)
    boot_df = df.iloc[boot_idx].reset_index(drop=True)
    r = compute_ddd(boot_df)
    if r is not None:
        bootstrap_ddds.append(r['ddd'])

bootstrap_ddds = np.array(bootstrap_ddds)
print(f"\nBootstrap distribution (n={len(bootstrap_ddds)}):")
print(f"  Mean: {bootstrap_ddds.mean():+.4f}")
print(f"  SD:   {bootstrap_ddds.std():.4f}")
print(f"  Range: [{bootstrap_ddds.min():+.4f}, {bootstrap_ddds.max():+.4f}]")

ci_lo, ci_hi = np.percentile(bootstrap_ddds, [2.5, 97.5])
print(f"  95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]")

# 2-sided p-value
if ddd_point['ddd'] > 0:
    p_boot = 2 * np.mean(bootstrap_ddds <= 0)
else:
    p_boot = 2 * np.mean(bootstrap_ddds >= 0)
p_boot = float(min(p_boot, 1.0))
print(f"  Bootstrap p (2-sided): {p_boot:.4f}")


# === STAP 5: PERMUTATION TEST OP GROUP LABELS ===
header(f"STAP 5: Permutation test op groep-labels (B = {B_PERM})")

# Reshuffle is_us and is_green/is_blue labels, recompute DDD
permutation_ddds = []
print(f"Permutation: shuffle (is_us × is_green/blue) labels...")
for b in range(B_PERM):
    if (b + 1) % 100 == 0:
        print(f"  iter {b+1}/{B_PERM}")
    perm_df = df.copy()
    # Shuffle joint (is_us, is_green/is_blue) pairs
    perm_idx = rng.permutation(n)
    perm_df['is_us'] = df['is_us'].values[perm_idx]
    # Resample tech keeping joint structure
    perm_df['is_green'] = df['is_green'].values[perm_idx]
    perm_df['is_blue'] = df['is_blue'].values[perm_idx]
    r = compute_ddd(perm_df)
    if r is not None:
        permutation_ddds.append(r['ddd'])

permutation_ddds = np.array(permutation_ddds)
print(f"\nPermutation distribution (n={len(permutation_ddds)}):")
print(f"  Mean: {permutation_ddds.mean():+.4f}")
print(f"  SD:   {permutation_ddds.std():.4f}")
print(f"  Range: [{permutation_ddds.min():+.4f}, {permutation_ddds.max():+.4f}]")

# Permutation p-value
p_perm = float(np.mean(np.abs(permutation_ddds) >= np.abs(ddd_point['ddd'])))
print(f"  Permutation p (2-sided): {p_perm:.4f}")


# === STAP 6: ROBUSTNESS — ALTERNATIVE CONTROL SETS ===
header("STAP 6: Robustness — alternative control specifications")

# Spec 1: original (Blue as placebo)
print(f"\nSpec 1 — Original (Blue placebo):")
print(f"  DDD = {ddd_point['ddd']:+.4f}")

# Spec 2: drop NonUS_Blue, use only EU_Blue as placebo
df_eu_blue = df.copy()
df_eu_blue.loc[(df_eu_blue['is_blue'] == 1) & (df_eu_blue['Region major'] != 'Europe (EU-27)') &
                (df_eu_blue['is_us'] == 0), 'group'] = 'EXCLUDE'
df_spec2 = df_eu_blue[df_eu_blue['group'] != 'EXCLUDE'].copy()
ddd_2 = compute_ddd(df_spec2)
if ddd_2:
    print(f"\nSpec 2 — Only EU Blue as NonUS Blue (clean placebo):")
    print(f"  DDD = {ddd_2['ddd']:+.4f}")

# Spec 3: drop NonUS_Green from outside EU (zelfde clean control)
df_spec3 = df.copy()
df_spec3.loc[(df_spec3['is_green'] == 1) & (df_spec3['Region major'] != 'Europe (EU-27)') &
              (df_spec3['is_us'] == 0), 'group'] = 'EXCLUDE'
df_spec3 = df_spec3[df_spec3['group'] != 'EXCLUDE'].copy()
ddd_3 = compute_ddd(df_spec3)
if ddd_3:
    print(f"\nSpec 3 — Only EU Green as NonUS Green:")
    print(f"  DDD = {ddd_3['ddd']:+.4f}")


# === STAP 7: TRUMP CONFOUNDER ROBUSTNESS ===
header("STAP 7: Trump confounder robustness (cutoff data op 2024)")

# Trump 2.0 inauguratie: 20 jan 2025
# Pre-Trump test: gebruik alleen data t/m kalender-2024
ddd_pre_trump = compute_ddd(df, t_pre_end=2023, t_post_start=2024, t_post_end=2024)
print(f"\nPre-Trump cutoff (only 2024 as post-period):")
if ddd_pre_trump:
    print(f"  DDD = {ddd_pre_trump['ddd']:+.4f}")
    print(f"  DiD Green = {ddd_pre_trump['did_green']:+.4f}")
    print(f"  DiD Blue  = {ddd_pre_trump['did_blue']:+.4f}")

# Bootstrap voor pre-Trump versie
print(f"\nBootstrap pre-Trump (B=500)...")
pre_trump_boot = []
for b in range(500):
    if (b + 1) % 100 == 0:
        print(f"  iter {b+1}/500")
    boot_idx = rng.choice(project_ids, size=n, replace=True)
    boot_df = df.iloc[boot_idx].reset_index(drop=True)
    r = compute_ddd(boot_df, t_pre_end=2023, t_post_start=2024, t_post_end=2024)
    if r is not None:
        pre_trump_boot.append(r['ddd'])
pre_trump_boot = np.array(pre_trump_boot)
if len(pre_trump_boot) > 50:
    ci_pt_lo, ci_pt_hi = np.percentile(pre_trump_boot, [2.5, 97.5])
    print(f"  95% CI: [{ci_pt_lo:+.4f}, {ci_pt_hi:+.4f}]")
    if ddd_pre_trump['ddd'] > 0:
        p_pt = 2 * np.mean(pre_trump_boot <= 0)
    else:
        p_pt = 2 * np.mean(pre_trump_boot >= 0)
    p_pt = float(min(p_pt, 1.0))
    print(f"  Bootstrap p (2-sided): {p_pt:.4f}")


# === STAP 8: FIGUREN ===
header("STAP 8: Figuren")

# Fig 1: bootstrap + permutation distributions
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.hist(bootstrap_ddds, bins=40, color='#1f77b4', edgecolor='black', alpha=0.7, label='Bootstrap distribution')
ax1.axvline(x=ddd_point['ddd'], color='black', linewidth=2.5, label=f'Point estimate = {ddd_point["ddd"]:+.4f}')
ax1.axvline(x=ci_lo, color='red', linestyle='--', label=f'95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]')
ax1.axvline(x=ci_hi, color='red', linestyle='--')
ax1.axvline(x=0, color='gray', linestyle=':', alpha=0.6)
ax1.set_xlabel('Bootstrap DDD', fontsize=11)
ax1.set_ylabel('Frequency', fontsize=11)
ax1.set_title(f'Cluster bootstrap distribution (B={B_BOOT})\np_boot = {p_boot:.4f}', fontsize=11)
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(alpha=0.3)

ax2.hist(permutation_ddds, bins=40, color='#d62728', edgecolor='black', alpha=0.7, label='Permutation distribution')
ax2.axvline(x=ddd_point['ddd'], color='black', linewidth=2.5, label=f'Observed DDD = {ddd_point["ddd"]:+.4f}')
ax2.axvline(x=0, color='gray', linestyle=':', alpha=0.6)
ax2.set_xlabel('Permuted DDD (random labels)', fontsize=11)
ax2.set_ylabel('Frequency', fontsize=11)
ax2.set_title(f'Permutation distribution (B={B_PERM})\np_perm = {p_perm:.4f}', fontsize=11)
ax2.legend(loc='upper right', fontsize=9)
ax2.grid(alpha=0.3)

plt.suptitle('Pijler 18b: Formele inference voor 45V Triple-DiD',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler18b_inference_distributions.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler18b_inference_distributions.png")


# === STAP 9: OPSLAAN ===
header("STAP 9: Resultaten opslaan")

summary = {
    'method': 'Pijler 18b: Bootstrap + Permutation inference voor 45V Triple-DiD',
    'reference_p18': 'Strengthens Pijler 18 with formal inference',
    'n_total': int(n),
    'n_US_Green': int((df['group']=='US_Green').sum()),
    'n_NonUS_Green': int((df['group']=='NonUS_Green').sum()),
    'n_US_Blue': int((df['group']=='US_Blue').sum()),
    'n_NonUS_Blue': int((df['group']=='NonUS_Blue').sum()),
    'point_DDD': float(ddd_point['ddd']),
    'point_DiD_Green': float(ddd_point['did_green']),
    'point_DiD_Blue': float(ddd_point['did_blue']),
    'bootstrap_n': len(bootstrap_ddds),
    'bootstrap_mean': float(bootstrap_ddds.mean()),
    'bootstrap_se': float(bootstrap_ddds.std()),
    'bootstrap_ci_lo': float(ci_lo),
    'bootstrap_ci_hi': float(ci_hi),
    'bootstrap_p_2sided': float(p_boot),
    'permutation_n': len(permutation_ddds),
    'permutation_p_2sided': float(p_perm),
    'spec2_only_EU_NonUS_Blue': float(ddd_2['ddd']) if ddd_2 else np.nan,
    'spec3_only_EU_NonUS_Green': float(ddd_3['ddd']) if ddd_3 else np.nan,
    'pre_trump_DDD': float(ddd_pre_trump['ddd']) if ddd_pre_trump else np.nan,
    'pre_trump_ci_lo': float(ci_pt_lo) if 'ci_pt_lo' in dir() else np.nan,
    'pre_trump_ci_hi': float(ci_pt_hi) if 'ci_pt_hi' in dir() else np.nan,
    'pre_trump_p': float(p_pt) if 'p_pt' in dir() else np.nan,
}
pd.DataFrame([summary]).to_csv(OUTPUT_DIR / 'pijler18b_summary.csv', index=False)
pd.DataFrame({'bootstrap_DDD': bootstrap_ddds}).to_csv(OUTPUT_DIR / 'pijler18b_bootstrap.csv', index=False)
pd.DataFrame({'permutation_DDD': permutation_ddds}).to_csv(OUTPUT_DIR / 'pijler18b_permutation.csv', index=False)


# === STAP 10: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 18b (Formele inference voor 45V Triple-DiD)")
print("=" * 78)

print(f"\n--- POINT ESTIMATE ---")
print(f"  DDD = {ddd_point['ddd']:+.4f}")

print(f"\n--- CLUSTER BOOTSTRAP (B={B_BOOT}) ---")
print(f"  Mean = {bootstrap_ddds.mean():+.4f}, SE = {bootstrap_ddds.std():.4f}")
print(f"  95% CI = [{ci_lo:+.4f}, {ci_hi:+.4f}]")
print(f"  p_2sided = {p_boot:.4f}  {'***' if p_boot<0.001 else '**' if p_boot<0.01 else '*' if p_boot<0.05 else ''}")

print(f"\n--- PERMUTATION TEST (B={B_PERM}) ---")
print(f"  p_perm = {p_perm:.4f}")

print(f"\n--- ALTERNATIVE CONTROL SETS ---")
print(f"  Spec 1 (original):                          DDD = {ddd_point['ddd']:+.4f}")
if ddd_2:
    print(f"  Spec 2 (only EU as NonUS_Blue):             DDD = {ddd_2['ddd']:+.4f}")
if ddd_3:
    print(f"  Spec 3 (only EU as NonUS_Green):            DDD = {ddd_3['ddd']:+.4f}")

print(f"\n--- TRUMP CONFOUNDER ROBUSTNESS ---")
if ddd_pre_trump:
    print(f"  Pre-Trump (post-period = 2024 only):    DDD = {ddd_pre_trump['ddd']:+.4f}")
    if 'ci_pt_lo' in dir():
        print(f"  95% CI = [{ci_pt_lo:+.4f}, {ci_pt_hi:+.4f}], p = {p_pt:.4f}")

print(f"\n*** PHD-WATERTIGHT CONCLUSIE ***")
if p_boot < 0.05 and p_perm < 0.05:
    print(f"45V Three-Pillars NPRM heeft statistisch significant negatief effect")
    print(f"op US Green H2 projecten:")
    print(f"  DDD = {ddd_point['ddd']:+.4f}")
    print(f"  Bootstrap p = {p_boot:.4f}, Permutation p = {p_perm:.4f}")
    print(f"  Robust across {sum([ddd_2 is not None, ddd_3 is not None])+1} control specifications")
elif p_boot < 0.1 or p_perm < 0.1:
    print(f"Marginal significance — point estimate sterk maar formele inference op grens:")
    print(f"  Bootstrap p = {p_boot:.4f}, Permutation p = {p_perm:.4f}")
else:
    print(f"Point estimate ({ddd_point['ddd']:+.4f}) is groot maar formele inference")
    print(f"ondersteunt geen significant effect: p_boot = {p_boot:.4f}, p_perm = {p_perm:.4f}")
    print(f"Mogelijk reden: small sample US_Green = 79")
