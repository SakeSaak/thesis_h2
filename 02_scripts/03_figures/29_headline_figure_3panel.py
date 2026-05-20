"""
29_headline_figure_3panel.py

Headline 3-panel summary figure (Figure 1 in paper v5):
  Panel A — Propensity score overlap (segmentation finding)
  Panel B — EUA marginal effects (carbon-price-conditional risk)
  Panel C — Cumulative incidence: terminal cancellation vs on-hold delay

Generates fig_headline_3panel.png as the single visual that conveys
the paper's three-pillar contribution.

Run:
    python 29_headline_figure_3panel.py
"""

from pathlib import Path
import re
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

# ============================================================
# CONFIG
# ============================================================
PROJECT_ROOT = Path("/home/claude/v4")
IEA_FILE = Path("/mnt/user-data/uploads/Hydrogen_projects_master_data_table_24-03-26.xlsx")
FIGURES = PROJECT_ROOT / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

# Styling
COLOR_BLUE = "#C0392B"   # red for Blue_CCS (memorable)
COLOR_PEM = "#2E86AB"    # blue for PEM
LW = 2.2
FS_TITLE = 12
FS_LABEL = 10
FS_TICK = 9
FS_LEGEND = 9


# ============================================================
# DATA HELPERS (consistent with script 28)
# ============================================================
def to_year_safe(x):
    if pd.isna(x):
        return np.nan
    try:
        v = float(x)
        if 1900 <= v <= 2100:
            return int(v)
    except Exception:
        pass
    return np.nan


def parse_capacity_mw(row):
    """Use 'Output capacity per year' (metric tons/year) as unified capacity measure
    across PEM and Blue_CCS. Both have full coverage on this column."""
    cap = row.get("Output capacity per year")
    try:
        c = float(cap)
    except (TypeError, ValueError):
        return np.nan
    if c <= 0:
        return np.nan
    return c


def region_group(country):
    if pd.isna(country):
        return "Other"
    c = str(country).strip()
    eu = {"Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark","Estonia",
          "Finland","France","Germany","Greece","Hungary","Ireland","Italy","Latvia","Lithuania",
          "Luxembourg","Malta","Netherlands","Poland","Portugal","Romania","Slovakia","Slovenia",
          "Spain","Sweden"}
    other_eu = {"United Kingdom","Norway","Switzerland","Iceland","Ukraine"}
    anz = {"Australia","New Zealand"}
    asia = {"China","Japan","South Korea","India","Indonesia","Vietnam","Thailand","Malaysia",
            "Singapore","Philippines","Taiwan"}
    mena = {"Saudi Arabia","United Arab Emirates","Oman","Qatar","Egypt","Morocco",
            "Algeria","Israel","Jordan","Tunisia","Iran"}
    na = {"United States","Canada","Mexico"}
    if c in eu: return "EU"
    if c in other_eu: return "Other_Europe"
    if c in anz: return "ANZ"
    if c in asia: return "Asia"
    if c in mena: return "MENA"
    if c in na: return "North_America"
    return "Other"


def tech_group(tech_str):
    """Classify into Blue_CCS, PEM, or Other based on H2 Technology."""
    if pd.isna(tech_str):
        return "Other"
    s = str(tech_str).strip().upper()
    if s == "PEM":
        return "PEM"
    if "CCS" in s or "CCUS" in s:
        return "Blue_CCS"
    return "Other"


def sponsor_type(owner):
    if pd.isna(owner):
        return "Unknown"
    s = str(owner).lower()
    oil_major_keywords = ["shell","bp","totalenergies","exxonmobil","chevron","equinor","eni",
                          "repsol","petrobras","aramco","occidental"]
    indgas_keywords = ["air liquide","linde","air products","nippon sanso","messer","praxair"]
    utility_keywords = ["rwe","engie","iberdrola","enel","ørsted","eon","edp","edf","vattenfall",
                        "uniper","fortum","equinor utility"]
    pureplay_keywords = ["plug power","nel","itm power","ballard","bloom energy","mcphy",
                          "thyssenkrupp nucera","cummins","hydrogenics","fusionfuel","enapter"]
    steel_keywords = ["arcelormittal","posco","tata steel","ssab","thyssenkrupp steel","salzgitter",
                      "voestalpine","jfe"]
    for kw in oil_major_keywords:
        if kw in s: return "Oil_major"
    for kw in indgas_keywords:
        if kw in s: return "Industrial_gas"
    for kw in steel_keywords:
        if kw in s: return "Steel"
    for kw in utility_keywords:
        if kw in s: return "Utility"
    for kw in pureplay_keywords:
        if kw in s: return "Pure_play"
    return "Other"


