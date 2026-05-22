"""
TEST 2: Offtake-mechanism decomposition (μ vs σ vs η)

Question: Is the Blue-Green cancellation hazard differential heterogeneous
across end-use sectors that proxy for different operating channels?
- μ_proxy (chemical/refinery feedstock): fixed-price contracts → μ-channel dominant
- σ_proxy (power & heat, industry other): indexed pricing → σ-channel dominant
- η_proxy (transport, gas grid): multi-counterparty/coordination → η-channel dominant

If the Blue-Green gap is concentrated in σ_proxy and minimal in μ_proxy,
this is direct evidence that volatility (σ) is the dominant discriminating mechanism,
supporting Paper 3's σ-channel claim.

Conversely, if the gap is uniform across channels, the mechanism interpretation
is undermined and the offtake claim must be softened.
"""
from __future__ import annotations
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

warnings.filterwarnings('ignore')

# ----------------------------------------
# 1. LOAD DATA
# ----------------------------------------
SP_PATH = "../../../01_data/raw/Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUT_DIR = Path(".")

df = pd.read_excel(SP_PATH, sheet_name='Export')
print(f"S&P raw: {df.shape}")

# ----------------------------------------
# 2. TECH CLASSIFICATION (Blue / Green)
# ----------------------------------------
df['tech_class'] = 'Other'
df.loc[df['Technology2'] == 'Electrolysis', 'tech_class'] = 'Green'
df.loc[df['Technology2'] == 'Fossil with CCS', 'tech_class'] = 'Blue'

bg = df[df['tech_class'].isin(['Blue', 'Green'])].copy()
print(f"Blue + Green: {len(bg)}  (Blue: {(bg['tech_class']=='Blue').sum()}, Green: {(bg['tech_class']=='Green').sum()})")

# ----------------------------------------
# 3. EVENT DEFINITION
# Canonical thesis event set: cancelled, on-hold, decommissioned
# (matches the 367-event count in the master Cox PH analysis)
# ----------------------------------------
status = bg['project_status'].astype(str).str.lower()

bg['event_cancel'] = status.str.contains('cancel', na=False)
bg['event_onhold'] = status.str.contains('on-hold|on hold|paused', na=False)
bg['event_decom'] = status.str.contains('decommiss', na=False)
bg['event_any'] = (bg['event_cancel'] | bg['event_onhold'] | bg['event_decom']).astype(int)

print(f"\nEvent counts:")
print(f"  Cancelled: {bg['event_cancel'].sum()}")
print(f"  On-hold: {bg['event_onhold'].sum()}")
print(f"  Decommissioned: {bg['event_decom'].sum()}")
print(f"  Any failure event: {bg['event_any'].sum()}")

# ----------------------------------------
# 4. CHANNEL PROXY via primary end-use sector
# ----------------------------------------
def channel_proxy(sec):
    if pd.isna(sec) or sec == 'Unknown':
        return 'Unknown'
    s = str(sec).lower()
    if 'chemical feedstock' in s or 'refinery' in s:
        return 'mu_proxy'      # fixed-price contracts → μ-channel
    if 'power' in s or 'industry (other)' in s:
        return 'sigma_proxy'   # indexed pricing → σ-channel
    if 'transport' in s or 'gas grid' in s:
        return 'eta_proxy'     # multi-counterparty → η-channel
    return 'Other'

bg['channel_proxy'] = bg['Primary end use sector'].apply(channel_proxy)

# ----------------------------------------
# 5. OFFTAKE COMMITMENT
# ----------------------------------------
bg['has_offtake'] = bg['Offtaker'].notna()

# ----------------------------------------
# 6. DESCRIPTIVES
# ----------------------------------------
print("\n" + "="*70)
print("DESCRIPTIVES: events per channel × tech")
print("="*70)
desc = bg.groupby(['channel_proxy', 'tech_class']).agg(
    n=('Record ID', 'size'),
    n_event=('event_any', 'sum'),
).reset_index()
desc['event_rate'] = (desc['n_event'] / desc['n']).round(4)
desc['event_rate_pct'] = (desc['event_rate'] * 100).round(1).astype(str) + '%'
print(desc.to_string(index=False))

# Pivot to show Blue-Green gap by channel
pivot = desc.pivot_table(index='channel_proxy', columns='tech_class', values='event_rate', aggfunc='first').round(4)
pivot['Blue-Green_gap_pp'] = ((pivot['Blue'] - pivot['Green']) * 100).round(1)
print("\nBlue-Green event-rate gap (percentage points) per channel:")
print(pivot.to_string())

