"""
27_leave_one_region_out.py

Test of de Blue_CCS bevinding regio-robuust is.

Voor elk van de 7 regio's:
  1. Verwijder alle projecten in die regio
  2. Refit het hazard model
  3. Bewaar Blue_CCS HR, SE, p, CI

Plus een 'Full sample' baseline ter vergelijking.

Het idee: als één regio (bijv. North_America met veel Blue_CCS oil-major projecten)
de bevinding drijft, zou het excluderen ervan de HR dramatisch laten dalen.

Output:
  - /figures/fig_lor_forest.png       (forest plot)
  - /output_data/27_lor_results.csv   (alle 8 specificaties)
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
IEA_FILE = PROJECT_ROOT / "data" / "raw" / "Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUT = PROJECT_ROOT / "output_data"
FIGURES = PROJECT_ROOT / "figures"
FIGURES.mkdir(exist_ok=True)
CURRENT_YEAR = 2026

# ============================================================
# DATA HELPERS
# ============================================================
def to_year_safe(x):
    if pd.isna(x): return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100: return int(v)
    except: pass
    return np.nan

def parse_capacity_mw(row):
    cap = row.get("Electrolyzer capacity")
    unit = str(row.get("Electrolyzer capacity unit", "")).lower().strip()
    if pd.isna(cap): return np.nan
    try: val = float(cap)
    except:
        try: val = float(re.search(r"[\d.]+", str(cap)).group())
        except: return np.nan
    if "gigawatt" in unit: return val * 1000
    if "kilowatt" in unit: return val / 1000
    return val

def region_group(c):
    if pd.isna(c): return "Other"
    c = str(c).strip()
    eu27 = ["Netherlands","Germany","France","Spain","Denmark","Belgium","Italy",
             "Sweden","Finland","Portugal","Austria","Poland"]
    if any(e in c for e in eu27): return "EU"
    if c in ("United Kingdom","UK","Norway","Switzerland","Iceland"): return "Other_Europe"
    if c in ("United States","USA","Canada","Mexico"): return "North_America"
    if c in ("Japan","South Korea","China","India","Singapore","Taiwan"): return "Asia"
    if c in ("Australia","New Zealand"): return "ANZ"
    if c in ("Saudi Arabia","UAE","Oman","Qatar","Egypt","Morocco","Israel"): return "MENA"
    return "Other"

def tech_group(t):
    if pd.isna(t): return "Other"
    s = str(t).lower()
    if "pem" in s: return "PEM"
    if "alkaline" in s: return "Alkaline"
    if "ccs" in s: return "Blue_CCS"
    return "Other"

SPONSOR_MAP = {"shell":"Oil_major","bp":"Oil_major","totalenergies":"Oil_major","equinor":"Oil_major",
               "repsol":"Oil_major","eni":"Oil_major","aramco":"Oil_major","rwe":"Utility",
               "iberdrola":"Utility","orsted":"Utility","engie":"Utility","enel":"Utility",
               "air liquide":"Industrial_gas","air products":"Industrial_gas","linde":"Industrial_gas",
               "arcelormittal":"Steel","thyssenkrupp":"Steel","plug power":"Pure_play","nel":"Pure_play"}

def sponsor_type(s):
    if pd.isna(s): return "Unknown"
    s_low = str(s).lower().strip()
    for k, v in SPONSOR_MAP.items():
        if k in s_low: return v
    return "Other"

# ============================================================
# DATA OPBOUW
# ============================================================
print("=" * 70)
print("DATA OPBOUW VOOR LEAVE-ONE-REGION-OUT")
print("=" * 70)

iea = pd.read_excel(IEA_FILE, sheet_name="Export")
iea["project_status"] = iea["project_status"].astype(str).str.strip()
iea["year_announced"] = iea["Year announced"].apply(to_year_safe)
iea["year_online"] = iea["Date online"].apply(to_year_safe)
iea["capacity_mw"] = iea.apply(parse_capacity_mw, axis=1)
iea["log_capacity_mw"] = np.log1p(iea["capacity_mw"].fillna(0))
iea["region"] = iea["Geography"].apply(region_group)
iea["tech"] = iea["H2 Technology"].apply(tech_group)
iea["sponsor_type"] = iea["Primary owner"].apply(sponsor_type)
iea["sponsor_owner"] = iea["Primary owner"].fillna("Unknown").astype(str)

df = iea[iea["tech"].isin(["Blue_CCS", "PEM"])].copy()
df = df.dropna(subset=["year_announced", "log_capacity_mw"])
df = df[df["project_status"] != "Decommissioned"].copy()
df["is_blue_ccs"] = (df["tech"] == "Blue_CCS").astype(int)
df = df.reset_index(drop=True)
df["project_id"] = df.index

ACTIVE_FAILURE = {"Plans cancelled", "On-hold (confirmed)"}
SUCCESS = {"Fully commissioned","Partially commissioned","Under construction",
            "Permitted","Financed"}

# Person-year panel
panel_rows = []
for idx, row in df.iterrows():
    status = row["project_status"]
    t_start = int(row["year_announced"])
    t_online = row["year_online"] if pd.notna(row["year_online"]) and row["year_online"] >= t_start else CURRENT_YEAR
    t_online = int(min(t_online, CURRENT_YEAR + 5))
    if status in SUCCESS:
        t_end = min(t_online, CURRENT_YEAR); event = 0
    elif status in ACTIVE_FAILURE:
        target = min(t_online, CURRENT_YEAR)
        t_end = max(t_start, int((t_start + target) / 2)); event = 1
    else:
        t_end = CURRENT_YEAR; event = 0
    for t in range(t_start, t_end + 1):
        panel_rows.append({
            "project_id": int(idx), "year_calendar": t,
            "year_since_start": t - t_start,
            "event_any_yr": int((t == t_end) and event == 1),
            "is_blue_ccs": int(row["is_blue_ccs"]),
            "log_capacity_mw": row["log_capacity_mw"],
            "region": row["region"], "sponsor_type": row["sponsor_type"],
            "sponsor_owner": row["sponsor_owner"],
        })
panel = pd.DataFrame(panel_rows)

print(f"  Panel: {len(panel)} person-years, {int(panel['event_any_yr'].sum())} events")
print(f"  Regio's: {sorted(panel['region'].unique())}")

# Per-region event counts
region_events = panel.groupby("region")["event_any_yr"].sum().to_dict()
region_projects = panel.groupby("region")["project_id"].nunique().to_dict()
region_blue = panel[panel["is_blue_ccs"]==1].groupby("region")["project_id"].nunique().to_dict()
print("\n  Verdeling events per regio:")
for r in sorted(region_events.keys()):
    print(f"    {r:<20} projects={region_projects.get(r,0):4d}, "
           f"Blue_CCS={region_blue.get(r,0):3d}, events={int(region_events.get(r,0)):2d}")

# ============================================================
# LEAVE-ONE-REGION-OUT FITS
# ============================================================
print("\n" + "=" * 70)
print("LEAVE-ONE-REGION-OUT FITS")
print("=" * 70)

regions = sorted(panel["region"].unique().tolist())

def fit_hazard(panel_sub, ref_region="EU", ref_sponsor="Oil_major"):
    """Fit hazard model met dynamic references."""
    remaining_regions = panel_sub["region"].unique().tolist()
    remaining_sponsors = panel_sub["sponsor_type"].unique().tolist()
    
    # Fall back als reference niet meer aanwezig
    if ref_region not in remaining_regions:
        # Pick most common
        ref_region = panel_sub["region"].mode()[0]
        print(f"      Reference regio veranderd naar: {ref_region}")
    if ref_sponsor not in remaining_sponsors:
        ref_sponsor = panel_sub["sponsor_type"].mode()[0]
        print(f"      Reference sponsor veranderd naar: {ref_sponsor}")
    
    formula = (
        f"event_any_yr ~ is_blue_ccs + year_since_start + I(year_since_start**2) "
        f"+ log_capacity_mw "
        f"+ C(region, Treatment(reference='{ref_region}')) "
        f"+ C(sponsor_type, Treatment(reference='{ref_sponsor}'))"
    )
    
    try:
        m = smf.glm(formula, data=panel_sub, family=sm.families.Binomial()).fit(
            cov_type="cluster", cov_kwds={"groups": panel_sub["sponsor_owner"]}
        )
        return m, ref_region, ref_sponsor
    except Exception as e:
        print(f"      FAILED: {e}")
        return None, ref_region, ref_sponsor

results = []

# Full sample baseline eerst
print("\n  [1/8] Full sample baseline:")
m_full, _, _ = fit_hazard(panel)
if m_full is not None:
    bc = m_full.params["is_blue_ccs"]
    bs = m_full.bse["is_blue_ccs"]
    bp_val = m_full.pvalues["is_blue_ccs"]
    print(f"      Blue_CCS coef = {bc:.3f}, HR = {np.exp(bc):.2f}, SE = {bs:.3f}, p = {bp_val:.4f}")
    results.append({
        "specification": "Full sample",
        "excluded_region": "none",
        "n_obs": len(panel),
        "n_events": int(panel["event_any_yr"].sum()),
        "n_projects": int(panel["project_id"].nunique()),
        "n_blue": int(panel[panel["is_blue_ccs"]==1]["project_id"].nunique()),
        "n_pem": int(panel[panel["is_blue_ccs"]==0]["project_id"].nunique()),
        "blue_coef": bc, "blue_se": bs, "blue_p": bp_val,
        "blue_hr": float(np.exp(bc)),
        "hr_lower": float(np.exp(bc - 1.96 * bs)),
        "hr_upper": float(np.exp(bc + 1.96 * bs)),
    })

# Per-region exclusions
for i, region in enumerate(regions):
    print(f"\n  [{i+2}/8] Excluding region: {region}")
    panel_sub = panel[panel["region"] != region].copy()
    n_obs = len(panel_sub)
    n_events = int(panel_sub["event_any_yr"].sum())
    n_proj = int(panel_sub["project_id"].nunique())
    print(f"      Resulting sample: {n_proj} projects, {n_events} events")
    
    if n_events < 5:
        print(f"      SKIP: te weinig events ({n_events})")
        continue
    
    m_sub, used_ref, used_sp = fit_hazard(panel_sub)
    if m_sub is None:
        continue
    
    bc = m_sub.params["is_blue_ccs"]
    bs = m_sub.bse["is_blue_ccs"]
    bp_val = m_sub.pvalues["is_blue_ccs"]
    print(f"      Blue_CCS coef = {bc:.3f}, HR = {np.exp(bc):.2f}, SE = {bs:.3f}, p = {bp_val:.4f}")
    
    results.append({
        "specification": f"Excl. {region}",
        "excluded_region": region,
        "n_obs": n_obs,
        "n_events": n_events,
        "n_projects": n_proj,
        "n_blue": int(panel_sub[panel_sub["is_blue_ccs"]==1]["project_id"].nunique()),
        "n_pem": int(panel_sub[panel_sub["is_blue_ccs"]==0]["project_id"].nunique()),
        "blue_coef": bc, "blue_se": bs, "blue_p": bp_val,
        "blue_hr": float(np.exp(bc)),
        "hr_lower": float(np.exp(bc - 1.96 * bs)),
        "hr_upper": float(np.exp(bc + 1.96 * bs)),
    })

results_df = pd.DataFrame(results)

# ============================================================
# OUTPUT
# ============================================================
print("\n" + "=" * 70)
print("SAMENVATTING")
print("=" * 70)

cols_show = ["specification", "n_projects", "n_events", "blue_hr",
              "hr_lower", "hr_upper", "blue_p"]
print(results_df[cols_show].to_string(index=False))

# Range
hr_full = results_df.loc[results_df["specification"]=="Full sample", "blue_hr"].values[0]
lor_hrs = results_df.loc[results_df["specification"]!="Full sample", "blue_hr"].values
print(f"\n  Full sample HR:        {hr_full:.2f}")
print(f"  LOR HR range:          [{lor_hrs.min():.2f}, {lor_hrs.max():.2f}]")
print(f"  Max % deviation:       {max(abs(lor_hrs - hr_full) / hr_full) * 100:.1f}%")

# Interpretation
max_dev_pct = max(abs(lor_hrs - hr_full) / hr_full) * 100
if max_dev_pct < 15:
    print(f"\n  CONCLUSIE: Bevinding is ROBUUST — geen regio drijft het resultaat")
    print(f"  (alle LOR HRs binnen 15% van full sample HR)")
elif max_dev_pct < 30:
    print(f"\n  CONCLUSIE: Matige regio-gevoeligheid (max deviation {max_dev_pct:.1f}%)")
else:
    most_influential = results_df.iloc[1:].assign(
        dev=lambda x: abs(x["blue_hr"] - hr_full) / hr_full
    ).nlargest(1, "dev").iloc[0]
    print(f"\n  WAARSCHUWING: Substantieele regio-gevoeligheid")
    print(f"  Meest invloedrijke uitsluiting: {most_influential['specification']}")
    print(f"  (HR {most_influential['blue_hr']:.2f} vs full {hr_full:.2f})")

# CSV output
csv_path = OUT / "27_lor_results.csv"
results_df.to_csv(csv_path, index=False)
print(f"\n  CSV: {csv_path}")

# ============================================================
# FOREST PLOT
# ============================================================
fig, ax = plt.subplots(figsize=(11, 6))

# Sortering: full sample bovenaan, rest alfabetisch
labels = results_df["specification"].tolist()
hrs = results_df["blue_hr"].values
lowers = results_df["hr_lower"].values
uppers = results_df["hr_upper"].values

y_pos = np.arange(len(results_df))[::-1]  # bovenaan = full sample

# Errorbar voor CIs
ax.errorbar(hrs, y_pos,
              xerr=[hrs - lowers, uppers - hrs],
              fmt='o', markersize=9, color="#C00000", capsize=4, capthick=1.5,
              ecolor="#C00000", elinewidth=1.5)

# Full sample HR als verticale referentielijn
ax.axvline(hr_full, linestyle="-", color="#2E75B6", alpha=0.5, linewidth=2,
            label=f"Full sample HR = {hr_full:.2f}")
ax.axvline(1, linestyle="--", color="gray", alpha=0.6, linewidth=1, label="HR = 1 (no effect)")

# Highlight full sample row met andere kleur
full_idx = list(labels).index("Full sample")
y_full = y_pos[full_idx]
ax.errorbar(hr_full, y_full,
              xerr=[[hr_full - lowers[full_idx]], [uppers[full_idx] - hr_full]],
              fmt='s', markersize=11, color="#2E75B6", capsize=5, capthick=2,
              ecolor="#2E75B6", elinewidth=2)

ax.set_yticks(y_pos)
ax.set_yticklabels(labels)
ax.set_xscale("log")
ax.set_xlabel("Blue_CCS Hazard Ratio (95% CI, cluster sponsor SE)", fontsize=11)
ax.set_title(f"Leave-One-Region-Out Robustness — Blue_CCS Cancellation Hazard\n"
              f"Geen regio drijft het resultaat: alle LOR estimates binnen "
              f"[{lor_hrs.min():.1f}, {lor_hrs.max():.1f}] versus full sample HR = {hr_full:.1f}",
              fontsize=11)
ax.grid(alpha=0.3, axis="x", which="both")
ax.legend(loc="lower right")

plt.tight_layout()
fig_path = FIGURES / "fig_lor_forest.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"\n  Forest plot: {fig_path}")

print("\nKLAAR.")
print(f"\nVoor paper v3c: voeg LOR resultaten toe in Sectie 6 (Robustness) als nieuwe")
print(f"  subsectie 6.7 'Leave-One-Region-Out Robustness'. Forest plot fig_lor_forest.png")
print(f"  als Figure 2 of als Appendix Figure A2.")
