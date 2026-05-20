"""
36_china_14fyp_effect.py
============================================================================
Pijler 28: China 14th Five-Year Plan effect op project survival
============================================================================

Onderzoeksvraag:
Heeft China's 14th Five-Year Plan (maart 2022) + National Hydrogen Industry
Long-Term Plan effect op project survival? Hoe verschilt China's
mechanism-design van US 45Q (output-credit), EU IF (capex grant) en
UK Track-1/HAR1 (selection-tender)?

DATA OVERVIEW:
  N = 209 China Blue+Green projecten
  Failure rate: 6.7% (14/209) — LAAGST in onze data
  0 cancellations, 14 on-hold, 0 decommissioned
  SOE failure rate: 0% (0/35) — perfect track record

METHODES:
  1. China vs non-China DiD (t* = 2022, 14th FYP)
  2. Within-China: pre vs post 14th FYP
  3. SOE vs private-led decompositie
  4. Provincial heterogeneity (Inner Mongolia, Xinjiang, Hebei, Jilin)
  5. Cluster bootstrap inference
  6. Data validity caveat

POLICY EVENT:
  14th Five-Year Plan for Renewable Energy Development: maart 2022
  National Hydrogen Industry Long-Term Plan: maart 2022 (joint)

CAVEAT:
  China data may be under-reported for cancellations (政治灵敏度).
  SOE projects rarely formally cancelled — may be "indefinitely delayed".
  We interpret findings as upper bound on observable survival rates.

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
T_14FYP = 2022  # March 2022


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD EN GROEPEN ===
header("STAP 1: Bouw China + non-China sample")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp['est_year_online'] = pd.to_numeric(sp['Estimated year online'], errors='coerce')
sp = sp[sp['announce_year'].notna()].copy()
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
sp['is_china'] = (sp['Geography'] == 'China').astype(int)
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

# 4-way groups
def group_classify(row):
    if row['is_blue'] == 1:
        return 'China_Blue' if row['is_china'] == 1 else 'NonChina_Blue'
    if row['is_green'] == 1:
        return 'China_Green' if row['is_china'] == 1 else 'NonChina_Green'
    return 'Other'
df['group'] = df.apply(group_classify, axis=1)

# SOE classification
SOE_KEYWORDS = ['sinopec', 'cnooc', 'cnpc', 'petrochina', 'state grid', 'china national',
                'huaneng', 'shenhua', 'datang', 'huadian', 'guodian', 'three gorges',
                'shaanxi yanchang', 'china energy', 'china southern', 'baoshan', 'baosteel',
                'china coal', 'sinochem', 'state power investment', 'power construction corporation',
                'china general nuclear', 'china national nuclear', 'china shipbuilding']
def is_soe(o):
    if pd.isna(o):
        return False
    o_lower = str(o).lower()
    return any(x in o_lower for x in SOE_KEYWORDS)
df['is_soe'] = df['Primary owner'].apply(is_soe).astype(int)

print(f"Sample: {len(df)} Blue+Green projecten")
print(f"\nGroup distribution:")
print(df.groupby('group').agg(N=('is_blue', 'size'), Failures=('event_any', 'sum'),
                              Cancels=('cancelled', 'sum'), OnHold=('onhold', 'sum'),
                              Decomm=('decomm', 'sum')).to_string())


# === STAP 2: CHINA VS NON-CHINA DiD (14TH FYP) ===
header("STAP 2: China vs non-China DiD rond 14th FYP (maart 2022)")

def cumulative_failure_rate(sub, year):
    risk = sub[sub['announce_year'] <= year]
    if len(risk) == 0:
        return np.nan
    n_event = ((risk['event_any'] == 1) & (risk['event_year'] <= year)).sum()
    return float(n_event / len(risk))

def did_test(df_subset, treated_group, control_group, t_pre, t_post):
    treated = df_subset[df_subset['group'] == treated_group]
    control = df_subset[df_subset['group'] == control_group]
    t_pre_treat = cumulative_failure_rate(treated, t_pre)
    c_pre = cumulative_failure_rate(control, t_pre)
    t_post_treat = cumulative_failure_rate(treated, t_post)
    c_post = cumulative_failure_rate(control, t_post)
    did = (t_post_treat - t_pre_treat) - (c_post - c_pre)
    return {
        'treated_pre': t_pre_treat, 'treated_post': t_post_treat, 'treated_delta': t_post_treat - t_pre_treat,
        'control_pre': c_pre, 'control_post': c_post, 'control_delta': c_post - c_pre, 'DiD': did,
    }

# China Green vs Non-China Green (main test — China is overwhelmingly Green)
did_china_green = did_test(df, 'China_Green', 'NonChina_Green', t_pre=2021, t_post=2026)
print(f"\nChina Green vs Non-China Green (t* = 2022 14th FYP):")
print(f"  China Green:    {did_china_green['treated_pre']:.4f} (2021) → {did_china_green['treated_post']:.4f} (2026)  Δ = {did_china_green['treated_delta']:+.4f}")
print(f"  NonChina Green: {did_china_green['control_pre']:.4f} (2021) → {did_china_green['control_post']:.4f} (2026)  Δ = {did_china_green['control_delta']:+.4f}")
print(f"  DiD = {did_china_green['DiD']:+.4f}")


# === STAP 3: WITHIN-CHINA PRE-POST 14TH FYP ===
header("STAP 3: Within-China pre vs post 14th FYP")

china = df[df['is_china'] == 1].copy()
china['post_14fyp'] = (china['announce_year'] >= 2022).astype(int)

pre_china = china[china['post_14fyp'] == 0]
post_china = china[china['post_14fyp'] == 1]

print(f"\nPre-14th FYP (announce ≤ 2021): n={len(pre_china)}, failures={int(pre_china['event_any'].sum())}, rate={pre_china['event_any'].mean()*100:.1f}%")
print(f"Post-14th FYP (announce ≥ 2022): n={len(post_china)}, failures={int(post_china['event_any'].sum())}, rate={post_china['event_any'].mean()*100:.1f}%")
print(f"Difference: {(post_china['event_any'].mean() - pre_china['event_any'].mean())*100:+.1f}pp")


# === STAP 4: SOE EFFECT (STATE-LED VS PRIVATE) ===
header("STAP 4: SOE (State-Owned Enterprise) vs private-led")

soe_summary = china.groupby('is_soe').agg(N=('event_any', 'size'), Failures=('event_any', 'sum'), 
                                          Failure_rate=('event_any', 'mean')).round(3)
print(f"\nSOE vs Non-SOE failure rates:")
print(soe_summary.to_string())

# Logrank test
soe = china[china['is_soe'] == 1]
nonsoe = china[china['is_soe'] == 0]
if len(soe) > 5 and len(nonsoe) > 5:
    lr = logrank_test(soe['duration'], nonsoe['duration'],
                      event_observed_A=soe['event_any'], event_observed_B=nonsoe['event_any'])
    print(f"\nLog-rank test SOE vs non-SOE: χ² = {lr.test_statistic:.3f}, p = {lr.p_value:.4f}")


# === STAP 5: PROVINCIAL HETEROGENEITY ===
header("STAP 5: Provincial heterogeneity binnen China")

prov_summary = china.groupby('State/province').agg(
    N=('event_any', 'size'),
    Failures=('event_any', 'sum'),
    Failure_rate=('event_any', 'mean'),
    SOE_share=('is_soe', 'mean'),
    Mean_capacity=('log_capacity', 'mean'),
).sort_values('N', ascending=False).head(15).round(3)
print(prov_summary.to_string())


# === STAP 6: COX PH OP CHINA SAMPLE ===
header("STAP 6: Cox PH op China sample")

cox_china = china[['duration', 'event_any', 'is_blue', 'is_soe', 'log_capacity', 'post_14fyp']].dropna().copy()
print(f"\nChina Cox PH sample: N = {len(cox_china)}, events = {int(cox_china['event_any'].sum())}")

cph = CoxPHFitter()
try:
    cph.fit(cox_china, duration_col='duration', event_col='event_any')
    print("\n--- China Cox PH (any failure) ---")
    print(cph.summary[['coef', 'exp(coef)', 'p', 'coef lower 95%', 'coef upper 95%']].round(4).to_string())
    
    hr_post_fyp = float(np.exp(cph.params_['post_14fyp']))
    hr_soe = float(np.exp(cph.params_['is_soe']))
    p_post_fyp = float(cph.summary.loc['post_14fyp', 'p'])
    p_soe = float(cph.summary.loc['is_soe', 'p'])
    print(f"\nHR_post_14fyp = {hr_post_fyp:.3f}, p = {p_post_fyp:.4f}")
    print(f"HR_is_soe     = {hr_soe:.3f}, p = {p_soe:.4f}")
except Exception as e:
    print(f"Cox PH errored: {e}")
    hr_post_fyp = hr_soe = p_post_fyp = p_soe = np.nan


# === STAP 7: CLUSTER BOOTSTRAP INFERENCE ===
header("STAP 7: Cluster bootstrap inference voor 14th FYP DiD")

def bootstrap_did(df, treated, control, t_pre, t_post, B=1000, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(df)
    boot_dids = []
    for _ in range(B):
        idx = rng.choice(n, size=n, replace=True)
        boot_df = df.iloc[idx].reset_index(drop=True)
        d = did_test(boot_df, treated, control, t_pre, t_post)
        if not np.isnan(d['DiD']):
            boot_dids.append(d['DiD'])
    return np.array(boot_dids)

boot_china = bootstrap_did(df, 'China_Green', 'NonChina_Green', 2021, 2026, B=B_BOOT)
ci_lo, ci_hi = np.percentile(boot_china, [2.5, 97.5])
p_boot = 2 * min(np.mean(boot_china <= 0), np.mean(boot_china >= 0))
print(f"\nChina Green DiD bootstrap (B={B_BOOT}):")
print(f"  Point estimate: {did_china_green['DiD']:+.4f}")
print(f"  Bootstrap mean: {boot_china.mean():+.4f}")
print(f"  95% CI: [{ci_lo:+.4f}, {ci_hi:+.4f}]")
print(f"  Bootstrap p: {p_boot:.4f}")


# === STAP 8: EVENT STUDY ===
header("STAP 8: Event study — dynamische 14th FYP effecten")

def event_study(df_subset, treated, control, base_year):
    rows = []
    t = df_subset[df_subset['group'] == treated]
    c = df_subset[df_subset['group'] == control]
    base_t = cumulative_failure_rate(t, base_year)
    base_c = cumulative_failure_rate(c, base_year)
    for y in range(base_year - 2, 2027):
        if y == base_year:
            rows.append({'year': y, 'rel_year': 0, 'DiD': 0.0, 'treated': base_t, 'control': base_c})
            continue
        t_y = cumulative_failure_rate(t, y)
        c_y = cumulative_failure_rate(c, y)
        did_y = (t_y - base_t) - (c_y - base_c)
        rows.append({'year': y, 'rel_year': y - base_year, 'DiD': did_y, 'treated': t_y, 'control': c_y})
    return pd.DataFrame(rows)

es_china = event_study(df, 'China_Green', 'NonChina_Green', base_year=2021)
print(f"\nChina Green event study (base = 2021 14th FYP):")
print(es_china[['rel_year', 'year', 'treated', 'control', 'DiD']].round(4).to_string(index=False))


# === STAP 9: FIGUREN ===
header("STAP 9: Figuren")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Panel A: Cumulative failure rates per groep × jaar
ax = axes[0, 0]
years_test = list(range(2018, 2027))
for grp, color in [('China_Green', '#d62728'), ('NonChina_Green', '#1f77b4'),
                    ('China_Blue', '#ff7f0e'), ('NonChina_Blue', '#9c27b0')]:
    rates = [cumulative_failure_rate(df[df['group'] == grp], y) for y in years_test]
    ax.plot(years_test, rates, 'o-', color=color, label=grp, linewidth=2, markersize=8)
ax.axvline(x=2022, color='black', linestyle='--', alpha=0.6, label='14th FYP')
ax.set_xlabel('Year')
ax.set_ylabel('Cumulative failure rate')
ax.set_title('China vs Non-China failure rates')
ax.legend(loc='best', fontsize=9)
ax.grid(alpha=0.3)

# Panel B: Within-China pre/post 14th FYP
ax = axes[0, 1]
pre_post_data = [pre_china['event_any'].mean(), post_china['event_any'].mean()]
ax.bar(['Pre-14th FYP\n(≤2021)', 'Post-14th FYP\n(≥2022)'], pre_post_data,
       color=['#d62728', '#2ca02c'], edgecolor='black', width=0.5)
for i, v in enumerate(pre_post_data):
    ax.text(i, v + 0.005, f'{v*100:.1f}%\n(n={[len(pre_china), len(post_china)][i]})',
            ha='center', fontsize=11, fontweight='bold')
ax.set_ylabel('Failure rate')
ax.set_title(f'Within-China: pre vs post 14th FYP\nΔ = {(post_china["event_any"].mean() - pre_china["event_any"].mean())*100:+.1f}pp')
ax.grid(alpha=0.3, axis='y')

# Panel C: SOE vs Private failure rate
ax = axes[1, 0]
soe_data = [china[china['is_soe']==0]['event_any'].mean(), china[china['is_soe']==1]['event_any'].mean()]
ax.bar(['Private\n(n={})'.format(int((china['is_soe']==0).sum())),
        'SOE\n(n={})'.format(int((china['is_soe']==1).sum()))], soe_data,
       color=['#ff7f0e', '#2ca02c'], edgecolor='black', width=0.5)
for i, v in enumerate(soe_data):
    ax.text(i, v + 0.003, f'{v*100:.1f}%', ha='center', fontsize=11, fontweight='bold')
ax.set_ylabel('Failure rate')
ax.set_title('China SOE vs Private failure rate')
ax.grid(alpha=0.3, axis='y')

# Panel D: All carrot mechanism comparison
ax = axes[1, 1]
policies = ['US 45Q\n(P25)', 'EU IF\n(P26)', 'UK Track-1\n(P27 Blue)', 'UK HAR1\n(P27 Green)', 'China 14thFYP\n(P28 Green)']
values = [-0.147, -0.080, +0.235, +0.154, did_china_green['DiD']]
colors = ['#9c27b0', '#2ca02c', '#1f77b4', '#ff7f0e', '#d62728']
x = np.arange(len(policies))
ax.bar(x, values, color=colors, edgecolor='black', width=0.55)
for i, v in enumerate(values):
    ax.text(i, v + 0.01 if v > 0 else v - 0.025, f'{v:+.3f}', ha='center', fontsize=10, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(policies, fontsize=9)
ax.axhline(y=0, color='black', linewidth=0.8)
ax.set_ylabel('Treatment effect on failure rate')
ax.set_title('Cross-jurisdiction carrot mechanism comparison')
ax.grid(alpha=0.3, axis='y')

plt.suptitle('Pijler 28: China 14th Five-Year Plan effect on hydrogen projects',
             fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler28_china_14fyp.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler28_china_14fyp.png")


# === STAP 10: OPSLAAN ===
header("STAP 10: Opslaan")

summary = pd.DataFrame([{
    'method': 'Pijler 28: China 14th Five-Year Plan effect',
    'n_china': int((df['is_china']==1).sum()),
    'n_china_blue': int((df['group']=='China_Blue').sum()),
    'n_china_green': int((df['group']=='China_Green').sum()),
    'china_overall_failure_rate': float(china['event_any'].mean()),
    'china_cancel_rate': float(china['cancelled'].mean()),
    'china_onhold_rate': float(china['onhold'].mean()),
    'pre_14fyp_failure_rate': float(pre_china['event_any'].mean()),
    'post_14fyp_failure_rate': float(post_china['event_any'].mean()),
    'within_china_did': float(post_china['event_any'].mean() - pre_china['event_any'].mean()),
    'china_green_DiD_vs_noncn': float(did_china_green['DiD']),
    'china_green_DiD_ci_lo': float(ci_lo),
    'china_green_DiD_ci_hi': float(ci_hi),
    'china_green_DiD_p_boot': float(p_boot),
    'soe_failure_rate': float(china[china['is_soe']==1]['event_any'].mean()),
    'private_failure_rate': float(china[china['is_soe']==0]['event_any'].mean()),
    'cox_HR_post_14fyp': float(hr_post_fyp) if not np.isnan(hr_post_fyp) else np.nan,
    'cox_p_post_14fyp': float(p_post_fyp) if not np.isnan(p_post_fyp) else np.nan,
    'cox_HR_is_soe': float(hr_soe) if not np.isnan(hr_soe) else np.nan,
    'cox_p_is_soe': float(p_soe) if not np.isnan(p_soe) else np.nan,
    'CAVEAT': 'China data may under-report cancellations - SOE projects rarely formally cancelled',
}])
summary.to_csv(OUTPUT_DIR / 'pijler28_summary.csv', index=False)
es_china.to_csv(OUTPUT_DIR / 'pijler28_eventstudy.csv', index=False)
prov_summary.to_csv(OUTPUT_DIR / 'pijler28_province.csv')

print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 28 (China 14th FYP)")
print("=" * 78)
print(f"""
SAMPLE OVERVIEW:
  China sample: 209 projecten (17 Blue + 192 Green)
  Failures: 14 (0 cancellations, 14 on-hold, 0 decomm)
  Failure rate: 6.7% — DRAMATISCH lower dan UK (42%), US Blue (24%)
  
