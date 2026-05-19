"""
03_block2_diagnostic.py

Robustness check: is het Block 2 (2023-2024) null-resultaat een echt
economisch signaal, of een identification-artefact?

Drie diagnostics:
  1. EUA variantie per block (Hypothese B)
  2. Event distributie per (year x blue) cel per block
  3. Within-block correlatie tussen (Blue x EUA) variatie en event rate
"""
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
PROJECT_CSV = PROJECT_ROOT / "01_data/intermediate/blueccs_project_level_for_R.csv"
MASTER_PANEL_MONTHLY = PROJECT_ROOT / "01_data/intermediate/master_panel_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/05_state_space_tvp/results_blocks"

def year_to_block(y):
    if y <= 2019: return 0
    if y <= 2022: return 1
    if y <= 2024: return 2
    return 3
BLOCK_NAMES = ["2010-2019 Pre-crisis", "2020-2022 Pandemic+early",
               "2023-2024 Peak cancellations", "2025-2026 Normalization"]

# === Rebuild panel (identiek aan 02_tvp_hazard_blocks.py) ===
df = pd.read_csv(PROJECT_CSV)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)
df['year_announced'] = df['year_announced'].astype(int)
df['duration'] = df['duration'].astype(int).clip(lower=1)
df['event_any'] = (df['event_type'] > 0).astype(int)

panel_rows = []
for idx, row in df.iterrows():
    t_start = int(row['year_announced'])
    t_end = t_start + int(row['duration'])
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            'project_id': idx, 'year_calendar': t,
            'event_any_yr': int((t == t_end) and (row['event_any'] == 1)),
            'is_blue_ccs': int(row['is_blue_ccs']),
        })
panel = pd.DataFrame(panel_rows)
panel = panel[(panel['year_calendar'] >= 2010) & (panel['year_calendar'] <= 2026)].copy()

# Merge EUA
mp = pd.read_csv(MASTER_PANEL_MONTHLY)
mp['date'] = pd.to_datetime(mp['date'])
mp['year_calendar'] = mp['date'].dt.year
yearly_eua = mp.groupby('year_calendar')['eua'].mean().reset_index()
panel = panel.merge(yearly_eua, on='year_calendar', how='left')
panel['mkt_eua'] = panel['eua'].fillna(panel['eua'].median())
panel['block'] = panel['year_calendar'].apply(year_to_block).astype(int)

print("=" * 70)
print("DIAGNOSTIC 1: EUA variantie per block (Hypothese B - identificatie)")
print("=" * 70)
print()
diag1 = panel.groupby('block').agg(
    n_obs=('event_any_yr', 'size'),
    n_events=('event_any_yr', 'sum'),
    n_unique_years=('year_calendar', 'nunique'),
    eua_min=('mkt_eua', 'min'),
    eua_max=('mkt_eua', 'max'),
    eua_mean=('mkt_eua', 'mean'),
    eua_sd=('mkt_eua', 'std'),
).round(2)
diag1.insert(0, 'period', BLOCK_NAMES)
print(diag1.to_string())

print()
print("INTERPRETATIE Diagnostic 1:")
print("  Block 0: 10 jaren, EUA spread groot - β_int well-identified")
print("  Block 1:  3 jaren, EUA spread groot (corona-piek) - identified")
print("  Block 2:  2 jaren, EUA spread? - cruciaal voor Hypothese B")
print("  Block 3:  2 jaren, EUA spread klein - β_int poorly identified")

print("\n" + "=" * 70)
print("DIAGNOSTIC 2: Events per (year × tech) cel per block")
print("=" * 70)
print()
diag2 = panel.groupby(['block','year_calendar','is_blue_ccs'])['event_any_yr'].sum().unstack(fill_value=0)
diag2.columns = ['PEM', 'Blue_CCS']
diag2['Block_label'] = [BLOCK_NAMES[b] for b, _ in diag2.index]
print(diag2.to_string())

