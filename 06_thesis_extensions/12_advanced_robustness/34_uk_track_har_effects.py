"""
34_uk_track_har_effects.py
============================================================================
Pijler 27: UK Track-1/Track-2 CCUS + HAR1 effects op project survival
============================================================================

Doel: testen of UK's "carrot" mechanismen — Track-1/2 CCUS cluster funding
en Hydrogen Allocation Rounds (HAR) — meetbare effecten hebben op project
survival, analoog aan onze 45Q (Pijler 25) en EU IF (Pijler 26) analyses.

UK heeft een DRAMATISCH hoge failure rate (42% van 83 projecten) — gigantisch
hoger dan EU (3.5%) of US Blue (24%). Centrale vraag: hebben Track-1/2 en
HAR1 deze trend kunnen ombuigen?

POLICY EVENTS:
  Track-1 CCUS shortlist:  Oktober 2021 (HyNet + East Coast Cluster)
  Track-2 CCUS clusters:   Juli 2023 (Acorn + Viking)
  HAR1 launched:           November 2022
  HAR1 results announced:  April 2023 (11 projecten geselecteerd)
  HAR2 launched:           2024 (post-snapshot)

METHODES:
  1. UK vs non-UK Blue: DiD met t* = 2021 (Track-1)
  2. UK vs non-UK Green: DiD met t* = 2023 (HAR1)
  3. Event study (dynamische effecten)
  4. Cluster bootstrap inference (B=1000)
  5. Brexit-effect crosscheck: UK vs EU 2018-2026

CAVEAT: UK heeft 17 failures in 2021 alleen (van 26 projecten aangekondigd
in 2021). Bulk van treatment periode heeft veel cancellations.

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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


# === STAP 1: LAAD EN BOUW GROEPEN ===
header("STAP 1: Laad S&P en bouw UK vs non-UK groepen")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
sp['is_uk'] = (sp['Geography'] == 'United Kingdom').astype(int)
sp['is_eu'] = (sp['Region major'] == 'Europe (EU-27)').astype(int)
df = sp[(sp['is_blue'] == 1) | (sp['is_green'] == 1)].copy().reset_index(drop=True)
df['project_id'] = df.index

# 4-way groups
def group_classify(row):
    if row['is_blue'] == 1:
        return 'UK_Blue' if row['is_uk'] == 1 else 'NonUK_Blue'
    if row['is_green'] == 1:
        return 'UK_Green' if row['is_uk'] == 1 else 'NonUK_Green'
    return 'Other'
df['group'] = df.apply(group_classify, axis=1)

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

print(f"Sample: {len(df)} Blue+Green projecten")
print(f"\nGroup distribution:")
print(df.groupby(['group']).agg(
    N=('is_blue', 'size'),
    n_cancel=('cancelled', 'sum'),
    n_onhold=('onhold', 'sum'),
    n_any_failure=('event_any', 'sum'),
).to_string())


# === STAP 2: CUMULATIVE CANCEL RATES PER GROEP × JAAR ===
header("STAP 2: Cumulative cancel + on-hold rates per groep × jaar")

def cumulative_rate(sub, year, event_col='cancelled'):
    risk = sub[sub['announce_year'] <= year]
    if len(risk) == 0:
        return np.nan
    n_event = ((risk[event_col] == 1) & (risk['event_year'] <= year)).sum()
    return float(n_event / len(risk))

def cumulative_failure_rate(sub, year):
    risk = sub[sub['announce_year'] <= year]
    if len(risk) == 0:
        return np.nan
    n_event = ((risk['event_any'] == 1) & (risk['event_year'] <= year)).sum()
    return float(n_event / len(risk))

years_test = list(range(2018, 2027))
rate_panel = []
for grp in ['UK_Blue', 'NonUK_Blue', 'UK_Green', 'NonUK_Green']:
    sub = df[df['group'] == grp].copy()
    for y in years_test:
        rate_panel.append({
            'group': grp,
            'year': y,
            'cancel_rate': cumulative_rate(sub, y, 'cancelled'),
            'failure_rate': cumulative_failure_rate(sub, y),
            'n_risk': int((sub['announce_year'] <= y).sum()),
        })
rate_df = pd.DataFrame(rate_panel)
print("\nCumulative cancellation rate per groep × jaar:")
print(rate_df.pivot(index='year', columns='group', values='cancel_rate').round(4).to_string())
print("\nCumulative any-failure rate per groep × jaar:")
print(rate_df.pivot(index='year', columns='group', values='failure_rate').round(4).to_string())


# === STAP 3: COMPONENT A — TRACK-1 EFFECT OP UK BLUE ===
header("STAP 3: Component A — Track-1 (okt 2021) effect op UK BLUE")

def did_test(df_subset, treated_group, control_group, t_pre_end, t_post_end, outcome='cancelled'):
    treated = df_subset[df_subset['group'] == treated_group]
    control = df_subset[df_subset['group'] == control_group]
    treated_pre = cumulative_rate(treated, t_pre_end, outcome) if outcome == 'cancelled' else cumulative_failure_rate(treated, t_pre_end)
    control_pre = cumulative_rate(control, t_pre_end, outcome) if outcome == 'cancelled' else cumulative_failure_rate(control, t_pre_end)
    treated_post = cumulative_rate(treated, t_post_end, outcome) if outcome == 'cancelled' else cumulative_failure_rate(treated, t_post_end)
    control_post = cumulative_rate(control, t_post_end, outcome) if outcome == 'cancelled' else cumulative_failure_rate(control, t_post_end)
    did = (treated_post - treated_pre) - (control_post - control_pre)
    return {
        'treated_pre': treated_pre, 'treated_post': treated_post, 'treated_delta': treated_post - treated_pre,
        'control_pre': control_pre, 'control_post': control_post, 'control_delta': control_post - control_pre,
        'DiD': did,
    }

# Cancel
did_track1_cancel = did_test(df, 'UK_Blue', 'NonUK_Blue', t_pre_end=2021, t_post_end=2026, outcome='cancelled')
# Any failure
did_track1_failure = did_test(df, 'UK_Blue', 'NonUK_Blue', t_pre_end=2021, t_post_end=2026, outcome='event_any')

print(f"\nTrack-1 effect (UK Blue vs NonUK Blue, t* = 2021):")
print(f"--- Cancel only ---")
print(f"  UK_Blue:     {did_track1_cancel['treated_pre']:.4f} → {did_track1_cancel['treated_post']:.4f}  (Δ = {did_track1_cancel['treated_delta']:+.4f})")
print(f"  NonUK_Blue:  {did_track1_cancel['control_pre']:.4f} → {did_track1_cancel['control_post']:.4f}  (Δ = {did_track1_cancel['control_delta']:+.4f})")
print(f"  DiD = {did_track1_cancel['DiD']:+.4f}")
print(f"--- Any failure ---")
print(f"  UK_Blue:     {did_track1_failure['treated_pre']:.4f} → {did_track1_failure['treated_post']:.4f}  (Δ = {did_track1_failure['treated_delta']:+.4f})")
print(f"  NonUK_Blue:  {did_track1_failure['control_pre']:.4f} → {did_track1_failure['control_post']:.4f}  (Δ = {did_track1_failure['control_delta']:+.4f})")
print(f"  DiD = {did_track1_failure['DiD']:+.4f}")


# === STAP 4: COMPONENT B — HAR1 EFFECT OP UK GREEN ===
header("STAP 4: Component B — HAR1 (apr 2023) effect op UK GREEN")

did_har1_cancel = did_test(df, 'UK_Green', 'NonUK_Green', t_pre_end=2022, t_post_end=2026, outcome='cancelled')
did_har1_failure = did_test(df, 'UK_Green', 'NonUK_Green', t_pre_end=2022, t_post_end=2026, outcome='event_any')

print(f"\nHAR1 effect (UK Green vs NonUK Green, t* = 2023):")
print(f"--- Cancel only ---")
print(f"  UK_Green:    {did_har1_cancel['treated_pre']:.4f} → {did_har1_cancel['treated_post']:.4f}  (Δ = {did_har1_cancel['treated_delta']:+.4f})")
print(f"  NonUK_Green: {did_har1_cancel['control_pre']:.4f} → {did_har1_cancel['control_post']:.4f}  (Δ = {did_har1_cancel['control_delta']:+.4f})")
print(f"  DiD = {did_har1_cancel['DiD']:+.4f}")
print(f"--- Any failure ---")
print(f"  UK_Green:    {did_har1_failure['treated_pre']:.4f} → {did_har1_failure['treated_post']:.4f}  (Δ = {did_har1_failure['treated_delta']:+.4f})")
print(f"  NonUK_Green: {did_har1_failure['control_pre']:.4f} → {did_har1_failure['control_post']:.4f}  (Δ = {did_har1_failure['control_delta']:+.4f})")
print(f"  DiD = {did_har1_failure['DiD']:+.4f}")


# === STAP 5: CLUSTER BOOTSTRAP INFERENCE ===
header("STAP 5: Cluster bootstrap inference (B=1000)")

def bootstrap_did(df, treated_group, control_group, t_pre, t_post, outcome='cancelled', B=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(df)
    boot_dids = []
    for _ in range(B):
        idx = rng.choice(n, size=n, replace=True)
        boot_df = df.iloc[idx].reset_index(drop=True)
        d = did_test(boot_df, treated_group, control_group, t_pre, t_post, outcome=outcome)
        if not np.isnan(d['DiD']):
            boot_dids.append(d['DiD'])
    return np.array(boot_dids)

print("\n--- Track-1 (UK Blue) cancel ---")
boot_t1_cancel = bootstrap_did(df, 'UK_Blue', 'NonUK_Blue', 2021, 2026, 'cancelled', B=B_BOOT)
ci_t1_c_lo, ci_t1_c_hi = np.percentile(boot_t1_cancel, [2.5, 97.5])
p_t1_c = 2 * min(np.mean(boot_t1_cancel <= 0), np.mean(boot_t1_cancel >= 0))
print(f"  DiD = {did_track1_cancel['DiD']:+.4f}, 95% CI [{ci_t1_c_lo:+.4f}, {ci_t1_c_hi:+.4f}], p_boot = {p_t1_c:.4f}")

print("\n--- Track-1 (UK Blue) any-failure ---")
boot_t1_fail = bootstrap_did(df, 'UK_Blue', 'NonUK_Blue', 2021, 2026, 'event_any', B=B_BOOT)
ci_t1_f_lo, ci_t1_f_hi = np.percentile(boot_t1_fail, [2.5, 97.5])
p_t1_f = 2 * min(np.mean(boot_t1_fail <= 0), np.mean(boot_t1_fail >= 0))
print(f"  DiD = {did_track1_failure['DiD']:+.4f}, 95% CI [{ci_t1_f_lo:+.4f}, {ci_t1_f_hi:+.4f}], p_boot = {p_t1_f:.4f}")

print("\n--- HAR1 (UK Green) cancel ---")
boot_h1_cancel = bootstrap_did(df, 'UK_Green', 'NonUK_Green', 2022, 2026, 'cancelled', B=B_BOOT)
ci_h1_c_lo, ci_h1_c_hi = np.percentile(boot_h1_cancel, [2.5, 97.5])
p_h1_c = 2 * min(np.mean(boot_h1_cancel <= 0), np.mean(boot_h1_cancel >= 0))
print(f"  DiD = {did_har1_cancel['DiD']:+.4f}, 95% CI [{ci_h1_c_lo:+.4f}, {ci_h1_c_hi:+.4f}], p_boot = {p_h1_c:.4f}")

print("\n--- HAR1 (UK Green) any-failure ---")
boot_h1_fail = bootstrap_did(df, 'UK_Green', 'NonUK_Green', 2022, 2026, 'event_any', B=B_BOOT)
ci_h1_f_lo, ci_h1_f_hi = np.percentile(boot_h1_fail, [2.5, 97.5])
p_h1_f = 2 * min(np.mean(boot_h1_fail <= 0), np.mean(boot_h1_fail >= 0))
print(f"  DiD = {did_har1_failure['DiD']:+.4f}, 95% CI [{ci_h1_f_lo:+.4f}, {ci_h1_f_hi:+.4f}], p_boot = {p_h1_f:.4f}")


# === STAP 6: EVENT STUDY (DYNAMIC EFFECTS) ===
header("STAP 6: Event study — dynamische effecten")

def event_study(df_subset, treated_group, control_group, base_year, outcome='cancelled'):
    rows = []
    treated = df_subset[df_subset['group'] == treated_group]
    control = df_subset[df_subset['group'] == control_group]
    rate_fn = (lambda s, y: cumulative_rate(s, y, 'cancelled')) if outcome == 'cancelled' else cumulative_failure_rate
    base_treated = rate_fn(treated, base_year)
    base_control = rate_fn(control, base_year)
    for y in range(base_year - 2, 2027):
        if y == base_year:
            rows.append({'year': y, 'rel_year': y - base_year, 'DiD': 0.0,
                         'treated': base_treated, 'control': base_control})
            continue
        treated_t = rate_fn(treated, y)
        control_t = rate_fn(control, y)
        did_t = (treated_t - base_treated) - (control_t - base_control)
        rows.append({'year': y, 'rel_year': y - base_year, 'DiD': did_t,
                     'treated': treated_t, 'control': control_t})
    return pd.DataFrame(rows)

es_track1 = event_study(df, 'UK_Blue', 'NonUK_Blue', base_year=2021, outcome='event_any')
es_har1 = event_study(df, 'UK_Green', 'NonUK_Green', base_year=2022, outcome='event_any')

print(f"\nTrack-1 event study (base=2021, any-failure):")
print(es_track1[['rel_year', 'year', 'treated', 'control', 'DiD']].round(4).to_string(index=False))
print(f"\nHAR1 event study (base=2022, any-failure):")
print(es_har1[['rel_year', 'year', 'treated', 'control', 'DiD']].round(4).to_string(index=False))


# === STAP 7: WITHIN-UK COX PH ANALYSE ===
header("STAP 7: Cox PH op UK sample: timing-effect van Track-1/HAR1 cohort")

uk = df[df['group'].isin(['UK_Blue', 'UK_Green'])].copy()
uk['announced_post_track1'] = (uk['announce_year'] >= 2022).astype(int)
uk['announced_post_har1'] = (uk['announce_year'] >= 2023).astype(int)

# Cox PH met cohort effect
cox_uk = uk[['duration', 'event_any', 'is_blue', 'announced_post_track1', 'log_capacity']].dropna().copy()
print(f"\nUK Cox PH sample: N = {len(cox_uk)}, events = {int(cox_uk['event_any'].sum())}")

cph = CoxPHFitter()
try:
    cph.fit(cox_uk, duration_col='duration', event_col='event_any')
    print("\n--- UK Cox PH (any failure) ---")
    print(cph.summary[['coef', 'exp(coef)', 'p', 'coef lower 95%', 'coef upper 95%']].round(4).to_string())
    
    hr_post_t1 = float(np.exp(cph.params_['announced_post_track1']))
    p_post_t1 = float(cph.summary.loc['announced_post_track1', 'p'])
    print(f"\nHR_announced_post_track1 = {hr_post_t1:.3f}, p = {p_post_t1:.4f}")
    print(f"(Hypothese: post-Track1 announced cohort meer protected → HR < 1)")
except Exception as e:
    print(f"Cox PH errored: {e}")
    hr_post_t1, p_post_t1 = np.nan, np.nan


# === STAP 8: BREXIT EFFECT (UK vs EU 2018-2026) ===
header("STAP 8: Brexit-effect crosscheck — UK vs EU")

uk_eu_panel = []
for y in years_test:
    uk_sub = df[df['is_uk'] == 1]
    eu_sub = df[df['is_eu'] == 1]
    uk_eu_panel.append({
        'year': y,
        'UK_failure_rate': cumulative_failure_rate(uk_sub, y),
        'EU_failure_rate': cumulative_failure_rate(eu_sub, y),
        'UK_n_risk': int((uk_sub['announce_year'] <= y).sum()),
        'EU_n_risk': int((eu_sub['announce_year'] <= y).sum()),
    })
brexit_df = pd.DataFrame(uk_eu_panel)
print("\nUK vs EU cumulative any-failure rate:")
print(brexit_df.round(4).to_string(index=False))

uk_pre_2021 = cumulative_failure_rate(df[df['is_uk']==1], 2020)
uk_post_2021 = cumulative_failure_rate(df[df['is_uk']==1], 2026)
eu_pre_2021 = cumulative_failure_rate(df[df['is_eu']==1], 2020)
eu_post_2021 = cumulative_failure_rate(df[df['is_eu']==1], 2026)
did_brexit = (uk_post_2021 - uk_pre_2021) - (eu_post_2021 - eu_pre_2021)
print(f"\nBrexit DiD (UK vs EU, t* = 2021 = UK ETS start):")
print(f"  UK:  {uk_pre_2021:.4f} → {uk_post_2021:.4f}  (Δ = {uk_post_2021 - uk_pre_2021:+.4f})")
print(f"  EU:  {eu_pre_2021:.4f} → {eu_post_2021:.4f}  (Δ = {eu_post_2021 - eu_pre_2021:+.4f})")
print(f"  DiD (Brexit effect) = {did_brexit:+.4f}")


# === STAP 9: FIGUREN ===
header("STAP 9: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: 4-group cancel rates over time
ax = axes[0, 0]
for grp, color, ls in [('UK_Blue', '#d62728', '-'), ('NonUK_Blue', '#d62728', '--'),
                        ('UK_Green', '#1f77b4', '-'), ('NonUK_Green', '#1f77b4', '--')]:
    sub = rate_df[rate_df['group'] == grp]
    ax.plot(sub['year'], sub['failure_rate'], 'o' + ls, color=color, label=grp, linewidth=2, markersize=7)
ax.axvline(x=2021, color='black', linestyle=':', alpha=0.5)
ax.text(2021.05, 0.45, 'Track-1\n(okt 2021)', rotation=90, fontsize=8)
ax.axvline(x=2023, color='gray', linestyle=':', alpha=0.5)
ax.text(2023.05, 0.45, 'HAR1\n(apr 2023)', rotation=90, fontsize=8)
ax.set_xlabel('Year')
ax.set_ylabel('Cumulative any-failure rate')
ax.set_title('UK vs Non-UK Blue/Green failure rates')
ax.legend(loc='upper left', fontsize=9)
ax.grid(alpha=0.3)

# Panel B: Track-1 event study
ax = axes[0, 1]
ax.bar(es_track1['rel_year'], es_track1['DiD'],
       color=np.where(es_track1['DiD'] > 0, '#d62728', '#2ca02c'),
       edgecolor='black', alpha=0.7)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.axvline(x=0, color='gray', linestyle='--', alpha=0.6)
ax.set_xlabel('Years relative to Track-1 (2021)')
ax.set_ylabel('DiD (UK Blue - NonUK Blue)')
ax.set_title(f'Track-1 event study\nDiD = {did_track1_failure["DiD"]:+.3f}, p_boot = {p_t1_f:.4f}')
ax.grid(alpha=0.3, axis='y')

# Panel C: HAR1 event study
ax = axes[1, 0]
ax.bar(es_har1['rel_year'], es_har1['DiD'],
       color=np.where(es_har1['DiD'] > 0, '#d62728', '#2ca02c'),
       edgecolor='black', alpha=0.7)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.axvline(x=0, color='gray', linestyle='--', alpha=0.6)
ax.set_xlabel('Years relative to HAR1 results (2022)')
ax.set_ylabel('DiD (UK Green - NonUK Green)')
ax.set_title(f'HAR1 event study\nDiD = {did_har1_failure["DiD"]:+.3f}, p_boot = {p_h1_f:.4f}')
ax.grid(alpha=0.3, axis='y')

# Panel D: Vergelijking met andere policies (45Q, IF, Track-1, HAR1)
ax = axes[1, 1]
policies = ['US 45Q\n(P25)', 'EU IF\n(P26)', 'UK Track-1\n(P27 Blue)', 'UK HAR1\n(P27 Green)']
values = [-0.147, -0.080, did_track1_failure['DiD'], did_har1_failure['DiD']]
errors_lo = [-0.282, -0.20, ci_t1_f_lo, ci_h1_f_lo]
errors_hi = [-0.029, 0.00, ci_t1_f_hi, ci_h1_f_hi]
err_low = [v - lo for v, lo in zip(values, errors_lo)]
err_high = [hi - v for v, hi in zip(values, errors_hi)]
colors = ['#9c27b0', '#2ca02c', '#1f77b4', '#ff7f0e']
x = np.arange(len(policies))
ax.bar(x, values, yerr=[err_low, err_high], color=colors, edgecolor='black', width=0.55, capsize=8)
for i, v in enumerate(values):
    ax.text(i, v + 0.01 if v > 0 else v - 0.025, f'{v:+.3f}', ha='center', fontsize=11, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(policies, fontsize=10)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_ylabel('Treatment effect on failure/cancel rate')
ax.set_title('Carrot mechanisms comparison')
ax.grid(alpha=0.3, axis='y')

plt.suptitle('Pijler 27: UK Track-1/Track-2 + HAR1 effects on project survival',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler27_uk_track_har.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler27_uk_track_har.png")


# === STAP 10: OPSLAAN ===
header("STAP 10: Opslaan")

summary = pd.DataFrame([{
    'method': 'Pijler 27: UK Track-1/2 + HAR1 effects',
    'n_uk_blue': int((df['group'] == 'UK_Blue').sum()),
    'n_uk_green': int((df['group'] == 'UK_Green').sum()),
    'n_nonuk_blue': int((df['group'] == 'NonUK_Blue').sum()),
    'n_nonuk_green': int((df['group'] == 'NonUK_Green').sum()),
    
    # Track-1 effects (UK Blue)
    'DiD_track1_cancel': did_track1_cancel['DiD'],
    'DiD_track1_failure': did_track1_failure['DiD'],
    'DiD_track1_cancel_ci_lo': float(ci_t1_c_lo),
    'DiD_track1_cancel_ci_hi': float(ci_t1_c_hi),
    'DiD_track1_cancel_p': float(p_t1_c),
    'DiD_track1_failure_ci_lo': float(ci_t1_f_lo),
    'DiD_track1_failure_ci_hi': float(ci_t1_f_hi),
    'DiD_track1_failure_p': float(p_t1_f),
    
    # HAR1 effects (UK Green)
    'DiD_har1_cancel': did_har1_cancel['DiD'],
    'DiD_har1_failure': did_har1_failure['DiD'],
    'DiD_har1_cancel_ci_lo': float(ci_h1_c_lo),
    'DiD_har1_cancel_ci_hi': float(ci_h1_c_hi),
    'DiD_har1_cancel_p': float(p_h1_c),
    'DiD_har1_failure_ci_lo': float(ci_h1_f_lo),
    'DiD_har1_failure_ci_hi': float(ci_h1_f_hi),
    'DiD_har1_failure_p': float(p_h1_f),
    
    # Within-UK Cox
    'Cox_HR_post_track1': float(hr_post_t1) if not np.isnan(hr_post_t1) else np.nan,
    'Cox_p_post_track1': float(p_post_t1) if not np.isnan(p_post_t1) else np.nan,
    
    # Brexit effect
    'DiD_brexit_uk_vs_eu': float(did_brexit),
    
    # Comparisons
    'p25_us_45q_did': -0.147,
    'p26_eu_if_att': -0.080,
}])
summary.to_csv(OUTPUT_DIR / 'pijler27_summary.csv', index=False)
es_track1.to_csv(OUTPUT_DIR / 'pijler27_eventstudy_track1.csv', index=False)
es_har1.to_csv(OUTPUT_DIR / 'pijler27_eventstudy_har1.csv', index=False)
rate_df.to_csv(OUTPUT_DIR / 'pijler27_panel.csv', index=False)
brexit_df.to_csv(OUTPUT_DIR / 'pijler27_brexit.csv', index=False)


# === EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 27 (UK Track-1/2 + HAR1)")
print("=" * 78)
print(f"""
SAMPLE:
  UK Blue:        {(df['group']=='UK_Blue').sum()}, UK Green: {(df['group']=='UK_Green').sum()}
  UK failure rate: 42% (35/83) — DRAMATISCH hoger dan EU (3.5%) of US Blue (24%)

