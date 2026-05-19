"""
01_bayesian_survival_pymc.py

Bayesian survival analysis voor Blue_CCS vs PEM hydrogen project cancellation,
met sensitivity grid over prior specificaties.

PyMC vervanging van het brms script. Identieke methodologie:
  - Piecewise constant baseline hazard (mathematisch equivalent aan
    semi-parametric Cox PH in de limit van veel intervallen)
  - 4 prior specificaties: vague, weakly_informative, skeptical, informative
  - Output: posterior summaries, hazard ratios met credible intervals,
    diagnostics, vergelijking met frequentist lifelines

Voer eerst 00_setup_pymc.sh uit om packages te installeren.

Auteur: Sake Saakstra
Thesis extension - Bayesian Methodology (Python implementatie)
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
from lifelines import CoxPHFitter

# ============================================================================
# CONFIGURATIE
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
EXT_ROOT = PROJECT_ROOT / "06_thesis_extensions/01_bayesian_methodology"
DATA_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
RESULTS_DIR = EXT_ROOT / "pymc_version/results"

# Mode: "quick" ~3 min totaal, "full" ~20 min totaal
RUN_MODE = "quick"

if RUN_MODE == "quick":
    N_CHAINS = 2
    N_DRAWS = 1000
    N_TUNE = 1000
    TARGET_ACCEPT = 0.90
else:
    N_CHAINS = 4
    N_DRAWS = 2000
    N_TUNE = 2000
    TARGET_ACCEPT = 0.95

RANDOM_SEED = 20260518

# Output directories
(RESULTS_DIR / "traces").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "tables").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "figures").mkdir(parents=True, exist_ok=True)


# ============================================================================
# PRIOR SPECIFICATIES (parallel aan R-versie)
# ============================================================================
PRIOR_SPECS = {
    "vague": {
        "blue_ccs": dict(mu=0.0, sigma=5.0),
        "default":  dict(mu=0.0, sigma=5.0),
    },
    "weakly_informative": {
        "blue_ccs": dict(mu=0.0, sigma=2.0),
        "default":  dict(mu=0.0, sigma=1.5),
    },
    "skeptical": {
        "blue_ccs": dict(mu=0.0, sigma=1.0),
        "default":  dict(mu=0.0, sigma=1.5),
    },
    "informative": {
        "blue_ccs": dict(mu=1.5, sigma=0.7),
        "default":  dict(mu=0.0, sigma=1.5),
    },
}


def header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================================
# DATA LADEN EN VOORBEREIDEN
# ============================================================================
header(f"Bayesian Survival - PyMC (RUN_MODE={RUN_MODE})")

print("\n--- Data laden ---")
df = pd.read_csv(DATA_CSV)
df["is_blue_ccs"] = df["is_blue_ccs"].astype(int)
df["duration"] = df["duration"].astype(int).clip(lower=1)
df["event_any"] = (df["event_type"] > 0).astype(int)

print(f"  N totaal     = {len(df)}")
print(f"  Blue_CCS     = {df['is_blue_ccs'].sum()} ({100*df['is_blue_ccs'].mean():.1f}%)")
print(f"  PEM          = {(1-df['is_blue_ccs']).sum()} ({100*(1-df['is_blue_ccs'].mean()):.1f}%)")
print(f"  Event (any)  = {df['event_any'].sum()} ({100*df['event_any'].mean():.1f}%)")


# ============================================================================
# FREQUENTIST BASELINE met lifelines
# ============================================================================
print("\n--- Frequentist Cox PH (lifelines, sanity check) ---")

# Reduceer covariates voor stabiliteit (sponsor_owner heeft veel levels)
freq_df = df[["duration", "event_any", "is_blue_ccs", "log_capacity_mw"]].copy()
# Region dummies
region_dum = pd.get_dummies(df["region"], prefix="region", drop_first=True).astype(int)
sponsor_dum = pd.get_dummies(df["sponsor_type"], prefix="sponsor", drop_first=True).astype(int)
freq_df = pd.concat([freq_df, region_dum, sponsor_dum], axis=1)

cph = CoxPHFitter(penalizer=0.001)  # kleine penalty voor stabiliteit met perfecte separation
cph.fit(freq_df, duration_col="duration", event_col="event_any")
beta_blue_freq = cph.params_["is_blue_ccs"]
se_blue_freq = cph.standard_errors_["is_blue_ccs"]
hr_freq = np.exp(beta_blue_freq)
hr_lo_freq = np.exp(beta_blue_freq - 1.96 * se_blue_freq)
hr_hi_freq = np.exp(beta_blue_freq + 1.96 * se_blue_freq)
print(f"  Frequentist coef on is_blue_ccs: {beta_blue_freq:.3f} (SE {se_blue_freq:.3f})")
print(f"  Frequentist HR:                  {hr_freq:.2f} (95% CI [{hr_lo_freq:.2f}, {hr_hi_freq:.2f}])")


# ============================================================================
# PERSON-PERIOD DATA RESHAPE
# ============================================================================
# Voor piecewise constant hazard: één rij per (subject, interval) waar het
# subject "at risk" was. Interval = unit-year (durations zijn integers).
print("\n--- Person-period reshape ---")

records = []
for idx, row in df.iterrows():
    d = int(row["duration"])
    e = int(row["event_any"])
    for j in range(1, d + 1):
        records.append({
            "subject_id": idx,
            "interval": j,            # 1-indexed interval
            "interval_idx": j - 1,    # 0-indexed voor array indexing
            "event": int((j == d) and (e == 1)),
            "is_blue_ccs": row["is_blue_ccs"],
            "log_capacity_mw": row["log_capacity_mw"],
            "region": row["region"],
            "sponsor_type": row["sponsor_type"],
        })
pp = pd.DataFrame(records)
n_intervals = int(pp["interval_idx"].max() + 1)
print(f"  Persoon-periode rijen: {len(pp)}")
print(f"  Aantal intervals:      {n_intervals} (jaren)")
print(f"  Events in person-periode: {pp['event'].sum()} (moet {df['event_any'].sum()} zijn)")
assert pp["event"].sum() == df["event_any"].sum(), "Event count mismatch in reshape"


# ============================================================================
# DESIGN MATRIX
# ============================================================================
pp_region_dum = pd.get_dummies(pp["region"], prefix="region", drop_first=True).astype(float)
pp_sponsor_dum = pd.get_dummies(pp["sponsor_type"], prefix="sponsor", drop_first=True).astype(float)

X_blue = pp["is_blue_ccs"].values.astype(float)
X_capacity = pp["log_capacity_mw"].values.astype(float)
X_region = pp_region_dum.values
X_sponsor = pp_sponsor_dum.values
interval_idx = pp["interval_idx"].values.astype(int)
events_obs = pp["event"].values.astype(int)

n_region = X_region.shape[1]
n_sponsor = X_sponsor.shape[1]
print(f"  Region levels (excl. baseline): {n_region}")
print(f"  Sponsor levels (excl. baseline): {n_sponsor}")


# ============================================================================
# BAYESIAN FIT - één model per prior spec
# ============================================================================
def fit_bayesian(spec_name: str, spec: dict):
    print(f"\n--- Bayesian PCE met prior: {spec_name} ---")
    print(f"  Fitting (~{('1-3' if RUN_MODE=='quick' else '5-10')} min)...")

    with pm.Model() as model:
        # Baseline log-hazard per interval (regularizing prior)
        log_lambda = pm.Normal("log_lambda", mu=-3.0, sigma=2.0, shape=n_intervals)

        # Coefficienten met prior spec
        beta_blue = pm.Normal("beta_blue",
                              mu=spec["blue_ccs"]["mu"],
                              sigma=spec["blue_ccs"]["sigma"])
        beta_capacity = pm.Normal("beta_capacity",
                                  mu=spec["default"]["mu"],
                                  sigma=spec["default"]["sigma"])
        beta_region = pm.Normal("beta_region",
                                mu=spec["default"]["mu"],
                                sigma=spec["default"]["sigma"],
                                shape=n_region)
        beta_sponsor = pm.Normal("beta_sponsor",
                                 mu=spec["default"]["mu"],
                                 sigma=spec["default"]["sigma"],
                                 shape=n_sponsor)

        # Linear predictor: log-hazard = log_lambda_j + X_i'β
        eta = (log_lambda[interval_idx] +
               beta_blue * X_blue +
               beta_capacity * X_capacity +
               pt.dot(X_region, beta_region) +
               pt.dot(X_sponsor, beta_sponsor))

        # Poisson likelihood (exposure = 1 per interval)
        mu_event = pt.exp(eta)
        pm.Poisson("events", mu=mu_event, observed=events_obs)

        # Sample
        trace = pm.sample(
            draws=N_DRAWS,
            tune=N_TUNE,
            chains=N_CHAINS,
            target_accept=TARGET_ACCEPT,
            random_seed=RANDOM_SEED,
            progressbar=False,
            return_inferencedata=True,
        )

    # Summary voor beta_blue
    summary = az.summary(trace, var_names=["beta_blue"])
    beta_draws = trace.posterior["beta_blue"].values.flatten()
    hr_draws = np.exp(beta_draws)

    row = {
        "prior_spec": spec_name,
        "beta1_est": float(np.median(beta_draws)),
        "beta1_se": float(np.std(beta_draws)),
        "HR_med": float(np.median(hr_draws)),
        "HR_lo": float(np.quantile(hr_draws, 0.025)),
        "HR_hi": float(np.quantile(hr_draws, 0.975)),
        "rhat_max": float(summary["r_hat"].max()),
        "ess_min": float(summary["ess_bulk"].min()),
    }
    print(f"  Posterior median β1: {row['beta1_est']:.3f} (SD {row['beta1_se']:.3f})")
    print(f"  Posterior median HR: {row['HR_med']:.2f} (95% CrI [{row['HR_lo']:.2f}, {row['HR_hi']:.2f}])")
    print(f"  Diagnostics: max Rhat = {row['rhat_max']:.3f}, min ESS = {row['ess_min']:.0f}")
    return row, hr_draws, trace


# ============================================================================
# RUN ALLE PRIORS
# ============================================================================
freq_row = {
    "prior_spec": "Frequentist MLE",
    "beta1_est": beta_blue_freq,
    "beta1_se": se_blue_freq,
    "HR_med": hr_freq,
    "HR_lo": hr_lo_freq,
    "HR_hi": hr_hi_freq,
    "rhat_max": np.nan,
    "ess_min": np.nan,
}

rows = [freq_row]
hr_collection = {}

for spec_name, spec in PRIOR_SPECS.items():
    row, hr_draws, _trace = fit_bayesian(spec_name, spec)
    rows.append(row)
    hr_collection[spec_name] = hr_draws
    if spec_name == 'weakly_informative':
        trace_wi = _trace


# ============================================================================
# SAMENVATTINGSTABEL
# ============================================================================
header("SENSITIVITY GRID")
summary_df = pd.DataFrame(rows)
print(summary_df.round(3).to_string(index=False))

out_csv = RESULTS_DIR / "tables/posterior_summary.csv"
summary_df.to_csv(out_csv, index=False)
print(f"\nOpgeslagen: {out_csv.relative_to(EXT_ROOT)}")


# ============================================================================
# POSTERIOR HR PLOT
# ============================================================================
print("\n--- Posterior HR plot ---")
fig, ax = plt.subplots(figsize=(9, 5.5))
colors = {"vague": "#4477AA", "weakly_informative": "#EE6677",
          "skeptical": "#228833", "informative": "#CCBB44"}

for spec_name, draws in hr_collection.items():
    ax.hist(np.log(draws), bins=80, density=True, alpha=0.45,
            color=colors[spec_name], label=spec_name)

ax.axvline(np.log(hr_freq), linestyle="--", color="black", linewidth=1.5,
           label=f"Frequentist MLE (HR={hr_freq:.1f})")

ax.set_xlabel("log Hazard Ratio: Blue_CCS vs PEM")
ax.set_ylabel("Posterior density")
ax.set_title("Posterior distribution of Blue_CCS hazard ratio across 4 prior specifications")
ax.legend(loc="upper right", framealpha=0.9)
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(RESULTS_DIR / "figures/posterior_HR.pdf")
print(f"Opgeslagen: figures/posterior_HR.pdf")
plt.close(fig)


# ============================================================================
# TRACE PLOTS voor weakly_informative
# ============================================================================
print("\n--- Trace plots (weakly_informative) ---")
# Custom trace plot (ArviZ 1.x compat)
fig, axes = plt.subplots(2, 2, figsize=(11, 6))
for i, var in enumerate(["beta_blue", "beta_capacity"]):
    draws = trace_wi.posterior[var].values  # shape (chains, draws)
    for chain_idx in range(draws.shape[0]):
        axes[i, 0].plot(draws[chain_idx], alpha=0.7, lw=0.6, label=f"chain {chain_idx}")
    axes[i, 0].set_title(f"{var} - trace")
    axes[i, 0].set_xlabel("iteration")
    axes[i, 0].legend(fontsize=8)
    axes[i, 1].hist(draws.flatten(), bins=50, density=True, alpha=0.7, color="#4477AA")
    axes[i, 1].set_title(f"{var} - posterior density")
plt.tight_layout()
fig.savefig(RESULTS_DIR / "figures/trace_plots.pdf")
plt.close(fig)
print(f"Opgeslagen: figures/trace_plots.pdf")


# ============================================================================
# AFRONDEN
# ============================================================================
header("KLAAR")
print(f"Mode: {RUN_MODE}")
print(f"Resultaten in: {RESULTS_DIR}")
print("\nVolgende stappen:")
print("  1. Inspecteer posterior_summary.csv")
print("  2. Controleer Rhat < 1.01 en ESS > 400 in alle fits")
print("  3. Voor productie: set RUN_MODE = 'full' en re-run")
print("  4. Vergelijk weakly_informative HR met frequentist (~13.7)")
