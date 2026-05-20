"""
27_carbon_conditional_sp.py
============================================================================
Pijler 22: Carbon-conditional replicatie op S&P (vervangt Pijler 4)
============================================================================

Doel: replicate v7 paper Bevinding 4 (Blue × EUA interaction) op S&P data
(N=1354 Blue+Green) en test of:
  1. De interactie coefficient Blue × EUA blijft significant
  2. De marginal HR_Blue curve is consistent met v7 (HR collapse over EUA range)
  3. De CIs zijn scherper (groter sample, meer recente periode)

v7 baseline (Pijler 4):
  Blue × EUA coef = -2.28 (paper rapporteerde -2.51)
  HR_Blue at EUA z=-1: 444
  HR_Blue at EUA z= 0: 45.5
  HR_Blue at EUA z=+1: 4.67

Methode: discrete-time hazard GLM (logit) op person-year panel met
time-varying EUA als interactie variabele.

Auteur: Sake Saakstra, 20 mei 2026
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
MACRO_PATH = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/results"
FIG_DIR = PROJECT_ROOT / "06_thesis_extensions/12_advanced_robustness/figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: LAAD S&P + MACRO ===
header("STAP 1: Laad S&P (Blue+Green) en master_panel_monthly (EUA)")

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

# Event year
df['event_year'] = np.where(
    df['event_any'] == 1,
    np.where(df['est_year_online'].notna(),
             np.ceil((df['announce_year'] + df['est_year_online']) / 2),
             df['announce_year'] + 3),
    2026.0
).clip(min=df['announce_year'], max=2026.0)

# Covariates
df['log_capacity'] = np.log1p(pd.to_numeric(df['Output capacity per year'], errors='coerce').fillna(0))
df['region'] = df['Region major']
df['region_eu'] = (df['region'] == 'Europe (EU-27)').astype(int)
df['region_na'] = (df['region'] == 'North America').astype(int)
df['region_asia'] = (df['region'] == 'Asia-Pacific').astype(int)

print(f"S&P sample: N = {len(df)}")
print(f"  is_blue:  {df['is_blue'].sum()}")
print(f"  is_green: {df['is_green'].sum()}")
print(f"  Events any: {df['event_any'].sum()}")

# Macro
macro = pd.read_csv(MACRO_PATH)
macro['date'] = pd.to_datetime(macro['date'])
macro['year'] = macro['date'].dt.year
eua_yearly = macro.groupby('year')['eua'].mean().reset_index()
eua_yearly.columns = ['year', 'eua_annual']
print(f"\nEUA jaarlijkse gemiddelden:")
print(eua_yearly.to_string(index=False))

# Standardiseren EUA over 2010-2025
eua_train = eua_yearly[(eua_yearly['year'] >= 2010) & (eua_yearly['year'] <= 2025)]
mu_eua = eua_train['eua_annual'].mean()
sd_eua = eua_train['eua_annual'].std()
print(f"\nEUA mu = {mu_eua:.2f}, sd = {sd_eua:.2f}")
eua_yearly['eua_z'] = (eua_yearly['eua_annual'] - mu_eua) / sd_eua


# === STAP 2: PERSON-YEAR PANEL ===
header("STAP 2: Bouw person-year panel met time-varying EUA")

panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['announce_year'])
    t_end = int(row['event_year'])
    is_event = int(row['event_any'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year': t,
            'event_yr': int(is_event and (t == t_end)),
            'is_blue': int(row['is_blue']),
            'log_capacity': float(row['log_capacity']),
            'region_eu': int(row['region_eu']),
            'region_na': int(row['region_na']),
            'region_asia': int(row['region_asia']),
            'years_since_announce': t - t_start,
        })

panel = pd.DataFrame(panel_rows)
panel = panel.merge(eua_yearly[['year', 'eua_annual', 'eua_z']], on='year', how='left')
panel['eua_z'] = panel['eua_z'].fillna(0.0)  # 2026 onwards: use mu
panel['eua_annual'] = panel['eua_annual'].fillna(eua_yearly[eua_yearly['year']==2025]['eua_annual'].iloc[0])
panel['blue_x_eua_z'] = panel['is_blue'] * panel['eua_z']

print(f"Person-year panel: {len(panel)} rijen")
print(f"  Events_yr=1: {panel['event_yr'].sum()}")
print(f"  Mean EUA_z over panel: {panel['eua_z'].mean():.3f}")


# === STAP 3: COX PH-equivalent VIA DISCRETE-TIME LOGIT ===
header("STAP 3: Carbon-conditional model (S&P discrete-time logit)")

formula = ('event_yr ~ is_blue + eua_z + blue_x_eua_z '
           '+ log_capacity + region_eu + region_na + region_asia '
           '+ years_since_announce + I(years_since_announce ** 2)')

mod = smf.glm(formula=formula, data=panel,
              family=sm.families.Binomial()).fit(cov_type='HC3')

print("\n--- S&P CARBON-CONDITIONAL FIT ---")
print(mod.summary().tables[1])

beta_blue = float(mod.params['is_blue'])
beta_eua = float(mod.params['eua_z'])
beta_int = float(mod.params['blue_x_eua_z'])
se_int = float(mod.bse['blue_x_eua_z'])
p_int = float(mod.pvalues['blue_x_eua_z'])

print(f"\n=== KEY COEFFICIENTS ===")
print(f"  is_blue (main):         beta = {beta_blue:+.4f}")
print(f"  eua_z (main):           beta = {beta_eua:+.4f}")
print(f"  blue × eua_z:           beta = {beta_int:+.4f}  (se = {se_int:.4f}, p = {p_int:.4f})")
print(f"\n  v7 paper baseline: blue × eua = -2.51 (p < 0.0001)")
print(f"  v7 replicatie:     blue × eua = -2.28 (p = 0.027)")
print(f"  S&P this run:      blue × eua = {beta_int:+.4f} (p = {p_int:.4f})")


# === STAP 4: MARGINAL HR_BLUE OVER EUA-RANGE (delta method) ===
header("STAP 4: Marginal HR_Blue curve over EUA range (delta method)")

cov_mat = mod.cov_params()
def get_var(name):
    return cov_mat.loc[name, name]
def get_cov(a, b):
    return cov_mat.loc[a, b]

z_grid = np.linspace(-1.5, 1.5, 7)
rows = []
for z in z_grid:
    eua_eur = mu_eua + z * sd_eua
    log_hr = beta_blue + z * beta_int
    var_log_hr = get_var('is_blue') + (z ** 2) * get_var('blue_x_eua_z') + 2 * z * get_cov('is_blue', 'blue_x_eua_z')
    se_log_hr = np.sqrt(max(var_log_hr, 0.0))
    hr = np.exp(log_hr)
    hr_lo = np.exp(log_hr - 1.96 * se_log_hr)
    hr_hi = np.exp(log_hr + 1.96 * se_log_hr)
    rows.append({
        'z': float(z),
        'eua_eur_tco2': float(eua_eur),
        'log_HR_blue': float(log_hr),
        'se_log_HR': float(se_log_hr),
        'HR_blue': float(hr),
        'HR_lo': float(hr_lo),
        'HR_hi': float(hr_hi),
    })
hr_grid = pd.DataFrame(rows)
print(hr_grid.round(4).to_string(index=False))


# === STAP 5: VERGELIJKING MET V7 PAPER ===
header("STAP 5: Vergelijking S&P vs v7 (replicate paper Table 5)")

v7_data = {
    -1.5: 1387, -1.0: 444, -0.5: 142.2, 0.0: 45.5,
     0.5: 14.58, 1.0: 4.67, 1.5: 1.49,
}
print(f"\n{'EUA z':<8}{'EUA €':<10}{'v7 HR':<14}{'S&P HR':<22}{'S&P 95% CI':<30}")
for _, r in hr_grid.iterrows():
    z = r['z']
    sp_str = f"{r['HR_blue']:.2f}"
    ci_str = f"[{r['HR_lo']:.2f}, {r['HR_hi']:.2f}]"
    v7_val = v7_data.get(z, np.nan)
    print(f"{z:<8.2f}{r['eua_eur_tco2']:<10.2f}{v7_val:<14.2f}{sp_str:<22}{ci_str:<30}")


# === STAP 6: ROBUSTHEIDSCHECKS (sub-groep analyses) ===
header("STAP 6: Sub-group robustness — alleen EU + Pre/Post 2018")

# EU only
panel_eu = panel[panel['region_eu'] == 1].copy()
if len(panel_eu) > 0 and panel_eu['event_yr'].sum() >= 15:
    print(f"\nEU-only sub-sample: N = {len(panel_eu)}, events = {panel_eu['event_yr'].sum()}")
    formula_eu = 'event_yr ~ is_blue + eua_z + blue_x_eua_z + log_capacity + years_since_announce + I(years_since_announce ** 2)'
    try:
        mod_eu = smf.glm(formula=formula_eu, data=panel_eu, family=sm.families.Binomial()).fit(cov_type='HC3')
        print(f"  blue × eua_z = {mod_eu.params['blue_x_eua_z']:+.4f}, p = {mod_eu.pvalues['blue_x_eua_z']:.4f}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Pre-2018 vs Post-2018 (EUA Phase 3 → Phase 4)
for tag, mask in [('Pre-2018 (EUA Phase 3)', panel['year'] <= 2018),
                   ('Post-2018 (EUA Phase 4)', panel['year'] > 2018)]:
    sub = panel[mask]
    if sub['event_yr'].sum() >= 10:
        print(f"\n{tag}: N = {len(sub)}, events = {sub['event_yr'].sum()}")
        try:
            mod_sub = smf.glm(formula=formula, data=sub, family=sm.families.Binomial()).fit(cov_type='HC3')
            print(f"  blue × eua_z = {mod_sub.params['blue_x_eua_z']:+.4f}, p = {mod_sub.pvalues['blue_x_eua_z']:.4f}")
        except Exception as e:
            print(f"  ERROR: {e}")


# === STAP 7: FIGUREN ===
header("STAP 7: Figuren")

# Fig 1: HR_Blue curve over EUA (S&P + v7 comparison)
fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(hr_grid['eua_eur_tco2'], hr_grid['HR_blue'], 'o-', color='#d62728',
        linewidth=2.5, markersize=10, label='S&P (this analysis)')
ax.fill_between(hr_grid['eua_eur_tco2'], hr_grid['HR_lo'], hr_grid['HR_hi'],
                color='#d62728', alpha=0.15, label='S&P 95% CI')

# Add v7 reference points
v7_eua_x = [mu_eua + z * sd_eua for z in v7_data.keys()]
v7_hr_y = list(v7_data.values())
ax.plot(v7_eua_x, v7_hr_y, 's--', color='#1f77b4', linewidth=2,
        markersize=10, label='v7 paper (frequentist)', alpha=0.7)

ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.6, label='HR = 1')
ax.set_yscale('log')
ax.set_xlabel('EUA carbon price (€/tCO₂)', fontsize=12)
ax.set_ylabel('HR_Blue (log scale)', fontsize=12)
ax.set_title(f'Pijler 22: Carbon-conditional HR_Blue — S&P vs v7\nBlue × EUA interaction: β = {beta_int:+.3f}, p = {p_int:.4f}',
             fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler22_carbon_conditional_HR.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler22_carbon_conditional_HR.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Opslaan")

hr_grid.to_csv(OUTPUT_DIR / 'pijler22_marginal_HR_sp.csv', index=False)

summary = pd.DataFrame([{
    'method': 'Pijler 22: Carbon-conditional discrete-time logit op S&P',
    'reference_paper_finding_4': 'v7 paper Bevinding 4 (Blue × EUA interactie)',
    'n_projects': len(df),
    'n_blue': int(df['is_blue'].sum()),
    'n_green': int(df['is_green'].sum()),
    'n_events_any': int(df['event_any'].sum()),
    'n_person_years': len(panel),
    'eua_mean_2010_2025': mu_eua,
    'eua_sd_2010_2025': sd_eua,
    'beta_blue_main': beta_blue,
    'beta_eua_main': beta_eua,
    'beta_int_blue_x_eua': beta_int,
    'se_int': se_int,
    'p_int': p_int,
    'v7_paper_beta_int': -2.51,
    'v7_replicatie_beta_int': -2.28,
    'HR_at_z_minus1': float(hr_grid[hr_grid['z']==-1.0]['HR_blue'].iloc[0]) if (hr_grid['z']==-1.0).any() else np.nan,
    'HR_at_z_0': float(hr_grid[hr_grid['z']==0.0]['HR_blue'].iloc[0]) if (hr_grid['z']==0.0).any() else np.nan,
    'HR_at_z_plus1': float(hr_grid[hr_grid['z']==1.0]['HR_blue'].iloc[0]) if (hr_grid['z']==1.0).any() else np.nan,
}])
summary.to_csv(OUTPUT_DIR / 'pijler22_summary.csv', index=False)


# === STAP 9: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 22 (Carbon-conditional op S&P)")
print("=" * 78)

print(f"\nSample: {len(df)} Blue+Green projecten ({int(df['event_any'].sum())} failure events)")
print(f"Person-year panel: {len(panel)} observaties")
print(f"\n--- INTERACTIE COEFFICIENT ---")
print(f"  v7 paper:        Blue × EUA = -2.51 (p < 0.0001)")
print(f"  v7 replicatie:   Blue × EUA = -2.28 (p = 0.027)")
print(f"  S&P this run:    Blue × EUA = {beta_int:+.3f} (p = {p_int:.4f})")

print(f"\n--- MARGINAL HR_BLUE ---")
print(f"  EUA z=-1 (low):  S&P HR = {hr_grid[hr_grid['z']==-1.0]['HR_blue'].iloc[0]:.2f}  vs v7 HR = 444")
print(f"  EUA z= 0 (mean): S&P HR = {hr_grid[hr_grid['z']==0.0]['HR_blue'].iloc[0]:.2f}  vs v7 HR = 45.5")
print(f"  EUA z=+1 (high): S&P HR = {hr_grid[hr_grid['z']==1.0]['HR_blue'].iloc[0]:.2f}  vs v7 HR = 4.67")

if p_int < 0.05:
    print(f"\n*** S&P BEVESTIGT carbon-conditional finding ***")
    print(f"Blue × EUA interactie blijft significant op S&P (p = {p_int:.4f})")
else:
    print(f"\n*** S&P NIET volledig replicatie ***")
    print(f"Interactie p = {p_int:.4f} (niet < 0.05) — sample-dependent magnitude")
