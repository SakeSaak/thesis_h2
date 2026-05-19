"""
01_reconstruct_v7.py — Reconstruct v7 sample uit raw S&P data 24-03-26.

Hypothese: v7 sample (714 projecten) = subset van Hydrogen_projects_master_data_table_24-03-26.xlsx
(3,249 projecten) gefilterd op:
  - Technology: Blue CCS (Fossil with CCS) OF PEM (Electrolysis)
  - Period: 2010-2025 announced
  - Status: alle (incl. planning, operational, cancelled)

Doel: vind voor elke v7 project_id de matching S&P Record ID, zodat we
end-use info kunnen toevoegen.
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 250)

V7_PATH = Path("/Users/sakesaakstra/Desktop/thesis_h2/01_data/intermediate/blueccs_project_level_for_R.csv")
SP_OLD_PATH = Path("/Users/sakesaakstra/Desktop/thesis_h2/01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx")
SP_NEW_PATH = Path("/Users/sakesaakstra/Downloads/Hydrogen projects master data table.xlsx")
OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/11_v7_sp_matching")


def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD beide samples
# ============================================================================
hdr("Load v7 + raw S&P 24-03-26")

v7 = pd.read_csv(V7_PATH)
print(f"v7: {len(v7):,} projecten")
print(f"v7 tech-classificatie:")
print(f"  is_blue_ccs=1: {(v7['is_blue_ccs']==1).sum()}")
print(f"  is_blue_ccs=0: {(v7['is_blue_ccs']==0).sum()}")
print(f"\nv7 'tech' distributie:")
print(v7['tech'].value_counts())

# Raw S&P 24-03-26
sp = pd.read_excel(SP_OLD_PATH)
print(f"\nRaw S&P 24-03-26: {len(sp):,} projecten")

# v7 vraagt is_blue_ccs flag — laten we de S&P Technology2 verdeling zien
print(f"\nS&P 24-03 Technology2 distributie:")
print(sp['Technology2'].value_counts(dropna=False).head(15))


# ============================================================================
# 2. RECONSTRUEER FILTER CRITERIA
# ============================================================================
hdr("Reconstrueer v7 filter criteria")

# Vermoedelijke filter: Fossil with CCS OF Electrolysis
sp_filtered = sp[sp['Technology2'].isin(['Fossil with CCS','Electrolysis'])].copy()
print(f"After 'Fossil with CCS OR Electrolysis': {len(sp_filtered):,}")

# v7 heeft year_announced 2010-2025. Filter S&P op deze range
sp['year_announced'] = pd.to_numeric(sp['Year announced'], errors='coerce')
sp_filtered = sp_filtered[
    (sp_filtered['Technology2'].isin(['Fossil with CCS','Electrolysis'])) &
    (pd.to_numeric(sp_filtered['Year announced'], errors='coerce').between(2010, 2025))
].copy()
print(f"After year filter 2010-2025: {len(sp_filtered):,}")

# v7 = 714. Mogelijke verdere filter:
# - Capacity > minimum drempel?
sp_filtered['capacity_mwel'] = pd.to_numeric(sp_filtered['Calculated hydrogen production per year'], errors='coerce')
sp_filtered['capacity_ty'] = pd.to_numeric(sp_filtered['Calculated hydrogen production per year'], errors='coerce')

print(f"\nCapacity (MWel) verdeling onder filter:")
print(sp_filtered['capacity_mwel'].describe())

# Test verschillende drempels
for thresh in [0, 0.1, 1, 5, 10]:
    n = (sp_filtered['capacity_mwel'] >= thresh).sum()
    n_na = sp_filtered['capacity_mwel'].isna().sum()
    print(f"  Capacity >= {thresh} MWel: n={n} (+ {n_na} NaN)")

# Misschien capaciteits-drempel + minder strict
# v7 heeft log_capacity_mw values; we kunnen die back-converten
v7['capacity_mw_implied'] = np.expm1(v7['log_capacity_mw'])
print(f"\nv7 capacity (MW) verdeling (back-converted):")
print(v7['capacity_mw_implied'].describe())


# ============================================================================
# 3. PROBEER MATCHING via STRUCTURELE KENMERKEN
# ============================================================================
hdr("Structural matching v7 ↔ raw S&P")

# Bouw match keys voor beide samples
def make_match_key(year, region, is_blue, capacity_mw):
    """Match key: (year, region_simple, blue_flag, capacity_bucket)"""
    yr = int(year) if pd.notna(year) else -1
    # Region simplification
    if pd.isna(region): reg = 'UNK'
    else:
        r = str(region).strip()
        if r == 'EU': reg = 'EU'
        elif r == 'Other_Europe': reg = 'OE'
        elif r == 'North_America': reg = 'NA'
        elif r == 'Asia_Pacific': reg = 'AP'
        else: reg = 'OT'
    bf = int(is_blue)
    if pd.isna(capacity_mw): cb = 'X'
    elif capacity_mw < 1: cb = 'S'
    elif capacity_mw < 10: cb = 'M'
    elif capacity_mw < 100: cb = 'L'
    elif capacity_mw < 1000: cb = 'XL'
    else: cb = 'XXL'
    return f"{yr}_{reg}_{bf}_{cb}"

# v7 match keys
v7['match_key'] = v7.apply(lambda r: make_match_key(
    r['year_announced'], r['region'], r['is_blue_ccs'], r['capacity_mw_implied']
), axis=1)

# S&P regio mapping
def sp_region_simple(r):
    if pd.isna(r): return 'UNK'
    rs = str(r).strip()
    return {
        'Europe (EU-27)': 'EU',
        'Europe (non EU-27)': 'OE',
        'North America': 'NA',
        'Asia-Pacific': 'AP',
        'Middle East': 'OT',
        'Africa': 'OT',
        'Latin America': 'OT',
    }.get(rs, 'UNK')

sp_filtered['region_simple'] = sp_filtered['Region major'].apply(sp_region_simple)
sp_filtered['is_blue_match'] = (sp_filtered['Technology2']=='Fossil with CCS').astype(int)
# capacity om te matchen: in MWel
sp_filtered['match_key'] = sp_filtered.apply(lambda r: make_match_key(
    r['year_announced'], 'EU' if r['region_simple']=='EU' else
    'Other_Europe' if r['region_simple']=='OE' else
    'North_America' if r['region_simple']=='NA' else
    'Asia_Pacific' if r['region_simple']=='AP' else 'Other',
    r['is_blue_match'], r['capacity_mwel']
), axis=1)

# Match keys distributie
v7_keys = v7['match_key'].value_counts()
sp_keys = sp_filtered['match_key'].value_counts()
print(f"\nMatch keys analyse:")
print(f"  v7 unique keys: {v7['match_key'].nunique()}")
print(f"  S&P unique keys: {sp_filtered['match_key'].nunique()}")
print(f"  Overlap keys: {len(set(v7['match_key']) & set(sp_filtered['match_key']))}")

# Per key: count v7 vs S&P projecten
key_stats = pd.DataFrame({'v7_count': v7_keys, 'sp_count': sp_keys}).fillna(0).astype(int)
key_stats['ratio_v7_in_sp'] = key_stats['v7_count'] / key_stats['sp_count'].replace(0, np.nan)
print(f"\nKey overlap top-15 (gesorteerd op v7 count):")
print(key_stats.sort_values('v7_count', ascending=False).head(15))


# ============================================================================
# 4. BLOCKED MATCHING: per (year × region × blue) one-to-many mapping
# ============================================================================
hdr("Blocked matching algorithm")

# Voor elke unieke (year, region, blue) combo, probeer projecten te koppelen
# Eenvoudigste benadering: capacity-based nearest neighbor binnen elk blok

matches = []
n_matched = 0
n_unmatched = 0

for key, v7_group in v7.groupby('match_key'):
    sp_group = sp_filtered[sp_filtered['match_key'] == key].copy()
    
    if len(sp_group) == 0:
        # Geen S&P projecten in dit blok — relax key (drop capacity bucket)
        # Parse key
        parts = key.split('_')
        if len(parts) >= 4:
            relaxed_key = '_'.join(parts[:3])  # year_region_blue, no capacity
            sp_group_relaxed = sp_filtered[
                sp_filtered['match_key'].str.startswith(relaxed_key + '_')
            ].copy()
            if len(sp_group_relaxed) == 0:
                # Volledig geen match
                for _, vrow in v7_group.iterrows():
                    matches.append({
                        'v7_project_id': vrow['project_id'],
                        'sp_record_id': None,
                        'match_quality': 'no_match',
                    })
                    n_unmatched += 1
                continue
            else:
                sp_group = sp_group_relaxed
                match_q = 'relaxed_no_capacity'
        else:
            for _, vrow in v7_group.iterrows():
                matches.append({
                    'v7_project_id': vrow['project_id'],
                    'sp_record_id': None,
                    'match_quality': 'no_match',
                })
                n_unmatched += 1
            continue
    else:
        match_q = 'exact_block'
    
    # Voor elke v7-project in dit blok, match capacity nearest neighbor
    v7_caps = v7_group['capacity_mw_implied'].values
    sp_caps = sp_group['capacity_mwel'].fillna(sp_group['capacity_mwel'].median()).values
    sp_ids = sp_group['Record ID'].values
    v7_ids = v7_group['project_id'].values
    
    # Hungarian-style: greedy matching op capacity gap
    used_sp_idx = set()
    for i, vid in enumerate(v7_ids):
        vcap = v7_caps[i]
        # Find best unused sp match
        best_idx = None
        best_dist = np.inf
        for j, scap in enumerate(sp_caps):
            if j in used_sp_idx: continue
            d = abs(np.log1p(vcap) - np.log1p(scap)) if scap > 0 else abs(np.log1p(vcap))
            if d < best_dist:
                best_dist = d
                best_idx = j
        if best_idx is not None:
            used_sp_idx.add(best_idx)
            matches.append({
                'v7_project_id': vid,
                'sp_record_id': sp_ids[best_idx],
                'match_quality': match_q,
                'capacity_dist': float(best_dist),
            })
            n_matched += 1
        else:
            matches.append({
                'v7_project_id': vid,
                'sp_record_id': None,
                'match_quality': 'sp_exhausted',
            })
            n_unmatched += 1

mapping_df = pd.DataFrame(matches)
print(f"\nMatching resultaat:")
print(f"  Total v7 projecten: {len(v7):,}")
print(f"  Gematched (exact block): {(mapping_df['match_quality']=='exact_block').sum()}")
print(f"  Gematched (relaxed): {(mapping_df['match_quality']=='relaxed_no_capacity').sum()}")
print(f"  Niet matched: {(mapping_df['match_quality']=='no_match').sum()}")
print(f"  Match rate: {100*(mapping_df['sp_record_id'].notna().sum())/len(v7):.1f}%")


# ============================================================================
# 5. EXPORTEER MAPPING + AUGMENT v7 MET S&P END-USE
# ============================================================================
hdr("Augment v7 met S&P end-use info")

# Voeg S&P end-use info toe via mapping
sp_endex = sp[['Record ID','Primary end use sector','Primary end use sector detail',
                'Secondary use sector','Output product','Will export',
                'Export destination geography']].copy()

# Functie voor CBAM endex
def cbam_endex(detail, sector):
    detail_low = str(detail).lower() if pd.notna(detail) else ''
    sector_low = str(sector).lower() if pd.notna(sector) else ''
    if any(k in detail_low for k in ['fertilizer','ammonia','steel','chemicals','refinery','cement']):
        return 1
    if 'chemical feedstock' in sector_low or 'refinery feedstock' in sector_low:
        return 1
    return 0
sp_endex['cbam_endex'] = sp_endex.apply(lambda r: cbam_endex(
    r['Primary end use sector detail'], r['Primary end use sector']), axis=1)

# Merge
v7_aug = v7.merge(mapping_df[['v7_project_id','sp_record_id','match_quality']],
                    left_on='project_id', right_on='v7_project_id', how='left')
v7_aug = v7_aug.merge(sp_endex, left_on='sp_record_id', right_on='Record ID', how='left')

print(f"v7 augmented: {v7_aug.shape}")
print(f"\nEnd-use info beschikbaar voor: {v7_aug['Primary end use sector'].notna().sum()}/{len(v7_aug)}")
print(f"CBAM-end-use exposed (uit S&P merge): {v7_aug['cbam_endex'].sum()} ({100*v7_aug['cbam_endex'].mean():.1f}%)")

# Save augmented v7
v7_aug.to_csv(OUT / "results/v7_augmented_with_sp.csv", index=False)
mapping_df.to_csv(OUT / "results/v7_to_sp_mapping.csv", index=False)
print(f"\nFiles saved:")
print(f"  {OUT}/results/v7_augmented_with_sp.csv")
print(f"  {OUT}/results/v7_to_sp_mapping.csv")


# ============================================================================
# 6. SUBSTANTIVE: HOE VERDEELT CBAM-ENDEX ZICH IN v7?
# ============================================================================
hdr("v7 distributie van CBAM-endex (na S&P augmentation)")

print("\nv7 met end-use info — per technology:")
v7_with_endex = v7_aug[v7_aug['Primary end use sector'].notna()].copy()
print(f"Sub-sample with end-use: {len(v7_with_endex):,}")

if len(v7_with_endex) > 50:
    # CBAM exposure × tech × event
    grouped = v7_with_endex.groupby(['is_blue_ccs','cbam_endex']).agg(
        n=('project_id','count'),
        events=('event_any','sum'),
        event_rate=('event_any','mean'),
    ).reset_index()
    grouped['event_rate_pct'] = (grouped['event_rate']*100).round(1)
    print(grouped)
    
    print(f"\nGlobal CBAM exposure × cancellation rate (v7 augmented):")
    cbam_ex_rate = v7_with_endex.groupby('cbam_endex')['event_any'].mean() * 100
    print(cbam_ex_rate.round(1))
    print(f"\nBlue × CBAM exposure crosstab (in v7 events alleen):")
    ev = v7_with_endex[v7_with_endex['event_any']==1]
    if len(ev) > 0:
        print(pd.crosstab(ev['is_blue_ccs'], ev['cbam_endex'], margins=True))
