"""
02_tvp_hazard_blocks.py

VERVANG voor 01_tvp_hazard_pilot.py — gebruikt 4 economische regimes als
time-blocks ipv 27 jaarlijkse states. Methodologisch eleganter EN sneller.

Economische regimes:
  Block 0: 2010-2019  "Pre-energy-crisis era"        (laag EUA, weinig events)
  Block 1: 2020-2022  "Pandemic + early energy crisis" (EUA stijgt, weinig events)
  Block 2: 2023-2024  "Peak cancellations + crisis"   (EUA piek €100, 34 events)
  Block 3: 2025-2026  "Post-peak normalization"        (EUA stabilizes, paar events)

Model:
  logit(h_it) = α + β_blue·blue + β_eua·eua_t 
              + β_int(block_t)·blue·eua_t + γ·controls

  β_int volgt random walk over blocks:
    β_int(b+1) = β_int(b) + η_b,    η ~ N(0, σ²)

Empirische vraag: is β_int(b) significant verschillend tussen blocks?
Specifiek: is de carbon-conditional sensitiviteit veranderd vlak voor
de cancellation wave van 2023-2024?

Auteur: Sake Saakstra
Methodologische extensie van Spoor B-2 — Koopman-supervised
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymc as pm
import pytensor.tensor as pt
import arviz as az

# ============================================================================
# CONFIG
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_blocks"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "figures").mkdir(exist_ok=True)

RUN_MODE = "quick"
if RUN_MODE == "quick":
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 1500, 2, 0.95
else:
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 3000, 3000, 4, 0.98
RANDOM_SEED = 20260518


# Economische regime definitie
def year_to_block(y):
    if y <= 2019: return 0
    if y <= 2022: return 1
    if y <= 2024: return 2
    return 3

BLOCK_LABELS = ["2010-2019\nPre-crisis", "2020-2022\nPandemic+\nearly crisis",
                "2023-2024\nPeak\ncancellations", "2025-2026\nNormalization"]
N_BLOCKS = 4


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# DATA + PANEL
# ============================================================================
header("Building person-year panel with 4-block time index")

df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)
df['project_id'] = df.index

panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()

mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
yearly_eua.columns = ['year_calendar', 'mkt_eua']
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['mkt_eua'].fillna(panel['mkt_eua'].median())
eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['mkt_eua_z'] = (panel['mkt_eua'] - eua_mean) / eua_sd
panel['block'] = panel['year_calendar'].apply(year_to_block).astype(int)

print(f"  Panel: {len(panel)} rows, events = {panel['event_any_yr'].sum()}")
print(f"  Events per block:")
for b in range(N_BLOCKS):
    n_obs = (panel['block']==b).sum()
    n_ev = panel[panel['block']==b]['event_any_yr'].sum()
    print(f"    Block {b} ({BLOCK_LABELS[b].split(chr(10))[0]}): {n_obs} obs, {n_ev} events")


# ============================================================================
# DESIGN
# ============================================================================
X_blue = panel['is_blue_ccs'].values.astype(float)
X_eua = panel['mkt_eua_z'].values.astype(float)
X_year_since = panel['year_since_start'].values.astype(float)
X_capacity = panel['log_capacity_mw'].values.astype(float)
block_idx = panel['block'].values.astype(int)
events_obs = panel['event_any_yr'].values.astype(int)


# ============================================================================
# MODEL
# ============================================================================
header(f"4-block TVP hazard model ({N_CHAINS} chains x {N_DRAWS} draws)")

with pm.Model() as block_model:
    # Hyperprior op innovation variance van β_int
    sigma_int = pm.HalfNormal("sigma_int", sigma=0.5)
    
    # β_int(block): random walk over 4 blocks
    # Initial value met informative prior gebaseerd op static Spoor B-2 result (~-1.5)
    init_dist = pm.Normal.dist(mu=-1.0, sigma=2.0)
    beta_int_block = pm.GaussianRandomWalk(
        "beta_int_block", sigma=sigma_int, init_dist=init_dist, shape=N_BLOCKS
    )
    
    # Static coefficients (parsimony)
    alpha = pm.Normal("alpha", mu=-4.5, sigma=1.5)
    beta_blue = pm.Normal("beta_blue", mu=0, sigma=2.0)
    beta_eua = pm.Normal("beta_eua", mu=0, sigma=2.0)
    beta_year_since = pm.Normal("beta_year_since", mu=0, sigma=1.5)
    beta_cap = pm.Normal("beta_cap", mu=0, sigma=1.5)
    
    eta = (alpha
           + beta_blue * X_blue
           + beta_eua * X_eua
           + beta_int_block[block_idx] * X_blue * X_eua
           + beta_year_since * X_year_since
           + beta_cap * X_capacity)
    
    pm.Bernoulli("events", logit_p=eta, observed=events_obs)
    
    trace = pm.sample(
        draws=N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
        target_accept=TARGET_ACCEPT, max_treedepth=12,
        random_seed=RANDOM_SEED,
        progressbar=False, return_inferencedata=True,
    )


# ============================================================================
# DIAGNOSTIEK + RESULTS
# ============================================================================
header("Diagnostics + results")

summary = az.summary(trace, var_names=[
    "alpha", "beta_blue", "beta_eua", "beta_year_since", "beta_cap",
    "sigma_int", "beta_int_block"
])
print(summary.round(3).to_string())

n_div = int(sum(trace.sample_stats.diverging.values.flatten()))
print(f"\nDivergences: {n_div}")

# Per-block beta_int extractie
header("β_int per economic regime")
block_rows = []
for b in range(N_BLOCKS):
    draws = trace.posterior["beta_int_block"].values[..., b].flatten()
    hr_draws = np.exp(draws)
    row = {
        'block': b,
        'period': BLOCK_LABELS[b].replace('\n', ' '),
        'beta_int_median': float(np.median(draws)),
        'beta_int_lo': float(np.quantile(draws, 0.025)),
        'beta_int_hi': float(np.quantile(draws, 0.975)),
        'HR_at_zEUA_eq_1_median': float(np.exp(np.median(trace.posterior["beta_blue"].values.flatten()) + np.median(draws))),
    }
    block_rows.append(row)
    sig = "✓ <0" if row['beta_int_hi'] < 0 else (" ✓ >0" if row['beta_int_lo'] > 0 else " 0 in CrI")
    print(f"  Block {b} {row['period'][:25]:25s}: β_int = {row['beta_int_median']:6.3f} [{row['beta_int_lo']:6.3f}, {row['beta_int_hi']:6.3f}]  {sig}")

blocks_df = pd.DataFrame(block_rows)
blocks_df.to_csv(OUTPUT_DIR / "blocks_results.csv", index=False)


# ============================================================================
# HOOFDFIGUUR
# ============================================================================
header("Saving figures")
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(N_BLOCKS)
medians = [r['beta_int_median'] for r in block_rows]
los = [r['beta_int_lo'] for r in block_rows]
his = [r['beta_int_hi'] for r in block_rows]

ax.errorbar(x, medians, yerr=[np.array(medians)-np.array(los), np.array(his)-np.array(medians)],
            fmt='o', markersize=10, color='#222288', capsize=8, lw=2,
            label='Posterior median ± 95% CrI')
ax.axhline(0, linestyle='--', color='red', alpha=0.7, label='No interaction (β_int = 0)')
ax.axhline(-1.43, linestyle=':', color='gray', alpha=0.7,
           label='Static estimate (Spoor B-2 weakly informative)')
ax.set_xticks(x)
ax.set_xticklabels(BLOCK_LABELS, fontsize=9)
ax.set_ylabel(r"$\beta_{int}$ per regime: carbon-conditional coefficient")
ax.set_title("Time-varying Blue × EUA interaction across 4 economic regimes (2010-2026)")
ax.legend(loc='best')
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/beta_int_blocks.pdf")
plt.close(fig)
print(f"  Opgeslagen: figures/beta_int_blocks.pdf")
print(f"  Opgeslagen: blocks_results.csv")
print(f"\nResultaten in: {OUTPUT_DIR}")
