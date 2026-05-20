"""
46_counterfactual_scenarios.py
============================================================================
Pijler 36: Counterfactual policy scenarios — getallen voor beleidsmakers
============================================================================
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
SP_PATH = PROJECT_ROOT / "01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/14_counterfactual"
FIG_DIR = OUTPUT_DIR / "figures"

SEED = 20260520
np.random.seed(SEED)
N_BOOTSTRAP = 500
HORIZON_YEARS = 3


def header(t):
    print("\n" + "=" * 78 + f"\n  {t}\n" + "=" * 78)


# === STAP 1: DATA + ATE INVENTARIS ===
header("STAP 1: Data en empirische ATE-input")

sp = pd.read_excel(SP_PATH, sheet_name='Export')
sp['announce_year'] = pd.to_datetime(sp['Date announced'], errors='coerce').dt.year
sp = sp[sp['announce_year'].notna()].copy()
sp['is_blue'] = (sp['Technology2'] == 'Fossil with CCS').astype(int)
sp['is_green'] = sp['H2 Technology'].isin(['PEM', 'Alkaline', 'SOEC', 'AEM', 'Alkaline & PEM']).astype(int)
df = sp[(sp['is_blue']==1) | (sp['is_green']==1)].copy().reset_index(drop=True)
df['failure'] = df['project_status'].isin(['Plans cancelled', 'On-hold (assumed)', 'On-hold (confirmed)', 'Decommissioned']).astype(int)
df['has_offtake'] = ((df['Offtake name'].notna()) | (df['Offtaker'].notna())).astype(int)

df['is_us'] = (df['Geography'] == 'United States').astype(int)
df['is_eu'] = (df['Region major'] == 'Europe (EU-27)').astype(int)
df['is_uk'] = (df['Geography'] == 'United Kingdom').astype(int)
df['is_china'] = (df['Geography'] == 'China').astype(int)
df['is_oecd'] = ((df['is_us']==1) | (df['is_eu']==1) | (df['is_uk']==1) | 
                 df['Geography'].isin(['Japan','South Korea','Canada','Australia','Norway','Switzerland'])).astype(int)

df['h2_capacity_ty'] = pd.to_numeric(df['Output capacity per year'], errors='coerce')
df['h2_unit'] = df['H2 capacity unit'].astype(str).str.lower()
df.loc[df['h2_unit'].str.contains('kg', na=False), 'h2_capacity_ty'] = df['h2_capacity_ty'] / 1000.0
df.loc[df['h2_unit'].str.contains('mw', na=False), 'h2_capacity_ty'] = df['h2_capacity_ty'] * 150.0
df['h2_capacity_ty'] = df['h2_capacity_ty'].fillna(df['h2_capacity_ty'].median())
df['co2_capture_ty'] = pd.to_numeric(df['Co2 capture (t/y)'], errors='coerce').fillna(0.0)

SECTOR_MAP = {
    'Industry (chemical feedstock)': 'chemical',
    'Industry (refinery feedstock)': 'refinery',
    'Power & heat': 'power_heat',
    'Transport (road)': 'transport',
    'Transport (shipping)': 'transport_marine',
    'Industry (other)': 'industry',
    'Gas grid': 'gas_grid',
}
df['sector_grp'] = df['Primary end use sector'].map(SECTOR_MAP).fillna('other')

print(f"Sample: N={len(df)}, failures={df['failure'].sum()} ({df['failure'].mean()*100:.1f}%)")

ATE_INPUTS = {
    '45Q_blue':       {'point': -0.045, 'se': 0.012, 'source': 'BJS-imputation Pijler 32, Honest M*=0.2'},
    'offtake_all':    {'point': -0.111, 'se': 0.031, 'source': 'PSM 1:3 Pijler 34, Oster delta_null=20.23'},
    'offtake_high_s': {'point': -0.228, 'se': 0.083, 'source': 'Sector LPM Pijler 34 (power & heat, refinery)'},
    'offtake_low_s':  {'point': -0.071, 'se': 0.074, 'source': 'Sector LPM (chemical)'},
    'china_fyp':      {'point': -0.045, 'se': 0.015, 'source': 'BJS Pijler 32, Honest M*=1.5 ROBUUST'},
    'uk_track_eff':   {'point': +0.036, 'se': 0.018, 'source': 'TWFE Pijler 27 (selection-funnel artefact)'},
}

print("\nATE inputs:")
for k, v in ATE_INPUTS.items():
    print(f"  {k:<18}: {v['point']:+.3f} +/- {v['se']:.3f}  ({v['source']})")


def cumulative_effect(annual_ate, horizon_years=HORIZON_YEARS):
    return annual_ate * horizon_years


def run_scenario(name, target_projects, annual_ate, ate_se, capacity_col='h2_capacity_ty'):
    if len(target_projects) == 0:
        return None
    cum_ate = cumulative_effect(annual_ate)
    n_extra_fid = -cum_ate * len(target_projects)
    avg_capacity = target_projects[capacity_col].mean()
    total_extra_capacity = n_extra_fid * avg_capacity
    avg_co2 = target_projects['co2_capture_ty'].mean()
    total_extra_co2 = n_extra_fid * avg_co2
    
    boot_n_fid, boot_capacity, boot_co2 = [], [], []
    rng = np.random.default_rng(SEED)
    for _ in range(N_BOOTSTRAP):
        ate_b = rng.normal(annual_ate, ate_se)
        cum_b = cumulative_effect(ate_b)
        idx_boot = rng.integers(0, len(target_projects), size=len(target_projects))
        sub_b = target_projects.iloc[idx_boot]
        n_b = -cum_b * len(sub_b)
        boot_n_fid.append(n_b)
        boot_capacity.append(n_b * sub_b[capacity_col].mean())
        boot_co2.append(n_b * sub_b['co2_capture_ty'].mean())
    
    return {
        'scenario': name,
        'n_target_projects': len(target_projects),
        'annual_ATE': annual_ate,
        'n_extra_FIDs_point': n_extra_fid,
        'n_extra_FIDs_lo': float(np.percentile(boot_n_fid, 2.5)),
        'n_extra_FIDs_hi': float(np.percentile(boot_n_fid, 97.5)),
        'avg_capacity_per_project': avg_capacity,
        'total_extra_capacity_point': total_extra_capacity,
        'total_extra_capacity_lo': float(np.percentile(boot_capacity, 2.5)),
        'total_extra_capacity_hi': float(np.percentile(boot_capacity, 97.5)),
        'total_extra_co2_point_ty': total_extra_co2,
        'total_extra_co2_lo_ty': float(np.percentile(boot_co2, 2.5)),
        'total_extra_co2_hi_ty': float(np.percentile(boot_co2, 97.5)),
    }


scenarios = {}


# === S1: EU 45Q-equivalent ===
header("S1: EU adopteert 45Q-equivalent (Blue)")
eu_blue = df[(df['is_eu']==1) & (df['is_blue']==1)].copy()
print(f"Target: EU Blue N={len(eu_blue)}, failure rate={eu_blue['failure'].mean()*100:.1f}%")
print(f"Avg CO2 capture: {eu_blue['co2_capture_ty'].mean():,.0f} t/y CO2")
s1 = run_scenario('S1: EU 45Q-equivalent (Blue)', eu_blue, ATE_INPUTS['45Q_blue']['point'], ATE_INPUTS['45Q_blue']['se'])
scenarios['S1_EU_45Q'] = s1
print(f"  Extra FIDs (3y): {s1['n_extra_FIDs_point']:.1f} [{s1['n_extra_FIDs_lo']:.1f}, {s1['n_extra_FIDs_hi']:.1f}]")
print(f"  Extra CO2: {s1['total_extra_co2_point_ty']/1e6:.2f} Mt/y [{s1['total_extra_co2_lo_ty']/1e6:.2f}, {s1['total_extra_co2_hi_ty']/1e6:.2f}]")


# === S2: EU offtake-mandate ===
header("S2: EU koppelt IF-eligibility aan offtake (Green sans offtake)")
eu_green_no_off = df[(df['is_eu']==1) & (df['is_green']==1) & (df['has_offtake']==0) & (df['announce_year']>=2017)].copy()
print(f"Target: EU Green sans offtake post-2017 N={len(eu_green_no_off)}, failure={eu_green_no_off['failure'].mean()*100:.1f}%")
s2 = run_scenario('S2: EU offtake-mandate (Green)', eu_green_no_off, ATE_INPUTS['offtake_all']['point'], ATE_INPUTS['offtake_all']['se'])
scenarios['S2_EU_offtake'] = s2
print(f"  Extra FIDs (3y): {s2['n_extra_FIDs_point']:.1f} [{s2['n_extra_FIDs_lo']:.1f}, {s2['n_extra_FIDs_hi']:.1f}]")
print(f"  Extra H2: {s2['total_extra_capacity_point']/1e3:.0f} kt/y [{s2['total_extra_capacity_lo']/1e3:.0f}, {s2['total_extra_capacity_hi']/1e3:.0f}]")


# === S3: UK switch to 45Q ===
header("S3: UK switch Track-1 -> 45Q (Blue)")
uk_blue = df[(df['is_uk']==1) & (df['is_blue']==1)].copy()
print(f"Target: UK Blue N={len(uk_blue)}, failure={uk_blue['failure'].mean()*100:.1f}%")
swap_ate = ATE_INPUTS['45Q_blue']['point'] - ATE_INPUTS['uk_track_eff']['point']
swap_se = np.sqrt(ATE_INPUTS['45Q_blue']['se']**2 + ATE_INPUTS['uk_track_eff']['se']**2)
print(f"Swap ATE: {swap_ate:+.4f} +/- {swap_se:.4f}")
s3 = run_scenario('S3: UK switch to 45Q', uk_blue, swap_ate, swap_se)
scenarios['S3_UK_45Q'] = s3
print(f"  Extra FIDs (3y): {s3['n_extra_FIDs_point']:.1f} [{s3['n_extra_FIDs_lo']:.1f}, {s3['n_extra_FIDs_hi']:.1f}]")
print(f"  Extra CO2: {s3['total_extra_co2_point_ty']/1e6:.2f} Mt/y")


# === S4: OECD China-FYP-equivalent ===
header("S4: OECD China-FYP-equivalent state-mandate (Green)")
oecd_green = df[(df['is_oecd']==1) & (df['is_green']==1) & (df['is_china']==0)].copy()
print(f"Target: OECD Green (excl China) N={len(oecd_green)}, failure={oecd_green['failure'].mean()*100:.1f}%")
print(f"  Note: gebruikt China FYP ATE die Honest DiD overleeft (M*=1.5)")
s4 = run_scenario('S4: OECD China-FYP-equivalent', oecd_green, ATE_INPUTS['china_fyp']['point'], ATE_INPUTS['china_fyp']['se'])
scenarios['S4_OECD_FYP'] = s4
print(f"  Extra FIDs (3y): {s4['n_extra_FIDs_point']:.1f} [{s4['n_extra_FIDs_lo']:.1f}, {s4['n_extra_FIDs_hi']:.1f}]")
print(f"  Extra H2: {s4['total_extra_capacity_point']/1e3:.0f} kt/y")


# === S5: EU sector-optimal mix ===
header("S5: EU sector-optimal carrot mix (full sample post-2017)")
eu_full = df[(df['is_eu']==1) & (df['announce_year']>=2017)].copy()
print(f"Target: EU full post-2017 N={len(eu_full)}")

SECTOR_ATE_MAP = {
    'chemical':         ATE_INPUTS['45Q_blue']['point'],
    'refinery':         ATE_INPUTS['offtake_high_s']['point'],
    'power_heat':       ATE_INPUTS['offtake_high_s']['point'],
    'transport':        ATE_INPUTS['offtake_all']['point'],
    'transport_marine': ATE_INPUTS['offtake_all']['point'],
    'industry':         ATE_INPUTS['45Q_blue']['point'],
    'gas_grid':         ATE_INPUTS['offtake_all']['point'],
    'other':            ATE_INPUTS['offtake_all']['point'],
}
SECTOR_SE_MAP = {
    'chemical':         ATE_INPUTS['45Q_blue']['se'],
    'refinery':         ATE_INPUTS['offtake_high_s']['se'],
    'power_heat':       ATE_INPUTS['offtake_high_s']['se'],
    'transport':        ATE_INPUTS['offtake_all']['se'],
    'transport_marine': ATE_INPUTS['offtake_all']['se'],
    'industry':         ATE_INPUTS['45Q_blue']['se'],
    'gas_grid':         ATE_INPUTS['offtake_all']['se'],
    'other':            ATE_INPUTS['offtake_all']['se'],
}

sector_results = []
total_extra_fid_point = 0.0
total_extra_capacity_point = 0.0
total_extra_co2_point = 0.0
boot_total_fid = np.zeros(N_BOOTSTRAP)
boot_total_cap = np.zeros(N_BOOTSTRAP)
boot_total_co2 = np.zeros(N_BOOTSTRAP)
rng_s5 = np.random.default_rng(SEED+1)

for sector, ate_pt in SECTOR_ATE_MAP.items():
    sub = eu_full[eu_full['sector_grp']==sector]
    if len(sub) < 5: continue
    cum_ate = cumulative_effect(ate_pt)
    n_extra = -cum_ate * len(sub)
    cap_extra = n_extra * sub['h2_capacity_ty'].mean()
    co2_extra = n_extra * sub['co2_capture_ty'].mean()
    sector_results.append({
        'sector': sector, 'n_projects': len(sub),
        'annual_ATE_used': ate_pt,
        'mechanism': 'sigma-attack' if abs(ate_pt) > 0.1 else 'V/I-boost',
        'n_extra_FIDs': n_extra,
        'extra_capacity_ty': cap_extra,
        'extra_co2_ty': co2_extra,
    })
    total_extra_fid_point += n_extra
    total_extra_capacity_point += cap_extra
    total_extra_co2_point += co2_extra
    ate_se = SECTOR_SE_MAP[sector]
    for b in range(N_BOOTSTRAP):
        ate_b = rng_s5.normal(ate_pt, ate_se)
        cum_b = cumulative_effect(ate_b)
        idx_b = rng_s5.integers(0, len(sub), size=len(sub))
        sub_b = sub.iloc[idx_b]
        n_b = -cum_b * len(sub_b)
        boot_total_fid[b] += n_b
        boot_total_cap[b] += n_b * sub_b['h2_capacity_ty'].mean()
        boot_total_co2[b] += n_b * sub_b['co2_capture_ty'].mean()

s5 = {
    'scenario': 'S5: EU sector-optimal mix',
    'n_target_projects': len(eu_full),
    'annual_ATE': np.nan,
    'n_extra_FIDs_point': total_extra_fid_point,
    'n_extra_FIDs_lo': float(np.percentile(boot_total_fid, 2.5)),
    'n_extra_FIDs_hi': float(np.percentile(boot_total_fid, 97.5)),
    'avg_capacity_per_project': np.nan,
    'total_extra_capacity_point': total_extra_capacity_point,
    'total_extra_capacity_lo': float(np.percentile(boot_total_cap, 2.5)),
    'total_extra_capacity_hi': float(np.percentile(boot_total_cap, 97.5)),
    'total_extra_co2_point_ty': total_extra_co2_point,
    'total_extra_co2_lo_ty': float(np.percentile(boot_total_co2, 2.5)),
    'total_extra_co2_hi_ty': float(np.percentile(boot_total_co2, 97.5)),
}
scenarios['S5_EU_sector_mix'] = s5
print(f"  Total extra FIDs: {s5['n_extra_FIDs_point']:.1f} [{s5['n_extra_FIDs_lo']:.1f}, {s5['n_extra_FIDs_hi']:.1f}]")
print(f"  Total extra H2: {s5['total_extra_capacity_point']/1e3:.0f} kt/y")
print(f"  Total extra CO2: {s5['total_extra_co2_point_ty']/1e6:.2f} Mt/y")
print(f"\nPer sector:")
for r in sector_results:
    print(f"  {r['sector']:<20}: N={r['n_projects']:>3}, ATE={r['annual_ATE_used']:+.3f}, mech={r['mechanism']:<13}, "
          f"FIDs={r['n_extra_FIDs']:>5.1f}, CO2={r['extra_co2_ty']/1e3:>6.0f} kt/y")


# === SAMENVATTING + EXPORT ===
header("Samenvatting + Export")
summary_rows = []
for k, s in scenarios.items():
    summary_rows.append({
        'scenario': s['scenario'],
        'n_target_projects': s['n_target_projects'],
        'extra_FIDs_point': s['n_extra_FIDs_point'],
        'extra_FIDs_CI_lo': s['n_extra_FIDs_lo'],
        'extra_FIDs_CI_hi': s['n_extra_FIDs_hi'],
        'extra_capacity_ty_point': s['total_extra_capacity_point'],
        'extra_capacity_kty_point': s['total_extra_capacity_point']/1e3,
        'extra_co2_ty_point': s['total_extra_co2_point_ty'],
        'extra_co2_mty_point': s['total_extra_co2_point_ty']/1e6,
        'extra_co2_mty_CI_lo': s['total_extra_co2_lo_ty']/1e6,
        'extra_co2_mty_CI_hi': s['total_extra_co2_hi_ty']/1e6,
    })
summary_df = pd.DataFrame(summary_rows)
print("\n", summary_df.to_string(index=False))
summary_df.to_csv(OUTPUT_DIR / 'pijler36_scenario_summary.csv', index=False)
pd.DataFrame(sector_results).to_csv(OUTPUT_DIR / 'pijler36_sector_optimal_mix.csv', index=False)


# === PLOTS ===
header("Plots")
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

ax = axes[0, 0]
scen_short = ['EU 45Q\n(Blue)', 'EU offtake\nmandate', 'UK->45Q\n(Blue)', 'OECD FYP\n(Green)', 'EU sector\nmix']
y_pos = np.arange(len(scenarios))
points = [s['n_extra_FIDs_point'] for s in scenarios.values()]
los = [s['n_extra_FIDs_lo'] for s in scenarios.values()]
his = [s['n_extra_FIDs_hi'] for s in scenarios.values()]
colors_s = ['#9c27b0', '#1f77b4', '#d62728', '#ff7f0e', '#2ca02c']
xerr_lo = [max(0, p-l) for p,l in zip(points, los)]
xerr_hi = [max(0, h-p) for p,h in zip(points, his)]
ax.barh(y_pos, points, xerr=[xerr_lo, xerr_hi], color=colors_s, edgecolor='black', capsize=6)
ax.set_yticks(y_pos); ax.set_yticklabels(scen_short, fontsize=10)
ax.set_xlabel('Extra FIDs over 3-year horizon')
ax.set_title('Counterfactual scenarios: extra FIDs (95% CI)')
ax.axvline(x=0, color='black', linewidth=0.8)
for i, p in enumerate(points):
    ax.text(p + 2 if p > 0 else p - 2, i, f'{p:+.0f}', va='center', fontsize=10, fontweight='bold')
ax.grid(alpha=0.3, axis='x')

ax = axes[0, 1]
co2_scens = ['S1_EU_45Q', 'S3_UK_45Q', 'S5_EU_sector_mix']
co2_names = ['EU 45Q\nequivalent', 'UK switch\nto 45Q', 'EU sector\nmix']
co2_pts = [scenarios[k]['total_extra_co2_point_ty']/1e6 for k in co2_scens]
co2_lo = [scenarios[k]['total_extra_co2_lo_ty']/1e6 for k in co2_scens]
co2_hi = [scenarios[k]['total_extra_co2_hi_ty']/1e6 for k in co2_scens]
yerr_lo = [max(0, p-l) for p,l in zip(co2_pts, co2_lo)]
yerr_hi = [max(0, h-p) for p,h in zip(co2_pts, co2_hi)]
ax.bar(range(len(co2_scens)), co2_pts, yerr=[yerr_lo, yerr_hi], color=['#9c27b0', '#d62728', '#2ca02c'], edgecolor='black', capsize=6)
ax.set_xticks(range(len(co2_scens))); ax.set_xticklabels(co2_names, fontsize=10)
ax.set_ylabel('Extra CO2 capture (Mt/y)')
ax.set_title('CO2-impact (Blue projecten)')
for i, p in enumerate(co2_pts):
    ax.text(i, p + 0.05, f'{p:+.2f} Mt/y', ha='center', fontsize=10, fontweight='bold')
ax.grid(alpha=0.3, axis='y')

ax = axes[1, 0]
h2_scens = ['S2_EU_offtake', 'S4_OECD_FYP', 'S5_EU_sector_mix']
h2_names = ['EU offtake\nmandate', 'OECD\nFYP-equiv.', 'EU sector\nmix']
h2_pts = [scenarios[k]['total_extra_capacity_point']/1e3 for k in h2_scens]
h2_lo = [scenarios[k]['total_extra_capacity_lo']/1e3 for k in h2_scens]
h2_hi = [scenarios[k]['total_extra_capacity_hi']/1e3 for k in h2_scens]
yerr_lo = [max(0, p-l) for p,l in zip(h2_pts, h2_lo)]
yerr_hi = [max(0, h-p) for p,h in zip(h2_pts, h2_hi)]
ax.bar(range(len(h2_scens)), h2_pts, yerr=[yerr_lo, yerr_hi], color=['#1f77b4', '#ff7f0e', '#2ca02c'], edgecolor='black', capsize=6)
ax.set_xticks(range(len(h2_scens))); ax.set_xticklabels(h2_names, fontsize=10)
ax.set_ylabel('Extra H2 capacity (kt/y)')
ax.set_title('H2-impact (Green projecten)')
for i, p in enumerate(h2_pts):
    ax.text(i, p + max(h2_pts)*0.02, f'{p:+.0f} kt/y', ha='center', fontsize=10, fontweight='bold')
ax.grid(alpha=0.3, axis='y')

ax = axes[1, 1]
sect_df = pd.DataFrame(sector_results).sort_values('n_extra_FIDs', ascending=True)
ax.barh(range(len(sect_df)), sect_df['n_extra_FIDs'], color='#2ca02c', edgecolor='black')
ax.set_yticks(range(len(sect_df))); ax.set_yticklabels(sect_df['sector'], fontsize=10)
ax.set_xlabel('Extra FIDs per sector (3y horizon)')
ax.set_title('S5 detail: per-sector optimal mechanism')
for i, v in enumerate(sect_df['n_extra_FIDs']):
    ax.text(v + 0.5, i, f'{v:+.1f}', va='center', fontsize=9, fontweight='bold')
ax.axvline(x=0, color='black', linewidth=0.8); ax.grid(alpha=0.3, axis='x')

plt.suptitle('Pijler 36: Counterfactual policy scenarios voor beleidsmakers', fontsize=14, fontweight='bold', y=1.00)
plt.tight_layout()
fig.savefig(FIG_DIR / 'pijler36_counterfactual_scenarios.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: pijler36_counterfactual_scenarios.png")


# === EINDCONCLUSIE ===
print("\n" + "=" * 78)
print("EINDCONCLUSIE PIJLER 36")
print("=" * 78)
print(f"""
KEY SCENARIO IMPACT (3-year horizon, 95% CI):
""")
for k, s in scenarios.items():
    name = s['scenario']
    fid = f"{s['n_extra_FIDs_point']:+.0f} [{s['n_extra_FIDs_lo']:+.0f}, {s['n_extra_FIDs_hi']:+.0f}]"
    if abs(s['total_extra_co2_point_ty']) > 1000:
        impact = f"{s['total_extra_co2_point_ty']/1e6:+.2f} Mt/y CO2"
    else:
        impact = f"{s['total_extra_capacity_point']/1e3:+.0f} kt/y H2"
    print(f"  {name:<35}: {fid:<25}  {impact}")

print(f"""

