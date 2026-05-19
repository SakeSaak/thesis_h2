"""
12_synthetic_did.py — Synthetic Difference-in-Differences (Arkhangelsky et al, AER 2021).

Adresseert direct onze grootste methodologische zwakte: pre-trends violation
(F(6,152)=20.18, p<0.0001). SDID loosent de parallel-trends assumption door
SC-style unit weights + time weights te leren.

Methode (Arkhangelsky-Athey-Hirshberg-Imbens-Wager 2021, AER 111:4088-4118):
  1. Solve voor omega-weights: SC weights op control units, matchen pre-period
  2. Solve voor lambda-weights: time weights op pre-period, matchen control
  3. SDID estimator: doubly-weighted DiD met beide weight sets
  4. Inference: placebo permutation over control units

Panel setup voor onze data:
  Units = 7 regio's (Europe EU-27, North America, Asia-Pacific, Europe non-EU,
                       Latin America, Africa, Middle East)
  Time  = years 2010-2026
  Outcome = cancellation_rate in CBAM-exposed projecten per (region, year)
  Treatment = Europe EU-27 × post-2022
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
def hdr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)


# ============================================================================
# DATA SETUP — Region × Year panel
# ============================================================================
hdr("Setup Region × Year panel voor Synthetic DiD")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2014, 2025)].copy()  # Balanced window 2014-2025
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled','Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned','Partially commissioned']).astype(int)
sp['finished'] = sp['cancel_B'] + sp['operating']

def cbam_endex(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if any(k in dl for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']): return 1
    if 'chemical feedstock' in sl or 'refinery feedstock' in sl: return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)

# Keep CBAM-exposed finished projects (treated technology pool)
cbam = sp[(sp['cbam_endex']==1) & (sp['finished']==1)].copy()
print(f"CBAM-exposed finished projects: N = {len(cbam)}")
print(f"Region × Year coverage:")
print(cbam.groupby(['Region major','year_announced']).size().unstack(fill_value=0))

# Build panel: regio × year
panel = cbam.groupby(['Region major','year_announced']).agg(
    n_projects=('cancel_B','size'),
    n_cancelled=('cancel_B','sum'),
).reset_index()
panel['cancel_rate'] = panel['n_cancelled'] / panel['n_projects'].clip(lower=1)

# Pivot to wide format
Y_wide = panel.pivot(index='Region major', columns='year_announced', values='cancel_rate').fillna(0.0)
N_wide = panel.pivot(index='Region major', columns='year_announced', values='n_projects').fillna(0)

print(f"\nPanel shape: {Y_wide.shape}")
print(f"\nCancellation rate matrix (regions × years):")
print(Y_wide.round(3))
print(f"\nProject counts:")
print(N_wide.astype(int))

# Define treated unit and treatment time
TREATED_UNIT = 'Europe (EU-27)'
TREATMENT_YEAR = 2022

units = list(Y_wide.index)
years = list(Y_wide.columns)
T0 = years.index(TREATMENT_YEAR)  # last pre-treatment period index
treated_idx = units.index(TREATED_UNIT)
control_idx = [i for i in range(len(units)) if i != treated_idx]

print(f"\nTreated unit: {TREATED_UNIT} (idx {treated_idx})")
print(f"Treatment year: {TREATMENT_YEAR} (T0 = {T0})")
print(f"Pre-period: years {years[:T0]} ({T0} periods)")
print(f"Post-period: years {years[T0:]} ({len(years)-T0} periods)")
print(f"Control units: {[units[i] for i in control_idx]}")


# ============================================================================
# SYNTHETIC DiD ESTIMATOR
# ============================================================================
hdr("Implementeer Synthetic DiD (Arkhangelsky et al 2021 AER)")

Y = Y_wide.values  # shape (N, T)
N, T = Y.shape
T_post = T - T0
N_co = len(control_idx)

# Step 1: Compute zeta — regularization parameter (Eq 3.7 in AER paper)
# zeta = (N_co * T_post)^(1/4) * sigma where sigma = std of pre-period first differences
delta_Y_co = np.diff(Y[control_idx, :T0], axis=1)  # control units, pre-period differences
sigma_hat = float(np.std(delta_Y_co))
zeta = ((N_co * T_post) ** (1/4)) * sigma_hat
print(f"Regularization zeta = {zeta:.6f} (sigma_hat = {sigma_hat:.4f})")

# Step 2: Solve for omega-weights (unit weights, SC-style)
# minimize ||Y_co_pre * omega + omega_0 - Y_tr_pre||^2 + zeta^2 * T0 * ||omega||^2
# subject to omega >= 0, sum(omega) = 1
def solve_omega(Y_pre_co, Y_pre_tr, zeta_val, T0_val):
    """Solve for SC-style unit weights with intercept omega_0."""
    n_co = Y_pre_co.shape[0]
    
    def obj(params):
        omega = params[:-1]
        omega_0 = params[-1]
        residual = Y_pre_co.T @ omega + omega_0 - Y_pre_tr
        loss = np.sum(residual ** 2) + (zeta_val ** 2) * T0_val * np.sum(omega ** 2)
        return loss
    
    # Initial guess: equal weights
    x0 = np.concatenate([np.ones(n_co)/n_co, [0.0]])
    
    # Constraints: omega >= 0, sum(omega) = 1
    cons = [{'type':'eq', 'fun': lambda x: np.sum(x[:-1]) - 1.0}]
    bnds = [(0.0, 1.0)] * n_co + [(-1.0, 1.0)]
    
    res = minimize(obj, x0, method='SLSQP', bounds=bnds, constraints=cons,
                    options={'maxiter':500, 'ftol':1e-12})
    return res.x[:-1], res.x[-1]

Y_pre_co = Y[control_idx, :T0]      # shape (N_co, T0)
Y_pre_tr = Y[treated_idx, :T0]       # shape (T0,)

omega, omega_0 = solve_omega(Y_pre_co, Y_pre_tr, zeta, T0)
print(f"\nUnit weights (omega):")
for i, ctrl in enumerate(control_idx):
    print(f"  {units[ctrl]:<25s}: {omega[i]:.4f}")
print(f"  Intercept omega_0: {omega_0:.4f}")
print(f"  Sum omega: {omega.sum():.4f}")

# Step 3: Solve for lambda-weights (time weights)
# minimize ||Y_co_pre^T * lambda + lambda_0 - Y_co_post_mean||^2
# subject to lambda >= 0, sum(lambda) = 1
def solve_lambda(Y_pre_co, Y_post_co_mean, T0_val):
    """Solve for time weights on pre-period."""
    def obj(params):
        lam = params[:-1]
        lam_0 = params[-1]
        residual = Y_pre_co @ lam + lam_0 - Y_post_co_mean
        loss = np.sum(residual ** 2)
        return loss
    
    x0 = np.concatenate([np.ones(T0_val)/T0_val, [0.0]])
    cons = [{'type':'eq', 'fun': lambda x: np.sum(x[:-1]) - 1.0}]
    bnds = [(0.0, 1.0)] * T0_val + [(-1.0, 1.0)]
    
    res = minimize(obj, x0, method='SLSQP', bounds=bnds, constraints=cons,
                    options={'maxiter':500, 'ftol':1e-12})
    return res.x[:-1], res.x[-1]

Y_post_co_mean = np.mean(Y[control_idx, T0:], axis=1)  # average post per control unit (N_co,)
lambda_w, lambda_0 = solve_lambda(Y_pre_co, Y_post_co_mean, T0)
print(f"\nTime weights (lambda):")
for t in range(T0):
    print(f"  Year {years[t]}: {lambda_w[t]:.4f}")
print(f"  Sum lambda: {lambda_w.sum():.4f}")

# Step 4: Compute SDID estimator
# tau_sdid = mean(Y[tr, post]) - mean(Y[tr, pre] * lambda) - sum(omega * (Y[co, post]_mean - Y[co, pre] * lambda))
mean_tr_post = np.mean(Y[treated_idx, T0:])
mean_tr_pre_weighted = np.sum(Y[treated_idx, :T0] * lambda_w)

# Control adjustment
Y_co_post_mean = np.mean(Y[control_idx, T0:], axis=1)  # (N_co,)
Y_co_pre_weighted = Y[control_idx, :T0] @ lambda_w     # (N_co,)
control_adj = np.sum(omega * (Y_co_post_mean - Y_co_pre_weighted))

tau_sdid = (mean_tr_post - mean_tr_pre_weighted) - control_adj
print(f"\nSDID estimate:")
print(f"  Treated post mean:                {mean_tr_post:.4f}")
print(f"  Treated pre (lambda-weighted):    {mean_tr_pre_weighted:.4f}")
print(f"  Control adjustment:               {control_adj:.4f}")
print(f"  τ_SDID = {tau_sdid:+.4f}")

# Compare with naive DiD
tau_naive = (np.mean(Y[treated_idx, T0:]) - np.mean(Y[treated_idx, :T0])) - \
             (np.mean(Y[control_idx, T0:]) - np.mean(Y[control_idx, :T0]))
print(f"  τ_naive_DiD = {tau_naive:+.4f}")
print(f"  Difference SDID vs naive: {tau_sdid - tau_naive:+.4f}")


# ============================================================================
# INFERENCE — Placebo permutation
# ============================================================================
hdr("Inference via placebo permutation (treat each control as 'fake treated')")

placebo_taus = []
for fake_treated in control_idx:
    fake_control = [i for i in range(N) if i != fake_treated]
    Y_pre_fco = Y[fake_control, :T0]
    Y_pre_ftr = Y[fake_treated, :T0]
    try:
        om_p, om0_p = solve_omega(Y_pre_fco, Y_pre_ftr, zeta, T0)
        Y_post_fco_mean = np.mean(Y[fake_control, T0:], axis=1)
        la_p, la0_p = solve_lambda(Y_pre_fco, Y_post_fco_mean, T0)
        
        mean_ftr_post = np.mean(Y[fake_treated, T0:])
        mean_ftr_pre_w = np.sum(Y[fake_treated, :T0] * la_p)
        Y_fco_post_mean = np.mean(Y[fake_control, T0:], axis=1)
        Y_fco_pre_w = Y[fake_control, :T0] @ la_p
        ctrl_adj = np.sum(om_p * (Y_fco_post_mean - Y_fco_pre_w))
        
        tau_placebo = (mean_ftr_post - mean_ftr_pre_w) - ctrl_adj
        placebo_taus.append(tau_placebo)
        print(f"  Placebo treated = {units[fake_treated]:<25s}: τ = {tau_placebo:+.4f}")
    except Exception as e:
        print(f"  Placebo {units[fake_treated]} failed: {e}")

placebo_taus = np.array(placebo_taus)
placebo_sd = float(np.std(placebo_taus))
placebo_se = placebo_sd / np.sqrt(len(placebo_taus))

# Two-sided p-value via permutation
abs_tau_sdid = abs(tau_sdid)
abs_placebos = np.abs(placebo_taus)
p_perm = float(np.mean(abs_placebos >= abs_tau_sdid))

print(f"\nPlacebo permutation inference:")
print(f"  Observed τ_SDID:        {tau_sdid:+.4f}")
print(f"  Placebo SD:             {placebo_sd:.4f}")
print(f"  Permutation p-value:    {p_perm:.4f}")
print(f"  Two-sided 90% CI:       [{tau_sdid - 1.645*placebo_sd:+.4f}, {tau_sdid + 1.645*placebo_sd:+.4f}]")


# ============================================================================
# PLOT
# ============================================================================
hdr("Generate SDID plot")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Treated vs synthetic control over time
ax = axes[0]
Y_synthetic = Y[control_idx, :].T @ omega + omega_0  # synthetic time series
ax.plot(years, Y[treated_idx, :], 'o-', color='#882288', lw=2, markersize=8,
         label=f'Treated ({TREATED_UNIT})')
ax.plot(years, Y_synthetic, 's--', color='#1f77b4', lw=2, markersize=7,
         label='Synthetic control')
ax.axvline(TREATMENT_YEAR - 0.5, ls='--', color='red', alpha=0.6, label=f'CBAM ({TREATMENT_YEAR})')
ax.fill_between([TREATMENT_YEAR - 0.5, max(years) + 0.5], 0, 1, alpha=0.1, color='red')
ax.set_xlabel('Year')
ax.set_ylabel('Cancellation rate in CBAM-exposed projects')
ax.set_title(f'Panel A: Treated vs Synthetic Control\nτ_SDID = {tau_sdid:+.3f}, perm p = {p_perm:.3f}')
ax.legend(fontsize=9)
ax.set_ylim(-0.05, 1.05)

# Plot 2: Placebo distribution
ax = axes[1]
ax.hist(placebo_taus, bins=10, color='#1f77b4', alpha=0.6, edgecolor='black',
         label='Placebo τ distribution')
ax.axvline(tau_sdid, color='#882288', lw=2.5, label=f'Observed τ_SDID = {tau_sdid:+.3f}')
ax.axvline(0, ls=':', color='black', alpha=0.5)
ax.set_xlabel('τ (SDID estimate)')
ax.set_ylabel('Frequency')
ax.set_title(f'Panel B: Placebo inference\nPermutation p = {p_perm:.3f}')
ax.legend(fontsize=9)

plt.suptitle('Synthetic Difference-in-Differences: EU CBAM-end-use projects vs synthetic control',
              y=1.00, fontsize=12)
plt.tight_layout()
fig.savefig(OUT / "figures/F_synthetic_did.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_synthetic_did.pdf")


# ============================================================================
# SUMMARY
# ============================================================================
hdr("EINDSAMENVATTING — SDID")

# Save results
result_df = pd.DataFrame([{
    'tau_sdid': tau_sdid,
    'tau_naive_did': tau_naive,
    'difference': tau_sdid - tau_naive,
    'placebo_sd': placebo_sd,
    'permutation_p': p_perm,
    'n_units': N,
    'n_control': N_co,
    'T0_pre': T0,
    'T_post': T_post,
    'zeta': zeta,
}])
result_df.to_csv(OUT / "results/sdid_summary.csv", index=False)

weights_df = pd.DataFrame({
    'unit': [units[i] for i in control_idx],
    'omega': omega,
}).sort_values('omega', ascending=False)
weights_df.to_csv(OUT / "results/sdid_omega_weights.csv", index=False)

print(f"""
Synthetic DiD vs onze conventional DiD:
  τ_SDID:     {tau_sdid:+.4f}  (placebo p = {p_perm:.3f})
  τ_naive_DiD: {tau_naive:+.4f}
  Verschil:   {tau_sdid - tau_naive:+.4f}

Verdict:
  {'✓ SDID significant' if p_perm < 0.10 else '⚠ SDID null'}
  Pre-trends violation in onze conventional DiD wordt door SDID's omega/lambda
  weights gemodelleerd — synthetic control matcht het pre-CBAM EU pattern
  via een gewogen combinatie van non-EU regions.

Belangrijkste insight: na controle voor pre-CBAM verschillen in cancellation
rates, {'IS' if abs(tau_sdid) > 0.05 and p_perm < 0.10 else 'IS GEEN'} er een statistisch detecteerbaar
post-CBAM differentieel effect.
""")
