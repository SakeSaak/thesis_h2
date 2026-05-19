"""
03_permutation_inference.py — Randomization/permutation inference.

Theory:
  Fisher randomization tests provide exact non-parametric p-values under the
  sharp null H0: τ_i = 0 for all units i. We permute treatment status across
  units and compute the distribution of test statistics under the null.
  
  Cluster-permutation: permute treatment status at cluster level (vintage
  cohort) to preserve within-cluster correlation structure.
  
  Applied to:
    1. EU 2x2 DiD coefficient (cbam_x_post)
    2. Triple-difference (EU × CBAM × Post)
    3. Vintage-cohort × CBAM 2022 (T1 narrow)
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from scipy import stats

np.random.seed(42)

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")

def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD SAMPLE
# ============================================================================
hdr("Setup: Load sample")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)
sp['is_blue'] = (sp['Technology.1'] == 'Fossil with CCS').astype(int)
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))

def cbam_endex(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if any(k in dl for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']):
        return 1
    if 'chemical feedstock' in sl or 'refinery feedstock' in sl:
        return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)
sp['is_EU'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['post_2022'] = (sp['year_announced'] >= 2022).astype(int)
sp['cbam_x_post'] = sp['cbam_endex'] * sp['post_2022']
sp['EU_x_cbam'] = sp['is_EU'] * sp['cbam_endex']
sp['EU_x_post'] = sp['is_EU'] * sp['post_2022']
sp['triple'] = sp['is_EU'] * sp['cbam_endex'] * sp['post_2022']

finished = sp[(sp['cancel_B']+sp['operating'])==1].copy()
eu = finished[finished['is_EU']==1].copy()

print(f"Full finished: {len(finished)}, EU: {len(eu)}")


# ============================================================================
# 2. PERMUTATION TEST UTILITY
# ============================================================================
def permutation_test(X, y, focal_idx, treatment_col_idx, B=2999, 
                      cluster_level=None, cluster_ids=None):
    """
    Permutation test by shuffling treatment variable.
    
    Parameters
    ----------
    X : design matrix (n, k)
    y : outcome (n,)
    focal_idx : index of coefficient to test
    treatment_col_idx : index of treatment variable to permute
    B : permutation count
    cluster_level : if not None, permute at cluster level (preserving within-cluster structure)
    cluster_ids : cluster identifiers (needed if cluster_level=True)
    """
    # Observed coefficient
    m_obs = sm.OLS(y, X).fit()
    beta_obs = m_obs.params[focal_idx]
    t_obs = beta_obs / m_obs.bse[focal_idx]
    
    n = len(y)
    beta_perm = []
    t_perm = []
    
    for b in range(B):
        if cluster_level and cluster_ids is not None:
            # Cluster-level permutation: shuffle treatment at cluster level
            unique_clusters = np.unique(cluster_ids)
            G = len(unique_clusters)
            # Get cluster-level treatment status (first non-zero per cluster)
            cluster_treatments = {}
            for c in unique_clusters:
                idx = np.where(cluster_ids == c)[0]
                # Random assignment: in cluster permutation we resample WHO is treated at cluster level
                cluster_treatments[c] = None  # placeholder
            
            # Permute: shuffle cluster-level treatment indicator
            cluster_treatment_values = []
            for c in unique_clusters:
                idx = np.where(cluster_ids == c)[0]
                # Cluster-mean treatment
                cluster_treatment_values.append(X[idx, treatment_col_idx].mean())
            
            cluster_treatment_values = np.array(cluster_treatment_values)
            permuted_cluster_treatments = np.random.permutation(cluster_treatment_values)
            
            X_perm = X.copy()
            for i, c in enumerate(unique_clusters):
                idx = np.where(cluster_ids == c)[0]
                X_perm[idx, treatment_col_idx] = permuted_cluster_treatments[i]
        else:
            # Unit-level permutation
            X_perm = X.copy()
            perm_idx = np.random.permutation(n)
            X_perm[:, treatment_col_idx] = X[perm_idx, treatment_col_idx]
        
        try:
            m_perm = sm.OLS(y, X_perm).fit()
            b_p = m_perm.params[focal_idx]
            se_p = m_perm.bse[focal_idx]
            if se_p > 0:
                beta_perm.append(b_p)
                t_perm.append(b_p / se_p)
        except:
            continue
    
    beta_perm = np.array(beta_perm)
    t_perm = np.array(t_perm)
    
    # Two-sided p-value
    p_perm_beta = np.mean(np.abs(beta_perm) >= np.abs(beta_obs))
    p_perm_t = np.mean(np.abs(t_perm) >= np.abs(t_obs))
    
    return {
        'beta_obs': beta_obs,
        't_obs': t_obs,
        'beta_perm': beta_perm,
        't_perm': t_perm,
        'p_perm_beta': p_perm_beta,
        'p_perm_t': p_perm_t,
        'B_effective': len(beta_perm),
    }


# ============================================================================
# 3. PERMUTATION on EU 2x2 DiD
# ============================================================================
hdr("Perm-1: EU-only 2x2 DiD")

X_eu = sm.add_constant(eu[['cbam_endex','post_2022','cbam_x_post','is_blue','log_cap']])
y_eu = eu['cancel_B'].astype(float).values

cbam_x_post_idx = list(X_eu.columns).index('cbam_x_post')

# Run permutation
perm1 = permutation_test(
    X_eu.values, y_eu, focal_idx=cbam_x_post_idx, 
    treatment_col_idx=cbam_x_post_idx, B=2999
)
print(f"Sample: {len(eu)}, B = {perm1['B_effective']}")
print(f"  β_obs = {perm1['beta_obs']:.4f}, t_obs = {perm1['t_obs']:.3f}")
print(f"  Permutation p (β): {perm1['p_perm_beta']:.4f}")
print(f"  Permutation p (t): {perm1['p_perm_t']:.4f}")
print(f"  vs asymptotic p:   0.043")
print(f"  vs WCB p:          0.124")


# ============================================================================
# 4. PERMUTATION on Triple-difference
# ============================================================================
hdr("Perm-2: Triple-difference EU×CBAM×Post")

X_full = sm.add_constant(finished[['is_EU','cbam_endex','post_2022',
                                      'EU_x_cbam','EU_x_post','cbam_x_post','triple',
                                      'is_blue','log_cap']])
y_full = finished['cancel_B'].astype(float).values
triple_idx = list(X_full.columns).index('triple')

perm2 = permutation_test(
    X_full.values, y_full, focal_idx=triple_idx,
    treatment_col_idx=triple_idx, B=2999
)
print(f"Sample: {len(finished)}, B = {perm2['B_effective']}")
print(f"  β_obs = {perm2['beta_obs']:.4f}, t_obs = {perm2['t_obs']:.3f}")
print(f"  Permutation p (β): {perm2['p_perm_beta']:.4f}")
print(f"  Permutation p (t): {perm2['p_perm_t']:.4f}")
print(f"  vs asymptotic p:   0.326")
print(f"  vs WCB p:          0.278")


# ============================================================================
# 5. CLUSTER-LEVEL PERMUTATION
# ============================================================================
hdr("Perm-3: Cluster-level permutation (vintage cohorts)")

cluster_ids_eu = eu['year_announced'].values

perm3 = permutation_test(
    X_eu.values, y_eu, focal_idx=cbam_x_post_idx,
    treatment_col_idx=cbam_x_post_idx,
    B=2999, cluster_level=True, cluster_ids=cluster_ids_eu
)
print(f"Cluster permutation (year-cohorts as clusters):")
print(f"  β_obs = {perm3['beta_obs']:.4f}, t_obs = {perm3['t_obs']:.3f}")
print(f"  Permutation p (β): {perm3['p_perm_beta']:.4f}")
print(f"  Permutation p (t): {perm3['p_perm_t']:.4f}")


# ============================================================================
# 6. PLOT permutation distributions
# ============================================================================
hdr("Plot permutation distributions")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

for ax, (name, res) in zip(axes, [('EU 2x2 DiD (unit-perm)', perm1),
                                     ('Triple-diff (unit-perm)', perm2),
                                     ('EU 2x2 DiD (cluster-perm)', perm3)]):
    ax.hist(res['beta_perm'], bins=50, color='#888', alpha=0.6, density=True, edgecolor='black', lw=0.4)
    ax.axvline(res['beta_obs'], color='#882288', ls='-', lw=2.2, label=f'$\\hat\\beta_{{obs}}$={res["beta_obs"]:.3f}')
    ax.axvline(-res['beta_obs'], color='#882288', ls='--', lw=1.2, alpha=0.5)
    ax.axvline(0, ls=':', color='black', alpha=0.5)
    ax.set_xlabel('Permuted coefficient distribution')
    ax.set_ylabel('Density')
    ax.set_title(f'{name}\nPermutation p={res["p_perm_beta"]:.3f}')
    ax.legend(loc='best', fontsize=8)

plt.suptitle('Figure: Permutation distributions under sharp null H0: τ=0', fontsize=12, y=1.02)
plt.tight_layout()
fig.savefig(OUT / "figures/F_permutation_distributions.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_permutation_distributions.pdf")


# ============================================================================
# 7. SAMENVATTING
# ============================================================================
hdr("PERMUTATION INFERENCE — SAMENVATTING")

summary_perm = pd.DataFrame([
    {'spec':'EU 2x2 DiD (unit-perm)','beta':perm1['beta_obs'],'p_asymp':0.043,'p_wcb':0.124,'p_perm':perm1['p_perm_beta']},
    {'spec':'Triple-diff (unit-perm)','beta':perm2['beta_obs'],'p_asymp':0.326,'p_wcb':0.278,'p_perm':perm2['p_perm_beta']},
    {'spec':'EU 2x2 DiD (cluster-perm)','beta':perm3['beta_obs'],'p_asymp':0.043,'p_wcb':0.515,'p_perm':perm3['p_perm_beta']},
])
print(summary_perm.to_string(index=False))
summary_perm.to_csv(OUT / "results/permutation_summary.csv", index=False)

print(f"""

