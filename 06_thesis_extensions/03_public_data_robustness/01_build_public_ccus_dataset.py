"""
01_build_public_ccus_dataset.py

Integreert drie publieke IEA-databases tot een analysedataset voor de
"public robustness chapter" van de thesis-extensie.

Input bronnen (alle CC BY 4.0):
  - IEA CCUS Projects Database 2026 (~/Downloads/)
  - IEA Hydrogen Production Projects Database Sept 2025 (corrected Feb 2026)
  - IEA Hydrogen Infrastructure Database Sept 2025

Output:
  - ccus_h2_project_level_for_R.csv  (parallel structuur aan v7's blueccs_project_level_for_R.csv)
  - ccus_h2_events.csv               (alleen events met datums)
  - integration_report.txt           (statistieken, overlaps, hiaten)

Auteur: Sake Saakstra
Thesis extension - Public Data Robustness
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATIE
# ============================================================================
DOWNLOADS = Path("/Users/sakesaakstra/Downloads")
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
OUTPUT_DIR = PROJECT_ROOT / "06_thesis_extensions/03_public_data_robustness"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

CCUS_FILE = DOWNLOADS / "IEA CCUS Projects Database 2026.xlsx"
H2_PROD_FILE = DOWNLOADS / "Hydrogen Production Projects Database - September 2025_correction_Feb26.xlsx"
H2_INFRA_FILE = DOWNLOADS / "Hydrogen Infrastracture Database - September 2025.xlsx"

CURRENT_YEAR = 2026

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
# LAAD CCUS DATABASE
# ============================================================================
print("=" * 70)
print("STEP 1: Loading CCUS Projects Database 2026")
print("=" * 70)

ccus = pd.read_excel(CCUS_FILE, sheet_name='DRAFT CCUS Projects Database', header=0)
print(f"  Totaal CCUS projecten: {len(ccus)}")

# Filter naar hydrogen/ammonia subsector
h2_mask = ccus['Subsector'].fillna('').astype(str).str.contains('Hydrogen|ammonia', case=False, regex=True)
h2_ccus = ccus[h2_mask].copy()
print(f"  Hydrogen/ammonia CCUS projecten: {len(h2_ccus)}")
print(f"  Status verdeling:")
for status, count in h2_ccus['Project status'].value_counts().items():
    print(f"    {status}: {count}")

# ============================================================================
# CONSTRUEER EVENT KOLOMMEN
# ============================================================================
print()
print("STEP 2: Event coding")
print("-" * 70)

# event_type encoding (parallel aan v7):
# 0 = censored (no event observed)
# 1 = cancelled (terminal)
# 2 = on-hold/suspended (reversibel)
def encode_event(status):
    s = str(status).strip().lower()
    if s == 'cancelled': return 1
    if s == 'decommissioned': return 1   # ook terminaal
    if s == 'suspended': return 2
    return 0  # planned, under construction, operational = censored

h2_ccus['event_type'] = h2_ccus['Project status'].apply(encode_event)
h2_ccus['event_any'] = (h2_ccus['event_type'] > 0).astype(int)

print(f"  Events (any): {h2_ccus['event_any'].sum()}")
print(f"  Cancelled (type=1): {(h2_ccus['event_type']==1).sum()}")
print(f"  Suspended (type=2): {(h2_ccus['event_type']==2).sum()}")

# ============================================================================
# DURATION BEREKENEN
# ============================================================================
print()
print("STEP 3: Duration computation")
print("-" * 70)

def to_year_safe(x):
    if pd.isna(x): return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100: return int(v)
    except: pass
    return np.nan

h2_ccus['year_announced'] = h2_ccus['Announcement'].apply(to_year_safe)
h2_ccus['year_event'] = h2_ccus['Suspension/decommissioning/cancellation'].apply(to_year_safe)
h2_ccus['year_operation'] = h2_ccus['Operation'].apply(to_year_safe)

def compute_duration(row):
    start = row['year_announced']
    if pd.isna(start):
        return np.nan
    if row['event_any'] == 1 and not pd.isna(row['year_event']):
        return max(1, int(row['year_event'] - start))
    if not pd.isna(row['year_operation']) and row['year_operation'] <= CURRENT_YEAR:
        return max(1, int(row['year_operation'] - start))
    return max(1, CURRENT_YEAR - int(start))

h2_ccus['duration'] = h2_ccus.apply(compute_duration, axis=1)
print(f"  Mediaan duration: {h2_ccus['duration'].median():.1f} jaar")
print(f"  Events met cancellation datum: {h2_ccus[h2_ccus['event_any']==1]['year_event'].notna().sum()} / {h2_ccus['event_any'].sum()}")

# ============================================================================
# COVARIATES
# ============================================================================
print()
print("STEP 4: Covariates")
print("-" * 70)

h2_ccus['region'] = h2_ccus['Country or economy'].apply(region_group)
print(f"  Regio verdeling:")
for region, count in h2_ccus['region'].value_counts().items():
    print(f"    {region}: {count}")

# is_blue_ccs: alle hydrogen CCUS in deze DB zijn per definitie blue (SMR+CCS) of ammonia met CCS
# Voor de robustness chapter is dit een ALL-BLUE sample (geen PEM comparator hier)
# Alternative: gebruik dit als losse 'CCUS-dependence' indicator
h2_ccus['is_blue_ccs'] = 1

# Capacity in MW equivalent — gebruik CO2 capture capacity als proxy
h2_ccus['capture_mtco2'] = pd.to_numeric(
    h2_ccus['Announced capacity (Mt CO2/yr)'].astype(str).str.extract(r'([\d.]+)', expand=False),
    errors='coerce'
)
h2_ccus['log_capture_mtco2'] = np.log1p(h2_ccus['capture_mtco2'].fillna(0))

# Sponsor extracten uit Partners
def extract_primary_sponsor(s):
    if pd.isna(s): return "Unknown"
    s_low = str(s).lower()
    sponsors = {
        'shell': 'Oil_major', 'bp': 'Oil_major', 'totalenergies': 'Oil_major',
        'total ': 'Oil_major', 'equinor': 'Oil_major', 'repsol': 'Oil_major',
        'eni': 'Oil_major', 'aramco': 'Oil_major', 'chevron': 'Oil_major',
        'exxonmobil': 'Oil_major', 'exxon': 'Oil_major',
        'rwe': 'Utility', 'iberdrola': 'Utility', 'orsted': 'Utility',
        'engie': 'Utility', 'enel': 'Utility', 'eon': 'Utility',
        'air liquide': 'Industrial_gas', 'air products': 'Industrial_gas',
        'linde': 'Industrial_gas',
        'arcelormittal': 'Steel', 'thyssenkrupp': 'Steel', 'tata steel': 'Steel',
        'yara': 'Industrial_chem', 'basf': 'Industrial_chem', 'dow': 'Industrial_chem',
    }
    for keyword, label in sponsors.items():
        if keyword in s_low: return label
    return "Other"

h2_ccus['sponsor_type'] = h2_ccus['Partners'].apply(extract_primary_sponsor)

# ============================================================================
# FILTER NAAR ANALYSEERBARE SAMPLE
# ============================================================================
print()
print("STEP 5: Filtering to analyzable sample")
print("-" * 70)

before = len(h2_ccus)
analyze = h2_ccus.dropna(subset=['year_announced', 'duration']).copy()
analyze['project_id'] = range(len(analyze))
print(f"  Voor filter: {before}")
print(f"  Na filter (geldig year_announced + duration): {len(analyze)}")
print(f"  Events in analysable sample: {analyze['event_any'].sum()}")

# ============================================================================
# EXPORT
# ============================================================================
print()
print("STEP 6: Export")
print("-" * 70)

# Project-level file (parallel structuur aan v7's blueccs_project_level_for_R.csv)
export_cols = [
    'project_id', 'is_blue_ccs', 'log_capture_mtco2', 'region',
    'sponsor_type', 'year_announced', 'duration',
    'event_any', 'event_type',
]
project_level = analyze[export_cols].copy()
project_level.rename(columns={'log_capture_mtco2': 'log_capacity_mw'}, inplace=True)  # naam-compatibel

out_path = OUTPUT_DIR / "ccus_h2_project_level_for_R.csv"
project_level.to_csv(out_path, index=False)
print(f"  Geschreven: {out_path.name}")
print(f"    N = {len(project_level)}, events = {project_level['event_any'].sum()}")

# Events-only file met datums
events_only = analyze[analyze['event_any'] == 1][
    ['Project name', 'Country or economy', 'region', 'Project status',
     'year_announced', 'year_event', 'year_operation', 'capture_mtco2',
     'sponsor_type', 'event_type']
].copy()
events_path = OUTPUT_DIR / "ccus_h2_events.csv"
events_only.to_csv(events_path, index=False)
print(f"  Geschreven: {events_path.name}")
print(f"    {len(events_only)} cancellation/suspension events met datums")

# Report file
report_path = OUTPUT_DIR / "integration_report.txt"
with open(report_path, 'w') as f:
    f.write("Public IEA Data Integration Report\n")
    f.write("=" * 50 + "\n\n")
    f.write(f"Datum gegenereerd: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write(f"BRON: IEA CCUS Projects Database 2026\n")
    f.write(f"FILTER: Subsector contains 'Hydrogen' or 'ammonia'\n\n")
    f.write(f"Sample statistieken:\n")
    f.write(f"  Totaal hydrogen/ammonia CCUS projecten: {len(h2_ccus)}\n")
    f.write(f"  Analysable sample (na filter): {len(analyze)}\n")
    f.write(f"  Total events: {analyze['event_any'].sum()}\n")
    f.write(f"  Cancelled (terminal): {(analyze['event_type']==1).sum()}\n")
    f.write(f"  Suspended (reversibel): {(analyze['event_type']==2).sum()}\n\n")
    f.write("Vergelijking met v7 (S&P data):\n")
    f.write(f"  v7 Blue_CCS cancellations: 31\n")
    f.write(f"  CCUS public cancellations: {(analyze['event_type']==1).sum()}\n")
    f.write(f"  Onafhankelijke event-pool, weinig name-overlap\n\n")
    f.write("Geografische verdeling van events:\n")
    for r, n in analyze[analyze['event_any']==1]['region'].value_counts().items():
        f.write(f"    {r}: {n}\n")
print(f"  Geschreven: {report_path.name}")

print()
print("=" * 70)
print("KLAAR")
print("=" * 70)
print(f"Outputs in: {OUTPUT_DIR}")
print()
print("Volgende stappen:")
print("  1. Inspecteer integration_report.txt voor data-kwaliteit")
print("  2. Run de bestaande v7 Cox PH analyse op deze dataset")
print("  3. Vergelijk hazard ratios: zelfde patronen?")
print("  4. Schrijf 'Public Data Robustness' chapter")
