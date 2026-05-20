"""
31_innovation_fund_effect.py
============================================================================
Pijler 26: EU Innovation Fund / EU funding effect op project survival
============================================================================

Onderzoeksvraag:
  Hebben EU-level funding mechanismen (Innovation Fund, ERDF, national 
  recovery plans, Hydrogen Bank pilot) een MEETBAAR effect op de 
  cancellation rate van EU hydrogen projecten?

Doel: testen of de EU al een 45Q-equivalente carrot heeft die WERKT,
of dat de EU nog een 45Q-equivalent moet bouwen (vs alleen schalen).

Treatment groepen (uit Funding scheme detail):
  - EU Innovation Fund: 14 projecten (13 + 1 ETS Innovation Fund)
  - National recovery plans / ERDF: ~5 projecten
  - Funding program for electrolyzers (Germany): 7 projecten
  - GEEN EU funding gelabeled: ~440 EU projecten

Methoden:
  1. Selection-adjusted matching (PSM) — Innovation Fund vs matched controls
  2. Aggregate EU event study rond Innovation Fund 1st call (jul 2020)
  3. Cox PH op EU sample met treatment indicator

CAVEAT: Innovation Fund laureaten zijn voorgeselecteerd op kwaliteit
        → bias-laden bovenste grens van treatment effect
        → niettemin nuttig als beleidsindicator

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.statistics import logrank_test

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"

B_BOOT = 1000
SEED = 20260520


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD EN IDENTIFICEER FUNDING ===
header("STAP 1: Identificeer EU funding treatment groups")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
df = sp[(sp['is_blue'] == 1) | (sp['is_green'] == 1)].copy().reset_index(drop=True)
df['project_id'] = df.index

df['cancelled'] = (df['project_status'] == 'Plans cancelled').astype(int)
df['onhold'] = df['project_status'].isin(['On-hold (assumed)', 'On-hold (confirmed)']).astype(int)
df['decomm'] = (df['project_status'] == 'Decommissioned').astype(int)
df['event_any'] = (df['cancelled'] | df['onhold'] | df['decomm']).astype(int)

df['event_year'] = np.where(
    df['event_any'] == 1,
    np.where(df['est_year_online'].notna(),
             np.ceil((df['announce_year'] + df['est_year_online']) / 2),
             df['announce_year'] + 3),
    2026.0
).clip(min=df['announce_year'], max=2026.0)
df['duration'] = (df['event_year'] - df['announce_year']).clip(lower=0.5)

df['log_capacity'] = np.log1p(pd.to_numeric(df['Output capacity per year'], errors='coerce').fillna(0))
df['is_eu'] = (df['Region major'] == 'Europe (EU-27)').astype(int)

# Treatment indicators
def classify_funding(row):
    fs = str(row.get('Funding scheme detail', ''))
    if 'Innovation Fund' in fs:
        return 'EU_Innovation_Fund'
    if 'Recovery' in fs or 'Resilience' in fs:
        return 'National_Recovery'
    if 'Regional Development Fund' in fs or 'ERDF' in fs:
        return 'ERDF'
    if 'ELY' in fs or 'electrolyzers' in fs:
        return 'Germany_ELY'
    if pd.notna(row.get('Funding scheme detail', None)) and str(row.get('Funding scheme detail', '')).strip() != '' and str(row.get('Funding scheme detail', '')) != 'nan':
        return 'Other_funded'
    return 'No_explicit_funding'

df['funding_type'] = df.apply(classify_funding, axis=1)

# EU sample
eu = df[df['is_eu'] == 1].copy()
print(f"EU Blue+Green sample: {len(eu)}")
print(f"\nFunding type distribution (EU):")
print(eu['funding_type'].value_counts().to_string())

# Outcomes per funding type
print(f"\nCancellation rate per funding type (EU):")
fund_outcomes = eu.groupby('funding_type').agg(
    N=('cancelled', 'size'),
    n_cancel=('cancelled', 'sum'),
    n_onhold=('onhold', 'sum'),
    n_any_failure=('event_any', 'sum'),
).reset_index()
fund_outcomes['cancel_rate'] = (fund_outcomes['n_cancel'] / fund_outcomes['N']).round(3)
fund_outcomes['failure_rate'] = (fund_outcomes['n_any_failure'] / fund_outcomes['N']).round(3)
print(fund_outcomes.to_string(index=False))


# === STAP 2: BINARIE TREATMENT (any EU funding labeled) ===
header("STAP 2: Binarie treatment — any EU-labeled funding vs none")

eu['has_eu_funding'] = (eu['funding_type'] != 'No_explicit_funding').astype(int)
print(f"\nWith EU funding: {eu['has_eu_funding'].sum()} / {len(eu)} ({eu['has_eu_funding'].mean()*100:.1f}%)")

# Univariate comparison
funded = eu[eu['has_eu_funding'] == 1]
unfunded = eu[eu['has_eu_funding'] == 0]

print(f"\nFunded EU (n={len(funded)}):")
print(f"  Cancel rate: {funded['cancelled'].mean():.4f}")
print(f"  On-hold rate: {funded['onhold'].mean():.4f}")
print(f"  Any failure rate: {funded['event_any'].mean():.4f}")
print(f"  Mean log_capacity: {funded['log_capacity'].mean():.3f}")
print(f"  Mean announce year: {funded['announce_year'].mean():.1f}")

print(f"\nUnfunded EU (n={len(unfunded)}):")
print(f"  Cancel rate: {unfunded['cancelled'].mean():.4f}")
print(f"  On-hold rate: {unfunded['onhold'].mean():.4f}")
print(f"  Any failure rate: {unfunded['event_any'].mean():.4f}")
print(f"  Mean log_capacity: {unfunded['log_capacity'].mean():.3f}")
print(f"  Mean announce year: {unfunded['announce_year'].mean():.1f}")

# Naive difference
naive_diff_cancel = funded['cancelled'].mean() - unfunded['cancelled'].mean()
naive_diff_failure = funded['event_any'].mean() - unfunded['event_any'].mean()
print(f"\nNaive difference (NOT causal — selection bias):")
print(f"  Δ Cancel rate: {naive_diff_cancel:+.4f}")
print(f"  Δ Failure rate: {naive_diff_failure:+.4f}")


# === STAP 3: PROPENSITY SCORE MATCHING ===
header("STAP 3: 1-NN Matching op covariates (selection-adjusted)")

# Matching features
features = ['log_capacity', 'is_blue', 'announce_year']
eu_clean = eu[features + ['has_eu_funding', 'cancelled', 'event_any']].dropna().copy()

X = eu_clean[features].values
treated = eu_clean[eu_clean['has_eu_funding'] == 1]
control_pool = eu_clean[eu_clean['has_eu_funding'] == 0]

if len(treated) > 0 and len(control_pool) > 5:
    # Standardize
    scaler = StandardScaler()
    X_co = scaler.fit_transform(control_pool[features].values)
    X_tr = scaler.transform(treated[features].values)
    
    # 1-NN matching
    nbrs = NearestNeighbors(n_neighbors=1, metric='euclidean').fit(X_co)
    distances, indices = nbrs.kneighbors(X_tr)
    
    matched_co = control_pool.iloc[indices.flatten()].reset_index(drop=True)
    treated_reset = treated.reset_index(drop=True)
    
    print(f"Treated (EU funded): {len(treated_reset)}")
    print(f"Matched controls: {len(matched_co)}")
    print(f"Mean matching distance (standardized): {distances.mean():.3f}")
    
    # ATT
    y_tr = treated_reset['cancelled'].values
    y_co = matched_co['cancelled'].values
    
    att_cancel = float(y_tr.mean() - y_co.mean())
    print(f"\nATT cancel rate (matched): {att_cancel:+.4f}")
    print(f"  Treated cancel: {y_tr.mean():.4f}")
    print(f"  Matched control cancel: {y_co.mean():.4f}")
    
    # Bootstrap CI
    rng = np.random.default_rng(SEED)
    boot_atts = []
    for b in range(B_BOOT):
        idx = rng.choice(len(treated_reset), size=len(treated_reset), replace=True)
        boot_atts.append(y_tr[idx].mean() - y_co[idx].mean())
    boot_atts = np.array(boot_atts)
    ci_lo, ci_hi = np.percentile(boot_atts, [2.5, 97.5])
    
    # Two-sided p
    if att_cancel > 0:
        p_boot = 2 * np.mean(boot_atts <= 0)
    else:
        p_boot = 2 * np.mean(boot_atts >= 0)
    p_boot = float(min(p_boot, 1.0))
    
    print(f"  Bootstrap SE: {boot_atts.std():.4f}")
    print(f"  95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"  Bootstrap p (2-sided): {p_boot:.4f}")
    
    # Also for any_failure
    y_tr_fail = treated_reset['event_any'].values
    y_co_fail = matched_co['event_any'].values
    att_failure = float(y_tr_fail.mean() - y_co_fail.mean())
    print(f"\nATT any_failure rate (matched): {att_failure:+.4f}")
    print(f"  Treated failure: {y_tr_fail.mean():.4f}")
    print(f"  Matched control failure: {y_co_fail.mean():.4f}")
else:
    att_cancel = att_failure = ci_lo = ci_hi = p_boot = np.nan


# === STAP 4: COX PH OP EU SAMPLE MET FUNDING DUMMY ===
header("STAP 4: Cox PH op EU sample met has_eu_funding")

cox_eu = eu[['duration', 'event_any', 'has_eu_funding', 'is_blue', 'log_capacity']].dropna().copy()

cph = CoxPHFitter()
try:
    cph.fit(cox_eu, duration_col='duration', event_col='event_any')
    print(cph.summary[['coef', 'exp(coef)', 'p', 'coef lower 95%', 'coef upper 95%']].round(4).to_string())
    
    hr_funding = float(np.exp(cph.params_['has_eu_funding']))
    p_funding = float(cph.summary.loc['has_eu_funding', 'p'])
    ci_lo_hr = float(np.exp(cph.confidence_intervals_.loc['has_eu_funding'].iloc[0]))
    ci_hi_hr = float(np.exp(cph.confidence_intervals_.loc['has_eu_funding'].iloc[1]))
    
    print(f"\nHR_has_eu_funding = {hr_funding:.3f} [{ci_lo_hr:.3f}, {ci_hi_hr:.3f}], p = {p_funding:.4f}")
except Exception as e:
    print(f"Cox PH errored: {e}")
    hr_funding = p_funding = np.nan


# === STAP 5: EVENT STUDY ROND INNOVATION FUND 1ST CALL (jul 2020) ===
header("STAP 5: EU vs non-EU event study rond Innovation Fund openingen")

# Innovation Fund 1st large-scale call opened July 2020
# Innovation Fund 4th call (hydrogen-specific window) opened Nov 2023

T_IF1 = 2020
T_IF4 = 2024  # 4th call results announced in 2024

def cumulative_cancel_rate(sub_df, year):
    risk = sub_df[sub_df['announce_year'] <= year]
    if len(risk) == 0:
        return np.nan
    n_cancel = ((risk['cancelled'] == 1) & (risk['event_year'] <= year)).sum()
    return float(n_cancel / len(risk))

years_test = list(range(2015, 2027))
rate_panel = []
for region_label, mask in [('EU-27', df['is_eu'] == 1),
                            ('Non-EU', df['is_eu'] == 0)]:
    sub = df[mask].copy()
    for y in years_test:
        rate_panel.append({
            'region': region_label,
            'year': y,
            'cancel_rate': cumulative_cancel_rate(sub, y),
            'n_risk': int((sub['announce_year'] <= y).sum()),
        })
rate_df_eu = pd.DataFrame(rate_panel)
print("\nCumulative cancel rate per regio × jaar:")
print(rate_df_eu.pivot(index='year', columns='region', values='cancel_rate').round(4).to_string())

# DiD: EU pre/post 2020 vs Non-EU pre/post 2020
eu_pre = cumulative_cancel_rate(df[df['is_eu']==1], 2019)
eu_post = cumulative_cancel_rate(df[df['is_eu']==1], 2026)
non_pre = cumulative_cancel_rate(df[df['is_eu']==0], 2019)
non_post = cumulative_cancel_rate(df[df['is_eu']==0], 2026)
did_if = (eu_post - eu_pre) - (non_post - non_pre)
print(f"\nDiD aggregate EU vs Non-EU rond Innovation Fund 1st call (2020):")
print(f"  EU:     {eu_pre:.4f} (2019) → {eu_post:.4f} (2026)  Δ = {eu_post - eu_pre:+.4f}")
print(f"  Non-EU: {non_pre:.4f} (2019) → {non_post:.4f} (2026)  Δ = {non_post - non_pre:+.4f}")
print(f"  DiD = {did_if:+.4f}")


# === STAP 6: KM CURVES VOOR FUNDED VS UNFUNDED ===
header("STAP 6: Kaplan-Meier curves voor funded vs unfunded EU projects")

kmf_funded = KaplanMeierFitter()
kmf_funded.fit(durations=funded['duration'], event_observed=funded['event_any'],
               label=f'EU funded (n={len(funded)})')

kmf_unfunded = KaplanMeierFitter()
kmf_unfunded.fit(durations=unfunded['duration'], event_observed=unfunded['event_any'],
                 label=f'EU unfunded (n={len(unfunded)})')

# Log-rank test
lr = logrank_test(funded['duration'], unfunded['duration'],
                  event_observed_A=funded['event_any'],
                  event_observed_B=unfunded['event_any'])
print(f"Log-rank test (any failure): chi² = {lr.test_statistic:.3f}, p = {lr.p_value:.4f}")


# === STAP 7: FIGUREN ===
header("STAP 7: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: KM curves
ax = axes[0, 0]
kmf_funded.plot_survival_function(ax=ax, color='#2ca02c', linewidth=2.5)
kmf_unfunded.plot_survival_function(ax=ax, color='#d62728', linewidth=2.5)
ax.set_xlabel('Years since announcement')
ax.set_ylabel('Survival probability (no any-failure)')
ax.set_title(f'KM Curves: funded vs unfunded EU projects\nLog-rank χ² = {lr.test_statistic:.2f}, p = {lr.p_value:.4f}')
ax.legend(loc='lower left')
ax.grid(alpha=0.3)

# Panel B: Bar chart cancel rates per funding type
ax = axes[0, 1]
plot_data = fund_outcomes[fund_outcomes['N'] >= 5].sort_values('cancel_rate')
ax.barh(plot_data['funding_type'], plot_data['cancel_rate'], color='#1f77b4',
        edgecolor='black', alpha=0.8)
for i, (idx, row) in enumerate(plot_data.iterrows()):
    ax.text(row['cancel_rate'] + 0.005, i, f"{row['cancel_rate']:.3f} (n={int(row['N'])})",
            va='center', fontsize=10)
ax.set_xlabel('Cancellation rate')
ax.set_title('Cancel rate per EU funding type')
ax.grid(alpha=0.3, axis='x')

# Panel C: EU vs Non-EU cumulative cancel over time
ax = axes[1, 0]
for r, color in [('EU-27', '#d62728'), ('Non-EU', '#1f77b4')]:
    sub = rate_df_eu[rate_df_eu['region'] == r]
    ax.plot(sub['year'], sub['cancel_rate'], 'o-', color=color, linewidth=2, markersize=8, label=r)
ax.axvline(x=T_IF1, color='gray', linestyle='--', alpha=0.6)
ax.text(T_IF1 + 0.1, 0.04, 'Innovation Fund\n1st call', fontsize=9)
ax.axvline(x=T_IF4, color='black', linestyle=':', alpha=0.5)
ax.text(T_IF4 + 0.1, 0.04, 'IF 4th call /\nHydrogen Bank', fontsize=9)
ax.set_xlabel('Year')
ax.set_ylabel('Cumulative cancellation rate')
ax.set_title(f'EU vs Non-EU cumulative cancellations\nAggregate DiD = {did_if:+.4f}')
ax.legend()
ax.grid(alpha=0.3)

# Panel D: ATT comparison with Pijler 25 45Q
ax = axes[1, 1]
methods_lbl = ['EU Funded\n(naive)', 'EU Funded\n(matched ATT)', 'US 45Q\n(Pijler 25)']
values = [naive_diff_cancel, att_cancel if not np.isnan(att_cancel) else 0, -0.147]
errors = [0, (ci_hi - ci_lo) / 2 if not np.isnan(ci_lo) else 0, (0.282 - 0.029) / 2]
colors = ['#ff7f0e', '#2ca02c', '#9c27b0']
x = np.arange(len(methods_lbl))
ax.bar(x, values, yerr=errors, color=colors, edgecolor='black', width=0.5, capsize=8)
for i, v in enumerate(values):
    ax.text(i, v + 0.005 if v > 0 else v - 0.020, f'{v:+.3f}', ha='center', fontsize=11, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(methods_lbl)
ax.axhline(y=0, color='black', linewidth=0.5)
ax.set_ylabel('Treatment effect on cancellation rate')
ax.set_title('Carrot effect comparison: EU Innovation Fund vs US 45Q')
ax.grid(alpha=0.3, axis='y')

plt.suptitle('Pijler 26: EU Innovation Fund effect on project survival',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler26_innovation_fund.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler26_innovation_fund.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Opslaan")

summary = pd.DataFrame([{
    'method': 'Pijler 26: EU Innovation Fund effect',
    'n_eu_total': len(eu),
    'n_eu_funded': int(eu['has_eu_funding'].sum()),
    'n_innovation_fund': int((eu['funding_type'] == 'EU_Innovation_Fund').sum()),
    'funded_cancel_rate': float(funded['cancelled'].mean()),
    'unfunded_cancel_rate': float(unfunded['cancelled'].mean()),
    'naive_diff_cancel': float(naive_diff_cancel),
    'naive_diff_failure': float(naive_diff_failure),
    'matched_att_cancel': float(att_cancel) if not np.isnan(att_cancel) else np.nan,
    'matched_ci_lo': float(ci_lo) if not np.isnan(ci_lo) else np.nan,
    'matched_ci_hi': float(ci_hi) if not np.isnan(ci_hi) else np.nan,
    'matched_p_boot': float(p_boot) if not np.isnan(p_boot) else np.nan,
    'cox_HR_eu_funding': float(hr_funding) if not np.isnan(hr_funding) else np.nan,
    'cox_p_eu_funding': float(p_funding) if not np.isnan(p_funding) else np.nan,
    'logrank_chi2': float(lr.test_statistic),
    'logrank_p': float(lr.p_value),
    'did_aggregate_eu_vs_noneu': float(did_if),
    'comparison_p25_45q': -0.147,
}])
summary.to_csv(OUTPUT_DIR / 'pijler26_summary.csv', index=False)
fund_outcomes.to_csv(OUTPUT_DIR / 'pijler26_funding_outcomes.csv', index=False)
rate_df_eu.to_csv(OUTPUT_DIR / 'pijler26_eu_vs_noneu_panel.csv', index=False)


# === EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 26 (Innovation Fund effect op EU)")
print("=" * 78)
print(f"""
SAMPLE:
  EU Blue+Green totaal:    {len(eu)}
  Met EU funding labeled:  {eu['has_eu_funding'].sum()} ({eu['has_eu_funding'].mean()*100:.1f}%)
  Innovation Fund specifiek: {(eu['funding_type'] == 'EU_Innovation_Fund').sum()}

