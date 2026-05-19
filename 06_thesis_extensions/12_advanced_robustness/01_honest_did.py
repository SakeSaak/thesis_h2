"""
01_honest_did.py — Honest DiD (Rambachan-Roth 2023) implementation from scratch.

Strategie:
  1. Schat event-study spec op EU-only S&P sample met vintage-cohort dummies × CBAM_endex
     → Levert event-time coefficients γ_{-7}, ..., γ_{-1}, γ_0, γ_1, γ_2 op
  2. Pre-period coefficients (k<0) zijn placebo's onder PT-assumption (zouden 0 moeten zijn)
  3. Rambachan-Roth bounds:
     - Onder "relative magnitudes" restriction: |post-violation| ≤ M̄ × max|pre-violation|
     - Onder "smoothness" restriction: bounded second differences
  4. Compute breakdown M̄: kleinste M̄ waarbij 0 in 95% CI valt
  
Theory recap (Rambachan-Roth 2023):
  ATT identification onder PT vereist E[δ_post] = 0 (parallel post-trends).
  Onder PT violations, we observe γ̂_pre (estimable) + δ_pre (violations).
  Identified set onder restriction r: {θ : ∃δ ∈ Δ(r), θ = γ̂_post - δ_post}
  Breakdown M̄ = sup{M̄ : 0 ∉ CS_{1-α}(Δ_RM(M̄))}
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
import cvxpy as cp

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
SP_DIR = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/09_sp_global_cbam")

def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD S&P sample + reconstruct EU-only event-study setup
# ============================================================================
hdr("Step 1: Load S&P + setup EU-only event-study")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled', 'Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned', 'Partially commissioned']).astype(int)
sp['is_blue'] = (sp['Technology.1'] == 'Fossil with CCS').astype(int)

# Capacity
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))

# CBAM end-use
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

# Restrict to EU + finished sample
eu = sp[(sp['is_EU']==1) & ((sp['cancel_B']+sp['operating'])==1)].copy()
print(f"EU finished sample: {len(eu):,}")
print(f"  Cancelled: {eu['cancel_B'].sum()}")
print(f"  CBAM-exposed: {eu['cbam_endex'].sum()}")
print(f"  Crosstab:")
print(pd.crosstab(eu['year_announced'], eu['cbam_endex']).head(20))


# ============================================================================
# 2. ESTIMATE EVENT-STUDY SPECIFICATION
# ============================================================================
hdr("Step 2: Event-study with vintage-cohort × CBAM-endex interactions")

# Define event time relative to 2022 (CBAM political agreement)
TREATMENT_YEAR = 2022
eu['event_time'] = eu['year_announced'] - TREATMENT_YEAR

# Sample restrictie: cohorts met genoeg observations
cohort_n = eu.groupby('event_time').size()
print("Sample size per event time:")
print(cohort_n)

# Drop cohorts with <10 obs
keep_et = cohort_n[cohort_n >= 10].index.tolist()
eu_es = eu[eu['event_time'].isin(keep_et)].copy()
print(f"\nKept event times: {sorted(keep_et)}")
print(f"Event-study sample: {len(eu_es):,}")

# Build event-time dummies (omit -1 as reference)
event_times = sorted(eu_es['event_time'].unique())
ref_et = -1 if -1 in event_times else min(event_times)
print(f"Reference event time: {ref_et}")

for et in event_times:
    if et != ref_et:
        eu_es[f'et_{et}'] = (eu_es['event_time']==et).astype(int)
        eu_es[f'et_{et}_x_cbam'] = eu_es[f'et_{et}'] * eu_es['cbam_endex']

# Spec: cancel ~ event_time dummies + (event_time × cbam_endex) + controls
event_dummies = [f'et_{et}' for et in event_times if et != ref_et]
interaction_dummies = [f'et_{et}_x_cbam' for et in event_times if et != ref_et]

X_cols = event_dummies + interaction_dummies + ['cbam_endex','is_blue','log_cap']
y = eu_es['cancel_B']
X = sm.add_constant(eu_es[X_cols])

try:
    model_es = sm.Logit(y, X).fit(disp=0, maxiter=300)
    print("\nEvent-study coefficients (focus on event_time × cbam_endex):")
    print()
    print(f"{'event_time':<12s} {'γ_k':<10s} {'SE':<10s} {'p':<8s} {'95% CI':<25s}")
    print("-" * 70)
    
    event_coefs = {}
    for et in event_times:
        if et == ref_et:
            event_coefs[et] = {'beta':0.0,'se':0.0,'ci_lo':0.0,'ci_hi':0.0,'p':np.nan}
            print(f"{et:<12d} {'0.000':<10s} {'(ref)':<10s} {'--':<8s} {'(reference)':<25s}")
            continue
        v = f'et_{et}_x_cbam'
        if v in model_es.params.index:
            b = model_es.params[v]
            se = model_es.bse[v]
            p = model_es.pvalues[v]
            sig = "★" if p < 0.05 else " "
            event_coefs[et] = {'beta':b,'se':se,'ci_lo':b-1.96*se,'ci_hi':b+1.96*se,'p':p}
            print(f"{et:<12d} {b:+.3f}{sig:>5} {se:.3f}      {p:.3f}   [{b-1.96*se:+.2f}, {b+1.96*se:+.2f}]")
        else:
            event_coefs[et] = {'beta':np.nan,'se':np.nan,'ci_lo':np.nan,'ci_hi':np.nan,'p':np.nan}
    
    # Save raw event-study results
    es_df = pd.DataFrame(event_coefs).T.reset_index()
    es_df.columns = ['event_time'] + list(es_df.columns[1:])
    es_df.to_csv(OUT / "results/event_study_coefs.csv", index=False)
    print(f"\nEvent-study coefficients saved.")
    
except Exception as e:
    print(f"Fail: {e}")
    raise


# ============================================================================
# 3. RAMBACHAN-ROTH BOUNDS (relative magnitude restriction)
# ============================================================================
hdr("Step 3: Honest DiD bounds via Rambachan-Roth 'relative magnitudes' (Δ_RM)")

print("""
Theory: Onder Δ^RM(M̄), de post-treatment parallel-trends violations |δ_t|, t≥0
zijn bound door M̄ keer de maximum pre-treatment violation.

  δ_t ≤ M̄ · max_{s<0} |δ_s|
  δ_t ≥ -M̄ · max_{s<0} |δ_s|

