"""
03_carbon_conditional_freq.py

Spoor B-1: Frequentist replicatie van v7's carbon-conditional finding
(Blue_CCS × EUA interactie) op person-year panel met discrete-time hazard GLM.

Gebruikt de bestaande v7 project-level CSV (244 Blue_CCS + 470 PEM = 714)
en bouwt daarop een person-year panel met time-varying EUA.

Model: event_any_yr ~ is_blue_ccs + eua_z + blue×eua + year_since_start
                     + year_since_start² + log_capacity + region + sponsor_type
Family: Binomial (logit) = discrete-time hazard model
SE: HC3 robust (skip cluster - sponsor_owner niet beschikbaar in deze CSV)

Outputs:
  - 03_carbon_conditional_summary.csv
  - 03_marginal_hr_grid.csv
  - 03_v7_comparison.csv
  - figures/carbon_conditional_HR.pdf

Auteur: Sake Saakstra
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

# ============================================================================
# CONFIG
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/04_carbon_conditional/results_freq"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "figures").mkdir(exist_ok=True)


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# DATA LADEN
# ============================================================================
header("Loading data")

df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)
df['project_id'] = df.index

print(f"  Project-level: {len(df)} rijen")
print(f"  Blue_CCS = {df['is_blue_ccs'].sum()}, PEM = {(1-df['is_blue_ccs']).sum()}")
print(f"  Events any = {df['event_any'].sum()}")
print(f"  Year_announced range: {df['year_announced'].min()} - {df['year_announced'].max()}")
print(f"  Duration range: {df['duration'].min()} - {df['duration'].max()}")


# ============================================================================
# PERSON-YEAR PANEL CONSTRUCTIE
# ============================================================================
header("Building person-year panel")
panel_rows = []
for _, row in df.iterrows():
    t_start = int(row['year_announced'])
    duration = int(row['duration'])
    t_end = t_start + duration
    
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': int(row['project_id']),
            'year_calendar': t,
            'year_since_start': t - t_start,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
            'log_capacity_mw': float(row['log_capacity_mw']),
            'region': row['region'],
            'sponsor_type': row['sponsor_type'],
            'year_announced': t_start,
        })

panel = pd.DataFrame(panel_rows)
print(f"  Person-year panel: {len(panel)} rijen")
print(f"    Projecten: {panel['project_id'].nunique()}")
print(f"    events_any_yr: {panel['event_any_yr'].sum()}")


# ============================================================================
# MERGE EUA + Z-SCORE
# ============================================================================
header("Merging EUA carbon price")

mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
yearly_eua.columns = ['year_calendar', 'mkt_eua']

panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['mkt_eua'].fillna(panel['mkt_eua'].median())

eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['mkt_eua_z'] = (panel['mkt_eua'] - eua_mean) / eua_sd
panel['blue_x_eua'] = panel['is_blue_ccs'] * panel['mkt_eua_z']

print(f"  EUA in panel: mean = €{eua_mean:.1f}/tCO2, sd = €{eua_sd:.1f}/tCO2")
print(f"  z range: [{panel['mkt_eua_z'].min():.2f}, {panel['mkt_eua_z'].max():.2f}]")
print(f"  Coverage: {panel['mkt_eua'].notna().sum()}/{len(panel)}")


# ============================================================================
# MODEL FIT
# ============================================================================
header("Discrete-time hazard GLM with Blue×EUA interaction")

FORMULA = (
    "event_any_yr ~ is_blue_ccs + mkt_eua_z + blue_x_eua "
    "+ year_since_start + I(year_since_start**2) "
    "+ log_capacity_mw "
    "+ C(region) + C(sponsor_type)"
)

print(f"\nFormule:\n  {FORMULA}\n")

# HC3 robuuste SE (sponsor_owner niet in deze CSV - cluster optioneel later)
m = smf.glm(FORMULA, data=panel, family=sm.families.Binomial()).fit(cov_type='HC3')
print(m.summary())

# Key coefs
header("Key coefficients")
key = ['is_blue_ccs', 'mkt_eua_z', 'blue_x_eua']
for k in key:
    coef = m.params[k]
    se = m.bse[k]
    p = m.pvalues[k]
    print(f"  {k:15s}: β = {coef:7.3f} (SE {se:5.3f}), p = {p:.4f}")

# Sla coefs op
coefs_df = pd.DataFrame({
    'term': m.params.index,
    'coef': m.params.values,
    'se': m.bse.values,
    'z': m.tvalues.values,
    'p': m.pvalues.values,
    'conf_lo': m.conf_int().iloc[:, 0].values,
    'conf_hi': m.conf_int().iloc[:, 1].values,
})
coefs_df.to_csv(OUTPUT_DIR / "03_carbon_conditional_summary.csv", index=False)
print(f"\nOpgeslagen: 03_carbon_conditional_summary.csv")


# ============================================================================
# MARGINAL HR(Blue|z) over grid via delta method
# ============================================================================
header("Marginal Blue HR as function of EUA z-score")

beta_blue = m.params['is_blue_ccs']
beta_int = m.params['blue_x_eua']
cov = m.cov_params()

z_grid = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5])
hr_rows = []
for z in z_grid:
    log_hr = beta_blue + beta_int * z
    var_log = (cov.loc['is_blue_ccs','is_blue_ccs']
               + (z**2) * cov.loc['blue_x_eua','blue_x_eua']
               + 2 * z * cov.loc['is_blue_ccs','blue_x_eua'])
    se_log = np.sqrt(max(var_log, 0))
    hr_rows.append({
        'z': z,
        'eua_eur_tco2': eua_mean + z * eua_sd,
        'log_HR_blue': log_hr,
        'HR_blue': np.exp(log_hr),
        'HR_lo': np.exp(log_hr - 1.96 * se_log),
        'HR_hi': np.exp(log_hr + 1.96 * se_log),
    })
hr_df = pd.DataFrame(hr_rows)
print(hr_df.round(3).to_string(index=False))
hr_df.to_csv(OUTPUT_DIR / "03_marginal_hr_grid.csv", index=False)


# ============================================================================
# V7 REPRODUCTION CHECK
# ============================================================================
header("v7 reproduction check")
v7_check = pd.DataFrame([
    {'metric': 'Blue×EUA interaction coef', 'v7_reported': -2.51, 'this_run': float(beta_int)},
    {'metric': 'HR at z = -1', 'v7_reported': 673.0,  'this_run': float(np.exp(beta_blue - beta_int))},
    {'metric': 'HR at z =  0', 'v7_reported':  59.73, 'this_run': float(np.exp(beta_blue))},
    {'metric': 'HR at z = +1', 'v7_reported':   4.67, 'this_run': float(np.exp(beta_blue + beta_int))},
])
print(v7_check.round(3).to_string(index=False))
v7_check.to_csv(OUTPUT_DIR / "03_v7_comparison.csv", index=False)


# ============================================================================
# FIGUUR
# ============================================================================
header("Marginal HR figure")
z_fine = np.linspace(-1.5, 1.5, 60)
log_hr_curve = beta_blue + beta_int * z_fine
var_curve = (cov.loc['is_blue_ccs','is_blue_ccs']
             + (z_fine**2) * cov.loc['blue_x_eua','blue_x_eua']
             + 2 * z_fine * cov.loc['is_blue_ccs','blue_x_eua'])
se_curve = np.sqrt(np.clip(var_curve, 0, None))

fig, ax = plt.subplots(figsize=(9.5, 6))
hr_curve = np.exp(log_hr_curve)
hr_lo = np.exp(log_hr_curve - 1.96 * se_curve)
hr_hi = np.exp(log_hr_curve + 1.96 * se_curve)

ax.plot(z_fine, hr_curve, color='#222288', lw=2, label='Estimated Blue_CCS HR')
ax.fill_between(z_fine, hr_lo, hr_hi, color='#222288', alpha=0.2, label='95% CI')
ax.axhline(1, linestyle='--', color='red', alpha=0.7, label='HR = 1 (no effect)')
ax.set_xlabel("EUA carbon price (z-score)")
ax.set_ylabel("Hazard ratio: Blue_CCS vs PEM (log scale)")
ax.set_yscale('log')
ax.set_title("Blue_CCS cancellation hazard conditional on EUA carbon price")
ax2 = ax.twiny()
ax2.set_xlim(ax.get_xlim())
xticks = np.linspace(-1.5, 1.5, 7)
ax2.set_xticks(xticks)
ax2.set_xticklabels([f"€{eua_mean + z*eua_sd:.0f}" for z in xticks])
ax2.set_xlabel("EUA price (€/tCO₂)")
ax.grid(alpha=0.3)
ax.legend(loc='upper right')
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/carbon_conditional_HR.pdf")
plt.close(fig)
print(f"Opgeslagen: figures/carbon_conditional_HR.pdf")


header("KLAAR (Spoor B-1: frequentist)")
print(f"Resultaten in: {OUTPUT_DIR}")
