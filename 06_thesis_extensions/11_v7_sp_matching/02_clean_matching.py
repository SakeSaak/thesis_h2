"""
02_clean_matching.py — Cleane v7 ↔ S&P (oud 24-03-26) matching implementatie.

Strategie:
  1. Load beide samples + parse capacity uit beide naar gemeenschappelijke schaal
  2. Build match key: (year, region, blue_flag, capacity_bucket)
  3. Voor elke v7 project, vind beste matching S&P Record ID via blok-NN
  4. Append S&P end-use info aan v7
  5. Run hazard model met juiste end-use exposure (vs eerder sponsor proxy)
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
pd.set_option('display.max_columns', 30)
pd.set_option('display.width', 200)

OUT = Path("/Users/sakesaakstra/Desktop/thesis_h2/06_thesis_extensions/11_v7_sp_matching")
(OUT / "results").mkdir(parents=True, exist_ok=True)


def hdr(t): print("\n" + "=" * 80 + f"\n{t}\n" + "=" * 80)


# ============================================================================
# 1. LOAD + CLEAN
# ============================================================================
hdr("Step 1: Load + clean beide samples")

v7 = pd.read_csv('/Users/sakesaakstra/Desktop/thesis_h2/01_data/intermediate/blueccs_project_level_for_R.csv')
v7['capacity_mw'] = np.expm1(v7['log_capacity_mw'])
print(f"v7: {len(v7):,} projecten, {v7['is_blue_ccs'].sum()} Blue + {(v7['is_blue_ccs']==0).sum()} PEM")

sp = pd.read_excel('/Users/sakesaakstra/Desktop/thesis_h2/01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx')
sp['year_announced'] = pd.to_numeric(sp['Year announced'], errors='coerce')
sp['capacity_kty'] = pd.to_numeric(sp['Calculated hydrogen production per year'], errors='coerce')
sp['capacity_mw'] = sp['capacity_kty']  # 1 kt/y H2 ≈ 1 MW electrolyzer (rough)

# Filter naar zelfde tech als v7
sp_eligible = sp[
    sp['Technology2'].isin(['Fossil with CCS','Electrolysis']) &
    sp['year_announced'].between(2010, 2025)
].copy()
sp_eligible['is_blue'] = (sp_eligible['Technology2']=='Fossil with CCS').astype(int)
print(f"S&P eligible: {len(sp_eligible):,} ({sp_eligible['is_blue'].sum()} Blue + {(sp_eligible['is_blue']==0).sum()} Electrolysis)")
print(f"  v7 wants: {v7['is_blue_ccs'].sum()} Blue + {(v7['is_blue_ccs']==0).sum()} PEM")
print(f"  Ratio match-able: Blue {v7['is_blue_ccs'].sum()}/{sp_eligible['is_blue'].sum()} = {v7['is_blue_ccs'].sum()/sp_eligible['is_blue'].sum()*100:.0f}%")


# ============================================================================
# 2. BUILD MATCH KEYS
# ============================================================================
hdr("Step 2: Match keys (year × region × blue × capacity-bucket)")

# v7 region map
v7_region_to_short = {
    'EU':'EU','Other_Europe':'OE','North_America':'NA','Asia_Pacific':'AP','Other':'OT'
}
v7['region_short'] = v7['region'].map(v7_region_to_short).fillna('UNK')

# S&P region map
def sp_reg(r):
    return {'Europe (EU-27)':'EU','Europe (non EU-27)':'OE','North America':'NA',
            'Asia-Pacific':'AP'}.get(str(r).strip(), 'OT')
sp_eligible['region_short'] = sp_eligible['Region major'].apply(sp_reg)

# Capacity bucket
def cap_bucket(c):
    if pd.isna(c) or c < 0.1: return 'XS'
    if c < 1: return 'S'
    if c < 10: return 'M'
    if c < 100: return 'L'
    if c < 1000: return 'XL'
    return 'XXL'

v7['cap_bkt'] = v7['capacity_mw'].apply(cap_bucket)
sp_eligible['cap_bkt'] = sp_eligible['capacity_mw'].apply(cap_bucket)

# Match key
v7['key'] = (v7['year_announced'].astype(int).astype(str) + '_' +
              v7['region_short'] + '_' + v7['is_blue_ccs'].astype(str) + '_' + v7['cap_bkt'])
sp_eligible['key'] = (sp_eligible['year_announced'].astype(int).astype(str) + '_' +
                       sp_eligible['region_short'] + '_' + sp_eligible['is_blue'].astype(str) + '_' + sp_eligible['cap_bkt'])

print(f"v7 unique keys: {v7['key'].nunique()}")
print(f"S&P unique keys: {sp_eligible['key'].nunique()}")
print(f"Overlap keys: {len(set(v7['key']) & set(sp_eligible['key']))}")


# ============================================================================
# 3. BLOCKED NEAREST-NEIGHBOR MATCHING
# ============================================================================
hdr("Step 3: Blocked matching algorithm")

matches = []
for key, v7_grp in v7.groupby('key'):
    sp_grp = sp_eligible[sp_eligible['key']==key].copy()
    
    if len(sp_grp) == 0:
        # Geen exacte match — relax capacity bucket (drop last segment)
        relaxed = '_'.join(key.split('_')[:3])
        sp_grp = sp_eligible[sp_eligible['key'].str.startswith(relaxed + '_')].copy()
        match_q = 'relaxed' if len(sp_grp) > 0 else 'no_match'
    else:
        match_q = 'exact'
    
    if len(sp_grp) == 0:
        # Still no match - log
        for _, vrow in v7_grp.iterrows():
            matches.append({
                'v7_project_id': int(vrow['project_id']),
                'sp_record_id': None,
                'match_quality': 'no_match',
                'cap_diff': np.nan,
            })
        continue
    
    # Nearest-neighbor op log(capacity)
    available_sp_idx = sp_grp.index.tolist()
    
    for _, vrow in v7_grp.iterrows():
        if len(available_sp_idx) == 0:
            matches.append({
                'v7_project_id': int(vrow['project_id']),
                'sp_record_id': None,
                'match_quality': match_q + '_exhausted',
                'cap_diff': np.nan,
            })
            continue
        
        v_cap = vrow['capacity_mw']
        best_sp_idx = None
        best_dist = np.inf
        
        for sp_idx in available_sp_idx:
            s_cap = sp_eligible.loc[sp_idx, 'capacity_mw']
            if pd.isna(s_cap): s_cap = 0
            d = abs(np.log1p(v_cap) - np.log1p(s_cap))
            if d < best_dist:
                best_dist = d
                best_sp_idx = sp_idx
        
        if best_sp_idx is not None:
            matches.append({
                'v7_project_id': int(vrow['project_id']),
                'sp_record_id': sp_eligible.loc[best_sp_idx, 'Record ID'],
                'sp_project_name': sp_eligible.loc[best_sp_idx, 'Project name'],
                'match_quality': match_q,
                'cap_diff': float(best_dist),
            })
            available_sp_idx.remove(best_sp_idx)

mapping = pd.DataFrame(matches)
print(f"Match results:")
print(mapping['match_quality'].value_counts())
n_matched = mapping['sp_record_id'].notna().sum()
print(f"\nMatch rate: {n_matched}/{len(v7)} = {100*n_matched/len(v7):.1f}%")


# ============================================================================
# 4. AUGMENT v7 MET S&P END-USE
# ============================================================================
hdr("Step 4: Augment v7 met S&P end-use info")

sp_endex = sp[['Record ID','Project name','Primary end use sector','Primary end use sector detail',
                'Secondary use sector','Output product','Will export','Export destination geography',
                'project_status','Project status major']].copy()

# CBAM endex
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
v7_aug = v7.merge(mapping[['v7_project_id','sp_record_id','match_quality']],
                    left_on='project_id', right_on='v7_project_id', how='left')
v7_aug = v7_aug.merge(sp_endex, left_on='sp_record_id', right_on='Record ID', how='left')

print(f"v7 augmented: shape={v7_aug.shape}")
n_with_endex = v7_aug['Primary end use sector'].notna().sum()
print(f"End-use info beschikbaar voor: {n_with_endex}/{len(v7_aug)} ({100*n_with_endex/len(v7_aug):.1f}%)")
print(f"CBAM-end-use exposed (mapped): {v7_aug['cbam_endex'].sum()} ({100*v7_aug['cbam_endex'].mean():.1f}%)")


# ============================================================================
# 5. CROSSTABULATIES voor verification
# ============================================================================
hdr("Step 5: Verification crosstabs")

print("End-use sector distributie in augmented v7 (waar mapped):")
print(v7_aug['Primary end use sector'].value_counts(dropna=False).head(10))

print(f"\nEnd-use detail (top 15):")
print(v7_aug['Primary end use sector detail'].value_counts(dropna=False).head(15))

# Compareer eerder sponsor-proxy met nu real end-use
print(f"\nVergelijking sponsor-proxy vs real end-use:")
v7_aug['sponsor_proxy_cbam'] = v7_aug['sponsor_type'].apply(
    lambda s: int(str(s).strip() in ['Oil_major','Industrial_gas','Steel']))
ct = pd.crosstab(v7_aug['sponsor_proxy_cbam'], v7_aug['cbam_endex'], dropna=False)
print(ct)

print(f"\nCancellation rate per CBAM-endex (augmented v7):")
v7_evt = v7_aug[v7_aug['Primary end use sector'].notna()]
if len(v7_evt) > 0:
    rates = v7_evt.groupby('cbam_endex')['event_any'].agg(['count','sum','mean'])
    rates['mean'] = (rates['mean']*100).round(1)
    rates.columns = ['n','events','cancel_rate_%']
    print(rates)


# ============================================================================
# 6. PROJECT-LEVEL HAZARD MODEL met REAL END-USE
# ============================================================================
hdr("Step 6: Hazard model met real S&P end-use (replicating Chapter 7 met juiste exposure)")

import statsmodels.api as sm

# Subset met end-use info
df = v7_aug[v7_aug['Primary end use sector'].notna()].copy()
print(f"Hazard model sample: {len(df)} projecten met end-use info, {df['event_any'].sum()} events")

# Basic logit
df['event_any'] = df['event_any'].astype(int)
df['cbam_endex'] = df['cbam_endex'].astype(int)
df['is_blue_ccs'] = df['is_blue_ccs'].astype(int)

# Model A: simple event ~ cbam_endex + blue + capacity
y = df['event_any']
X = sm.add_constant(df[['cbam_endex','is_blue_ccs','log_capacity_mw']])
try:
    m_a = sm.Logit(y, X).fit(disp=0, maxiter=200)
    print("\nModel A: event ~ CBAM-endex + Blue + log_cap")
    print(m_a.summary().tables[1])
except Exception as e:
    print(f"Fail: {e}")

# Model B: Interaction Blue × CBAM-endex
df['blue_cbam'] = df['is_blue_ccs'] * df['cbam_endex']
y = df['event_any']
X = sm.add_constant(df[['cbam_endex','is_blue_ccs','blue_cbam','log_capacity_mw','year_announced']])
try:
    m_b = sm.Logit(y, X).fit(disp=0, maxiter=200)
    print("\nModel B: event ~ CBAM-endex + Blue + Blue×CBAM-endex + log_cap + year")
    print(m_b.summary().tables[1])
    
    # Cross-tab effects
    print(f"\nCancellation rate per (Blue × CBAM-endex):")
    ct = df.groupby(['is_blue_ccs','cbam_endex']).agg(
        n=('project_id','count'),
        events=('event_any','sum'),
        rate=('event_any','mean'),
    )
    ct['rate'] = (ct['rate']*100).round(1)
    print(ct)
except Exception as e:
    print(f"Fail: {e}")


# Save augmented file
v7_aug.to_csv(OUT / "results/v7_augmented_with_sp_endex.csv", index=False)
mapping.to_csv(OUT / "results/v7_to_sp_mapping.csv", index=False)
print(f"\nResults saved in: {OUT}/results/")
