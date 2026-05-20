"""
prepare_h2_data_for_R.py

Standalone helper: bouwt project-level data set voor Blue_CCS + PEM en
exporteert als CSV. Lost readxl import probleem op in R 4.3 op Mac.

Run dit EERST, daarna 25b_competing_risks_frailty_csv.R
"""

from pathlib import Path
import re
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
IEA_FILE = PROJECT_ROOT / "data" / "raw" / "Hydrogen_projects_master_data_table_24-03-26.xlsx"
OUT = PROJECT_ROOT / "output_data"
CURRENT_YEAR = 2026

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

print("Reading IEA Excel...")
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

# Blue_CCS + PEM subset
df = iea[iea["tech"].isin(["Blue_CCS", "PEM"])].copy()
df = df.dropna(subset=["year_announced", "log_capacity_mw"])
df = df[df["project_status"] != "Decommissioned"].copy()
df["is_blue_ccs"] = (df["tech"] == "Blue_CCS").astype(int)
df = df.reset_index(drop=True)
df["project_id"] = df.index

ACTIVE_FAILURE = {"Plans cancelled", "On-hold (confirmed)"}
SUCCESS = {"Fully commissioned","Partially commissioned","Under construction",
            "Permitted","Financed"}
CANCELLED = {"Plans cancelled"}
ON_HOLD = {"On-hold (confirmed)"}

# 0=censored, 1=cancelled, 2=on-hold
df["event_type"] = 0
df.loc[df["project_status"].isin(CANCELLED), "event_type"] = 1
df.loc[df["project_status"].isin(ON_HOLD), "event_type"] = 2

df["event_any"] = (df["event_type"] > 0).astype(int)

# Build duration
df["t_start"] = df["year_announced"].astype(int)
df["t_online_use"] = np.where(
    df["year_online"].notna() & (df["year_online"] >= df["t_start"]),
    df["year_online"],
    CURRENT_YEAR
)
df["t_online_use"] = np.minimum(df["t_online_use"], CURRENT_YEAR + 5)

# t_end logic
def get_t_end(row):
    if row["project_status"] in SUCCESS:
        return int(min(row["t_online_use"], CURRENT_YEAR))
    elif row["event_type"] > 0:
        target = min(row["t_online_use"], CURRENT_YEAR)
        return int(max(row["t_start"], (row["t_start"] + target) / 2))
    else:
        return CURRENT_YEAR

df["t_end"] = df.apply(get_t_end, axis=1)
df["duration"] = np.maximum(1, df["t_end"] - df["t_start"]).astype(int)

# Export columns needed for R analyses
export_cols = [
    "project_id", "is_blue_ccs", "log_capacity_mw", "region",
    "sponsor_type", "sponsor_owner", "tech",
    "year_announced", "duration",
    "event_any", "event_type",
]
df_export = df[export_cols].copy()

csv_path = OUT / "blueccs_project_level_for_R.csv"
df_export.to_csv(csv_path, index=False, encoding="utf-8")

print(f"\nExport saved: {csv_path}")
print(f"  Total rows: {len(df_export)}")
print(f"  Blue_CCS: {df_export['is_blue_ccs'].sum()}")
print(f"  PEM: {(1-df_export['is_blue_ccs']).sum()}")
print(f"  Events (any): {df_export['event_any'].sum()}")
print(f"  Cancelled (type=1): {(df_export['event_type']==1).sum()}")
print(f"  On-hold (type=2): {(df_export['event_type']==2).sum()}")
print(f"\nNu kun je R script 25b draaien.")
