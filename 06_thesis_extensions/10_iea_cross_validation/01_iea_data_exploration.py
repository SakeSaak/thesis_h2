"""
01_iea_data_exploration.py — Eerst grondig de IEA data verkennen.

Doelen:
1. Status verdelingen begrijpen
2. End-use multi-checkbox structuur in kaart brengen
3. Bepalen wat de meest valide 'event' definitie is voor IEA
4. Cross-tabulate met S&P verwachte patronen
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 200)

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/10_iea_cross_validation")


def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD IEA met multi-level header
# ============================================================================
hdr("Load IEA Production Projects Database (Sep 2025 + Feb 2026 corr.)")

iea = pd.read_excel(
    '/Users/sakesaakstra/Downloads/Hydrogen Production Projects Database - September 2025_correction_Feb26.xlsx',
    sheet_name='Projects', header=[0,1])

# Flatten kolommen
new_cols = []
for c in iea.columns:
    lvl0, lvl1 = c
    if 'Unnamed' in str(lvl1) or pd.isna(lvl1) or lvl1 == '':
        new_cols.append(str(lvl0).split('\n')[0].strip())
    else:
        new_cols.append(f"{lvl0}_{lvl1}")
iea.columns = new_cols
iea = iea.iloc[1:].reset_index(drop=True)
print(f"IEA shape: {iea.shape}")

# Geographic info
iea['country'] = iea['Country'].astype(str)

# Parse dates
iea['date_online'] = pd.to_datetime(iea['Date online'], errors='coerce')
iea['decom_year'] = pd.to_numeric(iea['Decomission date'], errors='coerce')
iea['year_online'] = iea['date_online'].dt.year

# Numeric capacity
iea['capacity_mw'] = pd.to_numeric(iea['Normalised capacity_MWel'], errors='coerce')
iea['capacity_kty'] = pd.to_numeric(iea['Normalised capacity_kt H2/y'], errors='coerce')
iea['log_capacity_mw'] = np.log1p(iea['capacity_mw'].fillna(iea['capacity_mw'].median()))

# Technology classification
def iea_tech_class(t):
    if pd.isna(t): return 'Unknown'
    t = str(t).strip().upper()
    if 'CCS' in t or 'CCUS' in t or 'SMR' in t or 'ATR' in t or 'COAL' in t:
        return 'Blue_CCS'
    if t in ['PEM','ALKALINE','SOEC','AEM']:
        return 'Electrolysis'
    return 'Other'
iea['tech_class'] = iea['Technology'].apply(iea_tech_class)
iea['is_blue'] = (iea['tech_class']=='Blue_CCS').astype(int)
iea['is_electro'] = (iea['tech_class']=='Electrolysis').astype(int)

print(f"\nTech classificatie (IEA):")
print(iea.groupby(['Technology','tech_class']).size().head(20))

# Region — IEA gebruikt ISO-3 codes
# EU-27 ISO-3 codes
EU27_ISO = {'AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC',
             'HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK',
             'SVN','ESP','SWE'}
iea['region_EU27'] = iea['country'].apply(lambda x: int(str(x).strip() in EU27_ISO))
print(f"\nGeographic distribution:")
print(f"  EU-27 projecten:    {iea['region_EU27'].sum()}")
print(f"  Niet-EU:             {(1-iea['region_EU27']).sum()}")

print(f"\nTop 15 landen:")
print(iea['country'].value_counts().head(15))


# ============================================================================
# 2. STATUS DEEP DIVE
# ============================================================================
hdr("Status verdeling + alternatieve event definities")

print("Status verdeling:")
print(iea['Status'].value_counts(dropna=False))

# Hoeveel projecten hebben Decomission date?
print(f"\nProjecten met Decomission date ingevuld: {iea['decom_year'].notna().sum()}")
print(f"Decomission date verdeling (jaren):")
print(iea['decom_year'].value_counts(dropna=False).sort_index().head(20))

# Statuses combineren met decomission date
print(f"\nStatus × heeft Decomission date:")
print(pd.crosstab(iea['Status'], iea['decom_year'].notna(), dropna=False))

# Year announced — IEA heeft alleen Date online voor operationele projecten
# Voor non-operational projecten gebruiken we de eerste reference jaar
# Quick proxy: gebruik year_online voor operationele; voor anderen schat via Decomission date

# Hoe te bepalen "announce year" voor non-operational projecten in IEA?
# IEA heeft geen Year announced kolom. We moeten dit uit referenties halen
# Of we gebruiken: voor planning projecten, default = 2020 (IEA includes since 2020 mostly)
print(f"\nIEA heeft GEEN 'Year announced' kolom! We moeten een proxy gebruiken.")
print(f"Date online (alleen voor operationeel): {iea['year_online'].value_counts().sort_index().head(15)}")

# Status × year_online
print(f"\nStatus × year_online range:")
print(iea.groupby('Status')['year_online'].agg(['count','min','max','median']).round(0))


# ============================================================================
# 3. END-USE MULTI-CHECKBOX VERKENNING
# ============================================================================
hdr("End-use multi-checkbox verdeling")

end_use_cols = [c for c in iea.columns if c.startswith('End use_')]
print(f"Aantal end-use kolommen: {len(end_use_cols)}")
print(f"\nProjecten per end-use:")
for c in end_use_cols:
    n = iea[c].notna().sum()
    label = c.replace('End use_','')
    print(f"  {label:30s}: {n:>4} ({100*n/len(iea):.1f}%)")

# CBAM-relevant end-uses (direct CBAM-covered or proximate)
CBAM_END_USES = ['End use_Refining', 'End use_Ammonia', 'End use_Methanol',
                  'End use_Iron&Steel']
ALSO_CBAM_PROXIMATE = ['End use_Other Ind']  # broader CBAM-adjacent

# Build CBAM exposure dummies
iea['cbam_endex_strict'] = iea[CBAM_END_USES].notna().any(axis=1).astype(int)
iea['cbam_endex_broad'] = iea[CBAM_END_USES + ALSO_CBAM_PROXIMATE].notna().any(axis=1).astype(int)

# Per CBAM end-use
print(f"\nProjecten in CBAM-covered end-uses (strict):")
print(f"  Refining:    {iea['End use_Refining'].notna().sum():>4}")
print(f"  Ammonia:     {iea['End use_Ammonia'].notna().sum():>4}")
print(f"  Methanol:    {iea['End use_Methanol'].notna().sum():>4}")
print(f"  Iron&Steel:  {iea['End use_Iron&Steel'].notna().sum():>4}")
print(f"  ─ ANY of above (cbam_strict): {iea['cbam_endex_strict'].sum()} ({100*iea['cbam_endex_strict'].mean():.1f}%)")
print(f"  + Other Ind: {iea['End use_Other Ind'].notna().sum():>4}")
print(f"  ─ ANY (cbam_broad):           {iea['cbam_endex_broad'].sum()} ({100*iea['cbam_endex_broad'].mean():.1f}%)")

# Multi-checkbox: projecten met MEERDERE end-uses
iea['n_end_uses'] = iea[end_use_cols].notna().sum(axis=1)
print(f"\nAantal end-uses per project:")
print(iea['n_end_uses'].value_counts().sort_index())


# ============================================================================
# 4. EVENT DEFINITION — wat is de meest valide 'cancellation' analoog in IEA?
# ============================================================================
hdr("Event definitie voor IEA — onze opties")

# Status verdeling reminder:
# Feasibility study   1014  → veel zijn gestald, mogelijk cancel
# Concept              733  → idem
# Operational          385  → success
# DEMO                 263  → klein, mostly success
# FID/Construction     218  → success path
# Decommisioned          9  → echte 'cancellations'
# Various                3

# Optie 1: Strict — alleen 'Decommisioned' (9 projecten — te weinig)
# Optie 2: 'Stalled' proxy — Feasibility/Concept BUT IEA Decomission date filled
# Optie 3: Decomission date filled (116 projecten - mix van retired operational + cancelled planned)
# Optie 4: Status in {Decommisioned, Feasibility study, Concept} BUT no progress (no date_online)

# Optie 3 nader bekijken
print("Optie 3: 'Decomission date filled' as event (n=116)")
filled = iea[iea['decom_year'].notna()].copy()
print(f"  Status verdeling onder deze 116:")
print(filled['Status'].value_counts())
print(f"\n  Decomission jaar:")
print(filled['decom_year'].value_counts().sort_index())

# Veel zijn 'Operational' projecten met Decomission date in verleden — niet wat we willen
# We willen alleen projecten die GECANCELD zijn vóór operationeel worden

# Optie 4 nader bekijken
print(f"\nOptie 4: niet-operational = (Status in [Decommisioned, Feasibility, Concept] AND no date_online)")
non_op = iea[(iea['Status'].isin(['Decommisioned','Feasibility study','Concept'])) &
              (iea['date_online'].isna())].copy()
print(f"  Sample size: {len(non_op):,}")
print(f"  Maar dit is te broad — Concept/Feasibility kan nog steeds 'on-going' zijn")

# Optie 5: Conservative — alleen Decommisioned + niet-operational projecten met Decomission date in toekomst
# Reality: IEA data is fundamenteel anders dan S&P. IEA tracks COMMISSIONED projects.
# IEA cancellations zijn impliciet in projecten die uit oudere versies verdwijnen — niet directly observable

# Maakt onze analyse-keus: Use cross-section analysis on END-USE patterns
# zonder cancellation outcome — kunnen we de relatie tussen end-use en project status testen
# Plus voor de 9 Decommisioned + 116 met decomission date: speciale analysis


# ============================================================================
# 5. BESLISSING: WAT TE DOEN MET IEA?
# ============================================================================
hdr("Strategische beslissing voor IEA cross-validation")

print("""
IEA database is fundamenteel ANDERS dan S&P voor onze CBAM-vraag:
  - IEA tracked geen 'planned project cancellations' systematisch
  - 'Decommisioned' (n=9) zijn historische operationele units die end-of-life kwamen
  - 'Feasibility study' / 'Concept' kunnen still active zijn, niet cancelled

IEA WEL gebruiken voor:
  1. CROSS-VALIDATION van CBAM end-use classificatie
     - IEA heeft multi-checkbox (Ammonia, Iron&Steel, etc.)
     - We kunnen onze S&P-derived CBAM-endex tegen IEA's classificatie verifiëren
  
  2. END-USE EXPOSURE TEST: P(non-Operational) ~ CBAM-endex
     - Treat 'Operational' as success
     - Treat 'Status NOT in [Operational, FID/Construction]' as 'stalled/failed'
     - Cross-check of de S&P-bevinding (-10.8pp marginal in full sample) replicates
  
  3. AUGMENT v7 sample met IEA end-use info (next step Pijler 3)
""")

# Save processed IEA voor verdere analyses
iea.to_csv(OUT / "iea_processed.csv", index=False)
print(f"Processed IEA saved: {OUT}/iea_processed.csv")
print(f"\nKolommen in processed file: {iea.shape[1]}")
