"""
17_stochastic_volatility.py — Score-Driven Stochastic Volatility op β_int(t).

METHODE: GAS-vol model (Creal-Koopman-Lucas 2013, JoAE 28:777-795).
  Extension van onze Chapter 6 GAS-TVP: niet alleen de MEAN β_int(t) is
  tijds-variërend, maar ook de VARIANCE σ²(t).

MOTIVATION (uit script 14 — Conditional Score Residuals):
  CSR diagnostic toonde heteroskedasticiteit pre/post-2018 (F=328, p<0.001).
  Onze huidige TVP behandelt dit als data-feature; SV-extension modelleert
  het expliciet als tijdsvariërend proces.

MODEL SPEC:
  y_t = score residual op tijd t [uit script 14 output]
  log σ²_{t+1} = ψ + λ·(log σ²_t - ψ) + α_h · s_{h,t}
  s_{h,t} = ½(y_t²/σ²_t - 1)  [Gaussian score for log-variance]

PARAMETERS:
  ψ: long-run log-variance (mean reversion target)
  λ: persistence (close to 1 = slow movement in volatility)
  α_h: response to volatility-score (how strongly σ² adjusts to data)

VERGELIJKING:
  H0 (constant variance): λ=0, α_h=0 (alleen ψ vrij)
  H1 (SV): alle drie parameters vrij
  Test via likelihood ratio (asymptotic χ²_2 onder H0)
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import chi2, norm

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
def hdr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)


# ============================================================================
# STEP 1 — Load score residuals from Chapter 6 GAS-TVP fit
# ============================================================================
hdr("Step 1: Load score residuals from Chapter 6 GAS-TVP fit")

scores = pd.read_csv(OUT / "results/csr_score_residuals.csv")
scores = scores.sort_values('year').reset_index(drop=True)
print(f"Score residuals: {len(scores)} jaarpunten ({scores['year'].min()}-{scores['year'].max()})")
print(scores[['year','y_blue','n_blue','p_blue_t','score_blue','score_blue_std']].round(4).to_string(index=False))

# Use standardized score residuals voor SV analysis
y = scores['score_blue_std'].values
T = len(y)
years = scores['year'].values
print(f"\nScore residuals stats: mean={y.mean():+.4f}, std={y.std():.4f}, "
       f"range=[{y.min():+.4f}, {y.max():+.4f}]")


# ============================================================================
# STEP 2 — Define log-likelihoods for two models
# ============================================================================
hdr("Step 2: Specify two models")

def filter_gas_vol(params, y, return_paths=False):
    """
    Score-Driven Stochastic Volatility filter (GAS-vol).
    
    Params: (psi, lambda, alpha_h)
      psi: long-run log-variance
      lambda: persistence
      alpha_h: score response
    """
    psi, lam, alpha_h = params
    T = len(y)
    log_sig2 = np.zeros(T)
    log_lik = 0.0
    
    # Initialize log σ²_1 = ψ
    log_sig2[0] = psi
    
    for t in range(T):
        sig2_t = np.exp(log_sig2[t])
        sig2_t = max(sig2_t, 1e-8)  # numerical floor
        # Log-likelihood contribution
        log_lik += -0.5 * (np.log(2*np.pi*sig2_t) + y[t]**2 / sig2_t)
        # Update log σ² for t+1 via GAS recursion
        if t < T - 1:
            # Score s_h,t for log σ²: ½(y_t²/σ²_t - 1)
            s_h = 0.5 * (y[t]**2 / sig2_t - 1.0)
            log_sig2[t+1] = psi + lam * (log_sig2[t] - psi) + alpha_h * s_h
    
    if return_paths:
        return log_lik, log_sig2
    return log_lik

def neg_loglik_gas_vol(params, y):
    """Negative log-likelihood for minimization."""
    psi, lam, alpha_h = params
    if abs(lam) > 0.99 or abs(alpha_h) > 5.0:
        return 1e10
    try:
        ll = filter_gas_vol(params, y)
        if not np.isfinite(ll):
            return 1e10
        return -ll
    except (OverflowError, ValueError):
        return 1e10

def neg_loglik_constant(psi, y):
    """Negative log-likelihood under constant-variance H0."""
    sig2 = np.exp(psi)
    sig2 = max(sig2, 1e-8)
    return 0.5 * np.sum(np.log(2*np.pi*sig2) + y**2/sig2)


# ============================================================================
# STEP 3 — Estimate H0 (constant variance) and H1 (GAS-vol)
# ============================================================================
hdr("Step 3: Fit both models")

# H0: constant variance
res_h0 = minimize(lambda p: neg_loglik_constant(p[0], y), x0=[np.log(np.var(y))],
                    method='Nelder-Mead', options={'xatol':1e-8, 'fatol':1e-10})
psi_h0 = res_h0.x[0]
ll_h0 = -res_h0.fun
print(f"H0 (constant variance):")
print(f"  ψ = {psi_h0:.4f}  →  σ² = {np.exp(psi_h0):.4f}, σ = {np.sqrt(np.exp(psi_h0)):.4f}")
print(f"  Log-likelihood = {ll_h0:.4f}")
print(f"  k = 1 parameter")

# H1: GAS-vol — multiple starting points
best_ll, best_params = -np.inf, None
starting_points = [
    [np.log(np.var(y)), 0.5, 0.1],
    [np.log(np.var(y)), 0.8, 0.05],
    [np.log(np.var(y)), 0.3, 0.2],
    [0.0, 0.9, 0.1],
    [psi_h0, 0.0, 0.0],  # near H0
]
for sp in starting_points:
    res = minimize(neg_loglik_gas_vol, x0=sp, args=(y,),
                    method='Nelder-Mead', options={'xatol':1e-8, 'fatol':1e-10, 'maxiter': 5000})
    if -res.fun > best_ll:
        best_ll = -res.fun
        best_params = res.x

psi_h1, lam_h1, alpha_h1 = best_params
ll_h1 = best_ll
print(f"\nH1 (GAS-vol):")
print(f"  ψ       = {psi_h1:+.4f}  (long-run log-variance)")
print(f"  λ       = {lam_h1:+.4f}  (persistence)")
print(f"  α_h     = {alpha_h1:+.4f}  (score response)")
print(f"  Log-likelihood = {ll_h1:.4f}")
print(f"  k = 3 parameters")


# ============================================================================
# STEP 4 — Likelihood Ratio Test
# ============================================================================
hdr("Step 4: Likelihood ratio test H0 vs H1")

lr_stat = 2 * (ll_h1 - ll_h0)
p_lr = 1 - chi2.cdf(lr_stat, df=2)
print(f"LR statistic = 2(ℓ_1 - ℓ_0) = {lr_stat:.4f}")
print(f"χ²_2 critical value at α=0.05: {chi2.ppf(0.95, df=2):.4f}")
print(f"p-value = {p_lr:.4f}")
print(f"Verdict: {'⚠ REJECT H0 — SV significantly better' if p_lr < 0.05 else '✓ FAIL TO REJECT — constant variance acceptable'}")

# AIC / BIC comparison
aic_h0 = 2*1 - 2*ll_h0
aic_h1 = 2*3 - 2*ll_h1
bic_h0 = 1*np.log(T) - 2*ll_h0
bic_h1 = 3*np.log(T) - 2*ll_h1
print(f"\nAIC: H0 = {aic_h0:.3f}, H1 = {aic_h1:.3f} → {'H1 favoured' if aic_h1 < aic_h0 else 'H0 favoured'}")
print(f"BIC: H0 = {bic_h0:.3f}, H1 = {bic_h1:.3f} → {'H1 favoured' if bic_h1 < bic_h0 else 'H0 favoured'}")


# ============================================================================
# STEP 5 — Extract filtered volatility path
# ============================================================================
hdr("Step 5: Filtered volatility trajectory")

ll_check, log_sig2_path = filter_gas_vol(best_params, y, return_paths=True)
sigma_path = np.sqrt(np.exp(log_sig2_path))

# Compute annualised vol equivalent
vol_table = pd.DataFrame({
    'year': years,
    'score_residual': y,
    'log_sig2_t': log_sig2_path,
    'sigma_t': sigma_path,
    'sigma_t_pct': sigma_path / np.sqrt(np.exp(psi_h0)) * 100,  # relative to constant-var baseline
})
print("Filtered volatility trajectory:")
print(vol_table.round(4).to_string(index=False))

vol_table.to_csv(OUT / "results/sv_volatility_path.csv", index=False)


# ============================================================================
# STEP 6 — Connection to GAS-TVP from Chapter 6
# ============================================================================
hdr("Step 6: Compare uncertainty in β_int(t) with vs without SV")

# Onze Chapter 6 GAS posterior gives SD per year. If SV is true,
# the implied uncertainty band on β_int(t) should be wider in high-vol periods.
# Let's overlay onto GAS trajectory.
gas = pd.read_csv("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/05_state_space_tvp/results_gas/gas_trajectory.csv")

# Match years
common_yrs = sorted(set(gas['year']).intersection(set(years)))
print(f"Common years: {len(common_yrs)} ({common_yrs[0]}-{common_yrs[-1]})")

gas_match = gas[gas['year'].isin(common_yrs)].set_index('year')
sv_match = vol_table[vol_table['year'].isin(common_yrs)].set_index('year')

# Compare: gas posterior SD vs SV-filtered sigma
compare_df = pd.DataFrame({
    'year': common_yrs,
    'beta_int_t': gas_match.loc[common_yrs, 'median'].values,
    'gas_posterior_sd': gas_match.loc[common_yrs, 'sd'].values,
    'sv_filtered_sigma': sv_match.loc[common_yrs, 'sigma_t'].values,
    'sv_relative_vol': sv_match.loc[common_yrs, 'sigma_t_pct'].values,
})
print("\nComparison: GAS posterior uncertainty vs SV-filtered volatility:")
print(compare_df.round(4).to_string(index=False))
compare_df.to_csv(OUT / "results/sv_comparison_with_gas.csv", index=False)

# Correlation between two uncertainty proxies
corr = np.corrcoef(compare_df['gas_posterior_sd'], compare_df['sv_filtered_sigma'])[0,1]
print(f"\nCorrelation: GAS posterior SD vs SV-filtered σ_t = {corr:+.4f}")


# ============================================================================
# STEP 7 — Plot
# ============================================================================
hdr("Step 7: Plot")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(2, 2, figsize=(14, 9))

# Panel A: Score residuals over time
ax = axes[0,0]
ax.plot(years, y, 'o-', color='#1f77b4', markersize=8, lw=1.5)
ax.axhline(0, ls='--', color='black', alpha=0.5)
ax.set_xlabel('Year')
ax.set_ylabel('Standardized score residual $s_t$')
ax.set_title('Panel A: Score residuals from Chapter 6 GAS-TVP fit\n(input to SV analysis)')

# Panel B: Filtered log σ²(t) — SV path
ax = axes[0,1]
ax.plot(years, log_sig2_path, 'o-', color='#882288', markersize=8, lw=1.5,
         label=f'GAS-vol filtered (ψ={psi_h1:.2f}, λ={lam_h1:.2f}, α_h={alpha_h1:.2f})')
ax.axhline(psi_h0, ls='--', color='black', alpha=0.5, label=f'Constant baseline ψ_0 = {psi_h0:.2f}')
ax.set_xlabel('Year')
ax.set_ylabel(r'Filtered $\log\sigma^2_t$')
ax.set_title(f'Panel B: Filtered log-variance path\nLR = {lr_stat:.2f}, p = {p_lr:.3f}')
ax.legend(fontsize=8)

# Panel C: σ_t relative to constant baseline (volatility ratio)
ax = axes[1,0]
ax.fill_between(years, 0, sigma_path / np.sqrt(np.exp(psi_h0)), alpha=0.3, color='#2ca02c',
                  label='SV / constant ratio')
ax.plot(years, sigma_path / np.sqrt(np.exp(psi_h0)), 'o-', color='#2ca02c', markersize=8, lw=1.5)
ax.axhline(1.0, ls='--', color='black', alpha=0.5, label='Constant variance reference')
ax.set_xlabel('Year')
ax.set_ylabel(r'$\sigma_t / \sigma_{const}$')
ax.set_title('Panel C: Volatility ratio over time\n(>1 = above constant-var level)')
ax.legend(fontsize=8)

# Panel D: GAS posterior SD vs SV filtered σ
ax = axes[1,1]
ax_twin = ax.twinx()
ax.plot(compare_df['year'], compare_df['gas_posterior_sd'], 'o-', color='#882288',
         markersize=8, lw=1.5, label='GAS posterior SD (Chapter 6)')
ax_twin.plot(compare_df['year'], compare_df['sv_filtered_sigma'], 's-', color='#ff7f0e',
              markersize=8, lw=1.5, label=f'SV-filtered σ_t (corr={corr:+.2f})')
ax.set_xlabel('Year')
ax.set_ylabel('GAS posterior SD', color='#882288')
ax_twin.set_ylabel('SV-filtered σ_t', color='#ff7f0e')
ax.set_title(f'Panel D: GAS uncertainty vs SV vol (corr = {corr:+.3f})')
ax.legend(loc='upper left', fontsize=8)
ax_twin.legend(loc='upper right', fontsize=8)

plt.suptitle('Score-Driven Stochastic Volatility on Chapter 6 GAS-TVP residuals\n'
              '(Creal-Koopman-Lucas 2013 framework)', y=1.00, fontsize=12)
plt.tight_layout()
fig.savefig(OUT / "figures/F_stochastic_volatility.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_stochastic_volatility.pdf")


# ============================================================================
# STEP 8 — Save summary
# ============================================================================
hdr("Step 8: Save summary + verdict")

summary = pd.DataFrame([{
    'T': T,
    'psi_h0': psi_h0,
    'sigma2_h0': float(np.exp(psi_h0)),
    'loglik_h0': ll_h0,
    'aic_h0': aic_h0,
    'bic_h0': bic_h0,
    'psi_h1': psi_h1,
    'lambda_h1': lam_h1,
    'alpha_h_h1': alpha_h1,
    'loglik_h1': ll_h1,
    'aic_h1': aic_h1,
    'bic_h1': bic_h1,
    'lr_stat': lr_stat,
    'lr_p_value': p_lr,
    'sv_significant': bool(p_lr < 0.05),
    'corr_gas_sd_vs_sv_sigma': corr,
}])
summary.to_csv(OUT / "results/sv_summary.csv", index=False)

verdict = ('SV significantly improves fit' if p_lr < 0.05 else
            'Constant variance not significantly worse than SV')

print(f"""
EINDSAMENVATTING — Score-Driven Stochastic Volatility:

H0 (constant variance):  ψ = {psi_h0:+.3f}, σ² = {np.exp(psi_h0):.3f}
                          log-lik = {ll_h0:.3f}, k=1, AIC = {aic_h0:.3f}

H1 (GAS-vol):            ψ = {psi_h1:+.3f}, λ = {lam_h1:+.3f}, α_h = {alpha_h1:+.3f}
                          log-lik = {ll_h1:.3f}, k=3, AIC = {aic_h1:.3f}

LR test:                 χ²_2 = {lr_stat:.3f}, p = {p_lr:.4f}
Verdict:                 {verdict}

GAS-vol filtered trajectory:
  Min vol year:  {years[np.argmin(sigma_path)]} (σ = {sigma_path.min():.3f})
  Max vol year:  {years[np.argmax(sigma_path)]} (σ = {sigma_path.max():.3f})
  Range:         {sigma_path.max()/max(sigma_path.min(),1e-3):.1f}x

Correlation met GAS posterior SD: {corr:+.4f}
  → {'SV-volatility aligns with GAS Bayesian uncertainty' if abs(corr) > 0.3 else 'SV-vol en GAS-SD vangen verschillende aspecten op'}

OUTPUT:
  - results/sv_summary.csv
  - results/sv_volatility_path.csv
  - results/sv_comparison_with_gas.csv
  - figures/F_stochastic_volatility.pdf
""")