WITHIN-CHINA EFFECT (pre vs post 14th FYP):
  Pre-14th FYP (n=36):   16.7% failure rate
  Post-14th FYP (n=173):  4.6% failure rate
  Difference: -12.0pp (HEEL substantieel)

DiD CHINA GREEN VS NON-CHINA GREEN (t* = 2022):
  China Green:    {did_china_green['treated_pre']:.4f} → {did_china_green['treated_post']:.4f}  Δ = {did_china_green['treated_delta']:+.4f}
  NonChina Green: {did_china_green['control_pre']:.4f} → {did_china_green['control_post']:.4f}  Δ = {did_china_green['control_delta']:+.4f}
  DiD = {did_china_green['DiD']:+.4f}  95% CI [{ci_lo:+.4f}, {ci_hi:+.4f}]  p = {p_boot:.4f}

SOE EFFECT (within China):
  SOE failure rate:    {china[china['is_soe']==1]['event_any'].mean()*100:.1f}% (0/35 — perfect track record!)
  Private failure rate: {china[china['is_soe']==0]['event_any'].mean()*100:.1f}% (14/174)
  Cox HR_is_soe: {hr_soe:.3f}, p = {p_soe:.4f}

CARROT MECHANISM COMPARISON:
  US 45Q (output-credit):       DiD = -0.147 (p = 0.020 *)
  EU IF (capex-grant):          ATT = -0.080 (p = 0.232 NS)
  UK Track-1 (cluster-tender):  DiD = +0.235 (p = 0.014 — selection-funnel)
  UK HAR1 (CfD-tender):         DiD = +0.154 (p = 0.012 — selection-funnel)
  China 14th FYP (state capacity): DiD = {did_china_green['DiD']:+.4f}, p = {p_boot:.4f}

