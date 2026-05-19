"""
16_causal_forests.py — Causal Forests voor heterogeneous Blue-vs-PEM cancellation effect.

Methode: Athey, Tibshirani, Wager (2019), "Generalized Random Forests",
Annals of Statistics 47(2):1148-1178. Plus Wager-Athey (2018), "Estimation and
Inference of Heterogeneous Treatment Effects using Random Forests", JASA.

ONZE VRAAG (gegeven competing-risks finding van vandaag):
  Pre-commissioning cancellation is Blue-disproportioneel (HR=1.58, p=0.020).
  Welke project-KENMERKEN moderate dit effect?
  
WAAROM CAUSAL FORESTS VOOR ONS:
  - Onze subgroup-DiD (sectie 10.6) faalde door power per subgroep
  - Causal Forests exploiteert heterogeneity CONTINU via tree partitioning
  - Niet beperkt tot pre-gespecificeerde subgroepen
  - Non-parametric: geen functional form assumption op moderation
  - Honest splitting: orthogonalize against confounders via DML

SETUP:
  Y = cancel_B (binary, project-level cancellation)
  T = is_blue (binary, focal treatment)
  X = projectkenmerken voor heterogeneity discovery
  W = confounders (overlap met X is OK)
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import KFold
from econml.dml import CausalForestDML

np.random.seed(42)
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/12_advanced_robustness")
def hdr(t): print("\n" + "="*78 + f"\n{t}\n" + "="*78)


# ============================================================================
# STEP 1 — Load S&P sample en build feature matrix
# ============================================================================
hdr("Step 1: Load S&P sample + build feature matrix")

sp = pd.read_excel('/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx', sheet_name='Export')
sp = sp[sp['project_status'].notna() & sp['Year announced'].notna()].copy()
sp['year_announced'] = sp['Year announced'].astype(int)
sp = sp[sp['year_announced'].between(2010, 2026)].copy()
sp['cancel_B'] = sp['project_status'].isin(['Plans cancelled','Decommissioned']).astype(int)
sp['operating'] = sp['project_status'].isin(['Fully commissioned','Partially commissioned']).astype(int)
sp['is_blue'] = (sp['Technology.1']=='Fossil with CCS').astype(int)
sp['capacity_mw'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['log_cap'] = np.log1p(sp['capacity_mw'].fillna(sp['capacity_mw'].median()))
sp['is_EU'] = (sp['Region major']=='Europe (EU-27)').astype(int)
sp['is_NA'] = (sp['Region major']=='North America').astype(int)
sp['is_Asia'] = (sp['Region major']=='Asia-Pacific').astype(int)

def cbam_endex(d, s):
    dl = str(d).lower() if pd.notna(d) else ''
    sl = str(s).lower() if pd.notna(s) else ''
    if any(k in dl for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']): return 1
    if 'chemical feedstock' in sl or 'refinery feedstock' in sl: return 1
    return 0
sp['cbam_endex'] = sp.apply(lambda r: cbam_endex(r['Primary end use sector detail'], r['Primary end use sector']), axis=1)

# Sponsor type via Primary owner column (75% coverage volgens onze data check)
def sponsor_type(text):
    if pd.isna(text): return 0  # Unknown
    t = str(text).lower()
    majors = ['exxon','shell','bp ','chevron','total','equinor','aramco','eni','repsol',
              'phillips','occidental','petrobras','sinopec','cnpc','petronas','enbridge',
              'enagas','engie','rwe','iberdrola','vattenfall','statoil','marathon']
    industrial = ['linde','air liquide','airgas','praxair','air products','messer']
    if any(m in t for m in majors): return 1  # Major
    if any(i in t for i in industrial): return 2  # IndustrialGas
    if 'gov' in t or 'ministry' in t or 'state' in t: return 3  # Government
    return 4  # Independent

if 'Primary owner' in sp.columns:
    sp['sponsor_type_num'] = sp['Primary owner'].apply(sponsor_type)
else:
    sp['sponsor_type_num'] = 0
print(f"Sponsor type distribution: {sp['sponsor_type_num'].value_counts().to_dict()}")

# Restrict to "finished" projects (cancel_B + operating == 1)
sp['finished'] = sp['cancel_B'] + sp['operating']
df = sp[sp['finished']==1].copy().reset_index(drop=True)
print(f"\nFinished sample: N = {len(df)} ({df['cancel_B'].sum()} cancellations, {df['is_blue'].sum()} Blue)")

# Year-centered
df['year_c'] = df['year_announced'] - 2015

# Build matrices
feature_cols = ['log_cap','year_c','is_EU','is_NA','is_Asia','cbam_endex','sponsor_type_num']
X = df[feature_cols].values.astype(float)
Y = df['cancel_B'].values.astype(float)
T = df['is_blue'].values.astype(float)
W = X.copy()  # confounders = same as X (overlap is OK voor DML)

print(f"\nFeature matrix X: shape {X.shape}, columns: {feature_cols}")
print(f"Treatment T (is_blue): {int(T.sum())}/{len(T)} = {100*T.mean():.1f}%")
print(f"Outcome Y (cancel_B):  {int(Y.sum())}/{len(Y)} = {100*Y.mean():.1f}%")


# ============================================================================
# STEP 2 — Fit Causal Forest with DML residualization
# ============================================================================
hdr("Step 2: Fit Causal Forest DML")

# Model voor Y given W (outcome model)
model_y = RandomForestRegressor(n_estimators=200, min_samples_leaf=10, random_state=42, n_jobs=-1)
# Model voor T given W (propensity model)
model_t = RandomForestClassifier(n_estimators=200, min_samples_leaf=10, random_state=42, n_jobs=-1)

cf = CausalForestDML(
    model_y=model_y,
    model_t=model_t,
    discrete_treatment=True,
    n_estimators=500,
    min_samples_leaf=10,
    max_depth=8,
    honest=True,
    inference=True,
    cv=3,
    random_state=42,
)

print("Fitting Causal Forest (this takes 30-60 seconds)...")
cf.fit(Y=Y, T=T, X=X, W=W)
print("✓ Fit complete")

# Average treatment effect
ate = cf.ate(X)
ate_lo, ate_hi = cf.ate_interval(X, alpha=0.05)
print(f"\nAverage Treatment Effect (Blue effect on cancellation):")
print(f"  ATE = {ate:+.4f}, 95% CI [{ate_lo:+.4f}, {ate_hi:+.4f}]")

# CATE per individual
cate_estimates = cf.effect(X)
cate_lo, cate_hi = cf.effect_interval(X, alpha=0.05)
print(f"\nCATE distribution:")
print(f"  Mean = {np.mean(cate_estimates):+.4f}")
print(f"  Median = {np.median(cate_estimates):+.4f}")
print(f"  Std = {np.std(cate_estimates):.4f}")
print(f"  10th-90th percentile: [{np.percentile(cate_estimates, 10):+.4f}, {np.percentile(cate_estimates, 90):+.4f}]")
print(f"  Min, Max: [{cate_estimates.min():+.4f}, {cate_estimates.max():+.4f}]")


# ============================================================================
# STEP 3 — Feature importance for heterogeneity
# ============================================================================
hdr("Step 3: Feature importance — welke variabelen drijven heterogeneity?")

feat_imp = cf.feature_importances_
print(f"\nFeature importance ranking (heterogeneity-driving):")
imp_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': feat_imp,
}).sort_values('importance', ascending=False)
print(imp_df.to_string(index=False))


# ============================================================================
# STEP 4 — Heterogeneity discovery via subgroup CATE
# ============================================================================
hdr("Step 4: Heterogeneity discovery — CATE per subgroup")

df['cate'] = cate_estimates
df['cate_lo'] = cate_lo
df['cate_hi'] = cate_hi

# CATE per region
print("\nCATE per region:")
region_cate = df.groupby('Region major').agg(
    n=('cate','size'),
    mean_cate=('cate','mean'),
    median_cate=('cate','median'),
    n_blue=('is_blue','sum'),
).round(4)
print(region_cate)

# CATE per CBAM-exposure
print("\nCATE per CBAM-exposure:")
cbam_cate = df.groupby('cbam_endex').agg(
    n=('cate','size'),
    mean_cate=('cate','mean'),
    median_cate=('cate','median'),
    n_blue=('is_blue','sum'),
).round(4)
print(cbam_cate)

# CATE per size quartile
df['log_cap_q'] = pd.qcut(df['log_cap'], q=4, labels=['Q1','Q2','Q3','Q4'], duplicates='drop')
print("\nCATE per size quartile:")
size_cate = df.groupby('log_cap_q', observed=True).agg(
    n=('cate','size'),
    mean_cate=('cate','mean'),
    median_cate=('cate','median'),
    n_blue=('is_blue','sum'),
).round(4)
print(size_cate)

# CATE per year bucket
df['year_bucket'] = pd.cut(df['year_announced'], bins=[2009, 2017, 2020, 2022, 2026],
                              labels=['pre-2018','2018-2020','2021-2022','2023+'])
print("\nCATE per year bucket:")
year_cate = df.groupby('year_bucket', observed=True).agg(
    n=('cate','size'),
    mean_cate=('cate','mean'),
    median_cate=('cate','median'),
    n_blue=('is_blue','sum'),
).round(4)
print(year_cate)


# ============================================================================
# STEP 5 — Top heterogeneity contrasts (significant CATE)
# ============================================================================
hdr("Step 5: Significantie per individual CATE")

df['cate_significant'] = (df['cate_lo'] > 0).astype(int)  # significantly positive
df['cate_negative'] = (df['cate_hi'] < 0).astype(int)     # significantly negative
print(f"\nProjects with significantly positive CATE (Blue increases cancel hazard):")
print(f"  N = {df['cate_significant'].sum()} / {len(df)} ({100*df['cate_significant'].mean():.1f}%)")
print(f"\nProjects with significantly negative CATE (Blue decreases cancel hazard):")
print(f"  N = {df['cate_negative'].sum()} / {len(df)} ({100*df['cate_negative'].mean():.1f}%)")

if df['cate_significant'].sum() > 0:
    print(f"\nTop 5 projects with HIGHEST positive CATE (Blue most harmful):")
    top_pos = df.nlargest(5, 'cate')[['cate','cate_lo','cate_hi','Region major','cbam_endex','log_cap','year_announced','is_blue','cancel_B']]
    print(top_pos.to_string())

if df['cate_negative'].sum() > 0:
    print(f"\nTop 5 projects with MOST NEGATIVE CATE (Blue PROTECTIVE):")
    top_neg = df.nsmallest(5, 'cate')[['cate','cate_lo','cate_hi','Region major','cbam_endex','log_cap','year_announced','is_blue','cancel_B']]
    print(top_neg.to_string())


# ============================================================================
# STEP 6 — Plot
# ============================================================================
hdr("Step 6: Generate plot")

plt.rcParams.update({'font.family':'serif','font.size':10,'axes.grid':True,'grid.alpha':0.3})
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Distribution of CATE
ax = axes[0,0]
ax.hist(cate_estimates, bins=40, color='#882288', alpha=0.7, edgecolor='black')
ax.axvline(0, color='black', ls=':', alpha=0.6)
ax.axvline(np.mean(cate_estimates), color='#1f77b4', ls='-', lw=2, label=f'Mean = {np.mean(cate_estimates):+.3f}')
ax.set_xlabel('Estimated CATE (Blue effect on P(cancel))')
ax.set_ylabel('Number of projects')
ax.set_title(f'Panel A: CATE distribution\nMean = {np.mean(cate_estimates):+.3f}, range [{cate_estimates.min():+.2f}, {cate_estimates.max():+.2f}]')
ax.legend(fontsize=9)

# Panel B: Feature importance
ax = axes[0,1]
imp_sorted = imp_df.sort_values('importance')
ax.barh(imp_sorted['feature'], imp_sorted['importance'], color='#2ca02c', alpha=0.7, edgecolor='black')
ax.set_xlabel('Heterogeneity feature importance')
ax.set_title('Panel B: Welke kenmerken drijven CATE-heterogeneity?')

# Panel C: CATE per year bucket
ax = axes[1,0]
yb = year_cate.reset_index()
ax.bar(range(len(yb)), yb['mean_cate'], color='#1f77b4', alpha=0.7, edgecolor='black',
        yerr=df.groupby('year_bucket', observed=True)['cate'].std().values / np.sqrt(yb['n'].values),
        capsize=5)
ax.axhline(0, color='black', ls=':', alpha=0.6)
ax.set_xticks(range(len(yb)))
ax.set_xticklabels([f"{lbl}\n(N={n})" for lbl, n in zip(yb['year_bucket'], yb['n'])])
ax.set_ylabel('Mean CATE')
ax.set_title('Panel C: CATE per year bucket\n(temporal heterogeneity)')

# Panel D: CATE per size quartile
ax = axes[1,1]
sq = size_cate.reset_index()
ax.bar(range(len(sq)), sq['mean_cate'], color='#ff7f0e', alpha=0.7, edgecolor='black',
        yerr=df.groupby('log_cap_q', observed=True)['cate'].std().values / np.sqrt(sq['n'].values),
        capsize=5)
ax.axhline(0, color='black', ls=':', alpha=0.6)
ax.set_xticks(range(len(sq)))
ax.set_xticklabels([f"{lbl}\n(N={n})" for lbl, n in zip(sq['log_cap_q'], sq['n'])])
ax.set_ylabel('Mean CATE')
ax.set_title('Panel D: CATE per size quartile\n(size heterogeneity)')

plt.suptitle('Causal Forests: Heterogeneous Blue-vs-PEM Treatment Effects\n(Athey, Tibshirani, Wager 2019)',
              y=1.00, fontsize=12)
plt.tight_layout()
fig.savefig(OUT / "figures/F_causal_forests.pdf", bbox_inches='tight', dpi=120)
plt.close()
print(f"  → F_causal_forests.pdf")


# ============================================================================
# STEP 7 — Save results
# ============================================================================
hdr("Step 7: Save outputs")

summary = pd.DataFrame([{
    'N': len(df),
    'ATE': ate,
    'ATE_ci_lo': ate_lo,
    'ATE_ci_hi': ate_hi,
    'CATE_mean': float(np.mean(cate_estimates)),
    'CATE_std': float(np.std(cate_estimates)),
    'CATE_p10': float(np.percentile(cate_estimates, 10)),
    'CATE_p90': float(np.percentile(cate_estimates, 90)),
    'n_sig_positive': int(df['cate_significant'].sum()),
    'n_sig_negative': int(df['cate_negative'].sum()),
}])
summary.to_csv(OUT/"results/cf_summary.csv", index=False)
imp_df.to_csv(OUT/"results/cf_feature_importance.csv", index=False)

df[['Region major','cbam_endex','log_cap','year_announced','is_blue','cancel_B',
     'cate','cate_lo','cate_hi','cate_significant']].to_csv(OUT/"results/cf_cate_per_project.csv", index=False)

print("\nEINDSAMENVATTING — Causal Forests:")
print(f"""
  ATE = {ate:+.4f}, 95% CI [{ate_lo:+.4f}, {ate_hi:+.4f}]
  CATE range: [{cate_estimates.min():+.4f}, {cate_estimates.max():+.4f}]
  CATE std: {np.std(cate_estimates):.4f}
  Significantly positive CATE: {df['cate_significant'].sum()}/{len(df)} projects
  Significantly negative CATE: {df['cate_negative'].sum()}/{len(df)} projects
  
  Top heterogeneity-drivers: {', '.join(imp_df['feature'].head(3).tolist())}
""")