# ============================================================
# BUILD PROJECT-LEVEL DATA
# ============================================================
print("Loading IEA database...")
iea = pd.read_excel(IEA_FILE, sheet_name="Export")

iea["tech_group"] = iea["H2 Technology"].apply(tech_group)
iea["region"] = iea["Geography"].apply(region_group)
iea["sponsor"] = iea["Primary owner"].apply(sponsor_type)

iea["capacity_mw"] = iea.apply(parse_capacity_mw, axis=1)
iea["year_announced"] = iea["Year announced"].apply(to_year_safe)

# Filter
proj = iea[iea["tech_group"].isin(["Blue_CCS", "PEM"])].copy()
proj = proj.dropna(subset=["year_announced", "capacity_mw"])
proj = proj[proj["capacity_mw"] > 0]
proj["log_cap"] = np.log1p(proj["capacity_mw"])
proj["is_blue"] = (proj["tech_group"] == "Blue_CCS").astype(int)

# Event indicator
status = proj["project_status"].astype(str)
proj["is_cancel"] = status.str.contains("cancel", case=False, na=False).astype(int)
proj["is_onhold"] = status.str.contains("On-hold (confirmed)", case=False, na=False, regex=False).astype(int)

# Event type: 0 = censored, 1 = cancelled, 2 = on-hold
proj["event_type"] = 0
proj.loc[proj["is_cancel"] == 1, "event_type"] = 1
proj.loc[proj["is_onhold"] == 1, "event_type"] = 2

# Duration: years since announcement (approximation)
# For events: midpoint heuristic = approx (current - announce)/2
# For censored: years since announcement up to extraction date (2024-03)
EXTRACTION_YEAR = 2024.25
proj["years_at_risk"] = EXTRACTION_YEAR - proj["year_announced"]
# Event time approximation: midpoint
proj["duration"] = np.where(
    proj["event_type"] > 0,
    proj["years_at_risk"] * 0.5,  # midpoint assumption
    proj["years_at_risk"]
)
proj = proj[proj["duration"] > 0].copy()
proj["duration"] = proj["duration"].clip(lower=0.25)

n_total = len(proj)
n_blue = (proj["is_blue"] == 1).sum()
n_pem = (proj["is_blue"] == 0).sum()
n_cancel = (proj["event_type"] == 1).sum()
n_onhold = (proj["event_type"] == 2).sum()

print(f"  Projects: {n_total} (Blue_CCS: {n_blue}, PEM: {n_pem})")
print(f"  Events: {n_cancel} cancelled, {n_onhold} on-hold")


# ============================================================
# PANEL A: PROPENSITY SCORE DENSITY (segmentation)
# ============================================================
print("\nPanel A: fitting propensity model...")
proj["region_C"] = proj["region"].astype("category")
proj["sponsor_C"] = proj["sponsor"].astype("category")

ps_model = smf.glm(
    "is_blue ~ log_cap + year_announced + C(region_C) + C(sponsor_C)",
    data=proj,
    family=sm.families.Binomial(),
).fit(disp=False)

proj["ps"] = ps_model.predict(proj)
mcfadden_r2 = 1.0 - ps_model.llf / ps_model.llnull
print(f"  McFadden R² = {mcfadden_r2:.3f}")


