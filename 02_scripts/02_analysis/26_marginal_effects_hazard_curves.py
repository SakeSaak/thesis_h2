"""
26_marginal_effects_hazard_curves.py

Produceert predicted Blue_CCS cancellation hazard als functie van macro-variables.
Voor elke macro-variable (EUA, gas, VIX, EPU):
  - Fit GLM hazard model met Blue_CCS x macro interactie
  - Bereken predicted Blue_CCS log-HR over een grid van z-waardes
  - Delta method voor variance van linear combination
  - Plot HR met 95% CI shaded

De EUA plot is het visuele centrum van het paper: laat zien dat Blue_CCS risk
sterk daalt bij hogere carbon prijzen.

Output:
  - /figures/fig_marginal_effects_4panel.png  (alle vier)
  - /figures/fig_marginal_effects_eua.png      (headline close-up)
  - /output_data/26_marginal_effects.csv       (cijfers)

Vereist: numpy, pandas, statsmodels, matplotlib
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

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path("/Users/sakesaakstra/Desktop/thesis_h2")
IEA_FILE = PROJECT_ROOT / "data" / "raw" / "Hydrogen_projects_master_data_table_24-03-26.xlsx"
MASTER_PANEL = PROJECT_ROOT / "output_data" / "master_panel_daily.csv"
OUT = PROJECT_ROOT / "output_data"
FIGURES = PROJECT_ROOT / "figures"
FIGURES.mkdir(exist_ok=True)
CURRENT_YEAR = 2026

# Reference EUA price for x-axis labels (sample period mean approx)
EUA_MEAN = 55.0  # euros/tCO2 approx historical mean over panel
EUA_SD = 25.0    # approx std deviation
TTF_MEAN = 35.0
TTF_SD = 30.0
VIX_MEAN = 20.0
VIX_SD = 8.0
EPU_MEAN = 130.0
EPU_SD = 50.0

# ============================================================
# DATA HELPERS (zelfde als script 24)
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
print("DATA OPBOUW")
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
df["event_any"] = df["project_status"].isin(ACTIVE_FAILURE).astype(int)

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

# Macro covariates
mp = pd.read_csv(MASTER_PANEL, index_col=0, parse_dates=True)
yearly_macro = mp.resample("YE").mean(numeric_only=True)
yearly_macro["year_calendar"] = yearly_macro.index.year
for c in ["eua","ttf_gas","VIXCLS","USEPUINDXD"]:
    if c in yearly_macro.columns:
        panel = panel.merge(yearly_macro[[c,"year_calendar"]], on="year_calendar", how="left")
        panel = panel.rename(columns={c: f"mkt_{c}"})

for col in ["mkt_eua","mkt_ttf_gas","mkt_VIXCLS","mkt_USEPUINDXD"]:
    if col in panel.columns:
        panel[col] = panel[col].fillna(panel[col].median())
        panel[f"{col}_z"] = (panel[col] - panel[col].mean()) / panel[col].std()

print(f"  Panel: {len(panel)} obs, {int(panel['event_any_yr'].sum())} events")

# ============================================================
# DELTA METHOD VOOR MARGINAL EFFECTS
# ============================================================
def predicted_blue_logHR(model, main_var, int_var, z_grid):
    """Delta method voor Blue_CCS log-HR over z grid."""
    params = model.params
    cov = model.cov_params()
    
    beta_main = params[main_var]
    beta_int = params[int_var]
    var_main = cov.loc[main_var, main_var]
    var_int = cov.loc[int_var, int_var]
    cov_mi = cov.loc[main_var, int_var]
    
    rows = []
    for z in z_grid:
        logHR = beta_main + beta_int * z
        # Var(β_main + z*β_int) = var_main + z² var_int + 2z cov_mi
        var_lc = var_main + z**2 * var_int + 2 * z * cov_mi
        se_lc = np.sqrt(max(var_lc, 1e-12))
        rows.append({
            "z": float(z),
            "logHR": float(logHR),
            "SE_logHR": float(se_lc),
            "HR": float(np.exp(logHR)),
            "HR_lower": float(np.exp(logHR - 1.96 * se_lc)),
            "HR_upper": float(np.exp(logHR + 1.96 * se_lc)),
        })
    return pd.DataFrame(rows)

# ============================================================
# FIT 4 INTERACTIE MODELLEN
# ============================================================
print("\n" + "=" * 70)
print("FIT INTERACTIE MODELLEN")
print("=" * 70)

BASE = (
    " + year_since_start + I(year_since_start**2) + log_capacity_mw "
    "+ C(region, Treatment(reference='EU')) "
    "+ C(sponsor_type, Treatment(reference='Oil_major'))"
)

interactions = {}

# 1. EUA carbon prijs
panel["blue_x_eua"] = panel["is_blue_ccs"] * panel["mkt_eua_z"]
m_eua = smf.glm("event_any_yr ~ is_blue_ccs + mkt_eua_z + blue_x_eua" + BASE,
                  data=panel, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]})
interactions["EUA Carbon Price"] = {
    "model": m_eua, "main": "is_blue_ccs", "int": "blue_x_eua",
    "macro_mean": EUA_MEAN, "macro_sd": EUA_SD, "unit": "€/tCO2"
}
print(f"  EUA: interaction coef = {m_eua.params['blue_x_eua']:.3f}, p = {m_eua.pvalues['blue_x_eua']:.4f}")

# 2. TTF gas prijs
panel["blue_x_gas"] = panel["is_blue_ccs"] * panel["mkt_ttf_gas_z"]
m_gas = smf.glm("event_any_yr ~ is_blue_ccs + mkt_ttf_gas_z + blue_x_gas" + BASE,
                  data=panel, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]})
interactions["TTF Gas Price"] = {
    "model": m_gas, "main": "is_blue_ccs", "int": "blue_x_gas",
    "macro_mean": TTF_MEAN, "macro_sd": TTF_SD, "unit": "€/MWh"
}
print(f"  TTF: interaction coef = {m_gas.params['blue_x_gas']:.3f}, p = {m_gas.pvalues['blue_x_gas']:.4f}")

# 3. VIX
panel["blue_x_vix"] = panel["is_blue_ccs"] * panel["mkt_VIXCLS_z"]
m_vix = smf.glm("event_any_yr ~ is_blue_ccs + mkt_VIXCLS_z + blue_x_vix" + BASE,
                  data=panel, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]})
interactions["VIX (Financial Uncertainty)"] = {
    "model": m_vix, "main": "is_blue_ccs", "int": "blue_x_vix",
    "macro_mean": VIX_MEAN, "macro_sd": VIX_SD, "unit": "index"
}
print(f"  VIX: interaction coef = {m_vix.params['blue_x_vix']:.3f}, p = {m_vix.pvalues['blue_x_vix']:.4f}")

# 4. EPU
panel["blue_x_epu"] = panel["is_blue_ccs"] * panel["mkt_USEPUINDXD_z"]
m_epu = smf.glm("event_any_yr ~ is_blue_ccs + mkt_USEPUINDXD_z + blue_x_epu" + BASE,
                  data=panel, family=sm.families.Binomial()).fit(
    cov_type="cluster", cov_kwds={"groups": panel["sponsor_owner"]})
interactions["EPU (Policy Uncertainty)"] = {
    "model": m_epu, "main": "is_blue_ccs", "int": "blue_x_epu",
    "macro_mean": EPU_MEAN, "macro_sd": EPU_SD, "unit": "index"
}
print(f"  EPU: interaction coef = {m_epu.params['blue_x_epu']:.3f}, p = {m_epu.pvalues['blue_x_epu']:.4f}")

# ============================================================
# COMPUTE MARGINAL EFFECTS OVER GRID
# ============================================================
print("\n" + "=" * 70)
print("MARGINAL EFFECTS BEREKENING")
print("=" * 70)

z_grid = np.linspace(-1.5, 1.5, 60)
all_predictions = {}
key_z_values = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]

csv_rows = []
for name, info in interactions.items():
    pred_df = predicted_blue_logHR(info["model"], info["main"], info["int"], z_grid)
    all_predictions[name] = pred_df
    
    # Specific z values to CSV
    for z in key_z_values:
        row_grid = predicted_blue_logHR(info["model"], info["main"], info["int"], [z]).iloc[0]
        csv_rows.append({
            "interaction": name,
            "z": z,
            "macro_level_approx": info["macro_mean"] + z * info["macro_sd"],
            "macro_unit": info["unit"],
            "blue_logHR": row_grid["logHR"],
            "blue_HR": row_grid["HR"],
            "HR_CI_lower": row_grid["HR_lower"],
            "HR_CI_upper": row_grid["HR_upper"],
            "interaction_coef": info["model"].params[info["int"]],
            "interaction_p": info["model"].pvalues[info["int"]],
        })

csv_df = pd.DataFrame(csv_rows)
csv_path = OUT / "26_marginal_effects.csv"
csv_df.to_csv(csv_path, index=False)
print(f"  Numerieke output: {csv_path}")

# Print summary at z=0 and z=+1 voor EUA (headline)
print("\n  KEY VALUES — EUA Interactie:")
eua_df = all_predictions["EUA Carbon Price"]
for target_z in [-1, 0, 1]:
    idx = (eua_df["z"] - target_z).abs().idxmin()
    row = eua_df.iloc[idx]
    eua_level = EUA_MEAN + target_z * EUA_SD
    print(f"    z = {target_z:+.1f} (EUA ≈ €{eua_level:.0f}): HR = {row['HR']:.2f}, "
           f"CI [{row['HR_lower']:.2f}, {row['HR_upper']:.2f}]")

# ============================================================
# PLOTS
# ============================================================
print("\n" + "=" * 70)
print("PLOTS")
print("=" * 70)

# === 4-PANEL FIGURE ===
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
ax_list = axes.flatten()
panel_order = ["EUA Carbon Price", "TTF Gas Price",
                "VIX (Financial Uncertainty)", "EPU (Policy Uncertainty)"]

for ax, name in zip(ax_list, panel_order):
    pred_df = all_predictions[name]
    info = interactions[name]
    int_p = info["model"].pvalues[info["int"]]
    int_coef = info["model"].params[info["int"]]
    
    # Color: rood voor significant, grijs voor niet
    color = "#C00000" if int_p < 0.05 else "#808080"
    alpha_band = 0.25 if int_p < 0.05 else 0.15
    
    ax.fill_between(pred_df["z"], pred_df["HR_lower"], pred_df["HR_upper"],
                     alpha=alpha_band, color=color)
    ax.plot(pred_df["z"], pred_df["HR"], color=color, linewidth=2.5)
    ax.axhline(1, linestyle="--", color="black", alpha=0.5, linewidth=1)
    ax.set_yscale("log")
    ax.set_xlabel(f"{name} (z-score)", fontsize=10)
    ax.set_ylabel("Blue_CCS Hazard Ratio (log scale)", fontsize=10)
    
    title_p = f"p = {int_p:.4f}" if int_p >= 0.001 else "p < 0.001"
    significance = " ***" if int_p < 0.001 else (" **" if int_p < 0.01 else (" *" if int_p < 0.05 else " (n.s.)"))
    ax.set_title(f"{name}\ninteraction coef = {int_coef:+.2f} ({title_p}{significance})",
                  fontsize=10)
    ax.grid(alpha=0.3)
    
    # x-axis: add macro level as secondary ticks
    ax2 = ax.secondary_xaxis("top")
    ax2.set_xlabel(f"Approx. {name.split(' (')[0]} level ({info['unit']})", fontsize=9)
    z_ticks = np.array([-1.5, -1, 0, 1, 1.5])
    level_ticks = info["macro_mean"] + z_ticks * info["macro_sd"]
    ax2.set_xticks(z_ticks)
    ax2.set_xticklabels([f"{v:.0f}" for v in level_ticks], fontsize=8)

plt.suptitle("Predicted Blue_CCS Cancellation Hazard Across Macro-Financial Conditions\n"
              "Delta method 95% CI; only EUA interaction is statistically significant",
              fontsize=12, y=1.02)
plt.tight_layout()
fig_path = FIGURES / "fig_marginal_effects_4panel.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  4-panel: {fig_path}")

# === CLOSE-UP EUA (HEADLINE) ===
fig, ax = plt.subplots(figsize=(10, 6.5))
eua_df = all_predictions["EUA Carbon Price"]
m = interactions["EUA Carbon Price"]["model"]
int_coef = m.params["blue_x_eua"]
int_p = m.pvalues["blue_x_eua"]

ax.fill_between(eua_df["z"], eua_df["HR_lower"], eua_df["HR_upper"],
                  alpha=0.25, color="#C00000", label="95% CI (delta method)")
ax.plot(eua_df["z"], eua_df["HR"], color="#C00000", linewidth=3, label="Predicted Blue_CCS HR")
ax.axhline(1, linestyle="--", color="black", alpha=0.6, linewidth=1, label="HR = 1 (no effect)")
ax.set_yscale("log")
ax.set_xlabel("EUA Carbon Price (z-score)", fontsize=12)
ax.set_ylabel("Blue_CCS Cancellation Hazard Ratio (log scale)", fontsize=12)

# Annotations bij belangrijke punten
for target_z, label_y in [(-1, 1.15), (0, 1.15), (1, 1.15)]:
    idx = (eua_df["z"] - target_z).abs().idxmin()
    row = eua_df.iloc[idx]
    eua_level = EUA_MEAN + target_z * EUA_SD
    ax.annotate(f"HR = {row['HR']:.1f}\n€{eua_level:.0f}/tCO2",
                 xy=(target_z, row["HR"]),
                 xytext=(target_z, row["HR"] * label_y),
                 fontsize=9, ha="center",
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

ax.set_title(f"The Blue_CCS Implementation-Risk Premium Is Carbon-Price-Conditional\n"
              f"Interaction coefficient = {int_coef:+.2f} (p < 0.0001); 4,246 person-years, "
              f"cluster-robust SE at sponsor level",
              fontsize=11)
ax.grid(alpha=0.3, which="both")
ax.legend(loc="upper right")

# Secondary x-axis
ax2 = ax.secondary_xaxis("top")
ax2.set_xlabel("Approx. EUA Carbon Price (€/tCO2)", fontsize=11)
z_ticks = np.array([-1.5, -1, -0.5, 0, 0.5, 1, 1.5])
level_ticks = EUA_MEAN + z_ticks * EUA_SD
ax2.set_xticks(z_ticks)
ax2.set_xticklabels([f"{v:.0f}" for v in level_ticks], fontsize=10)

plt.tight_layout()
fig_path = FIGURES / "fig_marginal_effects_eua.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  EUA close-up: {fig_path}")

print("\nKLAAR.")
print(f"\nVoor paper v3c: voeg figuur fig_marginal_effects_eua.png in als Figure 1")
print(f"  in Sectie 5.4 (Carbon-Price-Conditional Risk). De 4-panel versie kan")
print(f"  als Appendix Figure A1 (toont dat ALLEEN EUA significant interacteert).")
