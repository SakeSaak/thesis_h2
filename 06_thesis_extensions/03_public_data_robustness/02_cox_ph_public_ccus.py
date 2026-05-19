"""
02_cox_ph_public_ccus.py

Cox PH analyse op de publieke IEA CCUS Projects Database 2026.
Spoor A van de thesis-extensie: robustness van het v7-paper findings op
volledig publieke data (CC BY 4.0).

Drie analytische modellen:
  Model A1: hydrogen-CCUS vs alle andere CCUS (broad comparator)
  Model A2: hydrogen-CCUS vs industriële CCUS only (fair comparator)
  Model A3: binnen-hydrogen CCUS sample (covariate analyse op 98 projecten)

Outputs:
  cox_summary_all_models.csv     - vergelijkingstabel van de 3 modellen
  cox_diagnostics.txt            - PH assumption checks
  forest_plot_HR.pdf             - hazard ratios met 95% CIs
  v7_vs_public_comparison.csv    - vergelijking met v7's HR=11.93

Auteur: Sake Saakstra
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lifelines import CoxPHFitter
from lifelines.statistics import proportional_hazard_test

# ============================================================================
# CONFIGURATIE
# ============================================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
DOWNLOADS = Path("/Users/sakesaakstra/Downloads")
EXT_DIR = PROJECT_ROOT / "06_thesis_extensions/03_public_data_robustness"

CCUS_FILE = DOWNLOADS / "IEA CCUS Projects Database 2026.xlsx"
OUTPUT_DIR = EXT_DIR / "results_cox"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CURRENT_YEAR = 2026

# Industriële subsectors (voor Model A2 fair comparator)
# Wel: industriële productie/transformatie met CCS
# Niet: pure infrastructure (T&S, storage), power generation (utility-driven),
#       DAC (different paradigm), bioethanol (different scale)
INDUSTRIAL_SUBSECTORS = {
    'Hydrogen or ammonia',
    'Refining',
    'Cement',
    'Iron and steel',
    'Fertiliser',
    'Chemicals',
    'Coal-to-liquids',
    'Pulp and paper',
    'Lime',
    'Natural gas processing/LNG',
}


def header(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


# ============================================================================
# REGION MAPPING (parallel aan v7)
# ============================================================================
def region_group(c):
    if pd.isna(c): return "Other"
    c = str(c).strip()
    eu = ["Netherlands","Germany","France","Spain","Denmark","Belgium","Italy",
          "Sweden","Finland","Portugal","Austria","Poland","Ireland","Greece"]
    if any(e in c for e in eu): return "EU"
    if c in ("United Kingdom","UK","Norway","Switzerland","Iceland"): return "Other_Europe"
    if c in ("United States","USA","US","Canada","Mexico"): return "North_America"
    if c in ("Japan","South Korea","China","India","Singapore","Taiwan","Korea"): return "Asia"
    if c in ("Australia","New Zealand"): return "ANZ"
    if c in ("Saudi Arabia","UAE","Oman","Qatar","Egypt","Morocco","Israel","Algeria"): return "MENA"
    return "Other"


# ============================================================================
# DATA LADEN EN PREP
# ============================================================================
header("Loading IEA CCUS Database 2026")
ccus = pd.read_excel(CCUS_FILE, sheet_name='DRAFT CCUS Projects Database', header=0)
print(f"  Total CCUS projecten: {len(ccus)}")

# Event encoding
def encode_event(status):
    s = str(status).strip().lower()
    if s in ('cancelled', 'decommissioned'): return 1
    if s == 'suspended': return 2
    return 0

ccus['event_type'] = ccus['Project status'].apply(encode_event)
ccus['event_any'] = (ccus['event_type'] > 0).astype(int)

def to_year(x):
    if pd.isna(x): return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100: return int(v)
    except: pass
    return np.nan

ccus['year_announced'] = ccus['Announcement'].apply(to_year)
ccus['year_event'] = ccus['Suspension/decommissioning/cancellation'].apply(to_year)

def compute_duration(row):
    start = row['year_announced']
    if pd.isna(start): return np.nan
    if row['event_any'] == 1 and not pd.isna(row['year_event']):
        return max(1, int(row['year_event'] - start))
    return max(1, CURRENT_YEAR - int(start))

ccus['duration'] = ccus.apply(compute_duration, axis=1)
ccus['region'] = ccus['Country or economy'].apply(region_group)
ccus['is_h2_ammonia'] = (ccus['Subsector'].fillna('').astype(str)
                        .str.contains('Hydrogen|ammonia', case=False, regex=True).astype(int))
ccus['is_industrial'] = ccus['Subsector'].astype(str).isin(INDUSTRIAL_SUBSECTORS).astype(int)

# Capacity (zelfde extractie als v7)
ccus['capacity_mtco2'] = pd.to_numeric(
    ccus['Announced capacity (Mt CO2/yr)'].astype(str).str.extract(r'([\d.]+)', expand=False),
    errors='coerce'
)
ccus['log_capacity_mtco2'] = np.log1p(ccus['capacity_mtco2'].fillna(0))

# Project type
ccus['project_type'] = ccus['Project type'].astype(str).str.strip()

# Filter naar analyseerbare sample
analyzable = ccus.dropna(subset=['year_announced', 'duration']).copy()
print(f"  Analyseerbaar (met year_announced + duration): {len(analyzable)}")
print(f"  Events totaal: {analyzable['event_any'].sum()}")
print(f"  H2/ammonia events: {analyzable[analyzable['is_h2_ammonia']==1]['event_any'].sum()}")
print(f"  Industrieel events: {analyzable[analyzable['is_industrial']==1]['event_any'].sum()}")


# ============================================================================
# HELPER: COX PH FIT MET DIAGNOSTICS
# ============================================================================
def fit_cox(data, model_name, formula_cols, hr_var='is_h2_ammonia'):
    """Fit Cox PH met lifelines. Retourneer summary dict."""
    print(f"\n--- {model_name} ---")
    print(f"  N = {len(data)}, events = {int(data['event_any'].sum())}")

    # Maak design matrix
    fit_df = data[['duration', 'event_any'] + formula_cols].copy()

    # One-hot voor categorische
    for col in ['region', 'project_type']:
        if col in fit_df.columns:
            d = pd.get_dummies(fit_df[col], prefix=col, drop_first=True).astype(int)
            fit_df = pd.concat([fit_df.drop(columns=[col]), d], axis=1)

    # Fit
    cph = CoxPHFitter(penalizer=0.01)
    try:
        cph.fit(fit_df, duration_col='duration', event_col='event_any')
        results_summary = cph.summary
    except Exception as e:
        print(f"  FAIL: {e}")
        return None

    # Extract is_h2_ammonia coefficient
    if hr_var not in results_summary.index:
        print(f"  WARN: {hr_var} not found in fit, fitting with only that var")
        return None

    row = results_summary.loc[hr_var]
    out = {
        'model': model_name,
        'n_obs': len(data),
        'n_events': int(data['event_any'].sum()),
        'n_h2_events': int(data[data['is_h2_ammonia']==1]['event_any'].sum()),
        'beta': row['coef'],
        'beta_se': row['se(coef)'],
        'HR': row['exp(coef)'],
        'HR_lo': row['exp(coef) lower 95%'],
        'HR_hi': row['exp(coef) upper 95%'],
        'p_value': row['p'],
        'concordance': cph.concordance_index_,
    }

    print(f"  is_h2_ammonia: β = {out['beta']:.3f} (SE {out['beta_se']:.3f})")
    print(f"  HR = {out['HR']:.2f} (95% CI [{out['HR_lo']:.2f}, {out['HR_hi']:.2f}])")
    print(f"  p-value = {out['p_value']:.4f}")
    print(f"  Concordance index = {out['concordance']:.3f}")

    return out, cph, fit_df


# ============================================================================
# MODEL A1: H2-CCUS vs alle andere CCUS (broad comparator)
# ============================================================================
header("MODEL A1: Hydrogen/Ammonia CCUS vs ALL OTHER CCUS sectors")

# Use de hele analyzable sample
res_a1, cph_a1, _ = fit_cox(
    analyzable.copy(),
    "Model A1: Broad comparator",
    formula_cols=['is_h2_ammonia', 'log_capacity_mtco2', 'region', 'project_type'],
)


# ============================================================================
# MODEL A2: H2-CCUS vs Industrial CCUS only (fair comparator)
# ============================================================================
header("MODEL A2: Hydrogen/Ammonia CCUS vs INDUSTRIAL CCUS only")
industrial = analyzable[analyzable['is_industrial'] == 1].copy()
print(f"Industriële sample (excl. DAC/T&S/Storage/Power): {len(industrial)}")
print(f"Subsector breakdown:")
print(industrial['Subsector'].value_counts())

res_a2, cph_a2, _ = fit_cox(
    industrial,
    "Model A2: Fair industrial comparator",
    formula_cols=['is_h2_ammonia', 'log_capacity_mtco2', 'region'],
)


# ============================================================================
# MODEL A3: Within-Hydrogen-CCUS sample (98 projecten)
# ============================================================================
header("MODEL A3: WITHIN Hydrogen/Ammonia CCUS sample")
within_h2 = analyzable[analyzable['is_h2_ammonia'] == 1].copy()
print(f"H2-CCUS sample: {len(within_h2)}, events = {within_h2['event_any'].sum()}")

# Hier kunnen we geen is_h2_ammonia gebruiken (constant), kijken naar andere covariates
# Use log_capacity en region als covariates voor risk factoren binnen blue hydrogen
fit_df_a3 = within_h2[['duration', 'event_any', 'log_capacity_mtco2', 'region', 'project_type']].copy()
for col in ['region', 'project_type']:
    d = pd.get_dummies(fit_df_a3[col], prefix=col, drop_first=True).astype(int)
    fit_df_a3 = pd.concat([fit_df_a3.drop(columns=[col]), d], axis=1)

cph_a3 = CoxPHFitter(penalizer=0.01)
try:
    cph_a3.fit(fit_df_a3, duration_col='duration', event_col='event_any')
    print("\nFull model summary:")
    print(cph_a3.summary[['coef','exp(coef)','exp(coef) lower 95%',
                          'exp(coef) upper 95%','p']].round(3).to_string())
except Exception as e:
    print(f"FAIL: {e}")


# ============================================================================
# VERGELIJKINGSTABEL
# ============================================================================
header("VERGELIJKINGSTABEL: Public CCUS vs v7 (S&P)")

comparison_rows = []

# v7 reference (frequentist)
comparison_rows.append({
    'analysis': 'v7 (S&P data)',
    'dataset': 'Blue_CCS vs PEM',
    'n_obs': 714,
    'n_events': 43,
    'HR': 11.93,
    'HR_lo': 4.67,
    'HR_hi': 30.49,
    'p_value': '<0.001',
    'comparator': 'Green PEM hydrogen',
})

# v7 Bayesian (weakly informative)
comparison_rows.append({
    'analysis': 'v7 Bayesian (weakly informative)',
    'dataset': 'Blue_CCS vs PEM',
    'n_obs': 714,
    'n_events': 43,
    'HR': 4.93,
    'HR_lo': 2.19,
    'HR_hi': 11.12,
    'p_value': 'CrI excludes 1',
    'comparator': 'Green PEM hydrogen',
})

# Public CCUS Model A1
if res_a1:
    comparison_rows.append({
        'analysis': 'Public A1: broad CCUS',
        'dataset': 'H2-CCUS vs all other CCUS',
        'n_obs': res_a1['n_obs'],
        'n_events': res_a1['n_events'],
        'HR': res_a1['HR'],
        'HR_lo': res_a1['HR_lo'],
        'HR_hi': res_a1['HR_hi'],
        'p_value': f"{res_a1['p_value']:.4f}",
        'comparator': 'All CCUS (DAC, T&S, Power, etc.)',
    })

# Public CCUS Model A2
if res_a2:
    comparison_rows.append({
        'analysis': 'Public A2: industrial only',
        'dataset': 'H2-CCUS vs industrial CCUS',
        'n_obs': res_a2['n_obs'],
        'n_events': res_a2['n_events'],
        'HR': res_a2['HR'],
        'HR_lo': res_a2['HR_lo'],
        'HR_hi': res_a2['HR_hi'],
        'p_value': f"{res_a2['p_value']:.4f}",
        'comparator': 'Industrial CCUS (steel, refining, etc.)',
    })

comp_df = pd.DataFrame(comparison_rows)
print(comp_df.to_string(index=False))

out_csv = OUTPUT_DIR / "v7_vs_public_comparison.csv"
comp_df.to_csv(out_csv, index=False)
print(f"\nOpgeslagen: {out_csv}")


# ============================================================================
# FOREST PLOT - hazard ratios met CIs
# ============================================================================
header("FOREST PLOT")
fig, ax = plt.subplots(figsize=(10, 5))
labels = comp_df['analysis'].tolist()
hrs = comp_df['HR'].values
hr_lo = comp_df['HR_lo'].values
hr_hi = comp_df['HR_hi'].values
y_pos = np.arange(len(labels))[::-1]

# Plot
for y, hr, lo, hi in zip(y_pos, hrs, hr_lo, hr_hi):
    ax.plot([lo, hi], [y, y], color='#4477AA', lw=2)
    ax.plot([hr], [y], 'o', color='#222222', markersize=8)

ax.axvline(1, linestyle='--', color='red', alpha=0.6, label='HR = 1 (no effect)')
ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xscale('log')
ax.set_xlabel("Hazard Ratio (log scale)")
ax.set_title("Blue hydrogen cancellation hazard: v7 (S&P) vs public IEA CCUS")
ax.grid(alpha=0.3, axis='x')
ax.legend(loc='lower right')
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "forest_plot_HR.pdf")
print(f"Opgeslagen: forest_plot_HR.pdf")
plt.close(fig)


# ============================================================================
# DIAGNOSTIEK
# ============================================================================
header("PROPORTIONAL HAZARDS ASSUMPTION CHECKS")
diag_text = []
for name, cph in [("A1", cph_a1), ("A2", cph_a2)]:
    if cph is None: continue
    try:
        ph_test = proportional_hazard_test(cph, cph.event_observed.to_frame().join(
            cph.durations.to_frame().rename(columns={0:'duration'})))
        diag_text.append(f"Model {name}:")
        diag_text.append(str(ph_test))
        diag_text.append("")
    except Exception as e:
        diag_text.append(f"Model {name}: PH test failed: {e}\n")

with open(OUTPUT_DIR / "cox_diagnostics.txt", 'w') as f:
    f.write("\n".join(diag_text))
print(f"PH-assumption tests opgeslagen: cox_diagnostics.txt")


# ============================================================================
# AFRONDEN
# ============================================================================
header("KLAAR")
print(f"Resultaten in: {OUTPUT_DIR}")
print("""
Volgende stappen:
  1. Bekijk forest_plot_HR.pdf - de visuele vergelijking
  2. v7_vs_public_comparison.csv - voor in thesis methodologie hoofdstuk
  3. Schrijf 'Public Data Robustness' sectie:
     - "When restricted to public IEA CCUS data, the H2/ammonia subsector
        shows elevated cancellation hazards consistent with v7 findings."
""")
