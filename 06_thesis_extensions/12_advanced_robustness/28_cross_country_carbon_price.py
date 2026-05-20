"""
28_cross_country_carbon_price.py
============================================================================
Pijler 23: Cross-country effective carbon-price test
============================================================================

Doel: test of het carbon-conditional Blue-fragility effect ook bestaat
ACROSS jurisdicties (niet alleen EU intern), gebruikmakend van effective
carbon-price equivalents:

  - EU/EEA:    EUA price (uit master panel)
  - UK:        Pre-2021 EUA, post-2021 UK ETS (proxy ~95% EUA)
  - US:        45Q tax credit ($0 → $85 post-IRA Aug 2022 for sequestration)
  - China:     National ETS price (~$8-10/tCO2 since Jul 2021)
  - Australia: Safeguard Mechanism ($30/tCO2 since Jul 2023)
  - Canada:    Federal carbon price ($50/tCO2 2022 → $80 2024+)
  - Japan:     GX-ETS voluntary (~$3-5/tCO2 since Apr 2023)
  - Andere:    $0

Test: discrete-time logit met Blue × effective_carbon_price interactie
op person-year panel + region fixed effects.

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


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: BUILD EFFECTIVE CARBON-PRICE PER COUNTRY × YEAR ===
header("STAP 1: Bouw effective carbon-price tabel per country × year")

# Laad EUA voor EU
macro = pd.read_csv(MACRO_PATH)
macro['date'] = pd.to_datetime(macro['date'])
macro['year'] = macro['date'].dt.year
eua_yearly = macro.groupby('year')['eua'].mean().reset_index()
eua_yearly.columns = ['year', 'eua_eur']
print("EUA yearly:")
print(eua_yearly.to_string(index=False))

# US 45Q tax credit history (in USD/tCO2 sequestered)
# Pre-2018: $0 (effectively, very small)
# 2018-2022 (FUTURE Act): $50/tCO2 for sequestration
# Aug 2022 IRA: $85/tCO2 for sequestration, $60/tCO2 for EOR
# We use $85 as upper bound from 2022 onwards (sequestration projects)
us_45q = {y: 0.0 for y in range(2010, 2027)}
for y in range(2018, 2023):
    us_45q[y] = 50.0
for y in range(2023, 2027):
    us_45q[y] = 85.0

# UK ETS: pre-2021 same as EUA, post-2021 trade at ~95% EUA on average
uk_etsprice = {}
for y in range(2010, 2027):
    eua_val = float(eua_yearly[eua_yearly['year'] == y]['eua_eur'].iloc[0]) if y in eua_yearly['year'].values else np.nan
    if y <= 2020:
        uk_etsprice[y] = eua_val
    else:
        uk_etsprice[y] = eua_val * 0.95 if not np.isnan(eua_val) else np.nan

# China National ETS (USD/tCO2, approximate)
# Pre-Jul 2021: $0
# 2021: $7
# 2022: $9, 2023: $9, 2024: $10, 2025: $11
china_ets = {y: 0.0 for y in range(2010, 2021)}
china_ets.update({2021: 7.0, 2022: 9.0, 2023: 9.0, 2024: 10.0, 2025: 11.0, 2026: 12.0})

# Australia Safeguard Mechanism
au_carbon = {y: 0.0 for y in range(2010, 2023)}
au_carbon.update({2023: 25.0, 2024: 30.0, 2025: 30.0, 2026: 30.0})

# Canada federal carbon pricing
ca_carbon = {y: 0.0 for y in range(2010, 2019)}
ca_carbon.update({2019: 16, 2020: 20, 2021: 30, 2022: 40, 2023: 50, 2024: 65, 2025: 80, 2026: 95})

# Japan GX-ETS (voluntary, low pricing)
jp_carbon = {y: 0.0 for y in range(2010, 2023)}
jp_carbon.update({2023: 3.0, 2024: 4.0, 2025: 5.0, 2026: 6.0})

# Norway CO2 tax (high, +EUA via EEA)
no_carbon = {}
for y in range(2010, 2027):
    eua_val = float(eua_yearly[eua_yearly['year'] == y]['eua_eur'].iloc[0]) if y in eua_yearly['year'].values else 0
    extra_co2_tax = 60.0 if y >= 2021 else 40.0  # NOK→USD approx
    no_carbon[y] = (eua_val if not np.isnan(eua_val) else 0) + extra_co2_tax

# Switzerland - similar to EU
ch_carbon = {y: float(eua_yearly[eua_yearly['year'] == y]['eua_eur'].iloc[0]) if y in eua_yearly['year'].values else 0
             for y in range(2010, 2027)}

# Build country-level carbon price function
def get_carbon_price(geography, year):
    """Returns effective carbon price in USD/tCO2 for project in country during year."""
    year = int(year)
    if year not in range(2010, 2027):
        return 0.0
    
    EU27 = {'Germany', 'France', 'Spain', 'Italy', 'Netherlands', 'Poland', 'Belgium', 'Sweden',
            'Austria', 'Denmark', 'Finland', 'Portugal', 'Czech Republic', 'Hungary', 'Romania',
            'Bulgaria', 'Greece', 'Slovakia', 'Slovenia', 'Croatia', 'Lithuania', 'Latvia',
            'Estonia', 'Ireland', 'Luxembourg', 'Malta', 'Cyprus'}
    
    if geography in EU27:
        return float(eua_yearly[eua_yearly['year'] == year]['eua_eur'].iloc[0]) if year in eua_yearly['year'].values else 0.0
    elif geography == 'United Kingdom':
        return uk_etsprice.get(year, 0.0)
    elif geography == 'United States':
        return us_45q.get(year, 0.0)
    elif geography == 'China':
        return china_ets.get(year, 0.0)
    elif geography == 'Australia':
        return au_carbon.get(year, 0.0)
    elif geography == 'Canada':
        return ca_carbon.get(year, 0.0)
    elif geography == 'Japan':
        return jp_carbon.get(year, 0.0)
    elif geography == 'Norway':
        return no_carbon.get(year, 0.0)
    elif geography == 'Switzerland':
        return ch_carbon.get(year, 0.0)
    elif geography == 'New Zealand':
        return 30.0 if year >= 2020 else 15.0  # NZ ETS
    elif geography in ['South Korea']:
        kr_carbon = {2015: 12, 2016: 18, 2017: 25, 2018: 23, 2019: 33, 2020: 22,
                     2021: 22, 2022: 23, 2023: 9, 2024: 9, 2025: 9, 2026: 9}
        return kr_carbon.get(year, 0.0)
    else:
        return 0.0  # Other countries: minimal/no carbon pricing


# === STAP 2: LAAD S&P + BUILD COUNTRY × YEAR PANEL ===
header("STAP 2: Bouw person-year panel met effective carbon-price per project")

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

df['log_capacity'] = np.log1p(pd.to_numeric(df['Output capacity per year'], errors='coerce').fillna(0))
df['Geography'] = df['Geography'].fillna('Other')

print(f"S&P sample: {len(df)} projecten")
print(f"  Top countries: {df['Geography'].value_counts().head(8).to_dict()}")


# Build person-year panel
panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['announce_year'])
    t_end = int(row['event_year'])
    is_event = int(row['event_any'])
    for t in range(t_start, t_end + 1):
        cp = get_carbon_price(row['Geography'], t)
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year': t,
            'event_yr': int(is_event and (t == t_end)),
            'is_blue': int(row['is_blue']),
            'country': row['Geography'],
            'region_major': row['Region major'],
            'log_capacity': float(row['log_capacity']),
            'years_since_announce': t - t_start,
            'effective_carbon_price': float(cp),
        })

panel = pd.DataFrame(panel_rows)

# Standardize effective carbon price
mu_ecp = panel['effective_carbon_price'].mean()
sd_ecp = panel['effective_carbon_price'].std()
panel['ecp_z'] = (panel['effective_carbon_price'] - mu_ecp) / sd_ecp
panel['blue_x_ecp_z'] = panel['is_blue'] * panel['ecp_z']

print(f"\nPerson-year panel: {len(panel)} rijen, {panel['event_yr'].sum()} events")
print(f"Effective carbon price: mean = ${mu_ecp:.2f}/tCO2, sd = ${sd_ecp:.2f}")
print(f"\nMean effective carbon-price per country (top 10):")
print(panel.groupby('country')['effective_carbon_price'].mean().sort_values(ascending=False).head(10).round(2))


# === STAP 3: MAIN MODEL ===
header("STAP 3: Cross-country carbon-conditional model")

formula = ('event_yr ~ is_blue + ecp_z + blue_x_ecp_z + log_capacity '
           '+ years_since_announce + I(years_since_announce ** 2) + C(region_major)')

mod = smf.glm(formula=formula, data=panel, family=sm.families.Binomial()).fit(cov_type='HC3')
print("\n--- CROSS-COUNTRY CARBON-CONDITIONAL FIT ---")
print(mod.summary().tables[1])

beta_blue = float(mod.params['is_blue'])
beta_ecp = float(mod.params['ecp_z'])
beta_int = float(mod.params['blue_x_ecp_z'])
p_int = float(mod.pvalues['blue_x_ecp_z'])

print(f"\n=== KEY RESULTS ===")
print(f"  is_blue main:        beta = {beta_blue:+.4f}")
print(f"  ecp_z main:          beta = {beta_ecp:+.4f}")
print(f"  blue × ecp_z:        beta = {beta_int:+.4f}  (p = {p_int:.4f})")
print(f"\n  Pijler 22 (EUA-only):  beta = -0.325 (p = 0.004)")
print(f"  Pijler 23 (effective): beta = {beta_int:+.3f} (p = {p_int:.4f})")


# === STAP 4: MARGINAL HR_BLUE OVER ECP-RANGE ===
header("STAP 4: Marginal HR_Blue curve over effective carbon-price range")

cov_mat = mod.cov_params()
z_grid = np.linspace(-1.0, 2.0, 7)  # range covers $0 to ~$100/tCO2
rows = []
for z in z_grid:
    ecp_usd = mu_ecp + z * sd_ecp
    log_hr = beta_blue + z * beta_int
    var_log_hr = cov_mat.loc['is_blue', 'is_blue'] + (z ** 2) * cov_mat.loc['blue_x_ecp_z', 'blue_x_ecp_z'] + 2 * z * cov_mat.loc['is_blue', 'blue_x_ecp_z']
    se_log_hr = np.sqrt(max(var_log_hr, 0.0))
    hr = np.exp(log_hr)
    hr_lo = np.exp(log_hr - 1.96 * se_log_hr)
    hr_hi = np.exp(log_hr + 1.96 * se_log_hr)
    rows.append({
        'z': float(z),
        'ecp_usd_tco2': float(ecp_usd),
        'log_HR_blue': float(log_hr),
        'HR_blue': float(hr),
        'HR_lo': float(hr_lo),
        'HR_hi': float(hr_hi),
    })
hr_grid = pd.DataFrame(rows)
print(hr_grid.round(3).to_string(index=False))


# === STAP 5: SUB-REGIONALE TESTS ===
header("STAP 5: Sub-regional tests — replicate per region")

for reg_label, reg_filter in [
    ('EU-27', panel['region_major'] == 'Europe (EU-27)'),
    ('North America', panel['region_major'] == 'North America'),
    ('Asia-Pacific', panel['region_major'] == 'Asia-Pacific'),
    ('Europe (non EU-27)', panel['region_major'] == 'Europe (non EU-27)'),
]:
    sub = panel[reg_filter].copy()
    if sub['event_yr'].sum() < 15:
        print(f"\n{reg_label}: too few events ({sub['event_yr'].sum()}), skip")
        continue
    print(f"\n--- {reg_label}: N = {len(sub)}, events = {sub['event_yr'].sum()} ---")
    try:
        formula_sub = 'event_yr ~ is_blue + ecp_z + blue_x_ecp_z + log_capacity + years_since_announce + I(years_since_announce ** 2)'
        mod_sub = smf.glm(formula=formula_sub, data=sub, family=sm.families.Binomial()).fit(cov_type='HC3')
        print(f"  is_blue:      beta = {mod_sub.params['is_blue']:+.4f}, p = {mod_sub.pvalues['is_blue']:.4f}")
        print(f"  ecp_z:        beta = {mod_sub.params['ecp_z']:+.4f}, p = {mod_sub.pvalues['ecp_z']:.4f}")
        print(f"  blue × ecp_z: beta = {mod_sub.params['blue_x_ecp_z']:+.4f}, p = {mod_sub.pvalues['blue_x_ecp_z']:.4f}")
    except Exception as e:
        print(f"  ERROR: {e}")


# === STAP 6: ALLEEN POST-IRA / POST-CBAM PERIODE ===
header("STAP 6: Post-2022 sub-sample (na IRA + CBAM transitional)")

panel_post = panel[panel['year'] >= 2022].copy()
print(f"Sample 2022+: N = {len(panel_post)}, events = {panel_post['event_yr'].sum()}")

if panel_post['event_yr'].sum() > 30:
    try:
        mod_post = smf.glm(formula=formula, data=panel_post, family=sm.families.Binomial()).fit(cov_type='HC3')
        print(f"\n  blue × ecp_z (post-2022): beta = {mod_post.params['blue_x_ecp_z']:+.4f}, p = {mod_post.pvalues['blue_x_ecp_z']:.4f}")
        print(f"  is_blue main (post-2022): beta = {mod_post.params['is_blue']:+.4f}, p = {mod_post.pvalues['is_blue']:.4f}")
        print(f"  ecp_z main (post-2022):   beta = {mod_post.params['ecp_z']:+.4f}, p = {mod_post.pvalues['ecp_z']:.4f}")
    except Exception as e:
        print(f"  ERROR: {e}")


# === STAP 7: FIGURES ===
header("STAP 7: Figuren")

fig, ax = plt.subplots(figsize=(11, 6))
ax.plot(hr_grid['ecp_usd_tco2'], hr_grid['HR_blue'], 'o-', color='#9c27b0',
        linewidth=2.5, markersize=10, label='Cross-country effective carbon-price')
ax.fill_between(hr_grid['ecp_usd_tco2'], hr_grid['HR_lo'], hr_grid['HR_hi'],
                color='#9c27b0', alpha=0.15, label='95% CI')
ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.6, label='HR = 1')
ax.set_yscale('log')
ax.set_xlabel('Effective carbon-price equivalent ($/tCO2)', fontsize=12)
ax.set_ylabel('HR_Blue (log scale)', fontsize=12)
ax.set_title(f'Pijler 23: Cross-country HR_Blue vs effective carbon-price\nBlue × ECP interaction: β = {beta_int:+.3f}, p = {p_int:.4f}',
             fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler23_cross_country_carbon.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved: pijler23_cross_country_carbon.png")


# === STAP 8: OPSLAAN ===
header("STAP 8: Opslaan")

hr_grid.to_csv(OUTPUT_DIR / 'pijler23_marginal_HR_crosscountry.csv', index=False)

summary = pd.DataFrame([{
    'method': 'Pijler 23: Cross-country effective carbon-price test',
    'n_projects': len(df),
    'n_person_years': len(panel),
    'n_events': int(panel['event_yr'].sum()),
    'ecp_mean_usd': float(mu_ecp),
    'ecp_sd_usd': float(sd_ecp),
    'beta_blue_main': beta_blue,
    'beta_ecp_main': beta_ecp,
    'beta_int_blue_x_ecp': beta_int,
    'p_int': p_int,
    'p22_eua_only_beta': -0.325,
    'p22_eua_only_p': 0.004,
}])
summary.to_csv(OUTPUT_DIR / 'pijler23_summary.csv', index=False)


# === STAP 9: EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 23 (Cross-country effective carbon-price)")
print("=" * 78)
print(f"\nSample: {len(df)} projecten, {len(panel)} person-years, {panel['event_yr'].sum()} events")
print(f"\n--- HOOFDRESULTAAT ---")
print(f"  Pijler 22 (EU EUA only):      beta_int = -0.325, p = 0.004")
print(f"  Pijler 23 (cross-country ECP): beta_int = {beta_int:+.3f}, p = {p_int:.4f}")
if p_int < 0.05 and beta_int < 0:
    print(f"\n*** CROSS-COUNTRY CARBON-CONDITIONAL EFFECT BEVESTIGD ***")
    print(f"Het Blue-fragility effect is conditional op effective carbon-price ACROSS")
    print(f"jurisdicties, niet alleen binnen EU. De carbon-price equivalent hypothese")
    print(f"(EUA + 45Q + UK ETS + China ETS + ...) WORKT als universele covariate.")
elif beta_int < 0:
    print(f"\n*** MARGINAL EVIDENCE — niet significant op 95% ***")
    print(f"Direction is consistent met carbon-conditional hypothese (beta = {beta_int:+.3f})")
    print(f"maar p = {p_int:.4f} ondersteunt geen sterke claim.")
else:
    print(f"\n*** UNEXPECTED — interactie heeft 'verkeerde' direction (positief) ***")
    print(f"Mogelijk: heterogeneity issues, of effectieve carbon-prices in andere landen")
    print(f"werken anders dan de EU EUA mechanism.")