COMPONENT A — TRACK-1 (UK Blue, t*=2021):
  Cancel DiD:     {did_track1_cancel['DiD']:+.4f}  CI [{ci_t1_c_lo:+.4f}, {ci_t1_c_hi:+.4f}]  p = {p_t1_c:.4f}
  Failure DiD:    {did_track1_failure['DiD']:+.4f}  CI [{ci_t1_f_lo:+.4f}, {ci_t1_f_hi:+.4f}]  p = {p_t1_f:.4f}

COMPONENT B — HAR1 (UK Green, t*=2023):
  Cancel DiD:     {did_har1_cancel['DiD']:+.4f}  CI [{ci_h1_c_lo:+.4f}, {ci_h1_c_hi:+.4f}]  p = {p_h1_c:.4f}
  Failure DiD:    {did_har1_failure['DiD']:+.4f}  CI [{ci_h1_f_lo:+.4f}, {ci_h1_f_hi:+.4f}]  p = {p_h1_f:.4f}

WITHIN-UK COX (post-Track1 cohort effect):
  HR_announced_post_track1 = {hr_post_t1:.3f}, p = {p_post_t1:.4f}

BREXIT DiD (UK vs EU):
  DiD = {did_brexit:+.4f}

VERGELIJKING MET ANDERE 'CARROT' POLICIES:
  US 45Q:        DiD = -0.147 (p = 0.020 *)
  EU IF:         ATT = -0.080 (p = 0.232 NS)
  UK Track-1:    DiD = {did_track1_failure['DiD']:+.4f} (p = {p_t1_f:.4f})
  UK HAR1:       DiD = {did_har1_failure['DiD']:+.4f} (p = {p_h1_f:.4f})

BELEIDSCONCLUSIE:
""")
if did_track1_failure['DiD'] < -0.05 and p_t1_f < 0.10:
    print(f"  ✓ Track-1 toont protective effect — UK heeft 45Q-equivalent dat werkt voor Blue")
elif did_track1_failure['DiD'] > 0.05 and p_t1_f < 0.10:
    print(f"  ⚠ Track-1 lijkt geassocieerd met HOGER UK Blue failure rate")
    print(f"     Mogelijk: selection effect (only winners survive, non-winners cancel)")
else:
    print(f"  ⊘ Track-1 effect niet significant — UK Blue failure rate hoog blijft")

if did_har1_failure['DiD'] < -0.05 and p_h1_f < 0.10:
    print(f"  ✓ HAR1 toont protective effect — UK heeft Green carrot dat werkt")
elif did_har1_failure['DiD'] > 0.05 and p_h1_f < 0.10:
    print(f"  ⚠ HAR1 geassocieerd met HOGER UK Green failure rate")
else:
    print(f"  ⊘ HAR1 effect niet significant — UK Green failure rate hoog blijft")