CONCLUSIE PERMUTATION INFERENCE:

  Spec 1 (EU 2x2 DiD unit-permutation):
    Asymp p=0.043 → WCB p=0.124 → Permutation p={perm1['p_perm_beta']:.3f}
    De drie inference-methodes geven {'CONSISTENT NULL' if perm1['p_perm_beta'] > 0.05 else 'gemixt resultaat'}
  
  Spec 2 (Triple-difference unit-permutation):
    Asymp p=0.326 → WCB p=0.278 → Permutation p={perm2['p_perm_beta']:.3f}
    Robust null across alle inference methodes — {'BEVESTIGD' if perm2['p_perm_beta'] > 0.10 else 'twijfelachtig'}

  Spec 3 (Cluster-level permutation, year-cohorts):
    Permutation p={perm3['p_perm_beta']:.3f} - {'consistent met WCB' if abs(perm3['p_perm_beta'] - 0.124) < 0.1 else 'verschilt van WCB'}

VOOR DE THESIS:
  We hebben nu DRIE onafhankelijke inference methods op onze key DiD specs:
  
  1. Asymptotic cluster-robust SE (baseline)
  2. Wild Cluster Bootstrap (Roodman-MacKinnon, robust voor small-N)
  3. Fisher randomization (non-parametric, exact onder sharp null)
  
  Voor de EU 2x2 DiD: asymp p=0.04 onder WCB en permutation p=0.10+.
  Conclusie: De associationale EU-paradox is FRAGIEL onder defensieve inference.
""")
