"""
08_event_study_pretrends.py — Event-study with leads and lags + pre-trends test.

Standaard DiD-validatie die top-tier work expliciet rapporteert: schat per
jaar-relatief-tot-CBAM een aparte coefficient, plot deze, en test formeel
of de leads (pre-CBAM coefficients) gezamenlijk nul zijn.

Data: S&P Global EU sample (consistent met onze EU 2x2 DiD).

Outputs:
  - Event-study coefficients per relatieve jaar
  - Joint F-test op pre-trends (H0: alle leads = 0)
  - Plot: coefficient + 95% CI per jaar, dashed lines voor treatment timing
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

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")

def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# LOAD S&P data
# ============================================================================
hdr("Load S&P Global sample voor event-study")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2014, 2026)].copy()  # 2014+ voor genoeg pre-CBAM data
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

# Treatment year: 2022 (political agreement Dec 2022)
TREATMENT_YEAR = 2022
sp['rel_year'] = sp['year_announced'] - TREATMENT_YEAR

# Finished projects only voor causale interpretation
finished = sp[(sp['cancel_B']+sp['operating'])==1].copy()
eu_finished = finished[finished['is_EU']==1].copy()

print(f"EU finished sample: N = {len(eu_finished)}")
print(f"Cancellation rate: {eu_finished['cancel_B'].mean()*100:.1f}%")
print(f"Years covered: {eu_finished['year_announced'].min()} - {eu_finished['year_announced'].max()}")
print(f"\nObservations per relative year:")
print(eu_finished.groupby(['rel_year','cbam_endex']).size().unstack(fill_value=0))


# ============================================================================
# A. EVENT-STUDY: jaar-fixed-effects × CBAM-end interaction
# ============================================================================
hdr("A. Event-study specification")

# Create year dummies relative to treatment
# Omit rel_year = -1 as baseline (year prior to treatment)
years_in_data = sorted(eu_finished['rel_year'].unique())
years_in_data = [y for y in years_in_data if eu_finished[eu_finished['rel_year']==y]['cbam_endex'].nunique() == 2]
# Need at least one CBAM and one non-CBAM observation per year for interaction term
print(f"Relevant years (with both CBAM=0 and CBAM=1 obs): {years_in_data}")

baseline_year = -1
print(f"Baseline year: rel_year = {baseline_year}")

# Build event-study design matrix
es_data = eu_finished.copy()

# Create year × cbam_endex interaction dummies, excluding baseline
es_vars = []
year_labels = []
for y in years_in_data:
    if y == baseline_year:
        continue
    var_name = f"cbam_x_y{'m' if y<0 else 'p'}{abs(y)}"
    es_data[var_name] = ((es_data['rel_year']==y) & (es_data['cbam_endex']==1)).astype(int)
    es_vars.append(var_name)
    year_labels.append(y)

# Year fixed effects (one per year, omit baseline)
year_fe_vars = []
for y in years_in_data:
    if y == baseline_year:
        continue
    fe_name = f"year_fe_{y}"
    es_data[fe_name] = (es_data['rel_year']==y).astype(int)
    year_fe_vars.append(fe_name)

# Treatment group fixed effect
es_data['cbam_main'] = es_data['cbam_endex']

# Full event-study spec
X_cols = ['cbam_main'] + year_fe_vars + es_vars + ['is_blue','log_cap']
X_es = sm.add_constant(es_data[X_cols])
y_es = es_data['cancel_B'].astype(float)

print(f"\nEvent-study regression — N = {len(y_es)}, K = {X_es.shape[1]}")

model_es = sm.OLS(y_es, X_es).fit(cov_type='HC1')

# Extract coefficients for the cbam_x_y* interaction terms
es_coefs = {}
for y_lab, var in zip(year_labels, es_vars):
    if var in model_es.params.index:
        es_coefs[y_lab] = {
            'beta': float(model_es.params[var]),
            'se': float(model_es.bse[var]),
            'p': float(model_es.pvalues[var]),
        }

es_coefs[baseline_year] = {'beta': 0.0, 'se': 0.0, 'p': 1.0}  # baseline = 0

es_df = pd.DataFrame(es_coefs).T.reset_index().rename(columns={'index':'rel_year'})
es_df['rel_year'] = es_df['rel_year'].astype(int)
es_df = es_df.sort_values('rel_year').reset_index(drop=True)
es_df['ci_lower'] = es_df['beta'] - 1.96 * es_df['se']
es_df['ci_upper'] = es_df['beta'] + 1.96 * es_df['se']
es_df['phase'] = np.where(es_df['rel_year'] < 0, 'pre-CBAM',
                            np.where(es_df['rel_year'] == 0, 'CBAM', 'post-CBAM'))

print("\nEvent-study coefficients per relative year:")
print(es_df[['rel_year','beta','se','p','ci_lower','ci_upper','phase']].round(4).to_string(index=False))
es_df.to_csv(OUT / "results/event_study_pretrends.csv", index=False)


# ============================================================================
# B. JOINT F-TEST OP PRE-TRENDS
# ============================================================================
hdr("B. Joint F-test op pre-CBAM trends (H0: alle leads = 0)")

# Pre-CBAM lead variables
pre_vars = [var for var, y_lab in zip(es_vars, year_labels) if y_lab < baseline_year]
print(f"Pre-CBAM leads: {pre_vars}")
print(f"({len(pre_vars)} leads — meer dan baseline year {baseline_year})")

if len(pre_vars) > 0:
    # Build hypothesis matrix: each lead = 0
    hypothesis = ' = '.join(pre_vars) + ' = 0'
    print(f"\nFormal hypothesis: {hypothesis}")
    
    try:
        f_test = model_es.f_test(', '.join([f"{v} = 0" for v in pre_vars]))
        print(f"\nJoint F-test resultaat:")
        print(f"  F-statistic: {float(f_test.statistic):.4f}")
        print(f"  df numerator: {int(f_test.df_num)}")
        print(f"  df denominator: {int(f_test.df_denom)}")
        print(f"  p-value: {float(f_test.pvalue):.4f}")
        
        if float(f_test.pvalue) < 0.05:
            verdict = "⚠ Pre-trends VIOLATED — parallel trends assumption mogelijk problematisch"
        elif float(f_test.pvalue) < 0.10:
            verdict = "⚠ MARGINAL pre-trends violation — caution"
        else:
            verdict = "✓ Pre-trends test PASSED — parallel trends assumption supported"
        print(f"\nVerdict: {verdict}")
        
        pretrends_result = {
            'F_statistic': float(f_test.statistic),
            'df_num': int(f_test.df_num),
            'df_denom': int(f_test.df_denom),
            'p_value': float(f_test.pvalue),
            'verdict': verdict,
        }
    except Exception as e:
        print(f"F-test failed: {e}")
        pretrends_result = None


# ============================================================================
# C. INDIVIDUAL PRE-TREND COEFFICIENT TESTS
# ============================================================================
hdr("C. Individuele pre-trend coefficienten")

print("Per-year pre-trend significance:")
for y_lab in sorted([y for y in year_labels if y < baseline_year]):
    var = [v for v, yl in zip(es_vars, year_labels) if yl == y_lab][0]
    if var in model_es.params.index:
        beta = model_es.params[var]
        se = model_es.bse[var]
        p = model_es.pvalues[var]
        marker = '⚠' if p < 0.05 else '✓'
        print(f"  rel_year = {y_lab}: β = {beta:+.4f} (SE {se:.4f}, p = {p:.4f}) {marker}")


# ============================================================================
# D. POST-TREATMENT DYNAMICS
# ============================================================================
hdr("D. Post-CBAM treatment dynamics")

print("Per-year post-CBAM treatment effects:")
post_betas = []
for y_lab in sorted([y for y in year_labels if y >= 0]):
    var = [v for v, yl in zip(es_vars, year_labels) if yl == y_lab][0]
    if var in model_es.params.index:
        beta = model_es.params[var]
        se = model_es.bse[var]
        p = model_es.pvalues[var]
        marker = '✓ sig' if p < 0.05 else '(ns)'
        print(f"  rel_year = +{y_lab}: β = {beta:+.4f} (SE {se:.4f}, p = {p:.4f}) {marker}")
        post_betas.append(beta)

if len(post_betas) > 0:
    avg_post = np.mean(post_betas)
    print(f"\nAverage post-CBAM treatment effect: {avg_post:+.4f}")


# ============================================================================
# E. PLOT — Event-study coefficient plot
# ============================================================================
hdr("E. Generate event-study plot")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})

fig, ax = plt.subplots(figsize=(11, 6))

pre_mask = es_df['rel_year'] < 0
post_mask = es_df['rel_year'] >= 0
baseline_mask = es_df['rel_year'] == baseline_year

# Pre-treatment coefficients (light blue)
ax.errorbar(es_df.loc[pre_mask, 'rel_year'], es_df.loc[pre_mask, 'beta'],
             yerr=1.96*es_df.loc[pre_mask, 'se'],
             fmt='o', color='#1f77b4', markersize=8, capsize=4, lw=1.5,
             label='Pre-CBAM (leads)', alpha=0.8)

# Baseline (filled)
ax.plot(baseline_year, 0, 'ks', markersize=10, label=f'Baseline (rel_year = {baseline_year})')

# Post-treatment coefficients (dark purple)
ax.errorbar(es_df.loc[post_mask, 'rel_year'], es_df.loc[post_mask, 'beta'],
             yerr=1.96*es_df.loc[post_mask, 'se'],
             fmt='o', color='#882288', markersize=10, capsize=4, lw=1.8,
             label='Post-CBAM (lags)', alpha=0.9)

# Treatment dates
ax.axvline(0, ls='--', color='red', alpha=0.6, label='CBAM political agreement (Dec 2022)')
ax.axvline(1, ls=':', color='orange', alpha=0.5, label='CBAM publication (May 2023)')
ax.axvline(4, ls=':', color='green', alpha=0.5, label='CBAM definitive phase (Jan 2026)')
ax.axhline(0, ls='-', color='black', alpha=0.4)

ax.set_xlabel('Years relative to CBAM political agreement (2022)')
ax.set_ylabel(r'$\hat\beta_t$: cbam_endex × year interaction (cancellation rate)')

ftest_title = ""
if pretrends_result:
    ftest_title = f" — Joint pre-trends F-test: F({pretrends_result['df_num']}, {pretrends_result['df_denom']}) = {pretrends_result['F_statistic']:.2f}, p = {pretrends_result['p_value']:.3f}"

ax.set_title(f'Event-study: EU CBAM-end-use effect on cancellation, leads and lags{ftest_title}',
              fontsize=11)
ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
ax.set_xticks(sorted(es_df['rel_year'].unique()))

plt.tight_layout()
fig.savefig(OUT / "figures/F_event_study_pretrends.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_event_study_pretrends.pdf")


# ============================================================================
# F. SUMMARY
# ============================================================================
hdr("EINDSAMENVATTING — EVENT-STUDY + PRE-TRENDS TEST")

if pretrends_result:
    print(f"""