STAKEHOLDER ROUTES:

EU DG CLIMA:
  - S1 (45Q-equivalent): {scenarios['S1_EU_45Q']['total_extra_co2_point_ty']/1e6:+.2f} Mt/y CO2 capture extra
  - S2 (offtake-mandate): {scenarios['S2_EU_offtake']['n_extra_FIDs_point']:+.0f} extra FIDs, {scenarios['S2_EU_offtake']['total_extra_capacity_point']/1e3:+.0f} kt/y H2
  - S5 (sector-mix): {scenarios['S5_EU_sector_mix']['total_extra_co2_point_ty']/1e6:+.2f} Mt/y CO2 + {scenarios['S5_EU_sector_mix']['total_extra_capacity_point']/1e3:+.0f} kt/y H2

GASUNIE BL Waterstof:
  - S2 (offtake-mandate) - HyNetwork business case lesson uit UK Track aggregation
  - Hub-effect onderbouwing voor Backbone via cluster mechanisms
  - Generic (niet NL-specifiek) findings extrapolable

SPONSORS:
  - Offtake-mandate: 11-13 pp failure reduction across sectors
  - Sector targeting: power & heat (-22.8 pp), refinery (-25.7 pp)
  - Carrot-policy interactie potentieel via offtake + grant combinaties

OUTPUT:
- pijler36_scenario_summary.csv
- pijler36_sector_optimal_mix.csv
- pijler36_counterfactual_scenarios.png
""")
