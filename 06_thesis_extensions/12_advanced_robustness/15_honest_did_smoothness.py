"""
15_honest_did_smoothness.py — Honest DiD met SMOOTHNESS restricties.

Methode: Rambachan & Roth (2023), Review of Economic Studies 90(5):2555-2591.

Twee complementaire restriction classes:
  1. RELATIVE MAGNITUDES (M̄) — al gedaan, breakdown M̄=0 (zie honest_did_bounds.csv)
  2. SMOOTHNESS (M) — DEZE SCRIPT — beperkt tweede-orde changes in bias

Smoothness restriction:
  Δ_SM(M) = {δ : |δ_{t+1} - 2δ_t + δ_{t-1}| ≤ M voor alle t}
  
ONS GEVAL:
  Pre-period coefficients zijn observed, dus δ_pre = β̂_pre exact.
  Smoothness wordt opgelegd op transitions die post-period raken
  (t-1, t, of t+1 ≥ 0). Dit is de R&R 2023 implementatie waarin pre-period
  data observed is en alleen de continuatie van bias naar post-period
  bounded second differences moet hebben.
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linprog
from scipy.stats import norm

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")


def smoothness_post_only(beta, Sigma, rel_year, M, target_objective, alpha=0.05):
    """
    Honest DiD smoothness restriction met post-period anchoring.
    Pre-period δ vast gehouden op β̂_pre; smoothness alleen op post-touching transities.
    """
    all_times = sorted(set(rel_year.tolist() + [-1]))
    T = len(all_times)
    time_to_idx = {t:i for i,t in enumerate(all_times)}
    anchor_idx = time_to_idx[-1]
    
    c = np.zeros(T)
    if isinstance(target_objective, int):
        c[time_to_idx[rel_year[target_objective]]] = 1.0
    else:
        weight = 1.0/len(target_objective)
        for j in target_objective:
            c[time_to_idx[rel_year[j]]] = weight
    
    A_ub, b_ub = [], []
    for i in range(1, T-1):
        if max(all_times[i-1], all_times[i], all_times[i+1]) >= 0:
            row = np.zeros(T)
            row[i+1] = 1.0; row[i] = -2.0; row[i-1] = 1.0
            A_ub.append(row); b_ub.append(M)
            A_ub.append(-row); b_ub.append(M)
    
    A_eq = np.zeros((1, T)); A_eq[0, anchor_idx] = 1.0
    b_eq = np.array([0.0])
    for j, t in enumerate(rel_year):
        if t < 0:
            row = np.zeros(T); row[time_to_idx[t]] = 1.0
            A_eq = np.vstack([A_eq, row])
            b_eq = np.append(b_eq, beta[j])
    
    A_ub_arr = np.array(A_ub) if len(A_ub) > 0 else None
    b_ub_arr = np.array(b_ub) if A_ub is not None else None
    
    res_max = linprog(-c, A_ub=A_ub_arr, b_ub=b_ub_arr, A_eq=A_eq, b_eq=b_eq,
                       bounds=[(None,None)]*T, method='highs')
    res_min = linprog(c, A_ub=A_ub_arr, b_ub=b_ub_arr, A_eq=A_eq, b_eq=b_eq,
                       bounds=[(None,None)]*T, method='highs')
    
    delta_max = -res_max.fun if res_max.success else np.nan
    delta_min = res_min.fun if res_min.success else np.nan
    
    if isinstance(target_objective, int):
        beta_t = beta[target_objective]
        se_t = np.sqrt(Sigma[target_objective, target_objective])
    else:
        beta_t = np.mean(beta[target_objective])
        se_t = np.sqrt(np.sum(np.diag(Sigma)[target_objective])) / len(target_objective)
    
    z = norm.ppf(1-alpha/2)
    return {
        'M': M, 'delta_min': delta_min, 'delta_max': delta_max,
        'theta_lo_id': beta_t - delta_max, 'theta_hi_id': beta_t - delta_min,
        'ci_lo': beta_t - delta_max - z*se_t, 'ci_hi': beta_t - delta_min + z*se_t,
        'contains_zero': bool((beta_t - delta_max - z*se_t <= 0) and (beta_t - delta_min + z*se_t >= 0))
    }


def main():
    es = pd.read_csv(OUT/"results/event_study_pretrends.csv").sort_values('rel_year').reset_index(drop=True)
    es_use = es[es['rel_year']!=-1].copy()
    beta = es_use['beta'].values
    se = es_use['se'].values
    rel_year = es_use['rel_year'].values
    Sigma = np.diag(se**2)
    pre_idx = np.where(rel_year < 0)[0]
    post_idx = np.where(rel_year >= 0)[0]
    target_t0 = int(post_idx[0])
    
    M_grid = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0]
    
    print("=== PER-PERIOD (rel_year=0) ===")
    res_pp = []
    for M in M_grid:
        r = smoothness_post_only(beta, Sigma, rel_year, M, target_t0)
        res_pp.append(r)
        cz = '✓' if r['contains_zero'] else '✗'
        print(f"  M={M:5.2f}: Id [{r['theta_lo_id']:+.3f},{r['theta_hi_id']:+.3f}], "
               f"CI [{r['ci_lo']:+.3f},{r['ci_hi']:+.3f}], 0∈CI: {cz}")
    
    print("\n=== AVERAGE post effect ===")
    res_avg = []
    for M in M_grid:
        r = smoothness_post_only(beta, Sigma, rel_year, M, list(post_idx))
        res_avg.append(r)
        cz = '✓' if r['contains_zero'] else '✗'
        print(f"  M={M:5.2f}: Id [{r['theta_lo_id']:+.3f},{r['theta_hi_id']:+.3f}], "
               f"CI [{r['ci_lo']:+.3f},{r['ci_hi']:+.3f}], 0∈CI: {cz}")
    
    pp_df = pd.DataFrame(res_pp); avg_df = pd.DataFrame(res_avg)
    pp_df.to_csv(OUT/"results/honest_did_smoothness.csv", index=False)
    avg_df.to_csv(OUT/"results/honest_did_smoothness_avg.csv", index=False)
    
    bp_pp = pp_df[pp_df['contains_zero']]
    bp_avg = avg_df[avg_df['contains_zero']]
    breakdown_pp = float(bp_pp['M'].iloc[0]) if len(bp_pp)>0 else None
    breakdown_avg = float(bp_avg['M'].iloc[0]) if len(bp_avg)>0 else None
    
    print(f"\nBreakdown M per-period: {breakdown_pp}")
    print(f"Breakdown M average:    {breakdown_avg}")
    
    # Plot
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    for ax, df, title, color, bp, beta_show in [
        (axes[0], pp_df, 'Panel A: First post-period (rel_year=0)', '#882288', breakdown_pp, beta[target_t0]),
        (axes[1], avg_df, 'Panel B: Average post-treatment', '#2ca02c', breakdown_avg, np.mean(beta[post_idx])),
    ]:
        M_arr = df['M'].values
        ax.fill_between(M_arr, df['ci_lo'], df['ci_hi'], alpha=0.25, color=color, label='95% robust CI')
        ax.plot(M_arr, df['theta_lo_id'], '--', color=color, lw=1.5, label='Identified set')
        ax.plot(M_arr, df['theta_hi_id'], '--', color=color, lw=1.5)
        ax.axhline(0, color='black', ls=':', alpha=0.6)
        ax.axhline(beta_show, color='#1f77b4', ls='-', alpha=0.7, label=f'β̂={beta_show:+.2f}')
        if bp is not None:
            ax.axvline(bp, color='red', ls='--', alpha=0.6, label=f'Breakdown M={bp}')
        ax.set_xlabel('Smoothness parameter $M$')
        ax.set_ylabel(r'Identified set / 95% CI')
        ax.set_title(f"{title}\nBreakdown M = {bp}")
        ax.legend(fontsize=8, loc='best')
        ax.set_xlim(0, max(M_grid))
    
    plt.suptitle('Honest DiD: Smoothness restricties $\\Delta_{\\mathrm{SM}}(M)$ — Rambachan \\& Roth (2023)',
                  y=1.02, fontsize=12)
    plt.tight_layout()
    fig.savefig(OUT/"figures/F_honest_did_smoothness.pdf", bbox_inches='tight', dpi=120)
    plt.close()
    print(f"→ F_honest_did_smoothness.pdf")
    
    return breakdown_pp, breakdown_avg

if __name__ == "__main__":
    main()
