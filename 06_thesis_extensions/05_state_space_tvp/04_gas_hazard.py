"""
04_gas_hazard.py

Observation-driven TVP hazard model met GAS (Generalized Autoregressive Score)
recursie (Creal-Koopman-Lucas 2008, JoE 2013).

Model:
  Observation: η_blue,t = α + β_blue + β_eua·z_t + β_int(t)·z_t
               η_pem,t  = α + β_eua·z_t
               y_tech,t ~ Binomial(n_tech,t, sigmoid(η_tech,t))

  GAS recursion:
    β_int(t+1) = ω·(1-φ) + φ·β_int(t) + α_gas·s_t

  Score (Bernoulli/Binomial likelihood):
    s_t = ∂log L_t / ∂β_int(t) = (y_blue,t - n_blue,t · p_blue,t) · z_t

Identification:
  - ω: long-run mean van β_int (mean reversion target)
  - φ: persistence (close to 1 = slow movement)
  - α_gas: response to score (how strongly β_int adjusts to data)

Aggregeert tot (year × technology) niveau om met scan over jaren te kunnen werken.

Auteur: Sake Saakstra
Koopman-supervised Chapter 7 - methodologische hoofdbijdrage
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pymc as pm
import pytensor
import pytensor.tensor as pt
import arviz as az

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_gas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "figures").mkdir(exist_ok=True)

RUN_MODE = "quick"
if RUN_MODE == "quick":
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 2, 0.98
else:
    N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 3000, 4000, 4, 0.99


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# DATA AGGREGATIE NAAR JAAR × TECH
# ============================================================================
header("Aggregating to year × technology level")

df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

# Bouw person-year panel
panel_rows = []
for idx, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'year_calendar': t,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()

# Merge EUA
mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['eua'].fillna(panel['eua'].median())
eua_mean_g = panel['mkt_eua'].mean()
eua_sd_g = panel['mkt_eua'].std()
panel['z'] = (panel['mkt_eua'] - eua_mean_g) / eua_sd_g

# Aggregeer naar year × tech
agg = panel.groupby(['year_calendar','is_blue_ccs']).agg(
    n_at_risk=('event_any_yr', 'size'),
    n_events=('event_any_yr', 'sum'),
    z=('z', 'first'),
    eua=('mkt_eua', 'first'),
).reset_index()

# Zorg dat we voor elk jaar beide tech-categorieën hebben (vul met 0 indien afwezig)
all_years = sorted(panel['year_calendar'].unique())
n_years = len(all_years)

def get_agg(year, blue):
    sub = agg[(agg['year_calendar']==year) & (agg['is_blue_ccs']==blue)]
    if len(sub) == 0:
        eua_val = float(yearly_eua[yearly_eua['year_calendar']==year]['eua'].iloc[0]) if (yearly_eua['year_calendar']==year).any() else eua_mean_g
        z_val = (eua_val - eua_mean_g) / eua_sd_g
        return 0, 0, z_val
    r = sub.iloc[0]
    return int(r['n_at_risk']), int(r['n_events']), float(r['z'])

blue_at = np.array([get_agg(y, 1)[0] for y in all_years], dtype=float)
blue_ev = np.array([get_agg(y, 1)[1] for y in all_years], dtype=float)
pem_at  = np.array([get_agg(y, 0)[0] for y in all_years], dtype=float)
pem_ev  = np.array([get_agg(y, 0)[1] for y in all_years], dtype=float)
z_arr   = np.array([get_agg(y, 1)[2] for y in all_years], dtype=float)

print(f"  Years: {n_years} (van {all_years[0]} tot {all_years[-1]})")
print(f"  Total events: blue={blue_ev.sum()}, PEM={pem_ev.sum()}")
print(f"  Year-level data preview:")
for i, y in enumerate(all_years):
    if blue_ev[i] + pem_ev[i] > 0:
        print(f"    {y}: blue {int(blue_ev[i])}/{int(blue_at[i])}, "
              f"PEM {int(pem_ev[i])}/{int(pem_at[i])}, z={z_arr[i]:.2f}")


# ============================================================================
# GAS MODEL
# ============================================================================
header(f"GAS hazard model ({N_CHAINS} chains x {N_DRAWS} draws)")

with pm.Model() as gas_model:
    # === GAS hyperparameters ===
    omega = pm.Normal("omega", mu=-1.0, sigma=1.0)
    phi = pm.Beta("phi", alpha=8, beta=2)
    alpha_gas = pm.HalfNormal("alpha_gas", sigma=0.5)
    
    # Initial state
    beta_int_init = pm.Normal("beta_int_init", mu=-1.0, sigma=1.5)
    
    # === Static observation parameters ===
    alpha_int = pm.Normal("alpha_int", mu=-4.0, sigma=1.0)
    beta_blue = pm.Normal("beta_blue", mu=0.0, sigma=2.0)
    beta_eua = pm.Normal("beta_eua", mu=0.0, sigma=2.0)
    
    # === Convert numpy arrays to pytensor tensors ===
    z_tensor = pt.as_tensor_variable(z_arr)
    blue_at_t = pt.as_tensor_variable(blue_at)
    blue_ev_t = pt.as_tensor_variable(blue_ev)
    pem_at_t = pt.as_tensor_variable(pem_at)
    pem_ev_t = pt.as_tensor_variable(pem_ev)
    
    # === GAS recursion via scan ===
    def gas_step(z, b_at, b_ev, p_at, p_ev, beta_prev,
                 omega_, phi_, alpha_, alpha_i, b_blue, b_eua):
        # Predicted prob using current state β_int(t)
        eta_blue = alpha_i + b_blue + b_eua * z + beta_prev * z
        p_blue = pt.sigmoid(eta_blue)
        
        # Score = ∂log L/∂β_int evaluated at β_int(t)
        # For binomial: s_t = (y - n·p) · z
        s_t = (b_ev - b_at * p_blue) * z
        
        # Scale by sqrt(information) for numerical stability
        info = b_at * p_blue * (1.0 - p_blue) * (z * z) + 0.1
        scaled_score = s_t / pt.sqrt(info)
        
        # GAS update: β_int(t+1) = ω(1-φ) + φβ_int(t) + α·s_t
        beta_new = omega_ * (1.0 - phi_) + phi_ * beta_prev + alpha_ * scaled_score
        return beta_new
    
    beta_int_seq, _ = pytensor.scan(
        fn=gas_step,
        sequences=[z_tensor, blue_at_t, blue_ev_t, pem_at_t, pem_ev_t],
        outputs_info=[beta_int_init],
        non_sequences=[omega, phi, alpha_gas, alpha_int, beta_blue, beta_eua],
    )
    
    # Trajectory = [β_int_init, β_int(1), ..., β_int(T-1)]
    # We want for likelihood at time t to use β_int(t)
    # So prepend init and drop last (we don't observe T+1)
    beta_int_traj = pt.concatenate([pt.stack([beta_int_init]), beta_int_seq[:-1]])
    
    pm.Deterministic("beta_int_traj", beta_int_traj)
    
    # === Likelihood: Binomial per (year, tech) ===
    eta_blue_full = alpha_int + beta_blue + beta_eua * z_tensor + beta_int_traj * z_tensor
    eta_pem_full = alpha_int + beta_eua * z_tensor
    
    p_blue_full = pt.sigmoid(eta_blue_full)
    p_pem_full = pt.sigmoid(eta_pem_full)
    
    pm.Binomial("blue_obs", n=blue_at_t, p=p_blue_full, observed=blue_ev_t)
    pm.Binomial("pem_obs", n=pem_at_t, p=p_pem_full, observed=pem_ev_t)
    
    trace = pm.sample(
        draws=N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
        target_accept=TARGET_ACCEPT, max_treedepth=12,
        random_seed=20260518, progressbar=False, return_inferencedata=True,
    )


# ============================================================================
# DIAGNOSTIEK
# ============================================================================
header("MCMC Diagnostics")
diag = az.summary(trace, var_names=["omega", "phi", "alpha_gas",
                                     "beta_int_init", "alpha_int",
                                     "beta_blue", "beta_eua"])
print(diag.round(3).to_string())
n_div = int(sum(trace.sample_stats.diverging.values.flatten()))
print(f"\nDivergences: {n_div}")

# Extract trajectory
beta_traj_draws = trace.posterior["beta_int_traj"].values  # (chains, draws, n_years)
beta_traj_flat = beta_traj_draws.reshape(-1, n_years)

# ============================================================================
# RESULTS
# ============================================================================
header("β_int(t) trajectory")
rows = []
for i, y in enumerate(all_years):
    d = beta_traj_flat[:, i]
    rows.append({
        'year': y,
        'median': float(np.median(d)),
        'mean': float(d.mean()),
        'sd': float(d.std()),
        'lo_95': float(np.quantile(d, 0.025)),
        'hi_95': float(np.quantile(d, 0.975)),
        'lo_80': float(np.quantile(d, 0.10)),
        'hi_80': float(np.quantile(d, 0.90)),
    })
gas_df = pd.DataFrame(rows)
print(gas_df.round(3).to_string(index=False))
gas_df.to_csv(OUTPUT_DIR / "gas_trajectory.csv", index=False)


# ============================================================================
# HOOFDFIGUUR: GAS-driven β_int(t) trajectorie
# ============================================================================
header("Figures")
fig, ax = plt.subplots(figsize=(11, 6))
ax.fill_between(gas_df['year'], gas_df['lo_95'], gas_df['hi_95'],
                color='#4477AA', alpha=0.20, label='95% credible band')
ax.fill_between(gas_df['year'], gas_df['lo_80'], gas_df['hi_80'],
                color='#4477AA', alpha=0.35, label='80% credible band')
ax.plot(gas_df['year'], gas_df['median'], color='#222288', lw=2.5, marker='o',
        markersize=4, label='Posterior median')
ax.axhline(0, linestyle='--', color='red', alpha=0.7, label='No interaction')
ax.axhline(-1.43, linestyle=':', color='gray', alpha=0.7,
           label='Static estimate (Spoor B-2)')
ax.set_xlabel("Calendar year")
ax.set_ylabel(r"$\beta_{int}(t)$: GAS-driven carbon-conditional coefficient")
ax.set_title("Observation-driven (GAS) time-varying Blue×EUA interaction")
ax.legend(loc='best')
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/gas_beta_int_trajectory.pdf")
plt.close(fig)

# Vergelijking met 4-block
blocks_csv = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_blocks/blocks_results.csv"
if blocks_csv.exists():
    blocks = pd.read_csv(blocks_csv)
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.fill_between(gas_df['year'], gas_df['lo_95'], gas_df['hi_95'],
                    color='#4477AA', alpha=0.20, label='GAS 95% CrI')
    ax.plot(gas_df['year'], gas_df['median'], color='#222288', lw=2.5,
            marker='o', markersize=4, label='GAS median')
    # 4 blocks als bars
    block_years = [(2010,2019), (2020,2022), (2023,2024), (2025,2026)]
    for i, (y1, y2) in enumerate(block_years):
        med = blocks.iloc[i]['beta_int_median']
        lo = blocks.iloc[i]['beta_int_lo']
        hi = blocks.iloc[i]['beta_int_hi']
        ax.fill_between([y1, y2], [lo, lo], [hi, hi], color='#EE6677', alpha=0.20)
        ax.plot([y1, y2], [med, med], color='#EE6677', lw=2.5)
    ax.plot([], [], color='#EE6677', lw=2.5, label='4-block parameter-driven TVP')
    ax.axhline(0, linestyle='--', color='red', alpha=0.7)
    ax.set_xlabel("Calendar year")
    ax.set_ylabel(r"$\beta_{int}$: carbon-conditional coefficient")
    ax.set_title("GAS observation-driven vs 4-block parameter-driven TVP")
    ax.legend(loc='best')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / "figures/gas_vs_blocks.pdf")
    plt.close(fig)
    print(f"  Vergelijking opgeslagen: gas_vs_blocks.pdf")

print(f"\nResultaten in: {OUTPUT_DIR}")