NAIVE COMPARISON (selection-biased upper bound):
  Funded cancel rate:    {funded['cancelled'].mean():.4f}
  Unfunded cancel rate:  {unfunded['cancelled'].mean():.4f}
  Naive Δ:               {naive_diff_cancel:+.4f}

MATCHED ATT (selection-adjusted):
  ATT cancel rate:       {att_cancel if not np.isnan(att_cancel) else 'n/a':+.4f}  CI [{ci_lo:+.4f}, {ci_hi:+.4f}]
  Bootstrap p:           {p_boot:.4f}  {'***' if p_boot<0.001 else '**' if p_boot<0.01 else '*' if p_boot<0.05 else '.' if p_boot<0.1 else 'NS'}

COX PH (EU sample):
  HR_has_eu_funding:     {hr_funding:.3f}  p = {p_funding:.4f}

LOG-RANK TEST:
  χ² = {lr.test_statistic:.2f}, p = {lr.p_value:.4f}

COMPARISON MET PIJLER 25 (US 45Q):
  US 45Q ATT:            -0.147 (p = 0.020 *)
  EU Innovation Fund ATT: {att_cancel:+.4f} (p = {p_boot:.4f})

BELEIDSCONCLUSIE:
""")

if not np.isnan(p_boot):
    if p_boot < 0.05 and att_cancel < 0:
        print("  ✓ EU Innovation Fund heeft MEETBAAR protective effect")
        print("  → EU heeft al een 45Q-equivalent dat werkt")
        print("  → Schaal vergroten heeft beleidsgevolg")
    elif p_boot < 0.10 and att_cancel < 0:
        print("  (.) Marginaal evidence — EU Innovation Fund mogelijk effectief")
        print("  → Sample is klein (n=25 funded), meer data nodig")
    elif att_cancel > 0:
        print("  ⚠ Funded projecten hebben HOGERE cancellation rate")
        print("  → Vermoedelijk niet causaal (riskante projecten zoeken funding)")
        print("  → EU 45Q-equivalent moet anders worden ontworpen")
    else:
        print("  ⊘ Geen significant effect detected")
        print("  → EU mist nog effectief carrot mechanism vergelijkbaar met US 45Q")