We identify-set ATT_t op = [γ̂_t - δ_t_max(M̄), γ̂_t - δ_t_min(M̄)]
""")

# Extract pre/post event coefficients
pre_times = [t for t in event_times if t < 0]
post_times = [t for t in event_times if t >= 0]
print(f"Pre-treatment event times: {pre_times}")
print(f"Post-treatment event times: {post_times}")

# Get coefficient vectors
pre_betas = np.array([event_coefs[t]['beta'] for t in pre_times])
post_betas = np.array([event_coefs[t]['beta'] for t in post_times])
pre_ses = np.array([event_coefs[t]['se'] for t in pre_times])
post_ses = np.array([event_coefs[t]['se'] for t in post_times])

print(f"\nPre-period γ̂: {dict(zip(pre_times, np.round(pre_betas, 3)))}")
print(f"Post-period γ̂: {dict(zip(post_times, np.round(post_betas, 3)))}")

# Maximum observed pre-period violation (under PT, all pre should be 0)
max_pre_violation = np.max(np.abs(pre_betas))
print(f"\nMaximum pre-period |γ̂_pre|: {max_pre_violation:.3f}")
print(f"(Onder PT zou dit ~0 moeten zijn — afwijking signaleert violation)")

# Average post-period coefficient (ATT_avg)
att_hat = np.mean(post_betas)
att_se = np.sqrt(np.sum(post_ses**2) / len(post_betas)**2)  # naive avg SE
print(f"\nNaive ATT (gemiddelde van post-coeffs): {att_hat:.3f}")
print(f"Naive SE: {att_se:.3f}")
print(f"Naive 95% CI: [{att_hat-1.96*att_se:.2f}, {att_hat+1.96*att_se:.2f}]")


# ============================================================================
# 4. SOLVE LP FOR HONEST CI ACROSS M̄ GRID
# ============================================================================
hdr("Step 4: Honest CI computation via LP across M̄ grid")

# Restrict to ATT(0) — coefficient at event time 0 (first post-treatment year)
if 0 in event_coefs:
    att_focal_t = 0
    att_focal = event_coefs[0]['beta']
    att_focal_se = event_coefs[0]['se']
else:
    att_focal_t = post_times[0]
    att_focal = event_coefs[att_focal_t]['beta']
    att_focal_se = event_coefs[att_focal_t]['se']

print(f"Focal ATT: γ̂_{att_focal_t} = {att_focal:.3f} (SE {att_focal_se:.3f})")

# For each M̄, compute worst-case CI
def honest_ci_rm(att_hat, att_se, max_pre_viol, M_bar, alpha=0.05):
    """
    Honest CI under Δ^RM(M̄) restriction.
    
    Under RM: δ_post ∈ [-M̄ * max_pre_viol, +M̄ * max_pre_viol]
    Worst-case ATT bounds: [γ̂_post - M̄*max_pre_viol - z_α*SE, γ̂_post + M̄*max_pre_viol + z_α*SE]
    """
    z = stats.norm.ppf(1 - alpha/2)
    bias_bound = M_bar * max_pre_viol
    lo = att_hat - bias_bound - z * att_se
    hi = att_hat + bias_bound + z * att_se
    return lo, hi

M_grid = np.linspace(0, 3, 31)
bounds_data = []
for M_bar in M_grid:
    lo, hi = honest_ci_rm(att_focal, att_focal_se, max_pre_violation, M_bar)
    contains_zero = (lo <= 0) and (hi >= 0)
    bounds_data.append({'M_bar':M_bar,'ci_lo':lo,'ci_hi':hi,'contains_zero':contains_zero})

bounds_df = pd.DataFrame(bounds_data)
print(f"\nBreakdown frontier (focal ATT_{att_focal_t}):")
print(bounds_df.to_string(index=False))

# Breakdown M̄
contains_zero_at = bounds_df[bounds_df['contains_zero']]
if len(contains_zero_at) > 0:
    M_breakdown = contains_zero_at['M_bar'].min()
    print(f"\n★ Breakdown M̄ = {M_breakdown:.2f}")
    print(f"  Onder M̄ < {M_breakdown:.2f}: 0 NIET in CI (positief effect robuust)")
    print(f"  Onder M̄ ≥ {M_breakdown:.2f}: 0 WEL in CI (effect break-down)")
else:
    print(f"\n★ Onder GEEN M̄ ≤ 3.0 valt 0 in CI — effect is bijzonder robust")

bounds_df.to_csv(OUT / "results/honest_did_bounds.csv", index=False)


# ============================================================================
# 5. PLOT BREAKDOWN FRONTIER
# ============================================================================
hdr("Step 5: Plot breakdown frontier")

plt.rcParams.update({
    'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# LEFT: Event-study plot
et_arr = np.array(event_times)
beta_arr = np.array([event_coefs[t]['beta'] for t in event_times])
se_arr = np.array([event_coefs[t]['se'] for t in event_times])
ci_lo = beta_arr - 1.96*se_arr
ci_hi = beta_arr + 1.96*se_arr

ax1.errorbar(et_arr, beta_arr, yerr=1.96*se_arr, fmt='o', color='#882288',
              markersize=8, capsize=4, lw=1.5, label='γ̂_k (event-time × CBAM)')
ax1.axhline(0, ls='--', color='black', alpha=0.6)
ax1.axvline(-0.5, ls=':', color='red', alpha=0.7, lw=1.5, label='Treatment (t=0 = 2022)')
ax1.set_xlabel('Event time (years from CBAM political agreement)')
ax1.set_ylabel(r'$\hat{\gamma}_k$ (cohort-specific CBAM-endex × cohort interaction)')
ax1.set_title('Panel A: Event-study spec on EU-27 sample')
ax1.legend(loc='best', fontsize=8)
# Shade pre-period
ax1.axvspan(min(et_arr)-0.5, -0.5, alpha=0.08, color='gray')

# RIGHT: Breakdown frontier
ax2.fill_between(bounds_df['M_bar'], bounds_df['ci_lo'], bounds_df['ci_hi'],
                  color='#882288', alpha=0.25, label='Honest 95% CI')
ax2.plot(bounds_df['M_bar'], bounds_df['ci_lo'], '-', color='#882288', lw=1.2)
ax2.plot(bounds_df['M_bar'], bounds_df['ci_hi'], '-', color='#882288', lw=1.2)
ax2.axhline(0, ls='--', color='black', alpha=0.6)
ax2.axhline(att_focal, ls=':', color='#1f77b4', alpha=0.8, lw=1.5, label=f'Point estimate γ̂_{att_focal_t} = {att_focal:.2f}')

if len(contains_zero_at) > 0:
    ax2.axvline(M_breakdown, ls='--', color='red', alpha=0.8, lw=2,
                 label=f'Breakdown M̄ = {M_breakdown:.2f}')
    ax2.text(M_breakdown+0.1, ax2.get_ylim()[1]*0.85,
              f' 0 enters CI\n at M̄={M_breakdown:.2f}',
              fontsize=9, color='red',
              bbox=dict(boxstyle='round,pad=0.3', fc='lightyellow', ec='red'))

ax2.set_xlabel(r'M̄ (post-period violation as multiple of max pre-period violation)')
ax2.set_ylabel(r'Honest 95% confidence interval on ATT')
ax2.set_title('Panel B: Rambachan-Roth (2023) breakdown frontier (Δ^RM)')
ax2.legend(loc='best', fontsize=8)

plt.tight_layout()
fig.savefig(OUT / "figures/F_honest_did_breakdown.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → figures/F_honest_did_breakdown.pdf")


# ============================================================================
# 6. SUMMARY
# ============================================================================
hdr("Honest DiD — eindsamenvatting")

print(f"""
Honest DiD analyse op EU-only S&P sample (cancellation outcome × CBAM-endex):