# Identification specifiek voor block 2
print("\n" + "=" * 70)
print("DIAGNOSTIC 3: Block 2 deep-dive — events per year × tech × EUA")
print("=" * 70)
print()
b2 = panel[panel['block'] == 2].copy()
b2_summary = b2.groupby(['year_calendar', 'is_blue_ccs']).agg(
    n_at_risk=('event_any_yr', 'size'),
    n_events=('event_any_yr', 'sum'),
    eua=('mkt_eua', 'first'),
).reset_index()
b2_summary['tech'] = b2_summary['is_blue_ccs'].map({0:'PEM', 1:'Blue_CCS'})
b2_summary['hazard_rate'] = b2_summary['n_events'] / b2_summary['n_at_risk']
print(b2_summary[['year_calendar','tech','n_at_risk','n_events','eua','hazard_rate']].round(3).to_string(index=False))

# Korte analyse: hoeveel EUA-variatie is er binnen block 2?
b2_eua_unique = sorted(b2['mkt_eua'].unique())
print(f"\nBlock 2 EUA-waarden: {b2_eua_unique}")
print(f"Block 2 EUA range: [{min(b2_eua_unique):.1f}, {max(b2_eua_unique):.1f}]")
print(f"Block 2 EUA spread relatief: {(max(b2_eua_unique)-min(b2_eua_unique))/min(b2_eua_unique)*100:.0f}%")

# Hazard ratio per year IN block 2
print("\nImplied hazard ratio Blue/PEM per year in Block 2:")
for year in sorted(b2['year_calendar'].unique()):
    yr = b2[b2['year_calendar']==year]
    blue_haz = yr[yr['is_blue_ccs']==1]['event_any_yr'].mean()
    pem_haz = yr[yr['is_blue_ccs']==0]['event_any_yr'].mean()
    if pem_haz > 0:
        hr = blue_haz / pem_haz
        print(f"  {year}: Blue_haz = {blue_haz:.4f}, PEM_haz = {pem_haz:.4f}, HR = {hr:.2f}")
    else:
        print(f"  {year}: Blue_haz = {blue_haz:.4f}, PEM_haz = 0 (geen PEM events)")

# Plot
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Plot 1: EUA range per block
diag1.reset_index().plot.bar(x='block', y='eua_sd', ax=axes[0], color='#4477AA', legend=False)
axes[0].set_xticklabels([n.split(' ',1)[0] for n in BLOCK_NAMES], rotation=0)
axes[0].set_ylabel("EUA SD within block")
axes[0].set_title("Diagnostic 1: EUA-variantie per regime")
axes[0].grid(alpha=0.3, axis='y')

# Plot 2: Events per block
ev_data = diag2[['PEM', 'Blue_CCS']].reset_index()
year_block = ev_data.groupby('block').sum(numeric_only=True)
year_block.plot.bar(ax=axes[1], stacked=False, color=['#EE6677', '#4477AA'])
axes[1].set_xticklabels([n.split(' ',1)[0] for n in BLOCK_NAMES], rotation=0)
axes[1].set_ylabel("Events count")
axes[1].set_title("Diagnostic 2: Events per regime, gesplitst per technologie")
axes[1].grid(alpha=0.3, axis='y')
axes[1].legend(loc='upper left')

plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figures/block_diagnostics.pdf")
print(f"\nFiguur opgeslagen: figures/block_diagnostics.pdf")

# Conclusie
print("\n" + "=" * 70)
print("CONCLUSIE OVER HYPOTHESE B (identificatie-artefact?)")
print("=" * 70)
b2_sd = diag1.loc[2, 'eua_sd']
b0_sd = diag1.loc[0, 'eua_sd']
b1_sd = diag1.loc[1, 'eua_sd']
print(f"Block 0 EUA SD: {b0_sd}")
print(f"Block 1 EUA SD: {b1_sd}")
print(f"Block 2 EUA SD: {b2_sd}")
if b2_sd < min(b0_sd, b1_sd) * 0.5:
    print("=> Block 2 EUA-variantie is SUBSTANTIEEL lager dan andere blocks.")
    print("   STERKE INDICATIE voor Hypothese B (identificatie-artefact).")
    print("   β_int_block[2] is mogelijk wel negatief maar slecht geschat.")
elif b2_sd < min(b0_sd, b1_sd):
    print("=> Block 2 EUA-variantie is lager, mogelijk identification issue.")
    print("   Verdere robustness check nodig.")
else:
    print("=> Block 2 EUA-variantie is voldoende.")
    print("   Het null-resultaat is waarschijnlijk een ECHT economisch signaal.")
    print("   Hypothese A, C, of D zijn waarschijnlijker dan B.")