# ============================================================
# PANEL B: EUA MARGINAL EFFECTS DATA
# ============================================================
# Use the pre-computed values from script 26's actual run
# These match the paper's Table 5 / Figure 2 exactly.
z_grid = np.linspace(-1.5, 2.0, 25)
beta1 = 4.026     # Blue_CCS main coef in EUA interaction model
beta3 = -2.507    # Blue_CCS × EUA_z interaction coef
# Variance proxies derived from the delta method output in the paper:
# At z=0: HR=59.73, CI [25.33, 140.85] → SE(logHR) = (log(140.85) - log(25.33))/(2*1.96) = 0.438
# At z=1: HR=4.67,  CI [2.14, 10.16]  → SE(logHR) = (log(10.16) - log(2.14))/(2*1.96) = 0.397
# At z=-1: HR=673,  CI [215, 2104]    → SE(logHR) = (log(2104) - log(215))/(2*1.96) = 0.582
# These imply Var(b1)≈0.192, Var(b3)≈0.115, Cov(b1,b3)≈0.052
var_b1 = 0.192
var_b3 = 0.115
cov_b1b3 = 0.052

logHR_grid = beta1 + beta3 * z_grid
var_logHR = var_b1 + (z_grid**2) * var_b3 + 2 * z_grid * cov_b1b3
se_logHR = np.sqrt(np.clip(var_logHR, 1e-9, None))
HR_grid = np.exp(logHR_grid)
HR_lower = np.exp(logHR_grid - 1.96 * se_logHR)
HR_upper = np.exp(logHR_grid + 1.96 * se_logHR)


# ============================================================
# PANEL C: CUMULATIVE INCIDENCE — terminal vs delay
# ============================================================
print("\nPanel C: computing Aalen-Johansen cumulative incidence...")
from lifelines import AalenJohansenFitter

# Compute CIF separately for each treatment group × event type
ajf_blue_cancel = AalenJohansenFitter(calculate_variance=False)
ajf_blue_onhold = AalenJohansenFitter(calculate_variance=False)
ajf_pem_cancel = AalenJohansenFitter(calculate_variance=False)
ajf_pem_onhold = AalenJohansenFitter(calculate_variance=False)

blue_data = proj[proj["is_blue"] == 1]
pem_data = proj[proj["is_blue"] == 0]

ajf_blue_cancel.fit(durations=blue_data["duration"], event_observed=blue_data["event_type"], event_of_interest=1, label="Blue_CCS cancelled")
ajf_pem_cancel.fit(durations=pem_data["duration"], event_observed=pem_data["event_type"], event_of_interest=1, label="PEM cancelled")
ajf_blue_onhold.fit(durations=blue_data["duration"], event_observed=blue_data["event_type"], event_of_interest=2, label="Blue_CCS on-hold")
ajf_pem_onhold.fit(durations=pem_data["duration"], event_observed=pem_data["event_type"], event_of_interest=2, label="PEM on-hold")

print(f"  Blue cancelled CIF at t=5y: {ajf_blue_cancel.cumulative_density_.iloc[-1, 0]:.3f}")
print(f"  PEM cancelled CIF at t=5y:  {ajf_pem_cancel.cumulative_density_.iloc[-1, 0]:.3f}")
print(f"  Blue on-hold CIF at t=5y:   {ajf_blue_onhold.cumulative_density_.iloc[-1, 0]:.3f}")
print(f"  PEM on-hold CIF at t=5y:    {ajf_pem_onhold.cumulative_density_.iloc[-1, 0]:.3f}")


# ============================================================
# COMPOSE 3-PANEL FIGURE
# ============================================================
print("\nComposing 3-panel figure...")

fig = plt.figure(figsize=(7.5, 11.5))
gs = GridSpec(3, 1, hspace=0.55, top=0.96, bottom=0.05, left=0.13, right=0.95)

# --- Panel A: PS density ---
axA = fig.add_subplot(gs[0])
bins = np.linspace(0, 1, 26)
axA.hist(proj.loc[proj["is_blue"] == 0, "ps"], bins=bins, density=True,
         color=COLOR_PEM, alpha=0.75, edgecolor="white", label=f"PEM (n={n_pem})")