# ----------------------------------------
# 7. STRATIFIED LOGIT (interpretable, sample-size-robust)
# ----------------------------------------
print("\n" + "="*70)
print("LOGIT EVENT MODELS: Blue × channel interactions")
print("="*70)
try:
    import statsmodels.formula.api as smf
    bg['is_blue'] = (bg['tech_class'] == 'Blue').astype(int)
    bg['year_announced_num'] = pd.to_numeric(bg['Year announced'], errors='coerce')
    bg['log_cap'] = np.log(pd.to_numeric(bg['Output capacity per year'], errors='coerce').fillna(1) + 1)
    bg['has_capex'] = bg['Capex support'].notna().astype(int)

    # Filter to channels with sufficient data (drop Unknown/Other for clean interpretation)
    main_channels = bg[bg['channel_proxy'].isin(['mu_proxy', 'sigma_proxy', 'eta_proxy'])].copy()
    print(f"\nAnalysis sample: {len(main_channels)} projects, {main_channels['event_any'].sum()} events")

    # Pooled model with channel × Blue interaction
    formula = (
        "event_any ~ is_blue * C(channel_proxy, Treatment(reference='sigma_proxy')) "
        "+ log_cap + has_capex + C(Region major, Treatment(reference='North America')) "
        "+ year_announced_num"
    )
    m = smf.logit(formula, data=main_channels).fit(disp=False)
    print("\nLOGIT MODEL (pooled, with Blue × channel interaction):")
    print(m.summary2().tables[1].round(3))

    # Marginal effects per channel
    print("\n\nESTIMATED Blue-Green event-rate differential PER CHANNEL (marginal effect):")
    for ch in ['mu_proxy', 'sigma_proxy', 'eta_proxy']:
        sub = main_channels[main_channels['channel_proxy'] == ch].copy()
        if (sub['is_blue'].sum() < 5) or (sub['event_any'].sum() < 5):
            print(f"  {ch}: insufficient events (n_blue={sub['is_blue'].sum()}, events={sub['event_any'].sum()})")
            continue
        try:
            m_sub = smf.logit(
                "event_any ~ is_blue + log_cap + has_capex + C(Region major) + year_announced_num",
                data=sub
            ).fit(disp=False)
            coef = m_sub.params.get('is_blue', np.nan)
            pval = m_sub.pvalues.get('is_blue', np.nan)
            print(f"  {ch:12s}: Blue coef = {coef:+.3f}  p = {pval:.4f}  (events={sub['event_any'].sum()}, n_blue={sub['is_blue'].sum()})")
        except Exception as e:
            print(f"  {ch}: model failed — {e}")

    # Likelihood-ratio test for heterogeneity (interaction vs no interaction)
    m_no_int = smf.logit(
        "event_any ~ is_blue + C(channel_proxy, Treatment(reference='sigma_proxy')) "
        "+ log_cap + has_capex + C(Region major) + year_announced_num",
        data=main_channels
    ).fit(disp=False)
    lr_stat = 2 * (m.llf - m_no_int.llf)
    from scipy.stats import chi2
    df_diff = m.df_model - m_no_int.df_model
    lr_p = 1 - chi2.cdf(lr_stat, df_diff)
    print(f"\nLR test of Blue × channel heterogeneity:")
    print(f"  LR stat = {lr_stat:.3f}, df = {df_diff}, p = {lr_p:.4f}")
    print(f"  → {'REJECT homogeneity' if lr_p < 0.10 else 'CANNOT reject homogeneity'} at p<0.10")

except ImportError as e:
    print(f"Required package missing: {e}")
except Exception as e:
    print(f"Model failed: {e}")
    import traceback
    traceback.print_exc()

# ----------------------------------------
# 8. SAVE RESULTS
# ----------------------------------------
desc.to_csv(OUT_DIR / "event_rates_by_channel_tech.csv", index=False)
pivot.to_csv(OUT_DIR / "blue_green_gap_by_channel.csv")
bg[['Record ID', 'tech_class', 'channel_proxy', 'has_offtake', 'event_any', 'event_cancel', 'event_onhold', 'event_decom', 'Year announced', 'Region major', 'Primary end use sector']].to_csv(
    OUT_DIR / "test2_analysis_sample.csv", index=False
)
print(f"\n\nResults written to: {OUT_DIR.absolute()}")