DiD VALIDATION VOOR EU CBAM 2x2:
  Sample: N = {len(eu_finished)} EU finished projects
  Years: {min(years_in_data) + TREATMENT_YEAR} - {max(years_in_data) + TREATMENT_YEAR}
  Pre-treatment leads: {len(pre_vars)}
  Post-treatment lags: {sum(1 for y in year_labels if y >= 0)}

JOINT F-TEST OP PRE-CBAM PARALLEL TRENDS:
  F({pretrends_result['df_num']}, {pretrends_result['df_denom']}) = {pretrends_result['F_statistic']:.3f}
  p-value = {pretrends_result['p_value']:.4f}
  
  {pretrends_result['verdict']}

INDIVIDUELE PRE-TREND CHECK: alle leads ≥ rel_year = {min(year_labels)} 
  zijn afzonderlijk ge-evalueerd; zie tabel hierboven.

CONCLUSIE: Dit completes het DiD-validation pakket. Combined with Honest DiD
bounds (Rambachan-Roth M̄=0), Wild Cluster Bootstrap, permutation inference,
en Roth-Sant'Anna functional form, we have nu een complete validation suite
voor de parallel trends assumption.

→ Resultaten opgeslagen naar:
  - results/event_study_pretrends.csv
  - figures/F_event_study_pretrends.pdf
""")