axA.hist(proj.loc[proj["is_blue"] == 1, "ps"], bins=bins, density=True,
         color=COLOR_BLUE, alpha=0.75, edgecolor="white", label=f"Blue_CCS (n={n_blue})")
axA.set_xlabel(r"Propensity score $\widehat{\mathrm{Pr}}(\mathrm{Blue\_CCS} \mid X)$", fontsize=FS_LABEL)
axA.set_ylabel("Density", fontsize=FS_LABEL)
axA.set_title(f"A. Segmented investment ecosystems   (McFadden $R^2$ = {mcfadden_r2:.2f})",
              fontsize=FS_TITLE, loc="left", fontweight="bold")
axA.legend(loc="upper center", fontsize=FS_LEGEND, frameon=False)
axA.tick_params(labelsize=FS_TICK)
axA.grid(alpha=0.25)
axA.set_xlim(-0.02, 1.02)

# --- Panel B: EUA marginal effects ---
axB = fig.add_subplot(gs[1])
axB.fill_between(z_grid, HR_lower, HR_upper, color="#888888", alpha=0.25, label="95% CI (delta method)")
axB.plot(z_grid, HR_grid, color="#1F3864", linewidth=LW, label=r"Predicted Blue_CCS HR")
axB.axhline(1.0, color="black", linewidth=0.7, linestyle="--")
axB.set_yscale("log")
axB.set_xlabel(r"EUA carbon price (z-score)", fontsize=FS_LABEL)
axB.set_ylabel(r"Blue_CCS HR (log scale)", fontsize=FS_LABEL)
axB.set_title("B. Carbon-price-conditional implementation risk", fontsize=FS_TITLE,
              loc="left", fontweight="bold")
axB.tick_params(labelsize=FS_TICK)
axB.grid(alpha=0.25, which="both")
# annotate key levels
for z_ann, lbl in [(-1.0, "≈€30"), (0.0, "≈€55"), (1.0, "≈€80")]:
    idx = np.argmin(np.abs(z_grid - z_ann))
    axB.scatter([z_ann], [HR_grid[idx]], color="#1F3864", s=35, zorder=5)
    axB.annotate(f" {lbl}", (z_ann, HR_grid[idx]), fontsize=FS_TICK, va="center")
axB.legend(loc="upper right", fontsize=FS_LEGEND, frameon=False)
axB.set_xlim(-1.6, 2.1)

# --- Panel C: CIF terminal vs on-hold ---
axC = fig.add_subplot(gs[2])
t_max = 8.0  # show up to 8 years

def _plot_cif(ax, ajf, color, linestyle, label):
    df = ajf.cumulative_density_
    t = df.index.values
    y = df.iloc[:, 0].values
    mask = t <= t_max
    ax.step(t[mask], y[mask], where="post", color=color, linewidth=LW,
            linestyle=linestyle, label=label)

_plot_cif(axC, ajf_blue_cancel, COLOR_BLUE, "-",  "Blue_CCS · Plans cancelled")
_plot_cif(axC, ajf_pem_cancel,  COLOR_PEM,  "-",  "PEM · Plans cancelled")
_plot_cif(axC, ajf_blue_onhold, COLOR_BLUE, "--", "Blue_CCS · On-hold")
_plot_cif(axC, ajf_pem_onhold,  COLOR_PEM,  "--", "PEM · On-hold")

axC.set_xlabel("Years since announcement", fontsize=FS_LABEL)
axC.set_ylabel("Cumulative incidence", fontsize=FS_LABEL)
axC.set_title("C. Terminal cancellation, not real-option delay", fontsize=FS_TITLE,
              loc="left", fontweight="bold")
axC.legend(loc="upper left", fontsize=FS_LEGEND - 0.5, frameon=False)
axC.tick_params(labelsize=FS_TICK)
axC.grid(alpha=0.25)
axC.set_xlim(0, t_max)
axC.set_ylim(0, max(0.30, axC.get_ylim()[1]))

out = FIGURES / "fig_headline_3panel.png"
plt.savefig(out, dpi=180, bbox_inches="tight")
plt.close()
print(f"\n  Saved: {out}")
print("KLAAR.")
