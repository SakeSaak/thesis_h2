"""
12_pooled_sponsor_control.py

Pooled (alle regio's) carbon-conditional analyse met sponsor controls.

Drie specificaties:
  M_base:    geen sponsor controle (baseline, reproduceert pooled finding)
  M_sponsor: voegt sponsor_known indicator toe
  M_full:    voegt OOK Blue × sponsor_known interactie toe

Doel: testen of de pooled β_int = -1.37 robuust is tegen sponsor confounding.
Hypothese: omdat NA-events (waar finding robuust is) numeriek domineren in pooled
sample, blijft β_int dichtbij -1.37 ook met sponsor controle.

Maar: misschien verandert het wel als sponsor_known correleert met EU-events
en daarmee met de "verkeerde" EU-signaal in pooled data.
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import pymc as pm
import pytensor.tensor as pt
import arviz as az
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUT = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_pooled_sponsor"
OUT.mkdir(parents=True, exist_ok=True)

N_DRAWS, N_TUNE, N_CHAINS, TARGET_ACCEPT = 1500, 2000, 4, 0.98
SEED = 20260518

def hdr(t): print("\n" + "=" * 72 + f"\n{t}\n" + "=" * 72)
def safe_float(x):
    if isinstance(x, (int, float, np.number)): return float(x)
    try: return float(str(x).split("±")[0].strip())
    except: return float("nan")
def hdi_cols(s):
    cols = list(s.columns)
    lo = [c for c in cols if 'lb' in c.lower() or 'hdi_3' in c.lower() or 'hdi_2' in c.lower()][0]
    hi = [c for c in cols if 'ub' in c.lower() or 'hdi_97' in c.lower() or 'hdi_94' in c.lower()][0]
    return lo, hi

# ============================================================================
# Data prep
# ============================================================================
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)
df['sponsor_known'] = (df['sponsor_owner'].astype(str) != 'Unknown').astype(int)

mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()

# Pooled panel
panel_rows = []
for idx, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': idx, 'year_calendar': t,
            'is_blue_ccs': int(row['is_blue_ccs']),
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'year_since_start': t - t_start,
            'log_capacity_mw': float(row['log_capacity_mw']),
            'sponsor_known': int(row['sponsor_known']),
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['eua'].fillna(panel['eua'].median())
eua_mean = panel['mkt_eua'].mean()
eua_sd = panel['mkt_eua'].std()
panel['z'] = (panel['mkt_eua'] - eua_mean) / eua_sd

hdr("Pooled sample karakteristieken")
print(f"Totaal person-years: {len(panel)}")
print(f"Totaal events: {panel['event_any_yr'].sum()}")
print(f"\nEvents per (Blue, sponsor_known):")
ev_table = panel[panel['event_any_yr']==1].groupby(['is_blue_ccs','sponsor_known']).size().rename('n_events').reset_index()
print(ev_table.to_string(index=False))

print(f"\nAt-risk per (Blue, sponsor_known):")
ar_table = panel.groupby(['is_blue_ccs','sponsor_known']).size().rename('n_obs').reset_index()
print(ar_table.to_string(index=False))


# ============================================================================
# M_base: geen sponsor controle
# ============================================================================
hdr("M_base: Pooled zonder sponsor controle (baseline)")

X_blue = panel['is_blue_ccs'].values.astype(float)
X_z = panel['z'].values.astype(float)
X_year = panel['year_since_start'].values.astype(float)
X_cap = panel['log_capacity_mw'].values.astype(float)
X_sk = panel['sponsor_known'].values.astype(float)
events = panel['event_any_yr'].values.astype(int)

with pm.Model() as m_base:
    alpha = pm.Normal("alpha", -5, 1.5)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_eua = pm.Normal("beta_eua", 0, 2)
    b_int = pm.Normal("beta_int", 0, 2)
    b_year = pm.Normal("beta_year_since", 0, 1.5)
    b_cap = pm.Normal("beta_cap", 0, 1.5)
    eta = alpha + b_blue*X_blue + b_eua*X_z + b_int*X_blue*X_z + b_year*X_year + b_cap*X_cap
    pm.Bernoulli("events", logit_p=eta, observed=events)
    trace_base = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                            target_accept=TARGET_ACCEPT, random_seed=SEED,
                            progressbar=False, return_inferencedata=True)

s_base = az.summary(trace_base, var_names=["beta_int","beta_blue","beta_eua"])
print(s_base.round(3).to_string())
lo_c, hi_c = hdi_cols(s_base)
base_bint_mean = safe_float(s_base.loc['beta_int','mean'])
base_bint_lo = safe_float(s_base.loc['beta_int',lo_c])
base_bint_hi = safe_float(s_base.loc['beta_int',hi_c])


# ============================================================================
# M_sponsor: met sponsor_known additieve controle
# ============================================================================
hdr("M_sponsor: Pooled MET sponsor_known additieve controle")

with pm.Model() as m_sp:
    alpha = pm.Normal("alpha", -5, 1.5)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_eua = pm.Normal("beta_eua", 0, 2)
    b_int = pm.Normal("beta_int", 0, 2)
    b_year = pm.Normal("beta_year_since", 0, 1.5)
    b_cap = pm.Normal("beta_cap", 0, 1.5)
    b_sk = pm.Normal("beta_sponsor_known", 0, 1.5)
    eta = (alpha + b_blue*X_blue + b_eua*X_z + b_int*X_blue*X_z 
           + b_year*X_year + b_cap*X_cap + b_sk*X_sk)
    pm.Bernoulli("events", logit_p=eta, observed=events)
    trace_sp = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                          target_accept=TARGET_ACCEPT, random_seed=SEED,
                          progressbar=False, return_inferencedata=True)

s_sp = az.summary(trace_sp, var_names=["beta_int","beta_blue","beta_eua","beta_sponsor_known"])
print(s_sp.round(3).to_string())
sp_bint_mean = safe_float(s_sp.loc['beta_int','mean'])
sp_bint_lo = safe_float(s_sp.loc['beta_int',lo_c])
sp_bint_hi = safe_float(s_sp.loc['beta_int',hi_c])


# ============================================================================
# M_full: MET sponsor_known additief EN Blue × sponsor_known interactie
# ============================================================================
hdr("M_full: Pooled MET volledige sponsor specificatie (additief + interactie)")

with pm.Model() as m_full:
    alpha = pm.Normal("alpha", -5, 1.5)
    b_blue = pm.Normal("beta_blue", 0, 2)
    b_eua = pm.Normal("beta_eua", 0, 2)
    b_int = pm.Normal("beta_int", 0, 2)
    b_year = pm.Normal("beta_year_since", 0, 1.5)
    b_cap = pm.Normal("beta_cap", 0, 1.5)
    b_sk = pm.Normal("beta_sponsor_known", 0, 1.5)
    b_sk_blue = pm.Normal("beta_sponsor_x_blue", 0, 1.5)
    eta = (alpha + b_blue*X_blue + b_eua*X_z + b_int*X_blue*X_z 
           + b_year*X_year + b_cap*X_cap + b_sk*X_sk + b_sk_blue*X_sk*X_blue)
    pm.Bernoulli("events", logit_p=eta, observed=events)
    trace_full = pm.sample(N_DRAWS, tune=N_TUNE, chains=N_CHAINS,
                            target_accept=TARGET_ACCEPT, random_seed=SEED,
                            progressbar=False, return_inferencedata=True)

s_full = az.summary(trace_full, var_names=["beta_int","beta_blue","beta_eua","beta_sponsor_known","beta_sponsor_x_blue"])
print(s_full.round(3).to_string())
full_bint_mean = safe_float(s_full.loc['beta_int','mean'])
full_bint_lo = safe_float(s_full.loc['beta_int',lo_c])
full_bint_hi = safe_float(s_full.loc['beta_int',hi_c])


# ============================================================================
# COMPARISON TABLE
# ============================================================================
hdr("VERGELIJKING: Pooled β_int across specifications")
print(f"\n{'Specificatie':<35s} | β_int      | 95% CrI")
print("-" * 80)
print(f"{'M_base: zonder sponsor':<35s} | {base_bint_mean:+.3f}     | [{base_bint_lo:+.2f}, {base_bint_hi:+.2f}]")
print(f"{'M_sponsor: additieve controle':<35s} | {sp_bint_mean:+.3f}     | [{sp_bint_lo:+.2f}, {sp_bint_hi:+.2f}]")
print(f"{'M_full: + Blue×sponsor interactie':<35s} | {full_bint_mean:+.3f}     | [{full_bint_lo:+.2f}, {full_bint_hi:+.2f}]")

delta1 = sp_bint_mean - base_bint_mean
delta2 = full_bint_mean - base_bint_mean
print(f"\nVerschuiving β_int door sponsor controle:")
print(f"  Additief:  Δ = {delta1:+.3f}")
print(f"  Volledig:  Δ = {delta2:+.3f}")

# Interpretatie
sponsor_main = safe_float(s_sp.loc['beta_sponsor_known','mean'])
sponsor_main_lo = safe_float(s_sp.loc['beta_sponsor_known',lo_c])
sponsor_main_hi = safe_float(s_sp.loc['beta_sponsor_known',hi_c])
sponsor_int = safe_float(s_full.loc['beta_sponsor_x_blue','mean'])
sponsor_int_lo = safe_float(s_full.loc['beta_sponsor_x_blue',lo_c])
sponsor_int_hi = safe_float(s_full.loc['beta_sponsor_x_blue',hi_c])

print(f"\nSponsor-related coefficienten (M_full):")
print(f"  β_sponsor_known: {sponsor_main:+.3f} [{sponsor_main_lo:+.2f}, {sponsor_main_hi:+.2f}]")
print(f"  β_sponsor×Blue:  {sponsor_int:+.3f} [{sponsor_int_lo:+.2f}, {sponsor_int_hi:+.2f}]")

print("\nINTERPRETATIE:")
if abs(delta2) < 0.3:
    print("  ✓ β_int is ROBUST tegen sponsor controle (verschuiving < 0.3)")
    print("    De pooled finding wordt niet fundamenteel veranderd door sponsor-confounding.")
    print("    Dit is omdat de NA-events (waar finding robuust is) numeriek domineren.")
elif abs(delta2) < 0.6:
    print("  ~ β_int is MATIG GEVOELIG voor sponsor controle (verschuiving 0.3-0.6)")
    print("    Pooled finding houdt zich staande maar moet gerapporteerd worden met deze caveat.")
else:
    print("  ✗ β_int is STERK GEVOELIG voor sponsor controle (verschuiving > 0.6)")
    print("    Pooled finding is fragiel — narrative moet voornamelijk op NA-only resultaat steunen.")

if sponsor_int_hi < 0:
    print(f"  ✗ Blue × sponsor_known coefficient is significant negatief: NAMED sponsor's Blue projecten cancelen MINDER")
elif sponsor_int_lo > 0:
    print(f"  ! Blue × sponsor_known coefficient is significant positief: NAMED sponsor's Blue projecten cancelen MEER")
else:
    print(f"  ~ Blue × sponsor_known coefficient niet significant: geen differentieel sponsor-effect")


# ============================================================================
# Save & visualize
# ============================================================================
results_df = pd.DataFrame([
    {'spec':'M_base','beta_int':base_bint_mean,'lo':base_bint_lo,'hi':base_bint_hi},
    {'spec':'M_sponsor','beta_int':sp_bint_mean,'lo':sp_bint_lo,'hi':sp_bint_hi},
    {'spec':'M_full','beta_int':full_bint_mean,'lo':full_bint_lo,'hi':full_bint_hi},
])
results_df.to_csv(OUT / "pooled_sponsor_comparison.csv", index=False)

fig, ax = plt.subplots(figsize=(9, 5))
specs = ['M_base\nbaseline', 'M_sponsor\n+sponsor', 'M_full\n+sponsor×Blue']
means = [base_bint_mean, sp_bint_mean, full_bint_mean]
los = [base_bint_lo, sp_bint_lo, full_bint_lo]
his = [base_bint_hi, sp_bint_hi, full_bint_hi]
errs = [(m-l, h-m) for m,l,h in zip(means,los,his)]
errs = np.array(errs).T

ax.errorbar(range(3), means, yerr=errs, fmt='o', markersize=10, capsize=8, capthick=2, lw=2, color='#222288')
ax.axhline(0, ls='--', color='red', alpha=0.5)
ax.axhline(-1.17, ls=':', color='green', alpha=0.6, label='NA Static β = -1.17')
ax.axhline(-1.88, ls=':', color='darkgreen', alpha=0.6, label='NA GAS ω = -1.88')
ax.set_xticks(range(3))
ax.set_xticklabels(specs)
ax.set_ylabel(r"$\beta_{\mathrm{int}}$")
ax.set_title("Pooled carbon-conditional coefficient: robustness to sponsor controls")
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(OUT / "pooled_sponsor_robustness.pdf")
plt.close()
print(f"\nFiguur opgeslagen: pooled_sponsor_robustness.pdf")
print(f"\nResultaten in: {OUT}")
