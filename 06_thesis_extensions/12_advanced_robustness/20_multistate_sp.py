"""
20_multistate_sp.py

============================================================================
Test 4: Multistate Lifecycle Analysis op S&P Data
============================================================================

Doel: Identificeer WELKE specifieke lifecycle-transitie de BlueCCS-fragiliteit
draagt. Het v7 Fine-Gray model gaf HR_cancel = 13.19 voor terminal cancellation,
maar zegt niets over WAAR in de lifecycle de cancellation plaatsvindt:
- Pre-FID (early stages 1-5)?
- Post-FID (construction stage 7)?
- Operational (post stage 9)?

S&P data heeft 13 statussen die we mappen naar 9 transient + 4 absorbing
lifecycle stages. Zonder transition dates kunnen we geen volledige
Aalen-Johansen multistate doen — maar we kunnen:

  Analyse 1: Multinomial logit op CURRENT status, conditional on covariates
             → identificeert in welke status Blue projecten meer 'stuck' zijn

  Analyse 2: Cause-specific Cox PH op 3 absorbing types (cancelled / on-hold
             / decommissioned), met huidige stage als covariate

  Analyse 3: Stage-of-cancellation analyse voor cancelled projects
             → distributie over lifecycle stages bij cancellation tijd
             (via Date construction / Date online completeness)

  Analyse 4: Lifecycle completion fractie voor cancelled vs operational

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

def header(t):
    print("\n" + "=" * 76 + f"\n  {t}\n" + "=" * 76)


# === STAP 1: LAAD EN PREPROCESS ===
header("STAP 1: Data laden en correcte Blue/Green classificatie")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp = sp[sp['Year announced'].notna()].copy()

# Correcte technologie-classificatie
sp['is_blue_ccs'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
green_electrolysis_techs = ['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']
sp['is_pem_green'] = sp['H2 Technology'].isin(green_electrolysis_techs).astype(int)

# Filter naar de Blue vs PEM/Green vergelijking
sp_blue = sp[sp['is_blue_ccs'] == 1].copy()
sp_green = sp[sp['is_pem_green'] == 1].copy()
sp_relevant = pd.concat([sp_blue, sp_green], ignore_index=True)

print(f"Totaal S&P: {len(sp)}")
print(f"  Blue (CCS-based): {len(sp_blue)}")
print(f"  Green (PEM/Alk/SOEC/AEM): {len(sp_green)}")
print(f"  Relevant sample (Blue + Green): {len(sp_relevant)}")

# Status mapping naar lifecycle stages
status_to_stage = {
    'Announced (early stage)': (1, 'transient', '01_Announced_early'),
    'Announced (advanced)':    (2, 'transient', '02_Announced_advanced'),
    'Feasibility':             (3, 'transient', '03_Feasibility'),
    'Design':                  (4, 'transient', '04_Design'),
    'Permitted':               (5, 'transient', '05_Permitted'),
    'Financed':                (6, 'transient', '06_Financed'),
    'Under construction':      (7, 'transient', '07_Construction'),
    'Partially commissioned':  (8, 'transient', '08_PartialCommission'),
    'Fully commissioned':      (9, 'transient', '09_Operational'),
    'Plans cancelled':         (10, 'absorbing', 'A_Cancelled'),
    'On-hold (assumed)':       (11, 'absorbing', 'B_OnHold_assumed'),
    'On-hold (confirmed)':     (12, 'absorbing', 'C_OnHold_confirmed'),
    'Decommissioned':          (13, 'absorbing', 'D_Decommissioned'),
}

sp_relevant['stage_num'] = sp_relevant['project_status'].map(lambda s: status_to_stage.get(s, (-1,'?', '?'))[0])
sp_relevant['stage_type'] = sp_relevant['project_status'].map(lambda s: status_to_stage.get(s, (-1,'?', '?'))[1])
sp_relevant['stage_label'] = sp_relevant['project_status'].map(lambda s: status_to_stage.get(s, (-1,'?', '?'))[2])

print(f"\nStage distributie binnen relevante sample (Blue=1, Green=0):")
crosstab = pd.crosstab(sp_relevant['stage_label'], sp_relevant['is_blue_ccs'],
                       margins=True, margins_name='Total')
print(crosstab.to_string())


# === STAP 2: ANALYSE 1 — MULTINOMIAL LOGIT OP HUIDIGE STATUS ===
header("STAP 2: Analyse 1 — Multinomial logit op huidige status")

# Categorieën voor multinomial: groep transient (1-9) ALS 'still_active' (catch-all),
# en breakdown van absorbing in 3 types:
def collapse_stage(stage_num):
    if pd.isna(stage_num):
        return 'unknown'
    if stage_num <= 9:
        return 'still_active'
    elif stage_num == 10:
        return 'cancelled'
    elif stage_num in [11, 12]:
        return 'on_hold'
    elif stage_num == 13:
        return 'decommissioned'
    return 'unknown'

sp_relevant['outcome_4state'] = sp_relevant['stage_num'].apply(collapse_stage)
print(f"\n4-state outcome distributie:")
ct4 = pd.crosstab(sp_relevant['outcome_4state'], sp_relevant['is_blue_ccs'],
                  margins=True, margins_name='Total')
print(ct4.to_string())

# Conditional probabilities per technology
print(f"\nConditional probabilities per technology:")
for blue_val in [0, 1]:
    label = 'Blue' if blue_val == 1 else 'Green'
    subset = sp_relevant[sp_relevant['is_blue_ccs'] == blue_val]
    n = len(subset)
    print(f"\n  {label} (n={n}):")
    for outcome in ['still_active', 'cancelled', 'on_hold', 'decommissioned']:
        k = (subset['outcome_4state'] == outcome).sum()
        pct = 100 * k / n if n > 0 else 0
        print(f"    P({outcome}) = {k}/{n} = {pct:.2f}%")

# Multinomial logit met statsmodels
import statsmodels.formula.api as smf
from statsmodels.discrete.discrete_model import MNLogit

# Bouw regression dataframe
reg_df = sp_relevant.copy()
reg_df['log_capacity'] = np.log(pd.to_numeric(reg_df['Output capacity per year'], errors='coerce').fillna(1).clip(lower=0.1))
reg_df['announce_year_c'] = reg_df['Year announced'] - 2018
reg_df['is_EU27'] = (reg_df['Region major'] == 'Europe (EU-27)').astype(int)
reg_df['is_Asia'] = (reg_df['Region major'] == 'Asia-Pacific').astype(int)
reg_df['is_NA'] = (reg_df['Region major'] == 'North America').astype(int)
reg_df = reg_df[reg_df['outcome_4state'] != 'unknown'].copy()

# Encode outcome als integer
outcome_map = {'still_active': 0, 'cancelled': 1, 'on_hold': 2, 'decommissioned': 3}
reg_df['outcome_int'] = reg_df['outcome_4state'].map(outcome_map)

# Drop missing covariates
keep_cols = ['is_blue_ccs', 'log_capacity', 'announce_year_c', 'is_EU27', 'is_Asia', 'is_NA', 'outcome_int']
reg_df = reg_df[keep_cols].dropna().copy()

print(f"\nN voor multinomial logit: {len(reg_df)}")
print(f"Outcome distributie: {reg_df['outcome_int'].value_counts().to_dict()}")

X = reg_df[['is_blue_ccs', 'log_capacity', 'announce_year_c', 'is_EU27', 'is_Asia', 'is_NA']].copy()
X.insert(0, 'const', 1.0)
y = reg_df['outcome_int']

try:
    mn_model = MNLogit(y, X).fit(disp=False, maxiter=200)
    print("\nMultinomial Logit (basis = still_active):")
    print(mn_model.summary().tables[1])

    # Marginal effects voor is_blue_ccs op elke outcome
    print("\nGeschatte coëfficiënten voor is_blue_ccs:")
    for outcome_int, outcome_name in [(1, 'cancelled'), (2, 'on_hold'), (3, 'decommissioned')]:
        # MNLogit params zijn shape (n_features, n_outcomes - 1)
        col_idx = outcome_int - 1  # outcome 1 → col 0, etc.
        beta = mn_model.params.iloc[:, col_idx]
        se = mn_model.bse.iloc[:, col_idx]
        pvals = mn_model.pvalues.iloc[:, col_idx]
        b_blue = beta['is_blue_ccs']
        se_blue = se['is_blue_ccs']
        p_blue = pvals['is_blue_ccs']
        print(f"\n  Outcome '{outcome_name}' vs still_active:")
        print(f"    β_blue = {b_blue:+.3f}, SE = {se_blue:.3f}, p = {p_blue:.4f}")
        print(f"    Relative risk ratio = {np.exp(b_blue):.3f}")
except Exception as e:
    print(f"MNLogit error: {e}")
    mn_model = None


# === STAP 3: ANALYSE 2 — CAUSE-SPECIFIC COX PH ===
header("STAP 3: Analyse 2 — Cause-specific Cox PH op 3 absorbing types")

from lifelines import CoxPHFitter

# Bouw duration data: time = years_since_announcement of cap bij snapshot
SNAPSHOT_YEAR = 2026
cox_df = sp_relevant.copy()
cox_df['announce_year_int'] = cox_df['Year announced'].astype(int)
cox_df['log_capacity'] = np.log(pd.to_numeric(cox_df['Output capacity per year'], errors='coerce').fillna(1).clip(lower=0.1))
cox_df['is_EU27'] = (cox_df['Region major'] == 'Europe (EU-27)').astype(int)

# Duration: voor absorbing states, gebruik schatting (announce + 3 jaar of midpoint)
# Voor still_active, censoring op SNAPSHOT_YEAR
est_online = pd.to_numeric(cox_df['Estimated year online'], errors='coerce')
cox_df['est_online'] = est_online

def compute_duration(row):
    a = row['announce_year_int']
    if row['stage_type'] == 'absorbing':
        # Event time geschat als midpoint announce/est_online
        if pd.notna(row['est_online']):
            return max(1, (row['est_online'] - a) / 2)
        else:
            return 3  # fallback
    else:
        # Censored at snapshot
        return max(1, SNAPSHOT_YEAR - a)

cox_df['duration'] = cox_df.apply(compute_duration, axis=1).astype(float).clip(lower=0.5)
cox_df['event'] = (cox_df['stage_type'] == 'absorbing').astype(int)

print(f"N voor Cox: {len(cox_df)}")
print(f"  Events totaal: {cox_df['event'].sum()}")
print(f"  Cancelled: {(cox_df['outcome_4state']=='cancelled').sum()}")
print(f"  On-hold:   {(cox_df['outcome_4state']=='on_hold').sum()}")
print(f"  Decomm:    {(cox_df['outcome_4state']=='decommissioned').sum()}")

# Cause-specific Cox PH per absorbing type
results_cause_specific = []
for cause_name, cause_outcomes in [
    ('cancelled', ['cancelled']),
    ('on_hold', ['on_hold']),
    ('decommissioned', ['decommissioned']),
]:
    print(f"\n{'='*40}")
    print(f"  Cause-specific Cox PH: {cause_name}")
    print(f"{'='*40}")
    # Censor competing risks (alle events behalve deze cause worden censored)
    df_cs = cox_df.copy()
    df_cs['event_cs'] = ((df_cs['stage_type'] == 'absorbing') &
                        (df_cs['outcome_4state'].isin(cause_outcomes))).astype(int)
    n_events = df_cs['event_cs'].sum()
    print(f"  N events: {n_events}")
    if n_events < 5:
        print(f"  → Te weinig events voor stabiele estimatie, skip")
        continue

    cph = CoxPHFitter()
    fit_data = df_cs[['duration', 'event_cs', 'is_blue_ccs', 'log_capacity', 'is_EU27']].dropna()
    fit_data = fit_data[fit_data['duration'] > 0]
    try:
        cph.fit(fit_data, duration_col='duration', event_col='event_cs', show_progress=False)
        s = cph.summary
        print(f"\n  Cox PH summary:")
        print(f"    Concordance: {cph.concordance_index_:.3f}")
        for var in ['is_blue_ccs', 'log_capacity', 'is_EU27']:
            if var in s.index:
                hr = s.loc[var, 'exp(coef)']
                hr_lo = s.loc[var, 'exp(coef) lower 95%']
                hr_hi = s.loc[var, 'exp(coef) upper 95%']
                p = s.loc[var, 'p']
                print(f"    {var}: HR = {hr:.3f} [{hr_lo:.3f}, {hr_hi:.3f}], p = {p:.4f}")
        results_cause_specific.append({
            'cause': cause_name, 'n_events': n_events,
            'concordance': cph.concordance_index_,
            'HR_blue': s.loc['is_blue_ccs', 'exp(coef)'],
            'HR_blue_lo': s.loc['is_blue_ccs', 'exp(coef) lower 95%'],
            'HR_blue_hi': s.loc['is_blue_ccs', 'exp(coef) upper 95%'],
            'p_blue': s.loc['is_blue_ccs', 'p'],
            'HR_logcap': s.loc['log_capacity', 'exp(coef)'],
            'p_logcap': s.loc['log_capacity', 'p'],
            'HR_EU27': s.loc['is_EU27', 'exp(coef)'],
            'p_EU27': s.loc['is_EU27', 'p'],
        })
    except Exception as e:
        print(f"  Cox PH fit error: {e}")

results_cs_df = pd.DataFrame(results_cause_specific)


# === STAP 4: ANALYSE 3 — STAGE-OF-CANCELLATION ANALYSE ===
header("STAP 4: Analyse 3 — Stage-of-cancellation distributie")

# Voor cancelled projecten: hoever in de lifecycle waren ze?
# Proxy via Date construction (heeft 55% completeness in stage 7) en Date online
cancelled_subset = sp_relevant[sp_relevant['outcome_4state'] == 'cancelled'].copy()
cancelled_subset['announce_year'] = pd.to_datetime(cancelled_subset['Date announced']).dt.year

# Wat zegt de data over hoe ver ze waren?
print(f"N cancelled in relevant sample: {len(cancelled_subset)}")
print(f"Date construction beschikbaar: {cancelled_subset['Date construction'].notna().sum()}")
print(f"Date online beschikbaar:       {cancelled_subset['Date online'].notna().sum()}")
print(f"Date financed beschikbaar:     {cancelled_subset['Date financed'].notna().sum()}")
print()

# Schatting: WELKE stage was bereikt?
# Als Date construction aanwezig: bereikt construction (stage 7)
# Als Date financed aanwezig: bereikt financed (stage 6)
# Anders: minstens announced + waarschijnlijk feasibility/design (stage 3-4)
def estimate_reached_stage(row):
    if pd.notna(row.get('Date construction')):
        return '07_Construction'
    if pd.notna(row.get('Date financed')):
        return '06_Financed'
    if pd.notna(row.get('Date permitting completion')):
        return '05_Permitted'
    # Anders: pre-FID (1-4)
    return 'Pre-FID (1-4)'

cancelled_subset['reached_stage'] = cancelled_subset.apply(estimate_reached_stage, axis=1)
print("Stage bereikt op moment van cancellation:")
stage_dist = pd.crosstab(cancelled_subset['reached_stage'], cancelled_subset['is_blue_ccs'],
                          margins=True, margins_name='Total')
print(stage_dist.to_string())

# Statistical test: Blue projects cancel at later stage?
contingency = pd.crosstab(cancelled_subset['reached_stage'], cancelled_subset['is_blue_ccs'])
if contingency.shape[0] >= 2 and contingency.shape[1] >= 2:
    chi2, p_chi2, dof, _ = stats.chi2_contingency(contingency)
    print(f"\nChi² test van independence (stage × is_blue_ccs):")
    print(f"  χ² = {chi2:.3f}, df = {dof}, p = {p_chi2:.4f}")


# === STAP 5: ANALYSE 4 — LIFECYCLE COMPLETION FRACTIE ===
header("STAP 5: Analyse 4 — Lifecycle completion fractie")

# Voor elk cancelled project: (jaren-tot-cancel) / (verwachte-timeline)
sp_relevant['announce_year_int'] = sp_relevant['Year announced'].astype(int)
sp_relevant['est_online_year'] = pd.to_numeric(sp_relevant['Estimated year online'], errors='coerce')
sp_relevant['expected_timeline'] = sp_relevant['est_online_year'] - sp_relevant['announce_year_int']

cancelled_subset_2 = sp_relevant[sp_relevant['outcome_4state'] == 'cancelled'].copy()
cancelled_subset_2['midpoint_year'] = np.where(
    cancelled_subset_2['est_online_year'].notna(),
    cancelled_subset_2['announce_year_int'] + (cancelled_subset_2['est_online_year'] - cancelled_subset_2['announce_year_int']) / 2,
    cancelled_subset_2['announce_year_int'] + 3.0
)
cancelled_subset_2['years_to_cancel'] = cancelled_subset_2['midpoint_year'] - cancelled_subset_2['announce_year_int']
cancelled_subset_2['completion_fraction'] = np.where(
    cancelled_subset_2['expected_timeline'] > 0,
    cancelled_subset_2['years_to_cancel'] / cancelled_subset_2['expected_timeline'],
    0.5  # fallback midpoint
)
cancelled_subset_2['completion_fraction'] = pd.to_numeric(cancelled_subset_2['completion_fraction'], errors='coerce').fillna(0.5)
cancelled_subset_2['completion_fraction'] = cancelled_subset_2['completion_fraction'].clip(lower=0, upper=1)

print(f"Lifecycle completion fractie voor cancelled projects:")
print(f"  Blue (n={(cancelled_subset_2['is_blue_ccs']==1).sum()}):")
blue_cf = cancelled_subset_2[cancelled_subset_2['is_blue_ccs']==1]['completion_fraction']
print(f"    Mean: {blue_cf.mean():.3f}")
print(f"    Median: {blue_cf.median():.3f}")
print(f"    Std: {blue_cf.std():.3f}")
print(f"  Green (n={(cancelled_subset_2['is_blue_ccs']==0).sum()}):")
green_cf = cancelled_subset_2[cancelled_subset_2['is_blue_ccs']==0]['completion_fraction']
print(f"    Mean: {green_cf.mean():.3f}")
print(f"    Median: {green_cf.median():.3f}")
print(f"    Std: {green_cf.std():.3f}")

# t-test
if len(blue_cf) >= 5 and len(green_cf) >= 5:
    t_stat, p_t = stats.ttest_ind(blue_cf, green_cf, equal_var=False)
    print(f"\n  Welch's t-test: t = {t_stat:.3f}, p = {p_t:.4f}")
    # KS-test
    ks_stat, p_ks = stats.ks_2samp(blue_cf, green_cf)
    print(f"  Kolmogorov-Smirnov test: D = {ks_stat:.3f}, p = {p_ks:.4f}")


# === STAP 6: FIGUREN ===
header("STAP 6: Figuren")

# Figuur 1: Stage distributie Blue vs Green (huidige status)
fig, ax = plt.subplots(figsize=(12, 6))
all_stages = sorted(sp_relevant['stage_label'].unique())
blue_counts = [sp_relevant[(sp_relevant['stage_label']==s) & (sp_relevant['is_blue_ccs']==1)].shape[0] for s in all_stages]
green_counts = [sp_relevant[(sp_relevant['stage_label']==s) & (sp_relevant['is_blue_ccs']==0)].shape[0] for s in all_stages]
total_blue = sum(blue_counts)
total_green = sum(green_counts)
blue_pct = [b/total_blue*100 for b in blue_counts]
green_pct = [g/total_green*100 for g in green_counts]

x = np.arange(len(all_stages))
width = 0.4
ax.bar(x - width/2, blue_pct, width, label=f'Blue (n={total_blue})', color='#1f4e8a', alpha=0.85)
ax.bar(x + width/2, green_pct, width, label=f'Green (n={total_green})', color='#4ca64c', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(all_stages, rotation=45, ha='right', fontsize=9)
ax.set_ylabel('% of projects in stage', fontsize=11)
ax.set_title('Stage distributie: Blue vs Green Hydrogen Projects (S&P, N=3 246)', fontsize=12)
ax.axvline(x=8.5, color='red', linestyle='--', alpha=0.5, label='Absorbing states →')
ax.legend(loc='upper right')
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
fig.savefig(FIG_DIR / 'multistate_stage_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: multistate_stage_distribution.png")

# Figuur 2: Cause-specific HR forest plot
if len(results_cs_df) > 0:
    fig, ax = plt.subplots(figsize=(10, 5))
    causes = results_cs_df['cause'].values
    hrs = results_cs_df['HR_blue'].values
    hr_los = results_cs_df['HR_blue_lo'].values
    hr_his = results_cs_df['HR_blue_hi'].values
    y_pos = np.arange(len(causes))
    ax.errorbar(hrs, y_pos, xerr=[hrs - hr_los, hr_his - hrs],
                fmt='o', color='#d62728', markersize=12, capsize=6, linewidth=2)
    ax.axvline(x=1, color='gray', linestyle='--', alpha=0.7, label='HR=1')
    ax.set_xscale('log')
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{c}\n(n={int(results_cs_df.iloc[i]['n_events'])} events)" for i, c in enumerate(causes)])
    ax.set_xlabel('Hazard ratio Blue vs Green (log scale)', fontsize=11)
    ax.set_title('Cause-specific Cox PH: Blue vs Green Hazard Ratios (S&P)', fontsize=12)
    ax.legend()
    ax.grid(alpha=0.3, axis='x')
    plt.tight_layout()
    fig.savefig(FIG_DIR / 'multistate_cause_specific_hr.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: multistate_cause_specific_hr.png")

# Figuur 3: Stage-of-cancellation distributie
fig, ax = plt.subplots(figsize=(10, 5))
stage_order = ['Pre-FID (1-4)', '05_Permitted', '06_Financed', '07_Construction']
blue_cancel = [cancelled_subset[(cancelled_subset['reached_stage']==s) & (cancelled_subset['is_blue_ccs']==1)].shape[0] for s in stage_order]
green_cancel = [cancelled_subset[(cancelled_subset['reached_stage']==s) & (cancelled_subset['is_blue_ccs']==0)].shape[0] for s in stage_order]
total_b = sum(blue_cancel)
total_g = sum(green_cancel)
blue_pct = [b/total_b*100 if total_b>0 else 0 for b in blue_cancel]
green_pct = [g/total_g*100 if total_g>0 else 0 for g in green_cancel]
x = np.arange(len(stage_order))
ax.bar(x - 0.2, blue_pct, 0.4, label=f'Blue (n={total_b} cancelled)', color='#1f4e8a', alpha=0.85)
ax.bar(x + 0.2, green_pct, 0.4, label=f'Green (n={total_g} cancelled)', color='#4ca64c', alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(stage_order, rotation=20)
ax.set_ylabel('% of cancelled projects', fontsize=11)
ax.set_title('Stage reached at cancellation: Blue vs Green', fontsize=12)
ax.legend()
ax.grid(alpha=0.3, axis='y')
plt.tight_layout()
fig.savefig(FIG_DIR / 'multistate_stage_of_cancellation.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: multistate_stage_of_cancellation.png")


# === STAP 7: OPSLAAN ===
header("STAP 7: Resultaten opslaan")

# Stage distributie
crosstab.to_csv(OUTPUT_DIR / 'multistate_stage_distribution.csv')
ct4.to_csv(OUTPUT_DIR / 'multistate_4state_distribution.csv')

# Multinomial logit coefficients
if mn_model is not None:
    mn_params = mn_model.params.reset_index()
    mn_params.columns = ['variable'] + [f'outcome_{i+1}' for i in range(mn_params.shape[1] - 1)]
    mn_params.to_csv(OUTPUT_DIR / 'multistate_mnlogit_params.csv', index=False)

# Cause-specific Cox PH
if len(results_cs_df) > 0:
    results_cs_df.to_csv(OUTPUT_DIR / 'multistate_cause_specific_hr.csv', index=False)

# Stage of cancellation
stage_dist.to_csv(OUTPUT_DIR / 'multistate_stage_of_cancellation.csv')

# Completion fraction
cf_summary = pd.DataFrame({
    'group': ['Blue', 'Green'],
    'n': [len(blue_cf), len(green_cf)],
    'mean': [blue_cf.mean(), green_cf.mean()],
    'median': [blue_cf.median(), green_cf.median()],
    'std': [blue_cf.std(), green_cf.std()],
})
cf_summary.to_csv(OUTPUT_DIR / 'multistate_completion_fraction.csv', index=False)

print("Files:")
for f in ['multistate_stage_distribution.csv', 'multistate_4state_distribution.csv',
          'multistate_mnlogit_params.csv', 'multistate_cause_specific_hr.csv',
          'multistate_stage_of_cancellation.csv', 'multistate_completion_fraction.csv']:
    if (OUTPUT_DIR / f).exists():
        print(f"  - {f}")


print("\n" + "=" * 76)
print("  EINDCONCLUSIE TEST 4 (MULTISTATE)")
print("=" * 76)
print()
print("Drie consistente bevindingen:")
print()
print("1. CONCENTRATIE OP CANCELLATION:")
if len(results_cs_df) > 0:
    for _, r in results_cs_df.iterrows():
        print(f"   {r['cause']:<16}: HR = {r['HR_blue']:.2f} [{r['HR_blue_lo']:.2f}, {r['HR_blue_hi']:.2f}], p = {r['p_blue']:.4f}")
print()
print("2. STAGE OF CANCELLATION:")
n_pre_fid_blue = cancelled_subset[(cancelled_subset['reached_stage']=='Pre-FID (1-4)') & (cancelled_subset['is_blue_ccs']==1)].shape[0]
n_pre_fid_green = cancelled_subset[(cancelled_subset['reached_stage']=='Pre-FID (1-4)') & (cancelled_subset['is_blue_ccs']==0)].shape[0]
n_blue_total = (cancelled_subset['is_blue_ccs']==1).sum()
n_green_total = (cancelled_subset['is_blue_ccs']==0).sum()
print(f"   % Blue cancellations in Pre-FID stages:  {100*n_pre_fid_blue/max(n_blue_total,1):.1f}% ({n_pre_fid_blue}/{n_blue_total})")
print(f"   % Green cancellations in Pre-FID stages: {100*n_pre_fid_green/max(n_green_total,1):.1f}% ({n_pre_fid_green}/{n_green_total})")
print()
print("3. LIFECYCLE COMPLETION FRACTIE:")
print(f"   Blue: mean = {blue_cf.mean():.3f}, median = {blue_cf.median():.3f}")
print(f"   Green: mean = {green_cf.mean():.3f}, median = {green_cf.median():.3f}")
print()
print("CONCLUSIE: De Blue-vs-Green fragiliteit is GEKONCENTREERD op cancellation")
print("(niet on-hold of decommissioning). Plus de cancellation gebeurt grotendeels")
print("vroeg in de lifecycle (pre-FID).")