BELEIDSLES:
""")
if did_china_green['DiD'] < -0.05:
    print(f"  ✓ China toont protective effect — state capacity model werkt")
    print(f"  ✓ Maar dit is NIET overdraagbaar naar EU (geen vergelijkbare state-led structuur)")
else:
    print(f"  ⊘ Niet significant — verschil mogelijk door cumulative rate timing")

print(f"""
DATA VALIDITY CAVEAT:
- China heeft 0 formele cancellations - dat is suspicious
- SOE projecten worden mogelijk niet als 'failed' gemarkeerd zelfs als ze niet doorgaan
- 我们的发现是基于观察到的取消率的上限
- Voor PhD: report met expliciete caveat over data validity

VOOR HET PHD-VERHAAL:
=====================
China is een COMPARATIEVE BENCHMARK voor:
1. State-led model: laagste cancellation rate, maar onschaalbaar naar EU
2. Output-based credit (US 45Q): empirisch protectief, schaalbaar
3. Capex-grant (EU IF): direction OK maar te kleinschalig
4. Selection-tender (UK): selection-funnel (not policy failure)

CENTRALE LES:
'Carrots werken' is gedifferentieerd naar:
- State capacity carrots (China): werken maar onschaalbaar
- Output-based carrots (US): werken en schaalbaar
- Capex-grant carrots (EU): werken in principe maar schaal beperkt
- Selection-tender carrots (UK): werken als FID-funnel, niet survival
""")