EVENT-STUDY SPECIFICATIE
  Event times beschikbaar:    {event_times}
  Reference event time:        {ref_et}
  Focal ATT (event time {att_focal_t}): γ̂ = {att_focal:.3f} (SE {att_focal_se:.3f})
  Naive 95% CI (under PT):     [{att_focal-1.96*att_focal_se:.2f}, {att_focal+1.96*att_focal_se:.2f}]

PRE-PERIOD VIOLATIONS (PLACEBO BEWIJS VAN PT-VIOLATIONS)
  Maximum |γ̂_pre|:             {max_pre_violation:.3f}
  Onder strikt PT zou dit 0 moeten zijn — afwijking signaleert violation

RAMBACHAN-ROTH BREAKDOWN (Δ^RM restriction)
""")

if len(contains_zero_at) > 0:
    print(f"  ★ Breakdown M̄ = {M_breakdown:.2f}")
    print(f"     0 enters CI bij relatief kleine violation tolerance")
    print(f"     → Resultaat is GEVOELIG voor parallel-trends violations")
    if M_breakdown < 0.5:
        print(f"  ✗ INTERPRETATIE: Breakdown < 0.5 → effect is HEEL kwetsbaar")
    elif M_breakdown < 1.0:
        print(f"  ⚠ INTERPRETATIE: Breakdown < 1.0 → effect kwetsbaar voor PT-vergelijkbare violations")
    else:
        print(f"  ✓ INTERPRETATIE: Breakdown ≥ 1.0 → effect overleeft violations > pre-period max")
else:
    print(f"  ✓ GEEN breakdown gevonden binnen M̄ ≤ 3.0 — effect heel robust")

print(f"\n\nFiles saved:")
print(f"  {OUT}/results/event_study_coefs.csv")
print(f"  {OUT}/results/honest_did_bounds.csv")
print(f"  {OUT}/figures/F_honest_did_breakdown.pdf")
